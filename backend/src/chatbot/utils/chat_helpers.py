from typing import List, Dict, Any, Tuple
from litellm import completion
from decouple import config
import os

from .prompts import UNIFIED_PROMPT, inject_current_time

# OpenRouter configuration
OPENROUTER_API_KEY = config("OPENROUTER_API_KEY", default="")
OPENROUTER_MODEL = config("OPENROUTER_MODEL", default="openai/gpt-4o-mini")
OPENROUTER_BASE_URL = config("OPENROUTER_BASE_URL", default="https://openrouter.ai/api/v1")

# Set OpenRouter API key for LiteLLM
if OPENROUTER_API_KEY:
    os.environ["OPENROUTER_API_KEY"] = OPENROUTER_API_KEY


def detect_intent(text: str, history: List[Dict[str, str]] = None) -> Tuple[str, str]:
    """Return (intent, expanded_query) using the unified prompt with conversation context."""
    try:
        # Build conversation context
        context_messages = []
        
        # Add conversation history for context
        if history:
            context_messages.append("Recent conversation history:")
            for turn in history:
                context_messages.append(f"User: {turn['input']}")
                context_messages.append(f"Assistant: {turn['response']}")
        else:
            context_messages.append("This is the start of the conversation.")
        
        context = "\n".join(context_messages)
        
        # Debug logging
        print(f"🔍 Intent Detection Debug:")
        print(f"Current text: '{text}'")
        print(f"History length: {len(history) if history else 0}")
        print(f"Context: {context[:200]}...")
        
        resp = completion(
            model=f"openrouter/{OPENROUTER_MODEL}",
            messages=[
                {"role": "system", "content": inject_current_time(UNIFIED_PROMPT)},
                {"role": "user", "content": f"{context}\n\nUser's current message: {text}"},
            ],
            temperature=0.5,
        )
        content = resp.choices[0].message.content.strip()
        
        print(f"LLM Response: '{content}'")
        
        # Extract intent and expanded query from the response format
        intent = "CHAT"  # default
        expanded_query = text  # default to original text
        
        if "INTENT:" in content:
            intent_line = [line for line in content.split('\n') if line.strip().startswith('INTENT:')]
            if intent_line:
                intent = intent_line[0].replace('INTENT:', '').strip()
        
        if "EXPANDED_QUERY:" in content:
            query_line = [line for line in content.split('\n') if line.strip().startswith('EXPANDED_QUERY:')]
            if query_line:
                expanded_query = query_line[0].replace('EXPANDED_QUERY:', '').strip()
        
        if intent in ['SEARCH', 'CHAT', 'EXIT']:
            print(f"✅ Detected Intent: {intent}")
            print(f"✅ Expanded Query: '{expanded_query}'")
            return intent, expanded_query
        
        # Simple fallback: let the LLM's response guide us
        # If the LLM didn't follow the format, default to CHAT
        print(f"❌ No valid intent found, defaulting to CHAT")
        return "CHAT", text
    except Exception as e:
        print(f"❌ Error in detect_intent: {e}")
        return "CHAT", text


def synthesise_research(
    current_input: str, research: Dict[str, Any], temperature: float = 0.7
) -> str:
    """Synthesize research results with LLM knowledge using the unified prompt."""
    # Build research context with better formatting
    summary = research.get('summary', '')
    sources = research.get('sources', [])
    citations = research.get('citations', [])
    
    # Format sources nicely
    sources_text = ""
    if sources:
        sources_text = "Sources found:\n"
        for i, source in enumerate(sources, 1):
            # Handle both dict and SourceInfo objects
            if hasattr(source, 'title'):
                title = source.title or 'No title'
                url = source.url or 'No URL'
                snippet = source.snippet or ''
            else:
                # Fallback for dict-like objects
                title = source.get('title', 'No title')
                url = source.get('url', 'No URL')
                snippet = source.get('snippet', '')
            
            sources_text += f"{i}. {title}\n"
            sources_text += f"   URL: {url}\n"
            if snippet:
                sources_text += f"   Summary: {snippet[:200]}...\n"
            sources_text += "\n"
    
    research_context = f"""
Research Results for: "{current_input}"

Summary:
{summary}

{sources_text}

Citations: {citations if citations else 'None provided'}

Please provide a comprehensive, warm, and helpful answer based on this research information.
"""
    
    # Use the unified prompt with research context
    system_prompt = inject_current_time(UNIFIED_PROMPT)
    
    try:
        resp = completion(
            model=f"openrouter/{OPENROUTER_MODEL}",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"{research_context}\n\nBased on the research above, provide a comprehensive answer to the user's question. Be warm, helpful, and format the response clearly."},
            ],
            temperature=temperature,
        )
        
        content = resp.choices[0].message.content.strip()
        
        # Extract response from the unified format
        if "RESPONSE:" in content:
            response_lines = content.split('RESPONSE:')
            if len(response_lines) > 1:
                return response_lines[1].strip()
        
        # Fallback: return the full content if format parsing fails
        return content
        
    except Exception as e:
        return f"I'm sorry, I encountered an error: {str(e)}"


def generate_chat_reply(history: List[Dict[str, str]], user_input: str) -> str:
    """Friendly chat response using the unified prompt and full conversation history."""
    # Build conversation context
    context_messages = []
    
    # Add conversation history for context
    if history:
        context_messages.append("Recent conversation history:")
        for turn in history:
            context_messages.append(f"User: {turn['input']}")
            context_messages.append(f"Assistant: {turn['response']}")
    else:
        context_messages.append("This is the start of the conversation.")
    
    context = "\n".join(context_messages)
    
    # Use the unified prompt
    system_prompt = inject_current_time(UNIFIED_PROMPT)
    
    try:
        resp = completion(
            model=f"openrouter/{OPENROUTER_MODEL}",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"{context}\n\nUser's current message: {user_input}"},
            ],
            temperature=0.5,
        )
        
        content = resp.choices[0].message.content.strip()
        
        # Extract response from the unified format
        if "RESPONSE:" in content:
            response_lines = content.split('RESPONSE:')
            if len(response_lines) > 1:
                return response_lines[1].strip()
        
        # Fallback: return the full content if format parsing fails
        return content
        
    except Exception as e:
        return f"I'm sorry, I encountered an error: {str(e)}"


def unified_llm_call(conversation_history: List[Dict[str, str]], user_input: str) -> Tuple[str, str]:
    """
    Single LLM call that determines intent and generates response using the unified prompt.
    Returns (intent, response) tuple.
    """
    # Build conversation context
    context_messages = []
    
    # Add conversation history for context
    if conversation_history:
        context_messages.append("Recent conversation history:")
        for turn in conversation_history:
            context_messages.append(f"User: {turn['input']}")
            context_messages.append(f"Assistant: {turn['response']}")
    else:
        context_messages.append("This is the start of the conversation.")
    
    context = "\n".join(context_messages)
    
    # Use the unified prompt
    system_prompt = inject_current_time(UNIFIED_PROMPT)
    
    try:
        resp = completion(
            model=f"openrouter/{OPENROUTER_MODEL}",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"{context}\n\nUser's current message: {user_input}"},
            ],
            temperature=0.5,
        )
        
        content = resp.choices[0].message.content.strip()
        
        # Parse the unified response format
        intent = "CHAT"  # Default
        response = content
        
        if "INTENT:" in content and "RESPONSE:" in content:
            lines = content.split('\n')
            for line in lines:
                line = line.strip()
                if line.startswith('INTENT:'):
                    intent_part = line.replace('INTENT:', '').strip()
                    if intent_part in ['SEARCH', 'CHAT', 'EXIT']:
                        intent = intent_part
                elif line.startswith('RESPONSE:'):
                    response_part = line.replace('RESPONSE:', '').strip()
                    if response_part:
                        response = response_part
        
        return intent, response
        
    except Exception as e:
        return 'CHAT', f"I'm sorry, I encountered an error: {str(e)}"

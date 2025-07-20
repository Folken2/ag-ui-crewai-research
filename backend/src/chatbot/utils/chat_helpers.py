from typing import List, Dict, Any, Tuple
from litellm import completion

from .prompts import INTENT_CLASSIFIER, CHAT_SYSTEM, UNIFIED_FLOW_PROMPT, inject_current_time



def detect_intent(text: str) -> str:
    """Return SEARCH, CHAT, or EXIT (default CHAT on error)."""
    try:
        resp = completion(
            model="gemini/gemini-2.0-flash",
            messages=[
                {"role": "system", "content": INTENT_CLASSIFIER},
                {"role": "user", "content": text},
            ],
            temperature=0.1,
            max_tokens=10,  # Increased to accommodate EXIT
        )
        return resp.choices[0].message.content.strip().upper()
    except Exception:
        return "CHAT"


def synthesise_research(
    current_input: str, research: Dict[str, Any], temperature: float = 0.7
) -> str:
    """Return a formatted answer built from research results, letting the LLM decide on formatting."""
    prompt = f"""
You are an expert research assistant. Create a clean, informative response based on the research summary, sources and citations.

Research Summary:
{research.get('summary', '')}

Sources:
{research.get('sources', [])}

Citations:
{research.get('citations', [])}

User Question: {current_input}

Format your response as clean markdown with proper headers, bullet points, and emphasis. Do not include any source references or URLs.
"""
    resp = completion(
        model="gemini/gemini-2.0-flash",
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": f"Format this research into a professional response: {current_input}"},
        ],
        temperature=temperature,
    )
    return resp.choices[0].message.content


def generate_chat_reply(history: List[Dict[str, str]], user_input: str) -> str:
    """Friendly chat response using the last three turns."""
    messages = [{"role": "system", "content": CHAT_SYSTEM}]
    for turn in history[-3:]:
        messages.append({"role": "user", "content": turn["input"]})
        messages.append({"role": "assistant", "content": turn["response"]})
    messages.append({"role": "user", "content": user_input})

    resp = completion(model="gemini/gemini-2.0-flash", messages=messages, temperature=0.7)
    return resp.choices[0].message.content


def unified_llm_call(conversation_history: List[Dict[str, str]], user_input: str) -> Tuple[str, str]:
    """
    Single LLM call that determines intent and generates response.
    Returns (intent, response) tuple.
    """
    # Build conversation context
    context_messages = []
    
    # Add recent conversation history for context (last 3 turns)
    if conversation_history:
        context_messages.append("Recent conversation history:")
        for turn in conversation_history[-3:]:
            context_messages.append(f"User: {turn['input']}")
            context_messages.append(f"Assistant: {turn['response']}")
    else:
        context_messages.append("This is the start of the conversation.")
    
    context = "\n".join(context_messages)
    
    # Prepare the prompt with current time
    system_prompt = inject_current_time(UNIFIED_FLOW_PROMPT)
    
    try:
        resp = completion(
            model="gemini/gemini-2.0-flash",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"{context}\n\nUser's current message: {user_input}"},
            ],
            temperature=0.7,
            max_tokens=300,
        )
        
        response_text = resp.choices[0].message.content.strip()
        
        # Parse the response to extract intent and response
        lines = response_text.split('\n', 2)
        intent_line = next((line for line in lines if line.startswith('INTENT:')), None)
        response_line = next((line for line in lines if line.startswith('RESPONSE:')), None)
        
        if intent_line and response_line:
            intent = intent_line.replace('INTENT:', '').strip().upper()
            response = response_line.replace('RESPONSE:', '').strip()
            
            # Validate intent
            if intent not in ['SEARCH', 'CHAT', 'EXIT']:
                intent = 'CHAT'  # Default fallback
                
            return intent, response
        else:
            # Fallback if parsing fails
            return 'CHAT', response_text
            
    except Exception as e:
        return 'CHAT', f"I'm sorry, I encountered an error: {str(e)}"

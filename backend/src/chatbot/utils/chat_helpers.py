import time
from typing import List, Dict, Any, Tuple
from litellm import completion

from .prompts import INTENT_CLASSIFIER, CHAT_SYSTEM, SYNTHESIS_SYSTEM, UNIFIED_FLOW_PROMPT, inject_current_time


def display_header() -> None:
    print("\n" + "=" * 60)
    print("💭 CHAT WITH ME!")
    print("=" * 60)


def display_sources(sources: List[str]) -> None:
    if not sources:
        return
    print(f"\n{'='*60}\n📚 Sources & References:\n{'='*60}")
    for i, src in enumerate(sources, 1):
        if src:
            print(f"[{i}] {src}")
    print(f"{'='*60}")


def get_user_input() -> str | None:
    time.sleep(0.5)
    text = input("\n💬 You: ").strip()
    if not text:
        print("❌ Please say something!")
        return None
    return text


def detect_intent(text: str) -> str:
    """Return SEARCH, CHAT, or EXIT (default CHAT on error)."""
    try:
        resp = completion(
            model="openai/gpt-4o",
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
    """Return a conversational answer built from research results."""
    resp = completion(
        model="openai/gpt-4o",
        messages=[
            {"role": "system", "content": SYNTHESIS_SYSTEM},
            {"role": "user", "content": f"User asked: {current_input}"},
            {
                "role": "assistant",
                "content": (
                    "Here is the raw summary I found:\n\n"
                    f"{research.get('summary', '')}"
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Sources: {research.get('sources', [])}\n"
                    f"Citations: {research.get('citations', [])}\n\n"
                    "Please present this information naturally."
                ),
            },
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

    resp = completion(model="openai/gpt-4o", messages=messages, temperature=0.7)
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
            model="openai/gpt-4o",
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

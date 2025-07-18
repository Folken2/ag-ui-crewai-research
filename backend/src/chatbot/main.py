#!/usr/bin/env python
import time
from typing import List, Optional
from pydantic import BaseModel, Field

from crewai.flow import Flow, listen, start, router, or_
from litellm import completion

from dotenv import load_dotenv
load_dotenv()

# Import listeners to register them with the event bus
from . import listeners

from .utils.chat_helpers import (
    display_header,
    display_sources,
    get_user_input,
    detect_intent,
    synthesise_research,
    generate_chat_reply,
)

from .crews.research_crew.research_crew import ResearchCrew

class ChatState(BaseModel):
    """Simple state management for the chat flow."""
    conversation_history: List[dict] = Field(default_factory=list)
    current_input: str = ""
    research_failed: bool = False
    research_error_message: str = ""
    research_results: Optional[dict] = None
    has_new_research: bool = False
    session_ended: bool = False


class SimpleChatFlow(Flow[ChatState]):
    """
    Simple chat flow: Start → Chat → Route to Research or Exit → Research loops back to Chat
    """

    @start()
    def start_flow(self):
        """Initialize the chat flow."""
        print("Flow started!")
        print("\n🤖 Hello! I'm your AI-powered assistant.")
        print("💬 I can chat with you or search for current information.")
        print("📝 Just ask me anything or say 'search for [topic]' for web research!")

    @router(or_(start_flow, "route_back_to_chat", "research_crew"))
    def chat_method(self):
        # Check if session should end first
        if self.state.session_ended:
            return "route_exit"
            
        display_header()

        # -------- 1. research synthesis --------
        if self.state.has_new_research and self.state.research_results:
            print("🔄 Processing research results...")
            answer = synthesise_research(
                self.state.current_input, self.state.research_results
            )
            self.state.conversation_history.append(
                {
                    "input": self.state.current_input,
                    "response": answer,
                    "type": "research_enhanced",
                    "raw_research": self.state.research_results.get("summary", ""),
                    "sources": self.state.research_results.get("sources", []),
                }
            )
            print(f"\n{'='*60}\n🤖 AI Response:\n{'='*60}")
            print(answer)
            display_sources(self.state.research_results.get("sources", []))
            self.state.has_new_research = False
            self.state.research_results = None
            return "route_back_to_chat"

        # -------- 2. handle failed research once --------
        if self.state.research_failed:
            print(f"⚠️ Research failed: {self.state.research_error_message}")
            self.state.research_failed = False
            self.state.research_error_message = ""

        # -------- 3. get user input --------
        user_input = get_user_input()
        if user_input is None:
            return "route_back_to_chat"
        self.state.current_input = user_input

        # -------- 4. intent detection --------
        intent = detect_intent(user_input)
        if intent == "EXIT":
            print("👋 Ending session...")
            self.state.session_ended = True
            return "route_exit"
        elif intent == "SEARCH":
            print("🔍 Search intent detected – routing to research crew...")
            return "route_research"

        # -------- 5. normal chat --------
        print("💬 Chat intent detected – generating response...")
        reply = generate_chat_reply(self.state.conversation_history, user_input)
        self.state.conversation_history.append(
            {"input": user_input, "response": reply, "type": "chat"}
        )
        print(f"\n{'='*60}\n🤖 AI Response:\n{'='*60}")
        print(reply)
        print(f"{'='*60}")
        return "route_back_to_chat"

    @listen("route_research")
    def research_crew(self):
        """Handle search requests using research crew and store results in shared state."""
        print("🔬 Starting research...")
        try:
            search_result = ResearchCrew().crew().kickoff(inputs={"query": self.state.current_input})
            
            # Extract data directly from CrewOutput using the pydantic method
            pydantic_result = search_result.pydantic
            self.state.research_results = {
                "summary": pydantic_result.summary if hasattr(pydantic_result, 'summary') else "",
                "sources": pydantic_result.sources if hasattr(pydantic_result, 'sources') else [],
                "citations": pydantic_result.citations if hasattr(pydantic_result, 'citations') else []
            }
            
            self.state.has_new_research = True
            
            # Clear any failure flags
            self.state.research_failed = False
            self.state.research_error_message = ""
            
        except Exception as e:
            print(f"❌ Research failed: {e}")
            # Set failure flag for chat method to handle gracefully
            self.state.research_failed = True
            self.state.research_error_message = str(e)
        
        # Return to chat for synthesis or error handling
        return "route_back_to_chat"

    @listen("route_exit")
    def exit_method(self):
        """Clean exit from the flow."""
        print(f"\n🎯 Chat session completed!")
        print(f"📈 Total conversations: {len(self.state.conversation_history)}")
        print("👋 Thanks for chatting!")
        # Don't return any route - this terminates the flow

    def is_session_active(self) -> bool:
        """Check if the chat session is still active."""
        return not self.state.session_ended

    def get_session_stats(self) -> dict:
        """Get session statistics."""
        return {
            "total_conversations": len(self.state.conversation_history),
            "session_ended": self.state.session_ended,
            "has_research_results": self.state.research_results is not None,
            "research_failed": self.state.research_failed
        }


def kickoff():
    """Start the simple chat flow."""
    print("Starting chat flow...")
    chat_flow = SimpleChatFlow()
    chat_flow.kickoff()


def plot():
    """Visualize the flow structure."""
    chat_flow = SimpleChatFlow()
    chat_flow.plot()


if __name__ == "__main__":
    kickoff()


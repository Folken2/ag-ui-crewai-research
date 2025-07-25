#!/usr/bin/env python
"""
AG-UI compatible server for CrewAI flow
Enhanced with real-time event streaming for Perplexity-like experience
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, AsyncGenerator
import json
import asyncio
from datetime import datetime

# Import listeners to register them with the event bus
from .listeners.real_time_listener import real_time_listener


from .main import ChatState

from .utils.chat_helpers import (
    detect_intent,
    generate_chat_reply,
    synthesise_research,
)
from .crews.research_crew.research_crew import ResearchCrew


# -------------------------------------------------------------
# Enhanced wrapper that utilises the existing helpers + crews and
# provides real-time event streaming capabilities
# -------------------------------------------------------------


class ChatbotSession:
    """Self-contained session replicating the behaviour of `SimpleChatFlow` with real-time events."""

    def __init__(self):
        self.state = ChatState()

    # ------------------------- Core API ----------------------
    def process_message(self, user_message: str) -> Dict[str, Any]:
        """Process a single user message and return a response payload."""
        
        # Reset event listener session for new message
        real_time_listener.reset_session()
        
        self.state.current_input = user_message

        # 1. Detect intent (SEARCH, CHAT, EXIT)
        intent = detect_intent(user_message)
        
        # 2. Handle EXIT intent upfront
        if intent == "EXIT":
            self.state.session_ended = True
            return {
                "intent": "EXIT",
                "response": "👋 Session ended. Feel free to start a new one whenever you like!",
            }

        # 3. Handle SEARCH intent via ResearchCrew
        if intent == "SEARCH":
            try:
                search_result = ResearchCrew().crew().kickoff(inputs={"query": user_message})

                pyd_res = search_result.pydantic
                research_results = {
                    "summary": getattr(pyd_res, "summary", ""),
                    "sources": getattr(pyd_res, "sources", []),
                    "citations": getattr(pyd_res, "citations", []),
                }

                # Store research in state for potential future use
                self.state.research_results = research_results
                self.state.has_new_research = True

                # Synthesize final answer from the raw research
                answer = synthesise_research(user_message, research_results)

                # Persist turn in history
                self.state.conversation_history.append(
                    {
                        "input": user_message,
                        "response": answer,
                        "type": "research_enhanced",
                        "sources": research_results.get("sources", []),
                    }
                )

                return {
                    "intent": "SEARCH",
                    "response": answer,
                    "sources": research_results.get("sources", []),
                }
            except Exception as e:
                return {"error": str(e)}

        # 4. Default: regular chat
        reply = generate_chat_reply(self.state.conversation_history, user_message)
        self.state.conversation_history.append(
            {"input": user_message, "response": reply, "type": "chat"}
        )

        return {"intent": "CHAT", "response": reply, "token_usage": 0}

    # ---------------------- Utility helpers ------------------
    def is_session_active(self) -> bool:
        return not self.state.session_ended

    def get_conversation_history(self) -> list:
        return self.state.conversation_history


# Factory expected by the rest of this module
def create_chatbot() -> ChatbotSession:
    return ChatbotSession()

app = FastAPI()

# Add CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AGUIFlowAdapter:
    def __init__(self):
        self.flow = create_chatbot()

    def _format_research_content(self, content: str) -> str:
        """Format research content with clean, professional formatting"""
        if not content:
            return content
            
        # Clean up the content first
        content = content.strip()
        
        # Split into paragraphs
        paragraphs = content.split('\n\n')
        formatted_paragraphs = []
        
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue
                
            # Handle bullet points that start with • 
            if paragraph.startswith('•'):
                # Split multiple bullet points in the same paragraph
                bullets = [line.strip() for line in paragraph.split('•') if line.strip()]
                for bullet in bullets:
                    bullet = bullet.strip()
                    if bullet:
                        formatted_paragraphs.append(f"• {bullet}")
                continue
            
            # Check for short paragraphs that might be headers
            if (len(paragraph) < 80 and 
                not paragraph.endswith('.') and 
                not paragraph.endswith('!') and 
                not paragraph.endswith('?') and
                not paragraph.startswith('In ') and
                not paragraph.startswith('The ') and
                not paragraph.startswith('This ')):
                formatted_paragraphs.append(f"## {paragraph}")
                continue
            
            # Regular paragraphs - keep them clean
            formatted_paragraphs.append(paragraph)
        
        return '\n\n'.join(formatted_paragraphs)
    
    def _emphasize_key_terms(self, text: str) -> str:
        """Simple emphasis for key terms - kept for compatibility"""
        return text

    async def process_message(self, user_message: str):
        """Process message through our unified chatbot flow and emit real-time events"""
        
        # Start event
        yield self._create_event("RUN_STARTED", {
            "status": "processing",
            "message": f"Processing: {user_message}"
        })
        
        # Reset the listener for new execution
        real_time_listener.reset_session()
        
        # Start the flow execution in a separate task
        flow_task = asyncio.create_task(self._run_flow_message(user_message))
        
        # Track processed events to avoid duplicates
        processed_events = set()
        
        try:
            # Monitor for events while the flow is running
            while not flow_task.done():
                # Check for new events
                events = real_time_listener.get_events_realtime()
                for event in events:
                    # Create a unique identifier for this event
                    event_id = f"{event['type']}-{event['timestamp']}"
                    if event_id not in processed_events:
                        processed_events.add(event_id)
                        yield self._create_ag_ui_event(event)
                
                # Minimal delay to prevent CPU spinning but allow immediate streaming
                await asyncio.sleep(0.01)
            
            # Get the flow result
            result = await flow_task
            
            # Stream any remaining events
            events = real_time_listener.get_events_realtime()
            for event in events:
                event_id = f"{event['type']}-{event['timestamp']}"
                if event_id not in processed_events:
                    processed_events.add(event_id)
                    yield self._create_ag_ui_event(event)
            
            if "error" in result:
                yield self._create_event("TEXT_MESSAGE_DELTA", {
                    "content": f"❌ Error: {result['error']}"
                })
            else:
                # Determine how to format based on intent
                intent = result.get("intent", "CHAT")
                response = result.get("response", "")
                
                if intent == "SEARCH":
                    # Format research response
                    formatted_content = self._format_research_content(response)
                    yield self._create_event("TEXT_MESSAGE_DELTA", {
                        "content": formatted_content
                    })
                    
                    # Send sources if available
                    sources = result.get("sources", [])
                    if sources:
                        # Handle both old string format and new SourceInfo format
                        formatted_sources = []
                        for source in sources[:5]:
                            if isinstance(source, str):
                                # Old format - convert to new format
                                formatted_sources.append({
                                    "url": source,
                                    "title": self._extract_domain(source),
                                    "image_url": None,
                                    "snippet": None
                                })
                            elif hasattr(source, 'url'):
                                # New SourceInfo format
                                formatted_sources.append({
                                    "url": source.url,
                                    "title": source.title or self._extract_domain(source.url),
                                    "image_url": getattr(source, 'image_url', None),
                                    "snippet": getattr(source, 'snippet', None)
                                })
                        
                        yield self._create_event("SOURCES_UPDATE", {
                            "sources": formatted_sources
                        })
                else:
                    # Regular chat response
                    yield self._create_event("TEXT_MESSAGE_DELTA", {
                        "content": response
                    })
                    
        except Exception as e:
            # Cancel the flow task if it's still running
            if not flow_task.done():
                flow_task.cancel()
            yield self._create_event("TEXT_MESSAGE_DELTA", {
                "content": f"❌ Unexpected error: {str(e)}"
            })
        
        # Finish event
        yield self._create_event("RUN_FINISHED", {
            "status": "complete"
        })
    
    async def _run_flow_message(self, user_message: str):
        """Run the flow message processing in executor"""
        def process_flow():
            try:
                # Use our simplified flow's process_message method
                return self.flow.process_message(user_message)
            except Exception as e:
                return {"error": str(e)}
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, process_flow)
    
    def _create_event(self, event_type: str, data: Dict[str, Any]):
        """Create AG-UI event"""
        return {
            "type": event_type,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }

    def _create_ag_ui_event(self, stream_event: Dict[str, Any]):
        """Convert real-time listener event to AG-UI format"""
        event_type_mapping = {
            "CREW_STARTED": "EXECUTION_STATUS",
            "CREW_COMPLETED": "EXECUTION_STATUS", 
            "AGENT_STARTED": "AGENT_STATUS",
            "AGENT_FINISHED": "AGENT_STATUS",
            "AGENT_COMPLETED": "AGENT_STATUS",
            "AGENT_ERROR": "AGENT_ERROR",
            "TASK_STARTED": "TASK_STATUS",
            "TASK_COMPLETED": "TASK_STATUS", 
            "TASK_FAILED": "TASK_ERROR",
            "TOOL_STARTED": "TOOL_USAGE",
            "TOOL_COMPLETED": "TOOL_USAGE",
            "TOOL_ERROR": "TOOL_ERROR",
            "LLM_STARTED": "LLM_STATUS",
            "LLM_COMPLETED": "LLM_STATUS",
            "LLM_ERROR": "LLM_ERROR",
            "LLM_STREAM_CHUNK": "TEXT_MESSAGE_DELTA"
        }
        
        ag_ui_type = event_type_mapping.get(stream_event["type"], "EXECUTION_STATUS")
        
        # Special handling for streaming chunks
        if stream_event["type"] == "LLM_STREAM_CHUNK":
            return {
                "type": "TEXT_MESSAGE_DELTA",
                "data": {
                    "content": stream_event["data"]["chunk"]
                },
                "timestamp": stream_event["timestamp"]
            }
        
        return {
            "type": ag_ui_type,
            "data": stream_event["data"],
            "timestamp": stream_event["timestamp"]
        }

    def _extract_domain(self, url: str) -> str:
        """Extract a clean domain name from URL"""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            domain = parsed.netloc
            # Remove www. if present
            if domain.startswith('www.'):
                domain = domain[4:]
            return domain.capitalize()
        except:
            return "Source"



# Global adapter
adapter = AGUIFlowAdapter()

@app.post("/agent")
async def agent_endpoint(request: Dict[str, Any]):
    """Main AG-UI endpoint with real-time event streaming"""
    
    messages = request.get("messages", [])
    if not messages:
        return {"error": "No messages"}
    
    user_message = messages[-1].get("content", "")
    if not user_message:
        return {"error": "Empty message"}
    
    async def event_stream():
        async for event in adapter.process_message(user_message):
            yield f"data: {json.dumps(event)}\n\n"
        yield "data: [DONE]\n\n"
    
    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream"
    )

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/flow/status")
async def flow_status():
    """Get current flow status including real-time event statistics"""
    return {
        "session_active": adapter.flow.is_session_active(),
        "conversation_count": len(adapter.flow.get_conversation_history()),
        "real_time_status": real_time_listener.get_session_status()
    }

@app.get("/flow/events")
async def get_pending_events():
    """Get any pending real-time events"""
    return {
        "events": real_time_listener.get_events_realtime(),
        "session_status": real_time_listener.get_session_status()
    }

@app.post("/flow/reset")
async def reset_flow():
    """Reset the flow to start fresh"""
    adapter.flow = create_chatbot()
    real_time_listener.reset_session()
    return {"status": "reset", "message": "Flow has been reset"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 
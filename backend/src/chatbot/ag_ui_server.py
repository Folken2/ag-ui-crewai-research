#!/usr/bin/env python
"""
AG-UI compatible server for CrewAI flow
Enhanced with real-time event streaming for Perplexity-like experience
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import Dict, Any, AsyncGenerator, List
import json
import asyncio
from datetime import datetime, timedelta

# Import authentication
from .auth import (
    authenticate_user, 
    create_access_token, 
    get_current_active_user, 
    User, 
    Token,
    fake_users_db,
    ACCESS_TOKEN_EXPIRE_MINUTES
)

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
        self.session_id = None

    # ------------------------- Core API ----------------------
    def process_message(self, user_message: str, conversation_history: List[Dict[str, str]] = None) -> Dict[str, Any]:
        """Process a single user message and return a response payload."""
        
        # Only reset event listener session for new chat sessions, not for each message
        if not self.session_id:
            real_time_listener.reset_session()
            self.session_id = real_time_listener.session_id
        
        self.state.current_input = user_message

        # Initialize conversation history if provided (from frontend)
        if conversation_history is not None:
            self.state.conversation_history = conversation_history

        # 1. Detect intent (SEARCH, CHAT, EXIT) and get expanded query
        intent, expanded_query = detect_intent(user_message, self.state.conversation_history)
        
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
                search_result = ResearchCrew().crew().kickoff(inputs={"query": expanded_query})

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

        # 4. Default: regular chat with full conversation history
        reply = generate_chat_reply(self.state.conversation_history, user_message)
        self.state.conversation_history.append(
            {"input": user_message, "response": reply, "type": "chat"}
        )

        return {"intent": "CHAT", "response": reply, "token_usage": 0}

    def start_new_chat(self):
        """Start a new chat session, clearing all history and state."""
        self.state = ChatState()
        self.session_id = None
        real_time_listener.reset_session()

    # ---------------------- Utility helpers ------------------
    def is_session_active(self) -> bool:
        return not self.state.session_ended

    def get_conversation_history(self) -> list:
        return self.state.conversation_history

    def get_session_id(self) -> str:
        return self.session_id or "no-session"


# Factory expected by the rest of this module
def create_chatbot() -> ChatbotSession:
    return ChatbotSession()

app = FastAPI()

# Add CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for production
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

    async def process_message(self, user_message: str, conversation_history: List[Dict[str, str]] = None):
        """Process message through our unified chatbot flow and emit real-time events"""
        
        # Start event
        yield self._create_event("RUN_STARTED", {
            "status": "processing",
            "message": f"Processing: {user_message}"
        })
        
        # Reset the listener for new execution
        real_time_listener.reset_session()
        
        # Start the flow execution in a separate task
        flow_task = asyncio.create_task(self._run_flow_message(user_message, conversation_history))
        
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
    
    async def _run_flow_message(self, user_message: str, conversation_history: List[Dict[str, str]] = None):
        """Run the flow message processing in executor"""
        def process_flow():
            try:
                # Use our simplified flow's process_message method
                return self.flow.process_message(user_message, conversation_history)
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
            "AGENT_STARTED": "AGENT_STATUS",
            "AGENT_FINISHED": "AGENT_STATUS",
            "AGENT_ERROR": "AGENT_ERROR", 
            "TASK_FAILED": "TASK_ERROR",
            "TOOL_STARTED": "TOOL_USAGE",
            "TOOL_COMPLETED": "TOOL_USAGE",
            "TOOL_ERROR": "TOOL_ERROR",
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

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "AG-UI CrewAI Research Assistant API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "token": "/token",
            "agent": "/agent",
            "docs": "/docs"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "Server is running"}

# Authentication endpoints
@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """Login endpoint to get access token - creates permanent token for Railway deployment"""
    user = authenticate_user(fake_users_db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create permanent token (no expiration)
    access_token = create_access_token(data={"sub": user.username}, expires_delta=None)
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    """Get current user information"""
    return current_user

@app.post("/agent")
async def agent_endpoint(request: Dict[str, Any], current_user: User = Depends(get_current_active_user)):
    """Main AG-UI endpoint with real-time event streaming"""
    
    messages = request.get("messages", [])
    if not messages:
        return {"error": "No messages"}
    
    user_message = messages[-1].get("content", "")
    if not user_message:
        return {"error": "Empty message"}
    
    # Convert frontend conversation history to backend format
    conversation_history = []
    for msg in messages[:-1]:  # All messages except the current one
        if msg.get("role") == "user":
            conversation_history.append({
                "input": msg.get("content", ""),
                "response": "",  # Will be filled by next assistant message
                "type": "chat"
            })
        elif msg.get("role") == "assistant":
            # Update the last conversation turn with the assistant's response
            if conversation_history:
                conversation_history[-1]["response"] = msg.get("content", "")

    async def event_stream():
        async for event in adapter.process_message(user_message, conversation_history):
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
async def flow_status(current_user: User = Depends(get_current_active_user)):
    """Get current flow status including real-time event statistics"""
    return {
        "session_active": adapter.flow.is_session_active(),
        "conversation_count": len(adapter.flow.get_conversation_history()),
        "real_time_status": real_time_listener.get_session_status()
    }

@app.get("/flow/events")
async def get_pending_events(current_user: User = Depends(get_current_active_user)):
    """Get any pending real-time events"""
    return {
        "events": real_time_listener.get_events_realtime(),
        "session_status": real_time_listener.get_session_status()
    }

@app.post("/flow/reset")
async def reset_flow(current_user: User = Depends(get_current_active_user)):
    """Reset the flow and start a new chat session"""
    adapter.flow.start_new_chat()
    return {"status": "reset", "message": "New chat session started"}

@app.post("/flow/new-chat")
async def start_new_chat(current_user: User = Depends(get_current_active_user)):
    """Start a new chat session, clearing all history"""
    adapter.flow.start_new_chat()
    return {
        "status": "new_chat", 
        "message": "New chat session started",
        "session_id": adapter.flow.get_session_id()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 
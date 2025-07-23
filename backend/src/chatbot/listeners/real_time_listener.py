from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict
from datetime import datetime
import queue
import threading
import uuid

from crewai.utilities.events import (
    CrewKickoffStartedEvent,
    CrewKickoffCompletedEvent,
    AgentExecutionStartedEvent,
    AgentExecutionCompletedEvent,
)
from crewai.utilities.events.base_event_listener import BaseEventListener


@dataclass
class StreamEvent:
    """Data structure for streaming events to frontend"""
    type: str
    data: Dict[str, Any]
    timestamp: str
    agent_id: Optional[str] = None
    session_id: Optional[str] = None


class RealTimeListener(BaseEventListener):
    """
    Real-time event listener that captures CrewAI events and streams them to the frontend.
    Provides Perplexity-like real-time visibility into agent execution.
    """
    
    def __init__(self):
        super().__init__()
        
        self.event_queue = queue.Queue()
        self.session_id = str(uuid.uuid4())
        
    def setup_listeners(self, crewai_event_bus):
        """Setup all event listeners for comprehensive monitoring"""
        
        # ==================== AGENT EVENTS ====================
        
        @crewai_event_bus.on(CrewKickoffStartedEvent)
        def on_crew_kickoff_started(source, event: CrewKickoffStartedEvent):
            self._emit_event(StreamEvent(
                type="CREW_STARTED",
                data={
                    "message": "Starting research...",
                    "status": "executing"
                },
                timestamp=datetime.now().isoformat(),
                session_id=self.session_id
            ))

        @crewai_event_bus.on(AgentExecutionStartedEvent)
        def on_agent_execution_started(source, event: AgentExecutionStartedEvent):
            agent = getattr(event, 'agent', None)
            if agent:
                agent_id = str(agent.id)
                agent_role = getattr(agent, 'role', 'Research Agent')
                
                # Emit the thinking message immediately when agent starts
                self._emit_event(StreamEvent(
                    type="AGENT_STARTED",
                    data={
                        "agent_role": agent_role,
                        "message": "Research agent thinking...",
                        "status": "executing"
                    },
                    timestamp=datetime.now().isoformat(),
                    agent_id=agent_id,
                    session_id=self.session_id
                ))

        @crewai_event_bus.on(AgentExecutionCompletedEvent)
        def on_agent_execution_finished(source, event: AgentExecutionCompletedEvent):
            agent = getattr(event, 'agent', None)
            if agent:
                agent_id = str(agent.id)
                agent_role = getattr(agent, 'role', 'Research Agent')
                
                # Emit the final thoughts message when agent finishes
                self._emit_event(StreamEvent(
                    type="AGENT_FINISHED",
                    data={
                        "agent_role": agent_role,
                        "message": "Gathering final thoughts...",
                        "status": "finished"
                    },
                    timestamp=datetime.now().isoformat(),
                    agent_id=agent_id,
                    session_id=self.session_id
                ))


    def _emit_event(self, event: StreamEvent):
        """Emit event to the queue for frontend consumption"""
        # Clean the event data to ensure JSON serialization
        clean_event = self._clean_event_data(event)
        self.event_queue.put_nowait(clean_event)
        # Debug output for essential events only
        if event.type in ["AGENT_STARTED", "AGENT_FINISHED"]:
            print(f"🔔 Event: {event.data.get('message', '')}")

    def _clean_event_data(self, event: StreamEvent) -> StreamEvent:
        """Clean event data to ensure JSON serialization"""
        # Create a clean copy of the event data
        clean_data = {}
        for key, value in event.data.items():
            if isinstance(value, (str, int, float, bool, type(None))):
                clean_data[key] = value
            else:
                # Convert other types to string
                clean_data[key] = str(value)
        
        # Create a new event with cleaned data
        return StreamEvent(
            type=event.type,
            data=clean_data,
            timestamp=event.timestamp,
            agent_id=event.agent_id,
            session_id=event.session_id
        )

    def get_events_realtime(self) -> List[Dict[str, Any]]:
        """Get events and immediately return them for real-time streaming"""
        events = []
        while True:
            try:
                event = self.event_queue.get_nowait()
                events.append(asdict(event))
            except queue.Empty:
                break
        return events

    def get_session_status(self) -> Dict[str, Any]:
        """Get current session status and statistics"""
        return {
            "session_id": self.session_id,
            "events_pending": self.event_queue.qsize()
        }

    def reset_session(self):
        """Reset the session and clear all events"""
        self.session_id = str(uuid.uuid4())
        
        while True:
            try:
                self.event_queue.get_nowait()
            except queue.Empty:
                break


# Create a global instance of the listener
real_time_listener = RealTimeListener() 
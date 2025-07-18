from typing import Optional, Dict, Any, List
import json
import time
from dataclasses import dataclass, asdict
from datetime import datetime
import asyncio
import queue
import threading

from crewai.utilities.events import (
    CrewKickoffStartedEvent,
    AgentExecutionStartedEvent,
    AgentExecutionCompletedEvent,
    AgentExecutionErrorEvent,
)
from crewai.utilities.events.base_event_listener import BaseEventListener


@dataclass
class StreamEvent:
    """Data structure for streaming events to frontend"""
    type: str
    data: Dict[str, Any]
    timestamp: str
    agent_id: Optional[str] = None
    task_id: Optional[str] = None
    session_id: Optional[str] = None


class RealTimeListener(BaseEventListener):
    """
    Real-time event listener that captures CrewAI events and streams them to the frontend.
    Provides Perplexity-like real-time visibility into agent execution.
    """
    
    def __init__(self):
        super().__init__()
        # Thread-safe queue for events
        self.event_queue = queue.Queue()
        self.session_id = f"session_{int(time.time())}"
        self.current_crew_name = None
        self.active_agents = {}
        self.active_tasks = {}
        self.tool_execution_stack = []
        
    def setup_listeners(self, crewai_event_bus):
        """Setup all event listeners for comprehensive monitoring"""
        
        # ==================== CREW EVENTS ====================
        @crewai_event_bus.on(CrewKickoffStartedEvent)
        def on_crew_kickoff_started(source, event: CrewKickoffStartedEvent):
            self.current_crew_name = getattr(event, 'crew_name', 'Research Crew')
            
            # Register agents for tracking
            if hasattr(source, 'agents'):
                for agent in source.agents:
                    self.active_agents[str(agent.id)] = {
                        'role': agent.role,
                        'goal': agent.goal,
                        'status': 'initialized'
                    }
            
            # Skip crew start event - we handle it in custom sequence
            pass

        # ==================== AGENT EVENTS ====================
        @crewai_event_bus.on(AgentExecutionStartedEvent)
        def on_agent_execution_started(source, event: AgentExecutionStartedEvent):
            agent = getattr(event, 'agent', None)
            if agent:
                agent_id = str(agent.id)
                agent_role = getattr(agent, 'role', 'Research Agent')
                
                # Update agent status
                if agent_id in self.active_agents:
                    self.active_agents[agent_id]['status'] = 'executing'
                
                # Emit the first message immediately when agent starts
                self._emit_event(StreamEvent(
                    type="AGENT_STARTED",
                    data={
                        "agent_role": agent_role,
                        "message": "🚀 Starting research...",
                        "status": "executing"
                    },
                    timestamp=datetime.now().isoformat(),
                    agent_id=agent_id,
                    session_id=self.session_id
                ))
                
                # Schedule the thinking message after 2 seconds
                def emit_thinking():
                    self._emit_event(StreamEvent(
                        type="AGENT_STARTED",
                        data={
                            "agent_role": agent_role,
                            "message": "💭 Research agent thinking...",
                            "status": "executing"
                        },
                        timestamp=datetime.now().isoformat(),
                        agent_id=agent_id,
                        session_id=self.session_id
                    ))
                
                threading.Timer(2.0, emit_thinking).start()
                
                # Schedule the final thoughts message after 9 seconds
                def emit_final_thoughts():
                    self._emit_event(StreamEvent(
                        type="AGENT_STARTED",
                        data={
                            "agent_role": agent_role,
                            "message": "🧠 Gathering final thoughts...",
                            "status": "executing"
                        },
                        timestamp=datetime.now().isoformat(),
                        agent_id=agent_id,
                        session_id=self.session_id
                    ))
                
                threading.Timer(9.0, emit_final_thoughts).start()

        @crewai_event_bus.on(AgentExecutionCompletedEvent)
        def on_agent_execution_completed(source, event: AgentExecutionCompletedEvent):
            # Skip agent completion events
            pass

        @crewai_event_bus.on(AgentExecutionErrorEvent)
        def on_agent_execution_error(source, event: AgentExecutionErrorEvent):
            # Skip agent error events
            pass


    def _emit_event(self, event: StreamEvent):
        """Emit event to the queue for frontend consumption"""
        try:
            # Filter events to reduce noise - only emit meaningful events
            if self._should_emit_event(event):
                # Clean the event data to ensure JSON serialization
                clean_event = self._clean_event_data(event)
                self.event_queue.put_nowait(clean_event)
                # Debug output for essential events only
                if event.type in ["CREW_STARTED", "AGENT_STARTED", "TASK_STARTED", "TOOL_STARTED", "LLM_STARTED"]:
                    print(f"🔔 Event: {event.data.get('message', '')}")
        except queue.Full:
            # If queue is full, remove oldest event and add new one
            try:
                self.event_queue.get_nowait()
                clean_event = self._clean_event_data(event)
                self.event_queue.put_nowait(clean_event)
            except queue.Empty:
                pass

    def _should_emit_event(self, event: StreamEvent) -> bool:
        """Collect all events for frontend processing"""
        
        # Collect all events - let frontend handle the display logic
        return True

    def _clean_event_data(self, event: StreamEvent) -> StreamEvent:
        """Clean event data to ensure JSON serialization"""
        # Create a clean copy of the event data
        clean_data = {}
        for key, value in event.data.items():
            if isinstance(value, (str, int, float, bool, type(None))):
                clean_data[key] = value
            elif isinstance(value, (list, dict)):
                # Recursively clean nested structures
                clean_data[key] = self._clean_nested_data(value)
            else:
                # Convert other types to string
                clean_data[key] = str(value)
        
        # Create a new event with cleaned data
        return StreamEvent(
            type=event.type,
            data=clean_data,
            timestamp=event.timestamp,
            agent_id=event.agent_id,
            task_id=event.task_id,
            session_id=event.session_id
        )
    
    def _clean_nested_data(self, data):
        """Recursively clean nested data structures"""
        if isinstance(data, dict):
            clean_dict = {}
            for key, value in data.items():
                if isinstance(value, (str, int, float, bool, type(None))):
                    clean_dict[key] = value
                elif isinstance(value, (list, dict)):
                    clean_dict[key] = self._clean_nested_data(value)
                else:
                    clean_dict[key] = str(value)
            return clean_dict
        elif isinstance(data, list):
            clean_list = []
            for item in data:
                if isinstance(item, (str, int, float, bool, type(None))):
                    clean_list.append(item)
                elif isinstance(item, (list, dict)):
                    clean_list.append(self._clean_nested_data(item))
                else:
                    clean_list.append(str(item))
            return clean_list
        else:
            return str(data)

    def get_events(self) -> List[Dict[str, Any]]:
        """Get all pending events from the queue"""
        events = []
        while True:
            try:
                event = self.event_queue.get_nowait()
                events.append(asdict(event))
            except queue.Empty:
                break
        return events

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
            "crew_name": self.current_crew_name,
            "active_agents": self.active_agents,
            "active_tasks": self.active_tasks,
            "tools_in_execution": len(self.tool_execution_stack),
            "events_pending": self.event_queue.qsize()
        }

    def reset_session(self):
        """Reset the session and clear all events"""
        self.session_id = f"session_{int(time.time())}"
        self.current_crew_name = None
        self.active_agents = {}
        self.active_tasks = {}
        self.tool_execution_stack = []
        
        # Clear the event queue
        while True:
            try:
                self.event_queue.get_nowait()
            except queue.Empty:
                break


# Create a global instance of the listener
real_time_listener = RealTimeListener() 
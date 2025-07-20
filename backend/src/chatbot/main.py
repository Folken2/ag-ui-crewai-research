#!/usr/bin/env python
"""
Main module for the CrewAI chatbot flow
Contains the ChatState class and core flow logic
"""

from pydantic import BaseModel
from typing import List, Dict, Any, Optional


class ChatState(BaseModel):
    """State management for the chatbot session."""
    
    # Current session state
    current_input: str = ""
    session_ended: bool = False
    
    # Conversation history
    conversation_history: List[Dict[str, Any]] = []
    
    # Research results
    research_results: Optional[Dict[str, Any]] = None
    has_new_research: bool = False
    
    # Processing state
    is_processing: bool = False
    
    # Event tracking
    last_event_update: Optional[str] = None

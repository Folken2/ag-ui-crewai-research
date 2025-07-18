# CrewAI EventBus Implementation

This document describes the implementation of CrewAI's EventBus listeners to provide real-time visibility into agent execution, similar to Perplexity's interface.

## Overview

The EventBus system captures all significant events during CrewAI execution and streams them to the frontend in real-time, providing users with detailed visibility into:

- 🚀 Crew initialization and completion
- 🤖 Agent execution status
- 📋 Task processing
- 🔍 Tool usage with queries
- 🧠 LLM calls and responses
- ⚡ Real-time streaming of execution progress

## Architecture

### Backend Components

#### 1. Event Listener (`src/chatbot/listeners/real_time_listener.py`)

The `RealTimeListener` class extends `BaseEventListener` and captures all relevant CrewAI events:

```python
class RealTimeListener(BaseEventListener):
    def setup_listeners(self, crewai_event_bus):
        # Registers handlers for all relevant events
        @crewai_event_bus.on(CrewKickoffStartedEvent)
        def on_crew_kickoff_started(source, event):
            # Handle crew start event
```

**Supported Events:**
- **Crew Events**: `CrewKickoffStartedEvent`, `CrewKickoffCompletedEvent`, `CrewKickoffFailedEvent`
- **Agent Events**: `AgentExecutionStartedEvent`, `AgentExecutionCompletedEvent`, `AgentExecutionErrorEvent`
- **Task Events**: `TaskStartedEvent`, `TaskCompletedEvent`, `TaskFailedEvent`
- **Tool Events**: `ToolUsageStartedEvent`, `ToolUsageFinishedEvent`, `ToolUsageErrorEvent`
- **LLM Events**: `LLMCallStartedEvent`, `LLMCallCompletedEvent`, `LLMCallFailedEvent`, `LLMStreamChunkEvent`

#### 2. Enhanced AG-UI Server (`src/chatbot/ag_ui_server.py`)

The server has been enhanced to:
- Integrate with the real-time listener
- Stream events to the frontend via Server-Sent Events (SSE)
- Convert CrewAI events to AG-UI compatible format
- Provide execution status endpoints

#### 3. Event Integration in Main Flow (`src/chatbot/main.py`)

The main flow imports the listeners to register them:
```python
# Import listeners to register them with the event bus
from . import listeners
```

### Frontend Components

#### 1. Execution Tracker (`frontend/src/components/ExecutionTracker.tsx`)

A React component that displays real-time execution status:

```tsx
<ExecutionTracker 
  events={executionEvents} 
  isProcessing={chatState.processing} 
/>
```

**Features:**
- 📊 Real-time event display with animations
- 🎨 Color-coded status indicators
- ⏱️ Execution timing information
- 🔄 Auto-clearing after completion

#### 2. Enhanced Chat Interface (`frontend/src/components/ChatInterface.tsx`)

Updated to handle and display execution events:
- Captures real-time events from SSE stream
- Displays execution tracker during processing
- Provides seamless user experience

## Event Flow

1. **User sends message** → Frontend sends request to `/agent` endpoint
2. **Server processes** → CrewAI execution begins, triggering events
3. **Event listeners capture** → All execution events are captured in real-time
4. **Events streamed** → Events converted to AG-UI format and streamed via SSE
5. **Frontend displays** → ExecutionTracker shows real-time progress
6. **Completion** → Final response displayed with sources

## Event Types and Data Structure

### StreamEvent Structure
```typescript
interface StreamEvent {
  type: string
  data: {
    message: string
    agent_role?: string
    tool_name?: string
    model?: string
    query?: string
    status?: string
    crew_name?: string
    execution_time?: number
    token_usage?: {
      total_tokens?: number
      prompt_tokens?: number
      completion_tokens?: number
    }
  }
  timestamp: string
  agent_id?: string
  task_id?: string
  session_id?: string
}
```

### Event Type Mapping
- `CREW_STARTED` → "🚀 Starting Research Crew..."
- `AGENT_STARTED` → "🤖 Expert Research Assistant is starting execution..."
- `TOOL_STARTED` → "🔍 Using SerperDevTool with query: 'search terms'"
- `LLM_STARTED` → "🧠 Calling gpt-4o-mini..."
- `TOOL_COMPLETED` → "✅ SerperDevTool completed in 2.34s"
- `AGENT_COMPLETED` → "✅ Expert Research Assistant completed execution"
- `CREW_COMPLETED` → "✅ Research Crew completed successfully"

## Configuration

### Environment Variables
No additional environment variables are required. The EventBus uses the existing CrewAI configuration.

### Customization
To add custom events or modify event handling:

1. **Add new event types** in `real_time_listener.py`
2. **Update frontend mapping** in `ChatInterface.tsx` 
3. **Extend ExecutionTracker** for custom display logic

## API Endpoints

### Enhanced Endpoints
- `GET /flow/status` - Returns session status including real-time event statistics
- `GET /flow/events` - Returns pending real-time events
- `POST /flow/reset` - Resets both flow and event listener sessions

### Event Stream Format
Events are streamed via SSE in the following format:
```
data: {"type": "CREW_STARTED", "data": {"message": "🚀 Starting Research Crew...", "crew_name": "Research Crew"}, "timestamp": "2024-12-19T10:30:00.000Z"}
```

## Testing

Run the test script to verify event listeners are working:
```bash
cd backend
python test_events.py
```

## Benefits

1. **Real-time Visibility** - Users see exactly what the AI is doing
2. **Better UX** - Similar to Perplexity's transparent approach
3. **Debugging** - Easier to identify issues in agent execution
4. **Performance Monitoring** - Track execution times and token usage
5. **Trust Building** - Users understand the AI's process

## Future Enhancements

- 📈 Performance analytics dashboard
- 🔍 Event filtering and search
- 📊 Execution metrics visualization
- 🔄 Event replay functionality
- 📱 Mobile-optimized event display

## Troubleshooting

### Common Issues

1. **Events not appearing**: Ensure listeners are imported in `main.py`
2. **Frontend not updating**: Check SSE connection and event mapping
3. **Performance issues**: Monitor event queue size and clear appropriately

### Debug Mode
Enable detailed logging by setting the `verbose=True` flag in crew configuration.

---

This implementation provides a comprehensive real-time monitoring solution for CrewAI workflows, enhancing user experience and system transparency. 
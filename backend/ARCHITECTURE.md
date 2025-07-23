# CrewAI Flow Architecture

Welcome to the architectural overview of the CrewAI Flow project! This document explains how the different parts of the system work together to create a smart, real-time chatbot experience.

## High-Level Overview

At its core, this project is a web application with a **Next.js frontend** and a **Python FastAPI backend**. The magic happens in the backend, where we intelligently decide how to answer a user's query.

The system can handle two types of requests:
1.  **Simple Chat**: For conversational questions, it gets a quick response from a Large Language Model (LLM).
2.  **In-depth Research**: For complex queries, it launches a team of AI agents (a "Crew") to research the topic, gather sources, and formulate a comprehensive answer.

This entire process is streamed to the user in real-time, so they can see the AI "thinking."

### Visual Flow

Here's a simple diagram of the process:

```
                  +----------------------+
 [User's Browser] |  Next.js Frontend    |
                  +----------------------+
                          | (User sends message)
                          v
                  +----------------------+
 [Python Server]  |   FastAPI Backend    |
                  +----------------------+
                          |
                          v
            +---------------------------+
            |   Intent Detection        |
            | (Is it a CHAT or SEARCH?) |
            +---------------------------+
                   |               |
(CHAT Intent)      |               | (SEARCH Intent)
         +---------+               +-----------+
         |                                     |
         v                                     v
+-------------------+                 +----------------------+
| Simple LLM Call   |                 | CrewAI Research Crew |
| (Quick Response)  |                 | (In-depth Research)  |
+-------------------+                 +----------------------+
         |                                     |
         +----------------+--------------------+
                          |
                          v
                  +----------------------+
                  |  Formatted Response  |
                  +----------------------+
                          | (Streamed back to user)
                          v
                  +----------------------+
 [User's Browser] |  Next.js Frontend    |
                  +----------------------+
```

---

## Component Breakdown

Let's look at the key pieces of the backend (`backend/src/chatbot/`) that make this work.

### 1. The Server: `ag_ui_server.py`

This file is the main entry point for the backend.

*   **What it does**: It creates a FastAPI web server that listens for messages from the frontend. It's responsible for receiving requests and sending back responses.
*   **Key Endpoint**: The `/agent` endpoint is the primary endpoint that the frontend talks to. It's set up to stream events, meaning it can send multiple small updates over a single connection instead of making the user wait for the final answer.
*   **For Advanced Users**: It uses `StreamingResponse` with the `text/event-stream` media type to achieve Server-Sent Events (SSE). This is an efficient way to push real-time data from the server to the client.

### 2. The Orchestrator: `AGUIFlowAdapter`

This class, found inside `ag_ui_server.py`, manages the entire process of handling a user's message.

*   **What it does**: When a message comes in, the adapter starts the process. It's responsible for running the core logic, listening for real-time updates from the AI, and sending those updates to the frontend. It also formats the final answer before sending it.
*   **For Advanced Users**: It uses `asyncio` to run the main message processing (`_run_flow_message`) in a non-blocking way. This allows it to simultaneously listen for events from the `real_time_listener` and stream them to the UI while the main logic is still executing.

### 3. The Brains: `ChatbotSession`

This class, also in `ag_ui_server.py`, decides *how* to handle the user's message.

*   **What it does**: This is where the core decision-making happens.
    1.  It first performs **Intent Detection** (`detect_intent`) to classify the message as "CHAT" or "SEARCH".
    2.  If it's a "CHAT" message, it gets a direct, conversational reply from an LLM (`generate_chat_reply`).
    3.  If it's a "SEARCH" message, it activates the powerful `ResearchCrew`.
*   **For Advanced Users**: It maintains the conversation state, including history and any research results, within its `self.state` object. This state is not persisted across server restarts but is maintained for a single user "session."

### 4. The Research Team: `ResearchCrew`

This is your CrewAI implementation, located in `backend/src/chatbot/crews/research_crew/`.

*   **What it does**: This is a team of specialized AI agents designed for research. When given a query, the crew works together to browse the web, read articles, extract key information, and compile a detailed report with sources.
*   **Key Files**:
    *   `research_crew.py`: Defines the crew, its agents, and the tasks they perform.
    *   `config/agents.yaml`: Defines the properties of each agent (e.g., their LLM, their role, their backstory).
    *   `config/tasks.yaml`: Defines the sequence of tasks the agents need to complete.
*   **For Advanced Users**: The crew is "kicked off" via `crew().kickoff()`. The `pydantic` output of the final task is used to ensure the data is returned in a structured, predictable format.

### 5. The Real-Time Announcer: `real_time_listener.py`

This is the secret sauce for the "Perplexity-like" real-time updates.

*   **What it does**: This module "listens" to everything the `ResearchCrew` does. It captures events like "Agent Started," "Tool Used," or "LLM Stream Chunk" (a piece of a sentence). The `AGUIFlowAdapter` then forwards these events to the UI.
*   **For Advanced Users**: This is implemented as a custom `AsyncEventHandler` for CrewAI. It hooks into the crew's execution lifecycle and stores events in a session-specific queue, which the main server process polls and streams to the client.

### 6. Helper Utilities: `utils/`

The utilities folder contains helper functions that support the main logic:

*   **`chat_helpers.py`**: Contains functions like `detect_intent()`, `generate_chat_reply()`, and `synthesise_research()`. These handle the core LLM interactions and decision-making logic.
*   **`prompts.py`**: Houses the prompts and instructions sent to the LLMs to guide their behavior.

---

## Data Flow Walkthrough

Let's trace what happens when a user sends a message:

### Step 1: Message Reception
1. User types a message in the frontend chat interface
2. Frontend sends POST request to `/agent` endpoint
3. `agent_endpoint()` function extracts the message and calls `adapter.process_message()`

### Step 2: Processing Setup
1. `AGUIFlowAdapter.process_message()` sends a "RUN_STARTED" event to the UI
2. Creates an async task to run the actual message processing
3. Starts monitoring for real-time events from the `real_time_listener`

### Step 3: Intent Classification
1. `ChatbotSession.process_message()` calls `detect_intent(user_message)`
2. An LLM analyzes the message and returns either "CHAT" or "SEARCH"

### Step 4a: Simple Chat Path (CHAT Intent)
1. Calls `generate_chat_reply()` with conversation history
2. LLM generates a conversational response
3. Response is added to conversation history
4. Returns formatted response

### Step 4b: Research Path (SEARCH Intent)
1. Creates and kicks off `ResearchCrew` with the user query
2. Crew agents execute their tasks (web search, analysis, compilation)
3. Real-time events are captured by `real_time_listener` during execution
4. Crew returns structured research results with sources
5. `synthesise_research()` creates a final polished answer
6. Research results are stored in session state

### Step 5: Response Streaming
1. `AGUIFlowAdapter` formats the response based on intent type
2. For research responses: formats content and extracts sources
3. Streams the final response as "TEXT_MESSAGE_DELTA" events
4. Sends sources as "SOURCES_UPDATE" events (if applicable)
5. Sends "RUN_FINISHED" event to signal completion

### Step 6: Frontend Display
1. Frontend receives and displays streamed events in real-time
2. Shows typing indicators, progress updates, and partial responses
3. Displays final formatted answer with sources and citations

---

## Key Technologies & Patterns

### Backend Technologies
- **FastAPI**: Modern, fast web framework for building APIs
- **CrewAI**: Multi-agent framework for coordinating AI agents
- **Pydantic**: Data validation and serialization
- **AsyncIO**: Asynchronous programming for concurrent operations

### Frontend Technologies
- **Next.js**: React framework for the web interface
- **Server-Sent Events (SSE)**: Real-time communication from server to client
- **TypeScript**: Type-safe JavaScript for better developer experience

### Architectural Patterns
- **Event-Driven Architecture**: Real-time events drive UI updates
- **Strategy Pattern**: Different handling strategies based on intent classification
- **Observer Pattern**: Real-time listener observes crew execution
- **Streaming Response**: Progressive loading of responses for better UX

---

## Benefits of This Architecture

### For Users
- **Real-time feedback**: See the AI working in real-time
- **Intelligent routing**: Get quick answers for simple questions, thorough research for complex ones
- **Source transparency**: See exactly where information comes from
- **Modern interface**: Clean, responsive design similar to popular AI assistants

### For Developers
- **Modular design**: Easy to extend with new agents, tools, or capabilities
- **Clear separation of concerns**: Frontend, orchestration, and AI logic are cleanly separated
- **Event-driven**: Easy to add new types of real-time updates
- **Type safety**: Pydantic models ensure data consistency between components

---

This architecture creates a system that is both powerful and efficient. It uses the full force of an AI agent crew only when necessary, while still providing quick, conversational responses for simpler interactions, all with a modern, real-time user experience. 
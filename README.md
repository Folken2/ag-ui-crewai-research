# AG-UI CrewAI Real-Time Research Assistant

A Perplexity-like AI research assistant built with **CrewAI**, **AG-UI Protocol**, and **Next.js**. Features real-time event streaming, web search capabilities, and a modern chat interface with source citations and images.



## Key Features

- **Real-time Research**: Web search with SerperDev integration
- **Live Event Streaming**: AG-UI protocol for real-time agent updates
- **Source Citations**: Perplexity-style source cards with images
- **Intent Detection**: Smart classification between search/chat/exit
- **Modern UI**: Clean Next.js frontend with Tailwind CSS

## Tech Stack

- **Agentic framework**: CrewAI
- **Protocol**: AG-UI for intelligent backend <-> frontend connection
- **Real-time web search**: EXA AI
- **LLM**: Gemini 2.0 Flash 

## Required API Keys

You'll need to obtain these API keys:

1. **SerperDev API Key** - For web search functionality
   - Sign up at [serper.dev](https://serper.dev)
   - Get your API key from the dashboard

2. **Google Gemini API Key** - For LLM responses
   - Go to [Google AI Studio](https://aistudio.google.com/)
   - Create a new API key
  
3. **EXA AI API Key** - For advanced web search
   - Go to [EXA AI](https://exa.ai/)
   - Create a new API key


### 1. Clone the Repository
```bash
git clone https://github.com/Folken2/ag-ui-crewai-research.git
cd crewai_flow
```

### 2. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create and activate virtual environment
python -m venv .venv

# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate

# Install the project
pip install -e
```

### 3. Frontend Setup

```bash
# Navigate to frontend directory (from project root)
cd frontend

# Install dependencies
npm install
```

## Running the Application

### Start the Backend Server
```bash
# From backend directory (with venv activated)
cd backend
python run_server.py
```

The backend will start on `http://localhost:8000`

### Start the Frontend (in a new terminal)
```bash
# From frontend directory
cd frontend
npm run dev
```

The frontend will start on `http://localhost:3000`

### Access the Application
Open your browser and go to `http://localhost:3000`


## Event Flow

1. **User Input** → Intent detection
2. **Search Intent** → Research crew activation  
3. **Real-time Events** → Live agent updates
4. **Results** → Formatted response with sources

## UI Features

- **Real-time streaming** with source cards and images
- **Perplexity-style layout** with domain extraction
- **Live agent status** and execution tracking


## Development

**Adding Tools**: Create in `backend/src/chatbot/tools/` and register in research crew  
**Customizing Events**: Modify `real_time_listener.py` and update frontend handlers  


## Adding More Crews

### Create a New Crew
```bash
# Create crew directory structure
mkdir -p backend/src/chatbot/crews/analysis_crew/config
```

### Example Crew Structure
```
analysis_crew/
├── config/
│   ├── agents.yaml      # Agent configurations
│   └── tasks.yaml       # Task definitions
└── analysis_crew.py     # Main crew class
```

### Register in Main Flow
```python
# In ag_ui_server.py
from .crews.analysis_crew.analysis_crew import AnalysisCrew

# Add to intent detection
if intent == "ANALYSIS":
    result = AnalysisCrew().crew().kickoff(inputs={"data": user_message})
```

### Crew Examples you can add
- **Research Crew**: Web search and information gathering
- **Analysis Crew**: Data analysis and insights
- **Writing Crew**: Content creation and summarization
- **Code Crew**: Programming and technical tasks

## 📄 License

MIT License




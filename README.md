# AG-UI CrewAI Real-Time Research Assistant

A Perplexity-like AI research assistant built with **CrewAI**, **AG-UI Protocol**, and **Next.js**. Features real-time event streaming, web search capabilities, and a modern chat interface with source citations and images.

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![Next.js](https://img.shields.io/badge/Next.js-15.3.4-black)
![CrewAI](https://img.shields.io/badge/CrewAI-0.134+-orange)

## 🚀 Key Features

- **Real-time Research**: Web search with SerperDev integration
- **Live Event Streaming**: AG-UI protocol for real-time agent updates
- **Source Citations**: Perplexity-style source cards with images
- **Intent Detection**: Smart classification between search/chat/exit
- **Modern UI**: Clean Next.js frontend with Tailwind CSS

## 🛠️ Tech Stack

**Backend**: Python 3.10+, FastAPI, CrewAI 0.134+, AG-UI Protocol, SerperDev, LiteLLM, Gemini  
**Frontend**: Next.js 15.3.4, React 19, TypeScript, Tailwind CSS, React Markdown, Server-Sent Events

## 📦 Quick Start

**Prerequisites**: Python 3.10+, Node.js 18+, SerperDev API key, Gemini API key

```bash
# Backend
cd backend
pip install -e .
echo "SERPER_API_KEY=your_key" > .env
echo "GEMINI_API_KEY=your_gemini_key" >> .env
python -m chat.ag_ui_server

# Frontend (new terminal)
cd frontend
npm install
npm run dev
# Open http://localhost:3000
```

## 🔄 Event Flow

1. **User Input** → Intent detection
2. **Search Intent** → Research crew activation  
3. **Real-time Events** → Live agent updates
4. **Results** → Formatted response with sources

## 🎨 UI Features

- **Real-time streaming** with source cards and images
- **Perplexity-style layout** with domain extraction
- **Live agent status** and execution tracking


## 🔧 Development

**Adding Tools**: Create in `backend/src/chatbot/tools/` and register in research crew  
**Customizing Events**: Modify `real_time_listener.py` and update frontend handlers  


## 🚀 Adding More Crews

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




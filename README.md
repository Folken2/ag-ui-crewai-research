# AG-UI CrewAI Real-Time Research Assistant

A Perplexity-like AI research assistant built with **CrewAI**, **AG-UI Protocol**, and **Next.js**. Features real-time event streaming, web search capabilities, and a modern chat interface with source citations and images.

## Key Features

- **Real-time Research**: Web search with EXA AI and SerperDev integration
- **Live Event Streaming**: AG-UI protocol for real-time agent updates
- **Source Citations**: Perplexity-style source cards with images
- **Intent Detection**: Smart classification between search/chat/exit
- **Modern UI**: Clean Next.js frontend with Tailwind CSS
- **JWT Authentication**: Secure token-based authentication system
- **Open Frontend**: No user login required - automatic token management

## Tech Stack

- **Agentic framework**: CrewAI
- **Protocol**: AG-UI for intelligent backend <-> frontend connection
- **Real-time web search**: EXA AI + SerperDev
- **LLM**: OpenRouter (via LiteLLM) - supports multiple models
- **Authentication**: JWT tokens with bcrypt password hashing
- **Frontend**: Next.js with automatic token management
- **Backend**: FastAPI with protected endpoints 

## Required API Keys

You'll need to obtain these API keys:

1. **OpenRouter API Key** - For LLM responses (supports multiple models)
   - Sign up at [OpenRouter](https://openrouter.ai/)
   - Get your API key from the dashboard

2. **EXA AI API Key** - For advanced web search
   - Go to [EXA AI](https://exa.ai/)
   - Create a new API key

3. **SerperDev API Key** - For Google search functionality
   - Sign up at [serper.dev](https://serper.dev)
   - Get your API key from the dashboard


## Local Development Setup

### 1. Clone the Repository
```bash
git clone https://github.com/Folken2/ag-ui-crewai-research.git
cd ag-ui-crewai-research
```

### 2. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create and activate virtual environment
python -m venv venv

# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Environment Configuration

Create environment files for both backend and frontend:

**Backend Environment** (`backend/.env`):
```bash
# Copy the example file
cp example.env .env

# Edit .env with your API keys
OPENROUTER_API_KEY=your-openrouter-api-key-here
OPENROUTER_MODEL=google/gemini-2.5-flash
EXA_API_KEY=your-exa-api-key-here
SERPER_API_KEY=your-serper-api-key-here

# Authentication (optional - uses defaults if not set)
SECRET_KEY=your-secret-key-for-jwt
ADMIN_USERNAME=admin
ADMIN_PASSWORD_HASH=your-admin-password
```

**Frontend Environment** (`frontend/.env.local`):
```bash
# Copy the example file
cp example.env.local .env.local

# Edit .env.local with your backend URL
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
```

### 4. Frontend Setup

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
source venv/bin/activate  # On Windows: venv\Scripts\activate
python run_server.py
```

The backend will start on `http://localhost:8000`

**Note**: The backend includes JWT authentication. The frontend will automatically get tokens using default credentials (`admin`/`secret`).

### Start the Frontend (in a new terminal)
```bash
# From frontend directory
cd frontend
npm run dev
```

The frontend will start on `http://localhost:3000`

### Access the Application
Open your browser and go to `http://localhost:3000`

## How It Works

### Authentication Flow
1. **Frontend starts** → Automatically requests JWT token from backend
2. **Backend validates** → Returns permanent token (no expiration)
3. **All requests** → Include `Authorization: Bearer <token>` header
4. **Backend protects** → All endpoints require valid JWT token

### Research Flow
1. **User Input** → Intent detection via OpenRouter LLM
2. **Search Intent** → Research crew activation with EXA/SerperDev
3. **Real-time Events** → Live agent updates via AG-UI protocol
4. **Results** → Formatted response with sources and images

### UI Features
- **Real-time streaming** with source cards and images
- **Perplexity-style layout** with domain extraction
- **Live agent status** and execution tracking
- **Automatic authentication** - no user interaction needed


## Development

### Available Models
You can change the LLM model by updating `OPENROUTER_MODEL` in your `.env` file:

See all available models at [OpenRouter Models](https://openrouter.ai/models)

### Development Tips
- **Adding Tools**: Create in `backend/src/chatbot/tools/` and register in research crew  
- **Customizing Events**: Modify `real_time_listener.py` and update frontend handlers
- **Authentication**: Default credentials are `admin`/`secret` - change in `.env` for production
- **API Keys**: All sensitive keys are managed via environment variables
- **Generate Secrets**: Use `python generate_secret.py` to create secure JWT secret keys
- **Production Setup**: Use `python generate_example_credentials.py` for deployment credentials  


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
- **Research Crew**: Web search and information gathering (already included)
- **Analysis Crew**: Data analysis and insights
- **Writing Crew**: Content creation and summarization
- **Code Crew**: Programming and technical tasks
- **Translation Crew**: Multi-language translation
- **Summarization Crew**: Document and text summarization

## Troubleshooting

### Common Issues

**Backend won't start:**
- Check if all API keys are set in `.env`
- Ensure virtual environment is activated
- Verify Python version compatibility (3.10-3.12 recommended)

**Frontend stuck on "Initializing...":**
- Verify `NEXT_PUBLIC_BACKEND_URL` points to running backend
- Check browser console for errors
- Ensure backend is running on the correct port

**Authentication errors:**
- Default credentials are `admin`/`secret`
- Check if `SECRET_KEY` is set in backend `.env`
- Verify JWT token is being sent in requests

**API key errors:**
- Verify all required API keys are set
- Check OpenRouter account has sufficient credits
- Ensure EXA and SerperDev API keys are valid

## 📄 License

MIT License




# Perplexity-like Search Chatbot

A CrewAI-powered search assistant that provides up-to-date information with follow-up question capabilities, similar to Perplexity AI.

## Features

🔍 **Real-time Web Search** - Get current information from the web
💬 **Follow-up Questions** - Ask related questions with maintained context  
🤖 **AI-Powered Analysis** - Intelligent synthesis of search results
📊 **Source Citations** - Transparent source references
🔄 **Conversation Loops** - Continuous search sessions
📈 **Search History** - Track your research journey

## Prerequisites

- Python 3.10+ (and <3.14)
- Groq API key
- Serper API key (for web search)

## Setup

### 1. Install Dependencies

```powershell
# Install UV package manager (if not already installed)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Install project dependencies
crewai install
```

### 2. Environment Variables

Create a `.env` file in the project root with your API keys:

```env
# Groq API Key (required)
GROQ_API_KEY=your_groq_api_key_here

# Serper API Key (required for web search)
# Get your free API key at: https://serper.dev/
SERPER_API_KEY=your_serper_api_key_here
```

**Getting API Keys:**

1. **Groq API Key**: 
   - Visit [Groq Console](https://console.groq.com/)
   - Create an account and generate an API key
   - Groq offers fast inference with Llama models

2. **Serper API Key**:
   - Visit [Serper.dev](https://serper.dev/)
   - Sign up for a free account (includes 2,500 free searches)
   - Copy your API key

### 3. Run the Search Assistant

```powershell
# Start the interactive search session
crewai run

# Or run directly with Python
python src/chatbot/main.py
```

## How It Works

### Flow Architecture

```
Start → Get User Query → Search Web → Analyze Results → Present Answer → Ask Follow-up?
  ↑                                                                            ↓
  └──────────────────────── Continue with Context ←─────────────────────────┘
```

### Example Interaction

```
🔍 Welcome to your AI-powered search assistant!
Ask me anything and I'll search for the latest information.

🤔 What would you like to search for? What are the latest developments in AI in 2024?

🔍 Searching for: 'What are the latest developments in AI in 2024?'...
🤖 Researching and analyzing information...

================================================================================
📊 SEARCH RESULTS
================================================================================
Based on my search of current information, here are the key AI developments in 2024:

**Major Breakthroughs:**
- Groq's Llama 3.1 70B with fast inference capabilities
- Google's Gemini Ultra achieving human-level performance on MMLU
- Meta's Code Llama for advanced programming assistance
- Anthropic's Claude 3 with enhanced reasoning abilities

**Key Trends:**
- Integration of AI into enterprise workflows
- Advances in AI safety and alignment research
- Multimodal AI becoming mainstream
- Open-source AI models gaining prominence

**Sources:**
- TechCrunch: "AI Trends 2024" (https://techcrunch.com/...)
- Nature: "AI Research Advances" (https://nature.com/...)
- MIT Technology Review (https://technologyreview.com/...)

💡 Search #1 completed!

🤔 Any follow-up questions? (or 'exit' to quit): Tell me more about AI safety developments

🔍 Searching for follow-up: 'Tell me more about AI safety developments'...
```

## Project Structure

```
chatbot/
├── src/chatbot/
│   ├── main.py              # Main search flow implementation
│   ├── crews/               # Research crew configurations  
│   └── tools/               # Custom tools
├── pyproject.toml           # Dependencies and configuration
├── .env                     # API keys (create this file)
└── README.md               # This file
```

## Key Components

### SearchState
Manages conversation state including:
- Search history and context
- Current queries and results  
- Message threads
- Search counters

### PerplexitySearchFlow
Main flow class with:
- `start_flow()`: Initialize the session
- `chat_and_search()`: Handle queries and search
- `continue_search()`: Process follow-ups with context
- `end_flow()`: Clean session termination

### Research Agent
Specialized AI agent that:
- Uses SerperDevTool for web search
- Analyzes and synthesizes results
- Provides sourced, factual responses
- Maintains conversation context

## Customization

### Change Search Behavior
Modify the agent configuration in `chat_and_search()`:

```python
search_agent = Agent(
    role="Expert Research Assistant",
    goal="Your custom goal here",
    backstory="Your custom backstory",
    tools=[search_tool],
    llm=llm,
    temperature=0.3,  # Adjust for creativity vs factuality
)
```

### Add More Tools
Extend functionality by adding tools:

```python
from crewai_tools import (
    SerperDevTool, 
    ScrapeWebsiteTool,
    YoutubeChannelSearchTool
)

tools = [SerperDevTool(), ScrapeWebsiteTool(), YoutubeChannelSearchTool()]
```

## Troubleshooting

**Common Issues:**

1. **Missing API Keys**: Ensure both GROQ_API_KEY and SERPER_API_KEY are set in `.env`
2. **Import Errors**: Run `crewai install` to install dependencies
3. **Search Failures**: Check your Serper API key and quota
4. **Slow Responses**: Normal for comprehensive search and analysis

## License

This project is open source. Feel free to modify and extend it for your needs.

## Contributing

Contributions welcome! Areas for improvement:
- Advanced search filters
- Multiple search engine support  
- Export conversation history
- Web interface
- Voice input/output

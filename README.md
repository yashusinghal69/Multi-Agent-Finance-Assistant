# 🤖 Multi-Agent Finance Assistant

A voice-enabled financial analysis system that combines multiple AI agents to deliver comprehensive market insights through spoken interaction.

## 🌟 Features

### Core Capabilities

- **🎤 Voice Input**: Speech-to-text using Groq's Whisper API
- **🔊 Voice Output**: Text-to-speech using ElevenLabs API
- **📊 Real-time Market Data**: Yahoo Finance integration for live stock prices and market data
- **📰 Financial News**: Tavily Search API for latest financial news and earnings
- **📄 Document Upload**: RAG system supporting PDF, TXT, CSV files
- **🤖 Multi-Agent Orchestration**: Intelligent routing using LangGraph

## 🚀 Setup

### Prerequisites

- Python 3.8+

### Installation

1. **Clone and setup:**

```bash
git clone <repository-url>
cd "Multi Agent Finance Assistant"
```



```bash
git clone <repository-url>
cd "Multi Agent Finance Assistant"
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements.txt
```



2. **Install dependencies:**

```bash
pip install -r requirements.txt
```

3. **Configure API keys:**
   Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key_here
TAVILY_API_KEY=your_tavily_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
MURF_API_KEY=your_murf_api_key_here
```

4. **Run the application:**

```bash
streamlit run app/main.py
```

## 🔑 API Keys Required

- **Groq**: Speech processing - [console.groq.com](https://console.groq.com/)
- **Tavily**: Financial news - [tavily.com](https://tavily.com/)
- **OpenAI**: AI orchestration - [platform.openai.com](https://platform.openai.com/)
- **Murf**: Text-to-speech - [murf.ai](https://murf.ai/)


## 📁 Project Structure

```
├── app/
│   ├── main.py                 # Main Streamlit application
│   └── agents/
│       ├── voice_agent.py      # Speech-to-text (Groq Whisper)
│       ├── api_agent.py        # Market data (Yahoo Finance)
│       ├── scraping_agent.py   # News search (Tavily)
│       ├── rag_agent.py        # Document processing
│       ├── tts_agent.py        # Text-to-speech (ElevenLabs)
│       └── orchestrator.py     # LangGraph workflow
├── requirements.txt            # Python dependencies
├── .env.example               # Environment template
├── sample_*.md               # Sample documents for testing
├── sample_portfolio.csv      # Sample portfolio data
└── README.md                 # This file
```

## 🔧 Technical Details

### Dependencies

- **Streamlit**: Web interface
- **LangChain**: Agent framework and document processing
- **LangGraph**: Workflow orchestration
- **Groq**: Speech-to-text API
- **ElevenLabs**: Text-to-speech API
- **Tavily**: Search API for financial news
- **YFinance**: Market data
- **FAISS**: Vector database for RAG
- **Sentence Transformers**: Text embeddings

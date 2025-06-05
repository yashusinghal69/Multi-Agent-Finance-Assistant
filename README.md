# 🤖 Multi-Agent Finance Assistant

A sophisticated voice-enabled financial analysis system that combines multiple AI agents to deliver comprehensive market insights through spoken interaction.

## 🌟 Features

### Core Capabilities

- **🎤 Voice Input**: Speech-to-text using Groq's Whisper API
- **🔊 Voice Output**: Text-to-speech using ElevenLabs API
- **📊 Real-time Market Data**: Yahoo Finance integration for live stock prices and market data
- **📰 Financial News**: Tavily Search API for latest financial news and earnings
- **📄 Document Upload**: RAG system supporting PDF, TXT, CSV files
- **🤖 Multi-Agent Orchestration**: Intelligent routing using LangGraph

### Agent Architecture

1. **Voice Agent**: Groq Whisper for speech-to-text conversion
2. **API Agent**: Yahoo Finance for real-time market data
3. **Scraping Agent**: Tavily Search for news and sentiment analysis
4. **RAG Agent**: Document processing and context retrieval
5. **TTS Agent**: ElevenLabs for speech synthesis
6. **Orchestrator**: LangGraph workflow management

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Virtual environment (recommended)
- Required API keys (see setup below)

### Installation

1. **Clone and setup environment:**

```bash
git clone <repository-url>
cd "Multi Agent Finance Assistant"
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

2. **Configure API keys:**
   Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key_here
TAVILY_API_KEY=your_tavily_api_key_here
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here
```

3. **Run the application:**

```bash
streamlit run app/main.py
```

The app will open at `http://localhost:8501`

## 🔑 API Keys Setup

### Required APIs

1. **Groq API** (Speech-to-text)

   - Sign up at: https://console.groq.com/
   - Free tier available

2. **Tavily Search API** (Financial news)

   - Sign up at: https://tavily.com/
   - Free tier: 1000 searches/month

3. **ElevenLabs API** (Text-to-speech)
   - Sign up at: https://elevenlabs.io/
   - Free tier: 10k characters/month

## 📖 Usage Guide

### Basic Workflow

1. **Voice Input**: Click microphone or upload audio file
2. **Transcription**: Review and edit the transcribed text
3. **Processing**: Click "Process Query" to engage AI agents
4. **Results**: View comprehensive analysis
5. **Voice Output**: Enable TTS for spoken responses

### Example Queries

```
"What's Apple's stock performance today?"
"Show me latest tech earnings news"
"Analyze my portfolio risk" (with uploaded CSV)
"What's the market sentiment on Tesla?"
"How are Asian markets performing?"
```

### Document Upload

- **PDFs**: Research reports, financial statements
- **Text Files**: Market analysis, news articles
- **CSV Files**: Portfolio data, stock lists
- The RAG system will use uploaded documents to enhance responses

### Voice Settings

- Enable TTS in the sidebar
- Choose from multiple voice options (Rachel, Josh, Bella, Antoni)
- Audio responses auto-play after processing

## 🧪 Testing the System

### 1. Test Voice Input

```bash
# Use the built-in microphone or upload sample audio files
# Test with queries like "What is Apple stock price?"
```

### 2. Test with Sample Documents

Upload the provided sample files:

- `sample_apple_research.md` - Apple financial analysis
- `sample_tesla_research.md` - Tesla company research
- `sample_portfolio.csv` - Sample investment portfolio

### 3. Test Different Query Types

**Market Data Queries:**

- "What's the current price of Microsoft?"
- "Show me tech sector performance"
- "Analyze portfolio risk for my holdings"

**News and Sentiment:**

- "Latest earnings news for Apple"
- "Market sentiment on electric vehicle stocks"
- "Recent developments in AI sector"

**Combined Analysis:**

- "How is Tesla performing and what's the recent news?"
- "Give me Apple's price and latest earnings information"

### 4. Test RAG Enhancement

1. Upload sample documents
2. Ask: "Based on my research, what's your view on Apple?"
3. The system should incorporate uploaded document content

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

### Agent Workflow

1. **Router**: Analyzes query and decides which agents to use
2. **Conditional Routing**: API_AGENT, SCRAPING_AGENT, or BOTH
3. **Parallel Processing**: Multiple agents can work simultaneously
4. **Synthesis**: Combines results into coherent response
5. **Output**: Text response + optional TTS audio

## 🛠️ Troubleshooting

### Common Issues

**Import Errors:**

```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

**API Key Issues:**

- Verify `.env` file exists and contains valid keys
- Check API key permissions and rate limits
- Ensure no extra spaces in key values

**Audio Issues:**

- Check browser microphone permissions
- Try uploading audio files instead of recording
- Supported formats: WAV, MP3, M4A

**Performance Issues:**

- Large documents may take time to process
- Consider reducing document size or splitting into chunks
- Check internet connection for API calls
 
import os
import re
from typing import Dict, Any, List
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from typing_extensions import Annotated, TypedDict
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Import agent tools
from .api_agent import market_data_tool
from .scraping_agent import news_search_tool, earnings_search_tool, sentiment_analysis_tool, url_extract_tool

# Removed clean_response_text function - formatting now handled by LLM

def check_response_relevancy(query: str, response: str) -> bool:
    """
    Check if API response is relevant to the query
    """
    if not response or len(response.strip()) < 10:
        return False
    
    # Check for error indicators
    error_indicators = ["error", "not found", "no data", "unavailable", "failed"]
    if any(indicator in response.lower() for indicator in error_indicators):
        return False
    
    # Check for financial relevance in query
    query_lower = query.lower()
    financial_terms = ["stock", "price", "market", "earnings", "revenue", "cap", "trading"]
    
    if any(term in query_lower for term in financial_terms):
        # For financial queries, check if response contains financial data
        financial_indicators = ["$", "%", "trading", "market cap", "revenue", "earnings", "shares"]
        return any(indicator in response.lower() for indicator in financial_indicators)
    
    return True

class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    query: str
    context: str  # RAG context
    agent_decision: str
    api_results: str
    scraping_results: str
    rag_results: str
    general_results: str
    final_response: str
    needs_fallback: bool  # For self-correcting workflow
    attempt_count: int    # Track retry attempts

def initialize_llm():
    """Initialize OpenAI LLM with brief response settings and formatting instructions"""
    openai_api_key = os.getenv('OPENAI_API_KEY')
    if not openai_api_key:
        raise ValueError("OPENAI_API_KEY not found in environment variables")
    
    return ChatOpenAI(
        openai_api_key=openai_api_key,
        model_name="gpt-4o-mini",
        temperature=0,
        max_tokens=800,  # Limit response length
        frequency_penalty=0.1,  # Reduce repetition
        presence_penalty=0.1    # Encourage diverse vocabulary
    )

def router_agent(state: AgentState) -> AgentState:
    """
    Enhanced router with document-aware routing
    """
    llm = initialize_llm()
    
    query = state["query"]
    context = state.get("context", "")
    has_context = bool(context and len(context.strip()) > 20)
    
    routing_prompt = f"""
    You are a smart routing agent. Current date: {datetime.now().strftime("%Y-%m-%d")}
    
    Query: "{query}"
    Document Context Available: {"YES" if has_context else "NO"}
    
    RULES:
    1. If query asks about uploaded documents/files AND context available → RAG_ONLY
    2. If query needs current prices/market data → API_AGENT  
    3. If query needs recent news/earnings → SCRAPING_AGENT
    4. If query needs both market data + news → BOTH
    5. If context available but query is about live markets → ignore docs, use API/SCRAPING
    6. If query is general conversation (greetings, general questions, non-finance) → GENERAL_CHAT
    
    Respond ONLY: RAG_ONLY, API_AGENT, SCRAPING_AGENT, BOTH, or GENERAL_CHAT
    
    Examples:
    - "Hello", "Hi", "How are you?" → GENERAL_CHAT
    - "What's in this report?" (with docs) → RAG_ONLY
    - "Apple stock price today?" → API_AGENT
    - "Tesla latest news?" → SCRAPING_AGENT
    - "NVDA price and recent news?" → BOTH
    - "What is AI?" → GENERAL_CHAT
    - "Tell me a joke" → GENERAL_CHAT
    """
    
    messages = [SystemMessage(content=routing_prompt)]
    response = llm.invoke(messages)
    
    agent_decision = response.content.strip().upper()
    
    # Fallback logic
    if agent_decision not in ["API_AGENT", "SCRAPING_AGENT", "BOTH", "RAG_ONLY", "GENERAL_CHAT"]:
        if has_context and any(word in query.lower() for word in ["document", "report", "file", "this", "uploaded"]):
            agent_decision = "RAG_ONLY"
        elif any(word in query.lower() for word in ["price", "stock", "market", "trading", "portfolio", "earnings", "financial"]):
            agent_decision = "API_AGENT"
        else:
            agent_decision = "GENERAL_CHAT"
    
    state["agent_decision"] = agent_decision
    state["messages"].append(HumanMessage(content=f"Route: {agent_decision}"))
    
    return state

def rag_agent_node(state: AgentState) -> AgentState:
    """
    RAG Agent for document-based queries
    """
    llm = initialize_llm()
    
    query = state["query"]
    context = state.get("context", "")
    
    if not context:
        state["rag_results"] = "No document context available."
        return state
    
    rag_prompt = f"""
    Answer the question based ONLY on the provided document context. Be concise and factual.
    
    Question: {query}
    
    Document Context: {context}
    
    Provide a brief, direct answer in 2-3 sentences. If the context doesn't contain the answer, say "The uploaded document doesn't contain information about this topic."
    """
    
    messages = [SystemMessage(content=rag_prompt)]
    response = llm.invoke(messages)
    
    state["rag_results"] = response.content
    state["messages"].append(HumanMessage(content=f"RAG Response: {response.content}"))
    
    return state

def api_agent_node(state: AgentState) -> AgentState:
    """
    API Agent with relevancy checking and fallback logic
    """
    llm = initialize_llm()
    
    query = state["query"]
    current_date = datetime.now().strftime("%Y-%m-%d")
    
    try:
        # Get market data
        api_results = market_data_tool(query)
        
        # Check if we got valid data
        if not api_results or "error" in api_results.lower():
            state["needs_fallback"] = True
            state["api_results"] = "API data unavailable"
            return state
          # Generate response with better formatting
        analysis_prompt = f"""
        Provide market analysis based on this data. Current date: {current_date}
        
        Market Data: {api_results}
        Query: {query}
        
        Keep response to 2-3 sentences. If no relevant data found, say "Current market data for [company] is not available."
        """
        
        messages = [SystemMessage(content=analysis_prompt)]
        response = llm.invoke(messages)
        
        # Check relevancy
        if check_response_relevancy(query, response.content):
            state["api_results"] = response.content
            state["needs_fallback"] = False
        else:
            state["needs_fallback"] = True
            state["api_results"] = "API response not relevant"
        
    except Exception as e:
        state["needs_fallback"] = True
        state["api_results"] = f"API error: {str(e)}"
    
    state["messages"].append(HumanMessage(content=f"API Response: {state['api_results']}"))
    return state

def scraping_agent_node(state: AgentState) -> AgentState:
    """
    Scraping Agent with concise news summaries
    """
    llm = initialize_llm()
    
    query = state["query"]
    current_date = datetime.now().strftime("%Y-%m-%d")
      # Get news data
    query_lower = query.lower()
    scraping_results = []
    
    if "news" in query_lower or "latest" in query_lower or not any(word in query_lower for word in ["earnings", "sentiment"]):
        news_results = news_search_tool(query)
        scraping_results.append(news_results)
    
    if "earnings" in query_lower or "results" in query_lower:
        earnings_results = earnings_search_tool(query)
        scraping_results.append(earnings_results)
    
    if "sentiment" in query_lower:
        sentiment_results = sentiment_analysis_tool(query)
        scraping_results.append(sentiment_results)
    
    combined_results = "\n\n".join(scraping_results)
    
    analysis_prompt = f"""
    Summarize the latest financial news/information BRIEFLY. Current date: {current_date}
    
    News Data: {combined_results}
    Query: {query}
    
    Rules:
    - Reference current date ({current_date})
    - Highlight only the most important recent developments
    - Keep to 2-3 sentences maximum
    - Include specific dates if available
    """
    
    messages = [SystemMessage(content=analysis_prompt)]
    response = llm.invoke(messages)
    
    state["scraping_results"] = response.content
    state["messages"].append(HumanMessage(content=f"News Response: {response.content}"))
    
    return state

def general_chat_agent_node(state: AgentState) -> AgentState:
    """
    General Chat Agent for non-finance queries
    """
    llm = initialize_llm()
    
    query = state["query"]
    current_date = datetime.now().strftime("%Y-%m-%d")
    
    general_prompt = f"""
    You are a helpful AI assistant. Today's date is {current_date}.
    
    Query: {query}
    
    Provide a friendly, helpful response. Keep it conversational and concise (2-3 sentences).
    If it's a greeting, respond warmly. If it's a general question, provide a brief but informative answer.    """
    
    messages = [SystemMessage(content=general_prompt)]
    response = llm.invoke(messages)
    
    state["general_results"] = response.content
    state["messages"].append(HumanMessage(content=f"General Response: {response.content}"))
    
    return state

def formatting_agent(state: AgentState) -> AgentState:
    """
    Final formatting agent to ensure proper text formatting using LLM
    """
    llm = initialize_llm()
    
    final_response = state.get("final_response", "")
    
    if not final_response or len(final_response.strip()) < 5:
        return state
    
    formatting_prompt = f"""
    You are a text formatting specialist. Fix any formatting issues in this financial response:
    
    Original Text: {final_response}
    
    FORMATTING RULES:
    1. Ensure proper spacing between words and numbers
    2. Add proper currency symbols ($) where needed for prices
    3. Format percentages correctly (e.g., "3.4%" not "3.4")
    4. Fix any concatenated words (e.g., "stockis" → "stock is")
    5. Ensure proper punctuation spacing
    6. Keep the same meaning and content
    7. Make it read naturally and professionally
    
    Examples of fixes:
    - "202.82,reflectingaslightdecrease" → "$202.82, reflecting a slight decrease"
    - "Applestockistrading" → "Apple stock is trading"
    - "down3.78" → "down 3.78%"
    
    Return ONLY the corrected, well-formatted text without any additional commentary.
    """
    
    messages = [SystemMessage(content=formatting_prompt)]
    response = llm.invoke(messages)
    
    # Update the final response with formatted version
    state["final_response"] = response.content.strip()
    
    return state

def synthesizer_agent(state: AgentState) -> AgentState:
    """
    Synthesize results with fallback handling
    """
    llm = initialize_llm()
    
    query = state["query"]
    agent_decision = state["agent_decision"]
    api_results = state.get("api_results", "")
    scraping_results = state.get("scraping_results", "")
    rag_results = state.get("rag_results", "")
    general_results = state.get("general_results", "")
    needs_fallback = state.get("needs_fallback", False)
    current_date = datetime.now().strftime("%Y-%m-%d")
    
    # Handle different scenarios
    if agent_decision == "RAG_ONLY":
        final_content = rag_results
    elif agent_decision == "GENERAL_CHAT":
        final_content = general_results
    elif agent_decision == "API_AGENT":
        if needs_fallback and scraping_results:
            # API failed, use scraping instead
            final_content = f"Based on web search: {scraping_results}"
        elif "not available" in api_results.lower() or "error" in api_results.lower():
            final_content = f"I'm sorry, but current market data for your query is not available. Please try asking about a specific stock symbol or check back later."
        else:
            final_content = api_results
    elif agent_decision == "SCRAPING_AGENT":
        final_content = scraping_results
    else:  # BOTH
        # Combine available results
        available_results = []
        if api_results and not needs_fallback:
            available_results.append(f"Market Data: {api_results}")
        if scraping_results:
            available_results.append(f"Recent News: {scraping_results}")
        if available_results:
            combined = " ".join(available_results)
            synthesis_prompt = f"""
            Combine this information into a brief response for: {query}
            
            Information: {combined}
            
            Create a natural response (2-3 sentences max).
            """
            
            messages = [SystemMessage(content=synthesis_prompt)]
            response = llm.invoke(messages)
            final_content = response.content
        else:
            final_content = "I'm sorry, I couldn't find relevant information for your query. Please try rephrasing or asking about a specific company or topic."
    
    state["final_response"] = final_content
    state["messages"].append(HumanMessage(content=f"Final: {final_content}"))
    
    return state

def create_agent_workflow():
    """
    Create self-correcting LangGraph workflow with fallback logic
    """
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("router", router_agent)
    workflow.add_node("rag_agent", rag_agent_node)
    workflow.add_node("api_agent", api_agent_node)
    workflow.add_node("scraping_agent", scraping_agent_node)
    workflow.add_node("general_chat_agent", general_chat_agent_node)
    workflow.add_node("synthesizer", synthesizer_agent)
    workflow.add_node("formatter", formatting_agent)
    
    # Set entry point
    workflow.set_entry_point("router")
    
    # Enhanced routing logic
    def route_decision(state: AgentState):
        decision = state["agent_decision"]
        if decision == "RAG_ONLY":
            return "rag_only"
        elif decision == "API_AGENT":
            return "api_only"
        elif decision == "SCRAPING_AGENT":
            return "scraping_only"
        elif decision == "GENERAL_CHAT":
            return "general_chat"
        else:  # BOTH
            return "both"
    
    workflow.add_conditional_edges(
        "router",
        route_decision,
        {
            "rag_only": "rag_agent",
            "api_only": "api_agent",
            "scraping_only": "scraping_agent",
            "general_chat": "general_chat_agent",
            "both": "api_agent"
        }
    )    
    # RAG and General chat go directly to synthesizer
    workflow.add_edge("rag_agent", "synthesizer")
    workflow.add_edge("general_chat_agent", "synthesizer")
    
    # API agent with fallback logic
    def after_api(state: AgentState):
        # If API failed and we need fallback, try scraping
        if state.get("needs_fallback", False) and state.get("attempt_count", 0) < 1:
            return "scraping_agent"  # Fallback to web search
        elif state["agent_decision"] == "BOTH":
            return "scraping_agent"
        else:
            return "synthesizer"
    
    workflow.add_conditional_edges(
        "api_agent",
        after_api,
        {
            "scraping_agent": "scraping_agent",
            "synthesizer": "synthesizer"
        }
    )    
    # Scraping to synthesizer
    workflow.add_edge("scraping_agent", "synthesizer")
    
    # Synthesizer to formatter for final text cleanup
    workflow.add_edge("synthesizer", "formatter")
    
    # End at formatter
    workflow.add_edge("formatter", END)
    
    return workflow.compile()

def process_query(query: str, context: str = "") -> str:
    """
    Process financial query with enhanced routing and brief responses
    """
    try:
        # Check OpenAI API key
        openai_api_key = os.getenv('OPENAI_API_KEY')
        if not openai_api_key or openai_api_key == "your_openai_api_key_here":
            return f"""⚠️ **OpenAI API Key Required**
            
Set OPENAI_API_KEY in .env file for intelligent routing.
Query: "{query}"
            
Without OpenAI, you can still use individual tools but won't get smart orchestration."""
        
        app = create_agent_workflow()
        initial_state = {
            "messages": [],
            "query": query,
            "context": context,
            "agent_decision": "",
            "api_results": "",
            "scraping_results": "",
            "rag_results": "",
            "general_results": "",
            "final_response": "",
            "needs_fallback": False,
            "attempt_count": 0
        }
        
        # Run workflow
        result = app.invoke(initial_state)
        return result["final_response"]
        
    except Exception as e:
        error_msg = str(e)
        if "rate_limit_exceeded" in error_msg:
            return f"⚠️ **Rate Limit**: Query too large. Try breaking it into smaller parts."
        else:
            return f"❌ **Error**: {error_msg}\n\nCheck your API keys and try again."

import os
from typing import Dict, List, Any
from langchain_tavily import TavilySearch, TavilyExtract
from langchain_openai import ChatOpenAI
from langchain.agents import create_openai_tools_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import HumanMessage, SystemMessage
from datetime import datetime
import streamlit as st
from dotenv import load_dotenv
load_dotenv()

class EnhancedScrapingAgent:
    def __init__(self):
        # Initialize OpenAI LLM
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if openai_api_key:
            self.llm = ChatOpenAI(temperature=0, model="gpt-4o", openai_api_key=openai_api_key)
        else:
            self.llm = None
            
        # Initialize Tavily tools
        self.tavily_search_tool = TavilySearch(max_results=5, topic="news")
        self.tavily_extract_tool = TavilyExtract()
        
        # Create tools list
        self.tools = [self.tavily_search_tool, self.tavily_extract_tool]
          # Setup prompt template
        today = datetime.now().strftime("%m/%d/%y")
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", f"""You are a helpful financial research assistant. You will be given a query and you will need to
            search the web for the most relevant financial information then extract content to gain more insights. 
            Focus on financial markets, earnings, stock performance, and market sentiment.
            The date today is {today}."""),
            MessagesPlaceholder(variable_name="messages"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        # Create agent executor if OpenAI is available
        if self.llm:
            self.agent = create_openai_tools_agent(
                llm=self.llm,
                tools=self.tools,
                prompt=self.prompt
            )
            self.agent_executor = AgentExecutor(agent=self.agent, tools=self.tools, verbose=False)
        else:
            self.agent_executor = None

    def enhanced_research(self, query: str) -> str:
       
        if not self.agent_executor:
            # Fallback to basic search if OpenAI not available
            return self.basic_search(query)
        
        try:
            response = self.agent_executor.invoke({
                "messages": [HumanMessage(content=f"Research financial information about: {query}")]
            })
            return response.get("output", "No results found")
            
        except Exception as e:
            st.error(f"Enhanced research error: {str(e)}")
            return self.basic_search(query)
    
    def basic_search(self, query: str) -> str:
        """
        Basic search fallback when OpenAI is not available
        """
        try:
            # Enhance query for financial context
            financial_query = f"financial news {query} earnings market stock analysis"
            result = self.tavily_search_tool.invoke({"query": financial_query})
            
            # Format results
            formatted_result = f"Search Results for: {query}\n\n"
            formatted_result += f"Summary: {result.get('answer', 'No summary available')}\n\n"
            
            for i, article in enumerate(result.get('results', [])[:3], 1):
                formatted_result += f"{i}. {article.get('title', 'No title')}\n"
                formatted_result += f"   {article.get('content', 'No content')[:200]}...\n"
                formatted_result += f"   URL: {article.get('url', 'No URL')}\n\n"
                
            return formatted_result
            
        except Exception as e:
            return f"Search error: {str(e)}"

# Global enhanced agent instance
enhanced_scraping_agent = EnhancedScrapingAgent()

# Original tool functions for backward compatibility
def search_financial_news(query: str) -> Dict[str, Any]:

    try:
        search_tool = TavilySearch(max_results=5, topic="news")
        
        # Enhance query for financial context
        financial_query = f"financial news {query} earnings market stock"
        
        result = search_tool.invoke({"query": financial_query})
        
        # Structure the output
        structured_results = {
            "query": query,
            "search_time": datetime.now().isoformat(),
            "answer": result.get("answer", ""),
            "articles": []
        }
        
        for article in result.get("results", []):
            structured_results["articles"].append({
                "title": article.get("title", ""),
                "url": article.get("url", ""),
                "content": article.get("content", "")[:500] + "..." if len(article.get("content", "")) > 500 else article.get("content", ""),
                "score": article.get("score", 0)
            })
        
        return structured_results
        
    except Exception as e:
        return {"error": f"News search error: {str(e)}"}

def search_earnings_data(company: str) -> Dict[str, Any]:
    """
    Search for earnings information
    """
    try:
        search_tool = TavilySearch(max_results=5, topic="general")
        
        earnings_query = f"{company} earnings report quarterly results financial performance"
        
        result = search_tool.invoke({"query": earnings_query})
        
        return {
            "company": company,
            "search_time": datetime.now().isoformat(),
            "earnings_summary": result.get("answer", ""),
            "sources": [
                {
                    "title": article.get("title", ""),
                    "url": article.get("url", ""),
                    "content": article.get("content", "")[:300] + "..." if len(article.get("content", "")) > 300 else article.get("content", "")
                }
                for article in result.get("results", [])[:3]
            ]
        }
        
    except Exception as e:
        return {"error": f"Earnings search error: {str(e)}"}

def extract_from_urls(urls: List[str]) -> Dict[str, Any]:
    """
    Extract content from specific URLs
    """
    try:
        extract_tool = TavilyExtract()
        
        result = extract_tool.invoke({"urls": urls})
        
        return {
            "extraction_time": datetime.now().isoformat(),
            "extracted_content": result,
            "urls_processed": len(urls)
        }
        
    except Exception as e:
        return {"error": f"URL extraction error: {str(e)}"}

def search_market_sentiment(topic: str) -> Dict[str, Any]:
    """
    Search for market sentiment on a topic
    """
    try:
        search_tool = TavilySearch(max_results=5, topic="general")
        
        sentiment_query = f"market sentiment {topic} analyst opinion bull bear outlook"
        
        result = search_tool.invoke({"query": sentiment_query})
        
        return {
            "topic": topic,
            "search_time": datetime.now().isoformat(),
            "sentiment_summary": result.get("answer", ""),
            "relevant_articles": [
                {
                    "title": article.get("title", ""),
                    "content": article.get("content", "")[:400] + "..." if len(article.get("content", "")) > 400 else article.get("content", ""),
                    "url": article.get("url", "")
                }
                for article in result.get("results", [])[:4]
            ]
        }
        
    except Exception as e:
        return {"error": f"Sentiment search error: {str(e)}"}

# Enhanced tool functions for LangGraph integration
def enhanced_news_search_tool(query: str) -> str:
    """
    Enhanced tool to search financial news using OpenAI + Tavily
    """
    result = enhanced_scraping_agent.enhanced_research(f"latest financial news about {query}")
    return f"Enhanced Financial News Research: {result}"

def enhanced_earnings_search_tool(query: str) -> str:
    """
    Enhanced tool to search earnings information
    """
    result = enhanced_scraping_agent.enhanced_research(f"earnings report and financial performance of {query}")
    return f"Enhanced Earnings Research: {result}"

def enhanced_sentiment_analysis_tool(query: str) -> str:
    """
    Enhanced tool to analyze market sentiment
    """
    result = enhanced_scraping_agent.enhanced_research(f"market sentiment and analyst opinions on {query}")
    return f"Enhanced Market Sentiment Analysis: {result}"

# Original tool functions for backward compatibility
def news_search_tool(query: str) -> str:
    """
    Tool to search financial news
    """
    result = search_financial_news(query)
    return f"Financial News Search Results: {result}"

def earnings_search_tool(query: str) -> str:
    """
    Tool to search earnings information
    """
    # Extract company name from query
    words = query.split()
    company = words[0] if words else "market"
    
    result = search_earnings_data(company)
    return f"Earnings Information: {result}"

def sentiment_analysis_tool(query: str) -> str:
    """
    Tool to analyze market sentiment
    """
    result = search_market_sentiment(query)
    return f"Market Sentiment Analysis: {result}"

def url_extract_tool(urls_string: str) -> str:
    """
    Tool to extract content from URLs
    """
    urls = [url.strip() for url in urls_string.split(",")]
    result = extract_from_urls(urls)
    return f"URL Extraction Results: {result}"

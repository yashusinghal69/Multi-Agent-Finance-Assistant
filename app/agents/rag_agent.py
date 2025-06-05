"""
RAG (Retrieval-Augmented Generation) Agent
Handles document upload, processing, and retrieval for enhanced context
Uses OpenAI embeddings for better performance
"""

import os
import tempfile
import streamlit as st
from typing import List, Optional
import pandas as pd
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain.schema import Document
from dotenv import load_dotenv

load_dotenv()

class RAGAgent:
    def __init__(self):
        # Initialize OpenAI embeddings
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if openai_api_key:
            self.embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)
        else:
            st.warning("OPENAI_API_KEY not found. RAG functionality will be limited.")
            self.embeddings = None
            
        self.vector_store = None
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len        )
    
    def process_uploaded_files(self, uploaded_files) -> bool:
        """
        Process uploaded files and create vector store
        
        Args:
            uploaded_files: Streamlit uploaded files
            
        Returns:
            Success status
        """
        if not uploaded_files or not self.embeddings:
            return False
            
        documents = []
        
        for uploaded_file in uploaded_files:
            try:
                # Create temporary file
                with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as tmp_file:
                    tmp_file.write(uploaded_file.getvalue())
                    tmp_file_path = tmp_file.name
                
                # Load document based on file type
                if uploaded_file.name.lower().endswith('.pdf'):
                    loader = PyPDFLoader(tmp_file_path)
                    docs = loader.load()
                elif uploaded_file.name.lower().endswith(('.txt', '.md')):
                    loader = TextLoader(tmp_file_path)
                    docs = loader.load()
                else:
                    # Try to read as text
                    content = uploaded_file.getvalue().decode('utf-8')
                    docs = [Document(page_content=content, metadata={"source": uploaded_file.name})]
                
                # Add source metadata
                for doc in docs:
                    doc.metadata["source"] = uploaded_file.name
                
                documents.extend(docs)
                
                # Clean up temp file
                os.unlink(tmp_file_path)
                
            except Exception as e:
                st.error(f"Error processing {uploaded_file.name}: {str(e)}")
                continue
        
        if documents:
            # Split documents into chunks
            texts = self.text_splitter.split_documents(documents)
            
            # Create vector store
            self.vector_store = FAISS.from_documents(texts, self.embeddings)
            
            return True
        
        return False
    
    def search_documents(self, query: str, k: int = 3) -> List[Document]:
        """
        Search documents for relevant context
        
        Args:
            query: Search query
            k: Number of results to return
            
        Returns:
            List of relevant documents
        """
        if not self.vector_store:
            return []
        
        try:
            docs = self.vector_store.similarity_search(query, k=k)
            return docs
        except Exception as e:
            st.error(f"Search error: {str(e)}")
            return []
    
    def get_context_for_query(self, query: str) -> str:
        """Get relevant context for a query"""
        relevant_docs = self.search_documents(query)
        
        if not relevant_docs:
            return ""
        
        context_parts = []
        for i, doc in enumerate(relevant_docs, 1):
            source = doc.metadata.get("source", "Unknown")
            content = doc.page_content.strip()
            context_parts.append(f"Document {i} ({source}):\n{content}")
        
        return "\n\n".join(context_parts)
    
    def add_csv_data(self, df: pd.DataFrame, filename: str) -> bool:
        """Add CSV data to vector store"""
        if not self.embeddings:
            return False
            
        try:
            # Convert DataFrame to text representation
            text_content = f"Data from {filename}:\n\n"
            text_content += f"Columns: {', '.join(df.columns.tolist())}\n\n"
            text_content += f"Summary:\n{df.describe().to_string()}\n\n"
            text_content += f"Sample rows:\n{df.head(10).to_string()}"
            
            # Create document
            doc = Document(
                page_content=text_content,
                metadata={"source": filename, "type": "csv_data"}
            )
            
            # Split and add to vector store
            texts = self.text_splitter.split_documents([doc])
            
            if self.vector_store:
                self.vector_store.add_documents(texts)
            else:
                self.vector_store = FAISS.from_documents(texts, self.embeddings)
            
            return True
            
        except Exception as e:
            st.error(f"Error adding CSV data: {str(e)}")
            return False
    def clear_documents(self):
        """Clear the vector store"""
        self.vector_store = None
    
    def has_documents(self) -> bool:
        """Check if vector store has documents"""
        return self.vector_store is not None


# Global RAG agent instance
rag_agent = RAGAgent()

def upload_documents_interface():
    """Streamlit interface for document upload"""
    st.sidebar.markdown("### 📄 Document Upload")
    
    uploaded_files = st.sidebar.file_uploader(
        "Upload documents for context",
        type=['pdf', 'txt', 'md', 'csv'],
        accept_multiple_files=True,
        help="Upload PDF, TXT, MD, or CSV files to enhance responses with your data"
    )
    
    if uploaded_files:
        if st.sidebar.button("Process Documents"):
            with st.spinner("Processing documents..."):
                # Handle CSV files separately
                csv_files = [f for f in uploaded_files if f.name.lower().endswith('.csv')]
                other_files = [f for f in uploaded_files if not f.name.lower().endswith('.csv')]
                
                success = True
                
                # Process CSV files
                for csv_file in csv_files:
                    try:
                        df = pd.read_csv(csv_file)
                        if not rag_agent.add_csv_data(df, csv_file.name):
                            success = False
                    except Exception as e:
                        st.sidebar.error(f"Error reading CSV {csv_file.name}: {str(e)}")
                        success = False
                
                # Process other files
                if other_files:
                    if not rag_agent.process_uploaded_files(other_files):
                        success = False
                
                if success:
                    st.sidebar.success(f"✅ Processed {len(uploaded_files)} documents!")
                else:
                    st.sidebar.error("❌ Some documents failed to process")
        
        # Clear documents button
        if st.sidebar.button("🗑️ Clear All Documents"):
            rag_agent.clear_documents()
            st.sidebar.success("Documents cleared")
            st.rerun()
    else:
        st.sidebar.info("📝 No documents uploaded yet")
        
        # Show sample instruction
        st.sidebar.markdown("""
        **Supported formats:**
        - 📄 PDF files
        - 📝 Text files (.txt, .md)
        - 📊 CSV files
        
        **Example uses:**
        - Upload financial reports
        - Add stock data (CSV)
        - Include company analysis
        """)
    
    # Show document status
    if rag_agent.has_documents():
        st.sidebar.success("✅ Documents ready for queries")
    else:
        st.sidebar.info("💡 Upload documents to enhance responses")

 
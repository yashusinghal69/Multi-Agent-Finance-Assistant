import streamlit as st
import os
import tempfile
import time
import re
from agents.voice_agent import transcribe_uploaded_audio, transcribe_audio_with_groq
 
from agents.rag_agent import upload_documents_interface, rag_agent

import os
import requests
import streamlit as st
from murf import Murf

def text_to_speech(text: str, voice_id: str = "en-US-natalie"):
    """Convert text to speech using Murf AI"""
    api_key = os.getenv("MURF_API_KEY")
    client = Murf(api_key=api_key)
    
    # Clean text
    clean_text = text.replace('*', '').replace('#', '').replace('`', '').strip()
    
    # Generate speech
    response = client.text_to_speech.generate(
        text=clean_text,
        voice_id=voice_id
    )
    
    # Download audio from URL
    audio_response = requests.get(response.audio_file)
    return audio_response.content


def play_audio_response(text: str, voice_id: str = "en-US-natalie"):
    """Generate and auto-play audio in Streamlit"""
    audio_bytes = text_to_speech(text, voice_id)
    st.audio(audio_bytes, format="audio/wav", autoplay=True)



DEFAULT_VOICES = {
    " Male Voice": "en-US-ken",
    " Female Voice": "en-US-natalie"
}


 
# Page configuration
st.set_page_config(
    page_title="Multi-Agent Finance Assistant",
    page_icon="📑",
    layout="wide"
)

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Helper function to process queries
def process_financial_query(query_text, enable_tts=False, voice_id=None, style=None, return_only=False):
    """Process financial query and optionally return result"""
    try:
        # Import orchestrator
        from agents.orchestrator import process_query
        
        # Get RAG context if available
        rag_context = ""
        if rag_agent.has_documents():
            rag_context = rag_agent.get_context_for_query(query_text)       
        agent_response = process_query(query_text, context=rag_context)
        
        if return_only:
            return agent_response
        
        st.success("✅ Query processed by AI agents!")
        
        st.markdown("### 🤖 AI Agent Analysis")
        st.markdown(agent_response)
        
        # Store in session state
        st.session_state.last_response = agent_response        
        if enable_tts and voice_id:
            st.markdown("### 🔊 Audio Response")
            play_audio_response(agent_response, voice_id)
            
        return agent_response
        
    except Exception as e:
        error_msg = f"❌ Error processing query: {str(e)}"
        if return_only:
            return error_msg
        else:
            st.error(error_msg)
            st.info("💡 Make sure you have set all required API keys in your .env file")
            return error_msg

# Title
st.title("🤖 Multi-Agent Finance Assistant")
st.markdown("### Voice-Enabled Financial Analysis with Document Upload & TTS")

# Sidebar for document upload and TTS settings
with st.sidebar:
    st.header("⚙️ Settings")
      # Document upload interface
    upload_documents_interface()
    
    st.markdown("---")    # TTS Settings
    st.markdown("### 🔊 Voice Output")
    enable_tts = st.checkbox("Enable Text-to-Speech", value=False)
    if enable_tts:
        # Voice selection - only 2 options
        voice_options = list(DEFAULT_VOICES.keys())
        selected_voice = st.selectbox("Select Voice", voice_options, index=0)
        voice_id = DEFAULT_VOICES[selected_voice]
        
        # Fixed style - always Conversational
        selected_style = "Conversational"
        
        # Preview info
        st.info(f"🎙️ Voice: {selected_voice}")
    else:
        voice_id = None
        selected_style = None
    
    st.markdown("---")
      # API Status
    st.markdown("### 🔑 API Status")
    
    # Check API keys
    groq_api_key = os.getenv('GROQ_API_KEY')
    openai_api_key = os.getenv('OPENAI_API_KEY')
    murf_api_key = os.getenv('MURF_API_KEY')
    
    if groq_api_key:
        st.sidebar.success("✅ Groq")
    else:
        st.sidebar.error("❌ Groq Missing")
    
    if openai_api_key and openai_api_key != "your_openai_api_key_here":
        st.sidebar.success("✅ OpenAI")
    else:
        st.sidebar.warning("⚠️ OpenAI")
        st.sidebar.info("💡 Add OpenAI key for full orchestration")
    
    if murf_api_key and murf_api_key != "your_murf_api_key_here":
        st.sidebar.success("✅ Murf API")
    else:
        st.sidebar.warning("⚠️ Murf API Missing")
        st.sidebar.info("💡 Add Murf API key for voice output")

# Check required API keys
groq_api_key = os.getenv('GROQ_API_KEY')
if not groq_api_key:
    st.error("❌ Please set GROQ_API_KEY in your .env file")
    st.stop()

# Main interface
# st.header("💬 Multi-Modal Input")

# Create tabs for different input methods
input_tab1, input_tab2 = st.tabs(["🎤 Voice Input", "💬 Text Chat"])

with input_tab1:
    st.subheader("Voice Recording & Upload")
    
    # Initialize session state
    if 'recording' not in st.session_state:
        st.session_state.recording = False
    if 'transcription' not in st.session_state:
        st.session_state.transcription = ""

    # Voice recording section
    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("🎙️ Record Audio")
        
        # Simple audio recorder with automatic timeout
        audio_value = st.audio_input(
            "Record your financial query (stops after 5 seconds of silence)",
            key="audio_input"
        )
        
        if audio_value is not None:
            st.success("✅ Audio recorded!")
            
            # Auto-transcribe when audio is recorded
            with st.spinner("🔄 Transcribing..."):
                # Save audio to temp file
                with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                    temp_file.write(audio_value.read())
                    temp_file_path = temp_file.name
                
                # Transcribe
                transcription = transcribe_audio_with_groq(temp_file_path)
                st.session_state.transcription = transcription
                
                # Clean up
                try:
                    os.unlink(temp_file_path)
                except:
                    pass
        
        # File upload option
        st.subheader("📁 Upload Audio File")
        uploaded_file = st.file_uploader(
            "Choose audio file", 
            type=['wav', 'mp3', 'm4a']
        )
        
        if uploaded_file is not None:
            st.audio(uploaded_file)
            
            with st.spinner("🔄 Transcribing uploaded file..."):
                # Save uploaded file
                with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                    temp_file.write(uploaded_file.read())
                    temp_file_path = temp_file.name
                
                transcription = transcribe_uploaded_audio(temp_file_path)
                st.session_state.transcription = transcription
                
                # Clean up
                try:
                    os.unlink(temp_file_path)
                except:
                    pass

    with col2:
        st.subheader("📝 Transcription")
        
        if st.session_state.transcription:
            st.info(f"**Transcribed:** {st.session_state.transcription}")            # Edit transcription
            edited_text = st.text_area(
                "Edit if needed:",
                value=st.session_state.transcription,
                height=100,
                key="voice_text_edit"
            )            
            if st.button("🚀 Process Voice Query", type="primary"):
                process_financial_query(edited_text, enable_tts, voice_id)
        else:
            st.info("👆 Record or upload audio to see transcription")

with input_tab2:
    st.subheader("💬 Text Chat Interface")
    
    # Initialize chat history
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []    # Display chat history
    chat_container = st.container()
    with chat_container:
        for i, (role, message) in enumerate(st.session_state.chat_history[-5:]):  # Show last 5 messages
            if role == "user":
                st.markdown(f"**🧑 You:** {message}")
            else:
                # Display the assistant message (already formatted by LLM)
                st.markdown(f"**🤖 Assistant:** {message}")
                if enable_tts and voice_id and i == len(st.session_state.chat_history[-5:]) - 1:  # Only TTS the latest response
                    with st.expander("🔊 Play Audio"):
                        play_audio_response(message, voice_id)
    
    # Text input
    with st.form(key="text_chat_form", clear_on_submit=True):
        user_input = st.text_input(
            "💬 Ask your financial question:",
            placeholder="e.g., What's Apple's stock price today? Latest Tesla news? Market sentiment?",
            key="text_input"
        )
        col_submit, col_clear = st.columns([1, 1])
        
        with col_submit:
            submit_button = st.form_submit_button("🚀 Send", type="primary")
        
        with col_clear:
            clear_button = st.form_submit_button("🗑️ Clear History")
    
    if submit_button and user_input:
        # Add user message to history
        st.session_state.chat_history.append(("user", user_input))        # Process query
        with st.spinner("🤖 AI is thinking..."):
            response = process_financial_query(user_input, enable_tts, voice_id, return_only=True)
            
        # Add AI response to history
        st.session_state.chat_history.append(("assistant", response))
          # Rerun to update display
        st.rerun()
    
    if clear_button:
        st.session_state.chat_history = []
        st.rerun()

 
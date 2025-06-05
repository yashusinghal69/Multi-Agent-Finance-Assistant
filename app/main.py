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
    enable_tts = st.checkbox("Enable Text-to-Speech", value=True)
    if enable_tts:
        # Voice selection - only 2 options
        voice_options = list(DEFAULT_VOICES.keys())
        selected_voice = st.selectbox("Select Voice", voice_options, index=1, help="Choose a voice for audio responses")
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

# Main interface - Tabbed Layout
st.markdown("---")

# Initialize session state
if 'recording' not in st.session_state:
    st.session_state.recording = False
if 'transcription' not in st.session_state:
    st.session_state.transcription = ""
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'last_audio_hash' not in st.session_state:
    st.session_state.last_audio_hash = None

# Create tabs for different input methods
tab1, tab2 = st.tabs(["🎤 Voice Input & Recording", "💬 Text Chat Interface"])

# TAB 1 - Voice Input Section
with tab1:
    st.markdown("## 🎤 Voice Input & Recording")
      # Clear transcription button
    col_clear, col_space = st.columns([1, 3])
    with col_clear:
        if st.button("🗑️ Clear Transcription", help="Clear previous transcription to start fresh"):
            st.session_state.transcription = ""
    
    st.markdown("---")
    
    # Create two columns for voice recording layout
    voice_col1, voice_col2 = st.columns([1, 1], gap="medium")
    
    with voice_col1:
        # Voice recording card
        with st.container():
            st.markdown("""
            <div style="background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); 
                        padding: 20px; border-radius: 15px; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                <h4 style="color: #ffffff; margin: 0; font-weight: bold;">🎙️ Voice Recording</h4>
                <p style="color: #ffffff; margin: 5px 0 0 0; opacity: 0.9;">Record your financial query</p>
            </div>
            """, unsafe_allow_html=True)
              # Audio input
            audio_value = st.audio_input(
                "🎵 Record your question (stops after 5 seconds of silence)",
                key="voice_tab_audio_input"
            )            
            if audio_value is not None:
                # Create a hash of the audio data to avoid reprocessing
                import hashlib
                audio_data = audio_value.read()
                audio_hash = hashlib.md5(audio_data).hexdigest()
                
                # Only process if this is new audio
                if audio_hash != st.session_state.last_audio_hash:
                    st.session_state.last_audio_hash = audio_hash
                    st.success("✅ Audio recorded successfully!")
                    
                    # Auto-transcribe when audio is recorded
                    with st.spinner("🔄 Transcribing your voice..."):
                        # Save audio to temp file
                        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                            temp_file.write(audio_data)
                            temp_file_path = temp_file.name
                        
                        # Transcribe
                        transcription = transcribe_audio_with_groq(temp_file_path)
                        st.session_state.transcription = transcription
                        
                        # Clean up
                        try:
                            os.unlink(temp_file_path)
                        except:
                            pass
        
        # File upload card
        with st.container():
            st.markdown("""
            <div style="background: linear-gradient(90deg, #f093fb 0%, #f5576c 100%); 
                        padding: 20px; border-radius: 15px; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                <h4 style="color: #ffffff; margin: 0; font-weight: bold;">📁 Upload Audio File</h4>
                <p style="color: #ffffff; margin: 5px 0 0 0; opacity: 0.9;">Choose an existing audio file</p>
            </div>
            """, unsafe_allow_html=True)
            uploaded_file = st.file_uploader(
                "Choose audio file", 
                type=['wav', 'mp3', 'm4a'],
                help="Drag and drop or browse for WAV, MP3, or M4A files",
                key="voice_tab_file_upload"
            )            
            if uploaded_file is not None:
                # Create a hash of the uploaded file to avoid reprocessing
                import hashlib
                file_data = uploaded_file.read()
                file_hash = hashlib.md5(file_data).hexdigest()
                
                # Only process if this is a new file
                if file_hash != st.session_state.last_audio_hash:
                    st.session_state.last_audio_hash = file_hash
                    st.audio(file_data, format="audio/wav")
                    
                    with st.spinner("🔄 Processing uploaded audio file..."):
                        # Save uploaded file
                        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                            temp_file.write(file_data)
                            temp_file_path = temp_file.name
                        
                        transcription = transcribe_uploaded_audio(temp_file_path)
                        st.session_state.transcription = transcription
                        
                        # Clean up
                        try:
                            os.unlink(temp_file_path)
                        except:
                            pass
    
    with voice_col2:
        # Transcription display and editing
        if st.session_state.transcription:
            st.markdown("### 📝 Voice Transcription")
            
            # Display transcription in a nice box
            st.markdown(f"""
            <div style="background: #f0f8ff; padding: 15px; border-radius: 10px; 
                        border-left: 4px solid #4CAF50; margin-bottom: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <strong style="color: #2c3e50; font-size: 16px;">🗣️ Transcribed Text:</strong><br>
                <span style="font-size: 16px; color: #34495e; line-height: 1.5;">{st.session_state.transcription}</span>
            </div>
            """, unsafe_allow_html=True)
            
            # Edit transcription
            edited_text = st.text_area(
                "✏️ Edit transcription if needed:",
                value=st.session_state.transcription,
                height=120,
                key="voice_text_edit",
                help="Make any corrections to the transcribed text before processing"
            )
            
            # Process button
            if st.button("🚀 Process Voice Query", type="primary", use_container_width=True):
                with st.spinner("🤖 Processing your voice query..."):
                    process_financial_query(edited_text, enable_tts, voice_id)
        else:
            st.markdown("""
            <div style="background: #fff3cd; padding: 30px; border-radius: 10px; 
                        text-align: center; margin-top: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <h4 style="color: #856404; margin-bottom: 10px;">🎙️ Ready to Listen!</h4>
                <p style="color: #856404; font-size: 16px; margin: 0;">Record audio or upload a file to see the transcription here</p>
            </div>
            """, unsafe_allow_html=True)

# TAB 2 - Text Chat Section
with tab2:
    st.markdown("## 💬 Text Chat Interface")
    
    # Chat history display
    chat_container = st.container()
    with chat_container:
        if st.session_state.chat_history:
            st.markdown("""
            <div style="background: linear-gradient(90deg, #4facfe 0%, #00f2fe 100%); 
                        padding: 15px; border-radius: 15px; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                <h4 style="color: #ffffff; margin: 0; font-weight: bold;">💭 Conversation History</h4>
                <p style="color: #ffffff; margin: 5px 0 0 0; opacity: 0.9;">Your recent chat messages</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Display last 5 messages
            for i, (role, message) in enumerate(st.session_state.chat_history[-5:]):
                if role == "user":
                    st.markdown(f"""
                    <div style="background: #e3f2fd; padding: 12px; border-radius: 10px; 
                                margin: 10px 0; border-left: 4px solid #2196F3; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                        <strong style="color: #1565C0; font-size: 16px;">🧑 You:</strong> 
                        <span style="color: #424242; font-size: 15px;">{message}</span>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div style="background: #f1f8e9; padding: 12px; border-radius: 10px; 
                                margin: 10px 0; border-left: 4px solid #4CAF50; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                        <strong style="color: #2E7D32; font-size: 16px;">🤖 Assistant:</strong> 
                        <span style="color: #424242; font-size: 15px;">{message}</span>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # TTS for latest response only
                    if enable_tts and voice_id and i == len(st.session_state.chat_history[-5:]) - 1:
                        with st.expander("🔊 Play Audio Response"):
                            play_audio_response(message, voice_id)
        else:
            st.markdown("""
            <div style="background: #f8f9fa; padding: 30px; border-radius: 15px; 
                        text-align: center; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <h4 style="color: #495057; margin-bottom: 10px;">💬 Start Your Conversation</h4>
                <p style="color: #6c757d; font-size: 16px; margin: 0;">Your chat history will appear here once you start asking questions</p>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Text input form
    st.markdown("### ✍️ Type Your Message")
    with st.form(key="text_chat_form", clear_on_submit=True):
        user_input = st.text_input(
            "💭 Ask your financial question:",
            placeholder="e.g., What's Apple's stock price today? Latest Tesla news? Market sentiment?",
            key="text_input",
            help="Type your question and press Enter or click Send"
        )
        
        # Form buttons
        col_submit, col_clear = st.columns([2, 1])
        
        with col_submit:
            submit_button = st.form_submit_button("🚀 Send Message", type="primary", use_container_width=True)
        
        with col_clear:
            clear_button = st.form_submit_button("🗑️ Clear History", use_container_width=True)
    
    # Handle form submissions
    if submit_button and user_input:
        # Add user message to history
        st.session_state.chat_history.append(("user", user_input))
        
        # Process query
        with st.spinner("🤖 AI agents are analyzing your question..."):
            response = process_financial_query(user_input, enable_tts, voice_id, return_only=True)
            
        # Add AI response to history
        st.session_state.chat_history.append(("assistant", response))
        
        # Rerun to update display
        st.rerun()
    
    if clear_button:
        st.session_state.chat_history = []
        st.success("💫 Chat history cleared!")
        st.rerun()

# Bottom section - Quick actions and tips
st.markdown("---")
st.markdown("### 💡 Quick Tips & Actions")

tip_col1, tip_col2, tip_col3 = st.columns(3)

with tip_col1:
    st.markdown("""
    <div style="background: #fff3e0; padding: 15px; border-radius: 10px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
        <h5 style="color: #ef6c00; margin-bottom: 10px; font-weight: bold;">🎯 Pro Tips</h5>
        <p style="font-size: 14px; color: #bf360c; line-height: 1.6; margin: 0;">
        • Upload documents for context<br>
        • Use voice for hands-free analysis<br>
        • Enable TTS for audio responses
        </p>
    </div>
    """, unsafe_allow_html=True)

with tip_col2:
    st.markdown("""
    <div style="background: #f3e5f5; padding: 15px; border-radius: 10px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
        <h5 style="color: #7b1fa2; margin-bottom: 10px; font-weight: bold;">📊 Ask About</h5>
        <p style="font-size: 14px; color: #4a148c; line-height: 1.6; margin: 0;">
        • Stock prices & trends<br>
        • Market news & analysis<br>
        • Portfolio insights
        </p>
    </div>
    """, unsafe_allow_html=True)

with tip_col3:
    st.markdown("""
    <div style="background: #e8f5e8; padding: 15px; border-radius: 10px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
        <h5 style="color: #2e7d32; margin-bottom: 10px; font-weight: bold;">🔧 Settings</h5>
        <p style="font-size: 14px; color: #1b5e20; line-height: 1.6; margin: 0;">
        • Check sidebar for documents<br>
        • Configure voice settings<br>
        • Monitor API status
        </p>
    </div>
    """, unsafe_allow_html=True)

 
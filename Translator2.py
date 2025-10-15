from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from dotenv import load_dotenv
import streamlit as st
import pandas as pd
import json
import time
from datetime import datetime
import pyperclip
import requests

load_dotenv()

# Configure page
st.set_page_config(
    page_title="Global Translator Pro",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for beautiful UI
st.markdown("""
<style>
    .main-header {
        font-size: 3.5rem;
        background: linear-gradient(45deg, #FF6B6B, #4ECDC4, #45B7D1, #96CEB4);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 2rem;
        font-weight: 800;
    }
    .translation-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 20px;
        padding: 30px;
        margin: 20px 0;
        color: white;
        box-shadow: 0 10px 30px rgba(0,0,0,0.2);
    }
    .input-card {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        border-radius: 20px;
        padding: 30px;
        margin: 20px 0;
        color: white;
        box-shadow: 0 10px 30px rgba(0,0,0,0.2);
    }
    .stats-card {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        border-radius: 15px;
        padding: 20px;
        margin: 10px 0;
        color: white;
        text-align: center;
    }
    .language-tag {
        background: rgba(255,255,255,0.2);
        padding: 5px 15px;
        border-radius: 20px;
        margin: 5px;
        display: inline-block;
        font-size: 0.9rem;
    }
    .translate-btn {
        background: linear-gradient(45deg, #FF6B6B, #4ECDC4);
        color: white;
        border: none;
        border-radius: 25px;
        padding: 12px 30px;
        font-size: 1.1rem;
        font-weight: bold;
        cursor: pointer;
        transition: all 0.3s ease;
        width: 100%;
    }
    .translate-btn:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(0,0,0,0.3);
    }
    .copy-btn {
        background: rgba(255,255,255,0.2);
        color: white;
        border: 2px solid white;
        border-radius: 20px;
        padding: 8px 20px;
        margin: 5px;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    .copy-btn:hover {
        background: white;
        color: #667eea;
    }
    .history-item {
        background: rgba(255,255,255,0.1);
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
        border-left: 4px solid #4ECDC4;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state for history
if 'translation_history' not in st.session_state:
    st.session_state.translation_history = []

if 'total_translations' not in st.session_state:
    st.session_state.total_translations = 0

# Available languages with emojis
LANGUAGES = {
    "English": "🇺🇸", "Spanish": "🇪🇸", "French": "🇫🇷", "German": "🇩🇪", 
    "Italian": "🇮🇹", "Portuguese": "🇵🇹", "Russian": "🇷🇺", "Chinese": "🇨🇳",
    "Japanese": "🇯🇵", "Korean": "🇰🇷", "Arabic": "🇸🇦", "Hindi": "🇮🇳",
    "Bengali": "🇧🇩", "Turkish": "🇹🇷", "Dutch": "🇳🇱", "Greek": "🇬🇷",
    "Hebrew": "🇮🇱", "Thai": "🇹🇭", "Vietnamese": "🇻🇳", "Swedish": "🇸🇪"
}

def detect_language(text):
    """Simple language detection based on common characters"""
    if not text.strip():
        return "Unknown"
    
    # Simple character-based detection (in real app, use proper language detection API)
    common_words = {
        'the': 'English', 'and': 'English', 'is': 'English',
        'el': 'Spanish', 'la': 'Spanish', 'de': 'Spanish',
        'le': 'French', 'la': 'French', 'et': 'French',
        'der': 'German', 'die': 'German', 'das': 'German',
        'क': 'Hindi', 'ह': 'Hindi', 'म': 'Hindi',
        'আ': 'Bengali', 'ক': 'Bengali', 'গ': 'Bengali'
    }
    
    words = text.lower().split()
    for word in words[:5]:  # Check first 5 words
        if word in common_words:
            return common_words[word]
    
    return "Unknown / Multiple"

def get_language_info(language):
    """Get basic information about languages"""
    language_info = {
        "English": {"speakers": "1.5B", "family": "Germanic", "countries": "60+"},
        "Spanish": {"speakers": "580M", "family": "Romance", "countries": "20+"},
        "French": {"speakers": "280M", "family": "Romance", "countries": "29"},
        "German": {"speakers": "130M", "family": "Germanic", "countries": "6"},
        "Hindi": {"speakers": "600M", "family": "Indo-Aryan", "countries": "4"},
        "Bengali": {"speakers": "230M", "family": "Indo-Aryan", "countries": "2"},
        "Chinese": {"speakers": "1.3B", "family": "Sino-Tibetan", "countries": "4"},
        "Japanese": {"speakers": "125M", "family": "Japonic", "countries": "1"}
    }
    return language_info.get(language, {"speakers": "N/A", "family": "N/A", "countries": "N/A"})

def copy_to_clipboard(text):
    """Copy text to clipboard"""
    try:
        pyperclip.copy(text)
        return True
    except:
        return False

def main():
    # Header
    st.markdown('<h1 class="main-header">🌍 Global Translator Pro</h1>', unsafe_allow_html=True)
    
    # Initialize model
    model = ChatGoogleGenerativeAI(model='gemini-2.5-flash', temperature=0.3)
    
    # Sidebar
    with st.sidebar:
        st.markdown("### 📊 Translation Stats")
        st.markdown(f'<div class="stats-card">Total Translations<br><h2>{st.session_state.total_translations}</h2></div>', unsafe_allow_html=True)
        
        st.markdown("### 🌐 Supported Languages")
        cols = st.columns(2)
        for i, (lang, flag) in enumerate(LANGUAGES.items()):
            with cols[i % 2]:
                st.markdown(f'{flag} {lang}')
        
        st.markdown("---")
        st.markdown("### 📝 Recent History")
        if st.session_state.translation_history:
            for i, item in enumerate(st.session_state.translation_history[-5:]):  # Show last 5
                with st.expander(f"{item['from_lang']} → {item['to_lang']}", expanded=False):
                    st.write(f"**Input:** {item['input'][:50]}...")
                    st.write(f"**Output:** {item['output'][:50]}...")
        else:
            st.write("No translations yet")
        
        # Clear history button
        if st.button("🗑️ Clear History"):
            st.session_state.translation_history = []
            st.session_state.total_translations = 0
            st.rerun()

    # Main content area
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown('<div class="input-card">', unsafe_allow_html=True)
        st.markdown("### 💬 Input Text")
        
        User_Input = st.text_area(
            "Enter text to translate",
            placeholder="Type your text here...",
            height=150,
            label_visibility="collapsed"
        )
        
        # Language detection
        if User_Input:
            detected_lang = detect_language(User_Input)
            st.markdown(f"**Detected Language:** {detected_lang}")
        
        # Character count
        char_count = len(User_Input) if User_Input else 0
        st.markdown(f"**Character Count:** {char_count}")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Additional features
        st.markdown("### ⚡ Quick Actions")
        quick_col1, quick_col2, quick_col3 = st.columns(3)
        
        with quick_col1:
            if st.button("📝 Clear Text"):
                st.rerun()
        
        with quick_col2:
            if st.button("📄 Sample Text"):
                st.session_state.sample_text = "Hello! How are you today? This is a sample text for translation."
                st.rerun()
        
        with quick_col3:
            if st.button("🔄 Swap Languages"):
                st.session_state.swap_languages = True

    with col2:
        st.markdown("### 🎯 Translation Settings")
        
        # Target language selection with search
        target_language = st.selectbox(
            "Select Target Language",
            list(LANGUAGES.keys()),
            index=5,  # Default to Hindi
            format_func=lambda x: f"{LANGUAGES[x]} {x}"
        )
        
        # Language info
        lang_info = get_language_info(target_language)
        st.markdown(f"""
        <div style='background: rgba(76, 175, 80, 0.2); padding: 15px; border-radius: 10px; margin: 10px 0;'>
            <strong>Language Info:</strong><br>
            • Speakers: {lang_info['speakers']}<br>
            • Language Family: {lang_info['family']}<br>
            • Countries: {lang_info['countries']}
        </div>
        """, unsafe_allow_html=True)
        
        # Translation options
        st.markdown("### ⚙️ Translation Options")
        col1, col2 = st.columns(2)
        
        with col1:
            translation_style = st.selectbox(
                "Translation Style",
                ["Standard", "Formal", "Casual", "Technical", "Literary"]
            )
        
        with col2:
            include_pronunciation = st.checkbox("Include Pronunciation", value=False)

    # Translate button
    if st.button("🚀 Translate Now", use_container_width=True, type="primary"):
        if User_Input.strip():
            with st.spinner("🔄 Translating... This may take a few seconds"):
                try:
                    # Enhanced prompt template
                    template = PromptTemplate(
                        template="""
                        Translate the following text into {language} with {style} style.
                        {pronunciation}
                        
                        Original Text: "{input_text}"
                        
                        Important: 
                        - Provide only the translated text
                        - Maintain the original meaning and context
                        - Use appropriate {style} tone
                        {extra_instruction}
                        
                        Translated Text:
                        """,
                        input_variables=['language', 'style', 'pronunciation', 'input_text', 'extra_instruction']
                    )
                    
                    pronunciation_instruction = "Include pronunciation in brackets after each sentence." if include_pronunciation else ""
                    extra_instruction = "If the text contains proper nouns or technical terms, keep them in their original form when appropriate." if translation_style == "Technical" else ""
                    
                    prompt = template.invoke({
                        'language': target_language,
                        'style': translation_style,
                        'pronunciation': pronunciation_instruction,
                        'input_text': User_Input,
                        'extra_instruction': extra_instruction
                    })
                    
                    # Get translation
                    response = model.invoke(prompt)
                    translated_text = response.content
                    
                    # Store in history
                    history_item = {
                        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        'input': User_Input,
                        'output': translated_text,
                        'from_lang': detect_language(User_Input),
                        'to_lang': target_language,
                        'style': translation_style
                    }
                    
                    st.session_state.translation_history.append(history_item)
                    st.session_state.total_translations += 1
                    
                    # Display results
                    st.markdown('<div class="translation-card">', unsafe_allow_html=True)
                    st.markdown("### ✅ Translation Result")
                    
                    # Original and translated text
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("**Original Text:**")
                        st.info(User_Input)
                    
                    with col2:
                        st.markdown(f"**Translated Text ({target_language}):**")
                        st.success(translated_text)
                    
                    # Copy buttons
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("📋 Copy Translation", use_container_width=True):
                            if copy_to_clipboard(translated_text):
                                st.toast("✅ Translation copied to clipboard!")
                            else:
                                st.toast("❌ Failed to copy to clipboard")
                    
                    with col2:
                        if st.button("💾 Save to History", use_container_width=True):
                            st.toast("✅ Translation saved to history!")
                    
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    # Additional analysis
                    with st.expander("📈 Translation Analysis"):
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.metric("Input Length", f"{len(User_Input)} chars")
                        
                        with col2:
                            st.metric("Output Length", f"{len(translated_text)} chars")
                        
                        with col3:
                            ratio = (len(translated_text) / len(User_Input)) if User_Input else 0
                            st.metric("Length Ratio", f"{ratio:.2f}")
                        
                        # Word count comparison
                        input_words = len(User_Input.split())
                        output_words = len(translated_text.split())
                        st.write(f"**Word Count:** {input_words} → {output_words}")
                        
                except Exception as e:
                    st.error(f"❌ Translation failed: {str(e)}")
        else:
            st.warning("⚠️ Please enter some text to translate")

    # Features section
    st.markdown("---")
    st.markdown("## ✨ Advanced Features")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("### 🔍 Batch Translation")
        st.write("Upload a file to translate multiple texts at once")
        uploaded_file = st.file_uploader("Choose a file", type=['txt', 'csv'])
        if uploaded_file:
            st.info("Batch translation feature - Coming Soon!")
    
    with col2:
        st.markdown("### 🎤 Voice Input")
        st.write("Speak instead of typing for translation")
        if st.button("🎤 Start Recording"):
            st.info("Voice input feature - Coming Soon!")
    
    with col3:
        st.markdown("### 📚 Phrasebook")
        st.write("Save and manage common phrases")
        if st.button("➕ Add to Phrasebook"):
            st.info("Phrasebook feature - Coming Soon!")

    # Footer
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: #666;'>"
        "Powered by Google Gemini AI • Built with Streamlit • 🌍 Breaking Language Barriers"
        "</div>",
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
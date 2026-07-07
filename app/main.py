"""Main Streamlit application."""
import streamlit as st
from pathlib import Path
import sys
import uuid

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.rag_pipeline import RAGPipeline
from utils.config import config
from utils.validators import validate_pdf
from utils.helpers import sanitize_filename, generate_file_hash
from database.metadata_store import MetadataStore
from app.components.chat_interface import render_chat_interface
from app.components.file_manager import render_file_manager
from app.components.source_viewer import render_source_viewer

# Page config
st.set_page_config(
    page_title="PDF Q&A RAG System",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        padding: 1rem 0;
    }
    .sidebar .sidebar-content {
        background-color: #f0f2f6;
    }
    .stButton>button {
        width: 100%;
    }
    .source-box {
        background-color: #f8f9fa;
        border-left: 3px solid #1f77b4;
        padding: 1rem;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'rag_pipeline' not in st.session_state:
    st.session_state.rag_pipeline = RAGPipeline()
if 'metadata_store' not in st.session_state:
    st.session_state.metadata_store = MetadataStore()
if 'session_id' not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'processed_files' not in st.session_state:
    st.session_state.processed_files = []

# Main header
st.markdown('<div class="main-header">📚 PDF Q&A RAG System</div>', unsafe_allow_html=True)
st.markdown("---")

# Sidebar
with st.sidebar:
    st.header("📄 Document Management")
    
    # File uploader
    uploaded_files = st.file_uploader(
        "Upload PDF Documents",
        type=['pdf'],
        accept_multiple_files=True,
        help="Upload one or more PDF files to analyze"
    )
    
    # Process uploaded files
    if uploaded_files:
        for uploaded_file in uploaded_files:
            if uploaded_file.name not in st.session_state.processed_files:
                with st.spinner(f"Processing {uploaded_file.name}..."):
                    # Save file
                    temp_path = config.temp_dir / sanitize_filename(uploaded_file.name)
                    with open(temp_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    
                    # Validate
                    is_valid, error = validate_pdf(temp_path)
                    
                    if is_valid:
                        # Generate hash
                        file_hash = generate_file_hash(temp_path)
                        
                        # Move to documents directory
                        final_path = config.documents_dir / 'pdf' / sanitize_filename(uploaded_file.name)
                        final_path.parent.mkdir(parents=True, exist_ok=True)
                        temp_path.rename(final_path)
                        
                        # Add to metadata
                        doc_id = st.session_state.metadata_store.add_document(
                            filename=uploaded_file.name,
                            file_path=str(final_path),
                            file_hash=file_hash,
                            file_size=final_path.stat().st_size,
                            file_type='pdf'
                        )
                        
                        # Process
                        result = st.session_state.rag_pipeline.process_document(final_path)
                        
                        if result['success']:
                            st.session_state.metadata_store.update_document_status(
                                doc_id,
                                'completed',
                                result['chunks']
                            )
                            st.session_state.processed_files.append(uploaded_file.name)
                            st.success(f"✅ {uploaded_file.name} processed!")
                            st.info(f"Pages: {result['pages']} | Chunks: {result['chunks']}")
                        else:
                            st.error(f"❌ Error: {result.get('error')}")
                    else:
                        st.error(f"❌ Invalid file: {error}")
                        temp_path.unlink()
    
    # Show processed files using file manager
    if st.session_state.processed_files:
        render_file_manager(
            st.session_state.processed_files,
            st.session_state.metadata_store,
            st.session_state.rag_pipeline
        )
    
    st.markdown("---")
    
    # Settings
    st.subheader("⚙️ Settings")
    
    use_memory = st.checkbox("Use Conversation Memory", value=True)
    top_k = st.slider("Number of Sources", 1, 10, 5)
    
    st.markdown("---")
    
    # Statistics
    if st.button("📊 Show Statistics"):
        stats = st.session_state.metadata_store.get_statistics()
        st.json(stats)
    
    # Clear database
    if st.button("🗑️ Clear Database"):
        if st.session_state.processed_files:
            confirm = st.warning("Are you sure? This will delete all documents.")
            if st.button("Yes, Clear All"):
                st.session_state.rag_pipeline.clear_database()
                st.session_state.processed_files = []
                st.session_state.chat_history = []
                st.success("Database cleared!")
                st.rerun()

# Main content area
col1, col2 = st.columns([2, 1])

with col1:
    st.header("💬 Ask Questions")
    
    # Display chat history
    for chat in st.session_state.chat_history:
        with st.chat_message("user"):
            st.write(chat['question'])
        
        with st.chat_message("assistant"):
            st.write(chat['answer'])
            if chat.get('pages'):
                st.caption(f"📄 Sources: Pages {', '.join(map(str, chat['pages']))}")
    
    # Question input
    if question := st.chat_input("Ask a question about your documents..."):
        if not st.session_state.processed_files:
            st.warning("⚠️ Please upload at least one PDF document first!")
        else:
            # Display user question
            with st.chat_message("user"):
                st.write(question)
            
            # Get answer
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    result = st.session_state.rag_pipeline.query(
                        question,
                        session_id=st.session_state.session_id,
                        use_memory=use_memory
                    )
                    
                    if result['success']:
                        answer = result['answer']
                        pages = result.get('pages', [])
                        sources = result.get('sources', [])
                        
                        st.write(answer)
                        
                        if pages:
                            st.caption(f"📄 Sources: Pages {', '.join(map(str, pages))}")
                        
                        # Save to history
                        st.session_state.chat_history.append({
                            'question': question,
                            'answer': answer,
                            'pages': pages,
                            'sources': sources
                        })
                    else:
                        st.error(f"❌ Error: {result.get('error')}")

with col2:
    st.header("📖 Source Preview")
    
    if st.session_state.chat_history:
        latest_chat = st.session_state.chat_history[-1]
        sources = latest_chat.get('sources', [])
        
        if sources:
            for idx, source in enumerate(sources, 1):
                with st.expander(f"Source {idx} - Page {source.get('page', 'N/A')}"):
                    st.markdown(f"**Source:** {source.get('source', 'Unknown')}")
                    st.markdown(f"**Page:** {source.get('page', 'N/A')}")
                    st.markdown("**Content:**")
                    st.text(source.get('content', '')[:300] + "...")
        else:
            st.info("No sources available. Ask a question to see sources.")
    else:
        st.info("No questions asked yet. Start a conversation!")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    <p>🤖 Advanced RAG System with Multi-Agent Support</p>
    <p style='font-size: 0.8rem;'>Built with LangChain, OpenAI, ChromaDB, and Streamlit</p>
</div>
""", unsafe_allow_html=True)
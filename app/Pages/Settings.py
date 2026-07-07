"""Settings page."""
import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from utils.config import config

st.set_page_config(page_title="Settings", page_icon="⚙️", layout="wide")

st.title("⚙️ System Settings")

# Model settings
st.subheader("🤖 Model Configuration")

col1, col2 = st.columns(2)

with col1:
    st.text_input("OpenAI Model", value=config.openai_model, disabled=True)
    st.text_input("Embedding Model", value=config.embedding_model, disabled=True)

with col2:
    st.number_input("Temperature", value=config.temperature, min_value=0.0, max_value=2.0, step=0.1)
    st.number_input("Top K Results", value=config.top_k_results, min_value=1, max_value=20)

st.markdown("---")

# Processing settings
st.subheader("⚙️ Processing Configuration")

col1, col2 = st.columns(2)

with col1:
    st.number_input("Chunk Size", value=config.chunk_size, min_value=100, max_value=2000, step=100)

with col2:
    st.number_input("Chunk Overlap", value=config.chunk_overlap, min_value=0, max_value=500, step=50)

st.markdown("---")

# Cache settings
st.subheader("💾 Cache Configuration")

st.checkbox("Enable Cache", value=config.enable_cache)
st.number_input("Cache TTL (seconds)", value=config.cache_ttl, min_value=60, max_value=7200, step=60)

st.markdown("---")

# System info
st.subheader("ℹ️ System Information")

info_col1, info_col2 = st.columns(2)

with info_col1:
    st.text(f"Environment: {config.environment}")
    st.text(f"Debug Mode: {config.debug}")
    st.text(f"Log Level: {config.log_level}")

with info_col2:
    st.text(f"Vector DB Path: {config.vectordb_dir}")
    st.text(f"Documents Path: {config.documents_dir}")

# Save button (placeholder)
if st.button("💾 Save Settings"):
    st.success("Settings saved! (Note: Some settings require restart)")
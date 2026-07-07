"""Analytics page."""
import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from database.metadata_store import MetadataStore
import pandas as pd

st.set_page_config(page_title="Analytics", page_icon="📊", layout="wide")

st.title("📊 System Analytics")

# Initialize metadata store
if 'metadata_store' not in st.session_state:
    st.session_state.metadata_store = MetadataStore()

metadata_store = st.session_state.metadata_store

# Get statistics
stats = metadata_store.get_statistics()

# Display metrics
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Documents", stats.get('total_documents', 0))

with col2:
    st.metric("Processed Documents", stats.get('processed_documents', 0))

with col3:
    st.metric("Total Chunks", stats.get('total_chunks', 0))

with col4:
    st.metric("Total Queries", stats.get('total_queries', 0))

st.markdown("---")

# Query statistics
st.subheader("📈 Query Statistics")

col1, col2 = st.columns(2)

with col1:
    avg_response_time = stats.get('avg_response_time', 0)
    st.metric("Avg Response Time", f"{avg_response_time:.3f}s")

with col2:
    st.metric("Active Sessions", stats.get('total_sessions', 0))

# Recent queries
st.subheader("🕐 Recent Queries")

queries = metadata_store.get_queries(limit=10)

if queries:
    df = pd.DataFrame(queries)
    df = df[['query_text', 'query_date', 'response_time']]
    df.columns = ['Query', 'Date', 'Response Time (s)']
    st.dataframe(df, use_container_width=True)
else:
    st.info("No queries yet.")

# Document breakdown
st.subheader("📚 Document Breakdown")

documents = metadata_store.get_all_documents()

if documents:
    df_docs = pd.DataFrame(documents)
    
    # Status distribution
    status_counts = df_docs['status'].value_counts()
    st.bar_chart(status_counts)
    
    # Documents table
    st.dataframe(
        df_docs[['filename', 'num_pages', 'num_chunks', 'status', 'upload_date']],
        use_container_width=True
    )
else:
    st.info("No documents uploaded yet.")
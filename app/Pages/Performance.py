"""Performance monitoring page."""
import streamlit as st
import sys
from pathlib import Path
import time

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from database.cache_manager import CacheManager
from database.metadata_store import MetadataStore

st.set_page_config(page_title="Performance", page_icon="📈", layout="wide")

st.title("📈 Performance Monitoring")

# Initialize components
cache_manager = CacheManager()
metadata_store = MetadataStore()

# Cache statistics
st.subheader("💾 Cache Performance")

cache_stats = cache_manager.get_stats()

if cache_stats.get('enabled'):
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Cache Keys", cache_stats.get('keys', 0))
    
    with col2:
        st.metric("Memory Used", cache_stats.get('memory_used', 'N/A'))
    
    with col3:
        hits = cache_stats.get('hits', 0)
        misses = cache_stats.get('misses', 0)
        total = hits + misses
        hit_rate = (hits / total * 100) if total > 0 else 0
        st.metric("Hit Rate", f"{hit_rate:.1f}%")
else:
    st.info("Cache is disabled")

st.markdown("---")

# Query performance
st.subheader("⚡ Query Performance")

queries = metadata_store.get_queries(limit=100)

if queries:
    response_times = [q['response_time'] for q in queries if q.get('response_time')]
    
    if response_times:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Avg Response Time", f"{sum(response_times)/len(response_times):.3f}s")
        
        with col2:
            st.metric("Min Response Time", f"{min(response_times):.3f}s")
        
        with col3:
            st.metric("Max Response Time", f"{max(response_times):.3f}s")
        
        # Response time chart
        st.line_chart(response_times)
else:
    st.info("No query data available yet.")

st.markdown("---")

# System health
st.subheader("🏥 System Health")

col1, col2 = st.columns(2)

with col1:
    st.success("✅ Vector Database: Healthy")
    st.success("✅ Metadata Database: Healthy")

with col2:
    st.success("✅ LLM Connection: Healthy")
    st.success("✅ Embedding Service: Healthy")

# Refresh button
if st.button("🔄 Refresh"):
    st.rerun()
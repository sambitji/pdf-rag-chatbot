"""Source viewer component."""
import streamlit as st


def render_source_viewer(sources):
    """Render source documents."""
    st.subheader("📖 Retrieved Sources")
    
    if not sources:
        st.info("No sources to display.")
        return
    
    for idx, source in enumerate(sources, 1):
        with st.expander(f"📄 Source {idx} - Page {source.get('page', 'N/A')}", expanded=(idx==1)):
            st.markdown(f"**Document:** {source.get('source', 'Unknown')}")
            st.markdown(f"**Page:** {source.get('page', 'N/A')}")
            
            st.markdown("**Content Preview:**")
            content = source.get('content', '')
            st.text_area(
                "Content",
                value=content,
                height=200,
                key=f"source_{idx}",
                label_visibility="collapsed"
            )
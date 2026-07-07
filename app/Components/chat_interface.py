"""Chat interface component."""
import streamlit as st


def render_chat_interface(chat_history):
    """Render chat interface."""
    st.subheader("💬 Conversation")
    
    for idx, chat in enumerate(chat_history):
        # User message
        st.markdown(f"""
        <div style='background-color: #e3f2fd; padding: 1rem; border-radius: 10px; margin: 0.5rem 0;'>
            <strong>You:</strong> {chat['question']}
        </div>
        """, unsafe_allow_html=True)
        
        # Assistant message
        st.markdown(f"""
        <div style='background-color: #f5f5f5; padding: 1rem; border-radius: 10px; margin: 0.5rem 0;'>
            <strong>Assistant:</strong> {chat['answer']}
        </div>
        """, unsafe_allow_html=True)
        
        # Sources
        if chat.get('pages'):
            st.caption(f"📄 Sources: Pages {', '.join(map(str, chat['pages']))}")
        
        st.markdown("---")
"""File manager component."""
import streamlit as st
from pathlib import Path


def render_file_manager(processed_files, metadata_store, rag_pipeline):
    """Render file manager."""
    st.subheader("📁 Document Manager")
    
    if not processed_files:
        st.info("No documents uploaded yet.")
        return
    
    # Get all documents
    documents = metadata_store.get_all_documents()
    
    # Display in table
    if documents:
        for doc in documents:
            col1, col2, col3 = st.columns([3, 1, 1])
            
            with col1:
                st.text(doc['filename'])
            
            with col2:
                status_color = {
                    'completed': '🟢',
                    'pending': '🟡',
                    'failed': '🔴'
                }
                st.text(f"{status_color.get(doc['status'], '⚪')} {doc['status']}")
            
            with col3:
                if st.button("🗑️", key=f"delete_{doc['id']}"):
                    try:
                        # 1. Delete metadata
                        doc_id = doc['id']
                        filename = doc['filename']
                        deleted_doc = metadata_store.delete_document(doc_id)
                        
                        if deleted_doc:
                            # 2. Delete vectors and update pipeline state
                            rag_pipeline.delete_document(filename)
                            
                            # 3. Delete physical file
                            file_path = Path(deleted_doc['file_path'])
                            if file_path.exists():
                                file_path.unlink()
                                
                            # 4. Remove from processed_files list in session state
                            if filename in processed_files:
                                processed_files.remove(filename)
                                
                            st.success(f"Deleted {filename}!")
                            st.rerun()
                    except Exception as e:
                        st.error(f"Error deleting document: {e}")
            
            st.markdown(f"*Pages: {doc.get('num_pages', 'N/A')} | Chunks: {doc.get('num_chunks', 'N/A')}*")
            st.markdown("---")
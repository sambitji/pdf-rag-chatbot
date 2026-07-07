"""Metadata database for document tracking."""
import sqlite3
import contextlib
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path
from passlib.context import CryptContext
from utils.config import config
from utils.logger import get_logger
from utils.error_handlers import DatabaseError

logger = get_logger(__name__)


class MetadataStore:
    """SQLite database for document metadata."""
    
    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize metadata store.
        
        Args:
            db_path: Path to SQLite database
        """
        self.db_path = db_path or config.metadata_db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._create_tables()
        
        logger.info(f"Initialized metadata store: {self.db_path}")
    
    @contextlib.contextmanager
    def _get_conn(self):
        """Get thread-safe connection context."""
        conn = sqlite3.connect(
            str(self.db_path),
            check_same_thread=False,
            timeout=30.0
        )
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    @property
    def conn(self):
        """Deprecate direct conn access but keep fallback for safety."""
        logger.warning("Direct conn access is deprecated. Use encapsulated methods instead.")
        return sqlite3.connect(str(self.db_path), check_same_thread=False)

    def _create_tables(self):
        """Create database tables."""
        try:
            with self._get_conn() as conn:
                cursor = conn.cursor()
                
                # Documents table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS documents (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        filename TEXT NOT NULL,
                        file_path TEXT NOT NULL,
                        file_hash TEXT NOT NULL UNIQUE,
                        file_size INTEGER,
                        file_type TEXT,
                        num_pages INTEGER,
                        num_chunks INTEGER,
                        upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        processed_date TIMESTAMP,
                        status TEXT DEFAULT 'pending',
                        metadata TEXT
                    )
                """)
                
                # Chunks table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS chunks (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        document_id INTEGER,
                        chunk_index INTEGER,
                        chunk_text TEXT,
                        chunk_size INTEGER,
                        vector_id TEXT,
                        metadata TEXT,
                        created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (document_id) REFERENCES documents (id)
                    )
                """)
                
                # Queries table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS queries (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        query_text TEXT NOT NULL,
                        response TEXT,
                        sources TEXT,
                        query_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        response_time REAL,
                        tokens_used INTEGER,
                        session_id TEXT
                    )
                """)
                
                # Sessions table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS sessions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        session_id TEXT UNIQUE NOT NULL,
                        created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        num_queries INTEGER DEFAULT 0
                    )
                """)
                
                # Users table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE NOT NULL,
                        hashed_password TEXT NOT NULL,
                        email TEXT,
                        full_name TEXT,
                        created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                conn.commit()
                
                # Seed default admin user if users table is empty
                cursor.execute("SELECT COUNT(*) as count FROM users")
                if cursor.fetchone()['count'] == 0:
                    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
                    hashed = pwd_context.hash("admin123")
                    cursor.execute("""
                        INSERT INTO users (username, hashed_password, email, full_name)
                        VALUES (?, ?, ?, ?)
                    """, ("admin", hashed, "admin@example.com", "Admin User"))
                    conn.commit()
                    logger.info("Created default admin user")
                
                logger.info("Database tables created/verified")
            
        except Exception as e:
            logger.error(f"Error creating tables: {e}")
            raise DatabaseError(f"Failed to create tables: {e}")
    
    def add_user(
        self,
        username: str,
        hashed_password: str,
        email: Optional[str] = None,
        full_name: Optional[str] = None
    ) -> int:
        """Add a new user."""
        try:
            with self._get_conn() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO users (username, hashed_password, email, full_name)
                    VALUES (?, ?, ?, ?)
                """, (username, hashed_password, email, full_name))
                conn.commit()
                return cursor.lastrowid
        except sqlite3.IntegrityError:
            logger.warning(f"User already exists: {username}")
            raise DatabaseError(f"Username '{username}' already exists")
        except Exception as e:
            logger.error(f"Error adding user: {e}")
            raise DatabaseError(f"Failed to add user: {e}")
            
    def get_user_by_username(self, username: str) -> Optional[Dict]:
        """Get user by username."""
        try:
            with self._get_conn() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            logger.error(f"Error retrieving user {username}: {e}")
            return None

    def add_document(
        self,
        filename: str,
        file_path: str,
        file_hash: str,
        file_size: int,
        file_type: str,
        num_pages: int = 0,
        metadata: Optional[Dict] = None
    ) -> int:
        """Add document record."""
        try:
            with self._get_conn() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO documents 
                    (filename, file_path, file_hash, file_size, file_type, num_pages, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    filename,
                    file_path,
                    file_hash,
                    file_size,
                    file_type,
                    num_pages,
                    str(metadata) if metadata else None
                ))
                
                conn.commit()
                doc_id = cursor.lastrowid
                
                logger.info(f"Added document record: {filename} (ID: {doc_id})")
                return doc_id
                
        except sqlite3.IntegrityError:
            logger.warning(f"Document already exists: {file_hash}")
            doc = self.get_document_by_hash(file_hash)
            return doc['id'] if doc else -1
        except Exception as e:
            logger.error(f"Error adding document: {e}")
            raise DatabaseError(f"Failed to add document: {e}")
    
    def update_document_status(
        self,
        doc_id: int,
        status: str,
        num_chunks: int = None
    ):
        """Update document processing status."""
        try:
            with self._get_conn() as conn:
                cursor = conn.cursor()
                
                if num_chunks is not None:
                    cursor.execute("""
                        UPDATE documents 
                        SET status = ?, num_chunks = ?, processed_date = CURRENT_TIMESTAMP
                        WHERE id = ?
                    """, (status, num_chunks, doc_id))
                else:
                    cursor.execute("""
                        UPDATE documents 
                        SET status = ?, processed_date = CURRENT_TIMESTAMP
                        WHERE id = ?
                    """, (status, doc_id))
                
                conn.commit()
                logger.info(f"Updated document {doc_id} status: {status}")
            
        except Exception as e:
            logger.error(f"Error updating document status: {e}")
    
    def get_document(self, doc_id: int) -> Optional[Dict]:
        """Get document details by ID."""
        try:
            with self._get_conn() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM documents WHERE id = ?", (doc_id,))
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            logger.error(f"Error getting document {doc_id}: {e}")
            return None

    def delete_document(self, doc_id: int) -> Optional[Dict]:
        """Delete a document from metadata store and return its details."""
        try:
            with self._get_conn() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM documents WHERE id = ?", (doc_id,))
                row = cursor.fetchone()
                if not row:
                    return None
                doc_dict = dict(row)
                
                # Delete related chunks
                cursor.execute("DELETE FROM chunks WHERE document_id = ?", (doc_id,))
                
                # Delete document record
                cursor.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
                conn.commit()
                
                logger.info(f"Deleted document {doc_id} metadata and chunks records")
                return doc_dict
        except Exception as e:
            logger.error(f"Error deleting document {doc_id}: {e}")
            raise DatabaseError(f"Failed to delete document: {e}")

    def get_document_by_hash(self, file_hash: str) -> Optional[Dict]:
        """Get document by file hash."""
        try:
            with self._get_conn() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM documents WHERE file_hash = ?", (file_hash,))
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            logger.error(f"Error getting document by hash: {e}")
            return None
    
    def get_all_documents(self) -> List[Dict]:
        """Get all documents."""
        try:
            with self._get_conn() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM documents ORDER BY upload_date DESC")
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error getting all documents: {e}")
            return []
    
    def add_query(
        self,
        query_text: str,
        response: str,
        sources: List[int],
        response_time: float,
        tokens_used: int = 0,
        session_id: str = None
    ) -> int:
        """Log query and response."""
        try:
            with self._get_conn() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO queries 
                    (query_text, response, sources, response_time, tokens_used, session_id)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    query_text,
                    response,
                    str(sources),
                    response_time,
                    tokens_used,
                    session_id
                ))
                
                conn.commit()
                return cursor.lastrowid
            
        except Exception as e:
            logger.error(f"Error logging query: {e}")
            return -1
    
    def get_queries(self, limit: int = 100) -> List[Dict]:
        """Get recent queries."""
        try:
            with self._get_conn() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM queries 
                    ORDER BY query_date DESC 
                    LIMIT ?
                """, (limit,))
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error getting queries: {e}")
            return []
            
    def get_query_history(self, session_id: str, limit: int = 10) -> List[Dict]:
        """Get query history for session."""
        try:
            with self._get_conn() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM queries 
                    WHERE session_id = ? 
                    ORDER BY query_date DESC 
                    LIMIT ?
                """, (session_id, limit))
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error getting query history for session {session_id}: {e}")
            return []

    def get_session(self, session_id: str) -> Optional[Dict]:
        """Get session info."""
        try:
            with self._get_conn() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM sessions WHERE session_id = ?", (session_id,))
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            logger.error(f"Error getting session {session_id}: {e}")
            return None
    
    def create_session(self, session_id: str) -> int:
        """Create new session."""
        try:
            with self._get_conn() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO sessions (session_id)
                    VALUES (?)
                """, (session_id,))
                conn.commit()
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"Error creating session: {e}")
            return -1
    
    def update_session_activity(self, session_id: str):
        """Update session last activity."""
        try:
            with self._get_conn() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE sessions 
                    SET last_activity = CURRENT_TIMESTAMP,
                        num_queries = num_queries + 1
                    WHERE session_id = ?
                """, (session_id,))
                conn.commit()
        except Exception as e:
            logger.error(f"Error updating session activity: {e}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get database statistics."""
        try:
            with self._get_conn() as conn:
                cursor = conn.cursor()
                
                stats = {}
                
                # Document stats
                cursor.execute("SELECT COUNT(*) as count FROM documents")
                stats['total_documents'] = cursor.fetchone()['count']
                
                cursor.execute("SELECT COUNT(*) as count FROM documents WHERE status = 'completed'")
                stats['processed_documents'] = cursor.fetchone()['count']
                
                cursor.execute("SELECT SUM(num_chunks) as total FROM documents")
                stats['total_chunks'] = cursor.fetchone()['total'] or 0
                
                # Query stats
                cursor.execute("SELECT COUNT(*) as count FROM queries")
                stats['total_queries'] = cursor.fetchone()['count']
                
                cursor.execute("SELECT AVG(response_time) as avg FROM queries")
                stats['avg_response_time'] = cursor.fetchone()['avg'] or 0
                
                # Session stats
                cursor.execute("SELECT COUNT(*) as count FROM sessions")
                stats['total_sessions'] = cursor.fetchone()['count']
                
                return stats
                
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {}
    
    def close(self):
        """No-op database connection close since we use session connection context manager."""
        pass
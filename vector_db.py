"""
Vector database integration for ProjectPrompt to improve file selection and semantic search.
This module provides functionality to:
1. Create embeddings for project files
2. Store and retrieve embeddings from a lightweight vector database
3. Execute semantic similarity searches across the codebase
"""

import os
import re
import json
import numpy as np
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Union
import logging
from logger_config import logger

# Try to import vector database dependencies
try:
    import chromadb
    from chromadb.utils import embedding_functions
    CHROMADB_AVAILABLE = True
    logger.info("ChromaDB available: Using vector database for semantic file analysis")
except ImportError:
    CHROMADB_AVAILABLE = False
    logger.warning("ChromaDB not available. Semantic search functionality will be disabled.")
    logger.warning("To enable, install: pip install chromadb")

# Try to import embedding model dependencies
try:
    from sentence_transformers import SentenceTransformer
    EMBEDDINGS_AVAILABLE = True
    DEFAULT_MODEL = "all-MiniLM-L6-v2"  # Lightweight model with good performance
    logger.info(f"SentenceTransformers available: Using {DEFAULT_MODEL} for embeddings")
except ImportError:
    EMBEDDINGS_AVAILABLE = False
    DEFAULT_MODEL = None
    logger.warning("SentenceTransformers not available. Will use basic embedding or API if available.")
    logger.warning("To enable local embeddings, install: pip install sentence-transformers")

# Try to use Google's Generative AI for embeddings as fallback
try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
    logger.info("Google GenerativeAI available: Can use as fallback for embeddings")
except ImportError:
    GENAI_AVAILABLE = False
    logger.warning("Google GenerativeAI not available. Fallback embedding API not available.")


class VectorDatabaseManager:
    """Manages vector embeddings and similarity search for ProjectPrompt files"""
    
    def __init__(self, root_dir: str, api_key: Optional[str] = None, model_name: str = DEFAULT_MODEL):
        """Initialize the vector database manager
        
        Args:
            root_dir: Project root directory
            api_key: Optional API key for Google GenerativeAI
            model_name: Name of the embedding model to use
        """
        self.root_dir = root_dir
        self.api_key = api_key
        self.model_name = model_name
        self.db_path = os.path.join(root_dir, ".projectprompt", "vectordb")
        self.model = None
        self.client = None
        self.collection = None
        self.is_initialized = False
        
        # Create directory for persistent storage
        os.makedirs(self.db_path, exist_ok=True)
        
        # Initialize embedding function based on available libraries
        if EMBEDDINGS_AVAILABLE and self.model_name:
            try:
                self.model = SentenceTransformer(self.model_name)
                logger.info(f"Loaded embedding model: {self.model_name}")
                self.embedding_function = self._get_sentence_transformer_embeddings
            except Exception as e:
                logger.error(f"Failed to load embedding model: {str(e)}")
                self.embedding_function = self._get_fallback_embeddings
        elif GENAI_AVAILABLE and self.api_key:
            # Initialize Google GenerativeAI as fallback
            try:
                genai.configure(api_key=self.api_key)
                logger.info("Using Google GenerativeAI embedding API")
                self.embedding_function = self._get_genai_embeddings
            except Exception as e:
                logger.error(f"Failed to initialize Google GenerativeAI: {str(e)}")
                self.embedding_function = self._get_fallback_embeddings
        else:
            logger.warning("No embedding models available. Using basic keyword-based fallback.")
            self.embedding_function = self._get_fallback_embeddings
        
        # Initialize ChromaDB if available
        if CHROMADB_AVAILABLE:
            try:
                self.client = chromadb.PersistentClient(path=self.db_path)
                # Get or create a new collection
                self.collection = self.client.get_or_create_collection(
                    name="projectprompt_files",
                    metadata={"description": "Project file embeddings for similarity search"}
                )
                self.is_initialized = True
                logger.info("Vector database initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize vector database: {str(e)}")
        else:
            logger.warning("Vector database functionality disabled due to missing dependencies")
    
    def _get_sentence_transformer_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Get embeddings using SentenceTransformers model"""
        try:
            return self.model.encode(texts, convert_to_numpy=True).tolist()
        except Exception as e:
            logger.error(f"Error generating embeddings with SentenceTransformer: {str(e)}")
            return self._get_fallback_embeddings(texts)
    
    def _get_genai_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Get embeddings using Google GenerativeAI API"""
        try:
            embeddings = []
            for text in texts:
                # Truncate if needed (API limit)
                if len(text) > 2048:
                    text = text[:2048]
                result = genai.embed_content(
                    model="models/embedding-001",
                    content=text,
                    task_type="retrieval_document"
                )
                embeddings.append(result["embedding"])
            return embeddings
        except Exception as e:
            logger.error(f"Error generating embeddings with Google GenerativeAI: {str(e)}")
            return self._get_fallback_embeddings(texts)
    
    def _get_fallback_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate very simple embeddings based on keyword frequency
        This is a fallback when no embedding models are available
        """
        logger.warning("Using fallback embedding method (very limited capability)")
        # Define some key programming concepts to track in the embeddings
        keywords = ["class", "function", "def", "import", "export", "const", "var", "let",
                   "return", "if", "else", "for", "while", "try", "catch", "async",
                   "await", "component", "model", "controller", "view", "route",
                   "database", "schema", "api", "http", "request", "response"]
        
        embeddings = []
        for text in texts:
            text = text.lower()
            # Create a simple embedding vector based on keyword frequency
            embedding = [text.count(keyword) for keyword in keywords]
            # Normalize to unit length
            norm = max(np.sqrt(sum([x*x for x in embedding])), 1e-6)
            embedding = [x/norm for x in embedding]
            # Pad to reasonable embedding dimension (64)
            embedding = embedding + [0] * (64 - len(embedding))
            embeddings.append(embedding)
        return embeddings
    
    def add_files(self, file_paths: List[str], file_contents: Dict[str, str]) -> bool:
        """Add files to the vector database
        
        Args:
            file_paths: List of file paths relative to root directory
            file_contents: Dictionary mapping file paths to their contents
            
        Returns:
            bool: Whether the operation was successful
        """
        if not self.is_initialized:
            logger.warning("Vector database not initialized, cannot add files")
            return False
        
        try:
            # Prepare data for the vector database
            ids = [f"file_{i}" for i in range(len(file_paths))]
            metadatas = [{"path": path, "type": "file"} for path in file_paths]
            documents = [file_contents.get(path, "") for path in file_paths]
            
            # Generate embeddings
            embeddings = self.embedding_function(documents)
            
            # Add to collection
            self.collection.add(
                ids=ids,
                embeddings=embeddings,
                metadatas=metadatas,
                documents=documents
            )
            logger.info(f"Added {len(file_paths)} files to vector database")
            return True
        except Exception as e:
            logger.error(f"Error adding files to vector database: {str(e)}")
            return False
    
    def query_similar_files(self, query: str, n_results: int = 10) -> List[Dict]:
        """Find files similar to the query
        
        Args:
            query: The query text to find similar files
            n_results: Number of results to return
            
        Returns:
            List of dictionaries with file paths and similarity scores
        """
        if not self.is_initialized:
            logger.warning("Vector database not initialized, cannot query")
            return []
        
        try:
            # Generate embedding for the query
            query_embedding = self.embedding_function([query])[0]
            
            # Query the collection
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                include=["metadatas", "distances"]
            )
            
            # Format results
            similar_files = []
            if results and 'metadatas' in results and len(results['metadatas']) > 0:
                for i, metadata in enumerate(results['metadatas'][0]):
                    distance = results['distances'][0][i] if 'distances' in results else 1.0
                    similarity = 1.0 - min(distance, 1.0)  # Convert distance to similarity
                    similar_files.append({
                        "path": metadata["path"],
                        "similarity": similarity
                    })
                    
            logger.info(f"Found {len(similar_files)} files similar to query: {query[:30]}...")
            return similar_files
        except Exception as e:
            logger.error(f"Error querying vector database: {str(e)}")
            return []
    
    def get_related_files(self, file_path: str, n_results: int = 5) -> List[Dict]:
        """Find files related to a given file
        
        Args:
            file_path: Path to the file to find related files for
            n_results: Number of results to return
            
        Returns:
            List of dictionaries with file paths and similarity scores
        """
        if not self.is_initialized:
            logger.warning("Vector database not initialized, cannot find related files")
            return []
        
        try:
            # Query by file path in metadata
            results = self.collection.query(
                query_texts=[file_path],
                n_results=n_results + 1,  # Add 1 to account for the file itself
                include=["metadatas", "documents", "distances"],
                where={"type": "file"}
            )
            
            # Format results, excluding the queried file itself
            related_files = []
            if results and 'metadatas' in results and len(results['metadatas']) > 0:
                for i, metadata in enumerate(results['metadatas'][0]):
                    if metadata["path"] != file_path:
                        distance = results['distances'][0][i] if 'distances' in results else 1.0
                        similarity = 1.0 - min(distance, 1.0)  # Convert distance to similarity
                        related_files.append({
                            "path": metadata["path"],
                            "similarity": similarity
                        })
            
            logger.info(f"Found {len(related_files)} files related to {file_path}")
            return related_files
        except Exception as e:
            logger.error(f"Error finding related files: {str(e)}")
            return []
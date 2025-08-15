"""
Text embeddings client for semantic search and similarity analysis.
Enables semantic analysis of market news, trading strategies, and user queries.
"""

import asyncio
import logging
import numpy as np
from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Union, Tuple
from datetime import datetime
import json


@dataclass
class EmbeddingsConfig:
    """Configuration for text embeddings."""
    model_name: str = "text-embedding-ada-002"
    provider: str = "openai"  # openai, huggingface, local
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    max_input_length: int = 8192
    batch_size: int = 100
    timeout: int = 30
    retry_attempts: int = 3
    normalize_embeddings: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return {
            'model_name': self.model_name,
            'provider': self.provider,
            'api_key': self.api_key,
            'base_url': self.base_url,
            'max_input_length': self.max_input_length,
            'batch_size': self.batch_size,
            'timeout': self.timeout,
            'retry_attempts': self.retry_attempts,
            'normalize_embeddings': self.normalize_embeddings
        }


@dataclass
class EmbeddingsResponse:
    """Response from embeddings generation."""
    embeddings: List[List[float]]
    model: str
    usage: Dict[str, int]
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert response to dictionary."""
        return {
            'embeddings': self.embeddings,
            'model': self.model,
            'usage': self.usage,
            'timestamp': self.timestamp.isoformat(),
            'metadata': self.metadata or {}
        }


class TextEmbeddingsClient:
    """
    Text embeddings client for semantic search and similarity analysis.
    
    Provides capabilities for:
    - Generating embeddings for market news and analysis
    - Semantic search across trading strategies
    - Similarity analysis for pattern matching
    - Clustering of market sentiment data
    """
    
    def __init__(self, config: EmbeddingsConfig, logger: Optional[logging.Logger] = None):
        """
        Initialize embeddings client.
        
        Args:
            config: Embeddings configuration
            logger: Optional logger instance
        """
        self.config = config
        self.logger = logger or logging.getLogger(__name__)
        self._client = None
        self._model = None
        self._initialized = False
        self._embedding_dimension = None
    
    async def initialize(self) -> bool:
        """
        Initialize the embeddings client.
        
        Returns:
            True if initialization successful, False otherwise
        """
        try:
            self.logger.info(f"Initializing embeddings client: {self.config.provider}/{self.config.model_name}")
            
            if self.config.provider == "openai":
                await self._initialize_openai()
            elif self.config.provider == "huggingface":
                await self._initialize_huggingface()
            elif self.config.provider == "local":
                await self._initialize_local()
            else:
                raise ValueError(f"Unsupported provider: {self.config.provider}")
            
            # Determine embedding dimension
            self._embedding_dimension = await self._get_embedding_dimension()
            
            self._initialized = True
            self.logger.info(f"Embeddings client initialized successfully (dimension: {self._embedding_dimension})")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize embeddings client: {e}")
            return False
    
    async def generate_embeddings(
        self, 
        texts: Union[str, List[str]],
        **kwargs
    ) -> EmbeddingsResponse:
        """
        Generate embeddings for text(s).
        
        Args:
            texts: Single text or list of texts to embed
            **kwargs: Additional provider-specific parameters
            
        Returns:
            EmbeddingsResponse containing embeddings and metadata
        """
        if not self._initialized:
            raise RuntimeError("Embeddings client not initialized")
        
        # Normalize input to list
        if isinstance(texts, str):
            texts = [texts]
        
        # Validate input length
        for text in texts:
            if len(text) > self.config.max_input_length:
                raise ValueError(f"Text too long: {len(text)} > {self.config.max_input_length}")
        
        try:
            self.logger.info(f"Generating embeddings for {len(texts)} text(s)")
            
            # Process in batches if necessary
            all_embeddings = []
            total_tokens = 0
            
            for i in range(0, len(texts), self.config.batch_size):
                batch = texts[i:i + self.config.batch_size]
                batch_embeddings, batch_tokens = await self._generate_batch_embeddings(batch, **kwargs)
                all_embeddings.extend(batch_embeddings)
                total_tokens += batch_tokens
            
            return EmbeddingsResponse(
                embeddings=all_embeddings,
                model=self.config.model_name,
                usage={
                    'prompt_tokens': total_tokens,
                    'total_tokens': total_tokens
                },
                timestamp=datetime.now(),
                metadata={
                    'provider': self.config.provider,
                    'embedding_dimension': self._embedding_dimension,
                    'batch_count': (len(texts) + self.config.batch_size - 1) // self.config.batch_size,
                    'normalized': self.config.normalize_embeddings
                }
            )
            
        except Exception as e:
            self.logger.error(f"Failed to generate embeddings: {e}")
            raise
    
    async def embed_market_news(
        self, 
        news_articles: List[Dict[str, Any]]
    ) -> EmbeddingsResponse:
        """
        Generate embeddings for market news articles.
        
        Args:
            news_articles: List of news articles with title and content
            
        Returns:
            EmbeddingsResponse for news articles
        """
        # Combine title and content for each article
        texts = []
        for article in news_articles:
            title = article.get('title', '')
            content = article.get('content', '')
            summary = article.get('summary', '')
            
            # Create combined text for embedding
            combined_text = f"Title: {title}\n"
            if summary:
                combined_text += f"Summary: {summary}\n"
            if content:
                combined_text += f"Content: {content}"
            
            texts.append(combined_text.strip())
        
        response = await self.generate_embeddings(texts)
        response.metadata['content_type'] = 'market_news'
        response.metadata['article_count'] = len(news_articles)
        
        return response
    
    async def embed_trading_strategies(
        self, 
        strategies: List[Dict[str, Any]]
    ) -> EmbeddingsResponse:
        """
        Generate embeddings for trading strategies.
        
        Args:
            strategies: List of trading strategies with descriptions
            
        Returns:
            EmbeddingsResponse for trading strategies
        """
        texts = []
        for strategy in strategies:
            name = strategy.get('name', '')
            description = strategy.get('description', '')
            rules = strategy.get('rules', [])
            
            # Create combined text for embedding
            combined_text = f"Strategy: {name}\n"
            if description:
                combined_text += f"Description: {description}\n"
            if rules:
                combined_text += f"Rules: {'; '.join(rules)}"
            
            texts.append(combined_text.strip())
        
        response = await self.generate_embeddings(texts)
        response.metadata['content_type'] = 'trading_strategies'
        response.metadata['strategy_count'] = len(strategies)
        
        return response
    
    async def semantic_search(
        self, 
        query: str,
        document_embeddings: List[List[float]],
        documents: List[str],
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Perform semantic search using embeddings.
        
        Args:
            query: Search query
            document_embeddings: Pre-computed document embeddings
            documents: Original documents corresponding to embeddings
            top_k: Number of top results to return
            
        Returns:
            List of search results with similarity scores
        """
        # Generate query embedding
        query_response = await self.generate_embeddings(query)
        query_embedding = query_response.embeddings[0]
        
        # Calculate similarities
        similarities = []
        for i, doc_embedding in enumerate(document_embeddings):
            similarity = self._cosine_similarity(query_embedding, doc_embedding)
            similarities.append({
                'index': i,
                'document': documents[i],
                'similarity': similarity
            })
        
        # Sort by similarity and return top_k
        similarities.sort(key=lambda x: x['similarity'], reverse=True)
        return similarities[:top_k]
    
    async def find_similar_strategies(
        self, 
        target_strategy: Dict[str, Any],
        strategy_embeddings: List[List[float]],
        strategies: List[Dict[str, Any]],
        threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Find similar trading strategies using embeddings.
        
        Args:
            target_strategy: Strategy to find similarities for
            strategy_embeddings: Pre-computed strategy embeddings
            strategies: Original strategies
            threshold: Similarity threshold
            
        Returns:
            List of similar strategies with similarity scores
        """
        # Generate embedding for target strategy
        target_response = await self.embed_trading_strategies([target_strategy])
        target_embedding = target_response.embeddings[0]
        
        # Find similar strategies
        similar_strategies = []
        for i, strategy_embedding in enumerate(strategy_embeddings):
            similarity = self._cosine_similarity(target_embedding, strategy_embedding)
            
            if similarity >= threshold:
                similar_strategies.append({
                    'strategy': strategies[i],
                    'similarity': similarity,
                    'index': i
                })
        
        # Sort by similarity
        similar_strategies.sort(key=lambda x: x['similarity'], reverse=True)
        return similar_strategies
    
    async def cluster_market_sentiment(
        self, 
        sentiment_texts: List[str],
        n_clusters: int = 5
    ) -> Dict[str, Any]:
        """
        Cluster market sentiment texts using embeddings.
        
        Args:
            sentiment_texts: List of sentiment texts to cluster
            n_clusters: Number of clusters to create
            
        Returns:
            Clustering results with cluster assignments
        """
        # Generate embeddings
        response = await self.generate_embeddings(sentiment_texts)
        embeddings = np.array(response.embeddings)
        
        # Perform clustering (simplified k-means simulation)
        clusters = await self._perform_clustering(embeddings, n_clusters)
        
        # Organize results
        cluster_results = {
            'clusters': {},
            'cluster_centers': clusters['centers'],
            'assignments': clusters['assignments'],
            'metadata': {
                'n_clusters': n_clusters,
                'n_texts': len(sentiment_texts),
                'embedding_dimension': self._embedding_dimension
            }
        }
        
        # Group texts by cluster
        for i, cluster_id in enumerate(clusters['assignments']):
            if cluster_id not in cluster_results['clusters']:
                cluster_results['clusters'][cluster_id] = []
            cluster_results['clusters'][cluster_id].append({
                'text': sentiment_texts[i],
                'index': i
            })
        
        return cluster_results
    
    async def _initialize_openai(self):
        """Initialize OpenAI embeddings client."""
        if not self.config.api_key:
            raise ValueError("OpenAI API key required")
        
        # In a real implementation, initialize OpenAI client
        self.logger.info("OpenAI embeddings client initialized")
    
    async def _initialize_huggingface(self):
        """Initialize Hugging Face embeddings client."""
        # In a real implementation, load Hugging Face model
        self.logger.info("Hugging Face embeddings client initialized")
    
    async def _initialize_local(self):
        """Initialize local embeddings model."""
        # In a real implementation, load local model
        self.logger.info("Local embeddings model initialized")
    
    async def _get_embedding_dimension(self) -> int:
        """Get the dimension of embeddings from the model."""
        # Test with a simple text to get dimension
        test_response = await self._generate_batch_embeddings(["test"])
        return len(test_response[0][0])
    
    async def _generate_batch_embeddings(
        self, 
        texts: List[str], 
        **kwargs
    ) -> Tuple[List[List[float]], int]:
        """Generate embeddings for a batch of texts."""
        # Simulate embedding generation
        await asyncio.sleep(0.1)  # Simulate API call
        
        # Generate mock embeddings (in real implementation, use actual model)
        embeddings = []
        for text in texts:
            # Create deterministic but varied embeddings based on text
            embedding = self._generate_mock_embedding(text)
            if self.config.normalize_embeddings:
                embedding = self._normalize_embedding(embedding)
            embeddings.append(embedding)
        
        # Calculate token usage (approximate)
        total_tokens = sum(len(text.split()) for text in texts)
        
        return embeddings, total_tokens
    
    def _generate_mock_embedding(self, text: str) -> List[float]:
        """Generate mock embedding for testing purposes."""
        # Create a deterministic embedding based on text hash
        import hashlib
        
        # Use text hash to create consistent embeddings
        text_hash = hashlib.md5(text.encode()).hexdigest()
        
        # Convert hash to numbers and create 1536-dimensional embedding (OpenAI standard)
        embedding = []
        for i in range(0, len(text_hash), 2):
            hex_pair = text_hash[i:i+2]
            value = int(hex_pair, 16) / 255.0 - 0.5  # Normalize to [-0.5, 0.5]
            embedding.append(value)
        
        # Pad or truncate to 1536 dimensions
        target_dim = 1536
        while len(embedding) < target_dim:
            embedding.extend(embedding[:min(len(embedding), target_dim - len(embedding))])
        
        return embedding[:target_dim]
    
    def _normalize_embedding(self, embedding: List[float]) -> List[float]:
        """Normalize embedding to unit length."""
        embedding_array = np.array(embedding)
        norm = np.linalg.norm(embedding_array)
        if norm > 0:
            return (embedding_array / norm).tolist()
        return embedding
    
    def _cosine_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Calculate cosine similarity between two embeddings."""
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)
        
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    async def _perform_clustering(
        self, 
        embeddings: np.ndarray, 
        n_clusters: int
    ) -> Dict[str, Any]:
        """Perform clustering on embeddings (simplified implementation)."""
        # Simplified k-means clustering simulation
        n_samples, n_features = embeddings.shape
        
        # Random initialization of cluster centers
        np.random.seed(42)  # For reproducibility
        centers = np.random.randn(n_clusters, n_features)
        
        # Assign each point to nearest cluster
        assignments = []
        for embedding in embeddings:
            distances = [np.linalg.norm(embedding - center) for center in centers]
            cluster_id = np.argmin(distances)
            assignments.append(cluster_id)
        
        return {
            'centers': centers.tolist(),
            'assignments': assignments
        }
    
    def is_initialized(self) -> bool:
        """Check if embeddings client is initialized."""
        return self._initialized
    
    def get_embedding_dimension(self) -> Optional[int]:
        """Get the dimension of embeddings."""
        return self._embedding_dimension
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get embeddings model information."""
        return {
            'model_name': self.config.model_name,
            'provider': self.config.provider,
            'initialized': self._initialized,
            'embedding_dimension': self._embedding_dimension,
            'config': self.config.to_dict()
        }
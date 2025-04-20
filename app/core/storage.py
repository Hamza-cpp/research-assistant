import os
import pinecone
from datetime import datetime

class PineconeStorage:
    """Class to store and retrieve article summaries using Pinecone"""
    
    def __init__(self, index_name):
        """Initialize the Pinecone storage with the specified index"""
        api_key = os.environ.get("PINECONE_API_KEY")
        environment = os.environ.get("PINECONE_ENVIRONMENT")
        
        if not api_key or not environment:
            raise ValueError("Pinecone API key and environment must be set")
        
        # Initialize Pinecone
        pinecone.init(api_key=api_key, environment=environment)
        
        # Check if the index exists, create it if not
        if index_name not in pinecone.list_indexes():
            pinecone.create_index(
                name=index_name,
                dimension=1536,  # Dimensions for OpenAI embeddings
                metric="cosine"
            )
        
        # Connect to the index
        self.index = pinecone.Index(index_name)
    
    def store_summary(self, article_id, source, title, summary, key_concepts, embedding):
        """
        Store an article summary in Pinecone
        
        Args:
            article_id: Unique identifier for the article
            source: Source of the article (arxiv, hal)
            title: Title of the article
            summary: Summary text
            key_concepts: List of key concepts
            embedding: Vector embedding of the article
        """
        # Create a unique ID for the record
        record_id = f"{source}_{article_id}"
        
        # Create metadata
        metadata = {
            'article_id': article_id,
            'source': source,
            'title': title,
            'summary': summary,
            'key_concepts': ','.join(key_concepts),
            'timestamp': datetime.now().isoformat()
        }
        
        # Upsert the record
        self.index.upsert(
            vectors=[(record_id, embedding, metadata)]
        )
        
        return record_id
    
    def search(self, query_embedding, top_k=5):
        """
        Search for similar article summaries
        
        Args:
            query_embedding: Vector embedding of the query
            top_k: Number of results to return
            
        Returns:
            List of matching articles with their metadata
        """
        results = self.index.query(
            vector=query_embedding,
            top_k=top_k,
            include_metadata=True
        )
        
        matches = []
        for match in results['matches']:
            metadata = match['metadata']
            
            # Parse key concepts back to a list
            key_concepts = metadata.get('key_concepts', '').split(',')
            if len(key_concepts) == 1 and key_concepts[0] == '':
                key_concepts = []
            
            matches.append({
                'id': match['id'],
                'score': match['score'],
                'article_id': metadata.get('article_id'),
                'source': metadata.get('source'),
                'title': metadata.get('title'),
                'summary': metadata.get('summary'),
                'key_concepts': key_concepts,
                'timestamp': metadata.get('timestamp')
            })
        
        return matches
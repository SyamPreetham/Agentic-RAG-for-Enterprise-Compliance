import os
import sys
from qdrant_client import QdrantClient
from qdrant_client.http import models

# Force Python to look at the absolute root workspace first
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.config import get_settings

def initialize_compliance_collection():
    settings = get_settings()
    
    print(f"📡 Connecting to Qdrant at {settings.QDRANT_HOST}:{settings.QDRANT_PORT}...")
    # Standardized client instantiation now that the circular import trap is gone
    client = QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT)
    
    collection_name = settings.COMPLIANCE_COLLECTION_NAME
    vector_dim = settings.EMBEDDING_DIM
    
    print(f"🔍 Checking if collection '{collection_name}' already exists...")
    try:
        collections = client.get_collections().collections
        exists = any(c.name == collection_name for c in collections)
    except Exception as e:
        print(f"⚠️ Connection check dropped: {e}")
        exists = False

    if exists:
        print(f"🗑️ Found existing index. Re-allocating layout structures...")
        client.delete_collection(collection_name=collection_name)
        
    print(f"🚀 Allocating pristine vector index: '{collection_name}' ({vector_dim} dimensions)...")
    client.create_collection(
        collection_name=collection_name,
        vectors_config=models.VectorParams(
            size=vector_dim,
            distance=models.Distance.COSINE
        ),
        quantization_config=models.ScalarQuantization(
            scalar=models.ScalarQuantizationConfig(
                type=models.ScalarType.INT8,
                always_ram=True
            )
        )
    )
    print(f"✅ Success! Collection '{collection_name}' successfully initialized.")

if __name__ == "__main__":
    initialize_compliance_collection()
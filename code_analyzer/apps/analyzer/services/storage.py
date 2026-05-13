import os
import chromadb

class Storage:
    '''Stores vector data in chromadb
    '''
    def __init__(self, collection_name: str):
        path = os.path.join(os.getenv("LOCAL_DATA_PATH"), "chromadb")
        os.makedirs(path, exist_ok=True)
        try:
            # Try the newer API first (chromadb >= 0.4.0)
            client = chromadb.PersistentClient(path=path)
        except TypeError:
            # Fallback to older API
            try:
                client = chromadb.Client(
                    chromadb.config.Settings(
                        chroma_db_impl="duckdb+parquet",
                        persist_directory=path,
                        anonymized_telemetry=False
                    )
                )
            except Exception:
                # Last resort - just use default client
                client = chromadb.Client()
        
        self._collection = client.get_or_create_collection(name=collection_name)
        
    def handler(self, data: dict):
        # Skip if no embeddings to add
        if not data.get('embeddings') or len(data['embeddings']) == 0:
            print("WARNING: No embeddings to store")
            return
        
        try:
            self._collection.add(**data)
        except Exception as e:
            print(f"Error adding embeddings to collection: {e}")

    def finder(self, query: dict):
        return self._collection.query(
            query_embeddings=query['embedding'],
            n_results=query['number_of_results']
        )
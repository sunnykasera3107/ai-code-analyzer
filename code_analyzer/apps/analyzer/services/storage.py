import os
import chromadb
import hashlib

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
            insert_items = {
                "ids": [],
                "documents": [],
                "embeddings": [],
                "metadatas": []
            }
            update_items = {
                "ids": [],
                "documents": [],
                "embeddings": [],
                "metadatas": []
            }
            for i, item in enumerate(data['ids']):
                item_hash = self.generate_hash(data['documents'][i])
                existing_doc = self.get_doc([item])
                existing_hash = existing_doc['metadatas']['0']['hash']
                data['metadatas'][i]['hash'] = item_hash
                if item_hash != existing_hash:
                    insert_items["ids"].append(item)
                    insert_items["documents"].append(data['documents'][i])
                    insert_items["metadatas"].append(data['metadatas'][i])
                    insert_items["embeddings"].append(data['embeddings'][i])
                else:
                    update_items["ids"].append(item)
                    update_items["documents"].append(data['documents'][i])
                    update_items["metadatas"].append(data['metadatas'][i])
                    update_items["embeddings"].append(data['embeddings'][i])

                if len(insert_items['ids']) > 0:
                    self._collection.add(**insert_items)
                
                if len(update_items['ids']) > 0:
                    self._collection.update(**update_items)

        except Exception as e:
            print(f"Error adding embeddings to collection: {e}")

    def finder(self, query: dict):
        return self._collection.query(
            query_embeddings=query['embedding'],
            n_results=query['number_of_results']
        )
    
    def get_doc(self, id: list):
        return self._collection.get(
            ids=id,
            include=["metadatas"]
        )
    
    def generate_hash(content: str):
        return hashlib.sha256(
            content.encode("utf-8")
        ).hexdigest()
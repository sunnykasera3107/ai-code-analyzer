
from sentence_transformers import SentenceTransformer

class Embedder:
    '''It will embed chunk of information the input format is customized
    '''
    def __init__(self):
        self._model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        pass

    def handler(self, data: list):
        if not data:
            print("WARNING: No data to embed")
            return {
                "ids": [],
                "documents": [],
                "embeddings": [],
                "metadatas": []
            }
        
        ids = []
        embeddings = []
        documents = []
        metadatas = []
        for item in data:
            if 'chunks' not in item or not item['chunks']:
                print(f"WARNING: No chunks in item: {item.get('file_name', 'unknown')}")
                continue
                
            for chunk in item['chunks']:
                if 'code' not in chunk or not chunk['code']:
                    continue
                    
                embeddings.append(self.encode(chunk['code']))
                documents.append(chunk.pop("code"))
                meta_values = {
                    **chunk,
                    "file_name": item['file_name'],
                    "dependencies": ",".join(item.get('dependencies', [])),
                }
                if "exports" in item:
                    meta_values["exports"] = item['exports']
                
                metadatas.append(meta_values)
                ids.append(f"{item['file_name']}:{chunk["name"]}")

        return {
            "ids": ids,
            "documents": documents,
            "embeddings": embeddings,
            "metadatas": metadatas
        }
    
    def encode(self, data: str):
        return self._model.encode(data)
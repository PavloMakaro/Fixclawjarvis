import os
import time
import hashlib
import traceback
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VectorMemory:
    def __init__(self, table_name="user_facts", persist_path="data/lancedb"):
        self.enabled = False
        self.table = None
        self.model = None

        try:
            import lancedb
            from sentence_transformers import SentenceTransformer

            # Ensure directory exists
            if not os.path.exists(persist_path):
                os.makedirs(persist_path)

            # Initialize LanceDB
            self.db = lancedb.connect(persist_path)
            self.table_name = table_name

            # Initialize Embedding Model (using a small, fast model)
            # This might download the model on first run
            logger.info("Loading embedding model (all-MiniLM-L6-v2)...")
            self.model = SentenceTransformer('all-MiniLM-L6-v2')

            # Open or Create Table
            if table_name in self.db.table_names():
                self.table = self.db.open_table(table_name)
            else:
                # We will create it lazily on first add, or create with a schema now.
                # Let's create lazily to infer schema from first data point,
                # but better to define it if we can.
                # For simplicity, we'll wait for the first add.
                pass

            self.enabled = True
            logger.info(f"Vector Memory (LanceDB) initialized at {persist_path}")

        except ImportError as e:
            logger.error(f"Failed to import lancedb or sentence_transformers: {e}")
            logger.error("Please install dependencies: pip install lancedb sentence-transformers")
            self.enabled = False
        except Exception as e:
            logger.error(f"Vector Memory initialization failed: {e}")
            traceback.print_exc()
            self.enabled = False

    def _get_embedding(self, text):
        if not self.model:
            return None
        return self.model.encode(text).tolist()

    def add(self, text, metadata=None):
        if not self.enabled:
            return "Vector memory not enabled."

        try:
            vector = self._get_embedding(text)
            if not vector:
                return "Failed to generate embedding."

            doc_id = hashlib.md5(f"{text}{time.time()}".encode()).hexdigest()

            data = [{
                "vector": vector,
                "text": text,
                "id": doc_id,
                "metadata": metadata or {}
            }]

            if self.table is None:
                if self.table_name in self.db.table_names():
                     self.table = self.db.open_table(self.table_name)
                     self.table.add(data)
                else:
                    self.table = self.db.create_table(self.table_name, data=data)
            else:
                self.table.add(data)

            return f"Fact stored (ID: {doc_id})"
        except Exception as e:
            logger.error(f"Error adding to vector memory: {e}")
            return f"Error adding to vector memory: {e}"

    def search(self, query, n_results=3):
        if not self.enabled:
            return []

        try:
            if self.table is None:
                if self.table_name in self.db.table_names():
                    self.table = self.db.open_table(self.table_name)
                else:
                    return []

            query_vector = self._get_embedding(query)
            if not query_vector:
                return []

            results = self.table.search(query_vector).limit(n_results).to_list()

            # Format results to match previous interface (list of strings or dicts)
            # The previous implementation returned results["documents"][0] which is a list of strings
            return [r["text"] for r in results]

        except Exception as e:
            logger.error(f"Error searching vector memory: {e}")
            return []

# Singleton instance
memory_instance = VectorMemory()

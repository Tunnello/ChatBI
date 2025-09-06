from langchain.tools.retriever import create_retriever_tool
from langchain.vectorstores import Chroma
from langchain_core.embeddings import Embeddings
import chromadb
ef = chromadb.utils.embedding_functions.DefaultEmbeddingFunction()
import os
current_file_dir = os.path.dirname(os.path.abspath(__file__))
CHROMADB_PATH = os.path.join(current_file_dir, "chroma_langchain_db")

from langchain_community.tools import DuckDuckGoSearchRun
search = DuckDuckGoSearchRun()


class DefChromaEF(Embeddings):
  def __init__(self,ef):
    self.ef = ef

  def embed_documents(self,texts):
    return self.ef(texts)

  def embed_query(self, query):
    return self.ef([query])[0]

embeddings = DefChromaEF(ef)

vector_store = Chroma(
    collection_name="example_collection",
    embedding_function=embeddings,
    persist_directory=CHROMADB_PATH
)

retriever_tool = create_retriever_tool(
    vector_store.as_retriever(),
    name="database_schema_rag",
    description="Search for database schema details",
)
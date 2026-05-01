from typing import Any, Dict

# import streamlit as st
# # from langchain.document_loaders import DirectoryLoader
# from langchain_community.document_loaders import DirectoryLoader
# # from langchain.embeddings.openai import OpenAIEmbeddings
# # from langchain_community.embeddings import OpenAIEmbeddings
# from langchain_community.vectorstores import SupabaseVectorStore
from langchain_community.document_loaders import TextLoader
from langchain.text_splitter import CharacterTextSplitter
# # from langchain.vectorstores import SupabaseVectorStore
from pydantic import BaseModel
from langchain_openai import OpenAIEmbeddings
from langchain_community.document_loaders import DirectoryLoader
from langchain_community.document_loaders import TextLoader
from tqdm import tqdm

# from supabase.client import Client, create_client

from langchain_community.vectorstores import Chroma
from langchain_core.embeddings import Embeddings
import chromadb
ef = chromadb.utils.embedding_functions.DefaultEmbeddingFunction()

import os
current_file_dir = os.path.dirname(os.path.abspath(__file__))
upper_dir        = os.path.dirname(current_file_dir)
DOCS_DIR         = os.path.join(upper_dir, "docs")  # 替换为你的数据库文件路径

class DefChromaEF(Embeddings):
  def __init__(self,ef):
    self.ef = ef

  def embed_documents(self,texts):
    return self.ef(texts)

  def embed_query(self, query):
    return self.ef([query])[0]

embeddings = DefChromaEF(ef)





class Config(BaseModel):
    chunk_size: int = 1000
    chunk_overlap: int = 0
    docs_dir: str = DOCS_DIR
    docs_glob: str = "**/*.md"

class QwenEmbeddings(OpenAIEmbeddings):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.model = "text-embedding-v4"
        self.base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"

    


class DocumentProcessor:
    def __init__(self, config: Config):
        self.loader = DirectoryLoader(config.docs_dir, glob=config.docs_glob, show_progress=True, loader_cls=TextLoader)
        self.text_splitter = CharacterTextSplitter(
            chunk_size=config.chunk_size, chunk_overlap=config.chunk_overlap
        )
        self.embeddings = embeddings
        

    def process(self) -> Dict[str, Any]:
        data = self.loader.load()
        texts = self.text_splitter.split_documents(data)
        # print(texts)
        # 使用绝对路径，统一使用项目根目录的向量数据库
        chromadb_path = os.path.join(upper_dir, "chroma_langchain_db")
        vector_store = Chroma(
            collection_name="example_collection",
            embedding_function=embeddings,
            persist_directory=chromadb_path
        )
        for i in tqdm(range(0, len(texts)), desc="Document Embedding and Saving"):
            vector_store.add_documents([texts[i]])
        return vector_store


def run():
    
    config = Config()
    doc_processor = DocumentProcessor(config)
    result = doc_processor.process()
    return result


if __name__ == "__main__":
    run()

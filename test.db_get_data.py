from langchain_chroma import Chroma
from langchain_google_vertexai import VertexAIEmbeddings
from google.oauth2.service_account import Credentials

credentials = Credentials.from_service_account_file(
    "ive-fyp-436703-3a208c6d96a0.json")

vertexAIEmbeddings = VertexAIEmbeddings(
        credentials=credentials,
        project=credentials.project_id,
        model_name="text-multilingual-embedding-002",
    )
db = Chroma(
    collection_name = "KMB",
    persist_directory='./chroma_db',
    embedding_function=vertexAIEmbeddings
    )

data = db.get(include=['embeddings', 'documents', 'metadatas'],limit=5)
print(data)
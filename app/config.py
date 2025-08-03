import os
from typing import Optional
from pydantic import BaseModel
from enum import Enum
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class LLMProvider(str, Enum):
    OLLAMA = "ollama"
    OPENAI = "openai"

class LLMConfig(BaseModel):
    provider: LLMProvider = LLMProvider.OLLAMA
    model: str = "mistral"  # Default Ollama model
    base_url: Optional[str] = "http://localhost:11434"  # Default Ollama URL
    api_key: Optional[str] = None  # For OpenAI
    temperature: float = 0.0

class AppConfig:
    def __init__(self):
        self.llm_config = LLMConfig(
            provider=LLMProvider(os.getenv("LLM_PROVIDER", "ollama")),
            model=os.getenv("LLM_MODEL", "mistral"),
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            api_key=os.getenv("OPENAI_API_KEY"),
            temperature=float(os.getenv("LLM_TEMPERATURE", "0.0"))
        )
        
        # ChromaDB settings
        self.chroma_dir = os.getenv("CHROMA_DIR", "rag_store")
        self.pdf_dir = os.getenv("PDF_DIR", "sample_docs")
        
        # Embeddings settings
        self.embedding_model = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
        
        # Database settings
        self.database_url = os.getenv("DATABASE_URL", "postgresql://lakshmana@localhost:5432/legal_db")

# Global configuration instance
config = AppConfig() 
from typing import Optional
from langchain_community.llms import Ollama
from langchain_openai import ChatOpenAI
from .config import LLMProvider, LLMConfig

class LLMFactory:
    @staticmethod
    def create_llm(config: LLMConfig):
        """Create LLM instance based on configuration"""
        if config.provider == LLMProvider.OLLAMA:
            # Use default Ollama URL if none provided
            base_url = config.base_url or "http://localhost:11434"
            return Ollama(
                model=config.model,
                base_url=base_url,
                temperature=config.temperature
            )
        elif config.provider == LLMProvider.OPENAI:
            if not config.api_key:
                raise ValueError("OpenAI API key is required when using OpenAI provider")
            return ChatOpenAI(
                model=config.model,
                api_key=config.api_key,
                temperature=config.temperature
            )
        else:
            raise ValueError(f"Unsupported LLM provider: {config.provider}")

    @staticmethod
    def create_llm_from_args(provider: str, model: str, base_url: Optional[str] = None, 
                            api_key: Optional[str] = None, temperature: float = 0.0):
        """Create LLM instance from function arguments"""
        config = LLMConfig(
            provider=LLMProvider(provider),
            model=model,
            base_url=base_url,
            api_key=api_key,
            temperature=temperature
        )
        return LLMFactory.create_llm(config) 
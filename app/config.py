# app/config.py

class Settings:
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.1"
    OLLAMA_TIMEOUT: int = 120  # seconds, LLM responses can be slow

settings = Settings()
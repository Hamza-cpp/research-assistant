import os

# Flask settings
SECRET_KEY = os.environ.get("SECRET_KEY", "dev_key_change_in_production")

# API Keys (loaded from environment variables)
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
PINECONE_API_KEY = os.environ.get("PINECONE_API_KEY")
PINECONE_ENVIRONMENT = os.environ.get("PINECONE_ENVIRONMENT")

# Pinecone settings
PINECONE_INDEX_NAME = "research-summaries"

# Summarization settings
LLAMA_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"
MAX_SUMMARY_LENGTH = 500
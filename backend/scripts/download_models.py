from sentence_transformers import SentenceTransformer
import os

model_name = "all-MiniLM-L6-v2"
print(f"Pre-downloading model: {model_name}...")
SentenceTransformer(model_name)
print("Model downloaded successfully.")

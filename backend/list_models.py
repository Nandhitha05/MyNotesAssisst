"""Diagnostic: list which Gemini models your API key can use, and which support embedContent.

Run:  python list_models.py
"""
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    raise SystemExit("GOOGLE_API_KEY missing from .env")

import google.generativeai as genai

genai.configure(api_key=api_key)

print("Models available to your API key:\n")
for m in genai.list_models():
    methods = ", ".join(m.supported_generation_methods)
    print(f"  {m.name:<55} -> {methods}")

print("\nLook for a model whose methods include 'embedContent'.")
print("Set GEMINI_EMBEDDING_MODEL=<that name> in .env, then restart the backend.")

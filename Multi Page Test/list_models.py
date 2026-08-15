import google.generativeai as genai
import toml
import os

try:
    with open(".streamlit/secrets.toml", "r") as f:
        secrets = toml.load(f)
        api_key = secrets.get("GEMINI_API_KEY")
        
    if not api_key:
        print("API Key not found in secrets.toml")
    else:
        print(f"Using API Key: {api_key[:5]}...{api_key[-5:]}")
        genai.configure(api_key=api_key)
        print("Available Models:")
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(f"- {m.name}")

except Exception as e:
    print(f"Error: {e}")

import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "app"))
from run import app

with app.app_context():
    import google.generativeai as genai
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("No GEMINI_API_KEY found")
    else:
        genai.configure(api_key=api_key)
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(m.name)

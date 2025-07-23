import os
from dotenv import load_dotenv
load_dotenv()

LLM_MODE = os.getenv("LLM_MODE", "gemini").lower()  # 'gemini' or 'local'

# --- Gemini API setup ---
if LLM_MODE == "gemini":
    import google.generativeai as genai
    from app.prompt import get_prompt
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY or API_KEY environment variable not set.")
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.5-flash")
    def get_sql_query_from_llm(question: str) -> str:
        prompt = get_prompt(question)
        try:
            response = model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            return f"-- LLM Error: {e}"

# --- Local LLM setup (placeholder) ---
elif LLM_MODE == "local":
    from app.prompt import get_prompt
    # Example: import llama_cpp or gpt4all here
    # from llama_cpp import Llama
    # model = Llama(model_path="/path/to/model.bin")
    def get_sql_query_from_llm(question: str) -> str:
        prompt = get_prompt(question)
        # TODO: Implement local LLM inference here
        return "-- Local LLM not yet implemented. Please configure your local LLM."
else:
    raise ValueError(f"Unsupported LLM_MODE: {LLM_MODE}")


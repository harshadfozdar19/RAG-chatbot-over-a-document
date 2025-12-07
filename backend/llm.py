import os
import google.generativeai as genai

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

MODEL_NAME = "models/gemini-flash-latest"

def answer_with_context(history, context, question):

    # Format conversation history like ChatGPT
    history_text = ""
    for msg in history:
        role = msg["role"]
        text = msg["text"]
        history_text += f"{role.upper()}: {text}\n"

    prompt = f"""
You are an AI assistant inside a RAG system.

Your job is:
1. Answer ONLY using the retrieved context below.
2. Maintain natural conversation flow using the chat history.
3. NEVER hallucinate or guess anything not present in the context.
4. If the answer is not in the context, say EXACTLY:
   "The document does not contain this information."

--- CHAT HISTORY ---
{history_text}

--- RETRIEVED CONTEXT (from documents) ---
{context}

--- NEW USER QUESTION ---
{question}

Provide a helpful and natural response based ONLY on the context above.
"""

    model = genai.GenerativeModel(MODEL_NAME)
    response = model.generate_content(prompt)
    return response.text

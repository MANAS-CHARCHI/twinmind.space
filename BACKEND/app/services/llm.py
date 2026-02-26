import httpx
from app.core.config import settings

STRICT_PROMPT = (
    "SYSTEM ROLE: Closed-Domain Knowledge Retrieval. "
    "RULE 1: Answer ONLY using the provided CONTEXT. "
    "RULE 2: If the answer is not explicitly in the CONTEXT, you MUST say 'Information not found.' "
    "RULE 3: Do NOT use your own training data, internal knowledge, or the internet. "
    "RULE 4: Zero fluff. No introductions. No pleasantries. No 'Based on the context'. "
    "RULE 5: If the user asks about general knowledge (e.g., politics, weather, celebrities) "
    "and it is not in the CONTEXT, respond with 'Information not found.'"
)

async def answer_me_llama(context: str, user_prompt: str) -> str:
    """Calls local Llama 3.2 via Ollama"""
    full_prompt = f"{STRICT_PROMPT}\n\nCONTEXT:\n{context}\n\nQUESTION: {user_prompt}\n\nANSWER:"
    
    async with httpx.AsyncClient() as client:
        res = await client.post(
            f"{settings.LLM_API_ADDRESS}/api/generate",
            json={"model": "llama3.2:3b", "prompt": full_prompt, "stream": False},
            timeout=60.0
        )
        # We only return the clean text string
        return res.json().get("response", "").strip()

async def answer_me_gemini(context: str, user_prompt: str) -> str:
    """Calls Google Gemini Flash API"""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-lite:generateContent?key={settings.GEMINI_API_KEY}"    
    full_text = f"{STRICT_PROMPT}\n\nCONTEXT:\n{context}\n\nQUESTION: {user_prompt}"
    payload = {"contents": [{"parts": [{"text": full_text}]}], 
               "generationConfig": {
                    "temperature": 0.0,  # <--- Forces the model to be literal and non-creative
                    "maxOutputTokens": 150,
                }}
    
    async with httpx.AsyncClient() as client:
        try:
            res = await client.post(url, json=payload, timeout=30.0)
            data = res.json()
            if not data.get('candidates') or not data['candidates'][0].get('content'):
                return None
            return data['candidates'][0]['content']['parts'][0]['text'].strip()
            
        except Exception as e:
            print(f"Gemini Connection Error: {e}")
            return None
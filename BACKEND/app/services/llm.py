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
        
STRICT_IDENTITY_PROMPT = """
You are an expert Linguistic Profiler. Your goal is to maintain a 'Writing Identity Profile' (Markdown) for a specific user.

INSTRUCTIONS:
1. Review the EXISTING PROFILE (if any).
2. Analyze the NEW EMAILS for patterns: Greetings, Sign-offs, Tone, Sentence Length, and specific Vocabulary.
3. REWRITE the profile. Do not just append. Refine the existing sections to be more accurate based on the new evidence.
4. The output MUST be valid Markdown.
5. Focus on 'How' they write, so a future AI can mimic this user perfectly.
"""

async def update_user_identity_gemini(existing_md: str, new_emails_text: str) -> str:
    """Calls Gemini to refactor the user_id.md file"""
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-lite:generateContent?key={settings.GEMINI_API_KEY}"    
    
    # We combine the task instructions with the data
    user_content = f"""
    EXISTING PROFILE:
    {existing_md if existing_md else "No profile exists yet. Create the first version."}

    NEW EMAILS TO ANALYZE:
    {new_emails_text}

    TASK: Refactor the profile based on these new emails. Return only the updated Markdown.
    """
    
    payload = {
        "contents": [{
            "parts": [{
                "text": f"{STRICT_IDENTITY_PROMPT}\n\n{user_content}"
            }]
        }], 
        "generationConfig": {
            "temperature": 0.2,  # Small bit of creativity helps with linguistic patterns
            "maxOutputTokens": 2048, # Increased to allow for a full Markdown file
        }
    }
    
    async with httpx.AsyncClient() as client:
        try:
            res = await client.post(url, json=payload, timeout=30.0)
            data = res.json()
            
            # Error checking for API response
            if "candidates" not in data or not data["candidates"]:
                print(f"Gemini API Error: {data}")
                return None
                
            return data['candidates'][0]['content']['parts'][0]['text'].strip()
            
        except Exception as e:
            print(f"Gemini Connection Error: {e}")
            return None
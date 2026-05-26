import json
import google.generativeai as genai
from groq import Groq
from backend.config.settings import settings

class LLMService:
    def __init__(self):
        if settings.GOOGLE_API_KEY:
            genai.configure(api_key=settings.GOOGLE_API_KEY)
            self.gemini_model = genai.GenerativeModel(settings.PRIMARY_MODEL)
        else:
            self.gemini_model = None
            
        if settings.GROQ_API_KEY:
            self.groq_client = Groq(api_key=settings.GROQ_API_KEY)
        else:
            self.groq_client = None

    def call(self, system_prompt: str, user_prompt: str, expect_json: bool = True) -> dict:
        # Try Gemini
        if self.gemini_model:
            try:
                full_prompt = f"{system_prompt}\n\n{user_prompt}"
                response = self.gemini_model.generate_content(full_prompt)
                if expect_json:
                    return self._parse_json(response.text)
                return response.text
            except Exception as e:
                if "429" in str(e):
                    print("Gemini quota exceeded. Falling back to Groq...")
                else:
                    print(f"Gemini call failed: {e}")

        # Try Groq
        if self.groq_client:
            try:
                chat_params = {
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    "model": settings.FALLBACK_MODEL
                }
                if expect_json:
                    chat_params["response_format"] = {"type": "json_object"}
                
                chat_completion = self.groq_client.chat.completions.create(**chat_params)
                content = chat_completion.choices[0].message.content
                if expect_json:
                    return json.loads(content)
                return content
            except Exception as e:
                print(f"Groq call failed: {e}")

        raise ConnectionError("All LLM providers failed.")

    def _parse_json(self, text: str) -> dict:
        try:
            # Clean up the text
            text = text.strip()
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "{" in text:
                text = text[text.find("{"):text.rfind("}")+1]
            
            data = json.loads(text)
            
            # If the LLM returned a list directly, wrap it in our expected format
            if isinstance(data, list):
                return {"actions": data}
            
            return data
        except Exception as e:
            print(f"JSON Parsing Error: {e}\nRaw Text: {text}")
            raise e

llm_service = LLMService()

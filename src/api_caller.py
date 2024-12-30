from openai import OpenAI

class APICaller:
    """Вызов модели по API"""
    
    def __init__(self, api_key):
        self.client = OpenAI(
            api_key=api_key, 
            base_url="https://api.proxyapi.ru/openai/v1"
        )
    
    def call_gpt35_turbo(self, system_prompt, user_prompt, max_tokens=200, temperature=0.7):
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=max_tokens, 
                temperature=temperature
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Произошла ошибка при вызове API: {e}")
            return None
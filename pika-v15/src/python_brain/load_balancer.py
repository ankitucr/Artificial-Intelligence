import os
import requests
import time
from dotenv import load_dotenv

# Load environment variables
dotenv_path = os.path.join(os.path.dirname(__file__), '../../.env')
load_dotenv(dotenv_path=dotenv_path)

class AI_LoadBalancer:
    def __init__(self):
        # 1. Define All Available Providers and their Configurations
        self.cf_account = os.getenv("CLOUDFLARE_ACCOUNT_ID", "")
        
        self.PROVIDERS = {
            "gemini": {
                "url": "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.6-flash:generateContent",
                "key": os.getenv("GEMINI_API_KEY"),
                "type": "gemini"
            },
            "groq": {
                "url": "https://api.groq.com/openai/v1/chat/completions",
                "key": os.getenv("GROQ_API_KEY"),
                "model": "openai/gpt-oss-120b",
                "type": "openai"
            },
            "mistral": {
                "url": "https://api.mistral.ai/v1/chat/completions",
                "key": os.getenv("MISTRAL_API_KEY"),
                "model": "mistral-small-latest",
                "type": "openai"
            },
            "cohere": {
                "url": "https://api.cohere.com/v2/chat",
                "key": os.getenv("COHERE_API_KEY"),
                "model": "command-a-03-2025",
                "type": "cohere"
            },
            "huggingface": {
                "url": "https://router.huggingface.co/v1/chat/completions",
                "key": os.getenv("HUGGINGFACE_API_KEY"),
                "model": "meta-llama/Llama-3.1-8B-Instruct:novita",
                "type": "hf"
            },
            "cloudflare": {
                "url": f"https://api.cloudflare.com/client/v4/accounts/{self.cf_account}/ai/v1/chat/completions",
                "key": os.getenv("CLOUDFLARE_API_TOKEN"),
                "model": "@cf/meta/llama-3.3-70b-instruct-fp8-fast",
                "type": "openai"
            },
            "github": {
                "url": "https://models.github.ai/inference/chat/completions",
                "key": os.getenv("GITHUB_MODELS_API_KEY"),
                "model": "openai/gpt-4o",
                "type": "openai"
            },
            "cerebras": {
                "url": "https://api.cerebras.ai/v1/chat/completions",
                "key": os.getenv("CEREBRAS_API_KEY"),
                "model": "llama3.1-8b",
                "type": "openai"
            }
        }

        # 2. Assign Fallback Arrays for each Agent Role
        # Agar pehla fail hua, toh automatically dusre par shift hoga
        self.AGENT_ROUTING = {
            "coder": ["mistral", "cloudflare", "huggingface", "groq", "github"],
            "analyzer": ["gemini", "cohere", "groq", "mistral"],
            "planner": ["groq", "cohere", "mistral", "cerebras"],
            "debugger": ["groq", "gemini", "cloudflare"]
        }

    def _format_payload(self, provider_info, prompt):
        """Formats the request payload based on the specific API provider's format"""
        p_type = provider_info["type"]
        
        if p_type == "openai":
            return {"model": provider_info["model"], "messages": [{"role": "user", "content": prompt}], "max_tokens": 1500}
        
        elif p_type == "gemini":
            return {"contents": [{"parts": [{"text": prompt}]}]}
        
        elif p_type == "cohere":
            return {"model": provider_info["model"], "messages": [{"role": "user", "content": prompt}], "max_tokens": 1500}
        
        elif p_type == "hf":
            return {"model": provider_info["model"], "messages": [{"role": "user", "content": prompt}], "max_tokens": 1500}
        
        return None

    def _extract_response(self, response_json, p_type):
        """Extracts the actual text from different JSON response structures"""
        try:
            if p_type in ["openai", "hf", "cohere"]:
                return response_json["choices"][0]["message"]["content"]
            elif p_type == "gemini":
                return response_json["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError):
            return None

    def ask(self, prompt, role="coder"):
        """
        The Main Routing Function.
        Tries providers in the sequence defined for the specific role.
        """
        fallback_chain = self.AGENT_ROUTING.get(role, self.AGENT_ROUTING["coder"])
        
        print(f"\n🔄 Initiating '{role.upper()}' Task...")
        
        for provider_name in fallback_chain:
            provider = self.PROVIDERS.get(provider_name)
            
            # Skip if key is missing
            if not provider["key"] or provider["key"] == "your_key_here":
                continue

            print(f"  --> Routing to {provider_name.upper()}...")
            
            # Setup URL and Headers
            url = provider["url"]
            headers = {"Content-Type": "application/json"}
            
            if provider["type"] == "gemini":
                url = f"{url}?key={provider['key']}"
            else:
                headers["Authorization"] = f"Bearer {provider['key']}"

            data = self._format_payload(provider, prompt)

            try:
                # 15 seconds timeout - if API is slow/dead, cut it off and jump to next
                response = requests.post(url, headers=headers, json=data, timeout=15)
                
                if response.status_code == 200:
                    text_output = self._extract_response(response.json(), provider["type"])
                    if text_output:
                        print(f"  ✅ SUCCESS: {provider_name.upper()} handled the task.")
                        return text_output
                else:
                    print(f"  ⚠️ FAILED ({response.status_code}). Switching to fallback...")
                    
            except requests.exceptions.RequestException as e:
                print(f"  ❌ TIMEOUT/ERROR with {provider_name.upper()}. Switching to fallback...")
                
            time.sleep(1) # Chota sa delay fallback se pehle taaki system breathe kar sake

        return "CRITICAL ERROR: All API providers in the fallback chain failed."

# ==========================================
# Testing the Load Balancer
# ==========================================
if __name__ == "__main__":
    lb = AI_LoadBalancer()
    
    test_prompt = "Write a one-line Python function to reverse a string."
    
    print("\n--- Testing Coder Agent ---")
    coder_response = lb.ask(test_prompt, role="coder")
    print(f"RESULT:\n{coder_response}")

    print("\n--- Testing Analyzer Agent ---")
    analyzer_response = lb.ask("Is this code safe: `eval('print(1)')`?", role="analyzer")
    print(f"RESULT:\n{analyzer_response}")

"""Platform Agent - Uses SurrealQL for all operations + configurable LLM."""

import os
from surrealdb import AsyncSurreal
from .config import AgentConfig


# =============================================================================
# LLM Integration - Configurable to any LLM provider
# =============================================================================

class LLM:
    """Configurable LLM - supports any provider.
    
    Providers by resource:
    - CPU only: ollama, llama.cpp, llama-server, huggingface
    - GPU: openai, anthropic, cohere, azure, etc
    
    Set LLM_PROVIDER env var to switch.
    """

    PROVIDERS = {
        # Local (CPU)
        "ollama": "http://localhost:11434",
        "llama.cpp": "http://localhost:8080",
        "llama-server": "http://localhost:8080",
        "lmstudio": "http://localhost:1234/v1",
        
        # API (cloud)
        "openai": "https://api.openai.com/v1",
        "anthropic": "https://api.anthropic.com/v1",
        "cohere": "https://api.cohere.ai/v1",
        "google": "https://generativelanguage.googleapis.com/v1",
        "mistral": "https://api.mistral.ai/v1",
        "groq": "https://api.groq.com/openai/v1",
        
        # Self-hosted
        "vllm": "http://localhost:8000/v1",
        "litellm": "http://localhost:4000",
        "tensorrt": "http://localhost:8000",
        
        # HuggingFace (inference api or local)
        "huggingface": "https://api-inference.huggingface.co",
        "huggingface-local": "http://localhost:8081",
        
        # Azure
        "azure": "",
    }
    
    # Model defaults per provider
    DEFAULT_MODELS = {
        # Local
        "ollama": "tinyllama",
        "llama.cpp": "model.gguf",
        "llama-server": "model.gguf",
        "lmstudio": "llama3",
        
        # Cloud
        "openai": "gpt-4o-mini",
        "anthropic": "claude-3-haiku-20240307",
        "cohere": "command-r-plus",
        "google": "gemini-1.5-flash",
        "mistral": "mistral-small-latest",
        "groq": "llama-3-70b",
        
        # Self-hosted
        "vllm": "meta-llama/Meta-Llama-3-70B-Instruct",
        "litellm": "gpt-4o-mini",
        
        # HuggingFace
        "huggingface": "TinyLlama/TinyLlama-1.1B-Chat",
        "huggingface-local": "TinyLlama/TinyLlama-1.1B-Chat",
        
        # Azure
        "azure": "gpt-4o-mini",
    }
    
    def __init__(
        self,
        provider: str = "ollama",
        model: str = None,
        api_key: str = None,
        base_url: str = None,
    ):
        self.provider = provider
        self.model = model or self.DEFAULT_MODELS.get(provider, "tinyllama")
        self.api_key = api_key or os.getenv("LLM_API_KEY", "")
        self.base_url = base_url or self.PROVIDERS.get(provider, "")
        self._client = None
    
    def _get_client(self):
        """Lazy-load transformers for local inference."""
        if not self._client and self.provider in ("transformers", "huggingface-local"):
            try:
                from transformers import AutoModelForCausalLM, AutoTokenizer
                import torch
                
                self._client = {
                    "model": AutoModelForCausalLM.from_pretrained(
                        self.model,
                        torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                        device_map="auto" if torch.cuda.is_available() else "cpu",
                    ),
                    "tokenizer": AutoTokenizer.from_pretrained(self.model),
                }
            except ImportError:
                raise ImportError("pip install transformers torch")
        return self._client
    
    async def generate(self, messages: list) -> str:
        """Generate response based on provider."""
        provider = self.provider.lower()
        
        # Local CPU
        if provider in ("ollama", "llama.cpp", "llama-server", "lmstudio"):
            return await self._local_chat(messages)
        
        # Cloud APIs
        elif provider == "openai":
            return await self._openai_chat(messages)
        elif provider == "anthropic":
            return await self._anthropic_chat(messages)
        elif provider == "cohere":
            return await self._cohere_chat(messages)
        elif provider == "google":
            return await self._google_chat(messages)
        elif provider in ("mistral", "groq"):
            return await self._openai_chat(messages)  # OpenAI compatible
        elif provider == "huggingface":
            return await self._huggingface_inference(messages)
        
        # Local transformers
        elif provider in ("transformers", "huggingface-local"):
            return await self._transformers_generate(messages)
        
        # Default: local
        return await self._local_chat(messages)
    
    async def _local_chat(self, messages: list) -> str:
        """Local API (ollama/llama.cpp/lmstudio)."""
        import ollama
        client = ollama.Client(self.base_url)
        response = client.chat(model=self.model, messages=messages)
        return response["message"]["content"]
    
    async def _openai_chat(self, messages: list) -> str:
        """OpenAI-compatible API."""
        import aiohttp
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json={"model": self.model, "messages": messages},
            ) as resp:
                data = await resp.json()
                return data["choices"][0]["message"]["content"]
    
    async def _anthropic_chat(self, messages: list) -> str:
        """Anthropic API."""
        import aiohttp
        
        system = ""
        user_msgs = []
        for msg in messages:
            if msg.get("role") == "system":
                system = msg.get("content", "")
            else:
                user_msgs.append(msg)
        
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/messages",
                headers=headers,
                json={
                    "model": self.model,
                    "max_tokens": 1024,
                    "messages": user_msgs,
                    "system": system,
                },
            ) as resp:
                data = await resp.json()
                return data["content"][0]["text"]
    
    async def _cohere_chat(self, messages: list) -> str:
        """Cohere API."""
        import aiohttp
        
        user_msg = ""
        for msg in reversed(messages):
            if msg.get("role") == "user":
                user_msg = msg.get("content", "")
                break
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/chat",
                headers=headers,
                json={"model": self.model, "message": user_msg},
            ) as resp:
                data = await resp.json()
                return data["text"]
    
    async def _google_chat(self, messages: list) -> str:
        """Google Gemini API."""
        import aiohttp
        
        user_msg = ""
        for msg in reversed(messages):
            if msg.get("role") == "user":
                user_msg = msg.get("content", "")
                break
        
        headers = {
            "Content-Type": "application/json",
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/models/{self.model}:generateContent",
                headers=headers,
                json={"contents": [{"parts": [{"text": user_msg}]}]},
            ) as resp:
                data = await resp.json()
                return data["candidates"][0]["content"]["parts"][0]["text"]
    
    async def _huggingface_inference(self, messages: list) -> str:
        """HuggingFace Inference API."""
        import aiohttp
        
        user_msg = ""
        for msg in reversed(messages):
            if msg.get("role") == "user":
                user_msg = msg.get("content", "")
                break
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/models/{self.model}",
                headers=headers,
                json={"inputs": user_msg},
            ) as resp:
                data = await resp.json()
                return data[0]["generated_text"]
    
    async def _transformers_generate(self, messages: list) -> str:
        """Transformers (local GPU/CPU)."""
        client = self._get_client()
        
        user_msg = ""
        for msg in reversed(messages):
            if msg.get("role") == "user":
                user_msg = msg.get("content", "")
                break
        
        inputs = client["tokenizer"](user_msg, return_tensors="pt")
        if inputs.device.type == "cuda":
            inputs = inputs.to("cuda")
        
        outputs = client["model"].generate(**inputs, max_new_tokens=256)
        return client["tokenizer"].decode(outputs[0])
    
    async def generate_raw(self, prompt: str) -> str:
        """Simple generate."""
        return await self.generate([{"role": "user", "content": prompt}])
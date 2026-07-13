import os
import httpx
from functools import lru_cache
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    sarvam_api_key: str = os.getenv("SARVAM_API_KEY")
    sarvam_endpoint: str = os.getenv("SARVAM_ENDPOINT", "https://api.sarvam.ai/v1")

@lru_cache()
def get_settings() -> Settings:
    return Settings()

def get_headers() -> dict:
    s = get_settings()
    return {
        "Authorization": f"Bearer {s.sarvam_api_key}",
        "Content-Type": "application/json",
    }

async def generate_text(prompt: str, model: str = "default") -> str:
    """Call Sarvam AI text‑generation endpoint.
    Adjust the payload according to the official Sarvam documentation if needed.
    """
    s = get_settings()
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{s.sarvam_endpoint}/chat/completions",
            json={"model": model, "prompt": prompt},
            headers=get_headers(),
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        # Expected response shape: {"choices": [{"text": "..."}]}
        return data["choices"][0]["text"]

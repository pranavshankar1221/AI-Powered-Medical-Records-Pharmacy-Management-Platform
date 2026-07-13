from fastapi import APIRouter
from utils.sarvam_client import generate_text

router = APIRouter(prefix="/api/ai", tags=["AI"])

@router.post("/chat")
async def chat(prompt: str):
    """Accept a prompt and return Sarvam AI generated text."""
    answer = await generate_text(prompt)
    return {"answer": answer}

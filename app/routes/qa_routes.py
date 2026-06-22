# app/routes/qa_routes.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.config import settings
import requests

router = APIRouter()


class QuestionRequest(BaseModel):
    question: str


@router.post("/ask")
def ask_question(body: QuestionRequest):
    """
    Answer any financial question using the local LLM.
    No ticker required — open-ended financial Q&A.
    """
    question = body.question.strip()

    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    if len(question) > 500:
        raise HTTPException(status_code=400, detail="Question too long (max 500 characters).")

    prompt = f"""You are a knowledgeable financial assistant. Answer the following question clearly and concisely (3-6 sentences). Use plain language. Do not give direct investment advice — only factual, educational information.

Question: {question}

Answer:"""

    payload = {
        "model": settings.OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
    }

    try:
        response = requests.post(
            f"{settings.OLLAMA_BASE_URL}/api/generate",
            json=payload,
            timeout=settings.OLLAMA_TIMEOUT,
        )
        response.raise_for_status()
    except requests.exceptions.ConnectionError:
        raise HTTPException(status_code=503, detail="Could not connect to Ollama.")
    except requests.exceptions.Timeout:
        raise HTTPException(status_code=503, detail="Ollama timed out.")
    except requests.exceptions.HTTPError as e:
        raise HTTPException(status_code=503, detail=str(e))

    answer = response.json().get("response", "").strip()
    return {"question": question, "answer": answer}
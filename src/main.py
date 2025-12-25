from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from app.config import get_settings
from app.knowledge_base import KnowledgeBase
from app.pipeline import QAEngine
from app.retriever import Retriever

app = FastAPI(title="Drug Q&A", version="0.1.0")


class QueryRequest(BaseModel):
    question: str


class AnswerResponse(BaseModel):
    question: str
    answer: str
    sources: list[str]
    last_updated: list[str]


@app.on_event("startup")
def startup_event():
    settings = get_settings()
    kb = KnowledgeBase(settings.data_path)
    retriever = Retriever(kb)
    app.state.qa_engine = QAEngine(kb=kb, retriever=retriever)


@app.post("/ask", response_model=AnswerResponse)
def ask_question(payload: QueryRequest):
    try:
        result = app.state.qa_engine.generate_answer(payload.question)
    except ValueError as exc:  # likely missing API key
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return result


@app.get("/health")
def health_check():
    return {"status": "ok"}

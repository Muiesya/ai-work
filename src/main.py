from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
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


@app.get("/", response_class=HTMLResponse)
def landing_page():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <title>Drug Q&A</title>
        <style>
            body { font-family: system-ui, -apple-system, "Segoe UI", sans-serif; padding: 24px; max-width: 960px; margin: auto; background: #f8fafc; color: #0f172a; }
            h1 { margin-bottom: 0.25rem; }
            p.description { margin-top: 0; color: #475569; }
            .card { background: #fff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 20px; box-shadow: 0 4px 16px rgba(15, 23, 42, 0.08); }
            label { display: block; font-weight: 600; margin-bottom: 8px; }
            textarea { width: 100%; min-height: 120px; padding: 12px; font-size: 1rem; border-radius: 8px; border: 1px solid #cbd5e1; resize: vertical; box-sizing: border-box; }
            button { margin-top: 12px; background: #2563eb; color: white; border: none; padding: 12px 16px; border-radius: 8px; cursor: pointer; font-size: 1rem; }
            button:disabled { background: #94a3b8; cursor: not-allowed; }
            .answer { margin-top: 20px; white-space: pre-wrap; }
            .meta { margin-top: 10px; font-size: 0.95rem; color: #475569; }
            .error { color: #b91c1c; margin-top: 10px; }
            .disclaimer { margin-top: 20px; font-size: 0.9rem; color: #475569; background: #f1f5f9; padding: 12px; border-radius: 8px; }
        </style>
    </head>
    <body>
        <h1>药物信息问答</h1>
        <p class="description">提供通用药物信息，仅供参考。请务必咨询医生或药师获得个性化建议。</p>
        <div class="card">
            <label for="question">请输入问题</label>
            <textarea id="question" placeholder="例如：对乙酰氨基酚的常见副作用是什么？"></textarea>
            <button id="askBtn">询问</button>
            <div id="error" class="error" role="alert"></div>
            <div id="answer" class="answer"></div>
            <div id="meta" class="meta"></div>
            <div class="disclaimer">免责声明：本工具不提供个性化医疗建议，信息可能过时或不完整。请咨询专业医疗人员。</div>
        </div>
        <script>
            const btn = document.getElementById("askBtn");
            const questionEl = document.getElementById("question");
            const answerEl = document.getElementById("answer");
            const metaEl = document.getElementById("meta");
            const errorEl = document.getElementById("error");

            async function ask() {
                const question = questionEl.value.trim();
                errorEl.textContent = "";
                answerEl.textContent = "";
                metaEl.textContent = "";
                if (!question) {
                    errorEl.textContent = "请输入问题。";
                    return;
                }
                btn.disabled = true;
                btn.textContent = "处理中...";
                try {
                    const res = await fetch("/ask", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ question })
                    });
                    if (!res.ok) {
                        const detail = await res.json().catch(() => ({}));
                        throw new Error(detail.detail || "请求失败");
                    }
                    const data = await res.json();
                    answerEl.textContent = data.answer || "未返回答案";
                    const sources = (data.sources || []).join(", ");
                    const updated = (data.last_updated || []).join(", ");
                    metaEl.textContent = sources ? `来源: ${sources} | 更新: ${updated}` : "";
                } catch (err) {
                    errorEl.textContent = err.message || "发生错误";
                } finally {
                    btn.disabled = false;
                    btn.textContent = "询问";
                }
            }

            btn.addEventListener("click", ask);
            questionEl.addEventListener("keydown", (ev) => {
                if (ev.key === "Enter" && (ev.metaKey || ev.ctrlKey || ev.shiftKey)) {
                    ask();
                }
            });
        </script>
    </body>
    </html>
    """

# -*- coding: utf-8 -*-
"""企业知识库 RAG 问答 - FastAPI 服务入口。"""
import sys
from pathlib import Path

# 将项目根目录加入 path，便于直接运行 python api/main.py
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from config import get_settings
from logger_config import logger
from rag import answer_question, rebuild_index

app = FastAPI(
    title="企业内部知识库问答 API",
    description="基于 RAG 的企业知识库检索与问答",
    version="1.0.0",
)


@app.on_event("startup")
def startup_warmup():
    """启动时预热：加载嵌入模型与向量库，避免首条请求卡顿。"""
    try:
        from knowledge import get_vector_store
        get_vector_store()
        logger.info("向量库与嵌入模型已预热")
    except Exception as e:
        logger.warning(f"启动预热跳过: {e}")


class QuestionRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000, description="用户问题")
    top_k: int | None = Field(default=None, ge=1, le=20, description="检索条数，不传则用配置默认值")


class QuestionResponse(BaseModel):
    answer: str
    sources: list[dict]
    retrieved_only: bool


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/api/ask", response_model=QuestionResponse)
def api_ask(req: QuestionRequest):
    """提交问题，返回 RAG 答案与引用来源。"""
    try:
        result = answer_question(req.question, top_k=req.top_k)
        return QuestionResponse(
            answer=result["answer"],
            sources=result["sources"],
            retrieved_only=result["retrieved_only"],
        )
    except Exception as e:
        logger.exception("问答请求失败")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/rebuild")
def api_rebuild():
    """重建知识库向量索引（管理员或定时任务调用）。"""
    try:
        return rebuild_index()
    except Exception as e:
        logger.exception("重建索引失败")
        raise HTTPException(status_code=500, detail=str(e))


# 静态页面：问答前端
STATIC_DIR = ROOT / "static"
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/", response_class=HTMLResponse)
def index():
    """返回问答机器人前端页面。"""
    html_file = ROOT / "static" / "index.html"
    if html_file.exists():
        return HTMLResponse(content=html_file.read_text(encoding="utf-8"))
    return HTMLResponse(content=_default_index_html())


def _default_index_html() -> str:
    """内嵌的简易问答页（无依赖 static 目录时使用，使用简化版样式）。"""
    # 如果 static/index.html 存在，应该不会走到这里，但作为后备方案保留简化版
    return """<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>企业内部知识库问答</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Microsoft YaHei", sans-serif; max-width: 900px; margin: 0 auto; padding: 2rem 1rem; background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%); min-height: 100vh; }
    .header { text-align: center; margin-bottom: 2rem; }
    h1 { font-size: 2rem; font-weight: 700; background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 0.5rem; }
    .subtitle { color: #64748b; font-size: 0.95rem; }
    .card { background: #fff; border-radius: 16px; padding: 1.5rem; margin-bottom: 1.5rem; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1); }
    textarea { width: 100%; min-height: 100px; padding: 1rem; border: 2px solid #e2e8f0; border-radius: 12px; font-size: 1rem; resize: vertical; transition: border-color 0.3s; }
    textarea:focus { outline: none; border-color: #6366f1; }
    .button-group { display: flex; gap: 0.75rem; margin-top: 1rem; flex-wrap: wrap; }
    button { padding: 0.75rem 1.5rem; border: none; border-radius: 10px; font-size: 1rem; font-weight: 600; cursor: pointer; transition: all 0.3s; }
    .btn-primary { background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%); color: white; }
    .btn-primary:hover:not(:disabled) { transform: translateY(-2px); box-shadow: 0 6px 16px rgba(99,102,241,0.4); }
    button:disabled { opacity: 0.6; cursor: not-allowed; }
    .answer { white-space: pre-wrap; line-height: 1.8; color: #1e293b; font-size: 1.05rem; padding: 1rem 0; }
    .sources { margin-top: 1.5rem; padding-top: 1.5rem; border-top: 2px solid #e2e8f0; }
    .sources summary { cursor: pointer; color: #64748b; font-weight: 600; }
    .sources ul { margin-top: 0.75rem; padding-left: 1.5rem; list-style: none; }
    .sources li { padding: 0.5rem 0; color: #64748b; }
    .error { background: #fef2f2; border: 2px solid #fecaca; color: #ef4444; padding: 1rem; border-radius: 12px; }
    .loading { text-align: center; padding: 2rem; color: #64748b; }
  </style>
</head>
<body>
  <div class="header">
    <h1>🤖 企业知识库问答助手</h1>
    <p class="subtitle">基于 RAG 技术的智能问答系统</p>
  </div>
  <div class="card">
    <textarea id="q" placeholder="💡 请输入您的问题，例如：请假类型与天数、请假流程是怎样的？"></textarea>
    <div class="button-group">
      <button id="btn" class="btn-primary">🚀 提交问题</button>
      <button id="rebuildBtn" style="background:#64748b;color:white;">🔄 重建索引</button>
    </div>
  </div>
  <div id="result"></div>
  <script>
    const q = document.getElementById('q');
    const btn = document.getElementById('btn');
    const rebuildBtn = document.getElementById('rebuildBtn');
    const result = document.getElementById('result');
    const esc = t => (t || '').replace(/</g,'&lt;').replace(/>/g,'&gt;');
    btn.onclick = async () => {
      const question = q.value.trim();
      if (!question) return;
      btn.disabled = true;
      result.innerHTML = '<div class="card loading">正在查询…</div>';
      try {
        const r = await fetch('/api/ask', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ question }) });
        const data = await r.json();
        if (!r.ok) throw new Error(data.detail || '请求失败');
        let html = '<div class="card"><div class="answer">' + esc(data.answer) + '</div>';
        if (data.sources && data.sources.length) {
          html += '<details class="sources"><summary>📚 参考来源 (' + data.sources.length + ')</summary><ul>';
          data.sources.forEach(s => { html += '<li>' + esc(s.filename || s.source || '') + '</li>'; });
          html += '</ul></details>';
        }
        html += '</div>';
        result.innerHTML = html;
      } catch (e) {
        result.innerHTML = '<div class="card"><div class="error">错误：' + esc(e.message) + '</div></div>';
      }
      btn.disabled = false;
    };
    rebuildBtn.onclick = async () => {
      rebuildBtn.disabled = true;
      result.innerHTML = '<div class="card loading">正在重建索引…</div>';
      try {
        const r = await fetch('/api/rebuild', { method: 'POST' });
        const data = await r.json();
        if (!r.ok) throw new Error(data.detail || '重建失败');
        result.innerHTML = '<div class="card"><div style="background:#f0fdf4;border:2px solid #bbf7d0;color:#10b981;padding:1rem;border-radius:12px;">✅ 索引已重建完成！</div></div>';
      } catch (e) {
        result.innerHTML = '<div class="card"><div class="error">错误：' + esc(e.message) + '</div></div>';
      }
      rebuildBtn.disabled = false;
    };
  </script>
</body>
</html>
"""


def run():
    s = get_settings()
    import uvicorn
    uvicorn.run(app, host=s.host, port=s.port)


if __name__ == "__main__":
    run()

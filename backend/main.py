# backend/main.py
"""
Phase 6: FastAPI 后端服务入口

将检索、生成、置信度评估、结构化数据校验等服务封装为 RESTful API，
供 Streamlit 前端或其他客户端调用。服务通过 backend.dependencies 注入，
实现全局单例，避免每次请求重复加载模型。
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routers import query, documents, structured


app = FastAPI(
    title="考研择校 RAG 系统",
    description="基于检索增强生成（RAG）的考研择校问答与结构化数据管理 API",
    version="1.0.0"
)

# 允许跨域（本地开发时前端 Streamlit 与后端不在同一端口）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载路由
app.include_router(query.router, prefix="/api", tags=["问答"])
app.include_router(documents.router, prefix="/api", tags=["文档"])
app.include_router(structured.router, prefix="/api", tags=["结构化数据"])


@app.get("/")
async def root():
    """健康检查"""
    return {"message": "考研择校 RAG 系统 API 运行中", "version": "1.0.0"}

# backend/routers/documents.py
"""
文档管理路由：/api/documents
提供知识库中文档的列表、新增、删除（当前实现基于现有 Chroma 集合，
如需完整写入可自行扩展）。
"""
from fastapi import APIRouter, Depends, HTTPException

from backend.dependencies import get_retrieval_service
from backend.services.retrieval import RetrievalService


router = APIRouter()


@router.get("/documents")
async def list_documents(
    retriever: RetrievalService = Depends(get_retrieval_service)
):
    """
    列出知识库中的所有文档。
    """
    raw = retriever.collection.get()
    documents = []
    for doc_id, content, meta in zip(raw["ids"], raw["documents"], raw["metadatas"]):
        documents.append({
            "id": doc_id,
            "content": content,
            "metadata": meta,
        })
    return {"total": len(documents), "documents": documents}


@router.get("/documents/{doc_id}")
async def get_document(
    doc_id: str,
    retriever: RetrievalService = Depends(get_retrieval_service)
):
    """
    根据文档 ID 获取单个文档。
    """
    raw = retriever.collection.get(ids=[doc_id])
    if not raw["ids"]:
        raise HTTPException(status_code=404, detail=f"文档 {doc_id} 不存在")

    return {
        "id": raw["ids"][0],
        "content": raw["documents"][0],
        "metadata": raw["metadatas"][0],
    }

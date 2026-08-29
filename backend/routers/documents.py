# backend/routers/documents.py
"""
文档管理路由：/api/documents
提供知识库中文档的上传、列表、查询、重新入库。
"""
import json
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from backend.config import RAW_DATA_DIR
from backend.dependencies import get_retrieval_service
from backend.services.retrieval import RetrievalService
from backend.services.ingestion import IngestionService


router = APIRouter()


class DocumentUploadRequest(BaseModel):
    school_name: str
    introduction: Optional[str] = None   # 介绍文本，写入 introductions/{school_name}.txt
    structured: Optional[dict] = None    # 结构化数据，写入/更新 schools.json


@router.post("/documents/upload")
async def upload_document(request: DocumentUploadRequest):
    """
    上传院校数据：可同时传介绍文本（introduction）和结构化数据（structured）。
    数据写入 data/raw 后，需调用 /documents/ingest 或命令行入库才会进入向量库。
    """
    written = []

    # 1. 写入介绍文本
    if request.introduction:
        intro_dir = RAW_DATA_DIR / "introductions"
        intro_dir.mkdir(parents=True, exist_ok=True)
        txt_path = intro_dir / f"{request.school_name}.txt"
        txt_path.write_text(request.introduction, encoding="utf-8")
        written.append(f"introductions/{request.school_name}.txt")

    # 2. 写入/更新结构化数据
    if request.structured:
        schools_file = RAW_DATA_DIR / "schools.json"
        schools = json.loads(schools_file.read_text(encoding="utf-8"))

        structured = dict(request.structured)
        structured.setdefault("school_name", request.school_name)

        updated = False
        for i, s in enumerate(schools):
            if s.get("school_name") == request.school_name:
                schools[i] = structured
                updated = True
                break
        if not updated:
            schools.append(structured)

        schools_file.write_text(
            json.dumps(schools, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        written.append("schools.json")

    if not written:
        raise HTTPException(status_code=400, detail="请至少提供 introduction 或 structured 之一")

    return {
        "message": "数据上传成功，已写入 data/raw，请调用 /documents/ingest 入库",
        "written": written,
    }


@router.post("/documents/ingest")
async def ingest_documents():
    """
    重新执行数据入库：清空向量库并重写入库。
    """
    service = IngestionService()
    service.clear()
    service.ingest()
    return {"message": "数据入库完成"}


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

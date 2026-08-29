# backend/dependencies.py
"""
Phase 6 依赖注入层

把重量级服务封装为 FastAPI Depends，使用 lru_cache 实现全局单例，
避免每个请求重复初始化模型与索引。
"""
from functools import lru_cache

from backend.services.retrieval import RetrievalService
from backend.services.generation import GenerationService
from backend.services.confidence import ConfidenceService
from backend.services.validation import ValidationService


@lru_cache()
def get_retrieval_service() -> RetrievalService:
    """检索服务（含 Embedding、BM25、Reranker）"""
    return RetrievalService()


@lru_cache()
def get_generation_service() -> GenerationService:
    """生成服务（DeepSeek API 客户端）"""
    return GenerationService()


@lru_cache()
def get_confidence_service() -> ConfidenceService:
    """置信度评估服务"""
    return ConfidenceService()


@lru_cache()
def get_validation_service() -> ValidationService:
    """结构化数据校验服务"""
    return ValidationService()

# backend/routers/query.py
"""
问答路由：/api/query
完整链路：检索 → 置信度评估 → 生成 → 引用解析 → 数据校验
"""
from fastapi import APIRouter, Depends

from backend.dependencies import (
    get_retrieval_service,
    get_generation_service,
    get_confidence_service,
    get_validation_service,
)
from backend.services.retrieval import RetrievalService
from backend.services.generation import GenerationService
from backend.services.confidence import ConfidenceService
from backend.services.validation import ValidationService
from backend.models.schemas import QueryRequest, QueryResponse
from backend.utils.citation import parse_citations


router = APIRouter()


@router.post("/query", response_model=QueryResponse)
async def query_endpoint(
    request: QueryRequest,
    retriever: RetrievalService = Depends(get_retrieval_service),
    generator: GenerationService = Depends(get_generation_service),
    confidence_svc: ConfidenceService = Depends(get_confidence_service),
    validator: ValidationService = Depends(get_validation_service),
):
    """
    接收用户问题，返回带引用、置信度和校验结果的回答。
    """
    # 1. 混合检索 + Reranker 精排
    retrieved_docs, max_score = retriever.retrieve(request.question)

    # 2. 召回覆盖率评估（问题提到的学校是否都被召回）
    coverage = retriever.assess_coverage(request.question, retrieved_docs)

    # 3. 置信度评估（单文档相关性 + 召回覆盖率）
    level, should_reject, reason = confidence_svc.evaluate(max_score, coverage)

    # 4. 低置信度：直接拒答
    if should_reject:
        return QueryResponse(
            answer=generator.generate_with_rejection(request.question, reason),
            citations=[],
            confidence_level=level,
            confidence_score=max_score,
            validation_results=[],
            is_rejected=True,
            rejection_reason=reason,
        )

    # 5. 生成回答
    answer = generator.generate(request.question, retrieved_docs)

    # 6. 解析引用
    citations = parse_citations(answer, retrieved_docs)

    # 7. 结构化数据校验
    validation_results = validator.validate_answer(answer)

    return QueryResponse(
        answer=answer,
        citations=citations,
        confidence_level=level,
        confidence_score=max_score,
        validation_results=validation_results,
        is_rejected=False,
        rejection_reason=None,
    )

# backend/models/schemas.py
from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class ConfidenceLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ValidationResult(str, Enum):
    CONSISTENT = "consistent"        # 一致
    INCONSISTENT = "inconsistent"    # 不一致
    UNVERIFIABLE = "unverifiable"    # 无法校验


class SchoolMajor(BaseModel):
    name: str
    exam_subjects: list[str]
    recent_scores: dict[str, dict[str, int]]
    admission_ratio: str
    acceptance_count: int
    recommend_ratio: float


class SchoolInfo(BaseModel):
    school_name: str
    location: str
    tags: list[str]
    cs_school: str
    majors: list[SchoolMajor]
    recommended: bool


class Citation(BaseModel):
    source_id: int
    school_name: str
    doc_title: str
    content: str
    similarity_score: float


class QueryRequest(BaseModel):
    question: str = Field(..., description="用户问题")


class ValidationItem(BaseModel):
    claim: str                           # 原始陈述
    extracted_value: str                 # 提取的数值
    expected_value: Optional[str]        # 期望值
    result: ValidationResult             # 校验结果


class QueryResponse(BaseModel):
    answer: str                          # LLM 生成的回答
    citations: list[Citation]            # 引用来源
    confidence_level: ConfidenceLevel    # 置信度等级
    confidence_score: float              # 置信度分数
    validation_results: list[ValidationItem]  # 数据校验结果
    is_rejected: bool = False            # 是否被拒答
    rejection_reason: Optional[str] = None  # 拒答原因

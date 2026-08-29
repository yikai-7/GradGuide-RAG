# backend/routers/structured.py
"""
结构化数据路由：/api/schools、/api/validate
提供院校标准答案查询与 LLM 回答校验接口。
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import List

from backend.dependencies import get_validation_service
from backend.services.validation import ValidationService
from backend.models.schemas import ValidationItem


class ValidateRequest(BaseModel):
    answer: str


router = APIRouter()


@router.get("/schools")
async def list_schools(
    validator: ValidationService = Depends(get_validation_service)
):
    """
    返回所有院校名称。
    """
    return {
        "schools": list(validator.schools_data.keys())
    }


@router.get("/schools/{school_name}")
async def get_school(
    school_name: str,
    validator: ValidationService = Depends(get_validation_service)
):
    """
    根据院校名称返回完整结构化数据（标准答案）。
    """
    school = validator.schools_data.get(school_name)
    if not school:
        return {"error": f"未找到院校：{school_name}"}
    return school


@router.post("/validate")
async def validate_answer(
    request: ValidateRequest,
    validator: ValidationService = Depends(get_validation_service)
) -> List[ValidationItem]:
    """
    对一段文本中的分数线、报录比、录取人数等关键数据进行校验。
    请求体示例：
    {
        "answer": "清华大学计算机专业2024年复试线总分330分。"
    }
    """
    return validator.validate_answer(request.answer)

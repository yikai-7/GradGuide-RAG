# backend/services/confidence.py
from backend.config import CONFIDENCE_THRESHOLD_HIGH, CONFIDENCE_THRESHOLD_LOW
from backend.models.schemas import ConfidenceLevel


class ConfidenceService:
    def evaluate(self, score: float) -> tuple[ConfidenceLevel, bool, str]:
        """
        评估置信度
        返回：(置信度等级, 是否拒答, 原因说明)
        """
        if score >= CONFIDENCE_THRESHOLD_HIGH:
            return ConfidenceLevel.HIGH, False, "检索结果高度相关"
        elif score >= CONFIDENCE_THRESHOLD_LOW:
            return ConfidenceLevel.MEDIUM, False, "检索结果部分相关，回答可能不够准确"
        else:
            return ConfidenceLevel.LOW, True, "未找到相关信息，建议换个问题或查看其他资料"

    def format_confidence_display(self, level: ConfidenceLevel) -> str:
        """格式化置信度显示"""
        emojis = {
            ConfidenceLevel.HIGH: "✅ 高",
            ConfidenceLevel.MEDIUM: "⚠️ 中",
            ConfidenceLevel.LOW: "❌ 低"
        }
        return emojis.get(level, "未知")

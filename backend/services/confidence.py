# backend/services/confidence.py
from backend.config import (
    CONFIDENCE_THRESHOLD_HIGH,
    CONFIDENCE_THRESHOLD_LOW,
    RECALL_FLOOR,
)
from backend.models.schemas import ConfidenceLevel


class ConfidenceService:
    def evaluate(self, score: float, coverage: float = 1.0) -> tuple[ConfidenceLevel, bool, str]:
        """
        评估置信度
        参数：
          score    - Reranker Top-1 单文档相关性分数
          coverage - 召回覆盖率（问题提到的学校被检索结果覆盖的比例，0~1）
        返回：(置信度等级, 是否拒答, 原因说明)

        核心改进：置信度 = 单文档相关性 + 召回充分性 两个维度。
        覆盖率满分说明"资料是齐的"，此时放宽拒答门槛，避免对比/开放类问题
        （如"清华和北邮哪个更好考"）因单文档分数低而被误拒答。
        """
        if coverage >= 1.0:
            # 问题涉及的学校都召回到了，资料齐全
            if score >= CONFIDENCE_THRESHOLD_HIGH:
                return ConfidenceLevel.HIGH, False, "检索结果高度相关"
            elif score >= CONFIDENCE_THRESHOLD_LOW:
                return ConfidenceLevel.MEDIUM, False, "检索结果部分相关，回答可能不够准确"
            elif score >= RECALL_FLOOR:
                # 覆盖率高但单文档分数一般：对比/开放类问题，资料齐全，放行
                return ConfidenceLevel.MEDIUM, False, "检索已覆盖问题涉及的院校，但单个文档相关度一般（对比/开放类问题）"
            else:
                # 覆盖率满分但分数极低：学校名在问题里，但内容完全不相关（如"医学部"）
                return ConfidenceLevel.LOW, True, "未找到相关信息，建议换个问题或查看其他资料"
        else:
            # 覆盖率不足：问题提到的学校没召回全
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

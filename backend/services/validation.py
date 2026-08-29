# backend/services/validation.py
import json
import re
from typing import List, Dict, Optional

from backend.config import RAW_DATA_DIR
from backend.models.schemas import ValidationItem, ValidationResult


class ValidationService:
    def __init__(self):
        self.schools_data = self._load_structured_data()

    def _load_structured_data(self) -> Dict[str, Dict]:
        """加载结构化数据（标准答案）"""
        schools_file = RAW_DATA_DIR / "schools.json"
        with open(schools_file, "r", encoding="utf-8") as f:
            schools = json.load(f)
        return {s["school_name"]: s for s in schools}

    def validate_answer(self, answer: str) -> List[ValidationItem]:
        """
        校验 LLM 回答中的关键数据
        目前支持：分数线、报录比、录取人数
        """
        results = []

        # 校验分数线
        results.extend(self._validate_scores(answer))

        # 校验报录比
        results.extend(self._validate_admission_ratio(answer))

        # 校验录取人数
        results.extend(self._validate_acceptance_count(answer))

        return results

    def _validate_scores(self, answer: str) -> List[ValidationItem]:
        """校验分数线数据"""
        results = []

        # 匹配模式：清华大学...2024年...总分330
        score_pattern = r'(\w+大学).*?(\d{4})年.*?总分(\d{3,4})'
        matches = re.findall(score_pattern, answer)

        for school_name, year, total_score in matches:
            expected = self._get_expected_score(school_name, year)
            if expected is not None:
                is_consistent = int(total_score) == expected
                results.append(ValidationItem(
                    claim=f"{school_name}{year}年总分分数线为{total_score}",
                    extracted_value=total_score,
                    expected_value=str(expected),
                    result=ValidationResult.CONSISTENT if is_consistent else ValidationResult.INCONSISTENT
                ))
            else:
                results.append(ValidationItem(
                    claim=f"{school_name}{year}年总分分数线为{total_score}",
                    extracted_value=total_score,
                    expected_value=None,
                    result=ValidationResult.UNVERIFIABLE
                ))

        return results

    def _validate_admission_ratio(self, answer: str) -> List[ValidationItem]:
        """校验报录比"""
        results = []

        # 匹配：报录比为X:1 或 报录比约X:1
        ratio_pattern = r'(\w+大学).*?报录比[约为]*(\d+):1'
        matches = re.findall(ratio_pattern, answer)

        for school_name, ratio in matches:
            expected = self._get_expected_ratio(school_name)
            if expected is not None:
                is_consistent = ratio == expected.split(":")[0]
                results.append(ValidationItem(
                    claim=f"{school_name}报录比为{ratio}:1",
                    extracted_value=f"{ratio}:1",
                    expected_value=expected,
                    result=ValidationResult.CONSISTENT if is_consistent else ValidationResult.INCONSISTENT
                ))

        return results

    def _validate_acceptance_count(self, answer: str) -> List[ValidationItem]:
        """校验录取人数"""
        results = []

        # 匹配：录取XXX人 或 招XXX人
        count_pattern = r'(\w+大学).*?录取[人数约]*(\d+)人'
        matches = re.findall(count_pattern, answer)

        for school_name, count in matches:
            expected = self._get_expected_count(school_name)
            if expected is not None:
                is_consistent = abs(int(count) - expected) <= 5  # 允许小误差
                results.append(ValidationItem(
                    claim=f"{school_name}录取人数为{count}人",
                    extracted_value=count,
                    expected_value=str(expected),
                    result=ValidationResult.CONSISTENT if is_consistent else ValidationResult.INCONSISTENT
                ))

        return results

    def _get_expected_score(self, school_name: str, year: str) -> Optional[int]:
        """获取期望的分数线"""
        school = self.schools_data.get(school_name)
        if not school:
            return None

        for major in school["majors"]:
            scores = major["recent_scores"].get(year)
            if scores:
                return scores["total"]
        return None

    def _get_expected_ratio(self, school_name: str) -> Optional[str]:
        """获取期望的报录比"""
        school = self.schools_data.get(school_name)
        if not school:
            return None

        for major in school["majors"]:
            return major["admission_ratio"]
        return None

    def _get_expected_count(self, school_name: str) -> Optional[int]:
        """获取期望的录取人数"""
        school = self.schools_data.get(school_name)
        if not school:
            return None

        for major in school["majors"]:
            return major["acceptance_count"]
        return None

    def format_validation_display(self, results: List[ValidationItem]) -> str:
        """格式化校验结果显示"""
        if not results:
            return "✅ 数据校验：无需校验的数据"

        lines = ["📊 数据校验结果："]
        for item in results:
            if item.result == ValidationResult.CONSISTENT:
                lines.append(f"  ✅ {item.claim}（正确）")
            elif item.result == ValidationResult.INCONSISTENT:
                lines.append(f"  ❌ {item.claim}（错误，应为{item.expected_value}）")
            else:
                lines.append(f"  ⚠️ {item.claim}（无法校验）")

        return "\n".join(lines)

# backend/services/generation.py
from openai import OpenAI
from typing import List, Dict, Tuple

from backend.config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL


class GenerationService:
    def __init__(self):
        self.client = OpenAI(
            api_key=DEEPSEEK_API_KEY,
            base_url=DEEPSEEK_BASE_URL
        )

    def build_prompt(self, question: str, retrieved_docs: List[Dict]) -> Tuple[str, str]:
        """构建带 Citation 的 Prompt"""
        # 构建上下文
        context_parts = []
        for i, doc in enumerate(retrieved_docs):
            school = doc["metadata"].get("school_name", "未知")
            doc_type = doc["metadata"].get("doc_type", "未知")
            context_parts.append(
                f"[来源{i+1}] ({school} - {doc_type})\n{doc['content']}"
            )

        context = "\n\n---\n\n".join(context_parts)

        system_prompt = """你是一个专业的考研择校顾问。请根据提供的检索资料回答用户问题。

【严格要求】
1. 回答中每句话必须标注来源，格式为 [来源X]，如 [来源1]、[来源2]
2. 如果检索资料中没有相关信息，请明确说明"根据现有资料无法回答该问题"
3. 绝对不要编造任何信息，如果不确定就说不确定
4. 回答要有条理，分点阐述

【回答格式】
先给出回答正文（每句话标注来源），然后在最后列出引用来源摘要"""

        user_prompt = f"""检索资料：
{context}

---

用户问题：{question}

请根据以上资料回答问题："""

        return system_prompt, user_prompt

    def generate(self, question: str, retrieved_docs: List[Dict]) -> str:
        """调用 LLM 生成回答"""
        system_prompt, user_prompt = self.build_prompt(question, retrieved_docs)

        response = self.client.chat.completions.create(
            model=DEEPSEEK_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,  # 低温度，减少幻觉
            max_tokens=1500
        )

        return response.choices[0].message.content

    def generate_with_rejection(self, question: str, rejection_reason: str) -> str:
        """生成拒答回复"""
        return f"抱歉，{rejection_reason}。"

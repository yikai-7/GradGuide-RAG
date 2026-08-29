# backend/utils/citation.py
import re
from typing import List, Dict
from backend.models.schemas import Citation


def parse_citations(llm_output: str, retrieved_docs: List[Dict]) -> List[Citation]:
    """
    解析 LLM 输出中的引用标注
    提取 [来源X] 标记，映射回源文档
    """
    citations = []
    seen_sources = set()

    # 匹配 [来源1]、[来源2] 等
    pattern = r'\[来源(\d+)\]'
    matches = re.findall(pattern, llm_output)

    for match in matches:
        source_idx = int(match) - 1  # 转为 0-indexed
        if source_idx in seen_sources:
            continue
        if source_idx < len(retrieved_docs):
            seen_sources.add(source_idx)
            doc = retrieved_docs[source_idx]

            citations.append(Citation(
                source_id=source_idx + 1,
                school_name=doc["metadata"].get("school_name", "未知"),
                doc_title=f"{doc['metadata'].get('doc_type', '文档')} - {doc['metadata'].get('source_file', '未知')}",
                content=doc["content"][:200] + "..." if len(doc["content"]) > 200 else doc["content"],
                similarity_score=doc.get("rerank_score", 0.0)
            ))

    # 按 source_id 排序
    citations.sort(key=lambda x: x.source_id)
    return citations


def format_citations_display(citations: List[Citation]) -> str:
    """格式化引用来源用于显示"""
    if not citations:
        return "无引用来源"

    lines = ["📎 引用来源："]
    for c in citations:
        lines.append(f"[来源{c.source_id}] {c.school_name} - {c.doc_title}（相关度：{c.similarity_score:.2f}）")

    return "\n".join(lines)

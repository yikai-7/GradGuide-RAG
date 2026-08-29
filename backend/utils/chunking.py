# backend/utils/chunking.py
from typing import List, Dict, Any
from backend.config import CHUNK_SIZE, CHUNK_OVERLAP


def recursive_chunk(
    text: str,
    chunk_size: int = CHUNK_SIZE,
    chunk_overlap: int = CHUNK_OVERLAP,
    separators: List[str] = None
) -> List[str]:
    """
    递归字符分块策略
    优先按大分隔符（段落）切分，不够再按小分隔符（句子）切分
    """
    if separators is None:
        separators = ["\n\n", "\n", "。", "！", "？", ".", "!", "?", " ", ""]

    chunks = []
    _recursive_split(text, chunk_size, chunk_overlap, separators, 0, chunks)
    return [c.strip() for c in chunks if c.strip()]


def _recursive_split(
    text: str,
    chunk_size: int,
    chunk_overlap: int,
    separators: List[str],
    sep_idx: int,
    chunks: List[str]
):
    if len(text) <= chunk_size:
        chunks.append(text)
        return

    if sep_idx >= len(separators):
        # 所有分隔符都试过了，强制按字符切
        for i in range(0, len(text), chunk_size - chunk_overlap):
            chunks.append(text[i:i + chunk_size])
        return

    separator = separators[sep_idx]
    if separator == "":
        # 空分隔符，直接按字符切
        for i in range(0, len(text), chunk_size - chunk_overlap):
            chunks.append(text[i:i + chunk_size])
        return

    parts = text.split(separator)
    current_chunk = ""

    for part in parts:
        test_chunk = current_chunk + separator + part if current_chunk else part
        if len(test_chunk) <= chunk_size:
            current_chunk = test_chunk
        else:
            if current_chunk:
                chunks.append(current_chunk)
            if len(part) > chunk_size:
                _recursive_split(part, chunk_size, chunk_overlap, separators, sep_idx + 1, chunks)
                current_chunk = ""
            else:
                current_chunk = part

    if current_chunk:
        chunks.append(current_chunk)


def create_chunks_with_metadata(
    text: str,
    metadata: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    创建带元数据的 chunks
    """
    chunks = recursive_chunk(text)
    result = []
    for i, chunk in enumerate(chunks):
        result.append({
            "content": chunk,
            "metadata": {
                **metadata,
                "chunk_index": i,
                "total_chunks": len(chunks)
            }
        })
    return result

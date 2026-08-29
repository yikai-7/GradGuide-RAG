# backend/services/ingestion.py
import json
import chromadb
from pathlib import Path
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any

from backend.config import (
    RAW_DATA_DIR, CHROMA_DIR, EMBEDDING_MODEL_NAME
)
from backend.utils.chunking import create_chunks_with_metadata


class IngestionService:
    def __init__(self):
        self.embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
        self.chroma_client = chromadb.PersistentClient(path=str(CHROMA_DIR))
        self.collection = self.chroma_client.get_or_create_collection(
            name="kaoyan_docs",
            metadata={"description": "考研择校文档集合"}
        )

    def load_school_introductions(self) -> List[Dict[str, Any]]:
        """加载院校介绍文本文件"""
        intro_dir = RAW_DATA_DIR / "introductions"
        documents = []

        for txt_file in intro_dir.glob("*.txt"):
            school_name = txt_file.stem  # 文件名即学校名
            content = txt_file.read_text(encoding="utf-8")

            # 创建带元数据的 chunks
            chunks = create_chunks_with_metadata(
                text=content,
                metadata={
                    "school_name": school_name,
                    "doc_type": "introduction",
                    "source_file": txt_file.name
                }
            )
            documents.extend(chunks)

        return documents

    def load_structured_data(self) -> List[Dict[str, Any]]:
        """加载结构化院校数据（同时用于校验）"""
        schools_file = RAW_DATA_DIR / "schools.json"
        with open(schools_file, "r", encoding="utf-8") as f:
            schools = json.load(f)

        documents = []
        for school in schools:
            # 将结构化数据转为文本描述，用于检索
            text = self._school_to_text(school)
            chunks = create_chunks_with_metadata(
                text=text,
                metadata={
                    "school_name": school["school_name"],
                    "doc_type": "structured",
                    "source_file": "schools.json"
                }
            )
            documents.extend(chunks)

        return documents

    def _school_to_text(self, school: dict) -> str:
        """将结构化数据转为可读文本"""
        lines = [f"{school['school_name']}考研招生信息"]
        lines.append(f"学校位置：{school['location']}")
        lines.append(f"学校标签：{', '.join(school['tags'])}")
        lines.append(f"计算机学院：{school['cs_school']}")

        for major in school["majors"]:
            lines.append(f"\n专业：{major['name']}")
            lines.append(f"考试科目：{', '.join(major['exam_subjects'])}")
            lines.append(f"报录比：{major['admission_ratio']}")
            lines.append(f"录取人数：{major['acceptance_count']}人")
            lines.append(f"推免比例：{major['recommend_ratio']*100:.0f}%")

            for year, scores in major["recent_scores"].items():
                lines.append(f"{year}年分数线：总分{scores['total']}，"
                           f"政治{scores['politics']}，英语{scores['english']}，"
                           f"数学{scores['math']}，专业课{scores['professional']}")

        return "\n".join(lines)

    def ingest(self):
        """执行完整的数据入库流程"""
        print("开始数据入库...")

        # 加载数据
        intro_docs = self.load_school_introductions()
        struct_docs = self.load_structured_data()
        all_docs = intro_docs + struct_docs

        print(f"共加载 {len(intro_docs)} 个介绍文档块，{len(struct_docs)} 个结构化文档块")

        # 生成 embeddings
        texts = [doc["content"] for doc in all_docs]
        embeddings = self.embedding_model.encode(texts, show_progress_bar=True)

        # 写入 ChromaDB
        ids = [f"doc_{i}" for i in range(len(all_docs))]
        metadatas = [doc["metadata"] for doc in all_docs]

        self.collection.add(
            ids=ids,
            documents=texts,
            embeddings=embeddings.tolist(),
            metadatas=metadatas
        )

        print(f"成功入库 {len(all_docs)} 个文档块到 ChromaDB")

    def clear(self):
        """清空已有数据"""
        self.chroma_client.delete_collection("kaoyan_docs")
        self.collection = self.chroma_client.get_or_create_collection(
            name="kaoyan_docs"
        )
        print("已清空 ChromaDB 数据")


if __name__ == "__main__":
    service = IngestionService()
    service.clear()
    service.ingest()

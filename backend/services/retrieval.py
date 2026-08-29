# backend/services/retrieval.py
import numpy as np
import chromadb
import jieba
from rank_bm25 import BM25Okapi
from sentence_transformers import CrossEncoder
from typing import List, Dict, Tuple
from collections import defaultdict

from backend.config import (
    CHROMA_DIR, EMBEDDING_MODEL_NAME, RERANKER_MODEL_NAME,
    BM25_TOP_K, VECTOR_TOP_K, RERANK_TOP_K, RRF_K
)


class RetrievalService:
    def __init__(self):
        # 向量检索
        self.chroma_client = chromadb.PersistentClient(path=str(CHROMA_DIR))
        self.collection = self.chroma_client.get_or_create_collection(
            name="kaoyan_docs"
        )

        # Embedding 模型
        from sentence_transformers import SentenceTransformer
        self.embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)

        # Reranker 模型
        self.reranker = CrossEncoder(RERANKER_MODEL_NAME)

        # BM25 索引
        self.bm25_index = None
        self.bm25_docs = None
        self._build_bm25_index()

    def _build_bm25_index(self):
        """构建 BM25 索引（中文用 jieba 分词）"""
        all_docs = self.collection.get()
        if not all_docs["documents"]:
            return

        self.bm25_docs = all_docs["documents"]
        self.bm25_ids = all_docs["ids"]
        self.bm25_metadatas = all_docs["metadatas"]

        # jieba 中文分词（指南注：简单切分实际可用 jieba，此处按工业标准实现）
        tokenized = [list(jieba.cut(doc)) for doc in self.bm25_docs]
        self.bm25_index = BM25Okapi(tokenized)

    def bm25_search(self, query: str, top_k: int = BM25_TOP_K) -> List[Dict]:
        """BM25 关键词检索"""
        if self.bm25_index is None:
            return []

        tokenized_query = list(jieba.cut(query))
        scores = self.bm25_index.get_scores(tokenized_query)

        # 获取 top_k
        top_indices = np.argsort(scores)[::-1][:top_k]

        results = []
        for idx in top_indices:
            if scores[idx] > 0:
                results.append({
                    "id": self.bm25_ids[idx],
                    "content": self.bm25_docs[idx],
                    "metadata": self.bm25_metadatas[idx],
                    "score": float(scores[idx])
                })

        return results

    def vector_search(self, query: str, top_k: int = VECTOR_TOP_K) -> List[Dict]:
        """向量语义检索"""
        query_embedding = self.embedding_model.encode(query).tolist()

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"]
        )

        # 转换为统一格式（ChromaDB 返回的是距离，需要转为相似度）
        formatted = []
        for i in range(len(results["ids"][0])):
            distance = results["distances"][0][i]
            # 距离转相似度（embedding 已归一化，distance ∈ [0, 2]）
            similarity = 1 - distance / 2

            formatted.append({
                "id": results["ids"][0][i],
                "content": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "score": similarity
            })

        return formatted

    def reciprocal_rank_fusion(
        self,
        bm25_results: List[Dict],
        vector_results: List[Dict],
        k: int = RRF_K
    ) -> List[Dict]:
        """RRF 融合两路检索结果（只看排名不看分数，量纲无关）"""
        scores = defaultdict(float)
        doc_map = {}

        # BM25 结果的 RRF 分数
        for rank, doc in enumerate(bm25_results):
            doc_id = doc["id"]
            scores[doc_id] += 1.0 / (k + rank + 1)
            doc_map[doc_id] = doc

        # 向量检索结果的 RRF 分数
        for rank, doc in enumerate(vector_results):
            doc_id = doc["id"]
            scores[doc_id] += 1.0 / (k + rank + 1)
            doc_map[doc_id] = doc

        # 按 RRF 分数排序
        sorted_ids = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)

        return [
            {
                **doc_map[doc_id],
                "rrf_score": scores[doc_id]
            }
            for doc_id in sorted_ids
        ]

    def rerank(self, query: str, documents: List[Dict], top_k: int = RERANK_TOP_K) -> List[Dict]:
        """使用 CrossEncoder Reranker 精排"""
        if not documents:
            return []

        # 构建 reranker 输入对（问题+文档拼接后一起过模型）
        pairs = [(query, doc["content"]) for doc in documents]

        # 计算相关性分数
        rerank_scores = self.reranker.predict(pairs)
        # 更新分数并排序
        for doc, score in zip(documents, rerank_scores):
            doc["rerank_score"] = float(score)

        sorted_docs = sorted(documents, key=lambda x: x["rerank_score"], reverse=True)

        return sorted_docs[:top_k]

    def retrieve(self, query: str) -> Tuple[List[Dict], float]:
        """
        完整检索流程：BM25 + 向量 → RRF 融合 → Reranker 精排
        返回：(检索结果列表, 最高置信度分数)
        """
        # 1. 两路检索
        bm25_results = self.bm25_search(query)
        vector_results = self.vector_search(query)

        # 2. RRF 融合
        fused_results = self.reciprocal_rank_fusion(bm25_results, vector_results)

        # 3. Reranker 精排
        reranked_results = self.rerank(query, fused_results)

        # 4. 计算置信度（取最高 rerank 分数）
        max_score = reranked_results[0]["rerank_score"] if reranked_results else 0.0

        return reranked_results, max_score

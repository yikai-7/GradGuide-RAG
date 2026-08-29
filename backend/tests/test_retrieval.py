# backend/test_retrieval.py
"""Phase 3 检索流程测试脚本"""
from backend.services.retrieval import RetrievalService
from backend.services.confidence import ConfidenceService


def main():
    print("=" * 50)
    print("初始化检索服务（加载模型中，首次需下载 Reranker）...")
    print("=" * 50)
    retriever = RetrievalService()
    conf = ConfidenceService()

    test_queries = [
        "清华大学计算机考研分数线是多少",
        "杭州电子科技大学的就业去向怎么样",
        "哪些学校报录比较低比较好考",
        "量子物理专业推荐",  # 知识库里没有，预期低置信度
    ]

    for q in test_queries:
        print("\n" + "=" * 50)
        print(f"问题：{q}")
        print("=" * 50)

        results, max_score = retriever.retrieve(q)
        level, rejected, reason = conf.evaluate(max_score)

        print(f"精排返回 {len(results)} 个文档，最高分 {max_score:.4f}")
        print(f"置信度：{conf.format_confidence_display(level)} | 拒答：{rejected} | {reason}")

        for i, doc in enumerate(results, 1):
            school = doc["metadata"].get("school_name", "?")
            dt = doc["metadata"].get("doc_type", "?")
            print(f"  [{i}] {school} ({dt}) rerank={doc['rerank_score']:.3f}"
                  f" rrf={doc.get('rrf_score', 0):.4f} | {doc['content'][:28]}...")


if __name__ == "__main__":
    main()

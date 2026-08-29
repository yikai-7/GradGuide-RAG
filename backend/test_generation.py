# backend/test_generation.py
"""Phase 4 生成服务测试脚本

用法：
  python -m backend.test_generation offline   # 离线测试（不需要 API Key）
  python -m backend.test_generation online    # 端到端测试（需要真实 DeepSeek Key）
"""
import sys

from backend.services.retrieval import RetrievalService
from backend.services.generation import GenerationService
from backend.utils.citation import parse_citations, format_citations_display


def test_offline():
    """离线测试：build_prompt + citation 解析（不调用 API）"""
    print("=" * 50)
    print("测试 1：build_prompt 构建")
    print("=" * 50)

    fake_docs = [
        {
            "id": "doc_x",
            "content": "清华大学2024年计算机复试线总分330。",
            "metadata": {"school_name": "清华大学", "doc_type": "structured", "source_file": "schools.json"},
            "rerank_score": 0.99,
        },
        {
            "id": "doc_y",
            "content": "杭电毕业生就业面向海康威视、大华等。",
            "metadata": {"school_name": "杭州电子科技大学", "doc_type": "introduction", "source_file": "杭州电子科技大学.txt"},
            "rerank_score": 0.85,
        },
    ]

    gen = GenerationService()
    system_prompt, user_prompt = gen.build_prompt("清华计算机分数线是多少？", fake_docs)

    assert "考研择校顾问" in system_prompt, "system prompt 缺少角色设定"
    assert "[来源1]" in user_prompt and "清华大学" in user_prompt, "user prompt 缺少来源1资料"
    assert "清华计算机分数线" in user_prompt, "user prompt 缺少用户问题"
    print("✅ build_prompt：system/user prompt 均正确注入资料和编号")

    print("\n" + "=" * 50)
    print("测试 2：citation 正则解析")
    print("=" * 50)

    # 模拟 LLM 输出（含重复引用、越界引用）
    fake_llm_output = (
        "清华大学2024年计算机复试线总分330分[来源1]。\n"
        "杭电毕业生就业面向海康威视等公司[来源2]。\n"
        "清华位于北京[来源1]。\n"  # 重复引用，应去重
        "无依据的话[来源9]。"       # 越界引用，应被忽略
    )

    citations = parse_citations(fake_llm_output, fake_docs)
    assert len(citations) == 2, f"应解析出 2 个去重引用，实际 {len(citations)}"
    assert citations[0].source_id == 1 and citations[0].school_name == "清华大学"
    assert citations[1].source_id == 2 and abs(citations[1].similarity_score - 0.85) < 1e-6
    print("✅ parse_citations：提取/去重/越界过滤/分数映射 全部正确")

    print("\n" + format_citations_display(citations))
    print("\n🎉 离线测试全部通过")


def test_online():
    """端到端测试：真实检索 → LLM 生成 → citation 解析"""
    print("=" * 50)
    print("端到端测试：检索 → 生成 → 引用解析")
    print("=" * 50)

    question = "清华大学计算机考研分数线是多少？"
    print(f"\n问题：{question}\n")

    retriever = RetrievalService()
    results, max_score = retriever.retrieve(question)
    print(f"[检索] 返回 {len(results)} 个文档，最高分 {max_score:.3f}")

    gen = GenerationService()
    answer = gen.generate(question, results)
    print(f"\n[LLM 回答]\n{answer}\n")

    citations = parse_citations(answer, results)
    print("=" * 50)
    print(format_citations_display(citations))
    print(f"\n[统计] 回答中被引用的来源数：{len(citations)}")
    if len(citations) == 0:
        print("⚠️ LLM 未输出任何引用标注，检查 prompt")
    else:
        print("🎉 端到端测试通过：每句话可溯源")


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "offline"
    if mode == "offline":
        test_offline()
    elif mode == "online":
        test_online()
    else:
        print(f"未知模式：{mode}，请用 offline 或 online")

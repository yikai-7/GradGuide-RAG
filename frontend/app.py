# frontend/app.py
"""
Phase 7: Streamlit 前端

通过 HTTP 调用 FastAPI 后端，展示带溯源、置信度、数据校验的问答结果。
启动方式：streamlit run frontend/app.py
"""
import streamlit as st
import requests

API_BASE_URL = "http://localhost:8000/api"

st.set_page_config(
    page_title="考研择校 RAG 系统",
    page_icon="🎓",
    layout="wide"
)

st.title("🎓 考研择校智能问答系统")
st.caption("基于 RAG 技术，带溯源机制和结构化数据校验")


# ========== 侧边栏 ==========
with st.sidebar:
    st.header("系统信息")
    st.markdown(
        """
        **技术栈**
        - LLM: DeepSeek
        - Embedding: BGE-small-zh
        - 向量库: ChromaDB
        - 检索: BM25 + 向量混合
        - 精排: BGE-Reranker
        """
    )

    st.divider()
    st.markdown("**后端状态**")
    try:
        resp = requests.get("http://localhost:8000/", timeout=2)
        if resp.status_code == 200:
            st.success("✅ 后端已连接")
        else:
            st.warning("⚠️ 后端响应异常")
    except Exception:
        st.error("❌ 后端未启动，请先运行 uvicorn backend.main:app --port 8000")

    st.divider()
    if st.button("🔄 重新入库数据"):
        with st.spinner("正在清空并重新入库..."):
            try:
                resp = requests.post(f"{API_BASE_URL}/documents/ingest", timeout=600)
                if resp.status_code == 200:
                    st.success("入库完成！")
                else:
                    st.error(f"入库失败：{resp.text}")
            except Exception as e:
                st.error(f"发生错误：{str(e)}")


# ========== 主界面 ==========
tab1, tab2 = st.tabs(["💬 智能问答", "📊 院校数据"])


# ====== Tab 1: 智能问答 ======
with tab1:
    st.header("问点什么？")
    question = st.text_input(
        "输入你的问题",
        placeholder="例如：清华计算机考研分数线是多少？"
    )

    if st.button("提问", type="primary") and question:
        with st.spinner("正在检索资料并生成回答..."):
            try:
                resp = requests.post(
                    f"{API_BASE_URL}/query",
                    json={"question": question},
                    timeout=120
                )

                if resp.status_code == 200:
                    data = resp.json()

                    # 显示回答
                    st.markdown("### 回答")
                    st.markdown(data["answer"])

                    # 显示置信度和校验结果
                    col1, col2 = st.columns(2)

                    with col1:
                        confidence = data["confidence_level"]
                        score = data["confidence_score"]
                        if confidence == "high":
                            st.success(f"✅ 置信度：高（{score:.2f}）")
                        elif confidence == "medium":
                            st.warning(f"⚠️ 置信度：中（{score:.2f}）")
                        else:
                            st.error(f"❌ 置信度：低（{score:.2f}）")

                    with col2:
                        if data["is_rejected"]:
                            st.error(f"🚫 已拒答：{data['rejection_reason']}")
                        elif data["validation_results"]:
                            consistent = sum(
                                1 for v in data["validation_results"]
                                if v["result"] == "consistent"
                            )
                            total = len(data["validation_results"])
                            if consistent == total:
                                st.success(f"✅ 数据校验：{consistent}/{total} 项正确")
                            else:
                                st.warning(f"⚠️ 数据校验：{consistent}/{total} 项正确")

                    # 显示引用来源
                    if data["citations"]:
                        st.markdown("---")
                        st.markdown("### 📎 引用来源")
                        for c in data["citations"]:
                            with st.expander(
                                f"[来源{c['source_id']}] {c['school_name']} - {c['doc_title']}"
                            ):
                                st.markdown(c["content"])
                                st.caption(f"相关度：{c['similarity_score']:.2f}")

                    # 显示校验详情
                    if data["validation_results"]:
                        st.markdown("---")
                        st.markdown("### 📊 数据校验详情")
                        for v in data["validation_results"]:
                            if v["result"] == "consistent":
                                st.markdown(f"✅ {v['claim']}")
                            elif v["result"] == "inconsistent":
                                st.markdown(f"❌ {v['claim']}（应为 {v['expected_value']}）")
                            else:
                                st.markdown(f"⚠️ {v['claim']}（无法校验）")

                else:
                    st.error(f"请求失败：{resp.text}")

            except Exception as e:
                st.error(f"发生错误：{str(e)}。请确认后端已启动。")


# ====== Tab 2: 院校数据 ======
with tab2:
    st.header("院校结构化数据")

    try:
        resp = requests.get(f"{API_BASE_URL}/schools", timeout=10)
        if resp.status_code == 200:
            schools = resp.json()

            for school in schools:
                with st.expander(f"{school['school_name']}（{', '.join(school['tags'])}）"):
                    st.markdown(f"**位置**：{school['location']}")
                    st.markdown(f"**学院**：{school['cs_school']}")

                    for major in school["majors"]:
                        st.markdown(f"#### {major['name']}")
                        st.markdown(f"**考试科目**：{', '.join(major['exam_subjects'])}")
                        st.markdown(f"**报录比**：{major['admission_ratio']}")
                        st.markdown(f"**录取人数**：{major['acceptance_count']}人")
                        st.markdown(f"**推免比例**：{major['recommend_ratio']*100:.0f}%")

                        st.markdown("**历年分数线**：")
                        for year, scores in major["recent_scores"].items():
                            st.markdown(
                                f"- {year}年：总分{scores['total']}"
                                f"（政治{scores['politics']} / 英语{scores['english']}"
                                f" / 数学{scores['math']} / 专业课{scores['professional']}）"
                            )

    except Exception as e:
        st.error(f"获取数据失败：{str(e)}。请确认后端已启动。")
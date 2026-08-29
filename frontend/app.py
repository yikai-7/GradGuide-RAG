# frontend/app.py
"""
Phase 7: Streamlit 前端

通过 HTTP 调用 FastAPI 后端，展示带溯源、置信度、数据校验的问答结果。
启动方式：streamlit run frontend/app.py
"""
import json

import streamlit as st
import requests

API_BASE_URL = "http://localhost:8000/api"

st.set_page_config(
    page_title="考研择校 RAG 系统",
    page_icon="🎓",
    layout="wide"
)

st.title("🎓 考研择校智能问答系统")


# ========== 侧边栏：数据管理 ==========
with st.sidebar:
    st.header("数据管理")

    with st.expander("📤 上传院校数据"):
        up_name = st.text_input("学校名称", key="up_name")
        up_intro = st.text_area("介绍文本（可选）", key="up_intro", height=150)
        up_struct = st.text_area("结构化数据 JSON（可选）", key="up_struct", height=150)

        if st.button("上传", key="btn_upload"):
            if not up_name.strip():
                st.error("请填写学校名称")
            else:
                payload = {"school_name": up_name.strip()}
                if up_intro.strip():
                    payload["introduction"] = up_intro
                if up_struct.strip():
                    try:
                        payload["structured"] = json.loads(up_struct)
                    except json.JSONDecodeError:
                        st.error("结构化数据 JSON 格式错误")
                        st.stop()

                with st.spinner("正在上传..."):
                    resp = requests.post(
                        f"{API_BASE_URL}/documents/upload",
                        json=payload,
                        timeout=30
                    )
                if resp.status_code == 200:
                    st.success(f"上传成功：{resp.json()['written']}")
                else:
                    st.error(f"上传失败：{resp.text}")

    st.divider()

    if st.button("🔄 重新入库数据", key="btn_ingest"):
        with st.spinner("正在清空并重新入库..."):
            resp = requests.post(f"{API_BASE_URL}/documents/ingest", timeout=600)
        if resp.status_code == 200:
            st.success("入库完成！")
        else:
            st.error(f"入库失败：{resp.text}")


# ========== 主界面：智能问答 ==========
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

            if resp.status_code != 200:
                st.error(f"请求失败：{resp.text}")
            else:
                data = resp.json()

                # 回答正文
                st.markdown("### 回答")
                st.markdown(data["answer"])

                # 置信度 + 校验摘要
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

                # 引用来源
                if data["citations"]:
                    st.markdown("---")
                    st.markdown("### 📎 引用来源")
                    for c in data["citations"]:
                        with st.expander(
                            f"[来源{c['source_id']}] {c['school_name']} - {c['doc_title']}"
                        ):
                            st.markdown(c["content"])
                            st.caption(f"相关度：{c['similarity_score']:.2f}")

                # 校验详情
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

        except Exception as e:
            st.error(f"发生错误：{str(e)}。请确认后端已启动。")
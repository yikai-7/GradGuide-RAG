# backend/test_api.py
"""
Phase 6 FastAPI 接口测试脚本

使用 FastAPI TestClient 直接调用接口，绕过 Windows 终端 GBK 编码问题，
也避免对运行中的 uvicorn 进程发起真实网络请求。

用法：
  python -m backend.test_api             # 全部接口测试（含 /api/query）
  python -m backend.test_api offline     # 跳过 /api/query（不加载检索模型、不调 LLM）
"""
import sys

from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def test_root():
    resp = client.get("/")
    assert resp.status_code == 200
    data = resp.json()
    assert "考研择校" in data["message"]
    print("✅ GET / 健康检查通过")


def test_schools():
    resp = client.get("/api/schools")
    assert resp.status_code == 200
    schools = resp.json()
    assert len(schools) > 0
    names = [s["school_name"] for s in schools]
    assert "清华大学" in names
    print(f"✅ GET /api/schools：返回 {len(schools)} 所院校 {names[:3]}...")


def test_school_detail():
    resp = client.get("/api/schools/清华大学")
    assert resp.status_code == 200
    data = resp.json()
    assert data["school_name"] == "清华大学"
    assert "majors" in data
    print(f"✅ GET /api/schools/清华大学：location={data['location']}, majors={len(data['majors'])}")

    resp404 = client.get("/api/schools/不存在的大学")
    assert "error" in resp404.json()
    print("✅ 不存在的院校正确返回 error")


def test_documents():
    resp = client.get("/api/documents")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] > 0
    print(f"✅ GET /api/documents：共 {data['total']} 个文档")

    first = data["documents"][0]
    resp2 = client.get(f"/api/documents/{first['id']}")
    assert resp2.status_code == 200
    print(f"✅ GET /api/documents/{{id}}：单文档查询通过")


def test_validate():
    # 正确数据
    resp = client.post("/api/validate", json={"answer": "清华大学计算机专业2024年复试线总分330分。"})
    assert resp.status_code == 200
    items = resp.json()
    assert len(items) == 1
    assert items[0]["result"] == "consistent"
    print("✅ POST /api/validate：正确分数线判 consistent")

    # 错误数据
    resp2 = client.post("/api/validate", json={"answer": "清华大学计算机专业2024年复试线总分350分。"})
    assert resp2.status_code == 200
    items2 = resp2.json()
    assert items2[0]["result"] == "inconsistent"
    assert items2[0]["expected_value"] == "330"
    print("✅ POST /api/validate：错误分数线判 inconsistent 并提示正确值 330")


def test_query_flow():
    resp = client.post("/api/query", json={"question": "清华计算机考研分数线是多少？"})
    assert resp.status_code == 200
    data = resp.json()
    assert "answer" in data
    assert "confidence_level" in data
    assert "citations" in data
    assert "validation_results" in data
    print(f"✅ POST /api/query：置信度={data['confidence_level']}，"
          f"引用数={len(data['citations'])}，校验项={len(data['validation_results'])}")
    if data["is_rejected"]:
        print(f"   （低置信度拒答：{data['rejection_reason']}）")
    else:
        print(f"   answer 前 80 字：{data['answer'][:80]}...")


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "online"

    print("=" * 50)
    print("Phase 6 FastAPI 接口测试")
    print("=" * 50)

    test_root()
    test_schools()
    test_school_detail()
    test_documents()
    test_validate()

    if mode == "offline":
        print("\n⚠️ 跳过 /api/query（offline 模式，不加载检索模型/不调 LLM）")
    else:
        print("\n[加载检索模型 + 调用 DeepSeek，可能需要较长时间...]")
        test_query_flow()

    print("\n" + "=" * 50)
    print("🎉 Phase 6 接口测试全部通过")
    print("=" * 50)


if __name__ == "__main__":
    main()
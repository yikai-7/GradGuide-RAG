# backend/test_confidence.py
"""
置信度升级（召回覆盖率）单元测试

验证 evaluate() 在引入 coverage 参数后，能正确区分：
- 对比类问题（覆盖率高但单文档分数一般 → 放行）
- 知识库外问题（覆盖率高但分数极低 → 仍拒答）
- 覆盖率不足（问题提到的学校没召回全 → 拒答）

用法：python -m backend.test_confidence
"""
from backend.services.confidence import ConfidenceService
from backend.models.schemas import ConfidenceLevel


def main():
    svc = ConfidenceService()

    print("=" * 50)
    print("置信度升级（召回覆盖率）单元测试")
    print("=" * 50)

    # 1. 对比类问题：覆盖率满分 + 分数 0.27（单文档相关性一般）
    level, reject, reason = svc.evaluate(0.27, coverage=1.0)
    print(f"\n对比问题(score=0.27, coverage=1.0): {level} 拒答={reject}")
    assert not reject and level == ConfidenceLevel.MEDIUM, \
        f"对比问题应放行为 MEDIUM，实际 {level}/拒答={reject}"
    print("✅ 对比类问题正确放行（不再误拒答）")

    # 2. 知识库外问题：覆盖率满分 + 分数 0.05（极低，如"医学部"）
    level, reject, reason = svc.evaluate(0.05, coverage=1.0)
    print(f"\n库外问题(score=0.05, coverage=1.0): {level} 拒答={reject}")
    assert reject and level == ConfidenceLevel.LOW, \
        f"库外问题应拒答，实际 {level}/拒答={reject}"
    print("✅ 知识库外问题仍正确拒答（分数极低）")

    # 3. 覆盖率不足：分数 0.3 + 覆盖率 0.5（只召回到一半学校）
    level, reject, reason = svc.evaluate(0.3, coverage=0.5)
    print(f"\n覆盖率不足(score=0.3, coverage=0.5): {level} 拒答={reject}")
    assert reject and level == ConfidenceLevel.LOW, \
        f"覆盖率不足应拒答，实际 {level}/拒答={reject}"
    print("✅ 覆盖率不足正确拒答")

    # 4. 高置信度：分数 0.9
    level, reject, reason = svc.evaluate(0.9, coverage=1.0)
    assert not reject and level == ConfidenceLevel.HIGH
    print("\n✅ 高置信度(0.9)正确判 HIGH")

    # 5. 中等置信度：分数 0.6
    level, reject, reason = svc.evaluate(0.6, coverage=1.0)
    assert not reject and level == ConfidenceLevel.MEDIUM
    print("✅ 中置信度(0.6)正确判 MEDIUM")

    # 6. 向后兼容：不传 coverage（默认 1.0）
    level, reject, reason = svc.evaluate(0.27)
    assert not reject and level == ConfidenceLevel.MEDIUM
    print("✅ 不传 coverage 默认满分，向后兼容")

    print("\n" + "=" * 50)
    print("🎉 置信度升级单元测试全部通过")
    print("=" * 50)


if __name__ == "__main__":
    main()

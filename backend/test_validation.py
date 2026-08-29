# backend/test_validation.py
"""Phase 5 结构化数据校验测试脚本

不需要 LLM / API Key，纯本地校验逻辑测试。
用法：python -m backend.test_validation
"""
from backend.services.validation import ValidationService
from backend.models.schemas import ValidationResult


def main():
    print("=" * 50)
    print("初始化校验服务（加载 schools.json 标准答案）...")
    print("=" * 50)
    validator = ValidationService()
    print(f"已加载 {len(validator.schools_data)} 所院校的结构化数据")

    # ------------------------------------------------------------------
    print("\n" + "=" * 50)
    print("测试 1：分数线校验（正确 / 错误 / 无法校验）")
    print("=" * 50)

    # 清华 2024 真实总分 = 330
    correct_answer = "清华大学计算机专业2024年复试线总分330分。"
    r1 = validator.validate_answer(correct_answer)
    print(f"输入：{correct_answer}")
    print(validator.format_validation_display(r1))
    assert len(r1) == 1 and r1[0].result == ValidationResult.CONSISTENT, \
        f"正确数字应判 CONSISTENT，实际 {r1}"

    wrong_answer = "清华大学计算机专业2024年复试线总分350分。"
    r2 = validator.validate_answer(wrong_answer)
    print(f"\n输入：{wrong_answer}")
    print(validator.format_validation_display(r2))
    assert len(r2) == 1 and r2[0].result == ValidationResult.INCONSISTENT, \
        f"错误数字应判 INCONSISTENT，实际 {r2}"
    assert r2[0].expected_value == "330", f"应提示正确值 330，实际 {r2[0].expected_value}"

    unknown_answer = "复旦大学计算机专业2024年复试线总分400分。"
    r3 = validator.validate_answer(unknown_answer)
    print(f"\n输入：{unknown_answer}")
    print(validator.format_validation_display(r3))
    assert len(r3) == 1 and r3[0].result == ValidationResult.UNVERIFIABLE, \
        f"知识库外的学校应判 UNVERIFIABLE，实际 {r3}"
    print("\n✅ 分数线校验：三种结果分类全部正确")

    # ------------------------------------------------------------------
    print("\n" + "=" * 50)
    print("测试 2：报录比校验（清华真实 = 8:1）")
    print("=" * 50)

    ratio_ok = "清华大学的报录比约为8:1，竞争比较激烈。"
    r4 = validator.validate_answer(ratio_ok)
    print(f"输入：{ratio_ok}")
    print(validator.format_validation_display(r4))
    assert any(x.result == ValidationResult.CONSISTENT for x in r4), \
        f"正确报录比应判 CONSISTENT，实际 {r4}"

    ratio_bad = "清华大学的报录比约为3:1，比较容易。"
    r5 = validator.validate_answer(ratio_bad)
    print(f"\n输入：{ratio_bad}")
    print(validator.format_validation_display(r5))
    assert any(x.result == ValidationResult.INCONSISTENT for x in r5), \
        f"错误报录比应判 INCONSISTENT，实际 {r5}"
    print("\n✅ 报录比校验：正确/错误均正确识别")

    # ------------------------------------------------------------------
    print("\n" + "=" * 50)
    print("测试 3：录取人数校验（清华真实 = 45，容差 ±5）")
    print("=" * 50)

    # 精确值 45
    count_ok = "清华大学计算机专业录取人数约45人。"
    r6 = validator.validate_answer(count_ok)
    print(f"输入：{count_ok}")
    print(validator.format_validation_display(r6))
    assert any(x.result == ValidationResult.CONSISTENT for x in r6), \
        f"精确人数应判 CONSISTENT，实际 {r6}"

    # 容差内 42（差3）
    count_near = "清华大学计算机专业录取人数约42人。"
    r7 = validator.validate_answer(count_near)
    print(f"\n输入：{count_near}")
    print(validator.format_validation_display(r7))
    assert any(x.result == ValidationResult.CONSISTENT for x in r7), \
        f"容差内人数(42,差3)应判 CONSISTENT，实际 {r7}"

    # 容差外 30（差15）
    count_far = "清华大学计算机专业录取人数约30人。"
    r8 = validator.validate_answer(count_far)
    print(f"\n输入：{count_far}")
    print(validator.format_validation_display(r8))
    assert any(x.result == ValidationResult.INCONSISTENT for x in r8), \
        f"容差外人数(30,差15)应判 INCONSISTENT，实际 {r8}"
    print("\n✅ 录取人数校验：精确/容差内/容差外 均正确")

    # ------------------------------------------------------------------
    print("\n" + "=" * 50)
    print("测试 4：综合回答（一次校验多类数据）")
    print("=" * 50)
    full_answer = (
        "清华大学计算机科学与技术专业2024年复试线总分330分，报录比约为8:1，"
        "录取人数约45人，推免比例较高。"
    )
    r9 = validator.validate_answer(full_answer)
    print(f"输入：{full_answer}")
    print(validator.format_validation_display(r9))
    n_consistent = sum(1 for x in r9 if x.result == ValidationResult.CONSISTENT)
    assert n_consistent == 3, f"综合回答应校验出 3 项全部正确，实际 {n_consistent} 项"
    print("\n✅ 综合回答：3 类数据一次性校验全部通过")

    print("\n" + "=" * 50)
    print("🎉 Phase 5 全部测试通过：数据校验防线工作正常")
    print("=" * 50)


if __name__ == "__main__":
    main()

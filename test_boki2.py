"""ジェネレータの検算テスト。

    python test_boki2.py
"""

from __future__ import annotations

import random
import sys

from boki2.exam import build_exam, grade_exam

N = 200
errors = []


def check_journal(b, ctx):
    d = sum(a for _, a in b["answer"]["debit"])
    c = sum(a for _, a in b["answer"]["credit"])
    if d != c:
        errors.append(f"{ctx} 貸借不一致 借{d:,} 貸{c:,} / {b['answer']}")
    for side in ("debit", "credit"):
        accs = [x[0] for x in b["answer"][side]]
        if len(accs) != len(set(accs)):
            errors.append(f"{ctx} {side}に同一科目が重複: {accs}")
        for acc, amt in b["answer"][side]:
            if amt <= 0:
                errors.append(f"{ctx} {side} 金額が0以下: {acc} {amt}")
            if acc not in b["choices"]:
                errors.append(f"{ctx} 正解科目が選択肢にない: {acc} / {b['choices']}")
    if len(b["choices"]) != len(set(b["choices"])):
        errors.append(f"{ctx} 選択肢が重複: {b['choices']}")


def main():
    rng = random.Random(0)
    for i in range(N):
        seed = rng.randrange(1, 10**9)
        exam = build_exam(seed)
        keys = set()
        for q in exam["questions"]:
            raw = sum(b["points"] for b in q["blocks"])
            if raw <= 0:
                errors.append(f"seed{seed} 第{q['no']}問 配点0")
            if not q["statement"].strip():
                errors.append(f"seed{seed} 第{q['no']}問 問題文が空")
            for b in q["blocks"]:
                ctx = f"seed{seed} 第{q['no']}問 {b['key']}"
                if b["key"] in keys:
                    errors.append(f"{ctx} キー重複")
                keys.add(b["key"])
                if b["type"] == "journal":
                    check_journal(b, ctx)
                elif b["type"] == "number":
                    if not isinstance(b["answer"], int):
                        errors.append(f"{ctx} 解答が整数でない: {b['answer']!r}")
                    if not b["explain"].strip():
                        errors.append(f"{ctx} 解説が空")
                else:
                    if b["answer"] not in b["options"]:
                        errors.append(f"{ctx} 正解が選択肢にない")

        # 満点の解答を作って100点になるか
        perfect = {}
        for q in exam["questions"]:
            for b in q["blocks"]:
                perfect[b["key"]] = b["answer"]
        res = grade_exam(exam, perfect)
        if abs(res["total"] - 100.0) > 0.35:
            errors.append(f"seed{seed} 満点解答が{res['total']}点")
        if not res["passed"]:
            errors.append(f"seed{seed} 満点なのに不合格判定")

        # 白紙は0点
        res0 = grade_exam(exam, {})
        if res0["total"] != 0:
            errors.append(f"seed{seed} 白紙が{res0['total']}点")

    print(f"検証した模試：{N}回")
    if errors:
        print(f"❌ 問題 {len(errors)}件")
        for e in errors[:40]:
            print("  -", e)
        sys.exit(1)
    print("✅ すべてOK（貸借一致・選択肢整合・満点100点・白紙0点）")


if __name__ == "__main__":
    main()

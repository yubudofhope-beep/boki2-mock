"""模擬試験1回分の組み立てと採点。"""

from __future__ import annotations

import random
from datetime import datetime

from . import q1, q2, q3, q4, q5
from .core import POINTS, PASS_SCORE

GENERATORS = {1: q1.generate, 2: q2.generate, 3: q3.generate, 4: q4.generate, 5: q5.generate}


def build_exam(seed: int | None = None, parts=(1, 2, 3, 4, 5),
               avoid: set[str] | None = None) -> dict:
    """avoid には直近に出題したテンプレート名を渡す（論点の偏りを防ぐ）。"""
    if seed is None:
        seed = random.randrange(1, 10**9)
    avoid = avoid or set()
    questions, used = [], []
    for no in parts:
        rng = random.Random(seed * 100 + no)   # 大問ごとに独立したシード
        gen = GENERATORS[no]
        try:
            q = gen(rng, avoid=avoid)
        except TypeError:                       # avoid 未対応のジェネレータ
            q = gen(rng)
        questions.append(q)
        used.extend(q.get("used", []))
    return {
        "seed": seed,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "parts": list(parts),
        "used": used,
        "questions": questions,
    }


# ---------------------------------------------------------------- 採点
def _norm_entries(entries):
    """[(科目, 金額)] を比較用の集合に。金額0や空欄は無視。"""
    out = []
    for acc, amt in entries:
        if acc and amt:
            out.append((str(acc).strip(), int(round(float(amt)))))
    return sorted(out)


def grade_block(block: dict, answer) -> dict:
    """1つの解答欄を採点し {earned, max, correct, given} を返す。"""
    mx = block["points"]
    if block["type"] == "journal":
        want_d = _norm_entries(block["answer"]["debit"])
        want_c = _norm_entries(block["answer"]["credit"])
        got_d = _norm_entries((answer or {}).get("debit", []))
        got_c = _norm_entries((answer or {}).get("credit", []))
        ok_d, ok_c = want_d == got_d, want_c == got_c
        earned = mx if (ok_d and ok_c) else (mx // 2 if (ok_d or ok_c) else 0)
        return {"earned": earned, "max": mx, "correct": ok_d and ok_c,
                "detail": {"debit_ok": ok_d, "credit_ok": ok_c}}
    if block["type"] == "number":
        try:
            ok = answer is not None and int(round(float(answer))) == block["answer"]
        except (TypeError, ValueError):
            ok = False
        return {"earned": mx if ok else 0, "max": mx, "correct": ok, "detail": {}}
    # choice
    ok = answer == block["answer"]
    return {"earned": mx if ok else 0, "max": mx, "correct": ok, "detail": {}}


def grade_exam(exam: dict, answers: dict) -> dict:
    """answers: {block_key: 解答} → 採点結果。"""
    per_part, per_topic = [], {}
    total = 0.0
    for q in exam["questions"]:
        raw = sum(b["points"] for b in q["blocks"])
        got = 0
        results = {}
        for b in q["blocks"]:
            r = grade_block(b, answers.get(b["key"]))
            results[b["key"]] = r
            got += r["earned"]
            topic = b.get("topic") or q["topic"]   # 仕訳は問題ごとの論点で集計
            t = per_topic.setdefault(topic, {"earned": 0, "max": 0})
            t["earned"] += r["earned"]
            t["max"] += r["max"]
        scaled = round(got / raw * POINTS[q["no"]], 1) if raw else 0
        total += scaled
        per_part.append({"no": q["no"], "title": q["title"], "topic": q["topic"],
                         "raw": got, "raw_max": raw, "score": scaled,
                         "full": POINTS[q["no"]], "results": results})
    total = round(total, 1)
    return {"per_part": per_part, "per_topic": per_topic,
            "total": total, "passed": total >= PASS_SCORE,
            "graded_at": datetime.now().isoformat(timespec="seconds")}

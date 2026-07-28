"""共通の型とユーティリティ。

問題オブジェクトの構造:
{
  "no": 1,                # 大問番号
  "title": "第1問（20点）",
  "topic": "商業簿記/仕訳",
  "statement": "markdown文字列",
  "blocks": [ ... ],      # 解答欄の定義（下記）
  "explanation": "markdown文字列",
}

blocks の要素は 2 種類:
  {"type":"journal", "key":"q1_1", "label":"1.", "choices":[...], "points":4,
   "answer":{"debit":[("貸倒引当金",200000)], "credit":[("売掛金",200000)]},
   "explain":"..."}
  {"type":"number", "key":"...", "label":"...", "points":2, "answer":123456,
   "unit":"円", "explain":"..."}
  {"type":"choice", "key":"...", "label":"...", "options":[...], "points":2,
   "answer":"売買目的有価証券", "explain":"..."}
"""

from __future__ import annotations

import random


def yen(n) -> str:
    """金額を 1,234,567 形式に。"""
    if n is None:
        return ""
    neg = n < 0
    s = f"{abs(int(round(n))):,}"
    return ("△" + s) if neg else s


def journal(key, label, choices, debit, credit, explain, points=4):
    return {
        "type": "journal",
        "key": key,
        "label": label,
        "choices": list(choices),
        "points": points,
        "answer": {"debit": list(debit), "credit": list(credit)},
        "explain": explain,
    }


def number(key, label, answer, points=2, unit="円", explain="", sign_note=None, trap=None):
    return {
        "type": "number",
        "key": key,
        "label": label,
        "points": points,
        "answer": int(round(answer)),
        "unit": unit,
        "explain": explain,
        "sign_note": sign_note,
        "trap": trap,
    }


def choice(key, label, options, answer, points=2, explain=""):
    return {
        "type": "choice",
        "key": key,
        "label": label,
        "options": list(options),
        "points": points,
        "answer": answer,
        "explain": explain,
    }


def rnd(rng: random.Random, lo: int, hi: int, step: int = 1) -> int:
    """lo〜hi を step 刻みでランダムに。"""
    return rng.randrange(lo, hi + 1, step)


def shuffled_choices(rng: random.Random, correct_accounts, distractors):
    """勘定科目の選択肢（正解を含む6個）をシャッフルして返す。"""
    pool = list(dict.fromkeys(correct_accounts))
    extra = [d for d in distractors if d not in pool]
    rng.shuffle(extra)
    while len(pool) < 6 and extra:
        pool.append(extra.pop())
    rng.shuffle(pool)
    return pool


# 大問ごとの配点（本試験に準拠）
POINTS = {1: 20, 2: 20, 3: 20, 4: 28, 5: 12}
PASS_SCORE = 70

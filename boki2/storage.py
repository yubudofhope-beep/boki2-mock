"""ユーザーごとの成績履歴と出題履歴の保存（JSON）。

Streamlit Community Cloud ではファイルが永続化されない場合があるため、
書き込みに失敗しても例外を投げず、セッション中だけの記録として動作する。
"""

from __future__ import annotations

import json
import re
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "boki2_data"
RECENT_LIMIT = 2          # 直近何回分の論点を避けるか


def _safe(name: str) -> str:
    name = (name or "guest").strip() or "guest"
    return re.sub(r"[^\w぀-ヿ一-鿿-]", "_", name)[:32]


def _path(user: str) -> Path:
    return DATA_DIR / f"history_{_safe(user)}.json"


def list_users() -> list[str]:
    if not DATA_DIR.exists():
        return []
    users = []
    for p in sorted(DATA_DIR.glob("history_*.json")):
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            users.append(data.get("user") or p.stem[len("history_"):])
        except (json.JSONDecodeError, OSError):
            continue
    return users


def _load(user: str) -> dict:
    p = _path(user)
    if p.exists():
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
            d.setdefault("user", user)
            d.setdefault("results", [])
            return d
        except (json.JSONDecodeError, OSError):
            pass
    return {"user": user, "results": []}


def _write(user: str, data: dict) -> bool:
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        _path(user).write_text(json.dumps(data, ensure_ascii=False, indent=2),
                               encoding="utf-8")
        return True
    except OSError:
        return False       # クラウド等で書き込めない環境


def load_history(user: str) -> list:
    return _load(user)["results"]


def save_result(user: str, exam: dict, result: dict) -> bool:
    data = _load(user)
    data["results"].append({
        "seed": exam["seed"],
        "graded_at": result["graded_at"],
        "total": result["total"],
        "passed": result["passed"],
        "used": exam.get("used", []),
        "per_part": [{"no": p["no"], "topic": p["topic"], "score": p["score"], "full": p["full"]}
                     for p in result["per_part"]],
        "per_topic": result["per_topic"],
    })
    return _write(user, data)


def save_issued(user: str, exam: dict) -> bool:
    """採点前でも「出題した論点」を記録しておく（ローテーション用）。"""
    data = _load(user)
    data.setdefault("issued", []).append(exam.get("used", []))
    data["issued"] = data["issued"][-20:]
    return _write(user, data)


def recent_topics(user: str, limit: int = RECENT_LIMIT) -> set[str]:
    """直近 limit 回に出題したテンプレート名の集合。"""
    data = _load(user)
    seq = data.get("issued", [])
    used = set()
    for batch in seq[-limit:]:
        used.update(batch)
    return used


def weak_points(user: str) -> list:
    agg = {}
    for h in load_history(user):
        for topic, v in h.get("per_topic", {}).items():
            a = agg.setdefault(topic, {"earned": 0, "max": 0, "times": 0})
            a["earned"] += v["earned"]
            a["max"] += v["max"]
            a["times"] += 1
    rows = [{"topic": t, "rate": (v["earned"] / v["max"] if v["max"] else 0),
             "earned": v["earned"], "max": v["max"], "times": v["times"]}
            for t, v in agg.items()]
    return sorted(rows, key=lambda r: r["rate"])

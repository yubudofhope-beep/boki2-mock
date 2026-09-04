"""成績・ログイン履歴の保存層。

接続情報（st.secrets の [supabase] url / key）があれば Supabase（クラウドDB）に、
なければ手元の SQLite ファイルに保存する。どちらでも同じ関数を使える。

    from boki2 import db
    db.log_login("ゆーき")
    db.save_result("ゆーき", exam, result)
"""

from __future__ import annotations

import hashlib
import json
import os
import secrets as secrets_mod
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "boki2_data"
SQLITE_PATH = DATA_DIR / "boki2.sqlite3"
RECENT_LIMIT = 2      # 直近何回分の論点を避けるか


def now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


# ================================================================ SQLite
class SqliteStore:
    kind = "SQLite（このPC内のファイル）"

    def __init__(self, path: Path = SQLITE_PATH):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init()

    def _conn(self):
        c = sqlite3.connect(self.path, timeout=10)
        c.row_factory = sqlite3.Row
        return c

    def _init(self):
        with self._conn() as c:
            c.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                name TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                pin_salt TEXT,
                pin_hash TEXT);
            CREATE TABLE IF NOT EXISTS logins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_name TEXT NOT NULL,
                at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_name TEXT NOT NULL,
                at TEXT NOT NULL,
                seed INTEGER,
                total REAL,
                passed INTEGER,
                per_part TEXT,
                per_topic TEXT,
                used TEXT);
            CREATE TABLE IF NOT EXISTS issued (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_name TEXT NOT NULL,
                at TEXT NOT NULL,
                used TEXT);
            """)
            # 既存DBに列を足す（すでにあればエラーを無視）
            for col in ("pin_salt TEXT", "pin_hash TEXT"):
                try:
                    c.execute(f"ALTER TABLE users ADD COLUMN {col}")
                except sqlite3.OperationalError:
                    pass

    # -------------------------------------------------- 書き込み
    def ensure_user(self, user):
        with self._conn() as c:
            c.execute("INSERT OR IGNORE INTO users(name, created_at) VALUES (?,?)",
                      (user, now()))

    def get_user(self, name):
        with self._conn() as c:
            r = c.execute("SELECT name, pin_salt, pin_hash FROM users WHERE name = ?",
                          (name,)).fetchone()
        return dict(r) if r else None

    def create_user(self, name, salt, hashed):
        with self._conn() as c:
            c.execute("INSERT INTO users(name, created_at, pin_salt, pin_hash) VALUES (?,?,?,?)",
                      (name, now(), salt, hashed))

    def set_pin(self, name, salt, hashed):
        with self._conn() as c:
            c.execute("UPDATE users SET pin_salt=?, pin_hash=? WHERE name=?",
                      (salt, hashed, name))

    def log_login(self, user):
        self.ensure_user(user)
        with self._conn() as c:
            c.execute("INSERT INTO logins(user_name, at) VALUES (?,?)", (user, now()))

    def save_issued(self, user, used):
        self.ensure_user(user)
        with self._conn() as c:
            c.execute("INSERT INTO issued(user_name, at, used) VALUES (?,?,?)",
                      (user, now(), json.dumps(used, ensure_ascii=False)))

    def save_result(self, user, row):
        self.ensure_user(user)
        with self._conn() as c:
            c.execute("""INSERT INTO results(user_name, at, seed, total, passed,
                                             per_part, per_topic, used)
                         VALUES (?,?,?,?,?,?,?,?)""",
                      (user, row["at"], row["seed"], row["total"], int(row["passed"]),
                       json.dumps(row["per_part"], ensure_ascii=False),
                       json.dumps(row["per_topic"], ensure_ascii=False),
                       json.dumps(row["used"], ensure_ascii=False)))

    # -------------------------------------------------- 読み出し
    def list_users(self):
        with self._conn() as c:
            return [r["name"] for r in c.execute("SELECT name FROM users ORDER BY name")]

    def results(self, user=None):
        q = "SELECT * FROM results"
        args = ()
        if user:
            q += " WHERE user_name = ?"
            args = (user,)
        q += " ORDER BY at"
        with self._conn() as c:
            return [_decode(dict(r)) for r in c.execute(q, args)]

    def logins(self, limit=500):
        with self._conn() as c:
            return [dict(r) for r in c.execute(
                "SELECT user_name, at FROM logins ORDER BY at DESC LIMIT ?", (limit,))]

    def recent_used(self, user, limit=RECENT_LIMIT):
        with self._conn() as c:
            rows = c.execute("SELECT used FROM issued WHERE user_name=? "
                             "ORDER BY id DESC LIMIT ?", (user, limit)).fetchall()
        out = set()
        for r in rows:
            out.update(json.loads(r["used"] or "[]"))
        return out


def _decode(row: dict) -> dict:
    for k in ("per_part", "per_topic", "used"):
        v = row.get(k)
        if isinstance(v, str):
            try:
                row[k] = json.loads(v)
            except json.JSONDecodeError:
                row[k] = [] if k == "used" else {}
    row["passed"] = bool(row.get("passed"))
    return row


# ================================================================ Supabase
class SupabaseStore:
    kind = "Supabase（クラウドDB・どこからでも履歴が残る）"

    def __init__(self, url: str, key: str):
        from supabase import create_client
        self.cli = create_client(url, key)
        # 接続確認（テーブルが無ければ例外）
        self.cli.table("users").select("name").limit(1).execute()

    def ensure_user(self, user):
        self.cli.table("users").upsert({"name": user, "created_at": now()},
                                       on_conflict="name", ignore_duplicates=True).execute()

    def get_user(self, name):
        r = (self.cli.table("users").select("name, pin_salt, pin_hash")
             .eq("name", name).limit(1).execute())
        return r.data[0] if r.data else None

    def create_user(self, name, salt, hashed):
        self.cli.table("users").insert({"name": name, "created_at": now(),
                                        "pin_salt": salt, "pin_hash": hashed}).execute()

    def set_pin(self, name, salt, hashed):
        self.cli.table("users").update({"pin_salt": salt, "pin_hash": hashed}) \
            .eq("name", name).execute()

    def log_login(self, user):
        self.ensure_user(user)
        self.cli.table("logins").insert({"user_name": user, "at": now()}).execute()

    def save_issued(self, user, used):
        self.ensure_user(user)
        self.cli.table("issued").insert({"user_name": user, "at": now(), "used": used}).execute()

    def save_result(self, user, row):
        self.ensure_user(user)
        self.cli.table("results").insert({
            "user_name": user, "at": row["at"], "seed": row["seed"],
            "total": row["total"], "passed": bool(row["passed"]),
            "per_part": row["per_part"], "per_topic": row["per_topic"],
            "used": row["used"]}).execute()

    def list_users(self):
        r = self.cli.table("users").select("name").order("name").execute()
        return [x["name"] for x in r.data]

    def results(self, user=None):
        q = self.cli.table("results").select("*")
        if user:
            q = q.eq("user_name", user)
        return [_decode(x) for x in q.order("at").execute().data]

    def logins(self, limit=500):
        r = (self.cli.table("logins").select("user_name, at")
             .order("at", desc=True).limit(limit).execute())
        return r.data

    def recent_used(self, user, limit=RECENT_LIMIT):
        r = (self.cli.table("issued").select("used").eq("user_name", user)
             .order("id", desc=True).limit(limit).execute())
        out = set()
        for x in r.data:
            out.update(x.get("used") or [])
        return out


# ================================================================ 切り替え
_store = None
_error = None


def _secrets():
    """st.secrets → 環境変数 の順に接続情報を探す。"""
    url = key = None
    try:
        import streamlit as st
        sec = st.secrets.get("supabase", {})
        url, key = sec.get("url"), sec.get("key")
    except Exception:
        pass
    url = url or os.environ.get("SUPABASE_URL")
    key = key or os.environ.get("SUPABASE_KEY")
    return url, key


def get_store():
    global _store, _error
    if _store is not None:
        return _store
    url, key = _secrets()
    if url and key:
        try:
            _store = SupabaseStore(url, key)
            return _store
        except Exception as e:      # 接続失敗時はSQLiteに落とす
            _error = f"{type(e).__name__}: {e}"
    _store = SqliteStore()
    return _store


def backend_info():
    s = get_store()
    return s.kind, _error


# ---------------------------------------------------------------- 合言葉（ログイン）
def _hash(pin: str, salt: str) -> str:
    """合言葉は平文で保存せず、ソルト付きハッシュにして保存する。"""
    return hashlib.pbkdf2_hmac("sha256", pin.encode("utf-8"),
                               bytes.fromhex(salt), 200_000).hex()


def name_taken(name: str) -> bool:
    try:
        return get_store().get_user(name) is not None
    except Exception:
        return False


def register(name: str, pin: str):
    """新規登録。成功なら (True, "") 、失敗なら (False, 理由)。"""
    name = (name or "").strip()
    if len(name) < 1:
        return False, "名前を入力してください。"
    if len(pin or "") < 4:
        return False, "合言葉は4文字以上にしてください。"
    try:
        store = get_store()
        if store.get_user(name) is not None:
            return False, f"「{name}」はすでに使われています。別の名前にしてください。"
        salt = secrets_mod.token_hex(16)
        store.create_user(name, salt, _hash(pin, salt))
        return True, ""
    except Exception as e:
        return False, f"登録できませんでした（{type(e).__name__}）"


def authenticate(name: str, pin: str):
    """ログイン。成功なら (True, "")。"""
    name = (name or "").strip()
    try:
        u = get_store().get_user(name)
    except Exception as e:
        return False, f"接続できませんでした（{type(e).__name__}）"
    if u is None:
        return False, "名前か合言葉が違います。"
    if not u.get("pin_hash"):
        # 合言葉を設定する前に作られた古いユーザー → この場で設定する
        if len(pin or "") < 4:
            return False, "この名前にはまだ合言葉が設定されていません。4文字以上で設定してください。"
        salt = secrets_mod.token_hex(16)
        try:
            get_store().set_pin(name, salt, _hash(pin, salt))
        except Exception:
            return False, "合言葉を保存できませんでした。"
        return True, "合言葉を設定しました。次回からこの合言葉でログインできます。"
    if _hash(pin or "", u["pin_salt"]) == u["pin_hash"]:
        return True, ""
    return False, "名前か合言葉が違います。"


def reset_pin(name: str) -> bool:
    """管理者用：合言葉を未設定に戻す（次回ログイン時に本人が付け直す）。"""
    try:
        get_store().set_pin(name, None, None)
        return True
    except Exception:
        return False


# ---------------------------------------------------------------- 共通API
def log_login(user):
    try:
        get_store().log_login(user)
        return True
    except Exception:
        return False


def save_issued(user, exam):
    try:
        get_store().save_issued(user, exam.get("used", []))
        return True
    except Exception:
        return False


def save_result(user, exam, result):
    row = {"at": result["graded_at"], "seed": exam["seed"], "total": result["total"],
           "passed": result["passed"], "used": exam.get("used", []),
           "per_part": [{"no": p["no"], "topic": p["topic"], "score": p["score"],
                         "full": p["full"]} for p in result["per_part"]],
           "per_topic": result["per_topic"]}
    try:
        get_store().save_result(user, row)
        return True
    except Exception:
        return False


def list_users():
    try:
        return get_store().list_users()
    except Exception:
        return []


def history(user):
    try:
        return get_store().results(user)
    except Exception:
        return []


def all_results():
    try:
        return get_store().results()
    except Exception:
        return []


def logins(limit=500):
    try:
        return get_store().logins(limit)
    except Exception:
        return []


def recent_topics(user, limit=RECENT_LIMIT):
    try:
        return get_store().recent_used(user, limit)
    except Exception:
        return set()


# ---------------------------------------------------------------- 集計
def topic_stats(rows):
    """results の行リストから論点別の正答率を集計する。"""
    agg = {}
    for h in rows:
        for topic, v in (h.get("per_topic") or {}).items():
            a = agg.setdefault(topic, {"earned": 0, "max": 0, "times": 0})
            a["earned"] += v.get("earned", 0)
            a["max"] += v.get("max", 0)
            a["times"] += 1
    out = [{"topic": t, "rate": (v["earned"] / v["max"] if v["max"] else 0),
            "earned": v["earned"], "max": v["max"], "times": v["times"]}
           for t, v in agg.items()]
    return sorted(out, key=lambda r: r["rate"])


def part_stats(rows):
    """大問別の平均得点率。"""
    agg = {}
    for h in rows:
        for p in (h.get("per_part") or []):
            a = agg.setdefault(p["no"], {"score": 0.0, "full": 0.0, "times": 0})
            a["score"] += p["score"]
            a["full"] += p["full"]
            a["times"] += 1
    return [{"no": no, "rate": (v["score"] / v["full"] if v["full"] else 0),
             "avg": (v["score"] / v["times"] if v["times"] else 0), "times": v["times"]}
            for no, v in sorted(agg.items())]


def user_summary():
    """管理者用：ユーザーごとの受験回数・平均・最高・直近・最終ログイン。"""
    rows = all_results()
    lg = logins(2000)
    last_login = {}
    login_count = {}
    for x in lg:
        u = x["user_name"]
        login_count[u] = login_count.get(u, 0) + 1
        if u not in last_login or x["at"] > last_login[u]:
            last_login[u] = x["at"]
    by_user = {}
    for r in rows:
        by_user.setdefault(r["user_name"], []).append(r)
    out = []
    for u in sorted(set(list(by_user) + list(last_login) + list_users())):
        rs = by_user.get(u, [])
        totals = [r["total"] for r in rs]
        out.append({
            "ユーザー": u,
            "受験回数": len(rs),
            "平均点": round(sum(totals) / len(totals), 1) if totals else None,
            "最高点": max(totals) if totals else None,
            "直近の点": totals[-1] if totals else None,
            "合格回数": sum(1 for r in rs if r["passed"]),
            "ログイン回数": login_count.get(u, 0),
            "最終ログイン": (last_login.get(u) or "")[:16].replace("T", " "),
        })
    return out

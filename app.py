"""日商簿記2級 模試メーカー（Streamlit）

ローカル起動:
    cd C:\\Users\\user\\MyPython\\apri
    python -m streamlit run app.py
"""

from __future__ import annotations

import os

import pandas as pd
import streamlit as st

from boki2 import db
from boki2.core import PASS_SCORE, yen
from boki2.exam import build_exam, grade_exam

st.set_page_config(page_title="簿記2級 模試メーカー", page_icon="🧮", layout="wide")

PART_LABELS = {1: "第1問 商業・仕訳", 2: "第2問 商業・個別論点",
               3: "第3問 商業・決算", 4: "第4問 工業", 5: "第5問 工業"}

ss = st.session_state
ss.setdefault("user", None)
ss.setdefault("answers", {})
ss.setdefault("result", None)
ss.setdefault("phone", False)
ss.setdefault("is_admin", False)
ss.setdefault("exam", None)


def admin_password() -> str:
    try:
        if "admin_password" in st.secrets:
            return str(st.secrets["admin_password"])
    except Exception:
        pass
    return os.environ.get("BOKI2_ADMIN_PASSWORD", "boki2-admin")


# ================================================================ ログイン
if not ss.user:
    st.title("🧮 簿記2級 模試メーカー")
    tab_in, tab_new = st.tabs(["ログイン", "はじめて使う"])

    with tab_in:
        st.write("自分の名前と合言葉を入れてください。")
        with st.form("login_form"):
            name = st.text_input("名前", max_chars=20, key="li_name")
            pin = st.text_input("合言葉", type="password", max_chars=40, key="li_pin")
            ok = st.form_submit_button("ログイン", type="primary", use_container_width=True)
        if ok:
            good, msg = db.authenticate(name, pin)
            if good:
                ss.user = name.strip()
                db.log_login(ss.user)
                if msg:
                    st.toast(msg, icon="🔑")
                st.rerun()
            else:
                st.error(msg)

    with tab_new:
        st.write("名前と合言葉を決めて登録します。同じ名前は登録できません。")
        with st.form("signup_form"):
            name2 = st.text_input("名前（ニックネームでOK）", max_chars=20, key="su_name")
            pin1 = st.text_input("合言葉（4文字以上）", type="password", max_chars=40, key="su_pin1")
            pin2 = st.text_input("合言葉をもう一度", type="password", max_chars=40, key="su_pin2")
            ok2 = st.form_submit_button("登録して始める", type="primary",
                                        use_container_width=True)
        if ok2:
            if pin1 != pin2:
                st.error("2つの合言葉が一致しません。")
            else:
                good, msg = db.register(name2, pin1)
                if good:
                    ss.user = name2.strip()
                    db.log_login(ss.user)
                    st.rerun()
                else:
                    st.error(msg)
        st.caption("合言葉は暗号化して保存され、管理者にも見えません。"
                   "忘れたときは管理者にリセットしてもらってください。")

    kind, err = db.backend_info()
    st.caption(f"保存先：{kind}")
    if err:
        st.caption(f"※クラウドDBに接続できなかったため手元に保存しています（{err}）")
    st.stop()

user = ss.user


# ================================================================ サイドバー
with st.sidebar:
    st.header("🧮 簿記2級 模試メーカー")
    st.write(f"👤 **{user}**" + ("　🛠 管理者" if ss.is_admin else ""))
    if st.button("名前を変える", use_container_width=True):
        ss.user = None
        ss.exam = None
        ss.is_admin = False
        st.rerun()

    ss.phone = st.toggle("📱 スマホ向け表示", value=ss.phone,
                         help="仕訳の入力欄を縦に並べます。画面が狭いときはオンに。")

    st.divider()
    st.subheader("模試を作る")
    parts = st.multiselect("出題する大問", [1, 2, 3, 4, 5], default=[1, 2, 3, 4, 5],
                           format_func=lambda n: PART_LABELS[n])
    rotate = st.checkbox("直近に出た論点を避ける", value=True)
    seed_text = st.text_input("シード（空欄でランダム）", "")
    if st.button("🆕 新しい模試を作る", type="primary", use_container_width=True):
        seed = int(seed_text) if seed_text.strip().isdigit() else None
        avoid = db.recent_topics(user) if rotate else set()
        exam = build_exam(seed, tuple(parts) or (1, 2, 3, 4, 5), avoid=avoid)
        db.save_issued(user, exam)
        ss.exam = exam
        ss.answers = {}
        ss.result = None
        st.rerun()
    st.caption("同じシードを入れると同じ問題を再現できます（復習用）。")

    st.divider()
    with st.expander("🛠 管理者"):
        if ss.is_admin:
            st.success("管理者モードです")
            if st.button("管理者モードを終了"):
                ss.is_admin = False
                st.rerun()
        else:
            pw = st.text_input("管理者パスワード", type="password")
            if st.button("ログイン"):
                if pw == admin_password():
                    ss.is_admin = True
                    st.rerun()
                else:
                    st.error("パスワードが違います")

    kind, err = db.backend_info()
    st.caption(f"保存先：{kind}")


# ================================================================ 解答欄
def show_trap(block):
    if block.get("trap"):
        st.warning("🪤 **ひっかけポイント**　" + block["trap"])


def render_journal(block, res):
    st.markdown(f"**{block['label']}**")
    opts = ["（未選択）"] + block["choices"]
    n_rows = max(3, len(block["answer"]["debit"]), len(block["answer"]["credit"]))
    rows_d, rows_c = [], []

    if ss.phone:
        st.caption("借方")
        for i in range(n_rows):
            a = st.selectbox(f"借方科目{i+1}", opts, key=f"{block['key']}_da{i}")
            m = st.number_input(f"借方金額{i+1}", min_value=0, step=1000,
                                key=f"{block['key']}_dm{i}")
            if a != "（未選択）" and m:
                rows_d.append((a, m))
        st.caption("貸方")
        for i in range(n_rows):
            a = st.selectbox(f"貸方科目{i+1}", opts, key=f"{block['key']}_ca{i}")
            m = st.number_input(f"貸方金額{i+1}", min_value=0, step=1000,
                                key=f"{block['key']}_cm{i}")
            if a != "（未選択）" and m:
                rows_c.append((a, m))
    else:
        c1, c2, c3, c4 = st.columns([3, 2, 3, 2])
        c1.caption("借方科目"); c2.caption("金額"); c3.caption("貸方科目"); c4.caption("金額")
        for i in range(n_rows):
            d_acc = c1.selectbox(f"借方科目{i}", opts, key=f"{block['key']}_da{i}",
                                 label_visibility="collapsed")
            d_amt = c2.number_input(f"借方金額{i}", min_value=0, step=1000,
                                    key=f"{block['key']}_dm{i}", label_visibility="collapsed")
            c_acc = c3.selectbox(f"貸方科目{i}", opts, key=f"{block['key']}_ca{i}",
                                 label_visibility="collapsed")
            c_amt = c4.number_input(f"貸方金額{i}", min_value=0, step=1000,
                                    key=f"{block['key']}_cm{i}", label_visibility="collapsed")
            if d_acc != "（未選択）" and d_amt:
                rows_d.append((d_acc, d_amt))
            if c_acc != "（未選択）" and c_amt:
                rows_c.append((c_acc, c_amt))

    ss.answers[block["key"]] = {"debit": rows_d, "credit": rows_c}

    if res:
        mark = "⭕" if res["correct"] else ("🔺" if res["earned"] else "❌")
        st.markdown(f"{mark} **{res['earned']} / {res['max']}点**")
        with st.expander("正解と解説", expanded=not res["correct"]):
            for side, label in (("debit", "借方"), ("credit", "貸方")):
                for acc, amt in block["answer"][side]:
                    st.write(f"　{label}：{acc}　{yen(amt)}")
            st.markdown(block["explain"].replace("\n", "  \n"))
            show_trap(block)


def render_number(block, res):
    label = block["label"] + (f"（{block['unit']}）" if block["unit"] else "")
    if block.get("sign_note"):
        label += f"　※{block['sign_note']}"
    ss.answers[block["key"]] = st.number_input(label, step=1, key=f"in_{block['key']}", value=0)
    if res:
        mark = "⭕" if res["correct"] else "❌"
        st.markdown(f"{mark} 正解：**{yen(block['answer'])}** {block['unit']}"
                    f"　（{res['earned']}/{res['max']}点）")
        if not res["correct"]:
            with st.expander("解説", expanded=True):
                st.markdown(block["explain"].replace("\n", "  \n"))
                show_trap(block)


def render_choice(block, res):
    opts = ["（未選択）"] + block["options"]
    ss.answers[block["key"]] = st.selectbox(block["label"], opts, key=f"in_{block['key']}")
    if res:
        mark = "⭕" if res["correct"] else "❌"
        st.markdown(f"{mark} 正解：**{block['answer']}**　{block['explain']}")


# ================================================================ 模試タブ
def page_exam():
    if not ss.exam:
        st.info("左のサイドバー（スマホは左上の «» ボタン）から"
                "「🆕 新しい模試を作る」を押してください。")
        return
    exam, result = ss.exam, ss.result
    st.caption(f"シード {exam['seed']}　／　目安 90分　／　合格 {PASS_SCORE}点")

    tabs = st.tabs([PART_LABELS[q["no"]] for q in exam["questions"]])
    for tab, q in zip(tabs, exam["questions"]):
        with tab:
            st.subheader(f"{q['title']}　〈{q['topic']}〉")
            st.markdown(q["statement"])
            st.divider()
            st.markdown("### 解答用紙")
            part_res = None
            if result:
                part_res = next((p for p in result["per_part"] if p["no"] == q["no"]), None)
            for b in q["blocks"]:
                r = part_res["results"][b["key"]] if part_res else None
                if b["type"] == "journal":
                    render_journal(b, r)
                    st.divider()
                elif b["type"] == "number":
                    render_number(b, r)
                else:
                    render_choice(b, r)
            if part_res:
                st.success(f"この大問の得点：{part_res['score']} / {part_res['full']}点")

    st.divider()
    if st.button("✅ 採点する", type="primary", use_container_width=True):
        res = grade_exam(exam, ss.answers)
        ss.result = res
        if not db.save_result(user, exam, res):
            st.toast("成績を保存できませんでした（画面には表示されます）", icon="⚠️")
        st.rerun()

    if result:
        st.header(f"採点結果：{result['total']} 点 / 100点　"
                  f"{'🎉 合格' if result['passed'] else '💪 もう一息'}")
        cols = st.columns(len(result["per_part"]))
        for c, p in zip(cols, result["per_part"]):
            c.metric(f"第{p['no']}問", f"{p['score']} / {p['full']}", help=p["topic"])
        st.subheader("この回の論点別")
        for topic, v in result["per_topic"].items():
            rate = v["earned"] / v["max"] if v["max"] else 0
            st.progress(rate, text=f"{topic}　{v['earned']}/{v['max']}（{rate:.0%}）")
        st.info("各大問のタブに戻ると、正解・解説・🪤ひっかけポイントが見られます。")


# ================================================================ マイ成績
def page_mypage():
    rows = db.history(user)
    if not rows:
        st.info("まだ採点結果がありません。模試を1回解くとここに記録されていきます。")
        return

    totals = [r["total"] for r in rows]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("受験回数", f"{len(rows)} 回")
    c2.metric("平均点", f"{sum(totals)/len(totals):.1f} 点")
    c3.metric("最高点", f"{max(totals):.1f} 点")
    c4.metric("合格回数", f"{sum(1 for r in rows if r['passed'])} 回",
              help=f"{PASS_SCORE}点以上")

    st.subheader("📈 点数の推移")
    chart = pd.DataFrame({
        "回": [f"{i+1}" for i in range(len(rows))],
        "点数": totals,
        "合格ライン": [PASS_SCORE] * len(rows),
    }).set_index("回")
    st.line_chart(chart)

    st.subheader("📊 大問別の得点率")
    ps = db.part_stats(rows)
    if ps:
        for p in ps:
            st.progress(min(p["rate"], 1.0),
                        text=f"{PART_LABELS[p['no']]}　平均 {p['avg']:.1f}点"
                             f"（得点率 {p['rate']:.0%}／{p['times']}回）")

    st.subheader("⚠️ 論点別の正答率（低い順＝苦手）")
    ts = db.topic_stats(rows)
    st.dataframe(pd.DataFrame([{
        "論点": t["topic"], "正答率": f"{t['rate']:.0%}",
        "得点": f"{t['earned']}/{t['max']}", "出題回数": t["times"],
    } for t in ts]), use_container_width=True, hide_index=True)

    st.subheader("🗒 受験履歴")
    hist_df = pd.DataFrame([{
        "日時": r["at"][:16].replace("T", " "),
        "点数": r["total"],
        "合否": "合格" if r["passed"] else "不合格",
        "シード": r["seed"],
        **{f"第{p['no']}問": p["score"] for p in (r.get("per_part") or [])},
    } for r in reversed(rows)])
    st.dataframe(hist_df, use_container_width=True, hide_index=True)
    st.caption("「シード」の数字をサイドバーに入れて模試を作ると、同じ問題をもう一度解けます。")
    st.download_button("⬇️ 自分の成績をCSVで保存",
                       hist_df.to_csv(index=False).encode("utf-8-sig"),
                       file_name=f"成績_{user}.csv", mime="text/csv")


# ================================================================ 管理者
def page_admin():
    st.subheader("👥 全ユーザーの成績一覧")
    summary = db.user_summary()
    if not summary:
        st.info("まだ記録がありません。")
        return
    sum_df = pd.DataFrame(summary)
    st.dataframe(sum_df, use_container_width=True, hide_index=True)
    st.download_button("⬇️ 成績一覧をCSVで保存",
                       sum_df.to_csv(index=False).encode("utf-8-sig"),
                       file_name="全ユーザー成績一覧.csv", mime="text/csv")

    with st.expander("🔑 合言葉を忘れた人の対応"):
        target = st.selectbox("リセットする人", ["（選んでください）"] + db.list_users())
        st.caption("リセットすると、その人が次にログインするときに入力した合言葉が"
                   "そのまま新しい合言葉になります。成績は消えません。")
        if st.button("合言葉をリセットする") and target != "（選んでください）":
            if db.reset_pin(target):
                st.success(f"「{target}」の合言葉をリセットしました。")
            else:
                st.error("リセットできませんでした。")

    all_rows = db.all_results()

    st.divider()
    st.subheader("🔥 論点別の苦手マップ（全員）")
    users = sorted({r["user_name"] for r in all_rows})
    topics = sorted({t for r in all_rows for t in (r.get("per_topic") or {})})
    if topics:
        grid = []
        for u in users:
            urows = [r for r in all_rows if r["user_name"] == u]
            stats = {t["topic"]: t["rate"] for t in db.topic_stats(urows)}
            grid.append({"ユーザー": u, **{t: (round(stats[t] * 100) if t in stats else None)
                                           for t in topics}})
        heat = pd.DataFrame(grid).set_index("ユーザー")
        st.dataframe(heat.style.background_gradient(cmap="RdYlGn", vmin=0, vmax=100,
                                                    axis=None).format("{:.0f}",
                                                                      na_rep="－"),
                     use_container_width=True)
        st.caption("数字は正答率（％）。赤いほど苦手、緑なら得意。「－」はまだ出題されていない論点。")

        st.markdown("**全員平均で苦手な論点 ワースト10**")
        worst = db.topic_stats(all_rows)[:10]
        for w in worst:
            st.progress(w["rate"], text=f"{w['topic']}　{w['rate']:.0%}"
                                        f"（延べ{w['times']}回）")

    st.divider()
    st.subheader("🕘 ログイン履歴")
    lg = db.logins(500)
    if lg:
        lg_df = pd.DataFrame([{"日時": x["at"][:19].replace("T", " "),
                               "ユーザー": x["user_name"]} for x in lg])
        st.dataframe(lg_df, use_container_width=True, hide_index=True, height=300)
        st.download_button("⬇️ ログイン履歴をCSVで保存",
                           lg_df.to_csv(index=False).encode("utf-8-sig"),
                           file_name="ログイン履歴.csv", mime="text/csv")
    else:
        st.info("ログイン履歴はまだありません。")

    st.divider()
    st.subheader("📄 全受験記録（生データ）")
    raw = pd.DataFrame([{
        "日時": r["at"][:19].replace("T", " "), "ユーザー": r["user_name"],
        "点数": r["total"], "合否": "合格" if r["passed"] else "不合格",
        "シード": r["seed"],
        **{f"第{p['no']}問": p["score"] for p in (r.get("per_part") or [])},
    } for r in reversed(all_rows)])
    st.dataframe(raw, use_container_width=True, hide_index=True, height=300)
    st.download_button("⬇️ 全受験記録をCSVで保存",
                       raw.to_csv(index=False).encode("utf-8-sig"),
                       file_name="全受験記録.csv", mime="text/csv")


# ================================================================ 画面切替
st.title("日商簿記2級 模擬試験")
names = ["📝 模試", "📊 マイ成績"] + (["🛠 管理"] if ss.is_admin else [])
pages = st.tabs(names)
with pages[0]:
    page_exam()
with pages[1]:
    page_mypage()
if ss.is_admin:
    with pages[2]:
        page_admin()

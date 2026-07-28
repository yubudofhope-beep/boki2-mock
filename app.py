"""日商簿記2級 模試メーカー（Streamlit）

ローカル起動:
    cd C:\\Users\\user\\MyPython\\apri
    python -m streamlit run app.py
スマホ・別PCから使う場合は README.md を参照。
"""

from __future__ import annotations

import streamlit as st

from boki2 import storage
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


# ================================================================ ログイン
def login_screen():
    st.title("🧮 簿記2級 模試メーカー")
    st.write("名前を選んでください。名前ごとに成績と苦手論点が記録されます。")
    users = storage.list_users()
    col1, col2 = st.columns(2)
    with col1:
        if users:
            pick = st.selectbox("登録済みの名前", ["（新しく作る）"] + users)
            if pick != "（新しく作る）" and st.button("この名前で始める", type="primary",
                                                     use_container_width=True):
                ss.user = pick
                st.rerun()
    with col2:
        new = st.text_input("新しい名前（ニックネームでOK）", max_chars=20)
        if st.button("はじめる", use_container_width=True,
                     type="primary" if not users else "secondary"):
            if new.strip():
                ss.user = new.strip()
                st.rerun()
            else:
                st.warning("名前を入力してください。")
    st.caption("※パスワードはありません。共有端末では他の人にも成績が見えます。")


if not ss.user:
    login_screen()
    st.stop()

user = ss.user


# ================================================================ サイドバー
with st.sidebar:
    st.header("🧮 簿記2級 模試メーカー")
    st.write(f"👤 **{user}**")
    if st.button("名前を変える", use_container_width=True):
        ss.user = None
        ss.exam = None
        st.rerun()

    ss.phone = st.toggle("📱 スマホ向け表示", value=ss.phone,
                         help="仕訳の入力欄を縦に並べます。画面が狭いときはオンに。")

    st.divider()
    parts = st.multiselect("出題する大問", [1, 2, 3, 4, 5], default=[1, 2, 3, 4, 5],
                           format_func=lambda n: PART_LABELS[n])
    rotate = st.checkbox("直近に出た論点を避ける", value=True,
                         help="同じ論点ばかり出ないように、直近3回で出た論点を除いて出題します。")
    seed_text = st.text_input("シード（空欄でランダム）", "")
    if st.button("🆕 新しい模試を作る", type="primary", use_container_width=True):
        seed = int(seed_text) if seed_text.strip().isdigit() else None
        avoid = storage.recent_topics(user) if rotate else set()
        exam = build_exam(seed, tuple(parts) or (1, 2, 3, 4, 5), avoid=avoid)
        storage.save_issued(user, exam)
        ss.exam = exam
        ss.answers = {}
        ss.result = None
        st.rerun()
    st.caption("同じシードを入れると同じ問題が再現できます（復習用）。")

    hist = storage.load_history(user)
    if hist:
        st.divider()
        st.subheader("📈 成績の推移")
        st.line_chart({"点数": [h["total"] for h in hist[-20:]]})
        st.caption(f"受験 {len(hist)}回／合格({PASS_SCORE}点以上) "
                   f"{sum(1 for h in hist if h['passed'])}回")

    weak = storage.weak_points(user)
    if weak:
        st.subheader("⚠️ 苦手な論点")
        for w in weak[:10]:
            st.progress(w["rate"], text=f"{w['topic']}　{w['rate']:.0%}")


if not ss.get("exam"):
    st.title("日商簿記2級 模擬試験")
    st.info("左のサイドバー（スマホは左上の «» ボタン）から"
            "「🆕 新しい模試を作る」を押してください。")
    st.stop()

exam = ss.exam
answers = ss.answers
result = ss.result


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

    answers[block["key"]] = {"debit": rows_d, "credit": rows_c}

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
    answers[block["key"]] = st.number_input(label, step=1, key=f"in_{block['key']}", value=0)
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
    answers[block["key"]] = st.selectbox(block["label"], opts, key=f"in_{block['key']}")
    if res:
        mark = "⭕" if res["correct"] else "❌"
        st.markdown(f"{mark} 正解：**{block['answer']}**　{block['explain']}")


# ================================================================ 本体
st.title("日商簿記2級 模擬試験")
st.caption(f"👤 {user}　／　シード {exam['seed']}　／　目安 90分　／　合格 {PASS_SCORE}点")

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
    res = grade_exam(exam, answers)
    ss.result = res
    if not storage.save_result(user, exam, res):
        st.toast("成績をファイルに保存できませんでした（この画面では表示できます）", icon="⚠️")
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
    st.info("各大問のタブに戻ると、まちがえた欄の正解・解説・🪤ひっかけポイントが表示されます。")

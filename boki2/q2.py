"""第2問（20点）：個別論点。有価証券 or 株主資本等変動計算書。"""

from __future__ import annotations

import random

from .core import choice, number, yen

HOLD_OPTIONS = ["売買目的有価証券", "満期保有目的の債券", "子会社株式", "関連会社株式", "その他有価証券"]


# ================================================================ A. 有価証券
def gen_yuka(rng: random.Random):
    shares = rng.choice([1000, 2000, 5000])
    p0 = rng.choice([200, 250, 300, 400])          # 取得単価
    fee_buy = rng.choice([1000, 2000, 5000])
    p1 = p0 + rng.choice([10, 14, 20, 25])          # ×1年度末時価
    sell_shares = rng.choice([200, 400, 500])
    if sell_shares >= shares:
        sell_shares = shares // 5
    p_sell = p1 + rng.choice([10, 15, 23, 30])      # 売却時単価
    fee_sell = rng.choice([200, 500, 1000])
    p2 = p1 + rng.choice([-10, 6, 12])              # ×2年度末時価

    rest = shares - sell_shares
    cost_total = p0 * shares + fee_buy              # 取得原価（付随費用込み）
    unit_cost = cost_total / shares

    # --- 売買目的（切放法）
    b_y1 = p1 * shares
    b_eval1 = b_y1 - cost_total
    b_book_sold = p1 * sell_shares
    proceeds = p_sell * sell_shares - fee_sell
    b_gain = proceeds - b_book_sold
    b_y2 = p2 * rest
    b_eval2 = b_y2 - p1 * rest

    # --- その他有価証券（全部純資産直入法・洗替法）
    o_y1 = p1 * shares
    o_diff1 = o_y1 - cost_total
    o_book_sold = unit_cost * sell_shares          # 洗替なので取得原価ベース
    o_gain = proceeds - o_book_sold
    o_y2 = p2 * rest
    o_diff2 = o_y2 - unit_cost * rest

    st = f"""問１　次の①〜⑥の有価証券について保有目的を答えなさい。

① Ａ社株式は安定株主の形成のために保有する株式であり、当社とＡ社でお互いの株式を保有している。当社の保有割合は１％である。
② Ｂ社株式は短期間の株価の値上がりによる売却益や配当による利殖を目的として保有する有価証券である。当該株式の運用は当社のトレーディング部門が担っている。
③ Ｃ社株式は長期的な利殖を目的として保有する株式である。
④ Ｄ社社債は長期の利殖目的で保有する社債であるが、将来の市場金利の動向次第では売却することも想定している。
⑤ Ｅ社社債は長期の利殖目的で取得したもので、満期まで所有する意図をもって保有する社債である。
⑥ Ｆ社株式はグループ経営を行うために取得した株式であり、当社の保有する株式数は160株である。なお、Ｆ社の発行済株式総数は200株である。

問２　次の〔資料〕にもとづいて設問に答えなさい。

〔資料〕
1. ×1年９月23日：甲社株式を{shares:,}株購入した。購入にあたり証券会社への支払手数料￥{yen(fee_buy)}が生じており、購入代価と合わせて普通預金から支払った。１株当たり時価￥{yen(p0)}。
2. ×1年12月31日（決算日）：１株当たり時価￥{yen(p1)}。
3. ×2年２月20日：×1年度に取得した甲社株式のうち{sell_shares:,}株を売却した。売却手数料￥{yen(fee_sell)}を差し引いた残額が普通預金に入金された。１株当たり時価￥{yen(p_sell)}。
4. ×2年12月31日（決算日）：１株当たり時価￥{yen(p2)}。

〔その他の事項〕
⑴ 当社の会計期間は１月から12月である。
⑵ 有価証券の売却損益は売却手数料と相殺して算定する。
⑶ 洗替法と切放法の両方が認められている場合には切放法を採用する。
⑷ 税効果会計は考慮しない。

設問１　甲社株式の保有目的が**売買目的有価証券**である場合の財務諸表計上額を求めなさい。
設問２　甲社株式の保有目的が**その他有価証券**である場合の財務諸表計上額を求めなさい（全部純資産直入法）。
"""

    ans1 = ["その他有価証券", "売買目的有価証券", "その他有価証券",
            "その他有価証券", "満期保有目的の債券", "子会社株式"]
    exp1 = [
        "持合株式で保有割合1%。売買目的でも支配・影響力もないため「その他有価証券」。",
        "トレーディング目的なので「売買目的有価証券」。",
        "長期の利殖目的の株式は「その他有価証券」。",
        "満期保有の意図がない（売却も想定）社債は「その他有価証券」。",
        "満期まで所有する意図が明確な社債は「満期保有目的の債券」。",
        "160株/200株＝80％で支配しているため「子会社株式」。",
    ]

    blocks = []
    for i, (a, e) in enumerate(zip(ans1, exp1)):
        blocks.append(choice(f"q2_h{i}", f"問1 {'①②③④⑤⑥'[i]}", HOLD_OPTIONS, a, points=1, explain=e))

    blocks += [
        number("q2_b1", "設問1 ×1年度 売買目的有価証券（B/S）", b_y1, points=2,
               explain=f"切放法・時価評価。{shares:,}株×@{yen(p1)} = {yen(b_y1)}"),
        number("q2_b2", "設問1 ×1年度 有価証券評価損益", b_eval1, points=2,
               explain=f"時価 {yen(b_y1)} − 取得原価 {yen(cost_total)}"
                       f"（@{yen(p0)}×{shares:,}株＋手数料{yen(fee_buy)}） = {yen(b_eval1)}",
               sign_note="評価益なら正、評価損なら負の数で入力"),
        number("q2_b3", "設問1 ×2年度 有価証券売却損益", b_gain, points=2,
               explain=f"手取額 @{yen(p_sell)}×{sell_shares:,}株 − 手数料{yen(fee_sell)} = {yen(proceeds)}\n"
                       f"簿価（切放法なので前期末時価）@{yen(p1)}×{sell_shares:,}株 = {yen(b_book_sold)}\n"
                       f"差額 {yen(b_gain)}",
               sign_note="売却益なら正、売却損なら負",
               trap="売買目的は**切放法**なので、売却時の簿価は取得原価ではなく"
                    f"前期末の時価@{yen(p1)}。取得原価@{yen(p0)}で計算すると外れる。"
                    "また手数料は売却損益に含めて（相殺して）計算する指示がある。"),
        number("q2_b4", "設問1 ×2年度 有価証券評価損益", b_eval2, points=2,
               explain=f"残{rest:,}株。時価 @{yen(p2)}×{rest:,} = {yen(b_y2)}、"
                       f"簿価 @{yen(p1)}×{rest:,} = {yen(p1*rest)} → {yen(b_eval2)}",
               sign_note="評価益なら正、評価損なら負"),
        number("q2_o1", "設問2 ×1年度 その他有価証券（B/S）", o_y1, points=2,
               explain=f"時価評価。{shares:,}株×@{yen(p1)} = {yen(o_y1)}"),
        number("q2_o2", "設問2 ×1年度 その他有価証券評価差額金", o_diff1, points=2,
               explain=f"{yen(o_y1)} − 取得原価 {yen(cost_total)} = {yen(o_diff1)}（貸方＝正）",
               sign_note="貸方残高なら正、借方残高なら負"),
        number("q2_o3", "設問2 ×2年度 投資有価証券売却損益", round(o_gain), points=2,
               explain=f"その他有価証券は洗替法。売却簿価は取得原価ベース "
                       f"@{unit_cost:,.1f}×{sell_shares:,}株 = {yen(o_book_sold)}\n"
                       f"手取額 {yen(proceeds)} − {yen(o_book_sold)} = {yen(o_gain)}",
               sign_note="売却益なら正、売却損なら負",
               trap="その他有価証券は**洗替法**が強制される。前期末の時価評価は期首に振り戻されて"
                    "いるので、売却簿価は取得原価ベース。売買目的と同じ計算をすると誤り。"
                    "科目名も「有価証券売却損益」ではなく**投資有価証券売却損益**。"),
        number("q2_o4", "設問2 ×2年度 その他有価証券評価差額金", round(o_diff2), points=2,
               explain=f"残{rest:,}株。時価 {yen(o_y2)} − 取得原価 {yen(unit_cost*rest)} = {yen(o_diff2)}",
               sign_note="貸方残高なら正、借方残高なら負"),
    ]
    return {
        "no": 2, "title": "第2問（20点）", "field": "商業簿記", "topic": "有価証券",
        "statement": st, "blocks": blocks, "explanation": "",
    }


# ================================================================ B. 株主資本等変動計算書
def gen_ss(rng: random.Random):
    cap = rng.choice([90_000, 120_000, 200_000]) * rng.choice([1, 10])
    cap_res = cap // rng.choice([6, 8, 9])
    profit_res = cap // rng.choice([10, 12, 15])
    building_res = rng.choice([30_000, 51_000, 80_000])
    retained = rng.choice([100_000, 108_000, 150_000])
    shares0 = 1_000
    div_per = rng.choice([20, 30, 40])
    div = div_per * shares0
    limit = cap / 4 - (cap_res + profit_res)
    res_add = int(min(div / 10, max(limit, 0)))
    new_res_add = rng.choice([5_000, 10_000, 20_000])
    new_shares = rng.choice([200, 300, 500])
    issue_price = rng.choice([300, 400, 500])
    paid = new_shares * issue_price
    cap_up = paid // 2
    cap_res_down = min(rng.choice([20_000, 50_000]), cap_res)
    ni = rng.choice([39_000, 52_000, 70_000])
    oci = rng.choice([2_000, 3_000, -1_500])

    end_cap = cap + cap_up
    end_cap_res = cap_res + (paid - cap_up) - cap_res_down
    end_other_cap = cap_res_down
    end_profit_res = profit_res + res_add
    end_building = building_res + new_res_add
    end_retained = retained - div - res_add - new_res_add + ni
    equity = end_cap + end_cap_res + end_other_cap + end_profit_res + end_building + end_retained
    total = equity + oci

    st = f"""以下の資料に基づき、当期（自×3年４月１日　至×4年３月31日）の株主資本等変動計算書を作成しなさい。

〔資料Ⅰ〕前期末貸借対照表の純資産の部（単位：円）

| 科目 | 金額 |
|---|---:|
| 資本金 | {yen(cap)} |
| 資本準備金 | {yen(cap_res)} |
| その他資本剰余金 | － |
| 利益準備金 | {yen(profit_res)} |
| 新築積立金 | {yen(building_res)} |
| 繰越利益剰余金 | {yen(retained)} |

〔資料Ⅱ〕期中取引等

1. 前期末現在の発行済株式総数は{shares0:,}株である。
2. ×3年６月27日の定時株主総会で決議：配当金 １株につき￥{div_per}（財源：利益剰余金）／利益準備金の積立：会社法規定の最低額／新築積立金の積立：￥{yen(new_res_add)}
3. ×3年９月１日に{new_shares}株の増資を行った。払込金額は１株当たり￥{issue_price}。資本金の増加額は会社法規定の最低額とする。
4. ×4年２月22日の臨時株主総会で、資本準備金￥{yen(cap_res_down)}を減少させ、その他資本剰余金に計上した（債権者保護手続は完了）。
5. ×4年３月31日決算：当期純利益￥{yen(ni)}／その他有価証券評価差額金￥{yen(abs(oci))}（{'貸方' if oci>=0 else '借方'}）
"""

    blocks = [
        number("ss_d_res", "剰余金の配当：利益準備金の積立額", res_add, points=2,
               explain=f"配当金 {yen(div)}（@{div_per}×{shares0:,}株）の1/10 = {yen(div//10)} と、"
                       f"資本金の1/4 {yen(cap/4)} −（資本準備金{yen(cap_res)}＋利益準備金{yen(profit_res)}）"
                       f"= {yen(limit)} の**小さい方** → {yen(res_add)}",
               trap="配当額の1/10を機械的に積むのは誤り。資本準備金と利益準備金の合計が"
                    "資本金の1/4に達するまでが上限で、**小さい方**を積み立てる。"),
        number("ss_d_re", "剰余金の配当：繰越利益剰余金の減少額", -(div + res_add), points=2,
               explain=f"配当 {yen(div)} ＋ 準備金積立 {yen(res_add)} = {yen(div+res_add)} の減少",
               sign_note="減少はマイナスで入力"),
        number("ss_cap_up", "増資：資本金の増加額", cap_up, points=2,
               explain=f"払込総額 {new_shares}株×{yen(issue_price)} = {yen(paid)}、最低額はその1/2 = {yen(cap_up)}"),
        number("ss_capres_up", "増資：資本準備金の増加額", paid - cap_up, points=2,
               explain=f"{yen(paid)} − {yen(cap_up)} = {yen(paid-cap_up)}"),
        number("ss_capres_down", "資本準備金の取崩：資本準備金の変動額", -cap_res_down, points=2,
               explain="その他資本剰余金へ振り替えるため減少（△表示）", sign_note="減少はマイナス"),
        number("ss_end_cap", "当期末残高：資本金", end_cap, points=2,
               explain=f"{yen(cap)} ＋ {yen(cap_up)} = {yen(end_cap)}"),
        number("ss_end_capres", "当期末残高：資本準備金", end_cap_res, points=2,
               explain=f"{yen(cap_res)} ＋ {yen(paid-cap_up)} − {yen(cap_res_down)} = {yen(end_cap_res)}"),
        number("ss_end_other", "当期末残高：その他資本剰余金", end_other_cap, points=1,
               explain=f"取崩分 {yen(cap_res_down)} がそのまま残高"),
        number("ss_end_pres", "当期末残高：利益準備金", end_profit_res, points=2,
               explain=f"{yen(profit_res)} ＋ {yen(res_add)} = {yen(end_profit_res)}"),
        number("ss_end_build", "当期末残高：新築積立金", end_building, points=1,
               explain=f"{yen(building_res)} ＋ {yen(new_res_add)} = {yen(end_building)}"),
        number("ss_end_re", "当期末残高：繰越利益剰余金", end_retained, points=2,
               explain=f"{yen(retained)} − 配当{yen(div)} − 準備金{yen(res_add)} − 新築積立{yen(new_res_add)}"
                       f" ＋ 当期純利益{yen(ni)} = {yen(end_retained)}"),
        number("ss_end_total", "当期末残高：純資産合計", total, points=2,
               explain=f"株主資本 {yen(equity)} ＋ その他有価証券評価差額金 {yen(oci)} = {yen(total)}"),
    ]
    return {
        "no": 2, "title": "第2問（20点）", "field": "商業簿記", "topic": "株主資本等変動計算書",
        "statement": st, "blocks": blocks, "explanation": "",
    }


def generate(rng: random.Random, avoid=None):
    avoid = avoid or set()
    pool = [g for g in (gen_yuka, gen_ss) if g.__name__ not in avoid] or [gen_yuka, gen_ss]
    chosen = rng.choice(pool)
    q = chosen(rng)
    q["used"] = [chosen.__name__]
    return q

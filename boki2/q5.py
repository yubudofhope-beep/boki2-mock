"""第5問（12点）：CVP分析 or 直接原価計算・全部原価計算の損益計算書。"""

from __future__ import annotations

import random

from .core import number, yen


# ================================================================ A. CVP分析
def gen_cvp(rng: random.Random):
    qty = rng.choice([5000, 6000, 8000, 10000])
    price = rng.choice([2500, 4000, 5000])
    # 変動費は販売単価の 50〜65％ に収める（貢献利益が必ず正になるように）
    v_total = price * rng.choice([50, 55, 60, 65]) // 100
    v_sell = rng.choice([100, 200, 300, 400])
    if v_sell >= v_total:
        v_sell = 100
    v_mfg = v_total - v_sell
    contrib_unit = price - v_total
    # 固定費は貢献利益総額の 60〜85％（＝営業利益が必ず正）
    fixed = contrib_unit * qty * rng.choice([60, 70, 75, 85]) // 100
    fixed_mfg = round(fixed * 0.7 / 10_000) * 10_000
    fixed_sga = fixed - fixed_mfg
    sales = price * qty
    contrib = contrib_unit * qty
    op = contrib - fixed
    ratio = contrib_unit / price

    bep_q = fixed / contrib_unit
    bep_s = bep_q * price
    target = rng.randrange(30, 60) * 100_000
    target_q = (fixed + target) / contrib_unit
    cut = rng.choice([10, 20])
    new_price = price * (100 - cut) // 100
    new_contrib = new_price - v_mfg - v_sell
    same_q = (fixed + op) / new_contrib if new_contrib > 0 else 0

    st = f"""当工場では製品Ｘを生産・販売しており、当期に{qty:,}個の生産・販売を行った。損益計算書（直接原価計算方式）は次のとおりである。次期における販売単価・製品単位あたり変動費額および期間あたり固定費額は当期と同一とする。仕掛品・製品の在庫はない。

〔資料〕損益計算書（単位：円）

| | 金額 | |
|---|---:|---|
| Ⅰ 売上高 | {yen(sales)} | （＠{yen(price)}円×{qty:,}個） |
| Ⅱ 変動売上原価 | {yen(v_mfg*qty)} | （＠{yen(v_mfg)}円×{qty:,}個） |
| 　製造マージン | {yen(sales - v_mfg*qty)} | |
| Ⅲ 変動販売費 | {yen(v_sell*qty)} | （＠{yen(v_sell)}円×{qty:,}個） |
| 　貢献利益 | {yen(contrib)} | |
| Ⅳ 固定製造原価 | {yen(fixed_mfg)} | |
| Ⅴ 固定販売費・一般管理費 | {yen(fixed_sga)} | |
| 　営業利益 | {yen(op)} | |

問１　次期における損益分岐点の販売数量を求めなさい。
問２　次期における損益分岐点の売上高を求めなさい。
問３　次期の目標営業利益{yen(target)}円を達成する販売数量を求めなさい。
問４　次期において販売価格を{cut}％値下げするものとして、当期と同額の営業利益を達成するための販売数量を求めなさい。
"""
    b = [
        number("cvp1", "問1 損益分岐点の販売数量", round(bep_q), 3, unit="個",
               explain=f"単位あたり貢献利益 = {yen(price)} − {yen(v_mfg)} − {yen(v_sell)} = {yen(contrib_unit)}\n"
                       f"固定費合計 {yen(fixed)} ÷ {yen(contrib_unit)} = {bep_q:,.1f} → {round(bep_q):,}個"),
        number("cvp2", "問2 損益分岐点の売上高", round(bep_s), 3,
               explain=f"{round(bep_q):,}個×@{yen(price)} = {yen(bep_s)}\n"
                       f"（別解：固定費 {yen(fixed)} ÷ 貢献利益率 {ratio:.1%}）",
               trap="貢献利益「率」で割るのであって、貢献利益「額」で割ると個数が出てしまう。"
                    "また変動費率で割るのは誤り。"),
        number("cvp3", "問3 目標営業利益を達成する販売数量", round(target_q), 3, unit="個",
               explain=f"（固定費 {yen(fixed)} ＋ 目標利益 {yen(target)}）÷ {yen(contrib_unit)} = {target_q:,.1f}"),
        number("cvp4", f"問4 {cut}％値下げ時に当期と同額の営業利益を得る販売数量", round(same_q), 3, unit="個",
               explain=f"値下げ後の単価 {yen(price)}×{100-cut}％ = {yen(new_price)}\n"
                       f"新しい単位貢献利益 = {yen(new_price)} − {yen(v_mfg)} − {yen(v_sell)} = {yen(new_contrib)}\n"
                       f"（固定費 {yen(fixed)} ＋ 当期営業利益 {yen(op)}）÷ {yen(new_contrib)} = {same_q:,.1f}",
               trap="値下げしても**変動費は変わらない**ので、単位あたり貢献利益だけが小さくなる。"
                    "貢献利益も20％下げてしまうミスに注意。分子は固定費＋（当期と同額の）営業利益。"),
    ]
    return {"no": 5, "title": "第5問（12点）", "field": "工業簿記", "topic": "CVP分析",
            "statement": st, "blocks": b, "explanation": ""}


# ================================================================ B. 全部原価計算 vs 直接原価計算
def gen_direct(rng: random.Random):
    annual_q = rng.choice([4800, 5400, 6000])
    v_rate = rng.choice([40, 50, 60])
    fixed_year = rng.choice([288_000, 324_000, 360_000])
    f_rate = fixed_year // annual_q
    fixed_month = fixed_year // 12

    produced = rng.randrange(400, 600, 10)
    begin_q = rng.choice([10, 20, 30])
    end_q = rng.choice([10, 20])
    sold = begin_q + produced - end_q

    dm = rng.randrange(50, 90) * 1_000
    dl = rng.randrange(40, 70) * 1_000
    v_sell = rng.randrange(6, 12) * 1_000
    f_sell = rng.randrange(8, 15) * 1_000
    admin = rng.randrange(8, 14) * 1_000
    # 製品1kgあたり総原価から、営業利益が必ず出る販売単価を逆算する
    _unit_cost = (dm + dl + v_rate * produced + fixed_month) / produced
    _need = (v_sell + f_sell + admin) / max(produced, 1)
    price = int(round((_unit_cost + _need) * rng.choice([1.3, 1.4, 1.5]) / 10) * 10)

    # 前月完成品の単価（月初製品）— 変動費部分と固定費部分
    prev_v_unit = rng.randrange(240, 300)
    begin_v = prev_v_unit * begin_q
    begin_f = f_rate * begin_q
    begin_full = begin_v + begin_f

    applied_v = v_rate * produced
    applied_f = f_rate * produced
    actual_oh = v_rate * produced + fixed_month
    vol_diff = fixed_month - applied_f          # 正＝不利差異

    made_v = dm + dl + applied_v
    made_full = made_v + applied_f
    v_unit = made_v / produced
    full_unit = made_full / produced

    end_v = round(v_unit * end_q)
    end_full = round(full_unit * end_q)

    sales = price * sold
    cogs_full = begin_full + made_full - end_full + vol_diff
    gross = sales - cogs_full
    op_full = gross - (v_sell + f_sell + admin)

    cogs_v = begin_v + made_v - end_v
    margin = sales - cogs_v
    contrib = margin - v_sell
    op_direct = contrib - (fixed_month + f_sell + admin)

    st = f"""以下の資料により、次の各問に答えなさい。

〔問１〕全部原価計算により、当月の損益計算書の各金額を求めなさい。
〔問２〕直接原価計算により、当月の損益計算書の各金額を求めなさい。

＜資料＞
1. 当社は実際総合原価計算を採用しているが、製造間接費については製品生産量を配賦基準として年間を通じて正常配賦している。
　年間の正常生産量 {annual_q:,}kg／年間予算（公式法変動予算）：変動費率 {v_rate}円/kg、固定費 {yen(fixed_year)}円
2. 製造間接費の操業度差異は、当月の売上原価に賦課する。
3. 製品の払出単価の計算は先入先出法による。
4. 当月の生産・販売資料

| | 数量 | | 数量 |
|---|---:|---|---:|
| 月初仕掛品量 | 0 kg | 月初製品在庫量 | {begin_q} kg |
| 当月投入量 | {produced} | 当月完成量 | {produced} |
| 月末仕掛品量 | 0 | 月末製品在庫量 | {end_q} |
| 当月完成量 | {produced} kg | 当月販売量 | {sold} kg |

5. 当月の財務資料
　当月直接材料費消費額（変動費）{yen(dm)}円／当月直接労務費消費額（変動費）{yen(dl)}円
　月初製品の変動製造原価は {yen(begin_v)}円（＠{prev_v_unit}円×{begin_q}kg）である。
　販売単価 {price}円/kg
　変動販売費 {yen(v_sell)}円／固定販売費 {yen(f_sell)}円／一般管理費（すべて固定費）{yen(admin)}円
　製造間接費は予算どおり発生した。
"""
    b = [
        number("d_sales", "問1 売上高", sales, 1,
               explain=f"@{price}円×{sold}kg = {yen(sales)}"),
        number("d_made", "問1 当月製品製造原価（全部）", made_full, 2,
               explain=f"直接材料費 {yen(dm)}＋直接労務費 {yen(dl)}\n"
                       f"＋変動製造間接費配賦 {v_rate}円×{produced}kg = {yen(applied_v)}\n"
                       f"＋固定製造間接費配賦 {f_rate}円（={yen(fixed_year)}÷{annual_q:,}kg）×{produced}kg"
                       f" = {yen(applied_f)}\n合計 {yen(made_full)}"),
        number("d_end", "問1 月末製品棚卸高（全部）", end_full, 2,
               explain=f"単価 {yen(made_full)}÷{produced}kg = {full_unit:,.1f}円 ×{end_q}kg = {yen(end_full)}"),
        number("d_vol", "問1 操業度差異", vol_diff, 2,
               explain=f"固定費実際発生額（月）{yen(fixed_year)}÷12 = {yen(fixed_month)}\n"
                       f"固定費配賦額 {f_rate}円×{produced}kg = {yen(applied_f)}\n"
                       f"差異 = {yen(vol_diff)}（正＝不利差異、売上原価に加算）",
               sign_note="不利差異（売上原価に加算）は正、有利差異は負",
               trap="操業度差異は**固定費のみ**から生じる。変動費率を混ぜて計算しないこと。"
                    "また基準は年間正常生産量から求めた固定費率であり、当月の実際生産量ではない。"),
        number("d_gross", "問1 売上総利益", gross, 2,
               explain=f"売上 {yen(sales)} − 売上原価 {yen(cogs_full)}"
                       f"（月初{yen(begin_full)}＋当月{yen(made_full)}−月末{yen(end_full)}"
                       f"＋操業度差異{yen(vol_diff)}） = {yen(gross)}"),
        number("d_op1", "問1 営業利益（全部原価計算）", op_full, 1,
               explain=f"{yen(gross)} −（販売費{yen(v_sell+f_sell)}＋一般管理費{yen(admin)}） = {yen(op_full)}"),
        number("d_vcogs", "問2 変動売上原価", cogs_v, 2,
               explain=f"月初{yen(begin_v)}＋当月変動製造原価{yen(made_v)}"
                       f"（{yen(dm)}＋{yen(dl)}＋{yen(applied_v)}）−月末{yen(end_v)} = {yen(cogs_v)}"),
        number("d_contrib", "問2 貢献利益", contrib, 2,
               explain=f"製造マージン {yen(margin)}（{yen(sales)}−{yen(cogs_v)}）"
                       f" − 変動販売費 {yen(v_sell)} = {yen(contrib)}"),
        number("d_op2", "問2 営業利益（直接原価計算）", op_direct, 2,
               explain=f"{yen(contrib)} − 固定費（製造{yen(fixed_month)}＋販売{yen(f_sell)}"
                       f"＋一般管理{yen(admin)}） = {yen(op_direct)}\n"
                       f"※全部原価計算との差 {yen(op_full-op_direct)} は、在庫に含まれる固定費の増減"
                       f"（月末{yen(end_full-end_v)}−月初{yen(begin_f)}）に一致する。"),
    ]
    return {"no": 5, "title": "第5問（12点）", "field": "工業簿記", "topic": "直接原価計算",
            "statement": st, "blocks": b, "explanation": ""}


def generate(rng: random.Random, avoid=None):
    avoid = avoid or set()
    pool = [g for g in (gen_cvp, gen_direct) if g.__name__ not in avoid] or [gen_cvp, gen_direct]
    chosen = rng.choice(pool)
    q = chosen(rng)
    q["used"] = [chosen.__name__]
    return q

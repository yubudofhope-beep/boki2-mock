"""第4問（28点）：⑴工業簿記の仕訳3題（12点）＋⑵原価計算（16点）。"""

from __future__ import annotations

import random

from .core import journal, number, shuffled_choices, yen

DISTRACTORS = ["材料", "賃金・給料", "製造間接費", "仕掛品", "製品", "売上原価",
               "買掛金", "当座預金", "現金", "未払金", "予算差異", "操業度差異"]


# ================================================================ ⑴ 仕訳
def j_material(rng):
    kg = rng.randrange(300, 900, 50)
    price = rng.choice([600, 800, 1000, 1200])
    freight = rng.randrange(10, 40) * 1_000
    total = kg * price + freight
    q = (f"素材甲{kg:,}kgを{price:,}円/kgで掛け購入した。なお、購入に際して発生する引取運賃等の"
         f"合計額{yen(freight)}円は小切手を振り出して支払った。")
    acc = ["材料", "賃金・給料", "製造間接費", "仕掛品", "買掛金", "当座預金"]
    return (q, acc, [("材料", total)], [("買掛金", kg * price), ("当座預金", freight)],
            f"材料の取得原価＝購入代価＋引取費用（材料副費）。\n"
            f"{kg:,}kg×{price:,}円 = {yen(kg*price)}、＋引取運賃 {yen(freight)} = {yen(total)}",
            "材料の購入",
            f"①引取運賃は費用（製造間接費）ではなく**材料の取得原価に含める**。"
            f"材料を {yen(kg*price)} だけにすると誤り。"
            "②代金の支払方法が「掛」と「小切手」で分かれているので、貸方は2行になる。"
            "まとめて買掛金にしないこと。")


def j_labor(rng):
    h1, h2, h3 = (rng.randrange(50, 180, 10) for _ in range(3))
    idle = rng.randrange(30, 80, 10)
    rate = rng.choice([1000, 1200, 1400])
    direct = (h1 + h2 + h3) * rate
    indirect_direct_worker = idle * rate
    paid = rng.randrange(150, 300) * 1_000
    prev = rng.randrange(40, 80) * 1_000
    cur = rng.randrange(50, 100) * 1_000
    indirect_worker = paid - prev + cur
    q = (f"当月の労務費の消費額を計上する。直接工の実際作業時間のうち、{h1}時間は製造指図書№101、"
         f"{h2}時間は№102、{h3}時間は№103に対して行われ、これら以外の間接作業時間や手待時間は"
         f"{idle}時間であった。直接工賃金の計算には１時間あたり{rate:,}円の予定消費賃率を用いている。"
         f"また、間接工については当月支払賃金が{yen(paid)}円、前月未払額が{yen(prev)}円、"
         f"当月未払額が{yen(cur)}円であった。")
    acc = ["賃金・給料", "製造間接費", "仕掛品", "製品", "賃率差異", "未払賃金"]
    return (q, acc,
            [("仕掛品", direct), ("製造間接費", indirect_direct_worker + indirect_worker)],
            [("賃金・給料", direct + indirect_direct_worker + indirect_worker)],
            f"直接工の直接作業 ({h1}+{h2}+{h3})時間×{rate:,}円 = {yen(direct)} → 仕掛品\n"
            f"直接工の間接作業・手待 {idle}時間×{rate:,}円 = {yen(indirect_direct_worker)} → 製造間接費\n"
            f"間接工 当月消費 = 支払{yen(paid)} − 前月未払{yen(prev)} + 当月未払{yen(cur)}"
            f" = {yen(indirect_worker)} → 製造間接費\n"
            f"製造間接費合計 {yen(indirect_direct_worker + indirect_worker)}",
            "労務費の消費",
            "①直接工でも**間接作業時間・手待時間は製造間接費**。全部を仕掛品にすると誤り。"
            "②間接工の当月消費額は「支払額」ではなく "
            "支払 − 前月未払 + 当月未払。支払額をそのまま使うのが最頻出のミス。"
            "③間接工の賃金は金額の大小にかかわらず全額が製造間接費。")


def j_overhead(rng):
    annual_budget = rng.randrange(40, 70) * 100_000
    annual_hours = rng.randrange(30, 50) * 100
    rate = annual_budget // annual_hours
    actual_hours = rng.randrange(250, 400, 10)
    applied = rate * actual_hours
    actual = applied + rng.choice([-1, 1]) * rng.randrange(10, 60) * 1_000
    diff = actual - applied      # 正なら不利差異（借方）
    q = (f"月末において当月の製造間接費配賦差異を計上する。製造間接費は機械稼働時間に基づいて各製造"
         f"指図書に予定配賦しており、当月の実際機械稼働時間合計は{actual_hours}時間、実際製造間接費"
         f"合計は{yen(actual)}円であった。なお、年間の製造間接費予算は{yen(annual_budget)}円であり、"
         f"配賦基準となる年間の機械稼働時間は{annual_hours:,}時間である。")
    acc = ["材料", "賃金・給料", "製造間接費", "仕掛品", "製造間接費配賦差異", "賃率差異"]
    if diff >= 0:
        debit, credit = [("製造間接費配賦差異", diff)], [("製造間接費", diff)]
        kind = "不利差異（借方差異）"
    else:
        debit, credit = [("製造間接費", -diff)], [("製造間接費配賦差異", -diff)]
        kind = "有利差異（貸方差異）"
    return (q, acc, debit, credit,
            f"予定配賦率 = {yen(annual_budget)} ÷ {annual_hours:,}時間 = {rate:,}円/時間\n"
            f"予定配賦額 = {rate:,}円×{actual_hours}時間 = {yen(applied)}\n"
            f"実際 {yen(actual)} − 予定 {yen(applied)} = {yen(abs(diff))} の{kind}",
            "製造間接費配賦差異",
            "①配賦率は**年間**予算 ÷ **年間**基準操業度。月額に直そうとして12で割ると誤り。"
            "②差異は 実際 − 予定。実際の方が多ければ不利差異で、差異勘定は**借方**。"
            "符号と貸借の向きを逆にするミスが多い。")


def j_complete(rng):
    n = rng.randrange(3, 8)
    each = rng.randrange(80, 200) * 1_000
    total = n * each
    q = (f"当月に製造指図書№201〜№{200+n}（合計{n}件）の製品が完成した。各指図書の製造原価は"
         f"それぞれ{yen(each)}円であった。完成した製品を製品勘定に振り替える。")
    acc = ["材料", "賃金・給料", "製造間接費", "仕掛品", "製品", "売上原価"]
    return (q, acc, [("製品", total)], [("仕掛品", total)],
            f"完成品原価 {n}件×{yen(each)} = {yen(total)} を仕掛品から製品へ振り替える。",
            "完成品の振替",
            "完成しただけで**まだ販売していない**ので、売上原価には振り替えない。"
            "「製品 / 仕掛品」であって「売上原価 / 仕掛品」ではない。"
            "引渡し・販売時に初めて売上原価へ振り替える。")


def j_price_diff(rng):
    std = rng.choice([500, 600, 800])
    kg = rng.randrange(200, 600, 50)
    actual_price = std + rng.choice([-50, -30, 20, 40])
    std_amt = std * kg
    act_amt = actual_price * kg
    diff = act_amt - std_amt
    q = (f"材料{kg:,}kgを消費した。材料費の計算には予定消費価格{std}円/kgを用いているが、"
         f"当月の実際消費価格は{actual_price}円/kgであった。材料消費価格差異を計上する。")
    acc = ["材料", "消費価格差異", "仕掛品", "製造間接費", "売上原価", "賃率差異"]
    if diff >= 0:
        debit, credit = [("消費価格差異", diff)], [("材料", diff)]
        kind = "不利差異"
    else:
        debit, credit = [("材料", -diff)], [("消費価格差異", -diff)]
        kind = "有利差異"
    return (q, acc, debit, credit,
            f"予定 {std}円×{kg:,}kg = {yen(std_amt)}、実際 {actual_price}円×{kg:,}kg = {yen(act_amt)}\n"
            f"差額 {yen(abs(diff))} の{kind}。",
            "材料消費価格差異",
            "①仕掛品に計上されるのは**予定価格**による金額であり、差異だけを"
            "材料勘定と差異勘定で調整する。仕掛品を実際額に直す仕訳を書かないこと。"
            "②実際 ＞ 予定 なら不利差異＝差異勘定は借方。有利差異の場合は逆になる。")


J_TEMPLATES = [j_material, j_labor, j_overhead, j_complete, j_price_diff]


# ================================================================ ⑵-A 指図書別原価計算表
def part2_kobetsu(rng):
    mat_price = rng.choice([200, 250, 300])
    wage = rng.choice([300, 360, 400])
    oh_rate = rng.choice([150, 180, 200])
    begin = rng.randrange(80, 150) * 1_000

    jobs = [
        ("No.503", rng.randrange(150, 300, 50), rng.randrange(20, 40, 5), "５月着手 ６月完成引渡済", begin),
        ("No.601", rng.randrange(600, 900, 50), rng.randrange(50, 80, 5), "６月着手 ６月完成引渡済", 0),
        ("No.602", rng.randrange(500, 800, 50), rng.randrange(40, 60, 5), "６月着手 完成（月末未引渡）", 0),
        ("No.603", rng.randrange(300, 500, 50), rng.randrange(20, 40, 5), "６月着手 月末未完成", 0),
    ]
    rows = []
    for name, kg, hrs, note, bi in jobs:
        m = kg * mat_price
        l = hrs * wage
        o = hrs * oh_rate
        rows.append({"name": name, "kg": kg, "hrs": hrs, "note": note,
                     "begin": bi, "mat": m, "lab": l, "oh": o, "total": bi + m + l + o})

    finished = sum(r["total"] for r in rows if "未完成" not in r["note"])
    wip_end = sum(r["total"] for r in rows if "未完成" in r["note"])
    cogs = sum(r["total"] for r in rows if "引渡済" in r["note"])

    st = f"""⑵（16点）当社は実際個別原価計算を行っている。次に示した６月の資料に基づき、指図書別原価計算表を完成させなさい。

〔資料〕
1. 月初有高：仕掛品 {rows[0]['name']} ￥{yen(begin)}
2. ⑴ 直接材料の消費単価 １kg当たり {mat_price}円　⑵ 直接工の消費賃率 １時間当たり {wage}円　⑶ 製造間接費配賦率 １直接作業時間当たり {oh_rate}円
3. その他

| 指図書 | 直接材料消費量 | 直接作業時間 | 備考 |
|---|---:|---:|---|
""" + "\n".join(f"| {r['name']} | {r['kg']:,}kg | {r['hrs']}時間 | {r['note']} |" for r in rows)

    b = []
    for r in rows:
        b.append(number(f"k_{r['name']}_m", f"{r['name']} 直接材料費", r["mat"], 1,
                        explain=f"{r['kg']:,}kg×{mat_price}円 = {yen(r['mat'])}"))
        b.append(number(f"k_{r['name']}_l", f"{r['name']} 直接労務費", r["lab"], 1,
                        explain=f"{r['hrs']}時間×{wage}円 = {yen(r['lab'])}"))
        b.append(number(f"k_{r['name']}_o", f"{r['name']} 製造間接費", r["oh"], 1,
                        explain=f"{r['hrs']}時間×{oh_rate}円 = {yen(r['oh'])}"))
        b.append(number(f"k_{r['name']}_t", f"{r['name']} 製品製造原価", r["total"], 1,
                        explain=(f"月初 {yen(r['begin'])} ＋ " if r["begin"] else "")
                                + f"{yen(r['mat'])}＋{yen(r['lab'])}＋{yen(r['oh'])} = {yen(r['total'])}"))
    b += [
        number("k_fin", "当月完成高（仕掛品勘定）", finished, 2,
               explain="完成した指図書（月末未完成のものを除く）の合計 = " + yen(finished)),
        number("k_wip", "月末仕掛品有高", wip_end, 2,
               explain="月末未完成の指図書の原価 = " + yen(wip_end)),
        number("k_cogs", "当月の売上原価", cogs, 2,
               explain="完成かつ**引渡済**の指図書だけの合計 = " + yen(cogs),
               trap="「完成」と「引渡済」は別物。完成しても未引渡なら**製品**であって"
                    "売上原価にはならない。また月初仕掛品のあった指図書は、月初有高も"
                    "その指図書の原価に加算すること。"),
    ]
    return st, b, "個別原価計算"


# ================================================================ ⑵-B 単純総合原価計算（平均法・正常減損）
def part2_sogo(rng):
    begin_q = rng.randrange(200, 600, 100)
    begin_deg = rng.choice([0.5, 0.4, 0.6])
    input_q = rng.randrange(1500, 3000, 100)
    end_q = rng.randrange(200, 600, 100)
    loss_q = rng.randrange(50, 200, 50)
    end_deg = rng.choice([0.5, 0.4, 0.8])
    done_q = begin_q + input_q - end_q - loss_q

    begin_mat = rng.randrange(50, 150) * 1_000
    begin_conv = rng.randrange(20, 80) * 1_000
    cur_mat = rng.randrange(400, 900) * 1_000
    cur_conv = rng.randrange(300, 700) * 1_000

    # 減損の発生点をランダムに（終点＝完成品のみ負担／始点＝両者負担）
    at_end = rng.random() < 0.5
    tot_mat = begin_mat + cur_mat
    tot_conv = begin_conv + cur_conv
    end_conv_q = round(end_q * end_deg)
    if at_end:
        # 度外視法：分母に減損を含める → 減損費は完成品だけが負担する
        denom_mat = done_q + end_q + loss_q
        denom_conv = done_q + end_conv_q + loss_q
        loss_text = ("減損は工程の**終点**で発生している（正常減損であり、正常減損費は"
                     "完成品のみに負担させる）")
        note_mat = "減損は終点発生＝完成品のみ負担。度外視法では分母に減損量を含め、月末仕掛品には配賦しない。"
        note_conv = f"減損{loss_q:,}kgは終点発生なので加工進捗度100％で換算量に含める。"
    else:
        # 度外視法：分母から減損を除く → 減損費を完成品と月末仕掛品の両者が負担する
        denom_mat = done_q + end_q
        denom_conv = done_q + end_conv_q
        loss_text = ("減損は工程の**始点**で発生している（正常減損であり、正常減損費は"
                     "完成品と月末仕掛品の**両者**に負担させる）")
        note_mat = "減損は始点発生＝両者負担。度外視法では分母から減損量を除く（＝単価が上がる形で自動的に按分される）。"
        note_conv = "始点発生の減損は加工費の換算量に含めない（分母から除く）。"
    unit_mat = tot_mat / denom_mat
    unit_conv = tot_conv / denom_conv
    end_mat = round(unit_mat * end_q)
    end_conv = round(unit_conv * end_conv_q)
    end_total = end_mat + end_conv
    done_total = tot_mat + tot_conv - end_total
    unit_total = done_total / done_q

    st = f"""⑵（16点）当工場では単純総合原価計算を行っている。原料はすべて工程の始点で投入され、{loss_text}。原価配分の方法は**平均法**による。答案用紙の各金額を求めなさい。

〔生産データ〕

| | 数量 |
|---|---:|
| 月初仕掛品 | {begin_q:,} kg （加工進捗度 {begin_deg:g}） |
| 当月投入 | {input_q:,} kg |
| 合計 | {begin_q+input_q:,} kg |
| 月末仕掛品 | {end_q:,} kg （加工進捗度 {end_deg:g}） |
| 正常減損 | {loss_q:,} kg |
| 完成品 | {done_q:,} kg |

〔原価データ〕

| | 原料費 | 加工費 |
|---|---:|---:|
| 月初仕掛品原価 | {yen(begin_mat)} 円 | {yen(begin_conv)} 円 |
| 当月製造費用 | {yen(cur_mat)} 円 | {yen(cur_conv)} 円 |

※完成品単位原価は円未満を四捨五入すること。
"""
    b = [
        number("s_end_mat", "月末仕掛品原価（原料費）", end_mat, 3,
               explain=f"平均単価 = ({yen(begin_mat)}＋{yen(cur_mat)}) ÷ {denom_mat:,}kg"
                       f" = {unit_mat:,.2f}円/kg\n×月末 {end_q:,}kg = {yen(end_mat)}\n※{note_mat}",
               trap="**減損の発生点**で分母の作り方が変わる。終点発生（完成品のみ負担）なら分母に"
                    "減損量を含め、始点発生（両者負担）なら分母から除く。ここを読み飛ばすと"
                    "以降の金額がすべてずれる。今回は"
                    + ("終点発生＝完成品のみ負担。" if at_end else "始点発生＝両者負担。")),
        number("s_end_conv", "月末仕掛品原価（加工費）", end_conv, 3,
               explain=f"完成品換算量：完成{done_q:,}＋月末{end_q:,}×{end_deg:g}＝{end_conv_q:,}"
                       + (f"＋減損{loss_q:,}" if at_end else "")
                       + f" = {denom_conv:,}kg\n"
                       f"平均単価 = ({yen(begin_conv)}＋{yen(cur_conv)}) ÷ {denom_conv:,}"
                       f" = {unit_conv:,.2f}円/kg\n×{end_conv_q:,}kg = {yen(end_conv)}\n※{note_conv}",
               trap="加工費は**完成品換算量**（数量×加工進捗度）で按分する。"
                    f"月末仕掛品は {end_q:,}kg ではなく {end_q:,}×{end_deg:g}＝{end_conv_q:,}kg。"
                    "原料費（始点投入なので進捗度100％）と同じ数量を使うのが典型的なミス。"),
        number("s_end_total", "月末仕掛品原価（合計）", end_total, 2,
               explain=f"{yen(end_mat)}＋{yen(end_conv)} = {yen(end_total)}"),
        number("s_done", "完成品総合原価", done_total, 4,
               explain=f"投入原価合計 {yen(tot_mat+tot_conv)} − 月末仕掛品 {yen(end_total)} = {yen(done_total)}\n"
                       "（正常減損費は完成品原価に含まれる）"),
        number("s_unit", "完成品単位原価（円/kg）", round(unit_total), 4, unit="円/kg",
               explain=f"{yen(done_total)} ÷ {done_q:,}kg = {unit_total:,.2f} → {round(unit_total):,}円"),
    ]
    return st, b, "総合原価計算"


def generate(rng: random.Random, avoid=None):
    avoid = avoid or set()
    pool = [t for t in J_TEMPLATES if t.__name__ not in avoid]
    if len(pool) < 3:
        rest = [t for t in J_TEMPLATES if t.__name__ in avoid]
        rng.shuffle(rest)
        pool = pool + rest[: 3 - len(pool)]
    picks = rng.sample(pool, 3)
    blocks, lines, topics, used = [], [], [], []
    for i, tpl in enumerate(picks, start=1):
        q, acc, debit, credit, explain, topic, trap = tpl(rng)
        acc = shuffled_choices(rng, acc, DISTRACTORS)
        marks = "アイウエオカキク"
        opts = "　".join(f"{marks[j]}. {a}" for j, a in enumerate(acc))
        lines.append(f"**{i}.** {q}\n\n　{opts}")
        blocks.append(journal(f"q4_{i}", f"⑴ {i}.", acc, debit, credit, explain))
        blocks[-1]["trap"] = trap
        blocks[-1]["topic"] = topic
        topics.append(topic)
        used.append(tpl.__name__)

    part2 = [p for p in (part2_kobetsu, part2_sogo) if p.__name__ not in avoid] \
        or [part2_kobetsu, part2_sogo]
    chosen = rng.choice(part2)
    st2, b2, topic2 = chosen(rng)
    used.append(chosen.__name__)
    blocks += b2

    st = ("⑴（12点）次の各取引について仕訳を示しなさい。勘定科目は各取引の下から最も適当と"
          "思われるものを選ぶこと。\n\n" + "\n\n".join(lines) + "\n\n---\n\n" + st2)
    return {
        "no": 4, "title": "第4問（28点）", "field": "工業簿記",
        "topic": f"工業簿記の仕訳／{topic2}", "topics": topics + [topic2],
        "used": used, "statement": st, "blocks": blocks, "explanation": "",
    }

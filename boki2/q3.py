"""第3問（20点）：決算整理後の損益計算書作成。"""

from __future__ import annotations

import random

from .core import number, yen


def generate(rng: random.Random, avoid=None):
    # ---- 決算整理前残高試算表（貸借一致するように繰越利益剰余金で調整）
    cash = rng.randrange(500, 1200) * 1_000
    notes_r = rng.randrange(200, 600) * 1_000
    accounts_r = rng.randrange(400, 900) * 1_000
    inv_begin = rng.randrange(150, 400) * 1_000
    building = rng.randrange(15, 30) * 100_000
    equip = rng.randrange(2, 6) * 100_000
    land = rng.randrange(2, 5) * 100_000
    purchases = rng.randrange(1200, 2000) * 1_000
    salary = rng.randrange(300, 500) * 1_000
    insurance = rng.randrange(40, 80) * 1_000
    interest = rng.randrange(40, 90) * 1_000

    notes_p = rng.randrange(150, 400) * 1_000
    accounts_p = rng.randrange(300, 600) * 1_000
    loan = rng.randrange(8, 15) * 100_000
    b_dep = rng.randrange(3, 8) * 100_000
    e_dep = rng.randrange(1, 3) * 100_000
    retained = rng.randrange(30, 120) * 1_000

    # ---- 決算整理事項
    allow_rate = rng.choice([2, 3])
    q_book = rng.randrange(800, 1500)
    q_actual = q_book - rng.randrange(20, 150)
    unit_cost = rng.choice([200, 300, 400])
    nrv = unit_cost - rng.choice([20, 30, 50])
    b_life, b_salvage = 30, 10          # 耐用30年・残存10%
    e_rate = rng.choice([20, 25, 30])   # 定率法
    prepaid_ins = rng.randrange(6, 30) * 1_000
    accrued_int = rng.randrange(5, 20) * 1_000
    tax_rate = rng.choice([30, 40])

    # ---- 計算
    receivables = notes_r + accounts_r
    allow_needed = receivables * allow_rate // 100
    # 既設定額は必要額より小さくして、繰入額が必ず正になるようにする
    allow_add = round(allow_needed * rng.choice([30, 40, 50, 60]) / 100 / 1000) * 1000
    allow_add = max(allow_add, 1_000)
    allowance = allow_needed - allow_add

    inv_end_book = q_book * unit_cost
    loss_short = (q_book - q_actual) * unit_cost
    loss_value = q_actual * (unit_cost - nrv)
    cogs_base = inv_begin + purchases - inv_end_book
    cogs = cogs_base + loss_short + loss_value

    dep_b = building * (100 - b_salvage) // 100 // b_life
    dep_e = (equip - e_dep) * e_rate // 100
    dep = dep_b + dep_e

    ins_after = insurance - prepaid_ins
    allow_exp = allow_add
    sga = salary + allow_exp + dep + ins_after
    int_after = interest + accrued_int

    # 税引前当期純利益が必ず正になるよう、売上高を逆算する
    pretax = rng.randrange(150, 600) * 1_000
    sales = cogs + sga + int_after + pretax
    gross = sales - cogs
    operating = gross - sga
    ordinary = operating - int_after
    tax = pretax * tax_rate // 100
    net = pretax - tax

    # 試算表の貸借を一致させる（資本金で調整）
    debit_sum = (cash + notes_r + accounts_r + inv_begin + building + equip + land
                 + purchases + salary + insurance + interest)
    capital = debit_sum - (notes_p + accounts_p + loan + allowance
                           + b_dep + e_dep + retained + sales)
    if capital < 100_000:                 # 足りなければ現金を増やして調整
        gap = 100_000 - capital
        cash += gap
        debit_sum += gap
        capital = 100_000

    st = f"""次の（Ａ）決算整理前残高試算表と（Ｂ）決算整理事項にもとづいて、損益計算書を完成させなさい。会計期間はX6年４月１日からX7年３月31日までの１年である。

（Ａ）決算整理前残高試算表（単位：円）

| 借方残高 | 勘定科目 | 貸方残高 |
|---:|:---:|---:|
| {yen(cash)} | 現金 | |
| {yen(notes_r)} | 受取手形 | |
| {yen(accounts_r)} | 売掛金 | |
| {yen(inv_begin)} | 繰越商品 | |
| {yen(building)} | 建物 | |
| {yen(equip)} | 備品 | |
| {yen(land)} | 土地 | |
| | 支払手形 | {yen(notes_p)} |
| | 買掛金 | {yen(accounts_p)} |
| | 長期借入金 | {yen(loan)} |
| | 貸倒引当金 | {yen(allowance)} |
| | 建物減価償却累計額 | {yen(b_dep)} |
| | 備品減価償却累計額 | {yen(e_dep)} |
| | 資本金 | {yen(capital)} |
| | 繰越利益剰余金 | {yen(retained)} |
| | 売上 | {yen(sales)} |
| {yen(purchases)} | 仕入 | |
| {yen(salary)} | 給料手当 | |
| {yen(insurance)} | 保険料 | |
| {yen(interest)} | 支払利息 | |
| **{yen(debit_sum)}** | | **{yen(debit_sum)}** |

（Ｂ）決算整理事項

1. 受取手形と売掛金の期末残高合計額に対して{allow_rate}％の貸倒引当金を差額補充法により設定する。
2. 商品の期末棚卸高：帳簿棚卸数量 {q_book:,}個／実地棚卸数量 {q_actual:,}個／原価 ＠￥{unit_cost}／正味売却価額 ＠￥{nrv}。棚卸減耗損・商品評価損はともに売上原価の内訳科目として表示する。
3. 減価償却：建物は定額法（耐用年数{b_life}年、残存価額{b_salvage}％）、備品は定率法（償却率年{e_rate}％）。
4. 保険料のうち￥{yen(prepaid_ins)}は前払分である。
5. 支払利息の未払分が￥{yen(accrued_int)}ある。
6. 税引前当期純利益の{tax_rate}％相当額を法人税等として計上する。
"""

    b = [
        number("p3_sales", "Ⅰ 売上高", sales, 1, explain="試算表の売上をそのまま。"),
        number("p3_begin", "Ⅱ1 期首商品棚卸高", inv_begin, 1, explain="試算表の繰越商品。"),
        number("p3_purch", "Ⅱ2 当期商品仕入高", purchases, 1, explain="試算表の仕入。"),
        number("p3_end", "Ⅱ3 期末商品棚卸高", inv_end_book, 2,
               explain=f"帳簿数量ベース {q_book:,}個×@{unit_cost} = {yen(inv_end_book)}",
               trap=f"損益計算書の「期末商品棚卸高」は**帳簿棚卸数量×原価**（{q_book:,}個）。"
                    f"実地数量{q_actual:,}個や正味売却価額@{nrv}を使うのは誤り。"
                    "減耗と評価損はこの下の行で別に引く。"),
        number("p3_short", "Ⅱ4 棚卸減耗損", loss_short, 2,
               explain=f"（{q_book:,}−{q_actual:,}）個×@{unit_cost} = {yen(loss_short)}"),
        number("p3_valloss", "Ⅱ5 商品評価損", loss_value, 2,
               explain=f"実地{q_actual:,}個×（@{unit_cost}−@{nrv}） = {yen(loss_value)}"),
        number("p3_gross", "売上総利益", gross, 2,
               explain=f"売上 {yen(sales)} − 売上原価 {yen(cogs)}"
                       f"（{yen(inv_begin)}＋{yen(purchases)}−{yen(inv_end_book)}"
                       f"＋{yen(loss_short)}＋{yen(loss_value)}） = {yen(gross)}"),
        number("p3_allow", "Ⅲ 貸倒引当金繰入額", allow_exp, 2,
               explain=f"（{yen(notes_r)}＋{yen(accounts_r)}）×{allow_rate}％ = {yen(allow_needed)}、"
                       f"既設定 {yen(allowance)} との差額 {yen(allow_add)}",
               trap=f"**差額補充法**なので、必要額 {yen(allow_needed)} をそのまま繰り入れてはいけない。"
                    f"すでにある {yen(allowance)} を引いた差額だけが当期の費用。"),
        number("p3_dep", "Ⅲ 減価償却費", dep, 2,
               explain=f"建物 {yen(building)}×0.9÷{b_life}年 = {yen(dep_b)}\n"
                       f"備品（{yen(equip)}−{yen(e_dep)}）×{e_rate}％ = {yen(dep_e)}\n合計 {yen(dep)}",
               trap=f"①建物は残存価額{b_salvage}％があるので、取得原価×0.9÷{b_life}年。"
                    "残存価額を無視して÷30するミスが多い。"
                    f"②備品は定率法なので**取得原価ではなく期首帳簿価額**"
                    f"（{yen(equip)}−累計額{yen(e_dep)}）に率を掛ける。"),
        number("p3_ins", "Ⅲ 保険料", ins_after, 1,
               explain=f"{yen(insurance)} − 前払 {yen(prepaid_ins)} = {yen(ins_after)}",
               trap="前払費用は当期の費用から**引く**、未払費用は**足す**。"
                    "方向を逆にするミスが多い（支払利息の未払分は加算）。"),
        number("p3_op", "営業利益", operating, 2,
               explain=f"売上総利益 {yen(gross)} − 販管費 {yen(sga)}"
                       f"（給料{yen(salary)}＋繰入{yen(allow_exp)}＋償却{yen(dep)}＋保険料{yen(ins_after)}）"),
        number("p3_int", "Ⅴ 支払利息", int_after, 1,
               explain=f"{yen(interest)} ＋ 未払 {yen(accrued_int)} = {yen(int_after)}"),
        number("p3_ord", "経常利益", ordinary, 1,
               explain=f"{yen(operating)} − {yen(int_after)} = {yen(ordinary)}"),
        number("p3_tax", "法人税等", tax, 1,
               explain=f"税引前 {yen(pretax)} ×{tax_rate}％ = {yen(tax)}"),
        number("p3_net", "当期純利益", net, 1,
               explain=f"{yen(pretax)} − {yen(tax)} = {yen(net)}"),
    ]

    # ---- 貸借対照表バージョン（同じ資料から出題する）
    bs_inv = q_actual * nrv
    bs_building = building - b_dep - dep_b
    bs_equip = equip - e_dep - dep_e
    bs_retained = retained + net
    assets = (cash + notes_r + accounts_r - allow_needed + bs_inv
              + bs_building + bs_equip + land + prepaid_ins)
    liabilities = notes_p + accounts_p + loan + accrued_int + tax
    b_bs = [
        number("b3_allow", "貸倒引当金（△表示）", allow_needed, 2,
               explain=f"（{yen(notes_r)}＋{yen(accounts_r)}）×{allow_rate}％ = {yen(allow_needed)}",
               trap="貸借対照表に載るのは**設定後の残高**。損益計算書に載る「繰入額」"
                    f"（差額 {yen(allow_add)}）と混同しないこと。"),
        number("b3_inv", "商品", bs_inv, 2,
               explain=f"実地数量 {q_actual:,}個 × 正味売却価額 @{nrv} = {yen(bs_inv)}",
               trap="貸借対照表の商品は**実地数量×低い方の単価**。"
                    f"帳簿数量{q_book:,}個や原価@{unit_cost}で計算すると誤り。"),
        number("b3_building", "建物（減価償却累計額控除後）", bs_building, 2,
               explain=f"{yen(building)} − 既償却 {yen(b_dep)} − 当期 {yen(dep_b)} = {yen(bs_building)}"),
        number("b3_equip", "備品（減価償却累計額控除後）", bs_equip, 2,
               explain=f"{yen(equip)} − 既償却 {yen(e_dep)} − 当期 {yen(dep_e)} = {yen(bs_equip)}"),
        number("b3_prepaid", "前払費用", prepaid_ins, 2,
               explain=f"前払保険料 {yen(prepaid_ins)}"),
        number("b3_accrued", "未払費用", accrued_int, 2,
               explain=f"未払利息 {yen(accrued_int)}"),
        number("b3_tax", "未払法人税等", tax, 2,
               explain=f"税引前 {yen(pretax)} ×{tax_rate}％ = {yen(tax)}（中間納付なし）"),
        number("b3_retained", "繰越利益剰余金", bs_retained, 3,
               explain=f"期首 {yen(retained)} ＋ 当期純利益 {yen(net)} = {yen(bs_retained)}",
               trap="試算表の繰越利益剰余金をそのまま書くのは誤り。"
                    "当期純利益を足した金額が期末残高になる。"),
        number("b3_assets", "資産合計", assets, 3,
               explain=f"現金{yen(cash)}＋受取手形{yen(notes_r)}＋売掛金{yen(accounts_r)}"
                       f"−貸倒引当金{yen(allow_needed)}＋商品{yen(bs_inv)}＋建物{yen(bs_building)}"
                       f"＋備品{yen(bs_equip)}＋土地{yen(land)}＋前払費用{yen(prepaid_ins)}"
                       f" = {yen(assets)}\n"
                       f"（検算：負債 {yen(liabilities)} ＋ 純資産 "
                       f"{yen(capital + bs_retained)} = {yen(liabilities + capital + bs_retained)}）",
               trap="貸倒引当金は資産のマイナス項目。足してしまわないこと。"),
    ]

    if rng.random() < 0.5:
        return {"no": 3, "title": "第3問（20点）", "field": "商業簿記",
                "topic": "損益計算書の作成", "used": ["p3_pl"],
                "statement": st, "blocks": b, "explanation": ""}
    st_bs = st.replace("損益計算書を完成させなさい", "**貸借対照表**を完成させなさい")
    return {"no": 3, "title": "第3問（20点）", "field": "商業簿記",
            "topic": "貸借対照表の作成", "used": ["p3_bs"],
            "statement": st_bs, "blocks": b_bs, "explanation": ""}

"""第1問：商業簿記の仕訳5題（各4点・計20点）。

各テンプレートは rng を受け取り
(問題文, 選択肢, 借方, 貸方, 解説, 論点名, ひっかけポイント) を返す。
「ひっかけポイント」は受験生が間違えやすい罠の説明で、採点後に必ず表示する。
"""

from __future__ import annotations

import random

from .core import journal, rnd, shuffled_choices, yen

DISTRACTORS = [
    "現金", "当座預金", "普通預金", "受取手形", "売掛金", "買掛金", "支払手形",
    "未収入金", "未払金", "仕入", "売上", "貸倒損失", "雑損", "雑益",
    "支払手数料", "有価証券売却損", "固定資産売却益", "繰延税金資産",
]


# ---------------------------------------------------------------- 1. 償却債権取立益
def t_shokyaku(rng):
    amt = rnd(rng, 5, 60, 1) * 10_000
    method = rng.choice(["現金", "普通預金"])
    prev = rng.random() < 0.5     # True=前期に貸倒処理／False=当期に貸倒処理
    if prev:
        q = f"当社は、前期に貸倒処理した売掛金￥{yen(amt)}を当期に{method}で回収した。"
        debit, credit = [(method, amt)], [("償却債権取立益", amt)]
        exp = ("前期に貸倒処理済みの債権は帳簿から消えているため、回収額は"
               "**収益（償却債権取立益）**として処理する。")
    else:
        q = (f"当社は、**当期**に貸倒処理した売掛金￥{yen(amt)}を、同じ当期中に{method}で回収した。"
             f"なお、貸倒処理時には貸倒引当金を全額取り崩している。")
        debit, credit = [(method, amt)], [("貸倒引当金", amt)]
        exp = ("同一会計期間内の貸倒れの取消しなので、収益ではなく**貸倒処理の取り消し**として、"
               "取り崩した貸倒引当金を元に戻す。")
    acc = ["貸倒引当金", "売掛金", "貸倒損失", "償却債権取立益", method, "貸倒引当金繰入"]
    return (q, acc, debit, credit, exp, "償却債権取立益",
            "**前期**の貸倒れか**当期**の貸倒れかで貸方科目が変わる。前期なら償却債権取立益、"
            "当期なら貸倒引当金（または貸倒損失）の戻し。反射的に「償却債権取立益」と書くと不正解。"
            "また売掛金は既に消えているので、売掛金の復活を書いてはいけない。")


# ---------------------------------------------------------------- 2. 為替予約（振当処理）
def t_kawase(rng):
    dollars = rnd(rng, 3, 12) * 100
    covered = dollars - rnd(rng, 1, 3) * 100
    if covered <= 0:
        covered = dollars
    sale_rate = rnd(rng, 100, 130)
    fwd_rate = sale_rate - rnd(rng, 3, 15)
    spot_today = sale_rate + rng.choice([-4, -2, 3, 5])
    diff = (sale_rate - fwd_rate) * covered
    q = (f"先日、海外の取引先に対して商品を＄{dollars:,}で掛け販売したが、為替変動リスクを"
         f"回避するため、本日、当該売掛金のうち＄{covered:,}について１＄＝￥{fwd_rate}で"
         f"為替予約を行った。なお、販売時の直物為替相場は１＄＝￥{sale_rate}、"
         f"本日の直物為替相場は１＄＝￥{spot_today}である。")
    acc = ["買掛金", "売掛金", "仕入", "為替差損益", "売上", "現金"]
    return (q, acc, [("為替差損益", diff)], [("売掛金", diff)],
            f"振当処理では、予約した部分の売掛金を予約レートに換算し直す。\n"
            f"換算前 ＄{covered:,}×￥{sale_rate} = ￥{yen(covered*sale_rate)}\n"
            f"換算後 ＄{covered:,}×￥{fwd_rate} = ￥{yen(covered*fwd_rate)}\n"
            f"差額 ￥{yen(diff)} を売掛金から減らし、同額を為替差損益とする。",
            "為替予約",
            f"①予約したのは＄{covered:,}だけで、全額＄{dollars:,}ではない。②使うのは"
            f"**販売時レート￥{sale_rate}と予約レート￥{fwd_rate}**であり、"
            f"本日の直物相場￥{spot_today}はダミー。取引発生後の予約なので直物は使わない。")


# ---------------------------------------------------------------- 3. 資本的支出＋修繕引当金
def t_shihonteki(rng):
    total = rnd(rng, 40, 120) * 100_000
    capital = rnd(rng, 10, 30) * 100_000
    if capital >= total:
        capital = total // 2
    revenue_exp = total - capital
    allowance = min(revenue_exp, rnd(rng, 5, 25) * 100_000)
    repair = revenue_exp - allowance
    q = (f"建物の改良と修繕を行い、代金￥{yen(total)}について小切手を振り出して支払った。"
         f"なお、このうち￥{yen(capital)}は改良（資本的支出）として処理する。また、この修繕の"
         f"ための修繕引当金が￥{yen(allowance)}設定されている。")
    acc = ["建物", "修繕費", "修繕引当金", "雑損", "現金", "当座預金"]
    debit = [("建物", capital), ("修繕引当金", allowance)]
    if repair:
        debit.append(("修繕費", repair))
    return (q, acc, debit, [("当座預金", total)],
            f"資本的支出￥{yen(capital)}は建物（資産）に加算。残り￥{yen(revenue_exp)}が収益的支出で、"
            f"うち￥{yen(allowance)}は設定済みの修繕引当金を取り崩し、"
            f"超過分￥{yen(repair)}を修繕費とする。", "資本的支出・修繕引当金",
            "①修繕引当金は**収益的支出の分だけ**取り崩す。総額から引くと誤り。"
            "②引当金を超えた分は修繕費。引当金が足りている前提で書くと不正解。"
            "③「小切手を振り出して」＝当座預金であって現金ではない。")


# ---------------------------------------------------------------- 4. 吸収合併＋のれん
def t_gappei(rng):
    assets = rnd(rng, 80, 160) * 1_000_000
    liabilities = rnd(rng, 30, 70) * 1_000_000
    net = assets - liabilities
    negative = rng.random() < 0.25          # 負ののれん（＝ひっかけ）
    if negative:
        consideration = net - rnd(rng, 1, 10) * 1_000_000
    else:
        consideration = net + rnd(rng, 1, 15) * 1_000_000
    shares = rnd(rng, 8, 20) * 100
    gw = consideration - net
    q = (f"日本商事㈱は東京商事㈱を吸収合併して、株式{shares:,}株（時価￥{yen(consideration)}、"
         f"全額資本金に計上）を交付した。なお、合併によって引き継いだ東京商事㈱の資産総額は"
         f"￥{yen(assets)}、負債総額は￥{yen(liabilities)}であった。仕訳にあたっては、"
         f"資産は「諸資産」、負債は「諸負債」とすること。")
    acc = ["資本金", "諸負債", "のれん", "資本準備金", "諸資産", "負ののれん発生益"]
    debit = [("諸資産", assets)]
    credit = [("諸負債", liabilities), ("資本金", consideration)]
    if gw >= 0:
        debit.append(("のれん", gw))
        tail = f"のれん = {yen(consideration)} − {yen(net)} = {yen(gw)}（借方・資産）"
    else:
        credit.append(("負ののれん発生益", -gw))
        tail = (f"取得原価 {yen(consideration)} が受入純資産 {yen(net)} を**下回る**ため、"
                f"差額 {yen(-gw)} は「負ののれん発生益」（貸方・収益）")
    return (q, acc, debit, credit,
            f"受入純資産 = {yen(assets)} − {yen(liabilities)} = {yen(net)}\n"
            f"交付株式の時価 {yen(consideration)} が取得原価。\n{tail}", "合併・のれん",
            "対価が受入純資産を**下回る**場合は「のれん」ではなく「負ののれん発生益」（収益）。"
            "毎回のれんが借方に出ると思い込むと落とす。まず純資産と対価の大小を確認すること。")


# ---------------------------------------------------------------- 5. 電子記録債権債務
def t_denshi(rng):
    amt = rnd(rng, 5, 30) * 100_000
    debtor = rng.random() < 0.5
    if debtor:
        q = (f"ＣＰＡ商事㈱は、横浜商事㈱に対する買掛金￥{yen(amt)}の支払いを電子債権記録機関"
             f"で行うこととし、取引銀行を通じて**債務**の発生記録の請求を行った。")
        debit, credit = [("買掛金", amt)], [("電子記録債務", amt)]
        exp = "債務者側の発生記録請求。買掛金を電子記録債務に振り替える。"
    else:
        q = (f"ＣＰＡ商事㈱は、横浜商事㈱に対する売掛金￥{yen(amt)}について、取引銀行を通じて"
             f"電子債権記録機関に**債権**の発生記録の請求を行い、その通知を受けた。")
        debit, credit = [("電子記録債権", amt)], [("売掛金", amt)]
        exp = "債権者側の発生記録。売掛金を電子記録債権に振り替える。"
    acc = ["買掛金", "電子記録債務", "仕入", "売上", "電子記録債権", "売掛金"]
    return (q, acc, debit, credit, exp, "電子記録債権債務",
            "自社が**債権者（もらう側）か債務者（払う側）か**を読み分ける。"
            "「買掛金の支払い」なら債務、「売掛金の回収」なら債権。"
            "また新たに仕入・売上を計上するのではなく、既存の債権債務の振替である点に注意。")


# ---------------------------------------------------------------- 6. 火災未決算
def t_kasai(rng):
    cost = rnd(rng, 20, 60) * 100_000
    acc_dep = rnd(rng, 5, 15) * 100_000
    if acc_dep >= cost:
        acc_dep = cost // 3
    book = cost - acc_dep
    over = rng.random() < 0.5      # 保険金額が帳簿価額より小さい＝火災損失が出る
    insured = int(book * (rng.uniform(0.4, 0.8) if over else rng.uniform(1.1, 1.6)))
    insured = round(insured, -4)
    q = (f"ＣＰＡ商事株式会社は、先日、営業用店舗にて火災が発生し、建物（取得原価￥{yen(cost)}、"
         f"焼失時の減価償却累計額￥{yen(acc_dep)}）が焼失した。ただし、この建物について、"
         f"保険会社と火災保険契約￥{yen(insured)}を結んでいたため、ただちに保険金の支払いを請求した。")
    acc = ["火災損失", "建物", "建物減価償却累計額", "保険差益", "未決算", "未収入金"]
    debit = [("建物減価償却累計額", acc_dep), ("未決算", min(book, insured))]
    credit = [("建物", cost)]
    if book > insured:
        debit.append(("火災損失", book - insured))
    return (q, acc, debit, credit,
            f"帳簿価額 = {yen(cost)} − {yen(acc_dep)} = {yen(book)}\n"
            f"保険契約額 {yen(insured)} を**限度**として未決算勘定に振り替える。"
            + (f"\n限度を超える {yen(book-insured)} は火災損失（費用）として当期に計上。"
               if book > insured else
               "\n保険契約額が帳簿価額以上なので、帳簿価額全額 "
               f"{yen(book)} を未決算とする（未決算 ＞ 帳簿価額 にはしない）。"),
            "火災未決算",
            "①未決算に振り替えるのは「帳簿価額」と「保険金額」の**小さい方**。"
            "保険金額をそのまま未決算にすると誤り。②この時点ではまだ保険金額が確定していないので"
            "「未収入金」や「保険差益」は使わない（保険金確定時の仕訳と混同しやすい）。")


# ---------------------------------------------------------------- 7. 定率法・期中売却
def t_teiritsu(rng):
    cost = rnd(rng, 20, 40) * 100_000
    rate = rng.choice([0.142, 0.200, 0.250, 0.319])
    years = rng.choice([2, 3])
    months = rng.choice([0, 3, 6, 9])       # 0なら期首売却、それ以外は期中売却
    bv = cost
    steps = []
    b = cost
    for i in range(years):
        d = round(b * rate)
        steps.append(f"{i+1}年目 {yen(b)}×{rate} = {yen(d)}")
        b -= d
    acc_dep = cost - b
    bv = b
    this_year = round(bv * rate * months / 12) if months else 0
    bv_at_sale = bv - this_year
    proceeds = bv_at_sale + rng.choice([-1, 1]) * rnd(rng, 1, 5) * 10_000
    gain = proceeds - bv_at_sale
    sale_month = {0: "４月１日", 3: "６月30日", 6: "９月30日", 9: "12月31日"}[months]
    q = (f"東京商事（年１回３月末日決算）は、X5年４月１日に取得した乗用車（取得原価￥{yen(cost)}）"
         f"をX{5+years}年{sale_month}に売却し、手取金￥{yen(proceeds)}は月末に受け取ることとした。"
         f"なお、この乗用車については定率法（償却率{rate}）により償却し、間接法で記帳している。"
         + ("減価償却費は月割計算による。" if months else ""))
    acc = ["車両減価償却累計額", "車両", "固定資産売却益", "固定資産売却損",
           "減価償却費", "未収入金"]
    debit = [("車両減価償却累計額", acc_dep), ("未収入金", proceeds)]
    if this_year:
        debit.append(("減価償却費", this_year))
    credit = [("車両", cost)]
    if gain >= 0:
        credit.append(("固定資産売却益", gain))
    else:
        debit.append(("固定資産売却損", -gain))
    exp = ("定率法は**期首帳簿価額**に償却率を掛ける。\n" + "\n".join(steps) +
           f"\n売却時の累計額 {yen(acc_dep)}、期首帳簿価額 {yen(bv)}")
    if this_year:
        exp += (f"\n当期分（{months}か月）＝ {yen(bv)}×{rate}×{months}/12 = {yen(this_year)}\n"
                f"売却時簿価 {yen(bv)} − {yen(this_year)} = {yen(bv_at_sale)}")
    exp += (f"\n売却価額 {yen(proceeds)} − 簿価 {yen(bv_at_sale)} = {yen(abs(gain))}"
            f"（{'売却益' if gain >= 0 else '売却損'}）")
    trap = ("定率法は取得原価ではなく**期首帳簿価額**に率を掛ける（毎年同額ではない）。"
            + (f"また期首ではなく期中（{sale_month}）の売却なので、当期{months}か月分の"
               "減価償却費を月割で計上してから売却損益を計算する。これを忘れると必ず外れる。"
               if months else "本問は**期首**売却なので当期の減価償却は不要。"
                              "つい月割計算をしてしまうと誤り。")
            + "「手取金は月末に受け取る」＝未収入金であり、現金ではない。")
    return (q, acc, debit, credit, exp, "固定資産の売却（定率法）", trap)


# ---------------------------------------------------------------- 8. 売上原価対立法
def t_taritsu(rng):
    cost = rnd(rng, 10, 40) * 10_000
    sale = cost * rng.choice([2, 3, 4])
    q = (f"中央商事は、商品（原価￥{yen(cost)}）を近畿商事に￥{yen(sale)}で掛け販売した。"
         f"当社は商品売買について売上原価対立法（販売のつど売上原価を計上する方法）を"
         f"採用している。")
    acc = ["仕入", "売上", "買掛金", "売上原価", "商品", "売掛金"]
    return (q, acc, [("売掛金", sale), ("売上原価", cost)], [("売上", sale), ("商品", cost)],
            "売上原価対立法では、販売時に①売上の計上と②商品から売上原価への振替を"
            "**同時に**行う。\n"
            f"① 売掛金 {yen(sale)} / 売上 {yen(sale)}\n"
            f"② 売上原価 {yen(cost)} / 商品 {yen(cost)}", "売上原価対立法",
            "①「仕入」勘定は使わない（三分法との混同）。仕入時点で「商品」勘定に計上済み。"
            "②仕訳が2行で終わると思って売上原価の振替を忘れるミスが多い。"
            "③原価と売価を取り違えないこと。")


# ---------------------------------------------------------------- 9. 税効果会計
def t_zeikoka(rng):
    kind = rng.choice(["減価償却", "貸倒引当金"])
    rate = rng.choice([30, 40])
    if kind == "減価償却":
        cost = rnd(rng, 4, 12) * 100_000
        acct_life = rng.choice([4, 5])
        tax_life = acct_life + rng.choice([1, 2])
        acct_dep = cost // acct_life
        tax_dep = cost // tax_life
        diff = acct_dep - tax_dep
        q = (f"決算にあたり、税効果会計に関する仕訳を行う。当期首に取得した備品"
             f"（取得原価￥{yen(cost)}、残存価額ゼロ、耐用年数{acct_life}年）について定額法により"
             f"償却を行った。税法上の耐用年数は{tax_life}年である。法定実効税率は{rate}％とする。")
        exp = (f"会計上の減価償却費 {yen(cost)}÷{acct_life}年 = {yen(acct_dep)}\n"
               f"税務上の限度額 {yen(cost)}÷{tax_life}年 = {yen(tax_dep)}\n"
               f"償却超過額（将来減算一時差異） {yen(diff)}")
    else:
        base = rnd(rng, 20, 60) * 100_000
        allowed = base * rng.choice([20, 30, 40]) // 100
        diff = base - allowed
        q = (f"決算にあたり、税効果会計に関する仕訳を行う。当期に売上債権に対して貸倒引当金"
             f"￥{yen(base)}を設定したが、そのうち税法上損金として認められる金額は"
             f"￥{yen(allowed)}であった。法定実効税率は{rate}％とする。なお、前期末に"
             f"一時差異はない。")
        exp = (f"会計上の繰入 {yen(base)} − 税務上の損金算入額 {yen(allowed)}\n"
               f"損金不算入額（将来減算一時差異） {yen(diff)}")
    dta = round(diff * rate / 100)
    acc = ["繰延税金負債", "法人税、住民税及び事業税", "法人税等調整額",
           "備品", "未払法人税等", "繰延税金資産"]
    return (q, acc, [("繰延税金資産", dta)], [("法人税等調整額", dta)],
            exp + f"\n繰延税金資産 = {yen(diff)}×{rate}％ = {yen(dta)}", "税効果会計",
            "①税効果の仕訳に載せるのは**差異の金額そのものではなく、差異×実効税率**。"
            "差額をそのまま書くミスが非常に多い。②将来**減算**一時差異なので"
            "繰延税金**資産**（借方）。負債と取り違えないこと。"
            "③取得原価や引当金の額をそのまま使わない。")


# ---------------------------------------------------------------- 10. 増資
def t_zoshi(rng):
    shares = rnd(rng, 2, 10) * 100
    price = rnd(rng, 3, 12) * 100
    total = shares * price
    minimum = rng.random() < 0.7
    if minimum:
        cap = total // 2
        note = "資本金への計上額は会社法が規定する最低限度額とする。"
        exp_tail = (f"会社法の最低限度額は払込金額の1/2 → 資本金 {yen(cap)}、"
                    f"残り {yen(total-cap)} は資本準備金。")
    else:
        cap = total
        note = "払込金額の全額を資本金とする。"
        exp_tail = "全額資本金とする指示があるので資本準備金は生じない。"
    q = (f"新株{shares:,}株を１株につき￥{yen(price)}で発行して増資を行い、払込金は全額"
         f"当座預金とした。なお、{note}")
    acc = ["当座預金", "資本金", "資本準備金", "その他資本剰余金", "株式交付費", "現金"]
    credit = [("資本金", cap)]
    if total - cap:
        credit.append(("資本準備金", total - cap))
    return (q, acc, [("当座預金", total)], credit,
            f"払込総額 {shares:,}株×{yen(price)} = {yen(total)}\n" + exp_tail, "増資",
            "「最低限度額」なのか「全額資本金」なのか、問題文の指示を必ず読む。"
            "最低限度額なら1/2ずつ、全額なら資本準備金は出ない。反射で1/2にすると外す。")


# ---------------------------------------------------------------- 11. リース取引
def t_lease(rng):
    years = rng.choice([4, 5])
    annual = rnd(rng, 20, 40) * 10_000
    total = annual * years
    acquisition = round(total * rng.uniform(0.85, 0.95), -4)
    interest = total - acquisition
    komi = rng.random() < 0.5
    if komi:
        q = (f"当社は当期首に、リース期間{years}年、年額リース料￥{yen(annual)}（毎年３月末日"
             f"後払い）のファイナンス・リース契約を締結し、リース物件（見積現金購入価額"
             f"￥{yen(acquisition)}）の引渡しを受けた。**利子込み法**により処理する。")
        debit, credit = [("リース資産", total)], [("リース債務", total)]
        exp = (f"利子込み法では、リース料総額 {yen(annual)}×{years}年 = {yen(total)} を"
               f"そのままリース資産・リース債務として計上する。"
               f"見積現金購入価額 {yen(acquisition)} は使わない。")
        trap = (f"利子込み法なので**リース料総額 {yen(total)}**で計上する。"
                f"見積現金購入価額 {yen(acquisition)} を使うのは利子抜き法。"
                "問題文の「利子込み／利子抜き」の一語で答えが変わる最頻出のひっかけ。")
    else:
        q = (f"当社は当期首に、リース期間{years}年、年額リース料￥{yen(annual)}（毎年３月末日"
             f"後払い）のファイナンス・リース契約を締結し、リース物件（見積現金購入価額"
             f"￥{yen(acquisition)}）の引渡しを受けた。**利子抜き法**により処理する。")
        debit, credit = [("リース資産", acquisition)], [("リース債務", acquisition)]
        exp = (f"利子抜き法では、見積現金購入価額 {yen(acquisition)} を計上する。"
               f"リース料総額 {yen(total)} との差額 {yen(interest)} は利息であり、"
               f"支払時に支払利息として費用処理していく。")
        trap = (f"利子抜き法なので**見積現金購入価額 {yen(acquisition)}**で計上する。"
                f"リース料総額 {yen(total)} を使うのは利子込み法。"
                "また契約時点では支払利息はまだ計上しない。")
    acc = ["リース資産", "リース債務", "支払利息", "支払リース料", "減価償却費", "当座預金"]
    return (q, acc, debit, credit, exp, "リース取引", trap)


# ---------------------------------------------------------------- 12. 役務収益・役務原価
def t_ekimu(rng):
    fee = rnd(rng, 20, 80) * 10_000
    cost = round(fee * rng.uniform(0.4, 0.6), -3)
    ratio = rng.choice([40, 50, 60])
    q = (f"当社はサービス業を営んでおり、先に顧客から受け取った代金￥{yen(fee)}を前受金として"
         f"処理していた。当期末までに当該役務の{ratio}％が提供済みとなったため、"
         f"提供割合に応じて収益を計上する。なお、対応する費用は仕掛品として￥{yen(cost)}"
         f"計上されており、同じ割合で役務原価に振り替える。")
    acc = ["前受金", "役務収益", "役務原価", "仕掛品", "売上", "売掛金"]
    rev = fee * ratio // 100
    exc = int(cost * ratio // 100)
    return (q, acc, [("前受金", rev), ("役務原価", exc)], [("役務収益", rev), ("仕掛品", exc)],
            f"役務収益 = {yen(fee)}×{ratio}％ = {yen(rev)}（前受金を取り崩す）\n"
            f"役務原価 = {yen(cost)}×{ratio}％ = {yen(exc)}（仕掛品から振り替える）",
            "役務収益・役務原価",
            "①収益は「売上」ではなく**役務収益**、費用は**役務原価**。"
            "②収益だけ計上して、対応する仕掛品→役務原価の振替を忘れるミスが多い（費用収益対応）。"
            f"③全額ではなく提供済みの{ratio}％分だけ。")


# ---------------------------------------------------------------- 13. 圧縮記帳
def t_asshuku(rng):
    grant = rnd(rng, 5, 20) * 100_000
    cost = grant + rnd(rng, 5, 20) * 100_000
    q = (f"当期首に国庫補助金￥{yen(grant)}を受け取り、これに自己資金を加えて機械装置"
         f"￥{yen(cost)}を取得し、代金は小切手を振り出して支払った。本日決算につき、"
         f"当該補助金について**直接減額方式**により圧縮記帳を行う。圧縮記帳の仕訳を示しなさい。")
    acc = ["機械装置", "固定資産圧縮損", "国庫補助金受贈益", "当座預金",
           "減価償却費", "繰延税金負債"]
    return (q, acc, [("固定資産圧縮損", grant)], [("機械装置", grant)],
            f"直接減額方式では、補助金相当額 {yen(grant)} を固定資産圧縮損（費用）として計上し、"
            f"同額だけ機械装置の帳簿価額を直接減らす。\n"
            f"これにより受贈益 {yen(grant)} と圧縮損 {yen(grant)} が相殺され、"
            f"補助金への課税が繰り延べられる。圧縮後の簿価は {yen(cost-grant)}。",
            "圧縮記帳",
            f"①減らすのは**補助金の額 {yen(grant)}**であって取得原価 {yen(cost)} ではない。"
            "②本問で問われているのは圧縮記帳の仕訳だけ。補助金受取や機械購入の仕訳を"
            "書いてしまわないこと。③減価償却は圧縮後の帳簿価額をもとに計算する。")


# ---------------------------------------------------------------- 14. 手形の不渡り
def t_fuwatari(rng):
    face = rnd(rng, 10, 50) * 10_000
    fee = rnd(rng, 1, 5) * 1_000
    q = (f"かねて得意先より受け取り、取引銀行で割り引いていた約束手形￥{yen(face)}が満期日に"
         f"不渡りとなり、銀行より償還請求を受けたので、小切手を振り出して支払った。"
         f"なお、償還請求費用￥{yen(fee)}も同時に小切手を振り出して支払い、"
         f"これらの金額を手形の振出人に請求した。")
    acc = ["不渡手形", "受取手形", "当座預金", "支払手形", "支払手数料", "貸倒損失"]
    return (q, acc, [("不渡手形", face + fee)], [("当座預金", face + fee)],
            f"割引済み手形が不渡りとなり銀行に支払った場合、支払額 {yen(face)} に"
            f"償還請求費用 {yen(fee)} を**含めて**不渡手形（債権）とし、振出人に請求する。\n"
            f"不渡手形 = {yen(face)} ＋ {yen(fee)} = {yen(face+fee)}",
            "手形の不渡り",
            "①償還請求費用も**不渡手形に含める**（支払手数料としない）。"
            "②既に割り引いて手元に手形はないので、受取手形を減らす仕訳は不要。"
            "自社が保有していた手形が不渡りになった場合との違いに注意。")


TEMPLATES = [
    t_shokyaku, t_kawase, t_shihonteki, t_gappei, t_denshi, t_kasai, t_teiritsu,
    t_taritsu, t_zeikoka, t_zoshi, t_lease, t_ekimu, t_asshuku, t_fuwatari,
]
TOPIC_NAMES = ["償却債権取立益", "為替予約", "資本的支出・修繕引当金", "合併・のれん",
               "電子記録債権債務", "火災未決算", "固定資産の売却（定率法）", "売上原価対立法",
               "税効果会計", "増資", "リース取引", "役務収益・役務原価", "圧縮記帳",
               "手形の不渡り"]


def generate(rng: random.Random, avoid: set[str] | None = None):
    """avoid に入っている論点は（可能なら）出題しない。"""
    avoid = avoid or set()
    pool = [t for t in TEMPLATES if t.__name__ not in avoid]
    if len(pool) < 5:
        # 未出題だけでは足りないときは、足りない分だけ既出から補う（全解除しない）
        rest = [t for t in TEMPLATES if t.__name__ in avoid]
        rng.shuffle(rest)
        pool = pool + rest[: 5 - len(pool)]
    picks = rng.sample(pool, 5)
    blocks, topics, lines, used = [], [], [], []
    marks = "アイウエオカキク"
    for i, tpl in enumerate(picks, start=1):
        q, acc, debit, credit, explain, topic, trap = tpl(rng)
        acc = shuffled_choices(rng, acc, DISTRACTORS)
        opts = "　".join(f"{marks[j]}. {a}" for j, a in enumerate(acc))
        lines.append(f"**{i}.** {q}\n\n　{opts}")
        blocks.append(journal(f"q1_{i}", f"{i}.", acc, debit, credit, explain))
        blocks[-1]["trap"] = trap
        blocks[-1]["topic"] = topic
        topics.append(topic)
        used.append(tpl.__name__)
    statement = ("次の各取引について仕訳を示しなさい。ただし、勘定科目は、各取引の下の"
                 "勘定科目から最も適当と思われるものを選ぶこと。\n\n" + "\n\n".join(lines))
    return {
        "no": 1, "title": "第1問（20点）", "field": "商業簿記", "topic": "仕訳",
        "topics": topics, "used": used, "statement": statement,
        "blocks": blocks, "explanation": "",
    }

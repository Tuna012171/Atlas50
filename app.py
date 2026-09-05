
import io
import math
import time
import json
from datetime import datetime

import pandas as pd
import streamlit as st
import yfinance as yf
from openai import OpenAI

st.set_page_config(page_title="Atlas 50", page_icon="🌍", layout="wide")

COMPANIES = [('NVDA', 'NVIDIA', '米国', '北米', '半導体', 'USD'), ('AAPL', 'Apple', '米国', '北米', 'テクノロジー', 'USD'), ('MSFT', 'Microsoft', '米国', '北米', 'ソフトウェア', 'USD'), ('GOOGL', 'Alphabet', '米国', '北米', '通信・広告', 'USD'), ('AMZN', 'Amazon', '米国', '北米', 'EC・クラウド', 'USD'), ('AVGO', 'Broadcom', '米国', '北米', '半導体', 'USD'), ('META', 'Meta Platforms', '米国', '北米', '通信・広告', 'USD'), ('TSLA', 'Tesla', '米国', '北米', '自動車', 'USD'), ('BRK-B', 'Berkshire Hathaway', '米国', '北米', '金融', 'USD'), ('WMT', 'Walmart', '米国', '北米', '小売', 'USD'), ('LLY', 'Eli Lilly', '米国', '北米', '医薬品', 'USD'), ('JPM', 'JPMorgan Chase', '米国', '北米', '銀行', 'USD'), ('XOM', 'Exxon Mobil', '米国', '北米', 'エネルギー', 'USD'), ('JNJ', 'Johnson & Johnson', '米国', '北米', 'ヘルスケア', 'USD'), ('V', 'Visa', '米国', '北米', '決済', 'USD'), ('MA', 'Mastercard', '米国', '北米', '決済', 'USD'), ('COST', 'Costco', '米国', '北米', '小売', 'USD'), ('ORCL', 'Oracle', '米国', '北米', 'ソフトウェア', 'USD'), ('AMD', 'AMD', '米国', '北米', '半導体', 'USD'), ('CRM', 'Salesforce', '米国', '北米', 'ソフトウェア', 'USD'), ('ASML', 'ASML', 'オランダ', '欧州', '半導体装置', 'USD'), ('SAP', 'SAP', 'ドイツ', '欧州', 'ソフトウェア', 'USD'), ('NVO', 'Novo Nordisk', 'デンマーク', '欧州', '医薬品', 'USD'), ('NVS', 'Novartis', 'スイス', '欧州', '医薬品', 'USD'), ('AZN', 'AstraZeneca', '英国', '欧州', '医薬品', 'USD'), ('SHEL', 'Shell', '英国', '欧州', 'エネルギー', 'USD'), ('HSBC', 'HSBC', '英国', '欧州', '銀行', 'USD'), ('UL', 'Unilever', '英国', '欧州', '生活必需品', 'USD'), ('MC.PA', 'LVMH', 'フランス', '欧州', '高級消費財', 'EUR'), ('NESN.SW', 'Nestlé', 'スイス', '欧州', '食品', 'CHF'), ('TSM', 'TSMC ADR', '台湾', 'アジア', '半導体', 'USD'), ('0700.HK', 'Tencent', '中国', 'アジア', 'インターネット', 'HKD'), ('BABA', 'Alibaba ADR', '中国', 'アジア', 'EC・クラウド', 'USD'), ('005930.KS', 'Samsung Electronics', '韓国', 'アジア', '半導体・電子', 'KRW'), ('7203.T', 'Toyota', '日本', 'アジア', '自動車', 'JPY'), ('6758.T', 'Sony Group', '日本', 'アジア', '電機・エンタメ', 'JPY'), ('8306.T', 'Mitsubishi UFJ FG', '日本', 'アジア', '銀行', 'JPY'), ('9984.T', 'SoftBank Group', '日本', 'アジア', '投資・通信', 'JPY'), ('6861.T', 'Keyence', '日本', 'アジア', 'FA・電子機器', 'JPY'), ('2330.TW', 'TSMC Taiwan', '台湾', 'アジア', '半導体', 'TWD'), ('000660.KS', 'SK hynix', '韓国', 'アジア', '半導体', 'KRW'), ('INFY', 'Infosys ADR', 'インド', 'アジア', 'ITサービス', 'USD'), ('RELIANCE.NS', 'Reliance Industries', 'インド', 'アジア', '複合・エネルギー', 'INR'), ('2222.SR', 'Saudi Aramco', 'サウジアラビア', '中東', 'エネルギー', 'SAR'), ('BHP', 'BHP ADR', 'オーストラリア', 'オセアニア', '資源', 'USD'), ('RIO', 'Rio Tinto ADR', '英国/豪州', '欧州・豪州', '資源', 'USD'), ('SHOP', 'Shopify', 'カナダ', '北米', 'ECソフトウェア', 'USD'), ('MELI', 'MercadoLibre', 'ウルグアイ', '中南米', 'EC・フィンテック', 'USD'), ('SE', 'Sea Ltd', 'シンガポール', '東南アジア', 'EC・デジタル', 'USD'), ('RELX', 'RELX', '英国', '欧州', '情報サービス', 'USD')]
MONTHLY_BUDGET_DEFAULT = 20000

st.markdown("""
<style>
.block-container {padding-top: 1.3rem; padding-bottom: 3rem;}
div[data-testid="stMetric"] {
    border: 1px solid rgba(120,120,120,.20);
    border-radius: 14px;
    padding: 12px 14px;
}
.atlas-title {font-size: 2.4rem; font-weight: 800; letter-spacing: -0.04em;}
.atlas-sub {opacity:.68; margin-top:-8px; margin-bottom:18px;}
.badge {display:inline-block; padding:4px 9px; border-radius:999px; font-size:.85rem; border:1px solid rgba(120,120,120,.25);}
.mobile-list-title,
.mobile-stock-card {
    display: none;
}
@media (max-width: 768px) {
.mobile-list-title,
.mobile-stock-card {
    display: block;
}
.st-key-world50_table {
    display: none;
}
.mobile-list-title {
    font-size: 1.8rem;
    font-weight: 700;
    margin: 18px 0 12px 0;
}
    .block-container {
        padding-top: 0.8rem;
        padding-left: 0.8rem;
        padding-right: 0.8rem;
        padding-bottom: 2rem;
    }

    .atlas-title {
        font-size: 1.8em;
        line-height: 1.15;
    }

    .atlas-sub {
        font-size: 0.92em;
        margin-bottom: 12px;
    }

    div[data-testid="stMetric"] {
        padding: 10px 10px;
        border-radius: 12px;
    }

    div[data-testid="stMetricValue"] {
        font-size: 1.45rem;
    }

    div[data-testid="stMetricLabel"] {
        font-size: 0.82rem;
    }

    [data-testid="stHorizontalBlock"] {
        gap: 0.5rem;
    }

    .stDataFrame {
        overflow-x: auto;
    }

    button {
        min-height: 42px;
    }


/* ここにカード用CSSを追加 */

.mobile-stock-card {
    border: 1px solid rgba(120,120,120,.20);
    border-radius: 14px;
    padding: 14px;
    margin-bottom: 10px;
}

.mobile-rank {
    font-size: 0.85rem;
    opacity: 0.65;
}

.mobile-company {
    font-size: 1.1rem;
    font-weight: 700;
    margin-top: 2px;
}

.mobile-meta {
    font-size: 0.85rem;
    opacity: 0.7;
    margin-top: 2px;
}

.mobile-score {
    font-size: 1rem;
    font-weight: 700;
    margin-top: 10px;
}

.mobile-stats {
    font-size: 0.88rem;
    margin-top: 4px;
}

.mobile-judge {
    display: inline-block;
    margin-top: 8px;
    padding: 3px 8px;
    border-radius: 999px;
    border: 1px solid rgba(120,120,120,.25);
    font-size: 0.8rem;
}
}
</style>
""", unsafe_allow_html=True)

def _extract_one(raw, ticker):
    if raw is None or raw.empty:
        return pd.DataFrame()
    if not isinstance(raw.columns, pd.MultiIndex):
        return raw.copy()
    lvl0 = list(map(str, raw.columns.get_level_values(0)))
    lvl1 = list(map(str, raw.columns.get_level_values(1)))
    if ticker in lvl0:
        return raw[ticker].copy()
    if ticker in lvl1:
        return raw.xs(ticker, axis=1, level=1).copy()
    return pd.DataFrame()

def _rsi(close, period=14):
    d = close.diff()
    gain = d.clip(lower=0).rolling(period).mean()
    loss = -d.clip(upper=0).rolling(period).mean()
    rs = gain / loss.replace(0, float("nan"))
    return 100 - (100 / (1 + rs))

def score_parts(cur, r1w, r1m, r3m, sma5, sma20, sma60, rsi, vr, dist_high):
    momentum_1w = max(0, min(12, 6 + r1w * 120))
    momentum_1m = max(0, min(15, 7 + r1m * 60))
    momentum_3m = max(0, min(15, 7 + r3m * 30))
    ma = 0
    ma += 8 if cur > sma20 else 0
    ma += 8 if cur > sma60 else 0
    ma += 6 if sma5 > sma20 else 0
    ma += 6 if sma20 > sma60 else 0
    rsi_score = 10 if 45 <= rsi <= 68 else (6 if 35 <= rsi <= 75 else 2)
    vol_score = max(0, min(10, (vr - 0.8) * 8))
    high_score = 10 if dist_high >= -0.05 else (7 if dist_high >= -0.10 else (4 if dist_high >= -0.20 else 0))
    total = round(max(0, min(100, momentum_1w + momentum_1m + momentum_3m + ma + rsi_score + vol_score + high_score)), 1)
    return total, {
        "1週モメンタム": round(momentum_1w,1),
        "1か月モメンタム": round(momentum_1m,1),
        "3か月モメンタム": round(momentum_3m,1),
        "移動平均": round(ma,1),
        "RSI": round(rsi_score,1),
        "出来高": round(vol_score,1),
        "52週高値": round(high_score,1),
    }

@st.cache_data(ttl=1800, show_spinner=False)
def load_fx():
    currencies = sorted(set(x[5] for x in COMPANIES if x[5] != "JPY"))
    pairs = [f"{c}JPY=X" for c in currencies]
    rates = {"JPY":1.0}
    try:
        raw = yf.download(pairs, period="5d", interval="1d", auto_adjust=False, progress=False, group_by="ticker", threads=True, timeout=20)
        for c,p in zip(currencies,pairs):
            try:
                d = _extract_one(raw,p)
                close = pd.to_numeric(d["Close"], errors="coerce").dropna()
                rates[c] = float(close.iloc[-1])
            except Exception:
                rates[c] = None
    except Exception:
        for c in currencies:
            rates[c] = None
    return rates

@st.cache_data(ttl=1800, show_spinner=False)
def load_data():
    rows, histories, errors = [], {}, []
    tickers = [x[0] for x in COMPANIES]

    for start in range(0, len(tickers), 10):
        batch = tickers[start:start+10]
        try:
            raw = yf.download(batch, period="1y", interval="1d", auto_adjust=True, group_by="ticker", threads=True, progress=False, timeout=20)
        except Exception as e:
            raw = pd.DataFrame()
            errors.append(f"batch {start//10+1}: {type(e).__name__}")

        for t in batch:
            _, name, country, region, sector, currency = next(x for x in COMPANIES if x[0] == t)
            try:
                d = _extract_one(raw, t)
                if d.empty or "Close" not in d.columns:
                    d = yf.download(t, period="1y", interval="1d", auto_adjust=True, progress=False, timeout=15)
                if d.empty or "Close" not in d.columns:
                    raise ValueError("価格列なし")
                d = d.dropna(subset=["Close"]).copy()
                close = pd.to_numeric(d["Close"], errors="coerce").dropna()
                if len(close) < 65:
                    raise ValueError("履歴不足")

                volume = pd.to_numeric(d["Volume"], errors="coerce").fillna(0) if "Volume" in d.columns else pd.Series(0,index=close.index)
                cur = float(close.iloc[-1])
                p1,p5,p21,p63 = map(float,[close.iloc[-2],close.iloc[-6],close.iloc[-22],close.iloc[-64]])
                r1d,r1w,r1m,r3m = cur/p1-1,cur/p5-1,cur/p21-1,cur/p63-1
                sma5,sma20,sma60 = float(close.rolling(5).mean().iloc[-1]),float(close.rolling(20).mean().iloc[-1]),float(close.rolling(60).mean().iloc[-1])
                rsiv = _rsi(close,14).iloc[-1]
                rsiv = float(rsiv) if pd.notna(rsiv) else 50.0
                avg20 = float(volume.rolling(20).mean().iloc[-1]) if len(volume)>=20 else 0
                vr = float(volume.iloc[-1])/avg20 if avg20>0 else 1.0
                high52 = float(close.max())
                dh = cur/high52-1 if high52 else 0.0
                score, parts = score_parts(cur,r1w,r1m,r3m,sma5,sma20,sma60,rsiv,vr,dh)
                signal = "強い＋" if score>=75 else ("＋" if score>=60 else ("様子見" if score>=45 else "－"))
                histories[t] = pd.DataFrame({"Close":close, "SMA20":close.rolling(20).mean(), "SMA60":close.rolling(60).mean()})
                rows.append([t,name,country,region,sector,currency,cur,r1d,r1w,r1m,r3m,rsiv,vr,cur/sma20-1,cur/sma60-1,dh,score,signal,close.index[-1].strftime("%Y-%m-%d"),parts])
            except Exception as e:
                errors.append(f"{t}: {type(e).__name__}")
        time.sleep(.35)

    cols = ["Ticker","会社名","国","地域","業種","通貨","現在値","1日","1週","1か月","3か月","RSI","出来高倍率","20日線比","60日線比","高値乖離","Atlas Score","判定","最終日","Score内訳"]
    df = pd.DataFrame(rows, columns=cols)
    if not df.empty:
        df = df.sort_values("Atlas Score",ascending=False).reset_index(drop=True)
        df.insert(0,"順位",range(1,len(df)+1))
    return df,histories,errors

@st.cache_data(ttl=1800, show_spinner=False)
def load_news(ticker, company_name=""):
    items = []

    try:
        raw = yf.Ticker(ticker).news or []

        company_text = str(company_name or "").lower()

        ignore_words = {
            "inc", "corp", "corporation", "group",
            "holdings", "plc", "ltd", "company", "the", "fg"
        }

        keywords = [
            word.lower()
            for word in company_text.replace("&", " ").split()
            if len(word) >= 3 and word.lower() not in ignore_words
        ]

        for n in raw[:20]:
            content = n.get("content", n)

            title = content.get("title") or n.get("title")
            summary = content.get("summary") or n.get("summary") or ""

            if not title:
                continue

            search_text = f"{title} {summary}".lower()

            # 選択した会社に関係するニュースだけ残す
            if keywords and not any(word in search_text for word in keywords):
                continue

            provider = content.get("provider", {})
            publisher = (
                provider.get("displayName")
                if isinstance(provider, dict)
                else n.get("publisher")
            )

            link = None

            link_candidates = [
                content.get("clickThroughUrl"),
                content.get("canonicalUrl"),
                content.get("financeUrl"),
                n.get("link"),
            ]

            for candidate in link_candidates:
                if isinstance(candidate, dict):
                    candidate = candidate.get("url")

                if isinstance(candidate, str) and candidate:
                    link = candidate
                    break
            items.append({
                "title": title,
                "publisher": publisher or "News",
                "link": link
            })

            if len(items) >= 6:
                break

    except Exception:
        pass

    return items
    
@st.cache_data(ttl=86400, show_spinner=False)
def analyze_news_with_ai(company_name, title):
    try:
        client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

        prompt = f"""
あなたはAtlas50の初心者向け株式ニュース解説AIです。

会社名:
{company_name}

ニュース見出し:
{title}

次のJSONだけを返してください。

{{
  "title_ja": "初心者にも分かる短い日本語タイトル",
  "summary": "専門用語をできるだけ使わず2文以内で説明",
  "impact": "追い風候補・中立・リスク候補 のどれか"
}}

ルール:
- 買う・売るなどの投資推奨はしない
- 見出しから分からない事実を作らない
- 判断できない場合は中立
- 日本語で書く
"""

        response = client.responses.create(
            model="gpt-5.6-luna",
            input=prompt
        )

        text = response.output_text.strip()

        if text.startswith("```"):
            text = text.replace("```json", "").replace("```", "").strip()

        return json.loads(text)

    except Exception:
        return {
            "title_ja": title,
            "summary": "AI解説を取得できませんでした。",
            "impact": "中立"
        }


if "favorites" not in st.session_state:
    st.session_state.favorites = set()
if "portfolio" not in st.session_state:
    st.session_state.portfolio = pd.DataFrame(columns=["Ticker","株数","平均取得単価"])

st.markdown('<div class="atlas-title">ATLAS 50</div>',unsafe_allow_html=True)
st.markdown('<div class="atlas-sub">世界の注目50社を、数分で把握する。</div>',unsafe_allow_html=True)

with st.spinner("世界50社と為替をチェック中..."):
    df,histories,errors = load_data()
    fx = load_fx()

if df.empty:
    st.error("株価データを取得できませんでした。右上メニューからRerunを試してください。")
    with st.expander("エラー詳細"): st.code("\n".join(errors[:50]))
    st.stop()

df["FX→JPY"] = df["通貨"].map(fx)
df["円換算価格"] = df["現在値"] * df["FX→JPY"]
df["2万円で1株"] = df["円換算価格"].apply(lambda x: "○" if pd.notna(x) and x <= 20000 else "×")
df["2万円で買える株数"] = df["円換算価格"].apply(lambda x: int(20000//x) if pd.notna(x) and x>0 else 0)

tabs = st.tabs(["🏠 ホーム","🌍 世界50","🔎 個別分析","⭐ お気に入り","💼 保有株","💴 月2万円"])

with tabs[0]:
    a,b,c,d,e = st.columns(5)
    a.metric("取得",f"{len(df)} / 50")
    b.metric("強い＋",int((df["判定"]=="強い＋").sum()))
    c.metric("＋",int((df["判定"]=="＋").sum()))
    d.metric("2万円で1株買える",int((df["2万円で1株"]=="○").sum()))
    e.metric("最終日",str(df["最終日"].max()))

    st.subheader("今日の上位10")
    top = df.head(10)[["順位","会社名","国","業種","円換算価格","1か月","3か月","Atlas Score","判定"]].copy()
    top["1か月"] = (top["1か月"]*100).round(2)
    top["3か月"] = (top["3か月"]*100).round(2)
    st.dataframe(top,use_container_width=True,hide_index=True,column_config={
        "円換算価格":st.column_config.NumberColumn(format="¥%.0f"),
        "1か月":st.column_config.NumberColumn(format="%.2f%%"),
        "3か月":st.column_config.NumberColumn(format="%.2f%%"),
        "Atlas Score":st.column_config.ProgressColumn(min_value=0,max_value=100,format="%.0f")
    })
    st.bar_chart(df.head(10).set_index("会社名")["Atlas Score"])

with tabs[1]:
    f1,f2,f3,f4 = st.columns(4)
    country = f1.selectbox("国",["すべて"]+sorted(df["国"].unique().tolist()),key="country")
    region = f2.selectbox("地域",["すべて"]+sorted(df["地域"].unique().tolist()),key="region")
    sector = f3.selectbox("業種",["すべて"]+sorted(df["業種"].unique().tolist()),key="sector")
    minscore = f4.slider("最低Score",0,100,0,key="score")

    view=df.copy()
    if country!="すべて": view=view[view["国"]==country]
    if region!="すべて": view=view[view["地域"]==region]
    if sector!="すべて": view=view[view["業種"]==sector]
    view=view[view["Atlas Score"]>=minscore]

    show=view[["順位","会社名","国","地域","業種","通貨","現在値","円換算価格","2万円で1株","2万円で買える株数","1日","1週","1か月","3か月","RSI","出来高倍率","Atlas Score","判定"]].copy()
    for col in ["1日","1週","1か月","3か月"]: show[col]=(show[col]*100).round(2)
    world50_table = st.container(key="world50_table")
    world50_table.dataframe(show,use_container_width=True,hide_index=True,column_config={
        "円換算価格":st.column_config.NumberColumn(format="¥%.0f"),
        "1日":st.column_config.NumberColumn(format="%.2f%%"),"1週":st.column_config.NumberColumn(format="%.2f%%"),
        "1か月":st.column_config.NumberColumn(format="%.2f%%"),"3か月":st.column_config.NumberColumn(format="%.2f%%"),
        "Atlas Score":st.column_config.ProgressColumn(min_value=0,max_value=100,format="%.0f")
    })
    st.markdown(
    '<div class="mobile-list-title">スマホ向け一覧</div>',
    unsafe_allow_html=True
    )

    for _, row in show.iterrows():
        score = int(row["Atlas Score"])
        one_month = row["1か月"] 
        three_month = row["3か月"] 

        st.markdown(
            f"""
            <div class="mobile-stock-card">
                <div class="mobile-rank">#{int(row['順位'])}</div>
                <div class="mobile-company">{row['会社名']}</div>
                <div class="mobile-meta">{row['国']} ・ {row['業種']}</div>
                <div class="mobile-score">Atlas Score {score}</div>
                <div class="mobile-stats">
                    1カ月 {one_month:.2f}% ｜ 3カ月 {three_month:.2f}%
                </div>
                <div class="mobile-judge">{row['判定']}</div>
            </div>
            """,
            unsafe_allow_html=True
        )
with tabs[2]:
    selected = st.selectbox("会社を選ぶ",df["会社名"].tolist(),key="detail_company")
    row = df[df["会社名"]==selected].iloc[0]
    t = row["Ticker"]
    
    st.markdown(f"## {selected}")
    st.caption(f"{row['国']} ・ {row['業種']}　｜　Ticker: {t}")
    
    c1,c2,c3,c4,c5 = st.columns(5)
    c1.metric("Atlas Score",f'{row["Atlas Score"]:.0f}')
    c2.metric("判定",row["判定"])
    c3.metric("円換算",f'¥{row["円換算価格"]:,.0f}' if pd.notna(row["円換算価格"]) else "-")
    c4.metric("1か月",f'{row["1か月"]*100:.2f}%')
    c5.metric("3か月",f'{row["3か月"]*100:.2f}%')
    score = float(row["Atlas Score"])
    one_month = float(row["1か月"]) * 100
    three_month = float(row["3か月"]) * 100

    st.markdown("### 🔰 30秒でわかる")

    good_points = []
    risk_points = []

    if score >= 80:
        good_points.append("Atlas Scoreが高く、現在の注目度は高めです")
    elif score >= 65:
        good_points.append("Atlas Scoreは中〜高水準です")

    if one_month > 0:
        good_points.append(f"直近1か月は +{one_month:.1f}%")
    else:
        risk_points.append(f"直近1か月は {one_month:.1f}%")

    if three_month > 0:
        good_points.append(f"直近3か月は +{three_month:.1f}%")
    else:
        risk_points.append(f"直近3か月は {three_month:.1f}%")

    if abs(one_month) >= 15:
        risk_points.append("1か月の値動きが大きく、価格変動には注意")

    if not good_points:
        good_points.append("現在は強いプラス材料が少なめです")

    if not risk_points:
        risk_points.append("値動きだけでは大きな警戒材料は確認されていません")

    st.info("✅ 良い材料\n\n" + "\n\n".join(f"・{x}" for x in good_points))
    st.warning("⚠️ 注意点\n\n" + "\n\n".join(f"・{x}" for x in risk_points))
    if st.button("⭐ お気に入りに追加/解除",key="fav_btn"):
        if t in st.session_state.favorites: st.session_state.favorites.remove(t)
        else: st.session_state.favorites.add(t)

    st.subheader("🔥 なぜ今注目？")

    news_preview = load_news(t, selected)
    reasons = []

    if score >= 80:
        reasons.append(f"Atlas Scoreが{score:.0f}と高く、現在の注目度はかなり高めです")
    elif score >= 65:
        reasons.append(f"Atlas Scoreが{score:.0f}で、中〜高水準の注目度です")

    if one_month >= 5:
        reasons.append(f"直近1か月で +{one_month:.1f}% 上昇しています")
    elif one_month <= -5:
        reasons.append(f"直近1か月で {one_month:.1f}% 下落しており、値動きには注意が必要です")

    if three_month >= 10:
        reasons.append(f"直近3か月では +{three_month:.1f}% と強い動きです")

    if news_preview:
        headline = news_preview[0].get("title")
        if headline:
            reasons.append(f"最近の注目ニュース：{headline}")

    if reasons:
        for reason in reasons[:4]:
            st.write(f"・{reason}")
    else:
        st.write("・現在は大きく目立つ材料が少ない状態です")
    st.subheader("最近のニュース")
    news = news_preview
    if news:
        for i, item in enumerate(news[:3], start=1):
            card = st.container(border=True)
            card.markdown(f"### 📰 注目ニュース {i}")

            ai_news = analyze_news_with_ai(selected, item["title"])

            title_ja = ai_news.get("title_ja", item["title"])
            summary_ja = ai_news.get(
                "summary",
                "ニュースの解説を取得できませんでした。"
            )
            impact = ai_news.get("impact", "中立")

            if impact == "追い風候補":
                impact_icon = "🟢"
            elif impact == "リスク候補":
                impact_icon = "🔴"
            else:
                impact_icon = "🟡"

            card.write(f"**🇯🇵 {title_ja}**")
            card.caption(f"情報元：{item['publisher']}")

            card.info(
                f"💡 初心者向け解説\n\n"
                f"{summary_ja}"
            )

            card.write(
                f"📊 **ニュースの影響：{impact_icon} {impact}**"
            )

            card.caption(f"英語原文：{item['title']}")

            if item["link"]:
                card.markdown(f"[🔗 元の記事を見る]({item['link']})")

    else:
        st.caption("この会社に関連するニュースを取得できませんでした。")
    st.subheader("1年チャート")
    hist = histories.get(t)
    if hist is not None and not hist.empty:
        st.line_chart(hist[["Close","SMA20","SMA60"]])

    st.subheader("Scoreの内訳")
    parts = row["Score内訳"]
    parts_df = pd.DataFrame({"項目":list(parts.keys()),"点数":list(parts.values())})
    st.bar_chart(parts_df.set_index("項目")["点数"])
with tabs[3]:
    favdf = df[df["Ticker"].isin(st.session_state.favorites)].copy()
    if favdf.empty:
        st.info("個別分析で「お気に入りに追加/解除」を押すとここに表示されます。")
    else:
        st.dataframe(favdf[["順位","会社名","国","円換算価格","1か月","3か月","Atlas Score","判定"]],use_container_width=True,hide_index=True)

with tabs[4]:
    st.caption("保有情報はこのブラウザセッション内で管理します。下のCSV保存/読込でバックアップできます。")
    tickmap = {x[0]:x[1] for x in COMPANIES}
    edited = st.data_editor(
        st.session_state.portfolio,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "Ticker":st.column_config.SelectboxColumn(options=[x[0] for x in COMPANIES],required=True),
            "株数":st.column_config.NumberColumn(min_value=0.0,step=0.01),
            "平均取得単価":st.column_config.NumberColumn(min_value=0.0,step=0.01),
        },
        key="portfolio_editor"
    )
    st.session_state.portfolio = edited

    calc=[]
    for _,p in edited.dropna(subset=["Ticker"]).iterrows():
        rr=df[df["Ticker"]==p["Ticker"]]
        if rr.empty: continue
        rr=rr.iloc[0]
        qty=float(p.get("株数",0) or 0); avg=float(p.get("平均取得単価",0) or 0)
        fxr=rr["FX→JPY"] if pd.notna(rr["FX→JPY"]) else 1
        invested=qty*avg*fxr; current=qty*rr["円換算価格"]; pnl=current-invested
        calc.append([p["Ticker"],rr["会社名"],qty,invested,current,pnl,(pnl/invested if invested else 0),rr["Atlas Score"],rr["判定"]])
    if calc:
        pf=pd.DataFrame(calc,columns=["Ticker","会社名","株数","投資額(円)","評価額(円)","損益(円)","損益率","Score","判定"])
        p1,p2,p3=st.columns(3)
        p1.metric("投資額",f'¥{pf["投資額(円)"].sum():,.0f}')
        p2.metric("評価額",f'¥{pf["評価額(円)"].sum():,.0f}')
        p3.metric("損益",f'¥{pf["損益(円)"].sum():,.0f}')
        st.dataframe(pf,use_container_width=True,hide_index=True)
    csv=edited.to_csv(index=False).encode("utf-8-sig")
    st.download_button("保有株CSVを保存",csv,"atlas50_portfolio.csv","text/csv")
    upl=st.file_uploader("保存した保有株CSVを読み込む",type=["csv"],key="pfupload")
    if upl is not None:
        try:
            st.session_state.portfolio=pd.read_csv(upl)
            st.success("読み込みました。")
        except Exception:
            st.error("CSVを読み込めませんでした。")

with tabs[5]:
    budget = st.number_input("今月の予算",min_value=0,value=MONTHLY_BUDGET_DEFAULT,step=1000)
    buyable = df[(df["円換算価格"].notna()) & (df["円換算価格"]<=budget)].copy()
    st.metric("1株買える企業",len(buyable))
    st.caption("これは『予算内で1株買えるか』の表示で、買い推奨ではありません。")
    if not buyable.empty:
        buyable=buyable.sort_values(["Atlas Score","円換算価格"],ascending=[False,True])
        st.dataframe(buyable[["順位","会社名","国","業種","円換算価格","2万円で買える株数","Atlas Score","判定"]],use_container_width=True,hide_index=True,column_config={
            "円換算価格":st.column_config.NumberColumn(format="¥%.0f"),
            "Atlas Score":st.column_config.ProgressColumn(min_value=0,max_value=100,format="%.0f")
        })

if errors:
    with st.expander("今回の取得エラー"):
        st.code("\n".join(errors[:50]))

st.divider()
st.caption("Atlas Scoreは価格トレンドを整理するための学習・監視指標です。買い推奨・売り推奨・将来の利益保証ではありません。為替・株価・ニュースには遅延や取得失敗があり得ます。")

import html
import time
import json
import hashlib
import io

import altair as alt
import pandas as pd
import streamlit as st
import yfinance as yf
from openai import OpenAI


st.set_page_config(page_title="ATLAS 50", layout="wide", initial_sidebar_state="collapsed")

APP_VERSION = "3.2.1"
APP_LABEL = "NOIR JP"
AI_TIMEOUT_SECONDS = 20.0

# ------------------------------
# 基本設定
# ------------------------------
COMPANIES = [
    ('NVDA', 'NVIDIA', '米国', '北米', '半導体', 'USD'),
    ('AAPL', 'Apple', '米国', '北米', 'テクノロジー', 'USD'),
    ('MSFT', 'Microsoft', '米国', '北米', 'ソフトウェア', 'USD'),
    ('GOOGL', 'Alphabet', '米国', '北米', '通信・広告', 'USD'),
    ('AMZN', 'Amazon', '米国', '北米', 'EC・クラウド', 'USD'),
    ('AVGO', 'Broadcom', '米国', '北米', '半導体', 'USD'),
    ('META', 'Meta Platforms', '米国', '北米', '通信・広告', 'USD'),
    ('TSLA', 'Tesla', '米国', '北米', '自動車', 'USD'),
    ('BRK-B', 'Berkshire Hathaway', '米国', '北米', '金融', 'USD'),
    ('WMT', 'Walmart', '米国', '北米', '小売', 'USD'),
    ('LLY', 'Eli Lilly', '米国', '北米', '医薬品', 'USD'),
    ('JPM', 'JPMorgan Chase', '米国', '北米', '銀行', 'USD'),
    ('XOM', 'Exxon Mobil', '米国', '北米', 'エネルギー', 'USD'),
    ('JNJ', 'Johnson & Johnson', '米国', '北米', 'ヘルスケア', 'USD'),
    ('V', 'Visa', '米国', '北米', '決済', 'USD'),
    ('MA', 'Mastercard', '米国', '北米', '決済', 'USD'),
    ('COST', 'Costco', '米国', '北米', '小売', 'USD'),
    ('ORCL', 'Oracle', '米国', '北米', 'ソフトウェア', 'USD'),
    ('AMD', 'AMD', '米国', '北米', '半導体', 'USD'),
    ('CRM', 'Salesforce', '米国', '北米', 'ソフトウェア', 'USD'),
    ('ASML', 'ASML', 'オランダ', '欧州', '半導体装置', 'USD'),
    ('SAP', 'SAP', 'ドイツ', '欧州', 'ソフトウェア', 'USD'),
    ('NVO', 'Novo Nordisk', 'デンマーク', '欧州', '医薬品', 'USD'),
    ('NVS', 'Novartis', 'スイス', '欧州', '医薬品', 'USD'),
    ('AZN', 'AstraZeneca', '英国', '欧州', '医薬品', 'USD'),
    ('SHEL', 'Shell', '英国', '欧州', 'エネルギー', 'USD'),
    ('HSBC', 'HSBC', '英国', '欧州', '銀行', 'USD'),
    ('UL', 'Unilever', '英国', '欧州', '生活必需品', 'USD'),
    ('MC.PA', 'LVMH', 'フランス', '欧州', '高級消費財', 'EUR'),
    ('NESN.SW', 'Nestlé', 'スイス', '欧州', '食品', 'CHF'),
    ('TSM', 'TSMC ADR', '台湾', 'アジア', '半導体', 'USD'),
    ('0700.HK', 'Tencent', '中国', 'アジア', 'インターネット', 'HKD'),
    ('BABA', 'Alibaba ADR', '中国', 'アジア', 'EC・クラウド', 'USD'),
    ('005930.KS', 'Samsung Electronics', '韓国', 'アジア', '半導体・電子', 'KRW'),
    ('7203.T', 'Toyota', '日本', 'アジア', '自動車', 'JPY'),
    ('6758.T', 'Sony Group', '日本', 'アジア', '電機・エンタメ', 'JPY'),
    ('8306.T', 'Mitsubishi UFJ FG', '日本', 'アジア', '銀行', 'JPY'),
    ('9984.T', 'SoftBank Group', '日本', 'アジア', '投資・通信', 'JPY'),
    ('6861.T', 'Keyence', '日本', 'アジア', 'FA・電子機器', 'JPY'),
    ('2330.TW', 'TSMC Taiwan', '台湾', 'アジア', '半導体', 'TWD'),
    ('000660.KS', 'SK hynix', '韓国', 'アジア', '半導体', 'KRW'),
    ('INFY', 'Infosys ADR', 'インド', 'アジア', 'ITサービス', 'USD'),
    ('RELIANCE.NS', 'Reliance Industries', 'インド', 'アジア', '複合・エネルギー', 'INR'),
    ('2222.SR', 'Saudi Aramco', 'サウジアラビア', '中東', 'エネルギー', 'SAR'),
    ('BHP', 'BHP ADR', 'オーストラリア', 'オセアニア', '資源', 'USD'),
    ('RIO', 'Rio Tinto ADR', '英国/豪州', '欧州・豪州', '資源', 'USD'),
    ('SHOP', 'Shopify', 'カナダ', '北米', 'ECソフトウェア', 'USD'),
    ('MELI', 'MercadoLibre', 'ウルグアイ', '中南米', 'EC・フィンテック', 'USD'),
    ('SE', 'Sea Ltd', 'シンガポール', '東南アジア', 'EC・デジタル', 'USD'),
    ('RELX', 'RELX', '英国', '欧州', '情報サービス', 'USD'),
]

COMPANY_META = {row[0]: row for row in COMPANIES}
COMPANY_BY_NAME = {row[1]: row for row in COMPANIES}

MONTHLY_BUDGET_DEFAULT = 20000
HISTORY_PERIOD = "2y"  # 1年騰落率を安定して計算するため、2年分取得する

# ニュースの別名。会社名だけでは拾いにくい見出しを補う。
NEWS_ALIASES = {
    "Alphabet": ["google"],
    "Meta Platforms": ["facebook"],
    "Berkshire Hathaway": ["berkshire", "warren buffett"],
    "Mitsubishi UFJ FG": ["mufg", "mitsubishi ufj financial group"],
    "TSMC ADR": ["tsmc", "taiwan semiconductor"],
    "TSMC Taiwan": ["tsmc", "taiwan semiconductor"],
    "Novo Nordisk": ["novo"],
    "Saudi Aramco": ["aramco"],
    "SoftBank Group": ["softbank"],
    "Samsung Electronics": ["samsung"],
    "Johnson & Johnson": ["johnson & johnson", "j&j"],
}

# Atlas50の29業種を、比較しやすい9つの大分類にまとめる。
# これはAtlas50内だけの独自グルーピングで、市場標準のセクター分類ではない。
SECTOR_GROUPS = {
    "半導体": "半導体・電子",
    "半導体・電子": "半導体・電子",
    "半導体装置": "半導体・電子",
    "ソフトウェア": "ソフトウェア・IT",
    "ITサービス": "ソフトウェア・IT",
    "情報サービス": "ソフトウェア・IT",
    "通信・広告": "インターネット・EC",
    "EC・クラウド": "インターネット・EC",
    "インターネット": "インターネット・EC",
    "ECソフトウェア": "インターネット・EC",
    "EC・フィンテック": "インターネット・EC",
    "EC・デジタル": "インターネット・EC",
    "金融": "金融・決済",
    "銀行": "金融・決済",
    "決済": "金融・決済",
    "医薬品": "ヘルスケア",
    "ヘルスケア": "ヘルスケア",
    "小売": "消費・生活",
    "生活必需品": "消費・生活",
    "食品": "消費・生活",
    "高級消費財": "消費・生活",
    "エネルギー": "エネルギー・資源",
    "複合・エネルギー": "エネルギー・資源",
    "資源": "エネルギー・資源",
    "自動車": "自動車・産業",
    "FA・電子機器": "自動車・産業",
    "テクノロジー": "テクノロジー・通信",
    "電機・エンタメ": "テクノロジー・通信",
    "投資・通信": "テクノロジー・通信",
}

WATCH_DEFAULTS = {
    "watch_score": 0.0,
    "watch_1m": -100.0,
    "watch_3m": -100.0,
    "watch_volume": 0.0,
    "watch_sma20": False,
    "watch_sma60": False,
    "watch_region": "すべて",
    "watch_sector_group": "すべて",
    "watch_sort": "Atlas Scoreが高い順",
    "watch_limit": 12,
}

WATCH_SORT_OPTIONS = [
    "Atlas Scoreが高い順",
    "1か月上昇率が高い順",
    "3か月上昇率が高い順",
    "出来高倍率が高い順",
]


# ------------------------------
# UI language layer (Japanese-first presentation)
# Internal data keys remain Japanese for backward compatibility.
# Short English kickers are intentionally kept as visual brand elements.
# ------------------------------
SIGNAL_EN = {"強い＋": "強い", "＋": "プラス", "様子見": "中立", "－": "弱い"}
SCORE_PART_EN = {
    "1週モメンタム": "1週モメンタム", "1か月モメンタム": "1か月モメンタム",
    "3か月モメンタム": "3か月モメンタム", "移動平均": "移動平均", "RSI": "RSI",
    "出来高": "出来高", "52週高値": "52週高値との位置",
}
WATCH_SORT_EN = {
    "Atlas Scoreが高い順": "Atlas Scoreが高い順", "1か月上昇率が高い順": "1か月上昇率が高い順",
    "3か月上昇率が高い順": "3か月上昇率が高い順", "出来高倍率が高い順": "出来高倍率が高い順",
}
WORLD_SORT_EN = {
    "Atlas Scoreが高い順": "Atlas Scoreが高い順", "1か月上昇率が高い順": "1か月上昇率が高い順",
    "3か月上昇率が高い順": "3か月上昇率が高い順", "円換算価格が安い順": "円換算価格が安い順",
}
DISPLAY_COLUMN_NAMES = {
    "順位": "順位", "会社名": "会社名", "国": "国", "地域": "地域", "業種": "業種",
    "業種グループ": "業種グループ", "通貨": "通貨", "現在値": "現在値", "円換算価格": "円換算価格",
    "1日": "1日", "1週": "1週", "1か月": "1か月", "3か月": "3か月", "6か月": "6か月", "1年": "1年",
    "出来高倍率": "出来高倍率", "20日線比": "20日線比", "60日線比": "60日線比",
    "高値乖離": "52週高値比", "判定": "判定", "最終日": "最新株価日",
    "平均Score": "平均Score", "銘柄数": "銘柄数", "1か月平均": "1か月平均", "3か月平均": "3か月平均",
    "6か月平均": "6か月平均", "1か月プラス率": "1か月プラス率", "予算で買える株数": "予算内株数",
    "株数": "株数", "投資額(円)": "投資額(円)", "評価額(円)": "評価額(円)",
    "損益(円)": "損益(円)", "損益率": "損益率", "平均取得単価": "平均取得単価",
}


def _country_en(value):
    return str(value)


def _region_en(value):
    return str(value)


def _sector_en(value):
    return str(value)


def _sector_group_en(value):
    return str(value)


def _signal_en(value):
    return SIGNAL_EN.get(str(value), str(value))


def _all_en(value):
    return "すべて" if str(value) == "すべて" else str(value)


def _ui_frame(frame):
    """表示専用の日本語コピー。内部データの列名や値は変更しない。"""
    out = frame.copy()
    if "判定" in out.columns:
        out["判定"] = out["判定"].map(_signal_en)
    return out.rename(columns=DISPLAY_COLUMN_NAMES)


def _section_intro(kicker, title, text):
    st.markdown(
        f'<div class="section-kicker">{html.escape(kicker)}</div>'
        f'<div class="section-title">{html.escape(title)}</div>'
        f'<div class="section-copy">{html.escape(text)}</div>',
        unsafe_allow_html=True,
    )


def _status_tone(signal):
    return {
        "強い＋": "positive", "＋": "positive", "様子見": "neutral", "－": "negative"
    }.get(str(signal), "neutral")

# ------------------------------
# 見た目
# ------------------------------
st.markdown(
    """
<style>
:root {
    --atlas-bg: #06090C;
    --atlas-surface: #0B1117;
    --atlas-surface-2: #0F171F;
    --atlas-surface-3: #131D27;
    --atlas-border: #1B2A36;
    --atlas-border-soft: #13202A;
    --atlas-text: #F5F7F9;
    --atlas-muted: #95A3B1;
    --atlas-muted-2: #697A89;
    --atlas-accent: #62E2D0;
    --atlas-accent-2: #78AEFF;
    --atlas-positive: #4ADE80;
    --atlas-negative: #FB7185;
    --atlas-warning: #F5C76B;
}

html, body, [data-testid="stAppViewContainer"], .stApp {
    background: var(--atlas-bg) !important;
    color: var(--atlas-text) !important;
}

[data-testid="stHeader"] {
    background: rgba(6, 9, 12, 0.88) !important;
    backdrop-filter: blur(18px);
    border-bottom: 1px solid rgba(255,255,255,.025);
}

[data-testid="stToolbar"] { right: 0.75rem; }

.block-container {
    max-width: 1460px;
    padding-top: 1.15rem;
    padding-bottom: 5rem;
}

p, label, span, div { -webkit-font-smoothing: antialiased; }

a { color: var(--atlas-accent-2) !important; }

.atlas-hero {
    padding: 24px 0 24px 0;
    border-bottom: 1px solid var(--atlas-border-soft);
    margin-bottom: 12px;
}

.atlas-wordmark {
    display: flex;
    align-items: baseline;
    gap: 11px;
}

.atlas-title {
    font-size: clamp(2.4rem, 5vw, 4.35rem);
    font-weight: 860;
    letter-spacing: -0.07em;
    line-height: .95;
    margin: 0;
    color: var(--atlas-text);
}

.atlas-title-mark {
    display: inline-block;
    width: 8px;
    height: 8px;
    background: var(--atlas-accent);
    border-radius: 2px;
    transform: translateY(-4px);
    box-shadow: 0 0 24px rgba(99,230,213,.25);
}

.atlas-sub {
    margin-top: 15px;
    color: #8798A8;
    font-size: .72rem;
    font-weight: 700;
    letter-spacing: .22em;
    text-transform: uppercase;
}

.atlas-tagline {
    margin-top: 11px;
    max-width: 650px;
    color: #C2CBD4;
    font-size: .96rem;
    line-height: 1.75;
    letter-spacing: .005em;
}

.atlas-version-row {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 6px;
    margin: 0 0 15px 0;
}

.atlas-chip, .badge {
    display: inline-flex;
    align-items: center;
    padding: 4px 8px;
    border: 1px solid #182631;
    border-radius: 5px;
    background: rgba(255,255,255,.012);
    color: #7F909F;
    font-size: .64rem;
    font-weight: 700;
    letter-spacing: .075em;
    text-transform: uppercase;
}

.section-kicker {
    color: var(--atlas-accent);
    font-size: .64rem;
    font-weight: 800;
    letter-spacing: .18em;
    text-transform: uppercase;
    margin-top: 30px;
}

.section-title {
    margin-top: 5px;
    color: var(--atlas-text);
    font-size: clamp(1.4rem, 2vw, 1.82rem);
    font-weight: 790;
    letter-spacing: -.025em;
}

.section-copy {
    margin-top: 5px;
    margin-bottom: 18px;
    color: var(--atlas-muted);
    font-size: .86rem;
    line-height: 1.65;
    max-width: 820px;
}

h1, h2, h3, h4 {
    color: var(--atlas-text) !important;
    letter-spacing: -.025em !important;
}

h2 { margin-top: 1.6rem !important; }

[data-testid="stMetric"] {
    background: linear-gradient(180deg, rgba(255,255,255,.016), rgba(255,255,255,.006));
    border: 1px solid var(--atlas-border) !important;
    border-radius: 10px !important;
    padding: 15px 16px 14px !important;
    min-height: 102px;
    display: flex;
    flex-direction: column;
    justify-content: center;
}
[data-testid="stMetricLabel"] { color: #8293A3 !important; font-size: .71rem !important; letter-spacing: .045em; min-height: 20px; }
[data-testid="stMetricValue"] { color: var(--atlas-text) !important; font-weight: 780 !important; letter-spacing: -.035em; line-height: 1.12; }
[data-testid="stMetricDelta"] { font-size: .78rem !important; }

[data-testid="stVerticalBlockBorderWrapper"] {
    border-color: var(--atlas-border) !important;
    border-radius: 10px !important;
    background: var(--atlas-surface) !important;
}

[data-testid="stExpander"] {
    border: 1px solid #192733 !important;
    border-radius: 9px !important;
    background: #0A1016 !important;
}
[data-testid="stExpander"] summary { color: var(--atlas-text) !important; font-weight: 650; }

[data-testid="stTabs"] [role="tablist"] {
    gap: 13px;
    border-bottom: 1px solid var(--atlas-border-soft);
    padding: 1px 0 0;
}
[data-testid="stTabs"] button[role="tab"] {
    background: transparent;
    border-radius: 0;
    color: #8696A5 !important;
    font-size: .76rem;
    font-weight: 680;
    letter-spacing: .025em;
    padding: 11px 3px 12px;
    transition: color .15s ease;
}
[data-testid="stTabs"] button[role="tab"]:hover { color: #C9D2DA !important; }
[data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
    color: var(--atlas-accent) !important;
    background: transparent;
}
[data-testid="stTabs"] button[role="tab"][aria-selected="true"] p { color: var(--atlas-accent) !important; }
[data-testid="stTabs"] [data-baseweb="tab-highlight"] { background-color: var(--atlas-accent) !important; height: 2px; }

.stButton > button, .stDownloadButton > button {
    border: 1px solid #2A3947 !important;
    background: #101820 !important;
    color: var(--atlas-text) !important;
    border-radius: 7px !important;
    font-weight: 680 !important;
    font-size: .78rem !important;
    transition: border-color .15s ease, transform .15s ease, background .15s ease;
}
.stButton > button:hover, .stDownloadButton > button:hover {
    border-color: #456075 !important;
    background: #14202A !important;
    transform: translateY(-1px);
}
.stButton > button[kind="primary"] { background: #173B3A !important; border-color: #28635F !important; }

[data-baseweb="input"] > div, [data-baseweb="select"] > div,
[data-testid="stNumberInput"] input, [data-testid="stTextInput"] input {
    background: #0B1117 !important;
    border-color: var(--atlas-border) !important;
    color: var(--atlas-text) !important;
}
[data-baseweb="popover"], [data-baseweb="menu"] { background: var(--atlas-surface-2) !important; }

[data-testid="stSlider"] [role="slider"] { background: var(--atlas-accent) !important; }
[data-testid="stCheckbox"] svg, [data-testid="stToggle"] svg { color: var(--atlas-accent) !important; }

[data-testid="stAlert"] {
    border-radius: 8px !important;
    border: 1px solid var(--atlas-border) !important;
    background: #0E151C !important;
    color: var(--atlas-text) !important;
}

[data-testid="stDataFrame"] {
    border: 1px solid var(--atlas-border) !important;
    border-radius: 8px;
    overflow: hidden;
}

hr { border-color: var(--atlas-border-soft) !important; }

.atlas-card-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 10px;
    align-items: stretch;
}
.mobile-detail-card, .compare-card, .pulse-region-card, .home-top10-card,
.atlas-radar-panel, .sector-spotlight-card, .sector-heatmap-mobile-card,
.atlas-guide-card, .data-health-item, .saved-filter-card {
    border: 1px solid var(--atlas-border) !important;
    border-radius: 9px !important;
    background: var(--atlas-surface) !important;
}
.mobile-detail-card { padding: 14px; margin-bottom: 10px; height: 100%; }
.mobile-detail-head, .compare-card-head, .pulse-region-head, .home-top10-head,
.sector-heatmap-mobile-head { display:flex; align-items:flex-start; justify-content:space-between; gap:10px; }
.mobile-detail-company, .compare-card-company, .pulse-region-name, .home-top10-company,
.sector-heatmap-mobile-name, .sector-spotlight-value, .atlas-radar-company, .saved-filter-name {
    color: var(--atlas-text); font-weight: 760;
}
.mobile-detail-meta, .compare-card-meta, .pulse-region-count, .home-top10-country,
.sector-spotlight-label, .sector-spotlight-meta, .atlas-radar-meta, .saved-filter-summary {
    color: var(--atlas-muted);
}
.mobile-detail-score, .compare-card-score, .home-top10-score, .atlas-radar-value { color: var(--atlas-accent); font-weight: 760; white-space: nowrap; }
.mobile-detail-grid, .compare-card-grid, .home-top10-grid, .sector-heatmap-mobile-grid {
    display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:8px; margin-top:11px;
}
.mobile-detail-item, .compare-card-item, .home-top10-item, .sector-heatmap-mobile-tile {
    padding: 8px 9px; border-radius: 6px; background: #0A1016; border: 1px solid var(--atlas-border-soft);
}
.mobile-detail-label, .compare-card-label, .home-top10-label, .sector-heatmap-mobile-label { color: var(--atlas-muted-2); font-size:.70rem; }
.mobile-detail-value, .compare-card-value, .home-top10-value, .sector-heatmap-mobile-value { color:var(--atlas-text); margin-top:2px; font-size:.90rem; font-weight:700; }
.mobile-detail-judge, .compare-card-judge, .home-top10-judge, .mobile-judge {
    display:inline-block; margin-top:10px; padding:4px 7px; border-radius:4px;
    border:1px solid var(--atlas-border); color:#BBC6D0; font-size:.70rem; font-weight:750; letter-spacing:.05em;
}
.signal-positive { color: var(--atlas-positive) !important; border-color: rgba(74,222,128,.30) !important; background: rgba(74,222,128,.055); }
.signal-neutral { color: var(--atlas-warning) !important; border-color: rgba(245,199,107,.28) !important; background: rgba(245,199,107,.045); }
.signal-negative { color: var(--atlas-negative) !important; border-color: rgba(251,113,133,.28) !important; background: rgba(251,113,133,.045); }

.pulse-region-card { padding:13px 14px; margin-bottom:10px; }
.pulse-region-name { font-size:.95rem; }
.pulse-region-count { font-size:.74rem; }
.pulse-region-score { margin-top:9px; font-size:.88rem; font-weight:700; }
.pulse-region-stats { margin-top:7px; color:var(--atlas-muted); font-size:.82rem; line-height:1.55; }

.compare-card { padding:14px; margin-bottom:10px; }
.compare-card-company { font-size:1.02rem; }
.compare-card-meta { font-size:.78rem; margin-top:2px; }
.compare-card-score { font-size:.95rem; }

.sector-spotlight-grid, .atlas-radar-grid {
    display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:10px; margin:10px 0 12px;
}
.sector-spotlight-card { padding:13px 14px; min-width:0; }
.sector-spotlight-label { font-size:.69rem; font-weight:700; letter-spacing:.045em; text-transform:uppercase; }
.sector-spotlight-value { margin-top:5px; font-size:.98rem; overflow-wrap:anywhere; }
.sector-spotlight-meta { margin-top:4px; font-size:.75rem; line-height:1.45; }

.atlas-radar-panel { padding:14px; min-width:0; }
.atlas-radar-title { color:var(--atlas-text); font-size:.92rem; font-weight:760; }
.atlas-radar-sub { margin-top:3px; color:var(--atlas-muted); font-size:.73rem; line-height:1.45; }
.atlas-radar-item { display:flex; align-items:flex-start; justify-content:space-between; gap:10px; padding:10px 0; border-bottom:1px solid var(--atlas-border-soft); }
.atlas-radar-item:last-child { border-bottom:0; padding-bottom:0; }
.atlas-radar-company { font-size:.86rem; }
.atlas-radar-meta { margin-top:2px; font-size:.70rem; line-height:1.45; }
.atlas-radar-value { font-size:.87rem; }

.sector-heatmap-desktop { display:grid; grid-template-columns:minmax(190px,1.3fr) repeat(4,minmax(105px,1fr)); gap:6px; margin:14px 0 8px; }
.sector-heatmap-header { padding:8px 10px; color:var(--atlas-muted); font-size:.69rem; font-weight:750; text-transform:uppercase; letter-spacing:.06em; }
.sector-heatmap-sector { border:1px solid var(--atlas-border); border-radius:7px; background:var(--atlas-surface); padding:10px 11px; min-width:0; }
.sector-heatmap-sector-name { color:var(--atlas-text); font-size:.84rem; font-weight:760; overflow-wrap:anywhere; }
.sector-heatmap-sector-meta { margin-top:3px; color:var(--atlas-muted); font-size:.68rem; line-height:1.4; }
.sector-heatmap-cell { border:1px solid var(--atlas-border-soft); border-radius:7px; min-height:58px; padding:9px 10px; display:flex; align-items:center; justify-content:center; text-align:center; }
.sector-heatmap-cell-value { color:var(--atlas-text); font-size:.88rem; font-weight:760; }
.sector-heatmap-mobile { display:none; }
.sector-heatmap-mobile-card { padding:13px; margin-bottom:10px; }

.home-top10-mobile, .mobile-list-wrap, .st-key-compare_mobile, .st-key-pulse_region_mobile,
.st-key-favorite_mobile, .st-key-portfolio_mobile, .st-key-budget_mobile { display:none; }
.home-top10-card { padding:13px 14px; margin-bottom:10px; }
.home-top10-rank, .mobile-rank { color:var(--atlas-muted-2); font-size:.70rem; font-weight:700; letter-spacing:.06em; }
.home-top10-company, .mobile-company { margin-top:2px; font-size:1rem; }
.home-top10-country, .mobile-meta { margin-top:2px; font-size:.74rem; }
.home-top10-score, .mobile-score { font-size:.90rem; }

.atlas-guide-grid, .data-health-grid { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:8px; margin:8px 0 4px; }
.atlas-guide-card { padding:11px 12px; }
.atlas-guide-step, .data-health-label { color:var(--atlas-muted-2); font-size:.65rem; font-weight:750; letter-spacing:.08em; text-transform:uppercase; }
.atlas-guide-title { margin-top:4px; color:var(--atlas-text); font-weight:760; font-size:.86rem; }
.atlas-guide-text { margin-top:4px; color:var(--atlas-muted); font-size:.73rem; line-height:1.45; }
.data-health-item { padding:9px 10px; }
.data-health-value { margin-top:3px; color:var(--atlas-text); font-size:.86rem; font-weight:740; }
.saved-filter-card { padding:10px 12px; margin-top:8px; }
.saved-filter-name { font-size:.86rem; }
.saved-filter-summary { margin-top:3px; font-size:.72rem; line-height:1.45; }

.mobile-stock-card { border:1px solid var(--atlas-border); border-radius:9px; background:var(--atlas-surface); padding:14px; margin-bottom:10px; }
.mobile-stats { color:var(--atlas-muted); font-size:.82rem; margin-top:5px; line-height:1.55; }
.mobile-list-title { color:var(--atlas-text); font-size:1.1rem; font-weight:760; margin:18px 0 12px; }


/* ---- V3.2.1 final polish ---- */
.atlas-top-controls {
    display:flex;
    align-items:center;
    justify-content:space-between;
    gap:12px;
    margin: 0 0 14px 0;
}
.atlas-top-controls .atlas-version-row { margin:0; }
.st-key-market_refresh_wrap { width: fit-content; }
.st-key-market_refresh_wrap .stButton > button {
    min-height: 34px !important;
    padding: 0 12px !important;
    color: #AEBBC6 !important;
    background: #0A1117 !important;
    border-color: #1B2B37 !important;
    font-size: .72rem !important;
}
.st-key-market_refresh_wrap .stButton > button:hover {
    color: var(--atlas-text) !important;
    border-color: #315161 !important;
    background: #0D171E !important;
}
[data-testid="stHorizontalBlock"] { align-items: stretch; }
[data-testid="stMetric"] > div { width:100%; }
[data-testid="stCaptionContainer"] { color: var(--atlas-muted) !important; }
.stMarkdown p { line-height: 1.62; }

@media (max-width: 1100px) {
    .atlas-radar-grid, .sector-spotlight-grid, .atlas-guide-grid, .data-health-grid { grid-template-columns:1fr; }
    .sector-heatmap-desktop { display:none; }
    .sector-heatmap-mobile { display:block; }
    .st-key-home_top10_table { display:none !important; }
    .home-top10-mobile, .mobile-list-wrap { display:block; }
    .st-key-world50_table, .st-key-compare_table, .st-key-pulse_region_table,
    .st-key-favorite_table, .st-key-portfolio_table, .st-key-budget_table { display:none !important; }
    .st-key-compare_mobile, .st-key-pulse_region_mobile, .st-key-favorite_mobile,
    .st-key-portfolio_mobile, .st-key-budget_mobile { display:block !important; }
    [data-testid="stTabs"] [role="tablist"] { overflow-x:auto; flex-wrap:nowrap; scrollbar-width:none; }
    [data-testid="stTabs"] [role="tablist"]::-webkit-scrollbar { display:none; }
    [data-testid="stTabs"] button[role="tab"] { flex:0 0 auto; white-space:nowrap; }
    .block-container { padding-top:.55rem; padding-left:.8rem; padding-right:.8rem; padding-bottom:2.5rem; }
    .atlas-hero { padding-top:10px; padding-bottom:18px; }
    .atlas-title { font-size:2.35rem; }
    .atlas-sub { font-size:.64rem; letter-spacing:.17em; }
    .atlas-tagline { font-size:.86rem; line-height:1.65; max-width:100%; }
    .atlas-top-controls { align-items:flex-start; flex-direction:column; gap:8px; }
    [data-testid="stTabs"] [role="tablist"] { gap:14px; }
    [data-testid="stTabs"] button[role="tab"] { padding-left:1px; padding-right:1px; }
    [data-testid="stMetric"] { min-height:82px; padding:11px !important; }
    [data-testid="stMetricValue"] { font-size:1.25rem !important; }
    [data-testid="stMetricLabel"] { font-size:.69rem !important; }
    [data-testid="stHorizontalBlock"] { gap:.45rem; }
    button { min-height:42px; }
}

#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
</style>
""",
    unsafe_allow_html=True,
)


# ------------------------------
# ヘルパー
# ------------------------------
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


def _session_return(close, sessions):
    """約1日/1週など、取引セッション数ベースの騰落率。"""
    if close is None or len(close) <= sessions:
        return float("nan")
    cur = float(close.iloc[-1])
    base = float(close.iloc[-(sessions + 1)])
    if base == 0:
        return float("nan")
    return cur / base - 1


def _calendar_return(close, months=0, years=0):
    """1/3/6か月・1年をカレンダー日付ベースで計算。市場ごとの休日差にも強い。"""
    if close is None or close.empty:
        return float("nan")

    end_date = close.index[-1]
    target_date = end_date - pd.DateOffset(months=months, years=years)
    past = close.loc[close.index <= target_date]

    if past.empty:
        return float("nan")

    cur = float(close.iloc[-1])
    base = float(past.iloc[-1])
    if base == 0:
        return float("nan")
    return cur / base - 1


def _pct_text(value, decimals=2, show_plus=True):
    if pd.isna(value):
        return "-"
    pct = float(value) * 100
    if show_plus:
        return f"{pct:+.{decimals}f}%"
    return f"{pct:.{decimals}f}%"


def _pct_number_text(value, decimals=2):
    """すでに%単位へ変換済みの数値を表示用文字列にする。"""
    if pd.isna(value):
        return "-"
    return f"{float(value):+.{decimals}f}%"


def _build_attention_reasons(
    score,
    one_month,
    three_month,
    six_month,
    one_year,
    has_news=False,
):
    """現在の価格トレンドを初心者向けに短く整理する。"""
    reasons = []
    if score >= 80:
        reasons.append("複数のトレンド指標が強く、現在はAtlas50の中でも注目度が高い状態です。")
    elif score >= 65:
        reasons.append("複数のトレンド指標が比較的良好で、Atlas Scoreは平均より高めです。")

    trend_values = [one_month, three_month, six_month, one_year]
    if all(v is not None and v > 0 for v in trend_values):
        reasons.append("1か月から1年まで騰落率がすべてプラスで、複数の期間で上向きの流れが見られます。")
    elif one_month is not None and three_month is not None and six_month is not None and one_month > 0 and three_month > 0 and six_month > 0:
        reasons.append("1か月・3か月・6か月がすべてプラスで、中期的な上向きの流れが続いています。")
    elif one_month is not None and three_month is not None and one_month > 0 and three_month < 0:
        reasons.append("直近1か月は反発していますが、3か月ではまだ回復途中の動きです。")
    elif one_month is not None and six_month is not None and one_year is not None and one_month < 0 and six_month > 0 and one_year > 0:
        reasons.append("中長期ではプラスですが、直近1か月は調整局面に入っています。")
    elif one_month is not None and three_month is not None and one_month < 0 and three_month < 0:
        reasons.append("1か月・3か月ともにマイナスで、短期から中期の勢いは弱めです。")

    if one_month is not None and abs(one_month) >= 15:
        reasons.append("直近1か月の値動きが大きいため、短期的な価格変動には注意が必要です。")
    if has_news:
        reasons.append("関連ニュースも出ているため、値動きの背景とあわせて確認できます。")
    return reasons[:5]



SCORE_PART_MAX = {
    "1週モメンタム": 12,
    "1か月モメンタム": 15,
    "3か月モメンタム": 15,
    "移動平均": 28,
    "RSI": 10,
    "出来高": 10,
    "52週高値": 10,
}


def _build_ranking_explanation(row, full_df):
    """Atlasデータだけを使って現在順位の背景を初心者向けに説明する。"""
    rank = int(row["順位"])
    score = float(row["Atlas Score"])
    parts = row.get("Score内訳", {}) or {}
    part_messages = {
        "1週モメンタム": "直近1週間の勢いがScoreを押し上げています。",
        "1か月モメンタム": "1か月の値動きが現在のScoreに大きく寄与しています。",
        "3か月モメンタム": "3か月のトレンドが現在の順位を支えています。",
        "移動平均": "移動平均線の並びが良く、中期トレンド面の得点が高めです。",
        "RSI": "RSIがAtlas上で比較的バランスの良い範囲にあります。",
        "出来高": "最近の出来高が勢いの指標を支えています。",
        "52週高値": "52週高値に比較的近く、価格位置の強さがScoreに反映されています。",
    }
    normalized_parts=[]
    for name,max_value in SCORE_PART_MAX.items():
        value=float(parts.get(name,0) or 0)
        ratio=value/max_value if max_value else 0
        normalized_parts.append((ratio,value,name))
    normalized_parts.sort(reverse=True)
    strengths=[]
    for ratio,value,name in normalized_parts[:3]:
        if value<=0: continue
        strengths.append(part_messages[name])
        if len(strengths)>=2: break
    if not strengths:
        strengths.append("特定の1項目ではなく、複数のAtlas Score構成要素の合計で現在の順位になっています。")

    def pct_value(col):
        value=row.get(col)
        return None if pd.isna(value) else float(value)*100
    one_month=pct_value("1か月"); three_month=pct_value("3か月"); six_month=pct_value("6か月"); one_year=pct_value("1年")
    vals=[one_month,three_month,six_month,one_year]
    if all(v is not None and v>0 for v in vals):
        trend="1か月・3か月・6か月・1年がすべてプラスで、複数期間の方向がそろっています。"
    elif all(v is not None and v<0 for v in vals):
        trend="1か月・3か月・6か月・1年がすべてマイナスで、複数期間に弱さが見られます。"
    elif one_month is not None and three_month is not None and six_month is not None and one_month>0 and three_month>0 and six_month>0:
        trend="1か月・3か月・6か月がすべてプラスで、中期的に上向きの流れです。"
    elif one_month is not None and six_month is not None and one_year is not None and one_month<0 and six_month>0 and one_year>0:
        trend="中長期はプラスですが、直近1か月は調整しています。"
    elif one_month is not None and three_month is not None and one_month>0 and three_month<0:
        trend="直近1か月は反発していますが、3か月ではまだマイナスです。"
    elif one_month is not None and three_month is not None and one_month<0 and three_month<0:
        trend="1か月・3か月ともにマイナスで、足元の勢いは弱めです。"
    else:
        trend="期間によって強弱が分かれており、短期と中長期の方向はまだそろっていません。"

    position_bits=[f"Atlas Score {score:.1f}で、50銘柄中 #{rank} です。"]
    if rank>1 and len(full_df)>=rank-1:
        upper=float(full_df.iloc[rank-2]["Atlas Score"]); position_bits.append(f"1つ上とは {upper-score:.1f}pt差です。")
    if rank<len(full_df):
        lower=float(full_df.iloc[rank]["Atlas Score"]); position_bits.append(f"1つ下には {score-lower:.1f}ptリードしています。")
    checks=[]
    if one_month is not None and abs(one_month)>=15:
        checks.append("1か月の値動きが大きく、短期的な変動が強まっています。")
    rsi=row.get("RSI")
    if pd.notna(rsi):
        rsi=float(rsi)
        if rsi>=75: checks.append("RSIが高めのため、短期的な過熱感が出ていないか確認したい状態です。")
        elif rsi<=35: checks.append("RSIが低めで、弱い勢いが続いている可能性があります。")
    volume_ratio=row.get("出来高倍率")
    if pd.notna(volume_ratio) and float(volume_ratio)<0.8:
        checks.append("出来高が20日平均を下回っており、最近の値動きへの参加はやや少なめです。")
    high_gap=row.get("高値乖離")
    if pd.notna(high_gap) and float(high_gap)<-0.15:
        checks.append("52週高値から距離があり、価格位置はまだ弱めです。")
    if not checks:
        checks.append("Atlasの入力値では大きな警戒サインは目立ちませんが、高順位でも将来の上昇を保証するものではありません。")
    return {"rank":rank,"score":score,"position":" ".join(position_bits),"strengths":strengths,"trend":trend,"checks":checks[:2]}



def _build_atlas_pulse(full_df):
    """Atlas50全体の値動きの広がりを、予測ではなく現在のスナップショットとして整理する。"""
    data = full_df.copy()
    total = len(data)

    def _positive_count(col):
        values = pd.to_numeric(data[col], errors="coerce")
        return int((values > 0).sum())

    one_month_positive = _positive_count("1か月")
    three_month_positive = _positive_count("3か月")
    above_sma20 = int((pd.to_numeric(data["20日線比"], errors="coerce") > 0).sum())

    one_month_series = pd.to_numeric(data["1か月"], errors="coerce")
    three_month_series = pd.to_numeric(data["3か月"], errors="coerce")
    avg_one_month = float(one_month_series.mean() * 100) if one_month_series.notna().any() else 0.0
    avg_three_month = float(three_month_series.mean() * 100) if three_month_series.notna().any() else 0.0

    breadth_1m = one_month_positive / total if total else 0
    breadth_sma20 = above_sma20 / total if total else 0
    breadth = (breadth_1m + breadth_sma20) / 2

    if breadth >= 0.65 and avg_one_month > 0:
        label = "全体に上向き"
        icon = ""
        summary = "1か月プラスの銘柄と20日線より上の銘柄が多く、Atlas50全体に強さが広がっています。"
    elif breadth <= 0.35 and avg_one_month < 0:
        label = "全体に弱め"
        icon = ""
        summary = "1か月プラスの銘柄や20日線より上の銘柄が少なく、Atlas50全体では弱さが目立ちます。"
    else:
        label = "強弱が混在"
        icon = ""
        summary = "上向きの銘柄と弱い銘柄が混在しており、Atlas50全体では方向感がそろっていません。"

    region = (
        data.groupby("地域", dropna=False)
        .agg(
            銘柄数=("Ticker", "count"),
            平均Score=("Atlas Score", "mean"),
            一か月平均=("1か月", "mean"),
            三か月平均=("3か月", "mean"),
        )
        .reset_index()
    )
    region["平均Score"] = region["平均Score"].round(1)
    region["1か月平均"] = (region.pop("一か月平均") * 100).round(2)
    region["3か月平均"] = (region.pop("三か月平均") * 100).round(2)
    region = region.sort_values(["平均Score", "銘柄数"], ascending=[False, False]).reset_index(drop=True)

    return {
        "total": total,
        "one_month_positive": one_month_positive,
        "three_month_positive": three_month_positive,
        "above_sma20": above_sma20,
        "avg_one_month": avg_one_month,
        "avg_three_month": avg_three_month,
        "label": label,
        "icon": icon,
        "summary": summary,
        "region": region,
    }



def _build_atlas_radar(full_df):
    """Atlas50内で直近の変化が目立つ銘柄を、推奨ではなく観察用に抽出する。"""
    data = full_df.copy()

    for col in ["1か月", "3か月", "出来高倍率", "Atlas Score"]:
        data[col] = pd.to_numeric(data[col], errors="coerce")

    up = (
        data.dropna(subset=["1か月"])
        .sort_values("1か月", ascending=False)
        .head(3)
        .copy()
    )
    down = (
        data.dropna(subset=["1か月"])
        .sort_values("1か月", ascending=True)
        .head(3)
        .copy()
    )
    volume = (
        data.dropna(subset=["出来高倍率"])
        .sort_values("出来高倍率", ascending=False)
        .head(3)
        .copy()
    )

    return {
        "up": up,
        "down": down,
        "volume": volume,
    }


def _build_sector_heatmap(full_df):
    """Atlas50内の業種を大分類し、複数期間の平均値をヒートマップ用に整理する。"""
    data = full_df.copy()
    data["業種グループ"] = data["業種"].map(SECTOR_GROUPS).fillna(data["業種"])

    for col in ["1か月", "3か月", "6か月", "Atlas Score"]:
        data[col] = pd.to_numeric(data[col], errors="coerce")

    data["1か月プラス"] = (data["1か月"] > 0).astype(float)

    summary = (
        data.groupby("業種グループ", dropna=False)
        .agg(
            銘柄数=("Ticker", "count"),
            平均Score=("Atlas Score", "mean"),
            一か月平均=("1か月", "mean"),
            三か月平均=("3か月", "mean"),
            六か月平均=("6か月", "mean"),
            一か月プラス率=("1か月プラス", "mean"),
        )
        .reset_index()
    )

    summary["平均Score"] = summary["平均Score"].round(1)
    summary["1か月平均"] = (summary.pop("一か月平均") * 100).round(2)
    summary["3か月平均"] = (summary.pop("三か月平均") * 100).round(2)
    summary["6か月平均"] = (summary.pop("六か月平均") * 100).round(2)
    summary["1か月プラス率"] = (summary.pop("一か月プラス率") * 100).round(0)
    summary = summary.sort_values(["平均Score", "銘柄数"], ascending=[False, False]).reset_index(drop=True)

    metric_settings = [
        ("1か月", "1か月平均", 15.0),
        ("3か月", "3か月平均", 30.0),
        ("6か月", "6か月平均", 50.0),
        ("Atlas Score", "平均Score", None),
    ]

    heat_rows = []
    for _, sector_row in summary.iterrows():
        for metric_name, source_col, scale_base in metric_settings:
            value = float(sector_row[source_col]) if pd.notna(sector_row[source_col]) else 0.0
            if metric_name == "Atlas Score":
                heat = max(-1.0, min(1.0, (value - 50.0) / 30.0))
                display = f"{value:.1f}"
            else:
                heat = max(-1.0, min(1.0, value / scale_base))
                display = f"{value:+.1f}%"

            heat_rows.append(
                {
                    "業種グループ": sector_row["業種グループ"],
                    "指標": metric_name,
                    "値": value,
                    "表示": display,
                    "熱度": heat,
                    "文字色": "#ffffff" if abs(heat) >= 0.58 else "#1f2937",
                    "銘柄数": int(sector_row["銘柄数"]),
                    "1か月プラス率": float(sector_row["1か月プラス率"]),
                }
            )

    return summary, pd.DataFrame(heat_rows)


def _sector_heat_cell_style(heat_value):
    """ヒート値(-1〜1)を、明暗どちらのテーマでも読める淡い背景色へ変換する。"""
    try:
        heat = max(-1.0, min(1.0, float(heat_value)))
    except (TypeError, ValueError):
        heat = 0.0

    strength = abs(heat)
    if heat > 0.04:
        alpha = 0.08 + (0.26 * strength)
        border_alpha = min(0.44, alpha + 0.10)
        return (
            f"background: rgba(16, 185, 129, {alpha:.3f});"
            f"border-color: rgba(16, 185, 129, {border_alpha:.3f});"
        )
    if heat < -0.04:
        alpha = 0.08 + (0.26 * strength)
        border_alpha = min(0.44, alpha + 0.10)
        return (
            f"background: rgba(239, 68, 68, {alpha:.3f});"
            f"border-color: rgba(239, 68, 68, {border_alpha:.3f});"
        )

    return "background: rgba(120, 120, 120, 0.07);"


def _render_sector_heatmap_html(summary, heat_frame):
    """Altairに依存せず、PC/スマホ両方で確実に表示できるHTMLヒートマップを返す。"""
    if summary.empty or heat_frame.empty:
        return ""

    metric_order = ["1か月", "3か月", "6か月", "Atlas Score"]
    metric_label = {"1か月": "1か月", "3か月": "3か月", "6か月": "6か月", "Atlas Score": "ATLAS SCORE"}
    heat_lookup = {}
    for _, heat_row in heat_frame.iterrows():
        heat_lookup[(str(heat_row["業種グループ"]), str(heat_row["指標"]))] = heat_row

    desktop_parts = ['<div class="sector-heatmap-desktop">']
    desktop_parts.append('<div class="sector-heatmap-header">業種グループ</div>')
    for metric in metric_order:
        desktop_parts.append(f'<div class="sector-heatmap-header">{html.escape(metric_label[metric])}</div>')

    mobile_parts = ['<div class="sector-heatmap-mobile">']

    for _, summary_row in summary.iterrows():
        sector_name = str(summary_row["業種グループ"])
        sector_escaped = html.escape(_sector_group_en(sector_name))
        count = int(summary_row["銘柄数"])
        breadth = float(summary_row["1か月プラス率"])

        desktop_parts.append(
            '<div class="sector-heatmap-sector">'
            f'<div class="sector-heatmap-sector-name">{sector_escaped}</div>'
            f'<div class="sector-heatmap-sector-meta">{count}銘柄 | 1か月プラス {breadth:.0f}%</div>'
            '</div>'
        )

        mobile_parts.append(
            '<div class="sector-heatmap-mobile-card">'
            '<div class="sector-heatmap-mobile-head">'
            f'<div class="sector-heatmap-mobile-name">{sector_escaped}</div>'
            f'<div class="sector-heatmap-mobile-meta">{count}銘柄</div>'
            '</div>'
            f'<div class="sector-heatmap-sector-meta">1か月プラス {breadth:.0f}%</div>'
            '<div class="sector-heatmap-mobile-grid">'
        )

        for metric in metric_order:
            row = heat_lookup.get((sector_name, metric))
            if row is None:
                display = "-"
                style = _sector_heat_cell_style(0)
            else:
                display = html.escape(str(row["表示"]))
                style = _sector_heat_cell_style(row["熱度"])

            desktop_parts.append(
                f'<div class="sector-heatmap-cell" style="{style}">'
                f'<div class="sector-heatmap-cell-value">{display}</div>'
                '</div>'
            )
            mobile_parts.append(
                f'<div class="sector-heatmap-mobile-tile" style="{style}">'
                f'<div class="sector-heatmap-mobile-label">{html.escape(metric_label[metric])}</div>'
                f'<div class="sector-heatmap-mobile-value">{display}</div>'
                '</div>'
            )

        mobile_parts.append('</div></div>')

    desktop_parts.append('</div>')
    mobile_parts.append('</div>')
    return "".join(desktop_parts + mobile_parts)


def _safe_float(value, default=None):
    """NaN/文字列を含む値を安全にfloatへ変換する。"""
    try:
        numeric = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
        if pd.isna(numeric):
            return default
        return float(numeric)
    except Exception:
        return default


def _build_data_health(full_df, fx_rates, error_list):
    """取得状況をUI表示用に整理する。投資判断ではなくデータ品質確認用。"""
    loaded = len(full_df)
    expected = len(COMPANIES)
    latest = str(full_df["最終日"].max()) if not full_df.empty and "最終日" in full_df else "-"
    used_currencies = sorted(set(full_df["通貨"].dropna().astype(str))) if not full_df.empty else []
    missing_fx = [c for c in used_currencies if c != "JPY" and not fx_rates.get(c)]
    return {
        "loaded": loaded,
        "expected": expected,
        "latest": latest,
        "missing_fx": missing_fx,
        "errors": list(error_list or []),
    }


def _watch_config_from_state():
    config = {}
    for key, default in WATCH_DEFAULTS.items():
        value = st.session_state.get(key, default)
        if isinstance(default, bool):
            config[key] = bool(value)
        elif isinstance(default, float):
            config[key] = float(value)
        elif isinstance(default, int):
            config[key] = int(value)
        else:
            config[key] = str(value)
    return config


def _apply_watch_config(config):
    """保存条件をウィジェット描画前にsession_stateへ安全に反映する。"""
    if not isinstance(config, dict):
        return

    numeric_ranges = {
        "watch_score": (0.0, 100.0),
        "watch_1m": (-100.0, 100.0),
        "watch_3m": (-100.0, 200.0),
        "watch_volume": (0.0, 10.0),
    }

    for key, default in WATCH_DEFAULTS.items():
        if key not in config:
            continue
        value = config[key]
        try:
            if isinstance(default, bool):
                st.session_state[key] = bool(value)
            elif isinstance(default, float):
                number = float(value)
                if key in numeric_ranges:
                    low, high = numeric_ranges[key]
                    number = max(low, min(high, number))
                st.session_state[key] = number
            elif isinstance(default, int):
                number = int(value)
                if key == "watch_limit" and number not in {12, 24, 50}:
                    number = 12
                st.session_state[key] = number
            else:
                text = str(value)
                if key == "watch_sort" and text not in WATCH_SORT_OPTIONS:
                    text = WATCH_DEFAULTS[key]
                st.session_state[key] = text
        except Exception:
            st.session_state[key] = default


def _watch_config_summary(config):
    if not isinstance(config, dict):
        return "この条件を読み込めません"
    bits = [f"Score ≥ {float(config.get('watch_score', 0)):.0f}"]
    one_m = float(config.get("watch_1m", -100))
    three_m = float(config.get("watch_3m", -100))
    volume = float(config.get("watch_volume", 0))
    if one_m > -100:
        bits.append(f"1か月 ≥ {one_m:+.0f}%")
    if three_m > -100:
        bits.append(f"3か月 ≥ {three_m:+.0f}%")
    if volume > 0:
        bits.append(f"出来高 ≥ {volume:.1f}x")
    region = str(config.get("watch_region", "すべて"))
    sector = str(config.get("watch_sector_group", "すべて"))
    if region != "すべて":
        bits.append(_region_en(region))
    if sector != "すべて":
        bits.append(_sector_group_en(sector))
    if bool(config.get("watch_sma20", False)):
        bits.append("20日線より上")
    if bool(config.get("watch_sma60", False)):
        bits.append("60日線より上")
    return " | ".join(bits)


def _atlas_setup_payload():
    """お気に入り・保有株・保存条件を1つのJSONとして持ち運べる形にする。"""
    saved_filters = st.session_state.get("saved_watch_filters", {})
    clean_saved = {
        str(name): dict(config)
        for name, config in saved_filters.items()
        if isinstance(config, dict)
    }

    portfolio_records = []
    portfolio_df = st.session_state.get("portfolio")
    if isinstance(portfolio_df, pd.DataFrame):
        for _, row in portfolio_df.iterrows():
            ticker_value = row.get("Ticker")
            if pd.isna(ticker_value):
                continue
            ticker = str(ticker_value).strip()
            if not ticker or ticker not in COMPANY_META:
                continue
            qty = _safe_float(row.get("株数"), None)
            avg = _safe_float(row.get("平均取得単価"), None)
            portfolio_records.append(
                {
                    "Ticker": ticker,
                    "株数": qty,
                    "平均取得単価": avg,
                }
            )

    return {
        "atlas_version": APP_VERSION,
        "favorites": sorted(str(x) for x in st.session_state.get("favorites", set())),
        "portfolio": portfolio_records,
        "saved_watch_filters": clean_saved,
        "current_watch_filter": _watch_config_from_state(),
    }


def _apply_atlas_setup_payload(payload):
    """アップロードされたAtlas設定を安全に反映する。"""
    if not isinstance(payload, dict):
        raise ValueError("JSON形式が正しくありません")

    valid_tickers = {row[0] for row in COMPANIES}
    favorites = payload.get("favorites", [])
    if isinstance(favorites, list):
        st.session_state.favorites = {str(t) for t in favorites if str(t) in valid_tickers}

    portfolio = payload.get("portfolio", [])
    if isinstance(portfolio, list):
        portfolio_rows = []
        for item in portfolio[:100]:
            if not isinstance(item, dict):
                continue
            ticker = str(item.get("Ticker") or "").strip()
            if ticker not in valid_tickers:
                continue
            portfolio_rows.append(
                {
                    "Ticker": ticker,
                    "株数": _safe_float(item.get("株数"), None),
                    "平均取得単価": _safe_float(item.get("平均取得単価"), None),
                }
            )
        st.session_state.portfolio = pd.DataFrame(
            portfolio_rows,
            columns=["Ticker", "株数", "平均取得単価"],
        )
        st.session_state.portfolio_editor_version = int(st.session_state.get("portfolio_editor_version", 0)) + 1

    st.session_state.favorites_editor_version = int(st.session_state.get("favorites_editor_version", 0)) + 1

    saved = payload.get("saved_watch_filters", {})
    if isinstance(saved, dict):
        cleaned = {}
        for name, config in list(saved.items())[:30]:
            if not isinstance(config, dict):
                continue
            cleaned[str(name)[:40]] = {
                key: config.get(key, default)
                for key, default in WATCH_DEFAULTS.items()
            }
        st.session_state.saved_watch_filters = cleaned

    current = payload.get("current_watch_filter")
    if isinstance(current, dict):
        _apply_watch_config(current)


def _settings_json_bytes():
    return json.dumps(
        _atlas_setup_payload(),
        ensure_ascii=False,
        indent=2,
    ).encode("utf-8")


def score_parts(cur, r1w, r1m, r3m, sma5, sma20, sma60, rsi, vr, dist_high):
    # 過去バージョンとの比較可能性を保つため、Score式自体は変更しない。
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

    total = round(
        max(
            0,
            min(
                100,
                momentum_1w
                + momentum_1m
                + momentum_3m
                + ma
                + rsi_score
                + vol_score
                + high_score,
            ),
        ),
        1,
    )

    return total, {
        "1週モメンタム": round(momentum_1w, 1),
        "1か月モメンタム": round(momentum_1m, 1),
        "3か月モメンタム": round(momentum_3m, 1),
        "移動平均": round(ma, 1),
        "RSI": round(rsi_score, 1),
        "出来高": round(vol_score, 1),
        "52週高値": round(high_score, 1),
    }


# ------------------------------
# データ取得
# ------------------------------
@st.cache_data(ttl=1800, show_spinner=False)
def load_fx():
    currencies = sorted(set(x[5] for x in COMPANIES if x[5] != "JPY"))
    pairs = [f"{c}JPY=X" for c in currencies]
    rates = {"JPY": 1.0}

    try:
        raw = yf.download(
            pairs,
            period="5d",
            interval="1d",
            auto_adjust=False,
            progress=False,
            group_by="ticker",
            threads=True,
            timeout=20,
        )

        for c, p in zip(currencies, pairs):
            try:
                d = _extract_one(raw, p)
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
        batch = tickers[start : start + 10]

        try:
            raw = yf.download(
                batch,
                period=HISTORY_PERIOD,
                interval="1d",
                auto_adjust=True,
                group_by="ticker",
                threads=True,
                progress=False,
                timeout=25,
            )
        except Exception as e:
            raw = pd.DataFrame()
            errors.append(f"batch {start // 10 + 1}: {type(e).__name__}")

        for t in batch:
            _, name, country, region, sector, currency = COMPANY_META[t]

            try:
                d = _extract_one(raw, t)

                if d.empty or "Close" not in d.columns:
                    d = yf.download(
                        t,
                        period=HISTORY_PERIOD,
                        interval="1d",
                        auto_adjust=True,
                        progress=False,
                        timeout=18,
                    )

                if d.empty or "Close" not in d.columns:
                    raise ValueError("価格列なし")

                d = d.dropna(subset=["Close"]).copy()
                close = pd.to_numeric(d["Close"], errors="coerce").dropna()

                # Score計算には最低でも約3か月の履歴が必要。
                if len(close) < 65:
                    raise ValueError("履歴不足")

                if "Volume" in d.columns:
                    volume = pd.to_numeric(d["Volume"], errors="coerce").reindex(close.index).fillna(0)
                else:
                    volume = pd.Series(0.0, index=close.index)

                cur = float(close.iloc[-1])

                # 短期は取引日、月次以降はカレンダー基準で計算。
                r1d = _session_return(close, 1)
                r1w = _session_return(close, 5)
                r1m = _calendar_return(close, months=1)
                r3m = _calendar_return(close, months=3)
                r6m = _calendar_return(close, months=6)
                r1y = _calendar_return(close, years=1)

                sma5 = float(close.rolling(5).mean().iloc[-1])
                sma20 = float(close.rolling(20).mean().iloc[-1])
                sma60 = float(close.rolling(60).mean().iloc[-1])

                rsiv = _rsi(close, 14).iloc[-1]
                rsiv = float(rsiv) if pd.notna(rsiv) else 50.0

                avg20 = float(volume.rolling(20).mean().iloc[-1]) if len(volume) >= 20 else 0
                vr = float(volume.iloc[-1]) / avg20 if avg20 > 0 else 1.0

                # 2年データを取っていても「52週高値」は直近約1年だけで計算する。
                close_52w = close.tail(252)
                high52 = float(close_52w.max()) if not close_52w.empty else float(close.max())
                dh = cur / high52 - 1 if high52 else 0.0

                # Score式は過去バージョンとの互換性を維持。
                score_r1w = 0.0 if pd.isna(r1w) else float(r1w)
                score_r1m = 0.0 if pd.isna(r1m) else float(r1m)
                score_r3m = 0.0 if pd.isna(r3m) else float(r3m)
                score, parts = score_parts(
                    cur,
                    score_r1w,
                    score_r1m,
                    score_r3m,
                    sma5,
                    sma20,
                    sma60,
                    rsiv,
                    vr,
                    dh,
                )

                signal = "強い＋" if score >= 75 else ("＋" if score >= 60 else ("様子見" if score >= 45 else "－"))

                history_all = pd.DataFrame(
                    {
                        "Close": close,
                        "SMA20": close.rolling(20).mean(),
                        "SMA60": close.rolling(60).mean(),
                    }
                )
                # 表示チャートは今まで通り約1年。
                histories[t] = history_all.tail(253)

                rows.append(
                    [
                        t,
                        name,
                        country,
                        region,
                        sector,
                        currency,
                        cur,
                        r1d,
                        r1w,
                        r1m,
                        r3m,
                        r6m,
                        r1y,
                        rsiv,
                        vr,
                        cur / sma20 - 1,
                        cur / sma60 - 1,
                        dh,
                        score,
                        signal,
                        close.index[-1].strftime("%Y-%m-%d"),
                        parts,
                    ]
                )

            except Exception as e:
                errors.append(f"{t}: {type(e).__name__}")

        time.sleep(0.35)

    cols = [
        "Ticker",
        "会社名",
        "国",
        "地域",
        "業種",
        "通貨",
        "現在値",
        "1日",
        "1週",
        "1か月",
        "3か月",
        "6か月",
        "1年",
        "RSI",
        "出来高倍率",
        "20日線比",
        "60日線比",
        "高値乖離",
        "Atlas Score",
        "判定",
        "最終日",
        "Score内訳",
    ]

    df = pd.DataFrame(rows, columns=cols)

    if not df.empty:
        df = df.sort_values("Atlas Score", ascending=False).reset_index(drop=True)
        df.insert(0, "順位", range(1, len(df) + 1))

    return df, histories, errors


# ------------------------------
# ニュース
# ------------------------------
@st.cache_data(ttl=1800, show_spinner=False)
def load_news(ticker, company_name=""):
    items = []

    try:
        raw = yf.Ticker(ticker).news or []

        company_text = str(company_name or "").lower()
        ignore_words = {
            "inc",
            "corp",
            "corporation",
            "group",
            "holdings",
            "plc",
            "ltd",
            "company",
            "the",
            "fg",
            "adr",
        }

        keywords = [
            word.lower()
            for word in company_text.replace("&", " ").split()
            if len(word) >= 3 and word.lower() not in ignore_words
        ]

        for alias in NEWS_ALIASES.get(company_name, []):
            keywords.append(alias.lower())

        # 重複を除きつつ順番を維持
        keywords = list(dict.fromkeys(keywords))

        for n in raw[:25]:
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
            publisher = provider.get("displayName") if isinstance(provider, dict) else n.get("publisher")

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

            items.append(
                {
                    "title": title,
                    "summary": summary,
                    "publisher": publisher or "ニュース",
                    "link": link,
                }
            )

            if len(items) >= 6:
                break

    except Exception:
        pass

    return items


@st.cache_data(ttl=86400, show_spinner=False)
def analyze_news_batch_with_ai(company_name, news_payload_json):
    """最大3件のニュースを1回のAPI呼び出しで初心者向けに整理する。"""
    try:
        payload = json.loads(news_payload_json)
        if not isinstance(payload, list):
            raise ValueError("news payload")
        payload = payload[:3]

        client = OpenAI(
            api_key=st.secrets["OPENAI_API_KEY"],
            timeout=AI_TIMEOUT_SECONDS,
            max_retries=0,
        )

        prompt = f"""
あなたはATLAS 50の初心者向けニュース解説AIです。
対象企業: {company_name}

以下のニュースだけを使い、初心者にも分かる自然な日本語で整理してください。
News:
{json.dumps(payload, ensure_ascii=False, separators=(",", ":"))}

JSONだけを返してください。
{{
  "items": [
    {{
      "index": 0,
      "title_ja": "初心者にも分かる短い日本語タイトル",
      "summary": "ニュースの意味を専門用語をできるだけ使わず2文以内で説明",
      "impact": "TAILWIND, NEUTRAL, RISK のいずれか"
    }}
  ]
}}

ルール:
- supplied headline / summary にない事実を作らない
- 決算、将来業績、その他不足情報を推測しない
- 買い・売りなどの投資推奨をしない
- 方向性が分からない場合は中立
- 断定しすぎず、専門用語を避ける
- indexは変えない
- 簡潔で自然な日本語で書く
"""

        response = client.responses.create(
            model="gpt-5.6-luna",
            input=prompt,
            max_output_tokens=1000,
        )
        text = response.output_text.strip()
        if text.startswith("```"):
            text = text.replace("```json", "").replace("```", "").strip()

        parsed = json.loads(text)
        raw_items = parsed.get("items", []) if isinstance(parsed, dict) else []
        cleaned = {}
        for item in raw_items:
            if not isinstance(item, dict):
                continue
            try:
                idx = int(item.get("index"))
            except Exception:
                continue
            if idx < 0 or idx >= len(payload):
                continue
            impact = str(item.get("impact", "中立")).strip().upper()
            if impact not in {"TAILWIND", "中立", "RISK"}:
                impact = "中立"
            cleaned[idx] = {
                "title_ja": str(item.get("title_ja") or payload[idx].get("title") or "ニュース").strip(),
                "summary": str(item.get("summary") or "AI解説を取得できませんでした。").strip(),
                "impact": impact,
            }

        return {"ok": True, "items": cleaned}
    except Exception as e:
        return {
            "ok": False,
            "items": {},
            "error_type": type(e).__name__,
        }


@st.cache_data(ttl=86400, show_spinner=False)
def analyze_comparison_with_ai(compare_payload_json):
    """選択銘柄の価格トレンドとAtlas Scoreだけを、初心者向けに比較整理する。

    外部AIが長時間応答しない場合でも画面を止めないよう、
    20秒でタイムアウトし、自動でエラー表示へ戻す。
    """
    try:
        compare_payload = json.loads(compare_payload_json)

        # API待ちでStreamlitが長時間止まらないようにする。
        # max_retries=0 にして、タイムアウト後の自動再試行も抑える。
        client = OpenAI(
            api_key=st.secrets["OPENAI_API_KEY"],
            timeout=AI_TIMEOUT_SECONDS,
            max_retries=0,
        )

        prompt = f"""
あなたはATLAS 50の初心者向け比較解説AIです。
以下の比較データだけを使い、違いを分かりやすい日本語で整理してください。

Comparison data:
{json.dumps(compare_payload, ensure_ascii=False, separators=(",", ":"))}

JSONだけを返してください。

{{
  "overview": "比較全体を2文以内で要約",
  "company_notes": [
    {{"company": "会社名", "note": "このデータから見える特徴を1〜2文で説明"}}
  ],
  "key_differences": [
    "入力データから確認できる重要な違い",
    "もう1つの重要な違い"
  ],
  "watch_points": [
    "比較するときに確認したいポイント"
  ]
}}

ルール:
- 与えられた数値とAtlas Score構成要素だけを使う
- 決算、企業価値、ニュース、将来業績、不足情報を推測しない
- 買い・売り・どちらを選ぶべきかの推奨をしない
- 勝敗ではなく、期間別の値動きとScore構成の違いを説明する
- 過去リターンを将来予測として扱わない
- Atlas Scoreは学習・監視指標として扱う
- 主な違いと確認ポイントは最大3件
- すべての企業についてcompany_notesを1件ずつ作る
- 初心者にも読みやすい簡潔な日本語で書く
"""

        response = client.responses.create(
            model="gpt-5.6-luna",
            input=prompt,
            max_output_tokens=900,
        )

        raw_text = response.output_text.strip()
        if raw_text.startswith("```"):
            raw_text = raw_text.replace("```json", "").replace("```", "").strip()

        parsed = json.loads(raw_text)

        overview = str(parsed.get("overview", "")).strip()
        company_notes = parsed.get("company_notes", [])
        key_differences = parsed.get("key_differences", [])
        watch_points = parsed.get("watch_points", [])

        if not isinstance(company_notes, list):
            company_notes = []
        if not isinstance(key_differences, list):
            key_differences = []
        if not isinstance(watch_points, list):
            watch_points = []

        valid_names = {
            str(item.get("company", ""))
            for item in compare_payload.get("companies", [])
            if isinstance(item, dict)
        }

        cleaned_notes = []
        for item in company_notes:
            if not isinstance(item, dict):
                continue
            company = str(item.get("company", "")).strip()
            note = str(item.get("note", "")).strip()
            if company in valid_names and note:
                cleaned_notes.append({"company": company, "note": note})

        return {
            "ok": True,
            "overview": overview or "選択した銘柄を、価格トレンドとAtlas Score構成要素で比較しました。",
            "company_notes": cleaned_notes,
            "key_differences": [str(x).strip() for x in key_differences[:3] if str(x).strip()],
            "watch_points": [str(x).strip() for x in watch_points[:3] if str(x).strip()],
        }

    except Exception as e:
        return {
            "ok": False,
            "overview": "AI比較は一時的に利用できません。通常の比較表とチャートはそのまま確認できます。",
            "company_notes": [],
            "key_differences": [],
            "watch_points": ["AIの応答がタイムアウトしたか、一時的に利用できませんでした。時間をおいて再度お試しください。"],
            "error_type": type(e).__name__,
        }


# ------------------------------
# セッション状態
# ------------------------------
if "favorites" not in st.session_state:
    st.session_state.favorites = set()

if "portfolio" not in st.session_state:
    st.session_state.portfolio = pd.DataFrame(columns=["Ticker", "株数", "平均取得単価"])

if "comparison_ai_result" not in st.session_state:
    st.session_state.comparison_ai_result = None

if "comparison_ai_key" not in st.session_state:
    st.session_state.comparison_ai_key = None

if "news_ai_result" not in st.session_state:
    st.session_state.news_ai_result = None

if "news_ai_key" not in st.session_state:
    st.session_state.news_ai_key = None

if "saved_watch_filters" not in st.session_state:
    st.session_state.saved_watch_filters = {}

if "atlas_setup_digest" not in st.session_state:
    st.session_state.atlas_setup_digest = None

if "atlas_setup_flash" not in st.session_state:
    st.session_state.atlas_setup_flash = None

if "portfolio_csv_digest" not in st.session_state:
    st.session_state.portfolio_csv_digest = None

if "portfolio_csv_flash" not in st.session_state:
    st.session_state.portfolio_csv_flash = None

if "portfolio_editor_version" not in st.session_state:
    st.session_state.portfolio_editor_version = 0

if "favorites_editor_version" not in st.session_state:
    st.session_state.favorites_editor_version = 0

if "watch_filter_flash" not in st.session_state:
    st.session_state.watch_filter_flash = None

for watch_key, watch_default in WATCH_DEFAULTS.items():
    if watch_key not in st.session_state:
        st.session_state[watch_key] = watch_default


# ------------------------------
# ヘッダー・データロード
# ------------------------------
st.markdown(
    '<div class="atlas-hero">'
    '<div class="atlas-wordmark"><div class="atlas-title">ATLAS 50</div><span class="atlas-title-mark"></span></div>'
    '<div class="atlas-sub">GLOBAL EQUITY INTELLIGENCE</div>'
    '<div class="atlas-tagline">世界50社の動きを、シンプルに、素早く把握する。市場全体から個別銘柄まで、ひとつの画面で整理できます。</div>'
    '</div>',
    unsafe_allow_html=True,
)

st.markdown(
    f'<div class="atlas-top-controls"><div class="atlas-version-row">'
    f'<span class="atlas-chip">V{APP_VERSION} {APP_LABEL}</span>'
    f'<span class="atlas-chip">学習・モニタリング</span>'
    f'<span class="atlas-chip">世界50銘柄</span>'
    f'</div></div>',
    unsafe_allow_html=True,
)

refresh_wrap = st.container(key="market_refresh_wrap")
if refresh_wrap.button("市場データを再取得", key="refresh_market_data"):
    load_data.clear()
    load_fx.clear()
    load_news.clear()
    st.rerun()

with st.spinner("株価と為替データを読み込み中..."):
    df, histories, errors = load_data()
    fx = load_fx()

if df.empty:
    st.error("株価データを取得できませんでした。市場データの再取得をお試しください。")
    with st.expander("エラー詳細"):
        st.code("\n".join(errors[:50]))
    st.stop()

df["FX→JPY"] = df["通貨"].map(fx)
df["円換算価格"] = df["現在値"] * df["FX→JPY"]
data_health = _build_data_health(df, fx, errors)

with st.expander("はじめに・データ状況"):
    st.markdown(
        '<div class="atlas-guide-grid">'
        '<div class="atlas-guide-card"><div class="atlas-guide-step">STEP 1</div><div class="atlas-guide-title">市場全体を見る</div><div class="atlas-guide-text">Pulse・Radar・業種マップで、まず市場全体の状態を確認します。</div></div>'
        '<div class="atlas-guide-card"><div class="atlas-guide-step">STEP 2</div><div class="atlas-guide-title">銘柄を見る</div><div class="atlas-guide-text">騰落率・Atlas Score・チャート・関連ニュースをまとめて確認します。</div></div>'
        '<div class="atlas-guide-card"><div class="atlas-guide-step">STEP 3</div><div class="atlas-guide-title">比較する</div><div class="atlas-guide-text">2〜4銘柄を同じ基準で並べて違いを確認します。</div></div>'
        '<div class="atlas-guide-card"><div class="atlas-guide-step">STEP 4</div><div class="atlas-guide-title">条件で探す</div><div class="atlas-guide-text">50銘柄から条件を絞り、あとで使いたい条件を保存できます。</div></div>'
        '</div>',
        unsafe_allow_html=True,
    )
    missing_fx_text = "なし" if not data_health["missing_fx"] else " / ".join(data_health["missing_fx"])
    st.markdown(
        '<div class="data-health-grid">'
        f'<div class="data-health-item"><div class="data-health-label">取得銘柄</div><div class="data-health-value">{data_health["loaded"]} / {data_health["expected"]}</div></div>'
        f'<div class="data-health-item"><div class="data-health-label">最新株価日</div><div class="data-health-value">{html.escape(data_health["latest"])}</div></div>'
        f'<div class="data-health-item"><div class="data-health-label">為替未取得</div><div class="data-health-value">{html.escape(missing_fx_text)}</div></div>'
        f'<div class="data-health-item"><div class="data-health-label">取得エラー</div><div class="data-health-value">{len(data_health["errors"])}</div></div>'
        '</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="atlas-version-row" style="margin-top:12px;margin-bottom:7px">'
        '<span class="atlas-chip">強い 75+</span>'
        '<span class="atlas-chip">プラス 60–74.9</span>'
        '<span class="atlas-chip">中立 45–59.9</span>'
        '<span class="atlas-chip">弱い &lt;45</span>'
        '</div>',
        unsafe_allow_html=True,
    )
    st.caption("判定はAtlas Scoreを読みやすくするための目安です。データには遅延や一時的な取得失敗があり、売買を推奨するものではありません。")

if st.session_state.atlas_setup_flash:
    st.success(st.session_state.atlas_setup_flash)
    st.session_state.atlas_setup_flash = None

with st.expander("設定を復元"):
    st.caption("ウォッチリスト・保有株・保存した条件をATLAS設定JSONから復元できます。")
    atlas_setup_upload_global = st.file_uploader(
        "ATLAS設定JSONを読み込む",
        type=["json"],
        key="atlas_setup_upload_global",
    )
    if atlas_setup_upload_global is not None:
        try:
            setup_bytes = atlas_setup_upload_global.getvalue()
            setup_digest = hashlib.sha256(setup_bytes).hexdigest()
            if setup_digest != st.session_state.atlas_setup_digest:
                setup_payload = json.loads(setup_bytes.decode("utf-8"))
                _apply_atlas_setup_payload(setup_payload)
                st.session_state.atlas_setup_digest = setup_digest
                st.session_state.atlas_setup_flash = "ATLAS設定を復元しました。"
                st.rerun()
        except Exception:
            st.error("ATLAS設定ファイルを読み込めませんでした。")

tabs = st.tabs(["ホーム", "世界50", "個別分析", "比較", "ウォッチリスト", "保有株", "予算", "条件検索"])


# ------------------------------
# ホーム
# ------------------------------
with tabs[0]:
    a, b, c, d, e = st.columns(5)

    a.metric("対象銘柄", f"{len(df)} / 50")
    b.metric("強い＋", int((df["判定"] == "強い＋").sum()))
    c.metric("プラス", int((df["判定"] == "＋").sum()))
    d.metric("平均Score", f'{df["Atlas Score"].mean():.1f}')
    e.metric("最新株価日", str(df["最終日"].max()))

    pulse = _build_atlas_pulse(df)
    _section_intro("MARKET BREADTH", "市場全体の広がり", "50銘柄の中で、強さや弱さがどれくらい広がっているかを確認します。")

    pulse_box = st.container(border=True)
    p1, p2, p3, p4 = pulse_box.columns(4)
    p1.metric("プラス 1か月", f"{pulse['one_month_positive']} / {pulse['total']}")
    p2.metric("プラス 3か月", f"{pulse['three_month_positive']} / {pulse['total']}")
    p3.metric("20日線より上", f"{pulse['above_sma20']} / {pulse['total']}")
    p4.metric("平均1か月", f"{pulse['avg_one_month']:+.2f}%")
    pulse_box.info(
        f"**市場状態: {pulse['label']}**\n\n"
        f"{pulse['summary']}"
    )
    pulse_box.caption(
        "市場状態は「1か月プラス銘柄の割合」「20日線より上の銘柄割合」「平均1か月騰落率」から整理しています。3か月プラス数は補助情報です。"
    )

    with st.expander("地域別の状態を見る"):
        region_show = pulse["region"].copy()

        region_table = st.container(key="pulse_region_table")
        region_table.dataframe(
            _ui_frame(region_show),
            use_container_width=True,
            hide_index=True,
            column_config={
                "平均Score": st.column_config.ProgressColumn(
                    min_value=0, max_value=100, format="%.1f"
                ),
                "1か月平均": st.column_config.NumberColumn(format="%.2f%%"),
                "3か月平均": st.column_config.NumberColumn(format="%.2f%%"),
            },
        )

        region_mobile = st.container(key="pulse_region_mobile")
        region_cards = ""
        for _, region_row in region_show.iterrows():
            region_name = _region_en(region_row["地域"])
            region_count = int(region_row["銘柄数"])
            region_score = float(region_row["平均Score"])
            region_1m = float(region_row["1か月平均"])
            region_3m = float(region_row["3か月平均"])
            region_cards += (
                f'<div class="pulse-region-card">'
                f'<div class="pulse-region-head">'
                f'<div class="pulse-region-name">{html.escape(region_name)}</div>'
                f'<div class="pulse-region-count">{region_count}銘柄</div>'
                f'</div>'
                f'<div class="pulse-region-score">平均Atlas Score {region_score:.1f}</div>'
                f'<div class="pulse-region-stats">'
                f'1か月平均 {region_1m:+.2f}% | 3か月平均 {region_3m:+.2f}%'
                f'</div>'
                f'</div>'
            )
        region_mobile.markdown(region_cards, unsafe_allow_html=True)

        st.caption("地域別の平均はATLAS 50に含まれる銘柄だけの集計です。地域市場全体の指数ではありません。")

    _section_intro("MARKET MOVERS", "変化が目立つ銘柄", "直近の値動きや出来高の変化が目立つ銘柄を確認します。")

    radar = _build_atlas_radar(df)

    def _radar_items_html(frame, mode):
        items = []
        for _, radar_row in frame.iterrows():
            company = html.escape(str(radar_row["会社名"]))
            country = html.escape(_country_en(radar_row["国"]))
            score = float(radar_row["Atlas Score"]) if pd.notna(radar_row["Atlas Score"]) else 0.0
            one_m = float(radar_row["1か月"]) * 100 if pd.notna(radar_row["1か月"]) else None
            three_m = float(radar_row["3か月"]) * 100 if pd.notna(radar_row["3か月"]) else None
            volume_ratio = float(radar_row["出来高倍率"]) if pd.notna(radar_row["出来高倍率"]) else None

            if mode == "volume":
                main_value = f"{volume_ratio:.2f}x" if volume_ratio is not None else "-"
                meta = f"{country} | 1か月 {one_m:+.2f}% | Score {score:.1f}" if one_m is not None else f"{country} | Score {score:.1f}"
            else:
                main_value = f"{one_m:+.2f}%" if one_m is not None else "-"
                meta = f"{country} | 3か月 {three_m:+.2f}% | Score {score:.1f}" if three_m is not None else f"{country} | Score {score:.1f}"

            items.append(
                '<div class="atlas-radar-item">'
                '<div>'
                f'<div class="atlas-radar-company">{company}</div>'
                f'<div class="atlas-radar-meta">{meta}</div>'
                '</div>'
                f'<div class="atlas-radar-value">{main_value}</div>'
                '</div>'
            )
        return "".join(items) or '<div class="atlas-radar-meta">データを取得できませんでした。</div>'

    radar_html = (
        '<div class="atlas-radar-grid">'
        '<div class="atlas-radar-panel">'
        '<div class="atlas-radar-title">1か月上昇が目立つ</div>'
        '<div class="atlas-radar-sub">直近1か月の上昇率が大きい3社</div>'
        + _radar_items_html(radar["up"], "up")
        + '</div>'
        '<div class="atlas-radar-panel">'
        '<div class="atlas-radar-title">1か月下落が目立つ</div>'
        '<div class="atlas-radar-sub">直近1か月の下落率が大きい3社</div>'
        + _radar_items_html(radar["down"], "down")
        + '</div>'
        '<div class="atlas-radar-panel">'
        '<div class="atlas-radar-title">出来高が目立つ</div>'
        '<div class="atlas-radar-sub">現在出来高 ÷ 20日平均が大きい3社</div>'
        + _radar_items_html(radar["volume"], "volume")
        + '</div>'
        '</div>'
    )
    st.markdown(radar_html, unsafe_allow_html=True)
    st.caption("Radarは最近の値動きや出来高の変化を整理する観察用表示です。今後の値動きを予測するものではありません。")

    _section_intro("SECTOR MOMENTUM", "業種別ヒートマップ", "29業種を9つの大分類にまとめ、期間別の平均値から強弱の分布を確認します。")

    sector_summary, sector_heat = _build_sector_heatmap(df)

    if not sector_summary.empty:
        best_score = sector_summary.sort_values("平均Score", ascending=False).iloc[0]
        best_1m = sector_summary.sort_values("1か月平均", ascending=False).iloc[0]
        best_breadth = sector_summary.sort_values(["1か月プラス率", "平均Score"], ascending=[False, False]).iloc[0]

        sector_spotlight_html = (
            '<div class="sector-spotlight-grid">'
            '<div class="sector-spotlight-card">'
            '<div class="sector-spotlight-label">平均Score 上位</div>'
            f'<div class="sector-spotlight-value">{html.escape(_sector_group_en(best_score["業種グループ"]))}</div>'
            f'<div class="sector-spotlight-meta">Score {float(best_score["平均Score"]):.1f} | {int(best_score["銘柄数"])}銘柄</div>'
            '</div>'
            '<div class="sector-spotlight-card">'
            '<div class="sector-spotlight-label">1か月平均 上位</div>'
            f'<div class="sector-spotlight-value">{html.escape(_sector_group_en(best_1m["業種グループ"]))}</div>'
            f'<div class="sector-spotlight-meta">1か月 {float(best_1m["1か月平均"]):+.2f}% | Score {float(best_1m["平均Score"]):.1f}</div>'
            '</div>'
            '<div class="sector-spotlight-card">'
            '<div class="sector-spotlight-label">上昇の広がり 上位</div>'
            f'<div class="sector-spotlight-value">{html.escape(_sector_group_en(best_breadth["業種グループ"]))}</div>'
            f'<div class="sector-spotlight-meta">1か月プラス {float(best_breadth["1か月プラス率"]):.0f}% | {int(best_breadth["銘柄数"])}銘柄</div>'
            '</div>'
            '</div>'
        )
        st.markdown(sector_spotlight_html, unsafe_allow_html=True)

        sector_order = sector_summary["業種グループ"].tolist()

        # Altairの描画差に依存しないHTMLヒートマップ。
        # PCは一覧型、スマホは業種ごとの2×2カードに自動切り替え。
        sector_heatmap_html = _render_sector_heatmap_html(sector_summary, sector_heat)
        if sector_heatmap_html:
            st.markdown(sector_heatmap_html, unsafe_allow_html=True)

        st.caption(
            "色の目安：赤は相対的に弱め、中央付近は中立、緑は相対的に強めです。色だけでなくセル内の数値を優先して確認してください。"
        )

        with st.expander("業種グループの内訳を見る"):
            grouped_sectors = {}
            for original_sector, grouped_sector in SECTOR_GROUPS.items():
                grouped_sectors.setdefault(grouped_sector, []).append(original_sector)
            for grouped_sector in sector_order:
                members = grouped_sectors.get(grouped_sector, [grouped_sector])
                st.markdown(f"**{_sector_group_en(grouped_sector)}**: {' / '.join(_sector_en(x) for x in members)}")
            st.caption("この分類はATLAS 50独自の見やすさ重視の分類で、市場標準の正式なセクター分類ではありません。")
    else:
        st.caption("業種データを集計できませんでした。")

    st.caption("業種別ヒートマップはATLAS 50内の現在データを整理する観察用表示です。業種や銘柄を推奨するものではありません。")

    _section_intro("RANKING", "注目TOP10", "現在のAtlas Scoreが高い順に上位10銘柄を表示します。")
    top = df.head(10)[
        [
            "順位",
            "会社名",
            "国",
            "1か月",
            "3か月",
            "6か月",
            "1年",
            "Atlas Score",
            "判定",
        ]
    ].copy()

    for col in ["1か月", "3か月", "6か月", "1年"]:
        top[col] = (top[col] * 100).round(2)

    home_top10_table = st.container(key="home_top10_table")
    home_top10_table.dataframe(
        _ui_frame(top),
        use_container_width=True,
        hide_index=True,
        column_config={
            "1か月": st.column_config.NumberColumn(format="%.2f%%"),
            "3か月": st.column_config.NumberColumn(format="%.2f%%"),
            "6か月": st.column_config.NumberColumn(format="%.2f%%"),
            "1年": st.column_config.NumberColumn(format="%.2f%%"),
            "Atlas Score": st.column_config.ProgressColumn(min_value=0, max_value=100, format="%.1f"),
        },
    )

    home_top10_cards = []
    for _, top_row in top.iterrows():
        home_top10_cards.append(
            '<div class="home-top10-card">'
            '<div class="home-top10-head">'
            '<div>'
            f'<div class="home-top10-rank">#{int(top_row["順位"])}</div>'
            f'<div class="home-top10-company">{html.escape(str(top_row["会社名"]))}</div>'
            f'<div class="home-top10-country">{html.escape(_country_en(top_row["国"]))}</div>'
            '</div>'
            f'<div class="home-top10-score">Score {float(top_row["Atlas Score"]):.1f}</div>'
            '</div>'
            '<div class="home-top10-grid">'
            f'<div class="home-top10-item"><div class="home-top10-label">1か月</div><div class="home-top10-value">{_pct_number_text(top_row["1か月"])}</div></div>'
            f'<div class="home-top10-item"><div class="home-top10-label">3か月</div><div class="home-top10-value">{_pct_number_text(top_row["3か月"])}</div></div>'
            f'<div class="home-top10-item"><div class="home-top10-label">6か月</div><div class="home-top10-value">{_pct_number_text(top_row["6か月"])}</div></div>'
            f'<div class="home-top10-item"><div class="home-top10-label">1年</div><div class="home-top10-value">{_pct_number_text(top_row["1年"])}</div></div>'
            '</div>'
            f'<div class="home-top10-judge signal-{_status_tone(top_row["判定"])}">{html.escape(_signal_en(top_row["判定"]))}</div>'
            '</div>'
        )

    st.markdown(
        '<div class="home-top10-mobile">' + "".join(home_top10_cards) + '</div>',
        unsafe_allow_html=True,
    )
    st.caption("表示Scoreは小数1桁に丸めています。同じ表示値でも内部の細かい値で順位が分かれる場合があります。")

    _section_intro("RANK EXPLAINER", "なぜこの順位？", "TOP10から銘柄を選ぶと、現在の順位を支えているAtlas指標を分かりやすく整理します。")

    rank_options = df.head(10)["会社名"].tolist()
    selected_rank_company = st.selectbox(
        "銘柄",
        rank_options,
        key="home_rank_reason_company",
        label_visibility="collapsed",
    )

    rank_row = df[df["会社名"] == selected_rank_company].iloc[0]
    rank_detail = _build_ranking_explanation(rank_row, df)

    rank_card = st.container(border=True)
    rank_card.markdown(
        f"#### #{rank_detail['rank']} {selected_rank_company}  "
        f"<span class='badge'>Atlas Score {rank_detail['score']:.1f}</span>",
        unsafe_allow_html=True,
    )
    rank_card.caption(rank_detail["position"])
    rank_card.info(
        "**順位を押し上げている主な要因**\n\n"
        + "\n\n".join(f"- {item}" for item in rank_detail["strengths"])
        + f"\n\n**値動きの流れ**\n\n- {rank_detail['trend']}"
    )
    rank_card.warning(
        "**チェックポイント**\n\n"
        + "\n\n".join(f"- {item}" for item in rank_detail["checks"])
    )
    rank_card.caption("順位は現在の価格トレンド指標を整理したものです。投資推奨や将来予測ではありません。")
 
# ------------------------------
# 世界50
# ------------------------------
with tabs[1]:
    _section_intro("対象銘柄", "世界50", "会社名・地域・業種・Scoreなどから世界50銘柄を絞り込めます。")

    search_text = st.text_input(
        "会社名またはTicker",
        placeholder="例：NVIDIA / NVDA / MUFG",
        key="world_search",
    ).strip()

    f1, f2, f3, f4 = st.columns(4)
    country = f1.selectbox("国", ["すべて"] + sorted(df["国"].unique().tolist()), key="country", format_func=lambda x: "すべて" if x == "すべて" else _country_en(x))
    region = f2.selectbox("地域", ["すべて"] + sorted(df["地域"].unique().tolist()), key="region", format_func=lambda x: "すべて" if x == "すべて" else _region_en(x))
    sector = f3.selectbox("業種", ["すべて"] + sorted(df["業種"].unique().tolist()), key="sector", format_func=lambda x: "すべて" if x == "すべて" else _sector_en(x))
    minscore = f4.slider("最低Atlas Score", 0, 100, 0, key="score")

    f5, f6 = st.columns(2)
    judge_filter = f5.selectbox(
        "判定",
        ["すべて", "強い＋", "＋", "様子見", "－"],
        key="world_judge",
        format_func=lambda x: "すべて" if x == "すべて" else _signal_en(x),
    )
    world_sort = f6.selectbox(
        "並び順",
        ["Atlas Scoreが高い順", "1か月上昇率が高い順", "3か月上昇率が高い順", "円換算価格が安い順"],
        key="world_sort",
        format_func=lambda x: WORLD_SORT_EN.get(x, x),
    )

    view = df.copy()
    if search_text:
        q = search_text.casefold()
        search_mask = (
            view["会社名"].astype(str).str.casefold().str.contains(q, regex=False)
            | view["Ticker"].astype(str).str.casefold().str.contains(q, regex=False)
        )
        view = view[search_mask]
    if country != "すべて":
        view = view[view["国"] == country]
    if region != "すべて":
        view = view[view["地域"] == region]
    if sector != "すべて":
        view = view[view["業種"] == sector]
    if judge_filter != "すべて":
        view = view[view["判定"] == judge_filter]
    view = view[view["Atlas Score"] >= minscore]

    world_sort_map = {
        "Atlas Scoreが高い順": ("Atlas Score", False),
        "1か月上昇率が高い順": ("1か月", False),
        "3か月上昇率が高い順": ("3か月", False),
        "円換算価格が安い順": ("円換算価格", True),
    }
    sort_col, sort_ascending = world_sort_map[world_sort]
    view = view.sort_values(sort_col, ascending=sort_ascending, na_position="last").copy()
    st.caption(f"表示中: {len(view)} / {len(df)}銘柄")

    show = view[
        [
            "順位",
            "会社名",
            "国",
            "業種",
            "円換算価格",
            "1か月",
            "3か月",
            "6か月",
            "1年",
            "Atlas Score",
            "判定",
        ]
    ].copy()

    for col in ["1か月", "3か月", "6か月", "1年"]:
        show[col] = (show[col] * 100).round(2)

    world50_table = st.container(key="world50_table")
    world50_table.dataframe(
        _ui_frame(show),
        use_container_width=True,
        hide_index=True,
        column_config={
            "円換算価格": st.column_config.NumberColumn(format="¥%.0f"),
            "1か月": st.column_config.NumberColumn(format="%.2f%%"),
            "3か月": st.column_config.NumberColumn(format="%.2f%%"),
            "6か月": st.column_config.NumberColumn(format="%.2f%%"),
            "1年": st.column_config.NumberColumn(format="%.2f%%"),
            "Atlas Score": st.column_config.ProgressColumn(
                min_value=0,
                max_value=100,
                format="%.1f",
            ),
        },
    )

    # スマホ用カードは1回のHTML描画にまとめる。
    # MarkdownにHTMLを渡す際、行頭の空白がコードブロック扱いされないよう
    # HTML文字列はインデントNoneで組み立てる。
    mobile_cards = []
    for _, mobile_row in show.iterrows():
        mobile_cards.append(
            "<div class=\"mobile-stock-card\">"
            f"<div class=\"mobile-rank\">#{int(mobile_row['順位'])}</div>"
            f"<div class=\"mobile-company\">{html.escape(str(mobile_row['会社名']))}</div>"
            f"<div class=\"mobile-meta\">{html.escape(_country_en(mobile_row['国']))} | {html.escape(_sector_en(mobile_row['業種']))}</div>"
            f"<div class=\"mobile-score\">Atlas Score {float(mobile_row['Atlas Score']):.1f}</div>"
            "<div class=\"mobile-stats\">"
            f"1か月 {_pct_number_text(mobile_row['1か月'])} | 3か月 {_pct_number_text(mobile_row['3か月'])}<br>"
            f"6か月 {_pct_number_text(mobile_row['6か月'])} | 1年 {_pct_number_text(mobile_row['1年'])}"
            "</div>"
            f"<div class=\"mobile-judge signal-{_status_tone(mobile_row['判定'])}\">{html.escape(_signal_en(mobile_row['判定']))}</div>"
            "</div>"
        )

    mobile_html = (
        '<div class="mobile-list-wrap">'
        '<div class="mobile-list-title">銘柄一覧</div>'
        + "".join(mobile_cards)
        + "</div>"
    )
    st.markdown(mobile_html, unsafe_allow_html=True)



# ------------------------------
# 個別分析
# ------------------------------
with tabs[2]:
    _section_intro("DEEP DIVE", "個別分析", "気になる企業を選ぶと、値動き・Atlas Score・チャート・関連ニュースをまとめて確認できます。")

    selected = st.selectbox("会社", df["会社名"].tolist(), key="detail_company")
    row = df[df["会社名"] == selected].iloc[0]
    t = row["Ticker"]

    price_text = f'¥{row["円換算価格"]:,.0f}' if pd.notna(row["円換算価格"]) else "-"

    st.markdown(f"## {selected}")
    st.caption(f"{_country_en(row['国'])} | {_sector_en(row['業種'])} | Ticker {t} | 円換算 {price_text}")

    # 6個の重要指標を、スマホでも崩れにくい3列×2段で表示。
    c1, c2, c3 = st.columns(3)
    c1.metric("Atlas Score", f'{row["Atlas Score"]:.1f}')
    c2.metric("判定", _signal_en(row["判定"]))
    c3.metric("1か月", _pct_text(row["1か月"]))

    c4, c5, c6 = st.columns(3)
    c4.metric("3か月", _pct_text(row["3か月"]))
    c5.metric("6か月", _pct_text(row["6か月"]))
    c6.metric("1年", _pct_text(row["1年"]))

    score = float(row["Atlas Score"])
    one_month = float(row["1か月"]) * 100 if pd.notna(row["1か月"]) else None
    three_month = float(row["3か月"]) * 100 if pd.notna(row["3か月"]) else None
    six_month = float(row["6か月"]) * 100 if pd.notna(row["6か月"]) else None
    one_year = float(row["1年"]) * 100 if pd.notna(row["1年"]) else None

    _section_intro("QUICK READ", "30秒でわかる", "現在データのプラス材料と確認ポイントを初心者向けに短く整理します。")

    good_points = []
    risk_points = []

    if score >= 80:
        good_points.append("Atlas Scoreが高く、50銘柄の中でも現在の注目度は高めです。")
    elif score >= 65:
        good_points.append("Atlas Scoreは中〜高水準です。")

    for label, value in [
        ("1か月", one_month),
        ("3か月", three_month),
        ("6か月", six_month),
        ("1年", one_year),
    ]:
        if value is None:
            continue
        if value > 0:
            good_points.append(f"{label}は +{value:.1f}%です。")
        else:
            risk_points.append(f"{label}は {value:.1f}%です。")

    if one_month is not None and abs(one_month) >= 15:
        risk_points.append("1か月の値動きが大きく、短期の価格変動には注意が必要です。")

    if not good_points:
        good_points.append("現在は特に強いプラス材料が目立たない状態です。")

    if not risk_points:
        risk_points.append("価格トレンドだけでは大きな警戒材料は確認されていません。")

    st.info(
        "### プラス材料\n\n"
        + "\n\n".join(f"- {x}" for x in good_points)
    )

    st.warning(
        "### チェックポイント\n\n"
        + "\n\n".join(f"- {x}" for x in risk_points)
    )

    is_favorite = t in st.session_state.favorites
    favorite_label = "ウォッチリストから解除" if is_favorite else "ウォッチリストに追加"
    if st.button(favorite_label, key="fav_btn"):
        if is_favorite:
            st.session_state.favorites.remove(t)
        else:
            st.session_state.favorites.add(t)
        st.session_state.favorites_editor_version += 1
        st.rerun()

    _section_intro("CONTEXT", "なぜ今注目？", "Scoreと期間別の値動きから、現在注目される背景を整理します。")

    news_preview = load_news(t, selected)
    reasons = _build_attention_reasons(
        score=score,
        one_month=one_month,
        three_month=three_month,
        six_month=six_month,
        one_year=one_year,
        has_news=bool(news_preview),
    )

    if reasons:
        st.info(
            "### 注目ポイント\n\n"
            + "\n\n".join(f"- {reason}" for reason in reasons)
        )
    else:
        st.info(
            "### 注目ポイント\n\n"
            "- 現在は大きく目立つトレンドが少ない状態です。"
        )

    _section_intro("NEWS", "最新ニュース & AI解説", "関連ニュースを最大3件表示します。AI解説はボタンを押した時だけ実行します。")
    st.caption(
        "AI解説は任意です。表示されている見出しと概要だけを使って整理します。"
    )

    if news_preview:
        news_payload = [
            {
                "title": str(item.get("title", "")),
                "summary": str(item.get("summary", ""))[:1500],
                "publisher": str(item.get("publisher", "ニュース")),
            }
            for item in news_preview[:3]
        ]
        news_ai_key = json.dumps(
            {"company": selected, "news": news_payload},
            ensure_ascii=False,
            sort_keys=True,
        )

        if st.button(
            "AIでニュースを整理する",
            key=f"news_ai_button_{t}",
            use_container_width=True,
        ):
            with st.spinner(f"ATLAS AIがニュースを整理中... 最大 {int(AI_TIMEOUT_SECONDS)}秒"):
                st.session_state.news_ai_result = analyze_news_batch_with_ai(
                    selected,
                    json.dumps(news_payload, ensure_ascii=False, sort_keys=True),
                )
                st.session_state.news_ai_key = news_ai_key

        active_news_ai = None
        if st.session_state.news_ai_key == news_ai_key:
            active_news_ai = st.session_state.news_ai_result

        if active_news_ai and not active_news_ai.get("ok", False):
            st.warning("AI解説を一時的に取得できません。元のニュース見出しはそのまま確認できます。")

        ai_items = active_news_ai.get("items", {}) if active_news_ai and active_news_ai.get("ok") else {}

        for i, item in enumerate(news_preview[:3], start=1):
            card = st.container(border=True)
            card.markdown(f"### ニュース {i}")

            ai_news = ai_items.get(i - 1) if isinstance(ai_items, dict) else None
            if ai_news:
                title_display = ai_news.get("title_ja", item["title"])
                summary_display = ai_news.get("summary", "AI解説を取得できませんでした。")
                impact = ai_news.get("impact", "NEUTRAL")
                impact_label = {
                    "TAILWIND": "追い風候補",
                    "NEUTRAL": "中立",
                    "RISK": "リスク候補",
                }.get(str(impact).upper(), "中立")

                card.write(f"**{title_display}**")
                card.caption(f"情報元: {item['publisher']}")
                card.info(f"初心者向け解説\n\n{summary_display}")
                card.write(f"**ニュースの影響: {impact_label}**")
                card.caption(f"原文見出し: {item['title']}")
            else:
                card.write(f"**{item['title']}**")
                card.caption(f"情報元: {item['publisher']} | 上のボタンからAI解説を作成できます")
                source_summary = str(item.get("summary", "") or "").strip()
                if source_summary:
                    card.write(source_summary[:500] + ("…" if len(source_summary) > 500 else ""))

            if item.get("link"):
                card.markdown(f"[元の記事を見る]({item['link']})")
    else:
        st.caption("関連ニュースを取得できませんでした。")

    _section_intro("PRICE", "1年チャート", "株価と20日・60日移動平均線を表示します。")

    hist = histories.get(t)
    if hist is not None and not hist.empty:
        st.line_chart(hist[["Close", "SMA20", "SMA60"]])
    else:
        st.caption("チャートデータを取得できませんでした。")

    _section_intro("SCORE MODEL", "Atlas Scoreの内訳", "Atlas Scoreを構成している各指標の点数を確認できます。")

    parts = row["Score内訳"]
    parts_df = pd.DataFrame({"項目": [SCORE_PART_EN.get(str(k), str(k)) for k in parts.keys()], "点数": list(parts.values())})
    st.bar_chart(parts_df.set_index("項目")["点数"])


# ------------------------------
# 銘柄比較
# ------------------------------
with tabs[3]:
    _section_intro("COMPARE", "銘柄比較", "2〜4銘柄を同じ期間とAtlas Scoreの基準で並べ、違いを確認します。")

    default_compare = df.head(2)["会社名"].tolist()
    compare_names = st.multiselect(
        "比較する企業（2〜4社）",
        options=df["会社名"].tolist(),
        default=default_compare,
        max_selections=4,
        key="compare_companies",
    )

    if len(compare_names) < 2:
        st.info("比較する企業を2社以上選んでください。")
    else:
        compare_df = df[df["会社名"].isin(compare_names)].copy()
        compare_order = {name: i for i, name in enumerate(compare_names)}
        compare_df["_order"] = compare_df["会社名"].map(compare_order)
        compare_df = compare_df.sort_values("_order")

        st.markdown("### 基本比較")
        compare_show = compare_df[
            [
                "会社名",
                "国",
                "業種",
                "円換算価格",
                "1か月",
                "3か月",
                "6か月",
                "1年",
                "Atlas Score",
                "判定",
            ]
        ].copy()

        for col in ["1か月", "3か月", "6か月", "1年"]:
            compare_show[col] = (compare_show[col] * 100).round(2)

        # PC: 情報量を落とさず表で比較。
        compare_table = st.container(key="compare_table")
        compare_table.dataframe(
            _ui_frame(compare_show),
            use_container_width=True,
            hide_index=True,
            column_config={
                "円換算価格": st.column_config.NumberColumn(format="¥%.0f"),
                "1か月": st.column_config.NumberColumn(format="%.2f%%"),
                "3か月": st.column_config.NumberColumn(format="%.2f%%"),
                "6か月": st.column_config.NumberColumn(format="%.2f%%"),
                "1年": st.column_config.NumberColumn(format="%.2f%%"),
                "Atlas Score": st.column_config.ProgressColumn(
                    min_value=0,
                    max_value=100,
                    format="%.1f",
                ),
            },
        )

        # スマホ: 横スクロール表ではなく、各社をカードにして主要情報を一画面で読む。
        mobile_compare_cards = []
        for _, compare_row in compare_df.iterrows():
            company = html.escape(str(compare_row["会社名"]))
            country = html.escape(_country_en(compare_row["国"]))
            sector = html.escape(_sector_en(compare_row["業種"]))
            judge = html.escape(_signal_en(compare_row["判定"]))
            price = compare_row["円換算価格"]
            price_text = f"¥{price:,.0f}" if pd.notna(price) else "-"
            score_text = f"{float(compare_row['Atlas Score']):.1f}"

            period_values = {}
            for period in ["1か月", "3か月", "6か月", "1年"]:
                value = compare_row[period]
                period_values[period] = _pct_text(value, decimals=1)

            mobile_compare_cards.append(
                '<div class="compare-card">'
                '<div class="compare-card-head">'
                '<div>'
                f'<div class="compare-card-company">{company}</div>'
                f'<div class="compare-card-meta">{country} | {sector} | {price_text}</div>'
                '</div>'
                f'<div class="compare-card-score">Score {score_text}</div>'
                '</div>'
                '<div class="compare-card-grid">'
                f'<div class="compare-card-item"><div class="compare-card-label">1か月</div><div class="compare-card-value">{period_values["1か月"]}</div></div>'
                f'<div class="compare-card-item"><div class="compare-card-label">3か月</div><div class="compare-card-value">{period_values["3か月"]}</div></div>'
                f'<div class="compare-card-item"><div class="compare-card-label">6か月</div><div class="compare-card-value">{period_values["6か月"]}</div></div>'
                f'<div class="compare-card-item"><div class="compare-card-label">1年</div><div class="compare-card-value">{period_values["1年"]}</div></div>'
                '</div>'
                f'<div class="compare-card-judge signal-{_status_tone(compare_row["判定"])}">{judge}</div>'
                '</div>'
            )

        compare_mobile = st.container(key="compare_mobile")
        compare_mobile.markdown(
            "".join(mobile_compare_cards),
            unsafe_allow_html=True,
        )

        st.markdown("### 1年の値動きを100基準で比較")
        st.caption("各社の開始時点を100として、株価水準ではなく値動きの差を比較します。")

        normalized_series = []
        for _, compare_row in compare_df.iterrows():
            compare_hist = histories.get(compare_row["Ticker"])
            if compare_hist is None or compare_hist.empty or "Close" not in compare_hist.columns:
                continue

            close = pd.to_numeric(compare_hist["Close"], errors="coerce").dropna()
            if close.empty or float(close.iloc[0]) == 0:
                continue

            normalized = close / float(close.iloc[0]) * 100
            normalized.name = compare_row["会社名"]
            normalized_series.append(normalized)

        if normalized_series:
            # 国ごとの休場日差で線が途切れないよう、既存の観測日に対して直前値を引き継ぐ。
            normalized_df = pd.concat(normalized_series, axis=1).sort_index()
            normalized_df = normalized_df.ffill().dropna(how="any")
            st.line_chart(normalized_df, height=360)
            st.caption("市場ごとの休場日は、比較表示上のみ直前の終値を引き継いでいます。")
        else:
            st.caption("比較チャートを作るための価格データが不足しています。")

        st.markdown("### Atlas Scoreの内訳比較")
        st.caption("総合Scoreだけでなく、どの項目で差が出ているか確認できます。")

        parts_map = {}
        part_order = []
        for _, compare_row in compare_df.iterrows():
            parts = compare_row["Score内訳"]
            if isinstance(parts, dict):
                if not part_order:
                    part_order = list(parts.keys())
                parts_map[compare_row["会社名"]] = pd.Series(parts, dtype="float64")

        if parts_map:
            parts_compare = pd.DataFrame(parts_map).fillna(0)
            parts_long = (
                parts_compare.rename_axis("項目")
                .reset_index()
                .assign(項目=lambda x: x["項目"].map(lambda v: SCORE_PART_EN.get(str(v), str(v))))
                .melt(id_vars="項目", var_name="会社", value_name="点数")
            )

            score_chart = (
                alt.Chart(parts_long)
                .mark_bar(cornerRadiusEnd=3)
                .encode(
                    y=alt.Y(
                        "項目:N",
                        sort=[SCORE_PART_EN.get(str(x), str(x)) for x in part_order],
                        title=None,
                        axis=alt.Axis(labelLimit=120),
                    ),
                    x=alt.X("点数:Q", title="点数", scale=alt.Scale(zero=True)),
                    color=alt.Color("会社:N", title=None, scale=alt.Scale(range=["#63E6D5", "#6BA8FF", "#F5C76B", "#C084FC"])),
                    yOffset=alt.YOffset("会社:N"),
                    tooltip=[
                        alt.Tooltip("会社:N", title="会社"),
                        alt.Tooltip("項目:N", title="項目"),
                        alt.Tooltip("点数:Q", title="点数", format=".1f"),
                    ],
                )
                .properties(height=max(300, len(part_order) * 48))
            )
            st.altair_chart(score_chart, use_container_width=True)
        else:
            st.caption("Score内訳を比較できませんでした。")

        st.markdown("### ATLAS AI 比較解説")
        st.caption("選択した騰落率とAtlas Score内訳だけを使い、違いを初心者向けの日本語で整理します。")

        compare_payload = {"companies": []}
        for _, ai_row in compare_df.iterrows():
            ai_parts = ai_row["Score内訳"] if isinstance(ai_row["Score内訳"], dict) else {}
            compare_payload["companies"].append(
                {
                    "company": str(ai_row["会社名"]),
                    "country": _country_en(ai_row["国"]),
                    "sector": _sector_en(ai_row["業種"]),
                    "returns_pct": {
                        "1か月": None if pd.isna(ai_row["1か月"]) else round(float(ai_row["1か月"]) * 100, 2),
                        "3か月": None if pd.isna(ai_row["3か月"]) else round(float(ai_row["3か月"]) * 100, 2),
                        "6か月": None if pd.isna(ai_row["6か月"]) else round(float(ai_row["6か月"]) * 100, 2),
                        "1年": None if pd.isna(ai_row["1年"]) else round(float(ai_row["1年"]) * 100, 2),
                    },
                    "atlas_score": round(float(ai_row["Atlas Score"]), 1),
                    "judge": _signal_en(ai_row["判定"]),
                    "score_parts": {
                        str(k): (None if pd.isna(v) else round(float(v), 1))
                        for k, v in ai_parts.items()
                    },
                }
            )

        compare_payload_json = json.dumps(
            compare_payload,
            ensure_ascii=False,
            sort_keys=True,
        )

        if st.button(
            "ATLAS AIで比較を整理する",
            key="compare_ai_button",
            use_container_width=True,
        ):
            with st.spinner(f"ATLAS AIが比較データを整理中... 最大 {int(AI_TIMEOUT_SECONDS)}秒"):
                st.session_state.comparison_ai_result = analyze_comparison_with_ai(
                    compare_payload_json
                )
                st.session_state.comparison_ai_key = compare_payload_json

        ai_result = None
        if st.session_state.comparison_ai_key == compare_payload_json:
            ai_result = st.session_state.comparison_ai_result

        if ai_result:
            if ai_result.get("ok", True):
                st.success(
                    "### 比較全体\n\n"
                    + ai_result.get(
                        "overview",
                        "選択した銘柄を、価格トレンドとAtlas Score構成要素で比較しました。",
                    )
                )
            else:
                st.warning(
                    "### AI解説を利用できません\n\n"
                    + ai_result.get(
                        "overview",
                        "通常の比較表とチャートはそのまま確認できます。",
                    )
                )

            company_notes = ai_result.get("company_notes", [])
            if company_notes:
                st.markdown("#### 各社の特徴")
                for note in company_notes:
                    note_card = st.container(border=True)
                    note_card.markdown(f"**{note.get('company', '会社')}**")
                    note_card.write(note.get("note", ""))

            key_differences = ai_result.get("key_differences", [])
            if key_differences:
                st.info(
                    "### 主な違い\n\n"
                    + "\n".join(f"- {item}" for item in key_differences)
                )

            watch_points = ai_result.get("watch_points", [])
            if watch_points:
                st.warning(
                    "### チェックポイント\n\n"
                    + "\n".join(f"- {item}" for item in watch_points)
                )

            st.caption(
                "AI解説はこの画面の価格トレンドとAtlas Scoreデータを整理したものです。投資助言や将来予測ではありません。"
            )

        st.info("### 比較の見方\n\n- 短期だけで判断せず、1か月〜1年の流れを合わせて確認します。\n\n- Atlas Scoreは現在の価格トレンドを整理する学習・監視指標で、企業価値や将来の利益を保証するものではありません。")


# ------------------------------
# お気に入り
# ------------------------------
with tabs[4]:
    _section_intro("WATCHLIST", "ウォッチリスト", "気になる銘柄を保存して、値動きやAtlas Scoreをまとめて確認できます。")

    with st.expander("ウォッチリストを編集"):
        current_favorite_names = [
            name for ticker, name, *_ in COMPANIES
            if ticker in st.session_state.favorites
        ]
        edited_favorite_names = st.multiselect(
            "ウォッチリストの企業",
            options=[row[1] for row in COMPANIES],
            default=current_favorite_names,
            key=f"favorites_editor_names_{st.session_state.favorites_editor_version}",
        )
        if st.button("ウォッチリストを更新", use_container_width=True, key="favorites_editor_apply"):
            name_to_ticker = {row[1]: row[0] for row in COMPANIES}
            st.session_state.favorites = {name_to_ticker[name] for name in edited_favorite_names}
            st.session_state.favorites_editor_version += 1
            st.rerun()

    favdf = df[df["Ticker"].isin(st.session_state.favorites)].copy()

    if favdf.empty:
        st.info("個別分析から追加するか、上の「ウォッチリストを編集」から企業を選んでください。")
    else:
        fm1, fm2, fm3 = st.columns(3)
        fm1.metric("保存銘柄", f"{len(favdf)}")
        fm2.metric("平均Score", f"{favdf['Atlas Score'].mean():.1f}")
        fav_1m_mean = favdf["1か月"].mean() * 100 if favdf["1か月"].notna().any() else float("nan")
        fm3.metric("平均1か月", "-" if pd.isna(fav_1m_mean) else f"{fav_1m_mean:+.2f}%")

        favorite_cards = []
        for _, fav_row in favdf.iterrows():
            price = (
                f"¥{float(fav_row['円換算価格']):,.0f}"
                if pd.notna(fav_row["円換算価格"])
                else "-"
            )
            favorite_cards.append(
                '<div class="mobile-detail-card">'
                '<div class="mobile-detail-head">'
                '<div>'
                f'<div class="mobile-detail-company">#{int(fav_row["順位"])} {html.escape(str(fav_row["会社名"]))}</div>'
                f'<div class="mobile-detail-meta">{html.escape(_country_en(fav_row["国"]))} | {html.escape(_sector_en(fav_row["業種"]))}</div>'
                '</div>'
                f'<div class="mobile-detail-score">Score {float(fav_row["Atlas Score"]):.1f}</div>'
                '</div>'
                '<div class="mobile-detail-grid">'
                f'<div class="mobile-detail-item"><div class="mobile-detail-label">円換算価格</div><div class="mobile-detail-value">{price}</div></div>'
                f'<div class="mobile-detail-item"><div class="mobile-detail-label">1か月</div><div class="mobile-detail-value">{_pct_text(fav_row["1か月"])}</div></div>'
                f'<div class="mobile-detail-item"><div class="mobile-detail-label">3か月</div><div class="mobile-detail-value">{_pct_text(fav_row["3か月"])}</div></div>'
                f'<div class="mobile-detail-item"><div class="mobile-detail-label">6か月</div><div class="mobile-detail-value">{_pct_text(fav_row["6か月"])}</div></div>'
                f'<div class="mobile-detail-item"><div class="mobile-detail-label">1年</div><div class="mobile-detail-value">{_pct_text(fav_row["1年"])}</div></div>'
                '</div>'
                f'<div class="mobile-detail-judge signal-{_status_tone(fav_row["判定"])}">{html.escape(_signal_en(fav_row["判定"]))}</div>'
                '</div>'
            )

        st.markdown(
            '<div class="atlas-card-grid">' + "".join(favorite_cards) + '</div>',
            unsafe_allow_html=True,
        )

        with st.expander("表で見る"):
            favshow = favdf[
                [
                    "順位", "会社名", "国", "円換算価格",
                    "1か月", "3か月", "6か月", "1年",
                    "Atlas Score", "判定",
                ]
            ].copy()
            for col in ["1か月", "3か月", "6か月", "1年"]:
                favshow[col] = (favshow[col] * 100).round(2)
            st.dataframe(
                _ui_frame(favshow),
                use_container_width=True,
                hide_index=True,
                column_config={
                    "円換算価格": st.column_config.NumberColumn(format="¥%.0f"),
                    "1か月": st.column_config.NumberColumn(format="%.2f%%"),
                    "3か月": st.column_config.NumberColumn(format="%.2f%%"),
                    "6か月": st.column_config.NumberColumn(format="%.2f%%"),
                    "1年": st.column_config.NumberColumn(format="%.2f%%"),
                    "Atlas Score": st.column_config.ProgressColumn(min_value=0, max_value=100, format="%.1f"),
                },
            )


# ------------------------------
# 保有株
# ------------------------------
with tabs[5]:
    _section_intro("PORTFOLIO", "保有株", "保有銘柄・株数・平均取得単価を入力すると、現在の評価額と損益を確認できます。")
    st.caption("株数と平均取得単価を入力してください。外国株は現在の為替で円換算するため、評価額は目安です。")

    if st.session_state.portfolio_csv_flash:
        st.success(st.session_state.portfolio_csv_flash)
        st.session_state.portfolio_csv_flash = None

    edited = st.data_editor(
        st.session_state.portfolio,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "Ticker": st.column_config.SelectboxColumn(
                options=[x[0] for x in COMPANIES],
                required=True,
            ),
            "株数": st.column_config.NumberColumn("株数", min_value=0.0, step=0.01),
            "平均取得単価": st.column_config.NumberColumn("平均取得単価（現地通貨）", min_value=0.0, step=0.01),
        },
        key=f"portfolio_editor_{st.session_state.portfolio_editor_version}",
    )

    st.session_state.portfolio = edited

    calc = []
    skipped_portfolio = []

    for _, p in edited.dropna(subset=["Ticker"]).iterrows():
        rr = df[df["Ticker"] == p["Ticker"]]
        if rr.empty:
            continue

        rr = rr.iloc[0]
        qty = pd.to_numeric(pd.Series([p.get("株数")]), errors="coerce").iloc[0]
        avg = pd.to_numeric(pd.Series([p.get("平均取得単価")]), errors="coerce").iloc[0]

        if pd.isna(qty) or pd.isna(avg):
            continue

        qty = float(qty)
        avg = float(avg)
        if qty <= 0 or avg <= 0:
            continue

        if pd.isna(rr["円換算価格"]):
            skipped_portfolio.append(rr["会社名"])
            continue

        if rr["通貨"] == "JPY":
            fxr = 1.0
        elif pd.notna(rr["FX→JPY"]):
            fxr = float(rr["FX→JPY"])
        else:
            skipped_portfolio.append(rr["会社名"])
            continue

        invested = qty * avg * fxr
        current = qty * float(rr["円換算価格"])
        pnl = current - invested

        calc.append([
            p["Ticker"], rr["会社名"], qty, invested, current, pnl,
            (pnl / invested if invested else 0), rr["Atlas Score"], rr["判定"],
        ])

    if skipped_portfolio:
        st.warning("為替または円換算価格を取得できず、計算できない保有株があります: " + ", ".join(dict.fromkeys(skipped_portfolio)))

    if calc:
        pf = pd.DataFrame(
            calc,
            columns=[
                "Ticker", "会社名", "株数", "投資額(円)", "評価額(円)",
                "損益(円)", "損益率", "Score", "判定",
            ],
        )

        st.markdown("### 保有状況サマリー")
        total_invested = pf["投資額(円)"].sum()
        total_current = pf["評価額(円)"].sum()
        total_pnl = pf["損益(円)"].sum()
        total_pnl_rate = total_pnl / total_invested * 100 if total_invested else 0

        p1, p2, p3 = st.columns(3)
        p1.metric("投資額", f"¥{total_invested:,.0f}")
        p2.metric("評価額", f"¥{total_current:,.0f}")
        p3.metric("損益", f"¥{total_pnl:,.0f}", delta=f"{total_pnl_rate:+.2f}%")

        if len(pf) >= 2:
            st.markdown("### 保有比率")
            allocation = (
                pf.groupby("会社名", as_index=False)["評価額(円)"]
                .sum()
                .sort_values("評価額(円)", ascending=False)
                .rename(columns={"会社名": "会社", "評価額(円)": "評価額(円)"})
            )
            allocation_chart = (
                alt.Chart(allocation)
                .mark_bar(cornerRadiusEnd=4)
                .encode(
                    y=alt.Y("会社:N", sort="-x", title=None),
                    x=alt.X("評価額(円):Q", title="評価額(円)"),
                    tooltip=[
                        alt.Tooltip("会社:N", title="会社"),
                        alt.Tooltip("評価額(円):Q", title="評価額", format=",.0f"),
                    ],
                )
                .properties(height=max(160, min(360, len(allocation) * 34)))
            )
            st.altair_chart(allocation_chart, use_container_width=True)
            st.caption("保有比率は現在の円換算評価額をもとに表示しています。資産配分を推奨するものではありません。")

        portfolio_cards = []
        for _, pf_row in pf.iterrows():
            pnl_rate_text = f"{float(pf_row['損益率']) * 100:+.2f}%"
            portfolio_cards.append(
                '<div class="mobile-detail-card">'
                '<div class="mobile-detail-head">'
                '<div>'
                f'<div class="mobile-detail-company">{html.escape(str(pf_row["会社名"]))}</div>'
                f'<div class="mobile-detail-meta">{html.escape(str(pf_row["Ticker"]))} | {float(pf_row["株数"]):g}株</div>'
                '</div>'
                f'<div class="mobile-detail-score">Score {float(pf_row["Score"]):.1f}</div>'
                '</div>'
                '<div class="mobile-detail-grid">'
                f'<div class="mobile-detail-item"><div class="mobile-detail-label">投資額</div><div class="mobile-detail-value">¥{float(pf_row["投資額(円)"]):,.0f}</div></div>'
                f'<div class="mobile-detail-item"><div class="mobile-detail-label">評価額</div><div class="mobile-detail-value">¥{float(pf_row["評価額(円)"]):,.0f}</div></div>'
                f'<div class="mobile-detail-item"><div class="mobile-detail-label">損益</div><div class="mobile-detail-value">¥{float(pf_row["損益(円)"]):+,.0f}</div></div>'
                f'<div class="mobile-detail-item"><div class="mobile-detail-label">損益率</div><div class="mobile-detail-value">{pnl_rate_text}</div></div>'
                '</div>'
                f'<div class="mobile-detail-judge signal-{_status_tone(pf_row["判定"])}">{html.escape(_signal_en(pf_row["判定"]))}</div>'
                '</div>'
            )

        st.markdown(
            '<div class="atlas-card-grid">' + "".join(portfolio_cards) + '</div>',
            unsafe_allow_html=True,
        )

        with st.expander("詳細を表で見る"):
            pf_display = pf.copy()
            pf_display["損益率"] = (pf_display["損益率"] * 100).round(2)
            st.dataframe(
                _ui_frame(pf_display),
                use_container_width=True,
                hide_index=True,
                column_config={
                    "投資額(円)": st.column_config.NumberColumn(format="¥%.0f"),
                    "評価額(円)": st.column_config.NumberColumn(format="¥%.0f"),
                    "損益(円)": st.column_config.NumberColumn(format="¥%.0f"),
                    "損益率": st.column_config.NumberColumn(format="%.2f%%"),
                },
            )
    elif not edited.dropna(subset=["Ticker"]).empty:
        st.caption("株数と平均取得単価の両方を入力すると、評価額と損益を計算します。")

    csv_export = edited.rename(
        columns={"株数": "Shares", "平均取得単価": "Avg Cost"}
    )
    csv = csv_export.to_csv(index=False).encode("utf-8-sig")
    st.download_button("保有株CSVを保存", csv, "atlas50_portfolio.csv", "text/csv")

    upl = st.file_uploader("保有株CSVを読み込む", type=["csv"], key="pfupload")
    if upl is not None:
        try:
            csv_bytes = upl.getvalue()
            csv_digest = hashlib.sha256(csv_bytes).hexdigest()
            if csv_digest != st.session_state.portfolio_csv_digest:
                loaded = pd.read_csv(io.BytesIO(csv_bytes))

                # Accept both the V3.1 English export and older ATLAS CSV files.
                if {"Ticker", "Shares", "Avg Cost"}.issubset(loaded.columns):
                    loaded = loaded.rename(
                        columns={"Shares": "株数", "Avg Cost": "平均取得単価"}
                    )
                elif not {"Ticker", "株数", "平均取得単価"}.issubset(loaded.columns):
                    raise ValueError("必要な保有株列が不足しています")

                valid_tickers = {row[0] for row in COMPANIES}
                loaded = loaded[["Ticker", "株数", "平均取得単価"]].copy()
                loaded = loaded[loaded["Ticker"].astype(str).isin(valid_tickers)].reset_index(drop=True)
                st.session_state.portfolio = loaded
                st.session_state.portfolio_csv_digest = csv_digest
                st.session_state.portfolio_editor_version += 1
                st.session_state.portfolio_csv_flash = "保有株CSVを読み込みました。"
                st.rerun()
        except Exception:
            st.error("CSVを読み込めませんでした。")


# ------------------------------
# 月予算
# ------------------------------
with tabs[6]:
    _section_intro("AFFORDABILITY", "予算で探す", "投資予算を入力すると、その金額で1株以上買える企業を確認できます。")
    budget = st.number_input(
        "投資予算（円）",
        min_value=0,
        value=MONTHLY_BUDGET_DEFAULT,
        step=1000,
    )

    buyable = df[(df["円換算価格"].notna()) & (df["円換算価格"] <= budget)].copy()
    st.metric("予算内で1株買える企業", f"{len(buyable)}")
    st.caption("これは「予算内で1株買えるか」を確認する機能で、投資推奨ではありません。")

    if not buyable.empty:
        buyable["予算で買える株数"] = buyable["円換算価格"].apply(
            lambda x: int(budget // x) if pd.notna(x) and x > 0 else 0
        )
        buyable = buyable.sort_values(["Atlas Score", "円換算価格"], ascending=[False, True])

        budget_cards = []
        for _, budget_row in buyable.iterrows():
            budget_cards.append(
                '<div class="mobile-detail-card">'
                '<div class="mobile-detail-head">'
                '<div>'
                f'<div class="mobile-detail-company">#{int(budget_row["順位"])} {html.escape(str(budget_row["会社名"]))}</div>'
                f'<div class="mobile-detail-meta">{html.escape(_country_en(budget_row["国"]))} | {html.escape(_sector_en(budget_row["業種"]))}</div>'
                '</div>'
                f'<div class="mobile-detail-score">Score {float(budget_row["Atlas Score"]):.1f}</div>'
                '</div>'
                '<div class="mobile-detail-grid">'
                f'<div class="mobile-detail-item"><div class="mobile-detail-label">1株の目安</div><div class="mobile-detail-value">¥{float(budget_row["円換算価格"]):,.0f}</div></div>'
                f'<div class="mobile-detail-item"><div class="mobile-detail-label">予算内株数</div><div class="mobile-detail-value">{int(budget_row["予算で買える株数"])}</div></div>'
                '</div>'
                f'<div class="mobile-detail-judge signal-{_status_tone(budget_row["判定"])}">{html.escape(_signal_en(budget_row["判定"]))}</div>'
                '</div>'
            )

        st.markdown(
            '<div class="atlas-card-grid">' + "".join(budget_cards) + '</div>',
            unsafe_allow_html=True,
        )

        with st.expander("表で見る"):
            st.dataframe(
                _ui_frame(buyable[[
                    "順位", "会社名", "国", "業種", "円換算価格",
                    "予算で買える株数", "Atlas Score", "判定",
                ]]),
                use_container_width=True,
                hide_index=True,
                column_config={
                    "円換算価格": st.column_config.NumberColumn(format="¥%.0f"),
                    "Atlas Score": st.column_config.ProgressColumn(min_value=0, max_value=100, format="%.1f"),
                },
            )
    else:
        st.info("現在の予算で1株買える銘柄はありません。")


# ------------------------------
# 条件で探す
# ------------------------------
with tabs[7]:
    _section_intro("SCREENER", "条件で探す", "Score・騰落率・出来高・地域・移動平均線など、自分の条件で50銘柄を絞り込めます。")

    if st.session_state.watch_filter_flash:
        st.success(st.session_state.watch_filter_flash)
        st.session_state.watch_filter_flash = None

    st.markdown("### 保存した条件")
    st.caption("保存した条件をワンタップで呼び出せます。ATLAS全体の設定は画面下部からJSONでバックアップできます。")

    saved_names = sorted(st.session_state.saved_watch_filters.keys())
    if saved_names:
        saved_select_col, saved_apply_col, saved_delete_col = st.columns([3, 1, 1])
        selected_saved_filter = saved_select_col.selectbox(
            "保存した条件",
            saved_names,
            key="saved_watch_filter_select",
            label_visibility="collapsed",
        )
        if saved_apply_col.button("呼び出す", use_container_width=True, key="saved_watch_filter_apply"):
            _apply_watch_config(st.session_state.saved_watch_filters[selected_saved_filter])
            st.rerun()
        if saved_delete_col.button("削除", use_container_width=True, key="saved_watch_filter_delete"):
            st.session_state.saved_watch_filters.pop(selected_saved_filter, None)
            st.rerun()

        selected_config = st.session_state.saved_watch_filters.get(selected_saved_filter, {})
        st.markdown(
            '<div class="saved-filter-card">'
            f'<div class="saved-filter-name">{html.escape(str(selected_saved_filter))}</div>'
            f'<div class="saved-filter-summary">{html.escape(_watch_config_summary(selected_config))}</div>'
            '</div>',
            unsafe_allow_html=True,
        )
    else:
        st.caption("保存した条件はまだありません。下で条件を作って保存できます。")

    st.divider()
    st.markdown("### 条件プリセット")
    st.caption("まずプリセットを選び、そのあと数値を自由に調整できます。")

    preset1, preset2, preset3, preset4 = st.columns(4)

    if preset1.button("上向き確認", use_container_width=True, key="watch_preset_up"):
        st.session_state.watch_score = 60.0
        st.session_state.watch_1m = 0.0
        st.session_state.watch_3m = 0.0
        st.session_state.watch_volume = 0.0
        st.session_state.watch_sma20 = True
        st.session_state.watch_sma60 = False

    if preset2.button("中期トレンド", use_container_width=True, key="watch_preset_mid"):
        st.session_state.watch_score = 60.0
        st.session_state.watch_1m = 0.0
        st.session_state.watch_3m = 5.0
        st.session_state.watch_volume = 0.0
        st.session_state.watch_sma20 = True
        st.session_state.watch_sma60 = True

    if preset3.button("出来高注目", use_container_width=True, key="watch_preset_volume"):
        st.session_state.watch_score = 0.0
        st.session_state.watch_1m = -100.0
        st.session_state.watch_3m = -100.0
        st.session_state.watch_volume = 1.5
        st.session_state.watch_sma20 = False
        st.session_state.watch_sma60 = False

    if preset4.button("リセット", use_container_width=True, key="watch_preset_reset"):
        st.session_state.watch_score = 0.0
        st.session_state.watch_1m = -100.0
        st.session_state.watch_3m = -100.0
        st.session_state.watch_volume = 0.0
        st.session_state.watch_sma20 = False
        st.session_state.watch_sma60 = False
        st.session_state.watch_region = "すべて"
        st.session_state.watch_sector_group = "すべて"
        st.session_state.watch_limit = 12

    w1, w2, w3 = st.columns(3)
    min_watch_score = w1.slider(
        "最低Atlas Score",
        min_value=0.0,
        max_value=100.0,
        step=1.0,
        key="watch_score",
    )
    min_watch_1m = w2.slider(
        "1か月騰落率の下限",
        min_value=-100.0,
        max_value=100.0,
        step=1.0,
        format="%.0f%%",
        key="watch_1m",
    )
    min_watch_3m = w3.slider(
        "3か月騰落率の下限",
        min_value=-100.0,
        max_value=200.0,
        step=1.0,
        format="%.0f%%",
        key="watch_3m",
    )

    w4, w5, w6 = st.columns(3)
    min_watch_volume = w4.number_input(
        "最低出来高倍率",
        min_value=0.0,
        max_value=10.0,
        step=0.1,
        help="現在の出来高 ÷ 20日平均出来高です。1.5なら直近平均の約1.5倍です。",
        key="watch_volume",
    )

    region_options = ["すべて"] + sorted(df["地域"].dropna().astype(str).unique().tolist())
    current_watch_region = st.session_state.get("watch_region", "すべて")
    if current_watch_region not in region_options:
        st.session_state.watch_region = "すべて"
    watch_region = w5.selectbox(
        "地域",
        region_options,
        key="watch_region",
        format_func=lambda x: "すべて" if x == "すべて" else _region_en(x),
    )

    watch_sector_series = df["業種"].map(SECTOR_GROUPS).fillna(df["業種"])
    sector_group_options = ["すべて"] + sorted(watch_sector_series.dropna().astype(str).unique().tolist())
    current_watch_sector = st.session_state.get("watch_sector_group", "すべて")
    if current_watch_sector not in sector_group_options:
        st.session_state.watch_sector_group = "すべて"
    watch_sector_group = w6.selectbox(
        "業種グループ",
        sector_group_options,
        key="watch_sector_group",
        format_func=lambda x: "すべて" if x == "すべて" else _sector_group_en(x),
    )

    t1, t2 = st.columns(2)
    only_above_sma20 = t1.toggle(
        "20日線より上だけ",
        key="watch_sma20",
    )
    only_above_sma60 = t2.toggle(
        "60日線より上だけ",
        key="watch_sma60",
    )

    sort_label = st.selectbox(
        "並び順",
        WATCH_SORT_OPTIONS,
        key="watch_sort",
        format_func=lambda x: WATCH_SORT_EN.get(x, x),
    )

    watch_limit = st.selectbox(
        "表示件数",
        [12, 24, 50],
        key="watch_limit",
        help="画面に表示する一致銘柄の件数を選びます。",
    )

    save_name_col, save_button_col = st.columns([3, 1])
    watch_save_name = save_name_col.text_input(
        "この条件に名前を付ける",
        placeholder="例：出来高＋上向き",
        key="watch_save_name",
    ).strip()
    if save_button_col.button("条件を保存", use_container_width=True, key="watch_save_button"):
        if not watch_save_name:
            st.warning("保存する条件名を入力してください。")
        else:
            saved_name = watch_save_name[:40]
            st.session_state.saved_watch_filters[saved_name] = _watch_config_from_state()
            st.session_state.watch_filter_flash = f"保存しました: {saved_name}"
            st.rerun()

    watch_df = df.copy()
    watch_df["業種グループ"] = watch_df["業種"].map(SECTOR_GROUPS).fillna(watch_df["業種"])

    watch_df = watch_df[watch_df["Atlas Score"].fillna(-1) >= min_watch_score]
    watch_df = watch_df[(watch_df["1か月"].fillna(-999) * 100) >= min_watch_1m]
    watch_df = watch_df[(watch_df["3か月"].fillna(-999) * 100) >= min_watch_3m]
    watch_df = watch_df[watch_df["出来高倍率"].fillna(-1) >= min_watch_volume]

    if watch_region != "すべて":
        watch_df = watch_df[watch_df["地域"].astype(str) == watch_region]
    if watch_sector_group != "すべて":
        watch_df = watch_df[watch_df["業種グループ"].astype(str) == watch_sector_group]
    if only_above_sma20:
        watch_df = watch_df[watch_df["20日線比"].fillna(-999) > 0]
    if only_above_sma60:
        watch_df = watch_df[watch_df["60日線比"].fillna(-999) > 0]

    sort_map = {
        "Atlas Scoreが高い順": "Atlas Score",
        "1か月上昇率が高い順": "1か月",
        "3か月上昇率が高い順": "3か月",
        "出来高倍率が高い順": "出来高倍率",
    }
    watch_df = watch_df.sort_values(sort_map[sort_label], ascending=False).copy()
    watch_display_df = watch_df.head(int(watch_limit)).copy()

    active_conditions = [f"Score ≥ {min_watch_score:.0f}"]
    if min_watch_1m > -100:
        active_conditions.append(f"1か月 ≥ {min_watch_1m:+.0f}%")
    if min_watch_3m > -100:
        active_conditions.append(f"3か月 ≥ {min_watch_3m:+.0f}%")
    if min_watch_volume > 0:
        active_conditions.append(f"出来高 ≥ {min_watch_volume:.1f}x")
    if watch_region != "すべて":
        active_conditions.append(f"地域: {_region_en(watch_region)}")
    if watch_sector_group != "すべて":
        active_conditions.append(f"業種: {_sector_group_en(watch_sector_group)}")
    if only_above_sma20:
        active_conditions.append("20日線より上")
    if only_above_sma60:
        active_conditions.append("60日線より上")

    st.info("**現在の条件**  " + " | ".join(active_conditions))

    r1, r2, r3, r4 = st.columns(4)
    r1.metric("条件一致", f"{len(watch_df)}")
    if not watch_df.empty:
        r2.metric("平均Score", f"{watch_df['Atlas Score'].mean():.1f}")
        r3.metric("平均1か月", f"{watch_df['1か月'].mean() * 100:+.2f}%")
        r4.metric("最大出来高倍率", f"{watch_df['出来高倍率'].max():.2f}x")
    else:
        r2.metric("平均Score", "-")
        r3.metric("平均1か月", "-")
        r4.metric("最大出来高倍率", "-")

    if watch_df.empty:
        st.warning("現在の条件に一致する銘柄はありません。条件を少し緩めてみてください。")
    else:
        st.caption(f"表示中: {len(watch_display_df)} / {len(watch_df)}社")

        watch_cards = []
        for _, watch_row in watch_display_df.iterrows():
            one_month_text = _pct_text(watch_row["1か月"])
            three_month_text = _pct_text(watch_row["3か月"])
            volume_text = f"{float(watch_row['出来高倍率']):.2f}x" if pd.notna(watch_row["出来高倍率"]) else "-"
            sma20_text = _pct_text(watch_row["20日線比"])

            watch_cards.append(
                '<div class="mobile-detail-card">'
                '<div class="mobile-detail-head">'
                '<div>'
                f'<div class="mobile-detail-company">#{int(watch_row["順位"])} {html.escape(str(watch_row["会社名"]))}</div>'
                f'<div class="mobile-detail-meta">{html.escape(_country_en(watch_row["国"]))} | {html.escape(_sector_group_en(watch_row["業種グループ"]))}</div>'
                '</div>'
                f'<div class="mobile-detail-score">Score {float(watch_row["Atlas Score"]):.1f}</div>'
                '</div>'
                '<div class="mobile-detail-grid">'
                f'<div class="mobile-detail-item"><div class="mobile-detail-label">1か月</div><div class="mobile-detail-value">{one_month_text}</div></div>'
                f'<div class="mobile-detail-item"><div class="mobile-detail-label">3か月</div><div class="mobile-detail-value">{three_month_text}</div></div>'
                f'<div class="mobile-detail-item"><div class="mobile-detail-label">出来高倍率</div><div class="mobile-detail-value">{volume_text}</div></div>'
                f'<div class="mobile-detail-item"><div class="mobile-detail-label">20日線比</div><div class="mobile-detail-value">{sma20_text}</div></div>'
                '</div>'
                f'<div class="mobile-detail-judge signal-{_status_tone(watch_row["判定"])}">判定: {html.escape(_signal_en(watch_row["判定"]))}</div>'
                '</div>'
            )

        st.markdown(
            '<div class="atlas-card-grid">' + "".join(watch_cards) + '</div>',
            unsafe_allow_html=True,
        )

        with st.expander("条件一致銘柄を表で見る"):
            watch_table = watch_df[[
                "順位", "会社名", "国", "業種グループ", "1か月", "3か月",
                "出来高倍率", "20日線比", "60日線比", "Atlas Score", "判定",
            ]].copy()
            for pct_col in ["1か月", "3か月", "20日線比", "60日線比"]:
                watch_table[pct_col] = (watch_table[pct_col] * 100).round(2)

            st.dataframe(
                _ui_frame(watch_table),
                use_container_width=True,
                hide_index=True,
                column_config={
                    "1か月": st.column_config.NumberColumn(format="%.2f%%"),
                    "3か月": st.column_config.NumberColumn(format="%.2f%%"),
                    "出来高倍率": st.column_config.NumberColumn(format="%.2fx"),
                    "20日線比": st.column_config.NumberColumn(format="%.2f%%"),
                    "60日線比": st.column_config.NumberColumn(format="%.2f%%"),
                    "Atlas Score": st.column_config.ProgressColumn(min_value=0, max_value=100, format="%.1f"),
                },
            )

    st.caption(
        "条件検索はATLAS 50内の現在データを機械的に絞り込む観察ツールです。条件一致は将来の上昇や投資成果を意味しません。"
    )


# ------------------------------
# Atlas設定の保存
# ------------------------------
with st.expander("ATLAS設定をバックアップ"):
    st.caption("ウォッチリスト・保有株・保存条件・現在の検索条件を1つのJSONファイルに保存できます。")
    st.download_button(
        "ATLAS設定JSONを保存",
        data=_settings_json_bytes(),
        file_name="atlas50_settings.json",
        mime="application/json",
        use_container_width=True,
        key="atlas_setup_download_global",
    )
    st.caption("保有株だけを保存する場合は、保有株タブのCSVも利用できます。")

# ------------------------------
# エラー・注意書き
# ------------------------------
if errors:
    with st.expander("データ取得エラー"):
        st.code("\n".join(errors[:50]))

st.divider()
st.caption(
    f"ATLAS 50 V{APP_VERSION} {APP_LABEL} | "
    "Atlas Scoreは価格トレンドを整理するための学習・監視指標です。買い推奨・売り推奨・将来の利益保証ではありません。株価・為替・ニュースには遅延や取得失敗があり、AI解説とあわせて元データも確認してください。"
)

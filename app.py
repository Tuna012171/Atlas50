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


st.set_page_config(page_title="Atlas 50", page_icon="🌍", layout="wide")

APP_VERSION = "3.0"
APP_LABEL = "Complete"
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
# 見た目
# ------------------------------
st.markdown(
    """
<style>
.block-container {
    padding-top: 1.3rem;
    padding-bottom: 3rem;
}

div[data-testid="stMetric"] {
    border: 1px solid rgba(120, 120, 120, 0.20);
    border-radius: 14px;
    padding: 12px 14px;
}

.atlas-title {
    font-size: 3rem;
    font-weight: 900;
    letter-spacing: -0.055em;
    line-height: 1.05;
    margin-bottom: 10px;
}

.atlas-title::after {
    content: "";
    display: block;
    width: 58px;
    height: 4px;
    margin-top: 12px;
    border-radius: 999px;
    background: #ff4b4b;
}

.atlas-sub {
    font-size: 1.02rem;
    font-weight: 500;
    opacity: 0.62;
    margin-top: 0;
    margin-bottom: 26px;
    letter-spacing: 0.01em;
}

.badge {
    display: inline-block;
    padding: 4px 9px;
    border-radius: 999px;
    font-size: 0.85rem;
    border: 1px solid rgba(120, 120, 120, 0.25);
}

/*
スマホ専用UIはStreamlitコンテナ単位で切り替える。
HTML要素だけを隠す方式より、不要な空白が残りにくい。
*/
.mobile-list-wrap {
    display: none;
}

.st-key-compare_mobile {
    display: none;
}

.st-key-pulse_region_mobile,
.st-key-favorite_mobile,
.st-key-portfolio_mobile,
.st-key-budget_mobile {
    display: none !important;
}


.atlas-card-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 10px;
    align-items: stretch;
}

.atlas-card-grid .mobile-detail-card {
    margin-bottom: 0;
    height: 100%;
}

.mobile-detail-card {
    border: 1px solid rgba(120, 120, 120, 0.20);
    border-radius: 14px;
    padding: 14px;
    margin-bottom: 10px;
}

.mobile-detail-head {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 10px;
}

.mobile-detail-company {
    font-size: 1.05rem;
    font-weight: 750;
}

.mobile-detail-meta {
    margin-top: 2px;
    font-size: 0.80rem;
    opacity: 0.68;
}

.mobile-detail-score {
    font-size: 0.95rem;
    font-weight: 750;
    white-space: nowrap;
}

.mobile-detail-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 8px 10px;
    margin-top: 11px;
}

.mobile-detail-item {
    padding: 8px 9px;
    border-radius: 10px;
    background: rgba(120, 120, 120, 0.06);
}

.mobile-detail-label {
    font-size: 0.72rem;
    opacity: 0.64;
}

.mobile-detail-value {
    margin-top: 1px;
    font-size: 0.90rem;
    font-weight: 650;
    overflow-wrap: anywhere;
}

.mobile-detail-judge {
    display: inline-block;
    margin-top: 10px;
    padding: 3px 8px;
    border-radius: 999px;
    border: 1px solid rgba(120, 120, 120, 0.25);
    font-size: 0.8rem;
}

.pulse-region-card {
    border: 1px solid rgba(120, 120, 120, 0.20);
    border-radius: 14px;
    padding: 13px 14px;
    margin-bottom: 10px;
}

.pulse-region-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 10px;
}

.pulse-region-name {
    font-size: 1rem;
    font-weight: 750;
}

.pulse-region-count {
    font-size: 0.78rem;
    opacity: 0.65;
    white-space: nowrap;
}

.pulse-region-score {
    margin-top: 9px;
    font-size: 0.92rem;
    font-weight: 700;
}

.pulse-region-stats {
    margin-top: 7px;
    font-size: 0.86rem;
    line-height: 1.55;
}

.compare-card {
    border: 1px solid rgba(120, 120, 120, 0.20);
    border-radius: 14px;
    padding: 14px;
    margin-bottom: 10px;
}

.compare-card-head {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 10px;
}

.compare-card-company {
    font-size: 1.05rem;
    font-weight: 750;
}

.compare-card-meta {
    font-size: 0.82rem;
    opacity: 0.68;
    margin-top: 2px;
}

.compare-card-score {
    font-size: 1rem;
    font-weight: 750;
    white-space: nowrap;
}

.compare-card-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 8px 12px;
    margin-top: 12px;
}

.compare-card-item {
    padding: 8px 10px;
    border-radius: 10px;
    background: rgba(120, 120, 120, 0.06);
}

.compare-card-label {
    font-size: 0.74rem;
    opacity: 0.64;
}

.compare-card-value {
    font-size: 0.92rem;
    font-weight: 650;
    margin-top: 1px;
}

.compare-card-judge {
    display: inline-block;
    margin-top: 10px;
    padding: 3px 8px;
    border-radius: 999px;
    border: 1px solid rgba(120, 120, 120, 0.25);
    font-size: 0.8rem;
}


.sector-spotlight-grid {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 12px;
    margin: 10px 0 12px 0;
}

.sector-spotlight-card {
    border: 1px solid rgba(120, 120, 120, 0.20);
    border-radius: 14px;
    padding: 13px 14px;
    min-width: 0;
}

.sector-spotlight-label {
    font-size: 0.76rem;
    opacity: 0.62;
}

.sector-spotlight-value {
    margin-top: 5px;
    font-size: 1rem;
    font-weight: 800;
    overflow-wrap: anywhere;
}

.sector-spotlight-meta {
    margin-top: 4px;
    font-size: 0.78rem;
    opacity: 0.66;
    line-height: 1.45;
}


.sector-heatmap-desktop {
    display: grid;
    grid-template-columns: minmax(180px, 1.25fr) repeat(4, minmax(110px, 1fr));
    gap: 7px;
    margin-top: 14px;
    margin-bottom: 8px;
}

.sector-heatmap-header {
    padding: 8px 10px;
    font-size: 0.76rem;
    font-weight: 750;
    opacity: 0.66;
}

.sector-heatmap-sector {
    border: 1px solid rgba(120, 120, 120, 0.18);
    border-radius: 11px;
    padding: 10px 11px;
    min-width: 0;
}

.sector-heatmap-sector-name {
    font-size: 0.90rem;
    font-weight: 800;
    overflow-wrap: anywhere;
}

.sector-heatmap-sector-meta {
    margin-top: 3px;
    font-size: 0.72rem;
    opacity: 0.62;
    line-height: 1.4;
}

.sector-heatmap-cell {
    border: 1px solid rgba(120, 120, 120, 0.16);
    border-radius: 11px;
    min-height: 58px;
    padding: 9px 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    text-align: center;
}

.sector-heatmap-cell-value {
    font-size: 0.94rem;
    font-weight: 800;
}

.sector-heatmap-mobile {
    display: none;
}

.sector-heatmap-mobile-card {
    border: 1px solid rgba(120, 120, 120, 0.20);
    border-radius: 14px;
    padding: 13px;
    margin-bottom: 10px;
}

.sector-heatmap-mobile-head {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 10px;
}

.sector-heatmap-mobile-name {
    font-size: 1rem;
    font-weight: 800;
    overflow-wrap: anywhere;
}

.sector-heatmap-mobile-meta {
    font-size: 0.74rem;
    opacity: 0.62;
    white-space: nowrap;
}

.sector-heatmap-mobile-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 8px;
    margin-top: 10px;
}

.sector-heatmap-mobile-tile {
    border: 1px solid rgba(120, 120, 120, 0.16);
    border-radius: 10px;
    padding: 9px 10px;
    min-width: 0;
}

.sector-heatmap-mobile-label {
    font-size: 0.71rem;
    opacity: 0.64;
}

.sector-heatmap-mobile-value {
    margin-top: 2px;
    font-size: 0.92rem;
    font-weight: 800;
}

.home-top10-mobile {
    display: none;
}

.home-top10-card {
    border: 1px solid rgba(120, 120, 120, 0.20);
    border-radius: 14px;
    padding: 13px 14px;
    margin-bottom: 10px;
}

.home-top10-head {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 10px;
}

.home-top10-rank {
    font-size: 0.76rem;
    opacity: 0.62;
}

.home-top10-company {
    margin-top: 2px;
    font-size: 1.04rem;
    font-weight: 800;
    overflow-wrap: anywhere;
}

.home-top10-country {
    margin-top: 2px;
    font-size: 0.78rem;
    opacity: 0.66;
}

.home-top10-score {
    font-size: 0.94rem;
    font-weight: 800;
    white-space: nowrap;
}

.home-top10-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 8px;
    margin-top: 11px;
}

.home-top10-item {
    padding: 8px 9px;
    border-radius: 10px;
    background: rgba(120, 120, 120, 0.06);
}

.home-top10-label {
    font-size: 0.70rem;
    opacity: 0.62;
}

.home-top10-value {
    margin-top: 1px;
    font-size: 0.90rem;
    font-weight: 700;
}

.home-top10-judge {
    display: inline-block;
    margin-top: 10px;
    padding: 3px 8px;
    border-radius: 999px;
    border: 1px solid rgba(120, 120, 120, 0.25);
    font-size: 0.80rem;
}

.atlas-radar-grid {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 12px;
    margin-top: 10px;
    margin-bottom: 8px;
}

.atlas-radar-panel {
    border: 1px solid rgba(120, 120, 120, 0.20);
    border-radius: 14px;
    padding: 14px;
    min-width: 0;
}

.atlas-radar-title {
    font-size: 1rem;
    font-weight: 800;
}

.atlas-radar-sub {
    margin-top: 3px;
    font-size: 0.77rem;
    opacity: 0.62;
    line-height: 1.45;
}

.atlas-radar-item {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 10px;
    padding: 10px 0;
    border-bottom: 1px solid rgba(120, 120, 120, 0.14);
}

.atlas-radar-item:last-child {
    border-bottom: 0;
    padding-bottom: 0;
}

.atlas-radar-company {
    font-size: 0.91rem;
    font-weight: 720;
    overflow-wrap: anywhere;
}

.atlas-radar-meta {
    margin-top: 2px;
    font-size: 0.74rem;
    opacity: 0.63;
    line-height: 1.45;
}

.atlas-radar-value {
    font-size: 0.92rem;
    font-weight: 800;
    white-space: nowrap;
}


.atlas-version-row {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 8px;
    margin-top: -12px;
    margin-bottom: 18px;
}

.atlas-chip {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    padding: 4px 9px;
    border: 1px solid rgba(120, 120, 120, 0.22);
    border-radius: 999px;
    font-size: 0.78rem;
    opacity: 0.78;
}

.atlas-guide-grid {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 10px;
    margin: 8px 0 4px 0;
}

.atlas-guide-card {
    border: 1px solid rgba(120, 120, 120, 0.18);
    border-radius: 12px;
    padding: 11px 12px;
    min-width: 0;
}

.atlas-guide-step {
    font-size: 0.72rem;
    opacity: 0.62;
}

.atlas-guide-title {
    margin-top: 3px;
    font-weight: 800;
    font-size: 0.92rem;
}

.atlas-guide-text {
    margin-top: 3px;
    font-size: 0.78rem;
    line-height: 1.45;
    opacity: 0.75;
}

.data-health-grid {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 8px;
    margin-top: 8px;
}

.data-health-item {
    border: 1px solid rgba(120, 120, 120, 0.18);
    border-radius: 11px;
    padding: 9px 10px;
}

.data-health-label {
    font-size: 0.70rem;
    opacity: 0.62;
}

.data-health-value {
    margin-top: 2px;
    font-size: 0.90rem;
    font-weight: 750;
}

.saved-filter-card {
    border: 1px solid rgba(120, 120, 120, 0.18);
    border-radius: 12px;
    padding: 10px 12px;
    margin-top: 8px;
}

.saved-filter-name {
    font-size: 0.90rem;
    font-weight: 800;
}

.saved-filter-summary {
    margin-top: 3px;
    font-size: 0.76rem;
    opacity: 0.68;
    line-height: 1.45;
}

@media (max-width: 1100px) {
    .atlas-radar-grid,
    .sector-spotlight-grid,
    .atlas-guide-grid,
    .data-health-grid {
        grid-template-columns: 1fr;
    }

    .sector-heatmap-desktop {
        display: none;
    }

    .sector-heatmap-mobile {
        display: block;
    }

    .st-key-home_top10_table {
        display: none !important;
    }

    .home-top10-mobile {
        display: block;
    }

    .mobile-list-wrap {
        display: block;
    }

    .st-key-world50_table,
    .st-key-compare_table,
    .st-key-pulse_region_table,
    .st-key-favorite_table,
    .st-key-portfolio_table,
    .st-key-budget_table {
        display: none !important;
    }

    .st-key-compare_mobile,
    .st-key-pulse_region_mobile,
    .st-key-favorite_mobile,
    .st-key-portfolio_mobile,
    .st-key-budget_mobile {
        display: block !important;
    }

    div[data-testid="stTabs"] div[role="tablist"] {
        overflow-x: auto;
        flex-wrap: nowrap;
        scrollbar-width: none;
    }

    div[data-testid="stTabs"] div[role="tablist"]::-webkit-scrollbar {
        display: none;
    }

    div[data-testid="stTabs"] button[role="tab"] {
        flex: 0 0 auto;
        white-space: nowrap;
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
        padding: 10px;
        border-radius: 12px;
    }

    div[data-testid="stMetricValue"] {
        font-size: 1.35rem;
    }

    div[data-testid="stMetricLabel"] {
        font-size: 0.80rem;
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

    .mobile-stock-card {
        border: 1px solid rgba(120, 120, 120, 0.20);
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
        line-height: 1.55;
    }

    .mobile-judge {
        display: inline-block;
        margin-top: 8px;
        padding: 3px 8px;
        border-radius: 999px;
        border: 1px solid rgba(120, 120, 120, 0.25);
        font-size: 0.8rem;
    }
}
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
    """「なぜ今注目？」用。数値の羅列ではなく、値動きの意味を短く整理する。"""
    reasons = []

    if score >= 80:
        reasons.append("複数の指標が強く、Atlas Score上では現在かなり注目度が高い状態です")
    elif score >= 65:
        reasons.append("複数の指標が比較的良好で、Atlas Score上では注目度が高めです")

    trend_values = [one_month, three_month, six_month, one_year]

    if all(v is not None and v > 0 for v in trend_values):
        reasons.append("短期から長期まで上昇基調がそろっており、幅広い期間で強さが見られます")
    elif (
        one_month is not None
        and three_month is not None
        and six_month is not None
        and one_month > 0
        and three_month > 0
        and six_month > 0
    ):
        reasons.append("直近半年は上向きの流れが続いており、中期的な勢いが見られます")
    elif (
        one_month is not None
        and three_month is not None
        and one_month > 0
        and three_month < 0
    ):
        reasons.append("足元では反発していますが、中期ではまだ回復途中の動きです")
    elif (
        one_month is not None
        and six_month is not None
        and one_year is not None
        and one_month < 0
        and six_month > 0
        and one_year > 0
    ):
        reasons.append("中長期では上向きですが、直近は一時的な調整局面に入っています")
    elif (
        one_month is not None
        and three_month is not None
        and one_month < 0
        and three_month < 0
    ):
        reasons.append("短期から中期では弱い動きが続いており、勢いの鈍化に注意が必要です")

    if one_month is not None and abs(one_month) >= 15:
        reasons.append("直近1か月の値動きが大きく、市場の注目が集まりやすい状態です")

    if has_news:
        reasons.append("最近の関連ニュースも出ており、値動きと合わせて確認したい局面です")

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
    """ホームの「なぜこの順位？」用。Atlasデータだけで順位の背景を説明する。"""
    rank = int(row["順位"])
    score = float(row["Atlas Score"])
    parts = row.get("Score内訳", {}) or {}

    part_messages = {
        "1週モメンタム": "直近1週間の勢いがScoreを支えています",
        "1か月モメンタム": "1か月の勢いがScoreを押し上げています",
        "3か月モメンタム": "3か月の勢いがScoreを押し上げています",
        "移動平均": "移動平均の並びが強く、中期トレンド面の得点が大きいです",
        "RSI": "RSIがAtlasの評価ゾーンにあり、勢いの安定感につながっています",
        "出来高": "出来高の活発さが注目度を支えています",
        "52週高値": "52週高値に比較的近く、価格位置の強さがScoreに反映されています",
    }

    normalized_parts = []
    for name, max_value in SCORE_PART_MAX.items():
        value = float(parts.get(name, 0) or 0)
        ratio = value / max_value if max_value else 0
        normalized_parts.append((ratio, value, name))

    normalized_parts.sort(reverse=True)
    strengths = []
    for ratio, value, name in normalized_parts[:3]:
        if value <= 0:
            continue
        strengths.append(part_messages[name])
        if len(strengths) >= 2:
            break

    if not strengths:
        strengths.append("特定の1項目ではなく、複数の指標を合わせた総合点で現在の順位になっています")

    def pct_value(col):
        value = row.get(col)
        return None if pd.isna(value) else float(value) * 100

    one_month = pct_value("1か月")
    three_month = pct_value("3か月")
    six_month = pct_value("6か月")
    one_year = pct_value("1年")
    trend_values = [one_month, three_month, six_month, one_year]

    if all(v is not None and v > 0 for v in trend_values):
        trend = "1か月〜1年がすべてプラスで、短期から長期まで値動きの方向がそろっています。"
    elif all(v is not None and v < 0 for v in trend_values):
        trend = "1か月〜1年がすべてマイナスで、複数の期間で弱い値動きが続いています。"
    elif (
        one_month is not None
        and three_month is not None
        and six_month is not None
        and one_month > 0
        and three_month > 0
        and six_month > 0
    ):
        trend = "直近半年はプラスが続いており、中期的な上向きの流れが見られます。"
    elif (
        one_month is not None
        and six_month is not None
        and one_year is not None
        and one_month < 0
        and six_month > 0
        and one_year > 0
    ):
        trend = "中長期ではプラスですが、直近1か月は調整しており、期間によって強弱があります。"
    elif (
        one_month is not None
        and three_month is not None
        and one_month > 0
        and three_month < 0
    ):
        trend = "直近1か月は反発していますが、3か月ではまだマイナスで回復途中の動きです。"
    elif (
        one_month is not None
        and three_month is not None
        and one_month < 0
        and three_month < 0
    ):
        trend = "短期〜中期ではマイナスが続いており、足元の勢いは弱めです。"
    else:
        trend = "期間別の騰落率には強弱があり、短期と中長期で方向がそろっていません。"

    position_bits = [f"Atlas Score {score:.1f}で、現在50社中 #{rank} です。"]
    if rank > 1 and len(full_df) >= rank - 1:
        upper_score = float(full_df.iloc[rank - 2]["Atlas Score"])
        position_bits.append(f"1つ上の順位とは {upper_score - score:.1f}pt 差です。")
    if rank < len(full_df):
        lower_score = float(full_df.iloc[rank]["Atlas Score"])
        position_bits.append(f"1つ下の順位には {score - lower_score:.1f}pt リードしています。")
    position = " ".join(position_bits)

    checks = []
    if one_month is not None and abs(one_month) >= 15:
        checks.append("直近1か月の値動きが大きいため、短期の振れには注意して確認したい状態です")

    rsi = row.get("RSI")
    if pd.notna(rsi):
        rsi = float(rsi)
        if rsi >= 75:
            checks.append("RSIが高めで、短期的な過熱感がないか確認したい水準です")
        elif rsi <= 35:
            checks.append("RSIが低めで、弱い勢いが続いていないか確認したい水準です")

    volume_ratio = row.get("出来高倍率")
    if pd.notna(volume_ratio) and float(volume_ratio) < 0.8:
        checks.append("出来高は20日平均を下回っており、上昇や反発の勢いが伴っているか確認が必要です")

    high_gap = row.get("高値乖離")
    if pd.notna(high_gap) and float(high_gap) < -0.15:
        checks.append("52週高値から距離があり、価格位置ではまだ回復余地と弱さの両方を確認する必要があります")

    if not checks:
        checks.append("Atlas上で大きく目立つ警戒サインは少なめですが、順位は将来の上昇を保証するものではありません")

    return {
        "rank": rank,
        "score": score,
        "position": position,
        "strengths": strengths,
        "trend": trend,
        "checks": checks[:2],
    }


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
        label = "広く上向き"
        icon = "🟢"
        summary = "複数の銘柄で1か月のプラスと20日線上回りが見られ、強さが一部の銘柄だけに偏っていない状態です。"
    elif breadth <= 0.35 and avg_one_month < 0:
        label = "全体に弱め"
        icon = "🔴"
        summary = "1か月のプラス銘柄と20日線を上回る銘柄が少なく、Atlas50全体では弱い値動きが目立つ状態です。"
    else:
        label = "強弱が混在"
        icon = "🟡"
        summary = "上向きの銘柄と弱い銘柄が混在しており、Atlas50全体では方向感がそろっていない状態です。"

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
    heat_lookup = {}
    for _, heat_row in heat_frame.iterrows():
        heat_lookup[(str(heat_row["業種グループ"]), str(heat_row["指標"]))] = heat_row

    desktop_parts = ['<div class="sector-heatmap-desktop">']
    desktop_parts.append('<div class="sector-heatmap-header">業種グループ</div>')
    for metric in metric_order:
        desktop_parts.append(f'<div class="sector-heatmap-header">{html.escape(metric)}</div>')

    mobile_parts = ['<div class="sector-heatmap-mobile">']

    for _, summary_row in summary.iterrows():
        sector_name = str(summary_row["業種グループ"])
        sector_escaped = html.escape(sector_name)
        count = int(summary_row["銘柄数"])
        breadth = float(summary_row["1か月プラス率"])

        desktop_parts.append(
            '<div class="sector-heatmap-sector">'
            f'<div class="sector-heatmap-sector-name">{sector_escaped}</div>'
            f'<div class="sector-heatmap-sector-meta">{count}銘柄 ｜ 1か月プラス {breadth:.0f}%</div>'
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
                f'<div class="sector-heatmap-mobile-label">{html.escape(metric)}</div>'
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
        return "条件を読み取れません"
    bits = [f"Score {float(config.get('watch_score', 0)):.0f}以上"]
    one_m = float(config.get("watch_1m", -100))
    three_m = float(config.get("watch_3m", -100))
    volume = float(config.get("watch_volume", 0))
    if one_m > -100:
        bits.append(f"1か月 {one_m:+.0f}%以上")
    if three_m > -100:
        bits.append(f"3か月 {three_m:+.0f}%以上")
    if volume > 0:
        bits.append(f"出来高 {volume:.1f}x以上")
    region = str(config.get("watch_region", "すべて"))
    sector = str(config.get("watch_sector_group", "すべて"))
    if region != "すべて":
        bits.append(region)
    if sector != "すべて":
        bits.append(sector)
    if bool(config.get("watch_sma20", False)):
        bits.append("20日線上")
    if bool(config.get("watch_sma60", False)):
        bits.append("60日線上")
    return " ｜ ".join(bits)


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
                    "publisher": publisher or "News",
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
あなたはAtlas50の初心者向け株式ニュース解説AIです。
会社名: {company_name}

以下のニュース最大3件だけを根拠に、それぞれを初心者向けに整理してください。
ニュース:
{json.dumps(payload, ensure_ascii=False, separators=(",", ":"))}

次のJSONだけを返してください。
{{
  "items": [
    {{
      "index": 0,
      "title_ja": "初心者にも分かる短い日本語タイトル",
      "summary": "専門用語をできるだけ避け、2文以内で意味を説明",
      "impact": "追い風候補・中立・リスク候補 のどれか"
    }}
  ]
}}

ルール:
- 入力された見出しと概要から分からない事実を作らない
- 決算や将来業績など、入力にない情報を推測しない
- 買う・売る・おすすめ等の投資推奨はしない
- 株価への方向性が判断できない場合は中立
- 断定しすぎない
- indexは入力ニュースの0始まりの番号をそのまま使う
- 日本語で簡潔に書く
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
            impact = str(item.get("impact", "中立")).strip()
            if impact not in {"追い風候補", "中立", "リスク候補"}:
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
あなたはAtlas50の初心者向け「銘柄比較」解説AIです。
以下の比較データだけを使って、違いを分かりやすく整理してください。

比較データ:
{json.dumps(compare_payload, ensure_ascii=False, separators=(",", ":"))}

次のJSONだけを返してください。

{{
  "overview": "比較全体を2文以内で要約",
  "company_notes": [
    {{"company": "会社名", "note": "このデータから読み取れる特徴を1〜2文"}}
  ],
  "key_differences": [
    "比較で特に差が出ている点",
    "別の重要な差"
  ],
  "watch_points": [
    "比較するときに注意して確認したい点"
  ]
}}

ルール:
- 必ず与えられた数値とAtlas Score内訳だけを根拠にする
- 決算、企業価値、ニュース、将来業績など、入力にない情報を推測しない
- 買う・売る・おすすめ・どちらを選ぶべきか、という投資推奨はしない
- 「A社の方が優れている」と単純に順位付けせず、期間やScore項目ごとの違いを説明する
- 上昇率が高いことを将来の上昇保証として扱わない
- Atlas Scoreは価格トレンドを整理する学習・監視指標として扱う
- key_differencesは最大3件、watch_pointsは最大3件
- company_notesは入力された会社をすべて1件ずつ含める
- 初心者向けの自然な日本語で簡潔に書く
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
            "overview": overview or "選択した銘柄の価格トレンドとAtlas Scoreを比較しました。",
            "company_notes": cleaned_notes,
            "key_differences": [str(x).strip() for x in key_differences[:3] if str(x).strip()],
            "watch_points": [str(x).strip() for x in watch_points[:3] if str(x).strip()],
        }

    except Exception as e:
        return {
            "ok": False,
            "overview": "AI比較解説を取得できませんでした。基本比較表とグラフはそのまま確認できます。",
            "company_notes": [],
            "key_differences": [],
            "watch_points": ["AI応答がタイムアウトしたか、一時的に取得できませんでした。もう一度試してください。"],
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
st.markdown('<div class="atlas-title">ATLAS 50</div>', unsafe_allow_html=True)
st.markdown('<div class="atlas-sub">世界の注目50社を、数分で把握する。</div>', unsafe_allow_html=True)
st.markdown(
    f'<div class="atlas-version-row">'
    f'<span class="atlas-chip">🚀 V{APP_VERSION} {APP_LABEL}</span>'
    f'<span class="atlas-chip">📚 学習・監視用</span>'
    f'<span class="atlas-chip">🌍 50銘柄</span>'
    f'</div>',
    unsafe_allow_html=True,
)

if st.button("🔄 データを更新", key="refresh_market_data"):
    load_data.clear()
    load_fx.clear()
    load_news.clear()
    st.rerun()

with st.spinner("世界50社と為替をチェック中..."):
    df, histories, errors = load_data()
    fx = load_fx()

if df.empty:
    st.error("株価データを取得できませんでした。『データを更新』を試してください。")
    with st.expander("エラー詳細"):
        st.code("\n".join(errors[:50]))
    st.stop()

df["FX→JPY"] = df["通貨"].map(fx)
df["円換算価格"] = df["現在値"] * df["FX→JPY"]
data_health = _build_data_health(df, fx, errors)

with st.expander("🧭 はじめて使う人へ / データ状態"):
    st.markdown(
        '<div class="atlas-guide-grid">'
        '<div class="atlas-guide-card"><div class="atlas-guide-step">STEP 1</div><div class="atlas-guide-title">🏠 全体を見る</div><div class="atlas-guide-text">Pulse・Radar・業種ヒートマップで、50社全体の現在地を確認。</div></div>'
        '<div class="atlas-guide-card"><div class="atlas-guide-step">STEP 2</div><div class="atlas-guide-title">🔎 深掘りする</div><div class="atlas-guide-text">個別分析で期間別騰落率・Score内訳・ニュースを確認。</div></div>'
        '<div class="atlas-guide-card"><div class="atlas-guide-step">STEP 3</div><div class="atlas-guide-title">⚖️ 比較する</div><div class="atlas-guide-text">2〜4社を同じ基準で比較。AI比較は必要な時だけ実行。</div></div>'
        '<div class="atlas-guide-card"><div class="atlas-guide-step">STEP 4</div><div class="atlas-guide-title">🔔 条件で探す</div><div class="atlas-guide-text">自分の観察条件を保存し、次回すぐ呼び出せます。</div></div>'
        '</div>',
        unsafe_allow_html=True,
    )
    missing_fx_text = "なし" if not data_health["missing_fx"] else " / ".join(data_health["missing_fx"])
    st.markdown(
        '<div class="data-health-grid">'
        f'<div class="data-health-item"><div class="data-health-label">取得銘柄</div><div class="data-health-value">{data_health["loaded"]} / {data_health["expected"]}</div></div>'
        f'<div class="data-health-item"><div class="data-health-label">最終価格日</div><div class="data-health-value">{html.escape(data_health["latest"])}</div></div>'
        f'<div class="data-health-item"><div class="data-health-label">未取得FX</div><div class="data-health-value">{html.escape(missing_fx_text)}</div></div>'
        f'<div class="data-health-item"><div class="data-health-label">取得エラー</div><div class="data-health-value">{len(data_health["errors"])}</div></div>'
        '</div>',
        unsafe_allow_html=True,
    )
    st.caption("データには遅延・取得失敗があり得ます。Atlas Scoreは価格トレンドを整理する観察指標で、売買推奨ではありません。")

if st.session_state.atlas_setup_flash:
    st.success(st.session_state.atlas_setup_flash)
    st.session_state.atlas_setup_flash = None

with st.expander("⬆️ Atlas設定を復元"):
    st.caption("お気に入り・保有株・保存した検索条件を、以前保存したAtlas設定JSONから復元できます。")
    atlas_setup_upload_global = st.file_uploader(
        "Atlas設定JSONを読み込む",
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
                st.session_state.atlas_setup_flash = "Atlas設定を復元しました。お気に入り・保有株・保存条件を反映しています。"
                st.rerun()
        except Exception:
            st.error("Atlas設定JSONを読み込めませんでした。")

tabs = st.tabs(["🏠 ホーム", "🌍 世界50", "🔎 個別分析", "⚖️ 比較", "⭐ お気に入り", "💼 保有株", "💰 予算で探す", "🔔 条件で探す"])


# ------------------------------
# ホーム
# ------------------------------
with tabs[0]:
    a, b, c, d, e = st.columns(5)

    a.metric("🌍 対象銘柄", f"{len(df)} / 50")
    b.metric("🔥 強い＋", int((df["判定"] == "強い＋").sum()))
    c.metric("📈 ＋", int((df["判定"] == "＋").sum()))
    d.metric("🎯 平均Score", f'{df["Atlas Score"].mean():.1f}')
    e.metric("🕒 最終更新", str(df["最終日"].max()))

    pulse = _build_atlas_pulse(df)
    st.markdown("### 📡 Atlas Pulse")
    st.caption("50社全体を見て、値動きの広がりと現在の状態を確認します。将来予測ではなく、現在データのスナップショットです。")

    pulse_box = st.container(border=True)
    p1, p2, p3, p4 = pulse_box.columns(4)
    p1.metric("📈 1か月プラス", f"{pulse['one_month_positive']} / {pulse['total']}")
    p2.metric("🗓️ 3か月プラス", f"{pulse['three_month_positive']} / {pulse['total']}")
    p3.metric("〽️ 20日線より上", f"{pulse['above_sma20']} / {pulse['total']}")
    p4.metric("📊 平均1か月", f"{pulse['avg_one_month']:+.2f}%")
    pulse_box.info(
        f"**{pulse['icon']} 全体像：{pulse['label']}**\n\n"
        f"{pulse['summary']}"
    )
    pulse_box.caption(
        "判定基準：『1か月プラス銘柄の割合』と『20日線より上の銘柄割合』を平均し、"
        "Atlas50の平均1か月騰落率と合わせて判定しています。3か月プラス銘柄数は補助情報です。"
    )

    with st.expander("🌍 地域別の状態を見る"):
        region_show = pulse["region"].copy()

        region_table = st.container(key="pulse_region_table")
        region_table.dataframe(
            region_show,
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
            region_name = str(region_row["地域"])
            region_count = int(region_row["銘柄数"])
            region_score = float(region_row["平均Score"])
            region_1m = float(region_row["1か月平均"])
            region_3m = float(region_row["3か月平均"])
            region_cards += (
                f'<div class="pulse-region-card">'
                f'<div class="pulse-region-head">'
                f'<div class="pulse-region-name">🌍 {region_name}</div>'
                f'<div class="pulse-region-count">{region_count}銘柄</div>'
                f'</div>'
                f'<div class="pulse-region-score">Atlas Score平均 {region_score:.1f}</div>'
                f'<div class="pulse-region-stats">'
                f'1か月平均 {region_1m:+.2f}% ｜ 3か月平均 {region_3m:+.2f}%'
                f'</div>'
                f'</div>'
            )
        region_mobile.markdown(region_cards, unsafe_allow_html=True)

        st.caption("※ 地域別の平均はAtlas50に含まれる銘柄だけを集計しています。市場全体の指数ではありません。")

    st.markdown("### 📡 Atlas Radar")
    st.caption("Atlas50の中から、直近1か月の値動きや出来高の変化が目立つ銘柄を確認します。変化の大きさは買い・売りの推奨を意味しません。")

    radar = _build_atlas_radar(df)

    def _radar_items_html(frame, mode):
        items = []
        for _, radar_row in frame.iterrows():
            company = html.escape(str(radar_row["会社名"]))
            country = html.escape(str(radar_row["国"]))
            score = float(radar_row["Atlas Score"]) if pd.notna(radar_row["Atlas Score"]) else 0.0
            one_m = float(radar_row["1か月"]) * 100 if pd.notna(radar_row["1か月"]) else None
            three_m = float(radar_row["3か月"]) * 100 if pd.notna(radar_row["3か月"]) else None
            volume_ratio = float(radar_row["出来高倍率"]) if pd.notna(radar_row["出来高倍率"]) else None

            if mode == "volume":
                main_value = f"{volume_ratio:.2f}x" if volume_ratio is not None else "-"
                meta = f"{country} ｜ 1か月 {one_m:+.2f}% ｜ Score {score:.1f}" if one_m is not None else f"{country} ｜ Score {score:.1f}"
            else:
                main_value = f"{one_m:+.2f}%" if one_m is not None else "-"
                meta = f"{country} ｜ 3か月 {three_m:+.2f}% ｜ Score {score:.1f}" if three_m is not None else f"{country} ｜ Score {score:.1f}"

            items.append(
                '<div class="atlas-radar-item">'
                '<div>'
                f'<div class="atlas-radar-company">{company}</div>'
                f'<div class="atlas-radar-meta">{meta}</div>'
                '</div>'
                f'<div class="atlas-radar-value">{main_value}</div>'
                '</div>'
            )
        return "".join(items) or '<div class="atlas-radar-meta">表示できるデータがありません。</div>'

    radar_html = (
        '<div class="atlas-radar-grid">'
        '<div class="atlas-radar-panel">'
        '<div class="atlas-radar-title">📈 1か月上昇が目立つ</div>'
        '<div class="atlas-radar-sub">直近1か月の騰落率が大きい順に3社</div>'
        + _radar_items_html(radar["up"], "up")
        + '</div>'
        '<div class="atlas-radar-panel">'
        '<div class="atlas-radar-title">📉 1か月下落が目立つ</div>'
        '<div class="atlas-radar-sub">直近1か月の下落率が大きい順に3社</div>'
        + _radar_items_html(radar["down"], "down")
        + '</div>'
        '<div class="atlas-radar-panel">'
        '<div class="atlas-radar-title">🔊 出来高が目立つ</div>'
        '<div class="atlas-radar-sub">直近出来高 ÷ 20日平均が大きい順に3社</div>'
        + _radar_items_html(radar["volume"], "volume")
        + '</div>'
        '</div>'
    )
    st.markdown(radar_html, unsafe_allow_html=True)
    st.caption("※ Atlas Radarは現在の値動き・出来高を整理する観察用表示です。急な上昇・下落や出来高増加だけで将来の値動きは判断できません。")

    st.markdown("### 🧩 業種別ヒートマップ")
    st.caption(
        "Atlas50の29業種を9つの大分類にまとめ、期間別の平均値から強弱の分布を確認します。"
        "色だけでなくセル内の実数も合わせて確認してください。"
    )

    sector_summary, sector_heat = _build_sector_heatmap(df)

    if not sector_summary.empty:
        best_score = sector_summary.sort_values("平均Score", ascending=False).iloc[0]
        best_1m = sector_summary.sort_values("1か月平均", ascending=False).iloc[0]
        best_breadth = sector_summary.sort_values(["1か月プラス率", "平均Score"], ascending=[False, False]).iloc[0]

        sector_spotlight_html = (
            '<div class="sector-spotlight-grid">'
            '<div class="sector-spotlight-card">'
            '<div class="sector-spotlight-label">🎯 平均Score上位</div>'
            f'<div class="sector-spotlight-value">{html.escape(str(best_score["業種グループ"]))}</div>'
            f'<div class="sector-spotlight-meta">Score {float(best_score["平均Score"]):.1f} ｜ {int(best_score["銘柄数"])}銘柄</div>'
            '</div>'
            '<div class="sector-spotlight-card">'
            '<div class="sector-spotlight-label">📈 1か月平均上位</div>'
            f'<div class="sector-spotlight-value">{html.escape(str(best_1m["業種グループ"]))}</div>'
            f'<div class="sector-spotlight-meta">1か月 {float(best_1m["1か月平均"]):+.2f}% ｜ Score {float(best_1m["平均Score"]):.1f}</div>'
            '</div>'
            '<div class="sector-spotlight-card">'
            '<div class="sector-spotlight-label">🌐 上昇の広がり上位</div>'
            f'<div class="sector-spotlight-value">{html.escape(str(best_breadth["業種グループ"]))}</div>'
            f'<div class="sector-spotlight-meta">1か月プラス {float(best_breadth["1か月プラス率"]):.0f}% ｜ {int(best_breadth["銘柄数"])}銘柄</div>'
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
            "色の基準：赤系は相対的に弱め、中央付近は中立、緑系は相対的に強めです。"
            "騰落率は0%を中立、Atlas Scoreは50を中立としており、セル内の実数を優先して確認してください。"
        )

        with st.expander("🗂️ 業種グループの内訳を見る"):
            grouped_sectors = {}
            for original_sector, grouped_sector in SECTOR_GROUPS.items():
                grouped_sectors.setdefault(grouped_sector, []).append(original_sector)
            for grouped_sector in sector_order:
                members = grouped_sectors.get(grouped_sector, [grouped_sector])
                st.markdown(f"**{grouped_sector}**：{' / '.join(members)}")
            st.caption("※ この大分類はAtlas50内で比較しやすくするための独自分類で、市場標準のセクター分類ではありません。")
    else:
        st.caption("業種別データを集計できませんでした。")

    st.caption("※ 業種別ヒートマップはAtlas50内の現在データを整理する観察用表示で、業種や銘柄の売買推奨ではありません。")

    st.markdown("## 🔥 今日の注目 TOP10")
    st.caption("Atlas Scoreをもとに、現在の注目度が高い銘柄を表示しています。")
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
        top,
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
            f'<div class="home-top10-country">{html.escape(str(top_row["国"]))}</div>'
            '</div>'
            f'<div class="home-top10-score">Score {float(top_row["Atlas Score"]):.1f}</div>'
            '</div>'
            '<div class="home-top10-grid">'
            f'<div class="home-top10-item"><div class="home-top10-label">1か月</div><div class="home-top10-value">{_pct_number_text(top_row["1か月"])}</div></div>'
            f'<div class="home-top10-item"><div class="home-top10-label">3か月</div><div class="home-top10-value">{_pct_number_text(top_row["3か月"])}</div></div>'
            f'<div class="home-top10-item"><div class="home-top10-label">6か月</div><div class="home-top10-value">{_pct_number_text(top_row["6か月"])}</div></div>'
            f'<div class="home-top10-item"><div class="home-top10-label">1年</div><div class="home-top10-value">{_pct_number_text(top_row["1年"])}</div></div>'
            '</div>'
            f'<div class="home-top10-judge">{html.escape(str(top_row["判定"]))}</div>'
            '</div>'
        )

    st.markdown(
        '<div class="home-top10-mobile">' + "".join(home_top10_cards) + '</div>',
        unsafe_allow_html=True,
    )
    st.caption("※ 同じScore表示でも、順位は内部のより細かい値によって決まる場合があります。")

    st.markdown("### 🧭 なぜこの順位？")
    st.caption("TOP10から1社を選ぶと、Atlas Scoreの内訳と値動きから現在の順位の背景を整理します。")

    rank_options = df.head(10)["会社名"].tolist()
    selected_rank_company = st.selectbox(
        "ランキング理由を見る企業",
        rank_options,
        key="home_rank_reason_company",
        label_visibility="collapsed",
    )

    rank_row = df[df["会社名"] == selected_rank_company].iloc[0]
    rank_detail = _build_ranking_explanation(rank_row, df)

    rank_card = st.container(border=True)
    rank_card.markdown(
        f"#### #{rank_detail['rank']} {selected_rank_company}　"
        f"<span class='badge'>Atlas Score {rank_detail['score']:.1f}</span>",
        unsafe_allow_html=True,
    )
    rank_card.caption(rank_detail["position"])
    rank_card.info(
        "**🎯 順位を押し上げている主な要因**\n\n"
        + "\n\n".join(f"・{item}" for item in rank_detail["strengths"])
        + f"\n\n**📈 値動きの流れ**\n\n・{rank_detail['trend']}"
    )
    rank_card.warning(
        "**⚠️ チェックポイント**\n\n"
        + "\n\n".join(f"・{item}" for item in rank_detail["checks"])
    )
    rank_card.caption(
        "※ 順位は現在の価格トレンドをAtlas Scoreで整理したものです。買い推奨・将来の利益予測ではありません。"
    )
 
# ------------------------------
# 世界50
# ------------------------------
with tabs[1]:
    st.markdown("## 🌍 世界50")
    st.caption("国・地域・業種・Atlas Scoreで、世界の注目銘柄を絞り込めます。")

    search_text = st.text_input(
        "会社名・Ticker検索",
        placeholder="例：NVIDIA / NVDA / MUFG",
        key="world_search",
    ).strip()

    f1, f2, f3, f4 = st.columns(4)
    country = f1.selectbox("国", ["すべて"] + sorted(df["国"].unique().tolist()), key="country")
    region = f2.selectbox("地域", ["すべて"] + sorted(df["地域"].unique().tolist()), key="region")
    sector = f3.selectbox("業種", ["すべて"] + sorted(df["業種"].unique().tolist()), key="sector")
    minscore = f4.slider("最低Score", 0, 100, 0, key="score")

    f5, f6 = st.columns(2)
    judge_filter = f5.selectbox(
        "判定",
        ["すべて", "強い＋", "＋", "様子見", "－"],
        key="world_judge",
    )
    world_sort = f6.selectbox(
        "並び順",
        ["Atlas Scoreが高い順", "1か月上昇率が高い順", "3か月上昇率が高い順", "円換算価格が安い順"],
        key="world_sort",
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
    st.caption(f"表示：{len(view)} / {len(df)}社")

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
        show,
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
    # HTML文字列はインデントなしで組み立てる。
    mobile_cards = []
    for _, mobile_row in show.iterrows():
        mobile_cards.append(
            "<div class=\"mobile-stock-card\">"
            f"<div class=\"mobile-rank\">#{int(mobile_row['順位'])}</div>"
            f"<div class=\"mobile-company\">{html.escape(str(mobile_row['会社名']))}</div>"
            f"<div class=\"mobile-meta\">{html.escape(str(mobile_row['国']))} ・ {html.escape(str(mobile_row['業種']))}</div>"
            f"<div class=\"mobile-score\">Atlas Score {float(mobile_row['Atlas Score']):.1f}</div>"
            "<div class=\"mobile-stats\">"
            f"1か月 {_pct_number_text(mobile_row['1か月'])} ｜ 3か月 {_pct_number_text(mobile_row['3か月'])}<br>"
            f"6か月 {_pct_number_text(mobile_row['6か月'])} ｜ 1年 {_pct_number_text(mobile_row['1年'])}"
            "</div>"
            f"<div class=\"mobile-judge\">{html.escape(str(mobile_row['判定']))}</div>"
            "</div>"
        )

    mobile_html = (
        '<div class="mobile-list-wrap">'
        '<div class="mobile-list-title">スマホ向け一覧</div>'
        + "".join(mobile_cards)
        + "</div>"
    )
    st.markdown(mobile_html, unsafe_allow_html=True)



# ------------------------------
# 個別分析
# ------------------------------
with tabs[2]:
    st.markdown("## 🔎 個別分析")
    st.caption("気になる企業を選ぶと、価格トレンド・AIニュース・Atlas Scoreをまとめて確認できます。")

    selected = st.selectbox("分析する企業", df["会社名"].tolist(), key="detail_company")
    row = df[df["会社名"] == selected].iloc[0]
    t = row["Ticker"]

    price_text = f'¥{row["円換算価格"]:,.0f}' if pd.notna(row["円換算価格"]) else "-"

    st.markdown(f"## {selected}")
    st.caption(f"{row['国']} ・ {row['業種']}　｜　Ticker: {t}　｜　円換算: {price_text}")

    # 6個の重要指標を、スマホでも崩れにくい3列×2段で表示。
    c1, c2, c3 = st.columns(3)
    c1.metric("Atlas Score", f'{row["Atlas Score"]:.1f}')
    c2.metric("判定", row["判定"])
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

    st.markdown("### 🔰 30秒でわかる")

    good_points = []
    risk_points = []

    if score >= 80:
        good_points.append("Atlas Scoreが高く、現在の注目度は高めです")
    elif score >= 65:
        good_points.append("Atlas Scoreは中〜高水準です")

    for label, value in [
        ("1か月", one_month),
        ("3か月", three_month),
        ("6か月", six_month),
        ("1年", one_year),
    ]:
        if value is None:
            continue
        if value > 0:
            good_points.append(f"直近{label}は +{value:.1f}%")
        else:
            risk_points.append(f"直近{label}は {value:.1f}%")

    if one_month is not None and abs(one_month) >= 15:
        risk_points.append("1か月の値動きが大きく、短期の価格変動には注意")

    if not good_points:
        good_points.append("現在は強いプラス材料が少なめです")

    if not risk_points:
        risk_points.append("値動きだけでは大きな警戒材料は確認されていません")

    st.info(
        "### ✅ プラス材料\n\n"
        + "\n\n".join(f"・{x}" for x in good_points)
    )

    st.warning(
        "### ⚠️ チェックポイント\n\n"
        + "\n\n".join(f"・{x}" for x in risk_points)
    )

    is_favorite = t in st.session_state.favorites
    favorite_label = "⭐ お気に入りから解除" if is_favorite else "⭐ お気に入りに追加"
    if st.button(favorite_label, key="fav_btn"):
        if is_favorite:
            st.session_state.favorites.remove(t)
        else:
            st.session_state.favorites.add(t)
        st.session_state.favorites_editor_version += 1
        st.rerun()

    st.markdown("## 🔥 なぜ今注目？")

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
            "### 📌 注目ポイント\n\n"
            + "\n\n".join(f"・{reason}" for reason in reasons)
        )
    else:
        st.info(
            "### 📌 注目ポイント\n\n"
            "・現在は大きく目立つトレンドが少ない状態です"
        )

    st.markdown("## 📰 最新ニュース & AI解説")
    st.caption(
        "関連ニュースを最大3件表示します。AI解説は必要な時だけボタンで生成するため、"
        "通常表示ではAPIを消費しません。"
    )

    if news_preview:
        news_payload = [
            {
                "title": str(item.get("title", "")),
                "summary": str(item.get("summary", ""))[:1500],
                "publisher": str(item.get("publisher", "News")),
            }
            for item in news_preview[:3]
        ]
        news_ai_key = json.dumps(
            {"company": selected, "news": news_payload},
            ensure_ascii=False,
            sort_keys=True,
        )

        if st.button(
            "🤖 ニュース3件をAIで整理する",
            key=f"news_ai_button_{t}",
            use_container_width=True,
        ):
            with st.spinner(f"Atlas AIがニュースを整理中...（最大{int(AI_TIMEOUT_SECONDS)}秒）"):
                st.session_state.news_ai_result = analyze_news_batch_with_ai(
                    selected,
                    json.dumps(news_payload, ensure_ascii=False, sort_keys=True),
                )
                st.session_state.news_ai_key = news_ai_key

        active_news_ai = None
        if st.session_state.news_ai_key == news_ai_key:
            active_news_ai = st.session_state.news_ai_result

        if active_news_ai and not active_news_ai.get("ok", False):
            st.warning("AIニュース解説を取得できませんでした。元ニュースはそのまま確認できます。")

        ai_items = active_news_ai.get("items", {}) if active_news_ai and active_news_ai.get("ok") else {}

        for i, item in enumerate(news_preview[:3], start=1):
            card = st.container(border=True)
            card.markdown(f"### 📰 注目ニュース {i}")

            ai_news = ai_items.get(i - 1) if isinstance(ai_items, dict) else None
            if ai_news:
                title_display = ai_news.get("title_ja", item["title"])
                summary_display = ai_news.get("summary", "AI解説を取得できませんでした。")
                impact = ai_news.get("impact", "中立")

                if impact == "追い風候補":
                    impact_icon = "🟢"
                elif impact == "リスク候補":
                    impact_icon = "🔴"
                else:
                    impact_icon = "🟡"

                card.write(f"**🇯🇵 {title_display}**")
                card.caption(f"情報元：{item['publisher']}")
                card.info(f"💡 初心者向け解説\n\n{summary_display}")
                card.write(f"📊 **ニュースの影響：{impact_icon} {impact}**")
                card.caption(f"原文見出し：{item['title']}")
            else:
                card.write(f"**{item['title']}**")
                card.caption(f"情報元：{item['publisher']} ｜ AI解説は上のボタンで生成できます")
                source_summary = str(item.get("summary", "") or "").strip()
                if source_summary:
                    card.write(source_summary[:500] + ("…" if len(source_summary) > 500 else ""))

            if item.get("link"):
                card.markdown(f"[🔗 元の記事を見る]({item['link']})")
    else:
        st.caption("この会社に関連するニュースを取得できませんでした。")

    st.markdown("## 📈 1年チャート")
    st.caption("株価と20日・60日移動平均線から、中長期の値動きを確認できます。")

    hist = histories.get(t)
    if hist is not None and not hist.empty:
        st.line_chart(hist[["Close", "SMA20", "SMA60"]])
    else:
        st.caption("チャートを取得できませんでした。")

    st.markdown("## 📊 Atlas Scoreの内訳")
    st.caption("Atlas Scoreを構成している各指標の点数を確認できます。")

    parts = row["Score内訳"]
    parts_df = pd.DataFrame(
        {"項目": list(parts.keys()), "点数": list(parts.values())}
    )
    st.bar_chart(parts_df.set_index("項目")["点数"])


# ------------------------------
# 銘柄比較
# ------------------------------
with tabs[3]:
    st.markdown("## ⚖️ 銘柄比較")
    st.caption("2〜4社を同じ基準で並べ、値動きとAtlas Scoreの違いを確認できます。")

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

        st.markdown("### 📋 基本比較")
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
            compare_show,
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
            country = html.escape(str(compare_row["国"]))
            sector = html.escape(str(compare_row["業種"]))
            judge = html.escape(str(compare_row["判定"]))
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
                f'<div class="compare-card-meta">{country} ・ {sector} ｜ {price_text}</div>'
                '</div>'
                f'<div class="compare-card-score">Score {score_text}</div>'
                '</div>'
                '<div class="compare-card-grid">'
                f'<div class="compare-card-item"><div class="compare-card-label">1か月</div><div class="compare-card-value">{period_values["1か月"]}</div></div>'
                f'<div class="compare-card-item"><div class="compare-card-label">3か月</div><div class="compare-card-value">{period_values["3か月"]}</div></div>'
                f'<div class="compare-card-item"><div class="compare-card-label">6か月</div><div class="compare-card-value">{period_values["6か月"]}</div></div>'
                f'<div class="compare-card-item"><div class="compare-card-label">1年</div><div class="compare-card-value">{period_values["1年"]}</div></div>'
                '</div>'
                f'<div class="compare-card-judge">{judge}</div>'
                '</div>'
            )

        compare_mobile = st.container(key="compare_mobile")
        compare_mobile.markdown(
            "".join(mobile_compare_cards),
            unsafe_allow_html=True,
        )

        st.markdown("### 📈 1年の値動きを100基準で比較")
        st.caption("各社の開始時点を100として、価格水準ではなく値動きの差を比較します。")

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
            st.caption("※ 市場ごとの休場日は、比較表示上のみ直前の終値を引き継いでいます。")
        else:
            st.caption("比較チャートを作成できる価格データがありません。")

        st.markdown("### 📊 Atlas Scoreの内訳比較")
        st.caption("総合Scoreだけでなく、どの項目で差が出ているかを確認できます。")

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
                .melt(id_vars="項目", var_name="会社名", value_name="点数")
            )

            score_chart = (
                alt.Chart(parts_long)
                .mark_bar(cornerRadiusEnd=3)
                .encode(
                    y=alt.Y(
                        "項目:N",
                        sort=part_order,
                        title=None,
                        axis=alt.Axis(labelLimit=120),
                    ),
                    x=alt.X("点数:Q", title="点数", scale=alt.Scale(zero=True)),
                    color=alt.Color("会社名:N", title=None),
                    yOffset=alt.YOffset("会社名:N"),
                    tooltip=[
                        alt.Tooltip("会社名:N", title="会社"),
                        alt.Tooltip("項目:N", title="項目"),
                        alt.Tooltip("点数:Q", title="点数", format=".1f"),
                    ],
                )
                .properties(height=max(300, len(part_order) * 48))
            )
            st.altair_chart(score_chart, use_container_width=True)
        else:
            st.caption("Score内訳を比較できませんでした。")

        st.markdown("### 🤖 Atlas AI 比較解説")
        st.caption(
            "選択した期間別の値動きとAtlas Score内訳だけを使い、各社の違いを初心者向けに整理します。"
        )

        compare_payload = {"companies": []}
        for _, ai_row in compare_df.iterrows():
            ai_parts = ai_row["Score内訳"] if isinstance(ai_row["Score内訳"], dict) else {}
            compare_payload["companies"].append(
                {
                    "company": str(ai_row["会社名"]),
                    "country": str(ai_row["国"]),
                    "sector": str(ai_row["業種"]),
                    "returns_pct": {
                        "1か月": None if pd.isna(ai_row["1か月"]) else round(float(ai_row["1か月"]) * 100, 2),
                        "3か月": None if pd.isna(ai_row["3か月"]) else round(float(ai_row["3か月"]) * 100, 2),
                        "6か月": None if pd.isna(ai_row["6か月"]) else round(float(ai_row["6か月"]) * 100, 2),
                        "1年": None if pd.isna(ai_row["1年"]) else round(float(ai_row["1年"]) * 100, 2),
                    },
                    "atlas_score": round(float(ai_row["Atlas Score"]), 1),
                    "judge": str(ai_row["判定"]),
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
            "🤖 Atlas AIで比較を整理する",
            key="compare_ai_button",
            use_container_width=True,
        ):
            with st.spinner(f"Atlas AIが比較データを整理中...（最大{int(AI_TIMEOUT_SECONDS)}秒）"):
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
                    "### 🧭 全体像\n\n"
                    + ai_result.get(
                        "overview",
                        "選択した銘柄の価格トレンドとAtlas Scoreを比較しました。",
                    )
                )
            else:
                st.warning(
                    "### 🤖 AI解説を取得できませんでした\n\n"
                    + ai_result.get(
                        "overview",
                        "基本比較表とグラフはそのまま確認できます。",
                    )
                )

            company_notes = ai_result.get("company_notes", [])
            if company_notes:
                st.markdown("#### 🏢 各社の特徴")
                for note in company_notes:
                    note_card = st.container(border=True)
                    note_card.markdown(f"**{note.get('company', '企業')}**")
                    note_card.write(note.get("note", ""))

            key_differences = ai_result.get("key_differences", [])
            if key_differences:
                st.info(
                    "### 🔍 主な違い\n\n"
                    + "\n\n".join(f"・{item}" for item in key_differences)
                )

            watch_points = ai_result.get("watch_points", [])
            if watch_points:
                st.warning(
                    "### ⚠️ 確認ポイント\n\n"
                    + "\n\n".join(f"・{item}" for item in watch_points)
                )

            st.caption(
                "※ AI解説は表示中の価格トレンドとAtlas Scoreを整理したものです。"
                "投資推奨や将来の利益予測ではありません。"
            )

        st.info(
            "### 🔰 比較の見方\n\n"
            "・短期の上昇率だけで判断せず、1か月〜1年の流れを合わせて確認します。\n\n"
            "・Atlas Scoreは現在の価格トレンドを整理する学習・監視指標で、企業価値や将来の利益を保証するものではありません。"
        )


# ------------------------------
# お気に入り
# ------------------------------
with tabs[4]:
    st.markdown("## ⭐ お気に入り")
    st.caption("気になる銘柄を保存して、値動きやAtlas Scoreをまとめて比較できます。")

    with st.expander("✏️ お気に入りを編集"):
        current_favorite_names = [
            name for ticker, name, *_ in COMPANIES
            if ticker in st.session_state.favorites
        ]
        edited_favorite_names = st.multiselect(
            "お気に入り銘柄",
            options=[row[1] for row in COMPANIES],
            default=current_favorite_names,
            key=f"favorites_editor_names_{st.session_state.favorites_editor_version}",
        )
        if st.button("⭐ お気に入りを更新", use_container_width=True, key="favorites_editor_apply"):
            name_to_ticker = {row[1]: row[0] for row in COMPANIES}
            st.session_state.favorites = {name_to_ticker[name] for name in edited_favorite_names}
            st.session_state.favorites_editor_version += 1
            st.rerun()

    favdf = df[df["Ticker"].isin(st.session_state.favorites)].copy()

    if favdf.empty:
        st.info("🔎 個別分析から気になる企業をお気に入りに追加すると、ここでまとめて比較できます。")
    else:
        fm1, fm2, fm3 = st.columns(3)
        fm1.metric("⭐ 登録数", f"{len(favdf)}社")
        fm2.metric("🎯 平均Score", f"{favdf['Atlas Score'].mean():.1f}")
        fav_1m_mean = favdf["1か月"].mean() * 100 if favdf["1か月"].notna().any() else float("nan")
        fm3.metric("📈 平均1か月", "-" if pd.isna(fav_1m_mean) else f"{fav_1m_mean:+.2f}%")

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
                f'<div class="mobile-detail-meta">{html.escape(str(fav_row["国"]))} ・ {html.escape(str(fav_row["業種"]))}</div>'
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
                f'<div class="mobile-detail-judge">{html.escape(str(fav_row["判定"]))}</div>'
                '</div>'
            )

        st.markdown(
            '<div class="atlas-card-grid">' + "".join(favorite_cards) + '</div>',
            unsafe_allow_html=True,
        )

        with st.expander("📋 表で比較する"):
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
                favshow,
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
    st.markdown("## 💼 保有株")
    st.caption(
        "保有銘柄・株数・平均取得単価を入力すると、現在の評価額と損益を自動計算します。"
        "外国株の平均取得単価は現地通貨で入力し、現在の為替で円換算する概算です。CSVで保存・復元できます。"
    )

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
            "株数": st.column_config.NumberColumn(min_value=0.0, step=0.01),
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
        st.warning(
            "為替または円換算価格を取得できず、計算対象外になった銘柄があります："
            + "、".join(dict.fromkeys(skipped_portfolio))
        )

    if calc:
        pf = pd.DataFrame(
            calc,
            columns=[
                "Ticker", "会社名", "株数", "投資額(円)", "評価額(円)",
                "損益(円)", "損益率", "Score", "判定",
            ],
        )

        st.markdown("### 📌 保有状況サマリー")
        total_invested = pf["投資額(円)"].sum()
        total_current = pf["評価額(円)"].sum()
        total_pnl = pf["損益(円)"].sum()
        total_pnl_rate = total_pnl / total_invested * 100 if total_invested else 0

        p1, p2, p3 = st.columns(3)
        p1.metric("💴 投資額", f"¥{total_invested:,.0f}")
        p2.metric("📊 評価額", f"¥{total_current:,.0f}")
        p3.metric("📈 損益", f"¥{total_pnl:,.0f}", delta=f"{total_pnl_rate:+.2f}%")

        if len(pf) >= 2:
            st.markdown("### 🧩 評価額の構成")
            allocation = (
                pf.groupby("会社名", as_index=False)["評価額(円)"]
                .sum()
                .sort_values("評価額(円)", ascending=False)
            )
            allocation_chart = (
                alt.Chart(allocation)
                .mark_bar(cornerRadiusEnd=4)
                .encode(
                    y=alt.Y("会社名:N", sort="-x", title=None),
                    x=alt.X("評価額(円):Q", title="評価額（円）"),
                    tooltip=[
                        alt.Tooltip("会社名:N", title="会社"),
                        alt.Tooltip("評価額(円):Q", title="評価額", format=",.0f"),
                    ],
                )
                .properties(height=max(160, min(360, len(allocation) * 34)))
            )
            st.altair_chart(allocation_chart, use_container_width=True)
            st.caption("※ 現在の円換算評価額による構成です。資産配分の推奨を示すものではありません。")

        portfolio_cards = []
        for _, pf_row in pf.iterrows():
            pnl_rate_text = f"{float(pf_row['損益率']) * 100:+.2f}%"
            portfolio_cards.append(
                '<div class="mobile-detail-card">'
                '<div class="mobile-detail-head">'
                '<div>'
                f'<div class="mobile-detail-company">{html.escape(str(pf_row["会社名"]))}</div>'
                f'<div class="mobile-detail-meta">{html.escape(str(pf_row["Ticker"]))} ・ {float(pf_row["株数"]):g}株</div>'
                '</div>'
                f'<div class="mobile-detail-score">Score {float(pf_row["Score"]):.1f}</div>'
                '</div>'
                '<div class="mobile-detail-grid">'
                f'<div class="mobile-detail-item"><div class="mobile-detail-label">投資額</div><div class="mobile-detail-value">¥{float(pf_row["投資額(円)"]):,.0f}</div></div>'
                f'<div class="mobile-detail-item"><div class="mobile-detail-label">評価額</div><div class="mobile-detail-value">¥{float(pf_row["評価額(円)"]):,.0f}</div></div>'
                f'<div class="mobile-detail-item"><div class="mobile-detail-label">損益</div><div class="mobile-detail-value">¥{float(pf_row["損益(円)"]):+,.0f}</div></div>'
                f'<div class="mobile-detail-item"><div class="mobile-detail-label">損益率</div><div class="mobile-detail-value">{pnl_rate_text}</div></div>'
                '</div>'
                f'<div class="mobile-detail-judge">{html.escape(str(pf_row["判定"]))}</div>'
                '</div>'
            )

        st.markdown(
            '<div class="atlas-card-grid">' + "".join(portfolio_cards) + '</div>',
            unsafe_allow_html=True,
        )

        with st.expander("📋 詳細を表で見る"):
            pf_display = pf.copy()
            pf_display["損益率"] = (pf_display["損益率"] * 100).round(2)
            st.dataframe(
                pf_display,
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
        st.caption("株数と平均取得単価を入力すると、保有状況サマリーと損益が表示されます。")

    csv = edited.to_csv(index=False).encode("utf-8-sig")
    st.download_button("保有株CSVを保存", csv, "atlas50_portfolio.csv", "text/csv")

    upl = st.file_uploader("保存した保有株CSVを読み込む", type=["csv"], key="pfupload")
    if upl is not None:
        try:
            csv_bytes = upl.getvalue()
            csv_digest = hashlib.sha256(csv_bytes).hexdigest()
            if csv_digest != st.session_state.portfolio_csv_digest:
                loaded = pd.read_csv(io.BytesIO(csv_bytes))
                required_cols = {"Ticker", "株数", "平均取得単価"}
                if not required_cols.issubset(loaded.columns):
                    raise ValueError("必要列不足")
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
    st.markdown("## 💰 予算で探す")
    st.caption("投資予算を入力すると、その金額で1株以上買える企業を一覧で確認できます。")
    budget = st.number_input(
        "投資予算（円）",
        min_value=0,
        value=MONTHLY_BUDGET_DEFAULT,
        step=1000,
    )

    buyable = df[(df["円換算価格"].notna()) & (df["円換算価格"] <= budget)].copy()
    st.metric("🎯 予算内で1株買える企業", f"{len(buyable)}社")
    st.caption("これは『予算内で1株買えるか』の表示で、買い推奨ではありません。")

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
                f'<div class="mobile-detail-meta">{html.escape(str(budget_row["国"]))} ・ {html.escape(str(budget_row["業種"]))}</div>'
                '</div>'
                f'<div class="mobile-detail-score">Score {float(budget_row["Atlas Score"]):.1f}</div>'
                '</div>'
                '<div class="mobile-detail-grid">'
                f'<div class="mobile-detail-item"><div class="mobile-detail-label">1株の目安</div><div class="mobile-detail-value">¥{float(budget_row["円換算価格"]):,.0f}</div></div>'
                f'<div class="mobile-detail-item"><div class="mobile-detail-label">予算で買える株数</div><div class="mobile-detail-value">{int(budget_row["予算で買える株数"])}株</div></div>'
                '</div>'
                f'<div class="mobile-detail-judge">{html.escape(str(budget_row["判定"]))}</div>'
                '</div>'
            )

        st.markdown(
            '<div class="atlas-card-grid">' + "".join(budget_cards) + '</div>',
            unsafe_allow_html=True,
        )

        with st.expander("📋 一覧を表で見る"):
            st.dataframe(
                buyable[[
                    "順位", "会社名", "国", "業種", "円換算価格",
                    "予算で買える株数", "Atlas Score", "判定",
                ]],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "円換算価格": st.column_config.NumberColumn(format="¥%.0f"),
                    "Atlas Score": st.column_config.ProgressColumn(min_value=0, max_value=100, format="%.1f"),
                },
            )
    else:
        st.info("現在の予算内で1株買える企業はありません。")


# ------------------------------
# 条件で探す
# ------------------------------
with tabs[7]:
    st.markdown("## 🔔 条件で探す")
    st.caption(
        "Atlas50を自分の条件で絞り込みます。ここで表示される銘柄は条件一致の一覧であり、"
        "買い・売りの推奨ではありません。"
    )

    if st.session_state.watch_filter_flash:
        st.success(st.session_state.watch_filter_flash)
        st.session_state.watch_filter_flash = None

    st.markdown("### 💾 保存済み条件")
    st.caption("保存した観察条件をワンタップで呼び出せます。アプリ全体の設定は画面下部からJSON保存できます。")

    saved_names = sorted(st.session_state.saved_watch_filters.keys())
    if saved_names:
        saved_select_col, saved_apply_col, saved_delete_col = st.columns([3, 1, 1])
        selected_saved_filter = saved_select_col.selectbox(
            "保存済み条件",
            saved_names,
            key="saved_watch_filter_select",
            label_visibility="collapsed",
        )
        if saved_apply_col.button("▶️ 呼び出す", use_container_width=True, key="saved_watch_filter_apply"):
            _apply_watch_config(st.session_state.saved_watch_filters[selected_saved_filter])
            st.rerun()
        if saved_delete_col.button("🗑️ 削除", use_container_width=True, key="saved_watch_filter_delete"):
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
        st.caption("保存済み条件はまだありません。下で条件を作って保存できます。")

    st.divider()
    st.markdown("### ⚡ 条件プリセット")
    st.caption("よく使う観察条件をワンクリックでセットできます。数値は下で自由に変更できます。")

    preset1, preset2, preset3, preset4 = st.columns(4)

    if preset1.button("📈 上向き確認", use_container_width=True, key="watch_preset_up"):
        st.session_state.watch_score = 60.0
        st.session_state.watch_1m = 0.0
        st.session_state.watch_3m = 0.0
        st.session_state.watch_volume = 0.0
        st.session_state.watch_sma20 = True
        st.session_state.watch_sma60 = False

    if preset2.button("🧭 中期トレンド", use_container_width=True, key="watch_preset_mid"):
        st.session_state.watch_score = 60.0
        st.session_state.watch_1m = 0.0
        st.session_state.watch_3m = 5.0
        st.session_state.watch_volume = 0.0
        st.session_state.watch_sma20 = True
        st.session_state.watch_sma60 = True

    if preset3.button("🔊 出来高注目", use_container_width=True, key="watch_preset_volume"):
        st.session_state.watch_score = 0.0
        st.session_state.watch_1m = -100.0
        st.session_state.watch_3m = -100.0
        st.session_state.watch_volume = 1.5
        st.session_state.watch_sma20 = False
        st.session_state.watch_sma60 = False

    if preset4.button("↩️ リセット", use_container_width=True, key="watch_preset_reset"):
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
        help="直近出来高 ÷ 20日平均出来高。1.5なら20日平均の約1.5倍です。",
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
    )

    watch_limit = st.selectbox(
        "表示件数",
        [12, 24, 50],
        key="watch_limit",
        help="条件一致が多いときに、画面へ表示するカード数を切り替えます。",
    )

    save_name_col, save_button_col = st.columns([3, 1])
    watch_save_name = save_name_col.text_input(
        "現在の条件に名前を付ける",
        placeholder="例：出来高＋上向き",
        key="watch_save_name",
    ).strip()
    if save_button_col.button("💾 条件を保存", use_container_width=True, key="watch_save_button"):
        if not watch_save_name:
            st.warning("保存名を入力してください。")
        else:
            saved_name = watch_save_name[:40]
            st.session_state.saved_watch_filters[saved_name] = _watch_config_from_state()
            st.session_state.watch_filter_flash = f"『{saved_name}』を保存しました。"
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

    active_conditions = [f"Score {min_watch_score:.0f}以上"]
    if min_watch_1m > -100:
        active_conditions.append(f"1か月 {min_watch_1m:+.0f}%以上")
    if min_watch_3m > -100:
        active_conditions.append(f"3か月 {min_watch_3m:+.0f}%以上")
    if min_watch_volume > 0:
        active_conditions.append(f"出来高 {min_watch_volume:.1f}x以上")
    if watch_region != "すべて":
        active_conditions.append(f"地域 {watch_region}")
    if watch_sector_group != "すべて":
        active_conditions.append(f"業種 {watch_sector_group}")
    if only_above_sma20:
        active_conditions.append("20日線より上")
    if only_above_sma60:
        active_conditions.append("60日線より上")

    st.info("**現在の条件**：" + " ｜ ".join(active_conditions))

    r1, r2, r3, r4 = st.columns(4)
    r1.metric("🔎 条件一致", f"{len(watch_df)}社")
    if not watch_df.empty:
        r2.metric("🎯 平均Score", f"{watch_df['Atlas Score'].mean():.1f}")
        r3.metric("📈 平均1か月", f"{watch_df['1か月'].mean() * 100:+.2f}%")
        r4.metric("🔊 最大出来高", f"{watch_df['出来高倍率'].max():.2f}x")
    else:
        r2.metric("🎯 平均Score", "-")
        r3.metric("📈 平均1か月", "-")
        r4.metric("🔊 最大出来高", "-")

    if watch_df.empty:
        st.warning("現在の条件に一致する銘柄はありません。条件を少し緩めて確認してください。")
    else:
        st.caption(f"表示中：{len(watch_display_df)} / {len(watch_df)}社")

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
                f'<div class="mobile-detail-meta">{html.escape(str(watch_row["国"]))} ・ {html.escape(str(watch_row["業種グループ"]))}</div>'
                '</div>'
                f'<div class="mobile-detail-score">Score {float(watch_row["Atlas Score"]):.1f}</div>'
                '</div>'
                '<div class="mobile-detail-grid">'
                f'<div class="mobile-detail-item"><div class="mobile-detail-label">1か月</div><div class="mobile-detail-value">{one_month_text}</div></div>'
                f'<div class="mobile-detail-item"><div class="mobile-detail-label">3か月</div><div class="mobile-detail-value">{three_month_text}</div></div>'
                f'<div class="mobile-detail-item"><div class="mobile-detail-label">出来高倍率</div><div class="mobile-detail-value">{volume_text}</div></div>'
                f'<div class="mobile-detail-item"><div class="mobile-detail-label">20日線比</div><div class="mobile-detail-value">{sma20_text}</div></div>'
                '</div>'
                f'<div class="mobile-detail-judge">判定：{html.escape(str(watch_row["判定"]))}</div>'
                '</div>'
            )

        st.markdown(
            '<div class="atlas-card-grid">' + "".join(watch_cards) + '</div>',
            unsafe_allow_html=True,
        )

        with st.expander("📋 条件一致銘柄を表で見る"):
            watch_table = watch_df[[
                "順位", "会社名", "国", "業種グループ", "1か月", "3か月",
                "出来高倍率", "20日線比", "60日線比", "Atlas Score", "判定",
            ]].copy()
            for pct_col in ["1か月", "3か月", "20日線比", "60日線比"]:
                watch_table[pct_col] = (watch_table[pct_col] * 100).round(2)

            st.dataframe(
                watch_table,
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
        "※ 条件で探す機能はAtlas50内の現在データを機械的に絞り込む観察ツールです。"
        "条件一致は将来の上昇や投資成果を意味しません。"
    )


# ------------------------------
# Atlas設定の保存
# ------------------------------
with st.expander("💾 Atlas設定を保存"):
    st.caption("お気に入り・保有株・保存した検索条件・現在の検索条件を1つのJSONにまとめて保存します。")
    st.download_button(
        "⬇️ Atlas設定JSONを保存",
        data=_settings_json_bytes(),
        file_name="atlas50_settings.json",
        mime="application/json",
        use_container_width=True,
        key="atlas_setup_download_global",
    )
    st.caption("保有株だけを管理したい場合は、保有株タブのCSV保存/読込も利用できます。")

# ------------------------------
# エラー・注意書き
# ------------------------------
if errors:
    with st.expander("今回の取得エラー"):
        st.code("\n".join(errors[:50]))

st.divider()
st.caption(
    f"ATLAS 50 V{APP_VERSION} {APP_LABEL} ｜ "
    "Atlas Scoreは価格トレンドを整理するための学習・監視指標です。"
    "買い推奨・売り推奨・将来の利益保証ではありません。"
    "為替・株価・ニュースには遅延や取得失敗があり得ます。AI解説も必ず元データと合わせて確認してください。"
)

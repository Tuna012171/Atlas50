import math
from datetime import datetime
import pandas as pd
import streamlit as st
import yfinance as yf

st.set_page_config(page_title="Atlas 50", page_icon="🌍", layout="wide")
COMPANIES = [('NVDA', 'NVIDIA', '米国', '半導体'), ('AAPL', 'Apple', '米国', 'テクノロジー'), ('MSFT', 'Microsoft', '米国', 'ソフトウェア'), ('GOOGL', 'Alphabet', '米国', '通信・広告'), ('AMZN', 'Amazon', '米国', 'EC・クラウド'), ('AVGO', 'Broadcom', '米国', '半導体'), ('META', 'Meta Platforms', '米国', '通信・広告'), ('TSLA', 'Tesla', '米国', '自動車'), ('BRK-B', 'Berkshire Hathaway', '米国', '金融'), ('WMT', 'Walmart', '米国', '小売'), ('LLY', 'Eli Lilly', '米国', '医薬品'), ('JPM', 'JPMorgan Chase', '米国', '銀行'), ('XOM', 'Exxon Mobil', '米国', 'エネルギー'), ('JNJ', 'Johnson & Johnson', '米国', 'ヘルスケア'), ('V', 'Visa', '米国', '決済'), ('MA', 'Mastercard', '米国', '決済'), ('COST', 'Costco', '米国', '小売'), ('ORCL', 'Oracle', '米国', 'ソフトウェア'), ('AMD', 'AMD', '米国', '半導体'), ('CRM', 'Salesforce', '米国', 'ソフトウェア'), ('ASML', 'ASML', 'オランダ', '半導体装置'), ('SAP', 'SAP', 'ドイツ', 'ソフトウェア'), ('NVO', 'Novo Nordisk', 'デンマーク', '医薬品'), ('NVS', 'Novartis', 'スイス', '医薬品'), ('AZN', 'AstraZeneca', '英国', '医薬品'), ('SHEL', 'Shell', '英国', 'エネルギー'), ('HSBC', 'HSBC', '英国', '銀行'), ('UL', 'Unilever', '英国', '生活必需品'), ('MC.PA', 'LVMH', 'フランス', '高級消費財'), ('NESN.SW', 'Nestlé', 'スイス', '食品'), ('TSM', 'TSMC ADR', '台湾', '半導体'), ('0700.HK', 'Tencent', '中国', 'インターネット'), ('BABA', 'Alibaba ADR', '中国', 'EC・クラウド'), ('005930.KS', 'Samsung Electronics', '韓国', '半導体・電子'), ('7203.T', 'Toyota', '日本', '自動車'), ('6758.T', 'Sony Group', '日本', '電機・エンタメ'), ('8306.T', 'Mitsubishi UFJ FG', '日本', '銀行'), ('9984.T', 'SoftBank Group', '日本', '投資・通信'), ('6861.T', 'Keyence', '日本', 'FA・電子機器'), ('2330.TW', 'TSMC Taiwan', '台湾', '半導体'), ('000660.KS', 'SK hynix', '韓国', '半導体'), ('INFY', 'Infosys ADR', 'インド', 'ITサービス'), ('RELIANCE.NS', 'Reliance Industries', 'インド', '複合・エネルギー'), ('2222.SR', 'Saudi Aramco', 'サウジアラビア', 'エネルギー'), ('BHP', 'BHP ADR', 'オーストラリア', '資源'), ('RIO', 'Rio Tinto ADR', '英国/豪州', '資源'), ('SHOP', 'Shopify', 'カナダ', 'ECソフトウェア'), ('MELI', 'MercadoLibre', 'ウルグアイ', 'EC・フィンテック'), ('SE', 'Sea Ltd', 'シンガポール', 'EC・デジタル'), ('RELX', 'RELX', '英国', '情報サービス')]

@st.cache_data(ttl=3600, show_spinner=False)
def load_data():
    tickers=[x[0] for x in COMPANIES]
    raw=yf.download(tickers,period="1y",interval="1d",auto_adjust=True,repair=True,threads=True,group_by="ticker",progress=False,timeout=25)
    rows=[]
    for t,name,country,sector in COMPANIES:
        try:
            d=raw[t].dropna(subset=["Close"]).copy()
            c=d["Close"].astype(float); v=d["Volume"].astype(float)
            if len(c)<65: continue
            cur=float(c.iloc[-1])
            def ret(n): return cur/float(c.iloc[-n-1])-1
            s5=float(c.rolling(5).mean().iloc[-1]); s20=float(c.rolling(20).mean().iloc[-1]); s60=float(c.rolling(60).mean().iloc[-1])
            delta=c.diff(); gain=delta.clip(lower=0).rolling(14).mean(); loss=-delta.clip(upper=0).rolling(14).mean()
            rs=gain/loss.replace(0,float("nan")); rsi=float((100-(100/(1+rs))).iloc[-1])
            av=float(v.rolling(20).mean().iloc[-1]); vr=float(v.iloc[-1]/av) if av else 0
            high=float(c.max()); dh=cur/high-1
            r1d=ret(1); r1w=ret(5); r1m=ret(21); r3m=ret(63)
            score=0
            score+=max(0,min(12,6+r1w*120)); score+=max(0,min(15,7+r1m*60)); score+=max(0,min(15,7+r3m*30))
            score+=8 if cur>s20 else 0; score+=8 if cur>s60 else 0; score+=6 if s5>s20 else 0; score+=6 if s20>s60 else 0
            score+=10 if 45<=rsi<=68 else (6 if 35<=rsi<=75 else 2)
            score+=max(0,min(10,(vr-0.8)*8)); score+=10 if dh>=-.05 else (7 if dh>=-.10 else (4 if dh>=-.20 else 0))
            score=round(max(0,min(100,score)),1)
            signal="強い＋" if score>=75 else ("＋" if score>=60 else ("様子見" if score>=45 else "－"))
            rows.append([t,name,country,sector,cur,r1d,r1w,r1m,r3m,rsi,vr,cur/s20-1,cur/s60-1,dh,score,signal,d.index[-1].strftime("%Y-%m-%d")])
        except Exception:
            pass
    df=pd.DataFrame(rows,columns=["Ticker","会社名","国","業種","現在値","1日","1週","1か月","3か月","RSI","出来高倍率","20日線比","60日線比","高値乖離","Atlas Score","判定","最終日"])
    if not df.empty:
        df=df.sort_values("Atlas Score",ascending=False).reset_index(drop=True)
        df.insert(0,"順位",range(1,len(df)+1))
    return df

st.title("ATLAS 50")
st.caption("世界の注目50社を、数分で把握する。")
with st.spinner("世界50社をチェック中..."):
    df=load_data()

if df.empty:
    st.error("株価データを取得できませんでした。少し時間を置いて更新してください。")
    st.stop()

a,b,c,d=st.columns(4)
a.metric("監視企業",len(df))
b.metric("強い＋",int((df["判定"]=="強い＋").sum()))
c.metric("＋",int((df["判定"]=="＋").sum()))
d.metric("データ最終日",str(df["最終日"].max()))

st.subheader("世界ランキング")
f1,f2,f3=st.columns(3)
country=f1.selectbox("国",["すべて"]+sorted(df["国"].unique().tolist()))
sector=f2.selectbox("業種",["すべて"]+sorted(df["業種"].unique().tolist()))
minscore=f3.slider("最低Score",0,100,0)

view=df.copy()
if country!="すべて": view=view[view["国"]==country]
if sector!="すべて": view=view[view["業種"]==sector]
view=view[view["Atlas Score"]>=minscore]

display=view[["順位","会社名","国","業種","現在値","1日","1週","1か月","3か月","RSI","出来高倍率","Atlas Score","判定"]].copy()
for col in ["1日","1週","1か月","3か月"]:
    display[col]=(display[col]*100).round(2)
st.dataframe(display,use_container_width=True,hide_index=True,
    column_config={
      "現在値":st.column_config.NumberColumn(format="%.2f"),
      "1日":st.column_config.NumberColumn(format="%.2f%%"),
      "1週":st.column_config.NumberColumn(format="%.2f%%"),
      "1か月":st.column_config.NumberColumn(format="%.2f%%"),
      "3か月":st.column_config.NumberColumn(format="%.2f%%"),
      "Atlas Score":st.column_config.ProgressColumn(min_value=0,max_value=100,format="%.0f"),
    })

st.subheader("Score 上位10")
st.bar_chart(df.head(10).set_index("会社名")["Atlas Score"])

st.subheader("銘柄を見る")
selected=st.selectbox("会社",df["会社名"].tolist())
row=df[df["会社名"]==selected].iloc[0]
x1,x2,x3,x4=st.columns(4)
x1.metric("Atlas Score",f'{row["Atlas Score"]:.0f}')
x2.metric("判定",row["判定"])
x3.metric("1か月",f'{row["1か月"]*100:.2f}%')
x4.metric("3か月",f'{row["3か月"]*100:.2f}%')

st.info("Atlas Scoreは最近の価格トレンドを比較する学習・監視用の指標です。買い推奨や将来の利益保証ではありません。")

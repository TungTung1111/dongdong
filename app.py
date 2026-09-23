import pandas as pd
import requests
import streamlit as st
from datetime import date
import matplotlib.pyplot as plt

st.markdown(
    """
    <style>
    .stApp {
        background:
            radial-gradient(circle at top left, #eef3ff 0%, transparent 35%),
            radial-gradient(circle at top right, #eafaf4 0%, transparent 30%),
            #f7f9fc;
    }

    .main-title {
        text-align: center;
        font-size: 42px;
        font-weight: 800;
        margin-bottom: 6px;
    }

    .sub-title {
        text-align: center;
        color: #5f6b7a;
        font-size: 18px;
        margin-bottom: 28px;
    }

    .section-card {
        background-color: rgba(255, 255, 255, 0.88);
        padding: 20px;
        border-radius: 18px;
        border: 1px solid #e7eaf0;
        box-shadow: 0 6px 18px rgba(0,0,0,0.05);
        margin-bottom: 18px;
    }

    div[data-testid="stMetric"] {
        background-color: rgba(255, 255, 255, 0.95);
        padding: 18px;
        border-radius: 16px;
        border: 1px solid #e5e7eb;
        box-shadow: 0 5px 14px rgba(0,0,0,0.05);
    }

    div[data-testid="stMetricLabel"] {
        font-size: 15px;
    }

    div[data-testid="stMetricValue"] {
        font-size: 28px;
        font-weight: 700;
    }

    h2, h3 {
        margin-top: 1.3rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="main-title">📊 投資風險比較器</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="sub-title">'
    '用歷史資料比較兩檔股票的報酬、波動與價格走勢'
    '</div>',
    unsafe_allow_html=True,
)

def get_split_data(stock_id):

    url = "https://api.finmindtrade.com/api/v4/data"

    parameters = {
        "dataset": "TaiwanStockSplitPrice",
    }

    response = requests.get(
        url,
        params=parameters,
        timeout=15,
    )

    result = response.json()

    split_data = pd.DataFrame(result["data"])

    split_data = split_data[
        split_data["stock_id"] == stock_id
    ]

    split_data["date"] = pd.to_datetime(
        split_data["date"]
    )

    return split_data

def get_stock_data(stock_id, start_date, end_date):

    url = "https://api.finmindtrade.com/api/v4/data"

    parameters = {
        "dataset": "TaiwanStockPrice",
        "data_id": stock_id,
        "start_date": start_date,
        "end_date": end_date,
    }

    response = requests.get(
        url,
        params=parameters,
        timeout=15,
    )

    print("連線狀態：", response.status_code)

    result = response.json()

    stock_data = pd.DataFrame(result["data"])
    
    if stock_data.empty:
        return None

    stock_data = stock_data[["date", "close"]]

    stock_data["date"] = pd.to_datetime(stock_data["date"])
    
    split_data = get_split_data(stock_id)

    for _, split in split_data.iterrows():

        split_date = split["date"]

        if (
            split_date >= stock_data["date"].iloc[0]
            and
            split_date <= stock_data["date"].iloc[-1]
        ):

            split_ratio = (
                split["before_price"]
                / split["after_price"]
            )

            stock_data.loc[
                stock_data["date"] < split_date,
                "close"
            ] = (
                stock_data.loc[
                    stock_data["date"] < split_date,
                    "close"
                ]
                / split_ratio
            )

    stock_data["base_100"] = (
        stock_data["close"]
        / stock_data["close"].iloc[0]
        * 100
    )

    return stock_data

col1, col2 = st.columns(2)

with col1:
    stock_a = st.text_input(
        "股票 A",
        value="2330",
    )

with col2:
    stock_b = st.text_input(
        "股票 B",
        value="0050",
    )

date_col1, date_col2 = st.columns(2)

with date_col1:
    start_date = st.date_input(
        "開始日期",
        value=date(2026, 1, 1),
    )

with date_col2:
    end_date = st.date_input(
        "結束日期",
        value=date(2026, 1, 31),
    )


if st.button(
    "開始比較",
    use_container_width=True,
):
    
    if start_date >= end_date:
        st.error("開始日期必須早於結束日期。")
        st.stop()
        
        

    stock_a_data = get_stock_data(
        stock_a,
        str(start_date),
        str(end_date),
    )

    stock_b_data = get_stock_data(
        stock_b,
        str(start_date),
        str(end_date),
    )
    
    if stock_a_data is None or stock_b_data is None:
        st.error("找不到股票資料，請檢查股票代碼或日期範圍。")
        st.stop()

    stock_a_data = stock_a_data.rename(
        columns={
            "close": f"{stock_a}_close",
            "base_100": f"{stock_a}_base_100",
        }
    )

    stock_b_data = stock_b_data.rename(
        columns={
            "close": f"{stock_b}_close",
            "base_100": f"{stock_b}_base_100",
        }
    )

    comparison = pd.merge(
        stock_a_data,
        stock_b_data,
        on="date",
        how="inner",
    )

    comparison[f"{stock_a}_return"] = (
        comparison[f"{stock_a}_close"].pct_change()
    )

    comparison[f"{stock_b}_return"] = (
        comparison[f"{stock_b}_close"].pct_change()
    )

    return_a = (
        comparison[f"{stock_a}_close"].iloc[-1]
        / comparison[f"{stock_a}_close"].iloc[0]
        - 1
    )

    return_b = (
        comparison[f"{stock_b}_close"].iloc[-1]
        / comparison[f"{stock_b}_close"].iloc[0]
        - 1
    )

    mean_a = comparison[f"{stock_a}_return"].mean()
    mean_b = comparison[f"{stock_b}_return"].mean()

    std_a = comparison[f"{stock_a}_return"].std()
    std_b = comparison[f"{stock_b}_return"].std()
    
    running_max_a = comparison[f"{stock_a}_close"].cummax()

    drawdown_a = (
        comparison[f"{stock_a}_close"]
        / running_max_a
        - 1
    )

    max_drawdown_a = drawdown_a.min()
    
    running_max_b = comparison[f"{stock_b}_close"].cummax()

    drawdown_b = (
        comparison[f"{stock_b}_close"]
        / running_max_b
        - 1
    )

    max_drawdown_b = drawdown_b.min()
    
    annual_vol_a = std_a * (252 ** 0.5)
    annual_vol_b = std_b * (252 ** 0.5)
    
    win_rate_a = (
        comparison[f"{stock_a}_return"].dropna() > 0
    ).mean()

    win_rate_b = (
        comparison[f"{stock_b}_return"].dropna() > 0
    ).mean()
    
    with st.expander("查看原始股價資料"):

        st.write(f"{stock_a} 資料")
        st.dataframe(
            stock_a_data,
            height=250,
            use_container_width=True,
        )

        st.write(f"{stock_b} 資料")
        st.dataframe(
            stock_b_data,
            height=250,
            use_container_width=True,
        )

    st.subheader("比較結果")
    
    col1, col2 = st.columns(2)

    with col1:
        st.subheader(stock_a)
        st.metric("累積報酬率", f"{return_a:.2%}")
        st.metric("平均日報酬率", f"{mean_a:.2%}")
        st.metric("日報酬標準差", f"{std_a:.2%}")
        st.metric(
            "最大回撤",
            f"{max_drawdown_a:.2%}"
        )
        st.metric(
            "年化波動率",
            f"{annual_vol_a:.2%}"
        )
        st.metric(
            "正報酬天數比例",
            f"{win_rate_a:.2%}"
        )

    with col2:
        st.subheader(stock_b)
        st.metric("累積報酬率", f"{return_b:.2%}")
        st.metric("平均日報酬率", f"{mean_b:.2%}")
        st.metric("日報酬標準差", f"{std_b:.2%}")
        st.metric(
            "最大回撤",
            f"{max_drawdown_b:.2%}"
        )
        st.metric(
            "年化波動率",
            f"{annual_vol_b:.2%}"
        )
        st.metric(
            "正報酬天數比例",
            f"{win_rate_b:.2%}"
        )
                
    st.caption(
        "年化波動率是將所選期間的每日波動換算成年尺度。  \n"
        "若觀察期間很短且剛好遇到劇烈行情，年化結果可能偏高。"
    )

    st.subheader("Base 100 價格走勢")
    
    fig, ax = plt.subplots()
    
    ax.plot(
          comparison["date"],
          comparison[f"{stock_a}_base_100"],
          label=stock_a,
          )
    
    ax.plot(
          comparison["date"],
          comparison[f"{stock_b}_base_100"],
          label=stock_b,
          )
    
    ax.set_xlabel("Date")
    ax.set_ylabel("Base 100")
    ax.set_title(f"{stock_a} vs {stock_b}")
    
    ax.legend() #顯示圖例
    ax.grid() #標示格線
    
    fig.autofmt_xdate()
    st.pyplot(fig)


    st.subheader("結果解讀")

    if return_a > return_b:
        better_return = stock_a
    else:
        better_return = stock_b

    if std_a > std_b:
        higher_risk = stock_a
    else:
        higher_risk = stock_b

    st.write(
        f"在這段期間內，{better_return} 的累積報酬較高；"
        f"{higher_risk} 的日報酬波動較大"
    )
    
    if max_drawdown_a > max_drawdown_b:
        smaller_drawdown = stock_a
    else:
        smaller_drawdown = stock_b
    
    st.write(
        f"{smaller_drawdown} 的最大回撤較小，"
        f"代表這段期間內從歷史高點下跌的幅度相對較低。"
    )


st.caption(
    "本工具使用歷史收盤價計算報酬與波動，"
    "結果僅供學習與比較使用，不構成投資建議。"
)
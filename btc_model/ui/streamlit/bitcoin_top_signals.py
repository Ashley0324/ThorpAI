import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 页面标题
st.set_page_config(page_title="比特币逃顶策略监控", layout="wide")
st.title("比特币逃顶策略监控")

# 上传数据
uploaded_file = st.file_uploader("上传预处理好的CSV文件", type=["csv"])
if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    df['date'] = pd.to_datetime(df['date'])  # 确保日期格式正确

    # 显示数据
    st.subheader("数据预览")
    st.write(df.tail())

    # 信号统计
    st.subheader("信号统计")
    col1, col2, col3 = st.columns(3)
    col1.metric("总逃顶信号数", len(df[df['combined_signal']]))
    col2.metric("最新价格", f"${df['close'].iloc[-1]:.2f}")
    col3.metric("当前RSI", f"{df['rsi'].iloc[-1]:.1f}")

    # 主图表：价格与逃顶信号
    st.subheader("价格与逃顶信号")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df['date'], y=df['close'], mode='lines', name='价格'))
    fig.add_trace(go.Scatter(
        x=df[df['combined_signal']]['date'],
        y=df[df['combined_signal']]['close'],
        mode='markers',
        marker=dict(color='red', size=10),
        name='逃顶信号'
    ))
    fig.update_layout(
        xaxis_title="日期",
        yaxis_title="价格",
        hovermode="x unified"
    )
    st.plotly_chart(fig, use_container_width=True)

    # 指标图表
    st.subheader("指标分析")
    tab1, tab2, tab3 = st.tabs(["RSI", "MACD", "布林带"])

    with tab1:
        st.write("RSI指标（超买阈值：70）")
        fig_rsi = go.Figure()
        fig_rsi.add_trace(go.Scatter(x=df['date'], y=df['rsi'], mode='lines', name='RSI'))
        fig_rsi.add_hline(y=70, line_dash="dot", line_color="orange")
        st.plotly_chart(fig_rsi, use_container_width=True)

    with tab2:
        st.write("MACD指标")
        fig_macd = go.Figure()
        fig_macd.add_trace(go.Scatter(x=df['date'], y=df['macd'], mode='lines', name='MACD'))
        fig_macd.add_trace(go.Scatter(x=df['date'], y=df['macd_signal'], mode='lines', name='Signal'))
        fig_macd.add_trace(go.Bar(
            x=df['date'],
            y=df['macd'] - df['macd_signal'],
            name='Histogram',
            marker_color=np.where((df['macd'] - df['macd_signal']) > 0, 'green', 'red')
        ))
        st.plotly_chart(fig_macd, use_container_width=True)

    with tab3:
        st.write("布林带指标")
        fig_boll = go.Figure()
        fig_boll.add_trace(go.Scatter(x=df['date'], y=df['close'], mode='lines', name='价格'))
        fig_boll.add_trace(go.Scatter(
            x=df['date'],
            y=df['bollinger_upper'],
            mode='lines',
            line=dict(color='gray', dash='dot'),
            name='上轨'
        ))
        st.plotly_chart(fig_boll, use_container_width=True)

    # 逃顶信号详情
    st.subheader("逃顶信号详情")
    st.write(df[df['combined_signal']][['date', 'close', 'mayer_multiple', 'rsi', 'macd', 'bollinger_upper']])

else:
    st.info("请上传预处理好的CSV文件以开始分析。")
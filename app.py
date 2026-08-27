# -*- coding: utf-8 -*-
"""
运营日报自动化工具
==================

【项目背景】
    在语音平台实习时，主管每天让实习生从后台把数据抄到 Excel：
    日期、在线人数、新进入人数、付费人数、流水、平均停留时长。
    然后还要手动算转化率、画折线图，再发到工作群里。
    这些事重复性太高，所以做了这个工具：
    上传 Excel/CSV，自动算指标、画图、生成日报。

【怎么用】
    1. 安装依赖：pip install -r requirements.txt
    2. 启动：    streamlit run app.py
    3. 上传 CSV 或 Excel 文件（列名见下方 REQUIRED_COLUMNS）
    4. 看板自动出指标卡片和图表，点「生成今日日报」下载 HTML 报告

【文件列名要求】
    日期、在线人数、新进入人数、付费人数、流水(元)、停留时长(分钟)
"""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# ==================== 基本配置 ====================

# 上传文件必须包含这些列（列名要一模一样）
REQUIRED_COLUMNS = ["日期", "在线人数", "新进入人数", "付费人数", "流水(元)", "停留时长(分钟)"]

# 页面设置（layout="wide" 让页面更宽，能放下左右两栏）
st.set_page_config(page_title="运营日报自动化工具", layout="wide")
st.title("运营日报自动化工具")


# ==================== 数据处理函数 ====================

def load_data(uploaded_file):
    """根据文件后缀，用 pandas 把文件读成表格（DataFrame）"""
    name = uploaded_file.name
    if name.endswith(".csv"):
        # CSV 有中文编码问题：先试 utf-8-sig（能兼容带/不带 BOM 的 UTF-8），
        # 失败再试 gbk（Windows 上的 Excel 常用这种编码）
        try:
            df = pd.read_csv(uploaded_file, encoding="utf-8-sig")
        except UnicodeDecodeError:
            df = pd.read_csv(uploaded_file, encoding="gbk")
    else:
        # Excel 文件（.xlsx）
        df = pd.read_excel(uploaded_file)
    return df


def add_metrics(df):
    """
    追加两个自动计算的指标列：
      付费转化率(%) = 付费人数 / 新进入人数 * 100
      人均流水(元)  = 流水(元) / 在线人数
    如果文件里本来就有这两列，就不重复计算。
    """
    df = df.copy()
    if "付费转化率(%)" not in df.columns:
        df["付费转化率(%)"] = df["付费人数"] / df["新进入人数"] * 100
    if "人均流水(元)" not in df.columns:
        df["人均流水(元)"] = df["流水(元)"] / df["在线人数"]
    return df


def prepare_data(df):
    """把日期列转成日期类型，并按日期从小到大排序"""
    df = df.copy()
    df["日期"] = pd.to_datetime(df["日期"])
    df = df.sort_values("日期").reset_index(drop=True)
    return df


def get_stats(df):
    """返回最新一天、昨天，以及 4 个指标的环比（今天 - 昨天）"""
    latest = df.iloc[-1]   # 最后一行 = 最新一天
    prev = df.iloc[-2]     # 倒数第二行 = 昨天
    return {
        "latest": latest,
        "prev": prev,
        "在线环比": latest["在线人数"] - prev["在线人数"],
        "转化率环比": latest["付费转化率(%)"] - prev["付费转化率(%)"],
        "人均流水环比": latest["人均流水(元)"] - prev["人均流水(元)"],
        "停留环比": latest["停留时长(分钟)"] - prev["停留时长(分钟)"],
    }


# ==================== 画图函数 ====================

def make_line_chart(x, y, title, y_title, color):
    """折线图"""
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=x, y=y,
        mode="lines+markers",
        line=dict(color=color, width=2),
        marker=dict(size=6),
    ))
    fig.update_layout(
        title=title,
        xaxis_title="日期",
        yaxis_title=y_title,
        template="plotly_white",
        height=320,
        margin=dict(l=50, r=20, t=50, b=40),
    )
    return fig


def make_bar_chart(x, y, title, y_title, color):
    """柱状图"""
    fig = go.Figure(go.Bar(x=x, y=y, marker_color=color))
    fig.update_layout(
        title=title,
        xaxis_title="日期",
        yaxis_title=y_title,
        template="plotly_white",
        height=320,
        margin=dict(l=50, r=20, t=50, b=40),
    )
    return fig


# ==================== 生成日报 HTML ====================

def build_report(df, stats, fig_online, fig_conv, fig_rev):
    """把指标卡片 + 三张图拼成一个完整的 HTML 日报"""
    latest = stats["latest"]
    date_str = latest["日期"].strftime("%Y-%m-%d")

    # 把三张图转成 HTML 片段。
    # 第一张图 include_plotlyjs=True：把绘图库一起打包进去，这样日报离线也能打开看图表。
    fig1_html = fig_online.to_html(full_html=False, include_plotlyjs=True)
    fig2_html = fig_conv.to_html(full_html=False, include_plotlyjs=False)
    fig3_html = fig_rev.to_html(full_html=False, include_plotlyjs=False)

    # 取出环比数值
    online_delta = stats["在线环比"]
    conv_delta = stats["转化率环比"]
    arpu_delta = stats["人均流水环比"]
    stay_delta = stats["停留环比"]

    # 生成一个指标卡片的 HTML（up=True 表示涨，绿色；否则跌，红色）
    def card(label, value, delta_text, up):
        cls = "up" if up else "down"
        return f'''
        <div class="card">
          <div class="label">{label}</div>
          <div class="value">{value}</div>
          <div class="delta {cls}">环比 {delta_text}</div>
        </div>'''

    cards = (
        card("在线人数", f"{int(latest['在线人数']):,}", f"{online_delta:+,}", online_delta >= 0)
        + card("付费转化率", f"{latest['付费转化率(%)']:.2f}%", f"{conv_delta:+.2f}%", conv_delta >= 0)
        + card("人均流水", f"{latest['人均流水(元)']:.2f} 元", f"{arpu_delta:+.2f} 元", arpu_delta >= 0)
        + card("平均停留时长", f"{latest['停留时长(分钟)']:.1f} 分钟", f"{stay_delta:+.1f} 分钟", stay_delta >= 0)
    )

    # 日报的样式（简洁、专业）
    css = """
    <style>
      body { font-family: "Microsoft YaHei", "PingFang SC", sans-serif; margin: 40px; color: #222; background: #fafafa; }
      h1 { text-align: center; font-size: 28px; }
      .date { text-align: center; color: #888; margin-bottom: 24px; }
      .cards { display: flex; gap: 16px; margin: 24px 0; }
      .card { flex: 1; background: #fff; border: 1px solid #eee; border-radius: 8px; padding: 18px; text-align: center; }
      .card .label { color: #888; font-size: 14px; }
      .card .value { font-size: 26px; font-weight: bold; margin: 8px 0; }
      .card .delta { font-size: 13px; }
      .up { color: #2e7d32; }
      .down { color: #c62828; }
      .chart { background: #fff; border: 1px solid #eee; border-radius: 8px; padding: 12px; margin: 16px 0; }
    </style>
    """

    # 拼成完整 HTML 文件
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<title>运营日报 {date_str}</title>
{css}
</head>
<body>
<h1>运营日报</h1>
<div class="date">{date_str}</div>
<div class="cards">{cards}</div>
<div class="chart">{fig1_html}</div>
<div class="chart">{fig2_html}</div>
<div class="chart">{fig3_html}</div>
</body>
</html>"""
    return html


# ==================== 页面主流程 ====================

# 上传文件（放在最顶部，方便随时更换数据）
uploaded_file = st.file_uploader(
    "上传数据文件（CSV 或 Excel）",
    type=["csv", "xlsx"],
    help="列名要求：日期、在线人数、新进入人数、付费人数、流水(元)、停留时长(分钟)",
)

# 还没上传文件时，给出提示并停止
if uploaded_file is None:
    st.info("请上传 CSV 或 Excel 文件。\n\n没有示例数据？可以先运行 `python 生成示例数据.py` 生成一份。")
    st.stop()

# 1. 读文件
df = load_data(uploaded_file)

# 2. 检查列名是否齐全
missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
if missing:
    st.error(f"文件缺少以下列：{missing}\n\n当前文件的列名是：{list(df.columns)}")
    st.stop()

# 3. 按日期排序
df = prepare_data(df)

# 4. 至少要 2 行（今天 + 昨天）才能算环比
if len(df) < 2:
    st.error("数据至少需要 2 行（今天和昨天），才能计算环比。")
    st.stop()

# 5. 计算指标
df = add_metrics(df)
stats = get_stats(df)
latest = stats["latest"]

# 先画好三张图（页面展示和日报导出共用同一批图，避免重复画）
recent = df.tail(7)  # 取最近 7 天
x = recent["日期"].dt.strftime("%m-%d").tolist()  # 横轴只显示「月-日」

fig_online = make_line_chart(x, recent["在线人数"], "近 7 天在线人数趋势", "在线人数", "#1f77b4")
fig_conv = make_line_chart(x, recent["付费转化率(%)"], "近 7 天付费转化率趋势", "付费转化率(%)", "#ff7f0e")
fig_rev = make_bar_chart(x, recent["流水(元)"], "近 7 天每日流水", "流水(元)", "#2ca02c")

# ==================== 顶部：4 个核心指标卡片 ====================
st.markdown(f"### 核心指标（最新一天：{latest['日期'].strftime('%Y-%m-%d')}）")

c1, c2, c3, c4 = st.columns(4)

# st.metric 的 delta 会自动显示「涨绿、跌红」的箭头
c1.metric("在线人数", f"{int(latest['在线人数']):,}", int(stats["在线环比"]))
c2.metric("付费转化率", f"{latest['付费转化率(%)']:.2f}%", round(stats["转化率环比"], 2))
c3.metric("人均流水", f"{latest['人均流水(元)']:.2f} 元", round(stats["人均流水环比"], 2))
c4.metric("平均停留时长", f"{latest['停留时长(分钟)']:.1f} 分钟", round(stats["停留环比"], 1))

st.markdown("---")

# ==================== 左右两栏：左数据，右图表 ====================
left, right = st.columns([1, 1.6])

with left:
    st.subheader("原始数据（前 5 行）")
    st.dataframe(df.head(), width="stretch")
    st.caption(f"共 {len(df)} 行数据，最新一天是 {latest['日期'].strftime('%Y-%m-%d')}")

    # 一键导出日报（HTML 格式，内含图表，双击即可用浏览器打开）
    report_html = build_report(df, stats, fig_online, fig_conv, fig_rev)
    st.download_button(
        "生成今日日报",
        data=report_html,
        file_name=f"运营日报_{latest['日期'].strftime('%Y-%m-%d')}.html",
        mime="text/html",
    )

with right:
    st.subheader("近 7 天在线人数趋势")
    st.plotly_chart(fig_online, width="stretch")

    st.subheader("近 7 天付费转化率趋势")
    st.plotly_chart(fig_conv, width="stretch")

    st.subheader("近 7 天每日流水")
    st.plotly_chart(fig_rev, width="stretch")

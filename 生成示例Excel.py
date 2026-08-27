# -*- coding: utf-8 -*-
"""
生成示例Excel.py
================
生成一份「示例数据.xlsx」，方便测试看板。

运行：
    python 生成示例Excel.py

会生成包含 30 天数据的 示例数据.xlsx，列名和看板要求一致。
"""

import random

import pandas as pd

random.seed(42)  # 固定随机种子，和 CSV 版生成一样的数据

# 最近 30 天（今天 2026-08-27），日期用「年-月-日」的字符串，最稳妥
dates = pd.date_range("2026-07-29", periods=30, freq="D")

rows = []
for i, d in enumerate(dates):
    online = random.randint(2500, 4000) + i * 15   # 在线人数
    new_users = random.randint(800, 1500)          # 新进入人数
    pay_users = int(new_users * random.uniform(0.08, 0.15))  # 付费人数
    revenue = round(pay_users * random.uniform(15, 40), 2)   # 流水(元)
    stay = round(random.uniform(18, 35), 1)                  # 停留时长(分钟)

    rows.append({
        "日期": d.strftime("%Y-%m-%d"),
        "在线人数": online,
        "新进入人数": new_users,
        "付费人数": pay_users,
        "流水(元)": revenue,
        "停留时长(分钟)": stay,
    })

df = pd.DataFrame(rows)
df.to_excel("示例数据.xlsx", index=False)
print("已生成 示例数据.xlsx，共", len(df), "行")
print("列名：", list(df.columns))

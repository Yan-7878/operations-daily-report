# -*- coding: utf-8 -*-
"""
生成示例数据.py
================
生成一份「示例数据.csv」，方便你测试看板。

运行：
    python 生成示例数据.py

会生成包含 30 天数据的 示例数据.csv，列名和看板要求一致。
（本脚本只用 Python 自带的标准库，不需要安装任何东西）
"""

import csv
import random
from datetime import datetime, timedelta

random.seed(42)  # 固定随机种子，每次生成的数据一样，方便对比

# 表头（和看板要求的列名一致）
columns = ["日期", "在线人数", "新进入人数", "付费人数", "流水(元)", "停留时长(分钟)"]

# 从 2026-07-29 开始，连续 30 天
start = datetime(2026, 7, 29)

rows = []
for i in range(30):
    d = start + timedelta(days=i)

    # 在线人数：2500~4000 之间波动，整体缓慢上升
    online = random.randint(2500, 4000) + i * 15
    # 新进入人数
    new_users = random.randint(800, 1500)
    # 付费人数：约 8%~15% 的新用户会付费
    pay_users = int(new_users * random.uniform(0.08, 0.15))
    # 流水：每个付费用户平均贡献 15~40 元
    revenue = round(pay_users * random.uniform(15, 40), 2)
    # 平均停留时长：18~35 分钟
    stay = round(random.uniform(18, 35), 1)

    rows.append([
        d.strftime("%Y-%m-%d"),
        online,
        new_users,
        pay_users,
        revenue,
        stay,
    ])

# 写入 CSV（utf-8-sig 带 BOM，Excel 打开中文不会乱码）
with open("示例数据.csv", "w", newline="", encoding="utf-8-sig") as f:
    writer = csv.writer(f)
    writer.writerow(columns)
    writer.writerows(rows)

print(f"已生成 示例数据.csv，共 {len(rows)} 行")
print("前 5 行预览：")
print("  " + " | ".join(columns))
for r in rows[:5]:
    print("  " + " | ".join(str(x) for x in r))

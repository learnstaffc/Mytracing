"""项目参数配置：数据文件路径、列映射、存款计划参数。

如需更换你的资产负债文件，只需修改 ASSET_FILE 与 SHEET；
外币列在 FX_RATES 中配置汇率（折算为人民币）。
"""
from pathlib import Path

# ========== 数据文件（xlsx 放在项目外，通过路径读取） ==========
ASSET_FILE = "/mnt/d/learning.xlsx"   # 你的资产负债记录文件（绝对路径）
SHEET = "record"                      # 读取的 sheet 名

# ========== 列映射 ==========
DATE_COL = "日期"                                     # 日期列（每月 1 号记一次）
ASSET_COLUMNS = ["ZSBank", "WeFinace", "A-inv", "US-inv"]  # 资产列（人民币）
FX_RATES = {"US-inv": 6.6}                            # 外币资产列 -> 汇率（折算成人民币）
LIABILITY_COLUMNS = ["Credit"]                        # 负债列
# 说明：净资产 = Σ(资产列 × 汇率) - Σ(负债列)

# ========== 存款计划参数 ==========
INITIAL_BALANCE = 150_000     # 初始本金 15 万
MONTHLY_DEPOSIT = 10_000      # 默认每月月初存入 1 万（供 projection 默认值使用）
TARGET = 1_000_000            # 目标：净资产达到 100 万

# 计划场景：月存金额 × 年化收益率 的组合（feature: 1万/1.5万 × 5%/10%）
PLAN_SCENARIOS = [
    {"deposit": 10_000, "rate": 0.05, "label": "月存1万 · 5%"},
    {"deposit": 10_000, "rate": 0.10, "label": "月存1万 · 10%"},
    {"deposit": 15_000, "rate": 0.05, "label": "月存1.5万 · 5%"},
    {"deposit": 15_000, "rate": 0.10, "label": "月存1.5万 · 10%"},
]

# ========== 输出 ==========
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "output"
OUTPUT_PNG = OUTPUT_DIR / "net_asset_plan.png"          # 主图：实际 + 4 条计划线 + 目标线
OUTPUT_ACCOUNTS_PNG = OUTPUT_DIR / "accounts_trend.png" # 各资产账户月度变化
OUTPUT_YEARLY_PNG = OUTPUT_DIR / "yearly_compare.png"   # 每年内 4 条理想线 + 实际线
OUTPUT_DELTA_PNG = OUTPUT_DIR / "net_assets_delta.png"  # 净资产总值变化 + 每月环比增减

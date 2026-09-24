"""绘图：实际净资产曲线 + 5%/10% 存款计划曲线 + 100 万目标线 + 达标标注。

时间轴统一从最早记录日期开始，实际数据与计划曲线画在同一张图上。
"""
import glob as _glob
import warnings
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
import pandas as pd

from . import config
from .projection import milestone

CJK_FONT_CANDIDATES = [
    "Noto Sans CJK SC", "Noto Sans CJK JP", "Noto Sans CJK TC",
    "WenQuanYi Micro Hei", "WenQuanYi Zen Hei", "SimHei", "Microsoft YaHei",
]

# matplotlib 默认扫不到系统 CJK 字体时，手动注册这些常见字体文件
CJK_FONT_FILE_GLOBS = [
    "/usr/share/fonts/**/*Noto*CJK*.ttc",
    "/usr/share/fonts/**/wqy*.ttc",
    "/usr/share/fonts/**/simhei*.ttf",
    "/usr/share/fonts/**/*YaHei*.ttc",
    "/usr/share/fonts/**/*yahei*.ttf",
    "/usr/share/fonts/**/*source*han*sans*.otf",
]


def _register_cjk_fonts() -> None:
    """把系统里的 CJK 字体文件手动注册给 matplotlib，保证中文/数字/字母都可用。"""
    for pattern in CJK_FONT_FILE_GLOBS:
        for p in _glob.glob(pattern, recursive=True):
            try:
                fm.fontManager.addfont(p)
            except Exception:
                continue


def _setup_cjk_font() -> None:
    _register_cjk_fonts()
    available = {f.name for f in fm.fontManager.ttflist}
    chosen = next((name for name in CJK_FONT_CANDIDATES if name in available), None)
    if chosen is None:
        warnings.warn("未找到中文字体，图表标签可能显示为方块。可安装 fonts-noto-cjk。")
    else:
        plt.rcParams["font.sans-serif"] = [chosen, "DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False
    return chosen


def _fmt_wan(value: float, _pos=None, decimals: int = 0) -> str:
    """把金额格式化成「万元」。decimals 控制小数位，小于万元的量级需要更多位数。"""
    return f"{value / 10000:,.{decimals}f}万"


# 场景配色：(月存, 年化) -> 颜色
SCENARIO_COLORS = {
    (10_000, 0.05): "#e67e22",   # 月存1万 · 5%  （橙）
    (10_000, 0.10): "#27ae60",   # 月存1万 · 10% （绿）
    (15_000, 0.05): "#8e44ad",   # 月存1.5万 · 5%（紫）
    (15_000, 0.10): "#16a085",   # 月存1.5万 ·10%（青）
}
ACTUAL_COLOR = "#2f6db5"
TARGET_COLOR = "#c0392b"


# 账户趋势图配色：账户数不多时用这套固定色，超出长度则改用 tab20 均匀取色
# 注意历史上日期列占了索引 0，所以第一个数据列从索引 1 开始，这里保持原样以免图变色
ACCOUNT_PALETTE = ["#2f6db5", "#e67e22", "#27ae60", "#16a085", "#c0392b", "#8e44ad", "#7f8c8d"]


def _account_colors(count: int) -> list:
    """给 count 个账户分配互不重复的颜色。"""
    if count <= len(ACCOUNT_PALETTE):
        return [ACCOUNT_PALETTE[(i + 1) % len(ACCOUNT_PALETTE)] for i in range(count)]
    cmap = matplotlib.colormaps["tab20"].resampled(count)
    return [cmap(i) for i in range(count)]


def _scenario_label(deposit: float, rate: float) -> str:
    for s in config.PLAN_SCENARIOS:
        if s["deposit"] == deposit and abs(s["rate"] - rate) < 1e-9:
            return s["label"]
    return f"月存{deposit/10000:.1f}万 · {rate*100:.0f}%"


def _mkdir(out_path: str) -> str:
    out_path = str(out_path)
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    return out_path


def render(actual: pd.DataFrame, curves: dict[tuple[float, float], pd.DataFrame],
           out_path=None) -> str:
    """主图：实际净资产 + 4 条计划曲线（1万/1.5万 × 5%/10%）+ 100 万目标线 + 达标标注。"""
    _setup_cjk_font()
    out_path = _mkdir(out_path or config.OUTPUT_PNG)
    fig, ax = plt.subplots(figsize=(13, 7.5), dpi=130)

    start_date = actual["日期"].min()

    # ---- 实际净资产曲线 ----
    ax.plot(actual["日期"], actual["净资产"], marker="o", linewidth=2,
            color=ACTUAL_COLOR, label="实际净资产", zorder=6)
    last_pt = actual.iloc[-1]
    ax.annotate(f"{last_pt['净资产'] / 10000:,.1f}万",
                (last_pt["日期"], last_pt["净资产"]),
                textcoords="offset points", xytext=(6, 6), fontsize=9,
                color=ACTUAL_COLOR)

    # ---- 目标线 ----
    ax.axhline(config.TARGET, color=TARGET_COLOR, linestyle="--", linewidth=1.2,
               label=f"目标 {config.TARGET / 10000:,.0f}万")

    # ---- 4 条存款计划曲线 ----
    # 达标点沿目标线从左到右排开，文字上/下交错避免重叠
    milestones = []
    for (deposit, rate), curve in sorted(curves.items()):
        color = SCENARIO_COLORS.get((deposit, rate), "#888888")
        label = _scenario_label(deposit, rate)
        ax.plot(curve["日期"], curve["余额"], linewidth=2, color=color,
                label=f"计划 {label}", zorder=5)
        m = milestone(curve)
        if m is not None:
            milestones.append((deposit, rate, m))

    for i, (deposit, rate, m) in enumerate(milestones):
        color = SCENARIO_COLORS.get((deposit, rate), "#888888")
        ax.scatter([m["日期"]], [m["余额"]], color=color, zorder=7, s=45)
        ax.axvline(m["日期"], color=color, linestyle=":", linewidth=1, alpha=0.6)
        label = f"{_scenario_label(deposit, rate)}: {m['日期'].strftime('%Y-%m')}"
        offset = 14 if i % 2 == 0 else -24
        # 白底避免文字压在目标虚线上看不清
        ax.annotate(label, xy=(m["日期"], m["余额"]),
                    xytext=(6, offset), textcoords="offset points",
                    fontsize=9, color=color, fontweight="bold",
                    bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="none", alpha=0.78))

    # ---- 坐标轴美化 ----
    ax.set_title("个人净资产 vs 存款计划（初始15万，月存1万/1.5万 × 5%/10%）",
                 fontsize=14, pad=14)
    ax.set_xlabel("日期", fontsize=11)
    ax.set_ylabel("金额（万元）", fontsize=11)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(_fmt_wan))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=6))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    ax.grid(True, which="both", linestyle="--", linewidth=0.5, alpha=0.5)
    ax.legend(loc="upper left", fontsize=9.5, ncol=2)
    fig.autofmt_xdate()

    # 右侧留白，避免最右侧那个达标标签被画布边缘裁掉
    last_date = max([actual["日期"].max()] + [m["日期"] for _, _, m in milestones])
    span_days = (last_date - start_date).days or 1
    ax.set_xlim(start_date - pd.Timedelta(days=span_days * 0.02),
                last_date + pd.Timedelta(days=span_days * 0.12))

    fig.tight_layout()
    fig.savefig(out_path, bbox_inches="tight")
    plt.close(fig)
    return out_path


def render_accounts(accounts: pd.DataFrame, out_path=None) -> str:
    """有记录以来，各资产/负债账户的月度变化折线图（单位：人民币）。"""
    _setup_cjk_font()
    out_path = _mkdir(out_path or config.OUTPUT_ACCOUNTS_PNG)
    fig, ax = plt.subplots(figsize=(12, 7), dpi=130)

    cols = [c for c in accounts.columns if c != "日期"]
    colors = _account_colors(len(cols))
    for i, col in enumerate(cols):
        color = colors[i]
        if col in config.LIABILITY_COLUMNS:
            # 负债用虚线
            ax.plot(accounts["日期"], accounts[col], marker="o", linewidth=2,
                    linestyle="--", color=color, label=f"{col}（负债）")
        else:
            ax.plot(accounts["日期"], accounts[col], marker="o", linewidth=2,
                    color=color, label=col)

    ax.set_title("各资产账户月度变化（人民币，US-inv 按汇率折算）", fontsize=14, pad=14)
    ax.set_xlabel("日期", fontsize=11)
    ax.set_ylabel("金额（万元）", fontsize=11)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(_fmt_wan))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    ax.grid(True, which="both", linestyle="--", linewidth=0.5, alpha=0.5)
    ax.legend(loc="best", fontsize=10)
    fig.autofmt_xdate()

    fig.tight_layout()
    fig.savefig(out_path, bbox_inches="tight")
    plt.close(fig)
    return out_path


def render_yearly(actual: pd.DataFrame, curves: dict[tuple[float, float], pd.DataFrame],
                  out_path=None) -> str:
    """每个有记录的年度一张子图：该年内 4 条理想计划线 + 实际净资产线。"""
    _setup_cjk_font()
    out_path = _mkdir(out_path or config.OUTPUT_YEARLY_PNG)

    years = sorted(actual["日期"].dt.year.unique())
    fig, axes = plt.subplots(len(years), 1, figsize=(12, 4.6 * len(years)),
                             dpi=130, squeeze=False)
    if len(years) == 0:
        plt.close(fig)
        return out_path

    for ax, year in zip(axes[:, 0], years):
        # 该年度实际净资产
        mask_a = actual["日期"].dt.year == year
        ax.plot(actual.loc[mask_a, "日期"], actual.loc[mask_a, "净资产"],
                marker="o", linewidth=2.2, color=ACTUAL_COLOR, label="实际净资产", zorder=6)

        # 4 条理想计划线（截取该年度区间）
        for (deposit, rate), curve in sorted(curves.items()):
            color = SCENARIO_COLORS.get((deposit, rate), "#888888")
            label = _scenario_label(deposit, rate)
            mask_c = curve["日期"].dt.year == year
            seg = curve.loc[mask_c]
            if not seg.empty:
                ax.plot(seg["日期"], seg["余额"], linewidth=1.8, color=color,
                        label=f"理想 {label}", zorder=5)

        ax.set_title(f"{year} 年：4 条理想计划线 vs 实际净资产", fontsize=12, pad=10)
        ax.set_ylabel("金额（万元）", fontsize=10)
        ax.yaxis.set_major_formatter(plt.FuncFormatter(_fmt_wan))
        ax.xaxis.set_major_locator(mdates.MonthLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
        ax.grid(True, which="both", linestyle="--", linewidth=0.5, alpha=0.5)
        ax.legend(loc="best", fontsize=9, ncol=2)

    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(out_path, bbox_inches="tight")
    plt.close(fig)
    return out_path


def render_net_assets_delta(actual: pd.DataFrame, out_path=None) -> str:
    """有记录以来净资产总值变化折线图 + 每月环比增减柱状图。

    上：净资产总值折线（每个点标注数值）；下：环比变化柱状图（每个柱子标注增减金额）。
    """
    _setup_cjk_font()
    out_path = _mkdir(out_path or config.OUTPUT_DELTA_PNG)

    dates = pd.to_datetime(actual["日期"])
    values = actual["净资产"].astype(float)
    deltas = values.diff()  # 环比变化：本月 - 上月

    fig, (ax_top, ax_bot) = plt.subplots(
        2, 1, figsize=(12, 8), dpi=130, sharex=True,
        gridspec_kw={"height_ratios": [2.2, 1.4]})

    # ---- 上：净资产总值折线 ----
    ax_top.plot(dates, values, marker="o", linewidth=2.2, color=ACTUAL_COLOR,
                label="净资产总值", zorder=5)
    for d, v in zip(dates, values):
        ax_top.annotate(f"{v / 10000:,.1f}万", (d, v),
                        textcoords="offset points", xytext=(6, 8), fontsize=9,
                        color=ACTUAL_COLOR)
    ax_top.set_title("有记录以来净资产总值变化（含每月环比增减）", fontsize=14, pad=12)
    ax_top.set_ylabel("净资产（万元）", fontsize=10)
    ax_top.yaxis.set_major_formatter(plt.FuncFormatter(_fmt_wan))
    ax_top.grid(True, which="both", linestyle="--", linewidth=0.5, alpha=0.5)
    ax_top.legend(loc="best", fontsize=10)

    # ---- 下：每月环比变化柱状图 ----
    colors_bar = ["#27ae60" if (pd.notna(x) and x >= 0) else "#c0392b" for x in deltas]
    ax_bot.bar(dates, deltas.fillna(0), width=24, color=colors_bar, alpha=0.85)
    for d, dv in zip(dates, deltas):
        if pd.isna(dv):
            ax_bot.annotate("首月", (d, 0), textcoords="offset points",
                            xytext=(0, 4), fontsize=8, color="#7f8c8d", ha="center")
        else:
            text = f"{dv / 10000:+.2f}万"
            y_off = 4 if dv >= 0 else -14
            ax_bot.annotate(text, (d, dv), textcoords="offset points",
                            xytext=(0, y_off), fontsize=9, ha="center",
                            fontweight="bold",
                            color="#27ae60" if dv >= 0 else "#c0392b")
    ax_bot.axhline(0, color="#7f8c8d", linewidth=0.8)
    ax_bot.set_ylabel("环比变化（万元）", fontsize=10)
    # 环比量级常在 ±1 万以内，整数格式化会把刻度全压成 "0万"，这里保留两位小数
    ax_bot.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, p: _fmt_wan(v, p, 2)))
    ax_bot.grid(True, which="both", linestyle="--", linewidth=0.5, alpha=0.5)

    ax_bot.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(out_path, bbox_inches="tight")
    plt.close(fig)
    return out_path

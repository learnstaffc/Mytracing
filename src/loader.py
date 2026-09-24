"""读取资产负债 Excel，计算每月净资产时间序列。

净资产 = Σ(资产列 × 汇率) - Σ(负债列)
若文件中存在名为 "Sum" 的列，会做一致性校验（提示数据是否有出入）。
"""
from typing import Optional

import pandas as pd

from . import config


def _read_raw(file_path: Optional[str], sheet: Optional[str]) -> pd.DataFrame:
    """读取并清洗原始表：日期解析、去空、按日期排序。"""
    file_path = file_path or config.ASSET_FILE
    sheet = sheet or config.SHEET

    try:
        raw = pd.read_excel(file_path, sheet_name=sheet)
    except FileNotFoundError:
        raise SystemExit(f"[错误] 找不到数据文件: {file_path}\n请检查 src/config.py 中的 ASSET_FILE 路径，或用 --file 指定。")
    except ValueError as e:
        raise SystemExit(f"[错误] 读取 sheet 失败: {e}\n请确认 sheet 名是否为 {sheet!r}（可用 --sheet 指定）。")

    if config.DATE_COL not in raw.columns:
        raise SystemExit(f"[错误] 文件中缺少日期列 {config.DATE_COL!r}，当前列: {list(raw.columns)}")

    df = raw.copy()
    df[config.DATE_COL] = pd.to_datetime(df[config.DATE_COL], errors="coerce")
    df = df.dropna(subset=[config.DATE_COL]).sort_values(config.DATE_COL).reset_index(drop=True)

    if df.empty:
        raise SystemExit("[错误] 日期列没有有效数据。")
    return df


def load_net_assets(file_path: Optional[str] = None, sheet: Optional[str] = None) -> pd.DataFrame:
    """读取并计算每月净资产时间序列（净资产 = Σ资产×汇率 - Σ负债）。"""
    df = _read_raw(file_path, sheet)

    # 需要使用的列（资产列 + 负债列）必须都存在
    needed = config.ASSET_COLUMNS + config.LIABILITY_COLUMNS
    missing = [c for c in needed if c not in df.columns]
    if missing:
        raise SystemExit(f"[错误] 文件中缺少列: {missing}\n当前列: {list(df.columns)}\n请检查 src/config.py 的列映射。")

    # 资产（考虑汇率折算）
    assets = pd.Series(0.0, index=df.index)
    for col in config.ASSET_COLUMNS:
        values = pd.to_numeric(df[col], errors="coerce").fillna(0.0)
        fx = config.FX_RATES.get(col, 1.0)
        assets = assets + values * fx

    # 负债
    liabilities = pd.Series(0.0, index=df.index)
    for col in config.LIABILITY_COLUMNS:
        liabilities = liabilities + pd.to_numeric(df[col], errors="coerce").fillna(0.0)

    net = assets - liabilities

    result = pd.DataFrame({"日期": df[config.DATE_COL], "净资产": net})

    # 一致性校验：若存在手动维护的 "Sum" 列，比较是否与计算值一致
    if "Sum" in df.columns:
        manual = pd.to_numeric(df["Sum"], errors="coerce")
        diff = (net - manual).abs().max()
        if pd.notna(diff) and diff > 1.0:
            print(f"[提示] 计算净资产与文件中的 Sum 列最大偏差 {diff:.2f} 元，"
                  f"请确认 FX_RATES 汇率或 Sum 列是否最新。")
        else:
            print("[提示] 计算净资产与文件 Sum 列一致。")

    return result


def load_accounts(file_path: Optional[str] = None, sheet: Optional[str] = None) -> pd.DataFrame:
    """读取每个资产/负债账户的月度值（统一折算为人民币，US-inv 按汇率×6.6）。

    返回 DataFrame：日期 + 各账户列（资产列带 ¥ 后缀，负债列原样）。
    """
    df = _read_raw(file_path, sheet)

    out = pd.DataFrame({"日期": df[config.DATE_COL]})
    for col in config.ASSET_COLUMNS:
        if col in df.columns:
            values = pd.to_numeric(df[col], errors="coerce").fillna(0.0)
            fx = config.FX_RATES.get(col, 1.0)
            out[f"{col}(¥)"] = values * fx
    for col in config.LIABILITY_COLUMNS:
        if col in df.columns:
            out[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)
    return out

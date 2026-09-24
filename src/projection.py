"""存款计划曲线计算。

规则（与你「规划表」sheet 中的手算一致）：
- 初始本金 INITIAL_BALANCE（默认 15 万）从 start_date 开始；
- 每月月初先存入 MONTHLY_DEPOSIT（1 万），再对整个余额按有效月利率计息：
      余额[t] = (余额[t-1] + 月存款) × (1 + 月利率)
- 月利率由年化折算：r = (1 + 年化)^(1/12) - 1
- 一直推到余额 >= TARGET（100 万），返回整条曲线与达标信息。
"""
from typing import Optional

import pandas as pd

from . import config


def plan_curve(start_date, annual_rate: float,
               initial: Optional[float] = None,
               deposit: Optional[float] = None,
               target: Optional[float] = None) -> pd.DataFrame:
    """返回 DataFrame(日期, 余额)，最后一行即首次达标（余额>=target）的月份。"""
    r = (1.0 + annual_rate) ** (1.0 / 12.0) - 1.0
    start = pd.Timestamp(start_date)
    balance = float(initial if initial is not None else config.INITIAL_BALANCE)
    deposit = float(deposit if deposit is not None else config.MONTHLY_DEPOSIT)
    target = float(target if target is not None else config.TARGET)

    dates = [start]
    balances = [balance]
    month = 0
    max_months = 1200  # 安全上限
    while balance < target and month < max_months:
        month += 1
        balance = (balance + deposit) * (1.0 + r)
        dates.append(start + pd.DateOffset(months=month))
        balances.append(balance)

    return pd.DataFrame({"日期": dates, "余额": balances})


def milestone(curve: pd.DataFrame) -> Optional[dict]:
    """从计划曲线中提取达标信息：首次余额>=TARGET 的日期、余额、所需月数。"""
    if curve.empty:
        return None
    last = curve.iloc[-1]
    if last["余额"] < config.TARGET:
        return None  # 未达标（不应出现）
    months = len(curve) - 1
    return {
        "日期": last["日期"],
        "余额": last["余额"],
        "月数": months,
    }

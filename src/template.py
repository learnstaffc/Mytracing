"""生成资产负债模板（xlsx 或 csv，写入用户指定路径，供照着填写）。

表头、列顺序、汇率与 Sum 公式**全部从 `src/config.py` 派生**，所以改过
`DATE_COL` / `ASSET_COLUMNS` / `LIABILITY_COLUMNS` / `FX_RATES` 之后，
生成的模板依然和 `loader.py` 的读取逻辑一致，不会再出现「模板列名和读取列对不上」。

列顺序固定为：日期 → 资产列 → 负债列 → Sum（Sum 为可选的人工核对列）。

输出格式按目标路径的扩展名决定：`.csv` 写 CSV（Sum 是数值），其余写 Excel（Sum 是公式）。
"""
import csv
from pathlib import Path
from typing import Optional

import openpyxl
from openpyxl.styles import Font, PatternFill
from openpyxl.utils import get_column_letter

from . import config

SUM_HEADER = "Sum"  # 可选列，只用于人工核对，loader 有值会做一致性校验

# 示例数据（每月 1 号记一次，纯虚构的整齐数字，仅供演示格式）。
# 用「列名 -> 值」表示：若 config 里新增了资产列而这里没提，会自动填 0，不会报错。
SAMPLE_ROWS = [
    {config.DATE_COL: "2026-01-01", "ZSBank": 60000, "WeFinace": 35000,
     "A-inv": 40000, "US-inv": 4000, "Credit": 0},
    {config.DATE_COL: "2026-02-01", "ZSBank": 62000, "WeFinace": 36000,
     "A-inv": 41000, "US-inv": 4200, "Credit": 2000},
    {config.DATE_COL: "2026-03-01", "ZSBank": 65000, "WeFinace": 37000,
     "A-inv": 42000, "US-inv": 4500, "Credit": 3000},
]


def columns() -> list[str]:
    """模板的列顺序：日期 → 资产列 → 负债列 → Sum（与 loader 的读法一致）。"""
    return [config.DATE_COL, *config.ASSET_COLUMNS, *config.LIABILITY_COLUMNS, SUM_HEADER]


def sum_formula(row: int, cols: Optional[list[str]] = None) -> str:
    """拼出 Sum = Σ(资产列 × 汇率) − Σ(负债列) 的 Excel 公式。"""
    cols = cols if cols is not None else columns()
    terms = []
    for name in config.ASSET_COLUMNS:
        ref = f"{get_column_letter(cols.index(name) + 1)}{row}"
        fx = config.FX_RATES.get(name, 1.0)
        terms.append(f"{ref}*{fx}" if fx != 1.0 else ref)
    formula = "+".join(terms) if terms else "0"
    for name in config.LIABILITY_COLUMNS:
        formula += f"-{get_column_letter(cols.index(name) + 1)}{row}"
    return f"={formula}"


def sum_value(row: dict) -> float:
    """按同一套规则算出 Sum 的数值。CSV 没有公式，只能写死算好的结果。"""
    total = 0.0
    for name in config.ASSET_COLUMNS:
        total += float(row.get(name) or 0) * config.FX_RATES.get(name, 1.0)
    for name in config.LIABILITY_COLUMNS:
        total -= float(row.get(name) or 0)
    return total


def _write_xlsx(target: Path, cols: list[str], data: list[dict]) -> None:
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = config.SHEET

    # 表头
    for i, name in enumerate(cols, start=1):
        cell = ws.cell(row=1, column=i, value=name)
        cell.font = Font(bold=True)
        cell.fill = PatternFill("solid", fgColor="DDEBF7")

    # 数据行
    for r, row in enumerate(data, start=2):
        for i, name in enumerate(cols, start=1):
            if name == SUM_HEADER:
                value, fmt = sum_formula(r, cols), "#,##0.00"
            elif name == config.DATE_COL:
                value, fmt = row.get(name), "yyyy-mm-dd"
            else:
                value, fmt = row.get(name, 0), "#,##0.00"
            ws.cell(row=r, column=i, value=value).number_format = fmt

    # 列宽
    for i, name in enumerate(cols, start=1):
        wide = name in (config.DATE_COL, SUM_HEADER)
        ws.column_dimensions[get_column_letter(i)].width = 14 if wide else 12

    wb.save(target)


def _write_csv(target: Path, cols: list[str], data: list[dict]) -> None:
    # utf-8-sig 让 Excel 直接双击打开也不乱码
    with target.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(cols)
        for row in data:
            values = []
            for name in cols:
                if name == SUM_HEADER:
                    values.append(f"{sum_value(row):.2f}")
                elif name == config.DATE_COL:
                    values.append(row.get(name, ""))
                else:
                    values.append(row.get(name, 0))
            writer.writerow(values)


def create_template(path: str, rows: Optional[list[dict]] = None) -> str:
    """生成模板并返回路径。按扩展名选格式，`rows` 为空时用内置的 3 行虚构示例。"""
    cols = columns()
    data = SAMPLE_ROWS if rows is None else rows

    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)

    if target.suffix.lower() in (".csv", ".txt", ".tsv"):
        _write_csv(target, cols, data)
    else:
        _write_xlsx(target, cols, data)
    return str(target)

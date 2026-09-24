"""生成 README 演示用的虚构示例数据（examples/sample_data.xlsx 与 .csv）。

数据全部是编造的整齐数字，不对应任何真实账户，仅用于展示图表效果。
表头、列顺序与 Sum 公式直接复用 `src/template.py`，所以改过 `src/config.py`
的列映射之后，这份示例数据和正式模板不会各自跑偏。

用法：
    python examples/make_sample_data.py
    python main.py --file examples/sample_data.xlsx --sheet record
    python main.py --file examples/sample_data.csv
"""
import sys
from pathlib import Path

# 让脚本无论从哪个目录启动，都能 import 到仓库根目录下的 src/
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import config                    # noqa: E402
from src.template import create_template  # noqa: E402

# (日期, ZSBank, WeFinace, A-inv, US-inv(USD), Credit) —— 每月 1 号一条，纯虚构
SAMPLE_MONTHS = [
    ("2025-01-01",  60000, 35000, 40000, 4000,    0),
    ("2025-02-01",  63000, 35200, 41500, 4100,    0),
    ("2025-03-01",  66000, 35500, 40800, 4050,  800),
    ("2025-04-01",  69000, 36000, 39000, 4150,    0),
    ("2025-05-01",  71500, 36500, 37800, 4300,    0),
    ("2025-06-01",  74000, 37000, 39200, 4400, 1200),
    ("2025-07-01",  76500, 37500, 40500, 4450,    0),
    ("2025-08-01",  80000, 38000, 38800, 4600,    0),
    ("2025-09-01",  83000, 38500, 37600, 4700, 2000),
    ("2025-10-01",  86000, 39000, 39500, 4800,    0),
    ("2025-11-01",  90000, 39500, 41200, 4950,    0),
    ("2025-12-01",  95000, 40000, 43000, 5100, 3000),
    ("2026-01-01", 100000, 40500, 41800, 5250,    0),
    ("2026-02-01", 106000, 41000, 44200, 5400, 1500),
    ("2026-03-01", 112000, 41500, 45600, 5600,    0),
    ("2026-04-01", 118000, 42000, 47000, 5750,    0),
    ("2026-05-01", 124000, 42500, 45800, 5900, 2500),
    ("2026-06-01", 131000, 43000, 48200, 6050,    0),
]


def sample_rows() -> list[dict]:
    """转成 `create_template` 需要的「列名 -> 值」形式。"""
    return [
        {config.DATE_COL: d, "ZSBank": zs, "WeFinace": wf,
         "A-inv": ai, "US-inv": us, "Credit": cr}
        for d, zs, wf, ai, us, cr in SAMPLE_MONTHS
    ]


def main() -> None:
    here = Path(__file__).resolve().parent
    # 两种格式内容完全一致，xlsx 便于用 Excel 打开看，csv 便于对照纯文本格式
    for name in ("sample_data.xlsx", "sample_data.csv"):
        create_template(str(here / name), rows=sample_rows())
        print(f"示例数据已生成: {here / name}")


if __name__ == "__main__":
    main()

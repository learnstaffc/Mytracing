"""主入口。

用法：
  python main.py                          # 读取配置的 ASSET_FILE 并出图
  python main.py --file /path/to/x.xlsx   # 临时指定文件
  python main.py --sheet other            # 临时指定 sheet
  python main.py --init-template /path/to/template.xlsx  # 生成示例模板
"""
import argparse

from src import config, template
from src.loader import load_accounts, load_net_assets
from src.plot import render, render_accounts, render_net_assets_delta, render_yearly
from src.projection import milestone, plan_curve


def main() -> None:
    ap = argparse.ArgumentParser(description="个人资产增长与百万目标可视化")
    ap.add_argument("--file", help="覆盖数据文件路径（默认取 config.ASSET_FILE）")
    ap.add_argument("--sheet", help="覆盖 sheet 名（默认取 config.SHEET）")
    ap.add_argument("--init-template", metavar="PATH", help="在指定路径生成示例模板后退出")
    args = ap.parse_args()

    if args.init_template:
        path = template.create_template(args.init_template)
        print(f"示例模板已生成: {path}\n请按每月 1 号的记录填写资产/负债，然后运行 python main.py。")
        return

    # ---- 读取实际净资产 ----
    df = load_net_assets(args.file, args.sheet)
    start_date = df["日期"].min()
    latest = df.iloc[-1]

    print("=" * 60)
    print(f"数据文件 : {args.file or config.ASSET_FILE}  (sheet: {args.sheet or config.SHEET})")
    print(f"记录期数 : {len(df)} 个月（{start_date:%Y-%m-%d} ~ {df['日期'].max():%Y-%m-%d}）")
    print(f"最新净资产: ¥{latest['净资产']:,.2f}")
    print("=" * 60)

    # ---- 4 个存款计划场景 ----
    curves: dict[tuple[float, float], dict] = {}
    print(f"\n[存款计划] 初始 {config.INITIAL_BALANCE / 10000:,.0f} 万，目标净资产 "
          f"{config.TARGET / 10000:,.0f} 万，起始时间 {start_date:%Y-%m-%d}")
    print(f"{'场景':<16}{'达标日期':<12}{'所需月数':<8}{'届时余额':<14}")
    print("-" * 52)
    for s in config.PLAN_SCENARIOS:
        dep, rate = s["deposit"], s["rate"]
        curve = plan_curve(start_date, rate, deposit=dep)
        curves[(dep, rate)] = curve
        m = milestone(curve)
        if m is None:
            print(f"{s['label']:<16}{'未达标':<12}")
            continue
        years = m["月数"] / 12
        print(f"{s['label']:<16}{m['日期']:%Y-%m-%d}{m['月数']:>6}个月"
              f"({years:.1f}年){m['余额']:>12,.0f}")

    # ---- 出图：四张 ----
    out_main = render(df, curves)
    accounts = load_accounts(args.file, args.sheet)
    out_accounts = render_accounts(accounts)
    out_yearly = render_yearly(df, curves)
    out_delta = render_net_assets_delta(df)

    print("\n输出文件:")
    print(f"  主图（实际 + 4 条计划 + 目标）: {out_main}")
    print(f"  账户月度变化: {out_accounts}")
    print(f"  逐年对比（4 理想 + 实际）: {out_yearly}")
    print(f"  净资产总值变化（含每月环比）: {out_delta}")


if __name__ == "__main__":
    main()

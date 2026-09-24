# 个人资产增长与百万目标可视化

把「实际净资产变化」和「存款计划曲线」画在一起，并计算净资产何时达到 100 万。

## 效果预览

> 下面 4 张图全部由 `examples/sample_data.xlsx` 里的**虚构示例数据**生成，不对应任何真实账户。
> 复现方式：`python examples/make_sample_data.py` 生成数据，再执行
> `python main.py --file examples/sample_data.xlsx --sheet record`。

**主图：实际净资产 + 4 条存款计划曲线 + 100 万目标线**

![主图：个人净资产 vs 存款计划](images/net_asset_plan.png)

**账户月度变化：各资产/负债账户逐月走势**

![各资产账户月度变化](images/accounts_trend.png)

**逐年对比：每个年度内 4 条理想计划线 vs 实际净资产**

![逐年对比](images/yearly_compare.png)

**净资产总值与每月环比增减**

![净资产总值变化](images/net_assets_delta.png)

## 功能
- 从外部 Excel（默认 `/mnt/d/learning.xlsx` 的 `record` sheet）读取每月 1 号的资产负债记录，计算净资产
- 净资产 = Σ(资产列 × 汇率) − Σ(负债列)，美股（US-inv）按 6.6 汇率折算成人民币
- **主图**：实际净资产 + 4 条计划曲线（月存 1万/1.5万 × 年化 5%/10%，月复利、月初存入）+ 100 万目标线 + 达标日期标注
- **账户趋势图**：有记录以来各资产/负债账户的月度变化（US-inv 折算人民币）
- **逐年对比图**：每个有记录的年度内，4 条理想计划线 vs 实际净资产线

## 安装依赖
```bash
pip install -r requirements.txt
```

## 使用
```bash
# 1) 首次使用：在指定路径生成示例模板（不放在项目内）
python main.py --init-template /你的路径/template.xlsx

# 2) 按每月 1 号填写资产/负债后，运行：
python main.py                    # 使用 config.py 里的 ASSET_FILE
python main.py --file /你的路径/learning.xlsx --sheet record   # 临时指定文件

# 3) 输出
#    控制台：各场景达标日期/所需月数
#    图片：output/net_asset_plan.png（主图）、accounts_trend.png（账户变化）、
#         yearly_compare.png（逐年对比）、net_assets_delta.png（净资产总值+每月环比）
```

## 配置文件 `src/config.py`
| 项 | 说明 | 默认值 |
|---|---|---|
| `ASSET_FILE` | 资产负债文件路径（项目外） | `/mnt/d/learning.xlsx` |
| `SHEET` | 读取的 sheet 名 | `record` |
| `ASSET_COLUMNS` | 资产列 | `ZSBank, WeFinace, A-inv, US-inv` |
| `FX_RATES` | 外币资产列 → 汇率 | `{"US-inv": 6.6}` |
| `LIABILITY_COLUMNS` | 负债列 | `Credit` |
| `INITIAL_BALANCE` | 计划初始本金 | `150_000` |
| `PLAN_SCENARIOS` | 计划场景列表（月存 × 年化） | 1万/1.5万 × 5%/10% |
| `TARGET` | 目标净资产 | `1_000_000` |

## 算法说明
- 有效月利率：`r = (1 + 年化)^(1/12) − 1`
- 逐月递推（月初存入、月复利）：`余额[t] = (余额[t-1] + 月存款) × (1 + r)`
- 首次 `余额 >= 100 万` 的月份即为达标月

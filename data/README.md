# 数据说明

- `raw/`：原始/下载数据，**不入库**（由 `scripts/fetch_data.py` 从 akshare/tushare 抓取）。
- `processed/`：清洗好的内置示例数据，**入库**，保证断网也能跑（由 `scripts/make_sample_data.py` 生成）。

## 加载方式

```python
from fi import data
df = data.load_sample("cgb_yield_curve")   # 读取 data/processed/cgb_yield_curve.{parquet,csv}
```

## 数据优先级

内置离线样本（默认） > akshare/tushare（免费联网） > Wind/WindPy（仅在有授权时可选）。

> 注：`processed/` 下的示例数据为教学用示意数据，非真实行情，使用真实数据请走 `fetch_data.py`。

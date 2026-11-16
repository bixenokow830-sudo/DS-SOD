# MLLM 类别识别混淆分析（自动生成，勿手改）

样本：ORSI-4199 测试集 2199 张，其中文件名可解析出真实类别 1660 张。
**类别正确率（按真实类别是否等于 MLLM 最高置信框的类别）=1516/1660 = 91.3%**

## 按真实类别统计（正确率升序）

| 真实类别（文件名） | 图数 | 类别正确率 |
|---|---|---|
| road | 15 | 60.0% |
| roads | 75 | 60.0% |
| lakes | 73 | 83.6% |
| bridges | 111 | 84.7% |
| cars | 244 | 89.3% |
| bridge | 48 | 89.6% |
| urban landmarks | 317 | 90.9% |
| stadiums | 79 | 92.4% |
| car | 46 | 93.5% |
| storage tanks | 79 | 94.9% |
| storage tank | 51 | 96.1% |
| ships | 155 | 98.1% |
| rural building | 83 | 98.8% |
| airplane | 194 | 100.0% |
| islands | 2 | 100.0% |
| lake | 17 | 100.0% |
| ship | 11 | 100.0% |
| stadium | 40 | 100.0% |
| urban landmark | 20 | 100.0% |

## 混淆对（真实类别 → MLLM 类别，图数 ≥5）

| 真实类别 | MLLM 给的类别 | 图数 | 语义是否等价 |
|---|---|---|---|
| urban landmarks | building | 288 | ✅ 等价 |
| cars | vehicle | 218 | ✅ 等价 |
| airplane | airplane | 194 | ✅ 等价 |
| ships | ship | 152 | ✅ 等价 |
| bridges | bridge | 94 | ✅ 等价 |
| rural building | building | 82 | ✅ 等价 |
| storage tanks | storage tank | 75 | ✅ 等价 |
| stadiums | playground | 73 | ✅ 等价 |
| lakes | river | 61 | ✅ 等价 |
| storage tank | storage tank | 49 | ✅ 等价 |
| roads | road | 45 | ✅ 等价 |
| bridge | bridge | 43 | ✅ 等价 |
| car | vehicle | 43 | ✅ 等价 |
| stadium | playground | 40 | ✅ 等价 |
| urban landmark | building | 20 | ✅ 等价 |
| urban landmarks | storage tank | 20 | ❌ 错认 |
| lake | river | 17 | ✅ 等价 |
| cars | building | 13 | ❌ 错认 |
| roads | river | 12 | ❌ 错认 |
| ship | ship | 11 | ✅ 等价 |
| road | road | 9 | ✅ 等价 |
| roads | bridge | 9 | ❌ 错认 |
| lakes | building | 7 | ❌ 错认 |
| roads | vehicle | 7 | ❌ 错认 |
| bridges | road | 6 | ❌ 错认 |
| cars | airplane | 5 | ❌ 错认 |
| cars | ship | 5 | ❌ 错认 |

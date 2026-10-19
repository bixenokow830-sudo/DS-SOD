# MGRQ-Net M03内部验证基线报告

> 执行日期：2026-10-18  
> 状态：`DIAGNOSTIC_COMPLETE_RETRAIN_REQUIRED`  
> 评测协议：`mgrq-sod-eval-v1-1256c0d3c1a6`

## 1. 实验目的

在M01-R1固定的400张严格内部验证图上运行现有监督NPA-SAM，确认权重、提示、SAM2推理和M02评测链路能够闭环，并判断现有权重能否直接作为MGRQ开发基线。

## 2. 实验配置

- SAM2：SAM2.1 base+。
- 解码器权重：`ds_sod/runs/mllm/adapter/p1c_traindist_e3.pt`，seed 42。
- 提示：从历史`sam2_prompts_train.json`中只抽取严格dev的400条逐图MLLM提示，共820个框；6张图为空提示。
- 推理模式：原始MLLM框；`tau=0`，关闭类别过滤、RESHAPE和DEDUP，不使用PRISM。
- 验证规模：ORSSD 60、EORSSD 140、ORSI-4199 200。
- GT来源：全部来自官方训练划分；未读取官方测试GT。
- 指标：M02冻结的Sα、Fβmax/Fβmean、Eξmax/Eξmean和MAE。

## 3. 推理与完整性

400张预测全部生成，缺失、多余、尺寸不一致和不可读文件均为0。内部验证GT中EORSSD有7张空GT，ORSSD和ORSI-4199无空GT；按M02冻结口径保留。

## 4. 诊断结果

| 数据集 | n | Sα | Fβmax | Fβmean | Eξmax | Eξmean | MAE |
|---|---:|---:|---:|---:|---:|---:|---:|
| ORSSD | 60 | 0.900994 | 0.913656 | 0.830739 | 0.978538 | 0.915490 | 0.014043 |
| EORSSD | 140 | 0.900074 | 0.841803 | 0.776044 | 0.979948 | 0.939378 | 0.011941 |
| ORSI-4199 | 200 | 0.905743 | 0.927367 | 0.883246 | 0.975330 | 0.952676 | 0.021227 |
| 三集宏平均 | 400 | **0.902270** | **0.894275** | **0.830010** | **0.977938** | **0.935848** | **0.015737** |

## 5. 关键门禁：该结果不是独立验证基线

`p1c_traindist_e3.pt`由旧`train_adapter.py`在三个官方训练划分的全部4000张原图上训练。M01-R1的400张内部验证图是之后才从这些训练图中划出的，因此：

- 当前dev 400张中有400张都在该权重的训练数据里，训练重叠率为100%；
- 训练使用的`prompt_stats_train.json`也由原4000张训练图统计，包含当前dev的聚合信息；
- 0.902270是同分布、训练内诊断值，不能与后续MGRQ的独立dev结果比较；
- 不得用该结果选择MGRQ结构、阈值、提示模板或超参数，也不得写入论文主表作为严格验证成绩。

该结果仅说明：现有权重可以加载，严格dev提示子集映射正确，400张推理和冻结评测实现均能完整运行。

## 6. M04的必要修正

M04不再是可选项。要得到有效的NPA-SAM内部验证基线，必须：

1. 只使用`strict_train_dev_manifest.json`中`split=train`的2928条记录训练；
2. 从这2928条记录重新统计提示误差分布，不能复用包含dev的旧`prompt_stats_train.json`；
3. 保持seed 42、SAM2.1 base+、原始MLLM框推理和M02评测口径；
4. 训练过程中不得读取400张dev GT，只有每个预先约定epoch结束后才能统一评测；
5. 输出新的独立权重和400张dev预测，禁止覆盖现有历史权重或本次诊断结果。

建议下一命令：

```text
执行 M04，seed=42，使用严格训练清单
```

## 7. 产物

- `ds_sod/banks/mgrq/m03/npa_sam_dev_prompts.json`
- `ds_sod/runs/mgrq/baselines/npa_sam_dev/provenance.json`
- `ds_sod/runs/mgrq/baselines/npa_sam_dev/baseline_summary.json`
- `ds_sod/runs/mgrq/baselines/npa_sam_dev/seed42/metrics.json`
- `ds_sod/runs/mgrq/baselines/npa_sam_dev/seed42/integrity.json`
- `ds_sod/runs/mgrq/baselines/npa_sam_dev/seed42/per_image_metrics.csv`


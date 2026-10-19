# MGRQ-Net M04：严格训练基线报告

## 1. 结论

M04已通过。使用严格去重后的2928张训练图、`seed=42`重训NPA-SAM掩码解码器，并在完全隔离的400张内部开发集上完成推理和冻结协议评测。训练集与开发集交集为0，未使用任何官方测试图像或GT，4份权重中的全部参数均为有限值，无NaN或Inf。

严格开发集宏平均为：**Sα 0.8920、Fβmax 0.8859、Fβmean 0.8225、Eξmax 0.9680、Eξmean 0.9313、MAE 0.0193**。该结果可以作为后续MGRQ-Net消融与模型选择的有效基线。

## 2. 固定设置

| 项目 | 设置 |
|---|---|
| 基础模型 | SAM2.1 Base+ |
| 可训练部分 | Mask Decoder，4,215,109参数 |
| 随机种子 | 42 |
| 训练轮数 | 3 |
| 损失函数 | BCE + IoU |
| 提示来源 | 严格train上的真实MLLM提示分布 |
| 正/负提示数 | `n_pos=1`，`n_neg=2` |
| 候选规则 | `score` |
| 扰动幅度 | `jitter=0.30` |
| 训练样本 | 2928 |
| 开发样本 | 400（ORSSD 60 / EORSSD 140 / ORSI-4199 200） |
| 评测协议 | `mgrq-sod-eval-v1-1256c0d3c1a6` |

## 3. 严格提示统计

提示分布仅从严格train重新估计，未读取dev或官方test：

- 有效候选框5919个，其中命中2925、错误2994，命中率约49.4%。
- 命中框统计：`dx=-0.005`、`dy=-0.021`、`sw=1.049`、`sh=1.045`、平均置信度0.900。
- 错误框统计：`dx=-0.529`、`dy=0.671`、`sw=1.229`、`sh=1.064`、平均置信度0.756。

## 4. 严格开发集结果

| 数据集 | 数量 | Sα | Fβmax | Fβmean | Eξmax | Eξmean | MAE |
|---|---:|---:|---:|---:|---:|---:|---:|
| ORSSD | 60 | 0.8881 | 0.8993 | 0.8282 | 0.9578 | 0.9142 | 0.0197 |
| EORSSD | 140 | 0.8924 | 0.8391 | 0.7732 | 0.9746 | 0.9365 | 0.0136 |
| ORSI-4199 | 200 | 0.8956 | 0.9193 | 0.8660 | 0.9716 | 0.9433 | 0.0245 |
| **宏平均** | **400** | **0.8920** | **0.8859** | **0.8225** | **0.9680** | **0.9313** | **0.0193** |

完整性检查：400张预测全部存在；缺失0、多余0、尺寸不一致0、不可读0。EORSSD中7张空GT按M02冻结规则保留。

## 5. 与旧权重的关系

| 对照 | 宏平均Sα | 解释 |
|---|---:|---|
| M03旧权重内部dev诊断 | 0.9023 | 训练时看过全部400张dev，重叠率100%，不能作为独立基线 |
| M04严格权重内部dev | 0.8920 | train/dev零重叠，可用于模型选择 |
| 旧权重历史官方test | 0.8923 | 仅作量级参照，数据划分不同 |

M04相对M03诊断值下降0.0103，符合消除训练泄漏后的预期。M04与旧权重历史官方test宏平均Sα仅相差-0.0003，说明严格重训没有造成基线能力的异常退化，但这不是同一测试集上的配对比较。

## 6. 可复现性与产物

- 最终权重：`ds_sod/runs/mgrq/baselines/npa_sam_strict_s42/weights/npa_sam_strict_s42_e3.pt`
- 最终权重SHA256：`57f7a34a32080e097d2fc0ae8a4239d4d60de127e9952820893e81dcaf15257a`
- Epoch检查点：`npa_sam_strict_s42_e3.epoch1.pt`、`epoch2.pt`、`epoch3.pt`
- 严格提示统计：`ds_sod/banks/mgrq/m04/prompt_stats_strict_train.json`
- 训练与溯源：`ds_sod/runs/mgrq/baselines/npa_sam_strict_s42/training_config_and_provenance.json`
- 汇总指标：`ds_sod/runs/mgrq/baselines/npa_sam_strict_s42/baseline_summary.json`
- 逐图指标：`ds_sod/runs/mgrq/baselines/npa_sam_strict_s42/dev/per_image_metrics.csv`
- 完整性审计：`ds_sod/runs/mgrq/baselines/npa_sam_strict_s42/dev/integrity.json`
- 实时进度页：`ds_sod/runs/mgrq/baselines/npa_sam_strict_s42/training_progress.html`

## 7. 下一步

M04已解决M03的训练泄漏问题。下一阶段可执行D10，在同一严格train/dev协议下训练MGRQ核心模块；后续所有模型选择均以本报告的M04严格基线为对照，不再使用M03污染诊断值。

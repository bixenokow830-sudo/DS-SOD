# MGRQ-Net实验执行记录

本文件按实验编号记录实际执行状态。计划定义见《MGRQ-Net分步骤实验执行计划书》。除非用户明确下令，不自动执行下一实验单元。

---

## M00｜只读环境与代码盘点

| 字段 | 记录 |
|---|---|
| 状态 | `PASSED_WITH_WARNINGS` |
| 执行时间 | 2026-10-18 21:47，Asia/Shanghai |
| API调用 | 否 |
| GPU训练 | 否 |
| 已有权重修改 | 否 |
| 审计产物 | `ds_sod/runs/mgrq/_audit/environment.json`、`inventory.md` |

### 主要结果

- Python 3.14.4、PyTorch 2.14.0+cu126、CUDA 12.6可用。
- GPU为RTX 4060 Laptop 8GB；审计时空闲显存5596 MiB。
- SAM2.1 base+权重与配置存在，CPU构建成功，参数量80,850,178。
- 三个数据集共有4000张训练原图和2999张测试图，图像与GT无缺配。
- 现有NPA-SAM两种子权重和LODO权重存在。
- D盘空闲空间115.97 GiB。

### 警告

1. `sam2_prompts_train.json`有6999条，实际覆盖全部训练和测试图，MGRQ训练不得直接使用。
2. 当前DeepSeek配置仍使用已退役别名`deepseek-v4-flash-vision-exp`，D10需改用`deepseek-flash`。
3. 当前工作区不是Git仓库，正式开发前需要可恢复的代码版本快照。
4. `scikit-image`未安装，但现有核心训练、预测和评测脚本未引用，不构成当前阻塞。

### 结论

M00通过。环境和资产足以进入数据协议审计，但必须先执行M01，不能直接启动MGRQ正式训练。

### 建议下一命令

```text
执行 M01
```

---

## M01｜数据清单与重复审计

| 字段 | 记录 |
|---|---|
| 状态 | `BLOCKED_BY_CROSS_SPLIT_DUPLICATES` |
| 执行时间 | 2026-10-18 21:54，Asia/Shanghai |
| API调用 | 否 |
| GPU训练 | 否 |
| 原始数据修改 | 否 |
| 固定种子 | 42 |
| 清单规模 | train 3600 / dev 400 / test 2999 |

### 已生成产物

- `ds_sod/scripts/build_mgrq_manifests.py`
- `ds_sod/banks/mgrq/manifests/train_dev_manifest.json`
- `ds_sod/banks/mgrq/manifests/test_manifest.json`
- `ds_sod/banks/mgrq/diagnostics/duplicate_audit.csv`
- `ds_sod/banks/mgrq/diagnostics/duplicate_audit_summary.json`
- `paper/MGRQ-Net_数据协议说明.md`

### 验证结果

- 6999条记录ID唯一，全部图像和GT路径存在。
- 固定划分为3600张训练图、400张内部验证图；分层数量符合计划。
- 发现61组跨官方训练/测试候选，其中2组字节完全重复、40组高置信同场景、19组需要人工复核。
- 还发现158组跨数据集同split的字节重复，说明ORSSD与EORSSD不能在联合训练中直接按独立样本重复采样。
- 已目视确认两组字节重复和多组重编码同场景；未删除、移动或覆盖任何原始文件。

### 门禁结论

M01的产物生成部分完成，但无泄漏验收失败。根据计划，停止后续正式训练并先确定去重协议。推荐保留官方测试集不变，排除所有与测试内容组相连的训练记录，对19组边界候选人工复核，然后重新冻结训练/内部验证清单。

### 建议下一命令

```text
执行 M01-R1，采用严格去重协议并生成人工复核清单
```

---

## M01-R1｜严格去重与人工复核清单

| 字段 | 记录 |
|---|---|
| 状态 | `PASSED_WITH_QUARANTINED_REVIEW_GROUPS` |
| 执行时间 | 2026-10-18 22:03，Asia/Shanghai |
| API调用 | 否 |
| GPU训练 | 否 |
| 原始数据修改 | 否 |
| 官方测试集 | 2999条，原样保留 |
| 严格训练/验证 | train 2928 / dev 400 |

### 严格处理结果

- 排除29条与测试内容组相连的训练记录。
- 隔离10条涉及未决候选的训练记录。
- 训练侧可信内容组折叠633条重复记录。
- 19条人工复核证据合并为8个独立内容组，并生成2页对照图。
- 严格清单保留3328条，数据集分布为ORSSD 417、EORSSD 972、ORSI-4199 1939。
- 内部验证集仍为ORSSD 60、EORSSD 140、ORSI-4199 200。

### 验证

- 严格测试清单与原官方测试清单逐记录一致。
- 保留记录与排除日志交集为0。
- 任一可信多成员内容组在严格清单中最多保留1条记录。
- 3328条严格记录和2999条测试记录的图像/GT路径全部存在。
- 人工复核项当前均为`PENDING`，相关训练记录已隔离，因此不阻塞使用严格清单进入M02。

### 主要产物

- `ds_sod/banks/mgrq/manifests/strict_train_dev_manifest.json`
- `ds_sod/banks/mgrq/manifests/strict_test_manifest.json`
- `ds_sod/banks/mgrq/diagnostics/strict_exclusion_log.csv`
- `ds_sod/banks/mgrq/diagnostics/strict_content_groups.json`
- `ds_sod/banks/mgrq/diagnostics/strict_protocol_summary.json`
- `ds_sod/banks/mgrq/diagnostics/manual_review.csv`
- `ds_sod/banks/mgrq/diagnostics/manual_review.md`
- `ds_sod/banks/mgrq/diagnostics/manual_review_sheets_consolidated/`

### 建议下一命令

```text
执行 M02
```

---

## M02｜冻结评测实现

| 字段 | 记录 |
|---|---|
| 状态 | `PASSED` |
| 执行时间 | 2026-10-18 22:07，Asia/Shanghai |
| API调用 | 否 |
| GPU训练 | 否 |
| 复评对象 | `hybrid-adapter`完整历史预测 |
| 协议编号 | `mgrq-sod-eval-v1-1256c0d3c1a6` |

### 结果

- 对ORSSD 200张、EORSSD 600张、ORSI-4199 2199张预测重新计算Sα、Fβmax/Fβmean、Eξmax/Eξmean和MAE。
- 21个历史字段全部精确复现，最大绝对差为0.0。
- 三个数据集均无缺失预测、多余预测、尺寸不一致或不可读文件。
- 检出ORSSD 4张、EORSSD 18张空GT；冻结协议保留这些样本以维持历史口径。ORSI-4199无空GT。
- 评测实现SHA256已冻结；后续若哈希变化，必须升级协议版本并重评全部对比方法。

### 产物

- `ds_sod/scripts/freeze_mgrq_evaluation.py`
- `ds_sod/runs/mgrq/_audit/m02/evaluation_freeze.json`
- `ds_sod/runs/mgrq/_audit/m02/metric_version.json`
- `ds_sod/runs/mgrq/_audit/m02/metric_comparison.csv`
- `ds_sod/runs/mgrq/_audit/m02/integrity_audit.csv`
- `paper/MGRQ-Net_评测协议说明.md`

### 建议下一命令

```text
执行 M03
```

---

## M03｜建立训练集内部验证基线

| 字段 | 记录 |
|---|---|
| 状态 | `DIAGNOSTIC_COMPLETE_RETRAIN_REQUIRED` |
| 执行时间 | 2026-10-18 22:17，Asia/Shanghai |
| API调用 | 否 |
| GPU训练 | 否 |
| GPU推理 | 是，400张 |
| 权重 | `p1c_traindist_e3.pt`，seed 42 |
| 评测协议 | `mgrq-sod-eval-v1-1256c0d3c1a6` |

### 完整性

- 严格dev共400张：ORSSD 60、EORSSD 140、ORSI-4199 200。
- 过滤得到400条历史逐图MLLM提示，共820个框，6张空提示；不含官方测试记录。
- 400张预测全部存在，无缺失、多余、尺寸不一致或不可读文件。
- EORSSD dev含7张空GT，按M02口径保留。

### 诊断指标

| 数据集 | Sα | Fβmax | Eξmax | MAE |
|---|---:|---:|---:|---:|
| ORSSD | 0.9010 | 0.9137 | 0.9785 | 0.0140 |
| EORSSD | 0.9001 | 0.8418 | 0.9799 | 0.0119 |
| ORSI-4199 | 0.9057 | 0.9274 | 0.9753 | 0.0212 |
| 宏平均 | 0.9023 | 0.8943 | 0.9779 | 0.0157 |

### 门禁结论

现有权重训练时使用了全部4000张官方训练原图，包含当前400张dev；训练重叠率为100%。因此上述分数只用于确认工程链路，不能作为独立基线或用于MGRQ模型选择。

M03的400张推理验收已完成，但“独立内部验证基线”未成立。M04由可选变为必需：必须使用严格train 2928条重训，并从严格train重新统计提示分布。

### 产物

- `ds_sod/scripts/prepare_eval_mgrq_m03.py`
- `ds_sod/banks/mgrq/m03/npa_sam_dev_prompts.json`
- `ds_sod/runs/mgrq/baselines/npa_sam_dev/baseline_summary.json`
- `ds_sod/runs/mgrq/baselines/npa_sam_dev/seed42/metrics.json`
- `ds_sod/runs/mgrq/baselines/npa_sam_dev/seed42/integrity.json`
- `ds_sod/runs/mgrq/baselines/npa_sam_dev/seed42/per_image_metrics.csv`
- `paper/MGRQ-Net_M03内部验证基线报告.md`

### 建议下一命令

```text
执行 M04，seed=42，使用严格训练清单
```

---

## M04｜严格清单重训NPA-SAM基线

| 字段 | 记录 |
|---|---|
| 状态 | `PASSED` |
| 执行时间 | 2026-10-19，Asia/Shanghai |
| API调用 | 否 |
| GPU训练 | 是，SAM2.1 Base+，3 epochs |
| 随机种子 | 42 |
| 严格划分 | train 2928 / dev 400，交集0 |
| 官方测试数据使用 | 0 |
| 评测协议 | `mgrq-sod-eval-v1-1256c0d3c1a6` |

### 训练与完整性

- 从严格train重新统计真实MLLM提示分布：5919个有效框，命中2925、错误2994。
- 仅训练Mask Decoder，共4,215,109参数；生成3个epoch检查点和1个最终权重。
- 4份权重逐张量检查全部为有限值，无NaN或Inf。
- 最终权重SHA256为`57f7a34a32080e097d2fc0ae8a4239d4d60de127e9952820893e81dcaf15257a`。
- 400张dev预测全部有效；缺失0、多余0、尺寸不一致0、不可读0。

### 严格dev指标

| 数据集 | Sα | Fβmax | Fβmean | Eξmax | Eξmean | MAE |
|---|---:|---:|---:|---:|---:|---:|
| ORSSD | 0.8881 | 0.8993 | 0.8282 | 0.9578 | 0.9142 | 0.0197 |
| EORSSD | 0.8924 | 0.8391 | 0.7732 | 0.9746 | 0.9365 | 0.0136 |
| ORSI-4199 | 0.8956 | 0.9193 | 0.8660 | 0.9716 | 0.9433 | 0.0245 |
| **宏平均** | **0.8920** | **0.8859** | **0.8225** | **0.9680** | **0.9313** | **0.0193** |

### 门禁结论

严格train/dev零重叠，M04成为可用于后续模型选择的有效内部验证基线。其宏平均Sα与旧权重历史官方test量级相当（0.8920对0.8923）；M03的0.9023因100%训练重叠继续仅保留为工程诊断值。

### 主要产物

- `ds_sod/scripts/eval_mgrq_m04.py`
- `ds_sod/banks/mgrq/m04/prompt_stats_strict_train.json`
- `ds_sod/runs/mgrq/baselines/npa_sam_strict_s42/weights/`
- `ds_sod/runs/mgrq/baselines/npa_sam_strict_s42/baseline_summary.json`
- `ds_sod/runs/mgrq/baselines/npa_sam_strict_s42/training_config_and_provenance.json`
- `ds_sod/runs/mgrq/baselines/npa_sam_strict_s42/dev/`
- `paper/MGRQ-Net_M04严格训练基线报告.md`

### 建议下一命令

```text
执行 D10
```

---

## D10｜新增MGRQ提示生成器

| 字段 | 记录 |
|---|---|
| 状态 | `PASSED` |
| 执行时间 | 2026-10-19 17:07，Asia/Shanghai |
| API调用 | 0 |
| API费用 | 0 |
| 请求模型 | `deepseek-flash` |
| 思考模式 | `disabled` |
| 输出协议 | `mgrq_semantic_queries_v1` |
| 提示模板 | `mgrq_prompt_v1_2026-10-19` |

### 实现结果

- 新增`generate_mgrq_prompts.py`，没有修改旧`pilot_mllm.py`、旧`llm.py`或既有提示库。
- 每张图使用单次结构化输出，字段包含短语、归一化框、显著置信度、理由、干扰物和空场景概率。
- 框统一为整数`[x1,y1,x2,y2]`和`[0,1000]`，非法范围、逆序坐标、缺失字段与额外字段均被拒绝。
- 密钥只从`DEEPSEEK_API_KEY`环境变量读取；干跑不创建API客户端。
- 原始响应与解析JSON分开保存，并记录图像哈希、清单哈希、模板版本、请求模型和服务返回模型。
- 实现缓存签名、断点续跑、真实调用重试和错误日志。

### 验收

- 4项离线单元检查全部通过。
- 严格dev首条记录完成完整离线解析、校验和落盘，状态`parsed_ok`。
- 相同命令再次运行返回`skipped_current_cache`，证明版本化断点续跑生效。
- API调用0，费用0，未发现密钥泄漏。

### 主要产物

- `ds_sod/scripts/generate_mgrq_prompts.py`
- `ds_sod/tests/test_generate_mgrq_prompts.py`
- `ds_sod/runs/mgrq/d10_acceptance_v1/`
- `paper/MGRQ-Net_D10提示生成器报告.md`

### 建议下一命令

```text
执行 D11
```

---

## D11｜MGRQ提示生成器五图干跑

| 字段 | 记录 |
|---|---|
| 状态 | `PASSED` |
| 执行时间 | 2026-10-19 17:16–17:19，Asia/Shanghai |
| API调用 | 0 |
| API费用 | 0 |
| 严格dev样本 | 5 |
| 首次解析成功 | 5/5 |
| 二次缓存跳过 | 5/5 |
| 自动测试 | 7/7通过 |

### 验收结果

- 5份原始响应和5份解析JSON分别保存，无缺失、无重复。
- 二次运行全部返回`skipped_current_cache`，API调用仍为0。
- 逆序坐标被拒绝并记录，未静默交换或裁剪。
- 缺失图像和损坏图像均在处理前被识别并写入错误日志。
- 空候选正常保存为合法空场景，`empty_scene_probability=0.98`。
- D11日志和产物未发现密钥内容。

### 主要产物

- `ds_sod/runs/mgrq/d11_dry_run/`
- `ds_sod/runs/mgrq/d11_empty_candidate/`
- `ds_sod/runs/mgrq/d11_invalid_bbox/`
- `ds_sod/runs/mgrq/d11_bad_images/`
- `ds_sod/runs/mgrq/d11_verification.json`
- `paper/MGRQ-Net_D11干跑验收报告.md`

### 建议下一命令

```text
执行 D12
```

---

## D12｜DeepSeek真实API冒烟测试

| 字段 | 记录 |
|---|---|
| 状态 | `PASSED` |
| 执行时间 | 2026-10-19 17:33–17:34，Asia/Shanghai |
| 请求模型 | `deepseek-flash` |
| 思考模式 | `disabled` |
| 严格dev样本 | 20，五类场景各4张 |
| API成功率 | 20/20，100% |
| JSON解析率 | 20/20，100% |
| 坐标合法率 | 121/121，100% |
| 重试 | 0 |
| 空回复 | 0 |
| 费用估算上界 | 约0.00982美元 |

### 结果

- 20次真实视觉API调用全部首次成功，服务返回模型字段均为`deepseek-flash`。
- 共得到75个显著候选和46个干扰区域；所有121个框通过归一化坐标检查。
- 人工检查20张框叠加图，未发现系统性x/y交换、坐标逆序或整体镜像偏移。
- 平均延迟2.253秒/图，P95为3.188秒；总token 16,703。
- 日志和产物未发现密钥；仅原图发送给API，GT和旧提示只用于抽样分层。
- 复杂场景存在候选较多或干扰框偏宽的现象，留待D13用GT定量诊断，不在D12添加逐图规则。

### 主要产物

- `ds_sod/banks/mgrq/manifests/d12_smoke_manifest.json`
- `ds_sod/banks/mgrq/d12_smoke/`
- `ds_sod/runs/mgrq/d12_smoke/`
- `ds_sod/runs/mgrq/d12_smoke/validation_summary.json`
- `paper/MGRQ-Net_D12真实API冒烟测试报告.md`

### 建议下一命令

```text
执行 D13
```

---

## D13｜300张API试点与提示模板冻结

| 字段 | 记录 |
|---|---|
| 状态 | `PASSED_SINGLE_IMAGE_TEMPLATE_FROZEN` |
| 执行日期 | 2026-10-19，Asia/Shanghai |
| 样本 | ORSSD 60、EORSSD 90、ORSI-4199 150 |
| D13新增API请求 | 280 |
| D12缓存复用 | 20 |
| API响应成功率 | 280/280，100% |
| 最终JSON解析率 | 300/300，100% |
| 请求模型 | `deepseek-flash` |
| 提示模板 | `mgrq_prompt_v1_2026-10-19` |
| 模板决策 | 冻结单整图，不执行2×2切片 |
| D13新增费用估算上界 | 约0.1191美元 |

### 验收结果

- 300个严格dev记录全部具有原始响应和解析缓存，记录ID无缺失、无重复。
- 首轮有5份响应因干扰物携带可选`saliency_confidence`未通过严格解析；校验器兼容该合法可选字段后，从原始响应本地恢复5/5，没有重复调用API。
- 相比旧提示库，候选框严格匹配率提高3.63个百分点，GT组件召回率提高22.76个百分点，像素召回率提高11.98个百分点。
- 小目标组件召回率由25.19%提高到52.26%，未触发“整图+2×2切片”对照。
- 框并集像素精确率下降5.80个百分点，严重失配候选比例增加7.11个百分点；后续必须依靠可靠性校准、负查询和发现查询，不能直接把MLLM框作为最终掩码。
- 8项生成器单元测试全部通过；缓存清单一致，未发现密钥内容。

### 主要产物

- `ds_sod/banks/mgrq/manifests/d13_pilot_manifest.json`
- `ds_sod/banks/mgrq/d13_pilot/`
- `ds_sod/runs/mgrq/d13_pilot/prompt_analysis.json`
- `ds_sod/runs/mgrq/d13_pilot/per_image_prompt_metrics.csv`
- `paper/MGRQ-Net_D13_300张API试点报告.md`

### 建议下一命令

```text
执行 D14
```

---

## D14｜完整训练提示缓存

| 字段 | 记录 |
|---|---|
| 状态 | `PASSED` |
| 执行时间 | 2026-10-19 18:25–20:15，Asia/Shanghai |
| 严格清单 | 3328（train 2928、dev 400） |
| D13缓存复用 | 300 |
| 新增API请求 | 3028 |
| 原始响应 | 3328/3328 |
| 有效解析 | 3322/3328，99.82% |
| 新增调用Token | 2,275,781 |
| 新增费用非峰时上界 | 0.6469美元 |

### 验收结果

- M01-R1严格去重后实际安全清单为3328张，没有将重复、测试关联或隔离记录重新加入。
- 所有请求均首次获得响应，服务返回模型均为`deepseek-flash`。
- 6份响应因非法框、未冻结字段或损坏JSON未通过严格解析；原始响应和失败原因均保留，没有静默修复或重复调用。
- 有效覆盖率99.82%，超过D14不低于99%的验收门槛。
- D13的300份原始响应未被覆盖。

### 主要产物

- `ds_sod/banks/mgrq/manifests/d14_strict_manifest.json`
- `ds_sod/banks/mgrq/d14_full/`
- `ds_sod/runs/mgrq/d14_full/final_summary.json`
- `paper/MGRQ-Net_D14完整提示缓存报告.md`

---

## D15｜DeepSeek训练提示质量报告

| 字段 | 记录 |
|---|---|
| 状态 | `PASSED` |
| 分析范围 | 严格train/dev有效记录3322张 |
| 官方测试GT | 未使用 |
| 候选严格匹配率 | 51.62% |
| GT组件召回率 | 71.66% |
| 小目标组件召回率 | 46.02% |
| 像素召回率/精确率 | 98.52% / 27.97% |
| 严重失配比例 | 35.96% |

### 核心结论

- 置信度≥0.6可将严格匹配率提高到71.18%，组件召回仅下降0.43个百分点，小目标召回仅下降0.59个百分点。
- 置信度≥0.9虽有91.91%严格匹配率，但小目标召回会降到29.81%，不能只保留最高置信候选。
- ORSI-4199小目标召回仅29.92%；密集目标小目标召回32.49%；大目标图中的伴生小组件召回仅8.64%，发现查询必须常开。
- 候选数从1–2增加到6–8时，严格匹配率从79.97%降至38.23%，候选数量应进入可靠性头。
- 4.88%的干扰框实际覆盖GT，干扰框只能作为软负先验，不能直接生成硬背景标签。
- 冻结三层入口：≥0.8可信正查询、0.6–0.8不确定查询、<0.6退出正查询池。

### 主要产物

- `ds_sod/banks/mgrq/diagnostics/deepseek_train_prompt_report.json`
- `ds_sod/banks/mgrq/diagnostics/deepseek_train_prompt_per_image.csv`
- `paper/MGRQ-Net_DeepSeek训练提示质量报告.md`

### 建议下一命令

```text
执行 D16
```

---

## D16｜冻结API提示协议

| 字段 | 记录 |
|---|---|
| 状态 | `FROZEN` |
| 执行时间 | 2026-10-20 10:18，Asia/Shanghai |
| 协议ID | `mgrq_api_protocol_v1_2026-10-20` |
| 提示模板 | `mgrq_prompt_v1_2026-10-19` |
| 输出协议 | `mgrq_semantic_queries_v1` |
| 模型别名 | `deepseek-flash` |
| D16 API调用 | 0 |
| D16费用 | 0 |
| 原始响应/唯一签名 | 3328/3328 |
| 有效解析 | 3322/3328，99.82% |

### 冻结结果

- 完整system prompt、user prompt、模型别名、请求参数、JSON字段、坐标约定、校验器规则、缓存签名和版本升级政策已写入机器可读冻结文件。
- 3328份原始响应的模型、提示模板版本、模板哈希和请求签名全部一致，没有协议混用。
- 冻结校验器拒绝逆序/越界/非数值框、损坏JSON、未知字段和`short_reason`等未冻结字段别名，不做静默修复。
- 下游查询规则独立版本化为`mgrq_query_admission_v1`，不进入API请求签名。
- `deepseek-flash`是可变服务别名；已有原始响应是论文实验的权威输入，未来重新调用不保证逐字复现。
- 后续任何提示、模型、图像策略、JSON协议或校验规则变化都必须升级协议并使用独立缓存，禁止原地混合。
- 8项生成器单元测试全部通过；D16没有读取密钥或调用API。

### 主要产物

- `ds_sod/banks/mgrq/protocols/mgrq_api_protocol_v1_2026-10-20.json`
- `paper/MGRQ-Net_D16_API提示协议冻结说明.md`

### 建议下一命令

```text
执行 I20
```

---

## I20｜GT组件目标生成

| 字段 | 记录 |
|---|---|
| 状态 | `PASSED` |
| 执行时间 | 2026-10-20，Asia/Shanghai |
| 严格清单 | 3328（train 2928、dev 400） |
| 连通性 | 8邻域 |
| 前景阈值 | `>128` |
| 最小组件面积 | 4像素，保留`area >= 4` |
| 原始/保留组件 | 6556/5817 |
| 移除组件/像素 | 739/778 |
| I20 API调用 | 0 |
| GPU | 不需要 |

### 验收结果

- 3328份组件目标全部生成，train/dev数量为2928/400，与严格清单一致。
- 过滤后GT与组件标签并集逐像素一致：3328/3328通过。
- 组件包围框精确覆盖验证：5817/5817通过；边界标签均从属于同ID组件。
- 输出包含标签图、边界图、包围框、面积、质心、边界像素数和图像边缘接触标记。
- 已冻结增强同步规则：水平/垂直翻转与90°/180°旋转均同步更新组件掩码和元数据。
- 空掩码、单组件、多组件、边界接触、微小组件、相连标注不拆分及几何变换共7项单元测试全部通过。
- 本阶段没有调用DeepSeek API、没有使用GPU、没有使用官方测试集GT。

### 主要产物

- `ds_sod/scripts/build_mgrq_gt_components.py`
- `ds_sod/tests/test_gt_components.py`
- `ds_sod/banks/mgrq/gt_components/v1/`
- `paper/MGRQ-Net_I20_GT组件目标生成报告.md`

### 建议下一命令

```text
执行 I21
```

---

## I21｜冻结CLIP文本特征缓存

| 字段 | 记录 |
|---|---|
| 状态 | `PASSED` |
| 执行时间 | 2026-10-20，Asia/Shanghai |
| 严格清单覆盖 | 3328/3328，100% |
| 有效解析 | 3322 |
| 文本编码器 | `openai/clip-vit-base-patch32` |
| 权重提交 | `3d74acf9a28c67741b2f4f2ea7635f0aaf6f0268` |
| 候选短语引用 | 16643（显著9655、干扰6988） |
| 唯一短语 | 10280（含4个回退短语） |
| 特征矩阵 | `10280 × 512`，float32，L2归一化 |
| 缺失/无候选回退 | 6/24 |
| I21 API调用 | 0 |

### 验收结果

- 3328条严格训练/开发记录全部具有本地特征入口，训练时不再调用API。
- 相同规范化短语唯一编码；6395个重复短语引用全部指向同一特征行。
- 特征无NaN或Inf，范数范围为0.9999998212–1.0000002384。
- 编码器名称、模型权重提交、提示模板版本、短语ID及所有产物哈希已写入索引。
- 6条解析缺失记录与24条无候选记录使用不同的明确回退向量；空短语回退逻辑已测试，本批实际触发0次。
- 7项文本规范化、去重、回退、版本和完整引用单元测试全部通过。
- 本阶段没有调用DeepSeek API；仅使用本地GPU进行冻结CLIP前向编码。

### 主要产物

- `ds_sod/mgrq/text_cache.py`
- `ds_sod/scripts/build_mgrq_text_cache.py`
- `ds_sod/tests/test_mgrq_text_cache.py`
- `ds_sod/banks/mgrq/text_embeddings/mgrq_prompt_v1_2026-10-19/`
- `paper/MGRQ-Net_I21_CLIP文本特征缓存报告.md`
- `training_progress.html`

### 建议下一命令

```text
执行 I22
```

---

## I22｜候选查询构造器

| 字段 | 记录 |
|---|---|
| 状态 | `PASSED` |
| 执行时间 | 2026-10-20，Asia/Shanghai |
| 视觉输入 | 256维SAM2特征 |
| 文本输入 | I21冻结512维CLIP特征 |
| 输出查询 | 256维 |
| RoI池化 | 3×3双线性采样后平均 |
| 查询类型 | 可信、不确定、低置信、干扰、回退，共5类 |
| 可训练参数 | 1,073,536 |
| I22 API调用 | 0 |

### 验收结果

- 实现视觉、文本、框几何、置信度和查询类型五分支融合，输出固定256维查询。
- 支持不同图像尺寸、空候选、1候选、5候选和任意批内padding；无效槽严格置零。
- 冻结框修复顺序：裁剪、重排、退化扩展；NaN/Inf直接拒绝，并返回可追踪修复标志。
- 9项单元测试全部通过。
- 使用真实D14框和I21文本缓存完成4类记录冒烟验收，输出`[4,5,256]`、无NaN或Inf。
- SAM2与CLIP输入没有梯度，21/21个I22可训练参数张量获得有限梯度。
- 本阶段没有调用DeepSeek API，没有启动长训练。

### 主要产物

- `ds_sod/mgrq/query_builder.py`
- `ds_sod/configs/mgrq_i22_query_builder.json`
- `ds_sod/tests/test_mgrq_query_builder.py`
- `ds_sod/scripts/validate_mgrq_query_builder.py`
- `ds_sod/banks/mgrq/diagnostics/i22_query_builder_validation.json`
- `paper/MGRQ-Net_I22_候选查询构造器报告.md`

### 建议下一命令

```text
执行 I23
```

---

## I23｜组件级匈牙利匹配器

| 字段 | 记录 |
|---|---|
| 状态 | `PASSED` |
| 执行时间 | 2026-10-20，Asia/Shanghai |
| 匹配代价 | `2×Dice + 2×BCE + 1×L1框代价` |
| 框格式 | 归一化`xyxy`，范围`[0,1]` |
| 语义代价 | 第一版不使用 |
| 最大匹配代价 | 4.0 |
| 未匹配查询标签 | `-1` |
| I23 API调用 | 0 |

### 验收结果

- 实现查询与GT组件一对一匈牙利分配，每个查询和GT最多出现一次。
- 匹配输出显式包含已匹配索引、未匹配查询、未匹配GT、匹配代价和`target_for_query`。
- 代价超过4.0的明显错误配对被拒绝；零logit中性初始查询仍可匹配，防止训练初期监督中断。
- 11项单元测试全部通过，覆盖单查询、重复查询、错误查询、查询少于/多于组件、空GT、空查询和padding。
- I20真实记录`EORSSD/train/0027`验收中，3个GT分别匹配查询0、1、2；重复查询3和错误查询4均标记为`-1`。
- 本阶段不需要GPU，没有调用DeepSeek API，也没有启动长训练。

### 主要产物

- `ds_sod/mgrq/matcher.py`
- `ds_sod/configs/mgrq_i23_matcher.json`
- `ds_sod/tests/test_mgrq_matcher.py`
- `ds_sod/scripts/validate_mgrq_matcher.py`
- `ds_sod/banks/mgrq/diagnostics/i23_matcher_validation.json`
- `paper/MGRQ-Net_I23_组件级匈牙利匹配器报告.md`

### 建议下一命令

```text
执行 I24
```

---

## I24｜基础查询解码器与小样本过拟合

| 字段 | 记录 |
|---|---|
| 状态 | `PASSED` |
| 执行时间 | 2026-10-20，Asia/Shanghai |
| 解码器 | 3层、8头、256维Transformer Decoder |
| 查询 | 最多5个MLLM查询＋5个可学习发现查询 |
| 掩码输出 | 单阶段组件mask logits |
| 损失 | 匹配查询BCE+Dice，未匹配查询0.1×背景BCE |
| 过拟合样本 | 严格train 12张，三个数据集各4张 |
| 实际训练步数 | 300，seed=42 |
| 可训练参数 | 4,433,024 |
| I24 API调用 | 0 |

### 验收结果

- 损失从1.6857降至0.0398，下降97.64%。
- 训练掩码平均并集IoU达到0.9519，平均匹配组件IoU达到0.8891。
- 12/12样本均来自严格train；未使用dev或官方test图像。
- 使用真实冻结SAM2.1 Base+图像特征和I21文本缓存；SAM2与CLIP均不更新。
- I24专项测试6/6通过，I22–I24相关测试合计26/26通过。
- 检查点84/84状态张量全部有限，参数量与配置一致。
- 本阶段使用本地GPU，没有调用DeepSeek API。

### 主要产物

- `ds_sod/mgrq/reliable_query_decoder.py`
- `ds_sod/configs/mgrq_i24_decoder.json`
- `ds_sod/tests/test_mgrq_decoder.py`
- `ds_sod/scripts/overfit_mgrq_i24.py`
- `ds_sod/runs/mgrq/i24_overfit_s42/`
- `paper/MGRQ-Net_I24_基础查询解码器与过拟合报告.md`

### 建议下一命令

```text
执行 I25
```

---

## I25｜查询可靠性头与人工小数据验证

| 字段 | 记录 |
|---|---|
| 状态 | `PASSED` |
| 执行时间 | 2026-10-20，Asia/Shanghai |
| 输入 | I24 解码后的 256 维查询 |
| 输出 | `p_obj`、`p_iou`、`r_i=p_obj×p_iou` |
| 可靠性头参数 | 33,666 |
| 人工数据 | 160 条查询（正32、负128） |
| 训练/留出 | 128/32，seed=42 |
| I25 API调用 | 0 |

### 验收结果

- 独立人工留出集正查询平均可靠性0.819689，负查询0.00000461，差值0.819684。
- 目标存在分类准确率100%，可靠性标准差0.344802，未出现全0或全1塌缩。
- 损失由0.171729降至0.000000529，所有预设阈值通过。
- 已匹配查询监督为1；未匹配、背景与重复查询监督为0；质量目标为实际掩码IoU。
- Focal Loss使用`alpha=0.75`、`gamma=2.0`，质量分支使用Smooth L1。
- I25专项单元测试6/6通过，检查点状态张量全部有限。
- 本阶段使用CPU，没有调用DeepSeek API；结果仅验证受控数据上的可优化性，不代表真实开发集泛化。

### 主要产物

- `ds_sod/mgrq/reliability_head.py`
- `ds_sod/configs/mgrq_i25_reliability.json`
- `ds_sod/tests/test_mgrq_reliability.py`
- `ds_sod/scripts/validate_mgrq_reliability.py`
- `ds_sod/runs/mgrq/i25_reliability_s42/`
- `paper/MGRQ-Net_I25_可靠性头验证报告.md`

### 建议下一命令

```text
执行 I26
```

---

## I26｜发现查询、适配器与细化模块单测

| 字段 | 记录 |
|---|---|
| 状态 | `PASSED` |
| 执行时间 | 2026-10-20，Asia/Shanghai |
| 发现查询 | 5个×256维，1,280参数 |
| 后层适配器 | 256→64→256残差瓶颈，33,728参数 |
| 两阶段细化 | 掩码池化＋查询更新＋精细掩码，592,896参数 |
| 专项单元测试 | 10/10通过 |
| 联合验收 | 9/9通过 |
| I26 API调用 | 0 |

### 验收结果

- 关闭MLLM后，5个发现查询仍可独立前向，基础解码器输出`[2,5,8,8]`且数值有限。
- 后层适配器采用残差瓶颈结构，上投影零初始化；初始输出与输入最大绝对误差为0.0。
- 全空/近空掩码的池化结果严格为零，细化输出无NaN或Inf。
- 模拟一步优化时冻结主干无梯度且权重不变，只有指定适配器参数更新。
- 无效查询的细化查询严格置零，细化掩码logit固定为-20。
- 本阶段只进行CPU单测，没有启动正式训练，没有调用DeepSeek API。

### 主要产物

- `ds_sod/mgrq/discovery_queries.py`
- `ds_sod/mgrq/sam2_adapters.py`
- `ds_sod/mgrq/mask_refinement.py`
- `ds_sod/configs/mgrq_i26_modules.json`
- `ds_sod/tests/test_mgrq_i26_modules.py`
- `ds_sod/scripts/validate_mgrq_i26_modules.py`
- `ds_sod/banks/mgrq/diagnostics/i26_modules_validation.json`
- `paper/MGRQ-Net_I26_发现查询适配器与细化模块单测报告.md`

### 建议下一命令

```text
执行 A30，seed=42
```

---

## A30｜纯视觉学习查询基线

| 字段 | 记录 |
|---|---|
| 工程状态 | `PASSED` |
| 性能门禁 | `NO-GO_A31` |
| 执行时间 | 2026-10-20，Asia/Shanghai |
| 严格划分 | train 2928 / dev 400，交集0 |
| 随机种子 | 42 |
| 模型 | 冻结SAM2.1 Base+＋5个纯视觉学习查询＋3层解码器 |
| MLLM输入 | 0 |
| 训练 | 3 epochs，batch 1，梯度累积8，AdamW，lr=1e-4 |
| 可训练参数 | 3,359,488 |
| A30 API调用 | 0 |

### 工程验收

- 完成8,784次训练样本访问和1,098次优化器更新，训练无NaN或Inf。
- 三轮窗口平均损失依次为0.6230、0.4080和0.3943。
- 最终检查点63个状态张量全部有限，SHA-256为`243f6cf3b551e0f6e424d6aa33695eca3e785c47e0e8c9d45131f761882edf54`。
- 400/400张严格dev预测完整；缺失、多余、尺寸不一致和不可读均为0。
- 未使用官方测试图像、测试GT或DeepSeek提示。

### 严格dev指标

| 数据集 | Sα | Fβmax | Fβmean | Eξmax | Eξmean | MAE |
|---|---:|---:|---:|---:|---:|---:|
| ORSSD | 0.7060 | 0.7671 | 0.5542 | 0.9831 | 0.7328 | 0.0855 |
| EORSSD | 0.6038 | 0.5916 | 0.3672 | 0.9823 | 0.6564 | 0.0885 |
| ORSI-4199 | 0.7357 | 0.8216 | 0.6119 | 0.9733 | 0.7578 | 0.1072 |
| 宏平均 | **0.6818** | **0.7268** | **0.5111** | **0.9795** | **0.7157** | **0.0938** |

### 门禁结论

- 同协议M04监督基线宏平均Sα为0.8920、MAE为0.0193；A30分别落后0.2102和增加0.0745。
- 当前组件匹配损失没有直接监督推理时的整图查询并集；超过5个组件的图像还存在监督截断，三个epoch累计舍弃606个组件引用。
- 根据计划中“若远低于现有监督基线，先诊断查询解码器，不进入A31”的规则，A31暂不执行。
- 建议A30-R1保持纯视觉定义不变，增加完整GT并集辅助损失并诊断空GT、多组件与密集组件子集。

### 主要产物

- `ds_sod/scripts/train_mgrq_a30.py`
- `ds_sod/configs/mgrq_a30_visual_query_s42.json`
- `ds_sod/runs/mgrq/A30_visual_query_s42/`
- `paper/MGRQ-Net_A30_纯视觉查询基线报告.md`
- `a30_training_progress.html`

### 建议下一命令

```text
执行 A30-R1，修复纯视觉基线
```

---

## A30-R1｜纯视觉查询基线修复

| 字段 | 记录 |
|---|---|
| 工程状态 | `PASSED` |
| 修复效果 | `PASSED` |
| 下一阶段门禁 | `GO_A31_WITH_RECORDED_GAP` |
| 执行时间 | 2026-10-20，Asia/Shanghai |
| 严格划分 | train 2928 / dev 400 |
| seed | 42 |
| 结构变化 | 无 |
| 损失修复 | 完整GT并集BCE+Dice；未匹配背景权重0.5 |
| MLLM输入/API调用 | 0/0 |

### 修复结果

- 严格dev宏平均Sα由A30的0.6818提高到0.8131，提升0.1312。
- MAE由0.0938降低到0.0373，下降0.0564。
- Fβmean由0.5111提高到0.6553，Eξmean由0.7157提高到0.8348。
- 空GT子集MAE由0.1411降至0.0018，多组件子集Sα由0.6451升至0.7814。
- 400/400张预测完整；最终检查点63个张量全部有限。
- A30-R1仍比M04低0.0789 Sα，差距必须保留并由后续模块逐项解释。

### 结论

A30的主要问题是组件匹配损失未直接监督推理使用的整图查询并集。A30-R1在不引入MLLM、不增加参数的前提下获得跨数据集一致改善，可以作为A31及后续消融的纯视觉基线。后续所有增量对比应使用A30-R1，不再使用未修复的原A30作为主基线。

### 主要产物

- `ds_sod/mgrq/reliable_query_decoder.py`
- `ds_sod/scripts/train_mgrq_a30.py`
- `ds_sod/configs/mgrq_a30_r1_visual_query_s42.json`
- `ds_sod/runs/mgrq/A30_R1_visual_query_s42/`
- `paper/MGRQ-Net_A30-R1_纯视觉基线修复报告.md`

### 建议下一命令

```text
执行 A31，seed=42
```

---

## A31｜DeepSeek几何查询

| 字段 | 记录 |
|---|---|
| 工程状态 | `PASSED` |
| 几何查询增益 | `PASSED` |
| 下一阶段门禁 | `GO_A32_WITH_RECORDED_GAP` |
| 执行时间 | 2026-10-20，Asia/Shanghai |
| 严格划分 | train 2928 / dev 400 |
| seed | 42 |
| 输入模态 | DeepSeek候选框＋置信度＋冻结SAM2 RoI特征 |
| 明确关闭 | 候选短语、查询类型、可靠性头、发现查询 |
| 训练 | 3 epochs，batch 1，梯度累积8，AdamW，lr=1e-4 |
| 可训练参数 | 4,299,136 |
| API调用 | 0 |

### 结果

- 宏平均Sα为0.8302，相比A30-R1的0.8131提高0.0171；三个数据集均提高。
- 宏平均MAE为0.0324，相比A30-R1的0.0373下降0.0050；三个数据集均下降。
- dev候选对GT组件的框IoU≥0.5召回为559/683（81.84%），候选匹配精度为602/1644（36.62%）。
- 400/400张预测完整，训练与检查点张量有限；最终权重SHA-256为`625a7f117c2205cfed05f07f1039c6c330d003dcfe3f58182ceec98b71209ad6`。
- A31仍低于M04 0.0618 Sα；几何查询收回约21.7%的Sα缺口，不能描述为已达到传统监督基线。

### 结论

DeepSeek离线候选的几何位置、置信度与SAM2 RoI视觉信息相对纯视觉学习查询具有明确正增益。由于A31完全未使用候选短语，本阶段结果是A32文本语义消融的干净基线。A32只应打开冻结CLIP短语特征，其他模块继续关闭。

### 主要产物

- `ds_sod/scripts/train_mgrq_a31.py`
- `ds_sod/configs/mgrq_a31_box_query_s42.json`
- `ds_sod/runs/mgrq/A31_box_query_s42/`
- `paper/MGRQ-Net_A31_DeepSeek几何查询报告.md`

### 建议下一命令

```text
执行 A32，seed=42
```

---

## A32｜加入DeepSeek短语语义

| 字段 | 记录 |
|---|---|
| 工程状态 | `PASSED` |
| 文本研究门 | `PASSED` |
| 下一阶段门禁 | `GO_A33_WITH_MODEST_TEXT_GAIN` |
| 执行时间 | 2026-10-20，Asia/Shanghai |
| 严格划分 | train 2928 / dev 400 |
| seed | 42 |
| 唯一主分支改动 | A31＋冻结CLIP短语特征与文本投影 |
| 明确关闭 | 查询类型、可靠性头、发现查询 |
| 可训练参数 | 4,430,464 |
| API调用 | 0 |

### 主分支结果

- 宏平均Sα为0.8348，相比A31提高0.0047；MAE为0.0304，相比A31下降0.0019。
- 三个数据集的Sα均未下降，ORSSD/EORSSD/ORSI-4199增量分别为+0.0003/+0.0061/+0.0076。
- 400/400张主预测完整，训练与检查点张量全部有限。
- 最终权重SHA-256为`5c45b9ef71c78a07da63027eb71f38b49eef38b4efb716f29959c540926bc07e`。

### 同权重文本对照

| 文本输入 | 宏平均Sα | MAE | 相对正确短语ΔSα |
|---|---:|---:|---:|
| 正确短语 | **0.8348** | **0.0304** | — |
| 粗类别词 | 0.8343 | 0.0318 | −0.0005 |
| 统一占位短语 | 0.8312 | 0.0325 | −0.0036 |
| 随机打乱短语 | 0.8258 | 0.0344 | −0.0091 |

三组对照共1,200张预测完整。正确短语在三个数据集上均优于打乱和占位文本，满足预设研究门；但相对粗类别词仅+0.0005，说明主要收益来自文本类别与候选位置的正确对齐，而不是长描述的细粒度语言内容。

### 结论

A32可以保留MLLM文本作为有证据的辅助创新点，但论文应表述为有限增益。A32仍比M04低0.0572 Sα，下一阶段应优先解决候选可靠性，而不是继续扩大文本编码器。

### 主要产物

- `ds_sod/scripts/train_mgrq_a32.py`
- `ds_sod/scripts/evaluate_mgrq_a32_text_controls.py`
- `ds_sod/configs/mgrq_a32_text_query_s42.json`
- `ds_sod/runs/mgrq/A32_text_query_s42/`
- `paper/MGRQ-Net_A32_DeepSeek短语语义报告.md`

### 建议下一命令

```text
执行 A33，seed=42
```

---

## A33｜加入查询可靠性头

| 字段 | 记录 |
|---|---|
| 工程状态 | `PASSED` |
| 研究门 | `FAILED` |
| 下一阶段门禁 | `NO-GO_A34` |
| 执行时间 | 2026-10-20，Asia/Shanghai |
| 严格划分 | train 2928 / dev 400 |
| seed | 42 |
| 新增模块 | `p_obj×p_iou`双分支可靠性头 |
| 最终融合 | 可靠性直接乘掩码概率后取最大并集 |
| 可训练参数 | 4,464,130 |
| API调用 | 0 |

### 工程与可靠性结果

- 训练8,784个样本、1,098次优化器更新，检查点张量全部有限。
- 正查询平均可靠性0.5248，负查询0.1084，ROC-AUC 0.8488，未发生全0或全1塌缩。
- A33三种提示与A32两种污染复评共2,000张预测完整。
- 最终权重SHA-256为`5a20c74a8ee068eef4b1139b13c2fe8669705e766cd291f6d471464be386e38f`。

### 失败门禁

- 干净提示Sα为0.8286，相比A32的0.8348下降0.0063，超过预设0.005容忍值；MAE由0.0304升至0.0329。
- ORSSD、EORSSD和ORSI-4199的Sα分别下降0.0050、0.0058和0.0080。
- 加入1/3个低前景占比背景框后，A32与A33都略有提高，说明压力输入没有造成有效污染，不能据此比较抗噪下降。
- 自动摘要已修正：两档`stress_valid=false`，不再把负下降值误写成抗噪通过。

### 结论

可靠性信号可学习，但`p_obj×p_iou`直接乘掩码概率的门控过强，损害干净性能。暂不进入A34。A33-R1应从A32权重初始化，先只训练可靠性头，采用残差软门，并以高置信错配显著短语构造真正困难的背景污染。

### 主要产物

- `ds_sod/scripts/train_mgrq_a33.py`
- `ds_sod/configs/mgrq_a33_reliability_s42.json`
- `ds_sod/runs/mgrq/A33_reliability_s42/`
- `paper/MGRQ-Net_A33_查询可靠性头报告.md`

### 建议下一命令

```text
执行 A33-R1，修复可靠性门控与污染协议
```

---

## A33-R1｜可靠性门控与污染协议修复

| 字段 | 记录 |
|---|---|
| 工程状态 | `PASSED` |
| 研究门 | `PASSED` |
| 下一阶段门禁 | `GO_A34_WITH_MODEST_RELIABILITY_GAIN` |
| 执行时间 | 2026-10-20，Asia/Shanghai |
| seed | 42 |
| 基础网络 | 加载并冻结A32查询构造器与解码器 |
| 可训练模块 | 可靠性头，33,666参数 |
| 训练 | 1 epoch，lr=5e-4 |
| 最终融合 | `max(P_i×[0.5+0.5p_obj p_iou])` |
| API调用 | 0 |

### 修复结果

- 残差乘积门控在三种候选中取得最高干净Sα 0.8356，相比A32提高0.0008；MAE由0.03044轻微降至0.03040。
- 可靠性ROC-AUC为0.8927，高于A33的0.8488；正负查询均值为0.2797/0.0414。
- 修复后的高置信错配污染使A32在+1/+3框下降0.0067/0.0187，压力协议有效。
- A33-R1在相同污染下降0.0066/0.0178，分别少下降0.0001/0.0010，方向通过但幅度很小。
- 2,800/2,800张评测预测完整；可靠性头检查点SHA-256为`8e2ec395321b909973b6cb9db0df7db16012cf66f33718c65b18fa246ec7634d`。

### 结论

A33-R1消除了A33的干净性能退化，并建立了有效污染对照，因此可以进入A34。但可靠性收益很小，论文应将其描述为轻微缓解高置信错误提示，不能作为主要性能贡献。

### 主要产物

- `ds_sod/scripts/train_mgrq_a33_r1.py`
- `ds_sod/configs/mgrq_a33_r1_reliability_s42.json`
- `ds_sod/runs/mgrq/A33_R1_reliability_s42/`
- `paper/MGRQ-Net_A33-R1_可靠性门控修复报告.md`

### 建议下一命令

```text
执行 A34，seed=42
```

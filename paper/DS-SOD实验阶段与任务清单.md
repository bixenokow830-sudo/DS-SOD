# DS-SOD 实验阶段与任务清单（控制文档）

> ⚠️ **v1 存档：任务编号 A～H 对应已废弃的 A+C 架构。v2 新任务清单见《DS-SOD_v2_MLLM生成显著图_设计文档.md》第 11 章（代码改造清单）与第 7.6 节（时间线）。**
> 版本：v1.0 ｜ 生成日期：2026-09-23
> 用途：**分阶段、按指令执行**的控制清单。用户点名阶段/任务编号（如 `A1`、`B2`、`阶段A全部`）后执行对应任务。
> 配套文档：`DS-SOD实验方案.md`（总体设计）、`DS-SOD完整框架详解_方案A+C.md`（架构）、`DeepSeek大模型集成ORSI-SOD创新方案报告.md`（选题论证）。

---

## 0. 项目现状（截至 v1.0）

### ✅ 已完成
| 项目 | 说明 |
|------|------|
| 硬件环境 | RTX 4060 Laptop 8GB（CUDA 12.6/12.7），PyTorch 2.14.0+cu126，Python 3.14.4 |
| 数据集 | ORSSD（train 4800 增强 / test 200）、ORSI-4199（train 16000 增强 / test 2199）、EORSSD（已解压并完成 ×8 增强 1400→11200 / test 600） |
| 预训练权重 | `GeleNet/model/pvt_v2_b2.pth`（96.8MB，whai362 官方 PVT-v2 release） |
| 基线代码 | GeleNet 官方仓库克隆并研读（`GeleNet/`） |
| DS-SOD 代码骨架 | `ds_sod/`：SPIM、SEM-RM、数据加载（含语义嵌入）、训练/测试/先验库/嵌入缓存脚本、LLM 客户端（含两套提示词模板）、`configs/default.yaml`、`secrets.env`（API key） |
| Python 依赖 | openai、transformers、pyyaml、numpy、tqdm 已装 |

### ⚠️ 进行中
- **A1**：pysodmetrics 兼容性处理（装不上则自实现四指标）；代码冒烟测试

### ❌ 待办
- A2 ～ H2 全部（见下）

---

## 1. 阶段总览

| 阶段 | 名称 | 目标（服务于哪条假设） | 预计 GPU/API 成本 | 状态 |
|------|------|------------------------|------------------|------|
| A | 基线复现 | 环境可信、指标口径校准 | ～3×8h GPU | 🔄 A1 ✅，A2～A4 待办 |
| B | LLM 语义先验库 | H1/H2/H3 的前提数据 | ～$3 API | ⬜ |
| C | 方案 A（SPIM）消融 | H1/H2/H3 | ～4×8h GPU | ⬜ |
| D | 方案 C（SEM-RM）闭环消融 | H4 | ～5×2h GPU | ⬜ |
| E | 主实验 | H6（SOTA 对比） | ～6×8h GPU | ⬜ |
| F | 附加实验 | H5/H7/H8 + 可视化 | ～2×8h GPU | ⬜ |
| G | 论文撰写 | 全部假设的成文 | 无 | ⬜ |
| H | 交付收尾 | 可复现性 | 无 | ⬜ |

**建议执行顺序**：`A1 → A2（后台训练）→ 并行 B1/B2（API 不占 GPU）→ A3/A4 → C → D → E → F → G → H`

---

## 2. 阶段 A｜基线复现

### A1 依赖补装 + 代码冒烟测试
- [x] 诊断 `pip install pysodmetrics` 失败原因（Python 3.14 兼容）
- [x] 方案：**自实现四指标**（Sα、Fβ、Eξ、MAE）→ `ds_sod/eval/metrics.py`（纯 numpy，口径移植自 PySODMetrics/MIT，已通过满分/零图/随机图自检）
- [x] 冒烟测试：GeleNet 前向+反向（batch 4/8 × 352，bf16 amp）记录显存 ✅ bs8 峰值 2.4GB（8GB 显存富余）
- [x] 冒烟测试：GeleNet+SPIM（variant=all，sem_dim=1536）前向+反向 ✅
- [x] 冒烟测试：SEM-RM 前向（dummy S0/F/e_diag）+ 损失监督 ✅
- [x] 冒烟测试：DSTrainDataset + SemanticBank（无 bank 时零向量兜底）✅
- [x] 输出：**参数量** GeleNet 25.454M ｜ SPIM +0.158M ｜ SEM-RM +0.073M（论文表5素材）
- 备注：补装依赖 timm 1.0.30；`_use_new_zipfile_serialization=False` 保存兼容已验证

### A2 GeleNet 基线训练（官方协议）
- [ ] 协议：Adam lr=1e-4，44 epoch，batch=8，352×352，30 epoch ×0.1 衰减，BCE+IoU
- [ ] 训练 EORSSD（11200 张）→ 产出 `runs/EORSSD_none_s42/`
- [ ] 训练 ORSSD（4800 张）→ 产出 `runs/ORSSD_none_s42/`
- [ ] 训练 ORSI-4199（16000 张）→ 产出 `runs/ORSI4199_none_s42/`
- [ ] 每 5 epoch 存 checkpoint；训练日志 JSONL

### A3 测试生成显著图 + 评测
- [ ] 对三数据集测试集推理，输出显著图（PNG 0-255）
- [ ] 计算 Sα / Fβ_max / Fβ_mean / Eξ_max / Eξ_mean / MAE
- [ ] **验收标准**：与 GeleNet 论文报告值差距 ≤0.5% Sα；否则排查预处理/评测口径

### A4 评测口径校准
- [ ] 解压 `GeleNet/GeleNet_saliencymap_PVT.zip`（官方发布显著图）
- [ ] 用我方评测脚本算官方显著图指标，与论文表对比 → 校准评测实现
- [ ] 结论写入 SOP（第 4 章）

---

## 3. 阶段 B｜LLM 语义先验库

### B1 API 试点（50 张）
- [ ] 从三数据集各抽 ～17 张（含明显难例）
- [ ] 先验模板 + 诊断模板各调一次
- [ ] **质检标准**：JSON 解析成功率 ≥95%；类别词落在固定词典；人工抽 10 张判断合理性
- [ ] 模板有问题 → 改模板重试（全量前修正免费）

### B2 全量构建 prior_bank.json
- [ ] 范围：仅原始图 6999 张（ORSSD 800 + EORSSD 2000 + ORSI-4199 4199）；增强副本按基名共享先验
- [ ] 参数：temperature=0、detail="low"、并发 25、0.2s 间隔、失败重试 3 次、断点续跑
- [ ] 校验：字段完整性 + 类别/难例标签词典合法性；失败图标记 `status=failed`
- [ ] 产出：`ds_sod/banks/prior_bank.json`（随代码开源）

### B3 CLIP 嵌入缓存
- [ ] 下载 `openai/clip-vit-base-patch32`（冻结）
- [ ] 三类字段分别编码：e_cat（类别模板句均值）/ e_app / e_chal
- [ ] 产出：`ds_sod/banks/embed_cache/{dataset}/{name}.npz`

---

## 4. 阶段 C｜方案 A（SPIM）实现与消融

### C1 SPIM 冒烟测试
- [ ] SPIM 三路注入（深层 11×11 / 中层 22×22 / 浅层 88×88）前向形状验证
- [ ] 语义缺失兜底：可学习默认向量

### C2 消融训练（5 变体 × 各数据集）
| 变体 | SPIM 输入 | 假设 |
|------|-----------|------|
| none | 无（= 基线，复用 A2） | 基准 |
| clip-static | 固定模板文本 "A photo of a ship." | H2（LLM 语义 > 静态文本） |
| cat | LLM 类别 only | H3 拆类别贡献 |
| cat+app | LLM 类别+外观 | H3 拆外观贡献 |
| all | 类别+外观+难例（完整 SPIM） | 完整方案 A |

- [ ] EORSSD 上先跑全部 4 个新变体（+all 与主实验复用）
- [ ] ORSSD / ORSI-4199 跑 all 变体（主实验需要）

### C3 消融评测 → 论文表2
- [ ] 各变体三数据集 Sα/Fβ/Eξ/MAE
- [ ] 预期单调性：all > cat+app > cat > clip-static > none
- [ ] 预案：若 clip-static ≈ all → H2 改为"文本先验有效"，重心压方案 C

---

## 5. 阶段 D｜方案 C（SEM-RM）验证-修正闭环

### D1 诊断库构建
- [ ] 用阶段 C 最优 M1 对训练集推理 S⁰
- [ ] S⁰ 半透明红色渲染图（透明度 0.3/0.4/0.5 试点选定）
- [ ] 诊断模板调用（原始训练图 2000 张，增强副本共享）
- [ ] GT 计算 A_miss（GT−S⁰>0.5）与 A_fp（S⁰−GT>0.5）监督标签
- [ ] 产出：`diag_bank.json`

### D2 SEM-RM 训练
- [ ] 冻结 M1；仅训练 SEM-RM（<2M 参数），lr=1e-4，30 epoch
- [ ] 损失：L_corr = BCE(S¹,GT)+IoU(S¹,GT) + 0.1·BCE(A_miss) + 0.1·BCE(A_fp)

### D3 消融（6 组）→ 论文表3
| 变体 | 诊断来源 | 假设 |
|------|----------|------|
| M1 | —（阶段 C 上限） | 基准 |
| +Blind-Refine | 无诊断（纯 refine） | 修正模块本身是否有用 |
| +Fixed-Text | 固定通用诊断句 | 诊断内容是否有意义 |
| +LLM-Diag-Offline | 离线诊断库 | 完整方案 C |
| +LLM-Diag-Online | 推理时实时调用 | 在线模式上限 |
| IPDiff 式对照 | 随机扰动迭代 | H4（语义引导 > 盲迭代） |

- [ ] 轮数消融：1 轮 vs 2 轮
- [ ] 预期：Online ≥ Offline > Fixed > Blind ≈ M1

---

## 6. 阶段 E｜主实验

### E1 DS-SOD 完整模型训练
- [ ] 三数据集 × 3 种子（all 变体）→ mean±std
- [ ] 离线模式（SPIM only）与在线模式（SPIM+SEM-RM）分别评测

### E2 SOTA 对比表 + PR/F 曲线 → 论文表1、图3
| 组别 | 方法 |
|------|------|
| CNN 代 | MCCNet、ACCoNet、CorrNet、ERPNet |
| Transformer 代 | GeleNet、VST、ICON、MRBINet |
| 大模型/扩散代 | SAM2-RS、IPDiff |
| 文本融合新工作 | 2026 文本-视觉融合方法 1～2 个 |
| 本文 | DS-SOD（离线）+ DS-SOD（在线） |

- [ ] 每数据集一张主表：方法 × {Sα, Fβ_max, Fβ_mean, Eξ_max, Eξ_mean, MAE}
- [ ] PR 曲线 + F-measure 曲线图
- [ ] 数值来源：优先引用原论文报告值；无法对齐的用官方代码复现并注明

### E3 统计检验
- [ ] 3 种子 mean±std；配对 t 检验 vs GeleNet（可选加分项）

---

## 7. 阶段 F｜附加实验

### F1 场景分组评测（H5）→ 论文表4
- [ ] 用先验库 challenge_tags 对测试集打标签分组
- [ ] 组别：low_contrast / shadow / multiple_objects / large_object / similar_spectrum / small_object / clutter / none
- [ ] DS-SOD vs GeleNet vs IPDiff 各子集 Sα/MAE；预期增益集中在难例组

### F2 效率与成本（H6）→ 论文表5、图5
- [ ] 参数量（SPIM + SEM-RM < 3M）、FLOPs、FPS（离线/在线）
- [ ] 每图 API 延迟与 token 数；总 API 花费
- [ ] "API 调用次数 vs Sα" 权衡曲线

### F3 跨主干 + 跨数据集（H7/H8）→ 论文表6
- [ ] SPIM+SEM-RM 移植到另一基线（如 MCCNet 的 VGG 编码-解码器）
- [ ] ORSSD 训练 → 直接测 EORSSD/ORSI-4199 测试集（不微调）

### F4 可视化 + 失败分析 → 图4、图6
- [ ] 四类难例成功/失败对比图
- [ ] LLM 思考过程（Thinking 模式）截图
- [ ] 失败案例 LLM 归因 → 论文 future work

---

## 8. 阶段 G｜论文撰写（中文初稿 + 英文摘要）

- [ ] **G1** 大纲 + Abstract（中英）+ Introduction
- [ ] **G2** Related Work + Method（框架图 / 公式 / 提示词模板 / 伪代码）
- [ ] **G3** Experiments（表1～6、图1～6 随实验进度填入）
- [ ] **G4** Conclusion + 审稿质疑应答（第八章）+ 公平性声明

**论文表格/图清单**（对照产出，避免白做实验）：
| 编号 | 内容 | 来源 |
|------|------|------|
| 表1 | 三数据集主结果对比（16+ 方法 × 6 指标） | 阶段 E |
| 表2 | 先验消融（5 行） | 阶段 C |
| 表3 | 修正闭环消融（6 行 + 轮数） | 阶段 D |
| 表4 | 场景分组评测 | 阶段 F1 |
| 表5 | 效率与成本 | 阶段 F2 |
| 表6 | 跨主干 + 跨数据集 | 阶段 F3 |
| 图1 | 总框架图 | G2 |
| 图2 | 提示词模板与先验库样例 | 阶段 B |
| 图3 | PR/F 曲线 | 阶段 E |
| 图4 | 难例成功案例可视化 | 阶段 F4 |
| 图5 | 成本-精度权衡曲线 | 阶段 F2 |
| 图6 | 失败案例分析（含 LLM 思考） | 阶段 F4 |

---

## 9. 阶段 H｜交付收尾

- [ ] **H1** 《DS-SOD 详细实验步骤 SOP》文档（环境/命令/协议/验收标准，逐条可执行）
- [ ] **H2** 开源仓库整理：README、requirements.txt、目录说明、prior_bank.json + diag_bank.json、公平性声明

---

## 10. 假设-实验对照速查

| 假设 | 内容 | 实验出处 |
|------|------|----------|
| H1 | LLM 语义先验提升 ORSI-SOD 精度 | C2/C3、E |
| H2 | "会看会想的 LLM 语义" 优于静态 CLIP 文本 | C2（clip-static vs cat/all） |
| H3 | 类别/外观/难例各自有贡献 | C2（cat / cat+app / all 逐项拆解） |
| H4 | 语义引导迭代优于 IPDiff 式盲迭代 | D3 |
| H5 | 增益集中在语义难例 | F1 |
| H6 | 达到/超过 SOTA 且成本可接受 | E、F2 |
| H7 | 主干无关、即插即用 | F3 |
| H8 | 跨数据集泛化 | F3 |

**成败标准（提前写死）**：
- ✅ 成功：三数据集全面超过 GeleNet（Sα ≥ +0.3%），与 IPDiff/SAM2-RS 打平或更好，难例子集 Sα +1% 以上，H2/H4 消融成立
- ⚠️ 部分成功：整体打平但难例显著提升 + 成本/效率优势 → 叙事转"语义难例专精 + 低成本"
- ❌ 失败兜底：见《DS-SOD实验方案.md》第 12 章预案

---

*控制文档完。执行方式：回复任务编号（如 `A2`、`B1`）或阶段名（如 `阶段B全部`）。*

# DS-SOD v2 详细实验步骤（可执行清单）

> 版本：v2.0-steps ｜ 配套：《DS-SOD_v2_MLLM生成显著图_设计文档.md》（架构与消融设计）
> 目标：**2～3 周、零 GPU 训练、纯 API + CPU**，产出论文全部表格与图。
> 任务编号规则：`V阶段-序号`（如 `V0-1`），执行时回复编号即可。

---

## 第 1 章 研究假设与成败标准（先写死）

| 假设 | 内容 | 对应任务 |
|------|------|---------|
| H1 | MLLM 仅凭"看图+语言"零训练生成达到竞争水平的显著图 | V2-3 |
| H2 | AI 链式生成的提示词优于一步到位的坐标输出 | V3-3 |
| H3 | 几何粒度单调：point < box < polygon < +zoom | V3-4 |
| H4 | 自修正闭环提升精度 | V3-1 / V3-5 |
| H5 | 增益集中在语义难例 | V4-2 |
| H6 | 达到/接近 SOTA 且总成本优势明显 | V2-3 + V4-3 |
| H7 | 精度随模型规模单调、成本可接受 | V4-4 |
| H8 | 跨数据集零样本泛化 | V2（三数据集直接零样本评测即证据） |

**成败标准**：
- ✅ 成功：DS-SOD-Full 三数据集与 GeleNet/IPDiff 同区间（Sα 差距 ≤3%），难例子集领先，H2/H4 成立；
- ⚠️ 部分成功：整体弱但难例显著领先 + 零训练/成本叙事成立 → 转"零训练 + 语义难例专精"；
- ❌ 兜底：见第 10 章预案 P-2（Hybrid 转正 / 回退 v1 路线）。

---

## 第 2 章 环境与预算

### 2.1 环境（无 GPU 要求）

- Python 3.x；依赖：`openai`、`numpy`、`opencv-python`（或 `scikit-image`）、`pyyaml`、`tqdm`；
- `ds_sod/secrets.env` 内 `DEEPSEEK_API_KEY`（已有）；
- 仅消融 V4-1（Hybrid/SAM2）需要 GPU ≥8GB——**可选**。

### 2.2 预算

| 项目 | 估算 |
|------|------|
| 全量 Pass1+Pass2（测试集 2999 + 训练集原始图 ≈7000 张） | ≈$40～100（实测单次调用输出 2～12K tokens，思考模式占大头） |
| SelfCheck / zoom-in / 消融重复调用 | ≈$30～60 |
| 试点 50 张 + 失败重试 + 更大模型抽样 | ≈$5～10 |
| **充值** | **$100（跑全部）；只跑测试集 $50 即可** |

---

## 第 3 章 数据集与公平性铁律

| 数据集 | 训练/测试 | 本方法推理对象 |
|--------|----------|---------------|
| ORSSD | 600/200 | 测试集 200（评测）+ 训练集（消融/分组素材） |
| EORSSD | 1400/600 | 测试集 600（评测）+ 训练集（同上） |
| ORSI-4199 | 2000/2199 | 测试集 2199（评测）+ 训练集（同上） |

**三条铁律（防测试集泄漏，写进论文）**：
1. **dev 集**：从 ORSSD 训练集抽 50 张，**只用于模板/渲染参数迭代**，永不进入最终测试评测；
2. 三数据集**测试集只在最终评测阶段接触一次**，模板迭代阶段绝不调用；
3. DeepSeek 全程不接触 GT；所有中间产物（JSON、渲染图）落盘，可复现。

---

## 第 4 章 评价指标

沿用 `ds_sod/eval/metrics.py`（v1 已自实现并自检）：**Sα、Fβ_max、Fβ_mean、Eξ_max、Eξ_mean、MAE**。

**边界情形口径（写进评测脚本注释）**：
- GT 全零 & 预测全零 → Fβ=1；
- GT 全零 & 预测非零 → Fβ=0、MAE 按预测面积计；
- 预测全零 & GT 非零 → Fβ=0。

---

## 第 5 章 流程总览（5 阶段）

```
阶段0  代码实现 + 50 张试点质检（模板迭代，免费）      → 渲染器、四套模板定稿
阶段1  全量构建 mask_bank.json（API 后台跑 1～2 天）    → 掩码库 + 质检报告
阶段2  渲染 + 评测 → 主表初版                          → DS-SOD-Zero 三数据集指标
阶段3  自修正闭环 + zoom-in + 消融 1～4                 → 论文表2（消融汇总）
阶段4  附加实验：Hybrid、场景分组、效率成本、模型规模   → 论文表4/5/6
阶段5  可视化 + 失败分析 + 论文素材汇总                 → 图4/6
```

---

## 第 6 章 各阶段详细步骤

### 阶段 0｜代码实现与试点（第 1 周，天 1～3）

**V0-1 实现渲染器 `ds_sod/utils/rasterize.py`** ✅ 已完成
（纯 numpy 零依赖实现——多边形奇偶射线法填充，无需 cv2/skimage，任何环境行为一致）

```
hard_rasterize(mask_json, H, W, conf_mult=True) -> np.ndarray [0,1]
  - polygon: 坐标 [0,1000]→[0,H/W] 映射后扫描线填充（cv2.fillPoly）
  - box:     矩形填充；point: 高斯圆盘（σ=8～12px）
  - none:    全零图；多实例: 并集 ∪
  - conf_mult=True 时各实例掩码乘 confidence 后取并集
soft_rasterize(mask_json, H, W, alpha=2.0) -> np.ndarray   # SDF + sigmoid（可微备用）
render_overlay(image, S, alpha=0.4) -> np.ndarray           # 半透明红叠加（SelfCheck 用）
validate_geometry(json) -> (cleaned, issues)                # 坐标∈[0,1000]、顶点3～24、
                                                           # box w/h>0、实例≤5；非法项剔除并记录
```

- **自检单测** ✅ `ds_sod/scripts/test_rasterize.py` 35 项断言全过（已知三角形 vs 手算掩码；空图/全图；顶点数边界；坐标越界/非数值剔除；实例上限；并集+置信度；高斯点；软渲染；叠加图）；真实 ORSSD 图集成验证通过，预览图在 `ds_sod/runs/mllm/pilot/v0_1_demo_*`。

**V0-2 改造 `ds_sod/utils/llm.py`** ✅ 已完成
新增四套 v2 模板（`PROMPTGEN_PROMPT` / `MASKGEN_PROMPT` / `ZOOMIN_PROMPT` / `SELFCHECK_PROMPT`，全文见设计文档第 2 章）+ 填充函数 `build_maskgen_prompt`/`build_selfcheck_prompt`；v1 模板保留存档。顺带修复 `_load_key` 中文 Windows 下 GBK 解码崩溃（显式 utf-8）。V0-3 试点后追加：max_tokens 默认 16000、SYSTEM_V2 system 消息、`_extract_json` 解析容错。验收：`ds_sod/scripts/test_llm_v2.py` 全部通过。

**V0-3 写试点脚本 `scripts/pilot_mllm.py`** ✅ 已完成（两轮迭代后达标）
首轮（max_tokens=1200、无 system）质量门不达标：Pass1 解析率 90%、Pass2 仅 24% —— 根因是**模型思考模式把输出预算吃满**（finish_reason=length、content 空、reasoning_tokens=4000/4000）。修复：max_tokens→16000、system 消息"直接输出最终 JSON，禁止逐步推理"（思考 token -31%）、`_extract_json` 解析容错、`--workers` 并发。第二轮：**Pass1/Pass2 解析率 100%、管线成功率 50/50**；又发现 box/point 格式漂移 → 校验器宽容化（救回 10 实例）+ MASKGEN 模板升级 v1.1；`scripts/rerender_pilot.py` 离线重渲染（零 API 费用）。QC 报告：`runs/mllm/pilot/qc_summary.txt`。

**V0-4 试点人工质检（质量门）**：

| 检查项 | 达标线 |
|--------|--------|
| JSON 解析成功率 | ≥95% |
| 几何合法率（validate 通过） | ≥90% |
| 人工抽看 20 张叠加图：类别正确、多边形大致贴合、无明显漏检/误检 | 15/20 以上 |

- 记录问题类型（类别漂移 / 坐标漂移 / 多目标漏检 / 边界粗糙 / 无目标误判），**按问题改模板重跑**（全量之前修正免费）；
- 达标后**冻结模板**，版本号记入 `configs/mllm.yaml`（如 `template_version: v1.0`）。

**V0-5 参数定稿写入 `configs/default.yaml` 新增 `mllm:` 节** ✅ 已完成
冻结参数：model/temperature=0/detail=high/max_tokens=16000/SYSTEM_V2/模板 v1.5/坐标 [0,1000]/实例≤5/顶点 3～40/单实例面积守卫 0.85/并集覆盖守卫 0.85/overlay 灰底 0.5/zoom 参数/dev_seed=42。详见配置文件注释。

**V0-6（可选）决定 zoom-in 是否进默认流程** ✅ 已完成：**不进默认**
dev 50 张 GT 对比（干净重跑，修复多线程共用临时文件致 400 错误的 bug）：
mean IoU 0.396→0.407（+1.11%）、Sα +1.25pt、MAE -0.005，变好 22/变差 16/不变 12。
ΔIoU=+1.11% < 1.5% 门限 → zoom 不进默认（`zoom_in_default: false`），保留为消融变体
DS-SOD-Zoom。zoom 实例级调用脚本：`scripts/zoom_demo.py`。

---

### 阶段 1｜全量掩码库构建（第 1 周，天 3～5，后台跑）

**V1-1 实现并运行 `scripts/build_mask_bank.py`** ✅ 已完成
三测试集 2999 张全量构建：**2999/2999 = 100% 成功**，实际费用 **$5.58 + $0.01（重试）**
（远低于 $32 预算线与 $24 预估——批量运行中思考 token 明显短于试点）。
2 张 Pass2 失败（ORSSD/0594、ORSI4199/2374）经 `--max_tokens 32000` 重试成功。
产出：`ds_sod/banks/mask_bank.json`（meta+images，含 pass1/pass2_raw/pass2_clean/issues）。

```json
{"meta": {"model": "...", "template_version": "v1.0", "generated": "..."},
 "images": {"ORSSD/0001.jpg": {"pass1": {...}, "pass2": {...},
                                "status": "ok", "issues": []}}}
```

**V1-2 质检统计报告** ✅ 已完成（`scripts/check_mask_bank.py --out` 生成，UTF-8 落盘）
终版（2999/2999）：Pass1 解析 100%、Pass2 99.9%→重试后 100%、管线 100%，门限全过。
问题实例 44/2999（empty×31 为守卫拦后判 none、oversized×7 为面积守卫生效、
too_many_vertices×4、too_many_instances×3）；顶点 mean 10/max 40；类别分布健康，
发现类别漂移 lake×7/cloud_shadow×1（不在词典，不影响渲染，记 limitation）。
实际费用 $5.59。报告：`runs/mllm/qc_report_v1_2.txt`。

**V1-3 失败图人工复跑** ✅ 已完成
2 张失败（ORSSD/0594、ORSI4199/2374，均为 Pass2 思考预算耗尽）用
`--max_tokens 32000` 重试成功（$0.01）。终版：2999/2999 = 100%。

---

### 阶段 2｜渲染 + 评测 → 主表初版（第 2 周，天 1～2）

**V2-1 实现推理入口 `scripts/predict_mllm.py`** ✅ 已完成（2999 张显著图已渲染，零 API 费用）：

```
python predict_mllm.py --variant zero --dataset ORSSD --split test
  → 读 mask_bank → hard_rasterize → 显著图 PNG（0-255）→ runs/mllm/zero/ORSSD/maps/
variant 选项: zero | r1 | zoom | full   （阶段3 逐步解锁）
```

**V2-2 评测 `scripts/eval_mllm.py`** ✅ 已完成：对 PNG 与 GT 算四指标 + PR/F 曲线 npz → `runs/mllm/zero/{dataset}/metrics.json`。

**V2-3 主表初版** ✅ 已完成 —— **DS-SOD-Zero 实测：ORSSD Sα 0.6788 / MAE 0.0818；EORSSD 0.6700 / 0.0474；ORSI-4199 0.6492 / 0.1087**（引用值 GeleNet/IPDiff 的 Sα 为 0.89～0.96）

**V2-4 成败判定** ❌ **不达标 → 触发预案 P-2 ①**：Sα 差距约 27pt（标准为 ≤3pt）。结论与 SaliLLM 基准一致——MLLM 定位强、分割弱，"文本-几何"输出通道的精度上限 ≈ 框级。→ **主线转为 DS-SOD v2.1-Hybrid（MLLM 提示 + SAM2 像素解码）**，详见《DS-SOD_v2.1_Hybrid方案_实验步骤.md》（**待人工审核**）。纯几何路线降级为消融变体 DS-SOD-Zero，其框级精度上限的实测数据成为论文 motivation 证据。

---

### 阶段 3｜闭环 + zoom + 消融（第 2 周，天 3～7）

**V3-1 自修正闭环（DS-SOD-R1）**：

```
predict_mllm.py --variant r1：
  S 渲染 → render_overlay(alpha 0.3/0.4/0.5 择一，dev 集选定) → SelfCheck 调用
  → merge(add/remove/refine) → 重渲染 → S¹ → 评测
```

**V3-2 zoom-in（DS-SOD-Zoom）与 Full**：

- Zoom：对每个 box 外扩 20% 裁剪 → 2× 放大 → ZOOMIN 模板要局部多边形 → 坐标映射回全图 → 替换原几何；
- Full = R1 + Zoom → 三数据集评测。

**V3-3 消融1（H2）**：一步坐标 vs 两段链——去掉 Pass1，用通用提示词直接 MaskGen，其余不变；预期两段链显著更好。

**V3-4 消融2（H3）**：几何粒度四档——`point-only` / `box-only` / `polygon`（默认）/ `+zoom`，各跑一个数据集（建议 EORSSD）对比。

**V3-5 消融3（H4）**：轮数 0/1/2 对比；若 1 轮与 2 轮差距 <0.1% Sα → 论文默认 1 轮（省成本）。

**V3-6 消融4（稳健性）**：硬 vs 软渲染；confidence 乘子 on/off（V0-1 的 `conf_mult`）——证明默认配置（硬渲染+乘子开）合理。

**产出**：论文表2（消融汇总表）。

---

### 阶段 4｜附加实验（第 3 周，天 1～2）

**V4-1 Hybrid 消融（需 GPU ≥8GB，可选）**：MaskGen 的 box/point 提示词 → SAM2 解码掩码 → 与 Full 对比。**意义**：回答"要不要分割基础模型兜底"（SaliLLM 已证明 MLLM 定位强、分割弱，此消融直接检验）。

**V4-2 场景分组评测（H5）**：用 Pass1 的 `challenge_tags` 对测试集分组（low_contrast / shadow / multiple_objects / large_object / similar_spectrum / small_object / clutter / none），报告 Zero/Full vs GeleNet 各子集 Sα/MAE → 论文表4。

**V4-3 效率与成本（H6）**：每图 tokens、每 pass 延迟、渲染速度（maps/s，CPU）、总 API 账 → 论文表5 + "API 调用次数 vs Sα"权衡曲线（图5）。

**V4-4 模型规模消融（H7，可选）**：测试集抽 100 张用更大模型（如 DeepSeek 更强型号）跑 Pass1+Pass2，对比精度与成本 → 图5 的第二条曲线。

---

### 阶段 5｜论文素材（第 3 周，天 2～4）

**V5-1 可视化**：四类难例成功/失败对比图（Zero vs R1 vs Full）+ LLM 思考过程截图 → 图4。

**V5-2 失败分析**：按 challenge_tags 与类别统计失败图，用 LLM 归因（"云雾遮挡/超小目标/多目标混淆"）→ 图6 + limitation 素材。

**V5-3 汇总**：全部表图对照设计文档第 7 章清单核对，移交论文写作（阶段 G）。

---

## 第 7 章 论文表格/图清单（来源对照）

| 编号 | 内容 | 来源任务 |
|------|------|---------|
| 表1 | 三数据集主结果（DS-SOD-Zero/R1/Zoom/Full + 引用值） | V2-3、V3-1/2 |
| 表2 | 消融汇总（两段链/几何粒度/轮数/渲染细节） | V3-3～V3-6 |
| 表3 | 场景分组评测 | V4-2 |
| 表4 | 效率与成本 | V4-3 |
| 表5 | Hybrid 对照 + 模型规模 | V4-1、V4-4 |
| 图1 | 总框架图 | 写作期 |
| 图2 | 提示词模板与掩码库样例 | V1 |
| 图3 | PR/F 曲线 | V2 |
| 图4 | 难例成功案例可视化 | V5-1 |
| 图5 | 成本-精度权衡曲线 | V4-3/4 |
| 图6 | 失败案例分析（含思考过程） | V5-2 |

---

## 第 8 章 时间线（3 周日历）

| 周 | 任务 | 里程碑 |
|----|------|--------|
| 1（天1-3） | V0 全部（代码+试点+模板冻结） | rasterize.py、模板 v1.0 |
| 1（天3-5） | V1 全量构建（后台） | mask_bank.json + 质检报告 |
| 2（天1-2） | V2 渲染评测 | Zero 三数据集指标 |
| 2（天3-7） | V3 闭环/zoom/消融 | 论文表2 |
| 3（天1-2） | V4 附加实验 | 论文表4/5、表3（分组） |
| 3（天2-4） | V5 素材 + 汇总 | 图4/6、全部表图齐 |
| 缓冲 | 0.5 周 | 失败重跑、补漏 |

---

## 第 9 章 工程执行细节

1. **目录约定**：`ds_sod/banks/mask_bank.json`、`mask_bank_progress.json`；`ds_sod/runs/mllm/{variant}/{dataset}/maps|metrics.json`；`ds_sod/configs/mllm.yaml`。
2. **断点续跑**：进度文件按 `{dataset}/{filename}` 记录，重跑自动跳过已完成 key。
3. **随机性控制**：temperature=0；所有中间产物落盘；模板版本号 + 模型名 + 日期写入 mask_bank 的 meta。
4. **评测口径**：显著图 PNG 0-255 与 GT 同分辨率；指标实现复用 `eval/metrics.py`，边界情形按第 4 章口径。
5. **API 限流**：并发 25 + 0.2s 间隔；遇到 429 自动指数退避。
6. **花费监控**：脚本每次调用累计 token 与估算费用，打日志；累计超预算线自动暂停。

---

## 第 10 章 风险与预案

| 编号 | 触发条件 | 预案 |
|------|---------|------|
| P-1 | 几何合法率 <90% 或坐标质量差 | ① detail 提高（默认→高清）；② 模板加 1 个 few-shot 坐标示例；③ 坐标空间从 [0,1000] 改为"直接像素 + 图像尺寸告知"；④ **思考模式占满输出预算**（试点已踩坑：max_tokens 必须 ≥16000 + SYSTEM_V2 抑制推理，重试 3 次兜底）；⑤ 试点阶段迭代，全量前免费 |
| P-2 | 整体 Sα 差距 >5% 且难例不领先 | ① Hybrid（LLM 提示 + SAM2）转为主方法，叙事改为"LLM 语义提示 + 基础分割模型"；② 仍不行 → 回退 v1 路线（CNN 主干 + LLM 先验）为主体，v2 写进 limitation——诚实收场 |
| P-3 | API 故障/预算超支 | mask_bank 已离线缓存，评测与消融全部可离线继续；模板版本冻结保证一致性 |
| P-4 | 多目标/无显著目标图表现差 | 统计该类占比单独报告；Pass1 加"先数目标个数再逐一描述"的计数自查句；SelfCheck 的 add 通道增强；作为 limitation 如实写 |

---

## 第 11 章 公平性声明（写进论文实验节）

1. DeepSeek 仅接收图像与自渲染图，从未接触 GT；
2. 提示词模板、mask_bank.json、渲染器、评测脚本全部开源；
3. 渲染器无学习参数、无视觉输入——显著图内容全部来自大模型输出；
4. 模板/渲染参数只在 dev 集（ORSSD 训练集 50 张）上迭代，测试集仅最终评测接触一次；
5. 对比方法数值优先引用原论文，无法对齐用官方代码复现并注明；
6. API 花费、每图 tokens、延迟、调用轮数、模型版本如实报告。

---

## 附：任务编号速查 + 假设-任务映射

| 假设 | 任务 | 假设 | 任务 |
|------|------|------|------|
| H1 | V2-3 | H5 | V4-2 |
| H2 | V3-3 | H6 | V2-3 + V4-3 |
| H3 | V3-4 | H7 | V4-4 |
| H4 | V3-1 / V3-5 | H8 | V2（零样本跨集评测） |

**执行顺序建议**：`V0-1 → V0-2（并行）→ V0-3～V0-6 → V1（后台挂起）→ V2 → V3 → V4 → V5`

---

*步骤清单完。回复任务编号（如 `V0-1`）或阶段名（如 `阶段0全部`）即可开始执行。*

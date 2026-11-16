# R4 主干升级实验（SAM2-large）— 暂停点与续跑说明

> 触发：审稿风险应对方案 D（小实验拉近 SOTA + 强化"能力边界诊断"定位）
> 暂停时间：训练任务在后台运行中（如未被打断会自动完成并保存权重）

## 一、为什么做

主结果（base+ 校准器）Sα 0.865/0.853/0.799，比 GeleNet 低 8.2/8.5/8.7 点、比 IPDiff 低 ～9 点。
方案 D = 换 SAM2-large 主干 + 校准器重训（预期 +2～3 点），同时把论文定位改为"能力边界诊断 + 效率前沿"。

## 二、已完成

1. ✅ 权重下载：`sam2_repo/checkpoints/sam2.1_hiera_large.pt`（898,083,611 字节）
2. ✅ 脚本改造（新增 `--model` 参数）：
   - `ds_sod/scripts/predict_hybrid.py`（--model base_plus|large）
   - `ds_sod/scripts/train_adapter.py`（--model；--out 留空自动命名 `adapter/mask_decoder_{model}_e{epochs}.pt`）
   - `ds_sod/scripts/gt_box_upperbound.py`（--model + --adapter）
3. ✅ 零训练 large 三集评测（`runs/mllm/hybrid-large/metrics.json`）：

| Sα | base+ 零训练 | large 零训练 | 变化 |
|----|-------------|-------------|------|
| ORSSD | 0.781 | 0.7815 | +0.0 |
| EORSSD | 0.770 | 0.7737 | +0.4 |
| ORSI-4199 | 0.735 | 0.7354 | +0.0 |

**诊断结论（已定稿可写入论文）**：零训练阶段换主干几乎无增益 → 瓶颈在提示（语义定位）质量，
不在主干容量。这直接支撑"意图层是主瓶颈、校准层补偿解码误差"的叙事，也说明单靠 B 路线
（换主干）拉分有限，A 路线（定位改写）是必须的。

## 三、运行中 / 待续

4. ⏸️ **large 校准器训练已暂停**（用户手动叫停，跑至 step 175/12000，权重未保存、无残留）
   - 续跑命令：`python ds_sod/scripts/train_adapter.py --model large --epochs 3`
   - 4000 图 × 3 epoch，预计 80～90 分钟；权重输出 `runs/mllm/adapter/mask_decoder_large_e3.pt`

## 四、训练完成后的续跑清单（按序）

5. 适配后三集评测（命令同 hybrid-adapter3ds，加 --model large --adapter mask_decoder_large_e3.pt，
   输出到 `runs/mllm/hybrid-large-adapter/{ORSSD,EORSSD,ORSI4199}/maps`）+ `eval_mllm.py --variant hybrid-large-adapter`
6. GT 框上界（large + 新校准器）：`gt_box_upperbound.py --model large --adapter ...` 三集各跑一遍
   （img/gt 路径：ORSSD/Image-test+GT-test；EORSSD/test-images+test-labels；ORSI-4199/Image-test+GT-test）
7. 对比 base+ vs large 最终数字，决定论文主结果用哪个（哪个高用哪个，另一个进消融/效率节）
8. 论文定位改写（`paper/DS-SOD-Hybrid_论文初稿.md`）：
   - §4.2 主表：加"类型/训练成本"列、DS-SOD 系列行前移、SOTA 行标注全监督
   - 新增"范式上限诊断"表：MLLM 框 0.865→GT 框 0.933→GeleNet 0.947（ORSSD），
     分解 = 提示质量 ～6.8pt + 范式天花板 ～1.4pt
   - 摘要/结论：加"本文目标不是超越全监督 SOTA，而是刻画 MLLM+基础模型的能力边界与效率前沿"
   - §3.4 效率：补 large 实测（训练时长、参数、推理速度）
9. `make_figures.py` fig5：加入 large 系列柱（三集平均 Sα），GeleNet 均值 0.924 修正
10. `paper/DS-SOD_数据溯源与真实性声明.md`：补 R4 实验记录
11. 重跑 `make_paper_pdf.py` 生成 PDF

## 五、关键既有数字（供改写引用）

- GT 框上界（base+ 校准器）：Sα 0.933 / 0.926 / 0.862
- 三集平均 Sα：Zero 0.666 / Hybrid 0.762 / Adapter(base+) 0.839 / GeleNet 0.9236 / IPDiff 0.9308
- base+ 校准器训练 46 分钟；可训练参数 4.22M

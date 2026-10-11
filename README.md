# DS-SOD

本仓库保存 DS-SOD-Hybrid 论文整理阶段的可审阅产物。当前快照聚焦于：冻结 MLLM 提示的可靠性测量、PRISM 无任务训练提示修复，以及冻结 SAM2 下的遥感显著性检测实验。

## 主要文件

- `paper/DS-SOD-Hybrid_论文稿_2026-10-10.md`：当前可编辑论文稿。
- `output/pdf/DS-SOD-Hybrid_论文稿_2026-10-10.pdf`：排版并逐页检查后的 PDF。
- `paper/DS-SOD-Hybrid_论文_v0.9_定位与主表修订稿.md`：定位与主表修订版本。
- `paper/DS-SOD-Hybrid_v0.9_四项补充实验记录.md`：PRISM、几何提示和 Oracle 等补充实验记录。
- `paper/外部对比_事件*.md`：外部方法对比的协议、筛选、审计、整合和闭环记录。
- `paper/figures/`：论文使用的框架图与主结果图。
- `paper/DS-SOD-Hybrid_v0.9_实时实验进度.html`：实验阶段进度页。
- `tools/build_review_pdf.py`：从 Markdown 重新生成 PDF 的 Windows 构建脚本。

## 生成 PDF

在 Windows 安装依赖后运行：

```powershell
python -m pip install -r requirements-pdf.txt
python tools/build_review_pdf.py
```

脚本使用 Windows 自带的等线字体，生成文件写入 `output/pdf/`。

## 备份范围

本仓库只保存论文、实验记录、图表及排版工具。原始数据集、模型权重、运行缓存、临时渲染文件和本地密钥均不纳入仓库。

## 后续增量备份

双击 `sync.cmd`，或执行：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\init-backup.ps1 -ProjectDir . -Message "说明本次改动"
```

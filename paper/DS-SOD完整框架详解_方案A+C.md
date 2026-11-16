# DS-SOD 完整框架详解（方案 A+C）
> ⚠️ **v1 存档：本架构已废弃（CNN 生成显著图）。当前设计见《DS-SOD_v2_MLLM生成显著图_设计文档.md》——AI 生成提示词、DS 多模态大模型直接生成最终显著图。**

## 将 DeepSeek-V4-Flash-Exp 集成到 ORSI-SOD 的详细设计文档

> 方法名（建议）：**DS-SOD**（DeepSeek-guided Semantic & Dynamic optimization for ORSI-SOD）
> 本文档是《DeepSeek大模型集成ORSI-SOD创新方案报告.md》的展开版：给出架构、公式、训练流程、伪代码与工程细节。
> 阅读前提：已理解四篇论文的基本概念（编码器-解码器、注意力、Q/K/V、损失函数）。

---

## 第 0 章 总览：一张图看懂整个框架

```
                        ┌─────────────────────────────────────────────────┐
                        │           阶段0（离线，一次性）                    │
                        │  遥感图 I ──► DeepSeek-V4-Flash-Exp               │
                        │      │           │ 提示词模板（第2章）             │
                        │      │           ▼                               │
                        │      │      语义先验 JSON 库                     │
                        │      │      {类别, 外观, 难例, 粗方位}            │
                        │      │           │ 冻结文本编码器(CLIP)           │
                        │      │           ▼                               │
                        │      │      语义嵌入 E_sem（离线缓存）            │
                        └──────┼───────────────────────────────────────────┘
                               │
   ┌───────────────────────────▼───────────────────────────────┐
   │                阶段1：视觉主干 + 语义先验注入                │
   │                                                            │
   │   I ──► PVT-v2 ──► f1 f2 f3 f4 ──► D-SWSAM/SWSAM/KTM       │
   │                                        │                   │
   │                                        ▼                   │
   │                                  解码器 ◄── SPIM ◄── E_sem  │
   │                                        │                   │
   │                                        ▼                   │
   │                                    首版显著图 S⁰            │
   └───────────────────────────────┬────────────────────────────┘
                                   │
   ┌───────────────────────────────▼───────────────────────────────┐
   │              阶段2：LLM 验证-修正闭环（在线模式）                │
   │                                                                │
   │   原图 I + S⁰渲染图 ──► DeepSeek ──► 诊断 JSON {漏检? 误检?}    │
   │                                        │                        │
   │                                        ▼ 诊断嵌入 E_diag         │
   │   S⁰ + 解码器特征 ──► 修正模块 SEM-RM ──► 修正版显著图 S¹         │
   └───────────────────────────────────────────────────────────────┘
```

**三个部件的分工**（记住这句话就够了）：
1. **视觉主干**：负责"看"（像素级感知，继承 GeleNet）。
2. **语义先验分支**：负责"懂"（LLM 告诉你图里是什么、什么显著）。
3. **验证-修正闭环**：负责"改"（LLM 当裁判，指出第一版错在哪，网络去改）。

---

## 第 1 章 部件一：视觉主干（复用 GeleNet，快速回顾）

为了让文档自洽，这里把 GeleNet 的结构浓缩成一页：

- **骨干 PVT-v2-b2**（输入 3×352×352），输出 4 层特征：

| 层 | 符号 | 通道 | 分辨率 | 含义 |
|----|------|------|--------|------|
| 第1层（浅） | f1 | 64 | 88×88 | 细节、边缘、朝向 |
| 第2层 | f2 | 128 | 44×44 | 中尺度纹理 |
| 第3层 | f3 | 320 | 22×22 | 中尺度语义 |
| 第4层（深） | f4 | 512 | 11×11 | 定位、全局语义 |

- **三个模块**：f1→D-SWSAM（方向感知细节增强）、f2+f3→KTM（跨层上下文）、f4→SWSAM（定位）。
- **Partial Decoder 变体**融合三路输出 → 初始显著图 S⁰（352×352）。
- **损失**：L = L_BCE + L_IoU（训练阶段1时沿用即可）。

**为什么直接复用 GeleNet 而不自己设计主干？**
1. 代码开源（github.com/MathLee/GeleNet）、单卡 12GB 可训练、复现成本低；
2. 论文叙事上更聚焦：**主干不是你的创新，LLM 语义与闭环才是**——审稿人不会因为主干"旧"而拒你，反而让对比更公平；
3. 后续消融可以把主干换成 IPDiff 的去噪网络或 SAM2-RS 做扩展实验（"我们的语义先验/闭环是主干无关的即插即用模块"——这是一个非常有价值的额外论证）。

---

## 第 2 章 部件二：语义先验分支（方案 A 全展开）

### 2.1 阶段0：离线构建"语义先验库"

#### 为什么离线做？
- 训练集只有 ～2,000～4,000 张图，每张图调一次 API，**全程约 2～3 美元**（详见上一份报告的成本算账）；
- 结果缓存为 JSON 文件随代码开源 → 别人无需 API 也能复现（回应审稿人"不可复现"的质疑）；
- 训练时不需要反复调用 API，速度快且结果确定。

#### 提示词模板（v1：先验生成）

```
你是一名光学遥感图像显著性分析专家。请观察这张遥感图像，
判断其中最吸引人类注意力的显著目标，并严格按以下 JSON 格式输出
（不要输出任何 JSON 以外的文字）：
{
  "salient_categories": ["ship"],          // 显著目标类别，按显著程度降序，1～3个
  "appearance": "一艘白色货轮位于画面中部偏左，与深色海面形成强对比",
  "challenges": ["海面反光干扰", "疑似存在小型目标"],   // 本图检测难点，0～3个
  "coarse_hint": "显著目标集中在画面中部偏左区域"        // 只描述大致方位，禁止给出像素坐标
}
```

**提示词设计的三个原则（写进论文就是方法贡献）**：
1. **不让 LLM 输出像素坐标**——LLM 的空间定位能力弱，坐标会"幻觉"；像素级精度交给视觉网络。让 LLM 只做它擅长的"语义 + 大致方位"。
2. **固定 JSON 模式**（API 的 JSON Output 功能 + `temperature=0`）——保证输出可解析、可复现。
3. **同时要"类别 + 外观 + 难例"**——这三者分别对应三种注入信息：类别→物体级语义、外观→外观描述、难例→场景先验（后面 SPIM 会分别利用）。

#### 调用方式（DeepSeek API 关键事实）

- 模型名：`deepseek-v4-flash-vision-exp`（实验版发布名，现由 DeepSeek-V4.1-Flash 服务，等价名 `deepseek-flash`；论文中建议写"DeepSeek-V4-Flash（vision）系列"并在脚注说明版本）；
- 接口：OpenAI 兼容的 Chat Completions，`base_url=https://api.deepseek.com`；
- 图片输入：base64 `data:image/jpeg;base64,...` 或公开 URL 或 Files API；图片只能在 user 消息里；
- 省钱技巧：`detail:"low"` 会把图缩到 512×512 再推理（遥感场景的"类别+大致方位"判断用 512×512 足够，还能让每张图 token 更少）；
- 输出限制：开启 JSON Output 模式；`max_tokens≈800` 足够。

#### 伪代码（批量构建先验库）

```python
# 阶段0：为全部训练/测试图像生成语义先验库（只跑一次）
import base64, json, time
from openai import OpenAI

client = OpenAI(api_key="<YOUR_KEY>", base_url="https://api.deepseek.com")
PROMPT = "...（上面的模板）..."

def one_image(path):
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    for attempt in range(3):                    # 重试机制
        try:
            r = client.chat.completions.create(
                model="deepseek-v4-flash-vision-exp",   # 或 deepseek-flash
                response_format={"type": "json_object"},
                temperature=0,
                max_tokens=800,
                messages=[{"role": "user", "content": [
                    {"type": "text", "text": PROMPT},
                    {"type": "image_url",
                     "image_url": {"url": f"data:image/jpeg;base64,{b64}",
                                   "detail": "low"}},
                ]}],
            )
            return json.loads(r.choices[0].message.content)
        except Exception as e:
            print("retry", attempt, e); time.sleep(2 * (attempt + 1))
    return None                                   # 失败的图进人工检查列表

# 顺序跑 7000 张图；失败重试；结果存 prior_bank.json
```

### 2.2 把 JSON 变成向量：文本编码

**问题**：DeepSeek 输出的是文本，网络要的是向量。谁来把文本变成向量？

**答案**：用一个**冻结的文本编码器**（推荐 CLIP ViT-B/32 的 text encoder，约 63M 参数，开源免费）。

- 为什么用 CLIP 而不是再调 DeepSeek：DeepSeek API 不开放 embedding 接口；且 CLIP 文本空间与视觉骨干同源，适合做跨模态对齐；
- 为什么冻结：你的数据量小，微调文本编码器容易过拟合，而且"冻结"让实验更干净（消融时变量少）；
- 中文怎么办：让 LLM 输出**英文类别词**（模板里要求英文类别），CLIP 英文效果好；若想保留中文描述，可用开源多语言编码器 BGE-m3。**建议：类别字段强制英文，appearance/challenges 允许中文 + BGE-m3，消融里对比两种编码器**（这又是一个消融点）。

**三种字段分别编码（关键设计）**：

```
类别文本：  "A remote sensing photo of a ship."  ← 用 CLIP 的 prompt 模板包装每个类别词
           → 每个类别一个嵌入 e_cat_k ∈ R^512，最多 3 个 → 平均池化 → e_cat ∈ R^512
描述文本：  appearance 句子 → CLIP 编码 → e_app ∈ R^512
难例文本：  challenges 列表拼成一句 → 编码 → e_chal ∈ R^512

E_sem = concat(e_cat, e_app, e_chal) ∈ R^1536     （最后可过一个 MLP 压回 512）
```

> 为什么分开编码？因为消融时能单独拆掉某一种（"只用类别"、"只用外观"），证明每种信息都有用——审稿人最爱看这种逐项拆解。

### 2.3 SPIM：语义先验注入模块（核心新模块）

**动机**：E_sem 是"全图级"的一个向量，但解码器需要的是"每个尺度"的语义线索。SPIM 的任务就是：**把一个全局语义向量，正确地播撒到解码器的多层特征里**。

**结构（三个步骤，公式 + 大白话）**：

```
第1步：语义向量按尺度投影
  e^i_sem = MLP_i(E_sem)   ∈ R^C,   i = 1,2,3,4
  （大白话：一个 MLP 把语义向量“翻译”成适合第 i 层特征的语言）

第2步：交叉注意力注入
  Q_i = W^q_i · f_i        （Query 来自视觉特征，问："我该关注什么？"）
  K_i = W^k_i · e^i_sem    （Key/Value 来自语义，答："船、强对比、反光……"）
  V_i = W^v_i · e^i_sem
  A_i = softmax( Q_i · K_i^T / √d )
  f'_i = f_i + A_i · V_i   （残差连接：原始视觉信息不丢失）

第3步：可选的空间先验
  用 coarse_hint 的嵌入过一个 1×1 卷积 + sigmoid，得到"粗方位注意力图" M_hint ∈ [0,1]^{h×w}
  f'_i = f'_i + λ · M_hint ⊙ f'_i   （在大致方位上略微加强响应）
```

**注入位置**：4 层特征都注入（每层一个轻量 MLP + 交叉注意力），因为"类别"（深层语义）与"外观细节"（浅层）各有用处。若算力紧张，只注入解码器最深两层也可，但默认做 4 层。

**参数量**：每个 MLP_i 约几万参数，整个 SPIM **总共不到 2M 参数**——几乎不影响推理速度，这也是"离线模式推理速度 ≈ GeleNet"的原因。

> 写论文时的模块命名建议：**SPIM（Semantic Prior Injection Module）**，公式和图按上面写即可。

---

## 第 3 章 部件三：LLM 验证-修正闭环（方案 C 全展开）

### 3.1 为什么需要这一环？与 IPDiff 的关系

- IPDiff 的"动态优化"是**盲迭代**：去噪网络一步步优化，但每一步都只有"图像+噪声"信息，没有人告诉它"你错在哪"。
- 你的闭环是**语义引导迭代**：让一个看得懂图的 LLM 当裁判，指出"左下方漏了一艘小船 / 右上角把屋顶误判成目标"，网络拿着诊断去定向修正。
- 一句话论文卖点：**把 IPDiff 的"盲迭代"升级为"语义引导的迭代优化"**。

### 3.2 第一轮：生成诊断

**输入**：原图 I + 首版显著图 S⁰ 的**渲染图**（把 S⁰ 做成半透明红色叠加在原图上，像热力图一样，LLM 一眼就能看出哪里标对、哪里标错）。

**诊断提示词模板（v2）**：

```
这是一张光学遥感图像及其当前显著性检测结果（红色半透明区域=模型认为显著的区域）。
请指出检测结果中的错误，严格按 JSON 输出：
{
  "missed": ["左下方疑似有一艘小型船只未被标出"],      // 漏检描述，0～2条
  "false_positive": ["右上角屋顶区域被误标为显著目标"],  // 误检描述，0～2条
  "boundary_issue": ["目标边界不够精确"]               // 边界问题，0～2条
}
```

**要点**：
- 让 LLM 用**自然语言描述错误位置**（"左下方"），不要像素坐标——描述本身就是可编码的语义信息；
- `temperature=0` + JSON Output，保证稳定；
- 同样只需一次 API 调用（成本 +～0.5 美元/千图量级）。

### 3.3 第二轮：SEM-RM 修正模块（核心新模块）

**输入**：首版显著图 S⁰、解码器某层特征 F、诊断文本编码 e_diag。
**输出**：修正版显著图 S¹。

**结构（故意设计得简单，因为简单 = 可训练 + 可解释）**：

```
第1步：诊断嵌入
  e_diag = TextEnc(missed + false_positive + boundary_issue)   （冻结文本编码器）

第2步：FiLM 调制（用诊断"拧"一下特征）
  γ, β = MLP(e_diag)          （γ：放大系数；β：偏移量，都是逐通道的）
  F' = γ ⊙ F + β              （"根据诊断，调整哪些特征通道该增强/抑制"）

第3步：两个方向明确的注意力图（修正的精髓）
  A_miss = σ( Conv1(F') )      ∈ [0,1]^{H×W}   // "这里该找回来"（补漏检）
  A_fp   = σ( Conv2(F') )      ∈ [0,1]^{H×W}   // "这里该压下去"（去误检）

第4步：像素级修正公式（清晰、可写进论文）
  S¹ = clamp( S⁰ + w1·A_miss − w2·A_fp , 0, 1 )
  （w1、w2 是可学习标量；clamp 保证输出仍是合法显著图）
```

> 大白话：裁判说"漏了左下角"→ e_diag 通过 FiLM 让 A_miss 在左下角变亮 → S⁰ 在左下角被"补"上；裁判说"右上角误检"→ A_fp 在右上角变亮 → S⁰ 在右上角被"擦"掉。**每一步都对应一句人类能看懂的诊断**——这是很强的可解释性卖点，也是和普通"加个 refine 模块"的本质区别。

**为什么能训练（不需要强化学习）**：诊断文本在训练集上**离线预生成**（用阶段1训练好的模型对训练集先跑一遍 S⁰ → 调 LLM 生成诊断 → 缓存）。于是 SEM-RM 的监督就绪了：

```
L_corr = L_BCE(S¹, GT) + L_IoU(S¹, GT) + L_BCE(A_miss, GT−S⁰的漏检区) + L_BCE(A_fp, S⁰−GT的误检区)
```

最后两项是"注意力图监督"：训练时我们知道 GT，就能精确算出哪些像素真漏检了、哪些真误检了，直接监督 A_miss/A_fp 学成"漏检图/误检图"。这样 SEM-RM 不需要 RL，纯监督即可训练。

**闭环轮数**：默认 1 轮（先验生成算离线，在线只多 1 次诊断调用）。论文里可加"第 2 轮验证"消融：把 S¹ 渲染后再问一次 LLM"是否还有错误"，多数情况下 1 轮即可收敛（这也是一个实验结果）。

### 3.4 双模式推理（回应"依赖 API"质疑的关键设计）

| 模式 | 流程 | 依赖 | 速度/精度 |
|------|------|------|----------|
| **离线模式** | 主干 + SPIM（读缓存先验库）→ S⁰ | 完全无 API | 速度 ≈ GeleNet，精度已高于基线 |
| **在线模式** | 离线模式 + LLM 诊断 + SEM-RM → S¹ | 推理时调 1 次 API | 略慢（+1～2 秒/图），精度最高 |

论文中报告两种模式的精度与成本曲线（X 轴：每图 API 调用次数 0/1；Y 轴：Sα）——"按需付费的精度"本身就是一个有吸引力的卖点。

---

## 第 4 章 完整训练流程（三阶段，每阶段都简单）

```
阶段1：主干 + SPIM
  - 训练数据：ORSSD+EORSSD 训练集（或 +ORSI-4199），语义先验库已离线就绪
  - 可训练：GeleNet 全部参数 + SPIM；冻结：文本编码器
  - 损失：L = L_BCE(S⁰,GT) + L_IoU(S⁰,GT)     （与 GeleNet 相同）
  - 输出：模型 M1

阶段2：诊断库生成（离线，不训练）
  - 用 M1 对训练集推理得 S⁰，渲染叠加图
  - 调 DeepSeek 生成诊断 JSON，缓存（与先验库同理，几美元）
  - 用 GT 计算 A_miss / A_fp 的监督标签

阶段3：SEM-RM 训练
  - 冻结 M1，只训练 SEM-RM（γ/β MLP + 两个卷积头 + w1/w2）
  - 损失：L_corr（见 3.3）
  - 输出：完整模型 M2

（可选阶段4：M1+SEM-RM 联合微调 5 个 epoch，小学习率，通常还能再涨一点）
```

---

## 第 5 章 关键模块的 PyTorch 骨架（可直接照着写）

```python
# ---------- SPIM ----------
class SPIM(nn.Module):
    def __init__(self, sem_dim=1536, c=32):
        super().__init__()
        self.proj  = nn.Linear(sem_dim, c)          # 语义向量 → 通道维度
        self.wq = nn.Linear(c, c); self.wk = nn.Linear(c, c); self.wv = nn.Linear(c, c)
        self.scale = c ** -0.5
    def forward(self, f, e_sem):                    # f: B×C×H×W, e_sem: B×sem_dim
        e = self.proj(e_sem)                        # B×C
        B, C, H, W = f.shape
        q = self.wq(f.flatten(2).permute(0,2,1))    # B×(HW)×C   （视觉当 Query）
        k = self.wk(e).unsqueeze(1)                 # B×1×C      （语义当 Key）
        v = self.wv(e).unsqueeze(1)                 # B×1×C      （语义当 Value）
        a = torch.softmax(q @ k.transpose(1,2) * self.scale, dim=-1)  # B×(HW)×1
        g = (a * v).permute(0,2,1).view(B, C, H, W) # 语义增益图
        return f + g                                # 残差注入

# ---------- SEM-RM ----------
class SEM_RM(nn.Module):
    def __init__(self, c=32, sem_dim=1536):
        super().__init__()
        self.gamma = nn.Linear(sem_dim, c); self.beta = nn.Linear(sem_dim, c)
        self.head_miss = nn.Sequential(nn.Conv2d(c, c, 3, padding=1), nn.ReLU(),
                                       nn.Conv2d(c, 1, 1))
        self.head_fp   = nn.Sequential(nn.Conv2d(c, c, 3, padding=1), nn.ReLU(),
                                       nn.Conv2d(c, 1, 1))
        self.w1 = nn.Parameter(torch.tensor(0.5)); self.w2 = nn.Parameter(torch.tensor(0.5))
    def forward(self, S0, F, e_diag):               # S0: B×1×H×W（已上采样对齐）
        gamma = self.gamma(e_diag).unsqueeze(-1).unsqueeze(-1)
        beta  = self.beta (e_diag).unsqueeze(-1).unsqueeze(-1)
        Fp = gamma * F + beta                       # FiLM 调制
        A_miss = torch.sigmoid(self.head_miss(Fp))
        A_fp   = torch.sigmoid(self.head_fp(Fp))
        S1 = (S0 + self.w1 * A_miss - self.w2 * A_fp).clamp(0, 1)
        return S1, A_miss, A_fp                     # 注意力图也返回，供损失监督
```

> 注：上面的交叉注意力把"语义向量"当成全局 Key/Value——语义先验本来就是全图级的，所以 K/V 只有一个 token（B×1×C），计算量极小。这个"全局语义 token"设计也可以换成学到的 4 个语义 token（分别对应类别/外观/难例/方位），是消融里的一个变体。

---

## 第 6 章 消融实验设计（决定论文能否中）

**消融主线（务必逐行做完）**：

| # | 变体 | 目的 |
|---|------|------|
| 1 | GeleNet 基线（无 SPIM） | 基准 |
| 2 | +SPIM（只用 CLIP 类别词，无 LLM） | 证明"静态文本"不如"LLM 语义" |
| 3 | +SPIM（LLM 类别 only） | 拆出类别信息贡献 |
| 4 | +SPIM（类别+外观） | 拆出外观贡献 |
| 5 | +SPIM（全部字段，即完整方案） | 完整方案 A |
| 6 | 完整方案 A + SEM-RM（离线诊断） | 完整方案 A+C |
| 7 | 变体 6 + 在线 LLM 诊断 | 证明在线推理更强的上限 |
| 8 | IPDiff 式盲迭代修正（把 e_diag 换成噪声/去掉诊断） | **证明"语义引导迭代 > 盲迭代"** |

**场景分组评测（强烈建议，是区分度所在）**：用 LLM 输出的 challenges 字段把测试集分成 {低对比、阴影、多目标、极大型、同谱异物} 子集，分别报告指标——预期增益集中在纯视觉失败的高难子集上，这就是"LLM 语义真的有用"的最直接证据。

**效率报告**：API 总花费、每图 tokens、推理延迟、参数量（SPIM + SEM-RM < 3M）、离线/在线模式 FPS 对比。

---

## 第 7 章 工程细节与"坑"（新手必读）

1. **JSON 解析失败**：约 1～3% 的调用会返回不合规 JSON。对策：重试 3 次 → 仍失败则用"空先验"（该图 SPIM 输入改为可学习默认向量，模型照常工作）。报告解析成功率（>97% 是正常水平）。
2. **API 限流**：并发 2500 足够；批量脚本加 0.2s 间隔 + 断点续跑（按文件名记录已完成清单），跑挂了接着跑。
3. **确定性**：`temperature=0`；同一批图全部存盘，保证任何人复现拿到同一先验库。
4. **图片大小**：原图 352×352 训练，但给 LLM 的图可以用原始分辨率（它内部会缩到 ～1300×1300）；`detail:"low"`（512×512）先做 20 张试点对比质量再决定。
5. **类别词规范**：让 LLM 从固定词典 {ship, airplane, vehicle, building, river, island, playground, road, bridge, ...} 里选（模板里给出词典），避免类别词五花八门导致文本编码不稳。
6. **渲染图设计**：S⁰ 半透明红叠加原图，并在提示词里说明"红色=模型认为显著"；测试不同透明度（0.3～0.5）选最好。
7. **公平性声明**：论文里明确写"LLM 只接收图像，不接收 GT；先验库随代码开源；离线模式完全不依赖 API"——提前堵住审稿人。
8. **显存**：GeleNet（PVT-v2-b2）单卡 12GB 可训练；SPIM/SEM-RM 增量极小，不会爆显存。

---

## 第 8 章 论文叙事模板（把技术变成故事）

- **引言第 2 段**：四篇论文的进化主线（CNN→Transformer→大模型→扩散）→ 共同盲区：闭世界、纯视觉、无推理。
- **引言第 3 段**：人类显著性 = 语义行为；给出 2 张图例：低对比（白车/斑马线）、同谱异物（船/海面）——纯视觉失败、语义一眼可解。
- **方法**：三部件（感知 / 语义 / 修正）+ "LLM 只给语义、网络定像素"的分工原则 + 双模式推理。
- **实验**：三数据集 SOTA 对比 + 第 6 章消融 + 场景分组 + 成本曲线。
- **结论**：LLM 语义先验是"主干无关的即插即用组件"，可为任何 ORSI-SOD 网络赋能。

---

*文档完。需要的话，下一步我可以：① 把第 5 章骨架补全成可直接接入 GeleNet 仓库的完整代码文件；② 写阶段0 批量脚本的完整可运行版本（含断点续跑与 JSON 校验）；③ 起草论文 Abstract 与 Introduction。*

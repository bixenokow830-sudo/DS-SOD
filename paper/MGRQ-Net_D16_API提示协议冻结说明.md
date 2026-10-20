# MGRQ-Net D16：API提示协议冻结说明

## 1. 冻结结论

MGRQ-Net 的 DeepSeek 提示生成协议已冻结。

| 字段 | 冻结值 |
|---|---|
| 协议ID | `mgrq_api_protocol_v1_2026-10-20` |
| 状态 | `FROZEN` |
| 冻结时间 | 2026-10-20 10:18，Asia/Shanghai |
| D16 API调用 | 0 |
| D16 API费用 | 0 |
| 提示模板版本 | `mgrq_prompt_v1_2026-10-19` |
| 输出协议 | `mgrq_semantic_queries_v1` |
| 请求模型别名 | `deepseek-flash` |
| API地址 | `https://api.deepseek.com` |

D16 只读取现有代码、清单和缓存完成冻结，没有读取密钥、没有发送图像，也没有调用 DeepSeek API。

## 2. 冻结依据

| 证据 | 结果 |
|---|---:|
| D14严格清单 | 3328 |
| 原始响应 | 3328/3328 |
| 唯一请求签名 | 3328/3328 |
| 有效解析缓存 | 3322/3328 |
| 有效覆盖率 | 99.82% |
| 请求模型一致性 | `deepseek-flash`，3328/3328 |
| 服务返回模型一致性 | `deepseek-flash`，3328/3328 |
| 解析协议一致性 | `mgrq_semantic_queries_v1`，3322/3322 |
| API响应生成区间 | 2026-10-19 17:33:54–20:15:26 |

所有原始响应的记录ID、图像SHA256、请求签名、模板版本和模板哈希均与D14严格清单一致，没有发现协议混用。

## 3. 请求协议

### 3.1 模型与推理参数

- 提供方：DeepSeek
- 请求模型别名：`deepseek-flash`
- 接口：OpenAI兼容 `chat.completions.create`
- 图像策略：每张图一次整图请求，不裁剪、不使用2×2切片
- 图像传输：按原始MIME类型编码为Base64 data URL
- 图像细节：`high`
- `temperature=0.0`
- `max_tokens=3000`
- 思考模式：`disabled`
- 响应格式：`{"type":"json_object"}`

### 3.2 提示模板

- 模板版本：`mgrq_prompt_v1_2026-10-19`
- 模板SHA256：`a0be7cc399f4bd619ff1abbc737e582762e9079383ff36f7bc0ea617bd95809d`
- 完整system prompt与user prompt保存在冻结JSON中，不在论文描述中依靠人工转录。

任何提示文本改动，即使只修改一个字符，也必须产生新模板版本、新协议ID和独立缓存目录。

## 4. 响应JSON协议

顶层必须且只能包含：

```json
{
  "salient_objects": [],
  "distractors": [],
  "empty_scene_probability": 0.0
}
```

### 4.1 `salient_objects`

- 数量：0–8；
- 必需且仅允许字段：`phrase`、`bbox`、`saliency_confidence`、`reason`；
- `phrase`：非空字符串，空白归一化后不超过160字符；
- `reason`：非空字符串，空白归一化后不超过320字符；
- `saliency_confidence`：数值，范围 `[0,1]`；
- `bbox`：整数 `[x1,y1,x2,y2]`，范围 `[0,1000]`，必须满足 `x1<x2`、`y1<y2`。

### 4.2 `distractors`

- 数量：0–5；
- 必需字段：`phrase`、`bbox`、`reason`；
- 可选字段：`saliency_confidence`；
- 坐标、文本和置信度约束与显著候选一致。

### 4.3 `empty_scene_probability`

必须为 `[0,1]` 范围内的数值。

## 5. 校验器冻结规则

| 行为 | 冻结规则 |
|---|---|
| Markdown JSON代码围栏 | 允许移除 |
| 响应前后附加文本 | 允许提取最外层JSON对象后重试解析 |
| 未知顶层字段 | 拒绝 |
| 未知对象字段 | 拒绝；仅允许已冻结的干扰物可选置信度 |
| 逆序坐标 | 拒绝，不自动交换 |
| 越界坐标 | 拒绝，不自动裁剪 |
| 非数值或非四元框 | 拒绝 |
| 损坏JSON | 拒绝，不猜测修复 |
| 字段别名，如`short_reason` | 拒绝，不自动映射 |

冻结校验器实现：`ds_sod/scripts/generate_mgrq_prompts.py`

实现SHA256：`8c7fbd610f94c248321098e496ef9c00c0f4459bc4c5aeee24c39e40d1cc2362`

D14中6份未解析响应继续保留为明确失败，不在D16中修改规则或重新调用API。

## 6. 缓存与请求签名

原始响应和解析结果必须分开保存。原始响应视为不可变实验产物。

请求签名包含：

- 记录ID；
- 图像SHA256；
- 模型别名；
- 输出协议版本；
- 提示模板版本及SHA256；
- 思考模式；
- 图像detail；
- 干跑场景字段。

只有解析状态、请求签名、干跑标记、模板版本和模板哈希全部一致时，断点续跑才允许跳过该图像。

## 7. 下游查询接纳规则

下游规则冻结为 `mgrq_query_admission_v1`：

| 类型 | 规则 | 用法 |
|---|---|---|
| 可信正查询 | `confidence ≥ 0.8` | 进入正查询池，仍由可靠性头学习权重 |
| 不确定查询 | `0.6 ≤ confidence < 0.8` | 保留语义和位置，由匹配器接纳或拒绝 |
| 低置信候选 | `confidence < 0.6` | 退出正查询池，可作困难负样本或忽略区 |
| 干扰框 | 全部 | 只作软负先验，不生成无条件硬背景 |
| 发现查询 | 全部图像 | 始终启用，不因存在高置信提示而关闭 |

该规则是API缓存的消费者配置，而不是请求签名的一部分。后续可以独立做阈值或网络结构消融，但必须升级下游配置版本，不能把变化错误描述为新的DeepSeek提示。

## 8. 版本升级规则

以下任一变化都必须创建新API协议版本和独立缓存，禁止与当前缓存混合：

- system prompt或user prompt；
- API提供方、地址或模型别名；
- 思考模式、temperature、max_tokens或响应格式；
- 图像detail、预处理、裁剪或切片策略；
- JSON字段、坐标约定或校验器接受规则；
- 请求签名中的任何字段。

以下变化不使API缓存失效，但必须版本化下游训练配置：

- 查询置信度阈值；
- 匹配器和可靠性头结构；
- 损失权重；
- 训练计划。

## 9. 可复现性边界

`deepseek-flash` 是服务端模型别名，不是可下载的不可变权重。即使请求参数完全相同，提供方未来更新别名所指向的模型后，重新调用也不保证逐字一致。

因此本论文实验的权威输入是D14保存的3328份原始响应与其请求签名，而不是未来重新请求得到的结果。后续切换本地MLLM时，必须使用新的提供方/模型标识、协议ID和独立提示缓存，不得伪装成当前DeepSeek缓存的等价替换。

## 10. 完整性哈希

| 产物 | SHA256 |
|---|---|
| D14严格清单 | `d280f800a3be2e4b2539c7e6cf46e62ead19b932a9693f02b268609dcafec191` |
| D14最终摘要 | `8261ce319993b6dd4fe9419ed9fe242a41233f15f9f8c382335508841d585e53` |
| D15质量JSON | `0fb37a598937005d8db1c3aa6e77f817aca29ae230bcfe44ac74f51dd60577a5` |
| 冻结校验器 | `8c7fbd610f94c248321098e496ef9c00c0f4459bc4c5aeee24c39e40d1cc2362` |

## 11. 产物

- `ds_sod/banks/mgrq/protocols/mgrq_api_protocol_v1_2026-10-20.json`
- `ds_sod/scripts/freeze_mgrq_d16_protocol.py`
- `paper/MGRQ-Net_D16_API提示协议冻结说明.md`

## 12. 建议下一命令

```text
执行 I20
```


# MGRQ-Net D10：提示生成器实现与离线验收报告

## 1. 结论

D10已通过。在不修改旧`pilot_mllm.py`、旧`llm.py`或既有提示库的条件下，新增MGRQ专用提示生成器`generate_mgrq_prompts.py`。生成器固定请求模型为`deepseek-flash`，每张图只生成一次结构化语义查询，不让API直接生成显著图或像素掩码。

离线假响应已经通过“清单选择→图像哈希校验→结构化响应→JSON提取→字段与坐标校验→原始响应落盘→解析结果落盘→缓存签名→断点续跑”的完整链路。API调用次数为0，没有产生费用。

## 2. 输出协议

每张图的解析结果采用`mgrq_semantic_queries_v1`：

```json
{
  "salient_objects": [
    {
      "phrase": "isolated bright vessel in dark water",
      "bbox": [118, 214, 472, 681],
      "saliency_confidence": 0.93,
      "reason": "The compact bright structure is isolated and strongly contrasts with the surrounding water."
    }
  ],
  "distractors": [
    {
      "phrase": "bright wave pattern",
      "bbox": [732, 82, 945, 246],
      "reason": "It is locally bright but lacks a coherent object boundary."
    }
  ],
  "empty_scene_probability": 0.03
}
```

约束如下：

- `salient_objects`最多8个，按显著程度降序；
- `distractors`最多5个，用作后续负查询或可靠性监督；
- 所有框均为整数`[x1,y1,x2,y2]`，归一化到`[0,1000]`；
- 强制`x1<x2`、`y1<y2`，置信度和空场景概率必须位于`[0,1]`；
- 禁止额外字段、掩码、多边形和最终显著图；
- 提示模板版本为`mgrq_prompt_v1_2026-10-19`，SHA256为`a0be7cc399f4bd619ff1abbc737e582762e9079383ff36f7bc0ea617bd95809d`。

## 3. API与安全设计

- 请求模型固定为`deepseek-flash`；
- 使用OpenAI兼容Chat Completions图像输入；
- 使用`response_format={"type":"json_object"}`；
- 通过`extra_body={"thinking":{"type":"disabled"}}`关闭思考模式；
- 每张图单次调用，真实模式最多重试3次并线性退避；
- 密钥只从环境变量`DEEPSEEK_API_KEY`读取，不读取或打印`secrets.env`；
- `--dry-run`分支不会创建API客户端，也不会读取密钥；
- 原始回复与解析JSON分目录保存；
- 同时保存请求模型、服务返回模型、调用日期、图像哈希、清单哈希、提示词版本与哈希、token使用量和结束原因。

官方接口核对结果：`deepseek-flash`支持图像输入；旧`deepseek-v4-flash-vision-exp`已成为兼容别名；JSON输出和显式关闭思考模式均为当前官方接口能力。

## 4. 缓存与断点续跑

缓存签名联合以下字段生成：

1. 清单记录ID；
2. 实际图像SHA256；
3. 请求模型；
4. 输出协议版本；
5. 提示模板版本与SHA256；
6. 图像细节等级和思考模式。

只有原始回复和解析结果同时存在，且缓存签名、图像哈希、模板版本和干跑/真实模式完全一致时，记录才会被跳过。图像内容或提示模板变化后不会误用旧缓存。

真实缓存默认写入：

```text
ds_sod/banks/mgrq/prompts_raw/{split}/
ds_sod/banks/mgrq/prompts_parsed/{split}/
```

干跑缓存默认写入`ds_sod/runs/mgrq/dry_run_prompts/`，避免混入正式提示库。

## 5. 离线验收

### 5.1 单元检查

4项检查全部通过：

- 合法假响应完整解析；
- Markdown JSON代码块兼容解析；
- `x1>=x2`非法坐标被拒绝；
- 未声明的额外字段被拒绝。

### 5.2 完整落盘检查

使用严格dev清单的稳定首条记录`EORSSD/train/0070`执行离线验收：

- 清单图像SHA256与磁盘文件一致；
- 原始响应文件1份；
- 解析结果文件1份；
- 状态为`parsed_ok`；
- 再次运行状态为`skipped_current_cache`；
- 失败数0；
- API调用0；
- 输出中未发现密钥内容。

验收目录：`ds_sod/runs/mgrq/d10_acceptance_v1/`。

## 6. 主要产物

- 生成器：`ds_sod/scripts/generate_mgrq_prompts.py`
- 生成器SHA256：`1d9470efbadaf3f718b4d3455661d9759e99b14ddb3e95dba262e6fbbb9fe5ca`
- 离线单元检查：`ds_sod/tests/test_generate_mgrq_prompts.py`
- 测试文件SHA256：`e9c85e88a33969002790eb75adb49d91e69a2272854903f10b077c203ff95c87`
- D10验收汇总：`ds_sod/runs/mgrq/d10_acceptance_v1/run_summary.json`
- 原始假响应：`ds_sod/runs/mgrq/d10_acceptance_v1/prompts_raw/dev/`
- 解析结果：`ds_sod/runs/mgrq/d10_acceptance_v1/prompts_parsed/dev/`

## 7. 下一步

执行D11：使用严格dev清单的5张图进行完整干跑，进一步验证多记录落盘、重复运行跳过、异常记录与目录级统计。D11仍不调用API、不产生费用。

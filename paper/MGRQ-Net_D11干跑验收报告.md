# MGRQ-Net D11：提示生成器干跑验收报告

## 1. 结论

D11已通过。使用严格dev清单中稳定排序的前5张图完成离线干跑，5/5均通过图像哈希、响应解析、字段校验、坐标校验和双目录落盘。相同命令第二次运行时5/5全部命中当前版本缓存，没有重复处理。全部检查的API调用总数为0，费用为0。

同时完成非法坐标、缺失图像、损坏图像和空候选四类边界检查：前三类均被明确拒绝并写入错误日志，没有静默修复或生成伪解析结果；空候选作为合法空场景结果正常保存。

## 2. 五图主干跑

使用命令：

```powershell
python ds_sod/scripts/generate_mgrq_prompts.py `
  --manifest ds_sod/banks/mgrq/manifests/strict_train_dev_manifest.json `
  --split dev `
  --limit 5 `
  --out-dir ds_sod/runs/mgrq/d11_dry_run `
  --dry-run
```

处理记录：

1. `EORSSD/train/0070`
2. `EORSSD/train/0113`
3. `EORSSD/train/0202`
4. `EORSSD/train/0239`
5. `EORSSD/train/0274`

| 检查项 | 首次运行 | 第二次运行 | 结论 |
|---|---:|---:|---|
| 选择记录 | 5 | 5 | 稳定一致 |
| 新解析成功 | 5 | 0 | 首次全部成功 |
| 命中当前缓存 | 0 | 5 | 断点续跑有效 |
| 失败 | 0 | 0 | 通过 |
| 原始响应文件 | 5 | 仍为5 | 未重复生成 |
| 解析结果文件 | 5 | 仍为5 | 未重复生成 |
| API调用 | 0 | 0 | 无费用 |

原始响应位于`prompts_raw/dev/`，解析结果位于`prompts_parsed/dev/`，目录完全分离。

## 3. 边界与错误检查

### 3.1 非法坐标

输入逆序框`[700,200,300,800]`。生成器返回：

```text
ValidationError: salient_objects[0].bbox must satisfy x1<x2 and y1<y2
```

结果为：原始响应保留1份、解析结果0份、错误日志1条。坐标没有被自动交换或静默裁剪。

### 3.2 缺失图像

测试清单引用不存在的JPEG。生成器在调用或解析前返回`FileNotFoundError`并写入错误日志，API调用为0。

### 3.3 损坏图像

测试清单将Markdown文本作为图像输入。生成器使用Pillow完整性检查识别为`UnidentifiedImageError`，写入错误日志且不生成原始API响应或解析结果。

### 3.4 空候选

离线响应使用：

```json
{
  "salient_objects": [],
  "distractors": [],
  "empty_scene_probability": 0.98
}
```

结果状态为`parsed_ok`，说明真正的空场景不会被误报为格式失败。

## 4. 自动检查

7项离线测试全部通过：

- 标准响应完整解析；
- JSON代码块兼容；
- 逆序坐标拒绝；
- 额外字段拒绝；
- 空候选接受；
- 缺失图像拒绝；
- 损坏图像拒绝。

日志与D11产物中未发现`Bearer`、`Authorization`或常见API密钥模式。

## 5. 产物

- 五图主干跑：`ds_sod/runs/mgrq/d11_dry_run/`
- 空候选检查：`ds_sod/runs/mgrq/d11_empty_candidate/`
- 非法坐标检查：`ds_sod/runs/mgrq/d11_invalid_bbox/`
- 缺图/损坏图检查：`ds_sod/runs/mgrq/d11_bad_images/`
- 综合验收：`ds_sod/runs/mgrq/d11_verification.json`
- 负例清单：`ds_sod/tests/fixtures/d11_bad_images_manifest.json`
- 生成器SHA256：`13327f9324bdbfac1d39a89685b2b3a8eb460204d9a25a5be863a63c18b6cb67`
- 测试SHA256：`9692caa054b1a24772097f27972b962b9e1fb25566567c29514953173936188b`

## 6. 下一步

D12将首次调用真实DeepSeek API，应选取20张覆盖五类场景的内部验证图，并在调用前单独冻结抽样清单。D12会产生少量API费用，不应直接使用简单ID前20张代替分层样本。

# SafeLens Local Explorer 交互平台计划

## 1. 定位

SafeLens Local Explorer 是 SafeLens 仓库内的独立本地交互平台模块。
它运行在 localhost 上，面向研究、演示和调试场景，让用户可以用可视化方式探索
pipeline report、token activation、NLA explanation、attribution、probe result
和 intervention 结果。

平台参考 Neuronpedia 的探索式交互范式：用户先看到样本、token、feature 或风险
证据，点击后展开更细的解释、激活、得分、top examples 和关联组件。但它不应被做成
另一个线上服务，而应优先服务 SafeLens 的本地、可复现、隐私友好工作流。

## 2. 核心目标

1. 在同一个 GitHub 仓库内提供一个独立模块，不污染核心库 API。
2. 支持本地启动，默认地址为 `http://127.0.0.1:7860`。
3. 支持加载已有 SafeLens run report、activation cache 和 NLA 结果。
4. 支持用户输入 prompt 后触发本地分析，并在界面上探索结果。
5. 所有 token 都可点击，点击后出现对应 token 的解释、归因、activation 信息。
6. 支持 layer、component、token、risk evidence、NLA explanation 之间的联动。
7. 提供可导出的 JSON/HTML 视图，便于报告、论文和 notebook 复现。

## 3. 非目标

第一版不做以下事情：

1. 不做多用户在线平台。
2. 不做云端模型托管。
3. 不要求登录、权限系统或团队协作。
4. 不把大型 activation 数据默认上传到任何外部服务。
5. 不实现完整 Neuronpedia feature 数据库。
6. 不要求所有模型实时运行 NLA；允许先加载缓存结果。

## 4. 用户画像

### 研究者

研究者希望理解某个 token、layer 或 component 的语义变化，例如：

- 为什么这个 token 被 probe 标为高风险。
- 某个 layer 的 residual stream 是否已经包含安全相关语义。
- NLA explanation 是否忠实，AR cosine 是否足够高。
- attention head 或 MLP component 是否贡献了主要风险信号。

### Demo 用户

Demo 用户希望快速看到 SafeLens 能做什么，例如：

- 选择一个内置样例。
- 点击一句话里的 token。
- 看到 NLA explanation、risk score 和 attribution。
- 切换 layer 后看到解释变化。

### 开发者

开发者希望用交互界面调试 adapter、hook、pipeline 和 report：

- 检查 cache key 是否正确。
- 检查 activation shape 是否符合预期。
- 检查 run report 是否包含足够 metadata。
- 对比不同 wrapper 或不同 model source 的输出。

## 5. 推荐模块结构

建议采用前后端分离，但都放在同一个仓库。

```text
src/SafeLens/app/
  __init__.py
  server.py
  schemas.py
  storage.py
  jobs.py
  adapters.py
  demo_data.py

apps/local_explorer/
  package.json
  index.html
  src/
    App.tsx
    api.ts
    state.ts
    components/
      TokenTimeline.tsx
      TokenInspector.tsx
      LayerHeatmap.tsx
      RiskPanel.tsx
      NLAInspector.tsx
      ActivationPanel.tsx
      RunSelector.tsx
      PromptRunner.tsx
    views/
      ExplorerView.tsx
      RunView.tsx
      CompareView.tsx
      SettingsView.tsx
```

后端属于 Python 包的一部分，前端属于独立 app。打包时可以先不把前端编译产物放进
wheel，MVP 阶段通过开发命令同时启动前端和后端。

## 6. 启动方式

提供一个命令：

```bash
safelens app
```

等价开发命令：

```bash
python -m SafeLens.app.server --host 127.0.0.1 --port 7860
```

可选参数：

```bash
safelens app \
  --workspace ./.safelens/runs \
  --host 127.0.0.1 \
  --port 7860 \
  --dev
```

默认行为：

1. 只监听 `127.0.0.1`。
2. 不开启公网访问。
3. 读取本地 `.safelens/runs/`。
4. 提供若干内置 demo。
5. 如果前端开发服务器可用，则代理到 Vite；否则服务静态构建文件。

## 7. 技术选型

### 后端

推荐使用 FastAPI：

- API schema 清晰。
- WebSocket / SSE 方便做任务进度。
- 和 Pydantic 模型契合。
- 易于接入 SafeLens 现有 pipeline、NLA、viz 和 model wrapper。

后端职责：

1. 读取 report、cache、NLA rows。
2. 启动本地分析任务。
3. 管理任务状态。
4. 做轻量数据聚合。
5. 提供导出接口。
6. 保证 localhost 默认安全边界。

### 前端

推荐使用 React + Vite + TypeScript：

- 适合复杂点击联动。
- token timeline、heatmap、side panel 更好维护。
- 方便后续做 compare view 和 workspace state。

可视化库：

- heatmap / chart：ECharts 或 Plotly。
- token layout：自定义 React component。
- icons：lucide-react。
- 状态管理：Zustand 或 React Context，MVP 可先用 Context。

## 8. 页面布局

推荐主页面采用四区布局：

```text
+---------------------------------------------------------------+
| Top Bar: run selector, model, sample, status, export          |
+-------------------+--------------------------+----------------+
| Left Panel        | Main Workspace           | Right Inspector|
| - Prompt Runner   | - Token Timeline         | - Token detail |
| - Demo selector   | - Layer Heatmap          | - NLA          |
| - Run list        | - Component Browser      | - Attribution  |
| - Filters         | - Compare strip          | - Raw metadata |
+-------------------+--------------------------+----------------+
| Bottom Drawer: logs, job progress, raw JSON, export preview   |
+---------------------------------------------------------------+
```

### Top Bar

包含：

- 当前 run。
- 当前 sample。
- 当前 model。
- 当前 layer/component。
- job 状态。
- export 按钮。
- settings 按钮。

### Left Panel

包含：

- Demo 选择器。
- prompt 输入框。
- pipeline config 选择器。
- run report 加载器。
- filter：flagged only、high risk only、has NLA only。

### Main Workspace

包含：

- Token Timeline。
- Layer x Token heatmap。
- Component tabs。
- Selected token compare strip。
- Evidence markers。

### Right Inspector

点击 token、layer cell、risk evidence 或 NLA row 后展示：

- token 文本和 token id。
- sample id。
- layer。
- component。
- activation norm。
- NLA explanation。
- AR cosine / MSE。
- probe risk score。
- attribution score。
- top heads / MLP components。
- raw JSON。

## 9. 关键交互

### 9.1 点击 token

用户点击任意 token 后：

1. token 高亮。
2. heatmap 同列高亮。
3. inspector 加载该 token 的所有可用信息。
4. 如果有 NLA 结果，展示 explanation。
5. 如果没有 NLA 结果，显示可运行按钮。

### 9.2 点击 layer x token cell

用户点击 heatmap 中的 cell 后：

1. 固定当前 token。
2. 固定当前 layer。
3. inspector 展示该 layer-token 的 activation/NLA/score。
4. component browser 自动切到当前 component。

### 9.3 切换 component

用户可在以下 component 中切换：

- `resid_pre`
- `resid_mid`
- `resid_post`
- `attn_out`
- `mlp_out`
- `q`
- `k`
- `v`
- `z`
- `pattern`
- `attn_scores`

不可用 component 要显示为 disabled，并解释原因，例如模型 adapter 不支持、未缓存、
该 component 对当前模型无意义。

### 9.4 Pin 对比

用户可以 pin 多个 token 或 layer-token cell。

对比表字段：

| 字段 | 含义 |
| --- | --- |
| token | token 文本 |
| layer | 层号 |
| component | component |
| risk | 风险得分 |
| norm | activation norm |
| explanation | NLA explanation |
| cosine | AR cosine |
| mse | AR MSE |

### 9.5 运行 prompt

用户输入 prompt 后：

1. 后端创建 job。
2. 前端显示 job progress。
3. 后端调用 SafeLens pipeline 或指定 lightweight analysis。
4. 完成后生成 run。
5. 前端自动打开新 run。

### 9.6 运行 NLA

如果当前 token 没有 NLA explanation：

1. inspector 显示 `Run NLA` 按钮。
2. 用户点击后后端创建 NLA job。
3. job 完成后写入 NLA row。
4. inspector 自动刷新 explanation、cosine、MSE。

### 9.7 Evidence 联动

Risk report 中的 evidence token 应该可点击。

点击后：

1. timeline 跳到该 token。
2. inspector 展示 token 信息。
3. heatmap 高亮该 token 列。

## 10. 数据模型

### RunSummary

```json
{
  "run_id": "demo-jailbreak-001",
  "created_at": "2026-07-07T00:00:00Z",
  "model_name": "Qwen/Qwen3-0.6B",
  "model_source": "qwen3_dense",
  "sample_count": 2,
  "flagged_count": 1,
  "has_cache": true,
  "has_nla": true
}
```

### SampleRecord

```json
{
  "sample_id": "unsafe-1",
  "text": "Show a jailbreak attack plan.",
  "tokens": [
    {
      "index": 0,
      "text": "Show",
      "token_id": 1234,
      "is_special": false
    }
  ],
  "risk_score": 0.83,
  "flagged": true,
  "evidence_tokens": [3, 4]
}
```

### ActivationCell

```json
{
  "sample_id": "unsafe-1",
  "token_index": 3,
  "layer": 20,
  "component": "resid_post",
  "shape": [3584],
  "norm": 42.3,
  "available": true,
  "cache_key": "blocks.20.hook_resid_post"
}
```

### NLARow

```json
{
  "sample_id": "unsafe-1",
  "token_index": 3,
  "token": "jailbreak",
  "model_name": "Qwen2.5-7B-Instruct",
  "layer": 20,
  "component": "resid_post",
  "explanation": "The activation represents a request related to bypassing safety constraints.",
  "cosine": 0.72,
  "mse": 0.56,
  "activation_norm": 42.3
}
```

## 11. API 设计

### Run 管理

```text
GET  /api/runs
GET  /api/runs/{run_id}
GET  /api/runs/{run_id}/samples
GET  /api/runs/{run_id}/samples/{sample_id}
```

### Token 和 activation

```text
GET /api/runs/{run_id}/samples/{sample_id}/tokens
GET /api/runs/{run_id}/samples/{sample_id}/heatmap?component=resid_post
GET /api/runs/{run_id}/activation?sample_id=...&token_index=...&layer=...&component=...
```

### NLA

```text
GET  /api/runs/{run_id}/nla?sample_id=...
POST /api/jobs/nla
```

`POST /api/jobs/nla` 请求体：

```json
{
  "run_id": "demo-jailbreak-001",
  "sample_id": "unsafe-1",
  "token_index": 3,
  "layer": 20,
  "component": "resid_post",
  "profile": "qwen2.5-7b-l20"
}
```

### Prompt 分析

```text
POST /api/jobs/analyze
GET  /api/jobs/{job_id}
GET  /api/jobs/{job_id}/events
```

`POST /api/jobs/analyze` 请求体：

```json
{
  "prompt": "Show a jailbreak attack plan.",
  "model": {
    "source": "dummy",
    "name": "dummy"
  },
  "pipeline": {
    "probes": ["dummy_probe"],
    "attributors": ["dummy_attributor"]
  }
}
```

### 导出

```text
POST /api/export/html
POST /api/export/json
```

## 12. 本地存储

推荐 workspace 结构：

```text
.safelens/
  runs/
    demo-jailbreak-001/
      run.json
      samples.json
      tokens.json
      heatmaps/
        resid_post.json
        mlp_out.json
      nla.json
      cache/
        manifest.json
```

第一版不直接把大型 tensor 全量写 JSON。大型 activation 有三种策略：

1. 只写 summary，例如 norm、shape、top-k dims。
2. 写 `.pt` / `.npz`，JSON 中保存路径。
3. 延迟读取，用户点击 cell 时才加载。

## 13. 与 SafeLens 核心库的边界

后端通过 adapter 层调用核心库：

```text
SafeLens.app.adapters
  -> SafeLens.pipelines.runner
  -> SafeLens.nla
  -> SafeLens.viz
  -> SafeLens.utils.model_wrapper
```

规则：

1. UI 不直接 import 核心内部实现。
2. 后端 API 不暴露原始 Python 对象。
3. 所有前后端数据都通过 JSON schema。
4. 大型 tensor 只通过 manifest 和摘要暴露。
5. 核心库可以没有前端依赖。
6. 前端可以没有模型依赖。

## 14. 安全与隐私

默认安全策略：

1. 只监听 `127.0.0.1`。
2. 禁止默认公网绑定。
3. 启动时如果用户传 `--host 0.0.0.0`，打印明确警告。
4. 不自动上传 prompt、activation 或 report。
5. 外部模型下载必须沿用 SafeLens 现有配置和 cache policy。
6. 导出文件写入 workspace，不写任意系统路径，除非用户显式指定。

## 15. MVP 范围

MVP 应该控制在可以快速完成、能展示核心交互价值的范围内。

### 必须有

1. `safelens app` 本地启动。
2. Run list。
3. 内置 demo run。
4. Token Timeline。
5. 点击 token 打开 inspector。
6. Layer x Token heatmap。
7. Risk report panel。
8. 加载已有 `RunReport` JSON。
9. JSONL prompt run 或单 prompt run。
10. 导出当前 view 为 JSON。

### 应该有

1. NLA explanation 展示。
2. NLA job 按钮。
3. Pin token 对比。
4. Raw JSON drawer。
5. Component tabs。

### 可以延后

1. WebSocket 实时日志。
2. 多 run 对比。
3. 大型 tensor lazy streaming。
4. 复杂 patching/intervention UI。
5. 前端截图导出。

## 16. 里程碑

### Phase 0: 设计冻结

产出：

- 本计划文档。
- API 草案。
- 前端页面草图。
- demo 数据格式。

验收：

- 可以明确第一版做什么、不做什么。
- 可以据此拆 issue。

### Phase 1: 后端骨架

任务：

1. 新增 `src/SafeLens/app/server.py`。
2. 新增 `schemas.py`。
3. 新增 `storage.py`。
4. 提供 `/api/health`。
5. 提供 `/api/runs`。
6. 提供 `/api/runs/{run_id}`。
7. 提供 demo run loader。

验收：

- `python -m SafeLens.app.server` 可启动。
- `GET /api/health` 返回 ok。
- `GET /api/runs` 返回 demo。

### Phase 2: 前端骨架

任务：

1. 新建 `apps/local_explorer`。
2. 初始化 Vite + React + TypeScript。
3. 实现 `RunSelector`。
4. 实现 `TokenTimeline`。
5. 实现 `TokenInspector`。
6. 接入 `/api/runs` 和 `/api/runs/{run_id}`。

验收：

- 打开 localhost 能看到 demo run。
- 点击 token 后右侧 inspector 更新。

### Phase 3: Heatmap 与 Risk 联动

任务：

1. 后端提供 heatmap API。
2. 前端实现 `LayerHeatmap`。
3. risk evidence token 可点击。
4. heatmap cell 可点击。
5. token、cell、inspector 三者联动。

验收：

- 点击 risk evidence 自动跳到 token。
- 点击 heatmap cell 显示 layer-token 详情。

### Phase 4: Prompt Runner

任务：

1. 后端提供 `POST /api/jobs/analyze`。
2. 实现同步 lightweight job。
3. 支持 dummy model 和已有 pipeline config。
4. 生成本地 run。
5. 前端完成 prompt input 和 job status。

验收：

- 用户输入一句话后能生成新 run。
- 新 run 自动出现在 run list。

### Phase 5: NLA 接入

任务：

1. 后端读取已有 NLA rows。
2. 前端展示 explanation、cosine、MSE。
3. 支持 `POST /api/jobs/nla`。
4. 首先支持缓存结果展示，实时推理作为可选。

验收：

- demo 中点击 token 能看到 NLA explanation。
- 对没有 NLA 的 token，UI 能显示运行入口或缺失原因。

### Phase 6: 导出与文档

任务：

1. 导出 JSON。
2. 导出当前 selected view。
3. 写使用文档。
4. 写开发文档。
5. 加入 mkdocs nav。

验收：

- 用户可以把当前探索状态保存到文件。
- 文档解释如何启动、如何加载 report、如何添加 demo。

## 17. 测试计划

### 后端测试

1. `GET /api/health`。
2. demo run list。
3. run detail schema。
4. sample tokens schema。
5. heatmap schema。
6. invalid run id。
7. invalid sample id。
8. prompt analyze job。
9. NLA job 参数校验。
10. export JSON。

### 前端测试

1. RunSelector 渲染。
2. TokenTimeline 点击。
3. TokenInspector 展示。
4. Heatmap cell 点击。
5. risk evidence 点击。
6. empty state。
7. loading state。
8. error state。

### 端到端测试

1. 启动本地 server。
2. 打开首页。
3. 选择 demo run。
4. 点击 token。
5. 点击 heatmap cell。
6. 运行 prompt。
7. 导出 JSON。

## 18. UX 细节

### 空状态

没有 run 时显示：

- 选择 demo。
- 加载 report。
- 输入 prompt。

不要显示大段说明文字，尽量通过明确按钮和短标签引导。

### 加载状态

长任务必须显示：

- job id。
- 当前阶段。
- 可取消按钮。
- 错误信息。

### 错误状态

错误信息要具体：

- 缺少 model dependency。
- 缺少 activation cache。
- 当前模型不支持 component。
- 当前 layer 不存在。
- NLA profile 和 activation dimension 不匹配。

### 视觉风格

平台应偏研究工具风格：

- 信息密度较高。
- 低装饰。
- token、heatmap、inspector 是主角。
- 不做 landing page。
- 不做大 hero。
- 不用大面积渐变和装饰图形。

## 19. 验收标准

MVP 完成时应满足：

1. `safelens app` 可以启动本地服务。
2. 首页直接是可用工作台，不是营销页。
3. 至少一个 demo run 可加载。
4. 每个 token 都可以点击。
5. 点击 token 后 inspector 有内容。
6. heatmap 可以点击。
7. risk evidence 可以跳转 token。
8. 可以运行一个 dummy prompt workflow。
9. 可以导出 JSON。
10. `pytest`、`ruff`、`mypy`、`mkdocs build --strict` 通过。

## 20. 风险与应对

### 风险：实时模型运行太慢

应对：

- MVP 默认使用 cached demo。
- prompt runner 先支持 dummy 和小模型。
- NLA 先支持缓存展示，再做实时推理。

### 风险：activation 太大

应对：

- 默认只存摘要。
- 点击时 lazy load。
- 支持 top-k dimension 和 norm。

### 风险：前后端耦合过深

应对：

- 强制使用 API schema。
- 前端不 import Python。
- 后端不返回 Python 对象 repr。

### 风险：和核心库边界混乱

应对：

- `SafeLens.app` 只作为适配层。
- 核心能力仍在 `SafeLens.pipelines`、`SafeLens.nla`、`SafeLens.viz`。
- 不为了 UI 改核心数据结构，除非核心数据结构本身有缺陷。

## 21. 第一批 Issue 拆分

1. Add `SafeLens.app` backend skeleton.
2. Add local explorer Vite app.
3. Add demo run storage format.
4. Add run list/detail APIs.
5. Add token timeline UI.
6. Add token inspector UI.
7. Add layer-token heatmap API.
8. Add heatmap UI interactions.
9. Add prompt analyze job API.
10. Add dummy prompt workflow.
11. Add NLA row display support.
12. Add export JSON endpoint.
13. Add docs and startup guide.
14. Add backend tests.
15. Add frontend interaction tests.

## 22. 建议的第一版 Demo

Demo 名称：`demo-jailbreak-token-inspection`

内容：

- 两条样本：一条 benign，一条 risky。
- risky 样本包含明显 risk term。
- 每个 token 有 token id 和文本。
- 有 layer x token norm heatmap。
- evidence token 指向 risky token。
- 至少一个 token 有 NLA explanation。
- inspector 可以展示 NLA、risk、attribution、raw JSON。

这个 demo 不依赖大模型，适合 CI、文档和第一次产品演示。

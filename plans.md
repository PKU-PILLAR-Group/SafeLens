# SafeLens Local Explorer 优化计划

## 1. 项目定位

SafeLens Local Explorer 的目标不是只展示若干静态图表，而是成为一个本地、可复现、
数据语义可信的大模型安全与机制可解释性研究工作台。

平台应支持研究者沿统一分析链路完成以下任务：

```text
选择 Run/Sample
    → 选择分析视图和 Layer
    → 选择 Token 或组件
    → 查看原始指标、代理指标和因果证据
    → Pin、比较、导出或启动进一步实验
```

所有界面必须明确区分：

- 原始模型数据（raw）。
- 派生代理指标（derived proxy）。
- 安全方法输出（safety method output）。
- 因果实验结果（causal evidence）。

## 2. 当前状态

当前 Local Explorer 已具备：

- `Overview / Residual / Attention / MLP / NLA / Attribution` 统一主视图。
- Overview 已提供探索性 Primary finding、Supporting/Contradicting evidence、Limitations、Recommended
  analysis 和可跳转 Evidence graph，不把缺失证据或代理指标写成安全结论。
- Residual Logit Lens 已提供每层 top-k 明细、target logit/probability 轨迹和 observed-target log-rank
  轨迹，Layer 轴与全局 selection/URL/键盘导航同步。
- 共享 Layer 和 Token 选择状态。
- Residual、Attention、MLP 的真实模型缓存派生指标。
- 严格 token/layer 匹配，不使用附近结果冒充当前结果。
- 指标 provenance、normalization 和 proxy 说明。
- 多视口响应式布局。
- Token 前后导航、键盘导航和 Pin。
- 当前证据 JSON 导出。
- NLA 不兼容状态展示。

当前主要局限：

- 已接入 localhost FastAPI、workspace 索引、metadata-first hydration 和 JSON sidecar 物理分块；
  大型 safetensors/NPZ 的二进制 range backend 与零拷贝解码尚未实现。
- Attention 已接入完整二维矩阵、同层共享色阶 Head Overview，以及 retained-head mean/max/
  entropy-weighted 聚合，但当前每层仅保留按风险质量排序的至多 3 个 head；全模型 head artifact
  仍取决于后端数据能力。
- bundled 生成器当前每层保留最多 16 个高峰值 neuron 的完整 signed token profile；前端已通过
  2,000-neuron 虚拟 Canvas、deferred 搜索与选择同步验收，但大模型全量 neuron 的 artifact 生成、
  neuron 维分页与二进制 range 读取尚未实现。
- Captum Attribution、NLA、Activation Patching 和 Intervention 已形成可取消的 SSE 任务与结果回填闭环；
  全量产品模型/方法组合仍取决于后端 artifact 能力。
- Compare Drawer 已支持跨 run/sample 的严格 token 对齐、单点 delta、Attention 行分布、signed
  Attribution profile difference、Intervention original→steered generation diff，以及小矩阵全量/长上下文有界采样的
  Attention matrix difference。
- 20 万 cell 已使用 Canvas 视口渲染并有 production 性能门禁；真实 WebGL/GPU memory 和跨浏览器
  性能验收仍是后续边界。

### 2.1 实施进度（2026-07-12）

Phase 1 的可视化操作基础已完成主体实现：

- 已建立基于 `useReducer` 的全局 Selection Store，统一 view、token、range、layer、
  head、track、metric、normalization 和 pinned items。
- 已实现 URL 双向同步与刷新恢复，旧 `mode` 参数仍可兼容。
- 已实现可复用 `MatrixHeatmap`，并接入 Residual、Attention 和 MLP。
- 已实现 metric toolbar、raw/normalized、zoom、reset、拖拽 token range、legend、
  provenance tooltip 和 cache key 复制。
- Pin 已升级为完整 `PinnedEvidence`，保存在 localStorage 中，点击可恢复原视图上下文。
- 已建立 Playwright E2E，覆盖 URL 恢复、状态同步、Pin 恢复、矩阵框选和移动端布局。
- 已实现响应式 Compare Drawer：首项作为 baseline，仅对同 metric、同 normalization
  的项目计算 delta；不同尺度明确标为不可直接比较，并支持移除与完整上下文恢复。

Phase 1 的六项主体交付和矩阵交互增强均已完成；Shift/Cmd 多选、矩阵平移、Fit、固定轴
以及二维键盘导航的完成情况见 2.4。后续重点转向 Token Timeline 与跨 Run 比较。

### 2.2 Phase 2 进度（2026-07-12）

- Attention destination×source 二维矩阵已完成，直接使用真实
  `blocks.{layer}.attn.hook_pattern[head]` 缓存。
- 已实现 layer/head 联动、source/destination 双选择、因果 mask、概率 tooltip、zoom、
  source/destination URL 恢复以及 pair 级 Pin/Compare。
- Attention evidence table 现在选择 source token，不再错误地改变 destination token。
- 移动端采用横向矩阵滚动且取消高顶栏 sticky，避免工具栏被遮挡。

Residual logit lens 也已完成：生成器对每层 `resid_post` 应用模型真实 final norm 和
unembedding，保存 top-k vocabulary prediction、raw logit、softmax probability、
observed-next-token rank 与 cache provenance；前端支持 Logit/Probability 切换和 layer
联动，并明确标注其为诊断投影而非因果贡献。

MLP token×neuron matrix 已完成：生成器保留每层最多 16 个高峰值 neuron 的完整
signed token activation profile、正负 top tokens 和 raw peak；前端提供正负发散色带、
signed/absolute/normalized 切换、threshold、neuron 搜索、token/neuron 双选择、URL 状态
以及 activation 级 Pin/Compare。选中 neuron 另有完整跨 token profile 曲线、正负峰值导航、
键盘 token rail 和严格轴对齐的 profile difference。界面明确区分 activation、logit
contribution、probe contribution 和 causal ablation effect。

Signed attribution matrix 已完成：数据契约按 method 保存 signed/unsigned、evidence kind、
normalization、source key、available 状态和 unavailable reason；Residual direction 使用
真实逐层 raw projection，attention/safety proxy 明确标为 unsigned。前端支持方法选择、
正负贡献分离、raw/normalized、token/layer 联动、Pin/Compare，并为未运行的 Integrated
Gradients 展示所需 artifact 和 target objective，不生成替代值。

NLA fidelity workspace 已完成：支持 Layer×Token×Component 精确覆盖矩阵、
cosine/MSE/FVE、threshold、explanation search、低保真状态和候选列表。新增结构化
profile compatibility，分别检查 model、layer 和 d_model。当前 tiny-GPT-2 run 明确展示
`0 available / 3 incompatible candidates / 120 expected cells`，不将缓存 activation 或附近
token/layer 冒充 NLA fidelity；Run NLA 在后端未接入前保持禁用。

至此 Phase 2 的五项主体视图均已实现。下一阶段进入真实 RunReport/Artifact 加载与任务闭环；
Captum attribution job 和 NLA job 属于 Phase 3 后端任务。

### 2.3 Phase 3 进度（2026-07-13）

多 Run/Artifact 本地加载基础已完成：

- 使用 Zod 建立 `schema_version: "1.0"` Explorer Artifact schema，同时兼容单个 legacy
  `ExplorerRun`。
- 校验必需字段以及 token index、layer reference、attention destination×source shape、
  neuron token profile 和 attribution row length 等跨字段不变量。
- 支持 4 MB 内 JSON 导入、最多 6 个最近样本、localStorage 持久化、替换、删除、
  Run/Sample 选择和 URL `run/sample` 恢复。
- 已解除所有子视图对模块级 `realRun` 单例的依赖，统一通过 Run Context 读取当前数据；
  Run 切换会重新初始化 selection，避免跨样本 token/layer/head/neuron 污染。
- 新增可回读的 Explorer Artifact 导出；Evidence JSON 与 Run Artifact 明确分离。
- 导入错误显示 JSON parse、schema version、字段路径和矩阵 shape 等结构化诊断。

只读 workspace 数据面与前端接入已于 2026-07-13 完成：

- 新增限制在指定 artifact root 的 localhost FastAPI，提供 `/api/health`、`/api/runs`
  和精确 run/sample endpoint；忽略 symlink、阻止路径越界并限制 compact JSON 大小。
- Run Library 已合并 `bundled / local / workspace` 三类来源，按 `runId + sampleId` 去重，
  单个远端样本校验失败不会阻塞其他有效样本。
- 已统一为 idle、loading、ready、empty、error、cancelled 六态，并实现 Retry 和 Cancel；
  API 离线归入 error 且保留具体原因，bundled 与 browser-imported runs 始终可用。
- URL 指向 workspace run 时会等待发现结果，不会在请求完成前错误覆盖 run/sample。
- 移动端新增 Run Library 底部抽屉，可直接导入 JSON、查看来源、刷新或取消 workspace 请求。
- E2E 已覆盖远端 URL 恢复、错误重试、取消、本地回退和移动端数据抽屉。

Phase 3 尚余：Activation Patching job，以及大 activation 的 safetensors/NPZ 分块加载。

### 2.4 矩阵操作一致性进度（2026-07-13）

- 通用 MatrixHeatmap 已增加 Select/Pan 分段模式、拖拽平移、Ctrl/Cmd+滚轮缩放、Fit、
  Reset 和默认固定行轴；移动端横向滚动后仍能看到当前 layer/row 语义。
- Shift+单击可固定第二个比较锚点，矩阵显示 anchor 位置并在 tooltip 中计算 raw delta；
  Ctrl/Cmd+单击会按精确 layer/token 构建 `PinnedEvidence` 并加入 Compare。
- 通用矩阵使用 roving tabindex，方向键、Home 和 End 在二维网格内导航；焦点、URL、
  selection 和 tooltip 同步，事件不会再冒泡导致页面级 token 快捷键重复移动。
- Attention、MLP、Attribution 和 NLA 已复用同一组 Select、Pan、Zoom、Fit、Pin axes、
  Reset 图标与行为，所有图标按钮均有 tooltip、`aria-label` 和 `aria-pressed`。
- 四类专用矩阵均改为单一 Tab 入口和二维方向键导航；Attention 导航严格限制在 causal
  mask 允许的 source≤destination 区域。
- 矩阵空详情区已改为状态文案，不再长期显示操作教程；桌面和 390px 移动端布局均完成
  截图检查。

### 2.5 Token Timeline 进度（2026-07-13）

- Timeline 已按 artifact 中真实 `source` 分成 User prompt 与 Assistant reply；当前 bundled run
  只有 prompt，因此不伪造 reply。Reply token 展示真实或按顺序派生的 generation step。
- Token schema 新增可选 `isSpecial`、`generationStep`、`probeScore` 和 `monitorHit`，保持旧
  artifact 兼容；真实生成器使用 tokenizer `all_special_ids` 写入 special 状态。
- 新增 Safety proxy、Attribution、Residual norm、NLA fidelity 和按数据可用性出现的 Probe
  score 着色；每种色阶使用独立语义色，缺失指标使用斜纹而不是零值颜色。
- 新增风险、attribution、NLA、probe、monitor 和 pinned marker，图例只展示当前数据中
  实际存在的 marker，不生成 Probe/Monitor 假命中。
- 支持 text、position、token id 搜索以及 `token-250`、`token:250`、`#250`、`id:20250`
  等自然定位格式；上一项/下一项会同步 selection、焦点和 URL。
- 支持 Token/Word 两级视图；Word 模式根据 tokenizer 空白边界合并 BPE 子词，并保留包含的
  token 数、范围、聚合指标和 marker。
- Shift+单击生成精确 token range，Ctrl/Cmd+单击加入 Compare，左右方向键使用单一 Tab
  入口移动；hover 只做临时联动，不改写 URL。
- 超过 180 个 item 时启用以当前选择为中心的窗口化渲染，260-token E2E 验证 DOM 固定为
  180 个 token，并可通过搜索跳转到窗口外位置。

### 2.6 跨 Run/Sample Compare 进度（2026-07-13）

- Pin 已从“当前 Run 局部状态”升级为最多 4 项的全局 comparison workspace；切换 Run
  不再过滤或覆盖其他 Run 的 Pin，Timeline 仍只标记当前 Run 的 pinned token。
- `PinnedEvidence` 新增 token id/source、model name/source、cache source key、provenance 和
  captured time 快照；Compare 不再用当前 Run 的 token 或 provenance 错误解释历史证据。
- 跨 Run token 对齐分为 exact、text-only、position-only 和 unaligned；exact 要求同模型/
  tokenizer、token id 和 decoded text 一致，text-only 明确警告 tokenizer/id 差异。
- 相同 position 但 text 不同只标记 position-only，禁止生成 delta；unaligned 同样不可比较，
  不再把 token position 冒充 token identity。
- delta 同时要求 metric、normalization、evidence class 和 token alignment 兼容；不兼容项
  仍可并排检查，但展示具体原因而不是笼统的“不同尺度”。
- 任意卡片可切换为 baseline，Drawer 会重排并重新计算 alignment、compatibility 和 delta；
  Summary 显示 evidence、run/sample、token position 和 baseline-compatible 数量。
- 新增 `safelens-comparison` JSON artifact 导出，包含 baseline、完整 evidence snapshots、
  alignment、comparability reason 和可用 delta。
- Restore context 支持先切换本地/远端 Run，再通过 URL 初始化 token、layer、view、metric、
  normalization、head/neuron/track；来源 Run 已删除时按钮禁用并明确提示。

### 2.7 Inspector 进度（2026-07-13）

- 原先按 View 拼接的多个 Inspector 分支已替换为统一 evidence model 和独立
  `EvidenceInspector`，桌面与移动端复用完全相同的数据语义和操作。
- Inspector 固定为 `Summary / Evidence / Actions` 三层，Summary 展示 primary、raw/stored、
  displayed、units、evidence class 和状态原因，不再用 0 代替缺失 raw value。
- Evidence 展示 method、normalization、精确 cache key、shape、source artifact、run/sample、
  model 和 warnings；cache key 与完整 reproduction context 可直接复制。
- Actions 提供 Pin/Unpin、Compare、Context copy 和 evidence export；只有 status=available 的
  精确证据允许 Pin，missing component、未运行方法和失败任务均禁用。
- 状态明确区分 available、unavailable、incompatible、not computed 和 failed；NLA profile
  不兼容、Integrated Gradients 未运行、MLP layer 无 retained neuron 和 metadata job failure
  均有独立 E2E。
- Attention Summary 明确 source→destination/head，MLP 显示 neuron，Attribution 显示 method，
  NLA 显示 exact component；warnings 分离 descriptive proxy 与 causal evidence。
- 860px 以下隐藏排在长页面底部的重复右栏，使用 44px 信息按钮打开底部详情抽屉；支持
  Escape、背景关闭、初始焦点和打开 Compare 时正确关闭上层抽屉。
- 三栏桌面断点从 1520px 提前到 1280px；1440px 首屏可直接看到 sticky Inspector，
  主分析区在 1280–1519px 自动改为单列，避免矩阵被压缩或溢出。

### 2.8 错误隔离与异步状态进度（2026-07-13）

- 新增可复用 `AsyncStatePanel`，统一使用 `idle / loading / ready / empty / error /
  cancelled` 六态；每种状态具有独立语义、图标、颜色、`aria-live` 与 `aria-busy`，不再把
  空结果、离线错误或取消操作伪装成 ready。
- Workspace discovery 已接入统一状态组件：loading 可取消，empty/error/cancelled 可重试；
  空 artifact root 显示明确原因，同时 bundled 与 imported runs 继续可分析。
- 保留 AbortController，并使用单调 request id 做 latest-request-wins 竞态保护；旧请求晚返回时
  不得覆盖新 Run 列表，组件卸载或 StrictMode effect 重建时也不会产生过期状态回写。
- URL 指向尚未发现的 workspace Run 时，idle 与 loading 均视为解析中，避免首个 render
  把深链接提前回退到 bundled Run 并覆盖 `run/sample` 参数。
- 新增按分析视图隔离的 `ViewErrorBoundary`。单个矩阵、Trace 或辅助分析崩溃时，只替换
  当前分析区域，Timeline、选择状态、Inspector、Compare、导出和 Run Library 仍保持可用。
- 错误边界展示可折叠技术详情与 Retry；切换 Run、View、Layer、Head、Neuron 或 Track 会
  自动清除旧错误并重新渲染，移动端 fallback 自动改为两行布局。
- 新增 empty state、取消后重试、重叠请求 latest-wins 和远端深链接等待的 Playwright 覆盖；
  当前完整前端 E2E 为 33 passed，Python 为 977 passed / 53 skipped，生产构建通过。

### 2.9 Prompt Runner 与任务队列进度（2026-07-13）

- 新增 Prompt Runner 表单，支持 prompt、plain/chat template、固定白名单模型、seed、
  max new tokens 和 temperature；运行参数全部进入任务 request snapshot 与结果 metadata，
  greedy/sampling 语义由 temperature 明确区分。
- Explorer API 新增 `POST /api/jobs/prompt`、`GET/DELETE /api/jobs/{id}`、
  `GET /api/jobs/{id}/events` 和 prompt options；SSE 只在 snapshot 变化时推送，并以
  ready/error/cancelled 终态关闭连接。
- 后端使用单 worker 队列限制模型并发，模型仅允许显式 allowlist；真实生成器运行在隔离
  子进程中，不接受任意脚本、任意模型或 `trust_remote_code`。
- Cancel 会设置 cooperative flag 并终止运行中的子进程；artifact 验证、写入与原子替换前
  均重复检查取消状态，cancelled job 不会产生 result、半成品或 workspace artifact。
- 生成结果先写入 `.jobs` 临时区，通过 Explorer schema 基础检查后原子移动到
  `generated/*.explorer.json`；异常和取消都会清理临时 TypeScript/JSON 文件。
- 前端使用 EventSource 接收任务快照，复用六态 AsyncStatePanel 展示阶段、百分比、取消、
  重试和诊断；invalid JSON/schema 会进入可恢复 error，不产生未捕获异常。
- ready 结果必须再次通过前端 Zod `ExplorerRun` schema，才会以独立 `generated` 来源加入
  Run Library、写入 localStorage 并切换当前 Run/Sample；旧 job 事件由 generation id 隔离。
- 切换 Run 或组件卸载会关闭 EventSource 并取消未完成 job，防止过期结果污染当前选择；
  generated run 保留 job id、模型、模板、seed、采样参数和 source artifact provenance。
- 1440px 桌面和 390px 移动端已完成实机截图检查；参数使用稳定两列网格，Run 列表具有
  最小行高和内部滚动，Run 数量增加时不会被压成不可读的薄行。
- 真实 `sshleifer/tiny-gpt2` smoke job 在约 7 秒内生成 17-token/2-layer activation artifact，
  SSE 到达 ready 且 workspace 可索引；真实取消 job 无 result、无 artifact、无残留子进程。
- 后端新增提交/进度/SSE、白名单和取消测试，前端新增完成回填与取消 E2E；当前全量基线
  为 Python 980 passed / 53 skipped，前端 E2E 35 条，生产构建通过。

### 2.10 Captum Attribution Job 进度（2026-07-13）

- 在 Attribution 视图内新增 Integrated Gradients 工作台，支持 response、response target
  token index、PAD/zero-token baseline 和 8/16/32/64/128 integration steps；目标函数固定为
  可审计的 `response_token_logit`，不接受含糊的自由文本 objective。
- Captum `LayerIntegratedGradients` 现在显式传入 baseline，并请求 convergence delta；结果记录
  target token id/text/position、baseline token id/text、steps、method/version 和 convergence。
- 新增显式 `prepend_bos` 契约。Explorer job 使用与真实 artifact 生成器一致的
  `prepend_bos=false`，并逐 token 校验 token id；BOS 或 tokenizer 错位会失败，不做静默截断。
- 通用任务队列已支持 `prompt-run / attribution` 两类 job；各类使用独立单 worker，但共享
  GET/DELETE/SSE 状态协议、取消、终态、临时文件清理和 latest-event 防污染语义。
- Attribution 请求中的完整 Run 只在服务端 job payload 保留；公共 snapshot/SSE 仅返回
  sourceRun、response、target、baseline 和 steps，避免每次进度更新重复传输约 140KB 矩阵。
- 任务只接受 4MB 内的结构化 Run snapshot 和模型白名单，不读取用户提供的路径；response
  写入受限临时 JSON 而非子进程命令行，失败/取消后 input/result 临时文件均删除。
- 完成结果创建新的 derived Run 和 `generated/attribution-*.explorer.json`，不覆盖源 Run；
  metadata 保留 parentRun、sourceKey、raw values、目标、baseline、版本和完整 job provenance。
- Integrated Gradients matrix 只展示源 prompt token slice；归一化域包含 target 之前的所有
  prompt + response context。被省略的 response-context token attribution 单独保存在 metadata，
  Inspector 明确提示其数量，防止把 prompt slice 误认成完整上下文。
- Inspector 对 Captum 显示真正 raw score、独立 displayed value、causal evidence class、Captum
  版本、target/baseline/steps、cache key 和 normalization；不再把 stored value 冒充 raw integral。
- ready 结果经 Zod 后进入 Run Library，并自动恢复 Attribution / Integrated Gradients；取消、
  error、invalid SSE 或 token alignment failure 均保持源 Run 和 unavailable method 不变。
- 1440px 桌面与 390px 移动端真实 derived Run 已截图检查；任务参数、causal 标识、矩阵和
  Inspector 无重叠，移动端表单自动单列，触控操作保持可用。
- 安装项目声明的 `attribution` extra 后，真实 tiny-gpt2 / Captum 0.9.0 smoke 在约 7 秒内
  完成 8-step IG，得到 target=`stairs`、PAD baseline 和 convergence delta；artifact 可索引，
  smoke 产物随后已清理以恢复测试 workspace 基线。
- 后端新增通用 job、Attribution 提交/校验、snapshot 瘦身和 prompt/context 切片测试；前端
  新增 ready 回填与 cancel E2E。当前完整基线为 Python 983 passed / 53 skipped、前端 E2E
  37 passed，生产构建和 `git diff --check` 通过。

### 2.11 NLA Job 进度（2026-07-13）

- NLA 视图新增完整工作台：profile、checkpoint revision、explanation token limit、最多 8 个
  exact token positions、AV/AR repo 和 gated access confirmation；移除原矩阵中永久禁用的
  静态 Run NLA 占位按钮。
- 新增 `GET /api/nla/profiles` 与 authoritative `POST /api/nla/preflight`，逐项检查 model、
  layer、component profile、d_model 和 gated HF token；状态区分 compatible、incompatible 和
  authorization_required，unknown profile 返回结构化 422。
- 当前 tiny-gpt2 真实 preflight 明确报告 model/L20/d_model 三项不兼容、public access 通过，
  前端禁用提交并将完整原因放在操作旁；不会下载 Qwen/Gemma 权重或生成伪解释。
- compatible job 最多接收 4MB Run snapshot 和 8 个唯一 token position；gated profile 同时要求
  API 进程配置 HF token 与用户显式确认，AR reconstructor 强制启用，只有 explanation 而无
  cosine/MSE 的结果会失败。
- NLA worker 在隔离子进程中使用源 Run 的 prompt 重新执行 profile layer/component，严格提取
  `[position, d_model]` activation；activation 搬到 CPU 后释放 base model，再加载固定 revision
  的 AV/AR，避免 base + AV + AR 同时驻留。
- NLA 加载全程 `trust_remote_code=false`；response snapshot 不包含整份 Run。metadata 记录
  profile、base model、AV/AR repo、requested revision、解析后的 actor/AR checkpoint SHA、
  exact positions、generation limit、sourceRun 和安全设置。
- 结果只替换匹配 profile/layer/component/position 的 NLA 行，其他 unavailable candidate 原样
  保留；exact row 必须包含 explanation、activation norm、cosine 和 normalized MSE。
- ready 创建新的 `generated/nla-*.explorer.json` 和 derived Run，不覆盖源 Run；前端自动恢复
  NLA/cosine/首个目标 token，Run Library 来源与成功消息显式标记 NLA，不再误标 Attribution。
- NLA Inspector 对 available 行显示 profile、AV/AR resolved revision、exact layer/component、
  cache source 和 `trust_remote_code=false`；incompatible Run 仍只显示真实兼容性原因。
- 1440px 与 390px 真实 incompatible 状态已截图检查；preflight 检查同时使用图标、文字和边框，
  token picker 内部横向滚动，移动端参数与检查单列，无页面横向溢出。
- compatible Qwen ready/cancel 使用注入 worker 完成后端与 E2E 闭环；当前 workspace 没有兼容的
  Qwen2.5-7B L20 或 Gemma-3-12B L32 Run，因此未把模拟测试冒充真实 7B AV/AR 推理。
- 当前完整基线为 Python 987 passed / 53 skipped、前端 E2E 40 passed；生产构建、
  `git diff --check`、临时目录清理和 localhost API 健康检查通过。

### 2.12 Activation Patching Job 进度（2026-07-13）

- 新增独立 Patching 工作区，实验配置明确区分 clean prompt、corrupted prompt、component、
  layer、token position 和 target token logit；支持 `resid_post`、`attn_out`、`mlp_out`，不会把
  residual/attention/MLP 的描述性 proxy 冒充 patching 结果。
- 新增 authoritative `POST /api/patching/preflight`：使用与源 Run 模型一致的 tokenizer 检查
  clean token ids、corrupted token 数量、逐位置变化、目标 token 词表范围和 component；模型在
  tokenizer 加载前先经过 allowlist，避免任意模型下载或 `trust_remote_code`。
- 前端预检同时展示 prompt 是否变化、token 数量、target 合法性和 changed positions；clean 与
  corrupted token 逐位置并排显示，变化位置有文字/描边标记，未对齐或完全相同的 prompt 禁止提交。
- patch spec 支持选择唯一 layer 和 token position，单任务最多 2048 个 cell；每个 cell 都执行
  独立 forward pass，把 clean activation 的同位置向量替换到 corrupted run，不进行插值或代理估计。
- objective 固定为 corrupted 序列末位置的指定 target-token raw logit。artifact 同时存储 clean、
  corrupted、patched score，causal effect 定义为 `patched - corrupted`，recovery 定义为
  `(patched - corrupted) / (clean - corrupted) * 100%`。
- clean-corrupted 分母绝对值接近零时 recovery 写为 `null` 并在矩阵/Inspector 显示 `n/a`；仍保留
  causal effect 和 patched logit，避免以 0% 或无穷值伪造可解释的恢复率。
- Patching 使用独立单 worker 隔离子进程，但复用统一 queue、GET/DELETE/SSE、进度、取消、错误、
  临时文件清理和公共 request 瘦身协议；完整源 Run 不进入进度 snapshot。
- worker 重新 tokenize clean/corrupted prompt，并逐 token 校验 clean ids 与源 artifact；任何 tokenizer
  漂移、position 越界、layer 不存在或输出缺少 causal cell grid 都会失败，不写半成品。
- ready 创建新的 `generated/patching-*.explorer.json` 与 derived Run，不覆盖源 Run；metadata 保留
  parentRun、component、layers、positions、target、三类 score、sourceKey 和 job version。
- 因果矩阵支持 Recovery %、Causal effect、Patched logit 三种指标，未计算 cell 保持空白；正负值使用
  发散色并同时显示数值。点击 cell 联动统一 layer/token selection，Pin、Compare 和 JSON export 保留
  causal provenance、原始 patched score 与 clean/corrupted 基准。
- Inspector 对 exact cell 显示 causal evidence class、raw patched score、display metric、cache key、
  grid shape 和三项 logit；未纳入 grid 的 cell 标为 not-computed，近零分母标为 unavailable。
- 修复中等桌面宽度下 token 对齐条的 grid min-content 横向撑开问题；1280/1440/390px 计算宽度均无
  页面横向溢出，只有 token 对齐条和宽矩阵在自身容器内滚动。
- 真实 tiny-gpt2 smoke 将 `benign` 替换为同 token 数的 `harmful`，仅位置 4 变化；2 layer × 2 position
  job 得到 clean logit `-0.0030773`、corrupted logit `-0.0031281`，L0/T4 causal effect
  `0.0000347563`、recovery `68.45%`，真实 derived Run 经桌面/移动端矩阵与 Inspector 检查后清理。
- 新增 preflight、白名单加载边界、错位拒绝、队列回填、结果 merge 和辅助函数测试；前端新增 blocked
  与 ready derived Run E2E。当前完整基线为 Python 991 passed / 53 skipped、前端 E2E 42 passed，
  生产构建、真实模型 smoke、无控制台错误、截图检查和 `git diff --check` 均通过。

### 2.13 Intervention 前后对比进度（2026-07-13）

- 新增独立 Intervention 工作区，支持 desired/undesired reference、layer、`resid_post/attn_out/mlp_out`、
  scale、半开 prompt position range、target token、seed、max new tokens 和 temperature；所有参数进入
  request snapshot 与 derived Run provenance。
- 扩展核心 `ContrastiveSteeringVector` position 契约，新增 `(start, end)` 半开范围；tensor 与 Python
  activation 均只修改范围内 token。增量生成阶段若当前序列短于 start 会安全 no-op，不把 prompt
  position 错映射到新生成 token。
- 新增 authoritative `POST /api/intervention/preflight`，在 tokenizer 加载前执行模型 allowlist，并检查
  layer、component、position range、target token 词表范围以及两个 reference 是否真正不同。
- worker 使用 desired 与 undesired prompt 的末 token activation 构造 mean-difference direction，记录 raw
  norm 后单位归一化；零向量会失败，不用任意默认方向继续运行。
- original 与 steered generation 使用完全相同的 seed、prompt、max tokens、temperature 和 tokenizer；
  temperature=0 使用 greedy，采样模式会在两种条件前重置 RNG，保证对比可复现。
- steering hook 只在指定 layer/component/range 临时安装；original、steered target logit 都取源 prompt
  最后位置的同一 target token raw logit，delta 定义为 `steered - original`，evidence class 为 causal。
- artifact 保存两侧 continuation text、token ids、逐 token 文本、target logit、固定词汇 risk rate、
  Levenshtein token edit distance、SequenceMatcher diff opcodes 和 generationChanged。
- 当前 Explorer 没有已训练 probe，因此 `probeScore=null` 并保存明确原因；词汇风险变化单独标为
  `derived_proxy`，不会伪装成 probe 或 causal safety score。
- ready 创建新的 `generated/intervention-*.explorer.json` 与 derived Run，不覆盖源 Run；公共 SSE snapshot
  不传完整 Run，metadata 保留 direction method、layer/component/range、scale、target、generation 参数、
  sourceRun、sourceKey 和 `trust_remote_code=false`。
- 前端结果区并排展示 original/steered 输出，用 equal/replace/insert/delete token 状态呈现 diff；指标区将
  target-logit delta、edit distance 标为 causal，将 lexical delta 标为 derived proxy，将 probe 标为 unavailable。
- Inspector 显示 raw steered logit、displayed causal delta、单位向量 shape、activation source、两侧 logit、
  edit distance 和 probe-unavailable 原因；Pin、Compare、URL 恢复和 JSON export 使用 raw normalization。
- 任务复用统一 queue、GET/DELETE/SSE、取消、终态、临时文件清理与 latest-event 隔离；blocked、ready、
  cancel 三条浏览器链路均验证取消不替换源 Run、ready 自动恢复 layer/range token。
- 真实 tiny-gpt2 smoke 使用 2d normalized direction、raw norm `0.02410`、scale `5.0`、T4 range；target
  `:` logit 从 `-0.0030773` 变为 `-0.0031182`，causal delta `-0.00004088`。greedy continuation 未改变，
  edit distance 如实为 0，不人为制造输出差异。
- 1440px 与 390px 真实 derived Run 已截图检查；面板宽度/scrollWidth 分别为 796/794 和 354/352，
  无页面横向溢出、无控制台错误，微小 delta 使用科学计数法避免显示为 `-0.0000`。
- 新增 position range、incremental no-op、preflight、队列、merge、diff、edit distance 和 proxy 测试；
  当前完整基线为 Python 997 passed / 53 skipped、前端 E2E 45 passed，生产构建、真实模型 smoke、
  桌面/移动视觉检查、临时 artifact 清理和 `git diff --check` 均通过。

### 2.14 MatrixHeatmap Canvas 与 20 万 Cell 性能进度（2026-07-13）

- 通用 `MatrixHeatmap` 新增自动渲染策略：逻辑 cell 数少于 2,500 时保留语义完整的 DOM button grid，
  达到阈值后自动切换 viewport Canvas；用户无需理解或手动选择渲染后端。
- 修复 raw bounds 对大数组使用 `Math.min(...values) / Math.max(...values)` 的参数展开风险，改为一次线性
  reduce；20 万值不会触发 JavaScript 参数上限或额外创建完整 values 数组。
- Canvas 使用固定高度双向滚动 viewport 和逻辑 spacer，只绘制可见行列及一格 overscan；画布 backing
  store 按 viewport 与 devicePixelRatio（上限 2）调整，不创建全尺寸 20 万 cell 像素面。
- 绘制保留 normalized/raw 色彩、unavailable 斜纹、range 下划线、hover 列、selected 实线、comparison
  虚线、列 token index、layer label 和 pinned row axis；无颜色时仍可通过轮廓/线型区分状态。
- Canvas 命中测试精确扣除 row label、header、cell gap 与 scroll offset；支持 click 主选择、Shift anchor、
  Cmd/Ctrl Pin、drag token range、pan、wheel zoom、Fit、Reset 和外部 selection 自动滚入视口。
- 键盘支持 Arrow/Home/End、Enter、Shift+Enter 和 Space Pin。Canvas 通过 live description 朗读当前
  layer/token、display/raw value、cache key 和 unavailable 状态，不为 20 万 cell 创建隐藏 DOM 节点。
- 工具栏新增 render status，显示 DOM/Canvas mode、visible/total cells 和最近 draw latency；Canvas 同时在
  data attributes 暴露 visibleCells、drawMs、hoverMs，供性能回归直接断言。
- 新增 2,000 layer × 100 token、完整 200,000 residual cells 的远端 workspace fixture；正式 E2E 验证
  DOM cell 数为 0、可见 cell 少于 3,000、draw/hover 均小于 100ms、Canvas 像素非空、页面无横向溢出。
- 实测 1280px 桌面只绘制约 480/200,000 cells，draw 约 1.0–1.6ms；390px 移动端约
  289/200,000 cells，draw 约 0.8ms。单独运行导航到可交互约 2.1s，46-worker 并行压力下约 6.7s。
- 大 layer 集合不再渲染数千个按钮：16 层内保留快速按钮，超过后切换 Previous/Select/Next 与当前位置
  计数；修复 1,000 layer 将页面撑到 54,815px 的 min-content 溢出。
- 修复远端深链接竞态：Selection Store 仅在 URL run/sample 属于当前 Run 时回写 view/token/layer，等待
  workspace 数据期间不会用 bundled Run 默认 layer 覆盖目标 Run 的 `layer=999`。
- Token Timeline 的窗口由固定 180 项改为桌面 180 / 移动 60 自适应，减少窄屏长列表高度和 DOM 数量，
  保持搜索跳转与前后窗口语义。
- Vite production build 新增稳定 vendor 分包：主应用约 269KB，React 143KB，Zod 72KB，icons 23KB；
  消除单 chunk 超过 500KB 警告，首屏缓存可独立复用框架依赖。
- 20 万 cell 用例附带桌面/移动截图与 Canvas pixel check；当前前端 E2E 46 passed，Python 基线保持
  997 passed / 53 skipped，生产构建、无控制台错误和 `git diff --check` 通过。

### 2.15 Specialized Matrix Canvas 进度（2026-07-13）

- 新增共享 `SpecializedMatrixCanvas` viewport renderer。它只负责双向可见区域裁剪、1 格 overscan、DPR
  backing store、滚动同步、命中测试、selection 自动滚入视口、键盘导航、focus ring、live description
  和 draw/hover 性能数据；业务颜色、标签、可用性与选择语义仍由各专业矩阵定义。
- Attention、MLP、Attribution、NLA 均采用相同自动策略：逻辑 cell 少于 2,500 时保留原有语义 DOM
  button grid，达到阈值后自动切换 Canvas。小样本的精细 DOM 可访问性不变，大样本不再创建成千上万
  button；用户无需手动选择渲染模式。
- Attention Canvas 保留 destination × source 轴、raw softmax 强度、因果 mask 斜纹和禁止选择语义；方向键
  会约束 `source <= destination`，Home/End 分别跳到首 source 和当前 destination，URL 的 source/target
  与统一 token selection 同步。
- MLP Canvas 保留 Token × Neuron 轴、正负发散色、threshold 低透明度、metric 精确值、neuron 搜索后
  的动态列集合以及 token/neuron 双选择；大 activation 数组的最大绝对值计算改为线性扫描，避免参数展开。
- Attribution Canvas 保留 Method Row × Token、signed/unsigned 分色、raw/normalized tooltip 和 source key；
  bounds 计算改为线性扫描，避免大方法矩阵触发 `Math.min(...values)` / `Math.max(...values)` 参数上限。
- NLA Canvas 保留 Layer-Component × Token 的 `high / low / incompatible / missing` 四态，后两态使用不同
  斜纹；新增 exact row lookup Map，使 viewport cell 查询从逐 cell 扫描 rows 改为 O(1)，稀疏 artifact
  不会因为逻辑矩阵很大而强制补齐完整数据。
- 修复 Canvas 键盘详情同步：当 Canvas 保持焦点且 selection 变化时，Tooltip 与 live description 同时更新；
  不再出现键盘已移动到新 cell、详情仍停留在旧 cell 的视觉误导。
- 专用 Canvas 统一使用固定 440px / 54vh 双向 viewport、pinned row axis、十字选择光标与 pan 光标；
  390px 视口保持页面宽度 390px，无工具栏或矩阵造成的页面级横向溢出。
- 新增 30 layer × 100 token、100 × 100 attention、100 × 30 MLP、30 × 100 attribution 和稀疏
  30 × 100 NLA 的远端 Run fixture。正式 E2E 验证四个矩阵 DOM cell 均为 0、Canvas 像素非空、
  visible cells 小于 3,000、draw 小于 100ms、鼠标点击与方向键正确更新 URL；移动端 visible cells
  小于 2,000，并执行 pixel check 和无横向溢出检查。
- 当前完整前端 E2E 为 47 passed；production build、TypeScript、桌面/移动 viewport 回归和
  `git diff --check` 均通过。Python 逻辑未变，基线保持 997 passed / 53 skipped。

### 2.16 Metadata-first 与 Artifact Chunk 协议进度（2026-07-13）

- Workspace 索引新增 `chunkProtocol: safelens-chunks-v1` 能力声明；默认 artifact 读取上限由仅适合紧凑
  JSON 的 4MB 提升为可配置的 128MB，仍限制在只读 artifact root、拒绝 symlink/path traversal，且不会
  将任意文件路径暴露给浏览器。
- 新增 `GET /api/runs/{run}/samples/{sample}/metadata`。响应仅包含 prompt、tokens、layers、NLA
  compatibility、metric provenance、run metadata 等 core 字段，不传 residual、attention、MLP、
  attribution、NLA、patching 或 intervention 大集合；同时返回每个组件的 itemCount、rangeAxis、
  layerFilter 和 selectorFilter 描述符。
- 新增 `GET /api/runs/{run}/samples/{sample}/chunks/{component}`，统一使用 `tokenStart/tokenEnd` 半开
  范围并支持 layer/selector 过滤；单块最多 512 tokens，越界、空范围和过大范围均返回明确 422 code。
- Chunk 覆盖 residualCells、logitLens、attentionHeads、attentionCells、mlpNeurons、mlpCells、
  attributionTracks、attributionMethods、nla、patching 和 intervention。cell 集合按 token/layer 精确过滤，
  NLA 还能按 component selector 过滤。
- Attention chunk 同时裁剪 destination/source 方阵并携带两轴 start/end；MLP activation、attribution
  track/method values 携带 token offset；客户端不会把局部数组误解释为从 token 0 开始的完整数组。
- Metadata 与每个 chunk 使用 artifactId + modifiedAt + size + range/filter 构造稳定 ETag，支持
  `If-None-Match` 与 304；响应声明 `no-cache`，允许浏览器复用已验证内容，同时每次重验证 artifact 版本。
- 前端 `explorerClient` 新增严格 Zod metadata/chunk schema、run/sample/component 一致性校验、半开范围
  前置校验，以及按 artifactId/run/sample/component/range/layer/selector 隔离的内存 ETag cache；提供
  指定 artifact 或全局 cache 失效入口。
- Run Library 改为 index-first：workspace discovery 只拉 `/api/runs` 并立即展示 summary records，不再
  对所有样本执行 `Promise.allSettled` 完整下载。默认 bundled 首屏即使发现 N 个远端 Run 也只有一个索引
  请求；用户选择远端 Run 或使用直接深链接时才加载目标 sample。
- 远端 summary record 与 active loaded record 分离：分析区永远只接收经过完整 schema 验证的 Run；目标
  sample 加载失败或取消时保留原分析，不把 partial/invalid 数据送入矩阵。列表仍展示 token/layer/model/
  source 信息，并支持之后再次选择。
- 修复异步索引覆盖显式选择的竞态：只捕获应用挂载瞬间的远端深链接一次；索引响应结束后不再重新读取
  运行期间已变化的 URL，因此不会把刚导入的 local Run 错误切回 bundled Run。
- 新增浏览器回归，直接断言 workspace 索引完成后 sample 请求数仍为 0，显式选择后才恰好请求一次并切换
  prompt/active record；并对导入竞态执行 6-worker 重复复现。
- 真实 artifact 已验证 metadata descriptors、L1/T8–T11 residual chunk 和 L1H0 的 4×4 attention
  方阵 chunk；当前完整基线为 Python 998 passed / 53 skipped、前端 E2E 48 passed，production build、
  TypeScript、真实 7861 API smoke 和 `git diff --check` 均通过。
- 当前边界：选择目标远端 Run 后仍使用兼容完整 sample 端点进入分析区；core + 当前 view partial hydration、
  viewport 相邻块预取、导出/任务提交前完整 hydration 尚未接入，不能将本阶段描述为完整分块加载已完成。

### 2.17 PartialExplorerRun 当前视图 Hydration 进度（2026-07-13）

- 新增独立 `explorerRunCoreSchema`，只验证 run/sample/model/prompt/tokens/layers、NLA compatibility、metric
  provenance 和 metadata；Partial Run 不伪装成通过完整 `explorerRunSchema` 的 artifact。
- 新增 `remoteHydration` store/helpers，使用 `run/sample/view/layer/destination block/source block` scope 管理
  loaded、loading 和 error；token block 固定为最多 512，scope 切换会取消上一请求，过期响应不会写回当前 Run。
- 支持从 metadata 构建明确的 partial shell。未加载的 Attention/Attribution placeholder 仅用于保证 React
  派生安全，不会进入 ready 视图；component chunk 到齐前分析区显示 loading，Inspector status 为 loading，
  Pin/Compare/Context/Export current evidence 操作禁用，不把“未加载”误报为 unavailable。
- 当前 view 依赖按语义加载：Overview/Residual 加载 residualCells + logitLens；Attention 加载 heads、聚合 cells
  和 residual trace；MLP 加载 neurons、聚合 cells 和 residual trace；Attribution 加载 methods、tracks 和
  residual trace；NLA 加载 exact rows 和 residual trace；Patching/Intervention 加载对应实验对象。
- Attention 协议扩展为独立 destination `tokenRange` 与 `sourceRange`；服务端分别校验两个半开范围且各不超过
  512，客户端将 source block 纳入 URL、cache key 与 hydration scope。跨 block source→destination pair
  不再被错误标记为已加载。
- Chunk merge 保留全局 token index：Attention 将局部二维块写入稀疏全局 destination/source 坐标；MLP
  activation、Attribution values 使用 tokenStart offset；cell/logit/NLA 使用 layer/component/token 精确键
  去重。视图切换后已加载块保留，不覆盖其他组件。
- 修复 cross-view Trace 语义：Attention、MLP、Attribution、NLA ready scope 均包含同 token block 的
  residualCells；Trace evidence 不会因依赖尚未加载而显示伪造 `0.0`。
- Run Library active/recent badge 对 partial 远端 Run 显示 `workspace · range`；完成 full hydration 后自动恢复
  `workspace`。顶部 NLA 指标在 NLA chunk 未加载时显示 `n/a`，不再用 `0.00` 冒充真实 fidelity。
- Attribution/NLA/Patching/Intervention job 配置在 partial 状态下由 full hydration gate 替代；用户可显式
  `Load full Run`。完整 artifact 导出也先拉取并通过 full sample schema，失败时保留 range visualization 并
  显示可恢复错误；不会将稀疏数组导出成看似完整的 artifact。
- 当前 evidence JSON 在 partial 状态只导出选中 Attention pair、MLP activation、Attribution value 和
  `completeArtifact=false` coverage 信息，不序列化带空洞的伪完整矩阵。Pin/Compare 继续保存精确已加载值。
- 新增 chunk-v1 浏览器链路：MLP 深链接只请求 metadata、MLP 和 residual chunks，完整 sample 请求为 0；
  随后切换 Attention、NLA、Patching、Intervention、Attribution 均只加载当前依赖。Attention 人为延迟时
  Inspector 显示 loading；NLA 首次 500 仅隔离当前视图，Retry 后恢复且不下载完整 Run。
- 同一链路验证实验门禁、桌面/390px 页面无横向溢出、范围矩阵截图、full artifact 下载 schema，以及只有
  完整导出时才发生唯一一次 sample 请求。当前完整基线为 Python 998 passed / 53 skipped、前端 E2E
  49 passed，production build、TypeScript、pixel/视觉检查和 `git diff --check` 均通过。
- 当前边界：客户端尚未预取相邻 token block，也未合并并发相同 chunk 请求；服务端每个 metadata/chunk
  请求仍会扫描并解析完整 JSON artifact。真正面向数百 MB artifact 还需要预分块存储或 sidecar index。

### 2.18 Chunk 调度、取消与缓存进度（2026-07-13）

- `explorerClient` 新增同 key in-flight Promise 去重；metadata/chunk 的 key 包含 artifactId、modifiedAt、
  sizeBytes、run/sample、component、destination/source range、layer 和 selector，artifact 更新不会命中旧版本。
- 共享请求为每个调用者维护独立 AbortSignal subscription；单个调用者取消只结束自己的等待，只有全部订阅者
  都取消才 abort 底层 fetch。已 abort 且尚未清理的 entry 不会拦截紧随其后的 Retry。
- Metadata 与 chunk cache 改为有界 LRU，分别最多保留 32 和 96 项；命中会提升最近使用顺序，超过上限淘汰
  最旧项。按 artifactId 或全局清理时同时终止对应 in-flight 请求，避免内存和事件监听持续增长。
- Partial Run 在 token 数超过 512 时使用 `requestIdleCallback(timeout=1000)` 低优先级预取相邻 destination
  block；不足 512 不发预取。前台 scope 变化、Run 切换、full hydration 或卸载会提升 generation 并取消旧预取。
- 预取只返回 chunks，完成时将每块 merge 到最新 state 中的 Run；不会用发起预取时的旧 Run 快照覆盖用户
  刚加载的其他 view。预取失败静默释放 scope，用户真正导航到该块时仍走可见 loading/error/Retry 链路。
- 新增 600-token E2E：Residual 首屏精确加载 T0–511，空闲期自动加载 T512–599 的 residualCells 与
  logitLens；当前块和相邻块各组件请求恰好一次，完整 sample 请求保持 0。
- Chunk loading 新增独立 Cancel：取消后保留已加载 ranges，scope 进入 cancelled 而不是 failed；Inspector
  同步显示 cancelled，Pin/Compare/Context/Export 禁用。Retry 清除 cancelled scope 并重新请求；浏览器链路
  对 Attention 延迟请求完整验证 loading → cancelled → Retry → ready。
- `RemoteRunState` 现在同步 view range 的 loading/ready/error/cancelled；局部 500 不破坏其他已加载 view，
  Cancel workspace discovery 仍保留原有离线回退文案和行为。
- 服务端 `_scan_artifacts` 新增 64 项解析 LRU，以 resolved path + mtime_ns + size 为 key。metadata、多个 chunk
  和 full sample 请求复用一次 `read_text + json.loads`；文件原子替换或内容更新后自动使用新 key，专项测试
  验证三类请求只读取一次、改写后恰好重新读取一次。
- 当前完整基线为前端 E2E 50 passed（含 partial 多视图、取消/Retry 与相邻预取）、Python
  999 passed / 53 skipped（API 专项 19 passed）；production build、TypeScript、桌面/移动截图检查和
  `git diff --check` 均通过。
- 当前边界：逻辑 chunk 已避免网络传输完整矩阵并消除重复 JSON 解析，但服务端进程首次仍需将完整 JSON
  读入内存。下一阶段必须使用离线 sidecar manifest + component/block 文件，或 safetensors/NPZ range backend。

### 2.19 物理 Sidecar 分块与只读加载进度（2026-07-13）

- 新增 `safelens-explorer-chunks` 离线生成器和 `scripts/build_explorer_chunk_sidecar.py` 入口；生成器只在构建
  阶段读取一次完整 Explorer JSON，并按 source SHA-256、sample、component 和 block range 写入不可变
  `.safelens-blocks`。在线 metadata/chunk 请求不再读取或解析完整 source artifact。
- 新增 `safelens-physical-chunks-v1` manifest。清单保存 source path、size、mtime_ns、SHA-256、sample core、
  component descriptor，以及每个 block 的相对路径、范围、size 和 SHA-256；先写临时文件再 `os.replace`，
  避免 API 观察到半写入的新版本。
- Residual、Logit Lens、MLP、Attribution、NLA、Patching 和 Intervention 使用 token block；Attention 使用
  独立 destination × source 二维 block，因此任意跨轴子窗口都只读取命中的物理块，不需要退回完整方阵。
- API discovery 优先索引有效 manifest，并用 source SHA 前 16 位作为 artifactId；同 run/sample 的 legacy
  embedded JSON 自动去重。manifest 过期、source size/mtime 不匹配或结构无效时记录诊断并回退 embedded
  JSON，旧 artifact 仍可继续使用。
- 物理读取器限制 block/source 必须位于 artifact root，拒绝 `..`、绝对路径和 symlink；读取后同时校验
  block size 与 SHA-256。完整 sample/export 路径仍读取原 source，并校验完整 source SHA，即使文件保持相同
  size/mtime 也不会静默接受被替换内容。
- metadata、chunk 和 full sample 分别返回 `X-SafeLens-Storage: physical`、`physical` 和
  `physical-source`，便于测试和后续可观测性区分。物理 block 读取同样使用有界缓存，重复视窗不会重复解析。
- 已为真实 `real-run.explorer.json` 生成 sidecar：source 143,902 B，manifest 17,873 B，11 个物理 block
  （文件系统占用约 202 KiB）。在线实测 metadata 7,388 B、MLP neurons 4,159 B、MLP cells 3,003 B、
  Residual 4,756 B、4×4 跨轴 Attention 653 B，完整 sample 66,328 B；常见组件视窗约为完整响应的
  4.5%–7.2%。
- 专项测试覆盖物理 manifest 优先、metadata/chunk 零 source read、任意 Residual/Attention 子范围、block
  checksum 损坏、过期 manifest fallback、路径越界，以及同 size/mtime source 篡改。当前完整基线为 Python
  1005 passed / 53 skipped（物理分块与 API 专项 25 passed）、前端 E2E 50 passed；production build、
  compileall、真实 7861 API smoke 和 `git diff --check` 均通过。
- 当前边界：block 仍为 JSON，尚未达到 safetensors/NPZ 的紧凑度和零拷贝能力；full sample 仍从校验后的
  embedded source 返回，而非从 blocks 重组；旧 source SHA 对应的不可变 block 尚无垃圾回收；首屏时间、
  服务端峰值内存和浏览器峰值内存还需在长序列/大模型 artifact 上建立自动化基准。

### 2.20 Modal 焦点管理与移动端工作区收敛（2026-07-13）

- 新增共享 `useModalDialog` 行为，Run Library、Evidence Inspector 和 Compare Drawer 统一支持初始焦点、
  Tab/Shift+Tab 焦点循环、Escape 关闭、背景滚动锁定，以及关闭后将焦点准确归还触发按钮。
- Modal 打开时对顶栏和主工作区应用原生 `inert`，背景内容同时退出键盘顺序和可访问树；全局左右键导航也会
  暂停，避免用户操作抽屉时背景 token 被静默切换。dialog 本身保留 `aria-modal`、label 和可聚焦 fallback。
- 860px 以下不再在主分析末尾重复显示完整左栏。Run Library、Prompt Runner、Data provenance 和 Evidence
  快捷入口统一收进 Data Workspace bottom sheet；选择 Run、生成 Run 或点击 Evidence 后自动关闭并回到分析。
- 520px 以下收紧顶栏 padding、品牌间距和图标尺寸，隐藏重复的 run-id 副标题；保留产品名、Run selector、
  三个核心指标、Compare 与导出操作，首屏信息层级更紧凑。
- 新增 E2E 验证三个 dialog 的初始焦点、末项 Tab 回环、Escape 焦点归还、`inert` 生命周期、modal 打开时
  token 不变化，以及移动端左栏隐藏但抽屉功能完整。当前前端完整基线为 51 passed；production build、
  TypeScript、390×844 关闭态/抽屉态截图、桌面回归和 `git diff --check` 均通过。
- 当前边界：完整无障碍验收仍需补自动化 WCAG 对比度扫描、读屏实测、所有长表单的错误关联，以及复杂
  Canvas 在不同读屏器上的行列导航验证；本阶段不能将“完整键盘和无障碍支持”标记为全部完成。

### 2.21 Roving 导航与全视图 WCAG 门禁（2026-07-13）

- Analysis View 改为标准 `tablist/tab/tabpanel`：仅当前 tab 进入 Tab 顺序，方向键循环切换，Home/End 跳转
  首尾；`aria-selected`、`aria-controls`、当前 panel label、URL 和实际视图保持同步。
- 16 层以内的 Layer selector 改为 `radiogroup/radio` roving focus；方向键与 Home/End 更新 layer、URL、焦点和
  `aria-checked`，不会触发背景全局 token 导航。长 layer 列表继续使用原生 select + 前后 stepper。
- 输入框、select 和 textarea 统一增加 2px focus ring；所有 button、matrix Canvas、Timeline token 和 modal
  保留既有可见焦点，形成连续的键盘分析路径。
- 引入 `@axe-core/playwright` 作为正式 E2E 门禁，对 Overview、Residual、Attention、MLP、NLA、Patching、
  Intervention、Attribution 八个视图，以及 390px 主页面、Run Library、Evidence Inspector、Compare Drawer
  执行 WCAG 2 A/AA 与 WCAG 2.1 A/AA 扫描，当前 violations 为 0。
- 根据扫描结果加深 Residual、Attention、MLP、NLA、Intervention、Attribution、Inspector 和 Compare 的
  辅助文本颜色，修复临界或明显低于 4.5:1 的组合；数值、状态色和布局语义保持不变。
- Inspector cache key 的复制按钮移入合法的 `<dt>/<dd>` group；Attention Evidence 移除不完整的伪 table
  ARIA，保留原生可操作 button 语义，不再向读屏器声明缺少 cell/row 的错误表格结构。
- `prefers-reduced-motion` 规则移至样式表最终优先级，并覆盖 mobile/compare drawer、backdrop、token pulse 和
  job progress；实际 reduced-motion 环境不再运行进入动画或进度 transition。
- 修复慢 workspace discovery 覆盖显式导入/生成/选择的竞态：任何用户选择都会废弃 mount-time deep link；
  即使远端 index 或 deep-link sample 后返回，也只更新索引，不夺回 active Run。E2E 使用受控延迟稳定复现。
- 当前完整前端基线为 53 passed；production build、TypeScript、npm audit（0 vulnerabilities）、1440×1000
  Attribution 与 390×844 Attention 截图、无横向溢出检查和 `git diff --check` 均通过。
- 当前边界：Axe 自动化不能替代 NVDA/VoiceOver 实测；Canvas 的 live description 已覆盖键盘选择，但仍需在
  多读屏器上验证长矩阵导航；任务表单的 field-level error association 和高对比度/forced-colors 模式仍待审计。

### 2.22 Forced Colors 与任务字段错误关联（2026-07-13）

- 新增 `@media (forced-colors: active)`：保留 MatrixHeatmap、Attention、MLP、Attribution、NLA、Patching
  的数据颜色编码，并用系统 `Highlight/HighlightText` 标出当前 View/Layer/Mode，用 `CanvasText` 3px outline
  标出选中 cell，用 `GrayText` dashed border 区分 masked、filtered、missing 和 unavailable。
- 修复 forced-colors 下矩阵被系统背景替换为全白的问题；1440×1000 Attention 截图确认概率强度、causal
  mask、选中 source/destination 和 legend 同时可辨认，不只依赖颜色。
- 20 万 cell 通用 Canvas 与 Attention/MLP/Attribution/NLA 专用 Canvas 均断言
  `forced-color-adjust: none`，在桌面/390px 高对比模式附加截图并继续执行像素非空、可见 cell 和交互检查。
- Patching 的 corrupted prompt/target token、Intervention 的两个 reference/layer/range/target、NLA revision、
  Prompt Runner prompt 和 Integrated Gradients response 全部增加字段级 `aria-invalid`、`aria-describedby` 与
  可见错误文本；preflight reason 使用稳定 id 和 polite live region，API 错误使用 alert。
- 高对比模式中的 ready/available 使用 double border，failed/unavailable/incompatible 使用 dashed border；
  状态文字和图标仍保留，因此关闭自定义颜色后不会丢失实验可用性语义。
- 新增 E2E 覆盖 forced-colors 的 View/Layer selection、DOM cells、Canvas、mask/selected 状态和五类长表单
  required/preflight 错误关联。当前完整前端基线为 55 passed；production build、TypeScript、Axe 全视图
  WCAG A/AA、forced-colors 截图、npm audit 和 `git diff --check` 均通过。
- 当前边界：仍需使用 NVDA、JAWS 和 VoiceOver 做人工矩阵导航与 live region 验证；Windows High Contrast
  不同系统主题的颜色组合还需真实设备视觉回归，自动化 Chromium forced-colors 不能完全替代该验收。

### 2.23 Skip Link 与全局快捷键作用域（2026-07-13）

- 页面首个 Tab 现在显示 `Skip to analysis workspace`，Enter 直接将焦点移到带稳定 landmark label 的主分析区，
  跳过品牌、Run selector、指标、导出按钮和左侧数据工具；分析区声明 `aria-keyshortcuts`。
- Skip Link 隐藏时不占空间，获得焦点后进入独立布局行并下推顶栏，不使用覆盖层遮挡品牌或操作；1440px 与
  390px 焦点截图均无内容重叠和横向溢出。
- 全局 ArrowLeft/ArrowRight token 导航只在非交互上下文生效；input、textarea、select、button、link、tab、
  radio 和 matrix grid 内的按键由控件自身处理，导出/Compare 等按钮不会再静默改变背景 token。
- 新增 E2E 验证首焦点、Skip Link 可见性、landmark 焦点转移、快捷键声明、分析区 token 导航，以及按钮/
  搜索输入中的左右键不改变 URL selection。当前完整前端基线为 56 passed；production build、TypeScript、
  桌面/移动焦点截图和 `git diff --check` 均通过。
- 当前边界：Skip Link 和 landmark 已解决长页面的首段跳转，但不同读屏器中的 landmark 快捷键、Canvas live
  description 节奏和连续快速 selection announcement 仍需人工验证。

### 2.24 移动端 Sticky Selection Action Bar（2026-07-13）

- 860px 以下的 selection summary 改为 sticky action bar；滚动进入矩阵、Trace、Model output 和 Evidence 长页
  后仍固定在 viewport `top: 8px`，持续显示当前 token、layer 与 safety proxy。
- 操作条新增三个 44×44px 图标按钮：Pin/Unpin 当前证据、打开 Compare、打开 Evidence Inspector；按钮包含
  tooltip、动态 aria-label、`aria-pressed`、disabled 和 active 状态，不依赖颜色表达是否已 Pin。
- Compare Drawer 记录实际触发元素：从顶栏、移动 sticky bar、桌面 Inspector 或移动 Inspector 打开时，关闭
  后分别归还正确焦点，不再固定跳回顶栏 Compare。
- 修复默认 evidence Pin ID 缺少 source-token 占位段的问题；初始 pinned `break` 与实时构造的 evidence ID
  现在一致，移动 bar 正确显示 Unpin，也不会再次 Pin 出语义相同的重复对象。
- 390×844 滚动态实测 action bar 为 354×62px，三项摘要各 58px、三项操作各 44px，页面 scrollWidth
  保持 390px；截图确认不遮挡矩阵选中 cell、legend 或下方证据内容。
- 新增 E2E 覆盖 sticky y 坐标、Pin toggle、Compare 打开/Escape 焦点归还和 Inspector 打开。当前完整前端
  基线为 57 passed；production build、TypeScript、移动滚动截图和 `git diff --check` 均通过。
- 当前边界：移动 sticky bar 已覆盖核心分析动作；后续可根据真实用户测试决定是否加入 Export，但当前保持
  三个高频按钮，避免 320–390px 屏幕过度拥挤。

### 2.25 视图级代码分割与首屏优先加载（2026-07-13）

- 高成本且低频的 Attention、MLP、NLA、Attribution、Patching、Intervention 矩阵与任务面板，以及 Residual
  的 logit lens 改为 `React.lazy` 命名导入；Overview 的 metadata、Token Timeline 和基础 Residual/Overview
  布局仍由首屏主包直接提供，单个视图模块加载失败继续由现有 View Error Boundary 隔离。
- 分析区域新增稳定的 `role=status` 模块加载占位，声明当前视图、`aria-busy` 和可读状态文案；移动端沿用双列
  紧凑布局，避免懒加载期间出现高度跳动或空白区域。
- View tabs 在 pointer enter 或键盘 focus 时预取对应模块；预取请求复用浏览器动态 import 缓存并吞掉预取错误，
  实际切换仍显示可恢复的加载/错误状态，不阻塞当前已可用视图。
- production 主入口从 310.87 kB（gzip 74.72 kB）降至 226.38 kB（gzip 56.43 kB），高成本模块以独立 chunk
  输出；CSS 110.19 kB（gzip 20.08 kB）。构建和 TypeScript 通过，专项 E2E 17 passed。
- 本阶段遗留的首屏、视图可交互、hover 和取消响应观测已在 2.26 接入；固定 CPU/network profile 下的常规
  样本 2 秒门槛与 JS heap 峰值仍按 2.26 的边界继续推进。

### 2.26 前端性能时间线与自动化门槛（2026-07-13）

- 新增本地性能事件层：通过浏览器 Performance Timeline 记录 `first-usable`、`view-ready`、`matrix-hover`、
  `selection-commit`、`cancel-request` 和 `cancel-feedback`，同时派发 `safelens:performance` CustomEvent；不向
  任何远端服务发送 telemetry。
- 首屏/视图就绪不以 React mount 代替可用状态，而是等待当前 artifact range ready、懒加载占位消失，并在
  下一次 animation frame 记录；事件 detail 保存 view/token/row/column/render mode，便于复现实验上下文。
- 通用 MatrixHeatmap Canvas 和 Attention/MLP/Attribution/NLA 专用 Canvas 统一记录真实 hit-test hover latency；
  chunk Cancel 从点击到 cancelled UI commit 的响应时间也使用同一 monotonic clock 记录。
- 高频事件使用最多 100 条的本地环形记录，并通过 `window.__SAFELENS_PERFORMANCE__` 供本地调试；每类原生
  Performance Mark 只保留最新一条，避免长时间 hover 或切换视图造成时间线持续增长。
- 20 万 cell Playwright 基准新增 first-usable、当前 ready view、hover latency 和有界记录断言；chunk-v1 用例
  新增 cancel feedback 小于 300ms 的门槛。当前完整前端基线为 57 passed，production build 和 TypeScript
  通过；主入口 227.60 kB（gzip 56.97 kB）。
- 20 万 cell 测试继续使用 CI 稳定门槛（首屏小于 10 秒、hover 小于 100ms）；常规样本 2 秒预算和 Chromium
  JS heap 增长已在 2.27 建立独立串行门禁，真实 WebGL 与跨浏览器内存仍为后续边界。

### 2.27 Production 首屏预算与长会话增长门禁（2026-07-13）

- 新增独立 `playwright.performance.config.ts` 和 `npm run test:performance`；使用 production build + preview、
  单 worker、禁用 browser cache、20ms RTT、10 Mbps download / 5 Mbps upload 和 2× CPU throttle，避免普通
  57 worker E2E 的并发负载污染首屏测量。
- 常规 bundled run 在该固定 profile 下必须于 navigation 后 2,000ms 内写入 `safelens:first-usable`，同时确认
  Overview 已 ready 且不存在残留的 lazy module loading placeholder；性能测试附加实际 JSON measurement。
- 长会话用例先预热八个视图及全部 lazy chunks，再连续完成 40 次视图切换；通过 CDP 强制 GC 后比较
  `JSHeapUsedSize`、DOM Nodes、JSEventListeners、Documents，并同时检查 live Canvas、100 条事件环形上限和
  每类只保留一个的 Performance Mark。
- 门槛为预热后 heap 增长小于 4 MiB、DOM 增长小于 120、listener 增长小于 24、Document 最多增加 1、live
  Canvas 不超过 1、Performance Mark 不超过 6；baseline/final runtime snapshot 作为 JSON attachment 保存。
- production 性能套件当前 2 passed（串行约 16 秒）；普通 `playwright.config.ts` 明确 ignore 专用预算文件，
  因此功能/Axe/移动端完整回归仍保持独立的 57 项并行门禁，不会被 CPU throttle 污染。
- 当前边界：Chromium CDP 已覆盖 JS heap、DOM 和 listener；Firefox/WebKit 的等价内存观测、GPU process memory
  与真正的 WebGL 渲染路径仍未建立，不能据此声称跨浏览器或 GPU 内存预算已完成。

### 2.28 超大矩阵 Minimap 与二维快速导航（2026-07-13）

- 新增共享 `MatrixOverviewNavigator`，仅在达到 Canvas threshold 的矩阵显示；通用 MatrixHeatmap、Attention、
  MLP、Attribution 和 NLA 均提供同一套 210×56px 低分辨率概览，不改变小矩阵的 DOM 操作界面。
- 概览最多采样 96×28 个点，因此 20 万乃至更大逻辑 cell 不会转化为同量 DOM 或绘图调用；颜色直接复用当前
  metric、normalization、method/head、threshold 和 component，控制变化后刷新概览而非显示过期图层。
- 概览持续绘制当前 viewport 矩形和 selected cell 圆点；点击任意位置居中跳转，按住拖动连续平移，方向键按
  0.75 viewport 步进，Home/End 跳到二维首尾。按钮提供 tooltip、focus ring、快捷键声明和读屏说明。
- navigator 使用零高度 sticky overlay 固定在矩阵右下角，不扩展虚拟 content 尺寸；最大宽度 210px、移动端
  自适应收缩。forced-colors 保留实际数据缩略色，同时以深色 viewport outline 表达当前位置。
- 20 万 cell E2E 新增非空像素、210×56 稳定尺寸、Home/End、点击居中和恢复原点断言；四类专用 Canvas 均
  验证 navigator 可见，390px 下不造成横向溢出。production 性能套件继续 2 passed，2 秒首屏和 40 次视图
  切换后的 heap/DOM/listener 门槛未回退。
- production 主入口为 231.27 kB（gzip 58.14 kB），CSS 110.90 kB（gzip 20.25 kB）；增加约 3.7 kB 主入口以
  换取所有超大矩阵共享的可视导航。当前边界仍是 Canvas 路径，尚未实现真实 WebGL/GPU memory 门禁。

### 2.29 大型 Run Library 搜索、筛选与窗口化（2026-07-13）

- workspace、imported 和 generated records 不再全部渲染为 card；Run Browser 固定窗口最多挂载 8 项，前后
  按 8 项翻页并显示 `start-end of total` live status。原生 Run/Sample selector 仍保留完整索引和快速跳转。
- 新增 run/sample/model/source name 的统一搜索，以及 All/Workspace/Imported/Generated 来源菜单；搜索或来源变化
  自动回到首窗口，零结果提供明确 empty state，不会把当前 active run 或主分析区域清空。
- 搜索、筛选和翻页仅作用于已获取的 metadata summaries，不触发 sample endpoint；只有明确选择某个 run 才沿用
  既有 lazy sample/chunk hydration。active run card 始终独立显示，不会因列表窗口或过滤条件丢失当前上下文。
- 桌面窗口按钮保持紧凑，860px 以下扩大为 44×44px；移动 Data Workspace drawer 复用同一逻辑，37 个 run 下
  页面仍保持 390px scrollWidth，不产生横向溢出。
- 新增 37-run E2E，验证首窗口仅 8 个 DOM card、下一窗口、source-name 搜索、来源空状态、移动端 44px 控件和
  sample request 为 0。完整前端基线增至 58 passed，production 性能套件继续 2 passed。
- production 主入口 233.02 kB（gzip 58.54 kB），CSS 112.29 kB（gzip 20.47 kB）；千级 records 的 native
  option 边界已在 2.30 通过自适应虚拟 combobox 解决，服务端分页仍是万级索引的后续方向。

### 2.30 千级 Run 索引自适应虚拟 Combobox（2026-07-13）

- 新增共享 `AdaptiveRunSelector`：100 条及以下继续输出原生 select，保留熟悉的系统菜单、现有自动化契约和
  小型 workspace 的最低交互成本；超过 100 条时，顶栏 Quick selector 与 Run Library selector 同时切换虚拟模式。
- 虚拟 combobox 搜索 run/sample/model/source name/type，结果 listbox 最多挂载 8 个 ARIA option；高亮窗口围绕
  当前 active descendant 移动，不会为 1,200 条 metadata 创建 1,200 个 `<option>` 或 button。
- 完整键盘模型覆盖 ArrowUp/Down、Home/End、Enter、Escape；输入声明 `aria-autocomplete=list`、expanded、controls
  和 active-descendant，listbox/option 维护 selected 状态。鼠标 hover/click 与键盘共享同一 highlighted index。
- Run Library 弹层按面板宽度展开；顶栏桌面最大 360px，860px 以下改以完整 run-status 定位并左右贴合容器，
  390px 实测 popup 不越界且 document scrollWidth 保持 390px。
- 1,200-run E2E 验证两个 selector 进入 combobox、初始只挂载 8 项、精确搜索、ArrowDown+Enter、只请求 1 个
  sample、active run 同步、Escape 关闭、移动边界和全 Run Library WCAG A/AA。扫描同时发现并修复旧 Run card
  9px 标题 4.08:1 的对比度不足，主次文本已加深。
- 完整前端基线增至 59 passed，production 性能套件 2 passed；production 主入口 235.78 kB（gzip 59.36 kB），
  CSS 114.56 kB（gzip 20.89 kB）。当前仍在客户端持有全部 metadata；万级/跨机器索引应增加服务端 search cursor。

### 2.31 分析会话导出与跨 Run 回放（2026-07-13）

- 新增版本化 `safelens-explorer-session` schema；session 保存目标 Run/Sample/model/artifact 来源、完整 view/token/
  source/target/range/layer/head/neuron/track/metric/normalization、最多 4 个完整 PinnedEvidence，以及 Evidence filter。
- 顶栏新增 Save 图标导出 session JSON；Run Library 的既有 Import JSON 入口先识别 session kind，再使用 Zod 做
  字段级验证。无效 session 显示具体 path 诊断，不会退回按普通 artifact 解析，也不会改变当前 Run。
- 恢复目标为当前 Run 时原子 dispatch 完整 selection；目标为已索引但尚未加载的 workspace Run 时，App 层保留
  pending session，先走既有 lazy sample 请求，目标 ExplorerWorkspace 挂载后再恢复，避免状态跨 key 丢失。
- replay 会校验 token/layer/head/neuron/track 是否存在于目标 Run；越界选择回退到目标 Run 的有效对象，attention
  source 保持不超过 target，range 仅在两个 endpoint 都存在时恢复。Pin 顺序同时恢复，因此 Compare baseline 保持一致。
- 若 session 引用的 Run/Sample 不在 Library，显示“先加载目标 Run”的可操作错误，不静默套用到当前数据。恢复成功
  显示 Run/Sample/View 状态，并关闭旧 Compare/Inspector，防止旧 drawer 上下文与新 selection 混合。
- 390px 顶栏保留 Compare、Session Save、完整 Artifact 三项图标；重复的 current-evidence export 在窄屏隐藏，仍可
  从移动 Inspector 导出，因此新增 Save 不与品牌重叠。真实 iPhone 13 Chromium 截图已检查无溢出。
- 新增跨 Run E2E：先拒绝 malformed session 且 sample request 为 0，再加载目标 Run、恢复 Attention source/range/
  filter/空 Pin，最后下载并核对语义等价 session；目标 sample 只请求一次。完整前端基线增至 60 passed，production
  性能套件 2 passed；主入口 240.48 kB（gzip 60.52 kB），CSS 114.59 kB（gzip 20.90 kB）。
- Timeline search/mode/metric 与 Compare baseline 已在 2.32 提升到 Workspace 并进入回放；矩阵 zoom、交互模式、
  axesPinned 和 Fit 语义状态已在 2.33 完成。临时 hover/tooltip 等瞬时 UI 参数仍有意不进入持久会话。

### 2.32 Timeline 与 Compare Baseline 会话回放（2026-07-13）

- TokenTimeline 从内部 `useState` 改为受控 `TimelineState`，Workspace 统一持有 token/word mode、risk/attribution/
  residual/nla/probe color metric 和 search query；现有搜索、分组、长文本窗口与键盘行为保持不变。
- session schema 新增可选 timeline。新导出文件保存三项状态；缺少 timeline 的早期 1.0 session 继续合法，并按
  Token + Safety proxy + 空搜索恢复。若目标 Run 没有 probeScore，replay 将 probe metric 安全回退为 risk。
- CompareDrawer 的 baselineId 从 drawer-local state 提升到 Workspace；Pin 被移除或 session baseline 不存在时自动
  回退首个 Pin。切换 baseline 后导出 session、临时改用另一 baseline、重新导入，会恢复原 ID 和首卡顺序。
- session schema 的 compare 字段保持可选，因此 2.31 已导出的文件继续使用 Pin 首项作为 baseline；新文件保存
  baseline override，不改变独立 `safelens-comparison` artifact 的 baseline/delta 语义。
- 跨 Run session E2E 现在先验证无 timeline 的旧文件恢复默认值，再导入新文件恢复 Word/residual/`jail`，导出后
  核对 timeline；跨 Run Compare 用例验证 text-aligned baseline 经 session 往返后仍为首卡。
- 完整前端基线保持 60 passed，production 性能套件 2 passed；production 主入口 241.34 kB（gzip 60.79 kB），
  CSS 114.59 kB（gzip 20.90 kB）。矩阵绝对 scroll pixel offset 仍不序列化，因为跨 viewport/device 回放该值
  不稳定；2.33 已改为保存语义化 zoom size、interaction mode、axesPinned 和 fit mode。

### 2.33 矩阵视口状态与跨设备会话回放（2026-07-13）

- 新增 Workspace 级 `MatrixViewportSessionProvider`，统一持有 Residual、Attention、MLP、Attribution 和 NLA 的
  cell size、Select/Pan 交互模式、行轴固定状态与 Manual/Fit 模式；通用 MatrixHeatmap 和专用 Canvas 矩阵不再
  各自维护无法导出的孤立视口状态。
- session schema 新增可选 matrices map，保持旧 1.0 文件兼容；新导出会保存每个已操作矩阵的语义状态，跨 Run
  lazy load 完成后与 selection、timeline、Pin 和 baseline 一起恢复。临时 hover、tooltip、pointer drag 和绝对
  `scrollLeft/scrollTop` 不持久化，避免不同屏幕尺寸回放到错误像素位置。
- Fit 按钮现在具有可见 active 状态与 `aria-pressed`，进入 Fit 后使用 ResizeObserver 根据矩阵列数、label 宽度和
  容器宽度重算 cell size；从桌面切到 390px 移动视口会自动重新适配。手动 Zoom 和 Reset 会退出 Fit，Reset 同时
  恢复 Select 模式，现有 Pan、双击和 pinned axes 操作语义保持一致。
- 导入会话会按各矩阵真实控件范围裁剪尺寸：Residual 10–34、Attention 14–36、MLP 20–42、Attribution/NLA
  14–38。schema 允许的通用 8–64 范围不会再让某个视图恢复到自身控件不可达的状态；越界输入仍保留 mode、
  axesPinned 和 fitMode。
- 跨 Run E2E 使用 Attention `63px` 脏输入验证恢复为 `36px`，随后验证 Pan、unpin axes、Fit active、桌面到移动
  宽度自动重算及再次导出的语义状态；20 万 cell、所有专用矩阵统一控件和 enlarged-matrix Pan/Fit 专项共
  5 passed。
- 完整前端 E2E 为 60 passed，production 性能套件 2 passed；production 主入口 245.68 kB（gzip 61.94 kB），
  CSS 114.59 kB（gzip 20.90 kB），TypeScript、production build 和 `git diff --check` 通过。新增会话上下文后，
  常规样本 2 秒首屏与 40 次视图切换后的 heap/DOM/listener/Canvas/mark 门槛均未回退。

### 2.34 Patching 因果矩阵统一交互与可访问语义（2026-07-13）

- Patching 从独立静态横向网格接入共享 `MatrixViewportControls`，补齐 Select/Pan、Zoom、Fit、固定行轴、Reset、
  Ctrl/Cmd wheel 和双击恢复；指标切换增加 `aria-pressed`，Pin 与视口操作进入同一紧凑工具栏。至此 Residual、
  Attention、MLP、Attribution、NLA 和 Patching 六类矩阵均使用一致的图标位置和操作词汇。
- Pan 模式会让计算与未计算 cell 都把 pointer gesture 交给滚动视口，真实指针拖动可以改变 `scrollLeft`，不会因
  disabled cell 截断事件；手动缩放直接改变 token 列宽，Fit 使用 Patching 的 54px layer label、1px gap 和列数
  计算适配尺寸。axesPinned 关闭后 row label 不再被旧 CSS 强制 sticky。
- 增加二维 roving keyboard entry：ArrowLeft/Right 在已计算 positions 间移动，ArrowUp/Down 在实验 layers 间
  移动，Home/End 跳到行首尾，Space Pin 当前 causal cell；焦点与主 selection/URL 保持同步，focus ring 不依赖颜色。
- Patching 加入 session matrices map，保存并回放 32–64px size、Select/Pan、axesPinned 和 Manual/Fit；同 Run
  derived session E2E 验证 `54px + Pan + unpinned` 导出，Reset 后重新导入可恢复，Fit 状态继续具有可见 active 与
  `aria-pressed`。
- 新增固定详情栏与发散图例。鼠标 hover 或键盘 focus 显示 layer、token、当前 metric 精确值、causal evidence
  class 和 cache key；图例同时说明 negative/zero/positive/not computed，未计算状态使用纹理，不靠颜色猜测。
- Axe 扫描发现并修复旧网格的非法 `role=grid` 直接子 button：现在使用合法 row/columnheader/rowheader/gridcell
  层级；同时加深旧 baselines 和 token header 的临界低对比文字。原 forced-colors CSS 中不存在的
  `.patching-causal-grid` 选择器也已改为真实 `.patching-grid-row`，选中与不可用状态在高对比模式继续可见。
- 390px 下 Patching 工具栏自动分行，指标与图标控件至少 44×44px，document scrollWidth 保持 390px；矩阵只在
  自身容器横向滚动。Patching 专项通过 WCAG A/AA 零违规、键盘、Pan、session 和移动几何验证。
- 完整前端 E2E 为 60 passed，production 性能套件 2 passed；production 主入口 245.72 kB（gzip 61.96 kB），
  Patching lazy chunk 6.96 kB（gzip 2.58 kB），CSS 117.18 kB（gzip 21.41 kB）。TypeScript、production build
  和 `git diff --check` 通过，常规首屏 2 秒及 40 次视图切换资源增长门槛未回退。

### 2.35 移动端可视化触控尺寸与工具栏节奏（2026-07-13）

- 基于运行中平台的 1440×1000 与 390×844 Chromium 实景截图重新检查首屏，而不是只依赖 CSS media query。
  原布局无重叠，但手机端 Quick Run、View tabs、Layer、Token/Word 和矩阵图标按钮实际高度只有 24–36px，未达到
  23.9 的 44px 触控验收，因此统一提高高频分析控件的移动 hit target。
- 860px 以下 Topbar Compare/Session/Artifact、Quick Run、Run Library、八个 View tabs、Layer radio、Timeline
  search/metric/granularity/navigation 均至少 44px 高；Run status 收敛为 46px 容器，selector 和旁侧 Library 图标
  使用同一垂直节奏，不再出现一个可点区域明显小于另一个的情况。
- 通用 MatrixHeatmap 与 Attention、MLP、Attribution、NLA 的 select、search、range、normalization 和七项共享
  viewport 图标均按 44px 触控尺寸渲染；工具栏允许 6px gap 自然换行。Attention 的 Pin pair 保留文字按钮形式，
  最小宽度 70px，避免强行压成难以理解的图标。
- 390px 实景中矩阵工具栏从一行微型图标改为两行稳定操作区，品牌只做自然两行换行，Run/指标/Layer/八视图和
  Timeline search 仍在首视口内形成清晰层级；1440px 仍保持原紧凑桌面密度，移动规则没有污染桌面布局。
- 新增跨视图移动几何 E2E：逐一进入 Residual、Attention、MLP、Attribution 和 NLA，读取每个可见 form、segment
  和 toolbar button 的真实 `getBoundingClientRect()`；所有目标高度至少 44px，图标按钮宽高均至少 44px，
  每次切换后 document scrollWidth 均严格为 390px。
- 同一用例对最终移动 main panel 执行 Axe WCAG A/AA，零违规；既有窄屏 Drawer、sticky selection、forced colors、
  键盘和桌面 Inspector 测试继续通过。完整前端 E2E 增至 61 passed，production 性能套件 2 passed。
- production 主入口保持 245.72 kB（gzip 61.96 kB），CSS 为 118.31 kB（gzip 21.57 kB）；TypeScript、production
  build 和 `git diff --check` 通过，常规首屏 2 秒及 40 次视图切换资源增长门槛未回退。

### 2.36 移动首屏数据可见性与 View Tab 导航（2026-07-13）

- 2.35 将触控目标提升到 44px 后，390×844 实景仍显示八个 View tabs 占三行、Timeline search result 独占一行，
  第一批 token 被推到首视口之外。本阶段不回退触控尺寸，而是减少导航本身的垂直占用，让数据重新成为首屏信号。
- 860px 以下 View tablist 改为单行内部横向滚动，每项保持至少 108×44px、图标和完整标签；右缘保留下一项的
  局部可见提示，tab strip 使用 scroll snap 和 contained overscroll，document 本身不产生横向溢出。
- WorkspaceTabs 在当前 view 变化时只调整 tablist 自己的 `scrollLeft`，不调用可能引起整页垂直跳动的
  `scrollIntoView`。直接 URL/session 回放 Attribution 等末端视图、点击和 roving keyboard 后，active tab 均完整
  进入可视范围；Home 键切回 Overview 时 strip 同步回到起点。
- 520px 以下 Timeline 继续保留 Search、Token/Word、Metric 和前后结果导航全部 44px 控件，但 Metric 与结果导航
  合并为同一行。390px 实景中 Search、三类 marker 与第一批真实 token 均进入 844px 首视口，未用折叠说明、
  隐藏指标或缩小文字换取空间。
- 移动几何 E2E 新增 tablist `scrollWidth > clientWidth`、直接 Attribution active-tab viewport rectangle、Home 后
  `scrollLeft=0`、首个 `.token-pill` 的 y 小于 844，以及跨五视图 document scrollWidth=390；移动 main-panel Axe
  WCAG A/AA 继续零违规，既有桌面/移动 roving keyboard、sticky action bar 和 drawer focus 回归通过。
- 完整前端 E2E 保持 61 passed，production 性能套件 2 passed；production 主入口 246.06 kB（gzip 62.12 kB），
  CSS 118.49 kB（gzip 21.63 kB）。TypeScript、production build 和 `git diff --check` 通过，常规首屏 2 秒及
  40 次视图切换资源增长门槛未回退。

### 2.37 Compare 基线差值图与性能门禁隔离（2026-07-13）

- Compare Drawer 在四项摘要与证据卡片之间新增 baseline-centered delta profile。每行同时显示 Run ID、token、
  layer、精确 delta 和中心轴条形；baseline 使用独立标记，正负 delta 只表达数学方向，不使用“改善/恶化”等未经
  metric 语义支持的判断。
- 只有 token alignment、metric、normalization 和 evidence class 全部兼容时才绘制 bar；position-only、unaligned、
  不同 metric/normalization/class 使用斜纹 track、`not comparable` 文本和完整读屏原因，不会把不可比项压到零点
  冒充相等。图例同时提供 negative/positive/not comparable，强制高对比继续保留 bar、baseline marker 和纹理。
- profile 标题按上下文区分 Attention、Attribution、跨 layer 和通用 baseline delta；切换 baseline 后图与卡片顺序、
  中心值、最大绝对缩放和精确 delta 同步重算。跨 Run 同名 token 会在截断标签中显示 Run ID，并用 `title` 保留
  Run/Sample/token/layer 全路径，图上的每个数字可以直接追溯来源。
- 390px Drawer 使用 80px label、弹性 track 和 64px exact value 三列，Header Export/Close 修复旧 CSS specificity
  导致的竖排问题并改为横排；Header、baseline/remove、Restore 等移动操作至少 44px。1440px 与 390px 稳定动画
  终态截图确认中心图、卡片和背景之间无穿透、遮挡或横向溢出。
- Compare Drawer 改为独立 lazy chunk，顶栏按钮在 pointer enter/focus 时预取；网络延迟时显示 aria-modal loading
  dialog，完成后进入既有 focus trap。受控 route E2E 验证首屏请求数为 0、focus 后请求 1 次、pending fallback
  可见且最终只加载一次。
- Compare 专项覆盖默认三/四项、不可比无 bar、跨 Run text-only/position-only、baseline 重排、artifact/session
  往返、Restore、Escape/focus return、forced colors 和 Drawer Axe WCAG A/AA 零违规。
- 主入口由接入图表后的 248.71 kB 降至 238.46 kB（gzip 59.90 kB）；Compare chunk 11.26 kB（gzip 3.80 kB），
  CSS 121.98 kB（gzip 22.34 kB）。普通功能套件为 60 passed。
- 20 万 cell 在 62 worker 争用 CPU 时两次分别仅超 10 秒门槛 26ms/192ms，但单独运行通过；未放宽 10 秒标准，
  而是将 `matrix-performance.spec.ts` 从普通并发套件移入单 worker production performance 配置。性能套件现为
  4 passed：20 万 cell、四类大型专用矩阵、2 秒首屏和 40 次视图资源增长，避免并发噪声掩盖真实回退。
- 当前 PinnedEvidence 是单点 snapshot，因此本阶段能诚实呈现 attention/attribution/layer point delta profile；完整
  attention matrix difference 和 intervention generation sequence diff 仍需在 Pin artifact 中增加版本化数组/序列
  payload，不能用单值条形冒充，继续作为 23.6 的后续数据契约边界。

### 2.38 700–1100px 顶栏密度与中间视口验收（2026-07-13）

- 补齐 23.7 明确要求但此前只有间接测试的 1024px、768px 中间视口实景检查。原 `max-width:1100px` 布局把
  Run selector 与三项指标分别放在两个全宽行，右侧留下大块空白，顶栏约 200–211px 高，主分析内容被无意义
  下推；700px 临界宽度还暴露出 grid min-content 与后置 860px media rule 的 cascade 冲突。
- 700–1100px 顶栏改为两行双列：第一行 Brand / Actions，第二行 Run / Metrics。列宽使用
  `minmax(280px, 0.8fr) minmax(356px, 1.2fr)`，横向 gap 18px、行 gap 12px；低于 700px 继续使用移动堆叠，
  高于 1100px 保持桌面单行，不用一个断点规则覆盖所有设备。
- `run-status` 增加 `min-width:0` 与 `box-sizing:border-box`，允许长 Run ID 在自身 selector 内截断而不撑开 grid；
  中间断点用 `.topbar > .run-status/.run-meta` 约束优先级，避免后置 `max-width:860px` 再把两项拉回全宽并重叠。
- 521–760px 品牌使用固定 16px 标题和 13px副标题，700px 时两段各保持单行；390px 仍沿用 15px 标题和隐藏
  副标题，1024px 仍使用默认桌面字号。没有使用 viewport-width 字号缩放。
- 1024/768/700 实测顶栏均为 141px，Run 与 Metrics 垂直中心差不超过 2px，二者边界不重叠；Analysis Workspace
  y=159px，document scrollWidth 分别严格等于 1024/768/700。699px 按设计切回 211px 堆叠，390px 维持 201px，
  两者同样无页面级横向溢出。
- 新增中间视口 Playwright 几何门禁，逐宽度读取 topbar、run-status、run-meta、workspace 的真实 DOMRect；同时
  复跑 390px touch/Axe、窄屏 Drawer 和 1440px Inspector 专项。700、768、1024 最终 Chromium 截图确认品牌、
  指标、tabs、Timeline 与 token 无遮挡，主分析内容比旧布局提前约 60–70px 出现。
- 完整功能 E2E 增至 61 passed，production 性能套件 4 passed；production 主入口保持 238.46 kB
  （gzip 59.90 kB），CSS 122.38 kB（gzip 22.42 kB）。TypeScript、production build 和 `git diff --check`
  通过，2 秒首屏、20 万 cell、四类大型专用矩阵及 40 次视图资源增长门槛均未回退。

### 2.39 320–380px 超窄屏可视化操作收口（2026-07-13）

- 增加 320px 与 360px 真实 Chromium 视口检查。修复前 320px 页面实际宽 337px：Run selector
  从 x=10 延伸到 x=336，Run Library 图标被裁切，第三个 metric card 移出屏幕，Timeline
  metric 被压缩成仅可见的 `Saf`，已确认是元素 min-content 与 flex shrink 叠加造成。
- 在 `max-width:380px` 下明确将 Run 和 Metrics 限制为容器全宽；三张 metric card 使用
  `flex: 1 1 0` 和 `min-width:0`，收紧固定 padding/字号并允许标签安全换行。Run Library
  触发器同时固定 `flex-basis/width/height:44px`，不再在超窄 flex 行中缩到 40.16px。
- 在 `max-width:340px` 下将 Token Timeline toolbar 切为单列，metric selector 和 search result
  navigation 分行排布；这使 320px 下 metric selector 实测宽 238px，完整显示
  `Safety proxy`，且不与 44px 高的结果导航重叠。360px 以上继续使用紧凑同行布局。
- 最终几何验收：320px 下 document/run/meta 宽分别为 320/300/300px，三张 metric
  card 均完整位于 meta 内；340、360、380px 同样无页面级横向滚动，390px 既有移动节奏
  不变。320px 实景截图确认三项指标、Run Library、Timeline 与移动选择条均未裁切。
- 新增 Playwright 超窄屏门禁，逐宽度检查 Run/Metrics 边界、三项指标完整性、44×44px
  Quick selector/Run Library、移动选择条、Timeline 分行和 document scrollWidth；320px
  `.main-panel` Axe WCAG A/AA 零违规，Compare Drawer 等待入场动画后严格占满视口且无内部溢出。
- 定向超窄用例 1 passed，相关移动端用例 5 passed，完整功能 E2E 增至 62 passed；
  production 性能套件 4 passed。production 主入口保持 238.46 kB（gzip 59.90 kB），
  CSS 为 122.87 kB（gzip 22.50 kB）；TypeScript、production build 和 `git diff --check` 通过。

### 2.40 Attention / Attribution Profile Difference（2026-07-13）

- 补齐 23.6 中 Compare 只有单点 delta、无法判断整体分布形状的缺口。`PinnedEvidence` 新增可选、
  向后兼容的 `profile` 快照，使用 `schemaVersion: "1.0"`，明确区分
  `attention_source_profile` 和 `signed_attribution_profile`，并保存 token index/id/text、raw value、
  axis、signedness、原始点数和采样状态。
- Attention Pin 保存当前 head 在当前 destination 下的真实 causal source row；Attribution 仅对后端明确
  标记为 signed 的当前 method/layer 保存 token profile。unsigned proxy、缺失行和其他 View 不伪造序列。
- 长上下文快照最多 256 点；超限时稳定均匀采样，始终保留首点、尾点和当前选择 token，
  同时写入 `originalLength/sampled`。300-token E2E 验证导出恰为 256 点、首尾为 0/299
  且当前 token 不会被采样丢失，避免 4 个 Pin 无界占用 localStorage 与会话 JSON。
- Compare Drawer 新增 profile difference 图：统一零轴与统一纵向范围，青绿/洋红分别表示
  高于/低于 baseline，同时显示 aligned point count、mean absolute delta、peak delta 和对应
  token。全零曲线显式使用 `0 / zero delta / 0` 刻度，不用人工 epsilon 误导用户。
- 同 Sample profile 按精确 token index 对齐并要求至少 90% 覆盖；跨 Run 必须满足同 model/tokenizer、
  原始轴长相同、采样点数相同且每一点 token id/text 一致。单点可接受的 text-only alignment
  不会被扩大为整条曲线对比；不兼容项只显示具体原因，不绘制差值图。
- Comparison artifact 现在导出可复算的 `profile_difference`，包含对齐点数、平均/最大绝对差和
  逐点 baseline/item/delta；Analysis Session schema 保留完整 profile 并支持导出/导入回放。
  localStorage 读取也校验版本、kind、axis、signedness、点数、采样不变量与所有 finite value，
  手工篡改数据不会进入 Compare 运行路径。
- 390px 实景验收中 profile 区为 360px，Drawer/document scrollWidth 均严格为 390px；曲线、
  三项统计和图例无裁切。移动 Drawer Axe WCAG A/AA 零违规，forced-colors 保留曲线/零轴边界。
- 新增 4 项 profile E2E，Compare/会话相关专项 10 passed，完整功能 E2E 增至 66 passed，
  production 性能套件 4 passed。主入口为 240.71 kB（gzip 60.61 kB）；Compare 仍为独立 lazy chunk，
  为 17.65 kB（gzip 5.36 kB）；CSS 为 126.25 kB（gzip 23.05 kB）。
- 当前边界：attention row 和 signed attribution token profile 仅是一维分布；Intervention generation
  sequence diff 的序列契约见 2.41，独立二维 Attention matrix difference 契约见 2.42。

### 2.41 Intervention Generation Sequence Diff（2026-07-13）

- 补齐 23.6 中最后一项尚未落地的 generation diff。`PinnedEvidence` 新增可选、向后兼容的
  `generation` 快照，使用 `schemaVersion: "1.0"`；保存 original/steered continuation text、逐 token
  index/id/text、两侧 target logit 与 lexical proxy、服务端 diff opcodes、edit distance、changed 状态、
  source Run/Sample、layer/component/scale/position range、target、seed、token budget 和 temperature。
- 前端不重算或猜测序列 diff，直接消费 Intervention worker 已保存的 authoritative
  `equal / replace / insert / delete` opcodes。UI 任务入口将 new tokens 限制为 1–64；Pin/Session schema
  保留 256 token 上限，为未来 artifact 版本留出有界扩展空间，不进行会改写编辑语义的采样。
- Analysis Session Zod 契约对 generation 做跨字段校验：position range 必须严格递增，token index
  必须从 0 连续，输出长度不得超过 maxNewTokens，`generationChanged` 必须与 edit distance 一致；
  opcode 必须从两侧 cursor 0 开始连续无缝覆盖全序列，且每种 kind 的空/非空 span 必须合法。
- localStorage 启动路径使用同等运行时不变量检查；手工将 opcode `originalEnd` 篡改为 99
  后，重载会丢弃该坏 Pin 并保留其他 3 项，Compare 不崩溃。对导入 Session 做同样篡改则显示
  `Analysis session validation failed`，不改变当前分析状态。
- Compare Drawer 新增 `Intervention generation differences` 区，每个 Pin 展示固定四项摘要（edit
  distance、target-logit delta、token edits、changed/unchanged），并列 original/steered 文本与 token chips；
  equal/replace/insert/delete 同时使用文字、边框和不同语义底色，不仅依赖颜色。
- baseline-compatible 不只检查单点 metric：必须同 model/tokenizer、同 source Run/Sample、同 target token、
  同 seed/token budget/temperature，且 original generation 的每个 token id/text 一致。Layer、component 和
  scale 允许不同，它们是受控干预的比较变量。不兼容项仍显示自身权威 original→steered diff，
  但标记 `standalone diff` 并显示具体不兼容原因，不生成跨实验数值差。
- Comparison artifact 每项新增 `generation_difference`，导出 available、baseline compatibility/reason、
  edit distance、changed 状态与完整 opcodes；`items` 中的版本化快照可复算两侧 token 显示。
  Analysis Session 导出/导入完整回放 3 个干预 Pin 与 Compare baseline。
- E2E 从真实 SSE ready 任务链路出发，验证 baseline scale=1、同源同 seed scale=2 与异 seed
  三个实验；baseline 的 replace、scale 变体的 insert 和 seed 变体的 delete 均有真实 DOM 语义。
  只改 scale 项标记 baseline-compatible，改 seed 项标记 standalone，comparison JSON 与 session JSON 逐项校验。
- 1440px 实景中 generation 区为 775px，original/steered 两列完整展示；390px 下区块为
  360px，两侧自动改为单列，Drawer/document scrollWidth 均为 390px。移动 Drawer Axe WCAG A/AA
  零违规，forced-colors 下 token 边界保留。
- Intervention/Compare/Session 相关专项 10 passed，完整功能 E2E 66 passed，production 性能套件
  4 passed。主入口为 245.35 kB（gzip 61.76 kB）；Compare 仍为独立 lazy chunk，为
  23.67 kB（gzip 6.75 kB）；CSS 为 130.85 kB（gzip 23.73 kB）。
- 当前边界：Compare 现在可并排检查多个 authoritative original→steered generation diff 并安全标记
  实验参数兼容性，但不在浏览器中重算两个不同 steered output 之间的第二套 diff。
  Attention matrix difference 的有界二维 Pin payload 和 Canvas 可视化已在 2.42 完成。

### 2.42 Attention Matrix Difference（2026-07-13）

- 完成 23.6 剩余的二维 Compare 数据契约。`PinnedEvidence` 新增可选、向后兼容的 `matrix`
  快照，使用 `schemaVersion: "1.0" / kind: "attention_matrix"`；保存 head label、原始轴长、
  sampled 状态、有序 token index/id/text axis 与二维 raw probability。causal mask 使用 `null`，
  不与真实零 attention 混用。
- token 数不超过 64 时保存完整 N×N 矩阵；更长上下文稳定均匀采样为 64×64，强制保留首/尾 token
  与当前 source/destination 两个独立选择。300-token E2E 从 Canvas 键盘导航选中 source=3 /
  destination=7，导出恰为 64 个 axis point，0/299 首尾与 3/7 选择均未丢失。
- workspace chunk-v1 Attention 在 range hydration 下只有当前 block，不允许直接生成 matrix/profile 快照。
  新 Pin 先调用既有 `loadFullActiveRun()`，在完整 Run 中重建当前 head 的 row 和 matrix 后原子写入；
  加载失败显示 `Attention matrix pin failed` 且不留半成品。已有 Pin 的 Unpin 不触发完整加载。
- Analysis Session Zod 和 localStorage 运行时校验同时约束：axis 1–64 且严格递增，
  `originalSize/sampled` 不变量一致，values 必须为与 axis 等宽等高的方阵，unmasked cell 必须是
  `[0,1]` finite probability，masked cell 必须为 `null`，且 axis 必须包含 Pin 的 source/destination。
  将 `[destination 0][source 1]` mask 篡改为 0 时，Session 导入明确失败；localStorage 重载丢弃坏 Pin
  并保留其他证据。
- 同 Sample matrix 按精确 token index 对齐，并要求至少 90% 采样轴覆盖；跨 Run 必须同
  model/tokenizer、同 original size、同轴长，且每一轴点的 index/id/text 全部一致。text-only 或
  position-only 单点匹配不会被扩大为二维差值；不兼容项只显示具体原因，不渲染 Canvas。
- Compare Drawer 在单点 delta 之后新增 `Attention matrix difference`；所有可比项共享同一个以零为中心的
  洋红/青绿发散尺度，展示 mean/max absolute delta、peak source→destination、aligned size、
  full/sampled 状态和精确 baseline/item/delta cell detail，不仅用颜色表达。
- 差值矩阵复用 `SpecializedMatrixCanvas`，保留双向视口裁剪、DPR backing store、causal 导航、
  方向键/Home/End、live description、命中测试和 draw/hover 性能数据。共享组件新增默认为 true 的
  `showOverview` 开关；既有矩阵行为不变，Compare 关闭内部 overlay 后在滚动区上方独立渲染同一
  `MatrixOverviewNavigator`，避免 390px 下 Minimap 遮挡可见 cells。
- Comparison artifact 每项新增可复算的 `matrix_difference`，导出 reason、sampled、aligned axis、
  mean/max absolute delta 和逐 cell baseline/item/delta；Analysis Session 完整回放 matrix 快照与 Compare baseline。
- 20×20 E2E 修改 L1H1 destination 10 整行分布，验证非空 Canvas pixels、Home 键更新 cell detail、
  max delta > 0、comparison/session JSON 和移动 Axe；300-token fixture 增加第二个真实 head，完成 64×64
  sampled matrix Compare，Canvas `visibleCells` 大于 0 且小于 4096，没有创建全量 DOM grid。
- 1440px 实景中 matrix difference 区为 775px，20×20 矩阵、统计、detail 和图例完整；390px
  区块为 360px，Minimap 为 y=267–313 的独立 46px 导航条，矩阵从 y=321 开始，不再遮挡 cell。
  Drawer/document scrollWidth 均为 390px，Axe WCAG A/AA 零违规，forced-colors 保留 Canvas/图例边界。
- 完整功能 E2E 66 passed，production 性能套件 4 passed；20 万 cell、四类大型专用矩阵、2 秒首屏和
  40 次视图资源增长门槛均未回退。主入口为 250.06 kB（gzip 63.03 kB）；Compare 仍为独立
  lazy chunk，为 33.18 kB（gzip 8.88 kB）；`SpecializedMatrixCanvas` 为 5.54 kB（gzip 2.48 kB）；
  CSS 为 135.30 kB（gzip 24.35 kB）。
- 当前边界：对于超过 64 token 的上下文，Compare 显式标记 sampled 并导出原始轴长，不宣称展示未采样
  的 N×N 全矩阵。更大全量二维差值需依赖未来的二进制 range backend，不应塞入浏览器 Pin。

### 2.43 千级 MLP Neuron 搜索与虚拟 Canvas（2026-07-13）

- 针对大 neuron 集合做当前实现审计后，确认 `SpecializedMatrixCanvas` 已能按视口裁剪 token×neuron
  cells，但搜索过滤掉当前 neuron 时存在语义错位：Canvas selection 画在第一个匹配列，
  Summary、URL 和 Inspector 却仍显示旧 neuron。这会在研究者通过 ID 搜索数千列时造成直接误判。
- `MLPActivationMatrix` 现在对 neuron 列表预构建小写 ID/数字 searchable index，使用 React
  `useDeferredValue` 延后大数组过滤，保持文本输入立即响应。不再在每次键入时对每个 neuron ID
  重复 `toLowerCase`，而是在数据变化时统一建索引。
- 匹配集非空且不再包含当前 neuron 时，组件自动选择第一个精确匹配项，通过全局
  Selection Store 同步 URL、Canvas、Summary、Inspector 和 Pin 上下文。匹配数为 0 时则保留旧选择并显示
  `No retained neuron matches`，不把空结果替换成不存在的选择。
- Neuron Search label 新增 `visible/total` aria-live 结果状态；deferred 计算期间固定宽度显示 `...`，
  完成后例如 `1/2000`。状态使用 tabular numerals，不会因数字长度改变工具栏布局。
- production 专用矩阵 fixture 从 30 neurons 提升到 2,000 neurons × 100 tokens，即 200,000 个
  MLP cells。初始严格使用 Canvas，`aria-colcount=2000`且 DOM `.mlp-activation-cell=0`；搜索
  `1999` 将匹配缩为 1/2000 并原子同步到 `L0N1999`，清空搜索后仍保留该选择并自动
  横向滚到第 1,999 列，ArrowLeft 继续正常选择 `L0N1998`。
- 2,000-neuron 桌面实景中 MLP 区为 796px，自动滚到 N1999 时只绘制 425 个可见 cells；
  390px 下区块为 354px，工具栏自然单列，搜索结果计数、44px 操作、Summary 和 Canvas 无重叠，
  只绘制 238 个 cells；document scrollWidth 分别严格为 1440/390。
- 小样本 E2E 新增搜索后 URL/Summary 立即同步、0/8 无结果保留选择、MLP 区 Axe WCAG A/AA 零违规；
  production 大矩阵 E2E 验证非空 pixels、draw/hover <100ms、Minimap、精确搜索、选择恢复、键盘导航与移动宽度。
- 完整功能 E2E 66 passed，production 性能套件 4 passed；同一套件内的 20 万 residual cells、
  2 秒首屏和 40 次视图资源增长门槛均未回退。主入口保持 250.06 kB（gzip 63.02 kB）；
  MLP lazy chunk 为 9.28 kB（gzip 3.34 kB）；CSS 为 135.54 kB（gzip 24.39 kB）。
- 当前边界：本阶段证明前端对“已进入 ExplorerRun 的千级 neuron profile”具有虚拟渲染与搜索能力，
  不代表 bundled 生成器已导出模型全量 neuron。真正 10k–100k 列需要后端按 neuron 维分页/索引、
  safetensors/NPZ range 读取和取消协议，不能用单个 JSON response 硬塞到浏览器。

### 2.44 Attention 多 Head 小倍图与共享色阶（2026-07-13）

- 针对 8.2 的“多 head 小倍图”做现状审计后，确认原界面只有 Head select，研究者必须逐项切换后凭记忆
  比较，无法在当前 destination token 上直观看到不同 head 的结构和集中程度。
- `AttentionPatternMatrix` 新增同层 `Head overview`。所有保留 head 使用同一个全层最大 probability 色阶，
  每个 76×76 Canvas 缩略图显示完整 causal 形状；黄色横线标记当前 destination 行，棕色点标记当前
  source→destination pair。缩略图对长轴做像素有界采样，不创建 N×N DOM，也不改变主矩阵的精确值。
- 每个小倍图从当前 destination 的真实 attention row 计算归一化 Shannon entropy，并展示 peak source 的
  token position/text 与 raw peak probability。不同 head 的颜色、熵和峰值因此可以在同一视口直接比较；
  标题和图例继续明确标注 `raw probability`，不把 attention probability 表述为因果贡献。
- Head Overview 使用 roving pressed-button group；点击、方向键、Home/End 均复用全局 `selectHead`，原子同步
  URL、主矩阵、Summary、Inspector 和后续 Pin。聚合工具栏另用完整 radiogroup 表达 display mode；
  原 Head select 保留，所有入口始终读取同一个 selection。
- 1440px 实景中 Overview 区宽 762px，两项各 376.5px 且无需内部滚动；390px 下区宽 328px，每项固定
  238px，第二项保留可见提示并通过局部横向 scroll/snap 切换，document scrollWidth 严格为 390px。
- 专项 E2E 验证 2 个 retained head、共享色阶、Canvas 非空且具有多个像素颜色、点击/键盘后的 URL 与
  pair selection 保持、移动几何和局部 Axe WCAG A/AA 零违规。辅助文字对比度在测试中从约 4.1:1
  修正到 AA 门槛以上；forced-colors 下 selected preview button 仍有系统 Highlight 描边与文字状态。
- 完整功能 E2E 67 passed，production 性能套件 4 passed；20 万 residual/MLP cells、2 秒首屏和 40 次
  视图资源增长门槛均未回退。主入口保持 250.06 kB（gzip 63.02 kB）；Attention lazy chunk 为
  12.33 kB（gzip 4.23 kB）；CSS 为 138.51 kB（gzip 24.92 kB）。
- 当前边界：本阶段只比较 artifact 中当前层已保留的 heads；bundled 数据仍为每层至多 3 个 head。
  全模型 head 排序仍需相应 artifact；retained-head cellwise difference 已在 2.50 按显式减法契约完成，
  明确公式与完整 layer 契约的 retained-head rollout 已在 2.54 完成，两者均不代表全模型比较。

### 2.45 Retained-Head Mean / Max / Entropy 聚合（2026-07-13）

- 完成 8.2 的 `mean/max` 与 `entropy-weighted` 聚合。Display segmented control 提供 Head、Mean、Max、
  Entropy 四种模式，并使用 radiogroup/roving tabindex；方向键、Home/End、点击和原 Head select 都更新
  同一个全局 selection。聚合 ID 稳定编码为 `aggregate:mean|max|entropy_weighted`，可写入 URL、Pin、
  Analysis Session 并跨刷新、Layer 切换恢复。
- 聚合仅使用当前层 artifact 中实际保留的 heads：Mean 为逐 cell 算术平均；Max 为逐 cell 最大 raw
  probability，不重新归一化整行；Entropy 为以 `1 / stored_head_entropy` 归一化权重的逐 cell 加权平均。
  计算结果 memoize 在稳定 layer-head 集合上，token/source 选择变化不会重复构造 N×N 聚合矩阵。
- 虚拟 head 保留参与计算的 `memberHeadIds`，并贯通主矩阵、pair summary、Attention distribution、Trace、
  Inspector、Evidence Pin、完整 artifact 回填、JSON export 和 Compare。原始 head 继续输出真实
  `blocks.L.attn.hook_pattern[H]`；聚合输出 `derived.attention.MODE[member ids]`，不会伪造单个 cache key。
- 聚合 provenance 固定为 `derived_proxy`，明确说明只覆盖 retained artifact heads，不代表全模型聚合或因果
  证据。三种聚合使用独立 metric（`attention_retained_*`）；例如 Mean 与 Max 可以并排检查，但 Compare
  显示 `Different metric; no delta.`，不会对不同算子生成误导差值。相同聚合仍可使用已有严格 token/matrix
  对齐进行跨 Run 比较。
- Attention 标题从“selected cached head probability”收敛为 head 或 retained-head aggregate 的
  destination×source values；Max 在 Inspector 中标为 `maximum retained-head probability`，不把其行误称为
  softmax distribution。Head Overview 在聚合模式下允许所有真实 head preview 均为未按下状态，不伪装单 head。
- 1440px 实景中 toolbar 为 762×108px，四个 mode 各 65×31px；390px 下 toolbar 为 328×290px，
  四项各 74×44px，Head、pair summary、viewport actions 无重叠，document scrollWidth 严格为 390px。
- 专项 E2E 使用人为分离的两个真实 head rows，逐项验证 mean/max/inverse-entropy 数值、URL、键盘首尾、
  跨 Layer 保持、Inspector source key、Pin profile/matrix、Session 刷新恢复、Compare 禁止异构 delta 和移动
  44px 触控；聚合态 Attention 区 Axe WCAG A/AA 零违规。完整功能 E2E 68 passed，production 性能套件
  4 passed。
- 最终生产构建：主入口 253.83 kB（gzip 64.34 kB）；Attention lazy chunk 13.82 kB（gzip 4.69 kB）；
  Compare lazy chunk 33.25 kB（gzip 8.91 kB）；CSS 139.27 kB（gzip 25.05 kB）。
- 当前边界：Entropy 使用 artifact 已存的 head-level entropy，而不是在浏览器重定义新的熵目标；Max 是
  cell-wise envelope，不保证每一 destination 行和为 1。真正全模型聚合仍需后端导出所有 head 或提供经过
  版本化验证的 aggregate artifact，当前 UI 不会把“至多 3 个 retained heads”冒充模型全部 heads。

### 2.46 Overview 结构化结论与 Evidence Map（2026-07-13）

- 完成第 6 节与 23.11 的结构化 Overview。原 `Current evidence` 单段结论卡升级为 Evidence map，固定展示
  Primary finding、Supporting evidence、Contradicting evidence、evidence class、exploratory confidence、
  Limitations 和 Recommended analysis；Overview 主分析区固定单列，避免在宽桌面被压进约 340px 侧栏。
- Primary finding 不再把当前选择都写成最高风险 token，而是对 artifact 全 token 的 run-relative safety
  proxy 做稳定排序，显示 `rank N of M`、score、token id、`derived proxy` 与 `exploratory`。文案明确其只定位
  待分析候选，不建立不安全行为或因果结论。
- Supporting/Contradicting 节点只使用当前 artifact 的精确数据：normalized residual direction 与 token
  attention proxy 按显式 0.5 中点分组；存在 exact patching cell 时按 causal effect 符号分组，并标为
  `causal evidence`。每个节点展示原值、方法边界并可直接进入 Residual、Attribution 或 Patching 视图，
  保留当前 token/layer selection。
- 当某一侧没有节点时使用斜纹缺失状态。尤其 `No contradictory measure is loaded; absence is not confirmation.`
  不会把“没有矛盾 artifact”冒充支持结论。局限区根据当前 run 动态说明 run-relative calibration、exact causal
  patch 是否缺失以及 target attribution 是否可用。
- Recommended analysis 提供 Inspect residual trajectory、Inspect/Run attribution 和 Inspect/Run causal
  patching 三个真实命令，依据 artifact 可用性改变动作名称和说明；点击走全局 view selection 与 URL，
  不维护 Overview 私有导航状态。
- 1440px 实景中 Evidence map 为 796×487px，三列 graph 为 762×242px；390px 下 map 为 354×1009px，
  graph 变为 finding→supporting→contradicting 单列，三个推荐操作均为 320×56px，document scrollWidth 严格
  为 390px。移动 scroll-margin 使 62px sticky action bar 底部停在 y=70，主发现从 y=82 开始，不再遮挡标题。
- 专项 E2E 覆盖默认 2 supporting / 0 contradicting、缺失不等于确认、3 项限制、3 项推荐、URL 路由与
  selection 保持；人工构造低 residual/attention proxy 与负 causal patch effect，验证 0 supporting /
  3 contradicting、causal 标记和值以及跳转精确 patch matrix。Evidence map Axe WCAG A/AA 零违规，7px
  metadata 对比度从 4.25:1 修正到门槛以上。
- 完整功能 E2E 70 passed，production 性能套件 4 passed；2 秒 Overview 首屏、20 万 cell 和 40 次视图资源
  增长门槛均未回退。最终生产构建：主入口 258.83 kB（gzip 65.80 kB）；vendor icons 24.64 kB
  （gzip 5.12 kB）；CSS 144.68 kB（gzip 25.94 kB）。
- 当前边界：0.5 只适用于 artifact 已声明的 normalized run-relative proxy，不用于 raw logits、概率或因果值；
  causal effect 只在 exact token/layer patch cell 存在时进入 graph。跨方法统计置信区间、人工结论编辑与
  图级 session 注释仍需要后续独立数据契约，当前前端不会推测。

### 2.47 Residual Target Logit / Rank 跨层轨迹（2026-07-13）

- 完成 7.2 中每层 target logit、selected observed-target rank 变化和 Layer×Target logit 的直接可视化。
  原 Logit Lens 仅按层纵向堆叠 top-k 卡片，研究者必须凭记忆比较；现在在精确明细前新增稳定高度的
  Target trajectory 概览，逐层卡片和 source key/provenance 保持不变。
- 左图随 Logit/Probability radiogroup 切换 target score；Probability 使用百分比坐标并在 delta 中标明
  percentage points。右图对原始整数 rank 仅做 `log10(rank)` 纵向显示，明确标注 `log display` 与
  `lower is better`；标题、rank path、best layer、layer rail aria-label 和 tooltip 始终保留原始 rank，
  不把对数坐标冒充数据值。
- 两图共享同一 Layer 轴。Layer rail 使用 radiogroup/roving tabindex，点击、方向键、Home/End 复用全局
  `selectLayer`，同步主 Layer selector、URL、Residual heatmap、Inspector 和下方精确 top-k 卡片；当前层用
  虚线 marker 与高对比实心点同时标记，不只依赖颜色。
- 小跨度数值使用自适应轴精度：坐标精度由当前 min-max span 决定，极小非零 delta 自动切换科学计数法。
  当前真实样本从两个均显示 `0.027` 修正为 `0.0267690 → 0.0267710`，摘要显示 `+2.00e-6`，曲线与数字
  不再矛盾；相同 rank 则保留水平线和 `#8,518 → #8,518`，不制造变化。
- 1440px 实景中 trajectory 为 762×260px，两图各 366×147px，Layer 按钮 34×31px；390px 下为
  320×467px，两图改为各 298×147px 单列，Layer 按钮统一 44×44px，document scrollWidth 严格为 390px。
- 专项 E2E 验证两个真实 SVG path、4 个 layer points、双 selected marker、Logit/Probability 键盘模式、
  Layer Home/End 的 URL/焦点同步、rank/best summary、移动触控和局部 Axe WCAG A/AA 零违规；副标题
  对比度从 4.4:1 修正到 AA 门槛以上。
- 完整功能 E2E 70 passed，production 性能套件 4 passed；2 秒首屏、20 万 cell 和 40 次视图资源门槛均
  未回退。主入口保持 258.83 kB（gzip 65.80 kB）；ResidualLogitLens lazy chunk 为 8.50 kB
  （gzip 2.91 kB）；CSS 为 147.82 kB（gzip 26.42 kB）。
- 当前边界：artifact 只存 observed target 的 exact rank 与每层 top-k predictions，没有全词表逐层 rank
  tensor，因此不能把本轨迹描述为完整 Layer×Vocabulary rank heatmap。LayerNorm 前后切换、cosine、完整
  residual decomposition 和 clean/corrupted delta 仍需新的 versioned artifact 字段，前端不从现有值推断。

### 2.48 MLP Neuron Activation Profile 与严格对比（2026-07-13）

- 完成 9.2 的 top activating tokens 与 activation profile 对比。MLP 主矩阵上方新增选中 neuron 的完整
  token 轴曲线，固定显示零基线、当前 token marker、signed raw 正负峰值和精确数值；Display 切换到
  absolute/normalized 时曲线同步使用对应显示指标，不把 raw、absolute 和 normalized 混为同一 profile。
- 曲线下方 token rail 使用 radiogroup/roving tabindex。点击、方向键、Home/End 与正负峰值按钮均复用
  全局 token selection，同步 URL、Matrix、Timeline、Inspector 和 Evidence；轨道使用 ResizeObserver 在
  token 变化、响应式宽度变化或设备旋转后把当前 token 滚到可视中央。
- Pin 新增版本化 `mlp_activation_profile` snapshot，记录 kind、axis、signedness、originalLength、采样状态、
  token id/text/index 与值。远端 partial hydration 状态下 Pin 会加载完整 artifact 并按 neuron ID 重建 profile，
  不把当前 token block 冒充完整轴；Session Zod schema 和 localStorage runtime validator 均接受并校验新 kind。
- Compare 使用既有严格规则：metric、normalization、evidence class 与 profile kind/signedness 必须一致；同 Run
  按精确 token index 对齐，跨 Run 要求 model/tokenizer 与逐点 token id/text 完全一致。兼容项显示 20 点
  MLP activation profile difference、mean |delta| 与 peak token，不兼容项只说明原因而不计算差值。
- 1440px 实景中 profile 为 762×310px；390px 下为 328×413px，图表 132px，token 按钮 60×56px，当前
  T10 自动居中且 document scrollWidth 严格为 390px。颜色对比经 Axe 修正到 WCAG AA，并为 forced-colors
  保留曲线、零线、选中 marker 和 token selected border 的非颜色编码。
- 专项 E2E 验证真实 profile path、20 个 token、正峰值导航、方向键焦点/URL、两个 neuron Pin、刷新恢复、
  20 点 Compare 差值、移动可视区/44px 触控与局部 Axe 零违规。完整功能 E2E 71 passed，production 性能
  套件 4 passed；20 万 MLP cells、2 秒首屏和资源增长门槛均未回退。
- 当前边界：profile 只覆盖 artifact 中 retained neurons，不能代表模型全部 neuron；目标 logit contribution、
  probe weight contribution、ablation effect 和 clustering 仍需各自版本化 artifact/方法契约，前端不会从
  activation magnitude 推断这些量。

### 2.49 Selected-Token Neuron 正负排名（2026-07-13）

- 完成 9.2 的 top positive/negative neurons。MLP selection summary 与 profile 之间新增 Neuron polarity
  ranking，严格按当前 layer、当前 selected token 的真实 signed raw activation 分组；正向从大到小、负向从
  小到大分别取前 5，不再用绝对值混排后让符号含义依赖颜色猜测。
- 每一项同时展示方向内 rank、neuron ID、精确 activation 和共享幅度尺度；正负幅度条使用不同方向与颜色，
  selected neuron 另有金色内边线、背景和 `aria-pressed`。某方向没有 retained activation 时明确显示空状态，
  不拿零值或另一方向补位。
- 两个列表各使用单一 roving keyboard 入口，方向键与 Home/End 更新全局 neuron selection、URL、矩阵列、
  profile、Summary 和 Inspector。排名选择会主动清空 neuron search；搜索同步 effect 在 deferred query 尚未
  落定时不重置 selection，修复“从过滤结果选排名后被旧 query 立即选回”的竞态。
- 语义结构使用标准 `ol > li > button`，列表和交互角色不互相覆盖。按钮的 pressed 状态、幅度条与选中边框
  在 forced-colors 下保留；文案固定说明这是 selected-token descriptive activation，不是 logit、probe 或
  causal contribution。
- 1440px 实景中排名区为 762×291px，正负双列并共享当前 token 尺度；390px 下为 328×282px，两方向改为
  各自局部横向列表，item 为 174×56px，document scrollWidth 严格为 390px。实际 fixture 在 T10 显示
  5 positive / 2 negative retained neurons，selected L1N0004 精确落在 negative rank 1。
- E2E 由真实 artifact 逐项重算排序与数量，验证首项 ID/value、search 清空、URL/profile 同步、方向键焦点、
  selected pressed state、移动 44px 触控与 MLP 全区 Axe WCAG A/AA 零违规。完整功能 E2E 71 passed，
  production 性能套件 4 passed；2,000-neuron / 200,000-cell MLP fixture 与 2 秒首屏均未回退。
- 最终生产构建：主入口 260.08 kB（gzip 66.05 kB）；MLP lazy chunk 15.80 kB（gzip 5.20 kB）；
  Compare lazy chunk 33.35 kB（gzip 8.93 kB）；CSS 154.48 kB（gzip 27.58 kB）。
- 当前边界：排名只覆盖 artifact retained neurons，不是全模型 top-k。跨 token 聚类、目标 logit contribution、
  probe contribution 与 causal ablation effect 仍缺独立 artifact/方法契约，继续保持未完成状态。

### 2.50 Retained Attention Head Difference Matrix（2026-07-13）

- 完成 8.2 的 head 差值矩阵。Attention Display 在 Head 后新增 Difference，严格定义为同一 layer、同一
  artifact 中 `selected retained head - baseline retained head` 的逐 destination×source raw probability delta；
  不重新归一化、不跨 token 对齐猜测，也不把差值解释为 attention rollout、attribution 或 causal effect。
- Difference 使用稳定虚拟 ID `difference:<selected>:<baseline>` 并安全编码 head ID，贯通全局 `head`
  selection、URL、刷新、Analysis Session、Layer 校验、Pin restore 和 Compare label。解析只接受两端不同的
  head；Session 恢复还要求两端在目标 layer 精确存在，失效上下文回退到真实 head。
- Toolbar 在差值模式明确拆成 Selected head 与 Baseline 两个 select，Baseline 禁止选择同一 head；更换
  selected 为原 baseline 时自动选择另一真实 head，保持有效减法。Display 使用 5 项 roving radiogroup，
  Home/End 仍落到 Head/Entropy；Head overview 同时以 Selected 和 Baseline 文本、边框方向和背景标记两端，
  点击 preview 只替换 minuend，不意外退出 Difference。
- 主矩阵使用共享 `max(abs(delta))` 发散色阶：正值青绿表示 selected 分配更多，负值洋红表示 baseline
  分配更多，零值中性灰，causal mask 继续斜纹，selected pair 继续金色轮廓。DOM 与 Canvas 路径使用同一
  公式；pair summary、tooltip、legend 和 aria-label 均显示 signed probability delta 与减法方向。
- Attention distribution 在差值模式按 `abs(delta)` 排序，但精确值和条形颜色保留正负；Trace、Evidence
  Summary、Inspector、JSON export、source key 与 provenance 统一标为 derived signed proxy。Metric 独立为
  `attention_retained_head_difference`，source key 为 `derived.attention.difference[A-B]`，不会与 raw
  probability 或 mean/max/entropy aggregate 计算差值。
- Pin 保存当前 destination row 的 versioned `attention_source_profile` 且 `signed=true`。远端 partial
  hydration 会先加载完整两端 head 再重建 profile。现有 `attention_matrix` snapshot 契约只允许 `[0,1]`
  probability，因此 signed difference 明确不写入该字段；Compare 对两个差值配置使用严格 metric、
  signedness 和 token 轴规则生成 row-profile delta，不伪造 probability matrix snapshot。
- 人工分离 fixture 在 D10 验证 H0-H1 的 S0=`+0.7000`、S1=`-0.7000`，反向配置符号完全翻转；E2E 同时
  覆盖差值 cell class、baseline swap、URL/刷新、键盘模式、derived source key、两个 signed Pin、Session
  导出、11 点 Compare、无 matrix snapshot、390px select/radio 44px 触控与全 Attention 区 Axe 零违规。
- 1440px 实景中 Head overview 清楚并列 Selected/Baseline，主矩阵保留完整 20×20 轴；390px 下 toolbar
  为 328×359px，两个 select 和 5 个 mode 全部单列可操作，document scrollWidth 严格为 390px。
- 完整功能 E2E 72 passed，production 性能套件 4 passed；100×100 Attention Canvas、2 秒首屏和 40 次
  视图资源增长门槛均未回退。最终生产构建：主入口 263.79 kB（gzip 66.97 kB）；Attention lazy chunk
  15.76 kB（gzip 5.29 kB）；Compare lazy chunk 33.43 kB（gzip 8.97 kB）；CSS 155.80 kB（gzip 27.78 kB）。
- 当前边界：Difference 只比较 artifact retained heads；全模型所有 head、跨 layer head mapping、ablation
  effect 与 SafetyHeadAttributor KL 仍需要各自版本化 artifact/方法契约。Retained-head rollout 见 2.54。

### 2.51 Attention Risk-Position 与 Explicit Monitor Markers（2026-07-13）

- 完成 8.2 的风险关键词位置标记，但不发明新的 risk threshold。组件对 artifact 已存 `token.risk` 做稳定
  run-relative 排序（score 降序、token index 破同分），只标出 top 3；`monitorHit=true` 作为独立 explicit
  marker 加入，即使不在 proxy top 3 也保留，二者不互相替代或混称。
- Head overview 与主矩阵之间新增 Risk-position markers rail。每项显示 token index/text、proxy rank、精确
  score 和 explicit monitor 状态；顶部实时报告 monitor hit 数，legend 明确 `run-relative proxy rank` 与
  `explicit monitor hit` 的差别，并固定说明 marker 只定位 token、不改变或解释 attention value。
- 每个 marker 提供两个 Lucide 图标按钮：定位为 source 或 destination。选择 source 大于当前 destination 时
  同步推进 destination；选择 destination 小于当前 source 时同步收敛 source，始终满足 causal
  `source <= destination`。按钮使用 `aria-pressed` 显示当前 pair，并复用全局 token/pair selection、URL、
  Timeline、Summary、Inspector 和矩阵高亮。
- DOM source/destination 两轴均显示 `R1/R2/R3` 与 `M` 文字，title 包含 rank、score 和 explicit hit；
  Canvas row/column label 使用相同 `D10·R1` / `10·R1` 后缀，因此大矩阵不会丢失位置语义。Proxy 使用红色
  实线、monitor 使用紫色虚线，可重叠；forced-colors 保留 article、action 和 legend 的形状编码。
- 默认真实 run 明确显示 T10=`proxy #1 · 1.000`、T17=`#2 · 0.881`、T1=`#3 · 0.846` 与
  `0 monitor hits`，不会因为提示词含 “monitor” 就伪造命中。专项 fixture 仅给 T18 设置
  `monitorHit=true`，验证它作为第 4 项显示 `outside proxy top 3 · explicit monitor hit`，top 3 不被挤掉。
- 1440px 实景中 marker rail 为 762×133px，三个 marker 同屏；390px 下为 328×164px，card 使用局部
  horizontal scroll/snap，source/destination 动作按钮为 44×44px，document scrollWidth 严格为 390px。
- 专项 E2E 验证 top-3 公式/顺序/数值、独立 monitor 项、DOM 双轴文字/title、source→destination causal
  调整、pressed 状态、URL、移动触控、局部 Axe WCAG A/AA 与 forced-colors。完整功能 E2E 73 passed，
  production 性能套件 4 passed；100-token Canvas 只新增固定 top-3 marker，不随 cell 数增长。
- 最终生产构建：主入口 263.79 kB（gzip 66.96 kB）；Attention lazy chunk 19.26 kB（gzip 6.25 kB）；
  vendor icons 25.69 kB（gzip 5.34 kB）；CSS 159.18 kB（gzip 28.29 kB）。
- 当前边界：run-relative risk proxy 不是校准安全概率；marker 不证明 attention head 对风险 token 的功能作用。
  Head ablation、SafetyHeadAttributor KL 与 causal explanation 仍需独立方法和 artifact；描述性的
  retained-head rollout 已在 2.54 完成。

### 2.52 Attention Incoming / Outgoing Edge Profiles（2026-07-13）

- 完成 8.1 的入边和出边切换。新增 Attention edge profile：Incoming 固定当前 destination，读取其
  destination row 中所有 `source <= destination`；Outgoing 固定当前 source，读取所有
  `destination >= source` 的同一 source column。两者都直接使用当前 raw head、retained aggregate 或
  head difference 的已显示矩阵，不创建第二套 attention 数值。
- `attentionEdgeMode` 进入统一 Selection Store，类型为 `incoming | outgoing`；Attention 视图使用
  `edge=incoming|outgoing` 深链接，离开视图删除参数。Analysis Session schema 对旧 1.0 文件缺字段时默认
  Incoming，新导出保存当前模式；Session sanitize、刷新与 Run replay 均复用同一状态。
- Edge direction 使用两项 radiogroup/roving tabindex，方向键与 Home/End 可切换。Token rail 也使用
  radiogroup：Incoming 点选择 source 并保持 destination，Outgoing 点选择 destination 并保持 source；
  左右/上下/Home/End 更新全局 pair、URL、Matrix、Timeline、Summary 和 Inspector，并把焦点移动到新点。
- Profile 对 raw/mean/max/entropy 显示从底部生长的共享尺度柱；head Difference 自动切换为零中线发散柱，
  正值表示 selected head 更多、负值表示 baseline 更多。每点保留 token index/text 与精确值，当前 pair
  使用金色边框和 `aria-checked`，ResizeObserver 在 pair 或响应式宽度变化后自动将当前点居中。
- 四项稳定摘要显示 profile sum/net delta、peak |value|、selected pair 与 eligible token 数。Incoming raw
  row sum 可以直接核对原 softmax row；Outgoing column sum 只称 `profile sum`，不误称归一化概率。Legend
  始终附带当前 head/aggregate/difference label，并明确它是 descriptive edge profile。
- 当前真实 L1H0/D10 Incoming 为 11 点、sum `1.0010`、peak `T0 · 0.0910`；切到 S1 Outgoing 为 19 点。
  1440px edge profile 为 762×245px；390px Outgoing 为 328×369px，mode 按钮至少 44px、token 点
  64×112px、当前 D10/D19 自动居中，document scrollWidth 严格为 390px。
- 专项 E2E 由 artifact 重算 Incoming sum/peak/selected value，验证 Outgoing point count、roving focus、
  pair/URL、End、`edge` 刷新、Session 导出、旧 Session 默认、移动可视区与 Axe WCAG A/AA；Difference
  fixture 额外验证 source 0/1 的 positive/negative signed bars。
- 完整功能 E2E 74 passed，production 性能套件 4 passed；edge derivation 为 O(tokens)，100-token Canvas、
  2 秒首屏和 40 次视图资源门槛均未回退。最终生产构建：主入口 264.28 kB（gzip 67.14 kB）；Attention
  lazy chunk 24.11 kB（gzip 7.37 kB）；CSS 163.28 kB（gzip 28.84 kB）。
- 当前边界：Outgoing column 是跨多个 destination query 的描述性切片，不是概率分布；edge profile 不建立
  head 功能、attribution 或 causal 结论。Rollout 与 ablation 仍需独立方法契约。

### 2.53 Persistent Attention Pair Value / Entropy Tooltip（2026-07-13）

- 完成 8.1 的 attention value 与 entropy tooltip。原 tooltip 只在 hover/focus 时显示 value，移出后退回
  `no cell focused`，与始终存在的全局 selected pair 矛盾；现在默认持续显示 selected pair，hover/focus
  matrix cell 时临时展示 focused cell，移出或 blur 后自动回到 selected pair。
- Tooltip 固定展示 source/destination token、六位精确 probability 或 signed probability delta、当前
  head/aggregate/difference label、交互状态、完整 source key、destination row entropy 与 source rank。
  `aria-label="Attention pair details"` 和 `aria-live=polite` 使键盘移动时读屏器获得同一证据上下文。
- Raw/mean/max/entropy aggregate 的 row entropy 对当前 destination 中所有 unmasked non-negative displayed
  values 重新归一化后按 `-Σ p log p` 计算 nats，与 Head overview 公式一致。Source rank 对 probability
  按 value 降序并用 token index 破同分；例如真实 L1H0/D10 为 `2.398 nats`，S1 为 `#2 / 11`。
- Head Difference 不对 signed delta row 伪算 entropy，而是按虚拟 ID 找到 selected 与 baseline 两个原始
  retained head，分别计算同一 destination row entropy，显示 `selected / baseline`，title 另给精确 ΔH。
  Source rank 则按 `abs(delta)` 排序，仍保留 cell 的正负值与减法方向。
- 人工 fixture 中 H0 row `[0.8, 0.2]` entropy=`0.500`，H1 row `[0.1, 0.9]` entropy=`0.325`；
  selected S1 显示 `-0.700000`、`#2 / 11`，hover S0 后切换为 `+0.700000`、`#1 / 11` 与
  `focused cell`，移出恢复 selected pair。公式与 UI 文本均由 E2E 重算验证。
- 1440px persistent tooltip 为 762×115px；390px Difference tooltip 为 328×183px、两列布局，完整
  entropy/source key 无页面横向溢出。既有 Attention 全区 Axe、移动端和 forced-colors 门禁继续通过。
- 完整功能 E2E 74 passed，production 性能套件 4 passed；entropy/rank 为 O(tokens) 当前 row 扫描，
  100×100 Canvas、2 秒首屏和资源增长门槛均未回退。生产构建：主入口 264.28 kB（gzip 67.14 kB）；
  Attention lazy chunk 25.81 kB（gzip 7.84 kB）；CSS 163.28 kB（gzip 28.84 kB）。
- 当前边界：entropy 描述 displayed destination row 的集中度，不是 head 功能、安全贡献或因果证据；
  Difference 的 ΔH 也只比较两个 retained heads，不代表全模型 head 集。

### 2.54 Retained Attention Rollout（2026-07-13）

- 完成 8.2 的 attention rollout，并把算法契约固定为 artifact-retained heads：每层先做
  `A_l = mean(retained heads at layer l)`，再做 `Â_l = row_normalize(A_l + I)`，最后按 layer 顺序计算
  `R_l = Â_l × R_(l-1)`，其中 `R_-1 = I`。矩阵乘法严格保留 causal 下三角；输出每个 destination
  row 仍为非负、和为 1 的 path-weight distribution。
- 新增稳定选择 ID `rollout:retained_mean_identity` 与 `AttentionRollout` 元数据，记录 fusion、identity
  residual、参与 layers 和全部 member head IDs。计算只接受目标 layer 及之前的完整 `run.layers` 集合；
  缺少任一前置 layer 时返回 unavailable，不把单层或缺层数据伪装成 rollout。
- Attention Display 现在提供 Head、Difference、Mean、Max、Rollout、Entropy 六种模式。Rollout 使用独立
  derived 状态、标题、legend 和 formula 文案；Head select 显示 `Derived display`，Head overview 不错误
  按下任何真实 head，但保留第一个 head 作为可键盘进入点。既有 Home/End 约定不变，End 仍到 Entropy。
- workspace chunk-v1 partial run 选择 Rollout 时自动加载完整 artifact，加载期间显示专用 status 和 Cancel；
  成功后才计算跨层结果，取消或失败回退当前层真实 head。专项 E2E 用可控 full-sample gate 验证点击
  Rollout 触发且只触发一次完整 sample 请求，禁止使用当前 range chunk 生成单层伪 rollout。
- 新增独立 metric `attention_retained_rollout_mean_identity`、derived source key
  `derived.attention.rollout.retained_mean_identity[...]` 和 provenance。Inspector、Trace、Evidence Summary、
  当前视图导出、URL、Session restore、Pin profile、bounded matrix snapshot 与 Compare label 全部贯通；
  文案明确它是 retained artifact 的描述性 path proxy，不是 full-model rollout、attribution 或 causal evidence。
- 精确 fixture 将 L0 所有 retained heads 设为 identity，L1/D10 设为 `S0=.8, S10=.2`；公式结果必须为
  `S0=.4, S10=.6`，L0 rollout 自环保持 `1.0`。E2E 同时覆盖 URL reload、键盘、Pin/Compare、session
  payload、390px 的六个 44px Display 控件、无横向溢出与 Attention 区 Axe WCAG A/AA 零违规。
- 完整功能 E2E 75 passed，production 性能套件 4 passed；100×100 Canvas、20 万 cell、2 秒首屏和
  40 次视图资源增长门槛均未回退。最终生产构建：主入口 268.77 kB（gzip 68.51 kB）；Attention lazy
  chunk 26.13 kB（gzip 7.99 kB）；CSS 163.28 kB（gzip 28.84 kB）。TypeScript、production build 和
  `git diff --check` 通过。
- 当前边界：这是客户端基于 artifact-retained heads 的 mean-fusion rollout；它不代表未保留的模型 head，
  不做 learned head weighting、gradient rollout、head ablation、SafetyHeadAttributor KL 或因果解释。

### 2.55 NLA Review Queue / Robust Norm Outliers（2026-07-13）

- 完成 10 节的 fidelity threshold 复核、activation norm outlier 标记和低保真警告。原 threshold 只改变
  heatmap 颜色，用户仍需逐格查找；现在新增紧凑 `NLA review queue`，持续显示当前 metric/threshold 下的
  low-fidelity 数量与 activation norm outlier 数量，并提供“最低 fidelity”和“norm outlier”一键定位。
- Low fidelity 严格服从当前显示 metric：Cosine/FVE 低于 minimum threshold，MSE 高于 maximum threshold；
  metric unavailable 不伪装成低 fidelity。切换 metric 会使用既有契约同步默认 threshold，手动 slider 变化
  会立即更新 review count、最差项和候选筛选，但不改变当前 layer/token selection。
- Activation norm outlier 使用当前 Run 已加载 available NLA rows 的 Tukey `Q1 - 1.5×IQR` /
  `Q3 + 1.5×IQR` fence；少于 4 行或 IQR 近零时不武断标记。它与 fidelity 是正交信号：矩阵 cell 使用
  双描边、tooltip 显示 `IQR outlier`、候选行显示文字 badge，颜色仍只编码 fidelity。
- Candidate review filter 提供 All、Low fidelity、Norm outlier 三段 roving radiogroup，方向键与 Home/End
  可操作；它只过滤下方 cached candidate 复核列表，不隐藏完整 Layer×Token×Component 矩阵。Explanation
  search 与 review mode 组合过滤，空状态区分无缓存、无文本匹配与当前 review 类别无结果。
- 精确 fixture 使用 cosine `[.95,.90,.85,.40,.92]` 与 activation norm `[1.0,1.1,.9,1.05,10]`，验证
  threshold `.8` 时只有 T4 低保真、IQR 只标 T10；同时覆盖一键 URL 定位、MSE threshold 重算、筛选键盘、
  tooltip、390px 全部 44px 操作、无横向溢出、forced-colors 双状态边界和全 NLA 区 Axe WCAG A/AA。
- 完整功能 E2E 76 passed，production 性能套件 4 passed；20 万 cell、2 秒首屏和 40 次视图资源增长门槛
  均未回退。最终生产构建：主入口 268.77 kB（gzip 68.51 kB）；NLA lazy chunk 15.13 kB
  （gzip 5.13 kB）；CSS 165.29 kB（gzip 29.19 kB）。TypeScript、production build 与
  `git diff --check` 通过。
- 当前边界：activation norm outlier 是当前已加载 NLA rows 的描述性 run-relative 统计，不是模型异常、
  安全风险或 causal effect；跨 Run 比较需要另行建立相同 profile/component 的尺度与分布契约。

### 2.56 NLA Exact Component Selection / Activation Context Links（2026-07-13）

- 修复 Layer×Token×Component 矩阵与全局 selection 契约不一致的问题。原 selection 只保存 token/layer，
  同一位置存在 `resid_post`、`attn_result`、`mlp_out` 多条记录时，Evidence、Inspector 和 Pin 会取数组
  第一行；现在新增强类型 `nlaComponent`，所有 NLA lookup 均严格匹配 token + layer + component。
- Matrix DOM/Canvas cell、row label、候选列表、Review Queue 一键定位与方向键导航都会提交 component；
  selected outline、roving tabindex 和 persistent tooltip 使用相同三元组。用户沿某 component 行移动到
  missing cell 时不会自动替换成该位置的其他 component，而是明确显示 no exact artifact。
- URL 在 NLA 视图写入 `nlaComponent`，离开 NLA 时清理该参数但在 selection 中保留，返回 NLA 可恢复；
  Analysis Session schema 对旧会话默认 `resid_post`，新会话完整导出/恢复 component。NLA Pin 使用精确
  component 参与稳定 ID、摘要和恢复，并保存当前 cosine/MSE/FVE metric 对应的真实值。
- 顶部 NLA summary、Exact evidence、Inspector cache key/source、reproduction payload 和 current-view export
  全部使用精确 component；没有匹配行时顶部显示 `n/a`，不再把 `undefined` 格式化成 `0.00`。Unavailable
  文案同时明确禁止 nearby token、layer 或 component substitution。
- Exact NLA evidence 新增紧凑 `Activation context` 操作组：Residual、Attention、MLP 三个入口保留当前
  token/layer，当前 NLA component 对应入口标记 `component context`，其余标记 `same token / layer`。
  桌面三列、390px 单列，按钮最小高度 48px，并提供独立图标、语义色边界、aria-label 与 forced-colors focus。
- 新增同 token/L1 三组件 fixture，分别使用 cosine `.91/.82/.73` 和不同 explanation/source，验证矩阵
  选择、URL deep link、刷新后 artifact 重载、Inspector、Pin 恢复、Session payload、跨视图返回、键盘焦点、
  390px 触控尺寸、无横向溢出和 NLA evidence Axe WCAG A/AA。另补 chunk hydration 缺行 summary 回归。
- 完整功能 E2E 77 passed，production 性能套件 4 passed；20 万 cell、2 秒首屏和 40 次视图资源增长门槛
  均未回退。最终生产构建：主入口 270.65 kB（gzip 69.05 kB）；NLA lazy chunk 15.54 kB
  （gzip 5.26 kB）；CSS 166.57 kB（gzip 29.40 kB）。TypeScript、production build、桌面/移动视觉检查、
  服务健康检查与 `git diff --check` 通过。
- 当前边界：Activation context 只把同一 token/layer 带到各诊断视图；Attention/MLP 视图展示 artifact
  中保留的 head/neuron 上下文，不等同于直接可视化 NLA decoder 输入向量，也不构成 causal attribution。

### 2.57 Attribution Method Snapshots / Accounting Audit（2026-07-13）

- 补齐 11 节的方法对照、baseline 展示和 attribution sum 检查。原 Attribution evidence 只列方法名称与
  signed/unsigned，用户切换前看不到同一 token 的候选值，也无法判断正负贡献如何抵消；现在方法目录显示
  selected token 的 exact layer/aggregate row、stored value、sign domain 和 evidence class。
- 方法快照严格使用 selected layer 的 exact row，只有显式 `layer < 0` aggregate row 才可跨层展示；无精确
  row 显示 `n/a`，unavailable 显示 `not run`。面板持续声明不同 method/normalization/scale 不生成直接 delta，
  避免把 residual projection、attention proxy、run-relative safety proxy 与 Integrated Gradients 混算。
- 新增 `Attribution accounting`。Signed 方法显示 positive sum、negative sum、net sum 与
  `1 - |net| / sum(|value|)` sign-cancellation ratio；unsigned 方法显示 stored mass、peak magnitude、
  selected-token share 与 `no sign semantics`。所有核算只在当前方法内部进行，不宣称 completeness 或因果充分性。
- 对 Integrated Gradients 优先使用 attribution job metadata 中与 token 轴等长的 finite `rawValues`，而非
  max-absolute normalized matrix values；同时展示 target response token/index、baseline、integration steps 和
  convergence delta。非 target-specific proxy 显示 `No target/baseline contract`，明确它只是 run-relative diagnostic。
- 方法快照保持两列桌面扫描结构，390px 改为单列；accounting 指标桌面四列、移动端 2×2，objective context
  自适应为单列信息流。辅助文字对比度经 Axe 修正到 WCAG AA，四个方法按钮移动端均不低于 44px，页面宽度
  实测 390/390，无新增横向溢出。
- 精确 IG fixture 使用 10 个 `+0.05` 与 10 个 `-0.025` raw values，验证 positive=`+0.5000`、
  negative=`-0.2500`、net=`+0.2500`、cancellation=`66.7%`，并核对 target `stairs / response[1]`、
  `pad_token` baseline、16 steps 与 `1.250e-3` convergence delta。Proxy fixture 覆盖 signed/unsigned 切换、
  URL、no-contract 提示、无跨尺度 delta、390px 触控和 Attribution evidence Axe WCAG A/AA。
- 完整功能 E2E 78 passed，production 性能套件 4 passed；20 万 cell、2 秒首屏和 40 次视图资源增长门槛
  均未回退。最终生产构建：主入口 274.49 kB（gzip 70.08 kB）；Attribution lazy matrix 9.65 kB
  （gzip 3.30 kB）；CSS 169.32 kB（gzip 29.76 kB）。TypeScript、production build、桌面/移动视觉检查
  和 `git diff --check` 通过。
- 当前边界：target response token 仍需通过 Attribution Job 重新选择并生成 derived Run；现有 artifact 只包含
  一个 target/baseline 契约。Sum/cancellation 是代数审计，不替代 Captum completeness delta、ablation 或
  跨方法校准。

### 2.58 MLP Activation-Profile Hierarchical Clustering（2026-07-13）

- 完成 9.2 的 neuron clustering，并使用维护中的 `ml-hclust@4.0.0` AGNES 实现，不在 React 主线程手写
  聚类核心。算法固定为 average-link agglomerative clustering，profile distance=`1 - |Pearson r|`；
  Minimum `|r|` slider 0.50–0.95 直接控制 dendrogram cut distance，默认 0.80。
- 聚类放入独立 module Web Worker；组件只提交 activation profiles 与 threshold，接收 cluster leaf indices、
  height 或显式 error。每次请求使用递增 id 丢弃 stale response，切换视图时 terminate Worker；loading、ready、
  error 均有独立 UI，不阻塞原 MLP matrix、search、ranking、profile 或 Pin。
- 为保持 2,000-neuron 场景可用，每层最多按 `maxAbsoluteActivation` 聚类 64 条 retained neurons；当前 neuron
  只有在不属于 baseline top-64 sample 时才替换最后一项，避免 sample 内键盘导航触发 Worker 重算。
  Coverage 明确显示 `clustered / retained` 和 `complete / sampled`，采样只影响聚类视图，不过滤完整矩阵。
- 完整 artifact 使用 full retained token axis；chunk-v1 partial artifact 只使用当前已加载、至少一个 retained
  neuron 非零的位置，并明确显示 `loaded positions only`。未加载稀疏零位不会静默冒充完整 profile 证据。
- 新增 `Neuron profile clusters`：每组显示 representative、member 数、mean `|r|`；member button 显示 neuron
  ID、带符号 Pearson r 和 `same direction / inverse`。因为 distance 使用 `|r|`，反向 profile 可进入同一形状簇，
  但 `r<0` 必须保留并显示 inverse，不能抹掉方向语义。点击与方向键/Home/End 可直接更新全局 neuron/URL。
- 桌面使用 cluster summary + 横向 member rail；390px 改为单列 cluster、2+1 coverage 布局与 132px member
  targets，所有 member 高度至少 44px。默认 bundled run 实测 8/8 neurons、20/20 tokens、1 group；桌面/移动
  截图无页面横向溢出，reduced-motion 关闭 worker spinner，forced-colors 保留 selected member 边界。
- 精确 fixture 使用 ramp、2×ramp、-ramp 与 alternating profiles：前三项必须同组，相关系数分别
  `+1.000/+1.000/-1.000`，alternating 保持 singleton；同时验证 inverse 文本、点击/键盘 URL 联动、390px、
  Axe WCAG A/AA。70-neuron fixture 验证 `64/70`、`sampled` 和单一同形 cluster，不允许无界 O(n²) 输入。
- 完整功能 E2E 79 passed，production 性能套件 4 passed；2,000-neuron/200,000-cell Canvas、2 秒首屏、
  40 次视图循环资源增长门槛均未回退。最终生产构建：主入口 274.52 kB（gzip 70.08 kB）；MLP lazy
  chunk 22.20 kB（gzip 7.12 kB）；独立 clustering Worker 78.16 kB；CSS 173.11 kB（gzip 30.36 kB）。
  TypeScript、production build、桌面/移动视觉检查、服务健康与 `git diff --check` 通过。
- 当前边界：cluster 只描述 artifact-retained activation shape，不代表功能语义、目标 logit contribution、
  probe weight 或 causal ablation。Absolute Pearson 会把同形反向响应放入同簇；跨 Run/Layer 聚类仍需 token
  对齐、相同缓存组件和统一采样契约。

### 2.59 Inspector Recommended Next Analysis / Focused Workflow Routing（2026-07-13）

- 补齐 14 节 Actions 与 23.5 P0 的“unavailable 状态提供具体下一步”。原 Inspector 只有 Pin、Compare、
  Context、Export，用户看到 `incompatible / not computed / failed` 后仍需自行猜测目标视图；现在根据
  `status + evidenceClass + current view` 生成最多三条 `Recommended next analysis` 命令。
- Loading/cancelled 不提供跳转以避免打断进行中的 hydration；Attribution not-computed 优先
  `Configure Integrated Gradients`，NLA incompatible 优先 `Configure NLA job`，Patching/Intervention 缺实验时
  优先对应配置。其他缺口先回 Overview；raw/derived proxy 优先 causal Patching、target Attribution 和 exact NLA；
  causal evidence 优先 Intervention、Overview 和 Attribution 复核。
- 推荐动作保留当前 Run/Sample、token、layer 和其他兼容 selection，只切换 view。Attribution、NLA、Patching、
  Intervention job roots 新增稳定 id/tabIndex；导航使用 bounded retry 等待 lazy panel 挂载，再 scroll + focus，
  移动端同时关闭 Inspector drawer。目标 panel 使用 3px focus outline，用户能确认命令实际落点。
- 推荐动作与 evidence-object 操作严格分区：Pin/Compare/Context/Export 仍排在 Actions 首屏顶部；推荐分析作为
  次级命令随后出现，不把“运行新实验”混成当前证据的导出或 Pin。1440×1000 实测基础 Actions bottom=856px，
  完整可见；推荐区从 875px 开始，可随页面继续滚动。
- 每个命令使用 Attribution、NLA、Patching、Intervention、Overview 对应 Lucide 图标和独立语义边界，按钮
  最小高度 48px；390px drawer 无横向溢出。可用 evidence 文案为 strengthen/challenge，缺口文案为 resolve gap，
  但不会宣称 job 可运行，真实 compatibility/preflight 仍由目标面板决定。
- 新增完整工作流 E2E：Attention proxy → `Run causal patching`，验证 view/token/layer 与 Patching job focus；
  NLA incompatible → Configure NLA job；IG not-computed → Configure Integrated Gradients；同时覆盖普通 Tab 顺序、
  移动 drawer 自动关闭、全部 44px+ 触控、目标 focus、390px 宽度和推荐区 Axe WCAG A/AA。
- 完整功能 E2E 80 passed，production 性能套件 4 passed；2 秒首屏、20 万 cell 和 40 次视图资源增长门槛
  均未回退。最终生产构建：主入口 278.11 kB（gzip 71.11 kB）；CSS 174.54 kB（gzip 30.60 kB）；
  job lazy chunks 仅因 anchor 增加约 0.03 kB。TypeScript、production build、桌面/移动视觉检查、服务健康
  与 `git diff --check` 通过。
- 当前边界：推荐动作是基于 evidence class/status 的工作流路由，不是模型自动决策或实验适用性证明；按钮
  不自动提交 job、不绕过 gated confirmation，也不会把 preflight failure 改写成可运行状态。

### 2.60 Browser History / Complete Analysis Context Restore（2026-07-14）

- 完成 23.1 P0 的浏览器前进/后退验收。原 selection 与 Run Library 虽然会把状态写入 URL，但统一使用
  `replaceState` 且没有 `popstate` 恢复；用户连续切换 View、Token、Layer 或 Run 后，浏览器后退无法回到上一
  分析上下文。现在用户主动选择使用 `pushState`，初始化、URL canonicalization 与依赖项纠正使用
  `replaceState`，hover 与 Pin toggle 不写历史。
- Selection Store 现在从当前 URL 恢复 view、token/source/target、range、layer、head、neuron、track、metric、
  normalization、attention edge mode 和 NLA component，同时保留本地 pinned evidence。后退/前进会恢复 URL 与
  tab、timeline、layer selector、matrix、Summary 和 Inspector 的真实选中态，不只是改变地址栏。
- Run Library 明确拥有 `run/sample` 历史：bundled、local import 和 workspace API Run 切换均形成单一历史节点；
  workspace sample 只在成功加载后提交新 URL，浏览器返回已加载 workspace Run 时复用内存记录，不重复下载。
  快速切换会取消旧 sample 请求，避免旧响应覆盖新上下文。
- 自动 fallback head、neuron、attribution track 和 rollout 取消后的 head 校正改用 replace，避免一次用户操作产生
  多个无意义历史节点。专项 E2E 通过连续三次后退精确回到初始 View/Token/Layer，反向三次前进再恢复终态，
  直接约束历史栈没有被内部纠正污染。
- 同 `runId + sampleId` 的重新导入被定义为数据刷新而非 Run 导航：更新来源与 artifact 内容时保留当前 selection
  和 NLA exact component，不清空 URL、不新增历史节点；真正跨 Run 导入仍重置不兼容的局部 selection。
- 新增桌面同 Run、local cross-Run、workspace API cross-Run 与 390px 移动端四条完整历史回归；workspace 测试
  同时断言前进恢复后 sample request 总数仍为 1。完整功能 E2E 84 passed，production 性能套件 4 passed；
  2 秒首屏、20 万 cell 与 40 次视图资源增长门槛均未回退。最终 production build：主入口 279.60 kB
  （gzip 71.61 kB）；CSS 174.54 kB（gzip 30.60 kB）；TypeScript 与 production build 通过。
- 当前边界：历史记录保存的是可分享的 URL selection，不包含 drawer 开关、hover、tooltip 或未提交的 job 表单；
  已从 Run Library 删除的本地 Run 无法通过旧的浏览器历史重新构造，返回时仍以当前可用 Run 为准。

### 2.61 Context Change Confirmation / Accessible Live Feedback（2026-07-14）

- 完成 23.1 P0 的“改变分析上下文时显示明确反馈”。原有 tab、Timeline、Layer、Inspector 和 URL 虽会同步，
  但在长页面、密集矩阵、键盘导航和浏览器历史恢复后没有统一确认；现在 View、Token/Range、Layer、Metric、
  Normalization、Attention pair/head/edge、MLP neuron、NLA component 与 Attribution method 变化都会生成同一语法的
  `Context updated` 摘要。
- 摘要使用当前已解析的真实 selection，而不是点击事件参数：Attention 显示 source→destination、token 文本、head、
  incoming/outgoing、metric 和 normalization；MLP/NLA/Attribution 显示各自精确对象。自动 fallback head/neuron/track
  不会产生中间错误提示，快速连续操作在 60ms 内合并为最终有效状态。
- App 级通知状态跨 `ExplorerWorkspace` 的 keyed Run remount 保留；bundled、local import、workspace API、浏览器
  后退/前进和删除当前本地 Run 都能在真正完成切换后显示 `Run changed`，远端 loading 期间不会提前宣称已切换。
- 可视提示不抢焦点、不可点击、1900ms 自动退出，z-index 低于所有 modal/drawer。桌面固定在底部安全区，实测
  1440×900 为 411×44；390×844 为 358px 宽，移动端采用“图标 + 小状态标签 + 最多两行正文”，不会制造横向滚动。
- 无障碍播报与视觉层分离：永久 visually-hidden `role=log + aria-live=polite + aria-atomic` 输出完整上下文，视觉层
  `aria-hidden`，不会与各视图已有 `role=status` 任务状态冲突。forced-colors 使用 Canvas/CanvasText，
  prefers-reduced-motion 关闭入场 transition。
- 新增桌面快速 View/Token/Layer 合并、历史恢复、自动退出，以及移动跨 Run、安全区、44px、无横向溢出和
  Axe WCAG A/AA 两条专项 E2E。完整功能 E2E 86 passed，production 性能套件 4 passed；2 秒首屏、20 万 cell、
  40 次视图循环的 heap/DOM/listener/canvas/mark 门槛均未回退。最终 production build：主入口 282.13 kB
  （gzip 72.34 kB）；CSS 176.16 kB（gzip 30.97 kB）；TypeScript 与 production build 通过。
- 当前边界：hover、tooltip、drawer 开关、Pin toggle 和未提交表单不属于分析上下文，不触发全局提示；通知只确认
  已生效的本地状态，不把 job compatibility、数据完整性或因果有效性写成成功结论。

### 2.62 Run Source Conflict Resolution / Provenance Transparency（2026-07-14）

- 完成 23.2 P0 的同 key 来源冲突解释。原 Run Library 用 `[bundled, browser import/generated, workspace]`
  顺序静默丢弃重复 `runId + sampleId`，界面只能看到胜出记录；现在唯一 Run 仍保持去重，但状态层会保留每个
  `sourceAlternative` 的 source type/name、artifact id、更新时间、model、token/layer 数和是否已加载。
- 明确并可视化固定优先级 `Bundled → browser artifact → workspace API`，保持既有保守数据选择不变。Active Run
  使用 Package/Upload/Sparkles/Database 图标加文字显示来源和 `N sources`；冲突详情列出 selected 与 lower priority
  候选，并明确“不同 artifact 的值永不混合”。
- 候选来源若 model、token count 或 layer count 与胜出 artifact 不同，会显示独立 `metadata differs`，但不会请求、
  拼接或用低优先级数据补齐当前 Run。专项 bundled/workspace fixture 故意声明 27 vs 20 tokens，验证仍使用 bundled
  20-token 数据且 workspace sample request 数为 0。
- 被遮蔽来源不再从发现界面消失：bundled 选中但存在 workspace duplicate 时仍进入 external Run browser；搜索会匹配
  alternative 的 source name/model/type，Workspace/Imported/Generated filter 也会按任一候选来源命中。Recent Run
  使用紧凑 `N sources · using X over Y` 摘要，长 Run ID 从开头显示并在末尾截断。
- 移动 Run Library 复用完全相同的 resolution；summary 和每个 candidate 最小 44px，390×844 实测宽度 332px、
  document scrollWidth 390。新增来源组合色的 WCAG AA 修正，移除冲突计数透明度，并提升 8–9px metadata 对比度；
  Run Library 局部 Axe WCAG A/AA 零违规。
- 新增 `bundled > workspace` 桌面与 `browser local > workspace` 移动两条 E2E，同时覆盖单一 selector option、
  metadata mismatch、source filter/search、零远端 sample 请求、触控尺寸和无障碍。完整功能 E2E 88 passed，
  production 性能套件 4 passed；千级 Run selector、2 秒首屏、20 万 cell 和 40 次视图资源门槛均未回退。
  最终 production build：主入口 285.38 kB（gzip 73.30 kB）；CSS 179.25 kB（gzip 31.57 kB）。
- 当前边界：来源优先级由平台固定，冲突详情用于追溯而非同 key 手动切源；研究者若要并排比较不同 artifact，必须使用
  不同 run/sample identity，避免 URL、Pin、Compare 和 provenance 在同一 key 下产生歧义。

### 2.63 Two-Axis Matrix Pan / Complete Viewport Reset（2026-07-14）

- 深化 23.3 P0 的统一矩阵手势。审计确认通用和专用矩阵都已有 Reset 按钮与 double-click 入口，但 Pan 实际只记录
  `clientX/scrollLeft`，Reset 也只恢复水平轴；长 token/layer/neuron Canvas 纵向滚动后仍停在旧位置，视觉上并未真正
  “恢复视口”。
- `useMatrixViewport` 共享路径和通用 `MatrixHeatmap` 现在同时记录 pointer `startX/startY` 与 `scrollLeft/scrollTop`，
  拖拽使用二维欧氏距离判断是否发生有效 Pan，并同步更新 X/Y。DOM 小矩阵没有纵向 overflow 时行为自然退化为原水平
  Pan，不建立第二套交互。
- Pan 起点移至 viewport `onPointerDownCapture`：在 Pan 模式中先阻断子 Canvas/cell 的 pointer-down，避免专用 Canvas
  先提交 cell selection、通用 DOM 先启动 token brush 后才开始平移。拖拽结束后的 click capture 继续抑制合成 click；
  Select 模式的单击、Shift anchor、Ctrl/Cmd Pin、brush 和键盘导航保持原契约。
- Reset 按钮与 double-click 现在同时恢复 `scrollLeft=0 / scrollTop=0`、初始 cell size、Select mode 和 manual fit；
  Fit to width 仍只改变宽度与水平位置，不意外跳动用户当前纵向阅读位置。Pan/Reset 不改写 token/layer/head/neuron、
  selection URL 或 evidence context。
- Production 大矩阵门禁新增真实对角拖拽：Residual 2000×100（20 万 cells）与 Attention 100×100 Canvas 均验证
  两轴 `scroll > 0`、URL byte-for-byte 不变、double-click 后两轴归零并回 Select；390×844 Attention 另验证显式 Pan
  与 Reset 按钮在窄屏保持相同语义且无页面横向溢出。
- 现有 DOM pan、brush、keyboard、anchor/Pin、统一 specialized controls 与移动触控 6 项相邻回归通过。完整功能
  E2E 88 passed，production 性能套件 4 passed；2 秒首屏、hover <100ms、可见 cells、40 次视图循环资源门槛均未
  回退。最终 production build：主入口 285.68 kB（gzip 73.38 kB）；CSS 179.25 kB（gzip 31.57 kB）。
- 当前边界：二维拖拽仅在用户明确选择 Pan mode 时接管触控/鼠标，Select mode 继续优先 cell、brush 与页面滚动；
  double-click reset 不清除全局 selection，只恢复矩阵 viewport 与通用矩阵的局部 range/anchor 语义。

### 2.64 Run Recency / Complete Recent-Run Metadata（2026-07-14）

- 完成 23.2 P0 的“最近使用项”语义。原 Run browser 虽名为 recent，实际只沿用 bundled/browser/workspace 合并顺序，
  刷新后也不知道研究者最近打开过什么；现在浏览器按“已打开 Run 的 last-used 降序 → 未打开 Run 的 artifact
  更新时间降序”排列，真正最近使用的上下文稳定出现在首位。
- 新增浏览器本地 usage index，以 `runId + sampleId` 为唯一键，仅在 Run 已解析并成为当前 `activeRecord` 后写入时间。
  workspace discovery、远端 sample loading、取消和失败都不会被误记为已打开；索引按时间裁剪至最近 100 项，避免
  长期使用后 localStorage 无界增长。
- 最近 Run 卡片补齐 sample id、model、token count、layer count、实际 source name、Opened 与 Updated。时间使用语义化
  `<time datetime>` 和固定 UTC 紧凑格式，未打开/未知状态明确写出，不再用空白暗示数据缺失；来源冲突时仍只展示
  胜出 artifact 的维度和更新时间，并保留 2.62 的 `using X over Y` 解释。
- 最近排序只作用于 Run browser，不改变 Quick run selector 与完整 selector 的稳定顺序，避免远程索引刷新后键盘选择项
  跳位。重新导入同 key artifact 会更新 Updated，但不会伪造 Opened；只有实际切换完成才更新 last-used。
- 390×844 移动抽屉沿用同一信息层级，recent card 主操作高度至少 74px，Run、样本/模型、维度/来源、打开/更新时间
  分为四个可扫描层级；实测无横向滚动，Run Library 局部 Axe WCAG A/AA 零违规。桌面常驻侧栏与移动底部抽屉均完成
  截图验收，长标识继续使用可预测截断而不挤压状态徽章。
- 新增三条 workspace Run 的更新时间初始排序、实际打开后置顶、切回 bundled 后仍保持、刷新后从 localStorage 恢复，
  并断言完整 metadata、UTC datetime 和 storage key；相邻 source conflict、千级 selector、搜索分页、导入持久化回归
  同时通过。完整功能 E2E 89 passed，production 性能套件 4 passed；2 秒首屏、20 万 cell 与 40 次视图资源增长门槛
  均未回退。最终 production build：主入口 287.48 kB（gzip 73.87 kB）；CSS 180.06 kB（gzip 31.73 kB）。
- 当前边界：最近记录属于当前浏览器 profile/device 的个人工作上下文，不跨设备同步，也不写回只读 workspace API；
  清理站点数据会清除 Opened 顺序，此时列表自然回退到 artifact Updated 排序。平台不记录 hover、搜索命中或后台预取，
  避免把“被发现”误写成“被使用”。

### 2.65 Time-Aware Run Search / Structured Artifact Diagnostics（2026-07-14）

- 完成 23.2 P0 的时间搜索缺口。Run browser 搜索现在除 run id、sample id、model、source type/name 外，也索引
  Opened、Updated 和冲突候选来源的更新时间；同一时间同时提供原始值、canonical ISO、UTC long form 与卡片紧凑
  `MM-DD HH:mm UTC`，研究者可直接按日期或精确 UTC 时间定位 Run，不改变 source filter、最近排序或 selector 顺序。
- Artifact diagnostic 从 `path + message` 字符串升级为结构化对象：`path / issueType / expected / actual / message`。
  unsupported schema version、invalid JSON、Zod invalid type/value/format/size/union/key/element 和 custom refinement 使用
  可追溯错误类型；Analysis Session 校验复用同一诊断语法，不再维护第二套模糊错误文本。
- Zod 公开 issue 不包含输入值，因此 formatter 显式接收原始 artifact，并沿 issue path 安全读取实际字段。缺字段显示
  `missing`，数组显示真实 length，对象只显示 key 数和有限 key preview，字符串限制长度；矩阵 shape 错误可明确对照
  `Expected 20×20 destination×source matrix / Actual array(length 19)`，而不会把所有错误误报为 missing。
- Run Library 错误区使用语义化有序列表、code path/type 和 Expected/Actual definition list。多错误只在诊断区内部纵向滚动，
  当前 Run、Workspace 状态、搜索和本地可用数据保持可见；错误导入不会添加 selector option、切换 Run 或清空当前分析。
- 桌面窄侧栏和 390×844 drawer 均完成视觉验收；长 `unsupported_schema_version` 实测 container/client scrollWidth 相等，
  无隐藏横向溢出。移动错误区宽度不超过 drawer，document scrollWidth 保持 390，局部 Axe WCAG A/AA 零违规。
- E2E 新增 JSON parse、未来 schema、缺失 tokens 与 19×20 matrix 四类诊断的 path/type/expected/actual 精确断言，另覆盖
  raw ISO 与紧凑 UTC 日期搜索、刷新后的 last-used 搜索，以及错误前后 active selector 不变。完整功能 E2E 89 passed，
  production 性能套件 4 passed；2 秒首屏、20 万 cell 与 40 次视图资源增长门槛均未回退。最终 production build：
  主入口 289.94 kB（gzip 74.68 kB）；CSS 181.37 kB（gzip 32.00 kB）。
- 当前边界：单次最多展示前 12 条 schema issue，防止损坏 artifact 生成无界 UI；Actual 只做类型/shape/有限预览，
  不在错误面板复制完整用户数据。诊断用于解释导入拒绝原因，不自动修复、不部分接纳，也不改变原校验规则。

### 2.66 Workspace Failure Semantics / Mobile Recovery Controls（2026-07-14）

- 完成 23.2 P0 的后端状态语义。原统一六态已能 Cancel/Retry，但所有非取消失败的主标签都写成
  `Workspace data error`，用户必须阅读 detail 才能判断 API 是否离线；现在 error 状态额外携带
  `offline / api / validation / unknown` 原因，主标签分别显示 `Workspace offline / Workspace API error /
  Workspace schema error / Workspace data error`。
- 状态机仍保持 2.8 的 `idle / loading / ready / empty / error / cancelled` 契约，failure kind 只是 error 的领域原因，
  不制造第七套异步状态。Fetch transport `TypeError` 归为 offline，`ExplorerApiError` 的 `invalid_*` 归为 validation，
  HTTP/sample/chunk 等服务错误归为 API；未知异常保守归为 data error。
- 每次 Retry 进入 connecting 时立即清除旧 failure kind 和 diagnostics，成功、empty 或 Cancel 后也不保留旧 offline/error
  标签，避免连接恢复期间继续显示过期故障。AbortController、request id latest-wins、深链接等待和 partial hydration
  取消逻辑保持原契约。
- 新增完整恢复路径：先模拟 connection refused，确认 bundled Timeline 与 Retry 仍可用；离线状态直接导入并切换
  local artifact；随后服务返回错误 index schema，主状态切换为 schema error 但 local Run 与 prompt 不变；再次 Retry
  到 ready 后 workspace Run 无刷新加入 selector，当前 local context 仍保持。
- 移动 Run Library 的恢复操作同步改善：Close、Run selector、Import、Retry、搜索、来源筛选和分页全部提升至至少
  44px 触控高度，图标型 Close/Retry 同时达到 44×44px；桌面常驻侧栏仍保留原紧凑密度。390×844 实测无横向
  溢出，离线原因、诊断入口与当前 bundled Run 可同时出现在首屏，AsyncStatePanel 局部 Axe WCAG A/AA 零违规。
- 新增 offline→local import→invalid schema→ready 四阶段 E2E，并与 HTTP 503、cancel、empty、overlapping refresh、
  remote deep link、移动来源冲突、focus trap 和 touch controls 相邻回归。完整功能 E2E 90 passed，production 性能
  套件 4 passed；2 秒首屏、20 万 cell 与 40 次视图资源增长门槛均未回退。最终 production build：主入口
  290.29 kB（gzip 74.81 kB）；CSS 182.01 kB（gzip 32.12 kB）。
- 当前边界：offline 基于浏览器 fetch transport failure 判断；HTTP 503 表示服务可达但请求失败，因此显示 API error，
  不误报为离线。状态面板不自动循环重试，继续由用户显式 Retry，避免本地研究环境故障时产生后台请求风暴。

### 2.67 Browser Artifact Removal / Read-Only Source Protection（2026-07-14）

- 完成 23.2 P0 的删除语义。原 local/generated recent card 的垃圾桶会单击立即删除，且 generated Run 的 tooltip
  也错误写成 `Remove imported run`；现在垃圾桶只进入 `Remove browser artifact?` 确认流程，第一次操作不改变 records、
  URL、active context、localStorage 或 last-used index。
- 确认对话框明确显示 Run、Sample、Source、Type、token/layer shape，并直述“只删除当前 browser profile 的保存副本；
  workspace files 与 bundled package 不变”。Imported artifact 与 Generated result 使用不同 Type，不再把 job result 伪装成
  import；bundled 和 workspace record 从 DOM 到可访问树都没有 removal trigger。
- 删除当前 Run 时单独警示会返回 bundled Run；确认后沿用既有 replace history 语义，不制造指向已删除 artifact 的新历史
  节点。删除同时清理 `importedRuns.v1` 与对应 `runUsage.v1` key，重新导入同 identity 不会错误继承旧 Opened 时间。
- 对话框通过 portal 放在 workspace inert 区域之外，复用 `useModalDialog` 的焦点陷阱、Escape、背景关闭和 body scroll lock；
  初始焦点落在 Cancel。Cancel 后返回原垃圾桶；桌面确认后回到 Run selector；移动删除 active Run 触发 keyed workspace
  重建并关闭 drawer 时，焦点回到可见的 Open run library 按钮，不落到 body。
- 桌面与 390×844 均完成视觉验收：来源 metadata、删除范围和 active warning 在首屏可见；Close、Cancel、Remove 均至少
  44px，dialog 宽度不超过 358px、document 无横向溢出，dialog 局部 Axe WCAG A/AA 零违规。危险操作使用文字加
  Trash 图标和明确红色，不以颜色作为唯一信号。
- E2E 覆盖 local Cancel 不删除、focus/inert 恢复、移动确认、storage/usage 清理、active URL 回退、workspace/bundled
  零删除入口，以及 generated Type 文案。完整功能 E2E 90 passed（4 workers 稳定全跑），production 性能套件 4 passed；
  2 秒首屏、20 万 cell 与 40 次视图资源增长门槛均未回退。最终 production build：主入口 292.87 kB
  （gzip 75.53 kB）；CSS 184.37 kB（gzip 32.54 kB）。
- 当前边界：确认删除后不提供应用内 undo，因为 artifact payload 已从 browser storage 移除；用户仍可重新导入原 JSON
  或重新运行 job。此流程没有、也不会新增 workspace DELETE API，保持服务端 artifact 完全只读。

### 2.68 Sticky Matrix Axes / Protected Header Hit Area（2026-07-14）

- 深化 23.3 P0 的行列标题一致性。审计发现 DOM matrix 只有 axes-pinned 行标题会横向固定，且容器明确
  `overflow-y:hidden`；通用与专用 Canvas 又只在 `scrollTop < headerHeight` 时绘制列标题。长 DOM matrix 会拉长整页，
  大 Canvas 纵向滚动后则完全看不到当前 token/neuron column。
- DOM matrix 现在使用有上限的双轴 viewport：内容低于 `min(480px, 58vh)` 时保持原自然高度，较高矩阵才在内部滚动。
  corner 与 column label 固定在 top，开启 axes pin 后 corner/row label 同时固定在 left；小矩阵不增加空白高度，也不建立
  另一套滚动语法。
- 两套 Canvas renderer 将 column header 改为 cells 之后绘制的顶层 overlay，始终固定在 viewport `y=0`，并增加底部
  分隔线；selected column 使用独立浅青背景和深色文字，range column 继续使用琥珀语义。row label 的 Pin 开关、Canvas
  viewport virtualization、overview navigator 和 forced-colors 契约不变。
- 修正 sticky header 的 pointer hit-test：Canvas 顶部 header band 直接返回 no cell，不再在纵向滚动后把标题下方被遮住的
  row 误选为当前 cell。标题点击不会改变 layer/token/head/neuron、URL、range、Pin 或 Compare；键盘在 Canvas 上仍按
  原 selection 语义移动。
- 新增 80×20 DOM fixture（1600 cells，低于 Canvas threshold），在桌面和 390px 同时滚动 X/Y 后精确约束 corner top/left、
  column top、visible row left；长 token header 的原生 title 包含完整文本、position 与 token id。20 万 cell 通用 Canvas、
  100×100 Attention desktop/mobile production 测试新增 sticky marker、header click URL 不变和 scrollTop 保持断言。
- DOM 与 Canvas 均完成真实截图验收：纵向滚动到 L20/L50 后顶部 token index 和左侧 layer 仍同时可见，current token 10
  有独立背景；移动 viewport 内 overview、header 与 cells 无页面横向溢出。相邻 brush、keyboard、anchor/Pin、Pan/Reset、
  specialized controls 和窄屏 6 项回归通过。
- 完整功能 E2E 91 passed（4 workers 稳定全跑），production 性能套件 4 passed；2 秒首屏、20 万 cell、hover <100ms
  与 40 次视图资源增长门槛均未回退。最终 production build：主入口 293.05 kB（gzip 75.58 kB）；CSS 184.54 kB
  （gzip 32.56 kB）。
- 当前边界：本轮完成标题固定、DOM 长 token 完整 title 和 header hit protection；专用 Attention/MLP/Attribution/NLA
  的 persistent detail 已支持键盘 focus，但 token text/id/position 字段尚未完全统一，继续作为 23.3 tooltip metadata 子项。

### 2.69 Unified Specialized Token Metadata / Focus Details（2026-07-14）

- 完成 23.3 P0 的专用矩阵 token metadata。原 Attention detail 只有文本和 position，MLP 只有数字 position，
  Attribution 依赖 `tokens[index]`，NLA 又优先使用 artifact 内的独立 token 字符串；四个视图无法用同一字段确认
  当前 token，也全部缺少 token id。
- 新增共享 `MatrixTokenDetail`，以 TokenInfo.index 查找而非数组下标假设，统一输出完整 token text、role、position 与 id；
  token 缺失时明确显示 fallback text / unknown id，不静默借用相邻 token。长文本视觉上 ellipsis，原生 title 与可访问文本
  保留完整值。
- Attention 同时显示 source 与 destination 两份独立 metadata，不再只写两个裸 position；MLP、Attribution、NLA 使用同一
  `token position N · id X` 语法。NLA 即使 cached row.token 与当前 token axis 文本不同，也以当前 Run 的 TokenInfo 为主，
  row.token 只作为缺失时 fallback，避免跨 artifact 文本混淆。
- Attention source/destination、MLP token、Attribution token、NLA token 的 DOM header title 统一为
  `role position · id · text`，与 persistent detail 一致。Canvas 紧凑 header 继续只绘制可读的 index/neuron 标识，精确
  text/id/position 在下方 persistent panel 展示，不把长字符串塞进 cell overlay。
- detail panel 始终位于 matrix viewport 外，不跟随 pointer 浮动，因此天然避开鼠标、viewport 边缘和当前 cell；DOM cell
  focus 与 Canvas grid focus 都会更新相同 panel。新增长 token fixture 逐一验证 Attention、MLP、Attribution、NLA 的
  header title、鼠标/selected state 与键盘 focus，不需要 hover 才能读取精确 metadata。
- 390×844 NLA detail 实测宽度不超过 358px，长 token、指标、profile 与 explanation 均未溢出；四种 panel 完成截图
  验收。新增 Axe 检查同时发现并修复旧 9px tooltip 辅助文字 `4.37:1` 对比度，统一加深后 WCAG A/AA 零违规。
- Production 100×100 Attention、100×2000 MLP、30×100 Attribution/NLA Canvas fixture 使用超长 token 与固定 id，
  验证 focus detail 精确输出且 viewport-render/hover 门槛不回退。完整功能 E2E 92 passed（4 workers 稳定全跑），
  production 性能套件 4 passed；2 秒首屏、20 万 cell、hover <100ms 与 40 次视图资源增长门槛均通过。
  最终 production build：主入口 293.10 kB（gzip 75.60 kB）；共享 MatrixTokenDetail chunk 0.57 kB（gzip 0.38 kB）；
  CSS 184.70 kB（gzip 32.60 kB）。
- 当前边界：平台采用 persistent cell detail 而非跟随鼠标的浮层 tooltip，以保证研究数值可复制、键盘可读且不遮挡矩阵；
  browser 原生 title 只作为截断 axis label 的补充，不承担唯一证据展示职责。

### 2.70 Metric-Synchronous Color Domains / Numeric Legends（2026-07-14）

- 完成 23.3 P0 的色阶语义审计。发现 MLP 的 Display 虽能在 signed raw、absolute raw 和 normalized magnitude
  间切换数值，但 DOM cell、Canvas fill 与 legend 始终使用原始正负号的青绿/洋红发散色；absolute/normalized
  因而会错误暗示方向性。通用 residual heatmap 的 legend 也只有 Low/Mid/High，无法从颜色读出实际数值域。
- MLP 现在由同一 metric 判定同步驱动 DOM、Canvas、selected summary、Canvas accessible description、cell aria-label
  与 legend。signed raw 使用以 0 为中心的对称 `[-maxAbs, 0, +maxAbs]` 发散色阶；absolute raw 使用 `[0, maxAbs]`
  顺序色阶；normalized magnitude 使用固定 `[0, 0.5, 1]` 顺序色阶。非负指标统一为单向青色强度，不再继承 raw sign。
- legend 直接显示当前域的低/中/高数值以及 threshold 的实际 cutoff，并通过 `data-domain=diverging|sequential`
  暴露可测试语义。Threshold 继续定义为全矩阵 max-absolute 下的 normalized magnitude，切换 Display 时筛选集合不漂移；
  absolute 显示 raw cutoff，normalized 显示 0–1 cutoff。选中 token/neuron、URL 与键盘焦点语义在三种模式往返时保持稳定。
- selected summary 现在先显示当前 Display 的精确值，再保留 signed raw source；Canvas 的 live description 与每个 DOM
  cell aria-label 同时说明当前显示值和 raw source。persistent tooltip 继续并列保留 signed raw、absolute raw、normalized
  magnitude 与 cache key，避免颜色域切换丢失原始证据。
- 通用 MatrixHeatmap legend 改为数值端点：raw 使用当前可用 cells 的 min/mid/max，normalized 固定显示
  `0.000 / 0.500 / 1.000`，Unavailable 继续使用斜纹。Canvas、DOM 与 overview 已复核使用同一 normalization signal；
  Attention difference、Attribution signed、NLA unavailable 与 Patching signed/missing 的既有零点或斜纹契约未发现漂移。
- DOM fixture 新增 signed → absolute → normalized → signed 往返断言，覆盖颜色 class、domain、数值 legend、选择稳定、
  threshold 与 Axe WCAG A/AA；2000-neuron production Canvas fixture 覆盖 metric 重绘、live description、选择稳定和虚拟化。
  desktop 与 390×844 真实截图确认单向色阶清晰，legend 正常换行，页面横向溢出为 0。
- 完整功能 E2E 92 passed（4 workers），production 性能套件 4 passed；20 万 cell、专用 Canvas、2 秒首屏、hover
  与 40 次视图资源增长门槛均未回退。最终 production build：主入口 293.38 kB（gzip 75.68 kB）；
  MLPActivationMatrix chunk 23.05 kB（gzip 7.40 kB）；CSS 184.92 kB（gzip 32.64 kB）。
- 当前边界：`Neuron polarity ranking` 是固定的 signed raw 诊断，不随 Display 改成 magnitude 排名；标题、列标签和说明
  均明确 raw activation。若后续需要 magnitude ranking，应作为独立排序模式加入，而不是复用当前正负极性榜单。

### 2.71 Discoverable Narrow-Screen View Navigation（2026-07-14）

- 深化 23.1 P0 与 23.9 P1 的主视图可达性。真实 768px/390px 首屏审查发现 Analysis view tab strip 虽支持横向
  滑动和当前 tab 自动滚入视口，但没有任何可见的 overflow 提示；MLP、NLA、Patching、Intervention、Attribution
  会完全藏在右侧，新用户无法从界面判断还有更多视图。
- `WorkspaceTabs` 现在根据 `scrollLeft / clientWidth / scrollWidth` 维护 previous/next 状态，并通过 scroll listener
  与 ResizeObserver 在手势滚动、viewport 变化和 selected view 变化后实时更新。监听器随组件卸载清理，既有 lazy
  preload、roving tab、URL/history 和当前 tab 自动可见语义不变。
- 860px 以下新增 Lucide 左右箭头控制：仅对应方向仍有隐藏视图时出现，提供 44×44 touch target、title、aria-label
  与 aria-controls；点击按 72% 可视宽度移动，prefers-reduced-motion 下禁用 smooth behavior。桌面多列 tabs 不显示
  冗余箭头。
- 箭头占据独立 grid column，不覆盖或截断 tab 文本；只有单向可滚时只分配一侧 44px，同时可双向滚动时才分配两侧。
  初版 overlay 在 390px 横滑后会遮住 Attention 首字母，视觉审查后已移除该方案。
- 滚到最左/最右导致触发箭头消失时，焦点转移到对应端的可见 tab，避免键盘/辅助技术焦点落回 document body。
  滚动本身不改变 view、URL、token 或 layer；在末端 tab 上按 Enter 才执行正常 view selection。
- 新增 390px 与 768px E2E：验证初始 overflow 状态、44px 触控尺寸、scrollLeft、按钮与 tab strip 零重叠、
  滚动不改 URL、终点焦点接续、Enter 切换 Attribution、刷新后 selected tab 自动可见、document 零横向溢出，
  并对 main header 执行 Axe WCAG A/AA。两个断点均保存真实组件截图。
- 完整功能 E2E 93 passed（4 workers），production 性能套件 4 passed；20 万 cell、2 秒首屏、hover 与 40 次视图
  资源增长门槛均未回退。最终 production build：主入口 295.07 kB（gzip 76.24 kB）；CSS 185.83 kB
  （gzip 32.81 kB）。
- 当前边界：按钮按 viewport page 滚动，不逐 tab 跳转；精确单步切换继续由 tab focus 后的方向键承担。触控用户仍可
  直接 swipe，箭头是可发现性和可点击替代入口，不阻止原生横向手势。

### 2.72 Mobile Run / Sample Context Confirmation（2026-07-14）

- 完成 23.1 P0 的首屏上下文确认。真实 390px 审查发现 Sample selector 显示 `real-forward-cache-001`，但品牌下方
  的完整 Run ID 在 520px 以下被隐藏；移动用户能确认 Sample、View、Layer、Token，却无法在不打开 Run Library
  的情况下确认当前 Run。
- `run-status` 现在包含统一的 `run-status-selection`：520px 以下显示两行紧凑上下文，第一行以可见 `Run` 标签展示
  当前 runId，第二行以 `Sample` 标签承载原有 AdaptiveRunSelector。520px 以上继续由品牌副标题显示 runId，移动专用
  行隐藏，避免桌面重复信息。
- 长 Run ID 使用单行 ellipsis，但 `strong` 的 title 和 DOM 文本保留完整值；Sample 仍是真实原生 select 或千级数据
  下的 virtual combobox，不引入第二套选择状态。Run 切换、session replay、source priority 和 workspace lazy load
  继续复用原回调与 active record key。
- 调整 selector wrapper 后，layer count、Database 图标和 44×44 Run Library 按钮仍位于同一紧凑 status band；
  320px 最窄视口中 selector 仍有约 159px 可用宽度，完整 status 宽度 300px，不挤出 320px viewport。
- 320/360/390/520/768 真实截图验证：Run/Sample 标签、样本选择器、三项 run metric 和 Timeline 均在首屏，
  document scrollWidth 精确等于 viewport；768px 使用品牌副标题而不是移动重复行。320px topbar 与 main panel
  同时通过 Axe WCAG A/AA。
- 既有响应式 E2E 增加完整 runId title/文本、选中 sample option、移动标签、44px selector、Timeline y、桌面隐藏规则
  和品牌 runId 断言。完整功能 E2E 93 passed（4 workers），千级 selector、跨 Run session、source conflict 与移动
  Run Library 回归均通过；production 性能套件 4 passed。
- 最终 production build：主入口 295.43 kB（gzip 76.32 kB）；CSS 186.58 kB（gzip 32.96 kB）。
- 当前边界：320px 下长 runId 必然视觉截断，完整字符串通过 title/accessible DOM 和 Run Library 获取；不通过缩小字体
  或压缩 44px 操作目标强行展示全长，以免破坏可读性和触控性。

### 2.73 Specialized Matrix Space Pin / Truthful Keyboard Contract（2026-07-14）

- 深化 23.3 P0 与 23.9 P1 的矩阵操作一致性。审计发现共享 SpecializedMatrixCanvas 的 `aria-keyshortcuts`
  宣称支持 Enter，但实现只处理 Arrow/Home/End；同时计划要求 Space Pin，Attention、MLP、Attribution、NLA 的
  DOM/Canvas keyboard entry 均未实现，读屏声明与真实能力不一致。
- SpecializedMatrixCanvas 新增可选 `onPin`，通过 ref 使用最新回调；提供时 Space preventDefault/stopPropagation 后 Pin
  当前已提交 selection，快捷键声明为 Arrow/Home/End/Space；未提供时完全不声明 Space，并移除未实现的 Enter。
  方向键仍先更新全局 selection，再由用户下一次 Space 保存，避免同一 key event 内 Pin 到旧 cell 的竞态。
- Attention、MLP、Signed Attribution、NLA 的 DOM cell 同步增加 Space handler 和精确 `aria-keyshortcuts`；Canvas
  使用相同共享入口。Patching 原有 Space Pin 保持不变，因此五个专用矩阵现在共享当前 selection 的键盘 Pin 语法。
- NLA `onPin` 设为 availability-aware optional：只有 Inspector evidence status 为 available 且 exact row 可用时，
  Canvas/DOM 才声明 Space，并在 toolbar 显示 `Pin selected NLA evidence` 图标按钮；incompatible/not-computed 状态
  不展示按钮、不宣称快捷键。Attention 的 Pin pair 按钮补齐 Lucide Pin 图标。
- DOM 长 token fixture 在 Attention → MLP → Attribution → NLA 四个视图逐一 focus selected cell、按 Space，最终
  Compare 的 4 张卡精确为 `compare-attention / compare-mlp / compare-attribution / compare-nla`。测试同时复核平台
  默认 4 Pin 上限：新 Pin 淘汰最旧项，不错误期待 badge 从 0 递增。
- 100×100 Attention、100×2000 MLP、30×100 Attribution/NLA production Canvas fixture 验证 Space 声明、Pin
  持久化与每种 view evidence；大矩阵 virtualization、sticky axes、metric switching 和 hover 门槛不变。不可用 bundled
  NLA 另有反向断言，确认无按钮、无 Space 声明。
- 390px available-NLA 整区通过 Axe WCAG A/AA/2.1，新增 Pin 控件实测 44×44，并保存移动组件截图。完整功能 E2E
  93 passed（4 workers），production 性能套件 4 passed；20 万 cell、2 秒首屏与 40 次 view cycle 资源门槛均通过。
- 最终 production build：主入口 295.45 kB（gzip 76.33 kB）；SpecializedMatrixCanvas 5.85 kB（gzip 2.56 kB）；
  NLA 15.95 kB（gzip 5.41 kB）；MLP 23.21 kB（gzip 7.47 kB）；Attention 26.32 kB（gzip 8.10 kB）；
  CSS 186.58 kB（gzip 32.96 kB）。
- 当前边界：本轮只统一键盘 Space Pin。专用矩阵的 Shift+单击第二锚点与 Cmd/Ctrl+单击直接加入 Compare 仍待设计
  精确 cell override API；不能先更新 selection 再同步调用旧 closure，否则 Attention source、MLP neuron 或 NLA component
  可能保存错误上下文。

### 2.74 Exact Specialized Matrix Anchor / Direct Compare（2026-07-14）

- 完成 23.3 P0 的专用矩阵 modifier 语义。此前通用 Residual Matrix 支持普通点击主选择、Shift 第二锚点、Cmd/Ctrl
  直接 Pin，但 Attention/MLP/Attribution/NLA/Patching 只有普通选择和工具栏 Pin；研究者无法在矩阵内快速固定差值对象
  或把非当前 cell 精确加入 Compare。
- `pinToken` / `buildPinnedEvidence` 新增显式 `sourceTokenIndex / neuronId / nlaComponent` override。Attention profile/matrix、
  MLP profile 与 partial full-hydration、Attribution layer row/sourceKey、NLA exact component、Patching causal cell 均从目标
  override 构建；不依赖 React 尚未提交的新 selection closure，因此 direct Pin 不会保存旧 source/neuron/component。
- 新增共享 `MatrixComparisonSummary`，五个专用矩阵统一显示 Primary、Anchor、当前 display/raw metric Delta 与 Clear；
  DOM anchor 使用琥珀虚线 outline，Canvas 增加独立 comparison row/column 虚线描边和可测试 `data-comparison-cell`。
  Clear 只清 anchor，不改变主选择、URL、Pin 或 Compare。
- 统一 pointer 语法：普通点击更新主选择；Shift+点击只固定目标 cell 为 Anchor，不改 URL；Cmd/Ctrl+点击按目标 cell
  精确 toggle Pin，不改主选择。NLA 只接受 available 且当前 metric 存在的 exact row，Patching 只接受 computed cell，
  unavailable/missing 不生成伪 anchor 或零值 evidence。
- 统一键盘等价操作：Arrow/Home/End 移动，Enter 显式提交当前 cell，Shift+Enter 固定 Anchor，Control/Meta+Enter 精确
  direct Pin，Space Pin 当前 selection。DOM 原生 button 与 Specialized Canvas 的 `aria-keyshortcuts` 现在与实际行为一致。
- Delta 遵守各视图当前语义：Attention 为 displayed probability/difference delta；MLP 随 signed/absolute/normalized metric
  变化；Attribution 显示 stored raw delta；NLA 使用 cosine/MSE/FVE；Patching 使用 recovery/effect/patched-logit。指标切换
  保留语义兼容 anchor，Run/token axis、neuron dataset、Attribution method、NLA rows/filter 或 Patching experiment 变化时清除，
  避免跨数据集复用旧 row index。
- DOM E2E 覆盖五类矩阵的 URL 不变、Anchor class、非 `n/a` delta、Clear、精确 localStorage evidence 字段与普通点击回归；
  键盘测试覆盖 Shift+Enter 后移动主选择、Control+Enter 精确 Pin。默认最多 4 Pin 的 toggle/淘汰语义保持不变。
- Production Canvas fixture 覆盖 100×100 Attention、100×2000 MLP、30×100 Attribution/NLA 的 pointer/keyboard
  modifier、comparison row/column、精确 source/neuron/layer/component evidence；20 万 cell 与 viewport virtualization 不回退。
- 390px 视觉验收发现 sticky mobile selection bar 会遮住程序化滚入的 comparison summary；新增 76px scroll margin 后，
  sticky bottom 为 70px、summary top 为 75.8px。Clear 提升为 44×44，四类移动摘要无横向溢出，有 Anchor/Delta 状态截图
  清晰可读。
- 完整功能 E2E 93 passed（4 workers），production 性能套件 4 passed；20 万 cell、2 秒首屏、hover 与 40 次 view cycle
  资源门槛均通过。最终 production build：主入口 296.01 kB（gzip 76.52 kB）；共享 MatrixComparisonSummary
  0.72 kB（gzip 0.39 kB）；SpecializedMatrixCanvas 6.58 kB（gzip 2.79 kB）；CSS 187.05 kB（gzip 33.08 kB）。
- 当前边界：Anchor 是当前视图的瞬时分析状态，不进入 URL/session；跨 Run、数据轴或 method 自动清除。Cmd/Ctrl direct Pin
  沿用 toggle 语义，重复点击完全相同 evidence 会 Unpin。专用矩阵 range brushing 已在 2.76 按各自二维语义完成。

### 2.75 Global Numeric Typography / Render-Mode Palette Parity（2026-07-14）

- 深化 23.7 P1 的数值排版与语义颜色。审计发现约 40 个局部 selector 已单独使用 `tabular-nums`，但顶栏 Metric、
  Evidence summary、MLP/NLA selection summary 和部分 Compare value 仍使用 proportional numerals；同一行从 `1.00`
  切到 `0.62` 时数字字宽可能变化，局部清单也容易继续遗漏。
- 将 `font-variant-numeric: tabular-nums` 提升到 `.app-shell` 统一继承。普通正文仍使用原 UI sans，只有数字 glyph 使用
  等宽 advance；cache key、artifact diagnostics 等原有 monospace 字段不变。移动测试读取 Metric、sticky selection、
  comparison summary 与 Compare value 的 computed style，确认四层均继承 tabular contract。
- 颜色审计发现 Signed Attribution 的 DOM/legend 已按计划使用 negative blue `#397f91`、positive orange `#c6682f`，
  但大矩阵 Canvas 仍沿用 MLP 的 negative magenta / positive green；unsigned Canvas 也错误使用 teal。同一 artifact 会因
  cell 数跨过 Canvas threshold 而改变视觉语义。
- Attribution Canvas 现在精确复用 blue `(57,127,145)` 与 orange `(198,104,47)`；signed negative、signed positive、
  unsigned 三条路径与 DOM/legend 一致。Production 30×100 Canvas 直接读取强负/强正 cell pixel，验证负值 blue > red、
  正值与 unsigned red > blue，不以源码字符串代替渲染证据。
- 同轮复核 Attention、MLP、NLA、Patching：NLA/Patching 已与 legend 精确一致；Attention unsigned Canvas 从近似 teal
  收敛到 `#147b76`，MLP signed Canvas 从近似 RGB 收敛到 negative `#b33f67` / positive `#188267`，magnitude
  `#23748a` 保持不变。方向性、zero point、hatch 与 unavailable 契约均未改变。
- 完整功能 E2E 93 passed（4 workers），320/390/768 响应式、forced-colors、Axe 与 Compare 回归均通过；production
  性能套件 4 passed，20 万 cell、2 秒首屏和资源回收门槛无回退。最终 build：主入口 296.01 kB（gzip 76.52 kB）；
  CSS 187.09 kB（gzip 33.09 kB）。
- 当前边界：精度采用两层策略而非机械统一位数：matrix/legend/profile 使用适合扫描的 3–4 位，Inspector/tooltip/export
  保留约 6 位精确 evidence。formatter registry 已在 2.77 完成；后续新增 metric 必须登记 compact/exact 两种格式。

### 2.76 Specialized Matrix Token Range Brushing（2026-07-14）

- 完成 23.3 P0 的专用矩阵范围框选。统一语义为 token range：Attention 沿 source token 列，MLP 沿 token 行，
  Attribution、NLA、Patching 沿 token 列；不把 layer、neuron 或 component 轴误写成 token range。
- 新增共享 `useMatrixRangeBrush`，DOM 矩阵通过事件代理读取 `data-range-token`，只在真正跨 token 移动后捕获指针并
  抑制随后 click。普通点击、Shift 第二锚点和 Cmd/Ctrl direct Pin 不被重定向；Pan 模式关闭 brush，touch pointer
  保留原生页面/矩阵滚动，mouse 与 pen 才接管范围拖拽。
- 扩展 `SpecializedMatrixCanvas` 的 row/column range axis。Canvas 使用位置范围绘制预览和琥珀色轴/单元格高亮，提交时
  再映射为真实 token index；非连续 token 轴不会把数组 position 当作 token id。单点 pointer down/up 继续选择原 cell，
  modifier、键盘、hover、overview 和 exact Pin 契约不变。
- 新增统一 Range summary：无范围时明确显示 all tokens，有范围时显示闭区间并提供图标 Clear。Attention 使用
  `Source token range` 避免与 destination 混淆；其他专业矩阵使用 `Token range`。状态写入已有 Selection Store、URL
  `range` 与 Timeline，因此跨 Attention / MLP / Attribution / NLA / Patching 切换可直接复用。
- DOM E2E 覆盖四类即时矩阵的 drag、跨视图同步、Clear、Pan 冲突与 touch pointer 不接管；Patching 派生任务覆盖
  未计算表头到 exact causal cell 的范围。Production 大矩阵分别验证 Attention column、MLP row、Attribution column、
  NLA column Canvas drag 及 `data-selected-range`，并继续通过原有 click / Shift / Ctrl / Space 回归。
- 390px 截图确认 Range summary 不挤压矩阵或 toolbar，Clear 为 44×44px，页面无横向溢出。完整功能 E2E 94 passed
  （4 workers），production 性能套件 4 passed；20 万 cell、2 秒首屏和资源回收门槛无回退。最终 build：主入口
  296.28 kB（gzip 76.55 kB）；共享 range chunk 2.80 kB（gzip 1.19 kB）；SpecializedMatrixCanvas 7.96 kB
  （gzip 3.29 kB）；CSS 187.40 kB（gzip 33.15 kB）。
- 当前边界：范围是全局 token selection，不是第二比较锚点；范围端点不在当前 run 的精确 token 轴时不会伪造 Canvas
  高亮。触屏默认滚动而不 brush，避免与移动浏览冲突；如后续需要 touch range，应采用显式“范围模式”而不是复用滚动手势。

### 2.77 Metric Compact / Exact Formatter Registry（2026-07-14）

- 完成 23.7 P1 的 metric 精度注册。新增集中 `metricFormatting.ts`，按 metric family 登记 `compactDigits` 与
  `exactDigits`：attention / signed residual / raw MLP / attribution compact 4 位，normalized / norm / safety proxy
  compact 3 位，patching recovery compact 1 位，其余 causal/logit metric compact 4 位；exact evidence 统一保留 6 位。
- `formatMetricNumber` 对 `null`、`undefined` 和非有限值统一返回 `n/a`，消除负零；极小非零值在 compact/exact
  阈值下转为科学计数法，避免 Inspector 将真实 `4.2e-9` 静默显示为 `0.000000`。`formatMetricDelta` 统一正号，
  `metricDisplayLabel` 统一 Pin / Compare 中的可读 metric 名称。
- Timeline、顶栏 metric、通用 Matrix cell/legend/ARIA/tooltip、Attention、MLP、Attribution、NLA、Patching、
  Inspector、Pinned strip 与 Compare primary value 已接入同一 registry。扫描表面调用 compact；Inspector、tooltip、
  Canvas live description 与 reproduction context 调用 exact。图表坐标、像素位置和非 evidence 参数不错误套用 metric 格式。
- Attention 派生 mean/max/rollout/difference 使用实际 `attentionHeadMetric`，不再沿用 raw probability 精度；NLA 的
  cosine/MSE/FVE delta、Patching recovery 百分号、MLP signed/absolute/normalized 与 Attribution raw/normalized 分别
  保持自己的 metric 语义。Compare 只在同 metric/normalization/evidence class 可比时显示同规则 delta。
- 新增注册表与浏览器联合回归：覆盖 probability compact/exact、recovery、负零、极小 integrated gradients、signed
  NLA delta 和可读 label；同一 residual value 在 Matrix tooltip/Inspector 显示 exact，在 Pin/Compare 显示 compact。
  完整功能 E2E 95 passed（4 workers），production 性能套件 4 passed；20 万 cell、2 秒首屏和资源回收门槛均通过。
- 1440px 与 390px 截图确认三/四位 compact 数字未挤压顶栏、Timeline、sticky selection、矩阵、Inspector 或移动操作条。
  最终 build：主入口 298.41 kB（gzip 77.22 kB）；Attention 28.11 kB（gzip 8.66 kB）；Compare 33.55 kB
  （gzip 9.03 kB）；CSS 187.40 kB（gzip 33.15 kB）。
- 当前边界：未知 metric 使用稳定 fallback（compact 3 / exact 6），保证界面可用但不代表语义注册完成；新增正式 metric
  必须加入 registry 并补 compact/exact/delta 测试。单位仍由 evidence contract 单独提供，formatter 不推断百分号或概率。

### 2.78 Retryable View Boundary / Lazy Module Timeout（2026-07-14）

- 深化 23.8 P0 的视图级故障隔离。原 `ViewErrorBoundary` 能显示 render error，但 Retry 只重挂同一个 `React.lazy`
  对象；lazy loader 一旦 rejected 会缓存失败，按钮可能反复失败。同时错误恰好发生在 View 切换时，旧
  `previousProps.resetKey` 判断会立即清除刚捕获的错误，使 fallback 无法稳定出现。
- 新增 `retryableLazy`：从原始 `import()` module + named export 精确提取组件 props，并在工厂闭包中按 retry generation
  缓存 Lazy 实例。缓存不依赖尚未 commit 的 hook（React 会丢弃首次 suspend 组件的 `useMemo`），Retry generation
  会创建新的 loader promise；Attention、Residual、MLP、Attribution、NLA、四类 job、Patching、Intervention 和
  Compare Drawer 均复用该基础。
- 动态模块 loader 增加 12 秒 production timeout。挂起 import 不再无限停留在 Suspense spinner，而会进入明确 error；
  DEV E2E 可将 timeout 缩短但该测试变量经 `import.meta.env.DEV` 在 production tree-shake，构建产物已确认无测试 hook。
- 移除七个分析 View 的 hover/focus 执行式 import preload，避免可选预加载失败污染用户随后真正的 lazy render。
  分析模块仅 3–28 kB，点击后继续使用局部 `ViewModuleFallback`；Compare 保留已有 focus preload 与稳定 loading dialog，
  production 2 秒首屏和 view-cycle 性能门禁证明没有可见回退。
- Error Boundary 现在记录错误发生时的 reset key，只在后续上下文变化时自动清除。fallback 自动获焦并明确声明
  Run、token、Timeline、Pin 与 Inspector 未变化；提供主操作 Retry、Open Overview、Copy diagnostics。诊断 JSON
  包含 schema、view、selection context、error、component stack、URL、UA 与时间；剪贴板失败显示 `Copy failed`。
- 桌面错误态保持主数据与 Inspector 可见；390px action group 使用两列 + 全宽 diagnostics，三个目标均至少 44px，
  无横向溢出。Axe WCAG A/AA 对 fallback 无违规；顶栏 Metric 同轮增加独立 accessible label，避免多个 `n/a` 歧义。
- E2E 挂起真实 Attention module request，验证 100ms 测试 timeout 后退出 loading、fallback 获焦、外围状态/URL 不丢、
  diagnostics 可复制、Overview 可安全离开；解除请求后返回错误视图并 Retry，在相同 `performance.timeOrigin` 下恢复真实矩阵。
  完整功能 E2E 96 passed（4 workers），production 性能套件 4 passed；20 万 cell、2 秒首屏和资源回收门槛均通过。
- 最终 build：主入口 298.32 kB（gzip 77.59 kB）；Attention 28.11 kB（gzip 8.65 kB）；Compare 33.55 kB
  （gzip 9.03 kB）；CSS 188.06 kB（gzip 33.25 kB）。
- 当前边界：本阶段隔离分析 View 的 lazy/render fault；Compare Drawer 的 modal 内恢复已在 2.79 完成。Error Boundary
  仍只覆盖前端模块加载/render fault，不替代 API、artifact schema 或长任务各自更具体的错误状态。

### 2.79 Compare Drawer Modal Error Recovery（2026-07-14）

- 将 2.78 的可重试故障隔离扩展到 Compare Drawer，但保持抽屉而非页面内 fallback。`ViewErrorBoundary` 新增 dialog
  变体：错误态继续渲染在 modal backdrop 与右侧 drawer 内，明确说明 workspace 与 pinned evidence 未变化，并提供
  Retry comparison、Close、Copy diagnostics；诊断对象使用独立 `safelens-dialog-render-error` 类型，便于区分视图故障。
- Compare 的既有 focus/pointer preload 保留，正常路径仍先显示稳定的 Loading comparison dialog；若动态模块超过 12 秒
  timeout，则同一 modal 原位切换为可恢复错误态，不会无限 spinner，也不会把错误内容追加到主页面流。Retry generation
  解除 rejected lazy cache 后重新发起真实 module loader，成功后直接恢复完整 Evidence comparison Drawer。
- 错误抽屉实现完整 modal 语义：`role="dialog"`、`aria-modal`、初始焦点、Tab/Shift+Tab 循环、Escape 与显式 Close；
  关闭后将焦点返回本次打开 Compare 的桌面或移动触发器。上下文 reset key 包含 run、pinned items 与 baseline，用户切换
  比较上下文时不会继续显示过期错误。
- 390px 下标题自然换行，header close 与三个恢复操作均至少 44px；操作区使用两列并令 diagnostics 独占整行，无横向
  溢出。桌面保持右侧工作抽屉和背景数据可辨识；Axe WCAG A/AA 对错误 modal 无违规。
- E2E 实际挂起预加载中的 Compare module request，验证 loading -> timeout error -> diagnostics copy -> Retry -> real drawer
  完整链路，同时覆盖焦点循环、移动尺寸、无障碍、Escape 关闭与 return-focus；原有 Compare preload、跨 run 对齐、移除项目
  和双入口 modal 回归继续通过。完整功能 E2E 97 passed（4 workers），production 性能套件 4 passed；20 万 cell、2 秒
  首屏和资源回收门槛均通过。
- 最终 build：主入口 300.76 kB（gzip 78.09 kB）；Compare 33.55 kB（gzip 9.03 kB）；CSS 189.89 kB
  （gzip 33.56 kB）。当前边界：该恢复面向 Compare 前端 module lazy/render fault；comparison 数据兼容性与 artifact
  错误继续由 Drawer 内的证据状态负责，不能用通用 module error 覆盖更精确的业务原因。

### 2.80 Unified Long-Job Progress / Elapsed Time（2026-07-14）

- 深化 23.8 P0 的长任务可读性。原 Prompt、Attribution、NLA、Patching、Intervention 虽都显示 `AsyncStatePanel`
  和进度细线，但五套实现各自重复，阶段与百分比挤在状态标题中，用户看不到已用时间，进度条也没有标准
  `progressbar` 数值语义。新增共享 `JobProgress`，统一显示 Stage / Progress / Elapsed 三列和明确的完成轨道。
- 共享组件直接消费现有 job schema 的 `stage`、`progress`、`createdAt`、`updatedAt`，不增加后端字段。运行时采用
  服务端 `updatedAt-createdAt` 已记录时长加浏览器 `performance.now()` 单调增量，不受浏览器/API 主机墙上时钟偏差
  影响；idle/loading 每秒刷新，ready/error/cancelled 后按最后 snapshot 冻结，卸载或进入终态立即清理 interval。
- 五类任务的状态标题回归职责单一：只表达 queued/running/ready/error/cancelled，阶段、百分比和时间由同一读数带
  承担。不同任务只保留克制的语义 accent，布局、数字 typography、边框、动画与 reduced-motion 规则完全共享；删除
  五套废弃 progress CSS，避免后续视觉与行为分叉。
- 每个轨道使用 `role="progressbar"`、`aria-valuemin/max/now` 和同时包含阶段、百分比、时间的 `aria-valuetext`。
  8px 辅助标签经 Axe 审计后由 4.08:1 调整到 AA 合格对比度；forced-colors 使用 CanvasText/Highlight，390px 下
  三列不截断、不横向溢出，终态 Retry 控件保持独立可操作。
- 补齐此前缺失的 Activation Patching 取消 E2E，并强化 Prompt、Attribution、NLA、Intervention 取消断言：运行中显示
  正确 stage/progress，取消后保留最后百分比并冻结 elapsed，当前 Run 不被替换。Prompt 另验证运行时每秒递增、取消后
  不再增长；任务成功切换派生 Run 后，由 Current generated run / 各方法 provenance 保留稳定结果入口。
- 完整功能 E2E 98 passed（4 workers），production 性能套件 4 passed；20 万 cell、2 秒首屏与 view-cycle 的 heap、DOM、
  listener、Canvas、performance mark 回收门槛均通过。最终 build：主入口 302.77 kB（gzip 78.76 kB）；Attribution
  7.31 kB（gzip 2.59 kB）；Patching 9.05 kB（gzip 3.14 kB）；NLA 9.85 kB（gzip 3.51 kB）；Intervention
  11.23 kB（gzip 3.40 kB）；CSS 190.48 kB（gzip 33.71 kB）。
- 当前边界：本阶段统一的是已建立 SSE job contract 的五类计算任务；NLA/Patching/Intervention preflight 仍是短请求，
  不伪装成长任务。所有任务已有取消，错误后的 Retry 仍受当前表单/preflight 是否有效约束；沿 API error code 的细分错误
  与诊断恢复已在 2.81 完成。

### 2.81 Structured Job Failure / Safe Diagnostics / Retry Recovery（2026-07-14）

- 完成 23.8 P0 的长任务错误分类。此前 API 已返回 `model_not_allowed`、`run_too_large`、`*_preflight_failed` 等
  authoritative code，但 `responseDetail()` 只保留 message，五个 runner 又把 submit、SSE 和 worker fault 全部降成字符串。
  `ExplorerApiError` 现在为 job submit/cancel 保留 client code、server code 与 HTTP status；其他 Run/chunk 请求契约不扩改。
- 新增统一 `JobFailure`，按发生来源区分 Network、Request、Compatibility、Authorization、Protocol、Computation，并保留
  submission / stream / execution / cancellation phase。HTTP 401/403 与 gated/access code 归 Authorization，409、preflight、
  incompatible 与 model mismatch 归 Compatibility，invalid JSON/Zod SSE 归 Protocol，job error snapshot 归 Computation；
  不再根据一段红色英文笼统猜测故障。
- Prompt、Attribution、NLA、Patching、Intervention runner 均接入同一分类。终态 ready/cancelled 不会被 EventSource close 后的
  `onerror` 覆盖；execution error 保留 job id/stage/progress，网络与协议错误保留 source Run。审计同时发现并修复五类任务
  的 submit-failure Retry 死锁：失败后原 `activeRef` 仍为 `submitting`，UI 永远判定运行中；现在只清除同 generation 的
  active submission，旧失败不能清除更新任务，Retry 无需刷新即可创建新 generation。
- 新增共享 Failure diagnostics：summary 始终显示故障类别，展开后显示恢复建议、phase、server/client code、HTTP 与 job id。
  Copy diagnostics 导出 `safelens-job-error` JSON，包含 category、phase、code、job stage/progress/timestamps、URL 与 UA；明确不含
  prompt、response、reference、完整 Run 或 request payload，避免诊断复制泄漏研究输入。复制失败保持就地明确反馈。
- 收敛恢复操作：失败时五类主命令从 `Run …` 变为带 Refresh 图标的 `Retry …`，Reset 只负责清空状态；移除状态行重复的
  Retry icon，从三个相似入口收敛为一个主重试与一个重置。`AsyncStatePanel` 无 Cancel/Retry 时不再预留空按钮列。
- 390px 真实移动 Run Library 抽屉截图确认 error -> stage/progress/elapsed -> diagnostics 的阅读顺序清晰，Retry、Reset、
  summary 与 Copy 均至少 44px，无横向溢出；Axe WCAG A/AA 无违规，forced-colors 保留边界、类别与操作可辨识。
- 新增三条 E2E：同页依次处理 Compatibility 422 与 fetch transport failure，再 Retry 成功启动；非法 SSE JSON 标为 Protocol，
  对仍可能运行的服务端 job 只提供 Cancel 而不重复提交；worker error snapshot 标为 Computation，保留 45% 进度后 Retry 新
  generation。诊断 JSON 验证不含请求正文，`performance.timeOrigin` 验证恢复未刷新页面；原五类 ready/cancel 回归继续通过。
- 完整功能 E2E 101 passed（4 workers），production 性能套件 4 passed；20 万 cell、2 秒首屏与 view-cycle 资源回收门槛均
  通过。最终 build：主入口 307.42 kB（gzip 80.04 kB）；Attribution 7.53 kB（gzip 2.68 kB）；Patching 9.30 kB
  （gzip 3.24 kB）；NLA 10.05 kB（gzip 3.59 kB）；Intervention 11.49 kB（gzip 3.50 kB）；CSS 193.28 kB
  （gzip 34.18 kB）。
- 当前边界：结构化 server code 目前用于 job submit/cancel；SSE worker snapshot 的 `error` 仍是 message，没有独立 worker
  error code，因此 execution 只能可靠分为 Computation，不能进一步声称是 CUDA OOM、模型加载、tokenizer 或 artifact write。
  若要细分，必须先扩展后端 `JobSnapshot.errorCode` 并为各 worker 建立稳定枚举，不能在前端解析异常字符串。

### 2.82 Complete Reduced-Motion Contract（2026-07-14）

- 完成 23.9 P1 的 `prefers-reduced-motion` 验收。此前存在两个分散 media block，只覆盖 Drawer、MLP spinner、token pulse、
  context notice 和部分 progress；前部规则仍引用已删除的旧 progress class，通用 async spinner、token hover transition、
  disclosure chevron 与未来新增动效可能漏网。现在删除旧块，在样式表末尾建立唯一权威规则，对所有元素及伪元素统一
  `animation: none`、`transition: none`、`scroll-behavior: auto`，且只在用户明确选择 reduce 时生效。
- JS 路径也遵守偏好：Workspace tab overflow 原本已根据 `matchMedia` 在 smooth/auto 间选择，本轮保留并补浏览器断言；
  全局 token 快捷键和 `focusToken` 不再在 reduce 下创建 560ms pulse state/timer，选择、URL、Inspector 与 Timeline 仍同步
  即时更新。切回 `no-preference` 时 pulse class 与 `token-pulse` keyframe 继续存在，不牺牲默认视觉反馈。
- 审计所有 `requestAnimationFrame` 后刻意保留 Canvas 绘制、DOM 测量、focus return 和 scroll-state 更新：这些是单帧功能
  调度，不是持续视觉运动；若在 reduce 下关闭，会造成空 Canvas、焦点丢失或 tab 控件状态错误。Job elapsed 的每秒文本
  更新同样不是空间运动，继续工作；仅进度宽度 transition 被关闭。
- 新增专门 E2E，挂起真实 workspace request 验证 loading icon 仍可见但 `animation-name: none`；验证 reduce 下 token 不产生
  pulse、context notice transition 为 0、Compare 与移动 Run Library 的 backdrop/drawer 无 fade/slide；切换回 no-preference
  验证 token pulse 仍运行；拦截真实 tab strip `scrollBy` 验证 reduce 使用 `behavior: auto`。现有全视图 Axe 测试本就以
  reduced motion 运行，继续通过。
- 完整功能 E2E 102 passed（4 workers），production 性能套件 4 passed；20 万 cell、2 秒首屏与资源回收门槛均通过。
  最终 build：主入口 307.48 kB（gzip 80.06 kB）；CSS 192.76 kB（gzip 34.06 kB）；Compare 33.55 kB
  （gzip 9.03 kB）；Attention 28.11 kB（gzip 8.66 kB）。
- 当前边界：reduced motion 关闭所有 CSS animation/transition 和 smooth scroll，但不会停止 Canvas render loop 的按需帧、
  focus 调度、计时文本或用户直接拖拽/滚动，因为这些属于功能输入与内容更新。若未来引入持续 Canvas/WebGL 动画，必须
  单独读取 media query 并暂停动画时钟，通用 CSS 规则无法约束像素内部运动。

### 2.83 Complete Keyboard Analysis / Pin / Compare Workflow（2026-07-14）

- 完成 23.9 P1 的“只使用键盘完成一次完整分析和 Pin/Compare”验收。真实 Tab 顺序审计确认 Skip Link 可直接进入
  Analysis workspace，随后按 Layer -> View -> Timeline -> visualization 排列，roving tab 保证每组只有一个焦点入口；
  但 Timeline token 的原生 Space 此前只触发 click/重新选择，不会 Pin，键盘链路在最自然的 token 入口处中断。
- Timeline token 现在统一 `Space = Pin`，并用 `aria-keyshortcuts="ArrowLeft ArrowRight Space Control+Enter Meta+Enter"`
  声明契约；Arrow 继续切换 token 并保持焦点，普通 click/Enter 继续主选择，Ctrl/Meta click 继续直接 Pin。Space 阻止原生
  click 二次触发且不改变 URL/view/layer，Pin 后 marker、Pinned strip、Inspector 与 Compare count 同步更新。
- Pin 后若只用 Tab 返回顶栏 Compare，需要反向穿过约二十个工具控件。新增作用域安全的 `Alt+Shift+C` Compare 效率入口，
  顶栏 trigger 同步声明 `aria-keyshortcuts`；它不替代正常 Tab/click 可达性，只在已有 Pin、没有 Compare/Run Library/
  Inspector modal、焦点不在 input/textarea/select/contenteditable 时触发。按钮、tab、radio、matrix 聚焦时可用，不劫持各组件
  自己的 Arrow/Space/Enter 语义。
- 快捷键打开前复用 Compare preload，并把 return target 固定为顶栏 Compare 按钮；Drawer 仍由统一 modal hook 建立 inert
  background、初始 Close focus、Tab trap 与 Escape。关闭后焦点准确回到可见顶栏 trigger，而不是不可预测地回到矩阵深处。
- 新增纯键盘 E2E：从首个 Tab 聚焦 Skip Link，Enter 进入 workspace，Tab 到 selected Timeline token，ArrowRight 定位
  `strategy`/token 11，Space 从 3 项 Pin 增至 4 项，`Alt+Shift+C` 打开 Compare 并看到 token 11，验证 focus/inert，Escape
  返回 trigger；Prompt textarea 与 Token Search 中同键不打开 Drawer。该工作区 Axe WCAG A/AA 无违规。
- 完整功能 E2E 103 passed（4 workers），production 性能套件 4 passed；20 万 cell、2 秒首屏与资源回收门槛均通过。
  最终 build：主入口 307.93 kB（gzip 80.25 kB）；CSS 192.76 kB（gzip 34.06 kB）；Compare 33.55 kB
  （gzip 9.04 kB）；Attention 28.11 kB（gzip 8.66 kB）。
- 当前边界：快捷键使用 `Alt+Shift+C` 避免与浏览器常用 Ctrl/Cmd 命令冲突，但操作系统、输入法或辅助技术仍可能占用
  任意全局组合，因此标准 Tab 路径始终保留为 authoritative fallback。平台目前不提供用户自定义快捷键映射；如未来添加，
  必须处理冲突检测、持久化、帮助面板与 `aria-keyshortcuts` 动态同步，不能只替换 keydown 常量。

### 2.84 2400-Token Timeline Indexing / Production Performance Gate（2026-07-14）

- 完成 23.4 P1 的“2000 个以上 token 仍可流畅滚动和定位”验收。原 260-token E2E 只证明 Timeline DOM 固定为
  180 items，并未覆盖 2000+ token、production build、固定 CPU/network、远端 chunk hydration 或性能数据；本轮新增
  2400-token production 基准，而不是用小 fixture 外推大轴表现。
- 审计先发现结构性热点：Residual metric 对每个 token `find` 全部 residual rows，NLA metric 对每个 token `filter`
  全部 NLA rows，复杂度为 O(tokens × evidence rows)；visible marker 又对每个 item 扫描 NLA 与 Pin 数组。现在当前 layer
  residual 用一次 Map 建索引，NLA 单遍聚合每 token 最大 cosine，available NLA 与 pinned positions 使用 Set，渲染窗口只做
  O(visible items) 查询。2400-token metric 切换不再重复全表扫描。
- Timeline item 在 token/word 分组时预存 normalized text，query 使用 memoized items + normalized query 过滤；避免每次输入
  对每个 item 重复 `toLowerCase`。Position/token id 的精确匹配语义不变，Word group 仍可跨多个 token 查找与定位。
- 接入现有本地 Performance Timeline：`timeline-ready` 记录 tokens/items/renderedItems/mode，`timeline-search-jump` 从触发到
  offscreen target render+focus 记录 duration/token，`timeline-hover` 记录 pointer 到下一帧联动延迟。事件继续受 100 条环形
  buffer 与同名 mark 单条策略约束，不发送遥测，也不会在长会话无界增长。
- Production fixture 走真实 `safelens-chunks-v1` metadata-first 协议：core metadata 含 2400 tokens，Overview 只加载当前及
  相邻 512-token Residual/LogitLens blocks。搜索 `token-2350` 后只追加 `2048-2400` 末端两类 chunk，full sample request
  始终为 0；不构造 2400×2400 attention matrix 来污染 Timeline 基准，且 metadata/chunk 均经过产品 Zod/merge 路径。
- 固定 2× CPU throttling、20ms latency 下验证 Timeline ready <2s、DOM `.token-pill` 恒为 180、Residual/NLA metric 可切换、
  1/2400 搜索结果将 token 2350 focus/URL/window 原子同步、端到端搜索 <1s、内部 search-jump <100ms、hover <100ms、
  Space Pin 后 marker 正确、性能事件 <=100。原 20/260-token search/word/range/marker/keyboard 回归继续通过。
- 完整功能 E2E 103 passed（4 workers），production 性能套件由 4 增至 5 passed；20 万 cell、2400-token Timeline、2 秒
  常规首屏与 view-cycle heap/DOM/listener/Canvas/marks 回收门槛全部通过。最终 build：主入口 308.72 kB
  （gzip 80.48 kB）；CSS 192.76 kB（gzip 34.06 kB）；Compare 33.55 kB（gzip 9.04 kB）；Attention 28.11 kB
  （gzip 8.66 kB）。
- 当前边界：Timeline 使用窗口化 DOM，而不是连续像素虚拟滚动条；Previous/Next window 与 search/selection 负责远端定位。
  2400-token 基准证明浏览器交互与 chunk 调度，不代表任意模型都能生成或存储超长 attention 全矩阵。全矩阵仍必须依赖
  block sidecar/Canvas，未来二进制 range backend 应保留本基准的 metadata-first 和 full-sample=0 契约。

### 2.85 Contextual Quick Actions / Global Help Entry（2026-07-14）

- 完成 23.1 P0 的全局帮助入口和“两次操作内切换 Run 或返回 Overview”。顶栏新增语义明确的 Help 图标，不展示教程或
  营销说明，而是直接打开可执行的 Quick actions；面板固定显示当前 Run、Sample、View、Layer、Token，避免用户离开当前
  上下文才能判断命令影响范围。
- 六个命令直接复用真实产品路径：Overview 打开 Evidence map，Find a token 聚焦 Timeline search，Runs and samples 打开
  Run Library，Compare 打开已有 Pin 比较，两个 Export 分别下载完整 Analysis Session 和当前 Evidence JSON。Compare 在无
  Pin 时禁用并显示 `Pin evidence first`，不产生无结果 drawer；有 Pin 时显示准确数量。
- 桌面采用 620px 紧凑命令面板和双列命令，390px 以下转为贴底 full-width sheet、单列 56px 操作目标和 2+2+1 上下文网格。
  手机视觉审查确认仍保留上方当前页面线索，顶栏 Help 加入后无图标重叠、无截字和横向溢出；重复的当前证据导出继续按既有
  移动规则隐藏，手机顶栏保持四个 44px 全局操作。
- 完整接入统一 modal 语义：打开后背景 inert、Close 初始聚焦、Tab/Shift+Tab trap、Escape/遮罩/Close 返回 Help。测试发现
  “执行命令关闭”原本会被通用 return-focus 下一帧抢回 Help；`useModalDialog` 现支持按本次关闭抑制原焦点恢复，使 Timeline、
  Analysis workspace 或下一 modal 成为唯一焦点接收者。Run Library 同时记录真实发起控件，从 Help 进入后 Escape 返回可见
  Help，从自身按钮进入仍返回自身，不再聚焦桌面不可见的移动按钮。
- 新增端到端命令回归：验证上下文、Pin 数、inert、首焦点、双向 focus trap、Escape return-focus、Overview/Token Search/
  Run Library/Compare 跨界交接和两个下载文件名；390x844 下验证 bottom sheet 几何、全部目标 >=44px、document 无 overflow、
  Axe WCAG A/AA 与真实截图。审计同时将上下文小标签从 4.07:1 提升到 AA 阈值以上。
- 完整功能 E2E 104 passed（固定 8 workers，显式与默认命令分别为 29.8s / 30.0s），production 性能套件 5 passed
  （33.5s）；20 万 cell、2400-token
  Timeline、2 秒常规首屏与资源回收门槛全部通过。最终 build：主入口 312.27 kB（gzip 81.32 kB）；CSS 196.19 kB
  （gzip 34.58 kB）；Compare 33.55 kB（gzip 9.04 kB）；Attention 28.11 kB（gzip 8.66 kB）。
- 验证说明：一次把自动推导的 96-worker 功能套件与 production 浏览器套件并发叠加，造成 20 个截图/Axe/加载用例资源争用
  超时；同一代码在定向 6-worker 回归、受控 8-worker 全量和独占 1-worker 性能门禁全部通过。Playwright 默认配置现固定为
  8 workers，`npm run test:e2e` 不再随主机核数放大；production 性能套件继续独占 1 worker 串行，避免不可复现噪声。
- 当前边界：Quick actions 是高频命令与上下文确认面板，不承担长教程、快捷键清单或用户偏好设置。新用户完整流程已由纯键盘
  Analysis -> Pin -> Compare 和本轮命令回归覆盖，但真实可用性研究仍需单独招募目标用户并记录任务完成时间/误操作，E2E
  不能替代用户研究。

### 2.86 Executable Advanced-View Empty States / Non-Overlapping Mobile Feedback（2026-07-14）

- 完成 23.1 P0 的“首次进入空视图展示可执行空状态”。审计发现 Patching 与 Intervention 在没有结果时只显示
  `configure above` 文案；NLA 的无精确行/decoder unavailable、Attribution 的 Integrated Gradients 未计算也只解释原因。
  虽然对应 job panel 已在同一 View 上方，结果区本身是死端，键盘与手机用户无法从看到的缺口直接进入下一步。
- 新增复用 `ActionableEmptyState`，统一呈现状态图标、明确原因、当前 selection/method/component 事实和一个主动作，不使用教程或
  营销说明。Patching 直接进入 aligned corruption 配置，Intervention 进入 matched generation 配置，NLA 无精确行与 decoder
  unavailable 都进入 exact NLA job，Integrated Gradients 缺失进入 target/baseline/convergence 配置；其他尚无可生成后端的
  Attribution 方法保持诚实的只读 unavailable，不承诺无效动作。
- 所有动作复用 `openJobSetup`：完整 Run 在下一 animation frame 滚动并聚焦对应 `tabIndex=-1` job section；chunk Run 先加载
  full artifact，再等待 lazy/job panel 最多约 1 秒并聚焦。加载失败保留当前 range visualization，并显示具体
  `Experiment setup could not be opened` 诊断，不让按钮静默无响应。Inspector 推荐动作也改用同一入口，消除两套聚焦逻辑。
- 修复移动 Inspector 的跨 modal 焦点竞争：推荐动作关闭 drawer 时明确抑制原 trigger return-focus，并等 inert background 清理
  后再聚焦 job panel；普通 Escape/Close 仍返回 Inspector trigger。该修复与 2.85 Quick Actions 的命令交接契约一致。
- 390px 截图审查发现首版可执行空态的主按钮被底部 `Context updated` toast 压住。Context notice 现在位于 app-shell 内：桌面
  继续使用底部轻量 toast，520px 以下转为 Topbar 与 Workspace 之间的短暂文档流状态带，出现时推开内容、消失时收起；live
  region 仍只有一份。新增几何断言要求 notice 底边不越过 workspace 顶边，从根本上防止反馈覆盖底部操作和安全区。
- 空态桌面保持紧凑虚线区域，手机 facts 由双列转单列、source key 可断行、主按钮全宽且 >=44px。真实 390x844 截图确认
  Patching 空态没有截字、嵌套卡片或无意义留白，事实与主动作层级清晰；Axe WCAG A/AA 无违规，document 宽度严格为 390px。
- 新增 E2E 逐一执行 Patching、Intervention、NLA、Attribution 四条空态 -> job setup 路径并验证真实焦点；覆盖上下文 facts、
  手机目标尺寸、overflow、Axe 与截图。移动 notice 回归新增非重叠几何；30 条高级视图/A11y/移动定向回归通过。
- 完整功能 E2E 105 passed（固定 8 workers，30.2s），production 性能套件 5 passed（37.2s）；20 万 cell、2400-token
  Timeline、2 秒常规首屏与资源回收门槛全部通过。最终 build：主入口 314.14 kB（gzip 81.91 kB）；CSS 197.81 kB
  （gzip 34.88 kB）；Signed Attribution 11.94 kB（gzip 4.08 kB）；Compare 33.55 kB（gzip 9.03 kB）。
- 当前边界：本轮动作解决“已有对应本地 job 能力”的结果缺口；它不自动提交高成本实验，仍要求用户确认输入、兼容性和参数。
  NLA incompatibility 进入 job panel 后会继续由 preflight 阻止错误提交。若未来新增 attribution/causal 方法，只有在存在真实配置和
  执行路径后才能加入 empty-state action，不能把外部文档链接伪装成可执行恢复。

### 2.87 Progressive Mobile Inspector / Touch Disclosure（2026-07-14）

- 完成 23.5 P0 的“移动端底部抽屉默认紧凑摘要，上滑展开完整 provenance”。原 mobile Inspector 虽为 bottom sheet，但打开
  即是最高 90vh 的单一长页，Summary、六行 provenance、warnings、四个 Actions 和最多三条推荐动作全部展开；用户必须穿过
  方法/cache key/source 等细节才能回到高频操作，不符合结论优先的移动信息层级。
- `EvidenceInspector` 新增明确的 `compact | full` detail level，默认仍为 full，因此桌面右栏完整 `Summary / Evidence / Actions`
  三层完全不变。移动 compact 只渲染选中对象、状态、结论、evidence class、raw/display/units 和 Pin/Compare/Context/Export；
  full 才渲染 Method、Normalization、Cache key、Source artifact、Run/Sample、Model、warnings 与 Recommended next analysis。
  使用 `useId` 为每个桌面/移动实例生成独立 heading 关联，避免同页双 Inspector 的重复 id。
- bottom sheet 现维护独立 disclosure state，每次关闭/重新打开都回到 compact；compact 最大约 64vh/540px，full 才扩到
  90vh/780px，切换时滚回顶部，避免从 provenance 深处收起后看不到 Summary。Header 固定显示拖拽把手、状态文案和横排的
  44px 展开/收起与关闭图标按钮；`aria-expanded`、动态 aria-label 与 ChevronUp/Down 为键盘和读屏提供与手势等价的路径。
- Header 支持 pointer/touch 上滑 48px 展开、下滑 48px 收起；`touch-action: none` 和 pointer capture 防止浏览器原生滚动抢走
  起点。调试连续双向手势时发现 Chromium 会在第二次下滑首段产生 `pointercancel(clientY=0)`；最终实现不把 cancel 当成有效
  坐标，且在 pointermove 越过阈值时立即提交状态，pointerup 仅作为无中间 move 的回退。window listeners 随 Workspace
  卸载清理，现有 production view-cycle listener 回收门禁继续通过。
- 新增真实 CDP `Input.dispatchTouchEvent` 回归，不以桌面 mouse 模拟替代触摸证据：验证 touch 上滑 compact -> full、touch
  下滑 full -> compact；同时覆盖图标按钮展开/收起、重新打开复位、Escape/Close return-focus、compact 不存在 Evidence/推荐项、
  full 恢复完整 provenance、两态高度/贴底几何、document 390px 无 overflow，以及 compact/full 两次 Axe WCAG A/AA。
- 390x844 双截图审查确认 compact 高约 498px，首屏完整看到 selected evidence、Summary 与四个高频动作；full 扩展后 Evidence
  表格、warning、Actions 按顺序出现，长 cache/source/run 文本可断行，双 header 按钮不再因旧 grid 规则纵向堆叠，拖拽把手
  与标题/按钮无重叠。forced-colors、reduced-motion、modal focus trap 和 11 条 Inspector/移动定向回归全部通过。
- 完整功能 E2E 106 passed（固定 8 workers，31.0s），production 性能套件 5 passed（35.7s）；20 万 cell、2400-token
  Timeline、2 秒常规首屏与 heap/DOM/listener/Canvas/marks 回收门槛全部通过。最终 build：主入口 315.55 kB
  （gzip 82.34 kB）；CSS 198.28 kB（gzip 34.99 kB）；icons 28.47 kB（gzip 5.73 kB）；Compare 33.55 kB
  （gzip 9.04 kB）。
- 当前边界：本轮实现的是二态 progressive disclosure，不是可停留在任意高度的物理 sheet。任意高度拖拽会显著增加键盘弹出、
  safe-area、scroll ownership 与焦点可见性复杂度；在有真实任务证据前，compact/full 两个稳定状态比自由高度更可预测。full
  内部仍使用标准滚动，手势只在 header 启动，不劫持 provenance 内容滚动。

### 2.88 Versioned Evidence Assessment / Export Trust Parity（2026-07-14）

- 完成 23.5 P0 的“所有导出对象携带与界面一致的 provenance 和 warning”。审计发现 Inspector 已统一计算 status、reason、
  raw/display value、units、evidence class、method、normalization、cache key、shape、source、warnings 与 reproduction，但当前
  Evidence JSON 只导出 `activeMetricProvenance`；界面显示的 attention non-causal warning、unavailable/failed 原因不会进入下载。
  Session/Comparison 的 Pin 也只有基础 provenance，无法重现捕获当时的完整可信度判断。
- 新增无 UI 依赖的 `EvidenceAssessment` v1 数据契约，固定包含 `schemaVersion: 1.0`、七类 status、statusReason、primary/raw/
  display/units、evidenceClass、method/normalization/cacheKey/shape/sourceArtifact、去重 warnings 与完整 reproduction。转换函数从当前
  `InspectorEvidence` 显式复制字段，不重新推断，也不序列化 React 临时状态；UI、Copy Context 与下载因此共享同一个权威判断。
- Current Evidence JSON 新增顶层 `evidenceAssessment`，保留所有原字段以兼容现有消费者；Analysis Session 新增
  `activeEvidenceAssessment`。Session Zod schema 对 active assessment 与 Pin assessment 做完整字段/枚举/版本校验，同时保持二者
  optional，旧 1.0 Session 可继续导入。新导出的 Session 已由产品 schema 实际 safeParse 通过。
- `PinnedEvidence` 新增可选 `assessment`。普通 Pin 按目标 token/layer/source/neuron/NLA component 重建 exact Inspector context，
  因此矩阵 Ctrl/Cmd Pin 不会错误保存当前 UI cell 的判断；Analysis Session 的 pinnedItems 与 Comparison Artifact 的 items 原样
  携带 assessment。chunk Attention/MLP Pin 在 full artifact hydrate 后重新生成 assessment/sourceArtifact，不保留错误的
  `range chunk` 来源或 partial 状态。首屏自动创建的 Overview 初始 Pin 也改为经过同一 Inspector 证据构建链路，当前版本导出的
  初始项同样携带 v1 assessment 与 run-relative/non-calibrated warning；仅对缺少必要 head/method 的 legacy artifact 保留无
  assessment 的兼容回退，不伪造无法从 artifact 证明的历史判断。
- 同步修复 Pin selection snapshot 的语义漂移：原 `buildPinnedEvidence` 的 ID 会使用当前 raw/normalized mode，但返回对象对除
  Attention/Intervention/部分 MLP 外一律写 `normalization: normalized`；raw Residual/Attribution Pin 因此在 Session/Compare/
  restore 中变成 normalized。现在先计算唯一 `pinNormalization` 并同时用于 ID、PinnedEvidence、assessment reproduction 与回放；
  method provenance normalization 仍保留方法本身的 min-max/raw contract，不与 display mode 混为一谈。
- 新增一条端到端 trust-parity 回归，从真实 Inspector DOM 读取 status/reason/method/normalization/evidence class/warning，再逐字段
  比对 Evidence JSON。覆盖 available Attention、unavailable MLP、failed Residual；raw Residual Pin 验证 mode=raw 与 assessment，
  Session 同时验证 active/pinned assessment 并通过 Zod，Comparison item assessment 与 Session Pin 完全相等。七条 Session/
  Pin/Compare/Inspector 相邻回归通过，旧无 assessment Session 继续完整 replay。
- 完整功能 E2E 107 passed（固定 8 workers，30.6s），production 性能套件 5 passed（35.5s）；20 万 cell、2400-token
  Timeline、2 秒常规首屏与 heap/DOM/listener/Canvas/marks 回收门槛全部通过。最终 build：主入口 318.01 kB
  （gzip 82.83 kB）；CSS 198.28 kB（gzip 34.99 kB）；Compare 33.55 kB（gzip 9.04 kB）；schema vendor 74.66 kB
  （gzip 20.00 kB）。
- 当前边界：EvidenceAssessment 保存的是“捕获/导出时界面所作判断”，不应在旧 Session 导入时用当前代码静默重算；方法定义或
  calibration 变化时，版本升级应新增 schemaVersion/迁移策略。旧 Pin 无 assessment 仍可比较与恢复，只是不能声称拥有历史
  warning parity；UI 可继续回退到基础 provenance，不能伪造缺失的捕获时状态。

### 2.89 Timeline Role / Generation Sequence Clarity（2026-07-14）

- 完成 23.4 P1 的 prompt、assistant reply、special token 与 generation step 显式区分。原 Timeline 已按 source 分组，也会以小号
  `step n` 文本展示单 token generation metadata，但 source header 只有名称/数量，special 只依赖虚线灰底；Word 模式合并多个
  reply token 后仅保留首个 step，用户无法直接判断该 word 覆盖的生成区间。
- Prompt / Reply header 新增语义一致的 Lucide 角色图标、`Input context / Generated continuation` 副标题，以及全局 token 范围；
  reply 同时展示 `G<start>–G<end>` 和 token 数。范围始终从完整 Run token metadata 派生，不随 180/60 item 窗口裁剪而变化，
  因此长 Timeline 进入中间窗口时仍能确认完整序列位置。
- 每个 reply item 新增不依赖颜色的 generation badge：Token 模式显示 `G1`，Word 模式对合并子词显示 `G0–1`。special item
  显式显示 `Special` 虚线 badge；完整角色、special 状态与 generation step/range 同时进入 button accessible name，视觉标签设为
  `aria-hidden`，避免读屏重复朗读。
- 实景检查发现 Word 分组只在“当前 token 是 special”时开始新组，没有在“上一组含 special”时切断；例如 special `User` 后的
  `:` 会被合并成一个 2-token special item，错误扩大 special 语义。现在 special token 前后都建立硬边界，普通子词不会继承
  special 样式或 accessible name。
- 同步修复 Timeline 旧 special 灰底上的 token count / metric value 与新增角色副标题的 WCAG AA 对比度；不禁用 Axe color-contrast。
  桌面 1440px 与移动 390px 真实截图确认 source header、范围、badge、token 和指标无重叠；390px Timeline `scrollWidth <= clientWidth`，
  Word 模式生成范围保持可见。
- E2E 覆盖 Prompt/Reply header、T/G 范围、Special、Token `G1`、Word `G0–1`、special 独立边界、accessible name、390px 无溢出与
  Timeline Axe WCAG A/AA；搜索、范围、Pin 和 260-token 窗口化三条相邻回归通过。完整功能 E2E 107 passed（固定 8 workers，
  31.2s），production 性能套件 5 passed（38.0s），2400-token、20 万 cell、首屏与资源回收门槛未回退。最终 build：主入口
  319.80 kB（gzip 83.30 kB）；CSS 199.95 kB（gzip 35.26 kB）；icons 28.92 kB（gzip 5.82 kB）；Compare 33.55 kB
  （gzip 9.03 kB）。
- 当前边界：generation badge 忠实显示 artifact 提供的 `generationStep`；字段缺失时仅使用 reply 内的稳定顺序作为现有兼容回退，
  不推断采样时间、beam 或 decoding event。跨 turn latency、logprob 与停止原因需要新的版本化 artifact 字段，不能从 step 序号臆造。

### 2.90 Shape-Coded Timeline Evidence Markers（2026-07-14）

- 完成 23.4 P1 的“risk、probe、monitor、attribution 和 pinned evidence 不只依赖颜色”。审计发现原 marker 除 Pinned 是小方形外，
  Risk、Attribution、NLA、Probe、Monitor 全部继承同一个圆点；红、青、金、绿、紫是唯一主要区别，去色、色觉差异或高对比模式下
  无法可靠判断 token 命中的证据类型。
- 六类 marker 现在使用稳定的双通道编码：Risk 为三角、Attribution 为菱形、NLA 为圆环、Probe 为五边形、Monitor 为十字、
  Pinned 为描边方形；原语义色保留作为第二通道。legend 与每个 token 的 marker row 复用同一 class/data-shape 契约，不会出现
  图例形状与数据项不一致。
- token marker row 继续作为装饰层对读屏隐藏，但 button accessible name 现在追加按固定顺序去重后的
  `evidence markers: Safety proxy, Attribution, NLA evidence, Probe, Monitor, Pinned`；读屏用户不需要通过不可见颜色猜测状态。
  legend marker 显式 `aria-hidden`，相邻文字提供可访问名称，避免图形与文字重复朗读。
- Windows forced-colors 模拟中统一使用 CanvasText/Canvas，但保留 triangle/diamond/ring/pentagon/cross/square 几何和圆环空心；
  不是把六类 marker 在高对比模式下重新压成同形。CSS shape signature 回归排除颜色字段，逐项验证六种计算样式互不相同。
- 1440px 与 390px 真实截图覆盖六类 marker 同时出现：桌面 legend 单行且 token row 不挤压指标，移动端自然换行，Pinned 独立落到
  下一行时仍与 token 列表保持清晰间距。390px 无横向溢出，Axe WCAG A/AA 零违规；Token/Word、搜索、范围、Pin 与长 Timeline
  窗口化相邻回归均通过。
- 完整功能 E2E 107 passed（固定 8 workers，31.3s），production 性能套件 5 passed（30.0s）；2400-token、20 万 cell、
  首屏与 heap/DOM/listener/Canvas/marks 回收门槛未回退。最终 build：主入口 320.10 kB（gzip 83.39 kB）；CSS 200.51 kB
  （gzip 35.41 kB）；icons 28.92 kB（gzip 5.82 kB）；Compare 33.55 kB（gzip 9.03 kB）。
- 当前边界：forced-colors 是 Chromium 自动化模拟，不能替代 Windows High Contrast、打印灰阶、NVDA/JAWS/VoiceOver 的人工验证；
  但形状、文本和 accessible name 已不依赖颜色。marker 仍只表达 artifact 已声明的 evidence presence，不把命中形状解释为结论强度。

### 2.91 Stable Local Analysis Loading Skeleton（2026-07-14）

- 完成 23.7 P1 的视图/chunk 局部 loading 骨架。原 lazy visualization module 或 workspace range chunk 加载时，主图从完整矩阵
  塌缩为最低 86px 的状态条；完成后再突然撑开，Timeline 以下内容随之跳动。加载时间稍长时，用户会误以为主分析区消失或页面
  切换失败。
- 新增共享 `AnalysisLoadingSkeleton`，同时接入 `ViewModuleFallback` 与 `ViewChunkState` 的 preparing/loading 分支；保持工具栏、
  双轴矩阵、当前视口和 legend 的稳定空间。骨架使用中性无数值网格、设置 `aria-hidden`，真实 View/Layer/Token、loading reason、
  Cancel 和 Inspector loading status 仍由现有权威文本/控件表达，不把 placeholder 冒充低分辨率 evidence。
- loading surface 保持至少约 320px 高，桌面矩阵 stage 为 228px，700px 以下收敛为 196px；1440px 与 390px 实景中状态首行、
  骨架工具条、轴区、视口框和 footer 均无重叠或横向溢出。Context Updated 浮层最多覆盖无语义 footer placeholder，不遮挡状态、
  Cancel 或矩阵 stage。
- Error/Cancelled 不保留大骨架：取消 range request 后立即回到低于 180px 的紧凑恢复状态，并保留 Retry；已加载 ranges 继续存在。
  Retry 后进入真实矩阵，既有 cancellation feedback 仍小于 300ms。lazy module 超时仍由 View Error Boundary 隔离，Retry 不刷新文档。
- 骨架 toolbar/axis 使用轻量 opacity breathe；全局 `prefers-reduced-motion: reduce` 将动画归零。forced-colors 统一为 Canvas/CanvasText
  并保留轴、网格和 viewport 边界；loading 区 Axe WCAG A/AA 零违规。扫描同时修复旧 loading/full-hydration 辅助文字在浅色背景上
  仅 4.34:1 的对比度，不禁用 color-contrast 规则。
- E2E 增强现有 chunk-v1 与 lazy module 两条真实延迟链路，覆盖骨架尺寸、Cancel 后移除、Retry、reduced-motion 和 Axe。完整功能
  E2E 107 passed（固定 8 workers，31.6s），production 性能套件 5 passed（37.5s）；2400-token、20 万 cell、首屏和资源回收
  门槛未回退。最终 build：主入口 320.82 kB（gzip 83.52 kB）；CSS 202.63 kB（gzip 35.88 kB）；icons 28.92 kB
  （gzip 5.82 kB）；Compare 33.55 kB（gzip 9.03 kB）。
- 当前边界：本轮解决的是 loading 布局稳定和状态可见性，不是 23.3 的真实数据缩略图。component metadata 尚未携带可验证的
  downsampled values，前端不会用随机色块或上一 scope 的旧矩阵伪装低分辨率 overview；该能力需要新增版本化 metadata summary。

### 2.92 Run Context Isolation / Explicit Transition Receipt（2026-07-14）

- 完成 23.2 P0 的来源切换上下文隔离验收。审计确认 `ExplorerWorkspace` 已按 `runId::sampleId` key remount，普通 Run 选择会先清理
  selection URL，旧 hydration/prefetch 会取消；但缺少一条把 token/range/head/neuron/track/viewport/Pin marker 全部放在同一条
  不兼容 Run 链路验证的回归，`Run changed` 提示也只显示 sample/model，用户无法确认新 active context 落在哪里。
- `selectionFromLocation` 现在除 token/layer 外也校验 URL token range 的两个端点必须存在于当前 Run token axis；`range=8-999`
  进入 20-token Run 时立即归零并从 URL 删除，不让无效范围长期残留在 Timeline、矩阵摘要或 Session 导出中。
- Run change receipt 现在显示 exact `Sample · View · T<token> · L<layer> · context kind`。普通选择显示 `fresh selection`，Pin/浏览器
  历史显示 `restored context`，跨 Run Session 显示 `session context`；移动端继续保持两行内与首屏工作区不重叠，live log 使用相同文案。
- 修复 transition kind 的 effect-order 竞态：子级 selection effect 可能先把新 Run 默认值写回 URL，父级再读取时会把 fresh 误判为
  restored。`useRunLibrary` 现在把一次性 `{key, kind}` receipt 写入对应 history entry；App 在匹配 Run 首次消费后原地删除，不污染
  后续 selection push/replace，也不会让前进/后退复用过期 transition intent。
- 新增一个结构不兼容 Run：旧上下文预先设置 Attention source=8/target=10、range=8–12、L0H0、L1N0、旧 attribution track、
  Timeline query 和放大的 Attention viewport；新 Run 使用不同 Head/Neuron/Track ID 且 top-risk token 为 T3。切换后逐项验证
  Overview/T3/L1、新 ID、source/target/range/edge 清除、query 清空、matrix viewport 空对象，并通过 Analysis Session 下载复核。
- Pin 边界显式验证：原 Run 的 3 个 versioned evidence snapshots 继续留在全局 Compare workspace，支持跨 Run 研究；新 Run Timeline
  的 `pinnedTokenIndices` 仅按当前 run/sample 过滤，因此 legend 不显示 Pinned，也不会把相同 position 冒充当前 Pin。这是保留证据，
  不是 active context 污染。
- Run notice、浏览器历史和不兼容切换三条专项回归通过。完整功能 E2E 增至 108 passed（固定 8 workers，31.5s），production
  性能套件 5 passed（36.9s）；2400-token、20 万 cell、首屏和资源回收门槛未回退。最终 build：主入口 322.27 kB
  （gzip 84.06 kB）；CSS 202.63 kB（gzip 35.88 kB）；icons 28.92 kB（gzip 5.82 kB）；Compare 33.55 kB
  （gzip 9.03 kB）。
- 当前边界：本轮 receipt 证明的是浏览器内已加载来源之间的 active context 隔离；未加载 workspace Run 的竞态、取消和旧响应隔离
  已由 2.8/2.18 覆盖。跨 Run Pin 会继续保留，只有 Restore context 才允许它显式切换 active Run，不能因普通切换自动回放。

### 2.93 Compact Responsive Timeline Toolbar（2026-07-14）

- 推进 23.9 P1 的移动端次级工具收敛。1440/1024/768/390 四档完整首屏实景审计发现，390px Timeline 在 token 数据前约有
  216px 工具区：Search、Token/Word、Color 被拆成三层，空查询时 Previous/Next 两个禁用 44px 按钮仍占位，首屏少显示约一行
  token；768px 同样为无效搜索导航保留额外纵向空间。
- 341–800px 空查询状态现在固定为两行：Search 独占首行，Token/Word 与 Color 同行；无查询时 search status/navigation 完全隐藏。
  320/340px 以下继续使用原有单列安全堆叠，不用压缩文字或缩小触控目标换空间。
- 输入查询后，匹配数量移动到 Search label 右侧，以 `1 match / n matches` 就地反馈；Previous/Next 仅在查询存在时出现。381–520px
  使用 Granularity + navigation 同行、Color 独立下一行，保证 Word 与 Safety proxy 完整；521–800px 空间足够时使用三列查询态。
- 第一版曾在 390px 强行把 Granularity/Color/navigation 放同一行，实景暴露 Word 和 Safety proxy 截断；随即改为上述分段规则，并新增
  每个可见 button/select 的 `scrollWidth <= clientWidth` 门禁。响应式压缩不能以不可读控件为代价。
- 390px 空查询实景中 token 区提前约一整行；查询态 Search count、Token、Word、Safety proxy 和 44px arrows 全部可见。768px token 区
  提前约 30px；两档 Timeline/toolbar 均无横向溢出。Token/Word、marker、special/generation、搜索跳转与 320/360px 全站触控相邻
  回归通过，Timeline Axe WCAG A/AA 保持零违规。
- 完整功能 E2E 108 passed（固定 8 workers，32.3s），production 性能套件 5 passed（38.6s）；2400-token 搜索/hover/窗口化、
  20 万 cell、首屏与资源回收门槛未回退。最终 build：主入口 322.41 kB（gzip 84.09 kB）；CSS 203.87 kB
  （gzip 36.05 kB）；icons 28.92 kB（gzip 5.82 kB）；Compare 33.55 kB（gzip 9.03 kB）。
- 当前边界：Search、Granularity 和 Color 都是 Timeline 高频控制，仍直接可见；本轮没有把它们藏进 bottom sheet。23.9 的全站次级工具
  menu/sheet 收敛仍需逐 View 依据真实操作频率审计，不能用一个通用 overflow menu 牺牲矩阵高频效率。

### 2.94 Compact Mobile Metric Summary / Full Semantic Labels（2026-07-14）

- 推进 23.7 P1 的首屏视觉焦点与稳定字号层级。390px 完整首屏审计发现顶栏指标仍显示桌面长标签
  `Max safety proxy / Mean attention proxy`，两张卡都换成两行；已有紧凑 metric CSS 只在 `<=380px` 生效，常见 390px 设备刚好
  落在空档，三卡区域接近 82px 高并继续把 Token Timeline 向下推。
- `Metric` 新增显式 full/short label 契约：桌面保持完整标签，`<=520px` 视觉显示 `Safety max / Attention mean / NLA cosine`；
  root `aria-label` 始终使用 `Max safety proxy metric / Mean attention proxy metric / NLA cosine metric`，不以视觉缩写降低读屏、测试
  选择器或指标语义精度。两个视觉 label 均 `aria-hidden`，避免 accessible name 重复。
- 移动 metric card 统一为最小 58px、单行短标签、稳定 18px 数值和 8px gap；`<=380px` 只进一步收紧左右 padding 与 label 字号，
  不缩小关键数值。320/360px 三卡仍各宽于 80px，card/label `scrollWidth <= clientWidth`，无截断或横向滚动。
- 520/390/320px 真实截图确认 Safety max、Attention mean、NLA cosine 全部单行，三项值继续是首要视觉；390px metric 区稳定为
  58px，完整 topbar 从约 213px 降到约 202px。520px 品牌保持单行，390/320px 品牌自然换行但不与四个全局动作重叠。
- 320/360px 几何门禁新增 metric 高度、内部 overflow、短标签数量与完整 aria label 断言；全八 View + 390px 主工作区 Axe WCAG
  A/AA 零违规。完整功能 E2E 108 passed（固定 8 workers，31.7s），production 性能套件 5 passed（37.3s）；首屏、
  2400-token、20 万 cell 和资源回收门槛未回退。
- 最终 build：主入口 322.63 kB（gzip 84.15 kB）；CSS 204.18 kB（gzip 36.12 kB）；icons 28.92 kB（gzip 5.82 kB）；
  Compare 33.55 kB（gzip 9.03 kB）。
- 当前边界：short label 是空间受限下的同义重排，不改变 metric 定义或精度；更长的本地化语言可能需要基于翻译后的容器测试，
  不能假设英文短标签长度代表所有 locale。全站其他面板字号层级仍应按各自容器继续实景审计。

### 2.95 Whole-Tab Mobile View Pagination（2026-07-14）

- 深化 2.71 / 23.9 的移动 View 导航。390px 最新首屏实景发现，箭头虽已占独立 grid column、不再覆盖按钮，但
  `min-width: 108px + 72% viewport scroll` 会让第三个 Attention tab 只露出 `Attenti…`；点击 More 后 Previous 出现又缩窄
  tab viewport，滚动位置落在 Attention 中间，仍存在半截按钮文字。
- 860px 以下左右箭头现在始终占据稳定的 44px columns；边界方向保留为低强调 disabled control，中间页两侧均可用。tab viewport
  不再因 Previous/Next 按钮挂载或卸载改变宽度，焦点顺序也不会随 DOM 插入删除跳动。桌面继续隐藏两个控件。
- View tab 改为 mandatory snap 的整数页：`<=389px` 每页完整 2 个，390–520px 完整 3 个，521–700px 完整 4 个，
  701–860px 完整 6 个；统一 44px 高、13px 文字、15px Lucide 图标与紧凑 gap/padding。每个 tab 的文字
  `scrollWidth <= clientWidth`，不使用 ellipsis 或父容器裁切表达更多视图。
- More/Previous 从 72% viewport 改为完整 `clientWidth` 页滚动，保留 smooth/reduced-motion auto 分支；原生 swipe 继续可用。
  selected View 初始化/刷新改为计算当前 page size 并对齐页首，而不是只做最小 scroll-into-view，避免选中项完整但左右各露半项。
- 页首对齐首版使用外层 shell 坐标 `offsetLeft`，导致 Overview 初始多滚动约一个左箭头宽度、Previous 错误启用；现在统一减去首个
  tab offset，scrollLeft=0 与边界状态一致。该回归证明了 DOM 可见不等于滚动语义正确。
- 390px 实景：初始页完整显示 Overview/Residual/Attention，中间页完整显示 MLP/NLA/Patching；320px 初始页完整显示
  Overview/Residual，中间页完整显示 Attention/MLP。disabled arrow、tab、active outline 无重叠；768px 初始 6-tab 页完整。
- E2E 逐页检查所有相交 tab 必须完全位于 viewport、内部文字不溢出、44px arrows、URL 不变、终点焦点接续、Attribution Enter、
  reload 选中页、reduced-motion 与 main-header Axe WCAG A/AA。完整功能 E2E 108 passed（固定 8 workers，32.0s），production
  性能套件 5 passed（35.7s）；首屏、2400-token、20 万 cell 和 listener/DOM 回收门槛未回退。
- 最终 build：主入口 322.84 kB（gzip 84.24 kB）；CSS 204.39 kB（gzip 36.16 kB）；icons 28.92 kB（gzip 5.82 kB）；
  Compare 33.55 kB（gzip 9.03 kB）。
- 当前边界：分页箭头只移动可见 View 页，不直接选择 View；点击 tab 或 roving keyboard 才改变 URL/analysis。触控 swipe 可能停在
  浏览器 snap 决定的相邻页，但不会停在半个 tab；更复杂的页码或 View 自定义排序仍需真实使用证据。

### 2.96 Mobile Deep-Link Scroll Ownership（2026-07-14）

- 完成 23.1 P0 的“选择变化不造成整页跳动或滚动位置重置”移动端验收。390px 直接打开 Attention 时页面会自动落到约
  `scrollY=1551`，直接打开 MLP 时会落到约 `scrollY=2112`；用户进入页面后看不到顶栏、Run/Sample、Token Timeline 和 View
  导航，等同于丢失分析上下文。其余六个 View 保持 `scrollY=0`，因此问题不是路由恢复，而是两个深层可视化的挂载副作用。
- 根因是 Attention edge profile 与 MLP neuron profile 为了居中选中 token，在 `useEffect` 和 `ResizeObserver` 中调用
  `scrollIntoView({ block: "nearest", inline: "center" })`。目标横向轨道位于长页面下方，浏览器在处理 inline 居中的同时也把
  document 纵向滚动到该组件；组件局部可见性逻辑越过了自身滚动边界。
- 新增共享 `scrollElementInlineCenter` 辅助函数，仅根据目标按钮 `offsetLeft/offsetWidth`、容器 `clientWidth/scrollWidth` 计算并约束
  轨道自身的 `scrollLeft`。Attention/MLP 的首次选择、URL 恢复、ResizeObserver 尺寸变化继续让选中 token 横向居中，但不再调用
  document 级滚动 API；不改变用户主动打开锚点、Skip link 或 Quick action 的显式页面导航语义。
- 新增 390×844 深链接回归，逐一直接打开 Overview、Residual、Attention、MLP、NLA、Patching、Intervention、Attribution，等待视图
  与局部 effect 稳定后断言 `window.scrollY === 0`、Token Timeline 和顶栏可见。随后真实聚焦 Attention selected radio 并按 End，
  验证末端 token 成为 checked、轨道 `scrollLeft > 0`、document `scrollY` 保持不变，证明修复没有牺牲键盘可达性和内部跟随。
- 完整功能 E2E 109 passed（固定 8 workers，33.1s），production 性能套件 5 passed（38.0s）；常规首屏、2400-token、20 万 cell
  和 listener/DOM/Canvas 回收门槛未回退。最终 build：主入口 322.89 kB（gzip 84.27 kB）；CSS 204.39 kB
  （gzip 36.16 kB）；共享滚动辅助 chunk 0.16 kB（gzip 0.13 kB）；Attention 28.12 kB（gzip 8.67 kB）；MLP 25.15 kB
  （gzip 8.10 kB）。
- 当前边界：本轮约束的是组件挂载与局部 selected-item reveal，不禁止明确由用户触发的页面级导航。未来新增任何横向 rail/carousel 时，
  默认必须操作自身 `scrollLeft`；只有“跳到分析区域/锚点”这类显式命令才可调用 `scrollIntoView` 改变 document 位置。

### 2.97 Compact-Desktop Evidence Actions / Adaptive Inspector（2026-07-14）

- 深化 23.1、23.5 与 23.9 的中间宽度主流程。实景审计发现 861–1279px 使用两栏 workspace 时，右侧 Inspector 被排到完整
  analysis 后方，而紧凑 Pin / Compare / Inspector 操作条只在 `<=860px` 显示。1024px 首屏因此既没有并排 Inspector，也没有
  抽屉入口；Attention/MLP 等长视图需要滚过整段分析才能找到证据动作，破坏 `Evidence → Compare/Export` 主流程。
- 响应式契约现在统一为：`>=1280px` 保留 Run Library / Analysis / sticky Inspector 三栏；`<1280px` 隐藏页面末尾的重复 Inspector，
  在 Timeline 后显示粘性 Current evidence actions。操作条持续展示 token、layer、safety proxy，并提供三个稳定 44px 图标入口：Pin、
  Compare、Inspector；滚过长矩阵后固定在 `top: 8px`，不会遮挡顶栏或改变正常文档流。
- 操作条新增 `role="region" / aria-label="Current evidence actions"`，Pin/Compare accessible name 去除 mobile 限定，使 390px、平板和
  compact desktop 使用同一语义。三栏桌面继续只暴露右侧 Inspector，不产生重复 region 或重复操作焦点。
- 第一版直接复用原 560px mobile Inspector drawer，1024px 实景截图暴露其继承两列 Inspector 的 260px + 320px 最小列宽，内部发生
  横向溢出；初始 close-button 焦点还会横向滚动容器，裁掉 `Full provenance / Evidence details` 标题左侧。861–1279px 抽屉现改为
  `min(760px, 100vw - 32px)`，完整容纳 Evidence / Actions 两列并明确禁止横向滚动；`<=860px` 继续使用 560px 上限和单列布局。
- 新增 1024×768 E2E：断言 compact action region 位于 Analysis workspace 内、末尾 right panel 隐藏、深滚后 sticky y 为 7–10px、
  三个按钮均至少 44px；打开 Inspector 后检查 viewport 边界、full disclosure、`scrollWidth <= clientWidth`、标题不裁切、关闭焦点
  返回原入口，并对完整 drawer 执行 Axe WCAG A/AA。390px sticky、Pin/Compare/Inspector 与 chunk hydration 同步改用通用语义回归。
- 1024px 初始 action bar 与展开 Inspector 两张 Chromium 实景图确认无重叠、裁切或无意义横向滚动。完整功能 E2E 110 passed
  （固定 8 workers，33.2s），production 性能套件 5 passed（37.7s）；常规首屏、2400-token、20 万 cell 和资源回收门槛未回退。
  最终 build：主入口 322.92 kB（gzip 84.27 kB）；CSS 204.51 kB（gzip 36.16 kB）；icons 28.92 kB（gzip 5.82 kB）；
  Compare 33.55 kB（gzip 9.03 kB）。
- 当前边界：compact desktop 以显式 modal drawer 提供完整 Inspector，而不是同时保留页面末尾副本；这避免长距离滚动和双重焦点。
  `>=1280px` 仍以常驻三栏支持持续证据对照。未来若主分析最小宽度或侧栏密度变化，应以实际可用宽度而不是设备名称调整阈值。

### 2.98 Legible Attention Display Modes / Non-Blocking Context Feedback（2026-07-14）

- 深化 23.1、23.3 与 23.7 的“完整标签、稳定控件、反馈不打断操作”。对 390/768/1024/1440px 的八个 View 执行可见
  button/tab/label/heading `scrollWidth/clientWidth` 扫描，document 均无横向溢出；排除带外 badge、原生 select、visually-hidden
  input 和 Run Library 已显式 ellipsis 后，确认 1440px 三栏 Attention toolbar 的 `Difference` 是未被覆盖的真实裁切。
- 根因是 Attention 有六种 display mode，但 segmented control 固定 `repeat(5, 1fr)`：中央 Analysis 列约 796px 时 control 只有约
  274px，前五项各得 49px，`Difference` 需要 56px 并显示为 `Differe…`，第六个 Entropy 又独占第二行，形成失衡的 5+1 布局。
  现在统一改为 3×2 等宽 grid；Head / Difference / Mean 与 Max / Rollout / Entropy 两行对齐，全部标签完整，正常态和 signed
  Difference 态均不改变控件尺寸或顺序。
- 3×2 首版视觉截图进一步暴露：切换 Difference 后，底部 `Context updated` fixed toast 横跨主 Analysis 并盖住 zoom/pan/pin
  工具。通知现改为两列、最多两行的 250px 紧凑状态，861px 以上固定在左侧数据工具列范围（x=18–268），与主 Analysis
  起点（1440px 下 x=282）保留明确间隔；保持 `pointer-events: none`、1.9 秒退出和完整 live-log 文本。`<=860px` 继续位于
  app-shell 文档流中，不以 fixed overlay 遮挡窄屏内容。
- 新增 390/1024/1280/1440px E2E，在每个断点逐项断言六个 mode label、`scrollWidth <= clientWidth`、精确 3 columns × 2 rows；
  切换 Difference 后再次验证布局、选中语义和 document 零横向溢出，并计算 visible notice 与 Attention controls 的矩形交集必须
  为零。既有 context live region、自动退出、390px Run notice、reduced-motion 与 forced-colors 回归继续通过。
- 1440px Attention controls 截图确认 Difference/Entropy 完整且工具按钮无遮挡；全视口截图确认 notice 不再覆盖 Timeline、
  Analysis、矩阵或 Inspector。完整功能 E2E 111 passed（固定 8 workers，33.9s），production 性能套件 5 passed（36.9s）；
  常规首屏、2400-token、20 万 cell 与资源回收门槛未回退。最终 build：主入口 322.92 kB（gzip 84.27 kB）；CSS
  204.44 kB（gzip 36.14 kB）；Attention 28.12 kB（gzip 8.67 kB）；icons 28.92 kB（gzip 5.82 kB）。
- 当前边界：视觉 notice 是 transient confirmation，完整上下文始终由 `aria-live` log 保留；左侧 250px 只显示两行摘要，不把缩小
  字号或扩大 overlay 当作展示全部内部 selection 的手段。后续新增 segmented option 必须同步调整显式网格与跨断点标签门禁。

### 2.99 Read-Only Run Card Containment / Complete Source Badge（2026-07-14）

- 深化 23.2 与 23.7 的 Run 来源可判断性。跨宽度可见控件扫描发现 1440px 三栏侧栏的 recent read-only Run 主按钮
  `clientWidth=215 / scrollWidth=238`，heading 实际宽 260px 并从卡片两侧溢出；`BUNDLED | 2 SOURCES` badge 右侧在真实截图中
  被裁成 `2 SOUR…`。1024px 同样为 227/244，来源冲突虽然存在于 DOM，视觉上却不能完整确认。
- 根因是 `.recent-run-list button:last-child` 本意样式化 local/generated removable 行的 29px 删除按钮，但 bundled/remote read-only 行
  只有一个主按钮，该按钮同时也是 `last-child`，因此被错误移除 7px padding、应用 `place-items: center`，内部 flex heading 按固有宽度
  向两侧溢出。规则现限定为 `.recent-run-list > div.removable > button:last-child`，删除语义不再依赖宽泛结构选择器。
- 修复后 1024px 主按钮/heading/badge 分别为 228/228、214/214、104/104；1280/1440px 为 216/216、202/202、104/104，
  三层 `scrollWidth === clientWidth`。长 runId 继续在剩余空间中 ellipsis，但 source type、冲突数量、sample/model、dimensions、打开/
  更新时间和 `using bundled over workspace` 决策保持完整，不用牺牲 provenance 换取 ID 全显。
- 既有 bundled-over-workspace E2E 新增主按钮、heading、badge 全部位于父边界、内部零溢出与真实卡片截图；390px
  browser-over-workspace drawer 继续验证 local `2 sources`、两项 candidate、74px 主按钮、Axe WCAG A/AA 和 document 零横向溢出。
  local artifact import/switch/remove 回归同时通过，证明 `.removable` 的独立删除按钮仍保持原行为。
- 完整功能 E2E 111 passed（固定 8 workers，34.0s），production 性能套件 5 passed（35.5s）；常规首屏、2400-token、20 万 cell
  与资源回收门槛未回退。最终 build：主入口 322.92 kB（gzip 84.27 kB）；CSS 204.46 kB（gzip 36.14 kB）；icons
  28.92 kB（gzip 5.82 kB）；Compare 33.55 kB（gzip 9.03 kB）。
- 当前边界：read-only 行没有删除能力，也不渲染伪删除占位；removable 行继续为主按钮 + 29px 删除按钮双列。所有新 row action 必须使用
  明确 class/role 作用域，不能再用 `:last-child` 推断控件职责。

### 2.100 Single-Process Packaged Explorer / Out-of-Box Deployment（2026-07-14）

- 将生产运行方式从 Vite `7860` + FastAPI `7861` 两个开发进程收敛为 `safelens explorer` 单进程、单端口入口。FastAPI 在所有
  `/api` 路由之后托管构建后的 React 资源，支持任意分析 deep link 回退到 `index.html`；未知 `/api/*` 继续返回 JSON 404，不能被
  SPA fallback 静默伪装为成功页面。
- 静态资源采用职责明确的缓存策略：带 hash 的 `/assets/*` 使用一年 immutable，HTML 与 deep-link fallback 使用 no-cache；所有响应
  带 `nosniff`。静态路径通过 resolve + root containment 校验，不能读取 web root 外文件。
- 新增 `safelens explorer` 与 `safelens-explorer` 两个等价入口，默认 `127.0.0.1:7860`、自动打开浏览器并创建 artifact root。
  非本地 bind 必须显式 `--allow-remote`，CLI 同时警告平台没有内建认证或 TLS；headless 环境使用 `--no-browser`。
- 新增 `prepare_explorer_distribution.py`，在发包前构建前端并将 22 个生产静态资源与 Prompt/Attribution/NLA/Patching/Intervention
  五个 worker 同步进 Python 包。worker 查找同时支持源码仓库与 wheel，Prompt worker 的成功日志不再假设输出位于仓库根目录。
- CI 与 PyPI publish 在 Python build 前固定 Node 22、执行 `npm ci` 和 production build；`verify_explorer_wheel.py` 强制校验 HTML、
  CSS、JavaScript、五个 worker 和两个 CLI entry point，避免发布“安装成功但页面空白”或 job 启动后才发现脚本缺失的 wheel。CI
  还会实际构建非 root Docker image，并通过容器内 `/api/health` 和首页 smoke test 后才允许 package build job 通过。
- 新增 multi-stage Dockerfile：Node builder 生成前端，Python 3.12 runtime 仅安装 Explorer 包；运行时 UID 10001、`/data` volume、
  `/api/health` HEALTHCHECK、端口 7860。推荐映射为 `127.0.0.1:7860:7860`，公网部署必须在可信反向代理后补鉴权与 HTTPS。
- README 将普通使用与前端开发明确分开：使用者只需安装 `.[explorer]` 后运行一个命令；只有开发态需要 Vite/API 双进程。轻量安装
  完整支持可视化和 artifact 浏览，真实模型 jobs 明确要求 `.[explorer,models,attribution,nla]`，不把轻量容器误写成全模型运行环境。
- 验收门禁：后端/CLI 目标测试、完整 Python 回归、前端 111 项 E2E、5 项性能门禁、production build、wheel 内容验证、已安装 wheel
  的根页面/API/deep-link smoke test；Docker 在本机工具可用时执行 image build 和 health check。

## 3. 全局交互模型

### 3.1 统一 Selection Store

所有视图应共享唯一选择状态，避免组件各自维护不同上下文。

```ts
interface ExplorerSelection {
  runId: string;
  sampleId: string;
  view:
    | "overview"
    | "residual"
    | "attention"
    | "mlp"
    | "nla"
    | "attribution"
    | "patching"
    | "intervention";
  tokenIndex: number;
  sourceTokenIndex?: number;
  targetTokenIndex?: number;
  layer: number;
  component: string;
  nlaComponent?: "resid_post" | "attn_result" | "mlp_out";
  head?: number;
  neuron?: number;
  metric: string;
  normalization: "raw" | "normalized";
  pinnedItems: PinnedEvidence[];
}
```

建议使用 Zustand；在状态规模较小时也可先使用 `useReducer`。

### 3.2 URL 状态同步

以下状态应同步到 URL query，以支持刷新恢复和本地链接分享：

- run。
- sample。
- view。
- token。
- layer。
- component。
- head/neuron。
- metric。
- normalization。

### 3.3 跨视图联动

- Timeline hover → Heatmap 同列高亮。
- Heatmap hover → Timeline token 高亮。
- Attention cell → 同时选择 source 与 destination token。
- Evidence row → 只选择 token，不擅自切换视图。
- Inspector head → Attention view 定位对应 head。
- Inspector neuron → MLP view 定位对应 neuron。
- NLA row → 定位对应 token、layer、component。
- Pinned item → 恢复完整证据上下文，而不只是 token。

## 4. 通用 MatrixHeatmap

下一项最高优先级工作是实现统一的 `MatrixHeatmap` 组件，并复用于 Residual、Attention、
MLP、NLA、Attribution 和 Patching。

### 4.1 基础操作

- Hover tooltip。
- 单击选择。
- Shift+单击固定第二个对象。
- 框选 token/layer 范围。
- 缩放和平移。
- 固定行列。
- Reset zoom。
- Fit to data。
- 搜索并跳转到 token、head 或 neuron。

### 4.2 通用工具栏

```text
Metric | Component | Raw/Normalized | Scale | Filter | Compare | Export
```

具体操作包括：

- Metric 切换。
- raw/normalized 切换。
- linear/log scale。
- 色阶范围调整。
- threshold 过滤。
- token range 过滤。
- Pin selection。
- Compare selection。
- 导出 PNG/SVG/JSON。
- 复制 cache key。
- 复制可复现 Python 代码。

### 4.3 Tooltip 数据

每个单元格至少展示：

```text
Token text / token id / position
Layer / component
Raw value
Normalized value
Metric name
Cache key
Evidence class
Normalization
Warnings
```

### 4.4 渲染策略

```text
少于 5,000 cells：DOM
5,000–200,000 cells：Canvas
超过 200,000 cells：Canvas/WebGL + 分块和采样
```

## 5. Token Timeline

需要增加：

- prompt/reply 分区。
- special token 样式。
- evidence marker。
- Probe/Monitor 命中标记。
- generation step。
- selected response target。
- token range brushing。
- token 搜索。
- word-level 合并与 token-level 展开。
- 长文本虚拟滚动。
- Shift+点击选择范围。
- Cmd/Ctrl+点击加入比较。

增加着色指标选择：

```text
Safety proxy | Attribution | Residual norm | NLA fidelity | Probe score
```

## 6. Overview 视图

Overview 应作为结论页，但不能生成过度确定的安全结论。

建议使用结构化摘要：

```json
{
  "finding": "Token 10 has the highest residual safety-direction alignment.",
  "evidence_class": "derived_proxy",
  "confidence": "exploratory",
  "supporting_evidence": [],
  "contradicting_evidence": [],
  "limitations": [],
  "recommended_analysis": []
}
```

页面展示：

- Primary finding。（已完成：run-relative rank、derived class 与 exploratory confidence）
- Supporting evidence。（已完成：proxy 中点与正 causal effect 分组）
- Contradicting evidence。（已完成：proxy 中点、非正 causal effect 与缺失警告）
- Evidence class。（已完成：derived proxy / causal evidence 文本标记）
- Limitations。（已完成：calibration、causal 与 attribution 动态边界）
- Recommended next analysis。（已完成：Residual / Attribution / Patching 可跳转动作）
- Sample evidence graph。（已完成：三列桌面与 finding-first 移动结构）

## 7. Residual 视图

### 7.1 组件和指标

- `resid_pre / resid_mid / resid_post`。
- norm。
- direction alignment。
- cosine similarity。
- target logit contribution。
- raw/normalized。
- LayerNorm 前后切换。

### 7.2 Logit Lens

- 每层 target token logit。（已完成：Logit/Probability 双轨迹与精确摘要）
- 每层 top-k token prediction。（已完成：逐层 raw projection 明细与 source key）
- selected token rank 变化。（已完成：observed target 原始 rank + log display 轨迹）
- Layer × Vocabulary rank。（待后端提供 full-vocabulary rank artifact）
- Layer × Target logit。（已完成：共享 Layer 轴、selected marker 与键盘同步）

### 7.3 Residual Decomposition

- embedding。
- attention output。
- MLP output。
- accumulated residual。
- 单组件贡献。
- clean/corrupted residual delta。
- stacked contribution chart。

## 8. Attention 视图

### 8.1 二维矩阵

- 完整 destination × source attention matrix。
- causal mask。
- source/destination 双向高亮。
- 入边和出边切换。（已完成：Incoming row / Outgoing column edge profile）
- 行列点击。
- attention 值和 entropy tooltip。（已完成：persistent pair value、row entropy 与 source rank）

### 8.2 Head 操作

- Layer/head selector。
- mean/max 聚合。（已完成：retained-head 逐 cell 聚合、独立 provenance/metric 与回放）
- entropy-weighted 聚合。（已完成：stored entropy 逆权重、成员 head 与公式可追溯）
- 多 head 小倍图。（已完成：同层共享色阶、当前 destination 行熵/峰值摘要与键盘切换）
- head 差值矩阵。（已完成：同层 retained-head signed cellwise difference）
- attention rollout。（已完成：retained-head mean + identity residual、跨层 causal product 与 partial 全量回填）
- 风险关键词位置标记。（已完成：run-relative top-3 proxy 与 explicit monitor hit 双轴标记）

### 8.3 因果区分

Attention probability 只能作为描述性信息。界面必须与以下结果分开：

- Head ablation effect。
- Patching effect。
- SafetyHeadAttributor KL score。

## 9. MLP 视图

### 9.1 激活矩阵

- token × neuron activation matrix。
- 正负值发散色带。
- raw activation。
- absolute activation。
- normalized activation。
- threshold 过滤。
- neuron 搜索。

### 9.2 Neuron 分析

- top positive/negative neurons。（已完成：selected-token signed raw 双向排名与直接选择）
- top activating tokens。（已完成：profile 峰值与 token rail 可直接导航）
- activation profile 对比。（已完成：版本化 Pin 与严格 token 轴差值）
- neuron clustering。（已完成：Worker AGNES、absolute Pearson distance、signed orientation 与 sampled coverage）
- 对目标 token logit 的贡献。
- Probe weight contribution。
- neuron ablation effect。

必须明确区分：

```text
activation magnitude
logit contribution
probe contribution
causal ablation effect
```

## 10. NLA 视图

- NLA token timeline。
- Layer × Token fidelity heatmap。（已完成：Layer×Token×Component exact-match matrix）
- cosine/MSE/FVE 切换。（已完成：metric-aware threshold 与 source evidence）
- explanation 搜索。（已完成：token/component/explanation 组合检索）
- fidelity threshold 过滤。（已完成：矩阵保留、candidate review filter 与最差项定位）
- norm outlier 标记。（已完成：Tukey 1.5×IQR、双描边、tooltip 与文字 badge）
- profile/model/layer/d_model 兼容性检查。（已完成：逐条件 diagnostics，禁止 nearest-row substitution）
- 低保真警告。（已完成：review queue 计数、metric-aware threshold 与一键定位）
- explanation 与 residual/attention/MLP 联动。（已完成：精确 component selection、同 token/layer Activation context 入口）
- Run NLA job。（已完成：preflight、SSE 进度、取消、失败与 derived Run 回填）

不兼容时必须显示具体原因，不能使用附近 token 或 layer 的结果代替。

## 11. Attribution 视图

接入真实 attribution 方法：

- Captum Integrated Gradients。（已完成：target-specific job、raw values、baseline/steps/convergence provenance）
- Residual direction projection。（已完成：signed layer-token projection 与 accounting）
- Attention proxy。（已完成：unsigned aggregate proxy，明确 non-causal/no-target contract）
- Safety head ablation。
- Probe feature contribution。

交互能力：

- 方法切换和并排比较。（已完成：selected-token exact-row snapshots；跨尺度不生成 delta）
- target response token 切换。
- baseline 展示。（已完成：IG target/baseline/steps/convergence objective context）
- signed attribution。（已完成：发散矩阵、正负排名与 balance audit）
- attribution sum 检查。（已完成：positive/negative/net/cancellation，IG 优先 raw job values）
- raw/normalized 切换。（已完成：method-aware stored/raw 与 display normalization）

Signed attribution 使用发散色带：

```text
负贡献 ← 蓝色 — 0 — 红色 → 正贡献
```

## 12. Patching 与 Intervention

新增 Patching 视图：

1. 选择 clean sample。
2. 选择 corrupted sample。
3. 选择 metric。
4. 选择 residual/head/MLP patch 类型。
5. 运行 patch grid。
6. 显示 Layer × Token causal effect。
7. 点击单元格查看 patched output。
8. 对比 original、corrupted 和 patched generation。

展示指标：

- clean metric。
- corrupted metric。
- patched metric。
- absolute delta。
- recovery percentage。

Steering/Intervention 支持：

- 加载或训练 steering vector。
- scale slider。
- position 范围。
- 原始/干预输出对比。
- Probe score、logit 和 generation 变化。

## 13. Pin 与 Compare

Pin 应保存完整证据对象：

```text
run + sample + token + layer + component + metric + head/neuron + value
```

Compare Drawer 支持：

- token 对比。
- layer 对比。
- component 对比。
- head/neuron 对比。
- clean/corrupted prompt 对比。
- intervention 前后对比。
- 模型/checkpoint 对比。
- attribution 方法对比。

默认最多同时比较 4 个对象。

展示方式：

- 精确数值表格。
- 折线图。
- delta heatmap。
- attribution 并排图。
- attention matrix difference。
- generation output diff。

## 14. Inspector

Inspector 使用三层结构：

### Summary

- 当前对象。
- 核心值。
- evidence class。
- raw/proxy/causal。
- 一句话结论。

### Evidence

- cache key。
- shape。
- raw value。
- normalization。
- method。
- source artifact。
- warnings。

### Actions

- Pin。
- Compare。
- Open in view。（已完成：状态驱动推荐动作保留 selection 并聚焦目标 panel）
- Run attribution。（已完成：Configure/Open Attribution job 路由）
- Run NLA。（已完成：Configure/Open NLA job 路由）
- Run ablation。（已完成：路由到 causal Patching workflow）
- Export。

移动端使用底部抽屉：默认显示紧凑摘要，上滑后展开完整 Inspector。

## 15. 颜色语义规范

| 数据语义 | 颜色 |
|---|---|
| Safety proxy / positive risk | 红色 |
| Negative contribution | 蓝色 |
| Attention | 青蓝色 |
| MLP activation | 绿色 |
| NLA fidelity | 金色 |
| Causal effect | 红蓝发散或橙色强调 |
| Neutral norm/magnitude | 灰蓝色 |
| Unavailable | 灰色斜纹 |
| Selected | 深色描边 |
| Pinned | 金色底边 |

原则：

- 红色只用于安全风险或正向危险贡献。
- activation 高不代表风险高。
- attention 高不代表因果影响高。
- 所有 heatmap 必须有 legend。
- signed 数据不能强制压缩到 `[0, 1]`。

## 16. 数据与后端

### 16.1 Explorer Artifact Schema

```json
{
  "schema_version": "1.0",
  "run": {},
  "samples": [],
  "metrics": [],
  "artifacts": {
    "activations": "activations.safetensors",
    "attention": "attention.npz"
  }
}
```

每个 metric 记录：

- method。
- metric name。
- raw/normalized。
- normalization。
- units。
- source cache key。
- model/layer/component/shape。
- computed_at。
- warnings。

大型 activation 不放入 JSON，使用 safetensors、NPZ 或分块文件。

### 16.2 FastAPI

最小 API：

```text
GET    /api/runs
GET    /api/runs/{run_id}
GET    /api/runs/{run_id}/samples/{sample_id}
GET    /api/runs/{run_id}/heatmap
GET    /api/runs/{run_id}/activation
POST   /api/jobs/analyze
POST   /api/jobs/nla
POST   /api/jobs/attribution
POST   /api/jobs/patching
GET    /api/jobs/{job_id}/events
DELETE /api/jobs/{job_id}
```

任务进度优先使用 SSE。

## 17. 前端工程结构

将当前集中式页面拆分为：

```text
src/
  api/
  schemas/
  state/
    explorerStore.ts
    selection.ts
  components/
    MatrixHeatmap.tsx
    TokenTimeline.tsx
    EvidenceSummary.tsx
    Inspector.tsx
    CompareDrawer.tsx
    ViewToolbar.tsx
  views/
    OverviewView.tsx
    ResidualView.tsx
    AttentionView.tsx
    MLPView.tsx
    NLAView.tsx
    AttributionView.tsx
    PatchingView.tsx
```

增加：

- Zod 数据验证。
- Error Boundary。
- loading/error/cancelled 状态。
- frontend unit tests。
- Playwright E2E。
- screenshot regression。
- URL state tests。

## 18. 性能与可扩展性

- Token 列表虚拟化。
- Heatmap Canvas/WebGL 渲染。
- Activation 分块读取。
- Tooltip 按需加载。
- Hover debounce。
- Worker 中进行矩阵归一化、排序和聚类。（部分完成：MLP profile clustering 已进入有界 Worker）
- 缓存派生 metric。
- 大模型采样和 progressive rendering。

## 19. 安全和隐私

- 默认仅监听 `127.0.0.1`。
- 文件访问限制在 workspace。
- 防止路径穿越。
- 限制 artifact 上传大小。
- `trust_remote_code` 必须显式确认。
- 不在浏览器和 artifact 中持久化 HF token。
- 显示当前后端是否允许下载或执行远程代码。

## 20. 实施阶段

### Phase 1：可视化操作基础

1. 全局 Selection Store。
2. URL 同步。
3. 通用 MatrixHeatmap。
4. Tooltip、zoom、brush、range selection。
5. 完整 Pin 对象。
6. Compare Drawer。

### Phase 2：真实组件视图

1. Attention 二维矩阵。
2. Residual logit lens。
3. MLP token-neuron matrix。
4. Signed attribution。
5. NLA fidelity heatmap。

### Phase 3：运行和实验闭环

1. RunReport/Artifact 加载。
2. Prompt Runner。
3. Attribution job。
4. NLA job。
5. Activation patching。（已完成）
6. Intervention 前后对比。（已完成）

### Phase 4：规模与质量

1. Canvas/WebGL。（通用 MatrixHeatmap 与 Attention/MLP/Attribution/NLA Canvas 已完成）
2. 虚拟化和分块读取。（Timeline/Matrix viewport、chunk 协议、Run 惰性加载、partial hydration、相邻预取和
   JSON sidecar 物理分块已完成；二进制 range backend 与大 artifact 基准待实现）
3. 完整键盘和无障碍支持。（Matrix/Timeline、View/Layer roving navigation、modal focus trap、移动端
   bottom sheet、全视图 Axe WCAG A/AA、forced-colors 和长表单错误关联已完成；多读屏器与真实 Windows
   High Contrast 设备验收待完成）
4. E2E 与视觉回归。
5. 大模型性能测试。

## 21. 第一阶段验收标准

- 所有视图共享同一个 selection state。
- 刷新页面后能够恢复当前 run/sample/view/token/layer。
- Heatmap 支持 hover、click、zoom、brush 和 reset。
- Heatmap 可切换 raw/normalized，并始终展示 legend。
- Tooltip 包含 raw value、metric、cache key 和 evidence class。
- Pin 保存完整上下文。
- Compare 可同时比较 2–4 个对象。
- Evidence 点击不会意外改变 view。
- 桌面、中等宽度和移动端无重叠或横向溢出。
- 关键交互有 Playwright 覆盖。
- 所有导出结果包含 provenance。

## 22. 立即执行项

下一项实现目标：

> 在现有 JSON sidecar 物理分块上建立可重复的大 artifact 性能基准，记录请求数、首屏可用时间、矩阵首次
> 可交互时间、hover 延迟、取消响应、服务端峰值内存和浏览器峰值内存；随后实现 full sample 从 blocks
> 校验重组、旧 source SHA block 垃圾回收，并评估 safetensors/NPZ + HTTP range backend。任何新 backend
> 都必须保留现有 metadata/chunk schema、ETag、checksum、路径隔离和 legacy embedded JSON fallback。

## 23. 可视化与交互深化优化清单

本节集中记录平台下一轮“美观、直观、可操作”的优化方向。原则是先消除理解和操作阻力，
再增加高级分析能力；视觉升级必须服务于研究判断，不能用装饰掩盖数据语义。

优先级定义：

- `P0`：阻碍主流程或容易造成误判，应优先处理。
- `P1`：显著提升高频分析效率，应在数据面稳定后完成。
- `P2`：增强深度研究和规模化使用能力。
- `P3`：长期高级能力。

### 23.1 信息架构与主流程（P0）

- 固定主流程为 `Run/Sample → View → Layer/Token → Evidence → Compare/Export`。
- 顶栏只保留全局对象：Run、Sample、后端状态、导入、导出和全局帮助。（全局 Help / Quick actions 已完成：见 2.85）
- 视图内工具放在对应 View Toolbar，不把局部操作堆到全局顶栏。
- 当前 Run、Sample、View、Layer 和 Token 必须在首屏内可确认。（已完成：见 2.42、2.71、2.72）
- 选择发生变化时，只更新相关区域，避免整个页面跳动或滚动位置重置。（已完成：见 2.96）
- 对可能改变分析上下文的操作显示明确反馈，例如“已切换至 Layer 8 / Token 14”，且反馈不遮挡主分析操作。（已完成：见 2.61、2.98）
- 首次进入某个空视图时展示可执行的空状态，不展示营销式说明页。（高级实验视图已完成：见 2.86）

验收标准：

- 新用户不阅读文档也能完成选择样本、定位 token、查看证据、Pin 和 Compare。
- 任意时刻都能在两次操作内切换 Run 或返回 Overview。（已完成：见 2.85）
- 页面中不存在两个含义不明的“当前 token”或“当前 layer”。
- 浏览器前进、后退和刷新不会丢失当前分析上下文。（已完成：见 2.60）

### 23.2 Run Library 与数据来源（P0）

- 统一展示 `Bundled / Local import / Workspace API` 三类来源，并使用文字加图标标识。（已完成：见 2.62）
- 明确显示后端 `connecting / ready / offline / error / cancelled` 状态。（已完成：见 2.8、2.66）
- 加载时提供 Cancel，失败时提供 Retry；失败不能阻塞 bundled/local 数据。（已完成：见 2.8、2.66）
- Run 列表支持按模型、run id、sample id、时间和来源搜索或过滤。（已完成：见 2.29、2.65）
- 最近使用项显示 token 数、layer 数、模型、更新时间和数据来源。（已完成：见 2.64）
- 相同 `runId + sampleId` 去重，来源冲突时显示来源优先级和覆盖说明，窄侧栏中来源 badge 仍完整。（已完成：见 2.62、2.99）
- 删除仅作用于浏览器本地导入项，不对 workspace artifact 暗示可写能力。（已完成：见 2.67）
- Artifact 校验失败显示字段路径、错误类型、期望 shape 和实际 shape。（已完成：见 2.65）

验收标准：

- API 不可用时仍可完整使用 bundled 和 local import。（已完成：见 2.66）
- Retry 成功后无需刷新页面即可出现 workspace runs。（已完成：见 2.66）
- URL 指向远端 run 时，加载期间不会提前回退并覆盖 URL。（已完成：见 2.8）
- 所有来源切换均不会残留上一样本的 token、head、neuron 或 active Pin marker 上下文；跨 Run Compare snapshots 按设计保留。（已完成：见 2.92）

### 23.3 MatrixHeatmap 操作一致性（P0）

- Residual、Attention、MLP、NLA、Attribution 和 Patching 复用相同的缩放、框选、
  Reset、Fit、legend 和 tooltip 交互语法。（已完成：见 2.63、2.69、2.70、2.76）
- 单击表示主选择；Shift+单击固定第二对象；Cmd/Ctrl+单击加入比较。（已完成：见 2.5、2.74）
- 支持触控板滚轮缩放、拖拽平移、框选范围和双击恢复。（已完成：见 2.63、2.76）
- 行列标题保持可见；长 token 文本截断但 tooltip 展示完整文本、id 和 position。（已完成：见 2.68、2.69）
- tooltip 避开鼠标和视口边缘，不遮挡当前单元格；键盘聚焦时也能打开。（已完成：见 2.69）
- raw、normalized、signed、absolute 的色阶和 legend 同步变化。（已完成：见 2.70）
- 对 signed 数据固定零点并使用发散色带；对 unavailable 使用斜纹而不是数值颜色。（已完成：见 2.49、2.70）
- 超大矩阵先显示低分辨率概览，再逐步加载当前视口，避免空白等待。（已完成：见 2.28）

验收标准：

- 同一操作在所有矩阵视图中的行为和图标位置一致。
- zoom、filter、metric 切换不会改变当前选择或造成布局位移。（已完成：见 2.63、2.70）
- 所有可见颜色都能通过 legend 解释，且 tooltip 可看到精确原始值。（已完成：见 2.69、2.70）
- 桌面和移动端均不存在 tooltip、工具栏或矩阵互相遮挡。（已完成：见 2.42、2.69、2.74）

### 23.4 Token Timeline 与跨视图联动（P1）

- 明确区分 prompt、assistant reply、special token 和 generation step。（已完成：见 2.89）
- Token Timeline 与 heatmap 使用同一 token selection，不维护第二套状态。
- hover 只做临时高亮，click 才改变选择，避免探索时上下文频繁跳动。
- 支持 token 搜索、前后导航、范围 brushing、word/token 两级展示和长文本虚拟滚动。
- 对风险、probe、monitor、attribution 和 pinned evidence 使用不同 marker，不只依赖颜色。（已完成：见 2.90）
- Attention cell 同时高亮 source 和 destination；其他 evidence row 只更新其语义对应对象。
- 切换视图时尽量保留兼容的 token/layer；不兼容项必须显式重置并说明原因。

验收标准：

- Timeline、矩阵、Inspector 三处对当前 token 的显示始终一致。
- hover 不改写 URL，click 后 URL 与视图同步。
- 2000 个以上 token 时仍可流畅滚动和定位。（2400-token production 基准已完成：见 2.84）

### 23.5 Inspector 与证据可信度（P0）

- Inspector 固定为 `Summary / Evidence / Actions` 三层，默认先展示结论和证据类型。
- 每项结论必须显示 `raw / derived proxy / safety output / causal evidence`。
- 展示 raw value、normalized value、单位、方法、normalization、cache key、shape、来源和警告。
- proxy 不使用“导致”“证明”等因果措辞；attention probability 不与 ablation effect 混排。
- unavailable、incompatible、not computed 和 failed 使用不同状态，不统一写成 N/A。
- 提供复制 cache key、复制复现实验信息、Pin、Compare 和导出操作。
- 移动端使用底部抽屉，默认紧凑摘要，上滑展开完整 provenance；compact desktop 同样保留就近抽屉入口。（已完成：见 2.87、2.97）

验收标准：

- 用户能在 Inspector 中判断一个值从哪里来、如何归一化、是否属于因果证据。
- 任意 unavailable 状态均提供具体原因和下一步动作。
- 所有导出对象携带与界面一致的 provenance 和 warning。（已完成：见 2.88）

### 23.6 Pin、Compare 与分析回溯（P1）

- Pin 保存完整 selection snapshot，并显示清晰的 run/sample/token/layer/component 摘要。
- Compare Drawer 支持 2–4 项，固定首项为 baseline，并允许更换 baseline。
- 只有相同 metric、normalization 和 evidence class 才默认计算 delta。
- 不同尺度仍可并排查看，但必须显示“不可直接比较”，不生成误导性差值。
- 支持 attention difference、signed attribution difference、layer curve 和 generation diff。
- 从 Compare 点击对象可恢复原始上下文，且不丢失 Drawer 中其他项目。
- 提供清空、单项移除和导出 comparison artifact。

验收标准：

- Compare 中每个数字都能追溯到具体 Run/Sample 和 cache key。
- 恢复 Pin 后 view、token、layer、head/neuron、metric、normalization 全部一致。
- 跨 run/sample 比较不会混用 token position；需按 token id/text 对齐或明确标记未对齐。

### 23.7 视觉层级与界面质感（P1）

- 使用中性背景、清晰分隔和少量语义强调色，避免整页单一色相。
- 主标题、面板标题、指标值、辅助文本建立稳定字号层级，不使用视口宽度缩放字体。（全站数值基础见 2.75；移动指标摘要见 2.94）
- 卡片仅用于可重复证据项、工具面板和抽屉；页面区块使用无框布局。
- 统一按钮高度、图标尺寸、输入框宽度、8px 以内圆角和 focus ring。
- 图标按钮使用现有图标库，并为不熟悉的图标提供 tooltip 和 `aria-label`。
- loading 使用骨架或局部进度，不让完整页面闪烁；成功反馈轻量且不打断操作。（已完成：视图/chunk 见 2.91；长任务见 2.80）
- 风险红色、负贡献蓝色、attention 青蓝、MLP 绿色、NLA 金色和 unavailable 灰色
  必须在全站保持同一语义。（已完成：见 2.49、2.70、2.75）
- 数字使用等宽或 tabular numerals，精度按 metric 统一，不在同表格混用小数位。（已完成：见 2.75、2.77）

验收标准：

- 首屏视觉焦点落在当前数据与主分析区域，而不是装饰或说明文字。
- 1440px、1024px、768px、390px 视口无重叠、截断和无意义横向滚动。
- 去除颜色后，仍能通过文字、形状、图标和描边区分关键状态。

### 23.8 Loading、错误与任务状态（P0）

- 所有异步操作统一使用 `idle / loading / ready / empty / error / cancelled` 状态模型。
- 网络错误、artifact 错误、兼容性错误和计算失败分别展示，不使用笼统的“加载失败”。（Workspace/artifact 见 2.65、2.66；五类 job 见 2.81）
- 错误区域保留当前可用数据，并提供 Retry、Cancel、查看诊断或切换本地数据。（Workspace 与五类 job 已完成：见 2.66、2.81）
- 长任务显示阶段、完成比例、已用时间和可取消状态；任务完成后保留结果入口。（五类 SSE job 已完成：见 2.80）
- 用户切换 Run/Sample 时取消过期请求，禁止旧响应覆盖新选择。
- Error Boundary 只隔离故障视图，不让单个图表错误拖垮整个平台。（分析视图与 Compare modal 已完成：见 2.78、2.79）

验收标准：

- 人为断开 API、返回错误 schema、取消请求和快速切换 run 均有 E2E 覆盖。（Workspace、job SSE 与五类取消已完成：见 2.66、2.80、2.81）
- 不存在无限 spinner；任何 loading 最终进入 ready、empty、error 或 cancelled。（视图与 Compare 模块已完成：见 2.78、2.79）
- 失败后用户无需刷新整个页面即可恢复。（视图/Compare lazy fault 与 job submit/execution 已完成：见 2.78、2.79、2.81）

### 23.9 键盘、无障碍与移动端（P1）

- 为 Run/Sample selector、View tabs、Token Timeline、MatrixHeatmap 和 Drawer 建立可预测 Tab 顺序。（移动 View tab 整页导航见 2.95）
- 支持方向键移动 token/cell，Enter 选择，Space Pin，Escape 关闭 tooltip/drawer。（已完成：见 2.5、2.15、2.73、2.74）
- 所有焦点状态清晰可见，modal/drawer 打开时管理 focus trap 和返回焦点。（Compare 正常态与错误态已完成：见 2.15、2.79）
- 文本与背景、状态色和 focus ring 满足 WCAG AA 对比度。
- 不用颜色作为唯一编码；图表状态同时提供文字、图标或纹理。
- 移动端将次级工具放入 menu/bottom sheet，保留选择、Pin、Compare 等高频操作。（Timeline 高频工具见 2.93；证据动作与
  861–1279px Inspector 入口见 2.97；全站仍继续）
- 触控目标至少 44×44px，矩阵手势与页面滚动之间不发生冲突。（已完成：见 2.42、2.63、2.71、2.76）

验收标准：

- 只使用键盘可以完成一次完整分析和 Pin/Compare 流程。（已完成：见 2.83）
- 390px 宽度下不遮挡当前 token、legend、主要操作和错误消息。（已完成：见 2.42、2.69、2.71）
- 使用 prefers-reduced-motion 时关闭非必要动画。（已完成：见 2.82）

### 23.10 性能和大数据体验（P2）

- 根据 cell 数量自动选择 DOM、Canvas 或 WebGL，不要求用户理解渲染模式。
- token 列表、长表格和 neuron 列表虚拟化；矩阵仅渲染视口和缓冲区。
- 大 artifact 使用 safetensors/NPZ 分块读取，支持 range request 和按需解码。
- 归一化、聚类、排序和采样放入 Worker，主线程只负责交互与绘制。
- 对同一 run/sample/metric/range 缓存派生结果，并在数据版本变化时正确失效。
- 首屏优先加载 metadata、timeline 和 overview，再加载高成本矩阵。
- 记录首屏时间、矩阵首次可交互时间、hover 延迟、内存峰值和取消响应时间。

目标指标：

- 常规样本首屏可用时间小于 2 秒。
- 可见矩阵交互保持接近 60 FPS，hover 反馈小于 100ms。
- 20 万 cells 不冻结主线程；取消操作在 300ms 内给出界面反馈。
- 长时间切换视图和 run 后无持续增长的事件监听、Canvas 或请求。

### 23.11 高级研究闭环（P2–P3）

- Prompt Runner：参数、seed、模板、模型和生成结果形成可复现 RunReport。
- Attribution/NLA/Patching job：提交、排队、SSE 进度、取消、失败诊断和结果回填。
- Patching：clean/corrupted 配对、Layer×Token causal effect、recovery percentage 和输出 diff。
- Intervention：steering vector、scale、position range、原始/干预 generation 和指标变化。
- 跨 checkpoint/run 比较：共享 token 对齐、layer 映射和 incompatible 提示。
- Evidence graph：连接 finding、supporting、contradicting、proxy 和 causal evidence。（已完成：见 2.46）
- 分析会话导出：保存选择、Pin、Compare、筛选器和 artifact 版本，支持完整回放。

验收标准：

- 每个后端任务均可取消、重试并关联到明确的 Run/Sample。
- 任务结果不能静默替换当前数据，必须显示方法、版本、target 和 baseline。
- patching/intervention 的因果结果与描述性 proxy 在视觉和文案上明确分区。

## 24. 推荐实施顺序

按以下顺序推进，避免同时改动过多交互契约：

1. 完成只读 FastAPI 数据面及 Run Library 远端状态，确保离线回退稳定。
2. 统一 loading/error/cancelled 状态和请求取消，补齐错误恢复 E2E。
3. 收敛顶栏、View Toolbar、Inspector 的职责，完成首屏信息层级优化。
4. 统一 MatrixHeatmap 操作语法，补 Shift/Cmd 选择、平移、固定行列和键盘操作。（已完成）
5. 深化 Token Timeline 联动，并完成跨 run/sample Compare 的安全对齐。（已完成）
6. 完成移动端 bottom sheet、键盘导航、对比度和视觉回归。
7. 接入 Prompt Runner、SSE jobs、Attribution/NLA/Patching 闭环。
8. 最后实施 Canvas/WebGL、虚拟化、分块读取和大规模性能基准。

每一步均要求同时完成：实现、数据语义检查、Playwright E2E、桌面/移动端截图检查、
构建和 Python 回归；未通过验收标准的功能不进入下一优先级。

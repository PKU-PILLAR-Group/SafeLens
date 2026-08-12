# SafeLens 项目交付时间线与验收追踪

## 1. 计划基线

- 计划起点：2026-08-12。
- 功能冻结目标：2026-10-31。
- Release Candidate：2026-12-18。
- 最终验收目标：2027-01-15。
- 主要范围：SafeLens 核心库、Local Explorer、本地真实模型任务、可复现实验与交付材料。
- 排期假设：1 名 ML/后端工程师、1 名前端/全栈工程师、0.5 名测试与文档支持，至少
  1 张可运行 Qwen2.5-7B BF16 的 GPU。单人开发时建议将时间整体放大 1.5 至 2 倍。

本计划以“验收证据可重复生成”为完成标准，不以页面出现按钮或已有缓存文件作为完成标准。
缓存结果可用于复现和离线演示，但必须标明来源、模型、版本、参数和生成时间。

## 2. 项目要求与交付指标

| ID | 项目要求 | 最终交付指标 | 主要验收证据 |
| --- | --- | --- | --- |
| D1 | 同一 GitHub 仓库内的独立本地交互模块 | `safelens explorer` 单进程启动，默认只监听 `127.0.0.1:7860`；wheel 和 Docker 均可部署 | 干净环境安装记录、`/api/health`、首页和 deep-link smoke test |
| D2 | 用户通过 Chat 完成分析 | 支持多轮上下文、对话恢复与删除、模型选择、1-512 输出长度、Retry/Cancel；固定 20 条真实模型用例成功率不低于 95% | Chat E2E、任务日志、生成 artifact、5 轮连续对话录像或 trace |
| D3 | 至少三类关键神经组件可视化 | Attention heads、Residual/Logit Lens、MLP/feature activation 三类均使用真实模型数据；NLA/J-Lens 作为解释层补充 | golden run、组件 provenance、截图、数值抽查脚本 |
| D4 | 至少三类用户交互操作 | 点击/聚焦 token 或 cell、按 layer/head/token/component 筛选、搜索/浏览 feature-linked evidence 均可完成并保持上下文一致 | Playwright 任务流、URL/session 回放、键盘操作验证 |
| D5 | 核心研究方法形成闭环 | Input Attribution、Steering、NLA、J-Lens、Attention 均有兼容性检查、提交、进度、取消、重试、结果回填；Patching/Intervention 保留高级入口 | 每类 job 的成功、失败、取消和重试 artifact；方法版本与参数记录 |
| D6 | 结果真实、可解释、可复现 | raw、derived proxy、safety method output、causal evidence 明确区分；不跨 token/layer/model 借用结果；分析 session 可导出和回放 | Schema 校验、golden artifact diff、provenance 审计、导出回读测试 |
| D7 | 大数据与性能可用 | 缓存工作台首屏小于 2 秒；hover 小于 100 ms；20 万 cell 不冻结；2400 token 可定位；Cancel 300 ms 内有 UI 反馈 | production performance suite、浏览器 Performance trace、内存与资源回收报告 |
| D8 | 质量、可访问性和安全 | Python、前端 E2E、性能、Ruff、format、mypy、wheel 校验全部通过；390-1440 px 无溢出；WCAG AA 自动检查无阻断问题；文件访问限定在 artifact root | CI 报告、Axe、真实设备检查表、安全测试与威胁模型 |
| D9 | 文档和最终演示可交付 | 安装、模型准备、方法限制、故障排查、演示脚本和验收报告完整；离线 artifact 演示与在线真实模型演示均可重复 | MkDocs、发布包、演示手册、验收矩阵、最终测试报告 |

验收中 D3 和 D4 直接覆盖项目对“至少三类关键神经组件可视化”和“至少三类交互分析
操作”的要求。D1、D2、D5-D9 将展示原型提升为可安装、可运行、可核验的项目交付物。

## 3. 当前状态审计

### 3.1 已有能力

Local Explorer 当前已经具备以下产品路径：

1. Chat 首页、多轮上下文、对话历史恢复与删除、模型和最大输出 token 配置。
2. Prompt GPU/CPU worker、SSE 进度、取消、Retry 和生成 artifact 回填。
3. Chat 内 Steering、Input Attribution、Explanation 和 Attention 四个聚焦入口。
4. Explanation 内按 layer/token 运行或查看 NLA 与 J-Lens。
5. 高级工作台内的 Overview、Residual、Attention、MLP、NLA、Attribution、Patching、
   Intervention 八类视图。
6. Token Timeline、搜索、Token/Word 聚合、证据 marker、Pin、跨 Run Compare、Inspector、
   URL 与 session 回放。
7. Local/workspace/bundled artifact、JSON sidecar 分块、metadata-first hydration 和惰性读取。
8. 单进程 Python 包部署、wheel 静态资源校验、Docker、localhost 与路径边界保护。

### 3.2 真实模型支持边界

| 能力 | 当前状态 | 验收前缺口 |
| --- | --- | --- |
| Prompt | TinyGPT2 与 Qwen2.5-7B 可走真实 worker | 批量稳定性、生成回复 token 的完整 trace、固定硬件性能报告 |
| 多轮 Chat | 前端和请求上下文已支持 | 5 轮真实 Qwen 回归、长上下文预算和截断提示审计 |
| Input Attribution | Captum job、目标 token 选择和 signed 结果已有 | Qwen 固定用例校准、目标/基线/步数的交付级说明 |
| Steering | Contrastive intervention、建议和自定义方向、前后输出 diff 已有 | 建议标签库质量、强度扫描、失败边界和量化效果指标 |
| NLA | Qwen2.5-7B L20 AV/AR 可真实运行，AV/AR revision 已分别固定 | 多 prompt 稳定性、回复 token 支持和 fidelity 阈值 |
| J-Lens | Qwen2.5-7B 公共 checkpoint 已接入并在 L20 GPU 实跑；TinyGPT2 保留为 smoke | 多 prompt 稳定性、性能报告和 golden artifacts |
| Attention | 真实 pattern、layer/head/token 交互已有 | 生成器目前主要保留高质量 head 子集；全 head artifact 和 7B 规模读取待补 |
| MLP | retained neuron 的 signed profile 与千级前端虚拟化已有 | 全 neuron artifact、分页和二进制 range 读取待补 |
| Patching | 可取消 job 与 Layer x Token 因果矩阵已有 | 真实 Qwen 配对用例、token 对齐失败集和数值复核 |
| Intervention | 原始/steered 输出、token diff 与指标变化已有 | 与 Chat Steering 合并验收口径、方向版本和强度 sweep |

### 3.3 当前质量基线

- 最近一次 Python 全量基线：1025 passed、53 skipped。
- 最近一次 Chat 首页定向基线：17 passed。
- `plans.md` 记录的完整前端基线：124 项 E2E、5 项 production performance gate。
- 当前生产构建、Ruff 和 wheel 资源校验已有成功记录。

完整前端基线是在 Chat 最近改版前后持续演进形成的记录，2026-08 的第一项门禁必须在
当前 commit 上重新执行并归档，不能只引用历史数字。

### 3.4 尚未完成的关键交付

1. Qwen2.5-7B 上覆盖 Chat、回复 token、NLA、Attribution、Steering、Attention 的固定验收集。
2. Qwen J-Lens/NLA 的多 prompt golden 集、耗时/显存记录和离线 cache 预热流程。
3. 全 head、全 neuron 与 safetensors/NPZ 二进制 range backend。
4. 真实浏览器、读屏器和 Windows High Contrast 人工验收。
5. 面向最终交付的模型 revision、硬件、耗时、显存、随机种子和 artifact manifest。
6. 最终用户手册、验收报告、演示脚本、发布包和可重复的 clean-machine 安装记录。

## 4. 总体里程碑

| 里程碑 | 日期 | 核心结果 | 放行条件 |
| --- | --- | --- | --- |
| M0 基线冻结 | 2026-08-31 | 当前功能、验收集、模型矩阵和已知缺口冻结 | P0 bug 为 0；当前 commit 全量门禁归档 |
| M1 真实模型闭环 | 2026-09-30 | Qwen Chat 与四项核心分析形成稳定真实链路 | 20 条用例成功率不低于 95%；5 轮上下文通过 |
| M2 方法与可视化冻结 | 2026-10-31 | NLA/J-Lens/Attribution/Steering/Attention 交付口径冻结 | D3-D6 的 golden evidence 全部可重放 |
| M3 规模与兼容性 | 2026-11-30 | 大 artifact、全组件数据、浏览器和设备验收 | D7、D8 性能和可访问性门禁通过 |
| M4 Release Candidate | 2026-12-18 | wheel、Docker、文档、演示和验收报告齐套 | clean-machine、离线和真实模型三套演示通过 |
| M5 最终验收 | 2027-01-15 | 修复验收问题并签署最终追踪矩阵 | D1-D9 全部有通过证据，无未豁免 P0/P1 |

## 5. 详细任务时间线

### 2026-08-12 至 2026-08-31：基线冻结与缺口清理

| ID | 时间 | P | 任务与功能 | 产物 | 对应指标 |
| --- | --- | --- | --- | --- | --- |
| B01 | 08-12 至 08-14 | P0 | 将 D1-D9 录入 issue/看板，给每项指定负责人、依赖和验收命令 | 可追踪验收矩阵 v1 | D1-D9 |
| B02 | 08-12 至 08-16 | P0 | 冻结支持矩阵：TinyGPT2 仅 smoke；Qwen2.5-7B 为主验收模型；Gemma 为 gated；J-Lens 单列 checkpoint | `supported-models` 表和限制说明 | D2、D5、D6、D9 |
| B03 | 08-15 至 08-20 | P0 | 建立 20 条 golden prompt：中英文、正常/风险、长短输入、多轮、目标 token、steering 对照 | 版本化 prompt 集与期望不变量 | D2、D5、D6 |
| B04 | 08-17 至 08-22 | P0 | 审计所有页面的 real/cached/bundled/unavailable 标签，补齐 model/revision/layer/component/seed/dtype/device | Provenance UI 与 artifact manifest | D6 |
| B05 | 08-18 至 08-24 | P0 | 对 Prompt、NLA、J-Lens、Attribution、Patching、Intervention 做成功/取消/Retry/失败矩阵回归 | Job 状态测试报告 | D2、D5、D8 |
| B06 | 08-21 至 08-26 | P0 | 清理生成 dtype、模型加载、任务竞态、对话删除和远端 history 恢复等阻断问题 | RC0 bugfix 集 | D2、D5、D8 |
| B07 | 08-24 至 08-28 | P1 | 当前 commit 重跑 Python、完整前端 E2E、performance、build、Ruff、format、mypy、wheel | 带 commit SHA 的基线报告 | D7、D8 |
| B08 | 08-28 至 08-31 | P0 | 评审 M1 范围并冻结界面信息架构；后续功能只能作为上下文分析入口，不再增加首页卡片堆叠 | M0 评审记录、冻结清单 | D2、D8、D9 |

M0 验收门禁：

- 干净环境可启动轻量 viewer；健康检查和首页均通过。
- 当前 commit 的完整质量门禁有归档结果。
- 所有展示值可判断是实时计算、历史 artifact 还是 bundled demo。
- P0 bug 为 0；P1 bug 有负责人和目标月份。
- J-Lens 明确显示 checkpoint 与模型匹配关系，不出现“TinyGPT2 lens 等同于 Qwen lens”的表述。

### 2026-09-01 至 2026-09-30：Qwen 真实模型与 Chat 闭环

| ID | 时间 | P | 任务与功能 | 产物 | 对应指标 |
| --- | --- | --- | --- | --- | --- |
| R01 | 09-01 至 09-05 | P0 | 固定 Qwen2.5-7B model revision、tokenizer revision、BF16/CUDA 环境和下载/cache policy | 可复现模型环境 manifest | D2、D6、D9 |
| R02 | 09-01 至 09-10 | P0 | 让每轮 assistant reply token 进入可分析 trace，保留 prompt/reply/source/generation step | 完整 turn artifact schema 与迁移 | D2、D3、D6 |
| R03 | 09-06 至 09-12 | P0 | 验证真实 5 轮 Chat，确保前序 user/assistant 内容按序进入模型并可恢复 | 多轮 trace 与 E2E | D2 |
| R04 | 09-08 至 09-14 | P0 | 长上下文和 token budget：默认 128、范围 1-512、达到模型上下文上限前提示，不静默截断 | 预算/截断 UX 和测试 | D2、D6、D8 |
| R05 | 09-10 至 09-18 | P0 | 在 Qwen golden prompts 上跑 NLA L20，记录 AV/AR revision、cosine、MSE、FVE、耗时和显存 | NLA golden artifacts | D5、D6 |
| R06 | 09-12 至 09-20 | P0 | 在回复中直接选择 target token 运行 Captum Attribution，验证 objective/baseline/steps 与 signed score | Attribution golden artifacts | D4、D5、D6 |
| R07 | 09-15 至 09-22 | P0 | 完成 Qwen Steering：匹配标签建议、自定义方向、scale/position、原始与 steered 输出差异 | Steering golden artifacts | D4、D5、D6 |
| R08 | 09-18 至 09-24 | P1 | 保存真实 Attention layer/head/token pattern，并将 prompt 和 reply token 轴严格对应 | Attention golden artifacts | D3、D4、D6 |
| R09 | 09-22 至 09-27 | P0 | 连续运行 20 条固定用例，统计成功率、首 token 延迟、总耗时、峰值显存、取消响应和失败类型 | Qwen 稳定性报告 | D2、D5、D7 |
| R10 | 09-26 至 09-30 | P0 | 修复 M1 阻断问题，完成真实模型演示脚本和回放 artifact | M1 Demo 及验收记录 | D2-D6、D9 |

M1 验收门禁：

- 固定 20 条 Qwen 用例成功率不低于 95%，失败均有结构化原因。
- 至少一个 5 轮对话可恢复；重新打开后每轮分析仍属于正确 parent run。
- assistant reply token 可点击，并可作为 NLA/Attribution/Attention 的目标或明确显示方法限制。
- Max 128 默认值生效；任何截断均有可见提示和 artifact 记录。
- NLA、Attribution、Steering 均有至少 5 条真实 golden artifacts。

### 2026-10-01 至 2026-10-31：研究方法和展示功能冻结

| ID | 时间 | P | 任务与功能 | 产物 | 对应指标 |
| --- | --- | --- | --- | --- | --- |
| A01 | 10-01 至 10-06 | P0 | NLA 批量/多 token 选择、fidelity 阈值、低保真队列和 exact layer/component 导航 | NLA 交付视图 | D4-D6 |
| A02 | 10-01 至 10-08 | P0 | 固化 Qwen J-Lens checkpoint manifest、许可证、镜像/cache 预热和算力预算 | 可复现 checkpoint manifest | D5、D6、D9 |
| A03 | 10-07 至 10-16 | P0 | 对 Qwen L20 J-Lens 建立多 prompt golden 集、性能门禁和外部 checkpoint 接入规范 | J-Lens 正式验收包 | D5、D6、D9 |
| A04 | 10-06 至 10-14 | P0 | Attribution 参数化：response target、objective、baseline、8-128 steps、signed normalization 与方法解释 | Attribution 完整面板 | D4-D6 |
| A05 | 10-09 至 10-18 | P0 | Steering suggestion 标签库按用户输入匹配，同时保留自定义方向；增加 scale sweep 和效果摘要 | Steering 方向库及评估集 | D4-D6 |
| A06 | 10-12 至 10-20 | P1 | Attention 支持 layer/head/token 浏览、incoming/outgoing、head compare 和明确 causal/proxy 区分 | Attention 交付视图 | D3、D4、D6 |
| A07 | 10-15 至 10-23 | P1 | 在 Chat 内以渐进披露方式接入 Residual、MLP 与 Patching 深入分析，不增加首页默认操作负担 | Chat contextual analyses | D2-D5、D8 |
| A08 | 10-18 至 10-26 | P0 | 统一原始/派生/安全方法/因果证据的颜色、标签、tooltip、Inspector 和导出字段 | Evidence semantics audit | D6、D8 |
| A09 | 10-22 至 10-29 | P0 | 完成“3 类组件 + 3 类交互”的正式验收脚本：真实权重、可点击、可筛选、可搜索、可导出 | Capability audit | D3、D4、D9 |
| A10 | 10-27 至 10-31 | P0 | 功能冻结，只保留性能、兼容性、文档与 bugfix 变更 | M2 冻结版本 | D1-D9 |

M2 验收门禁：

- Attention、Residual、MLP 三类真实组件可视化均有独立 golden evidence。
- 点击/聚焦、内部路径筛选、feature-linked evidence 搜索三类交互全部通过 E2E。
- NLA、Attribution、Steering 和 J-Lens 的支持边界、版本和失败原因清晰。
- 所有因果结论来自 Patching/Intervention 等因果任务，不把 attention 或投影 proxy 写成因果贡献。
- 功能冻结后不再新增一级导航或首页快捷卡片。

### 2026-11-01 至 2026-11-30：大 artifact、性能和兼容性

| ID | 时间 | P | 任务与功能 | 产物 | 对应指标 |
| --- | --- | --- | --- | --- | --- |
| S01 | 11-01 至 11-08 | P0 | 设计 Explorer artifact 1.1：二进制 tensor manifest、shape/dtype/checksum/range 与 1.0 兼容 | Schema 1.1 与迁移规范 | D6、D7 |
| S02 | 11-04 至 11-14 | P0 | 实现 safetensors/NPZ range backend、按需解码、越界与 checksum 校验 | 二进制分块 API | D6-D8 |
| S03 | 11-08 至 11-17 | P1 | 生成 Qwen 全 attention head artifact，前端按 layer/head 惰性加载 | 全 head 浏览 | D3、D4、D7 |
| S04 | 11-10 至 11-20 | P1 | 生成全 MLP neuron 索引，增加 neuron 分页、搜索和局部 profile 读取 | 全 neuron 浏览 | D3、D4、D7 |
| S05 | 11-15 至 11-22 | P0 | 完成真实 7B artifact、2400 token、20 万 cell、40 次视图切换的性能与资源回收基准 | 性能报告与 trace | D7 |
| S06 | 11-18 至 11-24 | P0 | GPU job queue、显存不足诊断、进程退出清理、cache 失效和并发请求隔离 | 稳定性测试集 | D2、D5、D7、D8 |
| S07 | 11-20 至 11-27 | P1 | Chromium/Firefox/WebKit 主流程兼容检查；390/768/1024/1440 px 视觉回归 | 浏览器与视口矩阵 | D8 |
| S08 | 11-23 至 11-30 | P1 | Windows High Contrast、NVDA/VoiceOver 至少各一条人工流程，补齐 keyboard/focus/error association | 人工无障碍报告 | D8 |

M3 验收门禁：

- 常规缓存样本首屏可用时间小于 2 秒，矩阵 hover 小于 100 ms。
- 20 万 cell 不阻塞主线程；2400 token 的搜索和定位可用。
- Cancel 操作 300 ms 内显示已取消反馈，worker 最终释放 GPU/进程资源。
- 40 次 view/run 切换后 listener、Canvas、DOM、request 和 heap 无持续增长。
- 二进制读取不能越过 artifact root，checksum 或 shape 不匹配时拒绝展示。

### 2026-12-01 至 2026-12-18：Release Candidate 与交付材料

| ID | 时间 | P | 任务与功能 | 产物 | 对应指标 |
| --- | --- | --- | --- | --- | --- |
| Q01 | 12-01 至 12-05 | P0 | 在新环境验证轻量 viewer、完整模型 extras、wheel 和 Docker 四种安装方式 | Clean-machine 安装记录 | D1、D8、D9 |
| Q02 | 12-01 至 12-08 | P0 | 编写用户手册：Chat、历史、模型、Max tokens、四项核心分析、导出和回放 | 用户文档 | D2-D6、D9 |
| Q03 | 12-03 至 12-09 | P0 | 编写运维与故障排查：GPU、cache、离线、dtype、checkpoint、端口和 worker 日志 | 运维手册 | D1、D5、D9 |
| Q04 | 12-05 至 12-11 | P0 | 形成两套演示：离线 artifact 5 分钟、Qwen 真实模型 15 分钟 | Demo 脚本、数据与截图 | D2-D6、D9 |
| Q05 | 12-07 至 12-12 | P1 | 邀请至少 5 名目标用户完成 Chat→token→analysis→compare/export 任务，记录成功率和误操作 | 可用性报告与修复清单 | D2、D4、D8 |
| Q06 | 12-10 至 12-14 | P0 | 安全审计：localhost、remote bind、路径穿越、symlink、超大文件、敏感 token 和导出内容 | 安全验收报告 | D8 |
| Q07 | 12-12 至 12-17 | P0 | 执行完整 CI、发布包、license/依赖、wheel 资源和 Docker health gate | RC 构建物 | D1、D7-D9 |
| Q08 | 12-18 | P0 | RC 评审：逐项展示 D1-D9 证据，冻结验收问题清单 | RC 签审记录 | D1-D9 |

建议的可用性目标：

- 5 名目标用户中至少 4 人无需开发者介入完成主任务。
- Chat→选择 token→运行一种分析→导出结果的中位完成时间不超过 8 分钟。
- 不出现将 cached demo 误认为本次实时计算的情况。
- 所有阻断性误操作在 RC 前修复；非阻断建议进入后续 backlog。

### 2026-12-19 至 2027-01-15：验收修复与最终交付

| ID | 时间 | P | 任务与功能 | 产物 | 对应指标 |
| --- | --- | --- | --- | --- | --- |
| F01 | 12-19 至 12-31 | P0 | 只处理 RC 发现的 P0/P1、数据正确性、安装和文档问题 | RC2 | D1-D9 |
| F02 | 01-01 至 01-06 | P0 | 在固定 A100 环境重跑 20 条 Qwen 集与所有 golden method artifacts | 最终真实模型报告 | D2-D7 |
| F03 | 01-03 至 01-08 | P0 | 重跑 Python、E2E、performance、Axe、build、mypy、wheel、Docker 全门禁 | 最终质量报告 | D7、D8 |
| F04 | 01-06 至 01-10 | P0 | 完成 API/Artifact schema、模型支持矩阵、方法限制和 changelog | 最终文档站 | D6、D9 |
| F05 | 01-09 至 01-12 | P0 | 生成最终 wheel、container、golden artifacts、验收演示包与 checksums | Release bundle | D1、D9 |
| F06 | 01-13 至 01-15 | P0 | 最终验收演示与 D1-D9 追踪矩阵签署；未完成项必须有书面豁免 | 最终交付报告 | D1-D9 |

## 6. 功能到指标追踪矩阵

| 展示平台功能 | 当前状态 | 计划任务 | 主要指标 | 最终验收动作 |
| --- | --- | --- | --- | --- |
| Chat 多轮与历史 | 已实现 | R02-R04、Q05 | D2、D6、D8 | 完成 5 轮对话，重启后恢复并删除其中一个对话 |
| 模型与 Max tokens | 已实现，需真实回归 | R01、R04、R09 | D2、D6 | 切换支持模型，验证默认 128 和显式截断提示 |
| Input Attribution | 已有真实 job | R06、A04 | D4-D6 | 直接点击回复 target token，运行 IG 并检查 signed attribution |
| Steering | 已有真实 intervention | R07、A05 | D4-D6 | 使用匹配建议和自定义方向，对比原始/steered 输出及参数 |
| NLA | Qwen L20 可真实运行 | R05、A01 | D5、D6 | 对 exact token/layer/component 运行，检查 fidelity 与 revision |
| J-Lens | Qwen L0-L26 已真实运行，L20 为默认 | A02、A03 | D5、D6、D9 | 使用固定 revision；模型、维度、层或 revision 不匹配时在 submit 前阻断 |
| Attention | 已有真实 retained heads | R08、A06、S03 | D3-D4、D6-D7 | 浏览 layer/head/token，核对 pattern shape、mask 与 source key |
| Residual/Logit Lens | 已实现 | A07、A09 | D3-D4、D6 | 查看逐层 top-k、target rank，并验证其标为诊断投影 |
| MLP neuron | retained neuron 已实现 | A07、S04 | D3-D4、D7 | 搜索 neuron、切 layer、点击 token 并读取 signed profile |
| Patching | 已实现高级 job | A07、S06 | D5-D6、D8 | 提交 clean/corrupted pair，查看 causal recovery 并取消一次任务 |
| Pin/Compare/Export | 已实现 | A08、A09、Q04 | D4、D6、D9 | Pin 两条证据、切 baseline、导出并重新导入 session |
| Run/Artifact Library | 已实现 | S01-S02、Q01 | D1、D6-D9 | 加载 1.0/1.1 artifact、处理损坏文件并验证离线回退 |

## 7. 每项任务的完成定义

功能只有同时满足以下条件才能标记完成：

1. 真实实现已合入，缓存或 mock 只作为明确标注的 fixture。
2. 输入、输出、模型、revision、token/layer/component 和指标语义经过校验。
3. 至少有单元/后端测试和一条用户路径 E2E；高风险方法包含失败与取消测试。
4. 1440 px 与 390 px 完成布局检查；交互控件满足键盘和 44 px 触控要求。
5. 相关文档、支持边界和错误排查已更新。
6. 验收证据包含 commit SHA、命令、环境、日志或报告位置。
7. 不引入未解释的性能回退、旧响应覆盖或跨 Run 数据污染。

## 8. 发布门禁命令

每个里程碑至少执行以下门禁；具体依赖版本写入该里程碑的报告。

```bash
pytest -q
python -m ruff check .
python -m ruff format --check .
python -m mypy src
mkdocs build --strict

cd apps/local_explorer
npm ci
npm run build
npm run test:e2e
npm run test:performance
```

发布候选还需执行：

```bash
python scripts/prepare_explorer_distribution.py
python -m build
python scripts/verify_explorer_wheel.py dist/safelens-*.whl
docker build -t safelens-explorer:rc .
```

真实模型门禁必须另行记录模型下载是否命中 cache、GPU 型号、CUDA/PyTorch/Transformers 版本、
dtype、峰值显存和总耗时，不能混入普通单元测试统计。

## 9. 风险与决策点

| 风险 | 最晚决策点 | 应对 |
| --- | --- | --- |
| Qwen J-Lens 上游 checkpoint 漂移或镜像不可达 | 2026-10-08 | 固定 Neuronpedia commit、预热 SafeLens cache、保留 TinyGPT2 smoke 与外部 checkpoint 接口 |
| GPU 或模型下载不稳定 | 2026-09-05 | 固定 revision 与镜像/cache；保留离线 golden artifacts；真实演示前做预热与健康检查 |
| 回复 token trace 增加显存和 artifact 体积 | 2026-09-10 | 只捕获用户选择的层/组件；设置最大 trace 长度；通过分块和 manifest 延迟读取 |
| 全 head/neuron 数据过大 | 2026-11-08 | 二进制 range、分页、按需解码；完整 tensor 不进入 JSON；保留摘要索引 |
| Chat 继续堆叠导致界面复杂 | 2026-08-31 | 首页只保留对话和核心入口；高级功能按当前 turn/token 渐进披露；功能冻结后不增一级导航 |
| 方法结果被误解为因果结论 | 持续门禁 | raw/proxy/method/causal 四级分类；Attribution/Attention/Logit Lens 不使用因果措辞 |
| 自动化通过但真实用户不会用 | 2026-12-12 | 至少 5 名目标用户的任务测试；记录完成时间、误操作和是否能识别缓存/实时结果 |
| 交付前范围继续扩大 | 2026-10-31 | 功能冻结；新需求只进入 post-release backlog，除非阻断 D1-D9 |

## 10. 最终交付包

最终验收应一次性交付：

1. SafeLens 源码与对应 commit/tag。
2. Python wheel、依赖说明和 SHA256。
3. 非 root Docker image/Dockerfile 与 health check。
4. 轻量离线 demo artifacts 和真实 Qwen golden artifacts。
5. 模型、NLA、J-Lens checkpoint 与 revision manifest。
6. 用户手册、开发文档、运维/故障排查和安全说明。
7. D1-D9 验收追踪矩阵与全部测试/性能/无障碍报告。
8. 5 分钟离线演示和 15 分钟真实模型演示脚本。
9. 已知限制、风险豁免、changelog 和后续 backlog。

## 11. 验收结论规则

- `通过`：D1-D9 均有当前 release commit 的可重复证据，且无未豁免 P0/P1。
- `有条件通过`：仅允许外部模型授权、gated checkpoint 或硬件不可用造成的条件项；必须提供
  离线 artifact、清晰限制和复验步骤。
- `不通过`：核心结果来自未标注 mock/cache、模型与 checkpoint 不匹配、无法一键启动、关键
  job 无法重试/取消、数据跨 Run 污染，或三类组件/三类交互要求未满足。

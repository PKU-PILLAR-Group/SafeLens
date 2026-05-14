# SafeLens Project Report

## 1. 项目概览

SafeLens 当前实现的是一个可插拔的模型安全分析基础设施。它的目标不是先写某一个具体安全算法，而是先建立统一的工程骨架，让后续的内生探针、运行时监测、输入或训练数据溯源、steering vector、FlagSafe 适配等模块可以按同一套接口接入。

当前仓库中的 Python 包名是 `SafeLens`，命令行入口是 `safelens`，项目发布名目前是 `safelens`。这意味着：

```bash
safelens run --config examples/config.yaml
```

在代码中导入时使用：

```python
from SafeLens.pipelines.runner import PipelineRunner
```

项目当前已经完成第一阶段基础设施：

- 统一的 `src` 包结构。
- 核心抽象接口和数据协议。
- 插件注册机制。
- YAML 驱动的 pipeline runner。
- dummy 纵向切片，可在不下载模型的情况下验证全流程。
- HuggingFace、Qwen3 Dense、TransformerLens-compatible 和 ModelScope 真实模型来源接口。
- SafeLens model bridge：用 architecture adapter 把 GPT-2、GPT-J、GPT-Neo、GPT-NeoX/Pythia、BLOOM/Falcon、MPT、Phi、OPT、BERT、T5 和 LLaMA-like 模型映射到统一 component hook vocabulary。
- TransformerLens 风格的 activation cache、临时 hook 和 generic activation patch 基础操作。
- FlagSafe 适配器骨架。
- README、MkDocs 文档、测试、CI、pre-commit、Ruff、mypy 配置。

## 2. 项目定位

SafeLens 面向的是模型安全研究和工程集成之间的中间层。它把不同研究方法统一封装成可组合的组件，使团队成员可以并行开发：

- 佳然可以实现内生探针、steering vector、activation patching 等方法。
- 健晖可以实现安全监测、数据溯源、运行时信号收集等方法。
- 基础架构负责人可以维护模型加载、接口契约、pipeline、报告格式和外部系统适配。

项目的关键原则是：

- 方法实现依赖抽象接口，而不是直接依赖具体模型或具体 pipeline。
- 所有结果返回统一的 Pydantic 数据结构，便于序列化和跨系统传输。
- 方法通过注册表按名字加载，配置文件可以决定运行哪些 probe、monitor、attributor。
- 模型来源可配置，支持 dummy、HuggingFace、Qwen3 Dense、TransformerLens-compatible、ModelScope。
- hook 和 patching 操作先作为基础层实现，具体算法复用这些操作。
- FlagSafe 相关逻辑在 adapter 层隔离，避免污染核心研究接口。

## 3. 当前目录结构

```text
SafeLens/
├── Architecture.md
├── README.md
├── REPORT.md
├── pyproject.toml
├── mkdocs.yml
├── examples/
│   ├── config.yaml
│   ├── modelscope_config.yaml
│   └── demo_pipeline.py
├── docs/
│   ├── index.md
│   ├── configuration.md
│   ├── development.md
│   └── api/
│       ├── core.md
│       ├── registry.md
│       ├── runner.md
│       ├── model_wrapper.md
│       └── flagsafe_adapter.md
├── src/
│   └── SafeLens/
│       ├── __init__.py
│       ├── core/
│       │   ├── base.py
│       │   └── registry.py
│       ├── utils/
│       │   └── model_wrapper.py
│       ├── pipelines/
│       │   └── runner.py
│       ├── probes/
│       │   └── dummy.py
│       ├── monitors/
│       │   └── dummy.py
│       ├── attribution/
│       │   └── dummy.py
│       ├── steering/
│       │   └── __init__.py
│       ├── adapters/
│       │   └── flagsafe_adapter.py
│       └── app/
│           └── __init__.py
└── tests/
    ├── test_pipeline.py
    └── test_registry.py
```

## 4. 安装和运行

### 4.1 基础安装

项目要求 Python 3.10 或更高版本。当前本地使用 `.conda` 环境验证。

```bash
.conda/bin/python -m pip install -e . --no-build-isolation
```

基础依赖：

- `pydantic>=2,<3`
- `PyYAML>=6,<7`

### 4.2 开发依赖

```bash
.conda/bin/python -m pip install -e ".[dev]" --no-build-isolation
```

开发依赖包括：

- `pytest`
- `ruff`
- `mypy`
- `pre-commit`
- `mkdocs`
- `mkdocs-material`
- `mkdocstrings[python]`

### 4.3 模型依赖

如果只跑 dummy pipeline，不需要安装真实模型依赖。

HuggingFace 模型加载：

```bash
.conda/bin/python -m pip install -e ".[models]" --no-build-isolation
```

ModelScope 模型加载：

```bash
.conda/bin/python -m pip install -e ".[modelscope]" --no-build-isolation
```

### 4.4 运行 dummy pipeline

```bash
.conda/bin/safelens run --config examples/config.yaml
```

预期输出类似：

```json
{
  "samples_scanned": 2,
  "flagged_count": 1,
  "max_risk_score": 1.0
}
```

pipeline 会把完整报告写入 `output.report_path`，默认是：

```text
./safety_scan.json
```

## 5. 配置文件格式

SafeLens pipeline 使用 YAML 配置。最小结构包含四部分：

```yaml
model:
  source: dummy
  name: dummy
  dtype: float32

pipeline:
  risk_threshold: 0.5
  probes:
    - name: dummy_probe
      config:
        layers: [0]
  monitors:
    - name: dummy_monitor
      config:
        threshold: 0.5
  attributors:
    - name: dummy_attributor
      config: {}

dataset:
  - id: sample-1
    text: "Explain the difference between a monitor and a probe."

output:
  report_path: "./safety_scan.json"
```

配置会被 `PipelineConfig` 校验并转成结构化对象。

### 5.1 `model` 字段

`model` 控制模型加载方式。对应类型是 `ModelLoadConfig`。

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `source` | `str` | 模型来源。支持 `dummy`、`huggingface`、`hf`、`qwen3_dense`、`qwen3`、`modelscope`、`ms` |
| `name` | `str` | 模型名或 dummy 名称 |
| `dtype` | `str` | 精度。常见值为 `float32`、`float16`、`bfloat16`、`auto` |
| `device` | `str | null` | 设备，如 `cpu`、`cuda`、`mps` |
| `revision` | `str | null` | HuggingFace 或 ModelScope 版本 |
| `cache_dir` | `str | null` | 下载缓存目录 |
| `local_dir` | `str | null` | ModelScope 下载到本地的目标目录 |
| `trust_remote_code` | `bool` | 是否信任远程模型代码 |
| `load_kwargs` | `dict` | 传给真实模型 loader 的额外参数 |
| `tokenizer_kwargs` | `dict` | 传给 `AutoTokenizer.from_pretrained` 的额外参数 |
| `modelscope_kwargs` | `dict` | 传给 `modelscope.snapshot_download` 的额外参数 |

### 5.2 `pipeline` 字段

`pipeline` 控制运行哪些方法。对应类型是 `PipelineSectionConfig`。

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `risk_threshold` | `float` | 总体风险阈值，默认 `0.5` |
| `probes` | `list[MethodSpec]` | 内生探针列表 |
| `monitors` | `list[MethodSpec]` | 安全监测器列表 |
| `attributors` | `list[MethodSpec]` | 溯源方法列表 |

每个方法使用统一的 `MethodSpec`：

```yaml
- name: dummy_probe
  config:
    layers: [0]
    risk_terms: ["jailbreak", "attack"]
```

`name` 必须是注册表中已经注册的方法名。`config` 会原样传入方法构造函数。

### 5.3 `dataset` 字段

当前 dataset 是一个 list，每个元素是字典。dummy 方法支持：

- `id`
- `text`
- `prompt`
- `risk_score`
- `evidence_tokens`

真实模型路径下，如果 batch 中没有 `input_ids`，`HuggingFaceModelWrapper` 会尝试从 `text` 或 `prompt` 进行 tokenizer 编码。

### 5.4 `output` 字段

`output.report_path` 决定 `RunReport` JSON 输出位置。

```yaml
output:
  report_path: "./safety_scan.json"
```

## 6. 核心接口

核心接口位于：

```text
src/SafeLens/core/base.py
```

这些接口是团队后续开发时最重要的契约。

### 6.1 `ModelWrapper`

`ModelWrapper` 抽象模型加载、hook 管理、带缓存推理和生成。

接口定义：

```python
class ModelWrapper(ABC):
    def load_model(self) -> Any:
        ...

    def add_hook(self, layer: LayerRef, hook_fn: HookFn) -> Any:
        ...

    def run_with_cache(
        self,
        batch: Batch,
        layers: Sequence[LayerRef] | None = None,
    ) -> tuple[Any, dict[str, Any]]:
        ...

    def generate(self, prompt: str, **generation_kwargs: Any) -> Any:
        ...

    def remove_hooks(self) -> None:
        ...
```

使用方式：

```python
from SafeLens.core.base import ModelLoadConfig
from SafeLens.utils import build_model_wrapper

config = ModelLoadConfig(source="dummy", name="dummy")
model = build_model_wrapper(config)
model.load_model()
output, cache = model.run_with_cache({"text": "hello"})
```

兼容性说明：

- `DummyModelWrapper` 不依赖 torch 或 transformers，适合 CI 和接口验证。
- `HuggingFaceModelWrapper` 依赖 `torch` 和 `transformers`。
- `ModelScopeModelWrapper` 依赖 `modelscope`、`torch` 和 `transformers`。
- `add_hook` 的 `layer` 支持 `int` 或 `str`。字符串会在 `named_modules()` 中查找。整数会尝试常见路径：`model.layers`、`transformer.h`、`gpt_neox.layers`。
- 对新模型结构，如果层路径不在上述候选中，需要扩展 `_resolve_layer` 或在配置中使用字符串层名。

### 6.2 Hook / Cache / Patching 基础操作

参考 TransformerLens 的 HookPoint、ActivationCache 和 generic activation patching 思路，SafeLens 现在提供了一层更基础的操作接口。后续真实算法可以直接复用这些接口，而不必重复实现 hook 注册、activation 缓存和 patch 执行逻辑。

核心模块：

```text
src/SafeLens/core/hooks.py
src/SafeLens/core/patching.py
src/SafeLens/core/hooked_root.py
src/SafeLens/core/factored_matrix.py
src/SafeLens/core/analysis.py
src/SafeLens/core/kv_cache.py
```

主要接口：

- `HookPoint`：独立的 identity hook point，支持临时 hook、永久 hook、prepend 顺序、方向过滤、上下文 `ctx`、层号解析。
- `get_act_name` / `safelens_act_name`：支持 TransformerLens 风格和 SafeLens 风格的 activation shorthand。
- `ActivationCache`：字典式 activation 缓存，支持 `select()`、`clone()` 和 `to_dict()`。
- `ActivationCache` tuple key：支持 `cache[("resid_pre", 0)]`、`cache[("q", 2)]` 这类索引。
- `keys_matching`、`apply_to_values`、`detach`、`cpu`、`to`：支持 cache 过滤和批量变换。
- `remove_batch_dim`、`apply_slice_to_batch_dim`：支持批量维度处理。
- `stack_activation`：按层堆叠同类 activation。
- `accumulated_resid`：构造 logit lens 常用 residual stack。
- `decompose_resid`：将 residual stream 分解为 embedding、attention output、MLP output。
- `stack_head_results`：按 attention head 堆叠结果向量。
- `stack_neuron_results`：按 MLP neuron 堆叠激活。
- `get_full_resid_decomposition`：组合 residual、head、neuron 级分解。
- `apply_ln_to_stack`：使用缓存的 layer norm scale 处理 residual stack。
- `logit_attrs`：将 residual component 投影到 token residual direction。
- `temporary_hooks`：上下文式临时 hook 注册，退出时保证移除 hook。
- `cache_activations`：运行模型并缓存指定层的 activation。
- `HookedRoot`：集中管理命名 `HookPoint`，支持临时 hook、永久 hook、批量 hook、cache hook 和 hook 名校验。
- `FactoredMatrix`：支持 `A @ B` 形式的矩阵分解表达、dense product、转置、组合、SVD、norm 和 corner inspection。
- `KeyValueCache` / `KeyValueCacheEntry`：提供自回归分析需要的 per-layer key/value cache 容器。
- `softmax`、`logits_to_log_probs`、`cross_entropy_loss`、`logit_diff`、`topk_tokens`：提供基础 logit/loss/token 分析工具。
- `residual_stack_to_logits`、`direct_logit_attribution`：支持 logit lens 和 direct logit attribution 工作流。
- `zero_ablation_hook`、`mean_ablation_hook`、`replace_activation_hook`：提供常见 ablation/intervention hook。
- `PatchSpec`：描述一次 patch 操作，包括目标层、目标 index、来源 index、模式和缩放。
- `run_activation_patch`：执行一次 patched forward 并返回 `PatchResult`。
- `generic_activation_patch`：批量执行 patch grid，适合后续实现 causal tracing、residual stream patching、attention/head patching 等方法。
- `component_activation_patch`：按组件名和轴名称运行 patch grid。
- `get_act_patch_*`：对齐 TransformerLens 常用组件级 patch API。

当前已覆盖的组件：

| 组件类别 | SafeLens API |
| --- | --- |
| Residual stream | `get_act_patch_resid_pre`、`get_act_patch_resid_mid`、`get_act_patch_resid_post` |
| Block outputs | `get_act_patch_attn_out`、`get_act_patch_mlp_out`、`get_act_patch_block_every` |
| Attention head vectors | `get_act_patch_attn_head_*_by_pos`、`get_act_patch_attn_head_*_all_pos`，覆盖 `q`、`k`、`v`、`z`、`result` |
| Attention pattern | `get_act_patch_attn_head_pattern_all_pos`、`get_act_patch_attn_head_pattern_by_pos`、`get_act_patch_attn_head_pattern_dest_src_pos` |
| Attention scores | `get_act_patch_attn_scores_all_pos`、`get_act_patch_attn_scores_by_pos`、`get_act_patch_attn_scores_dest_src_pos` |

示例：

```python
from SafeLens.core.hooks import ActivationCache
from SafeLens.core.patching import get_act_patch_resid_pre

clean_cache = ActivationCache({"layer_0.resid_pre": clean_resid_pre})

results = get_act_patch_resid_pre(
    model,
    corrupted_batch,
    clean_cache,
    metric=lambda output: float(output["score"]),
    layers=[0],
    positions=[3],
)
```

兼容性说明：

- Hook 函数支持 PyTorch forward hook 风格的 `(module, inputs, output)` 调用。
- Dummy wrapper 同时兼容旧的 `layer/batch/cache` 关键字 hook 和新的 `activation/output` hook。
- Patch setter 默认支持 `replace` 和 `add`，复杂算法可以通过 `PatchSpec.setter` 注入自定义逻辑。
- `LayerRef` 仍然支持整数层号和字符串 module path，缓存名统一为 `layer_0` 或传入的字符串层名。
- 组件命名支持 SafeLens 风格 `layer_0.resid_pre`，也支持 `name_style="transformer_lens"` 生成 `blocks.0.hook_resid_pre`。
- 需要注意：patch API 已经能表达上述组件操作，但具体 `ModelWrapper` 必须真的暴露对应 hook point。裸 HuggingFace wrapper 默认只能 hook module，不能自动得到 `q/k/v/pattern/resid_pre` 这类细粒度点。

### 6.3 `BaseProbe`

`BaseProbe` 是内生探针接口，用于读取或干预模型内部激活。

接口定义：

```python
class BaseProbe(ABC):
    name: ClassVar[str] = ""

    def attach(self, model: ModelWrapper, layers: Sequence[int]) -> None:
        ...

    def detect(self, batch: Batch) -> ProbeResult:
        ...

    def intervene(self, batch: Batch, direction: Any, scale: float) -> None:
        ...

    def detach(self) -> None:
        ...
```

实现示例：

```python
from collections.abc import Sequence
from typing import Any

from SafeLens.core.base import BaseProbe, Batch, ModelWrapper, ProbeResult
from SafeLens.core.registry import register_probe


@register_probe("linear_probe")
class LinearProbe(BaseProbe):
    def attach(self, model: ModelWrapper, layers: Sequence[int]) -> None:
        self.layers = list(layers)

    def detect(self, batch: Batch) -> ProbeResult:
        return ProbeResult(
            risk_score=0.0,
            critical_layers=self.layers,
            details={"method": self.name},
        )

    def intervene(self, batch: Batch, direction: Any, scale: float) -> None:
        ...

    def detach(self) -> None:
        ...
```

在 YAML 中使用：

```yaml
pipeline:
  probes:
    - name: linear_probe
      config:
        layers: [8, 16, 24]
```

### 6.4 `BaseMonitor`

`BaseMonitor` 用于运行时安全监测，可以在每个 batch 或生成步骤上输出安全信号。

接口定义：

```python
class BaseMonitor(ABC):
    name: ClassVar[str] = ""

    def start_monitoring(self, model: ModelWrapper) -> None:
        ...

    def step(self, batch: Batch, model_output: Any = None) -> MonitoringSignal:
        ...

    def report(self) -> SafetyReport:
        ...
```

适用场景：

- token 级别风险监测。
- entropy 或 logit 分布异常检测。
- refusal 或 jailbreak 状态监测。
- 外部安全分类器输出聚合。

当前 dummy monitor 逻辑：

- 读取 `batch.risk_score` 或 `model_output.risk_score`。
- 与 `threshold` 比较。
- 返回 `MonitoringSignal`。

### 6.5 `BaseAttributor`

`BaseAttributor` 用于输入溯源或训练数据溯源。

接口定义：

```python
class BaseAttributor(ABC):
    name: ClassVar[str] = ""

    def attribute_training(self, batch: Batch, model_output: Any = None) -> AttributionResult:
        ...

    def attribute_input(self, batch: Batch, model_output: Any = None) -> AttributionResult:
        ...
```

适用场景：

- 输入 token 贡献度分析。
- 训练样本影响分析。
- 检索或数据源置信度归因。
- 与 probe 或 monitor 的风险信号联合解释。

## 7. 数据结构和报告协议

所有主要结果结构都继承自 `SerializableModel`，底层使用 Pydantic v2。

### 7.1 `ProbeResult`

```python
ProbeResult(
    risk_score=0.8,
    critical_layers=[12, 18],
    intervention_applied=False,
    details={"risk_category": ["jailbreak"]},
)
```

字段：

| 字段 | 说明 |
| --- | --- |
| `risk_score` | 0 到 1 的风险分数 |
| `critical_layers` | 风险相关层 |
| `intervention_applied` | 是否应用干预 |
| `details` | 方法自定义细节 |

### 7.2 `MonitoringSignal`

```python
MonitoringSignal(
    name="entropy_monitor",
    risk_score=0.7,
    triggered=True,
    risk_category=["jailbreak"],
    evidence_tokens=[3, 4],
)
```

字段：

| 字段 | 说明 |
| --- | --- |
| `name` | monitor 名称 |
| `risk_score` | 风险分数 |
| `triggered` | 是否触发告警 |
| `risk_category` | 风险类别 |
| `evidence_tokens` | 证据 token index |
| `details` | 方法自定义细节 |

### 7.3 `TokenAttribution` 和 `AttributionResult`

`TokenAttribution` 表示 token 级证据：

```python
TokenAttribution(
    token_index=2,
    score=1.0,
    token_text="jailbreak",
    source="input",
)
```

`AttributionResult` 表示完整溯源结果：

```python
AttributionResult(
    method="dummy_attributor",
    attribution_score=1.0,
    tokens=[...],
)
```

### 7.4 `SafetyReport`

`SafetyReport` 是单个样本的标准安全报告，也是 FlagSafe adapter 的输入。

```python
SafetyReport(
    sample_id="risky-1",
    flagged=True,
    risk_score=1.0,
    risk_category=["jailbreak"],
    evidence_tokens=[2, 3],
    attribution_score=1.0,
    probe_results=[...],
    monitoring_signals=[...],
    attributions=[...],
)
```

聚合逻辑在 `PipelineRunner._build_report` 中完成：

- `risk_score` 取 probe 和 monitor 最高分。
- `flagged` 由 `risk_threshold` 或 monitor trigger 决定。
- `risk_category` 汇总 probe details 和 monitor signal。
- `evidence_tokens` 汇总 probe、monitor、attributor 的证据。
- `attribution_score` 取 attributor 的最高分。

### 7.5 `RunReport`

`RunReport` 是完整 pipeline 输出：

```python
RunReport(
    generated_at=...,
    reports=[SafetyReport(...), ...],
    summary={
        "samples_scanned": 2,
        "flagged_count": 1,
        "max_risk_score": 1.0,
    },
)
```

可以使用 `.to_dict()` 生成 JSON 可序列化结果。

## 8. 插件注册机制

注册机制位于：

```text
src/SafeLens/core/registry.py
```

提供三类注册表：

- probe registry
- monitor registry
- attributor registry

注册 probe：

```python
from SafeLens.core.registry import register_probe


@register_probe("linear_probe")
class LinearProbe(BaseProbe):
    ...
```

注册 monitor：

```python
from SafeLens.core.registry import register_monitor


@register_monitor("entropy_monitor")
class EntropyMonitor(BaseMonitor):
    ...
```

注册 attributor：

```python
from SafeLens.core.registry import register_attributor


@register_attributor("tracin")
class TracInAttributor(BaseAttributor):
    ...
```

加载实例：

```python
from SafeLens.core.registry import create_probe

probe = create_probe("linear_probe", config={"layers": [12]})
```

兼容性说明：

- 名称必须是非空字符串。
- 默认不允许重复注册同名方法。
- 如果确实要覆盖，可使用 `replace=True`。
- pipeline 启动时会导入内置 dummy 方法，确保 dummy 注册表可用。
- 新方法如果放在新模块中，需要保证模块在运行前被 import，否则装饰器不会执行。

## 9. Pipeline Runner

runner 位于：

```text
src/SafeLens/pipelines/runner.py
```

核心类：

```python
PipelineRunner
```

主要入口：

```python
PipelineRunner.from_yaml("examples/config.yaml").run()
```

或：

```python
from SafeLens.pipelines import run_from_config

report = run_from_config("examples/config.yaml")
```

运行流程：

1. `load_pipeline_config` 读取 YAML。
2. Pydantic 校验成 `PipelineConfig`。
3. `build_model_wrapper` 根据 `model.source` 创建模型 wrapper。
4. `create_probe`、`create_monitor`、`create_attributor` 根据注册名创建方法实例。
5. `setup` 加载模型并 attach probe hook。
6. 对每个 batch 执行：
   - `model.run_with_cache`
   - `probe.detect`
   - `monitor.step`
   - `attributor.attribute_input`
7. 聚合成 `SafetyReport`。
8. 汇总成 `RunReport`。
9. 写入 JSON 文件。
10. 在 `finally` 中清理 probe hook 和 model hook。

### 9.1 CLI

CLI 位于：

```text
src/SafeLens/cli.py
```

命令：

```bash
safelens run --config examples/config.yaml
```

支持 JSONL 数据集覆盖：

```bash
safelens run --config examples/config.yaml --input-jsonl data.jsonl
```

JSONL 每行是一个 JSON object，例如：

```json
{"id": "case-1", "text": "Explain monitoring."}
{"id": "case-2", "text": "Show a jailbreak attack plan."}
```

## 10. 模型来源兼容

模型 wrapper 位于：

```text
src/SafeLens/utils/model_wrapper.py
```

当前支持四类来源。

### 10.1 Dummy

用于测试、CI 和架构验证。

配置：

```yaml
model:
  source: dummy
  name: dummy
```

特点：

- 不下载模型。
- 不依赖 torch。
- 支持 hook 注册和移除。
- `run_with_cache` 返回简单的 `model_output` 和 layer cache。

适合：

- 验证 pipeline。
- 编写方法接口测试。
- 让团队在没有 GPU 或模型权重时开发业务逻辑。

### 10.2 HuggingFace

配置：

```yaml
model:
  source: huggingface
  name: Qwen/Qwen2.5-0.5B-Instruct
  dtype: float16
  device: cpu
  trust_remote_code: true
  cache_dir: ./.cache/huggingface
```

加载逻辑：

```python
AutoTokenizer.from_pretrained(...)
AutoModelForCausalLM.from_pretrained(...)
```

支持：

- `revision`
- `cache_dir`
- `trust_remote_code`
- `load_kwargs`
- `tokenizer_kwargs`

兼容注意：

- 当前模型类固定为 `AutoModelForCausalLM`。如果后续需要 encoder-only、seq2seq 或 VLM，需要扩展配置和 wrapper。
- 当前 tokenizer 输入假设为文本或已准备好的 `input_ids`。
- `device` 只做 `.to(device)`，没有自动 device_map 分片。
- 大模型加载需要自行在 `load_kwargs` 中传入量化、低显存或 device_map 参数。

### 10.3 Qwen3 Dense

配置：

```yaml
model:
  source: qwen3_dense
  name: Qwen/Qwen3-8B
  dtype: bfloat16
  device: cuda
  trust_remote_code: true
```

适配范围：

- 支持 Qwen3 dense decoder-only 模型，已按名称限制在 `0.6B`、`1.7B`、`4B`、`8B`、`14B`、`32B` 这类小于等于 35B 的 dense 模型。
- 明确拒绝 MoE 名称，例如 `Qwen3-30B-A3B`。
- 暴露 SafeLens 组件 hook：`layer_i.resid_pre`、`layer_i.resid_mid`、`layer_i.resid_post`、`layer_i.attn_out`、`layer_i.mlp_out`、`layer_i.q`、`layer_i.k`、`layer_i.v`、`layer_i.z`。
- 同时支持 TransformerLens 风格名称解析，例如 `blocks.0.attn.hook_q`。
- `pattern` 可通过 `run_with_cache` 缓存，底层会启用 `output_attentions=True`；`pattern` patching 和 pre-softmax `attn_scores` 仍明确报 `NotImplementedError`，因为需要更低层的 attention forward instrumentation。

### 10.4 ModelScope

配置：

```yaml
model:
  source: modelscope
  name: Qwen/Qwen2.5-0.5B-Instruct
  dtype: float16
  device: cpu
  trust_remote_code: true
  cache_dir: ./.cache/modelscope
  local_dir: ./models/qwen2.5-0.5b
```

加载逻辑：

1. 调用 `modelscope.snapshot_download(model_id=...)`。
2. 得到本地 snapshot 路径。
3. 将该路径传给 Transformers 的 `from_pretrained`。

支持：

- `revision`
- `cache_dir`
- `local_dir`
- `modelscope_kwargs`
- `load_kwargs`
- `tokenizer_kwargs`

示例：

```yaml
model:
  source: modelscope
  name: Qwen/Qwen2.5-0.5B-Instruct
  modelscope_kwargs:
    allow_file_pattern: "*.json"
```

兼容注意：

- ModelScope 下载和 Transformers 加载是两个阶段。
- `_pretrained_kwargs` 在 ModelScope wrapper 中返回空字典，避免把 HuggingFace 的 `revision` 或 `cache_dir` 再传给本地路径加载。
- 如果 ModelScope 模型仓库结构不兼容 Transformers，需要额外扩展 wrapper。

## 11. 内置 dummy 方法

当前内置三个 dummy 方法，用于跑通纵向切片。

### 11.1 `dummy_probe`

文件：

```text
src/SafeLens/probes/dummy.py
```

配置：

```yaml
pipeline:
  probes:
    - name: dummy_probe
      config:
        layers: [0]
        risk_terms: ["jailbreak", "attack", "harmful"]
        risk_category: ["jailbreak"]
        baseline_risk: 0.05
        category_threshold: 0.5
```

行为：

- 在 `attach` 中注册 hook。
- 在 `detect` 中扫描 `text` 或 `prompt`。
- 如果出现风险词，风险分数按命中数量增加。
- 返回 `ProbeResult`。

### 11.2 `dummy_monitor`

文件：

```text
src/SafeLens/monitors/dummy.py
```

配置：

```yaml
pipeline:
  monitors:
    - name: dummy_monitor
      config:
        threshold: 0.5
        risk_category: ["jailbreak"]
```

行为：

- 读取 batch 或 model output 中的 `risk_score`。
- 大于等于 threshold 时触发。
- 返回 `MonitoringSignal`。

### 11.3 `dummy_attributor`

文件：

```text
src/SafeLens/attribution/dummy.py
```

配置：

```yaml
pipeline:
  attributors:
    - name: dummy_attributor
      config:
        risk_terms: ["jailbreak", "attack", "harmful"]
```

行为：

- 扫描输入文本中的风险词。
- 为命中的 token 生成 `TokenAttribution`。
- 返回 `AttributionResult`。

## 12. FlagSafe 适配

FlagSafe adapter 位于：

```text
src/SafeLens/adapters/flagsafe_adapter.py
```

当前接口：

```python
from SafeLens.adapters import FlagSafeAdapter

rule = FlagSafeAdapter.to_flagsafe_rule(report)
rules = FlagSafeAdapter.to_flagsafe_batch(reports)
```

输出格式：

```python
{
    "action": "BLOCK" if report.flagged else "ALLOW",
    "reason": report.risk_category,
    "evidence": report.evidence_tokens,
    "score": report.risk_score,
    "attribution_score": report.attribution_score,
    "metadata": {
        "sample_id": report.sample_id,
        "source": "safelens",
    },
}
```

兼容说明：

- 当前 FlagSafe 格式是预留协议，不代表最终对方真实 API。
- 内部统一使用 `SafetyReport`，后续只需修改 adapter，不需要改 probe、monitor 或 pipeline。
- 如果 FlagSafe 要求更细的风险分类、证据文本、规则 ID 或拦截策略，可在 adapter 中完成转换。

## 13. 文档站点

MkDocs 配置位于：

```text
mkdocs.yml
```

本地预览：

```bash
.conda/bin/mkdocs serve
```

浏览器打开：

```text
http://127.0.0.1:8000
```

构建静态站点：

```bash
.conda/bin/mkdocs build --strict
```

输出目录：

```text
site/
```

当前文档包括：

- `docs/index.md`: 项目介绍和快速开始。
- `docs/configuration.md`: YAML 配置、模型来源、方法配置。
- `docs/development.md`: 如何扩展 probe、monitor、attributor。
- `docs/api/*.md`: API 导读和 `mkdocstrings` 自动生成内容。

## 14. 测试和质量检查

当前测试位于：

```text
tests/
```

已有测试覆盖：

- 内置方法注册。
- dummy pipeline 从配置到报告输出。
- FlagSafe adapter 行为。
- HuggingFace wrapper 选择。
- ModelScope wrapper 选择。
- ModelScope `snapshot_download` 参数传递。

推荐运行：

```bash
.conda/bin/ruff check .
.conda/bin/mypy src tests examples
.conda/bin/python -m pytest -q
.conda/bin/mkdocs build --strict
```

CI 配置位于：

```text
.github/workflows/ci.yml
```

pre-commit 配置位于：

```text
.pre-commit-config.yaml
```

## 15. 兼容性总结

### 15.1 Python 和依赖

| 项目 | 当前状态 |
| --- | --- |
| Python | `>=3.10` |
| Pydantic | v2 |
| YAML | PyYAML |
| Torch | 可选，仅真实模型需要 |
| Transformers | 可选，仅 HuggingFace / Qwen3 Dense / TransformerLens-compatible / ModelScope 真实模型需要 |
| ModelScope | 可选，仅 ModelScope 下载需要 |
| TransformerLens | 不需要；`transformer_lens` 来源是 SafeLens 独立兼容层 |

### 15.2 模型兼容

| 来源 | 配置值 | 下载方式 | 加载方式 |
| --- | --- | --- | --- |
| Dummy | `dummy` | 无下载 | 内存模拟 |
| HuggingFace | `huggingface` / `hf` | Transformers 内部处理 | `AutoModelForCausalLM.from_pretrained` |
| Qwen3 Dense | `qwen3_dense` / `qwen3` | Transformers 内部处理 | `AutoModelForCausalLM.from_pretrained` + SafeLens component hooks |
| TransformerLens-compatible | `transformer_lens` / `tl` | Transformers / HuggingFace 缓存 | SafeLens `TransformerLensCompatibleModelWrapper` + architecture adapters + Transformers auto classes |
| ModelScope | `modelscope` / `ms` | `modelscope.snapshot_download` | 本地路径传给 Transformers |

### 15.3 方法兼容

| 方法类型 | 基类 | 注册器 | 输出 |
| --- | --- | --- | --- |
| Probe | `BaseProbe` | `register_probe` | `ProbeResult` |
| Monitor | `BaseMonitor` | `register_monitor` | `MonitoringSignal` / `SafetyReport` |
| Attributor | `BaseAttributor` | `register_attributor` | `AttributionResult` |

### 15.4 报告兼容

所有核心报告对象都支持：

```python
report.to_dict()
```

这会使用 Pydantic 的 JSON mode 输出，适合写入 JSON 或传给 adapter。

## 16. 当前限制

当前项目是基础设施版本，还有一些明确限制：

- 真实 probe、monitor、attributor 还未实现。
- HuggingFace wrapper 目前默认使用 `AutoModelForCausalLM`，尚未覆盖 VLM、encoder-only、seq2seq 等模型类型。
- hook layer 自动解析只覆盖常见 Transformer 路径。
- pipeline 当前主要按 batch 扫描，不是完整 token-by-token generation loop。
- `BaseMonitor.report` 当前没有在 runner 汇总中单独调用，runner 使用的是逐 batch `step` 信号。
- FlagSafe adapter 是预留协议，等真实接口确定后还需要细化。
- app 目录仍为空，仅保留未来 demo 入口。

## 17. 推荐后续工作

建议按下面顺序推进：

1. 接入第一个真实 probe，例如 linear probe 或 activation patching。
2. 接入第一个真实 monitor，例如 entropy monitor 或 refusal monitor。
3. 用一个小型 HuggingFace 模型做真实端到端测试。
4. 用一个 ModelScope 模型做真实端到端测试，确认下载和本地加载路径。
5. 增加 JSONL 数据集示例。
6. 设计更正式的 risk category 枚举。
7. 明确 FlagSafe 最终 API 后完善 adapter。
8. 增加 pipeline 级别的 generation loop，用于逐 token monitor。
9. 将 docs 部署到 GitHub Pages。
10. 在 CI 中加入 docs build、Ruff、mypy、pytest 全量检查。

## 18. 结论

SafeLens 当前已经具备一个可协作、可测试、可扩展的安全分析基础架构。它完成了从 YAML 配置到模型包装、插件实例化、方法执行、报告生成、外部适配的最小闭环。

从工程状态看，项目已经可以支持团队成员并行开发真实方法。后续工作的重点不再是补基础骨架，而是把真实安全研究方法接入现有接口，并通过真实 HuggingFace / Qwen3 Dense / ModelScope 模型验证接口是否足够顺手和稳定。

如果你在团队里是 `Infrastructure Owner` 的角色（或负责基础架构），那么要做的是**先把骨架搭好，让 `Probe Method Owner`、`Monitoring/Attribution Method Owner` 的方法能像插件一样接入，同时保证代码质量和文档，并为 FlagSafe 预留好对接口径**。

下面按五个方面，给出可以直接执行的启动步骤。

---

## 1. 整体架构落地：从目录到设计模式

### 第一步：确定代码包结构与依赖
建议采用 `src` 布局，避免路径污染：

```
safelens/
├── src/
│   └── safelens/              # 包名（可改）
│       ├── __init__.py
│       ├── core/               # 基础接口、抽象类
│       ├── probes/             # 内生探针模块 (Probe Method Owner)
│       ├── monitors/           # 安全监测模块 (Monitoring Method Owner)
│       ├── steering/           # steering vector (Steering Method Owner)
│       ├── attribution/        # 数据溯源 (Attribution Method Owner)
│       ├── pipelines/          # 流程编排
│       ├── utils/              # 模型加载、hook工具
│       └── app/                # 第二阶段 Demo (暂空)
├── tests/
├── docs/
├── examples/                   # Tutorial notebooks
├── pyproject.toml
├── README.md
└── .github/workflows/         # CI
```

### 第二步：设计核心设计模式
- **插件注册**：用装饰器或入口函数注册每个方法，方便通过配置文件调用。
- **依赖反转**：所有方法依赖抽象 `BaseProbe` 等，不直接依赖具体模型。
- **数据类传输**：结果统一为 dataclass/pydantic，便于序列化和传给 FlagSafe。

**这一步你要产出的第一个文件**：`core/base.py`（接口定义，见下）。

---

## 2. 基础接口定义：让所有人写的代码遵循同一契约

这是整库的骨架，必须先写并由团队评审，因为 method owners 会基于它来开发具体方法。

### 需要定义的抽象类
1. **模型包装器 `ModelWrapper`**  
   封装 HuggingFace 模型加载、hook 管理、推理。可用 TransformerLens 简化，但也可以直接自己做，先保证易于理解。  
   - 方法：`load_model()`, `add_hook(layer, hook_fn)`, `run_with_cache()`, `generate()`。
   - **实现建议**：初期可直接依赖 `transformers` + `registering forward hooks`，后续可切到 TransformerLens。

2. **`BaseProbe`** (内生探针)  
   见之前设计，关键抽象方法：`attach`, `detect`, `intervene`, `detach`。  
   需要返回 `ProbeResult`（内含风险分数、激活位置、干预操作序列）。

3. **`BaseMonitor`** (安全监测)  
   `start_monitoring`, `step`, `report`。返回 `MonitoringSignal` 或 `SafetyReport`。

4. **`BaseAttributor`** (溯源)  
   `attribute_training`, `attribute_input`，返回 `TokenAttribution` 等。

5. **配置基类 `BaseMethodConfig`**  
   用 `pydantic` 定义每个方法所需参数，可序列化为 yaml。

### 你现在可以马上写的代码草稿（`core/base.py`）

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional
import torch

@dataclass
class ProbeResult:
    risk_score: float
    critical_layers: List[int]
    intervention_applied: bool = False
    details: Dict = field(default_factory=dict)

class BaseProbe(ABC):
    def __init__(self, config: dict = None):
        self.config = config or {}

    @abstractmethod
    def attach(self, model: 'ModelWrapper', layers: List[int]) -> None:
        """Register hooks on target layers."""
        ...

    @abstractmethod
    def detect(self, batch: Dict[str, torch.Tensor]) -> ProbeResult:
        """Compute safety risk from activations."""
        ...

    @abstractmethod
    def intervene(self, batch: Dict[str, torch.Tensor], direction: torch.Tensor, scale: float) -> None:
        """Add intervention to activations."""
        ...

    @abstractmethod
    def detach(self) -> None:
        """Remove all hooks."""
        ...
```

同时为 monitor、attributor 定义类似结构。这些抽象类一写完，就可以让 method owners 基于此写自己的方法，保证后续 Pipeline 可以统一调用。

---

## 3. CI / 代码质量 / 文档站点：从第一天就建好

**Github Actions 最小可用配置**（放在 `.github/workflows/ci.yml`）：

```yaml
name: CI

on: [push, pull_request]

jobs:
  quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
      - run: pip install pre-commit
      - run: pre-commit run --all-files
```

`pre-commit` 的 `.pre-commit-config.yaml` 内容：
```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.3.0
    hooks:
      - id: ruff        # linter
      - id: ruff-format # formatter
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.8.0
    hooks:
      - id: mypy
        additional_dependencies: [pydantic, torch]
```

**文档站点**：  
推荐使用 **MkDocs Material**（美观、搜索快、支持 API 自动生成）。

1. 在仓库根目录创建 `docs/` 文件夹。
2. `mkdocs.yml` 配置：
```yaml
site_name: SafeLens
theme:
  name: material
plugins:
  - search
  - mkdocstrings:
      handlers:
        python:
          paths: [src]
nav:
  - Home: index.md
  - API Reference:
      - Core: api/core.md
      - Probes: api/probes.md
      ...
```
3. 借助 `mkdocstrings` 自动拉取 docstring 生成文档。
4. 部署：可用 GitHub Pages + `mkdocs gh-deploy` 命令。在 CI 里添加一个 job 自动部署文档。

**你现在要做**：将以上文件提交到仓库，团队首次 push 后就会自动风格检查，保证代码一致。

---

## 4. Pipeline 集成：让科研流一键跑通

目标：提供命令 `safelens run --config config.yaml`，自动加载模型、挂载一组探针/监测器，对测试集跑完并输出报告。

### 你需要做的三件事：

**(a) 设计统一的配置文件格式**（用 yaml）
```yaml
model:
  name: "meta-llama/Llama-2-7b-chat-hf"
  dtype: float16
pipeline:
  probes:
    - name: linear_probe
      config: { ... }
    - name: activation_patching
      config: { ... }
  monitors:
    - name: entropy_monitor
      config: { ... }
  attributors:
    - name: tracin
      config: { ... }
output:
  report_path: "./safety_scan.json"
```

**(b) 编写 `pipelines/runner.py`**
- 加载模型 → 实例化所有 Probe/Monitor（根据 name 从注册表中查找）→ 执行 attach → 遍历数据集 → 执行 detect/step → 收集结果 → 生成报告。
- 注意：这个 runner 需要和 monitoring/attribution owners 约定的抽象接口对接，每个方法必须有一个唯一的 `name`，并通过简单的注册装饰器注册（如 `@register_probe("linear_probe")`）。

**(c) 创建一个简单的注册机制**（`core/registry.py`）
```python
_PROBE_REGISTRY = {}

def register_probe(name):
    def decorator(cls):
        _PROBE_REGISTRY[name] = cls
        return cls
    return decorator
```

这样，Pipeline 就能通过名字动态加载方法，扩展性极强。

**立即产出**：写完 `runner.py` 和一个假的实现（如 dummy probe），跑通“配置 → 加载 → 运行 → 打印”全链路。这就是团队开发的“纵向切片”，之后大家往里填真的方法就行了。

---

## 5. 后期 FlagSafe 适配：预留接口，定义数据格式

`FlagSafe provider` 侧的 FlagSafe 很可能是一个内容安全防火墙，输入是 prompt+response，输出是安全评分或拦截规则。我们的库需要能作为它的“增强分析层”。

**适配策略：**
1. **定义标准输出协议**：我们扫描完一个样本后，生成的 `SafetyReport` 需要包含 FlagSafe 能直接消费的字段，例如：
   - `flagged: bool`
   - `risk_category: List[str]`（暴力、色情、越狱等）
   - `evidence_tokens: List[int]`（定位到的有害 token）
   - `attribution_score: float`（溯源置信度）
2. **编写 Adapter 模块**（现在只需做骨架）：`adapters/flagsafe_adapter.py`  
   ```python
   class FlagSafeAdapter:
       @staticmethod
       def to_flagsafe_rule(report: SafetyReport) -> dict:
           """Convert our internal report to FlagSafe policy format."""
           return {
               "action": "BLOCK" if report.flagged else "ALLOW",
               "reason": report.risk_category,
               "evidence": report.evidence_tokens,
           }
   ```
3. **确保所有 Probe/Monitor 返回的数据可序列化**（用 pydantic 并含 `.to_dict()`）。
4. **保留演示入口**：`app/` 中未来会调用该 Adapter，把前端 Demo 的点击翻译成 FlagSafe 规则下发。

现阶段只要**定义好 `SafetyReport` 的数据结构和 Adapter 接口**，等后续与 `FlagSafe provider` 对接时直接填充转换细节即可。

---

## 你（Infrastructure Owner）第一周的启动清单

- **Day 1-2**：创建仓库，如 `SafeLens`，配置 `pyproject.toml`，安装依赖，推空骨架。
- **Day 3**：写出 `core/base.py` 全部抽象类 + `core/registry.py`，并加 docstring。
- **Day 4**：完成 `utils/model_wrapper.py` 第一版（能加载一个 HF 模型并注册 forward hook）。
- **Day 5**：写出 `pipelines/runner.py` 和一个 `examples/demo_pipeline.py`，确保能跑通一个虚拟探针。
- **Day 6**：配置 CI（pre-commit + ruff + mypy）+ MkDocs 基础结构，并尝试用 GitHub Pages 预览。
- **Day 7**：与 probe/monitoring/attribution owners 对齐接口，把抽象类发给他们，让他们分别在自己的分支上实现一个真实方法试试能不能跑通。

做到这一步，基础设施就立住了，团队可以并行开发，也不会跑偏。

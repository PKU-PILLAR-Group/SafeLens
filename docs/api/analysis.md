# Analysis Utilities

This module collects small, framework-light helpers used by logit lens,
attribution, and ablation experiments.

Core utilities:

- `softmax`, `log_softmax`, and `logits_to_log_probs`.
- `per_token_cross_entropy_loss`, `cross_entropy_loss`,
  `lm_log_probs`, `lm_cross_entropy_loss`, and `lm_accuracy`.
- `topk_tokens` and `logit_diff`.
- `residual_stack_to_logits`, `compute_head_results_from_z`, and
  `direct_logit_attribution`.
- `attention_pattern_score`, `previous_token_attention_score`, and
  `induction_attention_score` for causal attention-pattern diagonal workflows,
  including repeated-token induction stripes via `repeat_length`.
- `zero_ablation_hook`, `mean_ablation_hook`, and `replace_activation_hook`.

Example:

```python
from SafeLens.core.analysis import cross_entropy_loss, logit_diff

loss = cross_entropy_loss([[0.0, 0.0]], [1])
score = logit_diff([[[1.0, 4.0], [7.0, 2.0]]], 0, 1)
```

Ablation hooks can be attached to `HookPoint` or `HookedRoot` objects:

```python
from SafeLens.core.analysis import zero_ablation_hook
from SafeLens.core.hooked_root import HookedRoot

root = HookedRoot()
hook = root.add_hook_point("blocks.0.hook_resid_pre")

with root.hooks(fwd_hooks=[("blocks.0.hook_resid_pre", zero_ablation_hook)]):
    assert hook([1, 2, 3]) == [0, 0, 0]
```

::: SafeLens.core.analysis

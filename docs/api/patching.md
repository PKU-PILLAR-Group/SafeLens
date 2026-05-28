# Activation Patching

Activation patching restores or modifies activations in a corrupted run using
values from a clean cache. The SafeLens patching layer is intentionally generic:
it defines patch operations, not a specific safety algorithm.

Design reference:
[TransformerLens activation patching](https://transformerlensorg.github.io/TransformerLens/generated/code/transformer_lens.patching.html).

Core utilities:

- `PatchSpec`: describes one activation patch.
- `apply_patch`: applies one patch to an activation.
- `make_patch_hook`: creates a forward hook for one patch.
- `run_activation_patch`: runs one patched forward pass and scores it.
- `generic_activation_patch`: runs a sequence of patch specs.
- `make_patch_specs`: creates a simple grid of patch specs.
- `component_activation_patch`: runs a Transformer component patch grid.
- `make_component_patch_specs`: creates component-level specs by named axes.
- `patch_results_to_metric_grid`: converts detailed runs into a
  TransformerLens-style metric grid.
- `patch_results_to_index_table`: returns the axis index table for patch runs.

Supported Transformer component helpers:

| Component family | Helper functions |
| --- | --- |
| Residual stream | `get_act_patch_resid_pre`, `get_act_patch_resid_mid`, `get_act_patch_resid_post` |
| Block outputs | `get_act_patch_attn_out`, `get_act_patch_mlp_out`, `get_act_patch_block_every` |
| Head vectors by position | `get_act_patch_attn_head_out_by_pos`, `get_act_patch_attn_head_q_by_pos`, `get_act_patch_attn_head_k_by_pos`, `get_act_patch_attn_head_v_by_pos`, `get_act_patch_attn_head_result_by_pos` |
| Head vectors all positions | `get_act_patch_attn_head_out_all_pos`, `get_act_patch_attn_head_q_all_pos`, `get_act_patch_attn_head_k_all_pos`, `get_act_patch_attn_head_v_all_pos`, `get_act_patch_attn_head_result_all_pos` |
| Attention patterns | `get_act_patch_attn_head_pattern_all_pos`, `get_act_patch_attn_head_pattern_by_pos`, `get_act_patch_attn_head_pattern_dest_src_pos` |
| Attention scores | `get_act_patch_attn_scores_all_pos`, `get_act_patch_attn_scores_by_pos`, `get_act_patch_attn_scores_dest_src_pos` |

The component helpers support both SafeLens names such as `layer_0.resid_pre`
and TransformerLens-style names such as `blocks.0.hook_resid_pre` by setting
`name_style="transformer_lens"`.

When explicit positions are omitted, residual/head-vector helpers infer sequence
length from tokens or `[batch, pos, ...]` activations. Attention pattern and
score helpers infer destination/source positions from
`[batch, head, dest_pos, src_pos]` activations.

The TransformerLens-style component helpers default to metric grids: for
example `get_act_patch_resid_pre` returns a `[layer, pos]` grid and
`get_act_patch_block_every` returns a stacked `[patch_type, layer, pos]`
result. Pass `return_details=True` when you need detailed `PatchResult`
records with the patched output and cache for each run. Pass
`return_index_df=True` to also return the index table; the table is a list of
dictionaries and does not require pandas.

`generic_activation_patch` also accepts the TransformerLens-style call shape:
pass `patching_metric`, a TL-style `patch_setter(activation, index,
clean_activation)`, `activation_name`, and either `index_axis_names` or an
explicit `index_df` table. When `index_df` is explicit, metric output is flat,
matching TransformerLens' behavior. SafeLens-style calls that pass explicit
`PatchSpec` objects still return detailed `PatchResult` records by default;
pass `return_details=False` to format those as metric grids.

The exported component setters such as `layer_pos_patch_setter` and
`layer_head_vector_patch_setter` accept both SafeLens' internal
`(activation, PatchSpec, ActivationCache)` shape and TransformerLens'
`(activation, index, clean_activation)` shape.

Model compatibility note: the patching layer can express the operations above,
but a concrete `ModelWrapper` must expose matching hook points and tensor
shapes. In particular, `result` helpers require true per-head result tensors,
not merged attention projection outputs. A raw HuggingFace module wrapper only
exposes module-level hooks unless extended with component hooks.

Example:

```python
from SafeLens.core.hooks import ActivationCache
from SafeLens.core.patching import PatchSpec, run_activation_patch

clean_cache = ActivationCache({"layer_0": clean_activation})
spec = PatchSpec(layer=0, target_index=3)

result = run_activation_patch(
    model,
    corrupted_batch,
    clean_cache,
    spec,
    metric=lambda output: float(output["score"]),
)
```

::: SafeLens.core.patching

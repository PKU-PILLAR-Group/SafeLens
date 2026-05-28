"""Hook and activation-cache primitives inspired by TransformerLens."""

from __future__ import annotations

import re
from collections.abc import Callable, Iterable, Iterator, MutableMapping, Sequence
from contextlib import contextmanager
from copy import deepcopy
from dataclasses import dataclass
from inspect import Parameter, signature
from typing import Any, Literal, Protocol

from SafeLens.core.base import Batch, HookFn, LayerRef, ModelWrapper

NamesFilter = str | Sequence[str] | Callable[[str], bool] | None
ActivationKey = str | tuple[Any, ...]
HookDirection = Literal["fwd", "bwd", "both"]

_MISSING = object()
_FULL_SLICE = slice(None)

_ACT_NAME_ALIASES = {
    "attn": "pattern",
    "attn_logits": "attn_scores",
    "key": "k",
    "query": "q",
    "value": "v",
    "mlp_pre": "pre",
    "mlp_mid": "mid",
    "mlp_post": "post",
}
_LAYER_TYPE_ALIASES = {
    "a": "attn",
    "attention": "attn",
    "m": "mlp",
    "b": "",
    "block": "",
    "blocks": "",
}
_ATTN_ACTS = {"k", "v", "q", "z", "rot_k", "rot_q", "result", "pattern", "attn_scores"}
_MLP_ACTS = {"pre", "post", "mid", "pre_linear"}
_LAYER_NORM_ACTS = {"scale", "normalized"}


class RemovableHandle(Protocol):
    """Protocol for PyTorch-style removable hook handles."""

    def remove(self) -> None:
        """Remove a registered hook."""


@dataclass
class LensHandle:
    """Small removable hook handle with permanence and context-level metadata."""

    remove_fn: Callable[[], None]
    is_permanent: bool = False
    level: int | None = None
    removed: bool = False

    def remove(self) -> None:
        """Remove this hook once."""
        if not self.removed:
            self.remove_fn()
            self.removed = True


class HookPoint:
    """Dependency-free identity hook point for instrumenting custom SafeLens models."""

    def __init__(self, name: str | None = None) -> None:
        self.name = name
        self.ctx: dict[str, Any] = {}
        self.fwd_hooks: list[tuple[HookFn, LensHandle]] = []
        self.bwd_hooks: list[tuple[HookFn, LensHandle]] = []
        self.hook_conversion: Any = None

    def __call__(self, activation: Any) -> Any:
        """Run forward hooks over an activation and return the final value."""
        output = activation
        for hook_fn, _handle in list(self.fwd_hooks):
            hook_input = self.hook_conversion.convert(output) if self.hook_conversion else output
            patched = _call_hookpoint_fn(hook_fn, hook_input, self)
            if patched is not None:
                output = self.hook_conversion.revert(patched) if self.hook_conversion else patched
        if self.bwd_hooks:
            output = self._register_backward_hooks(output)
        return output

    def forward(self, activation: Any) -> Any:
        """TransformerLens-style module entrypoint."""
        return self(activation)

    def add_perma_hook(
        self,
        hook_fn: HookFn,
        dir: Literal["fwd", "bwd"] = "fwd",
    ) -> LensHandle:
        """Register a permanent hook."""
        return self.add_hook(hook_fn, dir=dir, is_permanent=True)

    def add_hook(
        self,
        hook_fn: HookFn,
        *,
        dir: Literal["fwd", "bwd"] = "fwd",
        is_permanent: bool = False,
        level: int | None = None,
        prepend: bool = False,
        alias_names: Sequence[str] | None = None,
    ) -> LensHandle:
        """Register a hook and return a removable handle."""
        if alias_names is not None:
            hook_fn = _alias_hook_fn(hook_fn, self, alias_names)
        hook_list = self._hook_list(dir)
        record: tuple[HookFn, LensHandle]

        def remove_record() -> None:
            if record in hook_list:
                hook_list.remove(record)

        handle = LensHandle(remove_record, is_permanent=is_permanent, level=level)
        record = (hook_fn, handle)
        if prepend:
            hook_list.insert(0, record)
        else:
            hook_list.append(record)
        return handle

    def has_hooks(
        self,
        dir: HookDirection = "both",
        *,
        including_permanent: bool = True,
        level: int | None = None,
    ) -> bool:
        """Return whether matching hooks are registered."""
        return any(
            _handle_matches(handle, including_permanent=including_permanent, level=level)
            for _hook_fn, handle in self._matching_hook_records(dir)
        )

    def remove_hooks(
        self,
        dir: HookDirection = "both",
        *,
        including_permanent: bool = False,
        level: int | None = None,
    ) -> None:
        """Remove hooks matching permanence and context-level filters."""
        for _hook_fn, handle in list(self._matching_hook_records(dir)):
            if _handle_matches(handle, including_permanent=including_permanent, level=level):
                handle.remove()

    def clear_context(self) -> None:
        """Clear this hook point's mutable context dictionary."""
        self.ctx.clear()

    def enable_reshape(self, hook_conversion: Any = None) -> None:
        """Set an optional conversion applied around user hooks."""
        self.hook_conversion = hook_conversion

    def layer(self) -> int:
        """Extract the layer index from names like `blocks.3.attn.hook_q`."""
        if self.name is None:
            raise ValueError("Cannot infer layer from an unnamed HookPoint.")
        match = re.search(r"(?:blocks\.|layer_)(\d+)", self.name)
        if match is None:
            raise ValueError(f"Cannot infer layer from hook name {self.name!r}.")
        return int(match.group(1))

    def _hook_list(self, dir: Literal["fwd", "bwd"]) -> list[tuple[HookFn, LensHandle]]:
        if dir == "fwd":
            return self.fwd_hooks
        if dir == "bwd":
            return self.bwd_hooks
        raise ValueError(f"Invalid hook direction {dir!r}.")

    def _matching_hook_records(self, dir: HookDirection) -> list[tuple[HookFn, LensHandle]]:
        if dir == "fwd":
            return list(self.fwd_hooks)
        if dir == "bwd":
            return list(self.bwd_hooks)
        if dir == "both":
            return [*self.fwd_hooks, *self.bwd_hooks]
        raise ValueError(f"Invalid hook direction {dir!r}.")

    def _register_backward_hooks(self, activation: Any) -> Any:
        register_hook = getattr(activation, "register_hook", None)
        if not callable(register_hook):
            return activation

        def backward_hook(grad: Any) -> Any:
            output_grad = grad
            for hook_fn, _handle in list(self.bwd_hooks):
                patched = _call_hookpoint_fn(hook_fn, output_grad, self)
                if patched is not None:
                    output_grad = patched
            return output_grad

        try:
            register_hook(backward_hook)
        except RuntimeError:
            return activation
        return activation


class _AliasedHookPoint:
    """HookPoint view that presents an alias name while sharing context."""

    def __init__(self, alias_name: str, target: HookPoint) -> None:
        self._alias_name = alias_name
        self._target = target

    @property
    def name(self) -> str:
        return self._alias_name

    @property
    def ctx(self) -> dict[str, Any]:
        return self._target.ctx

    @property
    def hook_conversion(self) -> Any:
        return self._target.hook_conversion

    def layer(self) -> int:
        match = re.search(r"(?:blocks\.|layer_)(\d+)", self._alias_name)
        if match is None:
            raise ValueError(f"Cannot infer layer from hook name {self._alias_name!r}.")
        return int(match.group(1))


def activation_name_for_layer(layer: LayerRef) -> str:
    """Return the canonical cache name for a layer reference."""
    if isinstance(layer, int):
        return f"layer_{layer}"
    return layer


def get_act_name(
    name: str,
    layer: int | str | None = None,
    layer_type: str | None = None,
) -> str:
    """Convert common TransformerLens activation shorthands into hook names."""
    if ("." in name or name.startswith("hook_")) and layer is None and layer_type is None:
        return name

    match = re.match(r"([a-z_]+)(\d+)([a-z]?.*)", name)
    if match is not None:
        name, parsed_layer, parsed_layer_type = match.groups()
        layer = parsed_layer
        layer_type = parsed_layer_type or layer_type

    name = _ACT_NAME_ALIASES.get(name, name)
    if name in _ATTN_ACTS:
        layer_type = "attn"
    elif name in _MLP_ACTS:
        layer_type = "mlp"
    elif layer_type in _LAYER_TYPE_ALIASES:
        layer_type = _LAYER_TYPE_ALIASES[layer_type]

    full_name = ""
    if layer is not None:
        full_name += f"blocks.{layer}."
    if layer_type:
        full_name += f"{layer_type}."
    full_name += f"hook_{name}"
    if name in _LAYER_NORM_ACTS and layer is None:
        full_name = f"ln_final.{full_name}"
    return full_name


def safelens_act_name(name: str, layer: int | str | None = None) -> str:
    """Return SafeLens-style activation names such as `layer_0.resid_pre`."""
    name = _ACT_NAME_ALIASES.get(name, name)
    if layer is None:
        return f"hook_{name}"
    return f"{activation_name_for_layer(layer)}.{name}"


def matches_names_filter(name: str, names_filter: NamesFilter = None) -> bool:
    """Return whether an activation name matches a TransformerLens-style names filter."""
    if names_filter is None:
        return True
    if isinstance(names_filter, str):
        return _activation_names_equivalent(name, names_filter)
    if callable(names_filter):
        return bool(names_filter(name))
    return any(_activation_names_equivalent(name, candidate) for candidate in names_filter)


class ActivationCache(MutableMapping[Any, Any]):
    """Dictionary-like activation cache with small tensor-friendly helpers."""

    def __init__(
        self,
        cache_dict: dict[str, Any] | None = None,
        model: Any = None,
        has_batch_dim: bool = True,
    ) -> None:
        self._cache = dict(cache_dict or {})
        self.model = model
        self.has_batch_dim = has_batch_dim

    @property
    def cache_dict(self) -> dict[str, Any]:
        """TransformerLens-compatible view of the underlying activation mapping."""
        return self._cache

    @cache_dict.setter
    def cache_dict(self, value: dict[str, Any]) -> None:
        self._cache = dict(value)

    @property
    def has_embed(self) -> bool:
        """Return whether token embeddings are cached."""
        return "hook_embed" in self._cache

    @property
    def has_pos_embed(self) -> bool:
        """Return whether positional embeddings are cached."""
        return "hook_pos_embed" in self._cache

    def __getitem__(self, key: ActivationKey) -> Any:
        return self._cache[self.resolve_key(key)]

    def __setitem__(self, key: str, value: Any) -> None:
        self._cache[key] = value

    def __delitem__(self, key: str) -> None:
        del self._cache[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self._cache)

    def __len__(self) -> int:
        return len(self._cache)

    def __contains__(self, key: object) -> bool:
        if isinstance(key, str) or isinstance(key, tuple):
            try:
                self.resolve_key(key)
                return True
            except KeyError:
                return False
        return False

    def __repr__(self) -> str:
        batch = "with batch dim" if self.has_batch_dim else "without batch dim"
        return f"ActivationCache({len(self)} activations, {batch})"

    def resolve_key(self, key: ActivationKey) -> str:
        """Resolve exact, SafeLens-style, or TransformerLens-style activation keys."""
        candidates = activation_name_candidates(key, n_layers=self._infer_n_layers())
        for candidate in candidates:
            if candidate in self._cache:
                return candidate
        raise KeyError(f"Unknown activation key {key!r}. Tried {candidates!r}.")

    def store(
        self,
        name: str,
        activation: Any,
        *,
        detach: bool = True,
        clone: bool = False,
        device: Any = None,
    ) -> None:
        """Store an activation, optionally detaching, cloning, or moving it."""
        self._cache[name] = prepare_activation_for_cache(
            activation,
            detach=detach,
            clone=clone,
            device=device,
        )

    def get_activation(self, name: str) -> Any:
        """Return one cached activation."""
        return self[name]

    def keys_matching(self, names_filter: NamesFilter) -> list[str]:
        """Return activation names matching a TransformerLens-style names filter."""
        return [name for name in self._cache if _cache_key_matches_filter(name, names_filter)]

    def select(self, names_filter: NamesFilter) -> ActivationCache:
        """Return a new cache containing only matching activation names."""
        return ActivationCache(
            {
                name: value
                for name, value in self._cache.items()
                if _cache_key_matches_filter(name, names_filter)
            },
            model=self.model,
            has_batch_dim=self.has_batch_dim,
        )

    def clone(self) -> ActivationCache:
        """Return a cloned copy when activations support `.clone()`, otherwise deep-copy values."""
        return ActivationCache(
            {name: clone_activation(value) for name, value in self._cache.items()},
            model=self.model,
            has_batch_dim=self.has_batch_dim,
        )

    def to_dict(self) -> dict[str, Any]:
        """Return a plain dictionary view copy."""
        return dict(self._cache)

    def apply_to_values(self, fn: Callable[[Any], Any]) -> ActivationCache:
        """Apply a function to every cached value and return a new cache."""
        return ActivationCache(
            {name: fn(value) for name, value in self._cache.items()},
            model=self.model,
            has_batch_dim=self.has_batch_dim,
        )

    def to(self, device: Any, move_model: bool | None = None) -> ActivationCache:
        """Move tensor-like activations to a device when values support `.to()`."""
        self._cache = {name: _move_value(value, device) for name, value in self._cache.items()}
        if move_model:
            model_to = getattr(self.model, "to", None)
            if callable(model_to):
                model_to(device)
        return self

    def cpu(self) -> ActivationCache:
        """Move tensor-like activations to CPU when supported."""
        return self.to("cpu")

    def detach(self) -> ActivationCache:
        """Detach tensor-like activations when values support `.detach()`."""
        return self.apply_to_values(_detach_value)

    def remove_batch_dim(self) -> ActivationCache:
        """Remove singleton batch dimensions in place and return this cache."""
        if not self.has_batch_dim:
            return self
        updated_values: dict[str, Any] = {}
        for name, value in list(self._cache.items()):
            if _has_leading_dim(value, 1):
                updated_values[name] = _slice_dim(value, 0, dim=0)
                continue
            shape = _shape_of(value)
            if len(shape) >= 2:
                raise ValueError(
                    f"Cannot remove batch dimension from cache with batch size > 1, "
                    f"for key {name} with shape {shape!r}."
                )
            updated_values[name] = value
        self._cache.update(updated_values)
        self.has_batch_dim = False
        return self

    def toggle_autodiff(self, mode: bool = False) -> None:
        """Set PyTorch's global grad-enabled state when PyTorch is available."""
        try:
            import torch
        except ImportError:
            return None
        torch.set_grad_enabled(mode)
        return None

    def apply_slice_to_batch_dim(self, batch_slice: Any) -> ActivationCache:
        """Return a cache sliced along the batch dimension."""
        if not self.has_batch_dim:
            raise ValueError("Cannot slice batch dimension on a cache without batch dim.")
        has_batch_dim = not isinstance(batch_slice, int)
        return ActivationCache(
            {name: _slice_dim(value, batch_slice, dim=0) for name, value in self._cache.items()},
            model=self.model,
            has_batch_dim=has_batch_dim,
        )

    def stack_activation(
        self,
        activation_name: str,
        layer: int | None = None,
        layer_type: str | None = None,
        *,
        sublayer_type: str | None = None,
    ) -> Any:
        """Stack one activation across layers."""
        if sublayer_type is not None:
            layer_type = sublayer_type
        n_layers = self._normalize_layer(layer)
        values = [
            self[(activation_name, current_layer, layer_type)] for current_layer in range(n_layers)
        ]
        return stack_values(values)

    def accumulated_resid(
        self,
        layer: int | None = None,
        incl_mid: bool = False,
        apply_ln: bool = False,
        pos_slice: Any = None,
        mlp_input: bool = False,
        return_labels: bool = False,
    ) -> Any:
        """Return residual stream states up to a layer, useful for logit-lens workflows."""
        target_layer = self._normalize_layer(layer)
        values: list[Any] = []
        labels: list[str] = []
        n_layers = self._infer_n_layers()
        max_pre_layer = min(target_layer, n_layers - 1)

        for current_layer in range(max_pre_layer + 1):
            if ("resid_pre", current_layer) in self:
                values.append(_maybe_slice_pos(self[("resid_pre", current_layer)], pos_slice))
                labels.append(f"{current_layer}_pre")
            if incl_mid and current_layer < target_layer and ("resid_mid", current_layer) in self:
                values.append(_maybe_slice_pos(self[("resid_mid", current_layer)], pos_slice))
                labels.append(f"{current_layer}_mid")

        if mlp_input and ("resid_mid", target_layer) in self:
            values.append(_maybe_slice_pos(self[("resid_mid", target_layer)], pos_slice))
            labels.append(f"{target_layer}_mid")
        if target_layer >= n_layers and n_layers > 0 and ("resid_post", n_layers - 1) in self:
            values.append(_maybe_slice_pos(self[("resid_post", n_layers - 1)], pos_slice))
            labels.append("final_post")
        if not values:
            raise KeyError("No residual stream activations found in cache.")

        residual_stack = stack_values(values)
        if apply_ln:
            residual_stack = self.apply_ln_to_stack(
                residual_stack,
                layer=target_layer,
                mlp_input=mlp_input,
                pos_slice=pos_slice,
                recompute_ln=target_layer == n_layers,
                has_batch_dim=self.has_batch_dim,
            )
        if return_labels:
            return residual_stack, labels
        return residual_stack

    def decompose_resid(
        self,
        layer: int | None = None,
        mlp_input: bool = False,
        mode: Literal["all", "mlp", "attn"] = "all",
        apply_ln: bool = False,
        pos_slice: Any = None,
        incl_embeds: bool = True,
        return_labels: bool = False,
    ) -> Any:
        """Decompose a residual stream into embedding, attention, and MLP components."""
        target_layer = self._normalize_layer(layer)
        values: list[Any] = []
        labels: list[str] = []
        include_attn = mode != "mlp"
        include_mlp = mode != "attn"

        for key, label in (("hook_embed", "embed"), ("hook_pos_embed", "pos_embed")):
            if incl_embeds and key in self:
                values.append(_maybe_slice_pos(self[key], pos_slice))
                labels.append(label)

        for current_layer in range(target_layer):
            if include_attn and ("attn_out", current_layer) in self:
                values.append(_maybe_slice_pos(self[("attn_out", current_layer)], pos_slice))
                labels.append(f"{current_layer}_attn_out")
            if include_mlp and ("mlp_out", current_layer) in self:
                values.append(_maybe_slice_pos(self[("mlp_out", current_layer)], pos_slice))
                labels.append(f"{current_layer}_mlp_out")

        if mlp_input and include_attn and ("attn_out", target_layer) in self:
            values.append(_maybe_slice_pos(self[("attn_out", target_layer)], pos_slice))
            labels.append(f"{target_layer}_attn_out")
        if not values:
            raise KeyError("No residual decomposition activations found in cache.")

        residual_stack = stack_values(values)
        if apply_ln:
            residual_stack = self.apply_ln_to_stack(
                residual_stack,
                layer=target_layer,
                pos_slice=pos_slice,
                has_batch_dim=self.has_batch_dim,
            )
        if return_labels:
            return residual_stack, labels
        return residual_stack

    def stack_head_results(
        self,
        layer: int | None = None,
        return_labels: bool = False,
        incl_remainder: bool = False,
        pos_slice: Any = None,
        apply_ln: bool = False,
        *,
        component: str = "result",
    ) -> Any:
        """Stack per-head activations from `[batch, pos, head, d_model]` caches."""
        target_layer = self._normalize_layer(layer)
        if component == "result" and not any(
            (component, current_layer) in self for current_layer in range(target_layer)
        ):
            try:
                self.compute_head_results(target_layer, store=True)
            except (KeyError, ValueError):
                pass
        values: list[Any] = []
        labels: list[str] = []
        for current_layer in range(target_layer):
            if (component, current_layer) not in self:
                continue
            activation = _maybe_slice_pos(
                self[(component, current_layer)],
                pos_slice,
                dim=_head_vector_pos_dim(component),
            )
            head_dim = _head_axis_after_pos_slice(activation, pos_slice)
            for head_index in range(_infer_head_count(activation, dim=head_dim)):
                values.append(_slice_dim(activation, head_index, dim=head_dim))
                labels.append(f"L{current_layer}H{head_index}")
        if incl_remainder:
            if ("resid_post", target_layer - 1) not in self:
                raise KeyError(
                    "incl_remainder=True requires cached `resid_post` for the previous layer."
                )
            remainder = _maybe_slice_pos(self[("resid_post", target_layer - 1)], pos_slice)
            if values:
                remainder = _subtract_values(remainder, _sum_values(values))
            values.append(remainder)
            labels.append("remainder")
        if not values:
            raise KeyError(f"No {component!r} head activations found in cache.")
        head_stack = stack_values(values)
        if apply_ln:
            head_stack = self.apply_ln_to_stack(
                head_stack,
                layer=target_layer,
                pos_slice=pos_slice,
                has_batch_dim=self.has_batch_dim,
            )
        if return_labels:
            return head_stack, labels
        return head_stack

    def compute_head_results(
        self,
        layer: int | None = None,
        *,
        store: bool = True,
        pos_slice: Any = None,
        return_labels: bool = False,
    ) -> Any:
        """Compute per-head residual-space results from cached `z` and model `W_O`.

        This fills the common TransformerLens workflow gap where a model exposes
        head outputs `z` and output weights `W_O`, but not cached `result`
        vectors directly.
        """
        if self.model is None or not hasattr(self.model, "W_O"):
            raise ValueError("compute_head_results requires a cache with a model exposing W_O.")
        from SafeLens.core.analysis import compute_head_results_from_z

        target_layer = self._normalize_layer(layer)
        n_layers = self._infer_n_layers()
        max_layer = min(target_layer, n_layers)
        values: list[Any] = []
        labels: list[str] = []

        for current_layer in range(max_layer):
            if ("z", current_layer) not in self:
                continue
            z_activation = _maybe_slice_pos(self[("z", current_layer)], pos_slice, dim=-3)
            result = compute_head_results_from_z(z_activation, self.model.W_O[current_layer])
            if store and pos_slice is None:
                self[f"layer_{current_layer}.result"] = result
            values.append(result)
            labels.append(f"{current_layer}_result")

        if not values:
            raise KeyError("No cached `z` activations found for head result computation.")
        result_stack = stack_values(values)
        if return_labels:
            return result_stack, labels
        return result_stack

    def get_neuron_results(
        self,
        layer: int,
        neuron_slice: Any = None,
        pos_slice: Any = None,
        project_output_onto: Any = None,
        *,
        component: str = "post",
    ) -> Any:
        """Return one layer's per-neuron residual contributions."""
        if (component, layer) not in self:
            raise KeyError(f"No cached {component!r} neuron activations found for layer {layer}.")
        w_out = _get_layer_weight(self.model, "W_out", layer)
        if w_out is None:
            raise ValueError("get_neuron_results requires a model exposing W_out.")

        neuron_acts = _maybe_slice_pos(self[(component, layer)], pos_slice)
        neuron_count = _infer_last_dim(neuron_acts)
        neuron_indices = _indices_from_slice(neuron_slice, neuron_count)
        neuron_acts = _select_indices_dim(neuron_acts, neuron_indices, dim=-1)
        layer_w_out = _select_indices_dim(w_out, neuron_indices, dim=0)
        neuron_results = _multiply_last_dim_by_matrix(neuron_acts, layer_w_out)
        if project_output_onto is not None:
            neuron_results = _project_last_dim(neuron_results, project_output_onto)
        return neuron_results

    def stack_neuron_results(
        self,
        layer: int | None = None,
        pos_slice: Any = None,
        neuron_slice: Any = None,
        return_labels: bool = False,
        incl_remainder: bool = False,
        apply_ln: bool = False,
        project_output_onto: Any = None,
        *,
        component: str = "post",
    ) -> Any:
        """Stack per-neuron MLP residual contributions when `W_out` is available."""
        target_layer = self._normalize_layer(layer)
        values: list[Any] = []
        labels: list[str] = []
        for current_layer in range(target_layer):
            if (component, current_layer) not in self:
                continue
            activation = _maybe_slice_pos(self[(component, current_layer)], pos_slice)
            neuron_indices = _indices_from_slice(neuron_slice, _infer_last_dim(activation))
            try:
                layer_results = self.get_neuron_results(
                    current_layer,
                    neuron_slice=neuron_indices,
                    pos_slice=pos_slice,
                    component=component,
                )
                neuron_dim = -2
            except ValueError:
                if project_output_onto is not None:
                    raise
                layer_results = _select_indices_dim(activation, neuron_indices, dim=-1)
                neuron_dim = -1
            for position, neuron_index in enumerate(neuron_indices):
                neuron_value = _slice_dim(layer_results, position, dim=neuron_dim)
                values.append(neuron_value)
                labels.append(f"L{current_layer}N{neuron_index}")
        if incl_remainder:
            if ("resid_post", target_layer - 1) not in self:
                raise KeyError(
                    "incl_remainder=True requires cached `resid_post` for the previous layer."
                )
            remainder = _maybe_slice_pos(self[("resid_post", target_layer - 1)], pos_slice)
            if values:
                remainder = _subtract_values(remainder, _sum_values(values))
            values.append(remainder)
            labels.append("remainder")
        if not values:
            raise KeyError(f"No {component!r} neuron activations found in cache.")
        neuron_stack = stack_values(values)
        if apply_ln:
            neuron_stack = self.apply_ln_to_stack(
                neuron_stack,
                layer=target_layer,
                pos_slice=pos_slice,
                has_batch_dim=self.has_batch_dim,
            )
        if project_output_onto is not None:
            neuron_stack = _project_last_dim(neuron_stack, project_output_onto)
        if return_labels:
            return neuron_stack, labels
        return neuron_stack

    def get_full_resid_decomposition(
        self,
        layer: int | None = None,
        mlp_input: bool = False,
        expand_neurons: bool = True,
        apply_ln: bool = False,
        pos_slice: Any = None,
        return_labels: bool = False,
        project_output_onto: Any = None,
    ) -> Any:
        """Return a best-effort decomposition into heads, MLP neurons, embeds, and bias."""
        target_layer = self._normalize_layer(layer)
        stacks: list[Any] = []
        labels: list[str] = []

        def add_stack(component_stack: Any, component_labels: list[str]) -> None:
            stacks.extend(_unstack_first_dim(component_stack))
            labels.extend(component_labels)

        try:
            head_stack, head_labels = self.stack_head_results(
                target_layer + (1 if mlp_input else 0),
                pos_slice=pos_slice,
                return_labels=True,
            )
            add_stack(head_stack, head_labels)
        except KeyError:
            try:
                attn_stack, attn_labels = self.decompose_resid(
                    target_layer,
                    mlp_input=mlp_input,
                    mode="attn",
                    incl_embeds=False,
                    pos_slice=pos_slice,
                    return_labels=True,
                )
                add_stack(attn_stack, attn_labels)
            except KeyError:
                pass

        if expand_neurons:
            try:
                neuron_stack, neuron_labels = self.stack_neuron_results(
                    target_layer,
                    pos_slice=pos_slice,
                    return_labels=True,
                )
                add_stack(neuron_stack, neuron_labels)
            except KeyError:
                try:
                    mlp_stack, mlp_labels = self.decompose_resid(
                        target_layer,
                        mode="mlp",
                        incl_embeds=False,
                        pos_slice=pos_slice,
                        return_labels=True,
                    )
                    add_stack(mlp_stack, mlp_labels)
                except KeyError:
                    pass
        else:
            try:
                mlp_stack, mlp_labels = self.decompose_resid(
                    target_layer,
                    mode="mlp",
                    incl_embeds=False,
                    pos_slice=pos_slice,
                    return_labels=True,
                )
                add_stack(mlp_stack, mlp_labels)
            except KeyError:
                pass

        for key, label in (("hook_embed", "embed"), ("hook_pos_embed", "pos_embed")):
            if key in self:
                stacks.append(_maybe_slice_pos(self[key], pos_slice))
                labels.append(label)

        accumulated_bias = _get_model_attr(self.model, "accumulated_bias")
        if callable(accumulated_bias):
            try:
                bias = accumulated_bias(
                    target_layer,
                    mlp_input,
                    include_mlp_biases=expand_neurons,
                )
            except TypeError:
                try:
                    bias = accumulated_bias(target_layer, mlp_input)
                except TypeError:
                    bias = accumulated_bias(target_layer)
            bias = _expand_bias_like(bias, stacks[0] if stacks else None)
            stacks.append(bias)
            labels.append("bias")

        if not stacks:
            raise KeyError("No activations found for a full residual decomposition.")
        full_stack = stack_values(stacks)
        if apply_ln:
            full_stack = self.apply_ln_to_stack(
                full_stack,
                layer=target_layer,
                pos_slice=pos_slice,
                has_batch_dim=self.has_batch_dim,
            )
        if project_output_onto is not None:
            full_stack = _project_last_dim(full_stack, project_output_onto)
        if return_labels:
            return full_stack, labels
        return full_stack

    def apply_ln_to_stack(
        self,
        residual_stack: Any,
        layer: int | None = None,
        mlp_input: bool = False,
        pos_slice: Any = None,
        batch_slice: Any = None,
        has_batch_dim: bool | None = None,
        recompute_ln: bool = False,
        *,
        scale_key: ActivationKey | None = None,
    ) -> Any:
        """Apply cached layer-norm scale to a residual stack when scale is available."""
        resolved_has_batch_dim = self.has_batch_dim if has_batch_dim is None else has_batch_dim
        target_layer = self._normalize_layer(layer)
        n_layers = self._infer_n_layers()
        if batch_slice is not None and resolved_has_batch_dim:
            residual_stack = _slice_dim(residual_stack, batch_slice, dim=1)
        if recompute_ln and scale_key is None and target_layer == n_layers:
            ln_final = _get_final_layer_norm(self.model)
            recomputed = _apply_final_layer_norm_to_stack(residual_stack, ln_final)
            if recomputed is not _MISSING:
                return recomputed

        resolved_scale_key = scale_key
        if resolved_scale_key is None:
            if target_layer == n_layers:
                candidates: list[ActivationKey] = ["ln_final.hook_scale"]
            else:
                candidates = [
                    ("scale", target_layer, "ln2" if mlp_input else "ln1"),
                    ("scale", target_layer, "ln1" if mlp_input else "ln2"),
                ]
            resolved_scale_key = next(
                (candidate for candidate in candidates if candidate in self),
                None,
            )
        if resolved_scale_key is None:
            return residual_stack
        scale = self[resolved_scale_key]
        if batch_slice is not None and resolved_has_batch_dim:
            scale = _slice_dim(scale, batch_slice, dim=0)
        if pos_slice is not None:
            pos_dim = 1 if resolved_has_batch_dim and len(_shape_of(scale)) >= 3 else 0
            scale = _slice_dim(scale, pos_slice, dim=pos_dim)
        if _uses_centered_layer_norm(self.model):
            residual_stack = _subtract_last_dim_mean(residual_stack)
        return _divide_values(residual_stack, scale)

    def logit_attrs(
        self,
        residual_stack: Any,
        tokens: Any,
        *,
        incorrect_tokens: Any = None,
        directions: Any = None,
        apply_ln: bool = True,
        pos_slice: Any = None,
        batch_slice: Any = None,
        has_batch_dim: bool | None = None,
    ) -> Any:
        """Project residual components onto token residual directions."""
        resolved_has_batch_dim = self.has_batch_dim if has_batch_dim is None else has_batch_dim
        if directions is None:
            if self.model is None:
                directions = tokens
            else:
                directions = self.model.tokens_to_residual_directions(
                    _normalize_logit_tokens(self.model, tokens)
                )
        if incorrect_tokens is not None:
            if self.model is None:
                incorrect_directions = incorrect_tokens
            else:
                incorrect_directions = self.model.tokens_to_residual_directions(
                    _normalize_logit_tokens(self.model, incorrect_tokens)
                )
            if _shape_of(directions) != _shape_of(incorrect_directions):
                raise ValueError(
                    "tokens and incorrect_tokens must resolve to residual directions with the "
                    f"same shape, got {_shape_of(directions)!r} and "
                    f"{_shape_of(incorrect_directions)!r}."
                )
            directions = _subtract_values(directions, incorrect_directions)
        if batch_slice is not None and _direction_has_batch_axis(directions, resolved_has_batch_dim):
            directions = _slice_dim(directions, batch_slice, dim=0)
        if pos_slice is not None and _direction_has_pos_axis(directions, resolved_has_batch_dim):
            pos_dim = 1 if resolved_has_batch_dim else 0
            directions = _slice_dim(directions, pos_slice, dim=pos_dim)
        if apply_ln:
            residual_stack = self.apply_ln_to_stack(
                residual_stack,
                layer=-1,
                pos_slice=pos_slice,
                batch_slice=batch_slice,
                has_batch_dim=resolved_has_batch_dim,
            )
        return _dot_last_dim(residual_stack, directions)

    def _infer_n_layers(self) -> int:
        n_layers = _get_config_int(self.model, ("n_layers", "num_hidden_layers", "num_layers"))
        if n_layers is not None:
            return n_layers
        layers: set[int] = set()
        for key in self._cache:
            for pattern in (r"blocks\.(\d+)\.", r"layer_(\d+)\."):
                match = re.search(pattern, key)
                if match is not None:
                    layers.add(int(match.group(1)))
        if layers:
            return max(layers) + 1
        return 0

    def _normalize_layer(self, layer: int | None) -> int:
        n_layers = self._infer_n_layers()
        if layer is None or layer == -1:
            return n_layers
        if layer < 0:
            return n_layers + layer
        return layer


def clone_activation(activation: Any) -> Any:
    """Clone tensor-like values and deep-copy everything else."""
    clone = getattr(activation, "clone", None)
    if callable(clone):
        return clone()
    return deepcopy(activation)


def prepare_activation_for_cache(
    activation: Any,
    *,
    detach: bool = True,
    clone: bool = False,
    device: Any = None,
) -> Any:
    """Prepare an activation for caching without requiring a torch dependency."""
    value = activation
    detach_fn = getattr(value, "detach", None)
    if detach and callable(detach_fn):
        value = detach_fn()
    if clone:
        value = clone_activation(value)
    to_fn = getattr(value, "to", None)
    if device is not None and callable(to_fn):
        value = to_fn(device)
    return value


def extract_hook_output(args: tuple[Any, ...], kwargs: dict[str, Any]) -> Any:
    """Extract an activation from either PyTorch-style or keyword-style hook calls."""
    if len(args) >= 3:
        return args[2]
    if len(args) == 2 and isinstance(args[1], HookPoint):
        return args[0]
    if "output" in kwargs:
        return kwargs["output"]
    if "activation" in kwargs:
        return kwargs["activation"]
    return _MISSING


def has_hook_output(args: tuple[Any, ...], kwargs: dict[str, Any]) -> bool:
    """Return whether a hook call contains an activation output."""
    return extract_hook_output(args, kwargs) is not _MISSING


def activation_name_candidates(key: ActivationKey, *, n_layers: int = 0) -> list[str]:
    """Return possible cache names for an activation key."""
    if isinstance(key, str):
        candidates = [key]
        candidates.extend(_safelens_names_from_transformer_lens_name(key))
        candidates.extend(_transformer_lens_names_from_safelens_name(key))
        candidates.append(get_act_name(key))
        if "." not in key:
            candidates.append(safelens_act_name(key))
        return _unique(candidates)

    if not key:
        return []

    name = str(key[0])
    original_layer = key[1] if len(key) >= 2 else None
    layer = original_layer
    layer_type = str(key[2]) if len(key) >= 3 and key[2] is not None else None
    if layer == -1 and n_layers > 0:
        layer = n_layers - 1
    aliased_name = _ACT_NAME_ALIASES.get(name, name)
    aliased_layer_type = _LAYER_TYPE_ALIASES.get(layer_type, layer_type)

    normalized_key = (name, layer, *key[2:]) if original_layer != layer else key
    candidates = [".".join(str(item) for item in normalized_key if item is not None)]
    if original_layer != layer:
        candidates.append(".".join(str(item) for item in key if item is not None))
    candidates.append(get_act_name(aliased_name, layer, layer_type))
    if layer is not None:
        candidates.append(safelens_act_name(aliased_name, layer))
        if layer_type is None:
            if aliased_name in _ATTN_ACTS:
                candidates.extend(
                    [
                        f"{activation_name_for_layer(layer)}.attn.{aliased_name}",
                        f"blocks.{layer}.attn.hook_{aliased_name}",
                    ]
                )
            elif aliased_name in _MLP_ACTS:
                candidates.extend(
                    [
                        f"{activation_name_for_layer(layer)}.mlp.{aliased_name}",
                        f"blocks.{layer}.mlp.hook_{aliased_name}",
                    ]
                )
        if aliased_layer_type:
            candidates.extend(
                [
                    f"{activation_name_for_layer(layer)}.{aliased_layer_type}.{aliased_name}",
                    f"blocks.{layer}.{aliased_layer_type}.hook_{aliased_name}",
                ]
            )
    return _unique(candidates)


def _safelens_names_from_transformer_lens_name(name: str) -> list[str]:
    match = re.fullmatch(
        r"blocks\.(\d+)\.(?:([a-zA-Z0-9_]+)\.)?hook_([a-zA-Z0-9_]+)",
        name,
    )
    if match is None:
        return []
    layer = int(match.group(1))
    layer_type = match.group(2)
    component = _ACT_NAME_ALIASES.get(match.group(3), match.group(3))
    candidates = [safelens_act_name(component, layer)]
    if layer_type:
        layer_type = _LAYER_TYPE_ALIASES.get(layer_type, layer_type)
        if layer_type:
            candidates.append(f"{activation_name_for_layer(layer)}.{layer_type}.{component}")
    return candidates


def _transformer_lens_names_from_safelens_name(name: str) -> list[str]:
    safe_match = re.fullmatch(
        r"layer_(\d+)\.(?:([a-zA-Z0-9_]+)\.)?([a-zA-Z0-9_]+)",
        name,
    )
    if safe_match is None:
        return []
    layer = int(safe_match.group(1))
    layer_type = safe_match.group(2)
    component = _ACT_NAME_ALIASES.get(safe_match.group(3), safe_match.group(3))
    return [get_act_name(component, layer, layer_type)]


def _cache_key_matches_filter(name: str, names_filter: NamesFilter) -> bool:
    if names_filter is None or callable(names_filter):
        return matches_names_filter(name, names_filter)
    if isinstance(names_filter, str):
        return _activation_names_equivalent(name, names_filter)
    return any(_activation_names_equivalent(name, candidate) for candidate in names_filter)


def _activation_names_equivalent(left: str, right: str) -> bool:
    if left == right:
        return True
    return right in activation_name_candidates(left) or left in activation_name_candidates(right)


def stack_values(values: Sequence[Any]) -> Any:
    """Stack tensor-like values or fall back to a list copy."""
    if not values:
        return []
    first = values[0]
    module = type(first).__module__.split(".")[0]
    if module == "torch":
        try:
            import torch

            return torch.stack(list(values))
        except Exception:
            pass
    return [clone_activation(value) for value in values]


def _call_hookpoint_fn(hook_fn: HookFn, activation: Any, hook: HookPoint) -> Any:
    hook_kwargs = {"activation": activation, "output": activation, "hook": hook}
    try:
        hook_signature = signature(hook_fn)
    except (TypeError, ValueError):
        return hook_fn(activation, hook)

    parameters = hook_signature.parameters.values()
    if any(param.kind == Parameter.VAR_KEYWORD for param in parameters):
        return hook_fn(**hook_kwargs)

    parameters = hook_signature.parameters.values()
    accepted_names = {
        param.name
        for param in parameters
        if param.kind in (Parameter.POSITIONAL_OR_KEYWORD, Parameter.KEYWORD_ONLY)
    }
    required_names = {
        param.name
        for param in hook_signature.parameters.values()
        if param.default is Parameter.empty
        and param.kind in (Parameter.POSITIONAL_OR_KEYWORD, Parameter.KEYWORD_ONLY)
    }
    filtered_kwargs = {name: value for name, value in hook_kwargs.items() if name in accepted_names}
    if required_names.issubset(filtered_kwargs):
        return hook_fn(**filtered_kwargs)

    try:
        return hook_fn(activation, hook)
    except TypeError:
        return hook_fn(**hook_kwargs)


def _alias_hook_fn(
    hook_fn: HookFn,
    target: HookPoint,
    alias_names: Sequence[str],
) -> HookFn:
    """Call one hook once per alias name, matching TransformerLens alias hooks."""

    def aliased_hook(activation: Any, _hook: HookPoint) -> Any:
        output = activation
        changed = False
        hook_result: Any = None
        for alias_name in alias_names:
            hook_result = _call_hookpoint_fn(hook_fn, output, _AliasedHookPoint(alias_name, target))
            if hook_result is not None:
                output = hook_result
                changed = True
        return output if changed else None

    return aliased_hook


def _handle_matches(
    handle: LensHandle,
    *,
    including_permanent: bool,
    level: int | None,
) -> bool:
    if handle.is_permanent and not including_permanent:
        return False
    return level is None or handle.level == level


def _move_value(value: Any, device: Any) -> Any:
    to_fn = getattr(value, "to", None)
    if callable(to_fn):
        return to_fn(device)
    return value


def _detach_value(value: Any) -> Any:
    detach = getattr(value, "detach", None)
    if callable(detach):
        return detach()
    return clone_activation(value)


def _remove_singleton_batch(value: Any) -> Any:
    shape = _shape_of(value)
    if shape and shape[0] != 1:
        raise ValueError(f"Expected singleton batch dimension, got shape {shape!r}.")
    return _slice_dim(value, 0, dim=0)


def _has_leading_dim(value: Any, size: int) -> bool:
    shape = _shape_of(value)
    return bool(shape and shape[0] == size)


def _maybe_slice_pos(value: Any, pos_slice: Any, *, dim: int = -2) -> Any:
    if pos_slice is None:
        return value
    return _slice_dim(value, pos_slice, dim=dim)


def _head_vector_pos_dim(component: str) -> int:
    return -3 if component in {"q", "k", "v", "z", "result"} else -2


def _slice_dim(value: Any, index: Any, *, dim: int) -> Any:
    index = _normalize_slice_index(index)
    shape = _shape_of(value)
    rank = len(shape)
    if dim < 0:
        dim = rank + dim
    if rank > 0:
        normalized = tuple(index if axis == dim else _FULL_SLICE for axis in range(rank))
        try:
            return value[normalized]
        except (TypeError, IndexError, KeyError):
            return _get_nested(value, normalized)
    return value


def _get_nested(value: Any, index: tuple[Any, ...]) -> Any:
    if not index:
        return value
    head = index[0]
    tail = index[1:]
    if isinstance(head, slice):
        if head == _FULL_SLICE:
            return [_get_nested(item, tail) for item in value]
        return [_get_nested(item, tail) for item in value[head]]
    indices = _explicit_indices(head, len(value) if isinstance(value, Sequence) else None)
    if indices is not None:
        return [_get_nested(value[position], tail) for position in indices]
    return _get_nested(value[head], tail)


def _explicit_indices(index: Any, size: int | None = None) -> list[int] | None:
    if isinstance(index, range):
        return [item % size if size is not None else item for item in index]
    tolist = getattr(index, "tolist", None)
    if callable(tolist):
        index = tolist()
    if isinstance(index, Sequence) and not isinstance(index, str | bytes):
        if index and all(isinstance(item, bool) for item in index):
            return [
                position
                for position, include in enumerate(index)
                if include and (size is None or position < size)
            ]
        return [int(item) % size if size is not None else int(item) for item in index]
    return None


def _normalize_slice_index(index: Any) -> Any:
    if index is None:
        return _FULL_SLICE
    if isinstance(index, tuple):
        return slice(*index)
    return index


def _shape_of(value: Any) -> tuple[int, ...]:
    shape = getattr(value, "shape", None)
    if shape is not None:
        return tuple(int(dim) for dim in shape)
    if isinstance(value, Sequence) and not isinstance(value, str | bytes):
        if not value:
            return (0,)
        return (len(value), *_shape_of(value[0]))
    return ()


def _direction_has_batch_axis(direction: Any, has_batch_dim: bool) -> bool:
    shape = _shape_of(direction)
    return has_batch_dim and len(shape) >= 3


def _direction_has_pos_axis(direction: Any, has_batch_dim: bool) -> bool:
    shape = _shape_of(direction)
    if not shape:
        return False
    return len(shape) >= (3 if has_batch_dim else 2)


def _head_axis_after_pos_slice(activation: Any, pos_slice: Any) -> int:
    if isinstance(pos_slice, int):
        return -2 if len(_shape_of(activation)) >= 2 else -1
    return -2


def _infer_head_count(activation: Any, *, dim: int = -2) -> int:
    shape = _shape_of(activation)
    if not shape:
        raise ValueError(f"Cannot infer head count from shape {shape!r}.")
    if dim < 0:
        dim = len(shape) + dim
    if dim < 0 or dim >= len(shape):
        raise ValueError(f"Cannot infer head count along dim {dim} from shape {shape!r}.")
    return shape[dim]


def _infer_last_dim(activation: Any) -> int:
    shape = _shape_of(activation)
    if not shape:
        raise ValueError("Cannot infer final dimension from a scalar activation.")
    return shape[-1]


def _unstack_first_dim(value: Any) -> list[Any]:
    shape = _shape_of(value)
    if not shape:
        return [value]
    return [_slice_dim(value, index, dim=0) for index in range(shape[0])]


def _divide_values(left: Any, right: Any) -> Any:
    try:
        return left / right
    except TypeError:
        if isinstance(left, list):
            if isinstance(right, list):
                left_shape = _shape_of(left)
                right_shape = _shape_of(right)
                if left_shape == right_shape:
                    return [
                        _divide_values(left_item, right_item)
                        for left_item, right_item in zip(left, right, strict=True)
                    ]
                if _can_broadcast_shape(right_shape, left_shape):
                    return [
                        _divide_values(
                            left_item,
                            _broadcast_index(right, right_shape, left_shape, 0, index),
                        )
                        for index, left_item in enumerate(left)
                    ]
                if _can_broadcast_shape(left_shape, right_shape):
                    return [
                        _divide_values(
                            _broadcast_index(left, left_shape, right_shape, 0, index),
                            right_item,
                        )
                        for index, right_item in enumerate(right)
                    ]
                if _is_vector(left) and _is_vector(right):
                    return [
                        _divide_values(left_item, right_item)
                        for left_item, right_item in zip(left, right, strict=True)
                    ]
                return [
                    _divide_values(left_item, right_item)
                    for left_item, right_item in zip(left, right, strict=True)
                ]
            return [_divide_values(left_item, right) for left_item in left]
        return left


def _multiply_by_last_vector(left: Any, right: Any) -> Any:
    try:
        return left[..., None] * right
    except Exception:
        pass
    if isinstance(left, list):
        return [_multiply_by_last_vector(left_item, right) for left_item in left]
    if isinstance(right, list):
        return [left * right_item for right_item in right]
    return left * right


def _multiply_last_dim_by_matrix(left: Any, right: Any) -> Any:
    try:
        import torch

        if hasattr(left, "shape") or hasattr(right, "shape"):
            if not hasattr(left, "shape"):
                left = torch.as_tensor(
                    left,
                    dtype=getattr(right, "dtype", None),
                    device=getattr(right, "device", None),
                )
            if not hasattr(right, "shape"):
                right = torch.as_tensor(
                    right,
                    dtype=getattr(left, "dtype", None),
                    device=getattr(left, "device", None),
                )
            return torch.einsum("...n,nm->...nm", left, right)
    except Exception:
        pass
    try:
        import numpy as np

        if hasattr(left, "shape") or hasattr(right, "shape"):
            return np.einsum("...n,nm->...nm", left, right)
    except Exception:
        pass

    if _shape_of(left) == ():
        return left
    if _is_vector(left):
        return [_multiply_by_last_vector(value, right[index]) for index, value in enumerate(left)]
    return [_multiply_last_dim_by_matrix(item, right) for item in left]


def _sum_values(values: Sequence[Any]) -> Any:
    if not values:
        return 0
    total = clone_activation(values[0])
    for value in values[1:]:
        total = _add_values(total, value)
    return total


def _add_values(left: Any, right: Any) -> Any:
    if isinstance(left, list) and isinstance(right, list):
        left_shape = _shape_of(left)
        right_shape = _shape_of(right)
        if left_shape == right_shape:
            return [
                _add_values(left_item, right_item)
                for left_item, right_item in zip(left, right, strict=True)
            ]
        if _can_broadcast_shape(right_shape, left_shape):
            return [
                _add_values(
                    left_item,
                    _broadcast_index(right, right_shape, left_shape, 0, index),
                )
                for index, left_item in enumerate(left)
            ]
        if _is_vector(left) and _is_vector(right):
            return [
                _add_values(left_item, right_item)
                for left_item, right_item in zip(left, right, strict=True)
            ]
        return [
            _add_values(left_item, right_item)
            for left_item, right_item in zip(left, right, strict=True)
        ]
    try:
        return left + right
    except TypeError:
        return left


def _indices_from_slice(index: Any, size: int) -> list[int]:
    if index is None:
        return list(range(size))
    if isinstance(index, slice):
        return list(range(size))[index]
    if isinstance(index, tuple):
        return list(range(size))[slice(*index)]
    if isinstance(index, int):
        return [index % size]
    if isinstance(index, range):
        return [item % size for item in index]
    tolist = getattr(index, "tolist", None)
    if callable(tolist):
        index = tolist()
    if isinstance(index, Sequence) and not isinstance(index, str | bytes):
        if index and all(isinstance(item, bool) for item in index):
            return [position for position, include in enumerate(index) if include]
        return [int(item) % size for item in index]
    raise TypeError(f"Unsupported neuron/head slice {index!r}.")


def _select_indices_dim(value: Any, indices: Sequence[int], *, dim: int) -> Any:
    try:
        import torch

        if hasattr(value, "shape"):
            shape = _shape_of(value)
            rank = len(shape)
            if dim < 0:
                dim = rank + dim
            index_tensor = torch.as_tensor(indices, dtype=torch.long, device=value.device)
            return value.index_select(dim, index_tensor)
    except Exception:
        pass
    try:
        import numpy as np

        if hasattr(value, "shape"):
            return np.take(value, list(indices), axis=dim)
    except Exception:
        pass
    shape = _shape_of(value)
    rank = len(shape)
    if dim < 0:
        dim = rank + dim
    if dim == 0:
        return [clone_activation(value[index]) for index in indices]
    if isinstance(value, list):
        return [_select_indices_dim(item, indices, dim=dim - 1) for item in value]
    return value


def _expand_bias_like(bias: Any, like: Any) -> Any:
    if like is None:
        return bias
    like_shape = _shape_of(like)
    bias_shape = _shape_of(bias)
    if not like_shape or not bias_shape or bias_shape == like_shape:
        return bias
    try:
        return bias.expand(like_shape)
    except Exception:
        pass
    if len(bias_shape) == 1 and bias_shape[-1] == like_shape[-1]:
        prefix = like_shape[:-1]
        result = bias
        for size in reversed(prefix):
            result = [clone_activation(result) for _ in range(size)]
        return result
    return bias


def _subtract_last_dim_mean(value: Any) -> Any:
    try:
        return value - value.mean(dim=-1, keepdim=True)
    except Exception:
        pass
    if _is_vector(value):
        if not value:
            return value
        mean = sum(float(item) for item in value) / len(value)
        return [float(item) - mean for item in value]
    if isinstance(value, list):
        return [_subtract_last_dim_mean(item) for item in value]
    return value


def _subtract_values(left: Any, right: Any) -> Any:
    try:
        return left - right
    except TypeError:
        if isinstance(left, list) and isinstance(right, list):
            left_shape = _shape_of(left)
            right_shape = _shape_of(right)
            if left_shape == right_shape:
                return [
                    _subtract_values(left_item, right_item)
                    for left_item, right_item in zip(left, right, strict=True)
                ]
            if _can_broadcast_shape(right_shape, left_shape):
                return [
                    _subtract_values(
                        left_item,
                        _broadcast_index(right, right_shape, left_shape, 0, index),
                    )
                    for index, left_item in enumerate(left)
                ]
            if _is_vector(left) and _is_vector(right):
                return [
                    _subtract_values(left_item, right_item)
                    for left_item, right_item in zip(left, right, strict=True)
                ]
            return [
                _subtract_values(left_item, right_item)
                for left_item, right_item in zip(left, right, strict=True)
            ]
        return left


def _dot_last_dim(left: Any, right: Any) -> Any:
    try:
        import torch

        if isinstance(left, torch.Tensor) or isinstance(right, torch.Tensor):
            if not isinstance(left, torch.Tensor):
                left = torch.as_tensor(
                    left,
                    dtype=getattr(right, "dtype", None),
                    device=getattr(right, "device", None),
                )
            if not isinstance(right, torch.Tensor):
                right = torch.as_tensor(
                    right,
                    dtype=getattr(left, "dtype", None),
                    device=getattr(left, "device", None),
                )
            return (left * right).sum(dim=-1)
    except Exception:
        pass
    try:
        import numpy as np

        if hasattr(left, "shape") or hasattr(right, "shape"):
            return (np.asarray(left) * np.asarray(right)).sum(axis=-1)
    except Exception:
        pass
    try:
        return (left * right).sum(dim=-1)
    except Exception:
        pass
    if isinstance(left, list) and isinstance(right, list):
        if _is_vector(left) and _is_vector(right):
            return sum(
                float(left_item) * float(right_item)
                for left_item, right_item in zip(left, right, strict=True)
            )
        if _is_vector(right):
            return [_dot_last_dim(left_item, right) for left_item in left]
        if _is_vector(left):
            return [_dot_last_dim(left, right_item) for right_item in right]
        left_shape = _shape_of(left)
        right_shape = _shape_of(right)
        if len(right_shape) < len(left_shape) and left_shape[-len(right_shape) :] == right_shape:
            return [_dot_last_dim(left_item, right) for left_item in left]
        if len(left_shape) < len(right_shape) and right_shape[-len(left_shape) :] == left_shape:
            return [_dot_last_dim(left, right_item) for right_item in right]
        if len(left) == len(right):
            return [
                _dot_last_dim(left_item, right_item)
                for left_item, right_item in zip(left, right)
            ]
        return [_dot_last_dim(left_item, right) for left_item in left]
    return left


def _project_last_dim(left: Any, projection: Any) -> Any:
    try:
        import torch

        if hasattr(left, "shape") or hasattr(projection, "shape"):
            if not hasattr(left, "shape"):
                left = torch.as_tensor(
                    left,
                    dtype=getattr(projection, "dtype", None),
                    device=getattr(projection, "device", None),
                )
            if not hasattr(projection, "shape"):
                projection = torch.as_tensor(
                    projection,
                    dtype=getattr(left, "dtype", None),
                    device=getattr(left, "device", None),
                )
            return left @ projection
    except Exception:
        pass
    try:
        import numpy as np

        if hasattr(left, "shape") or hasattr(projection, "shape"):
            return left @ projection
    except Exception:
        pass

    projection_shape = _shape_of(projection)
    if len(projection_shape) == 1:
        return _dot_last_dim(left, projection)
    if len(projection_shape) == 2:
        return _matmul_last_dim(left, projection)
    raise ValueError(
        "project_output_onto must have shape [d_model] or [d_model, num_outputs]."
    )


def _matmul_last_dim(left: Any, right: Any) -> Any:
    if _shape_of(left) == ():
        return left
    if _is_vector(left):
        return _matvec(left, right)
    if isinstance(left, list):
        return [_matmul_last_dim(item, right) for item in left]
    return left


def _matvec(vector: Any, matrix: Any) -> list[float]:
    matrix_rows = matrix.tolist() if hasattr(matrix, "tolist") else matrix
    vector_values = vector.tolist() if hasattr(vector, "tolist") else vector
    if not matrix_rows:
        return []
    return [
        sum(
            float(vector_values[row_index]) * float(row[col_index])
            for row_index, row in enumerate(matrix_rows)
        )
        for col_index in range(len(matrix_rows[0]))
    ]


def _is_vector(value: Any) -> bool:
    return isinstance(value, list) and (not value or not isinstance(value[0], list))


def _can_broadcast_shape(source: tuple[int, ...], target: tuple[int, ...]) -> bool:
    if len(source) > len(target):
        return False
    padded = (1,) * (len(target) - len(source)) + source
    return all(source_dim in (1, target_dim) for source_dim, target_dim in zip(padded, target))


def _broadcast_index(
    value: Any,
    source_shape: tuple[int, ...],
    target_shape: tuple[int, ...],
    axis: int,
    index: int,
) -> Any:
    padded_shape = (1,) * (len(target_shape) - len(source_shape)) + source_shape
    if axis < len(target_shape) - len(source_shape):
        return value
    source_axis = axis - (len(target_shape) - len(source_shape))
    return value[0] if padded_shape[axis] == 1 else value[index]


def _normalize_logit_tokens(model: Any, tokens: Any) -> Any:
    if isinstance(tokens, str):
        to_single_token = getattr(model, "to_single_token", None)
        if callable(to_single_token):
            return to_single_token(tokens)
    return tokens


def _get_final_layer_norm(model: Any) -> Any:
    candidates = (
        "ln_final",
        "final_layer_norm",
        "norm",
        "ln_f",
        "transformer.ln_f",
        "gpt_neox.final_layer_norm",
        "decoder.final_layer_norm",
        "model.ln_final",
        "model.final_layer_norm",
        "model.norm",
        "model.ln_f",
        "model.transformer.ln_f",
        "model.gpt_neox.final_layer_norm",
        "model.decoder.final_layer_norm",
        "model.model.norm",
        "model.model.final_layer_norm",
    )
    for name in candidates:
        value = _get_nested_attr(model, name)
        if value is not None:
            return value
    return None


def _get_nested_attr(owner: Any, dotted_name: str) -> Any:
    value = owner
    for part in dotted_name.split("."):
        if value is None:
            return None
        try:
            value = getattr(value, part)
        except Exception:
            return None
    return value


def _apply_final_layer_norm_to_stack(residual_stack: Any, ln_final: Any) -> Any:
    if ln_final is None or not callable(ln_final):
        return _MISSING
    shape = _shape_of(residual_stack)
    if not shape:
        return _MISSING
    try:
        import torch

        if hasattr(residual_stack, "shape"):
            stack = residual_stack
        else:
            stack = torch.as_tensor(residual_stack)
        had_pos_dim = len(_shape_of(stack)) == 4
        components = []
        for component_index in range(int(stack.shape[0])):
            component = stack[component_index]
            if component.ndim == 2:
                component = component.unsqueeze(1)
            normalized = ln_final(component)
            if not had_pos_dim:
                normalized = normalized.squeeze(1)
            components.append(normalized)
        return torch.stack(components, dim=0)
    except Exception:
        return _MISSING


def _uses_centered_layer_norm(model: Any) -> bool:
    normalization_type = _get_model_attr(model, "normalization_type")
    if normalization_type is not None:
        return str(normalization_type).lower() in {"ln", "lnpre", "layernorm", "layer_norm"}
    config = _get_model_attr(model, "config")
    model_type = str(getattr(config, "model_type", "")).lower() if config is not None else ""
    if model_type:
        return not any(name in model_type for name in ("llama", "mistral", "qwen", "gemma"))
    return False


def _get_config_int(model: Any, names: Sequence[str]) -> int | None:
    owners = [model, getattr(model, "cfg", None), getattr(model, "config", None)]
    wrapped = getattr(model, "model", None)
    if wrapped is not None:
        owners.extend([wrapped, getattr(wrapped, "cfg", None), getattr(wrapped, "config", None)])
    for owner in owners:
        if owner is None:
            continue
        for name in names:
            value = getattr(owner, name, None)
            if value is not None:
                return int(value)
    return None


def _get_model_attr(model: Any, name: str) -> Any:
    if model is None:
        return None
    owners = [model, getattr(model, "cfg", None), getattr(model, "config", None)]
    wrapped = getattr(model, "model", None)
    if wrapped is not None:
        owners.extend([wrapped, getattr(wrapped, "cfg", None), getattr(wrapped, "config", None)])
    for owner in owners:
        if owner is None:
            continue
        try:
            value = getattr(owner, name)
        except Exception:
            continue
        if value is not None:
            return value
    return None


def _get_layer_weight(model: Any, name: str, layer: int) -> Any:
    weights = _get_model_attr(model, name)
    if weights is None:
        return None
    shape = _shape_of(weights)
    if len(shape) >= 3:
        return _slice_dim(weights, layer, dim=0)
    if len(shape) >= 2:
        return weights
    return None


def _unique(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result


def make_cache_hook(
    cache: ActivationCache,
    name: str,
    *,
    detach: bool = True,
    clone: bool = False,
    device: Any = None,
    pos_slice: Any = None,
    remove_batch_dim: bool = False,
) -> HookFn:
    """Create a hook that stores its activation in an `ActivationCache`."""

    def cache_hook(*args: Any, **kwargs: Any) -> None:
        activation = extract_hook_output(args, kwargs)
        if activation is _MISSING:
            return None
        if remove_batch_dim:
            activation = _remove_singleton_batch(activation)
            cache.has_batch_dim = False
        if pos_slice is not None:
            activation = _slice_dim(activation, pos_slice, dim=_cache_pos_dim(name, activation))
        cache.store(name, activation, detach=detach, clone=clone, device=device)
        return None

    return cache_hook


def _cache_pos_dim(name: str, activation: Any) -> int:
    """Return TransformerLens' position dimension for a cached activation."""
    shape = _shape_of(activation)
    if not shape:
        return 0
    if name.endswith(("hook_q", "hook_k", "hook_v", "hook_z", "hook_result")):
        pos_dim = -3
    else:
        pos_dim = -2
    rank = len(shape)
    if rank < abs(pos_dim):
        return 0
    return pos_dim


@contextmanager
def temporary_hooks(
    model: ModelWrapper,
    hooks: Iterable[tuple[LayerRef, HookFn]],
) -> Iterator[list[Any]]:
    """Register hooks for one context and always remove them afterward."""
    handles: list[Any] = []
    try:
        for layer, hook_fn in hooks:
            handles.append(model.add_hook(layer, hook_fn))
        yield handles
    finally:
        for handle in reversed(handles):
            remove = getattr(handle, "remove", None)
            if callable(remove):
                remove()


def run_with_hooks(
    model: ModelWrapper,
    batch: Batch,
    hooks: Iterable[tuple[LayerRef, HookFn]],
    *,
    layers: Sequence[LayerRef] | None = None,
) -> tuple[Any, dict[str, Any]]:
    """Run a model with temporary hooks and remove them when the run finishes."""
    with temporary_hooks(model, hooks):
        return model.run_with_cache(batch, layers=layers)


def cache_activations(
    model: ModelWrapper,
    batch: Batch,
    layers: Sequence[LayerRef],
    *,
    names_filter: NamesFilter = None,
    detach: bool = True,
    clone: bool = False,
    device: Any = None,
) -> tuple[Any, ActivationCache]:
    """Run a model while caching selected layer activations through temporary hooks."""
    cache = ActivationCache()
    hooks = []
    for layer in layers:
        name = activation_name_for_layer(layer)
        if matches_names_filter(name, names_filter):
            hooks.append(
                (
                    layer,
                    make_cache_hook(cache, name, detach=detach, clone=clone, device=device),
                )
            )
    output, _ = run_with_hooks(model, batch, hooks)
    return output, cache

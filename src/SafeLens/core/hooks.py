"""Hook and activation-cache primitives inspired by TransformerLens."""

from __future__ import annotations

import re
from collections.abc import Callable, Iterable, Iterator, Mapping, MutableMapping, Sequence
from contextlib import contextmanager
from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Literal, Protocol, cast

from SafeLens.core.base import Batch, HookFn, LayerRef, ModelWrapper
from SafeLens.core.hook_call import call_user_hook

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
    "mlp_pre_linear": "pre_linear",
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
_PREFIXED_ATTN_BASE_ACTS = {"k", "v", "q", "z", "result", "pattern", "attn_scores"}
_PREFIXED_ATTN_LAYER_TYPES = {
    "cross_attn": "cross",
    "cross_attention": "cross",
    "encoder_decoder_attn": "cross",
    "decoder_attn": "decoder",
    "decoder_attention": "decoder",
}
_ENCODER_TOP_LEVEL_ACTS = {
    "resid_pre",
    "resid_mid",
    "resid_post",
    "attn_in",
    "attn_out",
    "q_input",
    "k_input",
    "v_input",
    "mlp_in",
    "mlp_out",
}
_DECODER_TOP_LEVEL_ACTS = {
    "resid_pre",
    "resid_mid",
    "resid_mid_cross",
    "resid_post",
    "attn_in",
    "attn_out",
    "q_input",
    "k_input",
    "v_input",
    "mlp_in",
    "mlp_out",
}
_CROSS_TOP_LEVEL_ACTS = {"cross_attn_in", "cross_attn_out"}
_MLP_ACTS = {"pre", "post", "mid", "pre_linear"}
_DECODER_MLP_ACTS = {"pre", "post", "pre_linear"}
_LAYER_NORM_ACTS = {"scale", "normalized"}
_TOP_LEVEL_ACT_NAMES = {
    "embed": "hook_embed",
    "hook_embed": "hook_embed",
    "pos_embed": "hook_pos_embed",
    "hook_pos_embed": "hook_pos_embed",
    "scale": "ln_final.hook_scale",
    "hook_scale": "ln_final.hook_scale",
    "normalized": "ln_final.hook_normalized",
    "hook_normalized": "ln_final.hook_normalized",
}


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
    user_hook: Callable[..., Any] | None = None
    is_cache: bool = False
    removed: bool = False

    @property
    def context_level(self) -> int | None:
        """TransformerLens-compatible alias for the hook context level."""
        return self.level

    @context_level.setter
    def context_level(self, value: int | None) -> None:
        self.level = value

    @property
    def hook(self) -> LensHandle:
        """TransformerLens-compatible removable-handle reference."""
        return self

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
        self.backward_scale: float = 1.0

    def __repr__(self) -> str:
        """Return a TransformerLens-style hook summary."""
        bits = [f"name={self.name!r}"] if self.name is not None else []
        if self.fwd_hooks:
            bits.append(f"{len(self.fwd_hooks)} fwd")
        if self.bwd_hooks:
            bits.append(f"{len(self.bwd_hooks)} bwd")
        return f"HookPoint({', '.join(bits)})" if bits else "HookPoint()"

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
        hook_fn: HookFn | None = None,
        dir: Literal["fwd", "bwd"] = "fwd",
        *,
        hook: HookFn | None = None,
    ) -> LensHandle:
        """Register a permanent hook."""
        resolved_hook = _resolve_hook_argument(hook_fn, hook=hook)
        return self.add_hook(resolved_hook, dir=dir, is_permanent=True)

    def add_hook(
        self,
        hook_fn: HookFn | None = None,
        dir: Literal["fwd", "bwd"] = "fwd",
        *,
        hook: HookFn | None = None,
        is_permanent: bool = False,
        level: int | None = None,
        prepend: bool = False,
        alias_names: Sequence[str] | None = None,
    ) -> LensHandle:
        """Register a hook and return a removable handle."""
        hook_fn = _resolve_hook_argument(hook_fn, hook=hook)
        user_hook = hook_fn
        if alias_names is not None:
            hook_fn = _alias_hook_fn(hook_fn, self, alias_names)
        hook_list = self._hook_list(dir)
        record: tuple[HookFn, LensHandle]

        def remove_record() -> None:
            if record in hook_list:
                hook_list.remove(record)

        handle = LensHandle(
            remove_record,
            is_permanent=is_permanent,
            level=level,
            user_hook=user_hook,
            is_cache=bool(getattr(user_hook, "_safelens_is_cache_hook", False)),
        )
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
        dir: HookDirection = "fwd",
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
                hook_grad = _scale_backward_gradient_for_hooks(output_grad, self.backward_scale)
                if self.hook_conversion is not None:
                    hook_grad = self.hook_conversion.convert(hook_grad)
                patched = _call_hookpoint_fn(hook_fn, hook_grad, self)
                if patched is not None:
                    if self.hook_conversion is not None:
                        patched = self.hook_conversion.revert(patched)
                    output_grad = _unwrap_scaled_gradient_value(patched)
            return output_grad

        try:
            register_hook(backward_hook)
        except RuntimeError:
            return activation
        return activation


def _resolve_hook_argument(
    hook_fn: HookFn | None = None,
    *,
    hook: HookFn | None = None,
) -> HookFn:
    if hook_fn is not None and hook is not None:
        raise TypeError("Pass only one of `hook_fn` or `hook`.")
    resolved_hook = hook_fn if hook_fn is not None else hook
    if not callable(resolved_hook):
        raise TypeError("hook must be callable.")
    return resolved_hook


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
    return str(layer)


def get_act_name(
    name: str,
    layer: int | str | None = None,
    layer_type: str | None = None,
) -> str:
    """Convert common TransformerLens activation shorthands into hook names."""
    if ("." in name or name.startswith("hook_")) and layer is None and layer_type is None:
        return name

    name = _strip_hook_prefix(name)
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
    name = _strip_hook_prefix(name)
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


def _canonicalize_cache_dict(cache_dict: dict[str, Any]) -> dict[str, Any]:
    """Normalize top-level activation aliases at cache construction boundaries."""
    normalized: dict[str, Any] = {}
    for key, value in cache_dict.items():
        normalized[_canonical_storage_key_for_string(key)] = value
    return normalized


class ActivationCache(MutableMapping[Any, Any]):
    """Dictionary-like activation cache with small tensor-friendly helpers."""

    def __init__(
        self,
        cache_dict: dict[str, Any] | None = None,
        model: Any = None,
        has_batch_dim: bool = True,
        canonicalize: bool = True,
    ) -> None:
        raw_cache = {} if cache_dict is None else cache_dict
        self._cache = _canonicalize_cache_dict(raw_cache) if canonicalize else raw_cache
        self.model = model
        self.has_batch_dim = has_batch_dim

    @property
    def cache_dict(self) -> dict[str, Any]:
        """TransformerLens-compatible view of the underlying activation mapping."""
        return self._cache

    @cache_dict.setter
    def cache_dict(self, value: dict[str, Any]) -> None:
        self._cache = _canonicalize_cache_dict(value)

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

    def __setitem__(self, key: ActivationKey, value: Any) -> None:
        self._cache[self.storage_key(key)] = value

    def __delitem__(self, key: ActivationKey) -> None:
        del self._cache[self.resolve_key(key)]

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

    def keys(self) -> Any:
        """Return cached activation names, matching TransformerLens' mapping API."""
        return self._cache.keys()

    def values(self) -> Any:
        """Return cached activation values, matching TransformerLens' mapping API."""
        return self._cache.values()

    def items(self) -> Any:
        """Return cached activation items, matching TransformerLens' mapping API."""
        return self._cache.items()

    def resolve_key(self, key: ActivationKey) -> str:
        """Resolve exact, SafeLens-style, or TransformerLens-style activation keys."""
        candidates = activation_name_candidates(
            key,
            n_layers=self._infer_n_layers(),
            decoder_n_layers=self._infer_stack_n_layers("decoder"),
        )
        for candidate in candidates:
            if candidate in self._cache:
                return candidate
        raise KeyError(f"Unknown activation key {key!r}. Tried {candidates!r}.")

    def storage_key(self, key: ActivationKey) -> str:
        """Return the existing or canonical storage name for an activation key."""
        try:
            return self.resolve_key(key)
        except KeyError:
            if isinstance(key, tuple) and key:
                tuple_key = list(key)
                if len(tuple_key) == 1:
                    top_level_name = _TOP_LEVEL_ACT_NAMES.get(str(tuple_key[0]))
                    if top_level_name is not None:
                        return top_level_name
                layer = tuple_key[1] if len(tuple_key) >= 2 else None
                raw_name = _strip_hook_prefix(str(tuple_key[0]))
                name = _ACT_NAME_ALIASES.get(raw_name, raw_name)
                if layer == -1:
                    stack = _activation_key_stack_name(name)
                    n_layers = self._infer_stack_n_layers(stack)
                    if n_layers > 0:
                        layer = n_layers - 1
                layer_type = (
                    str(tuple_key[2]) if len(tuple_key) >= 3 and tuple_key[2] is not None else None
                )
                if layer_type is not None:
                    layer_type = _LAYER_TYPE_ALIASES.get(layer_type, layer_type)
                if layer_type and layer is not None:
                    return f"{activation_name_for_layer(layer)}.{layer_type}.{name}"
                return safelens_act_name(name, layer)
            if isinstance(key, str):
                canonical_key = _canonical_storage_key_for_string(key)
                if canonical_key != key:
                    return canonical_key
            candidates = activation_name_candidates(
                key,
                n_layers=self._infer_n_layers(),
                decoder_n_layers=self._infer_stack_n_layers("decoder"),
            )
            if candidates:
                return candidates[0]
            return str(key)

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
        has_singleton_batch = any(_has_leading_dim(value, 1) for value in self._cache.values())
        for name, value in list(self._cache.items()):
            if _has_leading_dim(value, 1):
                updated_values[name] = _slice_dim(value, 0, dim=0)
                continue
            shape = _shape_of(value)
            if shape and not has_singleton_batch:
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
        normalized_slice = _normalize_slice_index(batch_slice)
        if not self.has_batch_dim:
            if normalized_slice == _FULL_SLICE:
                return ActivationCache(
                    dict(self._cache),
                    model=self.model,
                    has_batch_dim=False,
                )
            raise ValueError("Cannot slice batch dimension on a cache without batch dim.")
        has_batch_dim = not isinstance(normalized_slice, int)
        return ActivationCache(
            {
                name: _slice_dim(value, normalized_slice, dim=0)
                for name, value in self._cache.items()
            },
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
        *,
        stack: Literal["encoder", "decoder"] = "encoder",
    ) -> Any:
        """Return residual stream states up to a layer, useful for logit-lens workflows."""
        stack = _normalize_residual_stack_name(stack)
        target_layer = self._normalize_stack_layer(layer, stack=stack)
        values: list[Any] = []
        labels: list[str] = []
        n_layers = self._infer_stack_n_layers(stack)
        max_pre_layer = min(target_layer, n_layers - 1)

        for current_layer in range(max_pre_layer + 1):
            resid_pre_key = _residual_component_key("resid_pre", current_layer, stack=stack)
            resid_mid_key = _residual_component_key("resid_mid", current_layer, stack=stack)
            if resid_pre_key in self:
                values.append(_maybe_slice_pos(self[resid_pre_key], pos_slice))
                labels.append(f"{current_layer}_pre")
            if incl_mid and current_layer < target_layer and resid_mid_key in self:
                values.append(_maybe_slice_pos(self[resid_mid_key], pos_slice))
                labels.append(f"{current_layer}_mid")

        resid_mid_key = _residual_component_key("resid_mid", target_layer, stack=stack)
        if mlp_input and resid_mid_key in self:
            values.append(_maybe_slice_pos(self[resid_mid_key], pos_slice))
            labels.append(f"{target_layer}_mid")
        final_post_key = _residual_component_key("resid_post", n_layers - 1, stack=stack)
        if target_layer >= n_layers and n_layers > 0 and final_post_key in self:
            values.append(_maybe_slice_pos(self[final_post_key], pos_slice))
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
                stack=stack,
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
        *,
        stack: Literal["encoder", "decoder"] = "encoder",
    ) -> Any:
        """Decompose a residual stream into embedding, attention, and MLP components."""
        stack = _normalize_residual_stack_name(stack)
        target_layer = self._normalize_stack_layer(layer, stack=stack)
        values: list[Any] = []
        labels: list[str] = []
        include_attn = mode != "mlp"
        include_mlp = mode != "attn" and not _model_is_attn_only(self.model)

        for key, label in (("hook_embed", "embed"), ("hook_pos_embed", "pos_embed")):
            if incl_embeds and key in self:
                values.append(_maybe_slice_pos(self[key], pos_slice))
                labels.append(label)

        for current_layer in range(target_layer):
            attn_key = _residual_component_key("attn_out", current_layer, stack=stack)
            cross_attn_key = _residual_component_key("cross_attn_out", current_layer, stack=stack)
            mlp_key = _residual_component_key("mlp_out", current_layer, stack=stack)
            if include_attn and attn_key in self:
                values.append(_maybe_slice_pos(self[attn_key], pos_slice))
                labels.append(f"{current_layer}_attn_out")
            if include_attn and stack == "decoder" and cross_attn_key in self:
                values.append(_maybe_slice_pos(self[cross_attn_key], pos_slice))
                labels.append(f"{current_layer}_cross_attn_out")
            if include_mlp and mlp_key in self:
                values.append(_maybe_slice_pos(self[mlp_key], pos_slice))
                labels.append(f"{current_layer}_mlp_out")

        attn_key = _residual_component_key("attn_out", target_layer, stack=stack)
        cross_attn_key = _residual_component_key("cross_attn_out", target_layer, stack=stack)
        if mlp_input and include_attn and attn_key in self:
            values.append(_maybe_slice_pos(self[attn_key], pos_slice))
            labels.append(f"{target_layer}_attn_out")
        if mlp_input and include_attn and stack == "decoder" and cross_attn_key in self:
            values.append(_maybe_slice_pos(self[cross_attn_key], pos_slice))
            labels.append(f"{target_layer}_cross_attn_out")
        if not values:
            raise KeyError("No residual decomposition activations found in cache.")

        residual_stack = stack_values(values)
        if apply_ln:
            residual_stack = self.apply_ln_to_stack(
                residual_stack,
                layer=target_layer,
                mlp_input=mlp_input,
                pos_slice=pos_slice,
                has_batch_dim=self.has_batch_dim,
                stack=stack,
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
        if incl_remainder and component != "result":
            raise ValueError(
                "incl_remainder=True requires residual-space `result` head activations."
            )
        target_layer = self._normalize_layer(layer)
        if component == "result" and any(
            ("z", current_layer) in self and (component, current_layer) not in self
            for current_layer in range(target_layer)
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
            head_dim = _head_axis_after_pos_slice(activation, pos_slice, component=component)
            for head_index in range(_infer_head_count(activation, dim=head_dim)):
                values.append(_slice_dim(activation, head_index, dim=head_dim))
                labels.append(f"L{current_layer}H{head_index}")
        if incl_remainder:
            remainder = _residual_remainder_base(self, target_layer, pos_slice)
            if values:
                remainder = _subtract_values(remainder, _sum_values(values))
            values.append(remainder)
            labels.append("remainder")
        if not values:
            if target_layer == 0:
                head_stack = _empty_component_stack_like_cache(
                    self,
                    pos_slice=pos_slice,
                    has_batch_dim=self.has_batch_dim,
                )
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
        target_layer = self._normalize_layer(layer)
        n_layers = self._infer_n_layers()
        max_layer = min(target_layer, n_layers)
        values: list[Any] = []
        labels: list[str] = []

        for current_layer in range(max_layer):
            if ("result", current_layer) in self:
                result = _maybe_slice_pos(
                    self[("result", current_layer)],
                    pos_slice,
                    dim=_head_vector_pos_dim("result"),
                )
                values.append(result)
                labels.append(f"{current_layer}_result")
                continue
            if ("z", current_layer) not in self:
                continue
            w_o = _get_layer_weight(self.model, "W_O", current_layer)
            if w_o is None:
                raise ValueError(
                    "compute_head_results requires a cache with a model exposing W_O "
                    "when cached head result activations are missing."
                )
            from SafeLens.core.analysis import compute_head_results_from_z

            z_activation = _maybe_slice_pos(self[("z", current_layer)], pos_slice, dim=-3)
            result = compute_head_results_from_z(z_activation, w_o)
            if store and pos_slice is None:
                self[f"layer_{current_layer}.result"] = result
                self.cache_dict[f"blocks.{current_layer}.attn.hook_result"] = result
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
        if project_output_onto is not None:
            layer_w_out = _project_last_dim(layer_w_out, project_output_onto)
        return _multiply_last_dim_by_matrix(neuron_acts, layer_w_out)

    def _get_cached_ln_scale(
        self,
        layer: int | None,
        mlp_input: bool,
        pos_slice: Any = None,
        batch_slice: Any = None,
    ) -> Any:
        """Return cached layer-norm scale for a residual-stack target."""
        target_layer = self._normalize_layer(layer)
        n_layers = self._infer_n_layers()
        if target_layer == n_layers:
            key: ActivationKey = "ln_final.hook_scale"
        else:
            key = ("scale", target_layer, "ln2" if mlp_input else "ln1")
        try:
            scale = self[key]
        except KeyError as exc:
            resolved_key = key if isinstance(key, str) else get_act_name(*key)
            raise KeyError(
                f"Cached LN scale not found at {resolved_key!r}. apply_ln operations require "
                "this hook to be cached for the requested layer."
            ) from exc
        scale_has_batch_dim = self.has_batch_dim
        if batch_slice is not None and self.has_batch_dim:
            scale = _slice_dim(scale, batch_slice, dim=0)
            scale_has_batch_dim = not isinstance(batch_slice, int)
        if pos_slice is not None:
            pos_dim = _scale_pos_dim(scale, has_batch_dim=scale_has_batch_dim)
            scale = _slice_dim(scale, pos_slice, dim=pos_dim)
        return scale

    def _stack_neuron_results_apply_ln_projected(
        self,
        layer: int,
        pos_slice: Any,
        neuron_slice: Any,
        project_output_onto: Any,
    ) -> Any:
        """Stack LN-applied neuron projections without materializing d_mlp by d_model."""
        scale = self._get_cached_ln_scale(layer, mlp_input=False, pos_slice=pos_slice)
        apply_centering = _uses_centered_layer_norm(self.model)
        projection_sum = _sum_projection_input_dim(project_output_onto) if apply_centering else None
        values: list[Any] = []
        for current_layer in range(layer):
            if ("post", current_layer) not in self:
                continue
            neuron_acts = _maybe_slice_pos(self[("post", current_layer)], pos_slice)
            neuron_indices = _indices_from_slice(neuron_slice, _infer_last_dim(neuron_acts))
            neuron_acts = _select_indices_dim(neuron_acts, neuron_indices, dim=-1)
            w_out = _get_layer_weight(self.model, "W_out", current_layer)
            if w_out is None:
                raise ValueError("stack_neuron_results requires a model exposing W_out.")
            w_out = _select_indices_dim(w_out, neuron_indices, dim=0)
            linear_form = _project_last_dim(w_out, project_output_onto)
            if apply_centering:
                w_means = _mean_last_dim(w_out)
                linear_form = _subtract_values(
                    linear_form,
                    _multiply_by_last_vector(w_means, projection_sum),
                )
            scaled_acts = _divide_values(neuron_acts, scale)
            layer_values = _multiply_last_dim_by_matrix(scaled_acts, linear_form)
            neuron_dim = -1 if len(_shape_of(project_output_onto)) == 1 else -2
            for position in range(len(neuron_indices)):
                values.append(_slice_dim(layer_values, position, dim=neuron_dim))
        if values:
            return stack_values(values)
        return _empty_component_stack_like_cache(
            self,
            pos_slice=pos_slice,
            has_batch_dim=self.has_batch_dim,
            project_output_onto=project_output_onto,
        )

    def _can_fold_ln_neuron_projection(self, layer: int, pos_slice: Any) -> bool:
        try:
            scale = self._get_cached_ln_scale(layer, mlp_input=False, pos_slice=pos_slice)
        except KeyError:
            return False
        scale_shape = _shape_of(scale)
        return not scale_shape or scale_shape[-1] == 1

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
        require_output_weight: bool = False,
    ) -> Any:
        """Stack per-neuron MLP residual contributions when `W_out` is available."""
        target_layer = self._normalize_layer(layer)
        values: list[Any] = []
        labels: list[str] = []
        can_project_before_stack = (
            project_output_onto is not None and not apply_ln and not incl_remainder
        )
        can_fold_ln_projection = (
            component == "post"
            and project_output_onto is not None
            and apply_ln
            and not incl_remainder
            and self._can_fold_ln_neuron_projection(target_layer, pos_slice)
        )
        results_are_projected = False
        for current_layer in range(target_layer):
            if (component, current_layer) not in self:
                continue
            activation = _maybe_slice_pos(self[(component, current_layer)], pos_slice)
            neuron_indices = _indices_from_slice(neuron_slice, _infer_last_dim(activation))
            if can_fold_ln_projection:
                labels.extend(f"L{current_layer}N{neuron_index}" for neuron_index in neuron_indices)
                continue
            try:
                layer_results = self.get_neuron_results(
                    current_layer,
                    neuron_slice=neuron_indices,
                    pos_slice=pos_slice,
                    project_output_onto=project_output_onto if can_project_before_stack else None,
                    component=component,
                )
                results_are_projected = can_project_before_stack
                neuron_dim = (
                    -1 if results_are_projected and len(_shape_of(project_output_onto)) == 1 else -2
                )
            except ValueError:
                if project_output_onto is not None or require_output_weight or incl_remainder:
                    raise
                layer_results = _select_indices_dim(activation, neuron_indices, dim=-1)
                neuron_dim = -1
                results_are_projected = False
            for position, neuron_index in enumerate(neuron_indices):
                neuron_value = _slice_dim(layer_results, position, dim=neuron_dim)
                values.append(neuron_value)
                labels.append(f"L{current_layer}N{neuron_index}")
        if incl_remainder:
            remainder = _residual_remainder_base(self, target_layer, pos_slice)
            if values:
                remainder = _subtract_values(remainder, _sum_values(values))
            values.append(remainder)
            labels.append("remainder")
        if not values and not (can_fold_ln_projection and labels):
            if target_layer == 0:
                neuron_stack = _empty_component_stack_like_cache(
                    self,
                    pos_slice=pos_slice,
                    has_batch_dim=self.has_batch_dim,
                    project_output_onto=project_output_onto,
                )
                if apply_ln:
                    neuron_stack = self.apply_ln_to_stack(
                        neuron_stack,
                        layer=target_layer,
                        pos_slice=pos_slice,
                        has_batch_dim=self.has_batch_dim,
                    )
                if return_labels:
                    return neuron_stack, labels
                return neuron_stack
            raise KeyError(f"No {component!r} neuron activations found in cache.")
        if can_fold_ln_projection:
            neuron_stack = self._stack_neuron_results_apply_ln_projected(
                target_layer,
                pos_slice,
                neuron_slice,
                project_output_onto,
            )
            results_are_projected = True
        else:
            neuron_stack = stack_values(values)
        if apply_ln and not can_fold_ln_projection:
            neuron_stack = self.apply_ln_to_stack(
                neuron_stack,
                layer=target_layer,
                pos_slice=pos_slice,
                has_batch_dim=self.has_batch_dim,
            )
        if project_output_onto is not None and not results_are_projected:
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
        *,
        stack: Literal["encoder", "decoder"] = "encoder",
    ) -> Any:
        """Return a best-effort decomposition into heads, MLP neurons, embeds, and bias."""
        stack = _normalize_residual_stack_name(stack)
        target_layer = self._normalize_stack_layer(layer, stack=stack)
        stacks: list[Any] = []
        labels: list[str] = []
        expanded_neurons = False
        ln_folded = apply_ln and project_output_onto is not None
        bias_reference: Any = None

        def remember_bias_reference(component_stack: Any) -> None:
            nonlocal bias_reference
            if bias_reference is not None:
                return
            component_rows = _unstack_first_dim(component_stack)
            if component_rows:
                bias_reference = component_rows[0]

        def maybe_ln_then_project(component_stack: Any) -> Any:
            if ln_folded:
                component_stack = self.apply_ln_to_stack(
                    component_stack,
                    layer=target_layer,
                    mlp_input=mlp_input,
                    pos_slice=pos_slice,
                    has_batch_dim=self.has_batch_dim,
                    stack=stack,
                )
                return _project_last_dim(component_stack, project_output_onto)
            if project_output_onto is not None:
                return _project_last_dim(component_stack, project_output_onto)
            return component_stack

        def add_stack(component_stack: Any, component_labels: list[str]) -> None:
            stacks.extend(_unstack_first_dim(component_stack))
            labels.extend(component_labels)

        try:
            if stack == "decoder":
                head_stack, head_labels = _decoder_head_result_stack(
                    self,
                    target_layer + (1 if mlp_input else 0),
                    pos_slice=pos_slice,
                )
            else:
                head_stack, head_labels = self.stack_head_results(
                    target_layer + (1 if mlp_input else 0),
                    pos_slice=pos_slice,
                    return_labels=True,
                )
            remember_bias_reference(head_stack)
            head_stack = maybe_ln_then_project(head_stack)
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
                    stack=stack,
                )
                remember_bias_reference(attn_stack)
                attn_stack = maybe_ln_then_project(attn_stack)
                add_stack(attn_stack, attn_labels)
            except KeyError:
                pass

        if stack == "decoder" and not _model_is_attn_only(self.model):
            try:
                mlp_stack, mlp_labels = self.decompose_resid(
                    target_layer,
                    mode="mlp",
                    incl_embeds=False,
                    pos_slice=pos_slice,
                    return_labels=True,
                    stack=stack,
                )
                remember_bias_reference(mlp_stack)
                mlp_stack = maybe_ln_then_project(mlp_stack)
                add_stack(mlp_stack, mlp_labels)
            except KeyError:
                pass
        elif expand_neurons and not _model_is_attn_only(self.model):
            try:
                neuron_stack, neuron_labels = self.stack_neuron_results(
                    target_layer,
                    pos_slice=pos_slice,
                    return_labels=True,
                    require_output_weight=True,
                    apply_ln=ln_folded,
                    project_output_onto=project_output_onto,
                )
                if project_output_onto is None and not apply_ln:
                    remember_bias_reference(neuron_stack)
                add_stack(neuron_stack, neuron_labels)
                expanded_neurons = True
            except (KeyError, ValueError):
                try:
                    mlp_stack, mlp_labels = self.decompose_resid(
                        target_layer,
                        mode="mlp",
                        incl_embeds=False,
                        pos_slice=pos_slice,
                        return_labels=True,
                        stack=stack,
                    )
                    remember_bias_reference(mlp_stack)
                    mlp_stack = maybe_ln_then_project(mlp_stack)
                    add_stack(mlp_stack, mlp_labels)
                except KeyError:
                    pass
        elif not _model_is_attn_only(self.model):
            try:
                mlp_stack, mlp_labels = self.decompose_resid(
                    target_layer,
                    mode="mlp",
                    incl_embeds=False,
                    pos_slice=pos_slice,
                    return_labels=True,
                    stack=stack,
                )
                remember_bias_reference(mlp_stack)
                mlp_stack = maybe_ln_then_project(mlp_stack)
                add_stack(mlp_stack, mlp_labels)
            except KeyError:
                pass

        for key, label in (("hook_embed", "embed"), ("hook_pos_embed", "pos_embed")):
            if key in self:
                embed_stack = stack_values([_maybe_slice_pos(self[key], pos_slice)])
                remember_bias_reference(embed_stack)
                embed_stack = maybe_ln_then_project(embed_stack)
                stacks.extend(_unstack_first_dim(embed_stack))
                labels.append(label)

        accumulated_bias = _get_model_attr(self.model, "accumulated_bias")
        if callable(accumulated_bias):
            try:
                bias = accumulated_bias(
                    target_layer,
                    mlp_input,
                    include_mlp_biases=expanded_neurons,
                )
            except TypeError:
                try:
                    bias = accumulated_bias(target_layer, mlp_input)
                except TypeError:
                    bias = accumulated_bias(target_layer)
            if ln_folded:
                bias = _expand_bias_like_for_folded_projection(
                    bias,
                    bias_reference,
                    stacks[0] if stacks else None,
                    project_output_onto,
                )
                bias_stack = stack_values([bias])
                bias_stack = self.apply_ln_to_stack(
                    bias_stack,
                    layer=target_layer,
                    mlp_input=mlp_input,
                    pos_slice=pos_slice,
                    has_batch_dim=self.has_batch_dim,
                    stack=stack,
                )
                bias_stack = _project_last_dim(bias_stack, project_output_onto)
                stacks.extend(_unstack_first_dim(bias_stack))
            else:
                if project_output_onto is not None:
                    bias = _project_last_dim(bias, project_output_onto)
                bias = _expand_bias_like(bias, stacks[0] if stacks else None)
                stacks.append(bias)
            labels.append("bias")

        if not stacks:
            raise KeyError("No activations found for a full residual decomposition.")
        full_stack = stack_values(stacks)
        if apply_ln and not ln_folded:
            full_stack = self.apply_ln_to_stack(
                full_stack,
                layer=target_layer,
                mlp_input=mlp_input,
                pos_slice=pos_slice,
                has_batch_dim=self.has_batch_dim,
                stack=stack,
            )
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
        stack: Literal["encoder", "decoder"] = "encoder",
    ) -> Any:
        """Apply cached layer-norm scale to a residual stack when scale is available."""
        stack = _normalize_residual_stack_name(stack)
        resolved_has_batch_dim = self.has_batch_dim if has_batch_dim is None else has_batch_dim
        target_layer = self._normalize_stack_layer(layer, stack=stack)
        n_layers = self._infer_stack_n_layers(stack)
        if _model_explicitly_has_no_layer_norm(self.model):
            return residual_stack
        requires_cached_scale = _model_explicitly_uses_layer_norm(self.model)
        if batch_slice is not None and resolved_has_batch_dim:
            residual_stack = _slice_dim(residual_stack, batch_slice, dim=1)
        if recompute_ln and scale_key is None and target_layer == n_layers:
            ln_final = _get_final_layer_norm(self.model, stack=stack)
            recomputed = _apply_final_layer_norm_to_stack(residual_stack, ln_final)
            if recomputed is not _MISSING:
                return recomputed

        resolved_scale_key = scale_key
        candidates: list[ActivationKey] = []
        if resolved_scale_key is None:
            if target_layer == n_layers:
                candidates = ["ln_final.hook_scale"]
            else:
                requested_layer_norm = _residual_stack_ln_name(stack, mlp_input)
                fallback_layer_norm = _residual_stack_fallback_ln_name(stack, mlp_input)
                candidates = _layer_norm_scale_candidates(target_layer, requested_layer_norm)
                if fallback_layer_norm is not None and not requires_cached_scale:
                    candidates.extend(
                        _layer_norm_scale_candidates(target_layer, fallback_layer_norm)
                    )
            resolved_scale_key = next(
                (candidate for candidate in candidates if candidate in self),
                None,
            )
        if resolved_scale_key is None:
            if requires_cached_scale:
                expected_key = candidates[0] if scale_key is None else scale_key
                expected_name = (
                    get_act_name(*expected_key)
                    if isinstance(expected_key, tuple)
                    else str(expected_key)
                )
                raise KeyError(
                    f"Cached LN scale not found at {expected_name!r}. apply_ln operations "
                    "require this hook to be cached for the requested layer."
                )
            return residual_stack
        scale = self[resolved_scale_key]
        if batch_slice is not None and resolved_has_batch_dim:
            scale = _slice_dim(scale, batch_slice, dim=0)
        if pos_slice is not None:
            pos_dim = _scale_pos_dim_for_residual_stack(
                scale,
                residual_stack,
                has_batch_dim=resolved_has_batch_dim,
            )
            scale = _slice_dim(scale, pos_slice, dim=pos_dim)
        if _uses_centered_layer_norm(self.model):
            residual_stack = _subtract_last_dim_mean(residual_stack)
        return _divide_values(residual_stack, scale)

    def logit_attrs(
        self,
        residual_stack: Any,
        tokens: Any,
        incorrect_tokens: Any = None,
        pos_slice: Any = None,
        batch_slice: Any = None,
        has_batch_dim: bool | None = None,
        *,
        directions: Any = None,
        apply_ln: bool = True,
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
        batch_dim = _direction_batch_dim(
            directions,
            residual_stack,
            has_batch_dim=resolved_has_batch_dim,
            prefer_pos_axis=pos_slice is not None,
        )
        residual_batch_dim = _residual_stack_batch_dim(
            residual_stack,
            directions,
            pos_slice=pos_slice,
        )
        if batch_slice is not None and batch_dim is not None:
            directions = _slice_dim(directions, batch_slice, dim=batch_dim)
            direction_has_batch_dim = not isinstance(batch_slice, int)
        else:
            direction_has_batch_dim = resolved_has_batch_dim
        pos_dim = _direction_pos_dim(
            directions,
            residual_stack,
            has_batch_dim=direction_has_batch_dim,
            prefer_pos_axis=pos_slice is not None,
        )
        if pos_slice is not None and pos_dim is not None:
            directions = _slice_dim(directions, pos_slice, dim=pos_dim)
        if apply_ln:
            residual_stack = _slice_residual_stack_for_logit_attrs(
                residual_stack,
                pos_slice,
                batch_slice=batch_slice,
                has_batch_dim=resolved_has_batch_dim,
                residual_batch_dim=residual_batch_dim,
                reference=directions,
            )
            residual_stack = _apply_cached_ln_scale_to_sliced_stack(
                self,
                residual_stack,
                layer=-1,
                pos_slice=pos_slice,
                batch_slice=batch_slice,
            )
        elif batch_slice is not None and resolved_has_batch_dim:
            residual_stack = _slice_dim(
                residual_stack,
                batch_slice,
                dim=residual_batch_dim,
            )
        return _dot_last_dim(residual_stack, directions)

    def residual_stack_to_logits(
        self,
        residual_stack: Any,
        *,
        apply_ln: bool = True,
        pos_slice: Any = None,
        batch_slice: Any = None,
        has_batch_dim: bool | None = None,
        use_unembed_bias: bool = True,
        stack: Literal["encoder", "decoder"] = "encoder",
    ) -> Any:
        """Project residual components through the model unembedding matrix."""
        stack = _normalize_residual_stack_name(stack)
        if self.model is None:
            raise ValueError("residual_stack_to_logits requires a cache with an attached model.")
        unembed = _get_model_attr(self.model, "W_U")
        if unembed is None:
            raise ValueError("residual_stack_to_logits requires a model exposing W_U.")
        unembed_bias = _get_model_attr(self.model, "b_U") if use_unembed_bias else None
        resolved_has_batch_dim = self.has_batch_dim if has_batch_dim is None else has_batch_dim
        residual_batch_dim = _residual_stack_batch_dim(residual_stack, None, pos_slice=pos_slice)
        if apply_ln:
            residual_stack = _maybe_slice_residual_stack_pos(
                residual_stack,
                pos_slice,
                has_batch_dim=resolved_has_batch_dim,
            )
            residual_stack = self.apply_ln_to_stack(
                residual_stack,
                layer=-1,
                pos_slice=pos_slice,
                batch_slice=batch_slice,
                has_batch_dim=resolved_has_batch_dim,
                stack=stack,
            )
        else:
            if batch_slice is not None and resolved_has_batch_dim:
                residual_stack = _slice_dim(residual_stack, batch_slice, dim=residual_batch_dim)
            if pos_slice is not None:
                residual_stack = _slice_dim(
                    residual_stack,
                    pos_slice,
                    dim=_residual_stack_pos_dim_after_optional_batch_slice(
                        residual_stack,
                        has_batch_dim=resolved_has_batch_dim,
                        batch_slice=batch_slice,
                    ),
                )
        from SafeLens.core.analysis import residual_stack_to_logits

        return residual_stack_to_logits(residual_stack, unembed, unembed_bias)

    def accumulated_resid_to_logits(
        self,
        layer: int | None = None,
        incl_mid: bool = False,
        *,
        pos_slice: Any = None,
        return_labels: bool = False,
        use_unembed_bias: bool = True,
        stack: Literal["encoder", "decoder"] = "encoder",
    ) -> Any:
        """Run a logit lens over accumulated residual stream states."""
        stack = _normalize_residual_stack_name(stack)
        residual_stack, labels = self.accumulated_resid(
            layer=layer,
            incl_mid=incl_mid,
            apply_ln=True,
            pos_slice=pos_slice,
            return_labels=True,
            stack=stack,
        )
        logits = self.residual_stack_to_logits(
            residual_stack,
            apply_ln=False,
            use_unembed_bias=use_unembed_bias,
        )
        if return_labels:
            return logits, labels
        return logits

    def decompose_resid_to_logits(
        self,
        layer: int | None = None,
        mlp_input: bool = False,
        mode: Literal["all", "mlp", "attn"] = "all",
        *,
        pos_slice: Any = None,
        incl_embeds: bool = True,
        return_labels: bool = False,
        use_unembed_bias: bool = False,
        stack: Literal["encoder", "decoder"] = "encoder",
    ) -> Any:
        """Project residual-decomposition components through the unembedding."""
        stack = _normalize_residual_stack_name(stack)
        residual_stack, labels = self.decompose_resid(
            layer=layer,
            mlp_input=mlp_input,
            mode=mode,
            apply_ln=True,
            pos_slice=pos_slice,
            incl_embeds=incl_embeds,
            return_labels=True,
            stack=stack,
        )
        logits = self.residual_stack_to_logits(
            residual_stack,
            apply_ln=False,
            use_unembed_bias=use_unembed_bias,
        )
        if return_labels:
            return logits, labels
        return logits

    def _infer_n_layers(self) -> int:
        n_layers = _get_config_int(self.model, ("n_layers", "num_hidden_layers", "num_layers"))
        if n_layers is not None:
            return n_layers
        layers = _layer_indices_from_cache_keys(
            self._cache,
            patterns=(r"(?:blocks|encoder|decoder)\.(\d+)\.", r"layer_(\d+)\."),
        )
        if layers:
            return max(layers) + 1
        return 0

    def _infer_stack_n_layers(self, stack: Literal["encoder", "decoder"]) -> int:
        if stack == "encoder":
            return self._infer_n_layers()
        n_layers = _get_config_int(
            self.model,
            ("n_decoder_layers", "num_decoder_layers", "decoder_layers"),
        )
        if n_layers is not None:
            return n_layers
        layers = _layer_indices_from_cache_keys(
            self._cache,
            patterns=(
                r"decoder\.(\d+)\.",
                r"layer_(\d+)\.(?:decoder_|cross_)",
            ),
        )
        if layers:
            return max(layers) + 1
        return self._infer_n_layers()

    def _normalize_layer(self, layer: int | None) -> int:
        n_layers = self._infer_n_layers()
        if layer is None or layer == -1:
            return n_layers
        if layer < 0:
            return n_layers + layer
        return layer

    def _normalize_stack_layer(
        self,
        layer: int | None,
        *,
        stack: Literal["encoder", "decoder"],
    ) -> int:
        n_layers = self._infer_stack_n_layers(stack)
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
    if len(args) == 2 and _looks_like_hook_context(args[1]):
        return args[0]
    if "output" in kwargs:
        return kwargs["output"]
    if "activation" in kwargs:
        return kwargs["activation"]
    return _MISSING


def _looks_like_hook_context(value: Any) -> bool:
    """Return whether a two-arg hook call looks like `(activation, hook)`."""
    return value is None or isinstance(value, HookPoint) or hasattr(value, "name")


def has_hook_output(args: tuple[Any, ...], kwargs: dict[str, Any]) -> bool:
    """Return whether a hook call contains an activation output."""
    return extract_hook_output(args, kwargs) is not _MISSING


def activation_name_candidates(
    key: ActivationKey,
    *,
    n_layers: int = 0,
    decoder_n_layers: int | None = None,
) -> list[str]:
    """Return possible cache names for an activation key."""
    if isinstance(key, str):
        candidates = [key]
        top_level_name = _TOP_LEVEL_ACT_NAMES.get(key)
        if top_level_name is not None:
            candidates.append(top_level_name)
        candidates.extend(_safelens_names_from_transformer_lens_name(key))
        candidates.extend(_transformer_lens_names_from_safelens_name(key))
        tl_name = get_act_name(key)
        candidates.append(tl_name)
        candidates.extend(_safelens_names_from_transformer_lens_name(tl_name))
        if "." not in key:
            candidates.append(safelens_act_name(key))
        return _unique(candidates)

    if not key:
        return []

    raw_name = str(key[0])
    name = _strip_hook_prefix(raw_name)
    if len(key) == 1:
        top_level_name = _TOP_LEVEL_ACT_NAMES.get(raw_name) or _TOP_LEVEL_ACT_NAMES.get(name)
        if top_level_name is not None:
            return _unique([raw_name, name, top_level_name])

    original_layer = key[1] if len(key) >= 2 else None
    layer = original_layer
    layer_type = str(key[2]) if len(key) >= 3 and key[2] is not None else None
    aliased_name = _ACT_NAME_ALIASES.get(name, name)
    aliased_layer_type = (
        _LAYER_TYPE_ALIASES.get(layer_type, layer_type) if layer_type is not None else None
    )
    if layer == -1:
        stack_n_layers = (
            decoder_n_layers if _activation_key_stack_name(aliased_name) == "decoder" else n_layers
        )
        if stack_n_layers:
            layer = stack_n_layers - 1

    normalized_key = (name, layer, *key[2:])
    candidates = [".".join(str(item) for item in normalized_key if item is not None)]
    if raw_name != name or original_layer != layer:
        candidates.append(".".join(str(item) for item in key if item is not None))
    candidates.append(get_act_name(aliased_name, layer, layer_type))
    if layer is not None:
        candidates.append(safelens_act_name(aliased_name, layer))
        prefixed_attention = _prefixed_attention_parts(aliased_name)
        if prefixed_attention is not None:
            prefix, base_component = prefixed_attention
            tl_layer_type = "attn" if prefix == "decoder" else "cross_attn"
            compat_layer_type = "decoder_attn" if prefix == "decoder" else "cross_attn"
            candidates.extend(
                [
                    f"decoder.{layer}.{tl_layer_type}.hook_{base_component}",
                    f"blocks.{layer}.{compat_layer_type}.hook_{base_component}",
                    f"{activation_name_for_layer(layer)}.{compat_layer_type}.{base_component}",
                ]
            )
        decoder_top_level = _decoder_top_level_base(aliased_name)
        if decoder_top_level is not None:
            candidates.extend(
                [
                    f"decoder.{layer}.hook_{decoder_top_level}",
                    f"blocks.{layer}.hook_{aliased_name}",
                ]
            )
        elif aliased_name in _CROSS_TOP_LEVEL_ACTS:
            candidates.extend(
                [
                    f"decoder.{layer}.hook_{aliased_name}",
                    f"blocks.{layer}.hook_{aliased_name}",
                ]
            )
        decoder_mlp_base = _decoder_mlp_base(aliased_name)
        if decoder_mlp_base is not None:
            candidates.extend(
                [
                    f"decoder.{layer}.mlp.hook_{decoder_mlp_base}",
                    f"blocks.{layer}.decoder_mlp.hook_{decoder_mlp_base}",
                    f"{activation_name_for_layer(layer)}.decoder_mlp.{decoder_mlp_base}",
                ]
            )
        decoder_ln = _decoder_ln_parts(aliased_name)
        if decoder_ln is not None:
            ln_layer_type, ln_component = decoder_ln
            candidates.extend(
                [
                    f"decoder.{layer}.{ln_layer_type}.hook_{ln_component}",
                    f"blocks.{layer}.{ln_layer_type}.hook_{ln_component}",
                    f"{activation_name_for_layer(layer)}.{ln_layer_type}.{ln_component}",
                ]
            )
        if layer_type is None:
            if aliased_name in _ENCODER_TOP_LEVEL_ACTS:
                candidates.extend(
                    [
                        f"encoder.{layer}.hook_{aliased_name}",
                        f"blocks.{layer}.hook_{aliased_name}",
                    ]
                )
            elif aliased_name in _ATTN_ACTS:
                candidates.extend(
                    [
                        f"encoder.{layer}.attn.hook_{aliased_name}",
                        f"{activation_name_for_layer(layer)}.attn.{aliased_name}",
                        f"blocks.{layer}.attn.hook_{aliased_name}",
                    ]
                )
            elif aliased_name in _MLP_ACTS:
                candidates.extend(
                    [
                        f"encoder.{layer}.mlp.hook_{aliased_name}",
                        f"{activation_name_for_layer(layer)}.mlp.{aliased_name}",
                        f"blocks.{layer}.mlp.hook_{aliased_name}",
                    ]
                )
        if aliased_layer_type:
            stack_candidates = []
            if aliased_layer_type in {"attn", "mlp", "ln1", "ln2"}:
                stack_candidates.append(f"encoder.{layer}.{aliased_layer_type}.hook_{aliased_name}")
            candidates.extend(
                [
                    *stack_candidates,
                    f"{activation_name_for_layer(layer)}.{aliased_layer_type}.{aliased_name}",
                    f"blocks.{layer}.{aliased_layer_type}.hook_{aliased_name}",
                ]
            )
    return _unique(candidates)


def _safelens_names_from_transformer_lens_name(name: str) -> list[str]:
    match = re.fullmatch(
        r"(blocks|encoder|decoder)\.(\d+)\.(?:([a-zA-Z0-9_]+)\.)?hook_([a-zA-Z0-9_]+)",
        name,
    )
    if match is None:
        return []
    stack = match.group(1)
    layer = int(match.group(2))
    layer_type = match.group(3)
    component = _ACT_NAME_ALIASES.get(match.group(4), match.group(4))
    prefixed_component = _prefixed_component_from_stack(
        component,
        layer_type=layer_type,
        stack=stack,
    )
    candidates = [safelens_act_name(prefixed_component or component, layer)]
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
    prefixed_attention = _prefixed_attention_parts(component)
    if prefixed_attention is not None:
        prefix, base_component = prefixed_attention
        tl_layer_type = "attn" if prefix == "decoder" else "cross_attn"
        compat_layer_type = "decoder_attn" if prefix == "decoder" else "cross_attn"
        return [
            f"decoder.{layer}.{tl_layer_type}.hook_{base_component}",
            f"blocks.{layer}.{compat_layer_type}.hook_{base_component}",
        ]
    decoder_top_level = _decoder_top_level_base(component)
    if decoder_top_level is not None:
        return [f"decoder.{layer}.hook_{decoder_top_level}", f"blocks.{layer}.hook_{component}"]
    if component in _CROSS_TOP_LEVEL_ACTS:
        return [f"decoder.{layer}.hook_{component}", f"blocks.{layer}.hook_{component}"]
    decoder_mlp_base = _decoder_mlp_base(component)
    if decoder_mlp_base is not None:
        return [
            f"decoder.{layer}.mlp.hook_{decoder_mlp_base}",
            f"blocks.{layer}.decoder_mlp.hook_{decoder_mlp_base}",
        ]
    decoder_ln = _decoder_ln_parts(component)
    if decoder_ln is not None:
        ln_layer_type, ln_component = decoder_ln
        return [
            f"decoder.{layer}.{ln_layer_type}.hook_{ln_component}",
            f"blocks.{layer}.{ln_layer_type}.hook_{ln_component}",
        ]
    if component in _ATTN_ACTS:
        return [
            f"encoder.{layer}.attn.hook_{component}",
            get_act_name(component, layer, layer_type),
        ]
    if component in _MLP_ACTS:
        return [f"encoder.{layer}.mlp.hook_{component}", get_act_name(component, layer, layer_type)]
    if component in _ENCODER_TOP_LEVEL_ACTS:
        return [f"encoder.{layer}.hook_{component}", get_act_name(component, layer, layer_type)]
    return [get_act_name(component, layer, layer_type)]


def _prefixed_attention_parts(component: str) -> tuple[str, str] | None:
    for prefix in ("decoder", "cross"):
        prefix_text = f"{prefix}_"
        if component.startswith(prefix_text):
            base_component = component.removeprefix(prefix_text)
            if base_component in _PREFIXED_ATTN_BASE_ACTS:
                return prefix, base_component
    return None


def _decoder_mlp_base(component: str) -> str | None:
    if not component.startswith("decoder_"):
        return None
    base = component.removeprefix("decoder_")
    if base in _DECODER_MLP_ACTS:
        return base
    return None


def _decoder_ln_parts(component: str) -> tuple[str, str] | None:
    match = re.fullmatch(r"decoder_(ln[123])_(scale|normalized)", component)
    if match is None:
        return None
    return match.group(1), match.group(2)


def _prefixed_component_from_stack(
    component: str,
    *,
    layer_type: str | None,
    stack: str,
) -> str | None:
    prefix = _PREFIXED_ATTN_LAYER_TYPES.get(layer_type or "")
    if prefix is not None:
        if component == "attn":
            component = "pattern"
        if component == "scores":
            component = "attn_scores"
        if component == "out":
            return f"{prefix}_attn_out"
        if component in _PREFIXED_ATTN_BASE_ACTS:
            return f"{prefix}_{component}"
    if stack == "decoder" and layer_type == "attn":
        if component == "attn":
            component = "pattern"
        if component == "scores":
            component = "attn_scores"
        if component == "out":
            return "decoder_attn_out"
        if component in _PREFIXED_ATTN_BASE_ACTS:
            return f"decoder_{component}"
    if stack == "decoder" and layer_type == "mlp" and component in _DECODER_MLP_ACTS:
        return f"decoder_{component}"
    if stack == "decoder" and layer_type in {"ln1", "ln2", "ln3"}:
        if component in _LAYER_NORM_ACTS:
            return f"decoder_{layer_type}_{component}"
    if stack == "decoder" and layer_type is None:
        if component in _DECODER_TOP_LEVEL_ACTS:
            return f"decoder_{component}"
        if component in _CROSS_TOP_LEVEL_ACTS:
            return component
    if stack == "encoder" and layer_type == "attn":
        if component == "attn":
            return "pattern"
        if component == "scores":
            return "attn_scores"
        if component == "out":
            return "attn_out"
        if component in _PREFIXED_ATTN_BASE_ACTS:
            return component
    if stack == "encoder" and layer_type == "mlp":
        if component == "out":
            return "mlp_out"
        if component in _MLP_ACTS:
            return component
    if stack == "encoder" and layer_type in {"ln1", "ln2"}:
        if component in _LAYER_NORM_ACTS:
            return f"{layer_type}_{component}"
    if stack == "encoder" and layer_type is None:
        if component in _ENCODER_TOP_LEVEL_ACTS:
            return component
    return None


def _decoder_top_level_base(component: str) -> str | None:
    if not component.startswith("decoder_"):
        return None
    base = component.removeprefix("decoder_")
    if base in _DECODER_TOP_LEVEL_ACTS:
        return base
    return None


def _strip_hook_prefix(name: str) -> str:
    if name.startswith("hook_"):
        return name.removeprefix("hook_")
    return name


def _canonical_storage_key_for_string(key: str) -> str:
    top_level_name = _TOP_LEVEL_ACT_NAMES.get(key)
    if top_level_name is not None:
        return top_level_name
    if "." in key or key.startswith("hook_"):
        return key
    match = re.fullmatch(r"([a-z_]+)(\d+)([a-z]?.*)", key)
    if match is None:
        return key
    raw_name, layer_text, layer_type = match.groups()
    layer = int(layer_text)
    name = _ACT_NAME_ALIASES.get(_strip_hook_prefix(raw_name), _strip_hook_prefix(raw_name))
    if not _is_known_activation_component(name):
        return key
    layer_type = _LAYER_TYPE_ALIASES.get(layer_type, layer_type) if layer_type else None
    if layer_type:
        return f"{activation_name_for_layer(layer)}.{layer_type}.{name}"
    return safelens_act_name(name, layer)


def _is_known_activation_component(name: str) -> bool:
    return name in (
        _ATTN_ACTS
        | _MLP_ACTS
        | _LAYER_NORM_ACTS
        | _ENCODER_TOP_LEVEL_ACTS
        | _DECODER_TOP_LEVEL_ACTS
        | _CROSS_TOP_LEVEL_ACTS
    )


def _cache_key_matches_filter(name: str, names_filter: NamesFilter) -> bool:
    if names_filter is None or callable(names_filter):
        return matches_names_filter(name, names_filter)
    if isinstance(names_filter, str):
        return _activation_names_equivalent(name, names_filter)
    return any(_activation_names_equivalent(name, candidate) for candidate in names_filter)


def _activation_names_equivalent(left: str, right: str) -> bool:
    if left == right:
        return True
    return (
        right in activation_name_candidates(left)
        or left in activation_name_candidates(right)
        or _component_shorthand_matches_activation_name(left, right)
        or _component_shorthand_matches_activation_name(right, left)
    )


def _component_shorthand_matches_activation_name(shorthand: str, activation_name: str) -> bool:
    """Return whether a bare component shorthand matches a layer-qualified activation."""
    if "." in shorthand:
        return False
    component = _ACT_NAME_ALIASES.get(_strip_hook_prefix(shorthand), _strip_hook_prefix(shorthand))
    if not _is_known_activation_component(component):
        return False
    return any(
        _ACT_NAME_ALIASES.get(candidate, candidate) == component
        for candidate in _activation_name_components(activation_name)
    )


def _activation_name_components(name: str) -> list[str]:
    if "." not in name:
        return [_ACT_NAME_ALIASES.get(_strip_hook_prefix(name), _strip_hook_prefix(name))]
    components: list[str] = []
    for candidate in activation_name_candidates(name):
        if "." not in candidate:
            components.append(
                _ACT_NAME_ALIASES.get(_strip_hook_prefix(candidate), _strip_hook_prefix(candidate))
            )
            continue
        tail = candidate.rsplit(".", 1)[-1]
        components.append(_ACT_NAME_ALIASES.get(_strip_hook_prefix(tail), _strip_hook_prefix(tail)))
    return components


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
    if module == "numpy":
        try:
            import numpy as np

            return np.stack(list(values))
        except Exception:
            pass
    return [clone_activation(value) for value in values]


def _normalize_residual_stack_name(stack: str) -> Literal["encoder", "decoder"]:
    normalized = str(stack).lower()
    if normalized in {"encoder", "default", "residual"}:
        return "encoder"
    if normalized == "decoder":
        return "decoder"
    raise ValueError("stack must be 'encoder' or 'decoder'.")


def _activation_key_stack_name(name: str) -> Literal["encoder", "decoder"]:
    if name.startswith("decoder_") or name.startswith("cross_") or name in _CROSS_TOP_LEVEL_ACTS:
        return "decoder"
    return "encoder"


def _residual_component_key(
    component: str,
    layer: int,
    *,
    stack: Literal["encoder", "decoder"],
) -> ActivationKey:
    if stack == "decoder":
        decoder_components = {
            "resid_pre",
            "resid_mid",
            "resid_mid_cross",
            "resid_post",
            "attn_out",
            "mlp_out",
        }
        if component in decoder_components:
            return (f"decoder_{component}", layer)
        if component == "cross_attn_out":
            return (component, layer)
    return (component, layer)


def _residual_stack_ln_name(stack: Literal["encoder", "decoder"], mlp_input: bool) -> str:
    if stack == "decoder":
        return "decoder_ln3_scale" if mlp_input else "decoder_ln1_scale"
    return "ln2" if mlp_input else "ln1"


def _residual_stack_fallback_ln_name(
    stack: Literal["encoder", "decoder"],
    mlp_input: bool,
) -> str | None:
    if stack == "decoder":
        return "decoder_ln1_scale" if mlp_input else "decoder_ln3_scale"
    return "ln1" if mlp_input else "ln2"


def _layer_norm_scale_candidates(layer: int, name: str) -> list[ActivationKey]:
    decoder_match = re.fullmatch(r"decoder_(ln[123])_scale", name)
    if decoder_match is not None:
        return [
            (name, layer),
            ("scale", layer, decoder_match.group(1)),
        ]
    return [("scale", layer, name)]


def _decoder_head_result_stack(
    cache: ActivationCache,
    layer: int,
    *,
    pos_slice: Any = None,
) -> tuple[Any, list[str]]:
    stacks: list[Any] = []
    labels: list[str] = []
    for component, suffix in (
        ("decoder_result", "decoder"),
        ("cross_result", "cross"),
    ):
        try:
            component_stack, component_labels = cache.stack_head_results(
                layer,
                pos_slice=pos_slice,
                return_labels=True,
                component=component,
            )
        except KeyError:
            continue
        stacks.extend(_unstack_first_dim(component_stack))
        labels.extend(f"{label}_{suffix}" for label in component_labels)
    if not stacks:
        raise KeyError("No decoder self-attention or cross-attention head results found in cache.")
    return stack_values(stacks), labels


def _layer_indices_from_cache_keys(
    cache: Mapping[str, Any],
    *,
    patterns: Sequence[str],
) -> set[int]:
    layers: set[int] = set()
    for key in cache:
        for pattern in patterns:
            match = re.search(pattern, key)
            if match is not None:
                layers.add(int(match.group(1)))
    return layers


def _call_hookpoint_fn(hook_fn: HookFn, activation: Any, hook: Any) -> Any:
    return call_user_hook(
        hook_fn,
        {"activation": activation, "output": activation, "hook": hook},
        positional_arg_options=((activation, hook), (activation,)),
    )


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
    if handle.is_permanent:
        return including_permanent
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
    if pos_slice is None or _is_identity_slice_like(pos_slice):
        return value
    return _slice_dim(value, pos_slice, dim=dim)


def _head_vector_pos_dim(component: str) -> int:
    if _is_attention_pattern_component(component):
        return -2
    return -3 if component in {"q", "k", "v", "z", "result"} else -2


def _is_attention_pattern_component(component: str) -> bool:
    return component in {"pattern", "attn_scores"}


def _slice_dim(value: Any, index: Any, *, dim: int) -> Any:
    apply = getattr(index, "apply", None)
    if callable(apply):
        try:
            return apply(value, dim=dim)
        except Exception:
            pass
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
            if size is not None and len(index) != size:
                raise IndexError(
                    f"Boolean index has length {len(index)} but axis has length {size}."
                )
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
    slice_value = getattr(index, "slice", _MISSING)
    mode = getattr(index, "mode", None)
    if slice_value is not _MISSING:
        if mode == "identity" or slice_value is None:
            return _FULL_SLICE
        return slice_value
    if isinstance(index, tuple):
        return slice(*index)
    return index


def _is_identity_slice_like(index: Any) -> bool:
    if index is None:
        return True
    return getattr(index, "mode", None) == "identity"


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


def _direction_batch_dim(
    direction: Any,
    residual_stack: Any,
    *,
    has_batch_dim: bool,
    prefer_pos_axis: bool = False,
) -> int | None:
    shape = _shape_of(direction)
    if not has_batch_dim or len(shape) < 2:
        return None
    if len(shape) >= 3:
        return 0
    residual_shape = _shape_of(residual_stack)
    if len(residual_shape) >= 3 and shape[0] == residual_shape[1]:
        if len(residual_shape) < 4 or shape[0] != residual_shape[2]:
            return 0
    if prefer_pos_axis:
        return None
    return None


def _direction_pos_dim(
    direction: Any,
    residual_stack: Any,
    *,
    has_batch_dim: bool,
    prefer_pos_axis: bool = False,
) -> int | None:
    shape = _shape_of(direction)
    if len(shape) < 2:
        return None
    residual_shape = _shape_of(residual_stack)
    if has_batch_dim and len(shape) == 2 and len(residual_shape) >= 3:
        batch_size = residual_shape[1]
        if shape[0] == batch_size and (len(residual_shape) < 4 or shape[0] != residual_shape[2]):
            return None
    if not has_batch_dim:
        return 0
    if len(shape) >= 3:
        return 1
    if prefer_pos_axis:
        return 0
    if len(residual_shape) >= 4:
        batch_size = residual_shape[1]
        if shape[0] != batch_size or batch_size == 1:
            return 0
        return None
    return 0


def _residual_stack_batch_dim(
    residual_stack: Any,
    directions: Any | None = None,
    *,
    pos_slice: Any = None,
) -> int:
    residual_shape = _shape_of(residual_stack)
    if len(residual_shape) <= 2:
        return 0
    direction_shape = _shape_of(directions)
    if (
        len(residual_shape) == 3
        and len(direction_shape) == 2
        and direction_shape[0] == residual_shape[1]
    ):
        return 1
    if len(residual_shape) == 3 and pos_slice is not None and len(direction_shape) >= 3:
        return 1
    if direction_shape and residual_shape == direction_shape:
        return 0
    if len(residual_shape) == 3:
        return 0
    return 1


def _residual_stack_pos_dim_before_optional_batch_slice(
    residual_stack: Any,
    *,
    has_batch_dim: bool,
) -> int:
    shape = _shape_of(residual_stack)
    if len(shape) <= 2:
        return 0
    if not has_batch_dim:
        return 1
    return 2 if len(shape) >= 4 else 1


def _maybe_slice_residual_stack_pos(
    residual_stack: Any,
    pos_slice: Any,
    *,
    has_batch_dim: bool,
    reference: Any | None = None,
) -> Any:
    if pos_slice is None:
        return residual_stack
    pos_dim = _residual_stack_pos_dim_before_optional_batch_slice(
        residual_stack,
        has_batch_dim=has_batch_dim,
    )
    shape = _shape_of(residual_stack)
    if len(shape) <= pos_dim:
        return residual_stack
    reference_shape = _shape_of(reference)
    if reference is not None:
        if len(shape) <= 2 and len(reference_shape) == 1 and shape[-1:] == reference_shape:
            return residual_stack
        selected_len = _reference_position_length(
            reference_shape,
            residual_shape=shape,
            has_batch_dim=has_batch_dim,
        )
        if selected_len is not None and shape[pos_dim] == selected_len:
            return residual_stack
    if not _index_fits_axis(_normalize_slice_index(pos_slice), shape[pos_dim]):
        return residual_stack
    return _slice_dim(residual_stack, pos_slice, dim=pos_dim)


def _slice_residual_stack_for_logit_attrs(
    residual_stack: Any,
    pos_slice: Any,
    *,
    batch_slice: Any = None,
    has_batch_dim: bool,
    residual_batch_dim: int,
    reference: Any | None = None,
) -> Any:
    if batch_slice is not None and has_batch_dim:
        residual_stack = _slice_dim(residual_stack, batch_slice, dim=residual_batch_dim)
        has_batch_dim = not isinstance(_normalize_slice_index(batch_slice), int)
    return _maybe_slice_residual_stack_pos(
        residual_stack,
        pos_slice,
        has_batch_dim=has_batch_dim,
        reference=reference,
    )


def _scale_pos_dim(scale: Any, *, has_batch_dim: bool) -> int:
    shape = _shape_of(scale)
    if len(shape) >= 3 and has_batch_dim:
        return 1
    return 0


def _scale_pos_dim_for_residual_stack(
    scale: Any,
    residual_stack: Any,
    *,
    has_batch_dim: bool,
) -> int:
    scale_shape = _shape_of(scale)
    if len(scale_shape) < 2:
        return 0
    if has_batch_dim:
        return 1 if len(scale_shape) >= 3 else 0
    if len(scale_shape) >= 3 and scale_shape[0] == 1:
        return 1
    residual_shape = _shape_of(residual_stack)
    residual_pos_dim = _residual_stack_pos_dim_before_optional_batch_slice(
        residual_stack,
        has_batch_dim=False,
    )
    if len(residual_shape) > residual_pos_dim and len(scale_shape) >= 3:
        if scale_shape[1] == residual_shape[residual_pos_dim]:
            return 1
    return 0


def _apply_cached_ln_scale_to_sliced_stack(
    cache: ActivationCache,
    residual_stack: Any,
    *,
    layer: int | None,
    pos_slice: Any = None,
    batch_slice: Any = None,
) -> Any:
    target_layer = cache._normalize_layer(layer)
    if _model_explicitly_has_no_layer_norm(cache.model):
        return residual_stack
    requires_cached_scale = _model_explicitly_uses_layer_norm(cache.model)
    if target_layer == cache._infer_n_layers():
        candidates: list[ActivationKey] = ["ln_final.hook_scale"]
    else:
        candidates = [
            ("scale", target_layer, "ln1"),
        ]
        if not requires_cached_scale:
            candidates.append(("scale", target_layer, "ln2"))
    scale_key = next((candidate for candidate in candidates if candidate in cache), None)
    if scale_key is None:
        if requires_cached_scale:
            expected_key = candidates[0]
            expected_name = (
                get_act_name(*expected_key)
                if isinstance(expected_key, tuple)
                else str(expected_key)
            )
            raise KeyError(
                f"Cached LN scale not found at {expected_name!r}. apply_ln operations require "
                "this hook to be cached for the requested layer."
            )
        return residual_stack
    scale = cache._get_cached_ln_scale(
        target_layer,
        mlp_input=False,
        pos_slice=pos_slice,
        batch_slice=batch_slice,
    )
    if _uses_centered_layer_norm(cache.model):
        residual_stack = _subtract_last_dim_mean(residual_stack)
    return _divide_values(residual_stack, scale)


def _reference_position_length(
    reference_shape: tuple[int, ...],
    *,
    residual_shape: tuple[int, ...],
    has_batch_dim: bool,
) -> int | None:
    if len(reference_shape) < 2:
        return None
    if len(reference_shape) >= 3:
        return reference_shape[1 if has_batch_dim else 0]
    if has_batch_dim and len(residual_shape) >= 4 and reference_shape[0] == residual_shape[1]:
        return None
    return reference_shape[0]


def _index_fits_axis(index: Any, size: int) -> bool:
    if isinstance(index, slice):
        return True
    if isinstance(index, int):
        return -size <= index < size
    if isinstance(index, range):
        return all(-size <= item < size for item in index)
    tolist = getattr(index, "tolist", None)
    if callable(tolist):
        index = tolist()
    if isinstance(index, Sequence) and not isinstance(index, str | bytes):
        if index and all(isinstance(item, bool) for item in index):
            return len(index) == size
        return all(-size <= int(item) < size for item in index)
    return True


def _residual_stack_pos_dim_after_optional_batch_slice(
    residual_stack: Any,
    *,
    has_batch_dim: bool,
    batch_slice: Any = None,
) -> int:
    shape = _shape_of(residual_stack)
    if len(shape) <= 2:
        return 0
    if not has_batch_dim:
        return 1
    if batch_slice is not None and isinstance(_normalize_slice_index(batch_slice), int):
        return 1 if len(shape) >= 3 else 0
    return 2 if len(shape) >= 4 else 1


def _head_axis_after_pos_slice(
    activation: Any, pos_slice: Any, *, component: str = "result"
) -> int:
    if _is_attention_pattern_component(component):
        return -2 if isinstance(pos_slice, int) else -3
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


def _empty_component_stack_like_cache(
    cache: ActivationCache,
    *,
    pos_slice: Any = None,
    has_batch_dim: bool = True,
    project_output_onto: Any = None,
) -> Any:
    source = _first_available_activation(cache, ("hook_embed", "resid_pre", "resid_post"))
    if source is _MISSING:
        return []
    source = _maybe_slice_pos(source, pos_slice)
    if project_output_onto is not None:
        source = _project_last_dim(source, project_output_onto)
    shape = _shape_of(source)
    if not shape:
        return []
    try:
        import torch

        if isinstance(source, torch.Tensor):
            return torch.zeros((0, *shape), dtype=source.dtype, device=source.device)
    except Exception:
        pass
    try:
        import numpy as np

        if isinstance(source, np.ndarray):
            return np.zeros((0, *shape), dtype=source.dtype)
    except Exception:
        pass
    _ = has_batch_dim
    return []


def _residual_remainder_base(
    cache: ActivationCache,
    target_layer: int,
    pos_slice: Any = None,
) -> Any:
    if target_layer > 0:
        if ("resid_post", target_layer - 1) not in cache:
            raise KeyError(
                "incl_remainder=True requires cached `resid_post` for the previous layer."
            )
        return _maybe_slice_pos(cache[("resid_post", target_layer - 1)], pos_slice)
    if ("resid_pre", 0) in cache:
        return _maybe_slice_pos(cache[("resid_pre", 0)], pos_slice)
    embed_parts: list[Any] = []
    for key in ("hook_embed", "hook_pos_embed"):
        if key in cache:
            embed_parts.append(_maybe_slice_pos(cache[key], pos_slice))
    if embed_parts:
        return _sum_values(embed_parts)
    if cache._infer_n_layers() <= 1 and ("resid_post", 0) in cache:
        return _maybe_slice_pos(cache[("resid_post", 0)], pos_slice)
    raise KeyError(
        "incl_remainder=True for layer 0 requires cached `resid_pre`, `hook_embed`, "
        "or `hook_pos_embed`."
    )


def _first_available_activation(
    cache: ActivationCache,
    names: Sequence[str],
) -> Any:
    for name in names:
        if name in cache:
            return cache[name]
    if len(cache) > 0:
        return next(iter(cache.values()))
    return _MISSING


def _divide_values(left: Any, right: Any) -> Any:
    try:
        return left / right
    except TypeError:
        if _is_sequence(left):
            if _is_sequence(right):
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
    if _shape_of(right) == ():
        try:
            return left * right
        except Exception:
            pass
        if _is_sequence(left):
            return [_multiply_by_last_vector(left_item, right) for left_item in left]
        return left
    try:
        return left[..., None] * right
    except Exception:
        pass
    if _is_sequence(left):
        return [_multiply_by_last_vector(left_item, right) for left_item in left]
    if _is_sequence(right):
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
            if right.ndim == 1:
                return left * right
            return torch.einsum("...n,nm->...nm", left, right)
    except Exception:
        pass
    try:
        import numpy as np

        if hasattr(left, "shape") or hasattr(right, "shape"):
            right = np.asarray(right)
            if right.ndim == 1:
                return np.asarray(left) * right
            return np.einsum("...n,nm->...nm", left, right)
    except Exception:
        pass

    if _shape_of(left) == ():
        return left
    if _is_vector(left):
        return [_multiply_by_last_vector(value, right[index]) for index, value in enumerate(left)]
    if _is_sequence(left):
        return [_multiply_last_dim_by_matrix(item, right) for item in left]
    return left


def _sum_values(values: Sequence[Any]) -> Any:
    if not values:
        return 0
    total = clone_activation(values[0])
    for value in values[1:]:
        total = _add_values(total, value)
    return total


def _add_values(left: Any, right: Any) -> Any:
    if _is_sequence(left) and _is_sequence(right):
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
    if _is_sequence(value):
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


def _expand_bias_like_for_folded_projection(
    bias: Any,
    unprojected_like: Any,
    projected_like: Any,
    projection: Any,
) -> Any:
    if unprojected_like is not None:
        return _expand_bias_like(bias, unprojected_like)
    projected_shape = _shape_of(projected_like)
    bias_shape = _shape_of(bias)
    projection_shape = _shape_of(projection)
    if len(bias_shape) != 1 or not projection_shape or projection_shape[0] != bias_shape[-1]:
        return bias
    if len(projection_shape) == 1:
        target_shape = (*projected_shape, bias_shape[-1])
    elif len(projection_shape) == 2:
        if projected_shape and projected_shape[-1] == projection_shape[-1]:
            target_shape = (*projected_shape[:-1], bias_shape[-1])
        else:
            target_shape = bias_shape
    else:
        return bias
    if target_shape == bias_shape:
        return bias
    try:
        return bias.expand(target_shape)
    except Exception:
        pass
    prefix = target_shape[:-1]
    result = bias
    for size in reversed(prefix):
        result = [clone_activation(result) for _ in range(size)]
    return result


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
    if _is_sequence(value):
        return [_subtract_last_dim_mean(item) for item in value]
    return value


def _mean_last_dim(value: Any) -> Any:
    try:
        return value.mean(dim=-1)
    except Exception:
        pass
    try:
        import numpy as np

        if hasattr(value, "shape"):
            return np.asarray(value).mean(axis=-1)
    except Exception:
        pass
    if _is_vector(value):
        if not value:
            return 0.0
        return sum(float(item) for item in value) / len(value)
    if _is_sequence(value):
        return [_mean_last_dim(item) for item in value]
    return value


def _sum_last_dim(value: Any) -> Any:
    try:
        return value.sum(dim=-1)
    except Exception:
        pass
    try:
        import numpy as np

        if hasattr(value, "shape"):
            return np.asarray(value).sum(axis=-1)
    except Exception:
        pass
    if _is_vector(value):
        return sum(float(item) for item in value)
    if _is_sequence(value):
        return [_sum_last_dim(item) for item in value]
    return value


def _sum_projection_input_dim(projection: Any) -> Any:
    shape = _shape_of(projection)
    if len(shape) <= 1:
        return _sum_last_dim(projection)
    try:
        return projection.sum(dim=-2)
    except Exception:
        pass
    try:
        import numpy as np

        if hasattr(projection, "shape"):
            return np.asarray(projection).sum(axis=-2)
    except Exception:
        pass
    if _is_sequence(projection):
        return _sum_values([clone_activation(row) for row in projection])
    return projection


def _subtract_values(left: Any, right: Any) -> Any:
    try:
        return left - right
    except TypeError:
        if _is_sequence(left) and _is_sequence(right):
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
    if _is_sequence(left) and _is_sequence(right):
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
                for left_item, right_item in zip(left, right, strict=False)
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
        import numpy  # noqa: F401

        if hasattr(left, "shape") or hasattr(projection, "shape"):
            return left @ projection
    except Exception:
        pass

    projection_shape = _shape_of(projection)
    if len(projection_shape) == 1:
        return _dot_last_dim(left, projection)
    if len(projection_shape) == 2:
        return _matmul_last_dim(left, projection)
    raise ValueError("project_output_onto must have shape [d_model] or [d_model, num_outputs].")


def _matmul_last_dim(left: Any, right: Any) -> Any:
    if _shape_of(left) == ():
        return left
    if _is_vector(left):
        return _matvec(left, right)
    if _is_sequence(left):
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
    return _is_sequence(value) and (not value or not _is_sequence(value[0]))


def _is_sequence(value: Any) -> bool:
    return isinstance(value, Sequence) and not isinstance(value, str | bytes)


def _can_broadcast_shape(source: tuple[int, ...], target: tuple[int, ...]) -> bool:
    if len(source) > len(target):
        return False
    padded = (1,) * (len(target) - len(source)) + source
    return all(
        source_dim in (1, target_dim)
        for source_dim, target_dim in zip(padded, target, strict=False)
    )


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
    return value[0] if padded_shape[axis] == 1 else value[index]


def _normalize_logit_tokens(model: Any, tokens: Any) -> Any:
    if isinstance(tokens, str):
        to_single_token = getattr(model, "to_single_token", None)
        if callable(to_single_token):
            return to_single_token(tokens)
    return tokens


def _get_final_layer_norm(
    model: Any,
    *,
    stack: Literal["encoder", "decoder"] = "encoder",
) -> Any:
    candidates = list(
        (
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
    )
    if _normalize_residual_stack_name(stack) == "decoder":
        candidates = _unique(
            [
                "decoder.final_layer_norm",
                "model.decoder.final_layer_norm",
                *candidates,
            ]
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
                normalized = cast(Any, normalized).squeeze(1)
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


def _model_explicitly_has_no_layer_norm(model: Any) -> bool:
    normalization_type = _get_model_attr(model, "normalization_type")
    if normalization_type is None:
        return False
    return str(normalization_type).lower() not in {
        "ln",
        "lnpre",
        "layernorm",
        "layer_norm",
        "rms",
        "rmspre",
        "rmsnorm",
        "rms_norm",
    }


def _model_explicitly_uses_layer_norm(model: Any) -> bool:
    normalization_type = _get_model_attr(model, "normalization_type")
    if normalization_type is None:
        return False
    return str(normalization_type).lower() in {
        "ln",
        "lnpre",
        "layernorm",
        "layer_norm",
        "rms",
        "rmspre",
        "rmsnorm",
        "rms_norm",
    }


def _model_is_attn_only(model: Any) -> bool:
    for name in ("attn_only", "attention_only"):
        value = _get_model_attr(model, name)
        if value is None:
            continue
        if isinstance(value, str):
            return value.strip().lower() in {"true", "1", "yes"}
        return bool(value)
    return False


def _get_config_int(model: Any, names: Sequence[str]) -> int | None:
    owners = _model_config_owners(model)
    wrapped = _safe_getattr(model, "model")
    if wrapped is not None:
        owners.extend(_model_config_owners(wrapped))
    for owner in owners:
        if owner is None:
            continue
        for name in names:
            value = _config_owner_value(owner, name)
            if value is not None:
                return int(value)
    return None


def _safe_getattr(owner: Any, name: str) -> Any:
    if owner is None:
        return None
    if isinstance(owner, Mapping):
        return owner.get(name)
    try:
        return getattr(owner, name)
    except Exception:
        return None


def _model_config_owners(model: Any) -> list[Any]:
    if model is None:
        return []
    cfg = _safe_getattr(model, "cfg")
    config = _safe_getattr(model, "config")
    owners = [model, cfg, config]
    for nested_name in ("text_config", "language_config", "decoder", "decoder_config"):
        nested = _safe_getattr(config, nested_name)
        if nested is not None:
            owners.append(nested)
    return owners


def _config_owner_value(owner: Any, name: str) -> Any:
    value = _safe_getattr(owner, name)
    if value is not None:
        return value
    config = _safe_getattr(owner, "config")
    if config is not None and config is not owner:
        return _safe_getattr(config, name)
    return None


def _get_model_attr(model: Any, name: str) -> Any:
    if model is None:
        return None
    owners = _model_config_owners(model)
    wrapped = _safe_getattr(model, "model")
    if wrapped is not None:
        owners.extend(_model_config_owners(wrapped))
    for owner in owners:
        if owner is None:
            continue
        value = _config_owner_value(owner, name)
        if value is not None:
            return value
    return None


def _get_layer_weight(model: Any, name: str, layer: int) -> Any:
    weights = _get_model_attr(model, name)
    if weights is not None:
        shape = _shape_of(weights)
        if len(shape) >= 3:
            return _slice_dim(weights, layer, dim=0)
        if len(shape) >= 2:
            return weights
    block_weight = _get_block_layer_weight(model, name, layer)
    if block_weight is not None:
        return block_weight
    return None


def _get_block_layer_weight(model: Any, name: str, layer: int) -> Any:
    blocks = _get_model_attr(model, "blocks")
    if blocks is None:
        return None
    try:
        block = blocks[layer]
    except Exception:
        return None
    owner_names = {
        "W_O": ("attn", "attention", "self_attn", "self_attention"),
        "W_out": ("mlp", "feed_forward", "ffn"),
    }.get(name, ())
    for owner_name in owner_names:
        owner = getattr(block, owner_name, None)
        if owner is None:
            continue
        value = getattr(owner, name, None)
        if value is not None:
            return value
    return getattr(block, name, None)


def _unique(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result


class _ScaledGradientValue:
    """Small proxy that scales scalar gradient reductions for hook callbacks."""

    def __init__(self, value: Any, scale: float) -> None:
        self._value = value
        self._scale = scale

    def sum(self, *args: Any, **kwargs: Any) -> Any:
        result = self._value.sum(*args, **kwargs)
        numel = getattr(result, "numel", None)
        if callable(numel):
            try:
                if int(cast(Any, numel())) == 1:
                    return result * self._scale
            except Exception:
                return result
        if _shape_of(result) == ():
            try:
                return result * self._scale
            except Exception:
                return result
        return result

    def __getattr__(self, name: str) -> Any:
        return getattr(self._value, name)

    def __repr__(self) -> str:
        return f"ScaledGradientValue({self._value!r}, scale={self._scale!r})"


def _scale_backward_gradient_for_hooks(grad: Any, scale: float) -> Any:
    if scale == 1.0:
        return grad
    return _ScaledGradientValue(grad, scale)


def _unwrap_scaled_gradient_value(value: Any) -> Any:
    if isinstance(value, _ScaledGradientValue):
        return value._value
    return value


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
    normalized_pos_slice = _normalize_cache_pos_slice(pos_slice)

    def cache_hook(*args: Any, **kwargs: Any) -> None:
        activation = extract_hook_output(args, kwargs)
        if activation is _MISSING:
            return None
        if remove_batch_dim:
            activation = _remove_singleton_batch(activation)
            cache.has_batch_dim = False
        if normalized_pos_slice is not None:
            activation = _slice_dim(
                activation,
                normalized_pos_slice,
                dim=_cache_pos_dim(name, activation),
            )
        cache.store(name, activation, detach=detach, clone=clone, device=device)
        return None

    cache_hook._safelens_is_cache_hook = True  # type: ignore[attr-defined]
    return cache_hook


def _normalize_cache_pos_slice(pos_slice: Any) -> Any:
    if isinstance(pos_slice, int):
        return [pos_slice]
    return pos_slice


def _cache_pos_dim(name: str, activation: Any) -> int:
    """Return TransformerLens' position dimension for a cached activation."""
    shape = _shape_of(activation)
    if not shape:
        return 0
    activation_name = name.removesuffix("_grad")
    if activation_name.endswith(("hook_q", "hook_k", "hook_v", "hook_z", "hook_result")):
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

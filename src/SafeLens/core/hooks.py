"""Hook and activation-cache primitives inspired by TransformerLens."""

from __future__ import annotations

import re
from collections.abc import Callable, Iterable, Iterator, MutableMapping, Sequence
from contextlib import contextmanager
from copy import deepcopy
from dataclasses import dataclass
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

    def __call__(self, activation: Any) -> Any:
        """Run forward hooks over an activation and return the final value."""
        output = activation
        for hook_fn, _handle in list(self.fwd_hooks):
            patched = _call_hookpoint_fn(hook_fn, output, self)
            if patched is not None:
                output = patched
        return output

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
    ) -> LensHandle:
        """Register a hook and return a removable handle."""
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
        return name == names_filter
    if callable(names_filter):
        return bool(names_filter(name))
    return name in names_filter


class ActivationCache(MutableMapping[Any, Any]):
    """Dictionary-like activation cache with small tensor-friendly helpers."""

    def __init__(
        self,
        cache_dict: dict[str, Any] | None = None,
        model: Any = None,
        *,
        has_batch_dim: bool = True,
    ) -> None:
        self._cache = dict(cache_dict or {})
        self.model = model
        self.has_batch_dim = has_batch_dim

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
        return [name for name in self._cache if matches_names_filter(name, names_filter)]

    def select(self, names_filter: NamesFilter) -> ActivationCache:
        """Return a new cache containing only matching activation names."""
        return ActivationCache(
            {
                name: value
                for name, value in self._cache.items()
                if matches_names_filter(name, names_filter)
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

    def to(self, device: Any) -> ActivationCache:
        """Move tensor-like activations to a device when values support `.to()`."""
        return self.apply_to_values(lambda value: _move_value(value, device))

    def cpu(self) -> ActivationCache:
        """Move tensor-like activations to CPU when supported."""
        return self.to("cpu")

    def detach(self) -> ActivationCache:
        """Detach tensor-like activations when values support `.detach()`."""
        return self.apply_to_values(_detach_value)

    def remove_batch_dim(self) -> ActivationCache:
        """Return a cache with singleton batch dimensions removed."""
        if not self.has_batch_dim:
            return self.clone()
        return ActivationCache(
            {name: _remove_singleton_batch(value) for name, value in self._cache.items()},
            model=self.model,
            has_batch_dim=False,
        )

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
        *,
        layer: int | None = None,
        layer_type: str | None = None,
    ) -> Any:
        """Stack one activation across layers."""
        n_layers = self._normalize_layer(layer)
        values = [
            self[(activation_name, current_layer, layer_type)] for current_layer in range(n_layers)
        ]
        return stack_values(values)

    def accumulated_resid(
        self,
        layer: int | None = None,
        *,
        incl_mid: bool = False,
        apply_ln: bool = False,
        mlp_input: bool = False,
        pos_slice: Any = None,
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
            residual_stack = self.apply_ln_to_stack(residual_stack, layer=target_layer)
        if return_labels:
            return residual_stack, labels
        return residual_stack

    def decompose_resid(
        self,
        layer: int | None = None,
        *,
        mlp_input: bool = False,
        mode: Literal["all", "mlp", "attn"] = "all",
        apply_ln: bool = False,
        incl_embeds: bool = True,
        pos_slice: Any = None,
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
            residual_stack = self.apply_ln_to_stack(residual_stack, layer=target_layer)
        if return_labels:
            return residual_stack, labels
        return residual_stack

    def stack_head_results(
        self,
        layer: int | None = None,
        *,
        component: str = "result",
        pos_slice: Any = None,
        return_labels: bool = False,
    ) -> Any:
        """Stack per-head activations from `[batch, pos, head, d_model]` caches."""
        target_layer = self._normalize_layer(layer)
        values: list[Any] = []
        labels: list[str] = []
        for current_layer in range(target_layer):
            if (component, current_layer) not in self:
                continue
            activation = _maybe_slice_pos(self[(component, current_layer)], pos_slice)
            for head_index in range(_infer_head_count(activation)):
                values.append(_slice_dim(activation, head_index, dim=-2))
                labels.append(f"L{current_layer}H{head_index}")
        if not values:
            raise KeyError(f"No {component!r} head activations found in cache.")
        head_stack = stack_values(values)
        if return_labels:
            return head_stack, labels
        return head_stack

    def stack_neuron_results(
        self,
        layer: int | None = None,
        *,
        component: str = "post",
        pos_slice: Any = None,
        return_labels: bool = False,
    ) -> Any:
        """Stack per-neuron MLP activations from `[batch, pos, d_mlp]` caches."""
        target_layer = self._normalize_layer(layer)
        values: list[Any] = []
        labels: list[str] = []
        for current_layer in range(target_layer):
            if (component, current_layer) not in self:
                continue
            activation = _maybe_slice_pos(self[(component, current_layer)], pos_slice)
            for neuron_index in range(_infer_last_dim(activation)):
                values.append(_slice_dim(activation, neuron_index, dim=-1))
                labels.append(f"L{current_layer}N{neuron_index}")
        if not values:
            raise KeyError(f"No {component!r} neuron activations found in cache.")
        neuron_stack = stack_values(values)
        if return_labels:
            return neuron_stack, labels
        return neuron_stack

    def get_full_resid_decomposition(
        self,
        layer: int | None = None,
        *,
        pos_slice: Any = None,
        return_labels: bool = False,
    ) -> Any:
        """Return a best-effort decomposition into embeds, heads, and MLP neurons."""
        stacks: list[Any] = []
        labels: list[str] = []

        try:
            resid_stack, resid_labels = self.decompose_resid(
                layer,
                mode="all",
                pos_slice=pos_slice,
                return_labels=True,
            )
            stacks.extend(_unstack_first_dim(resid_stack))
            labels.extend(resid_labels)
        except KeyError:
            pass

        for stack_fn in (self.stack_head_results, self.stack_neuron_results):
            try:
                component_stack, component_labels = stack_fn(
                    layer,
                    pos_slice=pos_slice,
                    return_labels=True,
                )
                stacks.extend(_unstack_first_dim(component_stack))
                labels.extend(component_labels)
            except KeyError:
                continue

        if not stacks:
            raise KeyError("No activations found for a full residual decomposition.")
        full_stack = stack_values(stacks)
        if return_labels:
            return full_stack, labels
        return full_stack

    def apply_ln_to_stack(
        self,
        residual_stack: Any,
        *,
        layer: int | None = None,
        scale_key: ActivationKey | None = None,
    ) -> Any:
        """Apply cached layer-norm scale to a residual stack when scale is available."""
        resolved_scale_key = scale_key
        if resolved_scale_key is None:
            target_layer = self._normalize_layer(layer)
            candidates: list[ActivationKey] = [
                "ln_final.hook_scale",
                ("scale", target_layer, "ln2"),
                ("scale", target_layer, "ln1"),
            ]
            resolved_scale_key = next(
                (candidate for candidate in candidates if candidate in self),
                None,
            )
        if resolved_scale_key is None:
            return residual_stack
        return _divide_values(residual_stack, self[resolved_scale_key])

    def logit_attrs(
        self,
        residual_stack: Any,
        tokens: Any,
        *,
        incorrect_tokens: Any = None,
        directions: Any = None,
        apply_ln: bool = True,
    ) -> Any:
        """Project residual components onto token residual directions."""
        if directions is None:
            if self.model is None:
                directions = tokens
            else:
                directions = self.model.tokens_to_residual_directions(tokens)
        if incorrect_tokens is not None:
            if self.model is None:
                incorrect_directions = incorrect_tokens
            else:
                incorrect_directions = self.model.tokens_to_residual_directions(incorrect_tokens)
            directions = _subtract_values(directions, incorrect_directions)
        if apply_ln:
            residual_stack = self.apply_ln_to_stack(residual_stack, layer=-1)
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
        candidates.append(get_act_name(key))
        candidates.append(safelens_act_name(key))
        return _unique(candidates)

    if not key:
        return []

    name = str(key[0])
    layer = key[1] if len(key) >= 2 else None
    layer_type = str(key[2]) if len(key) >= 3 and key[2] is not None else None
    if layer == -1 and n_layers > 0:
        layer = n_layers - 1
    aliased_name = _ACT_NAME_ALIASES.get(name, name)

    candidates = [
        ".".join(str(item) for item in key if item is not None),
        get_act_name(aliased_name, layer, layer_type),
    ]
    if layer is not None:
        candidates.append(safelens_act_name(aliased_name, layer))
        if layer_type:
            candidates.extend(
                [
                    f"{activation_name_for_layer(layer)}.{layer_type}.{aliased_name}",
                    f"blocks.{layer}.{layer_type}.hook_{aliased_name}",
                ]
            )
    return _unique(candidates)


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
    try:
        return hook_fn(activation, hook)
    except TypeError:
        return hook_fn(activation=activation, output=activation, hook=hook)


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


def _maybe_slice_pos(value: Any, pos_slice: Any) -> Any:
    if pos_slice is None:
        return value
    return _slice_dim(value, pos_slice, dim=1)


def _slice_dim(value: Any, index: Any, *, dim: int) -> Any:
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
    return _get_nested(value[head], tail)


def _shape_of(value: Any) -> tuple[int, ...]:
    shape = getattr(value, "shape", None)
    if shape is not None:
        return tuple(int(dim) for dim in shape)
    if isinstance(value, Sequence) and not isinstance(value, str | bytes):
        if not value:
            return (0,)
        return (len(value), *_shape_of(value[0]))
    return ()


def _infer_head_count(activation: Any) -> int:
    shape = _shape_of(activation)
    if len(shape) < 3:
        raise ValueError(f"Cannot infer head count from shape {shape!r}.")
    return shape[-2]


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
                return [
                    _divide_values(left_item, right_item)
                    for left_item, right_item in zip(left, right, strict=True)
                ]
            return [_divide_values(left_item, right) for left_item in left]
        return left


def _subtract_values(left: Any, right: Any) -> Any:
    try:
        return left - right
    except TypeError:
        if isinstance(left, list) and isinstance(right, list):
            return [
                _subtract_values(left_item, right_item)
                for left_item, right_item in zip(left, right, strict=True)
            ]
        return left


def _dot_last_dim(left: Any, right: Any) -> Any:
    try:
        return (left * right).sum(dim=-1)
    except Exception:
        pass
    if isinstance(left, list) and isinstance(right, list):
        if left and isinstance(left[0], list):
            return [
                _dot_last_dim(left_item, right_item)
                for left_item, right_item in zip(left, right, strict=True)
            ]
        return sum(
            float(left_item) * float(right_item)
            for left_item, right_item in zip(left, right, strict=True)
        )
    return left


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
) -> HookFn:
    """Create a hook that stores its activation in an `ActivationCache`."""

    def cache_hook(*args: Any, **kwargs: Any) -> None:
        activation = extract_hook_output(args, kwargs)
        if activation is _MISSING:
            return None
        cache.store(name, activation, detach=detach, clone=clone, device=device)
        return None

    return cache_hook


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

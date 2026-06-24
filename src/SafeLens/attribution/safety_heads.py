"""Safety head attribution adapted from SafetyHeadAttribution SHIPS."""

from __future__ import annotations

import math
from collections.abc import Iterable, Mapping, Sequence
from typing import Any

from SafeLens.core.base import AttributionResult, BaseAttributor, Batch, ModelWrapper
from SafeLens.core.hooks import ActivationCache, extract_hook_output, has_hook_output
from SafeLens.core.patching import activation_name_for_component
from SafeLens.core.registry import register_attributor


def attribute_safety_heads(
    model: ModelWrapper,
    batch: Batch | str,
    *,
    layers: Sequence[int] | None = None,
    heads: Sequence[int] | None = None,
    component: str = "result",
    ablation_mode: str = "zero",
    scale_factor: float = 0.0,
    top_k: int | None = None,
    cache_pos_slice: Any = None,
    score_type: str = "kl",
) -> AttributionResult:
    """Score attention heads by zero-ablating each head and measuring output shift."""
    attributor = SafetyHeadAttributor(
        {
            "layers": list(layers) if layers is not None else None,
            "heads": list(heads) if heads is not None else None,
            "component": component,
            "ablation_mode": ablation_mode,
            "scale_factor": scale_factor,
            "top_k": top_k,
            "cache_pos_slice": cache_pos_slice,
            "score_type": score_type,
        }
    )
    attributor.attach(model)
    try:
        return attributor.attribute_input(_normalize_batch(batch))
    finally:
        attributor.detach()


@register_attributor("safety_head_attributor")
class SafetyHeadAttributor(BaseAttributor):
    """Rank attention heads by SHIPS-style zero-ablation KL attribution."""

    def __init__(self, config: Mapping[str, Any] | None = None) -> None:
        super().__init__(config)
        self.model: ModelWrapper | None = None

    def attach(self, model: ModelWrapper) -> None:
        self.model = model

    def detach(self) -> None:
        self.model = None

    def attribute_training(self, batch: Batch, model_output: Any = None) -> AttributionResult:
        _ = batch, model_output
        return AttributionResult(
            method=self.name,
            attribution_score=0.0,
            details={
                "message": ("training attribution is not implemented for safety head attribution")
            },
        )

    def attribute_input(self, batch: Batch, model_output: Any = None) -> AttributionResult:
        _ = model_output
        model = self._require_model()
        torch = _require_torch()
        component = str(self.config.get("component", "result"))
        score_type = str(self.config.get("score_type", "kl")).lower()
        if score_type != "kl":
            raise ValueError("Safety head attribution currently supports score_type='kl'.")

        model_batch = _model_batch(batch)
        layers = _resolve_layers(self.config.get("layers"), model=model)
        restore_runtime = _enable_component_runtime(model, component)
        try:
            cache_layers = [activation_name_for_component(component, layer) for layer in layers]
            base_output, raw_cache = model.run_with_cache(
                model_batch,
                layers=cache_layers,
                return_cache_object=True,
                return_type="logits",
            )
            cache = _ensure_activation_cache(raw_cache, model=model)
            base_probs = _last_token_probs(base_output, torch=torch)
            head_candidates = _head_candidates(
                cache,
                layers=layers,
                heads=self.config.get("heads"),
                component=component,
                pos_slice=self.config.get("cache_pos_slice"),
            )

            scored_heads: list[dict[str, Any]] = []
            for layer, head, activation_norm in head_candidates:
                activation_name = activation_name_for_component(component, layer)
                hook = _make_ablate_head_hook(
                    head,
                    mode=str(self.config.get("ablation_mode", "zero")),
                    scale_factor=float(self.config.get("scale_factor", 0.0)),
                )
                masked_output = _run_with_single_hook(
                    model,
                    model_batch,
                    activation_name,
                    hook,
                )
                masked_probs = _last_token_probs(masked_output, torch=torch)
                score = _kl_divergence(base_probs, masked_probs, torch=torch)
                scored_heads.append(
                    {
                        "layer": layer,
                        "head": head,
                        "score": score,
                        "activation_norm": activation_norm,
                        "activation_name": activation_name,
                        "ablation_mode": str(self.config.get("ablation_mode", "zero")),
                        "scale_factor": float(self.config.get("scale_factor", 0.0)),
                    }
                )
        finally:
            restore_runtime()

        scored_heads.sort(key=lambda item: float(item["score"]), reverse=True)
        top_k = self.config.get("top_k")
        if top_k is not None:
            scored_heads = scored_heads[: int(top_k)]
        max_score = max((float(item["score"]) for item in scored_heads), default=0.0)

        return AttributionResult(
            method=self.name,
            attribution_score=_bounded_score(max_score),
            details={
                "score_type": score_type,
                "component": component,
                "ablation_mode": str(self.config.get("ablation_mode", "zero")),
                "scale_factor": float(self.config.get("scale_factor", 0.0)),
                "heads": scored_heads,
                "head_count": len(scored_heads),
                "source": "SafetyHeadAttribution SHIPS-style head ablation",
            },
        )

    def _require_model(self) -> ModelWrapper:
        if self.model is None:
            raise RuntimeError("SafetyHeadAttributor must be attached to a model first.")
        return self.model


def _normalize_batch(batch: Batch | str) -> Batch:
    if isinstance(batch, str):
        return {"text": batch}
    return batch


def _model_batch(batch: Batch) -> Any:
    if "input_ids" in batch or "tokens" in batch or "token_ids" in batch:
        return batch
    if "text" in batch or "prompt" in batch:
        return batch
    raise ValueError("Safety head attribution requires text/prompt or token ids in the batch.")


def _require_torch() -> Any:
    try:
        import torch
    except ImportError as exc:
        raise ImportError(
            "Safety head attribution requires torch. Install SafeLens with "
            "`pip install -e '.[models]'` or another torch-enabled extra."
        ) from exc
    return torch


def _ensure_activation_cache(raw_cache: Any, *, model: ModelWrapper) -> ActivationCache:
    if isinstance(raw_cache, ActivationCache):
        return raw_cache
    return ActivationCache(raw_cache, model=model)


def _enable_component_runtime(model: ModelWrapper, component: str) -> Any:
    cfg = getattr(model, "cfg", None)
    if component == "result":
        setter = getattr(model, "set_use_attn_result", None)
        previous = getattr(cfg, "use_attn_result", None)
        if callable(setter):
            setter(True)
            return lambda: setter(previous) if previous is not None else None
    if component in {"q", "k", "v"}:
        setter = getattr(model, "set_use_split_qkv_input", None)
        previous = getattr(cfg, "use_split_qkv_input", None)
        if callable(setter):
            setter(True)
            return lambda: setter(previous) if previous is not None else None
    return lambda: None


def _resolve_layers(raw_layers: Any, *, model: ModelWrapper) -> list[int]:
    if raw_layers is not None:
        return [int(layer) for layer in _as_sequence(raw_layers)]
    cfg = getattr(model, "cfg", None)
    n_layers = getattr(cfg, "n_layers", None)
    if n_layers is None:
        wrapped_model = getattr(model, "model", None)
        config = getattr(wrapped_model, "config", None)
        n_layers = _first_config_int(
            config,
            "num_hidden_layers",
            "n_layer",
            "n_layers",
            "num_layers",
        )
    if n_layers is None:
        raise ValueError("Could not infer model layer count; pass config['layers'].")
    return list(range(int(n_layers)))


def _head_candidates(
    cache: ActivationCache,
    *,
    layers: Sequence[int],
    heads: Any,
    component: str,
    pos_slice: Any,
) -> list[tuple[int, int, float]]:
    requested_heads = None if heads is None else {int(head) for head in _as_sequence(heads)}
    candidates: list[tuple[int, int, float]] = []
    for layer in layers:
        try:
            head_stack, labels = cache.stack_head_results(
                layer=int(layer) + 1,
                return_labels=True,
                pos_slice=pos_slice,
                component=component,
            )
        except KeyError:
            continue
        norms = _activation_norms(head_stack)
        for label, norm in zip(labels, norms, strict=True):
            parsed = _parse_head_label(label)
            if parsed is None:
                continue
            parsed_layer, head = parsed
            if parsed_layer != int(layer):
                continue
            if requested_heads is not None and head not in requested_heads:
                continue
            candidates.append((parsed_layer, head, norm))
    if not candidates:
        raise ValueError(
            f"No per-head {component!r} activations were found in the activation cache."
        )
    return candidates


def _activation_norms(head_stack: Any) -> list[float]:
    try:
        import torch

        if isinstance(head_stack, torch.Tensor):
            flattened = head_stack.reshape(head_stack.shape[0], -1)
            return [float(value) for value in torch.linalg.vector_norm(flattened, dim=1)]
        if (
            isinstance(head_stack, Sequence)
            and not isinstance(head_stack, str | bytes)
            and head_stack
            and all(isinstance(item, torch.Tensor) for item in head_stack)
        ):
            flattened = torch.stack(
                [
                    item.detach().to(device="cpu", dtype=torch.float32).reshape(-1)
                    for item in head_stack
                ]
            )
            return [float(value) for value in torch.linalg.vector_norm(flattened, dim=1)]
    except ImportError:
        pass
    try:
        import numpy as np

        array = np.asarray(head_stack, dtype=float).reshape(len(head_stack), -1)
        return [float(value) for value in np.linalg.norm(array, axis=1)]
    except Exception:
        return [_nested_l2_norm(item) for item in head_stack]


def _make_zero_head_hook(head: int) -> Any:
    return _make_ablate_head_hook(head, mode="zero", scale_factor=0.0)


def _make_ablate_head_hook(head: int, *, mode: str, scale_factor: float) -> Any:
    normalized_mode = mode.strip().lower()
    if normalized_mode not in {"zero", "scale", "mean"}:
        raise ValueError("ablation_mode must be one of: 'zero', 'scale', 'mean'.")

    def hook(*args: Any, **kwargs: Any) -> Any:
        if not has_hook_output(args, kwargs):
            return None
        activation = extract_hook_output(args, kwargs)
        return _ablate_head_activation(
            activation,
            int(head),
            mode=normalized_mode,
            scale_factor=scale_factor,
        )

    return hook


def _zero_head_activation(activation: Any, head: int) -> Any:
    return _ablate_head_activation(activation, head, mode="zero", scale_factor=0.0)


def _ablate_head_activation(
    activation: Any,
    head: int,
    *,
    mode: str,
    scale_factor: float,
) -> Any:
    try:
        import torch

        if isinstance(activation, torch.Tensor):
            patched = activation.clone()
            if mode == "zero":
                patched[:, :, head, ...] = 0
            elif mode == "scale":
                patched[:, :, head, ...] *= scale_factor
            elif mode == "mean":
                patched[:, :, head, ...] = patched.mean(dim=2)
            return patched
    except ImportError:
        pass
    try:
        import numpy as np

        if isinstance(activation, np.ndarray):
            patched = activation.copy()
            if mode == "zero":
                patched[:, :, head, ...] = 0
            elif mode == "scale":
                patched[:, :, head, ...] *= scale_factor
            elif mode == "mean":
                patched[:, :, head, ...] = patched.mean(axis=2)
            return patched
    except ImportError:
        pass
    return _ablate_nested_head(
        activation,
        head,
        mode=mode,
        scale_factor=scale_factor,
    )


def _zero_nested_head(activation: Any, head: int) -> Any:
    return _ablate_nested_head(activation, head, mode="zero", scale_factor=0.0)


def _ablate_nested_head(
    activation: Any,
    head: int,
    *,
    mode: str,
    scale_factor: float,
) -> Any:
    if not isinstance(activation, Sequence) or isinstance(activation, str | bytes):
        raise TypeError("Expected attention head activation shaped [batch, pos, head, ...].")
    patched = _deep_list(activation)
    for batch_item in patched:
        for pos_item in batch_item:
            if mode == "zero":
                pos_item[head] = _zero_like(pos_item[head])
            elif mode == "scale":
                pos_item[head] = _scale_like(pos_item[head], scale_factor)
            elif mode == "mean":
                pos_item[head] = _mean_nested_heads(pos_item)
    return patched


def _run_with_single_hook(
    model: ModelWrapper,
    batch: Any,
    activation_name: str,
    hook: Any,
) -> Any:
    run_with_hooks = getattr(model, "run_with_hooks", None)
    if callable(run_with_hooks):
        return run_with_hooks(
            batch,
            fwd_hooks=[(activation_name, hook)],
            return_type="logits",
        )
    handle = model.add_hook(activation_name, hook)
    try:
        output, _cache = model.run_with_cache(
            batch,
            layers=[],
            return_type="logits",
        )
        return output
    finally:
        remove = getattr(handle, "remove", None)
        if callable(remove):
            remove()


def _last_token_probs(logits: Any, *, torch: Any) -> Any:
    if not isinstance(logits, torch.Tensor):
        logits = torch.as_tensor(logits, dtype=torch.float32)
    if logits.ndim == 3:
        logits = logits[:, -1, :]
    elif logits.ndim == 2:
        pass
    elif logits.ndim == 1:
        logits = logits.unsqueeze(0)
    else:
        raise ValueError(f"Expected logits shaped [batch, pos, vocab], got {tuple(logits.shape)}.")
    return torch.softmax(logits.to(dtype=torch.float32), dim=-1)


def _kl_divergence(base_probs: Any, masked_probs: Any, *, torch: Any) -> float:
    eps = torch.finfo(base_probs.dtype).eps
    value = (base_probs * ((base_probs + eps).log() - (masked_probs + eps).log())).sum(dim=-1)
    return max(0.0, float(value.mean().detach().cpu().item()))


def _bounded_score(score: float) -> float:
    if not math.isfinite(score) or score <= 0:
        return 0.0
    return min(1.0, float(score))


def _parse_head_label(label: str) -> tuple[int, int] | None:
    if not label.startswith("L") or "H" not in label:
        return None
    layer_part, head_part = label[1:].split("H", 1)
    return int(layer_part), int(head_part)


def _as_sequence(value: Any) -> Sequence[Any]:
    if isinstance(value, Sequence) and not isinstance(value, str | bytes):
        return value
    return [value]


def _first_config_int(config: Any, *names: str) -> int | None:
    for name in names:
        value = config.get(name) if isinstance(config, Mapping) else getattr(config, name, None)
        if value is not None:
            return int(value)
    return None


def _nested_l2_norm(value: Any) -> float:
    try:
        import torch

        if isinstance(value, torch.Tensor):
            flattened = value.detach().to(device="cpu", dtype=torch.float32).reshape(-1)
            return float(torch.linalg.vector_norm(flattened).item())
    except ImportError:
        pass
    total = 0.0
    for item in _flatten(value):
        total += float(item) ** 2
    return math.sqrt(total)


def _flatten(value: Any) -> Iterable[Any]:
    try:
        import torch

        if isinstance(value, torch.Tensor):
            yield from value.detach().to(device="cpu").reshape(-1).tolist()
            return
    except ImportError:
        pass
    if isinstance(value, Sequence) and not isinstance(value, str | bytes):
        for item in value:
            yield from _flatten(item)
    else:
        yield value


def _deep_list(value: Any) -> Any:
    if isinstance(value, Sequence) and not isinstance(value, str | bytes):
        return [_deep_list(item) for item in value]
    return value


def _zero_like(value: Any) -> Any:
    if isinstance(value, Sequence) and not isinstance(value, str | bytes):
        return [_zero_like(item) for item in value]
    return 0


def _scale_like(value: Any, scale_factor: float) -> Any:
    if isinstance(value, Sequence) and not isinstance(value, str | bytes):
        return [_scale_like(item, scale_factor) for item in value]
    return float(value) * scale_factor


def _mean_nested_heads(pos_item: Any) -> Any:
    try:
        import numpy as np

        array = np.asarray(pos_item, dtype=float)
        return array.mean(axis=0).tolist()
    except Exception:
        if not isinstance(pos_item, Sequence) or not pos_item:
            return pos_item
        return _mean_nested_values(pos_item)


def _mean_nested_values(values: Sequence[Any]) -> Any:
    first = values[0]
    if isinstance(first, Sequence) and not isinstance(first, str | bytes):
        return [
            _mean_nested_values([value[index] for value in values]) for index in range(len(first))
        ]
    return sum(float(value) for value in values) / len(values)

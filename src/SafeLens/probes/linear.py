"""Simple linear activation probe."""

from __future__ import annotations

import json
import math
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from SafeLens.core.base import BaseProbe, Batch, LayerRef, ModelWrapper, ProbeResult
from SafeLens.core.registry import register_probe


@register_probe("linear_probe")
class LinearProbe(BaseProbe):
    """Linear logistic-regression probe trained from labeled features."""

    def __init__(self, config: Mapping[str, Any] | None = None) -> None:
        self.config = dict(config or {})
        self.layers: list[LayerRef] = []
        self._handles: list[Any] = []
        self._last_activations: dict[str, Any] = {}
        self._intervention_applied = False

        self.feature_key = str(self.config.get("feature_key", "features"))
        self.label_key = str(self.config.get("label_key", "label"))
        self.positive_label = self.config.get("positive_label", 1)
        self.threshold = float(self.config.get("threshold", 0.5))
        self.activation_reduce = str(self.config.get("activation_reduce", "last_token"))
        self.training_epochs = int(self.config.get("epochs", 500))
        self.learning_rate = float(self.config.get("learning_rate", 0.1))
        self.l2 = float(self.config.get("l2", 0.0))
        self.train_from_dataset = bool(self.config.get("train_from_dataset", False))
        self.split_key = str(self.config.get("split_key", "split"))
        self.train_split = self.config.get("train_split")
        self.eval_split = self.config.get("eval_split")
        self._training_loss: float | None = None
        self._device = self.config.get("device")
        self._torch: Any | None = None
        self._model: ModelWrapper | None = None

        self.weights = self._optional_vector(self.config.get("weights"))
        self.bias = float(self.config.get("bias", 0.0))
        self._pending_train_data = self.config.get("train_data")
        self._pending_train_path = self.config.get("train_jsonl")
        self._runtime_dataset: list[Mapping[str, Any]] | None = None

    def set_dataset(self, dataset: Sequence[Mapping[str, Any]]) -> None:
        """Provide the active pipeline dataset for optional in-run training."""
        self._runtime_dataset = [dict(row) for row in dataset]

    def filter_dataset(self, dataset: Sequence[Mapping[str, Any]]) -> list[Mapping[str, Any]]:
        """Return the evaluation subset when an eval split is configured."""
        if self.eval_split is None:
            return list(dataset)
        return [row for row in dataset if row.get(self.split_key) == self.eval_split]

    def attach(self, model: ModelWrapper, layers: Sequence[int]) -> None:
        self._model = model
        if self._device is None:
            self._device = getattr(model, "device", None)
        raw_layers = layers or self.config.get("layers", [])
        self.layers = list(raw_layers)
        for layer in self.layers:
            self._handles.append(model.add_hook(layer, self._capture_activation))
        if self.weights is None:
            self._fit_from_config()
        elif self._device is not None:
            self._move_weights_to_device()

    def detect(self, batch: Batch) -> ProbeResult:
        features = self._features_from_batch(batch)
        source = "batch"
        if features is None:
            activation = self._select_activation()
            features = self._vector_from_activation(activation)
            source = "activation"

        if features is None or self.weights is None:
            risk_score = 0.0
            logit = None
        else:
            self._validate_feature_size(features)
            logit = self._predict_logit(features)
            risk_score = self._sigmoid(logit)

        triggered = risk_score >= self.threshold
        return ProbeResult(
            risk_score=risk_score,
            critical_layers=list(self.layers),
            intervention_applied=self._intervention_applied,
            details={
                "method": self.name,
                "threshold": self.threshold,
                "triggered": triggered,
                "feature_source": source,
                "logit": logit,
                "trained": self.weights is not None,
                "training_loss": self._training_loss,
                "risk_category": self.config.get("risk_category", ["linear_probe"])
                if triggered
                else [],
            },
        )

    def intervene(self, batch: Batch, direction: Any, scale: float) -> None:
        _ = batch, direction, scale
        self._intervention_applied = True

    def detach(self) -> None:
        for handle in self._handles:
            handle.remove()
        self._handles.clear()
        self.layers = []
        self._last_activations.clear()
        self._model = None

    def _capture_activation(self, *args: Any, **kwargs: Any) -> Any:
        activation = kwargs.get("activation")
        layer = kwargs.get("layer")
        hook = kwargs.get("hook")
        if activation is None and args:
            activation = args[0]
        layer_name = str(layer if layer is not None else getattr(hook, "name", "activation"))
        self._last_activations[layer_name] = activation
        return None

    def _fit_from_config(self) -> None:
        train_data = self._pending_train_data
        train_path = self._pending_train_path
        if train_data is None and train_path is not None:
            train_data = self._load_jsonl(Path(str(train_path)))
        if train_data is None and self.train_from_dataset:
            train_data = self._runtime_dataset
        if train_data is None:
            return
        train_data = self._filter_train_data(train_data)

        examples: list[tuple[Any, float]] = []
        for row in train_data:
            if not isinstance(row, Mapping):
                continue
            features = self._training_features_from_row(row)
            if features is None:
                continue
            label = 1.0 if row.get(self.label_key) == self.positive_label else 0.0
            examples.append((features, label))

        if not any(label == 1.0 for _features, label in examples) or not any(
            label == 0.0 for _features, label in examples
        ):
            raise ValueError(
                "linear_probe training requires at least one positive and one negative"
            )

        if self._fit_with_torch(examples):
            return

        python_examples = [(self._as_vector(features), label) for features, label in examples]
        self._fit_with_python(python_examples)

    def _filter_train_data(self, train_data: Any) -> Any:
        if self.train_split is None:
            return train_data
        return [
            row
            for row in train_data
            if isinstance(row, Mapping) and row.get(self.split_key) == self.train_split
        ]

    def _fit_with_torch(self, examples: Sequence[tuple[Any, float]]) -> bool:
        torch = self._torch_module()
        if torch is None:
            return False
        try:
            features_tensor = torch.stack(
                [self._as_torch_vector(features, torch) for features, _label in examples]
            )
        except Exception:
            return False
        labels_tensor = torch.tensor(
            [label for _features, label in examples],
            dtype=features_tensor.dtype,
            device=features_tensor.device,
        )

        feature_size = int(features_tensor.shape[-1])
        weights = torch.zeros(
            feature_size,
            dtype=features_tensor.dtype,
            device=features_tensor.device,
        )
        bias = torch.zeros((), dtype=features_tensor.dtype, device=features_tensor.device)
        for _epoch in range(max(self.training_epochs, 0)):
            logits = features_tensor.matmul(weights) + bias
            predictions = torch.sigmoid(logits)
            errors = predictions - labels_tensor
            loss = self._torch_binary_cross_entropy(predictions, labels_tensor, torch)
            loss = loss.mean() + 0.5 * self.l2 * (weights * weights).sum()

            grad_w = features_tensor.transpose(0, 1).matmul(errors) / features_tensor.shape[0]
            grad_w = grad_w + self.l2 * weights
            grad_b = errors.mean()

            weights = weights - self.learning_rate * grad_w
            bias = bias - self.learning_rate * grad_b
            self._training_loss = float(loss.detach().cpu().item())

        if self.training_epochs <= 0:
            predictions = torch.sigmoid(features_tensor.matmul(weights) + bias)
            loss = self._torch_binary_cross_entropy(predictions, labels_tensor, torch)
            loss = loss.mean() + 0.5 * self.l2 * (weights * weights).sum()
            self._training_loss = float(loss.detach().cpu().item())

        self._torch = torch
        self.weights = weights.detach()
        self.bias = bias.detach()
        return True

    def _fit_with_python(self, examples: Sequence[tuple[list[float], float]]) -> None:
        feature_size = len(examples[0][0])
        for features, _label in examples:
            if len(features) != feature_size:
                raise ValueError("linear_probe training features must share one dimension")

        self.weights = [0.0] * feature_size
        self.bias = 0.0
        for _epoch in range(max(self.training_epochs, 0)):
            grad_w = [0.0] * feature_size
            grad_b = 0.0
            loss = 0.0

            for features, label in examples:
                logit = self._dot(self.weights, features) + self.bias
                prediction = self._sigmoid(logit)
                error = prediction - label
                loss += self._binary_cross_entropy(prediction, label)
                for index, value in enumerate(features):
                    grad_w[index] += error * value
                grad_b += error

            count = float(len(examples))
            loss /= count
            for index, weight in enumerate(self.weights):
                loss += 0.5 * self.l2 * weight * weight
                grad_w[index] = grad_w[index] / count + self.l2 * weight
            grad_b /= count

            for index, gradient in enumerate(grad_w):
                self.weights[index] -= self.learning_rate * gradient
            self.bias -= self.learning_rate * grad_b
            self._training_loss = loss

        if self.training_epochs <= 0:
            self._training_loss = self._training_loss_for(examples)

    def _features_from_batch(self, batch: Mapping[str, Any]) -> list[float] | None:
        value = self._raw_features_from_batch(batch)
        if value is None:
            return None
        return self._as_vector(value)

    def _raw_features_from_batch(self, batch: Mapping[str, Any]) -> Any | None:
        if self.feature_key not in batch:
            return None
        return batch[self.feature_key]

    def _training_features_from_row(self, row: Mapping[str, Any]) -> Any | None:
        features = self._raw_features_from_batch(row)
        if features is not None:
            return features
        if self._model is None:
            return None
        activation = self._activation_from_model(row)
        if activation is None:
            return None
        return self._activation_to_feature_value(activation)

    def _activation_from_model(self, row: Mapping[str, Any]) -> Any | None:
        self._last_activations.clear()
        _output, cache = self._model.run_with_cache(row, layers=self.layers)
        activation = self._activation_from_cache(cache)
        if activation is not None:
            return activation
        return self._select_activation()

    def _activation_from_cache(self, cache: Any) -> Any | None:
        cache_dict = self._cache_to_dict(cache)
        if not cache_dict:
            return None

        preferred_layer = self.config.get("activation_layer")
        if preferred_layer is not None:
            for key, value in cache_dict.items():
                if str(key) == str(preferred_layer):
                    return value

        for layer in reversed(self.layers):
            layer_text = str(layer)
            for key, value in cache_dict.items():
                if str(key) == layer_text:
                    return value

        return next(reversed(cache_dict.values()))

    @staticmethod
    def _cache_to_dict(cache: Any) -> dict[Any, Any]:
        to_dict = getattr(cache, "to_dict", None)
        if callable(to_dict):
            return dict(to_dict())
        if isinstance(cache, Mapping):
            return dict(cache)
        items = getattr(cache, "items", None)
        if callable(items):
            return dict(items())
        return {}

    def _activation_to_feature_value(self, activation: Any) -> Any | None:
        if isinstance(activation, Mapping):
            for key in (self.feature_key, "activation", "hidden_state", "value"):
                if key in activation:
                    return self._activation_to_feature_value(activation[key])
            batch = activation.get("batch")
            if isinstance(batch, Mapping):
                return self._raw_features_from_batch(batch)
            return None
        return self._reduce_activation(activation)

    def _select_activation(self) -> Any:
        if not self._last_activations:
            return None
        preferred_layer = self.config.get("activation_layer")
        if preferred_layer is not None:
            return self._last_activations.get(str(preferred_layer))
        return next(reversed(self._last_activations.values()))

    def _vector_from_activation(self, activation: Any) -> list[float] | None:
        if isinstance(activation, Mapping):
            for key in (self.feature_key, "activation", "hidden_state", "value"):
                if key in activation:
                    return self._vector_from_activation(activation[key])
            batch = activation.get("batch")
            if isinstance(batch, Mapping):
                return self._features_from_batch(batch)
            return None

        reduced = self._reduce_activation(activation)
        if reduced is None:
            return None
        return self._as_vector(reduced)

    def _reduce_activation(self, activation: Any) -> Any:
        shape = getattr(activation, "shape", None)
        if shape is not None:
            rank = len(shape)
            if self.activation_reduce == "mean":
                mean = getattr(activation, "mean", None)
                if callable(mean) and rank >= 2:
                    dims = tuple(range(rank - 1))
                    if "torch" in type(activation).__module__:
                        return mean(dim=dims)
                    return mean(axis=dims)
            if self.activation_reduce == "last_token" and rank >= 3:
                return activation[0, -1, :]
            if self.activation_reduce == "last_token" and rank >= 2:
                return activation[-1, :]
            return activation

        if self.activation_reduce == "mean":
            rows = self._flatten_rows(activation)
            return self._mean(rows) if rows else None
        if self.activation_reduce == "last_token":
            return self._last_nested_vector(activation)
        return activation

    def _as_vector(self, value: Any) -> list[float]:
        detach = getattr(value, "detach", None)
        if callable(detach):
            value = detach()
        cpu = getattr(value, "cpu", None)
        if callable(cpu):
            value = cpu()
        tolist = getattr(value, "tolist", None)
        if callable(tolist):
            value = tolist()
        vector = self._last_nested_vector(value)
        if vector is None:
            raise ValueError(f"Could not convert {self.feature_key!r} to a numeric vector")
        return [float(item) for item in vector]

    def _validate_feature_size(self, features: Sequence[float]) -> None:
        weights_size = self._weights_size()
        if weights_size is not None and len(features) != weights_size:
            raise ValueError(
                "linear_probe feature dimension mismatch: "
                f"got {len(features)}, expected {weights_size}"
            )

    def _weights_size(self) -> int | None:
        if self.weights is None:
            return None
        shape = getattr(self.weights, "shape", None)
        if shape is not None:
            return int(shape[-1])
        return len(self.weights)

    @staticmethod
    def _optional_vector(value: Any) -> list[float] | None:
        if value is None:
            return None
        return [float(item) for item in value]

    @staticmethod
    def _load_jsonl(path: Path) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    rows.append(json.loads(line))
        return rows

    @staticmethod
    def _mean(rows: Sequence[Sequence[float]]) -> list[float]:
        width = len(rows[0])
        totals = [0.0] * width
        for row in rows:
            if len(row) != width:
                raise ValueError("linear_probe training features must share one dimension")
            for index, value in enumerate(row):
                totals[index] += float(value)
        return [value / len(rows) for value in totals]

    @staticmethod
    def _dot(left: Sequence[float], right: Sequence[float]) -> float:
        return sum(a * b for a, b in zip(left, right, strict=True))

    def _predict_logit(self, features: Sequence[float]) -> float:
        torch = self._torch
        if torch is not None and self._is_torch_tensor(self.weights):
            feature_tensor = self._as_torch_vector(features, torch)
            logit = feature_tensor.matmul(self.weights) + self.bias
            return float(logit.detach().cpu().item())
        return self._dot(self.weights, features) + self.bias

    def _move_weights_to_device(self) -> None:
        torch = self._torch_module()
        if torch is None or self.weights is None:
            return
        try:
            if not self._is_torch_tensor(self.weights):
                self.weights = torch.tensor(self.weights, dtype=torch.float32, device=self._device)
            else:
                self.weights = self.weights.to(self._device)
            if not self._is_torch_tensor(self.bias):
                self.bias = torch.tensor(
                    float(self.bias),
                    dtype=self.weights.dtype,
                    device=self._device,
                )
            else:
                self.bias = self.bias.to(self._device)
        except Exception:
            return

    @staticmethod
    def _sigmoid(value: float) -> float:
        if value >= 0:
            z = math.exp(-value)
            return 1.0 / (1.0 + z)
        z = math.exp(value)
        return z / (1.0 + z)

    @staticmethod
    def _binary_cross_entropy(prediction: float, label: float) -> float:
        eps = 1e-12
        prediction = min(1.0 - eps, max(eps, prediction))
        return -(label * math.log(prediction) + (1.0 - label) * math.log(1.0 - prediction))

    def _training_loss_for(self, examples: Sequence[tuple[list[float], float]]) -> float:
        if self.weights is None or self._is_torch_tensor(self.weights):
            return 0.0
        loss = 0.0
        for features, label in examples:
            prediction = self._sigmoid(self._dot(self.weights, features) + self.bias)
            loss += self._binary_cross_entropy(prediction, label)
        loss /= float(len(examples))
        loss += 0.5 * self.l2 * sum(weight * weight for weight in self.weights)
        return loss

    def _torch_module(self) -> Any | None:
        if self._torch is not None:
            return self._torch
        try:
            import torch
        except ModuleNotFoundError:
            return None
        self._torch = torch
        return torch

    def _as_torch_vector(self, value: Any, torch: Any) -> Any:
        if self._is_torch_tensor(value):
            tensor = value.detach()
            tensor = self._reduce_activation(tensor)
            if not self._is_torch_tensor(tensor):
                tensor = torch.as_tensor(tensor, dtype=torch.float32, device=self._device)
            if tensor.ndim != 1:
                tensor = tensor.reshape(-1)
            if self._device is not None:
                tensor = tensor.to(self._device)
            return tensor.float()

        vector = self._as_vector(value)
        return torch.tensor(vector, dtype=torch.float32, device=self._device)

    @staticmethod
    def _torch_binary_cross_entropy(prediction: Any, label: Any, torch: Any) -> Any:
        eps = 1e-12
        prediction = torch.clamp(prediction, eps, 1.0 - eps)
        return -(label * torch.log(prediction) + (1.0 - label) * torch.log(1.0 - prediction))

    @staticmethod
    def _is_torch_tensor(value: Any) -> bool:
        return "torch" in type(value).__module__ and hasattr(value, "detach")

    @classmethod
    def _last_nested_vector(cls, value: Any) -> list[Any] | None:
        if isinstance(value, str | bytes):
            return None
        if isinstance(value, Sequence):
            if not value:
                return None
            if all(
                not isinstance(item, Sequence) or isinstance(item, str | bytes) for item in value
            ):
                return list(value)
            return cls._last_nested_vector(value[-1])
        return None

    @classmethod
    def _flatten_rows(cls, value: Any) -> list[list[float]]:
        if isinstance(value, str | bytes):
            return []
        if not isinstance(value, Sequence) or not value:
            return []
        if all(not isinstance(item, Sequence) or isinstance(item, str | bytes) for item in value):
            return [[float(item) for item in value]]
        rows: list[list[float]] = []
        for item in value:
            rows.extend(cls._flatten_rows(item))
        return rows

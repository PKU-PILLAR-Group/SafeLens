"""Small TransformerLens-compatible utility helpers."""

from __future__ import annotations

import errno
import importlib.util
import inspect
import json
import logging
import math
import os
import random
import shutil
import stat
import time
import warnings
from copy import deepcopy
from typing import Any, TypeAlias

NonlinearityType: TypeAlias = str
USE_DEFAULT_VALUE = None
_HF_RETRY_MAX_ATTEMPTS = 3
_HF_RETRY_BASE_DELAY_SECONDS = 10.0
_HF_RETRY_MAX_DELAY_SECONDS = 120.0
_TL_RETRY_WRAPPED_ATTR = "_tl_hf_retry_wrapped"
_MPS_MIN_SAFE_TORCH_VERSION: tuple[int, ...] | None = None
_MPS_BROKEN_TORCH_VERSIONS: tuple[tuple[int, ...], ...] = ((2, 8),)
_mps_warned = False
_mps_broken_torch_warned = False
logger = logging.getLogger(__name__)


def get_nested_attr(obj: Any, attr_str: str) -> Any:
    """Retrieve a dot-separated nested attribute."""

    for attr in attr_str.split("."):
        obj = getattr(obj, attr)
    return obj


def set_nested_attr(obj: Any, attr_str: str, value: Any) -> None:
    """Set a dot-separated nested attribute."""

    attrs = attr_str.split(".")
    for attr in attrs[:-1]:
        obj = getattr(obj, attr)
    setattr(obj, attrs[-1], value)


def override_or_use_default_value(default_flag: Any, override: Any | None = None) -> Any:
    """Return ``override`` unless it is ``None``; otherwise return ``default_flag``."""

    return override if override is not None else default_flag


class LocallyOverridenDefaults:
    """Temporarily override TL-style model defaults and restore them on exit."""

    def __init__(self, model: Any, **overrides: Any) -> None:
        self.model = model
        self.overrides = overrides
        tokenizer = getattr(model, "tokenizer", None)
        self.values_with_defaults = {
            "prepend_bos": {
                "default_location": "model.cfg.default_prepend_bos",
                "valid_values": [USE_DEFAULT_VALUE, True, False],
                "skip_overriding": False,
                "default_value_to_restore": None,
            },
            "padding_side": {
                "default_location": "model.tokenizer.padding_side",
                "valid_values": [USE_DEFAULT_VALUE, "left", "right"],
                "skip_overriding": tokenizer is None,
                "default_value_to_restore": None,
            },
        }
        for override in overrides:
            assert override in self.values_with_defaults, (
                f"{override} is not a valid parameter to override. "
                f"Valid parameters are {self.values_with_defaults.keys()}."
            )

    def __enter__(self) -> LocallyOverridenDefaults:
        for property_name, override in self.overrides.items():
            info = self.values_with_defaults[property_name]
            if info["skip_overriding"]:
                continue
            valid_values = info["valid_values"]
            assert override in valid_values, (
                f"{property_name} must be one of {valid_values}, but got {override}."
            )
            default_location = info["default_location"]
            default_value = get_nested_attr(self, default_location)
            info["default_value_to_restore"] = deepcopy(default_value)
            set_nested_attr(
                self,
                default_location,
                override_or_use_default_value(default_value, override),
            )
        return self

    def __exit__(self, _exc_type: Any, _exc_val: Any, _exc_tb: Any) -> None:
        for property_name in self.overrides:
            info = self.values_with_defaults[property_name]
            if info["skip_overriding"]:
                continue
            set_nested_attr(
                self,
                info["default_location"],
                info["default_value_to_restore"],
            )


def is_library_available(name: str) -> bool:
    """Return whether an optional package appears importable without importing it."""

    import sys

    return name in sys.modules or importlib.util.find_spec(name) is not None


def _torch_version_tuple() -> tuple[int, ...]:
    """Parse ``torch.__version__`` into ``(major, minor)``."""

    torch = _require_torch()
    return tuple(int(value) for value in torch.__version__.split("+")[0].split(".")[:2])


def get_device() -> str:
    """Return the best available device following TransformerLens' MPS opt-in policy."""

    torch = _torch_module()
    if torch is None:
        return "cpu"
    if torch.cuda.is_available():
        return "cuda"
    mps = getattr(getattr(torch, "backends", None), "mps", None)
    if mps is not None and mps.is_available() and mps.is_built():
        major_version = int(torch.__version__.split(".")[0])
        if major_version >= 2 and os.environ.get("TRANSFORMERLENS_ALLOW_MPS", "") == "1":
            return "mps"
    return "cpu"


def warn_if_mps(device: Any) -> None:
    """Emit TransformerLens-style warnings for MPS devices."""

    global _mps_warned, _mps_broken_torch_warned
    torch = _torch_module()
    if torch is None:
        return
    if isinstance(device, torch.device):
        device = device.type
    if not (isinstance(device, str) and device == "mps"):
        return

    if _torch_version_tuple() in _MPS_BROKEN_TORCH_VERSIONS and not _mps_broken_torch_warned:
        _mps_broken_torch_warned = True
        warnings.warn(
            f"PyTorch {torch.__version__} has a known MPS correctness bug. Upgrade torch.",
            UserWarning,
            stacklevel=2,
        )
    if _mps_warned:
        return
    if (
        _MPS_MIN_SAFE_TORCH_VERSION is not None
        and _torch_version_tuple() >= _MPS_MIN_SAFE_TORCH_VERSION
    ):
        return
    if os.environ.get("TRANSFORMERLENS_ALLOW_MPS", "") != "1":
        _mps_warned = True
        warnings.warn(
            f"MPS backend may produce silently incorrect results (PyTorch {torch.__version__}).",
            UserWarning,
            stacklevel=2,
        )


def move_to_and_update_config(
    model: Any,
    device_or_dtype: Any,
    print_details: bool = True,
) -> Any:
    """Move a torch module and update ``model.cfg.device`` or ``model.cfg.dtype``."""

    torch = _require_torch()
    cfg = getattr(model, "cfg", None)
    if isinstance(device_or_dtype, torch.device):
        warn_if_mps(device_or_dtype)
        if cfg is not None:
            cfg.device = device_or_dtype.type
        if print_details:
            print("Moving model to device: ", getattr(cfg, "device", device_or_dtype.type))
    elif isinstance(device_or_dtype, str):
        warn_if_mps(device_or_dtype)
        if cfg is not None:
            cfg.device = device_or_dtype
        if print_details:
            print("Moving model to device: ", getattr(cfg, "device", device_or_dtype))
    elif isinstance(device_or_dtype, torch.dtype):
        if cfg is not None and hasattr(cfg, "dtype"):
            cfg.dtype = device_or_dtype
        if print_details:
            print("Changing model dtype to", device_or_dtype)

    to_fn = getattr(model, "to", None)
    if callable(to_fn):
        return to_fn(device_or_dtype)
    return model


def print_gpu_mem() -> None:
    """Print currently allocated CUDA memory, or a CPU-only message."""

    torch = _torch_module()
    if torch is None or not torch.cuda.is_available():
        print("CUDA is not available.")
        return
    allocated = torch.cuda.memory_allocated() / (1024**3)
    reserved = torch.cuda.memory_reserved() / (1024**3)
    print(f"Allocated: {allocated:.2f} GB, Reserved: {reserved:.2f} GB")


def get_rotary_pct_from_config(config: Any) -> float:
    """Return rotary percentage from legacy ``rotary_pct`` or v5 rope parameters."""

    if config is None:
        return 1.0
    if isinstance(config, dict):
        if "rotary_pct" in config:
            return config.get("rotary_pct", 1.0)
        rope_params = config.get("rope_parameters")
        if isinstance(rope_params, dict) and "partial_rotary_factor" in rope_params:
            return rope_params["partial_rotary_factor"]
        return 1.0
    if hasattr(config, "rotary_pct"):
        return getattr(config, "rotary_pct", 1.0)
    rope_params = getattr(config, "rope_parameters", None)
    if isinstance(rope_params, dict) and "partial_rotary_factor" in rope_params:
        return rope_params["partial_rotary_factor"]
    return 1.0


def select_compatible_kwargs(kwargs_dict: dict[str, Any], callable: Any) -> dict[str, Any]:
    """Keep kwargs accepted by a callable's explicit argument list."""

    return {
        key: value
        for key, value in kwargs_dict.items()
        if key in inspect.getfullargspec(callable).args
    }


def call_hf_with_retry(
    func: Any,
    *args: Any,
    max_attempts: int = _HF_RETRY_MAX_ATTEMPTS,
    base_delay: float = _HF_RETRY_BASE_DELAY_SECONDS,
    **kwargs: Any,
) -> Any:
    """Call a HuggingFace function, retrying HTTP 429 responses with backoff."""

    for attempt in range(max_attempts):
        try:
            return func(*args, **kwargs)
        except Exception as exc:
            if not _is_hf_rate_limit_error(exc) or attempt == max_attempts - 1:
                raise
            wait = _retry_after_seconds(exc)
            if wait is None:
                wait = min(base_delay * (2**attempt), _HF_RETRY_MAX_DELAY_SECONDS)
                wait *= 0.8 + 0.4 * random.random()
            logger.warning(
                "HuggingFace Hub rate-limited (HTTP 429); retrying in %.1fs "
                "(attempt %d/%d)",
                wait,
                attempt + 1,
                max_attempts,
            )
            time.sleep(wait)
    raise RuntimeError("call_hf_with_retry exited without returning or raising.")


def enable_hf_retry() -> None:
    """Globally wrap common transformers Auto*.from_pretrained calls with HTTP-429 retry."""

    try:
        from transformers import (
            AutoConfig,
            AutoFeatureExtractor,
            AutoModel,
            AutoProcessor,
            AutoTokenizer,
        )
    except ModuleNotFoundError as exc:
        raise ImportError("transformers is required for enable_hf_retry().") from exc

    for cls in (AutoConfig, AutoModel, AutoTokenizer, AutoProcessor, AutoFeatureExtractor):
        original = cls.from_pretrained
        if getattr(original, _TL_RETRY_WRAPPED_ATTR, False):
            continue
        underlying = original.__func__ if hasattr(original, "__func__") else original

        def _wrapped(klass: Any, *args: Any, _orig: Any = underlying, **kwargs: Any) -> Any:
            return call_hf_with_retry(_orig, klass, *args, **kwargs)

        setattr(_wrapped, _TL_RETRY_WRAPPED_ATTR, True)
        cls.from_pretrained = classmethod(_wrapped)


def get_hf_token() -> str | None:
    """Return the HuggingFace token from ``HF_TOKEN`` when one is configured."""

    return os.environ.get("HF_TOKEN", "") or None


def download_file_from_hf(
    repo_name: str,
    file_name: str,
    subfolder: str = ".",
    cache_dir: Any = None,
    force_is_torch: bool = False,
    **kwargs: Any,
) -> Any:
    """Download a file from HuggingFace Hub and load JSON/Torch files when appropriate."""

    try:
        from huggingface_hub import hf_hub_download
    except ModuleNotFoundError as exc:
        raise ImportError("huggingface_hub is required for download_file_from_hf().") from exc

    if cache_dir is None:
        cache_dir = _hf_cache_dir()
    file_path = call_hf_with_retry(
        hf_hub_download,
        repo_id=repo_name,
        filename=file_name,
        subfolder=subfolder,
        cache_dir=cache_dir,
        **select_compatible_kwargs(kwargs, hf_hub_download),
    )

    if file_path.endswith(".pth") or force_is_torch:
        torch = _require_torch()
        return torch.load(file_path, map_location="cpu", weights_only=False)
    if file_path.endswith(".json"):
        with open(file_path) as file:
            return json.load(file)
    print("File type not supported:", file_path.split(".")[-1])
    return file_path


def clear_huggingface_cache() -> None:
    """Delete the HuggingFace Hub cache directory, ignoring common race-condition errors."""

    cache_dir = _hf_cache_dir()
    print("Deleting Hugging Face cache directory and all its contents.")
    if not os.path.exists(cache_dir):
        return

    def handle_remove_readonly(func: Any, path: str, exc_info: Any) -> None:
        excvalue = exc_info[1]
        if isinstance(excvalue, FileNotFoundError):
            return
        if isinstance(excvalue, OSError) and excvalue.errno in {errno.ENOTEMPTY, errno.ENOENT}:
            return
        if os.path.exists(path) and not os.access(path, os.W_OK):
            try:
                os.chmod(path, stat.S_IWUSR)
                func(path)
            except (OSError, FileNotFoundError):
                return
        else:
            raise excvalue

    try:
        shutil.rmtree(cache_dir, onerror=handle_remove_readonly)
    except FileNotFoundError:
        pass
    except OSError as exc:
        if exc.errno not in {errno.ENOTEMPTY, errno.ENOENT}:
            print(f"Warning: Could not fully clear cache: {exc}")


def keep_single_column(dataset: Any, col_name: str) -> Any:
    """Return a dataset with all columns except ``col_name`` removed when supported."""

    features = getattr(dataset, "features", {})
    for key in list(features):
        if key != col_name:
            dataset = dataset.remove_columns(key)
    return dataset


def get_dataset(dataset_name: str, **kwargs: Any) -> Any:
    """Load one of TransformerLens' small convenience HuggingFace datasets."""

    try:
        from datasets import load_dataset
    except ModuleNotFoundError as exc:
        raise ImportError("datasets is required for get_dataset().") from exc

    dataset_aliases = {
        "openwebtext": "stas/openwebtext-10k",
        "owt": "stas/openwebtext-10k",
        "pile": "NeelNanda/pile-10k",
        "c4": "NeelNanda/c4-10k",
        "code": "NeelNanda/code-10k",
        "python": "NeelNanda/code-10k",
        "c4_code": "NeelNanda/c4-code-20k",
        "c4-code": "NeelNanda/c4-code-20k",
        "wiki": "NeelNanda/wiki-10k",
    }
    if dataset_name not in dataset_aliases:
        raise ValueError(f"Dataset {dataset_name} not supported")
    return load_dataset(dataset_aliases[dataset_name], split="train", **kwargs)


def vanilla_addmm(input: Any, mat1: Any, mat2: Any) -> Any:
    """TransformerLens-compatible wrapper around ``torch.addmm``."""

    torch = _require_torch()
    return torch.addmm(input, mat1, mat2)


def batch_addmm(bias: Any, weight: Any, x: Any) -> Any:
    """Fused add-multiply matching HuggingFace Conv1D's batched shape behavior."""

    n_output_features = weight.shape[-1]
    size_out = x.size()[:-1] + (n_output_features,)
    x = vanilla_addmm(bias, x.view(-1, x.size(-1)), weight)
    return x.view(size_out)


def simple_attn_linear(input: Any, w: Any, b: Any) -> Any:
    """Attention linear helper for ``[batch, pos, d_model]`` inputs."""

    torch = _require_torch()
    if input.device != w.device:
        w = w.to(input.device)
    if input.device != b.device:
        b = b.to(input.device)
    n_heads, _d_model, d_head = w.shape
    weight = w.permute(0, 2, 1).reshape(n_heads * d_head, _d_model)
    bias = b.reshape(n_heads * d_head)
    output = torch.nn.functional.linear(input, weight, bias)
    return output.reshape(*input.shape[:-1], n_heads, d_head)


def complex_attn_linear(input: Any, w: Any, b: Any) -> Any:
    """Attention linear helper for ``[..., head_index, d_model]`` inputs."""

    torch = _require_torch()
    if input.device != w.device:
        w = w.to(input.device)
    if input.device != b.device:
        b = b.to(input.device)
    return torch.einsum("...hd,hde->...he", input, w) + b


def get_matrix_corner(matrix: Any, n: int = 3) -> Any:
    """Return the dense top-left corner of a FactoredMatrix-like object."""

    from SafeLens.core.tensors import get_corner

    ndim = getattr(matrix, "ndim", None)
    if ndim is None:
        shape = getattr(matrix, "shape", None)
        ndim = len(shape) if shape is not None else 0
    if ndim:
        try:
            result = matrix[tuple(slice(n) for _ in range(int(ndim)))]
            dense = getattr(result, "AB", None)
            return dense if dense is not None else get_corner(result, n)
        except Exception:
            pass
    dense = getattr(matrix, "AB", None)
    return get_corner(dense if dense is not None else matrix, n)


def get_input_with_manually_prepended_bos(bos_token: str, input: str | list[str]) -> str | list[str]:
    """Prepend a BOS token string to one string or a list of strings."""

    if isinstance(input, str):
        return bos_token + input
    return [bos_token + string for string in input]


def get_tokenizer_with_bos(tokenizer: Any) -> Any:
    """Return a tokenizer configured to add BOS when this can be done locally."""

    if getattr(tokenizer, "bos_token", None) is None or getattr(tokenizer, "add_bos_token", False):
        return tokenizer

    init_kwargs = deepcopy(getattr(tokenizer, "init_kwargs", {}))
    pretrained_model_name_or_path = init_kwargs.pop("name_or_path", None)
    init_kwargs.pop("add_bos_token", None)
    if pretrained_model_name_or_path is not None:
        try:
            from transformers import AutoTokenizer

            huggingface_token = os.environ.get("HF_TOKEN", "")
            tokenizer_with_bos = AutoTokenizer.from_pretrained(
                pretrained_model_name_or_path,
                add_bos_token=True,
                token=huggingface_token if huggingface_token else None,
                **init_kwargs,
            )
            tokenizer_with_bos.padding_side = getattr(tokenizer, "padding_side", "right")
            return tokenizer_with_bos
        except Exception:
            pass

    tokenizer = deepcopy(tokenizer)
    try:
        setattr(tokenizer, "add_bos_token", True)
    except Exception:
        pass
    return tokenizer


def get_tokens_with_bos_removed(tokenizer: Any, tokens: Any) -> Any:
    """Remove one BOS token from the sequence dimension."""

    if getattr(tokenizer, "padding_side", "right") == "right":
        return _slice_last_dim(tokens, slice(1, None))

    torch = _torch_module()
    if torch is not None and isinstance(tokens, torch.Tensor):
        bos_removed_shape = list(tokens.shape)
        bos_removed_shape[-1] -= 1
        if getattr(tokenizer, "bos_token_id", None) == getattr(tokenizer, "pad_token_id", None):
            is_not_pad_token = tokens.ne(tokenizer.pad_token_id)
            is_leading_pad = _cumsum_along_dim(is_not_pad_token, -1, reverse=False) == 0
            real_bos_positions = is_leading_pad.sum(-1) - 1
        else:
            real_bos_positions = (tokens == tokenizer.bos_token_id).int().argmax(-1)
        tokens = tokens.scatter(dim=1, index=real_bos_positions.unsqueeze(-1), value=-100)
        return tokens[tokens != -100].view(*bos_removed_shape)

    rows, squeeze = _ensure_2d_rows(tokens)
    bos_id = getattr(tokenizer, "bos_token_id", None)
    pad_id = getattr(tokenizer, "pad_token_id", None)
    output_rows: list[list[Any]] = []
    for row in rows:
        remove_index = 0
        if bos_id == pad_id:
            leading_pads = 0
            for token in row:
                if token != pad_id:
                    break
                leading_pads += 1
            remove_index = max(0, leading_pads - 1)
        elif bos_id in row:
            remove_index = row.index(bos_id)
        output_rows.append(row[:remove_index] + row[remove_index + 1 :])
    return output_rows[0] if squeeze else output_rows


def get_attention_mask(tokenizer: Any, tokens: Any, prepend_bos: bool) -> Any:
    """Compute a TL-style attention mask for right- or left-padded tokens."""

    torch = _torch_module()
    if torch is not None and isinstance(tokens, torch.Tensor):
        attention_mask = torch.ones_like(tokens)
        if tokenizer is None:
            return attention_mask
        is_not_pad_token = tokens.ne(tokenizer.pad_token_id)
        if getattr(tokenizer, "padding_side", "right") == "right":
            is_trailing_pad = _cumsum_along_dim(is_not_pad_token, -1, reverse=True) == 0
            attention_mask[is_trailing_pad] = 0
        else:
            is_leading_pad = _cumsum_along_dim(is_not_pad_token, -1, reverse=False) == 0
            attention_mask[is_leading_pad] = 0
            if prepend_bos and tokenizer.bos_token_id == tokenizer.pad_token_id:
                pad_bos_positions = is_leading_pad.sum(-1) - 1
                attention_mask[torch.arange(attention_mask.shape[0]), pad_bos_positions] = 1
        return attention_mask

    rows, squeeze = _ensure_2d_rows(tokens)
    if tokenizer is None:
        masks = [[1 for _token in row] for row in rows]
        return masks[0] if squeeze else masks
    pad_id = getattr(tokenizer, "pad_token_id", None)
    masks = []
    for row in rows:
        mask = [1] * len(row)
        if getattr(tokenizer, "padding_side", "right") == "right":
            index = len(row) - 1
            while index >= 0 and row[index] == pad_id:
                mask[index] = 0
                index -= 1
        else:
            index = 0
            while index < len(row) and row[index] == pad_id:
                mask[index] = 0
                index += 1
            if prepend_bos and tokenizer.bos_token_id == tokenizer.pad_token_id and index > 0:
                mask[index - 1] = 1
        masks.append(mask)
    return masks[0] if squeeze else masks


def tokenize_and_concatenate(
    dataset: Any,
    tokenizer: Any,
    streaming: bool = False,
    max_length: int = 1024,
    column_name: str = "text",
    add_bos_token: bool = True,
    num_proc: int = 10,
    set_format: bool = True,
) -> Any:
    """Tokenize text documents, concatenate with EOS separators, and chunk into rows."""

    dataset = keep_single_column(dataset, column_name)
    has_pad_token = getattr(tokenizer, "pad_token", None) is not None
    if not has_pad_token and callable(getattr(tokenizer, "add_special_tokens", None)):
        tokenizer.add_special_tokens({"pad_token": "<PAD>"})
    seq_len = max_length - 1 if add_bos_token else max_length

    def tokenize_function(examples: dict[str, Any]) -> dict[str, Any]:
        text = examples[column_name]
        if not text:
            return {"tokens": []}
        encoded = tokenizer(text, add_special_tokens=False)["input_ids"]
        if encoded and not isinstance(encoded[0], (list, tuple)):
            encoded = [encoded]
        pieces: list[int] = []
        for index, row in enumerate(encoded):
            pieces.extend(int(token) for token in row)
            if index < len(encoded) - 1:
                pieces.append(int(tokenizer.eos_token_id))
        if len(pieces) < seq_len:
            padding_id = tokenizer.eos_token_id if not has_pad_token else tokenizer.pad_token_id
            pieces = pieces + [int(padding_id)] * (seq_len - len(pieces))
        else:
            rows_to_keep = max(1, len(pieces) // seq_len)
            pieces = pieces[: seq_len * rows_to_keep]
        rows = [pieces[index : index + seq_len] for index in range(0, len(pieces), seq_len)]
        if add_bos_token:
            rows = [[int(tokenizer.bos_token_id), *row] for row in rows]
        return {"tokens": rows}

    map_kwargs: dict[str, Any] = {"batched": True, "remove_columns": [column_name]}
    if not streaming:
        map_kwargs["num_proc"] = num_proc
    tokenized_dataset = dataset.map(tokenize_function, **map_kwargs)
    if set_format and callable(getattr(tokenized_dataset, "set_format", None)):
        tokenized_dataset.set_format(type="torch", columns=["tokens"])
    return tokenized_dataset


def calculate_available_device_cuda_memory(i: int) -> int:
    """Return currently available CUDA memory for device index ``i``."""

    torch = _require_torch()
    total = torch.cuda.get_device_properties(i).total_memory
    allocated = torch.cuda.memory_allocated(i)
    return int(total - allocated)


def determine_available_memory_for_available_devices(max_devices: int) -> list[tuple[int, int]]:
    """Return ``(device_index, available_memory)`` for visible CUDA devices."""

    return [(index, calculate_available_device_cuda_memory(index)) for index in range(max_devices)]


def sort_devices_based_on_available_memory(devices: list[tuple[int, int]]) -> list[tuple[int, int]]:
    """Sort devices with the most available memory first."""

    return sorted(devices, key=lambda item: item[1], reverse=True)


def get_best_available_cuda_device(max_devices: int | None = None) -> Any:
    """Return the CUDA device with the most currently available memory."""

    torch = _require_torch()
    max_devices = torch.cuda.device_count() if max_devices is None else max_devices
    devices = determine_available_memory_for_available_devices(max_devices)
    if not devices:
        raise EnvironmentError(
            "TransformerLens has been configured to use CUDA, but no available devices are present"
        )
    return torch.device("cuda", sort_devices_based_on_available_memory(devices)[0][0])


def get_best_available_device(cfg: Any) -> Any:
    """Return the best device for a TL-style config object."""

    torch = _require_torch()
    assert cfg.device is not None
    device = torch.device(cfg.device)
    if device.type == "cuda" and getattr(cfg, "n_devices", 1) > 1:
        return get_best_available_cuda_device(cfg.n_devices)
    return device


def get_device_for_block_index(index: int, cfg: Any, device: Any | None = None) -> Any:
    """Return the device assigned to a transformer block index."""

    torch = _require_torch()
    assert cfg.device is not None
    layers_per_device = cfg.n_layers // cfg.n_devices
    resolved_device = torch.device(cfg.device if device is None else device)
    if resolved_device.type == "cpu":
        return resolved_device
    device_index = (resolved_device.index or 0) + (index // layers_per_device)
    return torch.device(resolved_device.type, device_index)


def resolve_device_map(
    n_devices: int | None,
    device_map: str | dict[str, str | int] | None,
    device: str | Any | None,
    max_memory: dict[str | int, str] | None = None,
) -> tuple[str | dict[str, str | int] | None, dict[str | int, str] | None]:
    """Resolve TL-style ``n_devices`` / ``device_map`` / ``device`` arguments."""

    if device_map is not None and device is not None:
        raise ValueError("device and device_map are mutually exclusive - pass one.")
    if device_map is not None:
        _validate_device_map_values(device_map)
        return device_map, max_memory
    if n_devices is None or n_devices <= 1:
        return None, max_memory

    torch = _require_torch()
    if not torch.cuda.is_available():
        raise ValueError(f"n_devices={n_devices} requires CUDA, which is not available.")
    if torch.cuda.device_count() < n_devices:
        raise ValueError(
            f"n_devices={n_devices} but only {torch.cuda.device_count()} CUDA devices present."
        )
    resolved_max_memory = dict(max_memory) if max_memory else {index: "auto" for index in range(n_devices)}
    return "balanced", resolved_max_memory


def find_embedding_device(hf_model: Any) -> Any | None:
    """Return the input embedding device for a dispatched HuggingFace model."""

    hf_device_map = getattr(hf_model, "hf_device_map", None)
    if not hf_device_map:
        return None
    torch = _require_torch()
    get_input_embeddings = getattr(hf_model, "get_input_embeddings", None)
    if callable(get_input_embeddings):
        try:
            embed_module = get_input_embeddings()
        except (AttributeError, NotImplementedError):
            embed_module = None
        if embed_module is not None:
            try:
                param = next(embed_module.parameters())
                return param.device
            except StopIteration:
                pass
    first_device = next(iter(hf_device_map.values()))
    if isinstance(first_device, int):
        return torch.device("cuda", first_device)
    return torch.device(first_device)


def count_unique_devices(hf_model: Any) -> int:
    """Count unique devices in ``hf_model.hf_device_map``, defaulting to one."""

    hf_device_map = getattr(hf_model, "hf_device_map", None)
    if not hf_device_map:
        return 1
    return len(set(hf_device_map.values()))


def _validate_device_map_values(device_map: str | dict[str, str | int]) -> None:
    if isinstance(device_map, str):
        return
    for key, value in device_map.items():
        normalized = str(value).lower() if isinstance(value, str) else None
        if normalized in {"cpu", "disk", "meta"}:
            raise ValueError(
                f"device_map[{key!r}]={value!r} is not supported. Multi-device bridge "
                "support is GPU-only in v1; CPU / disk / meta offload routes are excluded."
            )


def calc_fan_in_and_fan_out(tensor: Any) -> tuple[int, int]:
    """Calculate fan-in/out using TransformerLens weight-shape conventions."""

    shape = tuple(int(dim) for dim in getattr(tensor, "shape", ()))
    if len(shape) == 0:
        raise ValueError("Fan in and fan out can not be computed for scalars.")
    if len(shape) == 1:
        return 1, shape[0]
    if len(shape) == 2:
        return shape[0], shape[1]
    if len(shape) == 3:
        return shape[1], shape[0] * shape[2]
    raise ValueError(f"Fan in and fan out can not be computed for shape {shape} tensors.")


def init_xavier_uniform_(param: Any, gain: float = 1.0) -> Any:
    """Initialize with TL-style Xavier uniform bounds."""

    torch = _require_torch()
    fan_in, fan_out = calc_fan_in_and_fan_out(param)
    bound = gain * math.sqrt(6.0 / (fan_in + fan_out))
    return torch.nn.init.uniform_(param, -bound, bound)


def init_xavier_normal_(param: Any, gain: float = 1.0) -> Any:
    """Initialize with TL-style Xavier normal std."""

    torch = _require_torch()
    fan_in, fan_out = calc_fan_in_and_fan_out(param)
    std = gain * math.sqrt(2.0 / (fan_in + fan_out))
    return torch.nn.init.normal_(param, mean=0.0, std=std)


def init_kaiming_uniform_(
    param: Any,
    a: float = 0,
    nonlinearity: NonlinearityType = "relu",
    gain: float = 1.0,
    mode: str = "fan_in",
) -> Any:
    """Initialize with TL-style Kaiming uniform bounds."""

    torch = _require_torch()
    fan_in, fan_out = calc_fan_in_and_fan_out(param)
    fan = fan_in if mode == "fan_in" else fan_out
    gain *= torch.nn.init.calculate_gain(nonlinearity, a)
    bound = gain * math.sqrt(3.0 / fan)
    return torch.nn.init.uniform_(param, -bound, bound)


def init_kaiming_normal_(
    param: Any,
    a: float = 0,
    nonlinearity: NonlinearityType = "relu",
    gain: float = 1.0,
    mode: str = "fan_in",
) -> Any:
    """Initialize with TL-style Kaiming normal std."""

    torch = _require_torch()
    fan_in, fan_out = calc_fan_in_and_fan_out(param)
    fan = fan_in if mode == "fan_in" else fan_out
    gain *= torch.nn.init.calculate_gain(nonlinearity, a)
    std = gain * math.sqrt(1.0 / fan)
    return torch.nn.init.normal_(param, mean=0.0, std=std)


def _torch_module() -> Any | None:
    try:
        import torch
    except ModuleNotFoundError:
        return None
    return torch


def _require_torch() -> Any:
    torch = _torch_module()
    if torch is None:
        raise ImportError("torch is required for this utility.")
    return torch


def _hf_cache_dir() -> str:
    try:
        from huggingface_hub.constants import HF_HUB_CACHE

        return str(HF_HUB_CACHE)
    except ModuleNotFoundError:
        return os.path.expanduser("~/.cache/huggingface/hub")


def _is_hf_rate_limit_error(exc: BaseException) -> bool:
    response = getattr(exc, "response", None)
    return response is not None and getattr(response, "status_code", None) == 429


def _retry_after_seconds(exc: BaseException) -> float | None:
    response = getattr(exc, "response", None)
    if response is None:
        return None
    headers = getattr(response, "headers", None) or {}
    raw = headers.get("Retry-After") if hasattr(headers, "get") else None
    if raw is None:
        return None
    try:
        return float(raw)
    except (TypeError, ValueError):
        return None


def _cumsum_along_dim(tensor: Any, dim: int, reverse: bool = False) -> Any:
    from SafeLens.core.tensors import get_cumsum_along_dim

    return get_cumsum_along_dim(tensor, dim, reverse=reverse)


def _slice_last_dim(value: Any, index: slice) -> Any:
    shape = getattr(value, "shape", None)
    if shape is not None:
        return value[(slice(None),) * (len(shape) - 1) + (index,)]
    if not isinstance(value, list):
        return value
    if value and isinstance(value[0], list):
        return [_slice_last_dim(item, index) for item in value]
    return value[index]


def _ensure_2d_rows(tokens: Any) -> tuple[list[list[Any]], bool]:
    tolist = getattr(tokens, "tolist", None)
    if callable(tolist):
        tokens = tolist()
    if not isinstance(tokens, list):
        return [[tokens]], True
    if tokens and isinstance(tokens[0], list):
        return [list(row) for row in tokens], False
    return [list(tokens)], True

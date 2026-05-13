# KV Cache

`KeyValueCache` and `KeyValueCacheEntry` provide small containers for
autoregressive key/value activations. They are intentionally simple so model
adapters can expose cache state without binding SafeLens to a specific
transformers implementation.

Supported operations:

- Lazy per-layer entry creation through `cache[layer]`.
- Sequence-axis append through `append(layer, keys, values)`.
- Best-effort `sequence_length` inference for tensor-like and nested-list data.
- Serialization-friendly `to_dict()`.

Example:

```python
from SafeLens.core.kv_cache import KeyValueCache

cache = KeyValueCache()
cache.append(0, keys=[[[1]]], values=[[[2]]])
cache.append(0, keys=[[[3]]], values=[[[4]]])

assert cache[0].keys == [[[1], [3]]]
assert cache[0].sequence_length == 2
```

::: SafeLens.core.kv_cache

# Hooked Root

`HookedRoot` is SafeLens' dependency-free equivalent of a TransformerLens-style
root hook manager. It is useful when a model adapter exposes many named
`HookPoint` objects and needs one place to add, remove, cache, and validate hooks.

Supported operations:

- Register hook points with `setup()` or `add_hook_point()`.
- Add one hook with `check_and_add_hook()`.
- Add hooks by exact name, list, or predicate with `add_hook()`.
- Add permanent hooks with `add_perma_hook()`.
- Remove hooks globally with `remove_all_hook_fns()` or `reset_hooks()`.
- Clear hook contexts with `clear_contexts()`.
- Create or install activation cache hooks with `get_caching_hooks()` and
  `add_caching_hooks()`.
- Run arbitrary callables with temporary hooks using `run_with_hooks()`.

Example:

```python
from SafeLens.core.hooked_root import HookedRoot

root = HookedRoot()
resid = root.add_hook_point("blocks.0.hook_resid_pre")

with root.hooks(
    fwd_hooks=[
        ("blocks.0.hook_resid_pre", lambda activation, hook: activation + [1])
    ]
):
    assert resid([0]) == [0, 1]

assert resid([0]) == [0]
```

Caching example:

```python
from SafeLens.core.hooked_root import HookedRoot

root = HookedRoot()
resid = root.add_hook_point("blocks.0.hook_resid_pre")
cache = root.add_caching_hooks(lambda name: "resid" in name)

resid([1, 2, 3])
assert cache["blocks.0.hook_resid_pre"] == [1, 2, 3]
```

`get_caching_hooks()` returns a live `ActivationCache` plus hook specs. The
returned cache is updated by the generated hooks:

```python
cache, fwd_hooks, _ = root.get_caching_hooks("blocks.0.hook_resid_pre")

with root.hooks(fwd_hooks=fwd_hooks):
    resid([4, 5, 6])

assert cache["blocks.0.hook_resid_pre"] == [4, 5, 6]
```

::: SafeLens.core.hooked_root

"""Signature-aware helpers for calling user hook functions."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from inspect import Parameter, signature
from typing import Any, Literal

from SafeLens.core.base import HookFn

UninspectableCall = Literal["kwargs", "first_positional"]


def call_user_hook(
    hook_fn: HookFn,
    hook_kwargs: Mapping[str, Any],
    *,
    positional_arg_options: Sequence[tuple[Any, ...]] = (),
    uninspectable: UninspectableCall = "first_positional",
) -> Any:
    """Call a hook without using user-raised TypeError as fallback control flow."""
    kwargs = dict(hook_kwargs)
    try:
        hook_signature = signature(hook_fn)
    except (TypeError, ValueError):
        if uninspectable == "kwargs" or not positional_arg_options:
            return hook_fn(**kwargs)
        return hook_fn(*positional_arg_options[0])

    call_args, call_kwargs = _select_hook_call(hook_signature, kwargs, positional_arg_options)
    return hook_fn(*call_args, **call_kwargs)


def _select_hook_call(
    hook_signature: Any,
    hook_kwargs: dict[str, Any],
    positional_arg_options: Sequence[tuple[Any, ...]],
) -> tuple[tuple[Any, ...], dict[str, Any]]:
    if positional_arg_options and _prefers_positional_options(hook_signature):
        positional_call = _select_positional_call(
            hook_signature,
            hook_kwargs,
            positional_arg_options,
        )
        if positional_call is not None:
            return positional_call

    keyword_kwargs = _keyword_kwargs_for_signature(
        hook_signature,
        hook_kwargs,
        positional_arg_count=0,
    )
    if _can_bind(hook_signature, (), keyword_kwargs):
        return (), keyword_kwargs

    positional_call = _select_positional_call(
        hook_signature,
        hook_kwargs,
        positional_arg_options,
    )
    if positional_call is not None:
        return positional_call

    if positional_arg_options:
        return tuple(positional_arg_options[0]), {}
    return (), keyword_kwargs


def _select_positional_call(
    hook_signature: Any,
    hook_kwargs: dict[str, Any],
    positional_arg_options: Sequence[tuple[Any, ...]],
) -> tuple[tuple[Any, ...], dict[str, Any]] | None:
    seen: set[tuple[int, tuple[str, ...]]] = set()
    for positional_args in positional_arg_options:
        args = tuple(positional_args)
        keyword_variants = (
            _keyword_kwargs_for_signature(
                hook_signature,
                hook_kwargs,
                positional_arg_count=len(args),
            ),
            {},
        )
        for candidate_kwargs in keyword_variants:
            key = (len(args), tuple(candidate_kwargs))
            if key in seen:
                continue
            seen.add(key)
            if _can_bind(hook_signature, args, candidate_kwargs):
                return args, candidate_kwargs

    return None


def _prefers_positional_options(hook_signature: Any) -> bool:
    parameters = list(hook_signature.parameters.values())
    return any(
        parameter.kind == Parameter.VAR_POSITIONAL
        for parameter in parameters
    ) and not any(parameter.kind == Parameter.VAR_KEYWORD for parameter in parameters)


def _keyword_kwargs_for_signature(
    hook_signature: Any,
    hook_kwargs: dict[str, Any],
    *,
    positional_arg_count: int,
) -> dict[str, Any]:
    parameters = list(hook_signature.parameters.values())
    if any(param.kind == Parameter.VAR_KEYWORD for param in parameters):
        kwargs = dict(hook_kwargs)
    else:
        accepted_names = {
            param.name
            for param in parameters
            if param.kind in (Parameter.POSITIONAL_OR_KEYWORD, Parameter.KEYWORD_ONLY)
        }
        kwargs = {name: value for name, value in hook_kwargs.items() if name in accepted_names}

    for name in _consumed_positional_or_keyword_names(parameters, positional_arg_count):
        kwargs.pop(name, None)
    return kwargs


def _consumed_positional_or_keyword_names(
    parameters: Sequence[Parameter],
    positional_arg_count: int,
) -> list[str]:
    consumed: list[str] = []
    remaining = positional_arg_count
    for param in parameters:
        if remaining <= 0:
            break
        if param.kind == Parameter.POSITIONAL_OR_KEYWORD:
            consumed.append(param.name)
            remaining -= 1
        elif param.kind == Parameter.POSITIONAL_ONLY:
            remaining -= 1
        elif param.kind == Parameter.VAR_POSITIONAL:
            break
    return consumed


def _can_bind(hook_signature: Any, args: tuple[Any, ...], kwargs: dict[str, Any]) -> bool:
    try:
        hook_signature.bind(*args, **kwargs)
    except TypeError:
        return False
    return True

"""Registered public Jacobian Lens checkpoints used by Explorer."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class JLensProfile:
    """A model-specific, immutable Jacobian Lens artifact manifest."""

    name: str
    base_model: str
    source: str
    filename: str
    revision: str
    d_model: int
    source_layers: tuple[int, ...]
    default_layer: int
    n_prompts: int
    description: str


QWEN25_7B_INSTRUCT_JLENS = JLensProfile(
    name="qwen2.5-7b-instruct-wikitext",
    base_model="Qwen/Qwen2.5-7B-Instruct",
    source="neuronpedia/jacobian-lens",
    filename=("qwen2.5-7b-it/jlens/Salesforce-wikitext/" "Qwen2.5-7B-Instruct_jacobian_lens.pt"),
    revision="4f30bb8c97e696115d4a2ef359923b5005fc860c",
    d_model=3584,
    source_layers=tuple(range(27)),
    default_layer=20,
    n_prompts=485,
    description=(
        "Neuronpedia's public Qwen2.5-7B-Instruct Jacobian Lens fitted on "
        "WikiText-103; L20 aligns with the released Qwen NLA profile."
    ),
)

JLENS_SUPPORTED_PROFILES = (QWEN25_7B_INSTRUCT_JLENS,)


def list_jlens_profiles() -> list[dict[str, Any]]:
    """Return JSON-ready manifests for Explorer model-specific defaults."""

    profiles: list[dict[str, Any]] = []
    for profile in JLENS_SUPPORTED_PROFILES:
        item = asdict(profile)
        item["baseModel"] = item.pop("base_model")
        item["dModel"] = item.pop("d_model")
        item["sourceLayers"] = list(item.pop("source_layers"))
        item["defaultLayer"] = item.pop("default_layer")
        item["nPrompts"] = item.pop("n_prompts")
        profiles.append(item)
    return profiles


def find_jlens_profile(
    source: str,
    filename: str,
) -> JLensProfile | None:
    """Find the registered manifest for a remote artifact reference."""

    normalized_source = source.strip().rstrip("/")
    normalized_filename = filename.strip().lstrip("/")
    return next(
        (
            profile
            for profile in JLENS_SUPPORTED_PROFILES
            if profile.source == normalized_source and profile.filename == normalized_filename
        ),
        None,
    )

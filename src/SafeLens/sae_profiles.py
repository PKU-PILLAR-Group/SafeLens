"""Validated Sparse Autoencoder profiles exposed by the local Explorer."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Literal

GEMMA_SCOPE_2_270M_IT_MODEL = "google/gemma-3-270m-it"
GEMMA_SCOPE_2_270M_IT_RELEASE = "gemma-scope-2-270m-it-res"


@dataclass(frozen=True)
class SAEProfile:
    """One exact base-model, activation-site, and SAE checkpoint combination."""

    id: str
    label: str
    model_name: str
    release: str
    sae_id: str
    layer: int
    component: Literal["resid_post"]
    width: int
    architecture: Literal["jump_relu"]
    source: str

    def to_api(self) -> dict[str, object]:
        payload = asdict(self)
        payload["modelName"] = payload.pop("model_name")
        payload["saeId"] = payload.pop("sae_id")
        return payload


GEMMA_SCOPE_2_PROFILES = tuple(
    SAEProfile(
        id=f"gemma-scope-2-270m-it-resid-post-l{layer}-16k-small",
        label=f"Gemma Scope 2 · L{layer} · residual · 16k · L0 small",
        model_name=GEMMA_SCOPE_2_270M_IT_MODEL,
        release=GEMMA_SCOPE_2_270M_IT_RELEASE,
        sae_id=f"layer_{layer}_width_16k_l0_small",
        layer=layer,
        component="resid_post",
        width=16_384,
        architecture="jump_relu",
        source="google/gemma-scope-2-270m-it",
    )
    for layer in (5, 9, 12, 15)
)


def list_sae_profiles(*, model_name: str | None = None) -> tuple[SAEProfile, ...]:
    """Return the Explorer-supported SAE profiles, optionally filtered by base model."""
    if model_name is None:
        return GEMMA_SCOPE_2_PROFILES
    return tuple(profile for profile in GEMMA_SCOPE_2_PROFILES if profile.model_name == model_name)


def get_sae_profile(
    *,
    model_name: str,
    release: str,
    sae_id: str,
) -> SAEProfile | None:
    """Resolve only an exact allow-listed model/checkpoint combination."""
    return next(
        (
            profile
            for profile in GEMMA_SCOPE_2_PROFILES
            if profile.model_name == model_name
            and profile.release == release
            and profile.sae_id == sae_id
        ),
        None,
    )

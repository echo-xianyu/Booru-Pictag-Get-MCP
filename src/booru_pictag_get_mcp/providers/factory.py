"""Booru provider factory — mirrored after lib/booru/factory.ts."""

from __future__ import annotations

from ..models import ProviderType
from .base import (
    BaseBooruProvider,
    DanbooruProvider,
    AibooruProvider,
    E621Provider,
    GelbooruProvider,
    Rule34Provider,
)


def get_provider(name: ProviderType) -> BaseBooruProvider:
    p = (name or "").lower()
    if p == "danbooru":
        return DanbooruProvider()
    if p == "aibooru":
        return AibooruProvider()
    if p == "e621":
        return E621Provider()
    if p == "gelbooru":
        return GelbooruProvider()
    if p == "rule34":
        return Rule34Provider()
    raise ValueError(f"Unknown provider type: {name}")
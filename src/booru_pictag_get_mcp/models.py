"""Shared data models."""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Literal, Optional


ProviderType = Literal["danbooru", "aibooru", "e621", "gelbooru", "rule34"]
OrderType = Literal["popular", "recent", "random"]
RatingFilter = Literal["all", "safe"]


@dataclass
class AiMetadata:
    prompt: Optional[str] = None
    negative_prompt: Optional[str] = None
    model: Optional[str] = None
    steps: Optional[int] = None
    cfg_scale: Optional[float] = None
    sampler: Optional[str] = None
    seed: Optional[int] = None


@dataclass
class BooruPost:
    id: int
    file_url: str = ""
    large_file_url: str = ""
    preview_file_url: str = ""
    tag_string: str = ""
    tag_string_artist: str = ""
    tag_string_character: str = ""
    tag_string_copyright: str = ""
    tag_string_meta: str = ""
    rating: str = ""
    score: int = 0
    source: Optional[str] = None
    width: int = 0
    height: int = 0
    provider: Optional[str] = None
    ai_metadata: Optional[AiMetadata] = None

    def to_dict(self) -> dict:
        d = asdict(self)
        if self.ai_metadata is None:
            d.pop("ai_metadata", None)
        return d


@dataclass
class SearchOptions:
    tags: str = ""
    page: int = 1
    limit: int = 30
    order: OrderType = "popular"
    has_prompt: bool = False
    rating: RatingFilter = "all"
    random_seed: int = 1


@dataclass
class ClassifiedTags:
    appearance: list = field(default_factory=list)
    clothing: list = field(default_factory=list)
    pose: list = field(default_factory=list)
    scenery: list = field(default_factory=list)
    character: list = field(default_factory=list)
    quality: list = field(default_factory=list)
    other: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)
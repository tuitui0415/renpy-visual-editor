"""Domain types shared by the visual editor core and launcher screens."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import PurePosixPath
from typing import Any, Dict, List, Optional


class ResourceKind(str, Enum):
    BACKGROUND = "background"
    CHARACTER = "character"
    CG = "cg"
    BGM = "bgm"
    SFX = "sfx"


class EventKind(str, Enum):
    SCENE = "scene"
    BACKGROUND = "background"
    CHARACTER = "character"
    CG = "cg"
    TEXT = "text"
    CONTROL = "control"
    CODE = "code"


class AdvanceMode(str, Enum):
    IMMEDIATE = "immediate"
    CLICK = "click"
    AUTO = "auto"
    VIDEO = "video"
    CHOICE = "choice"
    INTERACTION = "interaction"
    CODE = "code"


@dataclass(frozen=True)
class Resource:
    kind: ResourceKind
    relative_path: PurePosixPath

    @property
    def name(self) -> str:
        return self.relative_path.stem


@dataclass(frozen=True)
class ValidationIssue:
    code: str
    message: str
    path: Optional[PurePosixPath] = None
    severity: str = "error"


@dataclass(frozen=True)
class Transform:
    xalign: float = 0.5
    yalign: float = 0.5
    zoom: float = 1.0
    zorder: int = 0


@dataclass
class Attachment:
    kind: str
    note: str = ""
    parameters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Event:
    id: str
    kind: EventKind
    asset: Optional[str] = None
    text: Optional[str] = None
    speaker: Optional[str] = None
    advance: AdvanceMode = AdvanceMode.IMMEDIATE
    note: str = ""
    attachments: List[Attachment] = field(default_factory=list)
    editable: bool = True
    xalign: float = 0.5
    yalign: float = 0.5
    zoom: float = 1.0
    zorder: int = 0


@dataclass
class Scene:
    label: str
    events: List[Event] = field(default_factory=list)
    note: str = ""

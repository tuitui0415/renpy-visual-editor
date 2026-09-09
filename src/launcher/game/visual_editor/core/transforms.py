"""Resource assignment and stage transform operations."""

from __future__ import annotations

from pathlib import PurePosixPath
from typing import Optional

from .model import Attachment, Event, EventKind, ResourceKind, Transform, ValidationIssue
from .resources import ASSET_ROOTS, validate_portable_name


EVENT_RESOURCE_KINDS = {
    EventKind.BACKGROUND: ResourceKind.BACKGROUND,
    EventKind.CHARACTER: ResourceKind.CHARACTER,
    EventKind.CG: ResourceKind.CG,
}


def canvas_to_transform(
    x: float,
    y: float,
    width: float,
    height: float,
    snap_pixels: float = 0,
) -> Transform:
    """Convert a canvas point to portable relative alignment values."""

    if width <= 0 or height <= 0:
        raise ValueError("Canvas dimensions must be positive")

    xalign = min(1.0, max(0.0, float(x) / width))
    yalign = min(1.0, max(0.0, float(y) / height))
    if snap_pixels > 0:
        xalign = _snap_axis(xalign, width, snap_pixels)
        yalign = _snap_axis(yalign, height, snap_pixels)
    return Transform(xalign=xalign, yalign=yalign)


def _snap_axis(value: float, extent: float, snap_pixels: float) -> float:
    threshold = snap_pixels / extent
    nearest = min((0.0, 0.5, 1.0), key=lambda target: abs(target - value))
    if abs(nearest - value) <= threshold:
        return nearest
    return value


def assign_resource_to_kind(
    event_kind: EventKind,
    relative_path: str,
) -> Optional[ValidationIssue]:
    """Validate that a project-relative resource matches an event kind."""

    path = PurePosixPath(relative_path)
    name_issues = validate_portable_name(path)
    if name_issues:
        return name_issues[0]

    parts = path.parts
    actual_kind = ASSET_ROOTS.get(parts[1]) if len(parts) >= 3 and parts[0] == "assets" else None
    expected_kind = EVENT_RESOURCE_KINDS.get(event_kind)
    if expected_kind is None or actual_kind != expected_kind:
        return ValidationIssue(
            "kind-mismatch",
            f"{relative_path} cannot be assigned to a {event_kind.value} event",
            path,
        )
    return None


def assign_resource(event: Event, relative_path: str) -> Optional[ValidationIssue]:
    """Assign a compatible resource path to an event."""

    issue = assign_resource_to_kind(event.kind, relative_path)
    if issue is None:
        event.asset = relative_path
    return issue


def set_transform(
    event: Event,
    xalign: float,
    yalign: float,
    zoom: float,
    zorder: int,
) -> None:
    """Update a visual event using bounded relative transform values."""

    event.xalign = min(1.0, max(0.0, float(xalign)))
    event.yalign = min(1.0, max(0.0, float(yalign)))
    event.zoom = max(0.01, float(zoom))
    event.zorder = int(zorder)


def set_attachment(event: Event, attachment: Attachment) -> None:
    """Add an attachment or replace the existing attachment of its kind."""

    for index, current in enumerate(event.attachments):
        if current.kind == attachment.kind:
            event.attachments[index] = attachment
            return
    event.attachments.append(attachment)

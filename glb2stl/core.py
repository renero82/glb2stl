"""Conversion logic shared by the command line and the graphical interface."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import trimesh


@dataclass
class ConversionResult:
    src: Path
    dst: Path
    size_mm: tuple[float, float, float]
    faces: int
    watertight: bool
    warnings: list[str] = field(default_factory=list)

    def summary(self) -> str:
        x, y, z = self.size_mm
        return (f"{self.src.name} -> {self.dst}  |  {x:.1f} x {y:.1f} x {z:.1f} mm  |  "
                f"{self.faces:,} faces")


def parse_ratio(text: str) -> float:
    """Accept '1:16', '1/16' or '16' and return the denominator (16.0)."""
    t = str(text).strip().replace("/", ":")
    if ":" in t:
        num, den = t.split(":", 1)
        value = float(den) / float(num)
    else:
        value = float(t)
    if value <= 0:
        raise ValueError(f"invalid ratio: {text!r}")
    return value


AXES = ("height", "length", "width")


def measure(mesh: trimesh.Trimesh, axis: str = "height") -> float:
    """Size of the mesh along a reference dimension, in model units.

    ``height`` is the Z extent (the mesh is expected to be Z-up). ``length`` and ``width``
    are the long and short sides of the smallest rectangle around the footprint seen from
    above, so a vehicle is measured correctly even if it is not aligned with the X/Y axes.
    """
    axis = axis.lower()
    if axis not in AXES:
        raise ValueError(f"invalid axis: {axis!r} (use one of {', '.join(AXES)})")
    if axis == "height":
        return float(mesh.extents[2])
    sides = footprint_sides(mesh.vertices[:, :2])
    return float(sides[0] if axis == "length" else sides[1])


def _convex_hull_2d(points: np.ndarray) -> np.ndarray:
    """Convex hull of 2D points (counter-clockwise), numpy only - no scipy needed."""
    # cheap pre-filter: drop the points inside the octagon of the extreme points
    dirs = np.array([[1, 0], [1, 1], [0, 1], [-1, 1], [-1, 0], [-1, -1], [0, -1], [1, -1]],
                    dtype=float)
    octagon = points[np.argmax(points @ dirs.T, axis=0)]
    octagon = octagon[np.r_[True, np.any(np.diff(octagon, axis=0) != 0, axis=1)]]
    if len(octagon) >= 3:
        inside = np.ones(len(points), dtype=bool)
        for a, b in zip(octagon, np.roll(octagon, -1, axis=0)):
            if np.allclose(a, b):
                continue
            inside &= (b[0] - a[0]) * (points[:, 1] - a[1]) - (b[1] - a[1]) * (points[:, 0] - a[0]) > 0
        points = np.vstack([octagon, points[~inside]])
    pts = np.unique(points, axis=0)  # sorted by x, then y
    if len(pts) < 3:
        return pts

    def half(seq):
        out = []
        for q in seq:
            while len(out) >= 2 and ((out[-1][0] - out[-2][0]) * (q[1] - out[-2][1])
                                     - (out[-1][1] - out[-2][1]) * (q[0] - out[-2][0])) <= 0:
                out.pop()
            out.append(q)
        return out[:-1]

    rows = pts.tolist()
    return np.array(half(rows) + half(reversed(rows)))


def footprint_sides(points: np.ndarray) -> tuple[float, float]:
    """Long and short side of the minimum-area rectangle around 2D points."""
    hull = _convex_hull_2d(np.asarray(points, dtype=float))
    if len(hull) < 3:  # a point or a line
        span = np.ptp(hull, axis=0) if len(hull) else np.zeros(2)
        return float(np.hypot(*span)), 0.0
    edges = np.roll(hull, -1, axis=0) - hull
    edges = edges[np.hypot(edges[:, 0], edges[:, 1]) > 1e-12]
    u = edges / np.hypot(edges[:, 0], edges[:, 1])[:, None]  # edge directions
    v = np.column_stack([-u[:, 1], u[:, 0]])                  # perpendiculars
    pu, pv = hull @ u.T, hull @ v.T
    a, b = np.ptp(pu, axis=0), np.ptp(pv, axis=0)
    best = np.argmin(a * b)
    return float(max(a[best], b[best])), float(min(a[best], b[best]))


def convert(src: Path | str, dst: Path | str, *,
            height: float | None = None,
            ratio: float | None = None,
            real_height: float = 1.75,
            scale: float | None = None,
            rotate: bool = True,
            center: bool = True,
            axis: str = "height",
            real_size: float | None = None) -> ConversionResult:
    """Convert a GLB/glTF file to STL.

    Only one of ``height`` (target size in mm), ``ratio`` (1:N, pass N) or ``scale``
    should be set. ``axis`` chooses the reference dimension used by ``height`` and
    ``ratio``: ``"height"`` (default, figures), ``"length"`` or ``"width"`` (vehicles).
    ``real_size`` is the real-world size in meters along ``axis`` for ``ratio``;
    ``real_height`` is kept as its name from 2.x and is used when ``real_size`` is not given.
    """
    src, dst = Path(src), Path(dst)
    mesh = trimesh.load(src, force="mesh")
    if mesh.is_empty:
        raise ValueError("no geometry found")

    if rotate:
        # glTF is Y-up, slicers are Z-up: rotate +90 degrees around X
        mesh.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [1, 0, 0]))

    if height or ratio:
        reference = measure(mesh, axis)
        if reference <= 0:
            raise ValueError(f"model has no {axis}, choose another reference dimension")
        real = real_size if real_size is not None else real_height
        target = height if height else real * 1000.0 / ratio
        mesh.apply_scale(target / reference)
    elif scale:
        mesh.apply_scale(scale)

    # place on the build plate (Z = 0), optionally centered on X/Y
    lo, hi = mesh.bounds
    offset = [0.0, 0.0, -lo[2]]
    if center:
        offset[0], offset[1] = -(lo[0] + hi[0]) / 2, -(lo[1] + hi[1]) / 2
    mesh.apply_translation(offset)

    dst.parent.mkdir(parents=True, exist_ok=True)
    mesh.export(dst)

    size = tuple(float(v) for v in mesh.extents)
    warnings = []
    if max(size) < 10 and not (height or ratio or scale):
        warnings.append("model is smaller than 10 mm - the source was probably in meters, "
                        "set a target height, a ratio or a scale factor")
    if not mesh.is_watertight:
        warnings.append("mesh is not watertight, check it in your slicer")

    return ConversionResult(src, dst, size, len(mesh.faces), bool(mesh.is_watertight), warnings)

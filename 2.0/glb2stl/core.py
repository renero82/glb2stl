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


def convert(src: Path | str, dst: Path | str, *,
            height: float | None = None,
            ratio: float | None = None,
            real_height: float = 1.75,
            scale: float | None = None,
            rotate: bool = True,
            center: bool = True) -> ConversionResult:
    """Convert a GLB/glTF file to STL.

    Only one of ``height`` (mm), ``ratio`` (1:N, pass N) or ``scale`` should be set.
    """
    src, dst = Path(src), Path(dst)
    mesh = trimesh.load(src, force="mesh")
    if mesh.is_empty:
        raise ValueError("no geometry found")

    if rotate:
        # glTF is Y-up, slicers are Z-up: rotate +90 degrees around X
        mesh.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [1, 0, 0]))

    model_height = mesh.extents[2]
    if height:
        mesh.apply_scale(height / model_height)
    elif ratio:
        mesh.apply_scale((real_height * 1000.0 / ratio) / model_height)
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

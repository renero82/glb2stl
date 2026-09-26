#!/usr/bin/env python3
"""
glb2stl - Convert GLB/glTF models to STL, ready for 3D printing.

- merges all meshes in the scene into a single mesh
- rotates from glTF's Y-up to the Z-up convention used by slicers
- places the model on the build plate (Z = 0), centered on X/Y
- scales to a target height, a scale factor or a scale ratio (e.g. 1:16)

Examples:
    glb2stl.py model.glb                            # -> model.stl
    glb2stl.py model.glb -o out.stl --height 110    # 110 mm tall
    glb2stl.py model.glb --ratio 1:16               # 1/16 scale, 1.75 m real height
    glb2stl.py *.glb --ratio 1:35 --real-height 1.80
"""
import argparse
import sys
from pathlib import Path

import numpy as np
import trimesh

__version__ = "1.0.0"


def parse_ratio(text: str) -> float:
    """Accept '1:16', '1/16' or '16' and return the denominator (16.0)."""
    t = text.replace("/", ":")
    try:
        if ":" in t:
            num, den = t.split(":", 1)
            return float(den) / float(num)
        return float(t)
    except ValueError:
        raise argparse.ArgumentTypeError(f"invalid ratio: {text!r} (use e.g. 1:16)")


def convert(src: Path, dst: Path, args) -> None:
    mesh = trimesh.load(src, force="mesh")
    if mesh.is_empty:
        raise ValueError("no geometry found")

    if not args.no_rotate:
        # glTF is Y-up, slicers are Z-up: rotate +90 degrees around X
        mesh.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [1, 0, 0]))

    height = mesh.extents[2]
    if args.height:
        mesh.apply_scale(args.height / height)
    elif args.ratio:
        target_mm = args.real_height * 1000.0 / args.ratio
        mesh.apply_scale(target_mm / height)
    elif args.scale:
        mesh.apply_scale(args.scale)

    # place on the build plate, centered on X/Y
    lo, hi = mesh.bounds
    offset = [-(lo[0] + hi[0]) / 2, -(lo[1] + hi[1]) / 2, -lo[2]]
    if args.no_center:
        offset[0] = offset[1] = 0.0
    mesh.apply_translation(offset)

    dst.parent.mkdir(parents=True, exist_ok=True)
    mesh.export(dst)

    x, y, z = mesh.extents
    print(f"{src.name} -> {dst}  |  {x:.1f} x {y:.1f} x {z:.1f} mm  |  "
          f"{len(mesh.faces):,} faces")
    if max(x, y, z) < 10 and not (args.height or args.ratio or args.scale):
        print("  warning: model is smaller than 10 mm - the source was probably in meters, "
              "use --height, --ratio or --scale", file=sys.stderr)
    if not mesh.is_watertight:
        print("  warning: mesh is not watertight, check it in your slicer", file=sys.stderr)


def main() -> int:
    p = argparse.ArgumentParser(
        description="Convert GLB/glTF models to STL for 3D printing.",
        epilog="Note: glTF uses meters and STL has no units; slicers read STL as millimeters. "
               "Without a scaling option a 1.9 m model becomes 1.9 mm.")
    p.add_argument("inputs", nargs="+", type=Path, help="input .glb/.gltf file(s)")
    p.add_argument("-o", "--output", type=Path,
                   help="output file (single input) or directory (multiple inputs)")
    size = p.add_mutually_exclusive_group()
    size.add_argument("--height", type=float, metavar="MM", help="target height in mm")
    size.add_argument("--ratio", type=parse_ratio, metavar="1:N",
                      help="scale ratio for figures, e.g. 1:16 or 1:35")
    size.add_argument("--scale", type=float, metavar="F",
                      help="plain scale factor (e.g. 1000 to go from meters to mm)")
    p.add_argument("--real-height", type=float, default=1.75, metavar="M",
                   help="real-world height in meters used with --ratio (default: 1.75)")
    p.add_argument("--no-rotate", action="store_true",
                   help="keep original orientation (model is already Z-up)")
    p.add_argument("--no-center", action="store_true",
                   help="do not center the model on X/Y")
    p.add_argument("-V", "--version", action="version", version=f"%(prog)s {__version__}")
    args = p.parse_args()

    multi = len(args.inputs) > 1
    errors = 0
    for src in args.inputs:
        if multi or args.output is None:
            outdir = args.output if (multi and args.output) else src.parent
            dst = outdir / (src.stem + ".stl")
        else:
            dst = args.output
        try:
            convert(src, dst, args)
        except Exception as exc:  # keep going with the other files
            print(f"{src}: error: {exc}", file=sys.stderr)
            errors += 1
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())

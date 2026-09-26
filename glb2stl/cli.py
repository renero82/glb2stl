"""Command line interface: glb2stl model.glb [options]"""
import argparse
import sys
from pathlib import Path

from . import __version__
from .core import convert, parse_ratio


def _ratio(text: str) -> float:
    try:
        return parse_ratio(text)
    except (ValueError, ZeroDivisionError):
        raise argparse.ArgumentTypeError(f"invalid ratio: {text!r} (use e.g. 1:16)")


def main(argv=None) -> int:
    p = argparse.ArgumentParser(
        prog="glb2stl",
        description="Convert GLB/glTF models to STL for 3D printing.",
        epilog="Note: glTF uses meters and STL has no units; slicers read STL as millimeters. "
               "Without a scaling option a 1.9 m model becomes 1.9 mm.")
    p.add_argument("inputs", nargs="+", type=Path, help="input .glb/.gltf file(s)")
    p.add_argument("-o", "--output", type=Path,
                   help="output file (single input) or directory (multiple inputs)")
    size = p.add_mutually_exclusive_group()
    size.add_argument("--height", type=float, metavar="MM", help="target height in mm")
    size.add_argument("--ratio", type=_ratio, metavar="1:N",
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
    args = p.parse_args(argv)

    multi = len(args.inputs) > 1
    errors = 0
    for src in args.inputs:
        if multi or args.output is None:
            outdir = args.output if (multi and args.output) else src.parent
            dst = outdir / (src.stem + ".stl")
        else:
            dst = args.output
        try:
            res = convert(src, dst, height=args.height, ratio=args.ratio,
                          real_height=args.real_height, scale=args.scale,
                          rotate=not args.no_rotate, center=not args.no_center)
            print(res.summary())
            for w in res.warnings:
                print(f"  warning: {w}", file=sys.stderr)
        except Exception as exc:  # keep going with the other files
            print(f"{src}: error: {exc}", file=sys.stderr)
            errors += 1
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())

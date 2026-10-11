"""Command line interface: glb2stl model.glb [options]"""
import argparse
import sys
from pathlib import Path

from . import __version__
from .core import AXES, convert, parse_ratio


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
    size.add_argument("--length", type=float, metavar="MM",
                      help="target length in mm (long side of the footprint, for vehicles)")
    size.add_argument("--width", type=float, metavar="MM",
                      help="target width in mm (short side of the footprint)")
    size.add_argument("--ratio", type=_ratio, metavar="1:N",
                      help="scale ratio, e.g. 1:16 or 1:35, based on --real-size and --axis")
    size.add_argument("--scale", type=float, metavar="F",
                      help="plain scale factor (e.g. 1000 to go from meters to mm)")
    p.add_argument("--real-size", "--real-height", dest="real_size", type=float, metavar="M",
                   help="real-world size in meters along --axis, used with --ratio "
                        "(default: 1.75, a person's height; required with --axis length/width)")
    p.add_argument("--axis", choices=AXES, default="height",
                   help="reference dimension for --ratio: height (figures, default), "
                        "length or width (vehicles)")
    p.add_argument("--no-rotate", action="store_true",
                   help="keep original orientation (model is already Z-up)")
    p.add_argument("--no-center", action="store_true",
                   help="do not center the model on X/Y")
    p.add_argument("-V", "--version", action="version", version=f"%(prog)s {__version__}")
    args = p.parse_args(argv)

    target, axis = args.height, args.axis
    if args.length:
        target, axis = args.length, "length"
    elif args.width:
        target, axis = args.width, "width"
    elif args.height:
        axis = "height"
    real_size = args.real_size
    if args.ratio and real_size is None:
        if axis != "height":
            p.error(f"--axis {axis} needs --real-size, the real {axis} in meters "
                    f"(e.g. --real-size 5.84 for a 5.84 m long tank)")
        real_size = 1.75

    multi = len(args.inputs) > 1
    errors = 0
    for src in args.inputs:
        if multi or args.output is None:
            outdir = args.output if (multi and args.output) else src.parent
            dst = outdir / (src.stem + ".stl")
        else:
            dst = args.output
        try:
            res = convert(src, dst, height=target, ratio=args.ratio,
                          real_size=real_size, axis=axis, scale=args.scale,
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

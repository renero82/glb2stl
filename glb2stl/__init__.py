"""glb2stl - convert GLB/glTF models to STL, ready for 3D printing."""
__version__ = "2.3.0"

from .core import ConversionResult, AXES, convert, measure, parse_ratio  # noqa: F401

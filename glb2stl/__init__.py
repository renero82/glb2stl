"""glb2stl - convert GLB/glTF models to STL, ready for 3D printing."""
__version__ = "2.1.1"

from .core import ConversionResult, convert, parse_ratio  # noqa: F401

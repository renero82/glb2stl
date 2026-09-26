# Changelog

## 2.0.0
- New desktop GUI (PySide6): drag & drop of files and folders, batch conversion,
  size by target height / 1:N ratio / scale factor, output folder, progress bar and log.
- Conversion runs in a background thread, the window stays responsive with large models.
- Settings are remembered between sessions.
- Code reorganized as a package (`glb2stl/core.py`, `cli.py`, `gui.py`) and installable
  with pip, with `glb2stl` and `glb2stl-gui` commands.
- `python3 glb2stl.py ...` keeps working as in 1.x.

## 1.0.0
- First release: GLB/glTF to STL with auto-orientation, centering and scaling.

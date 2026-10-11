# Changelog

## 2.3.0
- Scaling for vehicles, ships and aircraft: new reference dimension (**height**, **length**
  or **width**) for the 1:N ratio and the target size.
- Command line: new `--axis`, `--length MM`, `--width MM` and `--real-size M`
  (`--real-height` keeps working as an alias). `--axis length/width` requires `--real-size`.
- Desktop app: "Target height" becomes "Target size", new "Measure along" menu,
  the hint shows the resulting size along the chosen dimension.
- Length and width are measured on the minimum-area rectangle of the footprint seen from
  above, so models turned on the plate are measured correctly. No new dependencies.
- `convert()` accepts `axis` and `real_size`; `real_height` still works.
- The selftest also checks a rotated vehicle scaled 1:35 by its length.

## 2.2.0
- Windows installer (Inno Setup): per-user install without admin rights, Start menu entry,
  optional desktop icon, uninstaller and optional "Open with glb2stl" for .glb/.gltf files.
  SmartScreen warns only once, when running the setup.
- The installed app uses a folder build: faster startup and far fewer antivirus false positives.
- The single-file exe is still available as `windows-portable`.
- The release workflow now also installs the app silently, runs the selftest on the installed
  copy and uninstalls it, and checks that the tag matches the version in the code.
- New `scripts/build_windows.ps1` for local builds on Windows.

## 2.1.1
- New `--selftest` option for the desktop app: loads the GUI, converts a test model and checks
  the result. The release workflow runs it on the freshly built macOS and Windows apps and
  publishes the release only if both pass.

## 2.1.0
- Standalone desktop apps, no Python required: `glb2stl.app` for macOS (Apple Silicon)
  and `glb2stl.exe` for Windows, attached to the GitHub release.
- Automatic builds with GitHub Actions on every version tag.
- New app icon.

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

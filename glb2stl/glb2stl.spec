# PyInstaller spec for the glb2stl desktop app.
# Build with:  pyinstaller glb2stl.spec
# macOS  -> dist/glb2stl.app
# Windows-> dist/glb2stl-portable.exe (single file) + dist/glb2stl/ (folder, for the installer)
import sys
from PyInstaller.utils.hooks import collect_data_files

import re
__version__ = re.search(r'__version__ = "([^"]+)"', open('glb2stl/__init__.py').read()).group(1)

IS_MAC = sys.platform == "darwin"
IS_WIN = sys.platform == "win32"

datas = collect_data_files("trimesh") + [("assets/icon.png", "assets")]

# Qt modules the app does not use: leaving them out keeps the bundle much smaller
excludes = [
    "tkinter", "matplotlib", "scipy", "pandas", "IPython",
    # optional trimesh extras not needed to load GLB and write STL
    "skimage", "sklearn", "lxml", "networkx", "shapely", "rtree", "embreex",
    "manifold3d", "open3d", "pyglet", "xxhash", "jsonschema",
    "PySide6.QtWebEngineCore", "PySide6.QtWebEngineWidgets", "PySide6.QtWebEngineQuick",
    "PySide6.Qt3DCore", "PySide6.Qt3DRender", "PySide6.QtQuick", "PySide6.QtQml",
    "PySide6.QtMultimedia", "PySide6.QtCharts", "PySide6.QtDataVisualization",
    "PySide6.QtPdf", "PySide6.QtSql", "PySide6.QtBluetooth", "PySide6.QtSerialPort",
]

a = Analysis(
    ["glb2stl_gui.py"],
    datas=datas,
    excludes=excludes,
    noarchive=False,
)
pyz = PYZ(a.pure)

icon = "assets/icon.png"   # PyInstaller converts it to .icns/.ico (needs Pillow)

if IS_WIN:
    # 1) portable single-file exe
    portable = EXE(
        pyz, a.scripts, a.binaries, a.datas,
        name="glb2stl-portable",
        console=False,
        icon="assets/icon.ico",
        upx=False,
    )
    # 2) folder build (dist/glb2stl/) used by the installer: starts faster and
    #    triggers far fewer antivirus false positives than the self-extracting exe
    exe = EXE(
        pyz, a.scripts,
        exclude_binaries=True,
        name="glb2stl",
        console=False,
        icon="assets/icon.ico",
        upx=False,
    )
    coll = COLLECT(exe, a.binaries, a.datas, name="glb2stl", upx=False)
else:
    exe = EXE(
        pyz, a.scripts,
        exclude_binaries=True,
        name="glb2stl",
        console=False,
        icon=icon,
        upx=False,
    )
    coll = COLLECT(exe, a.binaries, a.datas, name="glb2stl", upx=False)
    if IS_MAC:
        app = BUNDLE(
            coll,
            name="glb2stl.app",
            icon=icon,
            bundle_identifier="com.renero82.glb2stl",
            info_plist={
                "CFBundleShortVersionString": __version__,
                "CFBundleVersion": __version__,
                "NSHighResolutionCapable": True,
                "CFBundleDocumentTypes": [{
                    "CFBundleTypeName": "glTF model",
                    "CFBundleTypeRole": "Viewer",
                    "LSItemContentTypes": ["org.khronos.gltf.binary", "org.khronos.gltf"],
                    "LSHandlerRank": "Alternate",
                }],
            },
        )

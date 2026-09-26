"""Graphical interface for glb2stl (PySide6)."""
from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import QObject, QSettings, Qt, QThread, Signal
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import (
    QAbstractItemView, QApplication, QButtonGroup, QCheckBox, QDoubleSpinBox, QFileDialog,
    QGridLayout, QGroupBox, QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem,
    QMainWindow, QMessageBox, QPlainTextEdit, QProgressBar, QPushButton, QRadioButton,
    QVBoxLayout, QWidget,
)

from . import __version__
from .core import convert

EXTENSIONS = {".glb", ".gltf"}


class DropList(QListWidget):
    """File list that accepts .glb/.gltf files dropped from Finder/Explorer."""

    files_dropped = Signal(list)

    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setMinimumHeight(140)

    def _paths(self, event):
        return [Path(u.toLocalFile()) for u in event.mimeData().urls() if u.isLocalFile()]

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        paths = []
        for p in self._paths(event):
            if p.is_dir():
                paths += sorted(f for f in p.iterdir() if f.suffix.lower() in EXTENSIONS)
            elif p.suffix.lower() in EXTENSIONS:
                paths.append(p)
        if paths:
            self.files_dropped.emit(paths)
        event.acceptProposedAction()

    def paintEvent(self, event):
        super().paintEvent(event)
        if self.count() == 0:
            from PySide6.QtGui import QPainter
            painter = QPainter(self.viewport())
            painter.setPen(self.palette().placeholderText().color())
            painter.drawText(self.viewport().rect(), Qt.AlignCenter,
                             "Drop .glb / .gltf files or folders here\nor use \u201cAdd files\u2026\u201d")


class Worker(QObject):
    """Runs the conversions outside the UI thread."""

    progress = Signal(int)
    message = Signal(str, str)  # text, level: info | warn | error | ok
    done = Signal(int, int)     # converted, errors

    def __init__(self, jobs, options):
        super().__init__()
        self.jobs, self.options = jobs, options

    def run(self):
        ok = errors = 0
        for i, (src, dst) in enumerate(self.jobs, start=1):
            self.message.emit(f"Converting {src.name}\u2026", "info")
            try:
                res = convert(src, dst, **self.options)
                x, y, z = res.size_mm
                self.message.emit(f"\u2713 {dst.name}: {x:.1f} \u00d7 {y:.1f} \u00d7 {z:.1f} mm, "
                                  f"{res.faces:,} faces", "ok")
                for w in res.warnings:
                    self.message.emit(f"  \u26a0 {w}", "warn")
                ok += 1
            except Exception as exc:
                self.message.emit(f"\u2717 {src.name}: {exc}", "error")
                errors += 1
            self.progress.emit(i)
        self.done.emit(ok, errors)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"glb2stl {__version__}")
        self.resize(720, 680)
        self.settings = QSettings("renero82", "glb2stl")
        self.thread = None

        central = QWidget()
        root = QVBoxLayout(central)
        self.setCentralWidget(central)

        # --- input files -------------------------------------------------
        files_box = QGroupBox("Input files")
        fl = QVBoxLayout(files_box)
        self.files = DropList()
        self.files.files_dropped.connect(self.add_paths)
        fl.addWidget(self.files)
        row = QHBoxLayout()
        self.btn_add = QPushButton("Add files\u2026")
        self.btn_add.clicked.connect(self.choose_files)
        self.btn_remove = QPushButton("Remove selected")
        self.btn_remove.clicked.connect(self.remove_selected)
        self.btn_clear = QPushButton("Clear")
        self.btn_clear.clicked.connect(self.files.clear)
        for b in (self.btn_add, self.btn_remove, self.btn_clear):
            row.addWidget(b)
        row.addStretch()
        fl.addLayout(row)
        root.addWidget(files_box, stretch=2)

        # --- size ---------------------------------------------------------
        size_box = QGroupBox("Size")
        g = QGridLayout(size_box)
        self.size_group = QButtonGroup(self)
        self.rb_keep = QRadioButton("Keep original units")
        self.rb_height = QRadioButton("Target height")
        self.rb_ratio = QRadioButton("Scale ratio  1 :")
        self.rb_scale = QRadioButton("Scale factor")
        for i, rb in enumerate((self.rb_keep, self.rb_height, self.rb_ratio, self.rb_scale)):
            self.size_group.addButton(rb, i)

        self.sp_height = self._spin(1, 2000, 110, 1, " mm")
        self.sp_ratio = self._spin(1, 1000, 16, 0)
        self.sp_real = self._spin(0.01, 100, 1.75, 2, " m")
        self.sp_scale = self._spin(0.0001, 100000, 1000, 4)

        g.addWidget(self.rb_keep, 0, 0, 1, 4)
        g.addWidget(self.rb_height, 1, 0)
        g.addWidget(self.sp_height, 1, 1)
        g.addWidget(self.rb_ratio, 2, 0)
        g.addWidget(self.sp_ratio, 2, 1)
        g.addWidget(QLabel("real height"), 2, 2, alignment=Qt.AlignRight)
        g.addWidget(self.sp_real, 2, 3)
        g.addWidget(self.rb_scale, 3, 0)
        g.addWidget(self.sp_scale, 3, 1)
        self.lbl_hint = QLabel()
        self.lbl_hint.setStyleSheet("color: gray;")
        g.addWidget(self.lbl_hint, 4, 0, 1, 4)
        g.setColumnStretch(4, 1)
        self.size_group.idToggled.connect(self.update_size_widgets)
        for sp in (self.sp_ratio, self.sp_real):
            sp.valueChanged.connect(self.update_size_widgets)
        root.addWidget(size_box)

        # --- options + output --------------------------------------------
        opt_box = QGroupBox("Options")
        ol = QVBoxLayout(opt_box)
        self.cb_rotate = QCheckBox("Rotate Y-up \u2192 Z-up (stand the model on the plate)")
        self.cb_center = QCheckBox("Center on the build plate (X/Y)")
        ol.addWidget(self.cb_rotate)
        ol.addWidget(self.cb_center)

        out_row = QHBoxLayout()
        self.rb_same = QRadioButton("Same folder as source")
        self.rb_folder = QRadioButton("Folder:")
        self.out_group = QButtonGroup(self)
        self.out_group.addButton(self.rb_same, 0)
        self.out_group.addButton(self.rb_folder, 1)
        self.ed_folder = QLineEdit()
        self.btn_folder = QPushButton("Browse\u2026")
        self.btn_folder.clicked.connect(self.choose_folder)
        out_row.addWidget(self.rb_same)
        out_row.addWidget(self.rb_folder)
        out_row.addWidget(self.ed_folder, stretch=1)
        out_row.addWidget(self.btn_folder)
        ol.addLayout(out_row)
        self.out_group.idToggled.connect(lambda *_: self.update_output_widgets())
        root.addWidget(opt_box)

        # --- run ------------------------------------------------------------
        run_row = QHBoxLayout()
        self.progress = QProgressBar()
        self.progress.setTextVisible(True)
        self.btn_convert = QPushButton("Convert")
        self.btn_convert.setDefault(True)
        self.btn_convert.setMinimumWidth(140)
        self.btn_convert.clicked.connect(self.start)
        run_row.addWidget(self.progress, stretch=1)
        run_row.addWidget(self.btn_convert)
        root.addLayout(run_row)

        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)
        self.log.setMaximumBlockCount(2000)
        root.addWidget(self.log, stretch=1)

        quit_action = QAction(self)
        quit_action.setShortcut(QKeySequence.Quit)
        quit_action.triggered.connect(self.close)
        self.addAction(quit_action)

        self.load_settings()
        self.update_size_widgets()
        self.update_output_widgets()

    # ------------------------------------------------------------------ helpers
    @staticmethod
    def _spin(lo, hi, value, decimals, suffix=""):
        sp = QDoubleSpinBox()
        sp.setRange(lo, hi)
        sp.setDecimals(decimals)
        sp.setValue(value)
        sp.setSuffix(suffix)
        sp.setMinimumWidth(110)
        return sp

    def add_paths(self, paths):
        existing = {self.files.item(i).data(Qt.UserRole) for i in range(self.files.count())}
        for p in paths:
            p = str(Path(p).resolve())
            if p not in existing:
                item = QListWidgetItem(Path(p).name)
                item.setToolTip(p)
                item.setData(Qt.UserRole, p)
                self.files.addItem(item)
                existing.add(p)

    def choose_files(self):
        start = self.settings.value("last_dir", str(Path.home()))
        names, _ = QFileDialog.getOpenFileNames(self, "Choose GLB/glTF files", start,
                                                "3D models (*.glb *.gltf)")
        if names:
            self.settings.setValue("last_dir", str(Path(names[0]).parent))
            self.add_paths(names)

    def remove_selected(self):
        for item in self.files.selectedItems():
            self.files.takeItem(self.files.row(item))

    def choose_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Output folder",
                                                  self.ed_folder.text() or str(Path.home()))
        if folder:
            self.ed_folder.setText(folder)
            self.rb_folder.setChecked(True)

    def update_size_widgets(self, *_):
        mode = self.size_group.checkedId()
        self.sp_height.setEnabled(mode == 1)
        self.sp_ratio.setEnabled(mode == 2)
        self.sp_real.setEnabled(mode == 2)
        self.sp_scale.setEnabled(mode == 3)
        hints = {
            0: "Sizes stay as in the file: GLB is in meters, so models usually come out tiny.",
            1: "The model is scaled so its total height matches the value.",
            2: f"Figure height: {self.sp_real.value() * 1000 / self.sp_ratio.value():.1f} mm "
               f"(uses the total height of the model).",
            3: "Every dimension is multiplied by this factor (1000 = meters to mm).",
        }
        self.lbl_hint.setText(hints.get(mode, ""))

    def update_output_widgets(self):
        custom = self.rb_folder.isChecked()
        self.ed_folder.setEnabled(custom)
        self.btn_folder.setEnabled(custom)

    def options(self):
        mode = self.size_group.checkedId()
        return {
            "height": self.sp_height.value() if mode == 1 else None,
            "ratio": self.sp_ratio.value() if mode == 2 else None,
            "real_height": self.sp_real.value(),
            "scale": self.sp_scale.value() if mode == 3 else None,
            "rotate": self.cb_rotate.isChecked(),
            "center": self.cb_center.isChecked(),
        }

    def jobs(self):
        out_dir = Path(self.ed_folder.text()).expanduser() if self.rb_folder.isChecked() else None
        result = []
        for i in range(self.files.count()):
            src = Path(self.files.item(i).data(Qt.UserRole))
            result.append((src, (out_dir or src.parent) / (src.stem + ".stl")))
        return result

    def append_log(self, text, level="info"):
        colors = {"ok": "#2e9d4f", "warn": "#c98a00", "error": "#d64545"}
        color = colors.get(level)
        safe = text.replace("&", "&amp;").replace("<", "&lt;")
        self.log.appendHtml(f'<span style="color:{color}">{safe}</span>' if color else safe)

    def set_busy(self, busy):
        for w in (self.btn_add, self.btn_remove, self.btn_clear, self.btn_convert, self.files):
            w.setEnabled(not busy)
        self.btn_convert.setText("Converting\u2026" if busy else "Convert")

    # ------------------------------------------------------------------ run
    def start(self):
        jobs = self.jobs()
        if not jobs:
            QMessageBox.information(self, "glb2stl", "Add at least one .glb or .gltf file.")
            return
        if self.rb_folder.isChecked() and not self.ed_folder.text().strip():
            QMessageBox.warning(self, "glb2stl", "Choose an output folder.")
            return
        overwrite = [dst.name for _, dst in jobs if dst.exists()]
        if overwrite:
            answer = QMessageBox.question(
                self, "glb2stl",
                f"{len(overwrite)} file(s) already exist and will be overwritten:\n"
                + "\n".join(overwrite[:8]) + ("\n\u2026" if len(overwrite) > 8 else ""))
            if answer != QMessageBox.Yes:
                return

        self.save_settings()
        self.progress.setRange(0, len(jobs))
        self.progress.setValue(0)
        self.set_busy(True)

        self.thread = QThread(self)
        self.worker = Worker(jobs, self.options())
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.progress.connect(self.progress.setValue)
        self.worker.message.connect(self.append_log)
        self.worker.done.connect(self.finished)
        self.worker.done.connect(self.thread.quit)
        self.thread.finished.connect(self.worker.deleteLater)
        self.thread.start()

    def finished(self, ok, errors):
        self.set_busy(False)
        summary = f"Done: {ok} converted" + (f", {errors} failed" if errors else "")
        self.append_log(summary, "error" if errors else "ok")
        self.append_log("")

    # ------------------------------------------------------------------ settings
    def load_settings(self):
        s = self.settings
        self.size_group.button(int(s.value("size_mode", 2))).setChecked(True)
        self.sp_height.setValue(float(s.value("height", 110)))
        self.sp_ratio.setValue(float(s.value("ratio", 16)))
        self.sp_real.setValue(float(s.value("real_height", 1.75)))
        self.sp_scale.setValue(float(s.value("scale", 1000)))
        self.cb_rotate.setChecked(s.value("rotate", "true") == "true")
        self.cb_center.setChecked(s.value("center", "true") == "true")
        self.out_group.button(int(s.value("out_mode", 0))).setChecked(True)
        self.ed_folder.setText(s.value("out_dir", ""))

    def save_settings(self):
        s = self.settings
        s.setValue("size_mode", self.size_group.checkedId())
        s.setValue("height", self.sp_height.value())
        s.setValue("ratio", self.sp_ratio.value())
        s.setValue("real_height", self.sp_real.value())
        s.setValue("scale", self.sp_scale.value())
        s.setValue("rotate", "true" if self.cb_rotate.isChecked() else "false")
        s.setValue("center", "true" if self.cb_center.isChecked() else "false")
        s.setValue("out_mode", self.out_group.checkedId())
        s.setValue("out_dir", self.ed_folder.text())

    def closeEvent(self, event):
        if self.thread and self.thread.isRunning():
            QMessageBox.information(self, "glb2stl", "Please wait for the conversion to finish.")
            event.ignore()
            return
        self.save_settings()
        event.accept()


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("glb2stl")
    win = MainWindow()
    win.add_paths([a for a in sys.argv[1:] if Path(a).suffix.lower() in EXTENSIONS])
    win.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())

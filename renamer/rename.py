# -*- coding: utf-8 -*-
# rprename/rename.py

"""This module provides the Renamer class to rename multiple files."""

import time
from pathlib import Path

from PyQt5.QtCore import QObject, pyqtSignal

class Renamer(QObject):
    # Define custom signals
    progressed = pyqtSignal(int)
    renamedFile = pyqtSignal(Path, Path)
    finished = pyqtSignal()
    def __init__(self, files, fileNames):
        super().__init__()
        self._files = files
        self._fileNames = fileNames

    def renameFiles(self):
        for index, file in enumerate(self._files):
            originalName = Path(file)
            fileName = file.parent.joinpath(
                f"{self._fileNames[index]}{file.suffix}"
            )
            file.rename(fileName)
            time.sleep(0.1)  # Comment this line to rename files faster.
            self.progressed.emit(index)
            self.renamedFile.emit(originalName, fileName)
        self.progressed.emit(0)  # Reset the progress
        self.finished.emit()
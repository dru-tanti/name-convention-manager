from collections import deque
from pathlib import Path

from PyQt5.QtCore import QThread
from PyQt5.QtWidgets import QFileDialog, QWidget, QHeaderView, QTableWidgetItem

from .rename import Renamer
from .ui.window import Ui_Form
import json

FILTERS = ""

class Window(QWidget, Ui_Form):
    assetTypeIndex = 0
    assetSubTypeIndex = 0

    def __init__(self):
        super().__init__()
        self._files = deque()
        self._filesCount = len(self._files)
        self._setupUI()
        self._connectSignalsSlots()

    def resizeEvent(self, event):
        self.verticalLayoutWidget.resize(event.size())
    
    def _setupUI(self):
        self.setupUi(self)
        # Need to set the headers to stretch manually
        self.tableWidget.horizontalHeader().setStretchLastSection(True)
        self.tableWidget.horizontalHeader().setSectionResizeMode(
            QHeaderView.Stretch)
        # load the type lists with the defaults
        self._loadAssetTypes()
        self._setAssetTypeInput()
        self._setAssetSubTypeInput(self.assetTypeIndex)
        # Register the change events
        self.assetTypeInput.currentIndexChanged.connect(self._assetTypeChanged)
        self.subTypeInput.currentIndexChanged.connect(self._assetSubTypeChanged)

    def _assetTypeChanged(self, index):
        self.assetTypeIndex = index
        self._setAssetSubTypeInput(index)

    def _assetSubTypeChanged(self, index):
        self.assetSubTypeIndex = index
    
    def _loadAssetTypes(self):
        jsonFile = open('data/assetTypes.json', 'r')
        with jsonFile as file:
            data = json.load(file)
        self._assetTypeData = data
        jsonFile.close()
    
    def _setAssetTypeInput(self):
        self.assetTypeInput.clear()
        for assetType in self._assetTypeData:
            self.assetTypeInput.addItem(assetType["name"])

    def _setAssetSubTypeInput(self, index):
        self.subTypeInput.clear()
        for subTypes in self._assetTypeData[index]["subTypes"]:
            self.subTypeInput.addItem(subTypes["name"])

    def _connectSignalsSlots(self):
        self.browseButton.clicked.connect(self.loadFiles)
        self.startRenameButton.clicked.connect(self.renameFiles)

    def renameFiles(self):
        self._runRenamerThread()

    def _runRenamerThread(self):
        fileNames = []
        assetType = self._assetTypeData[self.assetTypeIndex]["convention"]
        assetSubType = self._assetTypeData[self.assetTypeIndex]["subTypes"][self.assetSubTypeIndex]["convention"]
        # Since all the names are stored in a table need to do an additional loop to prepare the names
        for index, file in enumerate(self._files):
            fileNames.append("_".join([
                assetType,
                assetSubType,
                self.tableWidget.item(index, 1).text(), # name
                self.tableWidget.item(index, 2).text(), # variant
                self.tableWidget.item(index, 3).text(), # descriptor
            ]))
        self._thread = QThread()
        self._renamer = Renamer(
            files = tuple(self._files),
            fileNames = fileNames
        )
        self._renamer.moveToThread(self._thread)
        self._renamer.moveToThread(self._thread)
        # Rename
        self._thread.started.connect(self._renamer.renameFiles)
        # Update state
        self._renamer.renamedFile.connect(self._updateStateWhenFileRenamed)
        # Clean up
        self._renamer.finished.connect(self._thread.quit)
        self._renamer.finished.connect(self._renamer.deleteLater)
        self._thread.finished.connect(self._thread.deleteLater)
        # Run the thread
        self._thread.start()

    def _updateStateWhenFileRenamed(self, originalFile, newFile):
        self._files.popleft()
        self.oldNameList.addItem(str(originalFile))
        self.newNameList.addItem(str(newFile))

    def loadFiles(self):
        print(self.assetTypeIndex)
        print(self.assetSubTypeIndex)
        # Reset the table
        self._files.clear()
        self.tableWidget.clearContents()
        self.tableWidget.setRowCount(0)
        if self.filePath.text():
            initDir = self.filePath.text()
        else:
            initDir = str(Path.home())
        files, filter = QFileDialog.getOpenFileNames(
            self, "Choose Files to Rename", initDir, filter=FILTERS
        )
        if (len(files) > 0):
            srcDirName = str(Path(files[0]).parent)
            self.filePath.setText(srcDirName)
            # Loop through the files and add them to the table
            for index, file in enumerate(files):
                self._files.append(Path(file))
                self.tableWidget.insertRow(index)
                test = self.tableWidget.setItem(index, 0, QTableWidgetItem(str(Path(file).name)))
            self._filesCount = len(self._files)
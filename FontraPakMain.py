import asyncio
import json
import logging
import multiprocessing
import os
import pathlib
import secrets
import signal
import sys
import tempfile
import threading
import traceback
import webbrowser
from contextlib import aclosing
from dataclasses import dataclass
from datetime import datetime
from random import random
from urllib.parse import quote
from urllib.request import urlopen

import psutil
from fontra import __version__ as fontraVersion
from fontra.backends import getFileSystemBackend, newFileSystemBackend
from fontra.backends.copy import copyFont
from fontra.backends.populate import populateBackend
from fontra.core.classes import DiscreteFontAxis
from fontra.core.server import FontraServer, findFreeTCPPort
from fontra.filesystem.projectmanager import FileSystemProjectManager
from PyQt6.QtCore import (
    QEvent,
    QObject,
    QPoint,
    QSettings,
    QSize,
    Qt,
    QTimer,
    pyqtSignal,
)
from PyQt6.QtWidgets import (
    QApplication,
    QFileDialog,
    QGridLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QProgressDialog,
    QPushButton,
    QSizePolicy,
    QWidget,
)

commonCSS = """
border-radius: 20px;
border-style: dashed;
font-size: 18px;
padding: 16px;
"""

neutralCSS = (
    """
background-color: rgba(255,255,255,128);
border: 5px solid lightgray;
"""
    + commonCSS
)

droppingCSS = (
    """
background-color: rgba(255,255,255,64);
border: 5px solid gray;
"""
    + commonCSS
)

mainText = """
<span style="font-size: 40px;">Drop font files here</span>
<br>
<br>
Your fonts will stay on your computer and will not be uploaded anywhere.
<br>
<br>
Fontra Pak reads and writes .ufo, .designspace, .rcjk and .fontra
<br>
Additionally, it can read (not write) .ttf, .otf, .woff, .woff2, and (with some limitations)
.glyphs and .glyphspackage
"""

fileTypes = [
    # name, extension
    ("Designspace", "designspace"),
    ("Fontra", "fontra"),
    ("RoboCJK", "rcjk"),
    ("Unified Font Object", "ufo"),
]

fileTypesMapping = {
    f"{name} (*.{extension})": f".{extension}" for name, extension in fileTypes
}

exportFileTypes = [
    # name, extension
    ("TrueType", "ttf"),
    ("OpenType", "otf"),
] + fileTypes

exportFileTypesMapping = {
    f"{name} (*.{extension})": f".{extension}" for name, extension in exportFileTypes
}

exportExtensionMapping = {v: k for k, v in exportFileTypesMapping.items()}

latestReleasePageURL = "https://github.com/fontra/fontra-pak/releases/latest"


class FontraApplication(QApplication):
    def __init__(self, argv, port):
        self.port = port
        super().__init__(argv)

    def event(self, event):
        """Handle macOS FileOpen events."""
        if event.type() == QEvent.Type.FileOpen:
            openFile(event.file(), self.port)
        else:
            return super().event(event)

        return True


def getFontPath(path, fileType, mapping):
    extension = mapping[fileType]
    if not path.endswith(extension):
        path += extension

    return path


class FontraMainWidget(QMainWindow):
    def __init__(self, port):
        super().__init__()
        self.port = port
        self.setWindowTitle("Fontra Pak")
        self.resize(720, 480)

        self.settings = QSettings("xyz.fontra", "FontraPak")

        self.resize(self.settings.value("size", QSize(720, 480)))
        self.move(self.settings.value("pos", QPoint(50, 50)))

        self.setAcceptDrops(True)

        self.label = QLabel(mainText)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setStyleSheet(neutralCSS)
        self.label.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self.label.setWordWrap(True)

        # Helpful: https://www.pythontutorial.net/pyqt/pyqt-qgridlayout/
        layout = QGridLayout()

        button = QPushButton("&New Font...", self)
        button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        button.clicked.connect(self.newFont)

        buttonDocs = QPushButton("Documentation", self)
        buttonDocs.setToolTip("Open documentation website")
        buttonDocs.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        buttonDocs.clicked.connect(lambda: webbrowser.open("https://docs.fontra.xyz"))

        layout.addWidget(button, 0, 0, alignment=Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(buttonDocs, 0, 1, alignment=Qt.AlignmentFlag.AlignRight)

        layout.addWidget(self.label, 1, 0, 1, 2)

        layout.addWidget(QLabel(f"Fontra version {fontraVersion}"), 4, 0)

        if sys.platform in {"darwin", "win32"}:
            self.downloadButton = QPushButton("Download latest Fontra Pak", self)
            self.downloadButton.setSizePolicy(
                QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed
            )
            self.downloadButton.clicked.connect(self.goToLatestDownload)
            layout.addWidget(
                self.downloadButton, 4, 1, alignment=Qt.AlignmentFlag.AlignRight
            )
            if "test-startup" not in sys.argv:
                self.checkForUpdate(1500)

        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)
        self.show()

    def closeEvent(self, event):
        self.settings.setValue("size", self.size())
        self.settings.setValue("pos", self.pos())

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
            self.label.setStyleSheet(droppingCSS)
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        self.label.setStyleSheet("background-color: lightgray;")
        self.label.setStyleSheet(neutralCSS)

    def dropEvent(self, event):
        self.label.setStyleSheet(neutralCSS)
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        for path in files:
            openFile(path, self.port)
        event.acceptProposedAction()

    @property
    def activeFolder(self):
        activeFolder = self.settings.value("activeFolder", os.path.expanduser("~"))
        if not os.path.isdir(activeFolder):
            activeFolder = os.path.expanduser("~")
        return activeFolder

    def newFont(self):
        fontPath, fileType = QFileDialog.getSaveFileName(
            self,
            "New Font...",
            os.path.join(self.activeFolder, "Untitled"),
            ";;".join(fileTypesMapping),
        )

        if not fontPath:
            # User cancelled
            return

        fontPath = getFontPath(fontPath, fileType, fileTypesMapping)

        self.settings.setValue("activeFolder", os.path.dirname(fontPath))

        # Create a new empty project on disk
        try:
            asyncio.run(createNewFont(fontPath))
        except Exception as e:
            showMessageDialog("The new font could not be saved", repr(e))
            return

        if os.path.exists(fontPath):
            openFile(fontPath, self.port)

    def messageFromServer(self, item):
        action, path, options = item
        handler = getattr(self, action, None)
        if handler is not None:
            handler(path, options)

    def exportAs(self, path, options):
        sourcePath = pathlib.Path(path)
        fileExtension = options["format"]

        wFlags = self.windowFlags()
        self.setWindowFlags(wFlags | Qt.WindowType.WindowStaysOnTopHint)
        self.show()
        self.setWindowFlags(wFlags)
        self.show()

        destPath, fileType = QFileDialog.getSaveFileName(
            self,
            "Export font...",
            os.path.join(self.activeFolder, sourcePath.stem),
            exportExtensionMapping["." + fileExtension],
        )

        if not destPath:
            # User cancelled
            return

        destPath = getFontPath(destPath, fileType, exportFileTypesMapping)

        self.settings.setValue("activeFolder", os.path.dirname(destPath))

        destPath = pathlib.Path(destPath)

        if sourcePath == destPath:
            showMessageDialog(
                "Cannot export font",
                "The destination file cannot be the same as the source file",
            )
            return

        self.doExportAs(sourcePath, destPath, fileExtension)

    def doExportAs(self, sourcePath, destPath, fileExtension):
        logFilePath = tempfile.NamedTemporaryFile().name

        exportProcess = multiprocessing.Process(
            target=exportFontToPath,
            args=(sourcePath, destPath, fileExtension, logFilePath),
        )

        cancelled = False

        def cancelExport():
            nonlocal cancelled
            cancelled = True
            os.kill(exportProcess.pid, signal.SIGINT)

        progressDialog = QProgressDialog(
            f"Exporting “{os.path.basename(destPath)}”", "Cancel", 0, 0
        )
        progressCancelButton = QPushButton("Cancel")
        progressCancelButton.clicked.connect(cancelExport)

        progressDialog.setCancelButton(progressCancelButton)
        progressDialog.setWindowTitle(f"Export as {fileExtension}")
        progressDialog.show()

        exportProcess.start()

        def exportFinished():
            if cancelled:
                return

            progressDialog.cancel()

            try:
                if exportProcess.exitcode:
                    with open(logFilePath, encoding="utf-8") as logFile:
                        logFile.seek(0)
                        logData = logFile.read()
                        logLines = logData.splitlines()
                        infoText = (
                            logLines[-1] if logLines else "The reason is not clear."
                        )
                        showMessageDialog(
                            "The font could not be exported",
                            infoText,
                            detailedText=logData,
                        )
            finally:
                os.unlink(logFilePath)

        def exportProcessJoin():
            exportProcess.join()
            callInMainThread(exportFinished)

        callInNewThread(exportProcessJoin)

    def checkForUpdate(self, msDelay):
        QTimer.singleShot(msDelay, lambda: callInNewThread(self._checkForUpdate))

    def _checkForUpdate(self):
        if "dev" in fontraVersion:
            return

        print(f"Checking for update on {datetime.now()}")

        latestVersion, downloadURL = fetchLatestReleaseInfo()

        if downloadURL is not None and latestVersion != fontraVersion:
            callInMainThread(
                self.downloadButton.setText, "‼️ A new version is available ‼️"
            )
        else:
            # Try again in a bit more than a day
            hours = 24 + 4 * random()
            minutes = hours * 60
            seconds = minutes * 60
            msDelay = seconds * 1000
            callInMainThread(self.checkForUpdate, int(msDelay))

    def goToLatestDownload(self):
        _, downloadURL = fetchLatestReleaseInfo()

        if downloadURL is None:
            downloadURL = latestReleasePageURL

        webbrowser.open(downloadURL)


def fetchLatestReleaseInfo() -> tuple[str, str | None]:
    try:
        return _fetchLatestReleaseInfo()
    except Exception:
        print("Failed to fetch release info")
        traceback.print_exc()

    return "0.0.0", None


def _fetchLatestReleaseInfo() -> tuple[str, str | None]:
    url = "https://api.github.com/repos/fontra/fontra-pak/releases/latest"
    response = urlopen(url)
    latestRelease = json.loads(response.read().decode("utf-8"))
    latestVersion = latestRelease["tag_name"]

    assetNamePart = None
    match sys.platform:
        case "darwin":
            assetNamePart = "macOS"
        case "win32":
            assetNamePart = "Windows"

    if assetNamePart is None:
        return latestVersion, None

    [assetInfo] = [
        asset for asset in latestRelease["assets"] if assetNamePart in asset["name"]
    ]

    return latestVersion, assetInfo["browser_download_url"]


def exportFontToPath(sourcePath, destPath, fileExtension, logFilePath):
    logFile = open(logFilePath, "w")
    sys.stdout = sys.stderr = logFile

    try:
        asyncio.run(exportFontToPathAsync(sourcePath, destPath, fileExtension))
    finally:
        logFile.flush()


async def exportFontToPathAsync(sourcePath, destPath, fileExtension):
    sourcePath = pathlib.Path(sourcePath)
    destPath = pathlib.Path(destPath)

    sourceBackend = getFileSystemBackend(sourcePath)

    if fileExtension in {"ttf", "otf"}:
        from fontra.workflow.workflow import Workflow

        continueOnError = False

        # For now, we drop discrete axes, and only export the default
        axes = await sourceBackend.getAxes()
        discreteAxisNames = [
            axis.name for axis in axes.axes if isinstance(axis, DiscreteFontAxis)
        ]

        dropDiscreteAxes = (
            [dict(filter="subset-axes", dropAxisNames=discreteAxisNames)]
            if discreteAxisNames
            else []
        )

        config = dict(
            steps=dropDiscreteAxes
            + [
                dict(filter="decompose-composites", onlyVariableComposites=True),
                dict(filter="drop-unreachable-glyphs"),
                dict(
                    output="compile-fontmake",
                    destination=destPath.name,
                    options={"verbose": "DEBUG", "overlaps-backend": "pathops"},
                ),
            ]
        )

        workflow = Workflow(config=config, parentDir=sourcePath.parent)

        async with workflow.endPoints(sourceBackend) as endPoints:
            assert endPoints.endPoint is not None

            for output in endPoints.outputs:
                await output.process(destPath.parent, continueOnError=continueOnError)
    else:
        destBackend = newFileSystemBackend(destPath)
        async with aclosing(sourceBackend), aclosing(destBackend):
            await copyFont(sourceBackend, destBackend)


async def createNewFont(fontPath):
    # Create a new empty project on disk
    destBackend = newFileSystemBackend(fontPath)
    await populateBackend(destBackend)
    await destBackend.aclose()


def openFile(path, port):
    path = pathlib.Path(path).resolve()
    assert path.is_absolute()
    parts = list(path.parts)
    if not path.drive:
        assert parts[0] == "/"
        del parts[0]
    path = "/".join(quote(part, safe="") for part in parts)

    webbrowser.open(f"http://localhost:{port}/fontoverview.html?project={path}")


def showMessageDialog(
    message, infoText, detailedText=None, icon=QMessageBox.Icon.Warning
):
    dialog = QMessageBox()
    if icon is not None:
        dialog.setIcon(icon)
    dialog.setText(message)
    dialog.setInformativeText(infoText)
    if detailedText is not None:
        dialog.setStyleSheet("QTextEdit { font-weight: regular; }")
        dialog.setDetailedText(detailedText)
    dialog.exec()


@dataclass
class FontraPakExportManager:
    appQueue: multiprocessing.Queue

    def getSupportedExportFormats(self):
        return [typ for (_name, typ) in exportFileTypes]

    async def exportAs(self, projectIdentifier, options):
        self.appQueue.put(("exportAs", projectIdentifier, options))


def runFontraServer(host, port, queue):
    logging.basicConfig(
        format="%(asctime)s %(name)-17s %(levelname)-8s %(message)s",
        level=logging.INFO,
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    projectManager = FileSystemProjectManager(
        None, exportManager=FontraPakExportManager(queue)
    )

    server = FontraServer(
        host=host,
        httpPort=port,
        projectManager=projectManager,
        versionToken=secrets.token_hex(4),
    )
    server.setup()
    server.run(showLaunchBanner=False)


class CallInMainThreadScheduler(QObject):
    signal = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.signal.connect(self.receive)
        self.items = {}

    def receive(self, identifier):
        assert threading.current_thread() is threading.main_thread()
        function, args, kwargs = self.items.pop(identifier)
        function(*args, **kwargs)

    def schedule(self, function, args, kwargs):
        identifier = secrets.token_hex(4)
        self.items[identifier] = function, args, kwargs
        self.signal.emit(identifier)


_callInMainThreadScheduler = CallInMainThreadScheduler()


def callInMainThread(function, *args, **kwargs):
    _callInMainThreadScheduler.schedule(function, args, kwargs)


def callInNewThread(function, *args, **kwargs):
    thread = threading.Thread(target=function, args=args, kwargs=kwargs)
    thread.start()
    return thread


def queueGetter(queue, callback):
    while True:
        item = queue.get()
        if item is None:
            break

        callInMainThread(callback, item)


def main():
    queue = multiprocessing.Queue()
    host = "localhost"
    port = findFreeTCPPort(host=host)
    serverProcess = multiprocessing.Process(
        target=runFontraServer, args=(host, port, queue)
    )
    serverProcess.start()

    app = FontraApplication(sys.argv, port)

    def cleanup():
        queue.put(None)
        thread.join()
        process = psutil.Process(serverProcess.pid)
        for p in [process] + process.children(recursive=True):
            if sys.platform != "win32":
                p.send_signal(psutil.signal.SIGINT)
            else:
                p.terminate()

    app.aboutToQuit.connect(cleanup)

    mainWindow = FontraMainWidget(port)

    thread = callInNewThread(queueGetter, queue, mainWindow.messageFromServer)

    mainWindow.show()

    if "test-startup" in sys.argv:

        def delayedQuit():
            print("test-startup")
            app.quit()

        QTimer.singleShot(1500, delayedQuit)

    sys.exit(app.exec())


if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()

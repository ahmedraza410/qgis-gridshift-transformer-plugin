from qgis.core import QgsApplication
from qgis.PyQt.QtWidgets import QAction

from .gui.dialog import GridShiftDialog
from .processing.provider import GridShiftProvider


class GridShiftPlugin:
    def __init__(self, iface):
        self.iface = iface
        self.action = None
        self.provider = None
        self.dialog = None

    def initGui(self):
        self.action = QAction("Grid Shift Transformer...", self.iface.mainWindow())
        self.action.triggered.connect(self.show_dialog)
        self.iface.addPluginToVectorMenu("Grid Shift Transformer", self.action)
        self.provider = GridShiftProvider()
        QgsApplication.processingRegistry().addProvider(self.provider)

    def unload(self):
        self.iface.removePluginVectorMenu("Grid Shift Transformer", self.action)
        QgsApplication.processingRegistry().removeProvider(self.provider)

    def show_dialog(self):
        self.dialog = GridShiftDialog(self.iface.mainWindow())
        self.dialog.exec_()

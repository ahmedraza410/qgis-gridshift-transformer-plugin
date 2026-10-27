"""Dialog: pick layer, pipeline, target CRS, validate, run, show control-point residuals."""
from qgis.core import QgsMapLayerProxyModel, QgsProject, QgsVectorLayer, QgsWkbTypes
from qgis.gui import QgsMapLayerComboBox, QgsProjectionSelectionWidget, QgsFileWidget
from qgis.PyQt.QtWidgets import (
    QDialog, QDialogButtonBox, QFormLayout, QLabel, QPlainTextEdit, QVBoxLayout,
)

from ..core.controlpoints import load_csv, residuals
from ..core.pipeline import PipelineError, validate_pipeline
from ..core.report import build_report, write_report
from ..core.transform import build_transform


class GridShiftDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Grid Shift Transformer")
        self.setMinimumWidth(560)
        self.layer_box = QgsMapLayerComboBox(self)
        self.layer_box.setProject(QgsProject.instance())
        self.layer_box.setFilters(QgsMapLayerProxyModel.VectorLayer)
        self.layer_box.setEnabled(True)
        self.target = QgsProjectionSelectionWidget()
        self.pipeline = QPlainTextEdit()
        self.pipeline.setPlaceholderText("+proj=pipeline +step ... +proj=hgridshift +grids=... ")
        self.control_csv = QgsFileWidget()
        self.control_csv.setFilter("CSV (*.csv)")
        self.report_path = QgsFileWidget()
        self.report_path.setStorageMode(QgsFileWidget.SaveFile)
        self.report_path.setFilter("JSON (*.json)")
        self.status = QLabel()
        self.status.setWordWrap(True)

        form = QFormLayout()
        form.addRow("Input layer", self.layer_box)
        form.addRow("Target CRS", self.target)
        form.addRow("PROJ pipeline", self.pipeline)
        form.addRow("Control points (optional)", self.control_csv)
        form.addRow("Report (optional)", self.report_path)
        buttons = QDialogButtonBox()
        self.validate_btn = buttons.addButton("Validate", QDialogButtonBox.ActionRole)
        self.run_btn = buttons.addButton("Run", QDialogButtonBox.AcceptRole)
        buttons.addButton(QDialogButtonBox.Close)
        self.validate_btn.clicked.connect(self.validate)
        self.run_btn.clicked.connect(self.run)
        buttons.rejected.connect(self.reject)
        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(self.status)
        layout.addWidget(buttons)

    def _transform(self):
        layer = self.layer_box.currentLayer()
        if layer is None:
            raise PipelineError("Select an input layer.")
        if not self.target.crs().isValid():
            raise PipelineError("Select a target CRS.")
        return layer, build_transform(layer.crs(), self.target.crs(), self.pipeline.toPlainText().strip())

    def validate(self):
        try:
            info, problems = validate_pipeline(self.pipeline.toPlainText().strip())
            if problems:
                raise PipelineError("\n".join(problems))
            layer, transform = self._transform()
            msg = f"OK: {' > '.join(info.operations)}; grids: {', '.join(info.grids) or 'none'}"
            if self.control_csv.filePath():
                res = residuals(transform, load_csv(self.control_csv.filePath()))
                msg += f"\nControl points: n={res.count}, max={res.max_m:.4f}, rms={res.rms_m:.4f}"
            self.status.setText(msg)
            return layer, transform
        except (PipelineError, OSError, KeyError, ValueError) as exc:
            self.status.setText(f"Problem: {exc}")
            return None

    def run(self):
        result = self.validate()
        if result is None:
            return
        layer, transform = result
        out = QgsVectorLayer(
            f"{QgsWkbTypes.displayString(layer.wkbType())}?crs={self.target.crs().authid()}",
            f"{layer.name()} (grid shift)", "memory")
        out.dataProvider().addAttributes(layer.fields())
        out.updateFields()
        feats = []
        for f in layer.getFeatures():
            g = f.geometry()
            g.transform(transform)
            f.setGeometry(g)
            feats.append(f)
        out.dataProvider().addFeatures(feats)
        QgsProject.instance().addMapLayer(out)
        if self.report_path.filePath():
            write_report(build_report(self.pipeline.toPlainText().strip(), layer.crs(),
                                      self.target.crs()), self.report_path.filePath())
        self.status.setText(self.status.text() + f"\nDone: {len(feats)} features.")


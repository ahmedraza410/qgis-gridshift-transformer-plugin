"""Processing algorithm: apply an explicit PROJ pipeline to a vector layer."""
from qgis.core import (
    QgsCoordinateTransform, QgsFeature, QgsFeatureSink, QgsProcessing,
    QgsProcessingAlgorithm, QgsProcessingException, QgsProcessingParameterCrs,
    QgsProcessingParameterFeatureSink, QgsProcessingParameterFeatureSource,
    QgsProcessingParameterString, QgsProcessingProvider,
)

from ..core.pipeline import PipelineError
from ..core.transform import build_transform


class ApplyPipelineAlgorithm(QgsProcessingAlgorithm):
    INPUT, PIPELINE, TARGET, OUTPUT = "INPUT", "PIPELINE", "TARGET_CRS", "OUTPUT"

    def name(self): return "applypipeline"
    def displayName(self): return "Apply PROJ pipeline (grid shift)"
    def group(self): return "Transformation"
    def groupId(self): return "transformation"
    def createInstance(self): return ApplyPipelineAlgorithm()

    def shortHelpString(self):
        return ("Transforms features with an explicit PROJ pipeline. Fails if a grid is "
                "missing instead of falling back to a ballpark transformation.")

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterFeatureSource(
            self.INPUT, "Input layer", [QgsProcessing.TypeVectorAnyGeometry]))
        self.addParameter(QgsProcessingParameterString(
            self.PIPELINE, "PROJ pipeline", multiLine=True))
        self.addParameter(QgsProcessingParameterCrs(self.TARGET, "Target CRS"))
        self.addParameter(QgsProcessingParameterFeatureSink(self.OUTPUT, "Transformed"))

    def processAlgorithm(self, parameters, context, feedback):
        source = self.parameterAsSource(parameters, self.INPUT, context)
        pipeline = self.parameterAsString(parameters, self.PIPELINE, context)
        target = self.parameterAsCrs(parameters, self.TARGET, context)
        try:
            transform = build_transform(source.sourceCrs(), target, pipeline)
        except PipelineError as exc:
            raise QgsProcessingException(str(exc))
        sink, dest = self.parameterAsSink(
            parameters, self.OUTPUT, context, source.fields(), source.wkbType(), target)
        total = source.featureCount() or 1
        for i, feat in enumerate(source.getFeatures()):
            if feedback.isCanceled():
                break
            out = QgsFeature(feat)
            geom = feat.geometry()
            if geom and not geom.isNull():
                try:
                    geom.transform(transform)
                except Exception as exc:
                    feedback.reportError(f"Feature {feat.id()}: {exc}")
                    continue
                out.setGeometry(geom)
            sink.addFeature(out, QgsFeatureSink.FastInsert)
            feedback.setProgress(100 * i / total)
        return {self.OUTPUT: dest}


class GridShiftProvider(QgsProcessingProvider):
    def id(self): return "gridshift"
    def name(self): return "Grid Shift Transformer"
    def loadAlgorithms(self): self.addAlgorithm(ApplyPipelineAlgorithm())

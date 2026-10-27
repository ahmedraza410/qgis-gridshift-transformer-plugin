def classFactory(iface):
    from .plugin import GridShiftPlugin
    return GridShiftPlugin(iface)

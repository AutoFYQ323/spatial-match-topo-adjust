# -*- coding: utf-8 -*-

import os

from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction

from .cdet_core import CDETCore
from .cdet_dialog import CDETDialog
from .i18n import language_changed, tr

# Repository name stays English. The menu, tooltip, and window use this source so each language sees its own wording.
PRODUCT_MSGID = "空间匹配与拓扑调整"


class Plugin(object):
    def __init__(self, iface):
        self.iface = iface
        self.action = None
        self.dialog = None
        self.core = CDETCore(iface)
        self._menu = ""
        try:
            from qgis.core import QgsSettings
            from .settings_compat import migrate_legacy_settings
            migrate_legacy_settings(QgsSettings())
        except Exception:  # nosec B110
            pass

    def initGui(self):
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.png")
        self.action = QAction(
            QIcon(icon_path),
            tr(PRODUCT_MSGID),
            self.iface.mainWindow(),
        )
        self.action.setToolTip(tr(PRODUCT_MSGID))
        self.action.triggered.connect(self.run)
        self._menu = tr(PRODUCT_MSGID)
        self.iface.addPluginToMenu(self._menu, self.action)
        self.iface.addToolBarIcon(self.action)
        language_changed().connect(self._on_language)

    def _on_language(self, *_args):
        if self.action is None:
            return
        self.iface.removePluginMenu(self._menu, self.action)
        self.action.setText(tr(PRODUCT_MSGID))
        self.action.setToolTip(tr(PRODUCT_MSGID))
        self._menu = tr(PRODUCT_MSGID)
        self.iface.addPluginToMenu(self._menu, self.action)

    def unload(self):
        try:
            language_changed().disconnect(self._on_language)
        except Exception:  # nosec B110
            pass
        if self.action is not None:
            self.iface.removePluginMenu(self._menu, self.action)
            self.iface.removeToolBarIcon(self.action)
            self.action = None
        if self.dialog is not None:
            self.dialog.close()
            self.dialog.deleteLater()
            self.dialog = None

    def run(self):
        if self.dialog is None:
            self.dialog = CDETDialog(self.iface, self.core)
        self.dialog.show()
        self.dialog.raise_()
        self.dialog.activateWindow()

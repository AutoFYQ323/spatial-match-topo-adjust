# -*- coding: utf-8 -*-
"""Small toolbar and filter icons for the main window (appearance only).

Inspired by the KMZ plugin's approach (theme icon, then a drawn letter or
glyph mark; language badge changes with the current language). This module
does not import KMZ code, copy KMZ assets, or touch KMZ settings keys.
Import / export keep the three scheme libraries separate; the main window uses a shared entry.
"""

from qgis.PyQt.QtCore import Qt, QLineF, QRectF, QSize
from qgis.PyQt.QtGui import QColor, QFont, QFontMetrics, QIcon, QPainter, QPainterPath, QPen, QPixmap
from qgis.PyQt.QtWidgets import QComboBox, QSizePolicy

from .i18n import current_language, tr

def _qattr(owner, name):
    if hasattr(owner, name):
        return getattr(owner, name)
    return None


def _transparent():
    v = _qattr(Qt, "transparent")
    if v is not None:
        return v
    return Qt.GlobalColor.transparent


def _no_pen():
    v = _qattr(Qt, "NoPen")
    if v is not None:
        return v
    return Qt.PenStyle.NoPen


def _no_brush():
    v = _qattr(Qt, "NoBrush")
    if v is not None:
        return v
    return Qt.BrushStyle.NoBrush


def _solid_line():
    v = _qattr(Qt, "SolidLine")
    if v is not None:
        return v
    return Qt.PenStyle.SolidLine


def _round_cap():
    v = _qattr(Qt, "RoundCap")
    if v is not None:
        return v
    return Qt.PenCapStyle.RoundCap


def _round_join():
    v = _qattr(Qt, "RoundJoin")
    if v is not None:
        return v
    return Qt.PenJoinStyle.RoundJoin


def _align_center():
    v = _qattr(Qt, "AlignCenter")
    if v is not None:
        return v
    return Qt.AlignmentFlag.AlignCenter


def _no_focus():
    v = _qattr(Qt, "NoFocus")
    if v is not None:
        return v
    return Qt.FocusPolicy.NoFocus


def _elide_none():
    v = _qattr(Qt, "ElideNone")
    if v is not None:
        return v
    return Qt.TextElideMode.ElideNone


def _pointing_hand():
    v = _qattr(Qt, "PointingHandCursor")
    if v is not None:
        return v
    return Qt.CursorShape.PointingHandCursor



# Short self-marks drawn on the language button (not UI copy).
_LANG_MARKS = {
    "zh": "中",
    "en": "EN",
    "es": "ES",
    "fr": "FR",
    "ar": "ع",
    "it": "IT",
    "de": "DE",
    "ja": "あ",
    "ko": "한",
}

ACTION_BTN_H = 28
FILTER_BTN_H = 48
ICON_BTN_SIZE = 28


def theme_or_letter(theme_name, letter, color, size=24):
    """QGIS theme icon when present, otherwise a letter badge."""
    if theme_name:
        try:
            from qgis.core import QgsApplication
            icon = QgsApplication.getThemeIcon(theme_name)
            if icon is not None and not icon.isNull():
                return icon
        except Exception:
            pass
    return letter_badge(letter, color, size)


def letter_badge(letter, color, size=24):
    pix = QPixmap(size, size)
    pix.fill(_transparent())
    painter = QPainter(pix)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setPen(_no_pen())
    painter.setBrush(QColor(color))
    rad = max(2.0, size * 0.16)
    painter.drawRoundedRect(QRectF(0, 0, size - 1, size - 1), rad, rad)
    painter.setPen(QColor("#ffffff"))
    font = QFont()
    font.setBold(True)
    text = str(letter or "?")
    font.setPixelSize(size - 8 if len(text) <= 1 else max(8, size - 12))
    painter.setFont(font)
    painter.drawText(pix.rect(), _align_center(), text)
    painter.end()
    return QIcon(pix)


def language_icon(lang=None, size=24):
    code = lang or current_language() or "en"
    mark = _LANG_MARKS.get(code, (code or "EN")[:2].upper())
    return letter_badge(mark, "#6a1b9a", size)


def help_icon(size=24):
    return theme_or_letter("mActionHelpContents.svg", "?", "#455a64", size)


def import_icon(size=24):
    return theme_or_letter("mActionSharingImport.svg", "入", "#1565c0", size)


def export_icon(size=24):
    return theme_or_letter("mActionSharingExport.svg", "出", "#2e7d32", size)


def _stroke(painter, width):
    pen = QPen(QColor("#ffffff"), width, _solid_line(), _round_cap(), _round_join())
    painter.setPen(pen)
    painter.setBrush(_no_brush())


def filter_icon(kind, size=18, color="#1565c0"):
    """Simple geometry / group marks for the layer-list filter buttons."""
    colors = {
        "point": "#1565c0",
        "line": "#ef6c00",
        "polygon": "#6a1b9a",
        "all": "#546e7a",
        "group": "#2e7d32",
    }
    bg = QColor(colors.get(kind, color))
    pix = QPixmap(size, size)
    pix.fill(_transparent())
    painter = QPainter(pix)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setPen(_no_pen())
    painter.setBrush(bg)
    painter.drawRoundedRect(QRectF(0, 0, size - 1, size - 1), size * 0.18, size * 0.18)
    painter.save()
    painter.scale(size / 16.0, size / 16.0)
    white = QColor("#ffffff")
    if kind == "point":
        painter.setBrush(white)
        painter.drawEllipse(QRectF(5.0, 5.0, 6.0, 6.0))
    elif kind == "line":
        _stroke(painter, 1.4)
        painter.drawLine(QLineF(3.0, 11.0, 13.0, 5.0))
    elif kind == "polygon":
        painter.setBrush(white)
        path = QPainterPath()
        path.moveTo(8.0, 3.0)
        path.lineTo(13.0, 12.0)
        path.lineTo(3.0, 12.0)
        path.closeSubpath()
        painter.drawPath(path)
    elif kind == "group":
        _stroke(painter, 1.15)
        painter.drawRoundedRect(QRectF(2.8, 5.2, 10.4, 7.4), 0.6, 0.6)
        painter.drawRoundedRect(QRectF(2.8, 3.4, 4.8, 2.2), 0.5, 0.5)
    else:  # all
        painter.setBrush(white)
        painter.drawEllipse(QRectF(3.0, 3.0, 4.0, 4.0))
        painter.drawEllipse(QRectF(9.0, 3.0, 4.0, 4.0))
        painter.drawEllipse(QRectF(6.0, 9.0, 4.0, 4.0))
    painter.restore()
    painter.end()
    return QIcon(pix)


def mode_icon(kind, size=20):
    """Prefer the plugin icons/ PNG; fall back to a drawn mark. Not taken from KMZ or LPT files."""
    try:
        from .icons import load_icon
    except ImportError:
        from icons import load_icon
    name = {"snap": "snap", "field": "field", "move": "move"}.get(kind)
    if name:
        icon = load_icon(name)
        if not icon.isNull():
            return icon
    return _drawn_mode_icon(kind, size)


def _drawn_mode_icon(kind, size=20):
    """Drawn fallback used only if the PNG is missing."""
    colors = {
        "snap": "#1565c0",
        "field": "#2e7d32",
        "move": "#6a1b9a",
    }
    bg = QColor(colors.get(kind, "#546e7a"))
    pix = QPixmap(size, size)
    pix.fill(_transparent())
    painter = QPainter(pix)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setPen(_no_pen())
    painter.setBrush(bg)
    painter.drawRoundedRect(QRectF(0, 0, size - 1, size - 1), size * 0.18, size * 0.18)
    painter.save()
    painter.scale(size / 16.0, size / 16.0)
    white = QColor("#ffffff")
    if kind == "snap":
        # two bars with a connecting "snap" tick
        _stroke(painter, 1.35)
        painter.setPen(QPen(white, 1.35, _solid_line(), _round_cap(), _round_join()))
        painter.setBrush(_no_brush())
        painter.drawLine(QLineF(3.2, 5.0, 8.2, 5.0))
        painter.drawLine(QLineF(7.8, 11.0, 12.8, 11.0))
        painter.drawLine(QLineF(8.0, 5.0, 8.0, 11.0))
        painter.setPen(_no_pen())
        painter.setBrush(white)
        painter.drawEllipse(QRectF(6.6, 3.8, 2.6, 2.6))
        painter.drawEllipse(QRectF(6.6, 9.8, 2.6, 2.6))
    elif kind == "field":
        # a small "tag / field" plate
        painter.setPen(QPen(white, 1.2, _solid_line(), _round_cap(), _round_join()))
        painter.setBrush(_no_brush())
        path = QPainterPath()
        path.moveTo(3.2, 4.2)
        path.lineTo(9.6, 4.2)
        path.lineTo(13.0, 8.0)
        path.lineTo(9.6, 11.8)
        path.lineTo(3.2, 11.8)
        path.closeSubpath()
        painter.drawPath(path)
        painter.setPen(_no_pen())
        painter.setBrush(white)
        painter.drawEllipse(QRectF(5.0, 6.8, 2.2, 2.2))
    else:
        # move: two opposing chevrons
        painter.setPen(QPen(white, 1.5, _solid_line(), _round_cap(), _round_join()))
        painter.setBrush(_no_brush())
        painter.drawLine(QLineF(4.0, 5.2, 8.0, 3.4))
        painter.drawLine(QLineF(8.0, 3.4, 12.0, 5.2))
        painter.drawLine(QLineF(4.0, 10.8, 8.0, 12.6))
        painter.drawLine(QLineF(8.0, 12.6, 12.0, 10.8))
        painter.drawLine(QLineF(8.0, 3.8, 8.0, 12.2))
    painter.restore()
    painter.end()
    return QIcon(pix)


def style_icon_button(button, icon, tip_src):
    button.setText("")
    button.setIcon(icon)
    button.setIconSize(QSize(20, 20))
    button.setFixedHeight(ICON_BTN_SIZE)
    button.setMinimumWidth(ICON_BTN_SIZE)
    button.setMaximumWidth(16777215)
    button.setToolTip(tr(tip_src))
    button.setProperty("tip", tip_src)
    button.setCursor(_pointing_hand())
    button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
    button.setObjectName("iconToolBtn")
    button.setFocusPolicy(_no_focus())
    button.setCheckable(False)
    button.setFlat(True)
    button.setAutoDefault(False)
    button.setDefault(False)


FILTER_TITLE_COLORS = {
    "point": "#1060c0",
    "line": "#e86800",
    "polygon": "#681898",
    "all": "#506878",
    "group": "#287830",
}


def style_filter_button(button, kind, name_src):
    try:
        from .icons import load_icon
    except ImportError:
        from icons import load_icon
    icon = load_icon(kind)
    if icon.isNull():
        icon = filter_icon(kind, size=20)
    button.setIcon(icon)
    button.setIconSize(QSize(20, 20))
    try:
        from qgis.PyQt.QtCore import Qt as _Qt
        button.setToolButtonStyle(_Qt.ToolButtonTextUnderIcon)
    except Exception:
        pass
    color = FILTER_TITLE_COLORS.get(kind, "#1060c0")
    font = button.font()
    font.setPointSize(9)
    font.setBold(True)
    button.setFont(font)
    button.setText(tr(name_src))
    button.setProperty("msgid", name_src)
    button.setProperty("filter_kind", kind)
    button.setToolTip(tr(name_src))
    button.setProperty("tip", name_src)
    button.setCursor(_pointing_hand())
    button.setObjectName("layerFilterBtn")
    button.setStyleSheet(
        "QToolButton#layerFilterBtn { color: %s; font-size: 9pt; font-weight: 700; }"
        % color
    )
    button.setFixedHeight(FILTER_BTN_H)
    # A long translation must not push the column, or the window jumps when the language changes.
    button.setMinimumWidth(0)
    button.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
    button.setCheckable(True)
    button.setAutoRaise(True)
    try:
        button.setAutoDefault(False)
        button.setDefault(False)
    except Exception:
        pass


def style_param_label(label, short_src=None, full_src=None):
    """One-line bold label. Full wording stays on the tooltip so a narrow column cannot overlap the next title."""
    font = label.font()
    font.setBold(True)
    label.setFont(font)
    label.setWordWrap(False)
    label.setMinimumWidth(0)
    label.setFixedHeight(22)
    label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Fixed)
    label.setStyleSheet('font-size: 12px; font-weight: 700; color: #212529;')
    src = short_src or full_src
    if src:
        label.setText(tr(src))
        label.setProperty("msgid", src)
    tip_src = full_src or short_src
    if tip_src:
        label.setToolTip(tr(tip_src))
        label.setProperty("tip", tip_src)


def configure_fit_combo(combo):
    """Closed combo stays within the right column; the popup may grow."""
    combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
    combo.setMinimumWidth(0)
    combo.setMaximumWidth(16777215)
    try:
        combo.setSizeAdjustPolicy(QComboBox.AdjustToMinimumContentsLengthWithIcon)
    except Exception:
        pass
    try:
        combo.setMinimumContentsLength(3)
    except Exception:
        pass
    try:
        combo.view().setTextElideMode(_elide_none())
    except Exception:
        pass
    if getattr(combo, "_cdet_popup_patched", False):
        return combo
    original = combo.showPopup

    def _show():
        try:
            fm = combo.fontMetrics()
            widest = combo.width()
            for i in range(combo.count()):
                text = combo.itemText(i)
                if hasattr(fm, "horizontalAdvance"):
                    w = fm.horizontalAdvance(text)
                else:
                    w = fm.boundingRect(text).width()
                widest = max(widest, w + 36)
            combo.view().setMinimumWidth(int(widest))
        except Exception:
            pass
        original()

    combo.showPopup = _show
    combo._cdet_popup_patched = True
    return combo


def param_block(label, widget, extra=None):
    """Title above the control (one parameter)."""
    from qgis.PyQt.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout

    box = QWidget()
    lay = QVBoxLayout(box)
    lay.setContentsMargins(0, 0, 0, 0)
    lay.setSpacing(3)
    lay.addWidget(label)
    if extra is None:
        lay.addWidget(widget)
    else:
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(6)
        row.addWidget(widget, 1)
        row.addWidget(extra)
        lay.addLayout(row)
    return box

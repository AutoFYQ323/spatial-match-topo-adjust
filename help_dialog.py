# -*- coding: utf-8 -*-
"""Four-tab help. Visible copy goes through tr(); Chinese is the source."""

import html

from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QFont
from qgis.PyQt.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QScrollArea,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from .i18n import localize_button_box, tr


# Short key phrases only. Never wrap a whole paragraph in red.
HIGHLIGHT_PHRASES = (
    "Spatial Match & Topo Adjust",
    "700×650",
    "不是报错",
    "不会因为当前页或吸附方案库里没有方案而禁用",
    "也不会因此切换当前功能",
    "阿拉伯语只更换文字，不翻转界面",
    "下拉框不能用鼠标滚轮改值",
    "窗口尺寸不变",
    "部分特殊检测不需要参考图层",
    "结果写到临时图层，不直接改原图层几何",
    "不会自动改成「标准」",
    "不是图层个数",
    "方案匹配和查看自检使用图层真名",
)


def _apply_help_highlights(text):
    out = html.escape(text or "")
    phrases = []
    for src in HIGHLIGHT_PHRASES:
        mapped = tr(src)
        if mapped:
            phrases.append(mapped)
        phrases.append(src)
    # Longer phrases first so a short overlap cannot eat a longer lock phrase.
    seen = set()
    ordered = []
    for ph in sorted(phrases, key=len, reverse=True):
        if ph and ph not in seen:
            seen.add(ph)
            ordered.append(ph)
    for ph in ordered:
        esc = html.escape(ph)
        if esc and esc in out:
            out = out.replace(esc, '<span style="color:#c2185b">%s</span>' % esc)
    return out


HELP_PAGES = (
    (
        "主页",
        (
            "本插件名为空间匹配与拓扑调整（英文名 Spatial Match & Topo Adjust）。同一窗口内切换三种功能：吸附检测、字段命名、移动。窗口标题、插件菜单和提示都随当前界面语言显示，不会夹杂另一种语言。",
            "每次重新启动 QGIS 后，窗口都按 700×650 打开。打开之后若你改了大小，只在本次 QGIS 运行期间记住，不写入本机设置。切换功能、切换语言或点选图层都不会再把窗口拉大或缩小，标题也不会互相叠到一起。左侧两个图层列表等宽，右侧参数列较窄，三列大约按 5∶2（两列列表 1∶1）拉伸。",
            "左右两个图层列各套一圈与右列参数区同类的浅色细边框，包住该列标题行、列表和底部筛钮，不包窗口顶栏、右列中区参数和底栏。列表不再套在已撤的「图层选择」分组框里。",
            "列标题左侧有图标。筛钮图标下方显示当前语言标题：吸附检测和移动是点、线、面、全部；字段命名是点、线、面、图层组。图层组只用于筛选，不会在列表里增加图层组行。标题不得裁切，也不得盖住列表最后一行。",
            "列表中图层名后可显示要素个数，仅供查看。方案匹配和查看自检使用图层真名，不从带个数的显示文字反解析。",
            "有分类的图层，行前有 ◆◆ 标记，标题加粗并以玫红色显示（不是报错）。点击图层名前的 ◆◆ 选择分类（点行内其它位置只切换这一条的选中，不弹分类）。按住左键拖动多选时也不弹出。分类弹窗按各分类条件现场计要素数，复选和顶栏图层名以「名称(数量)」显示；数量只作展示，不参与方案匹配反解析。尚未做过子集勾选时默认全选，表示整层。",
            "右侧顶栏有语言、帮助、导入、导出。导入和导出在任一功能下都可用，不会因为当前页或吸附方案库里没有方案而禁用，也不会因此切换当前功能。",
            "三个功能的方案库分开存放。导出时先选择「全部导出」或某一个功能；选择单一功能后再勾选该库中的方案。全部导出把三个库的全部方案写入一个总包，只含方案配置，不含图层数据。",
            "导入按文件自动识别并写入对应库。旧版单功能文件、旧总包、以及没有 kind 的旧吸附文件仍可导入；没有 kind 的旧吸附文件只进入吸附库。无法识别的文件会明确失败，不会把总包或旧吸附文件误写入字段或移动库。新导出只使用本版标识。",
            "语言仅在首次尚未保存语言时读取 QGIS 界面语言，再试系统语言；属于本插件九种语言则采用，否则使用英文。您选定之后只使用本插件自己保存的语言，下次打开不再跟随 QGIS。阿拉伯语只更换文字，不翻转界面。切换语言只更换界面用词和筛钮提示，不重建两个图层列表，左右 1∶1 和三列 5∶2 保持不变，列表不得变形。",
            "下拉框不能用鼠标滚轮改值，弹出的列表仍可滚动。容差转盘可以使用滚轮。",
            "底栏始终可见，提供功能切换、刷新和执行。点图层列表的空白处不会取消已经选中的图层。点某一条就选中它，再点一次只取消这一条，不必按住 Ctrl。按住鼠标左键拖动，可以一次选中划过的多条。点刷新会清空选择并重新载入列表。中区标题紧贴对应控件。参数放得下时不出现滚动条；文字更高、放不下时，只在中区内部滚动，窗口尺寸不变。三个模式的方案下拉标题均为「批量方案」。吸附和移动将该组放在中区底部，其余参数在其上方均匀留白，控件保持各自本来的高度，不再互相重叠。",
        ),
    ),
    (
        "吸附检测",
        (
            "吸附检测按容差和空间关系，检查判断图层的要素是否命中参考图层，并可按「提取已吸附」输出已命中或未命中的要素。",
            "标准模式需要参考图层。部分特殊检测不需要参考图层，界面会自行处理。检测方式在右侧列表上方合并为一个下拉：第一项且默认为「标准」，其后为现行特殊检测项，并按当前几何类型过滤。若切换图层后当前特殊项不再适用，回退到「标准」，不会自动改成其它特殊项。该下拉遵守滚轮锁。",
            "中区按钮自上而下各占一行：添加、查看、方案、样式。可把当前图层和参数加入批量方案；用查看管理子任务（按钮只显示短标题「查看」，图层是否齐全写在悬停提示里）；用样式配置结果层符号。",
            "结果写到临时图层，不直接改原图层几何。",
        ),
    ),
    (
        "字段命名",
        (
            "字段命名按空间关系和多匹配规则，从参考要素取值，写入被命名图层的字段，或生成临时图层。",
            "中区按钮布局与吸附、移动不同：第一行是「添加」和「方案」，第二行「查看」通栏。方案下拉标题为「批量方案」，位置仍在中区底部。",
            "筛选「图层组」后，列表显示该组内的图层。该按钮的悬停提示显示组内矢量要素合计，不是图层个数。",
        ),
    ),
    (
        "移动",
        (
            "移动按选定模式把被移要素整段平移，形状不变。先生成预览图层，确认后再写回原图层，不产出筛结果层。",
            "中区按钮自上而下各占一行：添加、方案、查看。方案下拉标题为「批量方案」，该组在中区最底部。",
            "下拉列表随被移图层和参考图层的几何类型变化。仅当两侧都是线时，列表只保留已有的 15 种模式（含「标准」）。",
            "若已保存或导入的方案引用了已从列表撤下的线-线模式，导入会跳过该子任务并明确提示，执行同样失败并跳过，不会自动改成「标准」。请改选这 15 种之一并保存后再运行。",
        ),
    ),
)


class HelpDialog(QDialog):
    def __init__(self, parent=None):
        super(HelpDialog, self).__init__(parent)
        self.setWindowTitle(tr("帮助"))
        self.setMinimumSize(560, 480)
        self.resize(640, 520)
        try:
            self.setWindowFlags(self.windowFlags() | Qt.WindowCloseButtonHint)
        except Exception:
            pass
        try:
            self.setLayoutDirection(Qt.LeftToRight)
        except Exception:
            pass

        base_size = 0
        if parent is not None and parent.font() is not None:
            base_size = parent.font().pointSize()
        if base_size <= 0:
            base_size = self.font().pointSize() if self.font().pointSize() > 0 else 9
        body_font = QFont(self.font())
        body_font.setPointSize(base_size + 4)
        body_font.setBold(True)

        root = QVBoxLayout(self)
        tabs = QTabWidget(self)
        for title, paragraphs in HELP_PAGES:
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setFrameShape(scroll.NoFrame if hasattr(scroll, "NoFrame") else 0)
            try:
                from qgis.PyQt.QtWidgets import QFrame
                scroll.setFrameShape(QFrame.NoFrame)
            except Exception:
                pass
            inner = QWidget()
            lay = QVBoxLayout(inner)
            lay.setContentsMargins(12, 12, 12, 12)
            lay.setSpacing(12)
            for msgid in paragraphs:
                lab = QLabel()
                lab.setWordWrap(True)
                lab.setProperty("msgid", msgid)
                lab.setTextFormat(Qt.RichText)
                lab.setText(_apply_help_highlights(tr(msgid)))
                lab.setFont(body_font)
                lab.setTextInteractionFlags(Qt.TextSelectableByMouse)
                lab.setAlignment(Qt.AlignTop | Qt.AlignLeft)
                lay.addWidget(lab)
            lay.addStretch(1)
            scroll.setWidget(inner)
            tabs.addTab(scroll, tr(title))
        root.addWidget(tabs, 1)

        box = QDialogButtonBox(QDialogButtonBox.Close)
        box.rejected.connect(self.reject)
        try:
            box.accepted.connect(self.accept)
        except Exception:
            pass
        close_btn = box.button(QDialogButtonBox.Close)
        if close_btn is not None:
            close_btn.clicked.connect(self.accept)
        localize_button_box(box)
        root.addWidget(box)

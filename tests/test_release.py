# -*- coding: utf-8 -*-
"""Release checks that do not need QGIS: version, scheme bundle, and the 1.0.0 wording."""
import importlib.util
import pathlib
import re
import sys
import types
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
I18N = ROOT / "i18n"
HAN = re.compile(r"[\u4e00-\u9fff]")

PRODUCT = "空间匹配与拓扑调整"
PHRASE = "窗口尺寸不变"
HELP_KEYS = (
    "本插件名为空间匹配与拓扑调整（英文名 Spatial Match & Topo Adjust）。同一窗口内切换三种功能：吸附检测、字段命名、移动。窗口标题、插件菜单和提示都随当前界面语言显示，不会夹杂另一种语言。",
    "每次重新启动 QGIS 后，窗口都按 700×650 打开。打开之后若你改了大小，只在本次 QGIS 运行期间记住，不写入本机设置。切换功能、切换语言或点选图层都不会再把窗口拉大或缩小，标题也不会互相叠到一起。左侧两个图层列表等宽，右侧参数列较窄，三列大约按 5∶2（两列列表 1∶1）拉伸。",
    "底栏始终可见，提供功能切换、刷新和执行。点图层列表的空白处不会取消已经选中的图层。不按 Ctrl 时，点哪一条，选中的就是哪一条，再点已经选中的那一条也不会取消。按住 Ctrl 再点可以多选或取消其中一条，按住 Shift 再点可以连选一段，按住左键拖过多条则选中划过的那些。点刷新会清空选择并重新载入列表。中区标题紧贴对应控件。参数放得下时不出现滚动条；文字更高、放不下时，只在中区内部滚动，窗口尺寸不变。三个模式的方案下拉标题均为「批量方案」。吸附和移动将该组放在中区底部，其余参数在其上方均匀留白，控件保持各自本来的高度，不再互相重叠。",
    "有分类的图层，行前有 ◆◆ 标记，标题加粗并以玫红色显示（不是报错）。点击图层名前的 ◆◆ 选择分类（点行内其它位置只选中图层，不弹分类，再点也不会取消）。按住 Ctrl、Shift 或拖动多选时也不弹出。分类弹窗按各分类条件现场计要素数，复选和顶栏图层名以「名称(数量)」显示；数量只作展示，不参与方案匹配反解析。尚未做过子集勾选时默认全选，表示整层。",
)


def _load_catalog():
    pkg = types.ModuleType("i18n")
    pkg.__path__ = [str(I18N)]
    sys.modules["i18n"] = pkg

    def _one(name):
        path = I18N / ("%s.py" % name)
        spec = importlib.util.spec_from_file_location("i18n.%s" % name, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules["i18n.%s" % name] = mod
        spec.loader.exec_module(mod)
        return mod

    _one("catalog_data")
    _one("catalog_extra")
    return _one("catalog")


_catalog = _load_catalog()


def _load_scheme_bundle():
    path = ROOT / "scheme_bundle.py"
    spec = importlib.util.spec_from_file_location("scheme_bundle", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_bundle = _load_scheme_bundle()


class TestReleaseMetadata(unittest.TestCase):
    def test_metadata_is_1_0_0(self):
        text = (ROOT / "metadata.txt").read_text(encoding="utf-8")
        self.assertIn("version=1.0.2", text)
        self.assertIn("experimental=False", text)
        self.assertIn("changelog=1.0.2", text)
        self.assertNotIn("2.2.", text)

    def test_bundle_records_1_0_0(self):
        payload = _bundle.make_bundle({}, {}, {}, {})
        self.assertEqual(payload["plugin_version"], "1.0.1")
        self.assertEqual(payload["generator"], "Spatial Match & Topo Adjust")
        self.assertEqual(payload["kind"], "spatial_match_topo_adjust_scheme_bundle")


class TestLanguageIsolation(unittest.TestCase):
    def test_product_name_and_help_exist_in_every_language(self):
        keys = (PRODUCT, PHRASE) + HELP_KEYS
        for lang in ("en", "es", "fr", "ar", "it", "de", "ja", "ko"):
            for key in keys:
                mapped = _catalog.text_for(lang, key)
                self.assertTrue(mapped, "%s missing %s" % (lang, key[:24]))
                self.assertNotEqual(mapped, key)
                if lang not in ("ja",):
                    self.assertIsNone(
                        HAN.search(mapped),
                        "%s still has Chinese in %s" % (lang, key[:24]),
                    )

    def test_help_highlight_phrase_is_inside_the_paragraph(self):
        paragraph = HELP_KEYS[2]
        for lang in ("en", "es", "fr", "ar", "it", "de", "ja", "ko"):
            body = _catalog.text_for(lang, paragraph)
            phrase = _catalog.text_for(lang, PHRASE)
            self.assertIn(phrase, body)

    def test_chinese_source_stays_chinese(self):
        self.assertEqual(_catalog.text_for("zh", PRODUCT), "")


if __name__ == "__main__":
    unittest.main()

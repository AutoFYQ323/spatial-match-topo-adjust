# Spatial Match & Topo Adjust

Snap check, field naming, and whole-feature move for vector layers, in one window.

- **QGIS:** 3.28 through 4.99 (Qt 5 and Qt 6)
- **License:** GNU GPL v2 (see `LICENSE`)
- **Data:** local project layers and files you choose. This plugin does not download data or sign in to a website.

## Install

In QGIS: Plugins → Manage and Install Plugins → Install from ZIP, and choose a zip whose top folder is `spatial_match_topo_adjust`.

Or copy that folder to:

`[QGIS profile]/python/plugins/spatial_match_topo_adjust`

Restart QGIS. The menu name follows the interface language. In English it is **Spatial Match & Topo Adjust**. In Chinese it is **空间匹配与拓扑调整**.

## What you can do

1. **Snap check.** Test whether features on the target layers meet reference layers within a tolerance. A standard test is the default. Optional special checks cover cases such as dangling ends, unsplit crossings, invalid geometry, and polygon inspection. Results can be written to temporary layers.
2. **Field naming.** Write a value from a nearby reference feature onto the source layer, or into a temporary layer. A multi-match rule decides what happens when more than one reference feature qualifies.
3. **Move.** Preview a translation of whole features, then write it back only after you confirm.

The two layer lists on the left are equal width. Click a row to select it. Click that row again to clear only that row. Drag with the left button to add every row the pointer crosses. Clicking empty space does not clear the selection. Refresh clears the selection and reloads the lists. A ◆◆ mark opens category filters for that layer.

Batch schemes for the three tools are stored separately. Import and export are on the top bar in every mode. A bundle can hold all three libraries. Older single-tool files can still be imported.

The window opens at 700×650 each time QGIS starts. A resize is kept only until QGIS exits and is not stored on disk. Switching tool, language, or selection does not resize the window.

Languages: English, 中文, Español, Français, العربية, Italiano, Deutsch, 日本語, and 한국어. Names in the language menu stay in each language. Arabic changes the words only and does not flip the layout.

## Links

- Page: https://yuyouhui.online/tools/qgis/spatial-match-topo-adjust/
- Source: https://github.com/AutoFYQ323/spatial-match-topo-adjust
- Issues: https://github.com/AutoFYQ323/spatial-match-topo-adjust/issues

## Tests without QGIS

From this folder:

```text
python -m unittest tests.test_release
```

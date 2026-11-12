# -*- coding: utf-8 -*-
"""Language codes and translation tables.

Chinese source strings are the keys. EN, ES, FR and AR catalogs are filled in
catalog_data.py. IT, DE, JA and KO are filled in catalog_extra.py.
text_for() returns "" when a line is not translated yet. For non-Chinese UI,
tr() falls back to English, then to the Chinese source if English is missing too.
"""

LANG_ZH = "zh"
LANG_EN = "en"
LANG_ES = "es"
LANG_FR = "fr"
LANG_AR = "ar"
LANG_IT = "it"
LANG_DE = "de"
LANG_JA = "ja"
LANG_KO = "ko"

_LOCALE_PREFIX = (
    ("zh", LANG_ZH),
    ("es", LANG_ES),
    ("fr", LANG_FR),
    ("ar", LANG_AR),
    ("it", LANG_IT),
    ("de", LANG_DE),
    ("ja", LANG_JA),
    ("ko", LANG_KO),
    ("en", LANG_EN),
)

from .catalog_data import AR as DATA_AR
from .catalog_data import EN as DATA_EN
from .catalog_data import ES as DATA_ES
from .catalog_data import FR as DATA_FR
from .catalog_extra import DE as DATA_DE
from .catalog_extra import IT as DATA_IT
from .catalog_extra import JA as DATA_JA
from .catalog_extra import KO as DATA_KO

EN = dict(DATA_EN)
ES = dict(DATA_ES)
FR = dict(DATA_FR)
AR = dict(DATA_AR)
IT = dict(DATA_IT)
DE = dict(DATA_DE)
JA = dict(DATA_JA)
KO = dict(DATA_KO)

# 1.0.0 visible copy. Chinese is the key. Other languages must not fall back to Chinese.
_RELEASE = {
    "en": {
        "空间匹配与拓扑调整": "Spatial Match & Topo Adjust",
        "窗口尺寸不变": "the window size stays the same",
        "本插件名为空间匹配与拓扑调整（英文名 Spatial Match & Topo Adjust）。同一窗口内切换三种功能：吸附检测、字段命名、移动。窗口标题、插件菜单和提示都随当前界面语言显示，不会夹杂另一种语言。":
            "This plugin is Spatial Match & Topo Adjust. Three tools share one window: snap check, field naming, and move. The window title, plugin menu, and prompts follow the current interface language and do not mix in another language.",
        "每次重新启动 QGIS 后，窗口都按 700×650 打开。打开之后若你改了大小，只在本次 QGIS 运行期间记住，不写入本机设置。切换功能、切换语言或点选图层都不会再把窗口拉大或缩小，标题也不会互相叠到一起。左侧两个图层列表等宽，右侧参数列较窄，三列大约按 5∶2（两列列表 1∶1）拉伸。":
            "Each time QGIS starts, the window opens at 700×650. If you resize it, that size is remembered only until QGIS exits and is not written to local settings. Switching tools, switching language, or selecting layers does not grow or shrink the window, and titles do not overlap. The two layer lists on the left have equal width, the parameter column on the right is narrower, and the three columns stretch at about 5∶2 (the two lists at 1∶1).",
        "底栏始终可见，提供功能切换、刷新和执行。点图层列表的空白处不会取消已经选中的图层。不按 Ctrl 时，点哪一条，选中的就是哪一条，再点已经选中的那一条也不会取消。按住 Ctrl 再点可以多选或取消其中一条，按住 Shift 再点可以连选一段，按住左键拖过多条则选中划过的那些。点刷新会清空选择并重新载入列表。中区标题紧贴对应控件。参数放得下时不出现滚动条；文字更高、放不下时，只在中区内部滚动，窗口尺寸不变。三个模式的方案下拉标题均为「批量方案」。吸附和移动将该组放在中区底部，其余参数在其上方均匀留白，控件保持各自本来的高度，不再互相重叠。":
            "The bottom bar stays visible and provides tool switching, refresh, and run. Clicking empty space in a layer list does not clear layers already selected. Without Ctrl, the row you click is the selection, and clicking that selected row again does not clear it. Hold Ctrl and click to add or remove one row, hold Shift and click to select a range, or drag with the left button to select the rows the pointer crosses. Click Refresh to clear the selection and reload the lists. Titles in the middle stay attached to their controls. When the parameters fit, there is no scrollbar. When the text is taller and does not fit, only the middle area scrolls, and the window size stays the same. In all three modes the scheme list is titled “Batch schemes”. Snap and move place that group at the bottom of the middle area. The other parameters sit above it with even gaps. Each control keeps its own height, and they do not overlap.",
    },
    "es": {
        "空间匹配与拓扑调整": "Coincidencia espacial y ajuste topológico",
        "窗口尺寸不变": "el tamaño de la ventana no cambia",
        "本插件名为空间匹配与拓扑调整（英文名 Spatial Match & Topo Adjust）。同一窗口内切换三种功能：吸附检测、字段命名、移动。窗口标题、插件菜单和提示都随当前界面语言显示，不会夹杂另一种语言。":
            "Este complemento es Spatial Match & Topo Adjust. Tres herramientas comparten una ventana: comprobación de ajuste, nombres de campo y desplazamiento. El título de la ventana, el menú del complemento y los avisos siguen el idioma actual de la interfaz y no mezclan otro idioma.",
        "每次重新启动 QGIS 后，窗口都按 700×650 打开。打开之后若你改了大小，只在本次 QGIS 运行期间记住，不写入本机设置。切换功能、切换语言或点选图层都不会再把窗口拉大或缩小，标题也不会互相叠到一起。左侧两个图层列表等宽，右侧参数列较窄，三列大约按 5∶2（两列列表 1∶1）拉伸。":
            "Cada vez que se inicia QGIS, la ventana se abre a 700×650. Si cambias el tamaño, se recuerda solo hasta que QGIS se cierra y no se guarda en el equipo. Cambiar de herramienta, de idioma o seleccionar capas no agranda ni reduce la ventana, y los títulos no se superponen. Las dos listas de capas de la izquierda tienen el mismo ancho, la columna de parámetros de la derecha es más estrecha y las tres columnas se estiran aproximadamente 5∶2 (las dos listas 1∶1).",
        "底栏始终可见，提供功能切换、刷新和执行。点图层列表的空白处不会取消已经选中的图层。不按 Ctrl 时，点哪一条，选中的就是哪一条，再点已经选中的那一条也不会取消。按住 Ctrl 再点可以多选或取消其中一条，按住 Shift 再点可以连选一段，按住左键拖过多条则选中划过的那些。点刷新会清空选择并重新载入列表。中区标题紧贴对应控件。参数放得下时不出现滚动条；文字更高、放不下时，只在中区内部滚动，窗口尺寸不变。三个模式的方案下拉标题均为「批量方案」。吸附和移动将该组放在中区底部，其余参数在其上方均匀留白，控件保持各自本来的高度，不再互相重叠。":
            "La barra inferior permanece visible y ofrece cambiar de herramienta, actualizar y ejecutar. Un clic en el espacio vacío de una lista de capas no quita las capas ya seleccionadas. Sin Ctrl, la fila que pulsas es la selección, y volver a pulsar esa fila ya seleccionada no la quita. Mantén Ctrl y pulsa para añadir o quitar una fila, mantén Mayús y pulsa para seleccionar un tramo, o arrastra con el botón izquierdo para seleccionar las filas que recorra el puntero. Pulsa Actualizar para vaciar la selección y volver a cargar las listas. Los títulos del centro quedan junto a su control. Si los parámetros caben, no hay barra de desplazamiento. Si el texto es más alto y no cabe, solo se desplaza la zona central, y el tamaño de la ventana no cambia. En los tres modos la lista de esquemas se titula «Esquemas por lotes». El ajuste y el desplazamiento colocan ese grupo al fondo de la zona central. Los demás parámetros quedan encima, con huecos uniformes. Cada control conserva su altura y no se superponen.",
    },
    "fr": {
        "空间匹配与拓扑调整": "Correspondance spatiale et ajustement topologique",
        "窗口尺寸不变": "la taille de la fenêtre ne change pas",
        "本插件名为空间匹配与拓扑调整（英文名 Spatial Match & Topo Adjust）。同一窗口内切换三种功能：吸附检测、字段命名、移动。窗口标题、插件菜单和提示都随当前界面语言显示，不会夹杂另一种语言。":
            "Cette extension est Spatial Match & Topo Adjust. Trois outils partagent une fenêtre : contrôle d’accrochage, nommage de champ et déplacement. Le titre de la fenêtre, le menu de l’extension et les messages suivent la langue courante de l’interface et ne mélangent pas une autre langue.",
        "每次重新启动 QGIS 后，窗口都按 700×650 打开。打开之后若你改了大小，只在本次 QGIS 运行期间记住，不写入本机设置。切换功能、切换语言或点选图层都不会再把窗口拉大或缩小，标题也不会互相叠到一起。左侧两个图层列表等宽，右侧参数列较窄，三列大约按 5∶2（两列列表 1∶1）拉伸。":
            "À chaque démarrage de QGIS, la fenêtre s’ouvre en 700×650. Si vous la redimensionnez, cette taille n’est retenue que jusqu’à la fermeture de QGIS et n’est pas enregistrée sur l’ordinateur. Changer d’outil, de langue ou sélectionner des couches n’agrandit ni ne réduit la fenêtre, et les titres ne se chevauchent pas. Les deux listes de couches à gauche ont la même largeur, la colonne de paramètres à droite est plus étroite, et les trois colonnes s’étirent environ selon 5∶2 (les deux listes en 1∶1).",
        "底栏始终可见，提供功能切换、刷新和执行。点图层列表的空白处不会取消已经选中的图层。不按 Ctrl 时，点哪一条，选中的就是哪一条，再点已经选中的那一条也不会取消。按住 Ctrl 再点可以多选或取消其中一条，按住 Shift 再点可以连选一段，按住左键拖过多条则选中划过的那些。点刷新会清空选择并重新载入列表。中区标题紧贴对应控件。参数放得下时不出现滚动条；文字更高、放不下时，只在中区内部滚动，窗口尺寸不变。三个模式的方案下拉标题均为「批量方案」。吸附和移动将该组放在中区底部，其余参数在其上方均匀留白，控件保持各自本来的高度，不再互相重叠。":
            "La barre du bas reste visible et permet de changer d’outil, d’actualiser et d’exécuter. Un clic dans le vide d’une liste de couches n’enlève pas les couches déjà choisies. Sans Ctrl, la ligne que vous cliquez est la sélection, et cliquer à nouveau cette ligne déjà choisie ne l’enlève pas. Maintenez Ctrl et cliquez pour ajouter ou retirer une ligne, maintenez Maj et cliquez pour un intervalle, ou faites glisser avec le bouton gauche pour sélectionner les lignes traversées. Cliquez sur Actualiser pour vider la sélection et recharger les listes. Les titres du milieu restent collés à leur contrôle. Quand les paramètres tiennent, il n’y a pas de barre de défilement. Quand le texte est plus haut et ne tient pas, seule la zone centrale défile, et la taille de la fenêtre ne change pas. Dans les trois modes, la liste des schémas s’intitule « Schémas par lot ». L’accrochage et le déplacement placent ce groupe en bas de la zone centrale. Les autres paramètres sont au-dessus, avec des espaces réguliers. Chaque contrôle garde sa hauteur et ils ne se chevauchent pas.",
    },
    "ar": {
        "空间匹配与拓扑调整": "المطابقة المكانية والضبط الطوبولوجي",
        "窗口尺寸不变": "حجم النافذة لا يتغير",
        "本插件名为空间匹配与拓扑调整（英文名 Spatial Match & Topo Adjust）。同一窗口内切换三种功能：吸附检测、字段命名、移动。窗口标题、插件菜单和提示都随当前界面语言显示，不会夹杂另一种语言。":
            "هذه الإضافة هي Spatial Match & Topo Adjust. ثلاث أدوات في نافذة واحدة: فحص الالتقاط، وتسمية الحقول، والتحريك. عنوان النافذة وقائمة الإضافة والتنبيهات تتبع لغة الواجهة الحالية ولا تخلط لغة أخرى.",
        "每次重新启动 QGIS 后，窗口都按 700×650 打开。打开之后若你改了大小，只在本次 QGIS 运行期间记住，不写入本机设置。切换功能、切换语言或点选图层都不会再把窗口拉大或缩小，标题也不会互相叠到一起。左侧两个图层列表等宽，右侧参数列较窄，三列大约按 5∶2（两列列表 1∶1）拉伸。":
            "في كل مرة يبدأ فيها QGIS تُفتح النافذة بمقاس 700×650. إذا غيّرت المقاس يُحفظ فقط حتى إغلاق QGIS ولا يُكتب في إعدادات الجهاز. تبديل الأداة أو اللغة أو تحديد الطبقات لا يكبر النافذة ولا يصغرها، والعناوين لا تتراكب. قائمتا الطبقات على اليسار متساويتان في العرض، وعمود المعاملات على اليمين أضيق، والأعمدة الثلاثة تتمدد بنحو 5∶2 (القائمتان 1∶1).",
        "底栏始终可见，提供功能切换、刷新和执行。点图层列表的空白处不会取消已经选中的图层。不按 Ctrl 时，点哪一条，选中的就是哪一条，再点已经选中的那一条也不会取消。按住 Ctrl 再点可以多选或取消其中一条，按住 Shift 再点可以连选一段，按住左键拖过多条则选中划过的那些。点刷新会清空选择并重新载入列表。中区标题紧贴对应控件。参数放得下时不出现滚动条；文字更高、放不下时，只在中区内部滚动，窗口尺寸不变。三个模式的方案下拉标题均为「批量方案」。吸附和移动将该组放在中区底部，其余参数在其上方均匀留白，控件保持各自本来的高度，不再互相重叠。":
            "الشريط السفلي يبقى ظاهرًا ويوفر تبديل الأداة والتحديث والتنفيذ. النقر على الفراغ في قائمة الطبقات لا يلغي الطبقات المحددة. من دون Ctrl، الصف الذي تنقره هو التحديد، والنقر مرة أخرى على الصف المحدد لا يلغيه. اضغط Ctrl وانقر لإضافة صف أو إزالته، واضغط Shift وانقر لتحديد مدى، أو اسحب بزر الماوس الأيسر لتحديد الصفوف التي يمر بها المؤشر. اضغط تحديث لمسح التحديد وإعادة تحميل القوائم. عناوين الوسط تبقى ملاصقة لعنصرها. إذا اتسعت المعاملات لا يظهر شريط تمرير. إذا كان النص أطول ولم يتسع، تتحرك منطقة الوسط فقط، وحجم النافذة لا يتغير. في الأوضاع الثلاثة عنوان قائمة المخططات هو «مخططات دفعة». الالتقاط والتحريك يضعان هذه المجموعة أسفل منطقة الوسط. بقية المعاملات فوقها بمسافات متساوية. كل عنصر يحتفظ بارتفاعه ولا تتراكب.",
    },
    "it": {
        "空间匹配与拓扑调整": "Corrispondenza spaziale e adattamento topologico",
        "窗口尺寸不变": "la dimensione della finestra non cambia",
        "本插件名为空间匹配与拓扑调整（英文名 Spatial Match & Topo Adjust）。同一窗口内切换三种功能：吸附检测、字段命名、移动。窗口标题、插件菜单和提示都随当前界面语言显示，不会夹杂另一种语言。":
            "Questo plugin è Spatial Match & Topo Adjust. Tre strumenti condividono una finestra: controllo di aggancio, denominazione dei campi e spostamento. Il titolo della finestra, il menu del plugin e i messaggi seguono la lingua corrente dell’interfaccia e non mescolano un’altra lingua.",
        "每次重新启动 QGIS 后，窗口都按 700×650 打开。打开之后若你改了大小，只在本次 QGIS 运行期间记住，不写入本机设置。切换功能、切换语言或点选图层都不会再把窗口拉大或缩小，标题也不会互相叠到一起。左侧两个图层列表等宽，右侧参数列较窄，三列大约按 5∶2（两列列表 1∶1）拉伸。":
            "A ogni avvio di QGIS la finestra si apre a 700×650. Se la ridimensioni, la dimensione resta solo fino alla chiusura di QGIS e non viene scritta sul computer. Cambiare strumento, cambiare lingua o selezionare layer non ingrandisce né riduce la finestra, e i titoli non si sovrappongono. Le due liste di layer a sinistra hanno la stessa larghezza, la colonna dei parametri a destra è più stretta e le tre colonne si estendono circa 5∶2 (le due liste 1∶1).",
        "底栏始终可见，提供功能切换、刷新和执行。点图层列表的空白处不会取消已经选中的图层。不按 Ctrl 时，点哪一条，选中的就是哪一条，再点已经选中的那一条也不会取消。按住 Ctrl 再点可以多选或取消其中一条，按住 Shift 再点可以连选一段，按住左键拖过多条则选中划过的那些。点刷新会清空选择并重新载入列表。中区标题紧贴对应控件。参数放得下时不出现滚动条；文字更高、放不下时，只在中区内部滚动，窗口尺寸不变。三个模式的方案下拉标题均为「批量方案」。吸附和移动将该组放在中区底部，其余参数在其上方均匀留白，控件保持各自本来的高度，不再互相重叠。":
            "La barra in basso resta visibile e offre il cambio strumento, l’aggiornamento e l’esecuzione. Un clic sullo spazio vuoto di una lista di layer non toglie i layer già selezionati. Senza Ctrl, la riga su cui fai clic è la selezione, e un altro clic sulla riga già selezionata non la toglie. Tieni premuto Ctrl e fai clic per aggiungere o togliere una riga, tieni premuto Maiusc e fai clic per un intervallo, oppure trascina con il pulsante sinistro per selezionare le righe attraversate. Fai clic su Aggiorna per svuotare la selezione e ricaricare le liste. I titoli al centro restano attaccati al proprio controllo. Se i parametri ci stanno, non c’è barra di scorrimento. Se il testo è più alto e non ci sta, scorre solo l’area centrale, e la dimensione della finestra non cambia. In tutti e tre i modi l’elenco schemi si intitola «Schemi in blocco». Aggancio e spostamento mettono quel gruppo in fondo all’area centrale. Gli altri parametri stanno sopra, con spazi uniformi. Ogni controllo mantiene la propria altezza e non si sovrappongono.",
    },
    "de": {
        "空间匹配与拓扑调整": "Räumliche Übereinstimmung und Topologieanpassung",
        "窗口尺寸不变": "die Fenstergröße bleibt gleich",
        "本插件名为空间匹配与拓扑调整（英文名 Spatial Match & Topo Adjust）。同一窗口内切换三种功能：吸附检测、字段命名、移动。窗口标题、插件菜单和提示都随当前界面语言显示，不会夹杂另一种语言。":
            "Dieses Plugin ist Spatial Match & Topo Adjust. Drei Werkzeuge teilen sich ein Fenster: Fangprüfung, Feldbenennung und Verschieben. Fenstertitel, Plugin-Menü und Hinweise folgen der aktuellen Oberflächensprache und mischen keine andere Sprache ein.",
        "每次重新启动 QGIS 后，窗口都按 700×650 打开。打开之后若你改了大小，只在本次 QGIS 运行期间记住，不写入本机设置。切换功能、切换语言或点选图层都不会再把窗口拉大或缩小，标题也不会互相叠到一起。左侧两个图层列表等宽，右侧参数列较窄，三列大约按 5∶2（两列列表 1∶1）拉伸。":
            "Bei jedem Start von QGIS öffnet sich das Fenster mit 700×650. Wenn Sie die Größe ändern, gilt sie nur bis QGIS beendet wird und wird nicht auf dem Computer gespeichert. Werkzeugwechsel, Sprachwechsel oder das Auswählen von Layern vergrößert oder verkleinert das Fenster nicht, und Titel überlappen sich nicht. Die beiden Layerlisten links sind gleich breit, die Parameterspalte rechts ist schmaler, und die drei Spalten strecken sich etwa im Verhältnis 5∶2 (die beiden Listen 1∶1).",
        "底栏始终可见，提供功能切换、刷新和执行。点图层列表的空白处不会取消已经选中的图层。不按 Ctrl 时，点哪一条，选中的就是哪一条，再点已经选中的那一条也不会取消。按住 Ctrl 再点可以多选或取消其中一条，按住 Shift 再点可以连选一段，按住左键拖过多条则选中划过的那些。点刷新会清空选择并重新载入列表。中区标题紧贴对应控件。参数放得下时不出现滚动条；文字更高、放不下时，只在中区内部滚动，窗口尺寸不变。三个模式的方案下拉标题均为「批量方案」。吸附和移动将该组放在中区底部，其余参数在其上方均匀留白，控件保持各自本来的高度，不再互相重叠。":
            "Die untere Leiste bleibt sichtbar und bietet Werkzeugwechsel, Aktualisieren und Ausführen. Ein Klick ins Leere einer Layerliste hebt bereits gewählte Layer nicht auf. Ohne Strg ist die angeklickte Zeile die Auswahl, und ein weiterer Klick auf diese bereits gewählte Zeile hebt sie nicht auf. Strg gedrückt halten und klicken fügt eine Zeile hinzu oder nimmt sie weg, Umschalt gedrückt halten und klicken wählt einen Bereich, und Ziehen mit der linken Maustaste wählt die überstrichenen Zeilen. Klicken Sie auf Aktualisieren, um die Auswahl zu leeren und die Listen neu zu laden. Titel in der Mitte bleiben an ihrem Steuerelement. Passen die Parameter, gibt es keine Bildlaufleiste. Ist der Text höher und passt nicht, rollt nur der Mittelbereich, und die Fenstergröße bleibt gleich. In allen drei Modi heißt die Schemaliste „Stapelschemata“. Fangen und Verschieben setzen diese Gruppe an den unteren Rand des Mittelbereichs. Die übrigen Parameter stehen darüber mit gleichmäßigen Abständen. Jedes Steuerelement behält seine Höhe, und sie überlappen sich nicht.",
    },
    "ja": {
        "空间匹配与拓扑调整": "空間マッチと位相調整",
        "窗口尺寸不变": "ウィンドウサイズは変わりません",
        "本插件名为空间匹配与拓扑调整（英文名 Spatial Match & Topo Adjust）。同一窗口内切换三种功能：吸附检测、字段命名、移动。窗口标题、插件菜单和提示都随当前界面语言显示，不会夹杂另一种语言。":
            "このプラグインは Spatial Match & Topo Adjust です。一つのウィンドウで三つの機能を切り替えます。スナップ検査、フィールド名の付与、移動です。ウィンドウタイトル、プラグインメニュー、メッセージはいまの界面言語だけを表示し、ほかの言語を混ぜません。",
        "每次重新启动 QGIS 后，窗口都按 700×650 打开。打开之后若你改了大小，只在本次 QGIS 运行期间记住，不写入本机设置。切换功能、切换语言或点选图层都不会再把窗口拉大或缩小，标题也不会互相叠到一起。左侧两个图层列表等宽，右侧参数列较窄，三列大约按 5∶2（两列列表 1∶1）拉伸。":
            "QGIS を起動するたびに、ウィンドウは 700×650 で開きます。開いたあとサイズを変えても、覚えているのはその QGIS を終了するまでで、パソコンには保存しません。機能の切替、言語の切替、レイヤの選択ではウィンドウは大きくも小さくもならず、タイトルが重なることもありません。左の二つのレイヤリストは同じ幅、右のパラメータ列は細め、三列はおよそ 5∶2（二つのリストは 1∶1）で伸びます。",
        "底栏始终可见，提供功能切换、刷新和执行。点图层列表的空白处不会取消已经选中的图层。不按 Ctrl 时，点哪一条，选中的就是哪一条，再点已经选中的那一条也不会取消。按住 Ctrl 再点可以多选或取消其中一条，按住 Shift 再点可以连选一段，按住左键拖过多条则选中划过的那些。点刷新会清空选择并重新载入列表。中区标题紧贴对应控件。参数放得下时不出现滚动条；文字更高、放不下时，只在中区内部滚动，窗口尺寸不变。三个模式的方案下拉标题均为「批量方案」。吸附和移动将该组放在中区底部，其余参数在其上方均匀留白，控件保持各自本来的高度，不再互相重叠。":
            "下のバーは常に表示され、機能の切替、更新、実行ができます。レイヤリストの空白をクリックしても、すでに選んだレイヤは解除されません。Ctrl を押さないとき、クリックした行だけが選択になり、すでに選ばれている行をもう一度クリックしても外れません。Ctrl を押してクリックするとその行を追加または解除でき、Shift を押してクリックすると範囲を選べ、左ボタンを押したままドラッグすると通過した行が選ばれます。更新を押すと選択を消してリストを読み直します。中央のタイトルは対応する項目にくっついたままです。パラメータが収まればスクロールバーは出ません。文字が高くて収まらないときは中央の中だけがスクロールし、ウィンドウサイズは変わりません。三つのモードともスキーマの見出しは「一括スキーマ」です。スナップと移動はこのグループを中央の一番下に置き、ほかのパラメータはその上に均等な間隔で並びます。各項目は自分の高さを保ち、重なりません。",
    },
    "ko": {
        "空间匹配与拓扑调整": "공간 정합 및 위상 조정",
        "窗口尺寸不变": "창 크기는 그대로입니다",
        "本插件名为空间匹配与拓扑调整（英文名 Spatial Match & Topo Adjust）。同一窗口内切换三种功能：吸附检测、字段命名、移动。窗口标题、插件菜单和提示都随当前界面语言显示，不会夹杂另一种语言。":
            "이 플러그인은 Spatial Match & Topo Adjust 입니다. 한 창에서 세 가지 기능을 바꿉니다. 스냅 검사, 필드 이름 지정, 이동입니다. 창 제목, 플러그인 메뉴, 안내 문구는 현재 인터페이스 언어만 보여 주며 다른 언어를 섞지 않습니다.",
        "每次重新启动 QGIS 后，窗口都按 700×650 打开。打开之后若你改了大小，只在本次 QGIS 运行期间记住，不写入本机设置。切换功能、切换语言或点选图层都不会再把窗口拉大或缩小，标题也不会互相叠到一起。左侧两个图层列表等宽，右侧参数列较窄，三列大约按 5∶2（两列列表 1∶1）拉伸。":
            "QGIS를 다시 시작할 때마다 창은 700×650으로 열립니다. 연 뒤에 크기를 바꾸면 그 QGIS가 끝날 때까지만 기억하고 컴퓨터에는 저장하지 않습니다. 기능을 바꾸거나 언어를 바꾸거나 레이어를 선택해도 창이 커지거나 작아지지 않으며 제목이 겹치지 않습니다. 왼쪽 두 레이어 목록은 같은 너비이고 오른쪽 매개변수 열은 더 좁으며 세 열은 약 5∶2(두 목록은 1∶1)로 늘어납니다.",
        "底栏始终可见，提供功能切换、刷新和执行。点图层列表的空白处不会取消已经选中的图层。不按 Ctrl 时，点哪一条，选中的就是哪一条，再点已经选中的那一条也不会取消。按住 Ctrl 再点可以多选或取消其中一条，按住 Shift 再点可以连选一段，按住左键拖过多条则选中划过的那些。点刷新会清空选择并重新载入列表。中区标题紧贴对应控件。参数放得下时不出现滚动条；文字更高、放不下时，只在中区内部滚动，窗口尺寸不变。三个模式的方案下拉标题均为「批量方案」。吸附和移动将该组放在中区底部，其余参数在其上方均匀留白，控件保持各自本来的高度，不再互相重叠。":
            "아래 막대는 항상 보이며 기능 전환, 새로 고침, 실행을 제공합니다. 레이어 목록의 빈 곳을 눌러도 이미 선택한 레이어는 해제되지 않습니다. Ctrl을 누르지 않으면 누른 줄만 선택되고, 이미 선택된 줄을 다시 눌러도 해제되지 않습니다. Ctrl을 누른 채 누르면 그 줄을 추가하거나 빼고, Shift를 누른 채 누르면 구간을 고르며, 왼쪽 단추로 끌면 지나간 줄이 선택됩니다. 새로 고침을 누르면 선택을 지우고 목록을 다시 불러옵니다. 가운데 제목은 해당 컨트롤에 붙어 있습니다. 매개변수가 들어가면 스크롤 막대가 없습니다. 글자가 더 높아 들어가지 않으면 가운데만 스크롤되고 창 크기는 그대로입니다. 세 모드 모두 스키마 목록 제목은 「일괄 스키마」입니다. 스냅과 이동은 그 그룹을 가운데 맨 아래에 두고, 나머지 매개변수는 그 위에 고른 간격으로 둡니다. 각 컨트롤은 자기 높이를 유지하며 겹치지 않습니다.",
    },
}
_LAYER_PICK = {
    "en": {
        "有分类的图层，行前有 ◆◆ 标记，标题加粗并以玫红色显示（不是报错）。点击图层名前的 ◆◆ 选择分类（点行内其它位置只选中图层，不弹分类，再点也不会取消）。按住 Ctrl、Shift 或拖动多选时也不弹出。分类弹窗按各分类条件现场计要素数，复选和顶栏图层名以「名称(数量)」显示；数量只作展示，不参与方案匹配反解析。尚未做过子集勾选时默认全选，表示整层。":
            "A layer with categories shows a ◆◆ mark before the row, and the title is bold rose (that is not an error). Click ◆◆ in front of the layer name to choose categories. Clicking anywhere else on the row only selects the layer and does not open categories, and clicking it again does not clear it. Holding Ctrl or Shift, or dragging to select several rows, does not open categories either. The category window counts features on the spot with each category filter. Checkboxes and the layer name in the top bar are shown as name(count). Counts are for display only and are not used when matching schemes. Until a subset is checked, every category starts checked, which means the whole layer.",
    },
    "es": {
        "有分类的图层，行前有 ◆◆ 标记，标题加粗并以玫红色显示（不是报错）。点击图层名前的 ◆◆ 选择分类（点行内其它位置只选中图层，不弹分类，再点也不会取消）。按住 Ctrl、Shift 或拖动多选时也不弹出。分类弹窗按各分类条件现场计要素数，复选和顶栏图层名以「名称(数量)」显示；数量只作展示，不参与方案匹配反解析。尚未做过子集勾选时默认全选，表示整层。":
            "Una capa con categorías muestra ◆◆ delante de la fila y el título va en rosa y negrita (no es un error). Pulse ◆◆ delante del nombre para elegir categorías. Un clic en otro punto de la fila solo selecciona la capa y no abre las categorías, y volver a pulsarlo no la quita. Mantener Ctrl o Mayús, o arrastrar para seleccionar varias, tampoco las abre. La ventana cuenta los elementos al momento con el filtro de cada categoría. Las casillas y el nombre de la capa en la barra superior se muestran como nombre(cantidad). Las cantidades solo se muestran y no intervienen al casar esquemas. Si aún no se ha marcado un subconjunto, al principio están todas marcadas, lo que significa la capa entera.",
    },
    "fr": {
        "有分类的图层，行前有 ◆◆ 标记，标题加粗并以玫红色显示（不是报错）。点击图层名前的 ◆◆ 选择分类（点行内其它位置只选中图层，不弹分类，再点也不会取消）。按住 Ctrl、Shift 或拖动多选时也不弹出。分类弹窗按各分类条件现场计要素数，复选和顶栏图层名以「名称(数量)」显示；数量只作展示，不参与方案匹配反解析。尚未做过子集勾选时默认全选，表示整层。":
            "Une couche avec des catégories affiche ◆◆ devant la ligne, et le titre est en rose gras (ce n’est pas une erreur). Cliquez sur ◆◆ devant le nom pour choisir les catégories. Un clic ailleurs sur la ligne ne fait que sélectionner la couche et n’ouvre pas les catégories, et un nouveau clic ne l’enlève pas. Maintenir Ctrl ou Maj, ou glisser pour en choisir plusieurs, ne les ouvre pas non plus. La fenêtre compte les entités sur place avec le filtre de chaque catégorie. Les cases et le nom de la couche dans la barre du haut s’affichent comme nom(nombre). Les nombres sont seulement affichés et ne servent pas à faire correspondre les schémas. Tant qu’aucun sous-ensemble n’est coché, toutes les catégories le sont au départ, ce qui signifie la couche entière.",
    },
    "ar": {
        "有分类的图层，行前有 ◆◆ 标记，标题加粗并以玫红色显示（不是报错）。点击图层名前的 ◆◆ 选择分类（点行内其它位置只选中图层，不弹分类，再点也不会取消）。按住 Ctrl、Shift 或拖动多选时也不弹出。分类弹窗按各分类条件现场计要素数，复选和顶栏图层名以「名称(数量)」显示；数量只作展示，不参与方案匹配反解析。尚未做过子集勾选时默认全选，表示整层。":
            "الطبقة ذات التصنيفات تظهر ◆◆ قبل الصف، والعنوان وردي عريض (وهذا ليس خطأ). انقر ◆◆ أمام اسم الطبقة لاختيار التصنيفات. النقر في موضع آخر من الصف يحدد الطبقة فقط ولا يفتح التصنيفات، والنقر مرة أخرى لا يلغيها. الضغط على Ctrl أو Shift أو السحب لتحديد عدة صفوف لا يفتحها أيضًا. نافذة التصنيف تعد المعالم فورًا بمرشح كل تصنيف. مربعات الاختيار واسم الطبقة في الشريط العلوي تظهر بصيغة اسم(عدد). الأعداد للعرض فقط ولا تدخل في مطابقة المخططات. إذا لم يُحدد جزء بعد، تبدأ كل التصنيفات محددة، وهذا يعني الطبقة كلها.",
    },
    "it": {
        "有分类的图层，行前有 ◆◆ 标记，标题加粗并以玫红色显示（不是报错）。点击图层名前的 ◆◆ 选择分类（点行内其它位置只选中图层，不弹分类，再点也不会取消）。按住 Ctrl、Shift 或拖动多选时也不弹出。分类弹窗按各分类条件现场计要素数，复选和顶栏图层名以「名称(数量)」显示；数量只作展示，不参与方案匹配反解析。尚未做过子集勾选时默认全选，表示整层。":
            "Un layer con categorie mostra ◆◆ prima della riga e il titolo è in rosa grassetto (non è un errore). Fare clic su ◆◆ davanti al nome per scegliere le categorie. Un clic altrove nella riga seleziona solo il layer e non apre le categorie, e un altro clic non lo toglie. Tenere premuto Ctrl o Maiusc, oppure trascinare per selezionare più righe, non le apre. La finestra conta gli elementi sul momento con il filtro di ogni categoria. Le caselle e il nome del layer nella barra in alto sono mostrati come nome(quantità). I conteggi sono solo di visualizzazione e non entrano nell’abbinamento degli schemi. Se non è ancora stato spuntato un sottoinsieme, all’inizio tutte le categorie sono spuntate, il che significa l’intero layer.",
    },
    "de": {
        "有分类的图层，行前有 ◆◆ 标记，标题加粗并以玫红色显示（不是报错）。点击图层名前的 ◆◆ 选择分类（点行内其它位置只选中图层，不弹分类，再点也不会取消）。按住 Ctrl、Shift 或拖动多选时也不弹出。分类弹窗按各分类条件现场计要素数，复选和顶栏图层名以「名称(数量)」显示；数量只作展示，不参与方案匹配反解析。尚未做过子集勾选时默认全选，表示整层。":
            "Ein Layer mit Kategorien zeigt ◆◆ vor der Zeile, und der Titel ist fett und rosa (das ist kein Fehler). Klicken Sie auf ◆◆ vor dem Namen, um Kategorien zu wählen. Ein Klick an einer anderen Stelle der Zeile wählt nur den Layer und öffnet keine Kategorien, und ein weiterer Klick hebt ihn nicht auf. Strg oder Umschalt gedrückt halten oder Ziehen, um mehrere zu wählen, öffnet sie ebenfalls nicht. Das Fenster zählt Objekte sofort mit dem Filter jeder Kategorie. Kontrollkästchen und der Layername in der oberen Leiste erscheinen als Name(Anzahl). Anzahlen dienen nur der Anzeige und fließen nicht in den Schemaabgleich ein. Wurde noch keine Teilmenge angekreuzt, sind anfangs alle Kategorien angekreuzt, was den ganzen Layer bedeutet.",
    },
    "ja": {
        "有分类的图层，行前有 ◆◆ 标记，标题加粗并以玫红色显示（不是报错）。点击图层名前的 ◆◆ 选择分类（点行内其它位置只选中图层，不弹分类，再点也不会取消）。按住 Ctrl、Shift 或拖动多选时也不弹出。分类弹窗按各分类条件现场计要素数，复选和顶栏图层名以「名称(数量)」显示；数量只作展示，不参与方案匹配反解析。尚未做过子集勾选时默认全选，表示整层。":
            "分類のあるレイヤは行の前に ◆◆ があり、見出しは太字のローズ色です（エラーではありません）。レイヤ名の前の ◆◆ をクリックすると分類を選べます。行のほかの場所をクリックするとレイヤが選ばれるだけで分類は開かず、もう一度クリックしても外れません。Ctrl や Shift を押して選ぶとき、左ボタンを押したままドラッグして複数選ぶときも開きません。分類ウィンドウは各分類の条件でその場の地物数を数えます。チェックと上のバーのレイヤ名は名前(数)と表示します。数は表示だけで、スキーマの照合には使いません。部分集合をまだチェックしていないときは、最初はすべてが選ばれ、レイヤ全体を意味します。",
    },
    "ko": {
        "有分类的图层，行前有 ◆◆ 标记，标题加粗并以玫红色显示（不是报错）。点击图层名前的 ◆◆ 选择分类（点行内其它位置只选中图层，不弹分类，再点也不会取消）。按住 Ctrl、Shift 或拖动多选时也不弹出。分类弹窗按各分类条件现场计要素数，复选和顶栏图层名以「名称(数量)」显示；数量只作展示，不参与方案匹配反解析。尚未做过子集勾选时默认全选，表示整层。":
            "분류가 있는 레이어는 줄 앞에 ◆◆ 가 있고, 제목은 굵은 장미색입니다(오류가 아닙니다). 레이어 이름 앞의 ◆◆ 를 누르면 분류를 고릅니다. 줄의 다른 곳을 누르면 레이어만 선택되고 분류는 열리지 않으며, 다시 눌러도 해제되지 않습니다. Ctrl이나 Shift를 누른 채 고르거나 왼쪽 단추로 끌어 여러 줄을 선택할 때도 열리지 않습니다. 분류 창은 각 분류 조건으로 그 자리의 피처 수를 셉니다. 확인란과 위쪽 막대의 레이어 이름은 이름(개수)으로 보입니다. 개수는 보여 주기만 하며 스키마 대조에 쓰이지 않습니다. 부분집합을 아직 고르지 않았으면 처음에는 모두 선택된 상태이며, 이는 레이어 전체를 뜻합니다.",
    },
}
_SNAP_FILTER = {
    "en": {
        "标准模式需要参考图层。选中不需要参考图层的特殊检测时，会清掉参考图层的选择，并把参考列表及其点、线、面、全部按钮一起变灰，不能再点。检测方式在右侧列表上方合并为一个下拉：第一项且默认为「标准」，其后为现行特殊检测项，并只按当前选中的判断图层过滤，不看参考图层。需要某种参考几何的检查，选中之后参考列表只留下该几何。若切换判断图层后当前特殊项不再适用，回退到「标准」，不会自动改成其它特殊项。该下拉遵守滚轮锁。":
            "Standard mode needs a reference layer. Choosing a special check that does not use a reference layer clears the reference selection and greys out the reference list together with its point, line, polygon, and all buttons, so they cannot be clicked. Detection is one dropdown above the right-hand list: the first item, and the default, is “Standard”, then the current special checks, filtered only by the target layers now selected, not by the reference layers. A check that needs a reference geometry, once chosen, leaves only that geometry in the reference list. If the current special item no longer applies after the target layers change, it returns to “Standard” and is not switched to another special item. This dropdown follows the wheel lock.",
    },
    "es": {
        "标准模式需要参考图层。选中不需要参考图层的特殊检测时，会清掉参考图层的选择，并把参考列表及其点、线、面、全部按钮一起变灰，不能再点。检测方式在右侧列表上方合并为一个下拉：第一项且默认为「标准」，其后为现行特殊检测项，并只按当前选中的判断图层过滤，不看参考图层。需要某种参考几何的检查，选中之后参考列表只留下该几何。若切换判断图层后当前特殊项不再适用，回退到「标准」，不会自动改成其它特殊项。该下拉遵守滚轮锁。":
            "El modo estándar necesita una capa de referencia. Al elegir una comprobación especial que no usa capa de referencia, se quita la selección de referencia y la lista de referencia, junto con sus botones de punto, línea, polígono y todo, se vuelve gris y no se puede pulsar. La detección es una lista sobre la lista derecha: el primer elemento, y el predeterminado, es «Estándar», y después van las comprobaciones especiales vigentes, filtradas solo por las capas de evaluación seleccionadas, no por las de referencia. Una comprobación que exige una geometría de referencia, una vez elegida, deja en la lista de referencia solo esa geometría. Si el elemento especial deja de aplicar al cambiar las capas de evaluación, vuelve a «Estándar» y no pasa a otro. Esta lista respeta el bloqueo de la rueda.",
    },
    "fr": {
        "标准模式需要参考图层。选中不需要参考图层的特殊检测时，会清掉参考图层的选择，并把参考列表及其点、线、面、全部按钮一起变灰，不能再点。检测方式在右侧列表上方合并为一个下拉：第一项且默认为「标准」，其后为现行特殊检测项，并只按当前选中的判断图层过滤，不看参考图层。需要某种参考几何的检查，选中之后参考列表只留下该几何。若切换判断图层后当前特殊项不再适用，回退到「标准」，不会自动改成其它特殊项。该下拉遵守滚轮锁。":
            "Le mode standard a besoin d’une couche de référence. Choisir un contrôle spécial qui n’utilise pas de couche de référence efface la sélection de référence et grise la liste de référence ainsi que ses boutons point, ligne, polygone et tout, qui ne peuvent plus être cliqués. La détection est une seule liste au-dessus de la liste de droite : le premier élément, et la valeur par défaut, est « Standard », puis les contrôles spéciaux en vigueur, filtrés seulement selon les couches à évaluer sélectionnées, et non selon les couches de référence. Un contrôle qui exige une géométrie de référence, une fois choisi, ne laisse dans la liste de référence que cette géométrie. Si l’élément spécial ne s’applique plus après un changement des couches à évaluer, le choix revient à « Standard » sans passer à un autre. Cette liste respecte le verrouillage de la molette.",
    },
    "ar": {
        "标准模式需要参考图层。选中不需要参考图层的特殊检测时，会清掉参考图层的选择，并把参考列表及其点、线、面、全部按钮一起变灰，不能再点。检测方式在右侧列表上方合并为一个下拉：第一项且默认为「标准」，其后为现行特殊检测项，并只按当前选中的判断图层过滤，不看参考图层。需要某种参考几何的检查，选中之后参考列表只留下该几何。若切换判断图层后当前特殊项不再适用，回退到「标准」，不会自动改成其它特殊项。该下拉遵守滚轮锁。":
            "الوضع القياسي يحتاج إلى طبقة مرجعية. اختيار فحص خاص لا يستخدم طبقة مرجعية يمسح تحديد المرجع ويعتم قائمة المرجع مع أزرار النقطة والخط والمضلع والكل، فلا يمكن النقر عليها. الفحص قائمة واحدة أعلى القائمة اليمنى: البند الأول والافتراضي هو «القياسي»، ثم الفحوص الخاصة الحالية، وتُصفى حسب طبقات الحكم المحددة فقط، لا حسب طبقات المرجع. الفحص الذي يطلب هندسة مرجعية، بعد اختياره، يُبقي في قائمة المرجع تلك الهندسة فقط. إذا لم يعد البند الخاص منطبقاً بعد تغيير طبقات الحكم، يُعاد إلى «القياسي» ولا يُبدَّل إلى بند خاص آخر. تلتزم هذه القائمة بقفل العجلة.",
    },
    "it": {
        "标准模式需要参考图层。选中不需要参考图层的特殊检测时，会清掉参考图层的选择，并把参考列表及其点、线、面、全部按钮一起变灰，不能再点。检测方式在右侧列表上方合并为一个下拉：第一项且默认为「标准」，其后为现行特殊检测项，并只按当前选中的判断图层过滤，不看参考图层。需要某种参考几何的检查，选中之后参考列表只留下该几何。若切换判断图层后当前特殊项不再适用，回退到「标准」，不会自动改成其它特殊项。该下拉遵守滚轮锁。":
            "La modalità Standard richiede un layer di riferimento. Scegliere un controllo speciale che non usa un layer di riferimento cancella la selezione di riferimento e disattiva in grigio la lista di riferimento insieme ai pulsanti punto, linea, poligono e tutti, che non si possono più premere. Il rilevamento è un unico elenco sopra la lista di destra: il primo elemento, e il predefinito, è «Standard», poi i controlli speciali in vigore, filtrati solo dai layer di valutazione selezionati e non dai layer di riferimento. Un controllo che richiede una geometria di riferimento, una volta scelto, lascia nella lista di riferimento solo quella geometria. Se il controllo speciale non vale più dopo un cambio dei layer di valutazione, si torna a «Standard» e non si passa a un altro. Questo elenco rispetta il blocco della rotella.",
    },
    "de": {
        "标准模式需要参考图层。选中不需要参考图层的特殊检测时，会清掉参考图层的选择，并把参考列表及其点、线、面、全部按钮一起变灰，不能再点。检测方式在右侧列表上方合并为一个下拉：第一项且默认为「标准」，其后为现行特殊检测项，并只按当前选中的判断图层过滤，不看参考图层。需要某种参考几何的检查，选中之后参考列表只留下该几何。若切换判断图层后当前特殊项不再适用，回退到「标准」，不会自动改成其它特殊项。该下拉遵守滚轮锁。":
            "Der Standardmodus braucht einen Referenzlayer. Wer eine Sonderprüfung wählt, die keinen Referenzlayer nutzt, löscht die Referenzauswahl und graut die Referenzliste samt den Schaltflächen Punkt, Linie, Polygon und Alle aus, sodass sie nicht mehr klickbar sind. Die Erkennung ist eine Liste über der rechten Liste: Der erste Eintrag und die Vorgabe ist „Standard“, danach die geltenden Sonderprüfungen, gefiltert nur nach den jetzt gewählten Prüflayern, nicht nach den Referenzlayern. Eine Prüfung, die eine Referenzgeometrie verlangt, lässt nach der Wahl in der Referenzliste nur diese Geometrie. Gilt der aktuelle Sondereintrag nach einem Wechsel der Prüflayer nicht mehr, fällt die Wahl auf „Standard“ zurück und wechselt nicht zu einem anderen. Diese Liste beachtet die Rad-Sperre.",
    },
    "ja": {
        "标准模式需要参考图层。选中不需要参考图层的特殊检测时，会清掉参考图层的选择，并把参考列表及其点、线、面、全部按钮一起变灰，不能再点。检测方式在右侧列表上方合并为一个下拉：第一项且默认为「标准」，其后为现行特殊检测项，并只按当前选中的判断图层过滤，不看参考图层。需要某种参考几何的检查，选中之后参考列表只留下该几何。若切换判断图层后当前特殊项不再适用，回退到「标准」，不会自动改成其它特殊项。该下拉遵守滚轮锁。":
            "標準モードには参照レイヤが必要です。参照レイヤを使わない特殊検査を選ぶと、参照レイヤの選択は消え、参照リストとその点・線・面・全部のボタンが一緒に灰色になり、押せなくなります。検出方式は右の一覧の上にある一つのドロップダウンです。先頭かつ既定は「標準」で、その後に現行の特殊検査が続き、いま選んでいる判定レイヤだけで絞り、参照レイヤでは絞りません。参照の幾何タイプが決まっている検査を選ぶと、参照リストにはその幾何だけが残ります。判定レイヤを切り替えて現在の特殊項目が使えなくなれば「標準」に戻り、別の特殊項目へは自動では移りません。このドロップダウンはホイールロックに従います。",
    },
    "ko": {
        "标准模式需要参考图层。选中不需要参考图层的特殊检测时，会清掉参考图层的选择，并把参考列表及其点、线、面、全部按钮一起变灰，不能再点。检测方式在右侧列表上方合并为一个下拉：第一项且默认为「标准」，其后为现行特殊检测项，并只按当前选中的判断图层过滤，不看参考图层。需要某种参考几何的检查，选中之后参考列表只留下该几何。若切换判断图层后当前特殊项不再适用，回退到「标准」，不会自动改成其它特殊项。该下拉遵守滚轮锁。":
            "표준 모드는 참조 레이어가 필요합니다. 참조 레이어를 쓰지 않는 특수 검사를 고르면 참조 레이어의 선택이 지워지고, 참조 목록과 점, 선, 면, 전체 단추가 함께 회색이 되어 누를 수 없습니다. 검출 방식은 오른쪽 목록 위의 드롭다운 하나입니다. 첫 항목이자 기본값은 「표준」이고, 그 뒤에 현재 특수 검사가 이어지며, 지금 선택한 판정 레이어만으로 걸러지고 참조 레이어로는 걸러지지 않습니다. 참조 기하가 정해진 검사를 고르면 참조 목록에는 그 기하만 남습니다. 판정 레이어를 바꾼 뒤 현재 특수 항목이 맞지 않으면 「표준」으로 돌아가고, 다른 특수 항목으로 자동으로 바꾸지 않습니다. 이 드롭다운은 휠 잠금을 따릅니다.",
    },
}


for _code, _rows in _RELEASE.items():
    _TABLES_READY = {
        "en": EN,
        "es": ES,
        "fr": FR,
        "ar": AR,
        "it": IT,
        "de": DE,
        "ja": JA,
        "ko": KO,
    }[_code]
    _TABLES_READY.update(_rows)
    _TABLES_READY.update(_LAYER_PICK.get(_code) or {})
    _TABLES_READY.update(_SNAP_FILTER.get(_code) or {})

_TABLES = {
    LANG_EN: EN,
    LANG_ES: ES,
    LANG_FR: FR,
    LANG_AR: AR,
    LANG_IT: IT,
    LANG_DE: DE,
    LANG_JA: JA,
    LANG_KO: KO,
}


def known_languages():
    return (LANG_EN, LANG_ZH, LANG_ES, LANG_FR, LANG_AR, LANG_IT, LANG_DE, LANG_JA, LANG_KO)


def detect_initial_language(qgis_locale=None, system_locale=None):
    """Prefer QGIS locale, then the system locale.

    A supported code (en / zh / es / fr / ar / it / de / ja / ko) is used as-is.
    Any other non-empty locale uses English.
    When both locales are empty or cannot be read, English is the fallback.
    """
    for raw in (qgis_locale, system_locale):
        text = str(raw or "").strip().lower().replace("_", "-")
        if not text:
            continue
        primary = text.split("-", 1)[0]
        for prefix, lang in _LOCALE_PREFIX:
            if primary == prefix:
                return lang
        return LANG_EN
    return LANG_EN


def text_for(language, msgid):
    if language == LANG_ZH or not msgid:
        return ""
    table = _TABLES.get(language) or {}
    return table.get(msgid) or ""

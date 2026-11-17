"""Palettes (sampled from the Figma export) and the QSS builder."""
LIGHT_SHELL = dict(topbar="#245d62", desk="#286d72", toptext="#dfe8dc", task="#d1d8c3", title="#cfd8bf", menubar="#e6e8db",
                   win="#d1d8c3", ink="#1d2a22", muted="#6f7d70", content="#f4f4e9", side="#e6e8db", accent="#c4f06a",
                   border="#1d2a22", shadow="#12413f", chip="#d9e0c8")
DARK_SHELL = dict(topbar="#132d31", desk="#0f282d", toptext="#cfdcd5", task="#23363b", title="#2f464b", menubar="#1a262a",
                  win="#23363b", ink="#e9f0e2", muted="#8fa29a", content="#212d31", side="#1a262a", accent="#c4f06a",
                  border="#0a1517", shadow="#050d0e", chip="#2b3d3b")

# key: (light bg, light surface, ink, accent, dark bg, dark surface)
PAGES = {
    "home":     ("#f4f4e9", "#f7f7ea", "#1d2a22", "#c4f06a", "#212d31", "#26363a"),
    "settings": ("#f4f4e9", "#f7f7ea", "#1d2a22", "#c4f06a", "#212d31", "#26363a"),
    "cpu":      ("#f2f4e8", "#ffffff", "#1d2a22", "#c4f06a", "#1c2826", "#26362f"),
    "bankers":  ("#f9e8ed", "#fff9f7", "#2a1b27", "#ffa3c4", "#2b1f28", "#3a2b37"),
    "paging":   ("#efebf9", "#fcfbff", "#2a2339", "#c5b3f2", "#231f31", "#312b44"),
    "pagerep":  ("#fff4d4", "#fffdf1", "#3a2a12", "#ffcc62", "#2a261d", "#3b3326"),
    "seg":      ("#e8f4f0", "#ffffff", "#17323a", "#84d9e0", "#1a2d31", "#22373c"),
    "frag":     ("#f6e8da", "#fff9f2", "#3a2418", "#ff9970", "#2f231f", "#3d2e28"),
    "disk":     ("#e8ebf9", "#fbfbff", "#1f2749", "#a9b4f9", "#1c2438", "#28324d"),
    "multi":    ("#e9efdd", "#f7f8ea", "#1d2b1d", "#c4f06a", "#212a1f", "#2d3a2a"),
}
PCOL = ["#c4f06a", "#c5b3f2", "#ffa3c4", "#84d9e0", "#ffcc62", "#ff9970", "#a9b4f9", "#9be3b0"]
SANS = "Inter, 'Segoe UI', Arial, sans-serif"
MONO = "'JetBrains Mono', Consolas, 'Courier New', monospace"


def shell_palette(mode):
    return dict(LIGHT_SHELL if mode == "light" else DARK_SHELL)


def palette(key, mode, accent=None):
    lb, ls, ink, acc, db, ds = PAGES[key]
    acc = accent or acc
    if mode == "light":
        p = dict(bg=lb, surface=ls, ink=ink, muted=_mix(ink, lb, .45), border=ink, shadow=ink, accent=acc, accent_ink=ink,
                 soft=_mix(ink, lb, .08), grid=_mix(ink, lb, .15), dark=ink, dark_ink="#ffffff", hit="#c4f06a")
    else:
        light = "#f1eedd"
        p = dict(bg=db, surface=ds, ink=light, muted=_mix(light, db, .5), border=_mix("#000000", db, .55), shadow=_mix("#000000", db, .6),
                 accent=acc, accent_ink="#1d2a22", soft=_mix(light, db, .06), grid=_mix(light, db, .14), dark=_mix("#000000", ds, .35),
                 dark_ink=light, hit="#c4f06a")
    p["mode"] = mode
    return p


def _mix(a, b, t):
    """t of colour a over colour b."""
    ca = [int(a[i:i + 2], 16) for i in (1, 3, 5)]
    cb = [int(b[i:i + 2], 16) for i in (1, 3, 5)]
    return "#%02x%02x%02x" % tuple(round(x * t + y * (1 - t)) for x, y in zip(ca, cb))


def build_qss(p):
    return f"""
QWidget {{ color:{p['ink']}; font-family:{SANS}; font-size:13px; }}
QWidget#page, QWidget#content {{ background:{p['bg']}; }}
QToolTip {{ background:{p['surface']}; color:{p['ink']}; border:2px solid {p['border']}; }}
QLabel {{ background:transparent; }}
QLabel[kind="h1"] {{ font-size:32px; font-weight:800; }}
QLabel[kind="h1s"] {{ font-size:26px; font-weight:800; }}
QLabel[kind="h1m"] {{ font-size:28px; font-weight:800; }}
QLabel[kind="hero"] {{ font-size:36px; font-weight:800; }}
QLabel[kind="h2"] {{ font-size:19px; font-weight:700; }}
QLabel[kind="h3"] {{ font-size:15px; font-weight:700; }}
QLabel[kind="big"] {{ font-size:34px; font-weight:800; }}
QLabel[kind="big2"] {{ font-size:24px; font-weight:800; }}
QLabel[kind="huge"] {{ font-size:82px; font-weight:800; }}
QLabel[kind="huge2"] {{ font-size:34px; font-weight:800; }}
QLabel[kind="stat"] {{ font-size:23px; font-weight:800; }}
QLabel[kind="body"] {{ font-size:13px; }}
QLabel[kind="small"] {{ font-size:11px; color:{p['muted']}; }}
QLabel[kind="muted"] {{ color:{p['muted']}; font-size:12px; }}
QLabel[kind="eyebrow"] {{ font-family:{MONO}; font-size:10px; color:{p['muted']}; }}
QLabel[kind="mono"] {{ font-family:{MONO}; font-size:11px; }}
QLabel[kind="boldmono"] {{ font-family:{MONO}; font-size:11px; font-weight:700; }}
QLabel[kind="arrow"] {{ font-size:20px; }}
QLabel[kind="refs"] {{ font-family:{MONO}; font-size:22px; }}
QLabel[gap="1"] {{ margin-top:8px; }}
QLabel[kind="band"] {{ background:{p['accent']}; color:{p['accent_ink']}; font-family:{MONO}; font-size:11px; padding:11px 14px; border-bottom:2px solid {p['border']}; }}
QFrame[card="shadow"], QFrame[card="plain"], QFrame[card="whitebox"], QFrame[card="darkline"], QFrame[card="side"] {{ background:{p['surface']}; border:2px solid {p['border']}; }}
QFrame[card="shadowaccent"], QFrame[card="accent"], QFrame[card="accentbox"], QFrame[card="accentbox2"], QFrame[card="band"] {{ background:{p['accent']}; border:2px solid {p['border']}; }}
QFrame[card="band"] {{ border-left:none; border-right:none; border-top:none; }}
QFrame[card="darkbox"] {{ background:{p['dark']}; border:2px solid {p['border']}; }}
QFrame[card="side"] {{ background:{p['bg']}; border:none; border-right:1px solid {p['grid']}; }}
QFrame[rule="1"] {{ background:{p['border']}; border:none; }}
QFrame[card="shadowaccent"] QLabel, QFrame[card="accent"] QLabel, QFrame[card="accentbox"] QLabel, QFrame[card="accentbox2"] QLabel, QFrame[card="band"] QLabel {{ color:{p['accent_ink']}; }}
QFrame[card="shadowaccent"] QLabel[kind="eyebrow"], QFrame[card="accentbox2"] QLabel[kind="eyebrow"] {{ color:{_mix(p['accent_ink'], p['accent'], .75)}; }}
QFrame[card="darkbox"] QLabel {{ color:{p['dark_ink']}; }}
QFrame[card="plain"] QLabel[kind="mono"] {{ font-size:10px; }}
QPushButton {{ background:{p['surface']}; border:2px solid {p['border']}; padding:4px 12px; font-weight:600; font-size:12px; }}
QPushButton:hover {{ background:{_mix(p['accent'], p['surface'], .35)}; }}
QPushButton:pressed {{ background:{p['accent']}; }}
QPushButton[role="primary"], QPushButton[role="seg"]:checked, QPushButton[role="memory"] {{ background:{p['accent']}; color:{p['accent_ink']}; font-weight:700; }}
QPushButton[role="primary"]:hover {{ background:{_mix('#ffffff', p['accent'], .25)}; }}
QPushButton[role="seg"] {{ font-weight:600; }}
QPushButton[role="memory"] {{ text-align:left; font-family:{MONO}; font-size:13px; padding:6px 14px; }}
QPushButton[role="dark"] {{ background:{p['dark']}; color:{p['dark_ink']}; font-weight:700; }}
QPushButton[role="dark"]:hover {{ background:{_mix(p['accent'], p['dark'], .3)}; color:{p['dark_ink']}; }}
QPushButton[role="link"] {{ border:none; background:transparent; font-size:11px; font-weight:600; padding:2px 4px; }}
QPushButton[role="link"]:hover {{ background:{p['soft']}; }}
QPushButton[role="mini"] {{ font-family:{MONO}; font-size:10px; padding:3px 9px; }}
QPushButton[role="mini"]:checked {{ background:{p['accent']}; color:{p['accent_ink']}; }}
QPushButton[role="flat"] {{ border:none; background:transparent; font-size:16px; font-weight:700; padding:0 6px; }}
QPushButton[role="flat"]:hover {{ background:{p['soft']}; }}
QPushButton[role="nav"] {{ border:none; background:transparent; text-align:left; padding:6px 8px; font-size:12px; font-weight:500; }}
QPushButton[role="nav"]:hover {{ background:{p['soft']}; }}
QPushButton[role="nav"]:checked {{ background:{_mix(p['ink'], p['bg'], .14)}; font-weight:700; }}
QPushButton[role="theme"] {{ background:{p['surface']}; padding:0; }}
QPushButton[role="theme"]:checked {{ background:{p['surface']}; border:3px solid {p['border']}; }}
QPushButton[role="swatch"] {{ padding:0; }}
QPushButton[role="swatch"]:checked {{ border:3px solid {p['border']}; }}
QPushButton[role="toggle"] {{ font-family:{MONO}; font-size:10px; font-weight:700; padding:0; background:{p['soft']}; }}
QPushButton[role="toggle"]:checked {{ background:{p['accent']}; color:{p['accent_ink']}; }}
QLineEdit, QSpinBox, QComboBox {{ background:{p['surface']}; border:2px solid {p['border']}; padding:2px 8px; selection-background-color:{p['accent']}; selection-color:{p['accent_ink']}; font-size:13px; }}
QLineEdit[kind="refs"] {{ border:none; background:transparent; font-family:{MONO}; font-size:21px; padding:0; }}
QLineEdit[kind="cell"] {{ border:none; border-bottom:1px solid {p['grid']}; background:transparent; font-family:{MONO}; font-size:12px; padding:1px 0; }}
QLineEdit[kind="cell"]:focus {{ border-bottom:2px solid {p['border']}; }}
QLineEdit[kind="pid"] {{ border:none; background:transparent; font-weight:800; font-size:17px; padding:0; }}
QComboBox QAbstractItemView {{ background:{p['surface']}; border:2px solid {p['border']}; selection-background-color:{p['accent']}; selection-color:{p['accent_ink']}; }}
QComboBox::drop-down {{ border:none; width:22px; }}
QSpinBox::up-button, QSpinBox::down-button {{ width:0; }}
QCheckBox {{ spacing:8px; font-size:12px; }}
QCheckBox::indicator {{ width:14px; height:14px; border:2px solid {p['border']}; background:{p['surface']}; }}
QCheckBox::indicator:checked {{ background:{p['accent']}; }}
QScrollArea {{ background:transparent; border:none; }}
QScrollArea > QWidget > QWidget {{ background:transparent; }}
QScrollBar:vertical {{ background:transparent; width:10px; margin:0; }}
QScrollBar:horizontal {{ background:transparent; height:10px; margin:0; }}
QScrollBar::handle {{ background:{_mix(p['ink'], p['bg'], .35)}; min-height:24px; min-width:24px; border-radius:0; }}
QScrollBar::add-line, QScrollBar::sub-line {{ width:0; height:0; }}
QScrollBar::add-page, QScrollBar::sub-page {{ background:transparent; }}
QTableWidget {{ background:transparent; border:none; gridline-color:transparent; font-size:12px; outline:0; }}
QTableWidget::item {{ padding:4px 2px; border-bottom:1px solid {p['grid']}; }}
QTableWidget::item:selected {{ background:{p['accent']}; color:{p['accent_ink']}; }}
QHeaderView {{ background:transparent; }}
QHeaderView::section {{ background:transparent; border:none; color:{p['muted']}; font-family:{MONO}; font-size:10px; padding:4px 2px; text-align:left; }}
QTableCornerButton::section {{ background:transparent; border:none; }}
QSlider::groove:horizontal {{ height:8px; background:{p['border']}; }}
QSlider::handle:horizontal {{ width:14px; height:24px; margin:-9px 0; background:{p['surface']}; border:2px solid {p['border']}; }}
QSlider::sub-page:horizontal {{ background:{p['border']}; }}
QMenu {{ background:{p['surface']}; border:2px solid {p['border']}; padding:4px; font-size:12px; }}
QMenu::item {{ padding:5px 22px; }}
QMenu::item:selected {{ background:{p['accent']}; color:{p['accent_ink']}; }}
QMenu::separator {{ height:1px; background:{p['grid']}; margin:4px 2px; }}
QDialog {{ background:{p['bg']}; }}
QToolTip {{ padding:3px; }}
"""


def shell_qss(s):
    return f"""
QWidget {{ font-family:{SANS}; font-size:12px; color:{s['ink']}; }}
QWidget#MainWindow {{ background:{s['desk']}; }}
QWidget#desktop {{ background:{s['desk']}; }}
QFrame#topbar {{ background:{s['topbar']}; }}
QFrame#topbar QLabel, QFrame#topbar QPushButton {{ color:{s['toptext']}; font-family:{MONO}; font-size:11px; background:transparent; border:none; padding:0; }}
QFrame#topbar QPushButton:hover {{ color:#ffffff; }}
QFrame#taskbar {{ background:{s['task']}; border-top:2px solid {s['border']}; }}
QFrame#taskbar QLabel {{ font-family:{MONO}; font-size:11px; color:{s['ink']}; }}
QPushButton[role="start"] {{ background:{s['accent'] if s['topbar']=='#132d31' else s['chip']}; border:2px solid {s['border']}; font-weight:800; font-size:13px; padding:4px 14px; text-align:left; min-width:78px; color:{'#1d2a22' if s['topbar']=='#132d31' else s['ink']}; }}
QPushButton[role="task"] {{ background:{s['content'] if s['topbar']!='#132d31' else s['topbar']}; border:2px solid {s['border']}; font-family:{MONO}; font-size:12px; text-align:left; padding:4px 14px; min-width:230px; font-weight:400; }}
QFrame#windowFrame {{ background:{s['win']}; border:2px solid {s['border']}; }}
QFrame#titlebar {{ background:{s['title']}; border-bottom:2px solid {s['border']}; }}
QFrame#titlebar QLabel {{ font-family:{MONO}; font-size:12px; background:transparent; }}
QPushButton[role="win"] {{ background:{s['content'] if s['topbar']!='#132d31' else s['topbar']}; border:2px solid {s['border']}; font-size:15px; font-weight:700; min-width:26px; max-width:26px; min-height:22px; max-height:22px; padding:0; }}
QPushButton[role="win"]:hover {{ background:{s['accent']}; color:#1d2a22; }}
QFrame#menubar {{ background:{s['menubar']}; }}
QFrame#menubar QPushButton {{ border:none; background:transparent; padding:2px 0; font-size:12px; font-weight:400; }}
QFrame#menubar QPushButton:hover {{ text-decoration:underline; }}
QLabel[kind="path"] {{ font-family:{MONO}; font-size:10px; color:{s['muted']}; }}
QFrame#statusbar {{ background:{s['menubar']}; border-top:1px solid {s['muted']}; }}
QLabel[kind="status"] {{ font-family:{MONO}; font-size:10px; color:{s['muted']}; }}
QMenu {{ background:{s['content']}; border:2px solid {s['border']}; padding:4px; font-size:12px; color:{s['ink']}; }}
QMenu::item {{ padding:5px 24px; }}
QMenu::item:selected {{ background:{s['accent']}; color:#1d2a22; }}
QMenu::separator {{ height:1px; background:{s['muted']}; margin:4px 2px; }}
"""

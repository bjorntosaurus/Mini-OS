"""Windows-XP-style stylesheet for the XP desktop shell (all rules are scoped by objectName / property
so they never leak into the neo-brutalist simulator pages hosted inside the windows)."""
XP_FONT = "Tahoma, 'Segoe UI', Inter, sans-serif"
TITLE_FONT = "'Trebuchet MS', Tahoma, Inter, sans-serif"


def grad(top, bottom, mid=None, mpos=0.5):
    stops = f"stop:0 {top}, " + (f"stop:{mpos} {mid}, " if mid else "") + f"stop:1 {bottom}"
    return f"qlineargradient(x1:0,y1:0,x2:0,y2:1,{stops})"


def _wrap(t):
    return t


def _sections():
    blue = grad("#0a5fe0", "#0545c8", "#3d95ff", 0.15)
    return dict(
        taskbar=f"""QFrame#xpTaskbar {{ background:{grad('#3168d5', '#1941a5', '#245edb', 0.18)}; border-top:1px solid #4f86ec; }}
QPushButton[role="xpstart"] {{ background:{grad('#5bb85a', '#2b7a2b', '#3f9f3f', 0.5)}; color:white; font-family:{TITLE_FONT}; font-style:italic; font-weight:800; font-size:21px;
    border:none; border-top-right-radius:16px; border-bottom-right-radius:16px; padding:0 10px 2px 44px; text-align:left; }}
QPushButton[role="xpstart"]:hover {{ background:{grad('#74cc72', '#35923a', '#4cb04c', 0.5)}; }}
QPushButton[role="xpstart"]:pressed {{ background:{grad('#2b7a2b', '#3f9f3f')}; }}
QPushButton[role="xpql"] {{ background:transparent; border:none; padding:0; }}
QPushButton[role="xpql"]:hover {{ background:rgba(255,255,255,50); border-radius:3px; }}
QFrame[xpsep="1"] {{ background:#5b8be3; border-right:1px solid #1941a5; }}
QWidget#taskButtons QPushButton {{ background:{grad('#4d8cf0', '#2a62d4')}; color:white; font-family:{XP_FONT}; font-size:12px; border:1px solid #1a49b8; border-radius:3px;
    min-width:170px; max-width:170px; min-height:28px; text-align:left; padding:0 8px; }}
QWidget#taskButtons QPushButton:checked {{ background:{grad('#1b4fb8', '#2559c6')}; border:1px solid #0e2f86; font-weight:bold; }}
QWidget#taskButtons QPushButton:hover {{ background:{grad('#6aa2f7', '#3b74e2')}; }}
QLabel[kind="xpnote"], QLabel[kind="xptray"] {{ color:white; font-family:{XP_FONT}; font-size:12px; background:transparent; }}
QFrame#xpTray {{ background:{grad('#18a0ea', '#0e72d0', '#12a2ee', 0.2)}; border-left:1px solid #0b4ea8; }}
QLabel[kind="xpnote"] {{ color:#dbe7ff; }}

""",
        chrome=f"""QFrame#xpWindow {{ background:#0831d9; border-top-left-radius:8px; border-top-right-radius:8px; }}
QFrame#xpWindow[active="false"] {{ background:#6a8ae0; }}
QFrame#xpTitle {{ background:{grad('#0a5fe0', '#0545c8', '#3d95ff', 0.12)}; border-top-left-radius:7px; border-top-right-radius:7px; }}
QFrame#xpTitle[active="false"] {{ background:{grad('#7a9bea', '#6584d8', '#97b3f0', 0.12)}; }}
QLabel[kind="xptitle"] {{ color:white; font-family:{TITLE_FONT}; font-size:13px; font-weight:bold; background:transparent; }}
QPushButton[role="xpwin"], QPushButton[role="xpclose"] {{ border:1px solid white; border-radius:4px; color:white; font-size:12px; font-weight:bold; padding:0;
    background:{grad('#5f9bf5', '#1e5fd6')}; }}
QPushButton[role="xpwin"]:hover {{ background:{grad('#86b6ff', '#3b7ae8')}; }}
QPushButton[role="xpclose"] {{ background:{grad('#e8896a', '#c4381b')}; }}
QPushButton[role="xpclose"]:hover {{ background:{grad('#f5a68a', '#d9502e')}; }}
QFrame#xpMenu, QFrame#xpToolbar, QFrame#xpAddress, QFrame#xpStatus {{ background:#ece9d8; }}
QFrame#xpMenu QPushButton {{ background:transparent; border:none; padding:2px 8px; font-family:{XP_FONT}; font-size:12px; color:black; }}
QFrame#xpMenu QPushButton:hover {{ background:#316ac5; color:white; }}
QFrame#xpStatus {{ border-top:1px solid #aca899; }}
QLabel[kind="xpstatus"], QLabel[kind="xpmuted"], QLabel[kind="xpsmall"] {{ font-family:{XP_FONT}; font-size:11px; color:#4b4b4b; background:transparent; }}
QLabel[kind="xpmuted"] {{ font-size:12px; color:#6a6a6a; }}
QFrame#xpToolbar {{ border-bottom:1px solid #d4d0c8; }}
QPushButton[role="xptool"] {{ background:transparent; border:1px solid transparent; border-radius:3px; padding:3px 10px; font-family:{XP_FONT}; font-size:12px; color:black; }}
QPushButton[role="xptool"]:hover {{ background:#f6f4ea; border:1px solid #b6b19a; }}
QPushButton[role="xptool"]:checked {{ background:#e0ddc9; border:1px solid #8c8870; }}
QFrame[xpsep="1"] {{ background:#aca899; }}
QFrame#xpAddress QLineEdit {{ background:white; border:1px solid #7f9db9; font-family:{XP_FONT}; font-size:12px; padding:1px 4px; }}
""",
        explorer=f"""QWidget#xpPane {{ background:{grad('#7ba2e7', '#6375d6')}; }}
QFrame[xp="box"] {{ background:#d6dff7; border-radius:4px; }}
QPushButton[role="xphead"] {{ background:{grad('#ffffff', '#c6d3f7')}; border:none; border-top-left-radius:4px; border-top-right-radius:4px; text-align:left; padding:5px 10px;
    font-family:{XP_FONT}; font-weight:bold; font-size:12px; color:#215dc6; }}
QPushButton[role="xphead"]:hover {{ color:#428eff; }}
QPushButton[role="xplink"] {{ background:transparent; border:none; text-align:left; padding:3px 12px; font-family:{XP_FONT}; font-size:11px; color:#215dc6; }}
QPushButton[role="xplink"]:hover {{ color:#428eff; text-decoration:underline; }}
QFrame[xp="box"] QLabel {{ background:transparent; }}
QLabel[kind="xpbold"] {{ font-family:{XP_FONT}; font-weight:bold; font-size:12px; color:#1e3c8c; padding-left:10px; }}
QFrame[xp="box"] QLabel[kind="xpsmall"] {{ color:#2a3b7a; padding-left:10px; }}
QWidget#xpContent {{ background:white; }}
QLabel[kind="xph1"] {{ font-family:{TITLE_FONT}; font-size:26px; font-weight:bold; color:#1e3c8c; }}
QLabel[kind="xph2"] {{ font-family:{TITLE_FONT}; font-size:16px; font-weight:bold; color:#1e3c8c; }}
QFrame[xprule="1"] {{ background:#a9c1ee; }}
QFrame[xp="tip"] {{ background:#fffbe6; border:1px solid #e8dc9c; }}
""",
        start=f"""QFrame#startMenu {{ background:#4282d6; border:2px solid #0831d9; border-top-left-radius:8px; border-top-right-radius:8px; }}
QFrame#smHeader {{ background:{grad('#1c5fd6', '#0b47b8', '#3b8cf2', 0.3)}; border-top-left-radius:6px; border-top-right-radius:6px; }}
QFrame#smFooter {{ background:{grad('#2a6fe0', '#0b47b8')}; }}
QFrame#smLeft {{ background:white; }}
QFrame#smRight {{ background:#d3e5fa; border-left:1px solid #95bdee; }}
QLabel[kind="smname"] {{ font-family:{TITLE_FONT}; font-size:20px; font-weight:bold; color:white; background:transparent; }}
QLabel[kind="smsub"] {{ font-family:{XP_FONT}; font-size:11px; color:#d6e4ff; background:transparent; }}
QPushButton[role="smitem"], QPushButton[role="smright"], QPushButton[role="smfoot"], QPushButton[role="small"] {{ background:transparent; border:none; text-align:left; font-family:{XP_FONT};
    font-size:12px; color:#1d2b4f; padding:5px 8px; }}
QPushButton[role="smitem"]:hover, QPushButton[role="smright"]:hover {{ background:#316ac5; color:white; }}
QPushButton[role="smfoot"] {{ color:white; padding:6px 12px; }}
QPushButton[role="smfoot"]:hover {{ background:rgba(255,255,255,40); }}
QPushButton[role="small"] {{ font-weight:bold; text-align:center; }}
QPushButton[role="small"]:hover {{ background:#316ac5; color:white; }}
QFrame#startMenu QLabel[kind="smhead"] {{ font-family:{XP_FONT}; font-size:11px; color:#5a6c8f; background:transparent; padding:4px 8px; }}
""",
        menu=f"""QMenu {{ background:#fdfcf5; border:1px solid #7f9db9; font-family:{XP_FONT}; font-size:12px; color:black; padding:2px; }}
QMenu::item {{ padding:4px 24px; }}
QMenu::item:selected {{ background:#316ac5; color:white; }}
QMenu::separator {{ height:1px; background:#d4d0c8; margin:3px 2px; }}
""")


def taskbar_qss():
    return _sections()["taskbar"]


def window_frame_qss():
    c = _sections()["chrome"]
    keep = [l for l in c.split("\n") if l.startswith("QFrame#xpWindow")]
    return "\n".join(keep) + "\n" + _sections()["menu"]


def chrome_qss():
    return _sections()["chrome"]


def explorer_qss():
    return _sections()["explorer"]


def start_qss():
    return _sections()["start"] + _sections()["menu"]


def menu_qss():
    return _sections()["menu"]


def xp_qss():
    return "\n".join(_sections().values())

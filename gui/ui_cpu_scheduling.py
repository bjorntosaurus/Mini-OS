# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'cpu_scheduling.ui'
##
## Created by: Qt User Interface Compiler version 6.12.0
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QCheckBox, QFrame, QHBoxLayout,
    QHeaderView, QLabel, QPushButton, QScrollArea,
    QSizePolicy, QSpacerItem, QSpinBox, QTableWidget,
    QTableWidgetItem, QVBoxLayout, QWidget)

class Ui_Form(object):
    def setupUi(self, page):
        if not page.objectName():
            page.setObjectName(u"page")
        self.layout65 = QVBoxLayout(page)
        self.layout65.setSpacing(12)
        self.layout65.setObjectName(u"layout65")
        self.layout65.setContentsMargins(22, 16, 22, 10)
        self.hdr = QWidget(page)
        self.hdr.setObjectName(u"hdr")
        self.layout66 = QHBoxLayout(self.hdr)
        self.layout66.setSpacing(6)
        self.layout66.setObjectName(u"layout66")
        self.layout66.setContentsMargins(0, 0, 0, 0)
        self.titleBlock = QWidget(self.hdr)
        self.titleBlock.setObjectName(u"titleBlock")
        self.layout67 = QVBoxLayout(self.titleBlock)
        self.layout67.setSpacing(2)
        self.layout67.setObjectName(u"layout67")
        self.layout67.setContentsMargins(0, 0, 0, 0)
        self.lblTitle = QLabel(self.titleBlock)
        self.lblTitle.setObjectName(u"lblTitle")
        self.lblTitle.setWordWrap(False)

        self.layout67.addWidget(self.lblTitle)

        self.lblSub = QLabel(self.titleBlock)
        self.lblSub.setObjectName(u"lblSub")
        self.lblSub.setWordWrap(False)

        self.layout67.addWidget(self.lblSub)


        self.layout66.addWidget(self.titleBlock)

        self.spacer64 = QSpacerItem(20, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.layout66.addItem(self.spacer64)

        self.badge = QFrame(self.hdr)
        self.badge.setObjectName(u"badge")
        self.badge.setMinimumSize(QSize(0, 32))
        self.badge.setMaximumSize(QSize(16777215, 32))
        self.layout68 = QVBoxLayout(self.badge)
        self.layout68.setSpacing(6)
        self.layout68.setObjectName(u"layout68")
        self.layout68.setContentsMargins(20, 6, 20, 6)
        self.lblState = QLabel(self.badge)
        self.lblState.setObjectName(u"lblState")
        self.lblState.setWordWrap(False)

        self.layout68.addWidget(self.lblState)


        self.layout66.addWidget(self.badge)


        self.layout65.addWidget(self.hdr)

        self.body = QWidget(page)
        self.body.setObjectName(u"body")
        self.layout69 = QHBoxLayout(self.body)
        self.layout69.setSpacing(16)
        self.layout69.setObjectName(u"layout69")
        self.layout69.setContentsMargins(0, 0, 0, 0)
        self.rack = QFrame(self.body)
        self.rack.setObjectName(u"rack")
        self.rack.setMinimumSize(QSize(250, 0))
        self.rack.setMaximumSize(QSize(250, 16777215))
        self.layout70 = QVBoxLayout(self.rack)
        self.layout70.setSpacing(10)
        self.layout70.setObjectName(u"layout70")
        self.layout70.setContentsMargins(14, 14, 14, 14)
        self.lblRack = QLabel(self.rack)
        self.lblRack.setObjectName(u"lblRack")
        self.lblRack.setWordWrap(False)

        self.layout70.addWidget(self.lblRack)

        self.lblCount = QLabel(self.rack)
        self.lblCount.setObjectName(u"lblCount")
        self.lblCount.setWordWrap(False)

        self.layout70.addWidget(self.lblCount)

        self.scrollRack = QScrollArea(self.rack)
        self.scrollRack.setObjectName(u"scrollRack")
        self.scrollRack.setWidgetResizable(True)
        self.scrollRack.setFrameShape(QFrame.NoFrame)
        self.rackContent = QWidget()
        self.rackContent.setObjectName(u"rackContent")
        self.layout71 = QVBoxLayout(self.rackContent)
        self.layout71.setSpacing(10)
        self.layout71.setObjectName(u"layout71")
        self.layout71.setContentsMargins(0, 4, 4, 4)
        self.scrollRack.setWidget(self.rackContent)

        self.layout70.addWidget(self.scrollRack)

        self.btnAdd = QPushButton(self.rack)
        self.btnAdd.setObjectName(u"btnAdd")
        self.btnAdd.setMinimumSize(QSize(0, 40))
        self.btnAdd.setMaximumSize(QSize(16777215, 40))

        self.layout70.addWidget(self.btnAdd)


        self.layout69.addWidget(self.rack)

        self.right = QWidget(self.body)
        self.right.setObjectName(u"right")
        self.layout72 = QVBoxLayout(self.right)
        self.layout72.setSpacing(12)
        self.layout72.setObjectName(u"layout72")
        self.layout72.setContentsMargins(0, 0, 0, 0)
        self.algoRow = QWidget(self.right)
        self.algoRow.setObjectName(u"algoRow")
        self.layout73 = QHBoxLayout(self.algoRow)
        self.layout73.setSpacing(10)
        self.layout73.setObjectName(u"layout73")
        self.layout73.setContentsMargins(0, 0, 0, 0)
        self.btnFCFS = QPushButton(self.algoRow)
        self.btnFCFS.setObjectName(u"btnFCFS")
        self.btnFCFS.setCheckable(True)
        self.btnFCFS.setChecked(True)
        self.btnFCFS.setAutoExclusive(True)
        self.btnFCFS.setMinimumSize(QSize(96, 38))
        self.btnFCFS.setMaximumSize(QSize(16777215, 38))

        self.layout73.addWidget(self.btnFCFS)

        self.btnSJF = QPushButton(self.algoRow)
        self.btnSJF.setObjectName(u"btnSJF")
        self.btnSJF.setCheckable(True)
        self.btnSJF.setAutoExclusive(True)
        self.btnSJF.setMinimumSize(QSize(96, 38))
        self.btnSJF.setMaximumSize(QSize(16777215, 38))

        self.layout73.addWidget(self.btnSJF)

        self.btnRR = QPushButton(self.algoRow)
        self.btnRR.setObjectName(u"btnRR")
        self.btnRR.setCheckable(True)
        self.btnRR.setAutoExclusive(True)
        self.btnRR.setMinimumSize(QSize(96, 38))
        self.btnRR.setMaximumSize(QSize(16777215, 38))

        self.layout73.addWidget(self.btnRR)

        self.btnPriority = QPushButton(self.algoRow)
        self.btnPriority.setObjectName(u"btnPriority")
        self.btnPriority.setCheckable(True)
        self.btnPriority.setAutoExclusive(True)
        self.btnPriority.setMinimumSize(QSize(96, 38))
        self.btnPriority.setMaximumSize(QSize(16777215, 38))

        self.layout73.addWidget(self.btnPriority)

        self.spacer61 = QSpacerItem(20, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.layout73.addItem(self.spacer61)

        self.chkPreempt = QCheckBox(self.algoRow)
        self.chkPreempt.setObjectName(u"chkPreempt")

        self.layout73.addWidget(self.chkPreempt)

        self.lblQ = QLabel(self.algoRow)
        self.lblQ.setObjectName(u"lblQ")
        self.lblQ.setWordWrap(False)

        self.layout73.addWidget(self.lblQ)

        self.spinQuantum = QSpinBox(self.algoRow)
        self.spinQuantum.setObjectName(u"spinQuantum")
        self.spinQuantum.setMinimumSize(QSize(64, 30))
        self.spinQuantum.setMaximumSize(QSize(64, 30))
        self.spinQuantum.setMinimum(1)
        self.spinQuantum.setMaximum(1000000)
        self.spinQuantum.setValue(2)

        self.layout73.addWidget(self.spinQuantum)

        self.btnRun = QPushButton(self.algoRow)
        self.btnRun.setObjectName(u"btnRun")
        self.btnRun.setMinimumSize(QSize(132, 38))
        self.btnRun.setMaximumSize(QSize(16777215, 38))

        self.layout73.addWidget(self.btnRun)


        self.layout72.addWidget(self.algoRow)

        self.timeline = QFrame(self.right)
        self.timeline.setObjectName(u"timeline")
        self.layout74 = QVBoxLayout(self.timeline)
        self.layout74.setSpacing(6)
        self.layout74.setObjectName(u"layout74")
        self.layout74.setContentsMargins(18, 14, 18, 12)
        self.tlHead = QWidget(self.timeline)
        self.tlHead.setObjectName(u"tlHead")
        self.layout75 = QHBoxLayout(self.tlHead)
        self.layout75.setSpacing(6)
        self.layout75.setObjectName(u"layout75")
        self.layout75.setContentsMargins(0, 0, 0, 0)
        self.lblTl = QLabel(self.tlHead)
        self.lblTl.setObjectName(u"lblTl")
        self.lblTl.setWordWrap(False)

        self.layout75.addWidget(self.lblTl)

        self.spacer62 = QSpacerItem(20, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.layout75.addItem(self.spacer62)

        self.lblMode = QLabel(self.tlHead)
        self.lblMode.setObjectName(u"lblMode")
        self.lblMode.setWordWrap(False)

        self.layout75.addWidget(self.lblMode)


        self.layout74.addWidget(self.tlHead)

        self.ganttHost = QWidget(self.timeline)
        self.ganttHost.setObjectName(u"ganttHost")
        self.ganttHost.setMinimumSize(QSize(0, 96))
        self.layout76 = QVBoxLayout(self.ganttHost)
        self.layout76.setSpacing(0)
        self.layout76.setObjectName(u"layout76")
        self.layout76.setContentsMargins(0, 0, 0, 0)

        self.layout74.addWidget(self.ganttHost)

        self.tlFoot = QWidget(self.timeline)
        self.tlFoot.setObjectName(u"tlFoot")
        self.layout77 = QHBoxLayout(self.tlFoot)
        self.layout77.setSpacing(10)
        self.layout77.setObjectName(u"layout77")
        self.layout77.setContentsMargins(0, 0, 0, 0)
        self.btnFirst = QPushButton(self.tlFoot)
        self.btnFirst.setObjectName(u"btnFirst")

        self.layout77.addWidget(self.btnFirst)

        self.sep1 = QLabel(self.tlFoot)
        self.sep1.setObjectName(u"sep1")
        self.sep1.setWordWrap(False)

        self.layout77.addWidget(self.sep1)

        self.btnPlay = QPushButton(self.tlFoot)
        self.btnPlay.setObjectName(u"btnPlay")

        self.layout77.addWidget(self.btnPlay)

        self.sep2 = QLabel(self.tlFoot)
        self.sep2.setObjectName(u"sep2")
        self.sep2.setWordWrap(False)

        self.layout77.addWidget(self.sep2)

        self.btnStep = QPushButton(self.tlFoot)
        self.btnStep.setObjectName(u"btnStep")

        self.layout77.addWidget(self.btnStep)

        self.spacer63 = QSpacerItem(20, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.layout77.addItem(self.spacer63)

        self.lblPlayback = QLabel(self.tlFoot)
        self.lblPlayback.setObjectName(u"lblPlayback")
        self.lblPlayback.setWordWrap(False)

        self.layout77.addWidget(self.lblPlayback)


        self.layout74.addWidget(self.tlFoot)


        self.layout72.addWidget(self.timeline)

        self.ledger = QFrame(self.right)
        self.ledger.setObjectName(u"ledger")
        self.layout78 = QVBoxLayout(self.ledger)
        self.layout78.setSpacing(6)
        self.layout78.setObjectName(u"layout78")
        self.layout78.setContentsMargins(18, 14, 18, 10)
        self.lblLed = QLabel(self.ledger)
        self.lblLed.setObjectName(u"lblLed")
        self.lblLed.setWordWrap(False)

        self.layout78.addWidget(self.lblLed)

        self.tblLedger = QTableWidget(self.ledger)
        self.tblLedger.setObjectName(u"tblLedger")

        self.layout78.addWidget(self.tblLedger)


        self.layout72.addWidget(self.ledger)

        self.layout72.setStretch(2, 1)

        self.layout69.addWidget(self.right)

        self.layout69.setStretch(1, 1)

        self.layout65.addWidget(self.body)

        self.stats = QWidget(page)
        self.stats.setObjectName(u"stats")
        self.layout79 = QHBoxLayout(self.stats)
        self.layout79.setSpacing(18)
        self.layout79.setObjectName(u"layout79")
        self.layout79.setContentsMargins(0, 0, 0, 0)
        self.stat0 = QFrame(self.stats)
        self.stat0.setObjectName(u"stat0")
        self.stat0.setMinimumSize(QSize(0, 66))
        self.stat0.setMaximumSize(QSize(16777215, 66))
        self.layout80 = QVBoxLayout(self.stat0)
        self.layout80.setSpacing(4)
        self.layout80.setObjectName(u"layout80")
        self.layout80.setContentsMargins(14, 10, 14, 8)
        self.lblAvgWait = QLabel(self.stat0)
        self.lblAvgWait.setObjectName(u"lblAvgWait")
        self.lblAvgWait.setWordWrap(False)

        self.layout80.addWidget(self.lblAvgWait)

        self.capAvgWait = QLabel(self.stat0)
        self.capAvgWait.setObjectName(u"capAvgWait")
        self.capAvgWait.setWordWrap(False)

        self.layout80.addWidget(self.capAvgWait)


        self.layout79.addWidget(self.stat0)

        self.stat1 = QFrame(self.stats)
        self.stat1.setObjectName(u"stat1")
        self.stat1.setMinimumSize(QSize(0, 66))
        self.stat1.setMaximumSize(QSize(16777215, 66))
        self.layout81 = QVBoxLayout(self.stat1)
        self.layout81.setSpacing(4)
        self.layout81.setObjectName(u"layout81")
        self.layout81.setContentsMargins(14, 10, 14, 8)
        self.lblAvgTat = QLabel(self.stat1)
        self.lblAvgTat.setObjectName(u"lblAvgTat")
        self.lblAvgTat.setWordWrap(False)

        self.layout81.addWidget(self.lblAvgTat)

        self.capAvgTat = QLabel(self.stat1)
        self.capAvgTat.setObjectName(u"capAvgTat")
        self.capAvgTat.setWordWrap(False)

        self.layout81.addWidget(self.capAvgTat)


        self.layout79.addWidget(self.stat1)

        self.stat2 = QFrame(self.stats)
        self.stat2.setObjectName(u"stat2")
        self.stat2.setMinimumSize(QSize(0, 66))
        self.stat2.setMaximumSize(QSize(16777215, 66))
        self.layout82 = QVBoxLayout(self.stat2)
        self.layout82.setSpacing(4)
        self.layout82.setObjectName(u"layout82")
        self.layout82.setContentsMargins(14, 10, 14, 8)
        self.lblBusy = QLabel(self.stat2)
        self.lblBusy.setObjectName(u"lblBusy")
        self.lblBusy.setWordWrap(False)

        self.layout82.addWidget(self.lblBusy)

        self.capBusy = QLabel(self.stat2)
        self.capBusy.setObjectName(u"capBusy")
        self.capBusy.setWordWrap(False)

        self.layout82.addWidget(self.capBusy)


        self.layout79.addWidget(self.stat2)

        self.stat3 = QFrame(self.stats)
        self.stat3.setObjectName(u"stat3")
        self.stat3.setMinimumSize(QSize(0, 66))
        self.stat3.setMaximumSize(QSize(16777215, 66))
        self.layout83 = QVBoxLayout(self.stat3)
        self.layout83.setSpacing(4)
        self.layout83.setObjectName(u"layout83")
        self.layout83.setContentsMargins(14, 10, 14, 8)
        self.lblThru = QLabel(self.stat3)
        self.lblThru.setObjectName(u"lblThru")
        self.lblThru.setWordWrap(False)

        self.layout83.addWidget(self.lblThru)

        self.capThru = QLabel(self.stat3)
        self.capThru.setObjectName(u"capThru")
        self.capThru.setWordWrap(False)

        self.layout83.addWidget(self.capThru)


        self.layout79.addWidget(self.stat3)


        self.layout65.addWidget(self.stats)


        self.retranslateUi(page)

        QMetaObject.connectSlotsByName(page)
    # setupUi

    def retranslateUi(self, page):
        self.lblTitle.setText(QCoreApplication.translate("Form", u"DISPATCH", None))
        self.lblTitle.setProperty(u"kind", QCoreApplication.translate("Form", u"h1", None))
        self.lblSub.setText(QCoreApplication.translate("Form", u"CPU SCHEDULING / TIMELINE WORKSTATION", None))
        self.lblSub.setProperty(u"kind", QCoreApplication.translate("Form", u"eyebrow", None))
        self.badge.setProperty(u"card", QCoreApplication.translate("Form", u"accent", None))
        self.lblState.setText(QCoreApplication.translate("Form", u"\u25cf   READY", None))
        self.lblState.setProperty(u"kind", QCoreApplication.translate("Form", u"mono", None))
        self.rack.setProperty(u"card", QCoreApplication.translate("Form", u"shadow", None))
        self.lblRack.setText(QCoreApplication.translate("Form", u"PROCESS RACK", None))
        self.lblRack.setProperty(u"kind", QCoreApplication.translate("Form", u"eyebrow", None))
        self.lblCount.setText(QCoreApplication.translate("Form", u"04 ready processes", None))
        self.lblCount.setProperty(u"kind", QCoreApplication.translate("Form", u"h2", None))
        self.btnAdd.setText(QCoreApplication.translate("Form", u"+ Add process", None))
        self.btnAdd.setProperty(u"role", QCoreApplication.translate("Form", u"primary", None))
        self.btnFCFS.setText(QCoreApplication.translate("Form", u"FCFS", None))
        self.btnFCFS.setProperty(u"role", QCoreApplication.translate("Form", u"seg", None))
        self.btnSJF.setText(QCoreApplication.translate("Form", u"SJF", None))
        self.btnSJF.setProperty(u"role", QCoreApplication.translate("Form", u"seg", None))
        self.btnRR.setText(QCoreApplication.translate("Form", u"Round robin", None))
        self.btnRR.setProperty(u"role", QCoreApplication.translate("Form", u"seg", None))
        self.btnPriority.setText(QCoreApplication.translate("Form", u"Priority", None))
        self.btnPriority.setProperty(u"role", QCoreApplication.translate("Form", u"seg", None))
        self.chkPreempt.setText(QCoreApplication.translate("Form", u"Preemptive", None))
        self.lblQ.setText(QCoreApplication.translate("Form", u"Quantum", None))
        self.lblQ.setProperty(u"kind", QCoreApplication.translate("Form", u"eyebrow", None))
        self.btnRun.setText(QCoreApplication.translate("Form", u"\u25b6  Run queue", None))
        self.btnRun.setProperty(u"role", QCoreApplication.translate("Form", u"primary", None))
        self.timeline.setProperty(u"card", QCoreApplication.translate("Form", u"shadow", None))
        self.lblTl.setText(QCoreApplication.translate("Form", u"EXECUTION TIMELINE", None))
        self.lblTl.setProperty(u"kind", QCoreApplication.translate("Form", u"eyebrow", None))
        self.lblMode.setText(QCoreApplication.translate("Form", u"FCFS / non-preemptive", None))
        self.lblMode.setProperty(u"kind", QCoreApplication.translate("Form", u"eyebrow", None))
        self.btnFirst.setText(QCoreApplication.translate("Form", u"First", None))
        self.btnFirst.setProperty(u"role", QCoreApplication.translate("Form", u"link", None))
        self.sep1.setText(QCoreApplication.translate("Form", u"|", None))
        self.sep1.setProperty(u"kind", QCoreApplication.translate("Form", u"eyebrow", None))
        self.btnPlay.setText(QCoreApplication.translate("Form", u"Play", None))
        self.btnPlay.setProperty(u"role", QCoreApplication.translate("Form", u"link", None))
        self.sep2.setText(QCoreApplication.translate("Form", u"|", None))
        self.sep2.setProperty(u"kind", QCoreApplication.translate("Form", u"eyebrow", None))
        self.btnStep.setText(QCoreApplication.translate("Form", u"Step", None))
        self.btnStep.setProperty(u"role", QCoreApplication.translate("Form", u"link", None))
        self.lblPlayback.setText(QCoreApplication.translate("Form", u"Playback 1\u00d7 / 11 of 11 ms", None))
        self.lblPlayback.setProperty(u"kind", QCoreApplication.translate("Form", u"eyebrow", None))
        self.ledger.setProperty(u"card", QCoreApplication.translate("Form", u"shadow", None))
        self.lblLed.setText(QCoreApplication.translate("Form", u"TIMING LEDGER", None))
        self.lblLed.setProperty(u"kind", QCoreApplication.translate("Form", u"eyebrow", None))
        self.stat0.setProperty(u"card", QCoreApplication.translate("Form", u"shadow", None))
        self.lblAvgWait.setText(QCoreApplication.translate("Form", u"\u2014", None))
        self.lblAvgWait.setProperty(u"kind", QCoreApplication.translate("Form", u"stat", None))
        self.capAvgWait.setText(QCoreApplication.translate("Form", u"AVG WAIT", None))
        self.capAvgWait.setProperty(u"kind", QCoreApplication.translate("Form", u"eyebrow", None))
        self.stat1.setProperty(u"card", QCoreApplication.translate("Form", u"shadow", None))
        self.lblAvgTat.setText(QCoreApplication.translate("Form", u"\u2014", None))
        self.lblAvgTat.setProperty(u"kind", QCoreApplication.translate("Form", u"stat", None))
        self.capAvgTat.setText(QCoreApplication.translate("Form", u"AVG TURNAROUND", None))
        self.capAvgTat.setProperty(u"kind", QCoreApplication.translate("Form", u"eyebrow", None))
        self.stat2.setProperty(u"card", QCoreApplication.translate("Form", u"accent", None))
        self.lblBusy.setText(QCoreApplication.translate("Form", u"\u2014", None))
        self.lblBusy.setProperty(u"kind", QCoreApplication.translate("Form", u"stat", None))
        self.capBusy.setText(QCoreApplication.translate("Form", u"CPU BUSY", None))
        self.capBusy.setProperty(u"kind", QCoreApplication.translate("Form", u"eyebrow", None))
        self.stat3.setProperty(u"card", QCoreApplication.translate("Form", u"shadow", None))
        self.lblThru.setText(QCoreApplication.translate("Form", u"\u2014", None))
        self.lblThru.setProperty(u"kind", QCoreApplication.translate("Form", u"stat", None))
        self.capThru.setText(QCoreApplication.translate("Form", u"THROUGHPUT", None))
        self.capThru.setProperty(u"kind", QCoreApplication.translate("Form", u"eyebrow", None))
        pass
    # retranslateUi


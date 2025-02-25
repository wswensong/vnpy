import ctypes
import platform
import sys
import traceback
import webbrowser
import types
import threading

import qdarkstyle
from PySide6 import QtGui, QtWidgets, QtCore

from ..setting import SETTINGS
from ..utility import get_icon_path
from ..locale import _


# 导入必要的模块并设置别名以方便使用
Qt = QtCore.Qt
QtCore.pyqtSignal = QtCore.Signal
QtWidgets.QAction = QtGui.QAction
QtCore.QDate.toPyDate = QtCore.QDate.toPython
QtCore.QDateTime.toPyDate = QtCore.QDateTime.toPython

def create_qapp(app_name: str = "VeighNa Trader") -> QtWidgets.QApplication:
    """
    创建Qt应用程序。

    参数:
    app_name (str): 应用程序名称，默认为"VeighNa Trader"。

    返回:
    QtWidgets.QApplication: 创建的Qt应用程序实例。
    """
    # 设置深色样式表
    qapp: QtWidgets.QApplication = QtWidgets.QApplication(sys.argv)
    qapp.setStyleSheet(qdarkstyle.load_stylesheet(qt_api="pyside6"))

    # 设置字体
    font: QtGui.QFont = QtGui.QFont(SETTINGS["font.family"], SETTINGS["font.size"])
    qapp.setFont(font)

    # 设置图标
    icon: QtGui.QIcon = QtGui.QIcon(get_icon_path(__file__, "vnpy.ico"))
    qapp.setWindowIcon(icon)

    # 设置Windows进程ID
    if "Windows" in platform.uname():
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            app_name
        )

    # 隐藏所有对话框的帮助按钮
    # qapp.setAttribute(QtCore.Qt.AA_DisableWindowContextHelpButton)

    # 异常处理
    exception_widget: ExceptionWidget = ExceptionWidget()

    def excepthook(exctype: type, value: Exception, tb: types.TracebackType) -> None:
        """使用QMessageBox显示异常详细信息。"""
        sys.__excepthook__(exctype, value, tb)

        msg: str = "".join(traceback.format_exception(exctype, value, tb))
        exception_widget.signal.emit(msg)

    sys.excepthook = excepthook

    if sys.version_info >= (3, 8):
        def threading_excepthook(args: threading.ExceptHookArgs) -> None:
            """使用QMessageBox显示后台线程的异常详细信息。"""
            sys.__excepthook__(args.exc_type, args.exc_value, args.exc_traceback)

            msg: str = "".join(traceback.format_exception(args.exc_type, args.exc_value, args.exc_traceback))
            exception_widget.signal.emit(msg)

        threading.excepthook = threading_excepthook

    return qapp


class ExceptionWidget(QtWidgets.QWidget):
    """
    异常信息显示窗口。
    """
    signal: QtCore.Signal = QtCore.Signal(str)

    def __init__(self, parent: QtWidgets.QWidget = None) -> None:
        """
        初始化异常信息显示窗口。

        参数:
        parent (QtWidgets.QWidget): 父窗口部件，默认为None。
        """
        super().__init__(parent)

        self.init_ui()
        self.signal.connect(self.show_exception)

    def init_ui(self) -> None:
        """
        初始化用户界面。
        """
        self.setWindowTitle(_("触发异常"))
        self.setFixedSize(600, 600)

        self.msg_edit: QtWidgets.QTextEdit = QtWidgets.QTextEdit()
        self.msg_edit.setReadOnly(True)

        copy_button: QtWidgets.QPushButton = QtWidgets.QPushButton(_("复制"))
        copy_button.clicked.connect(self._copy_text)

        community_button: QtWidgets.QPushButton = QtWidgets.QPushButton(_("求助"))
        community_button.clicked.connect(self._open_community)

        close_button: QtWidgets.QPushButton = QtWidgets.QPushButton(_("关闭"))
        close_button.clicked.connect(self.close)

        hbox: QtWidgets.QHBoxLayout = QtWidgets.QHBoxLayout()
        hbox.addWidget(copy_button)
        hbox.addWidget(community_button)
        hbox.addWidget(close_button)

        vbox: QtWidgets.QVBoxLayout = QtWidgets.QVBoxLayout()
        vbox.addWidget(self.msg_edit)
        vbox.addLayout(hbox)

        self.setLayout(vbox)

    def show_exception(self, msg: str) -> None:
        """
        显示异常信息。

        参数:
        msg (str): 异常信息字符串。
        """
        self.msg_edit.setText(msg)
        self.show()

    def _copy_text(self) -> None:
        """
        复制异常信息文本。
        """
        self.msg_edit.selectAll()
        self.msg_edit.copy()

    def _open_community(self) -> None:
        """
        打开社区求助页面。
        """
        webbrowser.open("https://www.vnpy.com/forum/forum/2-ti-wen-qiu-zhu")
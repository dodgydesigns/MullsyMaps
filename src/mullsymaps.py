import sys
from PySide2.QtCore import Qt
from PySide2.QtWidgets import QApplication, QMainWindow

from graphics.windowFrame import WindowFrame
import preferences


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__(None, Qt.FramelessWindowHint)

        self.showFullScreen()

        self.windowFrame = WindowFrame()
        self.windowFrame.initUi()

        self.setCentralWidget(self.windowFrame)
        self.setStyleSheet(""" QMainWindow {background-color: black;} """)
        self.show()


if __name__ == '__main__':

    app = QApplication(sys.argv)
    preferences.SCREEN_RESOLUTION = app.desktop().screenGeometry()
    mm = MainWindow()
    sys.exit(app.exec_())
import sys

from PySide2.QtCore import Qt
from PySide2.QtWidgets import QApplication, QMainWindow

from graphics.copView import COPView


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__(None, Qt.FramelessWindowHint)

        self.showFullScreen()

        self.copView = COPView()
        self.copView.initUi(self.width(), self.height())

        self.setCentralWidget(self.copView)
        self.setStyleSheet(""" QMainWindow {background-color: black;} """)
        self.setAutoFillBackground(True)
        self.show()

if __name__ == '__main__':

    app = QApplication(sys.argv)
    cop = MainWindow()
    sys.exit(app.exec_())
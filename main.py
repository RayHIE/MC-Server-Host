"""Launch file for MC_ServerHost"""
import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from Frontend.main_window import MainWindow, resource_path

def main():
    """Starts App"""
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()

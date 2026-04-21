"""Settings page for users"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QComboBox, QPushButton, QMessageBox)
from PyQt6.QtCore import Qt, pyqtSignal

class SettingsPage(QWidget):
    """Main Settings page with UI"""
    set_apply = pyqtSignal(str, str)

    def __init__(self, conf_man):
        super().__init__()
        self.conf_man = conf_man
        self.init_ui()

    def init_ui(self):
        """Main UI"""
        lay = QVBoxLayout(self)
        lay.setAlignment(Qt.AlignmentFlag.AlignTop)
        lay.setSpacing(20)
        lay.setContentsMargins(40, 40, 40, 40)

        # Title
        tit = QLabel("App Settings")
        tit.setStyleSheet(
            "font-size: 28px; font-weight: bold; color: white;"
        )
        lay.addWidget(tit)

        # Description
        desc = QLabel(
            "Adjust the global application settings here. Changes will be saved "
            "automatically and applied immediately.             "
            "           Note: This page is broken and only changes windows outside of the main window."
            "           I am tired, boss."
        )
        desc.setStyleSheet("""
            QLabel {
                background-color: rgba(46, 46, 46, 0.85);
                border-radius: 12px;
                padding: 20px;
                font-size: 16px; 
                color: #cccccc;
            }""")
        desc.setWordWrap(True)
        lay.addWidget(desc)

        # Theme Menu
        thlay = QHBoxLayout()
        thlab = QLabel("App Theme:")
        thlab.setStyleSheet(
            "font-size: 18px; font-weight: bold; color: white;"
        )
        self.thdrop = QComboBox()
        self.thdrop.addItems(["Dark", "Light"])
        self.thdrop.setCurrentText(
            self.conf_man.settings.get("theme", "Dark")
            )
        self.thdrop.setStyleSheet(
            "background-color: #2e2e2e; color: white; padding: 8px; font-size: 16px;"
        )
        thlay.addWidget(thlab)
        thlay.addWidget(self.thdrop)
        thlay.addStretch()
        lay.addLayout(thlay)

        # Font menu
        flay = QHBoxLayout()
        flab = QLabel(
            "Base Font Size:"
        )
        flab.setStyleSheet(
            "font-size: 18px; font-weight: bold; color: white;"
        )
        self.fdrop = QComboBox()
        self.fdrop.addItems(["Small", "Normal", "Large"])
        self.fdrop.setStyleSheet(
            "background-color: #2e2e2e; color: white; padding: 8px; font-size: 16px;"
        )
        flay.addWidget(flab)
        flay.addWidget(self.fdrop)
        flay.addStretch()
        lay.addLayout(flay)

        # Apply button
        self.btn_apply = QPushButton("Apply Settings")
        self.btn_apply.setStyleSheet("""
            QPushButton {
                background-color: #32CD32; color: black; font-weight: bold; font-size: 16px; padding: 15px; border-radius: 6px;
            }
            QPushButton:hover { background-color: #28a428; }
        """)
        self.btn_apply.clicked.connect(self.apply_settings)
        lay.addWidget(self.btn_apply)

    def apply_settings(self):
        """Func to apply settings"""
        thsel = self.thdrop.currentText()
        fsel = self.fdrop.currentText()

        # Save the file
        self.conf_man.save_settings(thsel, fsel)

        # Update the main app
        self.set_apply.emit(thsel, fsel)
        QMessageBox.information(
            self, "Settings Saved", "Your settings have been applied."
        )

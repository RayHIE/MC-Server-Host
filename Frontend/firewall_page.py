"""Page for firewall setup"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QMessageBox)
from PyQt6.QtCore import Qt
from Backend.firewall_manager import FirewallTask

class FirewallPage(QWidget):
    """Main class for the firewall setup page"""
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        """UI Components & Layout"""
        lay = QVBoxLayout(self)
        lay.setAlignment(Qt.AlignmentFlag.AlignTop)
        lay.setSpacing(20)
        lay.setContentsMargins(40, 40, 40, 40)

        # Title
        tit = QLabel("Firewall Setup")
        tit.setStyleSheet(
            "font-size: 28px; font-weight: bold; color: white;"
        )
        lay.addWidget(tit)

        # Description
        desc = QLabel(
            "To allow players outside of your local network to connect to your server, "
            "you must open the specific port on your computer's firewall.\n\n"
            "This process will request Administrator privileges. It will automatically open "
            "both TCP and UDP connections."
        )
        desc.setStyleSheet( """
            QLabel {
                background-color: rgba(46, 46, 46, 0.85);
                border-radius: 12px;
                padding: 20px;
                font-size: 16px; 
                color: #E1E1E1;
            }
        """)
        desc.setWordWrap(True)
        lay.addWidget(desc)

        # Input
        inlay = QHBoxLayout()
        self.portlab = QLabel("Port:")
        self.portlab.setStyleSheet(
            "font-size: 18px; font-weight: bold; color: white;"
        )
        self.portinp = QLineEdit()
        self.portinp.setText("25565") # This is MC's default port.
        self.portinp.setStyleSheet(
            "font-size: 18px; font-weight: bold; color: white;"
        )
        self.portinp.setFixedWidth(150)
        inlay.addWidget(self.portlab)
        inlay.addWidget(self.portinp)
        inlay.addStretch()
        lay.addLayout(inlay)

        # Action Button
        self.btn_commit = QPushButton("Commit Firewall Rules")
        self.btn_commit.setStyleSheet("""
            QPushButton {
                background-color: #32CD32; color: black; font-weight: bold; font-size: 16px; padding: 15px; border-radius: 6px;
            }
            QPushButton:hover { background-color: #28a428; }
            QPushButton:disabled { background-color: #555555; color: #aaaaaa; }
        """)
        self.btn_commit.clicked.connect(self.commit_firewall)
        lay.addWidget(self.btn_commit)

        # Status Label
        self.statlab = QLabel("")
        self.statlab.setStyleSheet(
            "font-size: 16px; font-weight: bold;"
        )
        self.statlab.setWordWrap(True)
        lay.addWidget(self.statlab)

    def commit_firewall(self):
        """Commits firewall changes"""
        port = self.portinp.text().strip()
        if not port.isdigit():
            QMessageBox.warning(self, "Invalid Port")
            return

        # Lock UI to prevent spam
        self.btn_commit.setEnabled(False)
        self.portinp.setEnabled(False)
        self.statlab.setText("Requesting Administrator Permissions...")
        self.statlab.setStyleSheet("color: #FFD700;")

        # Background Thread
        self.fire_thread = FirewallTask(port)
        self.fire_thread.fin_signal.connect(self.on_firewall_finished)
        self.fire_thread.start()

    def on_firewall_finished(self, success, message):
        """Post commit cleanup"""
        # Enable UI
        self.btn_commit.setEnabled(True)
        self.portinp.setEnabled(True)

        # Update Status
        if success:
            self.statlab.setStyleSheet(
                "color: #32CD32;"
            )
        else:
            self.statlab.setStyleSheet(
                "color: #FF4C4C;"
            )
        self.statlab.setText(message)

"""Frontend page for server creation."""
import os
import json
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QComboBox, QSlider, QSpinBox, 
                             QPushButton, QProgressBar, QMessageBox)
from PyQt6.QtCore import Qt, QThread, pyqtSignal

# Importing backend API tools.
from Backend.api_manager import APIManager, ServerDownloaderThread
from Frontend.server_page import ServerPage

class VersionFetcherThread(QThread):
    """Background thread for loading versions."""
    ver_loaded = pyqtSignal(list)
    def run(self):
        """Func to fetch versions."""
        vers = APIManager.fetch_ver(only_releases=True)
        self.ver_loaded.emit(vers)

class JarUrlFetcherThread(QThread):
    """Background thread to parse for JAR URL"""
    url_fetched = pyqtSignal(str)
    def __init__(self, version_url):
        super().__init__()
        self.version_url = version_url

    def run(self):
        """Actual func to fetch JAR url"""
        jar_url = APIManager.fetch_server_jar_url(self.version_url)
        self.url_fetched.emit(jar_url if jar_url else "")

class CreatorPage(QWidget):
    """Creator page, makes new servers."""
    server_created = pyqtSignal()
    def __init__(self):
        super().__init__()
        self.version_data = []
        self.init_ui()
        self.load_vers()

    def init_ui(self):
        """General UI Setup"""
        lay = QVBoxLayout(self)
        lay.setAlignment(Qt.AlignmentFlag.AlignTop)
        lay.setSpacing(20)
        lay.setContentsMargins(40, 40, 40, 40)
        tit = QLabel("Create New Server")
        tit.setStyleSheet(
            "font-size: 28px; font-weight: bold; color: white;")
        lay.addWidget(tit)

        # Server Name Input
        self.nlab = QLabel("Server Name:")
        self.nlab.setStyleSheet("color: white; font-size: 16px;")
        self.inp = QLineEdit()
        self.inp.setStyleSheet(
            "background-color: #2e2e2e; color: white; padding: 8px; font-size: 16px; border-radius: 4px;")
        self.inp.setPlaceholderText("e.g., My Server.")
        lay.addWidget(self.nlab)
        lay.addWidget(self.inp)

        # Version Dropdown
        self.vlab = QLabel("Minecraft Version:")
        self.vlab.setStyleSheet("color: white; font-size: 16px;")
        self.vdro = QComboBox()
        self.vdro.setStyleSheet(
            "background-color: #2e2e2e; color: white; padding: 8px; font-size: 14px;")
        self.vdro.addItem("Loading versions...")
        self.vdro.setEnabled(False)
        lay.addWidget(self.vlab)
        lay.addWidget(self.vdro)

        # RAM allocation
        self.rlab = QLabel("RAM Allocations (GB):")
        self.rlab.setStyleSheet(
            "color: white; font-size: 16px;")
        lay.addWidget(self.rlab)
        rlay = QHBoxLayout()

        self.rslide = QSlider(Qt.Orientation.Horizontal)
        self.rslide.setRange(1, 32)
        self.rslide.setValue(4)

        self.rspin = QSpinBox()
        self.rspin.setRange(1, 32)
        self.rspin.setValue(4)
        self.rspin.setStyleSheet(
            "background-color: #2e2e2e; color: white; padding: 5px; font-size: 16px;")

        # Slider & Spinbox sync
        self.rslide.valueChanged.connect(self.rspin.setValue)
        self.rspin.valueChanged.connect(self.rslide.setValue)
        rlay.addWidget(self.rslide)
        rlay.addWidget(self.rspin)
        lay.addLayout(rlay)

        # Button & Progress
        self.btn_create = QPushButton("Create Server")
        self.btn_create.setStyleSheet("""
            QPushButton {
                background-color: #32CD32; color: black; font-weight: bold; font-size: 16px; padding: 12px; border-radius: 6px;
            }
            QPushButton:hover { background-color: #28a428; }
            QPushButton:disabled { background-color: #555555; color: #aaaaaa; }
        """)
        self.btn_create.clicked.connect(self.start_creation_process)
        lay.addWidget(self.btn_create)
        self.progbar = QProgressBar()
        self.progbar.setStyleSheet(
            "QProgressBar { color: white; text-align: center; } QProgressBar::chunk { background-color: #32CD32; }")
        self.progbar.setValue(0)
        self.progbar.hide()
        lay.addWidget(self.progbar)
        self.statlab = QLabel("")
        self.statlab.setStyleSheet("color: #aaaaaa; font-style: italic;")
        lay.addWidget(self.statlab)

    # Loading & Creation Logic
    def load_vers(self):
        """Loads versions into dropdown."""
        self.fetch_thread = VersionFetcherThread()
        self.fetch_thread.ver_loaded.connect(self.on_vers_loaded)
        self.fetch_thread.start()

    def on_vers_loaded(self, versions):
        """Adds versions to dropdown once loaded."""
        self.vdro.clear()
        if not versions:
            self.vdro.addItem("Failed to load versions.")
            return
        self.vers_data = versions
        for ver in versions:
            self.vdro.addItem(ver['id'])
        self.vdro.setEnabled(True)

    def start_creation_process(self):
        """Server Creation Engine."""
        ser_name = self.inp.text().strip()
        if not ser_name:
            QMessageBox.warning(self, "Error", "Please enter a server name.")
            return
        self.btn_create.setEnabled(False)
        self.vdro.setEnabled(False)
        self.inp.setEnabled(False)
        sel_indx = self.vdro.currentIndex()
        vers_inf = self.vers_data[sel_indx]
        self.statlab.setText("Fetching server JAR...")

        # Fetch JAR URL for selected version
        self.url_thr = JarUrlFetcherThread(vers_inf['url'])
        self.url_thr.url_fetched.connect(
            lambda url: self.download_and_setup_server(url, ser_name, vers_inf['id']))
        self.url_thr.start()

    def download_and_setup_server(self, jar_url, serv_name, ver_id):
        """Downloads server JAR and sets up server folder."""
        if not jar_url:
            self.statlab.setText("Failed to find JAR link for this version.")
            self.btn_create.setEnabled(True)
            return

        # 1: Create file struct.
        base_dir = os.path.expanduser("~/MC_ServerHost/Servers")
        serv_dir = os.path.join(base_dir, serv_name)
        os.makedirs(serv_dir, exist_ok=True)

        # 2: Write Config File
        conf_data = {
            "server_name": serv_name,
            "version": ver_id,
            "ram_gb": self.rspin.value(),
            "jar_file": f"server_{ver_id}.jar"
        }
        conf_path = os.path.join(serv_dir, "server_settings.json")
        with open(conf_path, "w", encoding="utf-8") as f:
            json.dump(conf_data, f, indent=4)

        # 3: Start Downloader Thread
        self.statlab.setText(f"Downloading server_{ver_id}.jar...")
        self.progbar.setValue(0)
        self.progbar.show()
        self.down_thread = ServerDownloaderThread(jar_url, serv_dir, ver_id)
        self.down_thread.progress_updated.connect(self.progbar.setValue)
        self.down_thread.download_finished.connect(self.on_download_complete)
        self.down_thread.start()

    def on_download_complete(self, success, result_str):
        """Post Download Cleanup and UI Reset."""
        if success:
            self.statlab.setText("Server created successfully!")
            eula_path = os.path.join(os.path.dirname(result_str), "eula.txt")
            with open(eula_path, "w", encoding="utf-8") as f:
                f.write("eula=true\n")

            self.statlab.setStyleSheet("color: #32CD32; font-weight: bold;")
            self.statlab.setText(
                "Server Creation Complete! You can now start it from the Servers tab.")

            # Enable the Servers button in main window
            self.server_created.emit()

        else:
            self.statlab.setStyleSheet("color: #FF4C4C;")
            self.statlab.setText(f"Download failed: {result_str}")

        # Enable inputs
        self.btn_create.setEnabled(True)
        self.vdro.setEnabled(True)
        self.inp.setEnabled(True)

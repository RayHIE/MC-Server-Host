"""Creates visuals upon booting."""
import os
import sys
from PyQt6.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
                             QPushButton, QStackedWidget, QLabel, QGraphicsBlurEffect, 
                             QApplication, QGraphicsOpacityEffect)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt, QPropertyAnimation

from Backend.server_manager import ServerManager
from Backend.config_manager import ConfigManager
from Frontend.server_page import ServerPage
from Frontend.creator_page import CreatorPage
from Frontend.firewall_page import FirewallPage
from Frontend.settings_page import SettingsPage

def resource_path(rel_path: str) -> str:
    """returns an absolute path to a resource."""
    if getattr(sys, "frozen", False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.dirname(__file__))
    return os.path.join(base_path, rel_path)

class MainWindow(QMainWindow):
    """Starts Main Window for application"""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MC ServerHost")
        self.resize(850, 700)

        # Variables
        self.serv_list = []
        self.serv_man = ServerManager()
        self.conf_man = ConfigManager()
        self.init_ui()

        # Apply settings
        self.apply_global_settings(
            self.conf_man.settings["theme"],
            self.conf_man.settings["font_size"]
        )

    def init_ui(self):
        """Widget and Label layout"""
        # Widget & Layout
        cent_widg = QWidget()
        self.setCentralWidget(cent_widg)
        mlay = QHBoxLayout(cent_widg)
        mlay.setContentsMargins(0, 0, 0, 0)
        mlay.setSpacing(0)

        # BG Image cross-fade

        # 1: Bottom Layer (Current Image)
        self.bg_labbot = QLabel(self)
        self.bg_labbot.resize(850, 700)
        self.bg_labbot.setScaledContents(True)
        blur1 = QGraphicsBlurEffect()
        blur1.setBlurRadius(15)
        self.bg_labbot.setGraphicsEffect(blur1)

        # 2: Top Layer Container
        self.bg_contop = QWidget(self)
        self.bg_contop.resize(850, 700)
        self.opa_effect = QGraphicsOpacityEffect()
        self.opa_effect.setOpacity(0.0)
        self.bg_contop.setGraphicsEffect(self.opa_effect)

        # 3: Top Layer Image
        self.bg_labtop = QLabel(self.bg_contop)
        self.bg_labtop. resize(850, 700)
        self.bg_labtop.setScaledContents(True)
        blur2 = QGraphicsBlurEffect()
        blur2.setBlurRadius(15)
        self.bg_labtop.setGraphicsEffect(blur2)

        # Push bg to absolute back
        self.bg_contop.lower()
        self.bg_labbot.lower()

        # 4: Setup Animation Obj.
        self.fade_anim = QPropertyAnimation(self.opa_effect, b"opacity")
        self.fade_anim.setDuration(500)
        self.fade_anim.setStartValue(0.0)
        self.fade_anim.setEndValue(1.0)
        self.fade_anim.finished.connect(self.on_fade_finished)
        self.current_bg_pixmap = None

        # Sidebar Setup
        self.sbar = QWidget()
        self.sbar.setFixedWidth(250)
        self.sbar.setStyleSheet("""
            QWidget {
                background-color: rgba(20, 20, 20, 0.95); 
                color: white;
            }
            QPushButton {
                text-align: left;
                padding: 15px 20px;
                font-size: 15px;
                font-weight: bold;
                background-color: transparent;
                border: none;
                border-left: 3px solid transparent;
            }
            QPushButton:hover {
                background-color: rgba(60, 60, 60, 0.6);
                border-left: 3px solid #32CD32;
            }
            QPushButton:disabled {
                color: #555555;
            }
        """)
        sbarlay = QVBoxLayout(self.sbar)
        sbarlay.setContentsMargins(0, 20, 0, 0)
        sbarlay.setSpacing(5)

        # Sidebar Buttons
        self.btn_serv = QPushButton("Servers")
        self.btn_creator = QPushButton("Server Creator")
        self.btn_fire = QPushButton("Firewall Setup")
        self.btn_set = QPushButton("Settings")
        sbarlay.addWidget(self.btn_serv)
        sbarlay.addWidget(self.btn_creator)
        sbarlay.addWidget(self.btn_fire)
        sbarlay.addWidget(self.btn_set)
        sbarlay.addStretch()

        # Page Area, stacked widget
        self.pages = QStackedWidget()
        self.pages.setStyleSheet(
            "background-color: transparent; color: white;"
        )

        # Start pages
        self.page_serv = ServerPage(self.serv_man)
        self.page_creator = CreatorPage()
        self.page_fire = FirewallPage()
        self.page_set = SettingsPage(self.conf_man)

        # Listen for "Apply Settings"
        add_pages = self.pages.addWidget
        self.page_set.set_apply.connect(self.apply_global_settings)
        add_pages(self.page_serv)
        add_pages(self.page_creator)
        add_pages(self.page_fire)
        add_pages(self.page_set)

        # Main Layout
        mlay.addWidget(self.sbar)
        mlay.addWidget(self.pages)

        # Sidebar Logic
        self.setup_sidebar_logic()

        # Set initial background
        self.set_background("bg_servers.png")

    def set_background(self, image_name):
        """Preps new image, starts cross-fade"""
        bg_path = resource_path(os.path.join("Assets", image_name))
        if not os.path.exists(bg_path):
            return
        new_pmap = QPixmap(bg_path)

        # Stop running animations, prevents bugging.
        if self.fade_anim.state() == QPropertyAnimation.State.Running:
            self.fade_anim.stop()
            if self.current_bg_pixmap:
                self.bg_labbot.setPixmap(self.current_bg_pixmap)
        self.current_bg_pixmap = new_pmap
        self.bg_labtop.setPixmap(new_pmap)

        # Snap to image upon first boot.
        if self.bg_labbot.pixmap() is None:
            self.bg_labbot.setPixmap(new_pmap)
        else:
            self.fade_anim.start()

    def on_fade_finished(self):
        """Lock bottom layer after cross-fade"""
        if self.current_bg_pixmap:
            self.bg_labbot.setPixmap(self.current_bg_pixmap)
        self.opa_effect.setOpacity(0.0)

    def switch_page(self, page_widg, bg_img_name):
        """Switches stacked widget and updating the background."""
        if self.pages.currentWidget() != page_widg:
            self.pages.setCurrentWidget(page_widg)
            self.set_background(bg_img_name)

    def setup_sidebar_logic(self):
        """Sidebar logic for entirety of the app"""
        # Server Check
        self.check_and_refresh_servers()

        # Listen to creator & server pages for refresh
        self.page_creator.server_created.connect(self.check_and_refresh_servers)
        self.page_serv.serv_del.connect(self.check_and_refresh_servers)

        # Connect Navigation
        self.btn_serv.clicked.connect(
            lambda: self.switch_page(
                self.page_serv, "bg_servers.png"))
        self.btn_creator.clicked.connect(
            lambda: self.switch_page(
                self.page_creator, "bg_creator.png"))
        self.btn_fire.clicked.connect(
            lambda: self.switch_page(
                self.page_fire, "bg_firewall.png"))
        self.btn_set.clicked.connect(
            lambda: self.switch_page(
                self.page_set, "bg_settings.png"))

    def apply_global_settings(self, theme, font_size):
        """Applies saved global settings"""
        app = QApplication.instance()

        # Font Size
        font = app.font()
        if font_size == "Small":
            font.setPointSize(10)
        elif font_size == "Normal":
            font.setPointSize(12)
        elif font_size == "Large":
            font.setPointSize(14)
        app.setFont(font)

        # Sidebar Theme
        if theme == "Light":
            self.sbar.setStyleSheet("""
                QWidget { background-color: rgba(240, 240, 240, 0.95); color: black; }
                QPushButton { text-align: left; padding: 15px 20px; font-size: 15px; font-weight: bold; background-color: transparent; border: none; border-left: 3px solid transparent; color: black;}
                QPushButton:hover { background-color: rgba(200, 200, 200, 0.6); border-left: 3px solid #32CD32; }
                QPushButton:disabled { color: #aaaaaa; }
                """)
        else:
            self.sbar.setStyleSheet("""
                QWidget { background-color: rgba(20, 20, 20, 0.95); color: white; }
                QPushButton { text-align: left; padding: 15px 20px; font-size: 15px; font-weight: bold; background-color: transparent; border: none; border-left: 3px solid transparent; color: white;}
                QPushButton:hover { background-color: rgba(60, 60, 60, 0.6); border-left: 3px solid #32CD32; }
                QPushButton:disabled { color: #555555; }
            """)

    def check_and_refresh_servers(self):
        """Loads servers from backend"""
        serv = self.serv_man.load_servers()
        if not serv:
            self.btn_serv.setEnabled(False)
            self.switch_page(self.page_creator, "bg_creator.png")
        else:
            self.btn_serv.setEnabled(True)
            self.page_serv.refresh_list()
            self.switch_page(self.page_serv, "bg_servers.png")

    def resizeEvent(self, event):
        """Keeps images stretched to window size. Prevents white space."""
        self.bg_labbot.resize(self.width(), self.height())
        self.bg_contop.resize(self.width(), self.height())
        self.bg_labtop.resize(self.width(), self.height())
        super().resizeEvent(event)

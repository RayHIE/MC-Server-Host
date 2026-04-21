"""Server page for MC ServerHost application"""
import os
import platform
import subprocess

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QTextEdit, QLineEdit, QLabel, 
                             QStackedWidget, QScrollArea, QFrame,
                             QDialog, QFormLayout, QSpinBox, QDialogButtonBox, QMessageBox)
from PyQt6.QtCore import Qt, QProcess, pyqtSignal

class ServerSettingsDialog(QDialog):
    """Dialog for server settings"""
    def __init__(self, serv_man, instnce, parent=None):
        super().__init__(parent)
        self.serv_man = serv_man
        self.instnce = instnce
        self.setWindowTitle(f"Settings - {instnce.name}")
        self.setFixedSize(320,160)
        self.setStyleSheet(
            "background-color: #2e2e2e; color: white; font-size: 14px;"
        )
        self.init_ui()

    def init_ui(self):
        """Main UI for the Server Page"""
        lay = QVBoxLayout(self)
        formlay = QFormLayout()
        self.portspin = QSpinBox()
        self.portspin.setRange(1, 65535)
        self.portspin.setStyleSheet(
            "background-color: #444; padding: 5px; color: white;"
        )

        self.playspin = QSpinBox()
        self.playspin.setRange(1, 100000)
        self.playspin.setStyleSheet(
            "background-color: #444; padding: 5px; color: white;"
        )

        self.motdinp = QLineEdit()
        self.motdinp.setStyleSheet(
            "background-color: #444; padding: 5px; color: white;"
        )

        props = self.serv_man.get_server_properties(self.instnce.config['folder_path'])

        self.portspin.setValue(props.get('server-port', 25565))
        self.playspin.setValue(props.get('max-players', 20))
        self.motdinp.setText(str(props.get('motd', 'A Minecraft Server')))

        formlay.addRow("Server Port:", self.portspin)
        formlay.addRow("Max Players:", self.playspin)
        formlay.addRow("MOTD:", self.motdinp)
        lay.addLayout(formlay)

        btn_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        btn_box.setStyleSheet(
            "QPushButton { background-color: #555; padding: 6px 15px; border-radius: 4px; font-weight: bold; } QPushButton:hover { background-color: #777; }"
        )
        btn_box.accepted.connect(self.save_settings)
        btn_box.rejected.connect(self.reject)
        lay.addWidget(btn_box)

    def save_settings(self):
        """Controls saving server settings"""
        if self.instnce.status in ["starting", "online"]:
            QMessageBox.warning(
                self, "Server Running", "You must stop the server before editing its properties."
                )
            return
        new_props = {
            'server-port': self.port_spinbox.value(), 
            'max-players': self.players_spinbox.value(), 
            'motd': self.motd_input.text()
        }
        self.serv_man.save_server_properties(self.instnce.config['folder_path'])
        self.accept()

class ServerPage(QWidget):
    """Class for the server page"""
    serv_del = pyqtSignal()

    def __init__(self, serv_man):
        super().__init__()
        self.serv_man = serv_man
        self.cur_serv = None
        self.card_statlab = {}
        self.card_statdot = {}
        self.card_playlab = {}
        self.init_ui()

    def init_ui(self):
        """Main UI of page"""
        mlay = QVBoxLayout(self)
        mlay.setContentsMargins(20, 20, 20, 20)
        self.stack_widg = QStackedWidget()
        mlay.addWidget(self.stack_widg)

        # 1. Server List
        self.lview = QWidget()
        llay = QVBoxLayout(self.lview)
        llay.setAlignment(Qt.AlignmentFlag.AlignTop)
        tit = QLabel("Your Servers")
        tit.setStyleSheet(
            "font-size: 28px; font-weight: bold; color: white;"
        )
        llay.addWidget(tit)
        scr = QScrollArea()
        scr.setWidgetResizable(True)
        scr.setStyleSheet(
            "QScrollArea { border: none; background-color: transparent; }"
        )
        self.card_cont = QWidget()
        self.cardlay = QVBoxLayout(self.card_cont)
        self.cardlay.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.cardlay.setSpacing(15)
        scr.setWidget(self.card_cont)
        llay.addWidget(scr)

        # 2. Console View
        self.conview = QWidget()
        conlay = QVBoxLayout(self.conview)
        topb = QHBoxLayout()
        self.btn_back = QPushButton("[<] Back")
        self.btn_back.setStyleSheet("background-color: #444; color: white; padding: 8px; border-radius: 4px; font-weight: bold;")
        self.btn_back.clicked.connect(self.show_list_view)

        self.btn_del = QPushButton("Delete")
        self.btn_del.setStyleSheet("""
            QPushButton { background-color: #8B0000; color: white; padding: 8px; border-radius: 4px; font-weight: bold; }
            QPushButton:hover { background-color: #FF4C4C; }
        """)
        self.btn_del.clicked.connect(self.delete_current_server)
        self.con_stat_ind = QLabel()
        self.con_stat_ind.setFixedSize(20, 20)
        self.serv_namelab = QLabel("Selected Server: None")
        self.serv_namelab.setStyleSheet(
            "font-size: 18px; font-weight: bold; color: white;"
        )
        self.btn_start = QPushButton("[>] Start")
        self.btn_stop = QPushButton("[x] Stop")
        topb.addWidget(self.btn_back)
        topb.addWidget(self.btn_del)
        topb.addSpacing(20)
        topb.addWidget(self.con_stat_ind)
        topb.addWidget(self.serv_namelab)
        topb.addStretch()
        topb.addWidget(self.btn_start)
        topb.addWidget(self.btn_stop)
        self.termout = QTextEdit()
        self.termout.setReadOnly(True)
        self.termout.setStyleSheet(
            "background-color: rgba(30, 30, 30, 0.9); color: #d4d4d4; font-family: Consolas; font-size: 14px;"
        )
        cmdlay = QHBoxLayout()
        self.cmdin = QLineEdit()
        self.cmdin.setStyleSheet(
            "background-color: #2e2e2e; color: white; padding: 5px;"
        )
        self.cmdin.setPlaceholderText(
            "Server command here. Type 'help' for help."
        )
        self.cmdin.returnPressed.connect(self.send_command)
        self.btn_send = QPushButton("Send")
        self.btn_send.clicked.connect(self.send_command)

        cmdlay.addWidget(self.cmdin)
        cmdlay.addWidget(self.btn_send)

        conlay.addLayout(topb)
        conlay.addWidget(self.termout)
        conlay.addLayout(cmdlay)

        self.stack_widg.addWidget(self.lview)
        self.stack_widg.addWidget(self.conview)

        self.btn_start.clicked.connect(self.start_server)
        self.btn_stop.clicked.connect(self.stop_server)

    def delete_current_server(self):
        """func to delete the currently selected server."""
        if not self.cur_serv:
            return
        if self.cur_serv.status in [
            "starting", "online"
        ]:
            QMessageBox.warning(self, "Server Running", "You must stop the server before deleting it.")
            return
        reply = QMessageBox.question(
            self, 'Confirm Permanent Deletion', 
            f"Are you sure you want to permanently delete '{self.cur_serv.name}'?\n\nThis action CANNOT be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, 
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            success = self.serv_man.delete_server(self.cur_serv.name)
            if success:
                self.serv_del.emit()
                self.show_list_view()
            else:
                QMessageBox.critical(
                    self, "Error", "Failed to delete the server folder. A file might be locked by another program."
                    )

    def refresh_list(self):
        """Refreshes server list."""
        for i in reversed(range(self.cardlay.count())):
            self.cardlay.itemAt(i).widget().setParent(None)
        self.card_statlab.clear()
        self.card_statdot.clear()
        self.card_playlab.clear()
        insta = self.serv_man.load_servers()
        if not insta:
            return
        for name, inst in insta.items():
            try:
                inst.stat_changed.disconnect()
                inst.stats_updated.disconnect()
                inst.log_updated.disconnect()
            except TypeError:
                pass
            inst.stat_changed.connect(self.on_status_changed)
            inst.stats_updated.connect(self.on_stats_updated)
            inst.log_updated.connect(self.on_log_updated)
            card = QFrame()
            card.setStyleSheet("""
                QFrame {
                    background-color: rgba(46, 46, 46, 0.85);
                    border-radius: 12px;
                    border: 1px solid transparent;
                }
                QFrame:hover { border: 1px solid #555; }
            """)
            cardlay = QHBoxLayout(card)
            inflay = QVBoxLayout()
            namelab = QLabel(name)
            namelab.setStyleSheet(
                "font-size: 20px; font-weight: bold; color: white; background: transparent;"
            )
            detlab = QLabel(
                f"Version: {inst.config['version']}  |  RAM: {inst.config['ram_gb']}GB"
            )
            inflay.addWidget(namelab)
            inflay.addWidget(detlab)
            statlay = QVBoxLayout()
            playlab = QLabel(
                f"Players Online: {inst.player_count}"
            )
            playlab.setStyleSheet(
                "font-size: 14px; color: white; background: transparent;"
            )
            statrow = QHBoxLayout()
            statdot = QLabel()
            statdot.setFixedSize(14, 14)
            col = self.serv_man.get_server_status_color(inst.status)
            statdot.setStyleSheet(
                "font-size: 14px; color: white; background: transparent;"
            )
            statlab = QLabel(
                f"Status: {inst.status.capitalize()}"
            )
            statlab.setStyleSheet(
                "font-size: 14px; color: white; background: transparent;"
            )
            statrow.addWidget(statdot)
            statrow.addWidget(statlab)
            statrow.addStretch()
            statlay.addWidget(playlab)
            statlay.addLayout(statrow)
            btnlay = QVBoxLayout()
            btn_man = QPushButton("Manage Console")
            btn_man.setStyleSheet("""
                QPushButton { background-color: #444; color: white; padding: 10px 20px; border-radius: 6px; font-weight: bold; }
                QPushButton:hover { background-color: #555; border: 1px solid #32CD32;}
            """)
            btn_man.clicked.connect(
                lambda checked, inst=inst: self.open_console(inst)
                )
            btnlay.addWidget(btn_man)

            mini_btnlay = QHBoxLayout()
            btn_set = QPushButton("⚙")
            btn_set.setStyleSheet("""
                QPushButton { background-color: #444; color: white; padding: 10px 20px; border-radius: 6px; font-weight: bold; }
                QPushButton:hover { background-color: #666; border: 1px solid #FFD700;}
            """)
            btn_set.clicked.connect(
                lambda checked, inst=inst: self.open_settings(inst)
            )
            btn_brws = QPushButton("📂")
            btn_brws.setStyleSheet("""
                QPushButton { background-color: #444; color: white; padding: 10px 20px; border-radius: 6px; font-weight: bold; }
                QPushButton:hover { background-color: #666; border: 1px solid #1E90FF;}
            """)
            btn_brws.clicked.connect(
                lambda checked, inst=inst: self.open_file_explorer(inst)
            )
            mini_btnlay.addWidget(btn_set)
            mini_btnlay.addWidget(btn_brws)

            btnlay.addLayout(mini_btnlay)

            cardlay.addLayout(inflay, stretch=2)
            cardlay.addLayout(statlay, stretch=1)
            cardlay.addLayout(btnlay)
            self.card_statlab[name] = statlab
            self.card_statdot[name] = statdot
            self.card_playlab[name] = playlab
            self.cardlay.addWidget(card)

    def on_status_changed(self,name, stat):
        """Define what happens for a stat change"""
        if name in self.card_statlab:
            self.card_statlab[name].setText(
                f"Status: {stat.capitalize()}"
                )
            col = self.serv_man.get_server_status_color(stat)
            self.card_statdot[name].setStyleSheet(
                f"background-color: {col}; border-radius: 7px; border: 1px solid black;"
            )
        if self.cur_serv and self.cur_serv.name == name:
            self.update_console_top_bar()

    def on_stats_updated(self, name, play):
        """Updates Player count"""
        if name in self.card_playlab:
            self.card_playlab[name].setText(
                f"Players Online: {play}"
            )

    def on_log_updated(self, name, lline):
        """Updates console log"""
        if self.cur_serv and self.cur_serv.name == name:
            self.termout.append(lline)

    def open_console(self, instance):
        """Opens the console for use in app."""
        print(f"Opening console for {instance.name}")
        self.cur_serv = instance
        self.serv_namelab.setText(
            f"Server: {instance.name}"
        )
        self.termout.clear()
        if not instance.log_history:
            self.termout.append(
                f"Loaded {instance.name} (Ready to start)\n"
            )
            self.update_console_top_bar()
            self.stack_widg.setCurrentWidget(self.conview)
            print("Console Success")
        else:
            self.termout.setHtml(
                "<br>".join(instance.log_history)
            )
            self.update_console_top_bar()
            print(f"Stack widget count: {self.stack_widg.count()}")
            print(f"Current widget: {self.stack_widg.currentWidget()}")
            self.stack_widg.setCurrentWidget(self.conview)
            print(f"After set, current widget: {self.stack_widg.currentWidget()}")
            self.stack_widg.update()
            self.update()
            print("Console Failure")

    def open_settings(self, insta):
        """Func to open settings dialog"""
        dia = ServerSettingsDialog(self.serv_man, insta, self)
        dia.exec()

    def open_file_explorer(self, insta):
        """Opens File system for each OS"""
        foldpath = insta.config.get('folder_path')
        if not foldpath or not os.path.exists(foldpath):
            QMessageBox.warning(
                self, "Error", "Server directory not found."
                )
            return

        os_name = platform.system()
        try:
            if os_name == "Windows":
                os.startfile(foldpath)
            elif os_name == "Linux":
                subprocess.run(["xdg-open", foldpath])
            elif os_name == "Darwin": # MacOS
                subprocess.run(["open", foldpath])
        except Exception as e:
            QMessageBox.critical(
                self, "Error", f"Failed to open file explorer: {e}"
            )

    def show_list_view(self):
        """Shows list of servers."""
        self.cur_serv = None
        self.stack_widg.setCurrentWidget(self.lview)

    def update_console_top_bar(self):
        """Updates the top bar of the console page"""
        if not self.cur_serv:
            return
        col = self.serv_man.get_server_status_color(
            self.cur_serv.status
        )
        self.con_stat_ind.setStyleSheet(
            f"background-color: {col}; border-radius: 10px; border: 1px solid black;"
        )
        if self.cur_serv.status in ["starting", "online"]:
            self.btn_start.setEnabled(False)
            self.btn_stop.setEnabled(True)
            self.btn_del.setEnabled(False)
            self.btn_del.setStyleSheet(
                "background-color: #555; color: #aaa; padding: 8px; border-radius: 4px; font-weight: bold;"
            )
        else:
            self.btn_start.setEnabled(True)
            self.btn_stop.setEnabled(False)
            self.btn_del.setEnabled(True)
            self.btn_del.setStyleSheet(
                "background-color: #8B0000; color: white; padding: 8px; border-radius: 4px; font-weight: bold;"
            )

    def start_server(self):
        """Starts selected server"""
        if not self.cur_serv:
            return
        jarpath = os.path.join(
            self.cur_serv.config['folder_path'], self.cur_serv.config['jar_file']
            )
        comm = self.serv_man.generate_startup_command(
            jarpath, self.cur_serv.config['ram_gb']
            )
        self.cur_serv.start(comm)

    def stop_server(self):
        """Stops selected server."""
        if self.cur_serv:
            self.cur_serv.stop()

    def send_command(self, cmd=None):
        """Sends commands to the console"""
        if not isinstance(cmd, str):
            cmd = self.cmdin.text()
        if cmd and self.cur_serv:
            self.cur_serv.send_command(cmd)
            self.cmdin.clear()

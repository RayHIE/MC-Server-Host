"""Manages server instances, loading, saving, and deleting."""
import os
import json
import shutil
from PyQt6.QtCore import QObject, QProcess, pyqtSignal

procstate = QProcess.ProcessState

class ServerInstance(QObject):
    """Main handler for server instances"""
    stat_changed = pyqtSignal(str, str)
    log_updated = pyqtSignal(str, str)
    stats_updated = pyqtSignal(str, int)

    def __init__(self, config_data):
        super().__init__()
        self.config = config_data
        self.name = config_data['server_name']
        self.status = "offline"
        self.player_count = 0
        self.log_history = []
        self.process = QProcess()
        self.process.setWorkingDirectory(self.config['folder_path'])
        self.process.readyReadStandardOutput.connect(self.handle_stdout)
        self.process.readyReadStandardError.connect(self.handle_stderr)
        self.process.stateChanged.connect(self.handle_state_change)

    def start(self, startup_command):
        """Starts server"""
        if self.process.state() == procstate.NotRunning:
            self.player_count = 0
            self.log_history.clear()
            self.process.setProgram(startup_command[0])
            self.process.setArguments(startup_command[1:])
            self.process.start()

    def stop(self):
        """Stops server process"""
        if self.process.state() == procstate.Running:
            self.process.write(b"stop\n")

    def send_command(self, cmd):
        """Sends commands to server"""
        if self.process.state() == procstate.Running:
            self.process.write((cmd + "\n").encode())

    def handle_stdout(self):
        """Handles output from server"""
        data = self.process.readAllStandardOutput().data().decode(errors='replace')
        for line in data.splitlines():
            if not line.strip(): 
                continue
            self.log_history.append(line)

            if len(self.log_history) > 1000:
                self.log_history.pop(100)
            self.log_updated.emit(self.name, line)

            if 'Done' in line and 'For help, type "help"' in line:
                self.status = "online"
                self.stat_changed.emit(self.name, self.status)

            if 'joined the game' in line:
                self.player_count += 1
                self.stats_updated.emit(self.name, self.player_count)
                self.process.write(b"say A player has joined the game!\n")

            elif 'left the game' in line:
                self.player_count -= 1
                self.stats_updated.emit(self.name, self.player_count)
                self.process.write(b"say A player has left the game!\n")

    def handle_stderr(self):
        """Handles error output from server"""
        data = self.process.readAllStandardError().data().decode(errors='replace')
        for line in data.splitlines():
            if not line.strip():
                continue

            formatted = f"<font color='#FF4C4C'>{line}</font>"
            self.log_history.append(formatted)
            self.log_updated.emit(self.name, formatted)

    def handle_state_change(self, state):
        """Handles state changes of server"""
        if state == procstate.Starting:
            self.status = "starting"
        elif state == procstate.NotRunning:
            self.status = "offline"
            self.player_count = 0
            self.stats_updated.emit(self.name, self.player_count)
        self.stat_changed.emit(self.name, self.status)

class ServerManager:
    """Main manager for server instances"""
    def __init__(self):
        self.base_dir = os.path.expanduser("~/MC_ServerHost/Servers")
        os.makedirs(self.base_dir, exist_ok=True)
        self.server_instances = {}

    def load_servers(self):
        """Loads server list"""
        if not os.path.exists(self.base_dir):
            return
        for folder in os.listdir(self.base_dir):
            config_path = os.path.join(self.base_dir, folder, "server_settings.json")
            if os.path.exists(config_path):
                try:
                    with open(config_path, "r") as f:
                        data = json.load(f)
                        data['folder_path'] = os.path.join(self.base_dir, folder)

                        if data['server_name'] not in self.server_instances:
                            self.server_instances[data['server_name']] = ServerInstance(data)
                except Exception as e:
                    print(f"Error Loading server: {folder} - {e}")
        return self.server_instances

    def generate_startup_command(self, jar_path, ram_gb=4):
        """Create startup commands"""
        ram_gb = max(2, min(ram_gb, 32))
        return ["java", f"-Xms{ram_gb}G", f"-Xmx{ram_gb}G", "-jar", jar_path, "nogui"]

    def get_server_status_color(self, status):
        """Gives color based on server status"""
        colors = {
            "offline" : "#FF4C4C",
            "starting" : "#FFD700",
            "online" : "#32CD32"
        }
        return colors.get(status, "#FF4C4C")

    def get_server_properties(self, folder_path):
        """Checks server.properties, extracts port, max-players, and motd."""
        props_path = os.path.join(folder_path, "server.properties")
        props = {
            "server-port" : 25565,
            "max-players" : 20,
            "motd" : "A minecraft Server"
        }
        if os.path.exists(props_path):
            with open(props_path, 'r') as f:
                for line in f:
                    if '=' in line and not line.strip().startswith('#'):
                        key, val = line.split('=', 1)
                        key, val = key.strip(), val.strip()
                        if key in props:
                            try:
                                props[key] = int(val)
                            except ValueError:
                                pass
        return props

    def save_server_properties(self, folder_path, new_props):
        """Overwrites specified keys in server.properties"""
        props_path = os.path.join(folder_path, "server.properties")
        lines = []
        if os.path.exists(folder_path, "server.properties"):
            with open(props_path, 'r') as f:
                lines = f.readlines()
        new_lines = []
        found_keys = set()
        for line in lines:
            if '=' in line and not line.strip().startswith('#'):
                key, _ = line.split('=', 1)
                key = key.strip()
                if key in new_props:
                    new_lines.append(f"{key}={new_props[key]}\n")
                    found_keys.add(key)
                else:
                    new_lines.append(line)
            else:
                new_lines.append(line)

        # No properties?
        for k, v in new_props.items():
            if k not in found_keys:
                new_lines.append(f"{k}={v}\n")

        with open(props_path, "w") as f:
            f.writelines(new_lines)

    def delete_server(self, server_name):
        """Delete server files for specified server"""
        if server_name in self.server_instances:
            instance = self.server_instances[server_name]
            if instance.process.state() == QProcess.ProcessState.Running:
                instance.process.kill()
                instance.process.waitForFinished(2000)
            folder_path = instance.config['folder_path']

            # File Removal
            if os.path.exists(folder_path):
                try:
                    shutil.rmtree(folder_path)
                except Exception as e:
                    print(f"Failed to delete {folder_path}: {e}")
                    return False
            del self.server_instances[server_name]
            return True
        return False

"""Creates Firewall rules for selected ports"""
import subprocess
import platform
from PyQt6.QtCore import QThread, pyqtSignal

class FirewallTask(QThread):
    """Background thread to handle admin prompts"""
    fin_signal = pyqtSignal(bool, str)
    def __init__(self, port):
        super().__init__()
        self.port = str(port)

    def run(self):
        """Main method for Firewall"""
        oname = platform.system()
        success = False
        message = ""
        try:
            if oname == "Windows":
                # Powershell, request UAC admin.
                ps_script = (
                    f"Start-Process netsh -ArgumentList 'advfirewall firewall add rule name=\"MCServerPort_{self.port}_TCP\" dir=in action=allow protocol=TCP localport={self.port}' -Verb RunAs -WindowStyle Hidden -Wait; "
                    f"Start-Process netsh -ArgumentList 'advfirewall firewall add rule name=\"MCServerPort_{self.port}_UDP\" dir=in action=allow protocol=UDP localport={self.port}' -Verb RunAs -WindowStyle Hidden -Wait; "
                )
                cmd = f'powershell -Command "{ps_script}"'
                subprocess.run(cmd, shell=True, check=True)
                success = True
                message = f"Opened Port {self.port}, TCP & UDP"

            elif oname == "Linux":
                # pkexec, request sudo admin.
                cmd = f"pkexec sh -c 'ufw allow {self.port}/tcp && ufw allow {self.port}/udp'"
                subprocess.run(cmd, shell=True, check=True)
                success = True
                message = f"Opened Port {self.port}, TCP & UDP"
            else:
                message = f"Unsupported OS: {oname}"
        except subprocess.CalledProcessError as e:
            message = f"Error occurred: {str(e)}"

        self.fin_signal.emit(success, message)

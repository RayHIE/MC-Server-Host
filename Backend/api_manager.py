"""API manager for the backend of the minecraft server host app."""
import urllib.request
import json
import os
from PyQt6.QtCore import QThread, pyqtSignal

url_request = urllib.request.Request
url_open = urllib.request.urlopen
file_join = os.path.join
mkdir = os.makedirs

class APIManager:
    """Parses the Minecraft version API for downloads and lists"""
    API_URL = "https://launchermeta.mojang.com/mc/game/version_manifest_v2.json"

    @staticmethod
    def fetch_ver(only_releases=True):
        """Fetches the manifest, returning a list of game versions."""
        try:
            req = url_request(APIManager.API_URL, headers={'User-Agent': 'Mozilla/5.0'})
            with url_open(req) as response:
                data = json.loads(response.read().decode())
            versions = []

            for version in data.get("versions", []):
                if only_releases and version.get("type") != "release":
                    continue

                versions.append({
                    "id" : version.get("id"),
                    "url" : version.get("url")
                })
            return versions
        except Exception as e:
            print(f"Failed to fetch versions: {e}")
            return []

    @staticmethod
    def fetch_server_jar_url(version_url):
        """Grabs Version URL and grabs the specific server.jar"""
        try:
            req = url_request(version_url, headers={'User-Agent': 'Mozilla/5.0'})
            with url_open(req) as response:
                data = json.loads(response.read().decode())

            # Grab the server download URL
            server_url = data.get("downloads", {}).get("server", {}).get("url")
            return server_url
        except Exception as e:
            print(f"Failed to fetch server jar: {e}")
            return None

class ServerDownloaderThread(QThread):
    """Background thread to download server.jar files"""

    # Communication for frontend UI
    progress_updated = pyqtSignal(int)
    download_finished = pyqtSignal(bool, str)

    def __init__(self, download_url, desination_folder, version_id):
        super().__init__()
        self.download_url = download_url
        self.destination_folder = desination_folder
        self.version_id = version_id

    def run(self):
        """Starts the download Process"""
        if not self.download_url:
            self.download_finished.emit(False, "Invalid Download.")
            return

        # Create folder if it doesn't exist.
        mkdir(self.destination_folder, exist_ok=True)
        file_path = file_join(self.destination_folder, f"server_{self.version_id}.jar")

        try:
            req = url_request(self.download_url, headers={"user-agent" : "Mozilla/5.0"})
            with url_open(req) as response, open(file_path, "wb") as out_file:
                file_size = int(response.info().get("Content-Length", -1))
                downloaded_size = 0
                chunk_size = 8192

                while True:
                    chunk = response.read(chunk_size)
                    if not chunk:
                        break

                    out_file.write(chunk)
                    downloaded_size += len(chunk)

                    if file_size > 0:
                        percentage = int((downloaded_size / file_size) * 100)
                        self.progress_updated.emit(percentage)
            self.download_finished.emit(True, file_path)
        except Exception as e:
            self.download_finished.emit(False, str(e))
    

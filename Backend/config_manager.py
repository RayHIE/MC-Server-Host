"""Config Manager for user settings."""
import os
import json
opath = os.path
class ConfigManager:
    """Main class to handle config saving and loading"""
    def __init__(self):
        #Saves settings permanently
        app_dir = opath.expanduser("~/MC_ServerHost")
        os.makedirs(app_dir, exist_ok=True)

        self.config_file = opath.join(app_dir, "app_settings.json")
        self.settings = self.load_settings()

    def load_settings(self):
        """Loads Previously saved settings"""
        default_settings = {
            "theme" : "Dark",
            "font_size" : "Normal"
        }
        if opath.exists(self.config_file):
            try:
                with open(self.config_file, "r") as f:
                    data = json.load(f)
                    default_settings.update(data)
            except Exception as e:
                print(f"Failed to load settings: {e}")
        return default_settings

    def save_settings(self, theme, font_size):
        """Saves settings"""
        self.settings["theme"] = theme
        self.settings["font_size"] = font_size
        try:
            with open(self.config_file, "w") as f:
                json.dump(self.settings, f, indent=4)
        except Exception as e:
            print(f"Failed to save settings: {e}")

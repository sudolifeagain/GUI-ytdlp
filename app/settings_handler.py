
# ファイル: app/settings_handler.py
# 役割: settings.jsonの読み書きを担当します。
import os
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SETTINGS_FILE = os.path.join(BASE_DIR, 'settings.json')
DOWNLOADS_DIR = os.path.join(BASE_DIR, 'downloads')

app_settings = {}

def load_settings():
    global app_settings
    try:
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                app_settings = json.load(f)
        else:
            app_settings = {
                "general": {"concurrentDownloads": 1, "showWelcomeNotice": True},
                "last_options": {"savePath": DOWNLOADS_DIR}
            }
            save_settings()
    except Exception as e:
        print(f"Error loading settings: {e}")
    return app_settings

def save_settings(new_settings):
    global app_settings
    app_settings = new_settings
    try:
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(app_settings, f, indent=4)
    except Exception as e:
        print(f"Error saving settings: {e}")

def get_setting(key, default=None):
    return app_settings.get(key, default)

# ---
import os


def web_app_enabled() -> bool:
    return os.environ.get("WEB_APP_ENABLED", "false").strip().lower() == "true"

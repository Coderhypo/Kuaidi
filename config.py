import os


def get_config(key, default=None):
    return os.getenv(key, default)

DB_URI = get_config("DB_URI", 'sqlite:///../kuaidi.db')
API_KEY = get_config("API_KEY")
SECRET_KEY = get_config("SECRET_KEY")
TOKEN_SECRET_KEY = get_config("TOKEN_SECRET_KEY")
INTERNAL_CODE = get_config("INTERNAL_CODE")

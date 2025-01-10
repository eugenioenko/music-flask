from os import urandom


class FlaskConfig(object):
    DEBUG = False
    TESTING = False
    SECRET_KEY = urandom(32)
    WTF_CSRF_SECRET_KEY = urandom(32)
    SESSION_TYPE = 'filesystem'
    PERMANENT_SESSION_LIFETIME = (60*60*24)


class ProductionConfig(FlaskConfig):
    DEBUG = False
    TESTING = False


class DevelopmentConfig(FlaskConfig):
    DEBUG = True


class TestingConfig(FlaskConfig):
    TESTING = True


class Settings:
    hostname = 'http://192.168.0.3:5000/'
    static_url = 'http://192.168.0.3/music-flask/'
    database = 'database.db'
    client_secret = '/include/client_secret.json'
    OAuth_client_id = ''\
        '.apps.googleusercontent.com'
    OAuth_client_secret = ''
    google_api_key = ''
    last_fm_key = ''
    last_fm_secret = ''
    bing_app_id = ''
    bing_azure_key = ''

settings = Settings()

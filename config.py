import os

class Config:
    DEBUG = False
    DEVELOPMENT = False
    IEX_KEY = os.getenv("IEX_KEY")
    GOOGLE_NEWS_KEY = os.getenv("GOOGLE_NEWS_KEY")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")

class ProductionConfig(Config):
    pass

# class StagingConfig(Config):
#     DEBUG = True

class DevelopmentConfig(Config):
    DEBUG = True
    DEVELOPMENT = True

class TestingConfig(Config):
    TESTING = True
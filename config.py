import os

class Config:
    DEBUG = False
    DEVELOPMENT = False
    IEX_API_KEY = os.getenv("IEX_API_KEY")
    NEWS_API_KEY = os.getenv("NEWS_API_KEY")
    SECRET_KEY = os.getenv("SECRET_KEY")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")
    # Fix database URI for Postgresql and SQLAlchemy for Heroku
    if SQLALCHEMY_DATABASE_URI is not None and SQLALCHEMY_DATABASE_URI.startswith("postgres://"):
        SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace("postgres://", "postgresql://", 1)
    
class ProductionConfig(Config):
    pass

# class StagingConfig(Config):
#     DEBUG = True

class DevelopmentConfig(Config):
    DEBUG = True
    DEVELOPMENT = True

class TestingConfig(Config):
    TESTING = True
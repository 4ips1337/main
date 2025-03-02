from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """
    Configuration settings for the application.

    Attributes:
        SECRET_KEY (str): Secret key for JWT token encoding and decoding.
        DATABASE_URL (str): URL of the database.
        CLOUDINARY_CLOUD_NAME (str): Cloudinary cloud name for image hosting.
        CLOUDINARY_API_KEY (str): Cloudinary API key for authentication.
        CLOUDINARY_API_SECRET (str): Cloudinary API secret for authentication.
        ALGORITHM (str): Algorithm used for JWT token encoding.
        ACCESS_TOKEN_EXPIRE_MINUTES (int): Expiration time for access tokens in minutes.
        REDIS_HOST (str): Hostname of the Redis server.
        REDIS_PORT (int): Port number of the Redis server.
    """

    SECRET_KEY: str
    DATABASE_URL: str
    CLOUDINARY_CLOUD_NAME: str
    CLOUDINARY_API_KEY: str
    CLOUDINARY_API_SECRET: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    REDIS_HOST: str  
    REDIS_PORT: int  

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8"
    }

settings = Settings()
"""
Global settings instance.
This instance provides access to all configuration values.
"""
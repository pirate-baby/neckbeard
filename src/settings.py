from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    github_access_token: str
    openai_api_key: str



settings = Settings()



# Load settings here. keys etc

import os
import logging
from pathlib import Path
from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict
load_dotenv()


class Settings(BaseSettings):
    # API Keys
    google_api_key: str = os.getenv("GOOGLE_API_KEY")
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"
    # central paths
    project_root: Path = Path(__file__).parent.parent
    vectorstore_root: Path = project_root / "vectorstore"
    data_path: Path = project_root / "data"
    # This allows Pydantic to ignore extra env vars in your .env file
    model_config = SettingsConfigDict(extra="ignore")
    repo_registry_path: Path = Path("data/repos.txt")


settings = Settings()

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

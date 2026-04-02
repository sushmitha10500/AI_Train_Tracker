"""
Configuration management for Train Tracker application.
Loads settings from environment variables with sensible defaults.
"""
import os
from typing import Final
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Application configuration loaded from environment variables."""
    
    # OpenAI Configuration
    OPENAI_API_KEY: Final[str] = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: Final[str] = "gpt-4o-mini"
    OPENAI_TEMPERATURE: Final[float] = 0.3
    OPENAI_MAX_TOKENS: Final[int] = 1000
    
    # Railway API Configuration
    RAILWAY_API_BASE_URL: Final[str] = os.getenv(
        "RAILWAY_API_BASE_URL", 
        "https://railradar.in/api/v1"
    )
    RAILWAY_API_TIMEOUT: Final[int] = int(os.getenv("RAILWAY_API_TIMEOUT", "15"))
    
    # Retry Configuration
    MAX_RETRY_ATTEMPTS: Final[int] = int(os.getenv("MAX_RETRY_ATTEMPTS", "3"))
    RETRY_BACKOFF_FACTOR: Final[int] = int(os.getenv("RETRY_BACKOFF_FACTOR", "2"))
    
    # Cache Configuration
    CACHE_TTL_SECONDS: Final[int] = int(os.getenv("CACHE_TTL_SECONDS", "3600"))
    CACHE_MAX_SIZE: Final[int] = int(os.getenv("CACHE_MAX_SIZE", "1000"))
    
    # Flask Configuration
    FLASK_HOST: Final[str] = os.getenv("FLASK_HOST", "0.0.0.0")
    FLASK_PORT: Final[int] = int(os.getenv("FLASK_PORT", "5000"))
    FLASK_DEBUG: Final[bool] = os.getenv("FLASK_DEBUG", "True").lower() == "true"
    
    # Logging Configuration
    LOG_LEVEL: Final[str] = os.getenv("LOG_LEVEL", "INFO")
    
    # Route Finding Configuration
    MIN_LAYOVER_MINUTES: Final[int] = 20
    MAX_LAYOVER_MINUTES: Final[int] = 720  # 12 hours
    MAX_ROUTES_TO_RETURN: Final[int] = 5
    
    # Layover Thresholds (in minutes)
    LAYOVER_TIGHT_THRESHOLD: Final[int] = 30
    LAYOVER_MODERATE_THRESHOLD: Final[int] = 60
    LAYOVER_COMFORTABLE_THRESHOLD: Final[int] = 180
    
    # Junction Search Limits
    MAX_JUNCTIONS_2_LEG: Final[int] = 15
    MAX_JUNCTIONS_3_LEG: Final[int] = 8
    MAX_JUNCTIONS_4_LEG: Final[int] = 6
    
    # Station Code Validation
    STATION_CODE_MIN_LENGTH: Final[int] = 2
    STATION_CODE_MAX_LENGTH: Final[int] = 5
    
    @classmethod
    def validate(cls) -> None:
        """Validate critical configuration values."""
        if not cls.OPENAI_API_KEY:
            raise ValueError(
                "OPENAI_API_KEY is not set. Please set it in your .env file or environment variables."
            )
        
        if not cls.OPENAI_API_KEY.startswith("sk-"):
            raise ValueError(
                "OPENAI_API_KEY appears to be invalid. It should start with 'sk-'"
            )


# Major Indian Railway Junctions
MAJOR_JUNCTIONS: Final[list[str]] = [
    "NDLS",  # New Delhi
    "HWH",   # Howrah
    "MAS",   # Chennai Central
    "SBC",   # Bangalore City
    "BCT",   # Mumbai Central
    "CSTM",  # Mumbai CST
    "PNBE",  # Patna
    "LKO",   # Lucknow
    "CNB",   # Kanpur Central
    "ADI",   # Ahmedabad
    "ST",    # Surat
    "BRC",   # Vadodara
    "PUNE",  # Pune
    "NGP",   # Nagpur
    "BPL",   # Bhopal
    "JBP",   # Jabalpur
    "HYB",   # Hyderabad Deccan
    "BZA",   # Vijayawada
    "VSKP",  # Visakhapatnam
    "TVC",   # Trivandrum Central
    "ERS",   # Ernakulam
    "CBE",   # Coimbatore
    "JP",    # Jaipur
    "AII",   # Ajmer
    "UDR",   # Udaipur
    "JSM",   # Jaisalmer
    "SVDK",  # Vaishno Devi Katra
    "JAT",   # Jammu Tawi
    "BBS",   # Bhubaneswar
    "KUR",   # Khurda Road
    "KGP",   # Kharagpur
    "R",     # Raipur
    "BSP",   # Bilaspur
    "KOAA",  # Kolkata
]

# Common station mappings for better AI accuracy
COMMON_STATION_MAPPINGS: Final[dict[str, str]] = {
    "GOA": "MAO",           # Madgaon
    "VAISHNO DEVI": "SVDK", # Shri Mata Vaishno Devi Katra
    "TIRUPATI": "TPTY",     # Tirupati Main
    "VARANASI": "BSB",      # Varanasi Junction
    "PURI": "PURI",         # Puri
    "SHIRDI": "SNSI",       # Sainagar Shirdi
    "MUMBAI": "CSTM",       # Mumbai CST
    "DELHI": "NDLS",        # New Delhi
    "KOLKATA": "KOAA",      # Kolkata
    "CHENNAI": "MAS",       # Chennai Central
    "BANGALORE": "SBC",     # Bangalore City
}

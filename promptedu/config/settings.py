import os
from pathlib import Path
from dotenv import load_dotenv

# .env 파일이 있는 경우 로드
env_path = Path(__file__).parent.parent / '.env'
if env_path.exists():
    load_dotenv(env_path)

# API 키 설정
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# 환경 설정
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

# 앱 설정
APP_NAME = "친절한 프롬프트 트레이너J"
APP_DESCRIPTION = "프롬프트 교육 플랫폼"
APP_VERSION = "1.0.0"

# 경로 설정
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
STATIC_DIR = BASE_DIR / "static"

# API 키 확인 함수
def is_api_key_set():
    """Gemini API 키가 설정되어 있는지 확인합니다."""
    return bool(GEMINI_API_KEY)

# 보안 관련 설정을 저장하는 함수
def store_api_key(api_key):
    """API 키를 메모리에 저장합니다. 
    참고: 실제 서비스에서는 더 안전한 방법을 사용하세요."""
    global GEMINI_API_KEY
    GEMINI_API_KEY = api_key
    return True 
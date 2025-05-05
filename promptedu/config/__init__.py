# 친절한 프롬프트 트레이너J - 설정 패키지
# 이 모듈은 애플리케이션 설정과 환경 변수를 관리합니다.

from .settings import *

__version__ = "1.0.0"

__all__ = [
    'GEMINI_API_KEY',
    'DEBUG',
    'ENVIRONMENT',
    'APP_NAME',
    'APP_DESCRIPTION',
    'APP_VERSION',
    'BASE_DIR',
    'DATA_DIR',
    'STATIC_DIR',
    'is_api_key_set',
    'store_api_key'
] 
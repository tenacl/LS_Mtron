@echo off
echo PromptEdu 설치 스크립트
echo =======================
echo.

REM Python 버전 확인
echo Python 버전 확인 중...
python --version 2>NUL
if %ERRORLEVEL% NEQ 0 (
  echo Python이 설치되어 있지 않습니다. Python 3.10을 설치해주세요.
  exit /b 1
)

REM 가상환경 생성
echo.
echo 가상환경 생성 중...
if exist venv (
  echo 'venv' 디렉토리가 이미 존재합니다.
  set /p response="새로 생성하시겠습니까? (기존 환경은 삭제됩니다) [y/N]: "
  if /i "%response%"=="y" (
    rmdir /s /q venv
    python -m venv venv
    echo 가상환경이 생성되었습니다.
  ) else (
    echo 기존 가상환경을 사용합니다.
  )
) else (
  python -m venv venv
  echo 가상환경이 생성되었습니다.
)

REM 가상환경 활성화
echo.
echo 가상환경 활성화 중...
call venv\Scripts\activate
echo 가상환경이 활성화되었습니다.

REM pip 업그레이드
echo.
echo pip 업그레이드 중...
pip install --upgrade pip
echo pip가 업그레이드되었습니다.

REM 의존성 패키지 설치
echo.
echo 필요한 패키지 설치 중...
pip install -r promptedu\requirements.txt
echo 패키지가 설치되었습니다.

REM .env 파일 생성
echo.
echo 환경 설정 파일 생성 중...
if exist promptedu\.env (
  echo 'promptedu\.env' 파일이 이미 존재합니다.
  set /p response="이 파일을 수정하시겠습니까? [y/N]: "
  if /i "%response%"=="y" (
    echo # PromptEdu 환경 설정 > promptedu\.env
    echo # 이 파일에 민감한 정보를 저장하세요. >> promptedu\.env
    echo. >> promptedu\.env
    echo # Gemini API 키 (https://makersuite.google.com/app/apikey에서 발급) >> promptedu\.env
    echo GEMINI_API_KEY= >> promptedu\.env
    echo. >> promptedu\.env
    echo # 환경 설정 >> promptedu\.env
    echo DEBUG=True >> promptedu\.env
    echo ENVIRONMENT=development >> promptedu\.env
    echo .env 파일이 수정되었습니다.
  ) else (
    echo 기존 .env 파일이 유지됩니다.
  )
) else (
  echo # PromptEdu 환경 설정 > promptedu\.env
  echo # 이 파일에 민감한 정보를 저장하세요. >> promptedu\.env
  echo. >> promptedu\.env
  echo # Gemini API 키 (https://makersuite.google.com/app/apikey에서 발급) >> promptedu\.env
  echo GEMINI_API_KEY= >> promptedu\.env
  echo. >> promptedu\.env
  echo # 환경 설정 >> promptedu\.env
  echo DEBUG=True >> promptedu\.env
  echo ENVIRONMENT=development >> promptedu\.env
  echo .env 파일이 생성되었습니다.
)

echo.
echo ==========================================
echo 설치가 완료되었습니다!
echo 다음 단계:
echo 1. promptedu\.env 파일에 Gemini API 키를 입력하세요.
echo 2. 애플리케이션을 실행하려면: run.bat
echo ========================================== 
@echo off
echo PromptEdu 실행 스크립트
echo ======================
echo.

REM 가상환경 활성화 확인
echo 가상환경 확인 중...

if not defined VIRTUAL_ENV (
  echo 가상환경을 활성화합니다...
  
  if exist venv (
    call venv\Scripts\activate
    echo 가상환경이 활성화되었습니다.
  ) else (
    echo 가상환경을 찾을 수 없습니다.
    echo setup.bat을 먼저 실행하여 환경을 설정해주세요.
    exit /b 1
  )
) else (
  echo 가상환경이 이미 활성화되어 있습니다.
)

REM .env 파일 확인
if not exist promptedu\.env (
  echo .env 파일이 없습니다. 기본 설정으로 생성합니다.
  
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
  echo 애플리케이션을 사용하려면 이 파일에 API 키를 입력하세요. 또는 앱 내에서 입력할 수도 있습니다.
)

REM Streamlit 실행
echo.
echo PromptEdu 애플리케이션을 시작합니다...
streamlit run promptedu\app.py 
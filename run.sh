#!/bin/bash

# 색상 정의
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}친절한 프롬프트 트레이너J 실행 스크립트${NC}"
echo -e "${BLUE}===========================================${NC}"

# 가상환경 활성화 확인
if [[ "$VIRTUAL_ENV" == "" ]]; then
  echo -e "${YELLOW}가상환경을 활성화합니다...${NC}"
  
  if [ -d "venv" ]; then
    source venv/bin/activate
    echo -e "${GREEN}✓ 가상환경이 활성화되었습니다.${NC}"
  else
    echo -e "${RED}✗ 가상환경을 찾을 수 없습니다.${NC}"
    echo -e "${YELLOW}setup.sh를 먼저 실행하여 환경을 설정해주세요.${NC}"
    exit 1
  fi
else
  echo -e "${GREEN}✓ 가상환경이 이미 활성화되어 있습니다.${NC}"
fi

# .env 파일 확인
if [ ! -f "promptedu/.env" ]; then
  echo -e "${YELLOW}⚠️ .env 파일이 없습니다. 기본 설정으로 생성합니다.${NC}"
  
  cat > promptedu/.env << EOL
# 친절한 프롬프트 트레이너J 환경 설정
# 이 파일에 민감한 정보를 저장하세요.

# Gemini API 키 (https://makersuite.google.com/app/apikey에서 발급)
GEMINI_API_KEY=

# 환경 설정
DEBUG=True
ENVIRONMENT=development
EOL
  
  echo -e "${GREEN}✓ .env 파일이 생성되었습니다.${NC}"
  echo -e "${YELLOW}애플리케이션을 사용하려면 이 파일에 API 키를 입력하세요. 또는 앱 내에서 입력할 수도 있습니다.${NC}"
fi

# 실행 중인 Streamlit 프로세스 확인 및 종료
pkill -f streamlit
echo -e "${YELLOW}기존 Streamlit 프로세스를 종료했습니다.${NC}"
sleep 2

# 현재 디렉토리 경로를 Python 경로에 추가
export PYTHONPATH="$PYTHONPATH:$(pwd)"
echo -e "${YELLOW}PYTHONPATH 설정: $PYTHONPATH${NC}"

# Google API 키 직접 환경 변수에 설정 - 따옴표와 공백 제거
export GEMINI_API_KEY=$(grep GEMINI_API_KEY promptedu/.env | cut -d'=' -f2 | sed 's/[" ]//g')
echo -e "${YELLOW}Gemini API 키가 환경 변수에 설정되었습니다.${NC}"

# 필요한 Python 패키지 확인
echo -e "${YELLOW}필요한 Python 패키지 확인 중...${NC}"
pip show google-generativeai > /dev/null 2>&1
if [ $? -ne 0 ]; then
  echo -e "${RED}⚠️ google-generativeai 패키지가 설치되어 있지 않습니다.${NC}"
  echo -e "${YELLOW}패키지를 설치합니다...${NC}"
  pip install google-generativeai==0.3.2
else
  echo -e "${GREEN}✓ 필요한 패키지가 설치되어 있습니다.${NC}"
fi

# Streamlit 실행 (다른 포트 사용)
echo -e "\n${YELLOW}친절한 프롬프트 트레이너J 애플리케이션을 시작합니다...${NC}"
cd "$(pwd)" && python -m streamlit run promptedu/app.py --server.port=8520 
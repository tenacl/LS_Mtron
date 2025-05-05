#!/bin/bash

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}친절한 프롬프트 트레이너J 설치 스크립트${NC}"
echo -e "${BLUE}===========================================${NC}"

# Python 버전 확인
echo -e "\n${YELLOW}Python 버전 확인 중...${NC}"
PYTHON_VERSION=$(python3 --version)

if [[ $PYTHON_VERSION == *"Python 3.10"* ]]; then
  echo -e "${GREEN}✓ Python 3.10 버전이 감지되었습니다: $PYTHON_VERSION${NC}"
  PYTHON_CMD="python3"
else
  echo -e "${YELLOW}⚠️ Python 3.10 버전을 사용하는 것이 권장됩니다.${NC}"
  echo -e "${YELLOW}⚠️ 현재 감지된 버전: $PYTHON_VERSION${NC}"
  
  # Python3.10 명령어 확인
  if command -v python3.10 &> /dev/null; then
    echo -e "${GREEN}✓ python3.10 명령어가 발견되었습니다.${NC}"
    PYTHON_CMD="python3.10"
  else
    echo -e "${RED}✗ Python 3.10이 설치되어 있지 않은 것 같습니다.${NC}"
    echo -e "${YELLOW}계속 진행하시겠습니까? (권장하지 않음) [y/N]${NC}"
    read -r response
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
      PYTHON_CMD="python3"
    else
      echo -e "${RED}설치가 취소되었습니다. Python 3.10을 설치한 후 다시 시도해주세요.${NC}"
      exit 1
    fi
  fi
fi

# 가상환경 생성
echo -e "\n${YELLOW}가상환경 생성 중...${NC}"
if [ -d "venv" ]; then
  echo -e "${YELLOW}⚠️ 'venv' 디렉토리가 이미 존재합니다.${NC}"
  echo -e "${YELLOW}새로 생성하시겠습니까? (기존 환경은 삭제됩니다) [y/N]${NC}"
  read -r response
  if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
    rm -rf venv
    $PYTHON_CMD -m venv venv
    echo -e "${GREEN}✓ 가상환경이 생성되었습니다.${NC}"
  else
    echo -e "${YELLOW}기존 가상환경을 사용합니다.${NC}"
  fi
else
  $PYTHON_CMD -m venv venv
  echo -e "${GREEN}✓ 가상환경이 생성되었습니다.${NC}"
fi

# 가상환경 활성화
echo -e "\n${YELLOW}가상환경 활성화 중...${NC}"
source venv/bin/activate
echo -e "${GREEN}✓ 가상환경이 활성화되었습니다.${NC}"

# pip 업그레이드
echo -e "\n${YELLOW}pip 업그레이드 중...${NC}"
pip install --upgrade pip
echo -e "${GREEN}✓ pip가 업그레이드되었습니다.${NC}"

# 의존성 패키지 설치
echo -e "\n${YELLOW}필요한 패키지 설치 중...${NC}"
pip install -r promptedu/requirements.txt
echo -e "${GREEN}✓ 패키지가 설치되었습니다.${NC}"

# .env 파일 생성
echo -e "\n${YELLOW}환경 설정 파일 생성 중...${NC}"
if [ -f "promptedu/.env" ]; then
  echo -e "${YELLOW}⚠️ 'promptedu/.env' 파일이 이미 존재합니다.${NC}"
  echo -e "${YELLOW}이 파일을 수정하시겠습니까? [y/N]${NC}"
  read -r response
  if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
    cat > promptedu/.env << EOL
# 친절한 프롬프트 트레이너J 환경 설정
# 이 파일에 민감한 정보를 저장하세요.

# Gemini API 키 (https://makersuite.google.com/app/apikey에서 발급)
GEMINI_API_KEY=

# 환경 설정
DEBUG=True
ENVIRONMENT=development
EOL
    echo -e "${GREEN}✓ .env 파일이 수정되었습니다.${NC}"
  else
    echo -e "${YELLOW}기존 .env 파일이 유지됩니다.${NC}"
  fi
else
  # .env 파일 생성
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
fi

echo -e "\n${BLUE}==========================================${NC}"
echo -e "${GREEN}설치가 완료되었습니다!${NC}"
echo -e "${YELLOW}다음 단계:${NC}"
echo -e "1. ${YELLOW}promptedu/.env 파일에 Gemini API 키를 입력하세요.${NC}"
echo -e "2. ${YELLOW}애플리케이션을 실행하려면:${NC} ${GREEN}./run.sh${NC}"
echo -e "${BLUE}==========================================${NC}" 
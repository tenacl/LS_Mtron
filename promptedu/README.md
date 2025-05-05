# 친절한 프롬프트 트레이너J

프롬프트 작성 능력을 향상시키는 교육 플랫폼입니다. 다양한 AI 도구를 효과적으로 활용하기 위한 체계적인 30일 훈련 과정을 제공합니다.

## 제공 트랙

- 🟢 **텍스트 초급**: 프롬프트의 기본 구조와 작성법 이해
- 🟡 **텍스트 중급**: 조건, 반복, 포맷 제어 등 고급 프롬프트 능력 강화
- 🔎 **딥리서치**: LLM을 활용한 심층 정보 수집 능력 향상
- 🎨 **이미지 프롬프트**: MidJourney, DALL·E 등을 위한 시각 묘사 프롬프트
- 🎬 **영상 프롬프트**: Runway, Sora, Pika 등을 위한 영상 프롬프트

## 설치 및 실행

### 1. 준비사항

- Python 3.10 이상
- Gemini API 키 (https://aistudio.google.com/)

### 2. 설치

```bash
# 가상 환경 생성 (Python 3.10 필수)
python -m venv venv

# 가상 환경 활성화
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

# 필요한 패키지 설치
pip install -r requirements.txt
```

### 3. API 키 설정

`.env` 파일을 프로젝트 루트 디렉토리에 생성하고 다음 내용을 추가하세요:

```
GEMINI_API_KEY=your_api_key_here
```

또는 애플리케이션 실행 후 사이드바에서 API 키를 직접 입력할 수 있습니다.

### 4. 실행

```bash
# Windows
python -m streamlit run app.py

# macOS/Linux
python -m streamlit run app.py
```

## 기능

- **30일 훈련 가이드**: 각 트랙별로 체계적인 30일 훈련 과정 제공
- **프롬프트 생성기**: 다양한 프롬프트 예시 생성 및 학습 
- **프롬프트 평가**: 작성한 프롬프트에 대한 피드백 제공

## 개발자

- 제작: 여행가J ([@jkwon](https://litt.ly/jkwon))
- 문의: [스타트업실험실](https://www.startuplab.seoul.kr/)

## 사용 기술

- Streamlit
- Google Gemini AI
- Python 3.10

## 라이선스

이 프로젝트는 개인 및 교육 목적으로만 사용할 수 있습니다. 
# PromptEdu - 프롬프트 교육 플랫폼

PromptEdu는 다양한 AI 도구를 효과적으로 활용하기 위한 프롬프트 작성 능력을 훈련하는 웹 기반 교육 플랫폼입니다.

## 📋 주요 기능

- **5가지 전문 트랙**: 텍스트 초급, 텍스트 중급, 딥리서치, 이미지 프롬프트, 영상 프롬프트
- **30일 훈련 가이드**: 각 트랙별 단계적 학습 가이드 제공
- **프롬프트 생성기**: 제미나이 API를 활용한 맞춤형 프롬프트 생성 기능

## 🚀 설치 및 실행 방법

### 필요 조건
- Python 3.10
- Gemini API 키 ([Google AI Studio](https://makersuite.google.com/app/apikey)에서 발급 가능)

### 설치 방법

1. 저장소 클론 후 프로젝트 폴더로 이동
```bash
git clone https://github.com/yourusername/promptedu.git
cd LS_Mtron
```

2. Python 3.10 가상 환경 생성 및 활성화
```bash
# macOS/Linux
python3.10 -m venv venv
source venv/bin/activate

# Windows
py -3.10 -m venv venv
venv\Scripts\activate
```

3. 필요 패키지 설치
```bash
pip install -r promptedu/requirements.txt
```

4. 환경 변수 설정 (두 가지 방법 중 선택)
   
   a) `.env` 파일 생성 (권장)
   ```bash
   # promptedu/.env 파일 생성
   echo "GEMINI_API_KEY=your_api_key_here" > promptedu/.env
   ```
   
   b) 터미널에서 직접 설정
   ```bash
   # Linux/Mac
   export GEMINI_API_KEY="your_api_key_here"

   # Windows
   set GEMINI_API_KEY=your_api_key_here
   ```

5. 애플리케이션 실행
```bash
streamlit run promptedu/app.py
```

## 📊 트랙 구성

1. **🟢 텍스트 초급 트랙**
   - 프롬프트의 기본 구조와 작성법 이해
   - 명확하고 구체적인 프롬프트 작성 능력 향상

2. **🟡 텍스트 중급 트랙**
   - 조건, 반복, 포맷 제어 등 고급 프롬프트 능력 강화
   - 상황별 최적화된 프롬프트 작성

3. **🔎 딥리서치 트랙**
   - LLM 기반 심층 정보 수집 프롬프트 작성 능력 향상
   - 다중 출처, 분석 형식 지정 등 고급 리서치 기법

4. **🎨 이미지 프롬프트 트랙**
   - MidJourney, DALL·E 등을 위한 시각 묘사 프롬프트
   - 주제, 배경, 스타일, 분위기 등 구조화된 요소 학습

5. **🎬 영상 프롬프트 트랙**
   - Runway, Sora, Pika 등을 위한 영상 프롬프트
   - 카메라 움직임, 장면 묘사, 시퀀스 구성 능력 강화

## 🛠️ 프로젝트 구조

```
LS_Mtron/
└── promptedu/
    ├── app.py               # 메인 애플리케이션 파일
    ├── requirements.txt     # 의존성 파일
    ├── README.md            # 프로젝트 설명
    ├── config/              # 설정 관리
    │   ├── __init__.py
    │   └── settings.py
    ├── data/                # 트랙별 데이터 파일
    │   ├── text_beginner_track.json
    │   ├── text_intermediate_track.json
    │   ├── deep_research_track.json
    │   ├── image_prompt_track.json
    │   └── video_prompt_track.json
    └── static/              # 정적 파일
        ├── css/
        ├── js/
        └── images/
            └── prompt_edu_banner.png
```

## ❓ 문제 해결

1. **API 키 오류**
   - API 키가 올바르게 설정되었는지 확인하세요
   - 웹 애플리케이션 실행 후 사이드바에서 API 키를 직접 입력할 수도 있습니다

2. **패키지 설치 오류**
   - Python 3.10 환경인지 확인하세요: `python --version`
   - pip를 최신 버전으로 업데이트하세요: `pip install --upgrade pip`

3. **Streamlit 실행 오류**
   - 포트 충돌 시: `streamlit run promptedu/app.py --server.port=8501`

## 📝 라이선스

이 프로젝트는 MIT 라이선스를 따릅니다.

---

PromptEdu는 프롬프트 엔지니어링 교육을 위한 오픈소스 프로젝트입니다. 
import streamlit as st
import requests
import json
import os
import sys
from pathlib import Path
import re

# 현재 디렉토리를 sys.path에 추가하여 모듈을 찾을 수 있도록 함
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

try:
    import google.generativeai as genai
except ImportError:
    st.error("google.generativeai 모듈을 찾을 수 없습니다. 필요한 패키지가 설치되어 있는지 확인해주세요.")
    st.info("pip install google-generativeai==0.3.2")
    st.stop()

# 설정 모듈 import (상대 경로로 변경)
try:
    from .config.settings import (
        GEMINI_API_KEY, 
        APP_NAME, 
        APP_DESCRIPTION,
        is_api_key_set,
        store_api_key,
        DATA_DIR,
        STATIC_DIR
    )
except ImportError:
    # 직접 경로 지정
    CONFIG_DIR = os.path.join(current_dir, "config")
    sys.path.insert(0, CONFIG_DIR)
    try:
        from config.settings import (
            GEMINI_API_KEY, 
            APP_NAME, 
            APP_DESCRIPTION,
            is_api_key_set,
            store_api_key,
            DATA_DIR,
            STATIC_DIR
        )
    except ImportError:
        st.error("설정 모듈을 불러올 수 없습니다.")
        st.stop()

# 페이지 기본 설정
st.set_page_config(
    page_title=f"{APP_NAME} - {APP_DESCRIPTION}",
    page_icon="🧠",
    layout="wide"
)

# CSS 적용
def load_css():
    css_file = STATIC_DIR / "css" / "style.css"
    if css_file.exists():
        with open(css_file, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    else:
        st.warning("CSS 파일을 찾을 수 없습니다.")

# API 키 설정 및 관리
def setup_api():
    # 먼저 환경 변수에서 API 키를 가져옵니다
    api_key = os.environ.get("GEMINI_API_KEY", "")
    
    if api_key:
        # 환경 변수에 API 키가 있으면 그것을 사용
        genai.configure(api_key=api_key)
        store_api_key(api_key)  # 전역 변수 업데이트
        st.toast("환경 변수에서 API 키를 불러왔습니다.", icon="🔑")
    elif is_api_key_set():
        # config에서 가져온 API 키가 있으면 사용
        genai.configure(api_key=GEMINI_API_KEY)
    else:
        # 하드코딩된 백업 API 키 사용
        backup_key = "AIzaSyDdx6biN2-jq3v3wjJkWt4UNoOxkBwwq-Q" 
        genai.configure(api_key=backup_key)
        store_api_key(backup_key)  # 전역 변수 업데이트
        st.toast("백업 API 키를 사용합니다.", icon="🔑")

# 사이드바 내비게이션 설정
def setup_sidebar():
    st.sidebar.title(APP_NAME)

    # 모든 옵션을 하나의 리스트로 통합
    st.sidebar.markdown("#### 메뉴 선택")
    
    # 통합된 옵션 리스트 - 트랙과 생성기 모두 포함
    all_options = [
        ("🏠 홈", "home"),
        ("🟢 초급 프롬프트", "beginner"),
        ("🟡 중급 프롬프트", "intermediate"),
        ("🔎 딥리서치 프롬프트", "deepresearch"),
        ("🎨 이미지 프롬프트", "image"),
        ("🎬 영상 (Sora) 프롬프트", "video"),
        ("――――――――", "divider"),  # 구분선 역할의 항목 추가
        ("🔧 딥리서치 프롬프트 생성기", "deep_generator"),
        ("🖌️ 이미지 프롬프트 생성기", "image_generator"),
        ("🎥 영상 (Sora) 프롬프트 생성기", "video_generator")
    ]
    
    selection = st.sidebar.radio(
        "메뉴 선택",
        options=[option[0] for option in all_options],
        label_visibility="collapsed",
        key="menu_selection_radio"
    )
    
    # 구분선 추가
    st.sidebar.markdown("---")
    
    # 제작자 정보
    st.sidebar.markdown("👤 **만든사람** : 여행가J ([프로필](https://litt.ly/jkwon))")
    st.sidebar.markdown("📧 **관련 문의** : [스타트업실험실](https://www.startuplab.seoul.kr/)")
    
    # 구분선 선택 시 홈으로 리다이렉트
    if selection == "――――――――":
        return "🏠 홈"
        
    return selection

# 훈련 데이터 로드 함수
def load_track_data(track_name):
    data_path = {
        "🟢 초급 프롬프트": "text_beginner_track.json",
        "🟡 중급 프롬프트": "text_intermediate_track.json",
        "🔎 딥리서치 프롬프트": "deep_research_track.json",
        "🎨 이미지 프롬프트": "image_prompt_track.json",
        "🎬 영상 (Sora) 프롬프트": "video_prompt_track.json"
    }
    
    try:
        file_path = DATA_DIR / data_path.get(track_name, "")
        if not file_path.exists():
            st.error(f"{track_name} 트랙 데이터를 찾을 수 없습니다.")
            return None
            
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        st.error(f"{track_name} 트랙 데이터를 찾을 수 없습니다.")
        return None
    except json.JSONDecodeError:
        st.error(f"{track_name} 트랙 데이터 형식이 올바르지 않습니다.")
        return None

# Gemini API 모델 상수 정의
GEMINI_MODELS = [
    'gemini-2.5-flash-preview-04-17',  # 최우선 시도 모델
    'gemini-2.0-flash',                # 두 번째 시도 모델
    'gemini-1.5-pro'                   # 최종 폴백 모델
]

# 할당량 초과 오류 확인 함수
def is_quota_exceeded_error(error_msg):
    error_msg = str(error_msg).lower()
    return any(keyword in error_msg for keyword in ["quota", "rate limit", "exceeded", "limit"])

# Gemini API를 사용한 프롬프트 생성 함수
def extract_prompt_and_explanation(text):
    import re
    # 1. 영어 프롬프트(코드블록, Prompt: 등) 추출
    code_blocks = re.findall(r"```[a-zA-Z]*\n(.*?)```", text, re.DOTALL)
    if code_blocks:
        prompt = code_blocks[0].strip()
    else:
        prompt = ""
        for line in text.splitlines():
            if line.strip().lower().startswith("prompt:") or "prompt:" in line.lower():
                prompt = line.split(":", 1)[-1].strip()
                break
        if not prompt:
            english_lines = [l for l in text.splitlines() if re.search(r"[a-zA-Z]", l) and len(l) > 30]
            prompt = max(english_lines, key=len) if english_lines else text.strip()
    # 2. 한글 설명(프롬프트가 아닌 부분)
    explanation = ""
    for line in text.splitlines():
        if not re.search(r"[a-zA-Z]", line) and len(line.strip()) > 10:
            explanation += line.strip() + "\n"
    return prompt, explanation.strip()

def generate_prompt(track, topic, purpose=None, sources=None, format=None):
    prompt_text = get_prompt_text(track, topic, purpose, sources, format)
    for i, model_name in enumerate(GEMINI_MODELS):
        try:
            model = genai.GenerativeModel(model_name)
            st.session_state['current_model'] = model_name
            if i > 0:
                st.toast(f"{GEMINI_MODELS[i-1]} 모델 사용량 초과로 {model_name} 모델로 전환합니다.", icon="⚠️")
            response = model.generate_content(prompt_text)
            if hasattr(response, "text") and isinstance(response.text, str):
                return extract_prompt_and_explanation(response.text)
            elif hasattr(response, "parts") and isinstance(response.parts, list) and response.parts:
                return extract_prompt_and_explanation(response.parts[0].text if hasattr(response.parts[0], "text") else str(response.parts[0]))
            elif hasattr(response, "candidates") and response.candidates:
                parts = response.candidates[0].content.parts
                return extract_prompt_and_explanation(parts[0].text if hasattr(parts[0], "text") else str(parts[0]))
            else:
                return extract_prompt_and_explanation(str(response))
        except Exception as e:
            if i < len(GEMINI_MODELS) - 1 and is_quota_exceeded_error(e):
                continue
            else:
                st.error(f"프롬프트 생성 중 오류가 발생했습니다: {str(e)}")
                return None, None
    st.error("모든 모델 시도 후 프롬프트 생성에 실패했습니다.")
    return None, None

# 프롬프트 텍스트 생성 함수 분리 (기존 로직 추출)
def get_prompt_text(track, topic, purpose=None, sources=None, format=None):
    if track == "🎨 이미지 프롬프트" or track == "🖌️ 이미지 프롬프트 생성기":
        prompt_text = f"""
        ## 역할:
        당신은 이미지 생성 AI 프롬프트 전문가입니다.
        사용자가 입력한 주제와 설정을 바탕으로 MidJourney, DALL·E 등에서 바로 사용할 수 있는 프롬프트와 설명을 구조화해서 작성하세요.

        ## 사용자 입력:
        주제: "{topic}"
        스타일: {purpose.split('스타일: ')[1].split(',')[0] if '스타일: ' in purpose else '지정되지 않음'}
        구도/앵글: {purpose.split('구도: ')[1].split(',')[0] if '구도: ' in purpose else '지정되지 않음'}
        색감: {purpose.split('색감: ')[1].split(',')[0] if '색감: ' in purpose else '지정되지 않음'}
        조명: {purpose.split('조명: ')[1].split(',')[0] if '조명: ' in purpose else '지정되지 않음'}
        분위기: {purpose.split('분위기: ')[1].split(',')[0] if '분위기: ' in purpose else '지정되지 않음'}
        추가 옵션: {purpose.split('추가 옵션: ')[1].split(',')[0] if '추가 옵션: ' in purpose else '없음'}
        추가 지시사항: {purpose.split('추가 지시사항: ')[1] if '추가 지시사항: ' in purpose else '없음'}

        ## 출력 형식:
        다음 형식으로 이미지 생성 AI를 위한 프롬프트를 작성하세요. 하나의 영어 문장으로 된 최종 프롬프트만 출력하세요:

        ```
        ## [주제] 이미지 생성 AI 프롬프트

        **주제:** [주제에 대한 상세한 설명, 핵심 요소 포함]

        **스타일/시각적 특징:** [스타일, 시각적 특징에 대한 자세한 설명]

        **카메라 설정:**
        - 앵글/샷: [구체적 설명]
        - 구도: [구체적 설명]
        - 초점: [구체적 설명]

        **분위기/조명:** [분위기와 조명 요소에 대한 자세한 설명]

        **색감/톤:** [색감과 색조에 대한 설명]

        **프롬프트 요소:** [사용된 주요 키워드와 요소들 나열, 쉼표로 구분된 형태로]

        **프롬프트 예시 1 (간결):**
        [주요 요소만 포함한 짧고 간결한 영어 프롬프트, 약 1-2문장]

        **프롬프트 예시 2 (상세):**
        [모든 요소를 체계적으로 포함한 중간 길이의 영어 프롬프트, 약 3-5문장]

        **프롬프트 예시 3 (강조):**
        [이미지의 감성과 분위기를 강조한 창의적이고 상세한 영어 프롬프트, 약 5-7문장]

        **추가 팁:**
        * [이미지 생성 시 도움이 될 만한 팁 1]
        * [이미지 생성 시 도움이 될 만한 팁 2]
        * [이미지 생성 시 도움이 될 만한 팁 3]
        ```

        ## 지침:
        1. 모든 섹션을 상세하게 작성하고, 사용자가 제공한 모든 설정 요소를 반영해야 합니다.
        2. 프롬프트 요소는 반드시 쉼표로 구분된 키워드 목록 형태로 작성하세요.
        3. 프롬프트 예시는 반드시 영어로 작성하고, 각 예시는 다른 복잡도와 길이를 가져야 합니다.
        4. 프롬프트 예시 1은 간결하게, 프롬프트 예시 2는 상세하게, 프롬프트 예시 3은 창의적이고 강조된 표현으로 작성하세요.
        5. 모든 영어 프롬프트는 MidJourney, DALL·E 등 이미지 생성 AI에 바로 입력할 수 있는 형식으로 작성합니다.
        6. 각 영어 프롬프트는 문장 형태로 작성하며, 마크다운이나 기타 포맷 없이 순수한 텍스트만 포함해야 합니다.
        7. 프롬프트 예시 1, 2, 3은 반드시 완전한 영어 문장으로 작성하고, 다른 설명이나 한글은 포함하지 마세요.
        8. 모든 프롬프트 예시는 독립적인 완전한 문장이어야 하며, "예시:", "프롬프트:", "Prompt:" 같은 접두어는 붙이지 마세요.

        출력에는 반드시 위에 지정한 출력 형식의 모든 섹션을 포함해야 하며, 각 섹션은 충분히 상세하게 작성되어야 합니다.
        """
    elif track == "🎬 영상 (Sora) 프롬프트" or track == "🎥 영상 (Sora) 프롬프트 생성기":
        prompt_text = f"""
        ## 역할:
        저는 사용자가 제공하는 프롬프트를 시네마틱한 비디오 제작에 적합한 형태로 변환하는 시스템입니다.
        사용자의 입력을 바탕으로 Sora 등의 영상 생성 AI를 위한 구조화된 프롬프트를 생성합니다.

        ## 목표:
        사용자가 제공한 주제 및 설정 요소를 바탕으로 5~20초 길이의 시네마틱 영상을 위한 
        구조화된 프롬프트를 생성합니다. 결과물은 구분된 섹션으로 나뉘어 명확하게 제시됩니다.

        ## 사용자 제공 정보:
        주제: "{topic}"
        스타일: {purpose.split('스타일: ')[1].split(',')[0] if '스타일: ' in purpose else '지정되지 않음'}
        카메라 앵글/샷: {purpose.split('카메라 앵글: ')[1].split(',')[0] if '카메라 앵글: ' in purpose else '지정되지 않음'}
        카메라 움직임: {purpose.split('카메라 움직임: ')[1].split(',')[0] if '카메라 움직임: ' in purpose else '지정되지 않음'}
        조명: {purpose.split('조명: ')[1].split(',')[0] if '조명: ' in purpose else '지정되지 않음'}
        분위기: {purpose.split('분위기: ')[1].split(',')[0] if '분위기: ' in purpose else '지정되지 않음'}
        시간: {purpose.split('시간: ')[1].split(',')[0] if '시간: ' in purpose else '지정되지 않음'}
        추가 지시사항: {purpose.split('추가 지시사항: ')[1] if '추가 지시사항: ' in purpose else '없음'}

        ## 출력 형식:
        다음 형식으로 영상 생성 AI를 위한 프롬프트를 작성하세요. 순수한 영어 문장으로 된 최종 프롬프트만 출력하세요:

        ```
        ## [주제] 영상 생성 AI 프롬프트

        **주제:** [주제에 대한 상세한 설명, 핵심 요소 포함]

        **장면 설정:** [배경, 장소, 환경에 대한 구체적인 설명]

        **스타일:** [선택된 스타일과 추가적인 스타일 요소]

        **카메라 작업:**
        - 앵글/샷: [카메라 앵글/샷 정보]
        - 움직임: [카메라 움직임 정보]
        - 장면 전환: [필요시 장면 전환 방식 설명]

        **분위기/조명:** [분위기 및 조명 정보 + 추가 설명]

        **시간:** [시간대 + 추가 설명]

        **프롬프트 요소:** [사용된 주요 키워드와 요소들 나열, 쉼표로 구분된 형태로]

        **프롬프트 예시 1 (간결):**
        [주요 요소만 포함한 짧고 간결한 영어 프롬프트, 약 1-2문장]

        **프롬프트 예시 2 (상세):**
        [모든 요소를 체계적으로 포함한 중간 길이의 영어 프롬프트, 약 3-5문장]

        **프롬프트 예시 3 (강조):**
        [영상의 감성과 분위기를 강조한 창의적이고 상세한 영어 프롬프트, 약 5-7문장]

        **추가 팁:**
        * [영상 생성 시 도움이 될 만한 팁 1]
        * [영상 생성 시 도움이 될 만한 팁 2]
        * [영상 생성 시 도움이 될 만한 팁 3]
        * [영상 생성 시 도움이 될 만한 팁 4]
        ```

        ## 지침:
        1. 모든 섹션을 상세하게 작성하고, 사용자가 제공한 모든 설정 요소를 반영해야 합니다.
        2. 프롬프트 요소는 반드시 쉼표로 구분된 키워드 목록 형태로 작성하세요.
        3. 프롬프트 예시는 반드시 영어로 작성하고, 각 예시는 다른 복잡도와 길이를 가져야 합니다.
        4. 프롬프트 예시 1은 간결하게, 프롬프트 예시 2는 상세하게, 프롬프트 예시 3은 창의적이고 강조된 표현으로 작성하세요.
        5. 모든 영어 프롬프트는 Sora, Runway 등의 영상 생성 AI에 바로 입력할 수 있는 형식으로 작성합니다.
        6. 각 영어 프롬프트는 문장 형태로 작성하며, 마크다운이나 기타 포맷 없이 순수한 텍스트만 포함해야 합니다.
        7. 프롬프트 예시 1, 2, 3은 반드시 완전한 영어 문장으로 작성하고, 다른 설명이나 한글은 포함하지 마세요.
        8. 모든 프롬프트 예시는 독립적인 완전한 문장이어야 하며, "예시:", "프롬프트:", "Prompt:" 같은 접두어는 붙이지 마세요.

        ## 영상 프롬프트 작성 시 고려할 요소:
        - 장면의 전체적인 흐름과 스토리텔링
        - 카메라 움직임과 전환의 역동성
        - 시간의 흐름과 변화 (정적인 장면이 아닌 동적인 요소 포함)
        - 등장인물이나 피사체의 동작과 표현
        - 배경 요소의 변화와 상호작용
        - 조명과 색감의 변화
        - 분위기를 강화하는 시각적, 청각적 요소 (비, 바람, 낙엽 등의 움직임)

        출력에는 반드시 위에 지정한 출력 형식의 모든 섹션을 포함해야 하며, 각 섹션은 충분히 상세하게 작성되어야 합니다.
        """
    elif track == "🔎 딥리서치 프롬프트" or track == "🔧 딥리서치 프롬프트 생성기":
        prompt_text = f"""
        사용자가 제공한 정보를 바탕으로 딥 리서치를 위한 프롬프트를 작성해주세요.

        주제: "{topic}"
        목적(목표): {purpose}
        원하는 출처: {sources}
        결과 형식: {format}
        
        지침:
        1. 사용자가 제공한 주제, 목적, 출처, 결과 형식을 90% 그대로 유지하세요.
        2. 10% 정도의 개선점(필요한 시간 범위, 중요 개념 정의, 분석 기준 등)만 추가하세요.
        3. 간결하고 명확한 한 문단으로 작성하세요.
        4. 사용자가 실제로 딥 리서치에 바로 활용할 수 있도록 실용적인 형태로 작성하세요.
        
        출력은 복사하여 바로 사용할 수 있는 단일 프롬프트 문장만 제공하세요.
        불필요한 설명이나 주석은 포함하지 마세요.
        """
    else:  # 텍스트 트랙들
        prompt_text = f"""
        "{topic}" 주제로 {purpose}을 진행하고 싶습니다. {sources}에서 관련 정보를 찾아 {format} 형식으로 정리해주세요.
        """
    
    return prompt_text

# 프롬프트 피드백 생성 함수
def generate_feedback(track, day, user_prompt):
    try:
        model = genai.GenerativeModel('gemini-1.5-pro')
        
        # 트랙별 이름 추출
        track_short_name = track.split()[1] if len(track.split()) > 1 else track
        track_icon = track.split()[0] if len(track.split()) > 0 else "🔎"
        
        prompt_text = f"""
        당신은 프롬프트 작성 훈련을 제공하는 '프롬프트 훈련 전문가'입니다.
        다음 사용자가 작성한 프롬프트에 대해 다음 4가지 기준으로 피드백을 제공해주세요:
        
        1. 명확성 (Clear): 요청이 모호하지 않고 의도가 분명한가
        2. 구체성 (Specific): 대상, 범위, 형식이 명확히 정의되었는가
        3. 창의성 (Creative): 표현이 흥미롭고 독창적인가
        4. 목표 달성 가능성 (Achievable): AI가 정확히 수행할 수 있는가
        
        트랙: {track}, Day {day}
        사용자 프롬프트: "{user_prompt}"
        
        다음 형식으로 피드백을 제공해주세요:
        
        🔍 **[피드백 - Day {day} | {track_short_name} 트랙]**  
        **프롬프트**: "{user_prompt}"  
        - 🔸 **명확성**: (피드백)  
        - 🔸 **구체성**: (피드백)  
        - 🔸 **창의성**: (피드백)  
        - 🔸 **목표 달성 가능성**: (피드백)  
        ✅ **개선 예시**:  
        > `"(개선된 프롬프트 예시)"`
        
        피드백은 항상 따뜻하고 친절한 말투를 유지하며, 격려와 함께 실질적인 개선 포인트를 제안해주세요.
        
        트랙별 추가 지침:
        - 초급 프롬프트 트랙: 기본적인 명확성과 구체성에 초점을 맞추세요.
        - 중급 프롬프트 트랙: 조건, 반복, 포맷 제어 등 고급 프롬프트 기술을 활용했는지 확인하세요.
        - 딥리서치 프롬프트 트랙: 정보 수집과 분석을 위한 복합적인 지시와 출처 활용에 주목하세요.
        """
        
        response = model.generate_content(prompt_text)
        return response.text
    
    except Exception as e:
        st.error(f"피드백 생성 중 오류가 발생했습니다: {str(e)}")
        return None

# 홈 페이지
def show_home():
    st.title(f"{APP_NAME}")
    st.markdown("""
    ### 30일 동안 프롬프트 실력을 단계별로 성장시켜 드릴게요!
    
    친절한 프롬프트 트레이너J는 다양한 AI 도구를 효과적으로 활용하기 위한 프롬프트 작성 능력을 훈련하는 플랫폼입니다.
    
    #### 📚 학습 트랙:
    - 🟢 **초급 프롬프트**: 프롬프트의 기본 구조와 작성법 이해
    - 🟡 **중급 프롬프트**: 조건, 반복, 포맷 제어 등 고급 프롬프트 능력 강화
    - 🔎 **딥리서치 프롬프트**: LLM을 활용한 심층 정보 수집 능력 향상
    - 🎨 **이미지 프롬프트**: MidJourney, DALL·E 등을 위한 시각 묘사 프롬프트
    - 🎬 **영상 (Sora) 프롬프트**: Runway, Sora, Pika 등을 위한 영상 프롬프트
    
    #### 🛠️ 프롬프트 생성기:
    - 🔧 **딥리서치 프롬프트 생성기**: 복잡한 리서치 프롬프트를 쉽게 생성
    - 🖌️ **이미지 프롬프트 생성기**: MidJourney, DALL·E용 이미지 프롬프트 생성
    - 🎥 **영상 프롬프트 생성기**: Sora, Runway 등을 위한 영상 프롬프트 생성
    """)
    
    # 설명 문구 및 시작 버튼
    st.markdown("""
    <div class="track-card">
        <h3>🚀 시작하기</h3>
        <p>왼쪽 사이드바에서 원하는 트랙이나 생성기를 선택하여 시작하세요!</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 제작자 정보
    st.markdown("---")
    st.markdown("👤 **만든사람** : 여행가J ([프로필](https://litt.ly/jkwon))")
    st.markdown("📧 **관련 문의** : [스타트업실험실](https://www.startuplab.seoul.kr/)")

# 트랙별 페이지 표시
def show_track_page(track_name):
    track_data = load_track_data(track_name)
    
    # 트랙별 헤더 설정
    track_headers = {
        "🟢 초급 프롬프트": {"title": "초급 프롬프트 트랙", "subtitle": "프롬프트의 기본 구조와 작성법 이해"},
        "🟡 중급 프롬프트": {"title": "중급 프롬프트 트랙", "subtitle": "조건, 반복, 포맷 제어 등 고급 프롬프트 능력 강화"},
        "🔎 딥리서치 프롬프트": {"title": "딥리서치 프롬프트 트랙", "subtitle": "LLM 기반 심층 정보 수집 프롬프트 작성 능력 향상"},
        "🎨 이미지 프롬프트": {"title": "이미지 프롬프트 트랙", "subtitle": "시각 묘사 중심 프롬프트 구성, 이미지 생성 도구에 맞춘 최적화 학습"},
        "🎬 영상 (Sora) 프롬프트": {"title": "영상 (Sora) 프롬프트 트랙", "subtitle": "시네마틱 영상 프롬프트 구성, 흐름/앵글/분위기 기반 텍스트 구성 능력 강화"},
        "🛠️ 딥리서치 프롬프트 생성기": {"title": "딥리서치 프롬프트 생성기", "subtitle": "다양한 목적에 맞는 프롬프트 자동 생성"}
    }
    
    header = track_headers.get(track_name, {"title": track_name, "subtitle": ""})
    st.title(header["title"])
    st.subheader(header["subtitle"])
    
    # 데이터가 없는 경우 처리
    if not track_data:
        st.warning(f"{track_name} 트랙의 데이터를 불러올 수 없습니다.")
        return
    
    # 일별 버튼 레이아웃을 사용하는 트랙들
    if track_name in ["🟢 초급 프롬프트", "🟡 중급 프롬프트", "🔎 딥리서치 프롬프트", "🎨 이미지 프롬프트", "🎬 영상 (Sora) 프롬프트"]:
        # 트랙별 아이콘 설정
        track_icons = {
            "🟢 초급 프롬프트": "🟢",
            "🟡 중급 프롬프트": "🟡",
            "🔎 딥리서치 프롬프트": "🔎",
            "🎨 이미지 프롬프트": "🎨",
            "🎬 영상 (Sora) 프롬프트": "🎬"
        }
        
        icon = track_icons.get(track_name, "📝")
        track_short_name = track_name.split()[1] if len(track_name.split()) > 1 else track_name
        
        # 상단에 30일 버튼 생성
        st.write("### 일차별 학습 내용")
        
        # 버튼을 5개씩 6줄로 배치하기 위한 레이아웃
        for row in range(6):
            cols = st.columns(5)
            for col in range(5):
                day = row * 5 + col + 1
                if day <= 30:  # 1일부터 30일까지만
                    with cols[col]:
                        if st.button(f"Day {day}", key=f"{track_name}_day_{day}"):
                            # 세션 상태에 선택한 일차 저장
                            st.session_state[f"{track_name}_selected_day"] = day

        # 기본값 설정 (처음 페이지 로드 시 Day 1 선택)
        if f'{track_name}_selected_day' not in st.session_state:
            st.session_state[f"{track_name}_selected_day"] = 1
            
        # 선택한 일차 표시
        day_idx = st.session_state[f"{track_name}_selected_day"] - 1
        
        if day_idx < len(track_data):
            day_data = track_data[day_idx]
            
            st.markdown("---")
            st.write(f"## {icon} {track_short_name} 트랙 Day {st.session_state[f'{track_name}_selected_day']} 훈련")
            
            st.markdown(f"### ✅ Day {st.session_state[f'{track_name}_selected_day']}: {day_data['title']}")
            st.markdown("#### 🎯 학습 목표:")
            st.markdown(day_data.get('objective', ''))
            
            st.markdown("#### 📘 개념 설명:")
            st.markdown(day_data.get('description', ''))
            
            st.markdown("#### ✍️ 오늘의 과제:")
            for task in day_data.get('tasks', []):
                st.markdown(f"- {task}")
                
            # 프롬프트 피드백 섹션
            st.markdown("---")
            st.markdown("### 🔄 프롬프트 실습 및 피드백")
            user_prompt = st.text_area("아래에 오늘의 과제에 맞는 프롬프트를 작성해보세요:", height=100, 
                                       key=f"{track_name}_prompt_input")
            
            if st.button("피드백 받기", key=f"{track_name}_feedback_button"):
                if user_prompt:
                    with st.spinner("피드백을 생성 중입니다..."):
                        feedback = generate_feedback(track_name, st.session_state[f"{track_name}_selected_day"], user_prompt)
                        st.session_state[f"{track_name}_feedback"] = feedback
                
                    if f'{track_name}_feedback' in st.session_state:
                        st.success("피드백이 생성되었습니다!")
                        st.markdown("### 🔍 피드백:")
                        st.markdown(st.session_state[f"{track_name}_feedback"])
                else:
                    st.error("프롬프트를 먼저 작성해주세요.")
        else:
            st.warning(f"Day {st.session_state[f'{track_name}_selected_day']}의 데이터를 찾을 수 없습니다.")
    else:
        # 탭 구조는 프롬프트 생성기만 사용
        tab1, tab2 = st.tabs(["30일 훈련 가이드", "프롬프트 생성기"])
        
        with tab1:
            for i, day in enumerate(track_data):
                with st.expander(f"Day {i+1}: {day['title']}"):
                    st.markdown(f"**학습 목표**: {day.get('objective', '')}")
                    st.markdown(f"**설명**: {day.get('description', '')}")
                    st.markdown("**과제**:")
                    for task in day.get('tasks', []):
                        st.markdown(f"- {task}")
        
        with tab2:
            # 트랙 이름에 따라 적절한 생성기 선택
            generator_mapping = {
                "🔎 딥리서치 프롬프트": "🔧 딥리서치 프롬프트 생성기",
                "🎨 이미지 프롬프트": "🖌️ 이미지 프롬프트 생성기",
                "🎬 영상 (Sora) 프롬프트": "🎥 영상 (Sora) 프롬프트 생성기"
            }
            generator_to_show = generator_mapping.get(track_name, "🔧 딥리서치 프롬프트 생성기")
            show_prompt_generator(generator_to_show)

def parse_gemini_sections(text):
    import re
    sections = {
        "title": "",
        "summary": "",
        "elements": "",
        "prompt1": "",
        "prompt2": "",
        "prompt3": "",
        "tips": ""
    }
    lines = text.splitlines()
    current = None
    buffer = []
    
    # 첫 줄부터 스캔해서 섹션 판별
    for line in lines:
        line_lower = line.lower()
        if "영상 생성 ai 프롬프트" in line_lower or "이미지 생성 ai 프롬프트" in line_lower:
            if buffer and current:
                sections[current] = "\n".join(buffer).strip()
                buffer = []
            current = "title"
            buffer.append(line)
        elif any(marker in line_lower for marker in ["프롬프트 예시 1", "예시 1", "간결", "(간결)"]) and not any(marker in line_lower for marker in ["프롬프트 예시 2", "예시 2"]):
            if buffer and current:
                sections[current] = "\n".join(buffer).strip()
                buffer = []
            current = "prompt1"
            buffer.append(line)
        elif any(marker in line_lower for marker in ["프롬프트 예시 2", "예시 2", "상세", "(상세)"]) and not any(marker in line_lower for marker in ["프롬프트 예시 3", "예시 3"]):
            if buffer and current:
                sections[current] = "\n".join(buffer).strip()
                buffer = []
            current = "prompt2"
            buffer.append(line)
        elif any(marker in line_lower for marker in ["프롬프트 예시 3", "예시 3", "강조", "(강조)"]):
            if buffer and current:
                sections[current] = "\n".join(buffer).strip()
                buffer = []
            current = "prompt3"
            buffer.append(line)
        elif any(marker in line_lower for marker in ["추가 팁", "* [이미지", "* [영상"]):
            if buffer and current:
                sections[current] = "\n".join(buffer).strip()
                buffer = []
            current = "tips"
            buffer.append(line)
        elif any(marker in line_lower for marker in ["프롬프트 요소", "요소:", "elements:"]):
            if buffer and current:
                sections[current] = "\n".join(buffer).strip()
                buffer = []
            current = "elements"
            buffer.append(line)
        elif any(marker in line_lower for marker in ["한글 요약", "주제:", "요약", "설명", "summary"]) and current != "prompt1" and current != "prompt2" and current != "prompt3":
            if buffer and current:
                sections[current] = "\n".join(buffer).strip()
                buffer = []
            current = "summary"
            buffer.append(line)
        else:
            if current:
                buffer.append(line)
            else:
                # 시작 부분에 아직 섹션을 못 찾았다면 title로 간주
                current = "title"
                buffer.append(line)
                
    # 마지막 섹션 처리
    if buffer and current:
        sections[current] = "\n".join(buffer).strip()
    
    # 프롬프트 예시 섹션에서 영어 프롬프트만 추출
    for section in ["prompt1", "prompt2", "prompt3"]:
        if sections[section]:
            lines = sections[section].splitlines()
            prompt_lines = []
            in_prompt = False
            
            for i, line in enumerate(lines):
                line_lower = line.lower().strip()
                
                # 프롬프트 시작 표시 찾기 (제목 라인은 건너뛰기)
                if any(marker in line_lower for marker in ["프롬프트 예시", "예시", "간결", "상세", "강조"]):
                    in_prompt = True
                    continue
                
                # 영어로 된 라인만 수집
                if in_prompt and line.strip() and re.search(r"[a-zA-Z]", line) and len(re.findall(r"[a-zA-Z]", line)) > 5:
                    # 라인 시작에 있는 불필요한 접두어 제거
                    cleaned_line = re.sub(r"^[*\-\s]*(?:prompt:|example:)?", "", line).strip()
                    # 코드 블록 마커 제거
                    cleaned_line = re.sub(r"^```.*$|```$", "", cleaned_line).strip()
                    
                    if cleaned_line:
                        prompt_lines.append(cleaned_line)
                    
                # 다음 섹션 시작 감지
                elif in_prompt and i > 0 and (any(marker in line_lower for marker in ["프롬프트 예시", "추가 팁"]) or line_lower.startswith("*")):
                    break
            
            if prompt_lines:
                sections[section] = "\n".join(prompt_lines)
    
    # 프롬프트 요소 섹션 추출 및 정리
    if sections["elements"]:
        lines = sections["elements"].splitlines()
        element_lines = []
        
        for line in lines:
            if "프롬프트 요소" in line or "요소:" in line:
                continue
            cleaned_line = line.strip()
            if cleaned_line:
                element_lines.append(cleaned_line)
        
        if element_lines:
            sections["elements"] = "\n".join(element_lines)
    
    # 섹션이 하나도 파싱되지 않았다면 전체 텍스트를 summary에 넣기
    if not any(value for value in sections.values() if value.strip()):
        sections["summary"] = text
        
    return sections

# 프롬프트 생성기만 표시하는 함수
def show_prompt_generator(generator_type):
    if generator_type == "🔧 딥리서치 프롬프트 생성기":
        st.title("딥리서치 프롬프트 생성기")
        st.subheader("다양한 목적에 맞는 프롬프트 자동 생성")
        
        # 주제 입력 (상단에 배치)
        topic = st.text_input("주제(목표)")
        
        # 목적 드롭다운 (하나만 선택 가능)
        purpose = st.selectbox(
            "학습목적",
            [
                "학술연구", 
                "일반 정보 수집", 
                "비교 분석", 
                "트렌드 파악", 
                "문제 해결책 찾기",
                "장단점 분석",
                "역사적 변천 과정 조사",
                "사례 연구(Case Study)",
                "수요 예측",
                "정책·제도 분석",
                "타당성 검토",
                "리스크 평가",
                "기술 분석",
                "시장 경쟁력 평가",
                "다른 분야 연관성 파악",
                "데이터 기반 의사결정",
                "사용자 경험(UX) 연구",
                "문화·사회적 인식 조사",
                "미래 예측(Foresight)",
                "윤리적·철학적 접근"
            ]
        )
        
        # 결과 형식 드롭다운 (하나만 선택 가능)
        result_format = st.selectbox(
            "결과 형식",
            [
                "시간순(연대기) 정리", 
                "핵심 요약(Executive Summary)", 
                "상세 분석 보고서", 
                "비교표(Comparative Table)", 
                "인포그래픽(Infographic)",
                "타임라인(Timeline)",
                "차트/그래프",
                "맵(Heatmap, Mind Map 등)",
                "SWOT 분석",
                "PESTEL 분석",
                "스토리텔링 형식",
                "도표/차트 중심 슬라이드(프레젠테이션)",
                "QA(Question & Answer) 또는 FAQ 형식",
                "가이드라인/체크리스트",
                "문제-해결(Action Items) 보고서",
                "케이스 스터디 형태",
                "프로세스 플로우 다이어그램",
                "요인 분석(Factor Analysis)",
                "원자료(Raw Data) 공개",
                "정성적·정량적 결합 보고"
            ]
        )
        
        # 출처 선택 (1~5개 선택)
        st.write("출처 (1~5개 선택)")
        
        # 출처 옵션들
        source_options = [
            "전문가 인터뷰", 
            "학술 논문", 
            "공식 보고서(White Paper)", 
            "정부 기관 데이터(공공 데이터)", 
            "업계 분석 리포트",
            "특허 문서",
            "전문 단체/협회 자료",
            "기업 IR 자료",
            "뉴스 기사 및 미디어 리포트",
            "컨퍼런스 발표 자료(Proceedings)",
            "소셜 미디어 분석",
            "현장 관찰 및 실험 데이터",
            "인터넷 포럼, Q&A 사이트",
            "데이터베이스(DB)",
            "기술 문서 및 매뉴얼",
            "전자책, 오디오·비디오 자료",
            "역사적 기록물 및 아카이브",
            "공개 질의응답(FAQ, Help Center)",
            "국제기구 발표자료(UN, OECD 등)",
            "서적(전문 서적·단행본)"
        ]
        
        # 세션 상태 초기화
        if "selected_sources" not in st.session_state:
            st.session_state.selected_sources = []
        
        # 버튼 그리드 배치 (3열)
        source_cols = st.columns(3)
        for i, source in enumerate(source_options):
            col_index = i % 3
            with source_cols[col_index]:
                # 이미 선택된 출처라면 활성화된 버튼으로 표시
                is_selected = source in st.session_state.selected_sources
                button_type = "primary" if is_selected else "secondary"
                
                # 버튼 클릭 처리
                if st.button(source, key=f"src_{i}", type=button_type):
                    if source in st.session_state.selected_sources:
                        # 이미 선택된 경우 제거
                        st.session_state.selected_sources.remove(source)
                    else:
                        # 선택 안된 경우 추가 (최대 5개까지)
                        if len(st.session_state.selected_sources) < 5:
                            st.session_state.selected_sources.append(source)
                        else:
                            st.warning("출처는 최대 5개까지 선택 가능합니다.")
                    
                    # 버튼 상태 업데이트를 위해 페이지 리로드
                    st.rerun()
        
        # 선택된 출처 표시
        if st.session_state.selected_sources:
            st.info(f"출처를 {len(st.session_state.selected_sources)}개 선택하셨습니다.")
        else:
            st.info("출처를 최소 1개 이상 선택해주세요.")
        
        # 프롬프트 생성 버튼
        if st.button("프롬프트 생성", key="generate_button"):
            if not topic:
                st.error("주제를 입력해주세요.")
                return
                
            if not st.session_state.selected_sources:
                st.error("출처를 최소 1개 이상 선택해주세요.")
                return
                
            with st.spinner("프롬프트를 생성 중입니다..."):
                # 선택된 출처들을 문자열로 변환
                sources_text = ", ".join(st.session_state.selected_sources)
                # 프롬프트 생성 함수 호출
                generated_prompt, _ = generate_prompt(
                    "🔧 딥리서치 프롬프트 생성기", 
                    topic, 
                    purpose, 
                    sources_text, 
                    result_format
                )
                
                if generated_prompt:
                    st.success("프롬프트가 생성되었습니다!")
                    
                    # 영상 프롬프트처럼 직접 파싱하여 섹션별로 구분해서 표시
                    lines = generated_prompt.splitlines()
                    current_section = None
                    section_content = []
                    
                    # 각 줄을 살펴보면서 섹션 파악
                    for line in lines:
                        line = line.strip()
                        if not line:
                            continue
                            
                        if "주제:" in line or "주제 :" in line:
                            if current_section:
                                # 이전 섹션 출력
                                st.markdown(f"### {current_section}")
                                st.markdown("\n".join(section_content))
                                section_content = []
                            current_section = "주제"
                        elif "스타일" in line or "시각적 특징" in line:
                            if current_section:
                                st.markdown(f"### {current_section}")
                                st.markdown("\n".join(section_content))
                                section_content = []
                            current_section = "스타일"
                        elif "카메라" in line or "앵글/샷:" in line or "구도" in line:
                            if current_section:
                                st.markdown(f"### {current_section}")
                                st.markdown("\n".join(section_content))
                                section_content = []
                            current_section = "카메라 설정"
                        elif "분위기" in line or "조명:" in line:
                            if current_section:
                                st.markdown(f"### {current_section}")
                                st.markdown("\n".join(section_content))
                                section_content = []
                            current_section = "분위기/조명"
                        elif "시간:" in line or "시간 :" in line:
                            if current_section:
                                st.markdown(f"### {current_section}")
                                st.markdown("\n".join(section_content))
                                section_content = []
                            current_section = "시간"
                        elif "프롬프트 요소" in line or "요소:" in line:
                            if current_section:
                                st.markdown(f"### {current_section}")
                                st.markdown("\n".join(section_content))
                                section_content = []
                            current_section = "프롬프트 요소"
                        elif "프롬프트 예시 1" in line or "간결" in line:
                            if current_section:
                                st.markdown(f"### {current_section}")
                                st.markdown("\n".join(section_content))
                                section_content = []
                            current_section = "프롬프트 예시 1"
                            continue
                        elif "프롬프트 예시 2" in line or "상세" in line:
                            if current_section and section_content:
                                if current_section == "프롬프트 예시 1":
                                    st.markdown(f"### {current_section}")
                                    st.code("\n".join(section_content), language="markdown")
                                else:
                                    st.markdown(f"### {current_section}")
                                    st.markdown("\n".join(section_content))
                                section_content = []
                            current_section = "프롬프트 예시 2"
                            continue
                        elif "프롬프트 예시 3" in line or "강조" in line:
                            if current_section and section_content:
                                if current_section == "프롬프트 예시 2":
                                    st.markdown(f"### {current_section}")
                                    st.code("\n".join(section_content), language="markdown")
                                else:
                                    st.markdown(f"### {current_section}")
                                    st.markdown("\n".join(section_content))
                                section_content = []
                            current_section = "프롬프트 예시 3"
                            continue
                        elif "추가 팁" in line or "추가팁" in line:
                            if current_section and section_content:
                                if current_section == "프롬프트 예시 3":
                                    st.markdown(f"### {current_section}")
                                    st.code("\n".join(section_content), language="markdown")
                                else:
                                    st.markdown(f"### {current_section}")
                                    st.markdown("\n".join(section_content))
                                section_content = []
                            current_section = "추가 팁"
                            continue
                        
                        # 현재 줄을 현재 섹션에 추가
                        section_content.append(line)
                    
                    # 마지막 섹션 출력
                    if current_section and section_content:
                        if current_section in ["프롬프트 예시 1", "프롬프트 예시 2", "프롬프트 예시 3"]:
                            st.markdown(f"### {current_section}")
                            st.code("\n".join(section_content), language="markdown")
                        else:
                            st.markdown(f"### {current_section}")
                            st.markdown("\n".join(section_content))
                    
                    # 어떤 섹션도 파싱되지 않았을 경우
                    if not current_section:
                        # 영어 프롬프트만 추출해서 코드 블록으로 표시
                        english_prompts = extract_english_prompts(generated_prompt)
                        if english_prompts:
                            st.markdown("### 프롬프트 예시 1")
                            st.code(english_prompts[0], language="markdown")
                            if len(english_prompts) > 1:
                                st.markdown("### 프롬프트 예시 2")
                                st.code(english_prompts[1], language="markdown")
                            if len(english_prompts) > 2:
                                st.markdown("### 프롬프트 예시 3")
                                st.code(english_prompts[2], language="markdown")
                        else:
                            st.markdown("### 생성된 프롬프트")
                            st.code(generated_prompt, language="markdown")
                else:
                    st.error("프롬프트 생성에 실패했습니다.")
    
    elif generator_type == "🖌️ 이미지 프롬프트 생성기":
        st.title("이미지 프롬프트 생성기")
        st.subheader("이미지 생성 AI를 위한 프롬프트 생성")
        
        # 주제 입력
        topic = st.text_input("주제/대상", placeholder="예: 미래도시, 판타지 풍경, 고양이 초상화 등")
        
        # 스타일 선택
        style_options = [
            "사실적(Realistic)", 
            "초현실적(Surreal)", 
            "판타지(Fantasy)", 
            "미니멀리즘(Minimalist)", 
            "추상적(Abstract)",
            "레트로(Retro)",
            "아트 데코(Art Deco)",
            "픽셀 아트(Pixel Art)",
            "수채화(Watercolor)",
            "유화(Oil Painting)",
            "인상주의(Impressionism)",
            "팝 아트(Pop Art)",
            "사이버펑크(Cyberpunk)",
            "고딕(Gothic)",
            "카툰(Cartoon)",
            "지브리 스타일(Ghibli Style)",
            "디지털 아트(Digital Art)",
            "3D 렌더링(3D Rendering)",
            "벡터 아트(Vector Art)",
            "포토리얼리스틱(Photorealistic)"
        ]
        
        style = st.selectbox("스타일", style_options)
        
        # 레이아웃 - 2개의 컬럼으로 분할
        col1, col2 = st.columns(2)
        
        with col1:
            # 구도/앵글 드롭다운
            angle_options = [
                "정면 샷(Front View)",
                "측면 샷(Side View)",
                "조감도(Bird's Eye View)",
                "로우 앵글(Low Angle)",
                "클로즈업(Close-up)",
                "와이드 샷(Wide Shot)",
                "전신 샷(Full Body Shot)",
                "파노라마(Panorama)",
                "매크로(Macro)",
                "초점 스태킹(Focus Stacking)",
                "오버헤드 샷(Overhead Shot)",
                "틸트 시프트(Tilt-Shift)",
                "반신 샷(Medium Shot)",
                "대각선 구도(Diagonal Composition)",
                "대칭 구도(Symmetrical Composition)",
                "프레임 속 프레임(Frame within Frame)",
                "삼등분 구도(Rule of Thirds)",
                "황금비율(Golden Ratio)",
                "사선 구도(Dutch Angle)",
                "실루엣(Silhouette View)"
            ]
            angle = st.selectbox("구도/앵글", angle_options)
            
            # 색감/색조 드롭다운
            color_options = [
                "비비드(Vivid Colors)",
                "파스텔(Pastel Colors)",
                "모노크롬(Monochrome)",
                "세피아(Sepia)",
                "네온(Neon Colors)",
                "흑백(Black & White)",
                "컬러풀(Colorful)",
                "어두운(Dark Tones)",
                "밝은(Light Tones)",
                "대비가 강한(High Contrast)",
                "따뜻한 색조(Warm Tones)",
                "차가운 색조(Cool Tones)",
                "청록색 톤(Teal & Orange)",
                "빈티지(Vintage Colors)",
                "크리미 색상(Creamy Tones)",
                "금속성(Metallic)",
                "그라디언트(Gradient Colors)",
                "아쿠아(Aqua Tones)",
                "모노크로매틱(Monochromatic)",
                "이중톤(Duotone)"
            ]
            color = st.selectbox("색감/색조", color_options)
        
        with col2:
            # 조명 드롭다운
            light_options = [
                "자연광(Natural Light)",
                "드라마틱 조명(Dramatic Lighting)",
                "백라이트(Backlight)",
                "리믹스 조명(Rembrandt Lighting)",
                "저조도(Low Light)",
                "네온 조명(Neon Lighting)",
                "스플릿 조명(Split Lighting)",
                "소프트 박스(Soft Box Lighting)",
                "황금빛 시간(Golden Hour)",
                "파란 시간(Blue Hour)",
                "촛불 조명(Candlelight)",
                "하드 라이트(Hard Light)",
                "환형 플래시(Ring Light)",
                "실루엣 조명(Silhouette Lighting)",
                "키 라이트(Key Light)",
                "스포트라이트(Spotlight)",
                "앰비언트 라이트(Ambient Light)",
                "컬러 젤 라이트(Color Gel Lighting)",
                "체커보드 라이트(Checkerboard Light)",
                "반사광(Reflected Light)"
            ]
            light = st.selectbox("조명", light_options)
            
            # 분위기 드롭다운
            mood_options = [
                "평화로운(Peaceful)",
                "신비로운(Mysterious)",
                "불길한(Ominous)",
                "활기찬(Energetic)",
                "멜랑콜리(Melancholic)",
                "행복한(Happy)",
                "고요한(Serene)",
                "혼란스러운(Chaotic)",
                "감성적인(Emotional)",
                "놀라운(Surprising)",
                "우아한(Elegant)",
                "판타지적(Fantastical)",
                "초현실적인(Surreal)",
                "긴장감 있는(Suspenseful)",
                "미니멀리즘(Minimalistic)",
                "청량한(Refreshing)",
                "향수를 불러일으키는(Nostalgic)",
                "동화적인(Fairytale-like)",
                "고독한(Solitary)",
                "활력 넘치는(Vibrant)"
            ]
            mood = st.selectbox("분위기", mood_options)
        
        # 추가 옵션 (체크박스 형태)
        st.write("### 추가 옵션")
        additional_options = st.columns(2)
        
        with additional_options[0]:
            high_quality = st.checkbox("고품질 렌더링(High Quality)", value=True)
            detailed = st.checkbox("세부 묘사(Detailed)", value=True)
            
        with additional_options[1]:
            high_resolution = st.checkbox("고해상도(High Resolution)", value=True)
            film_grain = st.checkbox("필름 그레인(Film Grain)")
        
        # 추가 지시사항
        additional_instructions = st.text_area("추가 지시사항 (선택)", 
                                            placeholder="예: 특정 요소 강조, 특별한 효과, 특정 영감 등",
                                            height=100)
        
        # 프롬프트 생성 버튼
        if st.button("이미지 프롬프트 생성", key="generate_image_prompt"):
            if not topic:
                st.error("주제/대상을 입력해주세요.")
                return
                
            with st.spinner("이미지 프롬프트를 생성 중입니다..."):
                # 추가 옵션 처리
                additional_params = []
                if high_quality:
                    additional_params.append("high quality")
                if detailed:
                    additional_params.append("detailed")
                if high_resolution:
                    additional_params.append("high resolution")
                if film_grain:
                    additional_params.append("film grain")
                
                # 추가 옵션을 문자열로 변환
                additional_options_text = ", ".join(additional_params)
                
                # 프롬프트 생성 함수 호출
                generated_prompt, _ = generate_prompt(
                    "🖌️ 이미지 프롬프트 생성기", 
                    topic, 
                    f"스타일: {style}, 구도: {angle}, 색감: {color}, 조명: {light}, 분위기: {mood}, 추가 옵션: {additional_options_text}, 추가 지시사항: {additional_instructions}"
                )
                
                if generated_prompt:
                    st.success("이미지 프롬프트가 생성되었습니다!")
                    sections = parse_gemini_sections(generated_prompt)
                    if sections["title"]:
                        st.markdown(f"### {sections['title']}")
                    if sections["summary"]:
                        st.markdown(sections["summary"])
                    if sections["elements"]:
                        st.markdown("#### 프롬프트 요소")
                        st.markdown(sections["elements"])
                    if sections["prompt1"]:
                        st.markdown("#### 프롬프트 예시 1 (간결)")
                        st.code(sections["prompt1"], language="markdown")
                    if sections["prompt2"]:
                        st.markdown("#### 프롬프트 예시 2 (상세)")
                        st.code(sections["prompt2"], language="markdown")
                    if sections["prompt3"]:
                        st.markdown("#### 프롬프트 예시 3 (강조)")
                        st.code(sections["prompt3"], language="markdown")
                    if sections["tips"]:
                        st.markdown("#### 추가 팁")
                        st.markdown(sections["tips"])
                else:
                    st.error("프롬프트 생성에 실패했습니다.")
    
    elif generator_type == "🎥 영상 (Sora) 프롬프트 생성기":
        st.title("영상 (Sora) 프롬프트 생성기")
        st.subheader("Runway, Sora, Pika 등의 영상 생성 AI를 위한 프롬프트 생성")
        
        # 주제/장면 입력
        topic = st.text_input("주제/장면", placeholder="예: 해변에서 일몰, 도시 거리 산책, 우주 탐험 등")
        
        # 스타일 선택
        style_options = [
            "사실적(Realistic)", 
            "시네마틱(Cinematic)", 
            "다큐멘터리(Documentary)",
            "판타지(Fantasy)", 
            "SF(Sci-Fi)",
            "애니메이션(Animation)",
            "실험적(Experimental)",
            "뮤직비디오(Music Video)",
            "드론 촬영(Drone Shot)",
            "핸드헬드(Handheld)",
            "슬로우 모션(Slow Motion)",
            "타임랩스(Time Lapse)",
            "스톱모션(Stop Motion)",
            "블랙코미디(Black Comedy)",
            "드라마(Drama)",
            "공포(Horror)",
            "레트로(Retro)",
            "미니멀리즘(Minimalism)",
            "자연 다큐멘터리(Nature Documentary)",
            "CCTV 스타일(Surveillance)"
        ]
        
        style = st.selectbox("스타일", style_options)
        
        # 레이아웃 - 2개의 컬럼으로 분할
        col1, col2 = st.columns(2)
        
        with col1:
            # 카메라 앵글/샷 드롭다운
            shot_options = [
                "와이드 샷(Wide Shot)",
                "미디엄 샷(Medium Shot)",
                "클로즈업(Close-up)",
                "익스트림 클로즈업(Extreme Close-up)",
                "로우 앵글(Low Angle)",
                "하이 앵글(High Angle)",
                "버드아이 뷰(Bird's Eye View)",
                "포인트 오브 뷰(POV)",
                "트래킹 샷(Tracking Shot)",
                "달리 샷(Dolly Shot)",
                "스테디캠(Steadicam)",
                "틸트(Tilt)",
                "서스펜스 샷(Suspense Shot)",
                "오버더숄더(Over-the-shoulder)"
            ]
            shot = st.selectbox("카메라 앵글/샷", shot_options)
            
            # 카메라 움직임 드롭다운
            movement_options = [
                "고정(Static)",
                "패닝(Panning)",
                "틸팅(Tilting)",
                "줌인/줌아웃(Zoom In/Out)",
                "달리(Dolly In/Out)",
                "트래킹(Tracking)",
                "스테디캠 무빙(Steadicam)",
                "드론 비행(Drone Flying)",
                "점프 컷(Jump Cut)",
                "카메라 스웨이(Camera Sway)",
                "360도 회전(360 Rotation)",
                "크레인 샷(Crane Shot)",
                "지미집(Gimbal Movement)",
                "핸드헬드 셰이킹(Handheld Shaky)",
                "슬로우 푸시인(Slow Push In)"
            ]
            movement = st.selectbox("카메라 움직임", movement_options)
        
        with col2:
            # 조명 드롭다운
            light_options = [
                "자연광(Natural Light)",
                "골든 아워(Golden Hour)",
                "블루 아워(Blue Hour)",
                "로우 키(Low Key)",
                "하이 키(High Key)",
                "실루엣(Silhouette)",
                "백라이트(Backlight)",
                "스포트라이트(Spotlight)",
                "제품 조명(Product Lighting)",
                "레인보우(Rainbow Lighting)",
                "네온 사인(Neon Lighting)",
                "캠프파이어(Campfire)",
                "플래시(Flash)",
                "스트로브(Strobe)",
                "그림자 장난(Shadow Play)"
            ]
            light = st.selectbox("조명", light_options)
            
            # 분위기 드롭다운
            mood_options = [
                "밝고 활기찬(Bright & Vibrant)",
                "어둡고 분위기있는(Dark & Moody)",
                "신비로운(Mysterious)",
                "행복한(Happy)",
                "공포스러운(Scary)",
                "긴장감 넘치는(Suspenseful)",
                "서정적인(Lyrical)",
                "에너제틱(Energetic)",
                "고요한(Serene)",
                "몽환적인(Dreamy)",
                "우울한(Melancholic)",
                "초현실적인(Surreal)",
                "향수를 불러일으키는(Nostalgic)",
                "희망찬(Hopeful)",
                "차가운(Cold)"
            ]
            mood = st.selectbox("분위기", mood_options)
        
        # 시간 설정
        time_options = [
            "낮(Day)",
            "밤(Night)",
            "해 뜰 때(Sunrise)",
            "해 질 때(Sunset)",
            "황혼(Dusk)",
            "새벽(Dawn)",
            "골든 아워(Golden Hour)",
            "블루 아워(Blue Hour)",
            "미드나잇(Midnight)",
            "스톱 모션(Time Freeze)",
            "타임랩스(Time Lapse)",
            "슬로우 모션(Slow Motion)",
            "리버스(Reverse)",
            "현재(Present)",
            "과거(Past)",
            "미래(Future)"
        ]
        time_setting = st.selectbox("시간", time_options)
        
        # 추가 지시사항
        additional_instructions = st.text_area("추가 지시사항 (선택)", 
                                            placeholder="예: 특정 장면 전환, 특수 효과, 이야기 진행 방식 등",
                                            height=100)
        
        # 프롬프트 생성 버튼
        if st.button("영상 프롬프트 생성", key="generate_video_prompt"):
            if not topic:
                st.error("주제/장면을 입력해주세요.")
                return
                
            with st.spinner("영상 프롬프트를 생성 중입니다..."):
                # 프롬프트 생성 함수 호출
                generated_prompt, _ = generate_prompt(
                    "🎥 영상 (Sora) 프롬프트 생성기", 
                    topic, 
                    f"스타일: {style}, 카메라 앵글: {shot}, 카메라 움직임: {movement}, 조명: {light}, 분위기: {mood}, 시간: {time_setting}, 추가 지시사항: {additional_instructions}"
                )
                
                if generated_prompt:
                    st.success("영상 프롬프트가 생성되었습니다!")
                    sections = parse_gemini_sections(generated_prompt)
                    if sections["title"]:
                        st.markdown(f"### {sections['title']}")
                    if sections["summary"]:
                        st.markdown(sections["summary"])
                    if sections["elements"]:
                        st.markdown("#### 프롬프트 요소")
                        st.markdown(sections["elements"])
                    if sections["prompt1"]:
                        st.markdown("#### 프롬프트 예시 1 (간결)")
                        st.code(sections["prompt1"], language="markdown")
                    if sections["prompt2"]:
                        st.markdown("#### 프롬프트 예시 2 (상세)")
                        st.code(sections["prompt2"], language="markdown")
                    if sections["prompt3"]:
                        st.markdown("#### 프롬프트 예시 3 (강조)")
                        st.code(sections["prompt3"], language="markdown")
                    if sections["tips"]:
                        st.markdown("#### 추가 팁")
                        st.markdown(sections["tips"])
                else:
                    st.error("프롬프트 생성에 실패했습니다.")

def extract_english_prompts(text):
    """영어 문장 위주로 프롬프트 예시 추출"""
    import re
    prompts = []
    
    # 1. 코드 블록 추출
    code_blocks = re.findall(r"```[a-zA-Z]*\n(.*?)```", text, re.DOTALL)
    if code_blocks:
        for block in code_blocks:
            prompts.append(block.strip())
            
    # 2. 코드 블록이 없으면 영어 문장 중 긴 것만 추출
    if not prompts:
        lines = text.splitlines()
        for line in lines:
            # 영어 문자가 대부분인 줄에서 30자 이상인 것만 선택
            if re.search(r"[a-zA-Z]", line) and len(line) > 30 and sum(c.isalpha() for c in line) / len(line) > 0.5:
                prompts.append(line.strip())
    
    return prompts

# 메인 함수
def main():
    # API 키 설정
    setup_api()
    
    # CSS 로드
    load_css()
    
    # 사이드바 설정
    selected_option = setup_sidebar()
    
    # 선택된 옵션에 따라 페이지 표시
    if selected_option == "🏠 홈" or selected_option == "――――――――":
        show_home()
    elif selected_option in ["🔧 딥리서치 프롬프트 생성기", "🖌️ 이미지 프롬프트 생성기", "🎥 영상 (Sora) 프롬프트 생성기"]:
        show_prompt_generator(selected_option)
    else:
        show_track_page(selected_option)

if __name__ == "__main__":
    main() 
import streamlit as st
import google.generativeai as genai
from PIL import Image

# 1. 페이지 설정 및 세이지 그린 테마 CSS 적용
st.set_page_config(
    page_title="스마트 OTC 맞춤 처방 & DUR 약물 융합 시스템",
    page_icon="🌿",
    layout="wide"
)

# 세이지 그린(Sage Green) 테마 & 포스터 디자인 커스텀 CSS
st.markdown("""
<style>
    .stApp {
        background-color: #F2F6F3;
    }
    [data-testid="stSidebar"] {
        background-color: #E3EBE5;
    }
    h1, h2, h3 {
        color: #1E4D2B !important;
        font-family: 'Pretendard', sans-serif;
    }
    .stButton>button {
        background-color: #2D6A4F !important;
        color: white !important;
        border-radius: 8px !important;
        font-weight: bold !important;
        font-size: 16px !important;
        padding: 10px 24px !important;
        border: none !important;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .stButton>button:hover {
        background-color: #1B4332 !important;
    }
    /* 포스터 카드 스타일 */
    .poster-card {
        background-color: #FFFFFF;
        padding: 30px;
        border-radius: 16px;
        border: 2px solid #C8D6CB;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        margin-bottom: 25px;
    }
    .badge-info {
        background-color: #2D6A4F;
        color: white;
        padding: 6px 14px;
        border-radius: 20px;
        font-weight: bold;
        font-size: 14px;
        display: inline-block;
        margin-bottom: 10px;
    }
    .feature-card {
        background-color: #FFFFFF;
        padding: 18px;
        border-radius: 12px;
        border-left: 5px solid #52B788;
        box-shadow: 0 2px 6px rgba(0,0,0,0.04);
        height: 100%;
    }
    .drug-card {
        background-color: #FFFFFF;
        padding: 20px;
        border-radius: 12px;
        border-left: 6px solid #40916C;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
        margin-bottom: 15px;
    }
    .badge-main { background-color: #E8F5E9; color: #1B5E20; padding: 4px 10px; border-radius: 15px; font-weight: bold; font-size: 13px; }
    .badge-synergy { background-color: #E3F2FD; color: #0D47A1; padding: 4px 10px; border-radius: 15px; font-weight: bold; font-size: 13px; }
    .badge-stomach { background-color: #FFF3E0; color: #E65100; padding: 4px 10px; border-radius: 15px; font-weight: bold; font-size: 13px; }
    .badge-warning { background-color: #FFEBEE; color: #C62828; padding: 4px 10px; border-radius: 15px; font-weight: bold; font-size: 13px; }
</style>
""", unsafe_allow_html=True)

# 2. 세션 상태 관리 (메뉴 이동용)
if 'menu' not in st.session_state:
    st.session_state.menu = "🏠 프로젝트 소개"

# 3. 사이드바 설정 및 네비게이션 메뉴
st.sidebar.header("⚙️ 시스템 설정 & 메뉴")
api_key = st.sidebar.text_input("Gemini API Key (선택)", type="password", help="API 키 입력 시 AI 처방전 OCR 및 맞춤 정밀 리포트가 활성화됩니다.")

try:
    if api_key:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        has_api = True
    else:
        has_api = False
except Exception:
    has_api = False

st.sidebar.markdown("---")
st.sidebar.subheader("📌 메뉴 이동")

menu_choice = st.sidebar.radio(
    "원하는 기능을 선택하세요",
    [
        "🏠 프로젝트 소개",
        "💊 맞춤 약물 조합 & DUR 진단",
        "🔍 시판 약품 성분 변환기",
        "📷 처방전/약봉지 AI 스캐너"
    ],
    index=["🏠 프로젝트 소개", "💊 맞춤 약물 조합 & DUR 진단", "🔍 시판 약품 성분 변환기", "📷 처방전/약봉지 AI 스캐너"].index(st.session_state.menu)
)
st.session_state.menu = menu_choice

# ==============================================================================
# MENU 1: 🏠 프로젝트 소개 (첫 화면 - 포스터 스타일)
# ==============================================================================
if st.session_state.menu == "🏠 프로젝트 소개":
    st.markdown("""
    <div class="poster-card">
        <span class="badge-info">🎓 실생활 문제 해결 프로젝트 보고서 연계 애플리케이션</span>
        <h1>🌿 스마트 맞춤형 OTC 약물 조합 & DUR 케어 가이드</h1>
        <p style="font-size:18px; color:#2D6A4F; font-weight:600; margin-top:-10px;">
            의생명과학 약리 기전과 간호학적 복약 지도를 결합한 정밀 헬스케어 시스템
        </p>
        <hr style="border: 0.5px solid #C8D6CB;">
        <p style="font-size:15px; color:#4A5D4E;">
            <b>개발자</b>: 2학년 9반 1번 강은유 (학번: 20901)<br>
            <b>개발 환경</b>: Python, Streamlit, Google Gemini AI (1.5 Flash)<br>
            <b>주요 목표</b>: 일반의약품(OTC) 오남용 예방, 약물 상호작용(DUR) 스크리닝, 부작용 방지 및 맞춤형 간호 케어 제공
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.subheader("💡 주요 시스템 기능 안내")
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        st.markdown("""
        <div class="feature-card">
            <h4>💊 1. 증상별 융합 약물 & 위장 보호 매칭</h4>
            <p>콧물, 인후통, 근육통 등 다중 증상 분석 후 <b>[메인 치료제 + 시너지제 + 위장 보호제]</b> 3중 최적 조합을 자동 산출합니다.</p>
        </div>
        """, unsafe_allow_html=True)
        st.write("")
        st.markdown("""
        <div class="feature-card">
            <h4>🔍 2. 시판 약품명 ↔ 성분명 자동 변환</h4>
            <p>타이레놀, 탁센, 판콜 등 일반인에게 친숙한 상품명을 입력하면 유효 약학 성분명으로 자동 변환해 드립니다.</p>
        </div>
        """, unsafe_allow_html=True)

    with col_f2:
        st.markdown("""
        <div class="feature-card">
            <h4>☕ 3. 약물 - 음식(음료) 상호작용 분석</h4>
            <p>커피(카페인), 우유, 자몽즙 등 함께 마신 음료와 약물 간의 대사 이상 및 위험도를 사전에 검증합니다.</p>
        </div>
        """, unsafe_allow_html=True)
        st.write("")
        st.markdown("""
        <div class="feature-card">
            <h4>📷 4. 처방전 / 약봉지 AI 사진 OCR</h4>
            <p>약봉지나 처방전 사진을 업로드하면 Gemini Vision AI가 텍스트를 자동 인식하여 약물 정보와 복약 팁을 추출합니다.</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
    with col_btn2:
        if st.button("🚀 스마트 약물 진단 프로그램 시작하기", use_container_width=True):
            st.session_state.menu = "💊 맞춤 약물 조합 & DUR 진단"
            st.rerun()

# ==============================================================================
# MENU 2: 💊 맞춤 약물 조합 & DUR 진단 (메인 진단 앱)
# ==============================================================================
elif st.session_state.menu == "💊 맞춤 약물 조합 & DUR 진단":
    st.title("🌿 스마트 맞춤형 OTC 약물 조합 & DUR 케어 가이드")
    st.caption("의생명과학 약리 기전 및 간호학적 복약 지도를 결합한 정밀 헬스케어 시스템")
    st.markdown("---")

    st.subheader("📋 1. 환자 증상 및 기저 상태 종합 평가")

    col_symptom, col_condition = st.columns([1.2, 1])

    with col_symptom:
        symptoms = st.multiselect(
            "현재 겪고 있는 주요 증상을 모두 선택하세요 (다중 선택 가능)",
            [
                "콧물 / 코막힘 / 재채기",
                "근육통 / 담 결림 / 관절통",
                "인후통 (목 통증 및 부종)",
                "발열 및 오한 / 몸살",
                "기침 / 가래",
                "속쓰림 / 소화불량 / 위통"
            ]
        )

    with col_condition:
        st.write("**기저 질환 및 신체 상태 체크**")
        has_stomach_ache = st.checkbox("평소 위염 / 위장 장애 / 속쓰림이 자주 있음")
        has_liver_disease = st.checkbox("간 기능 저하 / 간 질환 이력")
        is_drowsy_sensitive = st.checkbox("운전나 공부로 인해 졸음 부작용 절대 불가")

    col_supp, col_food = st.columns(2)
    with col_supp:
        supplements = st.text_input("현재 복용 중인 약물 / 영양제 (예: 타이레놀, 탁센, 아스피린, 비타민C)", "")

    with col_food:
        foods = st.multiselect(
            "함께 섭취한 음료 / 음식 (약물-음식 상호작용 검사)",
            ["커피 / 고카페인 음료", "우유 / 유제품 / 제산음료", "자몽즙 / 자몽 에이드", "녹차 / 홍차 (탄닌 성분)", "알코올 / 술"]
        )

    if st.button("🔍 증상별 융합 약물 조합 & DUR 안전성 분석 실행", use_container_width=True):
        if not symptoms:
            st.error("⚠️ 최소 하나 이상의 증상을 선택해 주세요.")
        else:
            st.markdown("---")
            st.subheader("💊 2. 맞춤 융합 약물 처방 매칭 및 DUR 결과")

            main_drugs = []
            synergy_drugs = []
            stomach_protectors = []
            dur_cautions = []
            matching_reasons = []

            # 증상별 약물 매칭 알고리즘
            if "콧물 / 코막힘 / 재채기" in symptoms:
                if is_drowsy_sensitive:
                    main_drugs.append("2세대 항히스타민제 (세티리진 / 팩소페나딘)")
                    matching_reasons.append("• [콧물] 졸음 부작용이 적은 2세대 항히스타민제로 콧물·재채기 제어")
                else:
                    main_drugs.append("1세대 항히스타민제 (클로르페니라민)")
                    matching_reasons.append("• [콧물] 항콜린 작용이 강력하여 콧물에 즉각 효과적")

                synergy_drugs.append("비충혈제거제 (슈도에페드린)")
                matching_reasons.append("• [시너지 매칭] 항히스타민제 + 슈도에페드린 조합으로 코막힘 혈관 수축 해소")
                dur_cautions.append("코막힘 약(슈도에페드린)은 심장 두근거림이나 불면을 유발할 수 있어 야간 복용 주의가 필요합니다.")

            if "근육통 / 담 결림 / 관절통" in symptoms:
                main_drugs.append("근이완제 (클로르조키사존)")
                synergy_drugs.append("NSAIDs 소염진통제 (덱시부프로펜 / 이부프로펜)")
                matching_reasons.append("• [근육통 융합] 뭉친 근육을 풀어주는 근이완제 + 염증 통증을 줄이는 소염진통제 동시 조합")

                if not has_stomach_ache:
                    stomach_protectors.append("위장관운동조절제 / 제산제 (트리메부틴 또는 알마게이트)")
                    matching_reasons.append("• [위장 보호] 소염진통제와 근이완제 병용 시 위막 자극 완화를 위한 위장약 동시 조합")

                dur_cautions.append("근이완제 복용 시 졸음이나 나른함이 생길 수 있으므로 운전 및 정밀 작업 금지")

            if "인후통 (목 통증 및 부종)" in symptoms:
                if has_stomach_ache:
                    main_drugs.append("아세트아미노펜 (해열진통제)")
                    synergy_drugs.append("생약 소염제 (은교산)")
                    matching_reasons.append("• [인후통 위장보호] 위 자극이 있는 NSAIDs 대신 아세트아미노펜 + 은교산 생약 소염제 조합")
                else:
                    main_drugs.append("NSAIDs 소염진통제 (이부프로펜)")
                    synergy_drugs.append("소염효소제 (트라넥삼산 또는 소염효소제)")
                    matching_reasons.append("• [인후통 시너지] 소염진통제 + 부종 완화 소염효소제로 목 염증·발열 완화")

            if "발열 및 오한 / 몸살" in symptoms:
                if has_liver_disease:
                    main_drugs.append("이부프로펜 계열")
                    dur_cautions.append("간 기능 저하 소견으로 간 대사 부담이 있는 아세트아미노펜 대신 이부프로펜 우선 권장")
                else:
                    main_drugs.append("아세트아미노펜 (타이레놀 계열)")
                    matching_reasons.append("• [발열/몸살] 중추신경계 해열 및 전신 몸살 완화")

            if "기침 / 가래" in symptoms:
                main_drugs.append("진해거담제 (앙브록솔 + 덱스트로메토르판 복합제)")
                matching_reasons.append("• [기침/가래] 기침 반사 억제제 + 가래 배출 진해거담제 융합 복합제")

            if "속쓰림 / 소화불량 / 위통" in symptoms or has_stomach_ache:
                stomach_protectors.append("H2 블로커 (파모티딘) 또는 제산제 (알마겔)")
                matching_reasons.append("• [위장 케어] 위산 분비를 억제하여 약물 복용 시 위막 손상 차단")

            # 음식-약물 상호작용 (Food-Drug Interaction) 검사
            if "커피 / 고카페인 음료" in foods:
                dur_cautions.append("☕ [음식 상호작용] 커피의 카페인이 소염진통제(NSAIDs)와 반응하여 위산 분비를 크게 촉진하므로 위통 및 속쓰림 위험이 커집니다.")
            if "우유 / 유제품 / 제산음료" in foods:
                dur_cautions.append("🥛 [음식 상호작용] 우유의 칼슘이 약물 성분과 결합하여 체내 흡수를 방해하므로 물과 함께 복용하세요.")
            if "자몽즙 / 자몽 에이드" in foods:
                dur_cautions.append("🍊 [음식 상호작용] 자몽 성분이 간 대사 효소(CYP3A4)를 억제하여 항히스타민제/혈압약 등의 혈중 농도를 유해 수준으로 높일 수 있습니다.")
            if "알코올 / 술" in foods:
                dur_cautions.append("🍺 [긴급 위험] 약물 복용 중 음주는 아세트아미노펜 복용 시 급성 간 손상, NSAIDs 복용 시 위장관 출혈을 유발합니다.")

            # 결과 시각화
            col_res1, col_res2 = st.columns(2)

            with col_res1:
                st.markdown("""
                <div class="drug-card">
                    <h3>💊 추천 약물 성분 융합 조합</h3>
                """, unsafe_allow_html=True)
                
                if main_drugs:
                    st.markdown("<span class='badge-main'>주 치료제</span> " + ", ".join(set(main_drugs)), unsafe_allow_html=True)
                if synergy_drugs:
                    st.markdown("<br><span class='badge-synergy'>시너지 연합제</span> " + ", ".join(set(synergy_drugs)), unsafe_allow_html=True)
                if stomach_protectors:
                    st.markdown("<br><span class='badge-stomach'>위장 보호제</span> " + ", ".join(set(stomach_protectors)), unsafe_allow_html=True)
                
                st.markdown("</div>", unsafe_allow_html=True)

                st.markdown("#### 🧪 약물 조합 및 매칭 근거")
                for reason in matching_reasons:
                    st.write(reason)

            with col_res2:
                st.markdown("""
                <div class="drug-card">
                    <h3>🩺 간호 케어 & DUR 안전 가이드</h3>
                """, unsafe_allow_html=True)

                if dur_cautions:
                    for caution in set(dur_cautions):
                        st.markdown(f"<span class='badge-warning'>위험 경고</span> {caution}", unsafe_allow_html=True)
                        st.write("")
                else:
                    st.success("✅ 특이 약물 상호작용 위험이 탐지되지 않았습니다.")

                st.markdown("---")
                st.write("**🩺 필수 간호 복약 수칙**")
                st.write("1. **식후 30분 미온수 복용**: 위막 자극을 줄이고 약물 흡수를 돕기 위해 따뜻한 물 1컵과 복용하세요.")
                st.write("2. **수분 섭취**: 진해거담제나 항히스타민제 복용 시 점막 건조를 예방하기 위해 하루 1.5L 이상 물을 마시세요.")

                st.markdown("</div>", unsafe_allow_html=True)

            if has_api:
                st.markdown("---")
                st.subheader("🤖 Gemini AI 맞춤형 헬스케어 피드백")
                prompt = f"""
                환자 증상: {', '.join(symptoms)}, 복용 음료: {', '.join(foods)}
                추천 약물: 주치료제({', '.join(main_drugs)}), 시너지제({', '.join(synergy_drugs)}), 위장약({', '.join(stomach_protectors)})
                임상 간호사 관점에서 약물 이점과 복약 팁을 3문장으로 친절히 안내해줘.
                """
                with st.spinner("AI가 분석 리포트를 생성 중입니다..."):
                    try:
                        response = model.generate_content(prompt)
                        st.info(response.text)
                    except Exception as e:
                        st.error(f"AI 호출 오류: {e}")

# ==============================================================================
# MENU 3: 🔍 시판 약품 성분 변환기
# ==============================================================================
elif st.session_state.menu == "🔍 시판 약품 성분 변환기":
    st.title("🔍 시판 약품명 ↔ 유효 성분명 자동 변환기")
    st.caption("약국이나 편의점에서 구입한 상품명을 입력하면 유효 약학 성분과 효능을 분석해 드립니다.")
    st.markdown("---")

    # 성분 사전 DB
    drug_db = {
        "타이레놀": {"성분": "아세트아미노펜 (Acetaminophen)", "분류": "해열진통제", "설명": "위장 장애가 적으나 일일 4,000mg 초과 시 간 손상 주의"},
        "탁센": {"성분": "나프록센 (Naproxen)", "분류": "NSAIDs 소염진통제", "설명": "진통 효과가 길게 유지되나 식후 복용 필수"},
        "이지엔6": {"성분": "덱시부프로펜 / 이부프로펜", "분류": "NSAIDs 소염진통제", "설명": "생리통, 치통, 염증 완화에 빠르고 우수함"},
        "판콜": {"성분": "아세트아미노펜 + 클로르페니라민 + 카페인", "분류": "복합 감기약", "설명": "타 진통제와 함께 먹으면 아세트아미노펜 중복 위험"},
        "판피린": {"성분": "아세트아미노펜 + 메틸에페드린 + 카페인", "분류": "복합 감기약", "설명": "카페인이 포함되어 밤 늦게 복용 시 불면 유발 가능"},
        "화이투벤": {"성분": "아세트아미노펜 + 슈도에페드린 + 항히스타민", "분류": "종합 감기약", "설명": "코막힘, 기침, 발열 완화용 종합성분"},
        "게보린": {"성분": "아세트아미노펜 + 이소프로필안티피린 + 카페인", "분류": "복합 진통제", "설명": "강한 진통 효과가 있으나 장기 복용 금물"},
        "은교산": {"성분": "금은화, 연교, 길경 (생약 제제)", "분류": "한방 소염제", "설명": "목 통증, 인후염 부종 완화에 부작용이 적고 우수함"}
    }

    search_keyword = st.text_input("찾고 싶은 약품 이름을 입력하세요 (예: 타이레놀, 탁센, 판콜 등)", "")

    if search_keyword:
        found = False
        for name, info in drug_db.items():
            if search_keyword.strip() in name:
                found = True
                st.success(f"✅ 검색 결과: **{name}**")
                st.write(f"- **유효 성분**: {info['성분']}")
                st.write(f"- **약학 분류**: {info['분류']}")
                st.info(f"💡 **복약 팁 및 주의사항**: {info['설명']}")
                break
        if not found:
            st.warning("DB에 등록되지 않은 약품입니다. (타이레놀, 탁센, 이지엔6, 판콜, 판피린, 화이투벤, 게보린, 은교산 검색 가능)")

# ==============================================================================
# MENU 4: 📷 처방전/약봉지 AI 스캐너 (Vision OCR)
# ==============================================================================
elif st.session_state.menu == "📷 처방전/약봉지 AI 스캐너":
    st.title("📷 처방전 / 약봉지 AI 사진 스캐너")
    st.caption("Google Gemini Vision AI가 업로드한 사진에서 약품명을 인식하여 주의사항을 자동 분석합니다.")
    st.markdown("---")

    uploaded_file = st.file_uploader("처방전이나 약봉지 사진을 업로드하세요 (JPG, PNG)", type=["jpg", "jpeg", "png"])

    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption="업로드된 약봉지/처방전 이미지", use_column_width=True)

        if st.button("🤖 AI 텍스트 인식 및 약물 스크리닝 분석"):
            if not has_api:
                st.error("⚠️ AI 스캔 기능을 사용하려면 사이드바에 Gemini API Key를 입력해 주세요.")
            else:
                with st.spinner("Gemini Vision AI가 이미지 속 약물 정보를 읽고 있습니다..."):
                    try:
                        prompt = """
                        이 처방전 또는 약봉지 사진에서 인식되는 모든 약품명을 찾고, 
                        각 약품의 효능과 복용 시 핵심 주의사항(DUR)을 간호학적 관점에서 간략하게 요약 정리해 줘.
                        """
                        response = model.generate_content([prompt, image])
                        st.subheader("📋 AI 스캔 분석 결과")
                        st.markdown(response.text)
                    except Exception as e:
                        st.error(f"이미지 분석 중 오류가 발생했습니다: {e}")

st.markdown("---")
st.caption("※ 본 프로그램은 20901 강은유 학생의 수행평가 개발 보고서용 시뮬레이터입니다.")

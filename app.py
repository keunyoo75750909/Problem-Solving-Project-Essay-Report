import streamlit as st
import google.generativeai as genai

# 1. 페이지 기본 설정 및 세이지 그린(Sage Green) 디자인 커스텀 CSS
st.set_page_config(
    page_title="스마트 OTC 맞춤 처방 & DUR 약물 융합 시스템",
    page_icon="🌿",
    layout="wide"
)

# 마음의 평화를 주는 그린 계열 CSS 스타일링
st.markdown("""
<style>
    /* 전체 배경색: 맑고 차분한 세이지 그린 계열 */
    .stApp {
        background-color: #F2F6F3;
    }
    /* 사이드바 배경 */
    [data-testid="stSidebar"] {
        background-color: #E3EBE5;
    }
    /* 메인 텍스트 및 제목 색상 */
    h1, h2, h3 {
        color: #1E4D2B !important;
        font-family: 'Pretendard', sans-serif;
    }
    /* 버튼 스타일 */
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
    /* 커스텀 카드 디자인 */
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

# 2. 타이틀 영역
st.title("🌿 스마트 맞춤형 OTC 약물 조합 & DUR 케어 가이드")
st.caption("의생명과학 약리 기전 및 간호학적 복약 지도를 결합한 정밀 헬스케어 시스템")
st.markdown("---")

# 3. 사이드바 설정
st.sidebar.header("⚙️ 시스템 설정")
api_key = st.sidebar.text_input("Gemini API Key (선택)", type="password", help="API 키 입력 시 AI 맞춤 정밀 리포트가 생성됩니다.")

try:
    if api_key:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        has_api = True
    else:
        has_api = False
except Exception:
    has_api = False

# 4. 환자 정보 및 다중 증상 입력
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

supplements = st.text_input("현재 복용 중인 약물 / 영양제 (예: 종합감기약, 아스피린, 비타민C)", "")

# 5. 매칭 분석 실행
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

        # ----------------------------------------------------
        # [알고리즘] 증상별 세부 조합 (메인 + 시너지 + 위장약) 매칭
        # ----------------------------------------------------

        # Case 1: 콧물 / 코막힘 / 재채기
        if "콧물 / 코막힘 / 재채기" in symptoms:
            if is_drowsy_sensitive:
                main_drugs.append("2세대 항히스타민제 (세티리진 / 팩소페나딘)")
                matching_reasons.append("• [콧물] 졸음 부작용을 최소화한 2세대 항히스타민제로 콧물·재채기 억제")
            else:
                main_drugs.append("1세대 항히스타민제 (클로르페니라민)")
                matching_reasons.append("• [콧물] 항콜린 작용이 강력하여 콧물을 즉각적으로 dry 시킴")

            synergy_drugs.append("비충혈제거제 (슈도에페드린)")
            matching_reasons.append("• [시너지 매칭] 항히스타민제와 슈도에페드린을 조합하여 혈관을 수축시키고 코막힘을 시원하게 해소")
            dur_cautions.append("코막힘 약(슈도에페드린)은 심장 두근거림이나 불면을 유발할 수 있으므로 저녁 늦게 복용 시 주의하세요.")

        # Case 2: 근육통 / 담 결림 / 관절통
        if "근육통 / 담 결림 / 관절통" in symptoms:
            main_drugs.append("근이완제 (클로르조키사존)")
            synergy_drugs.append("NSAIDs 소염진통제 (덱시부프로펜 / 이부프로펜)")
            matching_reasons.append("• [근육통 융합 처방] 뭉친 근육을 풀어주는 '근이완제' + 뼈/근육 염증 통증을 줄이는 '소염진통제'를 동시 조합하여 치료 효과 극대화")

            if not has_stomach_ache:
                stomach_protectors.append("위장관운동조절제 / 제산제 (트리메부틴 또는 알마게이트)")
                matching_reasons.append("• [위장 보호 필수] NSAIDs 소염진통제와 근이완제 병용 시 위막 자극이 심해지므로 위장약 동시 복용 조합 권장")

            dur_cautions.append("근이완제 복용 시 나른함이나 졸음이 심해질 수 있으므로 운전이나 위험한 기계 조작을 금합니다.")

        # Case 3: 인후통 (목 통증)
        if "인후통 (목 통증 및 부종)" in symptoms:
            if has_stomach_ache:
                main_drugs.append("아세트아미노펜 (해열진통제)")
                synergy_drugs.append("생약 소염제 (은교산)")
                matching_reasons.append("• [인후통 위장보호 처방] 위 자극이 있는 NSAIDs 대신 아세트아미노펜 + 한방 은교산 생약 소염제 조합으로 목 통증 완화")
            else:
                main_drugs.append("NSAIDs 소염진통제 (이부프로펜)")
                synergy_drugs.append("소염효소제 (트라넥삼산 또는 소염효소제)")
                matching_reasons.append("• [인후통 시너지 처방] 소염진통제에 부종을 줄이는 소염효소제를 조합하여 목 발열 및 염증 부종 동시 완화")

        # Case 4: 발열 및 오한 / 몸살
        if "발열 및 오한 / 몸살" in symptoms:
            if has_liver_disease:
                main_drugs.append("이부프로펜 계열")
                dur_cautions.append("간 기능 저하 소견으로 간 대사 부담이 큰 아세트아미노펜 대신 이부프로펜을 우선 권장합니다.")
            else:
                main_drugs.append("아세트아미노펜 (타이레놀 계열)")
                matching_reasons.append("• [발열/몸살] 중추신경계에 작용하여 빠른 해열 및 전신 몸살 완화")

        # Case 5: 기침 / 가래
        if "기침 / 가래" in symptoms:
            main_drugs.append("진해거담제 (앙브록솔 + 덱스트로메토르판 복합제)")
            matching_reasons.append("• [기침/가래] 기침 반사를 억제하는 '진해제'와 가래 끈적임을 줄여 배출을 돕는 '거담제' 융합 복합제")

        # Case 6: 속쓰림 / 소화불량
        if "속쓰림 / 소화불량 / 위통" in symptoms or has_stomach_ache:
            stomach_protectors.append("H2 블로커 (파모티딘) 또는 제산제 (알마겔)")
            matching_reasons.append("• [위장 보호 처방] 위산 분비를 억제하고 위막을 코팅하여 약물 복용으로 인한 위장 장애 사전에 완전 방어")

        # DUR 중복 및 상호작용 검사
        if "종합감기약" in supplements:
            dur_cautions.append("🚨 [DUR 경고] 복용 중인 '종합감기약'에 이미 아세트아미노펜/항히스타민이 포함되어 있어 성분 중복 오남용 위험이 높습니다. 단일제 위주 복용을 권장합니다.")
        if "아스피린" in supplements and any("NSAIDs" in d for d in synergy_drugs + main_drugs):
            dur_cautions.append("🚨 [DUR 경고] 아스피린과 NSAIDs(이부프로펜 등) 동시 복용 시 위장관 출혈 위험이 크게 증가합니다.")

        # ----------------------------------------------------
        # 화면 시각화 출력 (세이지 그린 카드 형태)
        # ----------------------------------------------------

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
            st.write("1. **식후 30분 복용**: 위장 보호제가 포함되어 있더라도 위막 자극을 낮추기 위해 미온수 1컵과 함께 식후 복용하세요.")
            st.write("2. **수분 섭취**: 진해거담제나 항히스타민제 복용 시 기도 점막이 건조해지므로 하루 1.5L 이상 미지근한 물을 자주 마시세요.")
            st.write("3. **증상 지속 시**: 3일 이상 증상이 호전되지 않거나 고열 동반 시 즉시 병원 방문이 필요합니다.")

            st.markdown("</div>", unsafe_allow_html=True)

        # Gemini AI 가이드 호출 (키 입력 시)
        if has_api:
            st.markdown("---")
            st.subheader("🤖 Gemini AI 맞춤형 헬스케어 피드백")
            prompt = f"""
            당신은 임상 간호사이자 약학 전문가입니다.
            - 환자 증상: {', '.join(symptoms)}
            - 위장장애 유무: {has_stomach_ache}, 졸음 민감: {is_drowsy_sensitive}
            - 매칭된 약물: 주치료제({', '.join(main_drugs)}), 시너지제({', '.join(synergy_drugs)}), 위장약({', '.join(stomach_protectors)})
            
            환자에게 약물 조합의 이점과 일상 속 간호 케어 팁을 3문장 이내로 친절하게 설명해 주세요.
            """
            with st.spinner("AI가 상세 약리학/간호학 리포트를 생성 중입니다..."):
                try:
                    response = model.generate_content(prompt)
                    st.info(response.text)
                except Exception as e:
                    st.error(f"AI 호출 오류: {e}")

st.markdown("---")
st.caption("※ 본 프로그램은 학술 및 보고서 작성용 시뮬레이터이며, 실제 약물 복용 시 의사·약사와 상의하십시오.")

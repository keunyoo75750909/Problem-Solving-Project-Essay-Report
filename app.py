import streamlit as st
import google.generativeai as genai

# 1. 페이지 기본 설정
st.set_page_config(
    page_title="맞춤형 OTC 약물 추천 및 DUR 가이드",
    page_icon="💊",
    layout="centered"
)

# 2. 타이틀 및 안내문
st.title("💊 증상 맞춤형 일반의약품(OTC) 추천 및 DUR 가이드")
st.caption("의생명과학 및 간호학적 관점의 안전한 복약 지도 스마트 헬스케어 시스템")
st.markdown("---")

# 3. 사이드바 - 제미나이 API 키 입력 (선택 사항)
st.sidebar.header("⚙️ 설정")
api_key = st.sidebar.text_input("Gemini API Key (선택)", type="password", help="API 키를 입력하면 AI 맞춤 복약 지도가 활성화됩니다.")

# 4. 메인 입력 폼
st.subheader("1. 환자 정보 및 증상 입력")

col1, col2 = st.columns(2)

with col1:
    symptom = st.selectbox(
        "현재 가장 불편한 주요 증상",
        ["선택하세요", "인후통 (목 통증)", "발열 및 몸살", "두통 / 치통", "기침 / 가래"]
    )

with col2:
    st.write("기저 질환 및 신체 상태 (다중 선택 가능)")
    has_stomach_ache = st.checkbox("위장 장애 / 위염 / 위궤양")
    has_liver_disease = st.checkbox("간 질환 / 간 기능 저하")

supplements = st.text_input("현재 복용 중인 영양제 또는 약물 (예: 비타민C, 종합감기약)", "")

# 5. 분석 버튼 클릭 시 실행
if st.button("🔍 맞춤 약물 및 DUR 안전성 분석 실행", use_container_width=True):
    if symptom == "선택하세요":
        st.error("⚠️ 주요 증상을 선택해 주세요.")
    else:
        st.markdown("---")
        st.subheader("2. 분석 및 추천 결과")
        
        recommended_drugs = []
        dur_warnings = []
        nursing_guides = []
        
        # [알고리즘 1] 증상별 및 기저질환별 약물 선별 알고리즘
        if symptom == "인후통 (목 통증)":
            if has_stomach_ache:
                recommended_drugs = ["아세트아미노펜 (해열진통제)", "은교산 (생약 소염제)"]
                dur_warnings.append("위장 장애가 있어 위막을 자극하는 NSAIDs(이부프로펜) 대신 위장 자극이 적은 아세트아미노펜과 소염제 조합을 추천합니다.")
            else:
                recommended_drugs = ["이부프로펜 또는 덱시부프로펜 (소염진통제)", "소염효소제 (소염작용 강화)"]
                dur_warnings.append("소염진통제와 소염제의 시너지 조합으로 목 부종과 통증을 함께 완화합니다.")
                
        elif symptom == "발열 및 몸살":
            if has_liver_disease:
                recommended_drugs = ["이부프로펜 (소염진통제)"]
                dur_warnings.append("간 기능 저하 소견이 있어 간 대사 부담이 있는 아세트아미노펜 대신 이부프로펜 성분을 권장합니다.")
            else:
                recommended_drugs = ["아세트아미노펜 (해열진통제)", "이부프로펜 (필요 시 4시간 간격 교대복용)"]
                dur_warnings.append("발열 지속 시 아세트아미노펜과 이부프로펜을 4~6시간 간격으로 교대 복용할 수 있습니다.")

        elif symptom == "두통 / 치통":
            if has_stomach_ache:
                recommended_drugs = ["아세트아미노펜 단일제"]
                dur_warnings.append("위장 장애를 고려하여 NSAIDs 계열 복용을 피하고 아세트아미노펜을 복용하세요.")
            else:
                recommended_drugs = ["덱시부프로펜 또는 나프록센"]
                dur_warnings.append("빠르고 강한 진통 효과를 위해 NSAIDs 계열 진통제를 권장합니다.")

        elif symptom == "기침 / 가래":
            recommended_drugs = ["진해거담제 (덱스트로메토르판 + 앙브록솔 성분)"]
            dur_warnings.append("기침 억제제와 가래 배출제가 함께 포함된 복합 성분을 추천합니다.")

        # [알고리즘 2] 복용 중인 영양제/약물 상호작용 검사 (DUR)
        if "종합감기약" in supplements or "감기약" in supplements:
            dur_warnings.append("🚨 [중요 DUR 경고] 종합감기약에는 이미 아세트아미노펜이 포함되어 있을 가능성이 높습니다. 추가 진통제 복용 시 중복 복용으로 인한 간 손상 위험이 있으니 성분표를 반드시 확인하세요.")

        # 공통 간호학적 복약 가이드 생성
        nursing_guides.append("약물 복용 시 미온수(미지근한 물) 1컵 이상을 충분히 섭취하세요.")
        if has_stomach_ache or "이부프로펜" in str(recommended_drugs):
            nursing_guides.append("위장 장애 예방을 위해 반드시 식후 30분 이내에 복용하세요.")
        else:
            nursing_guides.append("일일 정해진 용량과 복용 간격(4~6시간)을 준수하세요.")

        # 결과 출력 화면 구성
        col_res1, col_res2 = st.columns(2)
        
        with col_res1:
            st.success("✅ **추천 약물 성분 조합**")
            for drug in recommended_drugs:
                st.write(f"- {drug}")
                
        with col_res2:
            st.info("🩺 **간호학적 복약 케어 가이드**")
            for guide in nursing_guides:
                st.write(f"- {guide}")

        st.warning("⚠️ **약물 안전성(DUR) 및 주의사항**")
        for warning in dur_warnings:
            st.write(f"- {warning}")

        # [알고리즘 3] 생성형 AI (Gemini) 연동 피드백 (API 키 존재 시 실행)
        if api_key:
            try:
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel('gemini-1.5-flash')
                
                prompt = f"""
                당신은 임상 간호사이자 약학 전문가입니다.
                - 환자 증상: {symptom}
                - 기저질환: 위장장애({has_stomach_ache}), 간질환({has_liver_disease})
                - 현재 복용 중인 영양제/약물: {supplements}
                - 추천된 약물: {', '.join(recommended_drugs)}
                
                위 환자 상태에 맞는 3줄 이내의 따뜻하고 전문적인 간호 복약 지도 팁을 작성해 주세요.
                """
                
                with st.spinner("AI가 상세 복약 지도 리포트를 생성 중입니다..."):
                    response = model.generate_content(prompt)
                    st.markdown("---")
                    st.subheader("🤖 AI 맞춤형 헬스케어 리포트")
                    st.write(response.text)
            except Exception as e:
                st.error(f"AI 연동 중 오류가 발생했습니다: {e}")

# Footer
st.markdown("---")
st.caption("※ 본 프로그램은 참고용이며, 정확한 진단과 처방은 의사 또는 약사와 상의하십시오.")

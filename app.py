# -*- coding: utf-8 -*-
"""
==========================================================================================
 SmartMed DUR  |  스마트 맞춤형 OTC 약물 조합 & DUR 케어 가이드  (v2.0 Premium)
 개발: 20901 강은유   |   고등학교 의생명과학·간호학 진로 연계 프로젝트
==========================================================================================
 [앱 구조 한눈에 보기]
  1. 설정/CSS        : 페이지 설정, 글래스모피즘 테마
  2. 약물 데이터베이스: 약(DRUGS), 영양제(SUPPS), 약물 상호작용(INTERACTIONS), 증상(SYMPTOMS)
  3. 분석 엔진       : 환자 플래그화 → 약물별 위험평가 → 후보 선택 → PK 보정 → 상호작용 → 점수화
  4. 스케줄러        : PK 보정 간격으로 24시간 복약 시각 생성 + 킬레이트(흡수방해) 간격 자동 확보
  5. UI 페이지       : 대시보드 / 스마트 문진·DUR / 복약 타임라인 / AI 처방전 스캐너
  6. 라우터          : st.session_state 기반 페이지 이동

 [핵심 알고리즘 - 보고서에서 설명할 포인트]
  A. 환자 프로파일 → '플래그 집합'(예: renal_severe, pregnant, ulcer ...)으로 변환
  B. 각 약물의 규칙표(rules)와 플래그를 교집합 → 위험등급(Danger/Warning/Safe) 자동 산출
  C. 금기(Danger) 약물은 후보에서 제외하고, 남은 후보 중 (위험등급 → 경고 개수 → 우선순위) 순으로 선택
  D. PK 보정: 신장/간 기능·고령에 따라 반감기(t½)를 보정 → 복용 간격 자동 연장
  E. PARS(Patient-Adjusted Regimen Safety score): 처방 조합 전체의 안전 점수(0~100)
  F. 스케줄러: 보정 간격 + 식사 시각 + 약물 간 필요 간격(예: 철분↔제산제 2시간)을 동시에 만족하는 시간표

 ※ 본 앱은 교육·연구용 프로토타입입니다. 실제 복약 결정은 반드시 의사·약사와 상의하세요.
==========================================================================================
"""

import datetime as dt
import itertools
import json
import math
import re
import time
from urllib.parse import quote

import pandas as pd
import streamlit as st

# 선택 라이브러리: 설치되지 않아도 앱이 죽지 않도록 안전하게 import
try:
    from PIL import Image
except ImportError:  # pragma: no cover
    Image = None
try:
    import google.generativeai as genai
except ImportError:  # pragma: no cover
    genai = None

# ------------------------------------------------------------------------------------------
# 1. 페이지 설정 & 글로벌 CSS (Glassmorphism + Sage Green)
# ------------------------------------------------------------------------------------------
st.set_page_config(
    page_title="SmartMed DUR | 스마트 OTC 케어",
    page_icon="💊",
    layout="wide",
    initial_sidebar_state="expanded",
)

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700;900&display=swap');

:root{
  --sage-50:#f4f8f5; --sage-100:#e5efe8; --sage-200:#cfe1d5; --sage-300:#a9c9b4;
  --sage-500:#6f9f82; --sage-600:#548569; --sage-700:#3f6b53; --sage-900:#223b2f;
  --danger:#d64545; --danger-bg:#fdecec;
  --warn:#d9822b;   --warn-bg:#fff3e3;
  --safe:#2f9e6b;   --safe-bg:#e6f7ee;
  --ink:#1f2d28; --muted:#5f7168;
}
html, body, [class*="css"], .stApp { font-family:'Noto Sans KR', sans-serif; }
.stApp{
  color:var(--ink);
  background:
    radial-gradient(1100px 560px at 8% -8%, #d7e9de 0%, transparent 60%),
    radial-gradient(900px 520px at 100% 0%, #e6f0e8 0%, transparent 55%),
    linear-gradient(180deg,#f7fbf8 0%,#edf4ef 100%);
}
.block-container{ padding-top:2rem; max-width:1180px; }
h1,h2,h3,h4{ color:var(--sage-900); letter-spacing:-0.02em; }

/* ---------- 사이드바 ---------- */
[data-testid="stSidebar"]{ background:linear-gradient(180deg,#2c4f3f 0%,#3f6b53 100%); }
[data-testid="stSidebar"] label, [data-testid="stSidebar"] p, [data-testid="stSidebar"] span,
[data-testid="stSidebar"] h1,[data-testid="stSidebar"] h2,[data-testid="stSidebar"] h3,
[data-testid="stSidebar"] div[role="radiogroup"] *{ color:#eef6f0 !important; }
[data-testid="stSidebar"] input{ color:#1f2d28 !important; }
[data-testid="stSidebar"] div[role="radiogroup"] > label{
  background:rgba(255,255,255,.08); border:1px solid rgba(255,255,255,.14);
  border-radius:14px; padding:.55rem .8rem; margin-bottom:.4rem; transition:all .2s ease;
}
[data-testid="stSidebar"] div[role="radiogroup"] > label:hover{
  background:rgba(255,255,255,.18); transform:translateX(4px);
}

/* ---------- 글래스 카드 ---------- */
.glass{
  background:rgba(255,255,255,.62);
  -webkit-backdrop-filter:blur(14px) saturate(160%); backdrop-filter:blur(14px) saturate(160%);
  border:1px solid rgba(255,255,255,.75); border-radius:22px;
  box-shadow:0 8px 32px rgba(63,107,83,.12);
  padding:1.25rem 1.4rem; margin-bottom:1rem;
  transition:transform .25s ease, box-shadow .25s ease;
}
.glass:hover{ transform:translateY(-4px); box-shadow:0 18px 42px rgba(63,107,83,.20); }
.glass h4{ margin:0 0 .35rem 0; font-size:1.05rem; }
.glass p{ margin:0; color:var(--muted); font-size:.93rem; line-height:1.6; }

/* ---------- 히어로 ---------- */
.hero{
  position:relative; overflow:hidden; border-radius:28px; padding:2.4rem 2.2rem; margin-bottom:1.2rem;
  background:linear-gradient(135deg,#3f6b53 0%,#6f9f82 55%,#a9c9b4 100%);
  box-shadow:0 20px 50px rgba(63,107,83,.30); color:#fff;
}
.hero:before{ content:""; position:absolute; right:-60px; top:-60px; width:260px; height:260px;
  background:radial-gradient(circle,rgba(255,255,255,.35),transparent 70%); border-radius:50%; }
.hero h1{ color:#fff; font-size:2.1rem; font-weight:900; margin:.3rem 0 .5rem 0; }
.hero p{ color:#eaf5ee; font-size:1.02rem; margin:0; max-width:680px; line-height:1.7; }
.hero .tag{ display:inline-block; background:rgba(255,255,255,.2); border:1px solid rgba(255,255,255,.4);
  padding:.2rem .8rem; border-radius:999px; font-size:.82rem; font-weight:500; }

/* ---------- 배지 ---------- */
.badge{ display:inline-block; padding:.18rem .7rem; border-radius:999px; font-size:.78rem; font-weight:700; margin-right:.3rem; }
.badge-danger{ background:var(--danger-bg); color:var(--danger); border:1px solid #f3b9b9; }
.badge-warning{ background:var(--warn-bg); color:var(--warn); border:1px solid #f1cfa3; }
.badge-safe{ background:var(--safe-bg); color:var(--safe); border:1px solid #b5e4cc; }
.badge-info{ background:var(--sage-100); color:var(--sage-700); border:1px solid var(--sage-200); }

/* ---------- 위험도 카드 ---------- */
.finding{ border-radius:16px; padding:.8rem 1rem; margin:.45rem 0; border-left:6px solid; background:#fff;
  box-shadow:0 4px 14px rgba(0,0,0,.05); transition:transform .2s ease; }
.finding:hover{ transform:translateX(4px); }
.finding.danger{ border-color:var(--danger); background:var(--danger-bg); }
.finding.warning{ border-color:var(--warn); background:var(--warn-bg); }
.finding.safe{ border-color:var(--safe); background:var(--safe-bg); }
.finding b{ color:var(--ink); } .finding span.cat{ color:var(--muted); font-size:.78rem; margin-left:.3rem; }
.finding div{ margin-top:.25rem; font-size:.92rem; line-height:1.55; }

/* ---------- 지표 / 점수 ---------- */
.score-ring{ text-align:center; padding:1rem; }
.score-num{ font-size:3.2rem; font-weight:900; line-height:1; }
.score-lab{ color:var(--muted); font-size:.85rem; margin-top:.3rem; }
.kpi{ text-align:center; } .kpi .n{ font-size:1.9rem; font-weight:900; color:var(--sage-700); }
.kpi .l{ font-size:.82rem; color:var(--muted); }

/* ---------- 타임라인 ---------- */
.tl-item{ display:flex; gap:.9rem; align-items:flex-start; padding:.75rem 1rem; margin:.4rem 0;
  background:rgba(255,255,255,.7); border-radius:16px; border:1px solid rgba(255,255,255,.8);
  box-shadow:0 4px 14px rgba(63,107,83,.08); transition:all .2s ease; }
.tl-item:hover{ transform:translateX(6px); box-shadow:0 8px 22px rgba(63,107,83,.16); }
.tl-time{ min-width:64px; font-weight:900; font-size:1.15rem; color:var(--sage-700); }
.tl-body b{ font-size:1rem; } .tl-body div{ color:var(--muted); font-size:.86rem; margin-top:.15rem; }

/* ---------- HTML 표 (모바일 가로 스크롤) ---------- */
.tbl-wrap{ overflow-x:auto; border-radius:18px; box-shadow:0 8px 28px rgba(63,107,83,.12); background:rgba(255,255,255,.8); }
table.tl{ border-collapse:collapse; width:100%; font-size:.86rem; }
table.tl th{ background:var(--sage-700); color:#fff; padding:.6rem .7rem; text-align:center; white-space:nowrap; }
table.tl td{ padding:.5rem .6rem; text-align:center; border-bottom:1px solid var(--sage-100); white-space:nowrap; }
table.tl tr:hover td{ background:var(--sage-50); }
table.tl td:first-child{ font-weight:700; color:var(--sage-700); }
.dose{ background:var(--sage-100); color:var(--sage-700); border-radius:999px; padding:.15rem .6rem; font-weight:700; }

/* ---------- 버튼 / 탭 / 익스팬더 ---------- */
.stButton > button, [data-testid="stFormSubmitButton"] > button,
[data-testid="stBaseButton-secondary"], [data-testid="stBaseButton-secondaryFormSubmit"], [data-testid="stBaseButton-primary"]{
  width:100%; border-radius:14px; border:1px solid rgba(63,107,83,.25);
  background:linear-gradient(135deg,#ffffff,#e5efe8); color:var(--sage-900); font-weight:700;
  padding:.6rem 1rem; transition:all .22s ease; box-shadow:0 4px 12px rgba(63,107,83,.10);
}
.stButton > button:hover, [data-testid="stFormSubmitButton"] > button:hover{
  background:linear-gradient(135deg,#548569,#3f6b53); color:#fff; transform:translateY(-2px) scale(1.01);
  box-shadow:0 10px 24px rgba(63,107,83,.30); border-color:transparent;
}
.stTabs [data-baseweb="tab-list"]{ gap:.4rem; flex-wrap:wrap; }
.stTabs [data-baseweb="tab"]{ background:rgba(255,255,255,.55); border-radius:12px 12px 0 0; padding:.5rem 1rem; }
.stTabs [aria-selected="true"]{ background:#fff !important; color:var(--sage-700) !important; font-weight:700; }
[data-testid="stExpander"]{ background:rgba(255,255,255,.6); border-radius:16px; border:1px solid rgba(255,255,255,.8); }
.stProgress > div > div > div > div{ background:linear-gradient(90deg,#a9c9b4,#548569); }
.footer-note{ color:var(--muted); font-size:.78rem; text-align:center; margin-top:2rem; }

@media (max-width:768px){
  .hero{ padding:1.6rem 1.2rem; } .hero h1{ font-size:1.5rem; }
  .score-num{ font-size:2.4rem; } .tl-time{ min-width:54px; font-size:1rem; }
}
@media (prefers-reduced-motion:reduce){ *{ transition:none !important; } }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

# ------------------------------------------------------------------------------------------
# 2. 약물 데이터베이스 (교육용 요약 DB - 실제 서비스에서는 식약처 e약은요/DUR API로 대체)
# ------------------------------------------------------------------------------------------
RANK = {"safe": 0, "warning": 1, "danger": 2}
SEV = {
    "danger": ("금기", "Danger", "🔴"),
    "warning": ("주의", "Warning", "🟠"),
    "safe": ("병용가능", "Safe", "🟢"),
}

# NSAIDs(이부프로펜·나프록센)는 규칙이 거의 같으므로 공통 규칙표를 복사해서 사용
_NSAID_RULES = {
    "pregnant": ("danger", "임신 중 NSAIDs는 태아 동맥관 조기 폐쇄·양수과소 위험(특히 임신 후기 금기). 의사 확인 없이 복용 금지."),
    "lactating": ("safe", "수유 중: 모유 이행이 적어 단기·저용량 사용은 비교적 안전하다고 알려져 있음."),
    "renal_mild": ("warning", "신기능 저하(eGFR 30~59): 신장 혈류 감소로 신독성 위험↑ — 복용 전 의료진 상담."),
    "renal_severe": ("danger", "중증 신기능 저하(eGFR<30): NSAIDs는 사실상 금기."),
    "hepatic_mild": ("warning", "경도 간기능 이상: 출혈·체액저류 위험이 올라갈 수 있어 최소 기간만 사용."),
    "hepatic_severe": ("danger", "중증 간기능 이상: 응고 이상·출혈 위험↑ — 사용 회피."),
    "ulcer": ("danger", "위궤양/위장관 출혈 병력: 재출혈 위험이 크게 증가."),
    "asthma": ("warning", "천식: 일부 환자에서 NSAIDs가 기관지 수축을 유발(아스피린 과민성 천식)."),
    "allergy_nsaid": ("danger", "NSAIDs/아스피린 알레르기: 교차 과민반응 위험."),
    "htn": ("warning", "고혈압: 수분·나트륨 저류로 혈압이 오르거나 혈압약 효과가 감소할 수 있음."),
    "heart": ("warning", "심장질환: 장기·고용량 사용 시 심혈관 위험 증가."),
    "age_elder": ("warning", "65세 이상: 위장관 출혈·신장 부작용 위험이 높아 최소 용량·최단 기간."),
    "med_warfarin": ("danger", "와파린(항응고제)과 병용 시 출혈 위험 급증."),
    "med_bp": ("warning", "ACEi/ARB/이뇨제와 병용 시 신장 손상 위험↑('트리플 훼미' 조합)."),
    "med_steroid": ("warning", "스테로이드와 병용 시 위장관 출혈·궤양 위험↑."),
}

DRUGS = {
    "apap": dict(
        name="아세트아미노펜", brand="타이레놀 등", cls="해열진통제", icon="🌡️",
        tags={"analgesic", "apap"}, aliases=["아세트아미노펜", "타이레놀", "acetaminophen", "paracetamol", "tylenol"],
        moa="중추신경계(시상하부)의 COX 활성을 억제해 체온설정점을 낮추고 통증 역치를 높임. 말초 항염 작용은 거의 없음.",
        t_half=2.5, tmax=1.0, interval=6, max_doses=4, clearance="hepatic", meal="any",
        rules={
            "hepatic_severe": ("danger", "중증 간기능 이상: 간에서 대사되는 약으로 간독성 위험 — 자가 복용 회피."),
            "hepatic_mild": ("warning", "경도 간기능 이상: 1회량·1일 총량을 줄이고 간격을 늘려야 함."),
            "allergy_apap": ("danger", "아세트아미노펜 알레르기 병력."),
            "renal_severe": ("warning", "중증 신기능 저하: 복용 간격 연장 필요."),
            "med_warfarin": ("warning", "고용량·장기 복용 시 INR 상승 가능 — 증상이 길어지면 의료진 상담."),
            "pregnant": ("safe", "임신 중 상대적으로 우선 고려되는 해열진통제(최소 용량·최단 기간, 의료진 확인 권장)."),
            "lactating": ("safe", "수유 중 일반적으로 사용 가능한 것으로 알려져 있음."),
        },
        food={"alcohol": ("warning", "음주 시 간독성 위험↑ (CYP2E1 유도로 독성 대사체 NAPQI 증가).")},
        note="종합감기약에도 들어 있는 경우가 많아 '성분 중복'을 꼭 확인하세요.",
    ),
    "ibuprofen": dict(
        name="이부프로펜", brand="브루펜·애드빌 등", cls="NSAIDs(소염진통제)", icon="💊",
        tags={"nsaid"}, aliases=["이부프로펜", "브루펜", "애드빌", "ibuprofen", "advil"],
        moa="말초 COX-1/COX-2를 비선택적으로 억제 → 프로스타글란딘 합성↓ → 통증·염증·발열 감소. COX-1 억제로 위점막 보호 기능도 감소.",
        t_half=2.0, tmax=1.5, interval=8, max_doses=3, clearance="mixed", meal="after",
        rules=dict(_NSAID_RULES),
        food={"alcohol": ("warning", "음주 시 위점막 손상·위장관 출혈 위험↑.")},
        note="공복 복용은 위장 장애를 높입니다. 식후 복용을 기본으로 하세요.",
    ),
    "naproxen": dict(
        name="나프록센", brand="낙센 등", cls="NSAIDs(소염진통제)", icon="💊",
        tags={"nsaid"}, aliases=["나프록센", "낙센", "naproxen"],
        moa="COX-1/COX-2 비선택 억제. 반감기가 길어 하루 2회 복용이 가능한 지속형 NSAID.",
        t_half=14.0, tmax=2.0, interval=12, max_doses=2, clearance="mixed", meal="after",
        rules=dict(_NSAID_RULES),
        food={"alcohol": ("warning", "음주 시 위장관 출혈 위험↑.")},
        note="반감기가 길어 간격을 줄이면 약물이 체내에 빠르게 축적됩니다.",
    ),
    "pseudoephedrine": dict(
        name="슈도에페드린", brand="슈다페드 등", cls="비충혈 제거제(코막힘)", icon="👃",
        tags={"coldmed", "sympathomimetic", "pseudoephedrine"},
        aliases=["슈도에페드린", "슈다페드", "pseudoephedrine", "sudafed"],
        moa="α-아드레날린 수용체 작용 → 코점막 혈관 수축 → 부종·코막힘 완화. 교감신경 자극으로 혈압·심박 상승 가능.",
        t_half=6.0, tmax=2.0, interval=6, max_doses=3, clearance="renal", meal="any", last_before_bed=4.0,
        rules={
            "heart": ("danger", "심장질환(부정맥·협심증 등): 심박·혈압 상승으로 위험."),
            "htn": ("warning", "고혈압: 혈압 상승 가능 — 조절되지 않는 고혈압은 사용 금지."),
            "thyroid": ("warning", "갑상선 질환: 교감신경 자극 증상(빈맥·떨림)이 악화될 수 있음."),
            "diabetes": ("warning", "당뇨: 혈당 상승 가능성이 있어 주의."),
            "glaucoma_bph": ("warning", "녹내장/전립선비대: 안압 상승·배뇨곤란 악화 가능."),
            "pregnant": ("warning", "임신 중(특히 초기): 태아 위험 가능성 → 의료진과 상의 후 사용."),
            "lactating": ("warning", "수유 중: 모유량 감소 보고가 있어 주의."),
            "renal_severe": ("warning", "중증 신기능 저하: 신장으로 배설되어 축적 위험."),
            "med_maoi": ("danger", "MAO 억제제와 병용 시 고혈압 위기 위험."),
            "med_bp": ("warning", "혈압약 효과를 떨어뜨릴 수 있음."),
            "age_elder": ("warning", "65세 이상: 불면·혈압상승·배뇨장애 위험↑."),
        },
        food={"caffeine": ("warning", "카페인과 교감신경 자극이 겹쳐 불면·가슴 두근거림이 심해질 수 있음.")},
        note="불면을 막기 위해 마지막 복용은 취침 4시간 전까지로 스케줄링됩니다.",
    ),
    "chlorpheniramine": dict(
        name="클로르페니라민", brand="페니라민 등", cls="1세대 항히스타민제", icon="💧",
        tags={"antihistamine", "coldmed", "sedating", "chlorpheniramine"},
        aliases=["클로르페니라민", "페니라민", "chlorpheniramine"],
        moa="H1 수용체 길항(역작용) → 콧물·재채기·가려움 완화. 뇌혈관장벽을 통과해 졸음, 항콜린 작용(구갈·변비·요저류)을 유발.",
        t_half=20.0, tmax=3.0, interval=8, max_doses=3, clearance="hepatic", meal="any",
        rules={
            "allergy_antihist": ("danger", "항히스타민제 알레르기 병력."),
            "glaucoma_bph": ("warning", "항콜린 작용으로 녹내장·전립선비대 악화 가능."),
            "asthma": ("warning", "기도 분비물이 끈적해져 천식 증상이 악화될 수 있음."),
            "age_elder": ("warning", "65세 이상: 인지저하·낙상·변비·요저류 위험(Beers 기준 회피 권고)."),
            "hepatic_severe": ("warning", "간대사 약물로 축적 위험."),
            "pregnant": ("safe", "임신 중 사용 경험이 많은 편이나 졸림 등 확인 후 사용."),
            "lactating": ("warning", "수유 중: 영아 졸림·모유량 감소 가능."),
        },
        food={"alcohol": ("warning", "알코올과 중추억제 효과가 겹쳐 졸음·집중력 저하 가중.")},
        note="졸음이 있어 운전·기계 조작은 피하세요.",
    ),
    "cetirizine": dict(
        name="세티리진", brand="지르텍 등", cls="2세대 항히스타민제", icon="💧",
        tags={"antihistamine", "cetirizine"}, aliases=["세티리진", "지르텍", "cetirizine", "zyrtec"],
        moa="말초 H1 수용체를 선택적으로 차단 → 알레르기성 콧물·가려움 완화. 뇌 이행이 적어 졸음이 1세대보다 적음.",
        t_half=8.0, tmax=1.0, interval=24, max_doses=1, clearance="renal", meal="any",
        rules={
            "allergy_antihist": ("danger", "항히스타민제 알레르기 병력."),
            "renal_mild": ("warning", "신기능 저하: 신장 배설이 감소해 용량 감량이 필요할 수 있음."),
            "renal_severe": ("warning", "중증 신기능 저하: 감량·의료진 확인 필수."),
            "pregnant": ("safe", "임신 중 비교적 사용 경험이 있는 2세대 항히스타민제(의료진 확인 권장)."),
            "lactating": ("warning", "수유 중: 영아 졸림 관찰 필요."),
            "age_elder": ("warning", "고령: 신기능 저하 동반 가능 → 용량 확인."),
        },
        food={"alcohol": ("warning", "알코올과 병용 시 졸음이 증가할 수 있음.")},
        note="1일 1회 복용이므로 복용 시각을 일정하게 유지하세요.",
    ),
    "dextromethorphan": dict(
        name="덱스트로메토르판", brand="종합감기약 성분", cls="중추성 진해제(기침약)", icon="😮‍💨",
        tags={"antitussive", "coldmed", "dextromethorphan"}, aliases=["덱스트로메토르판", "dextromethorphan", "dxm"],
        moa="뇌 연수의 기침중추를 억제(NMDA 길항·σ1 작용). 세로토닌 재흡수에도 약하게 영향을 줌.",
        t_half=3.0, tmax=2.0, interval=8, max_doses=3, clearance="hepatic", meal="any",
        rules={
            "med_maoi": ("danger", "MAO 억제제와 병용 시 세로토닌 증후군 위험(금기)."),
            "med_ssri": ("warning", "SSRI 항우울제와 병용 시 세로토닌 증후군·CYP2D6 억제로 혈중농도↑ 가능."),
            "asthma": ("warning", "가래가 많은 기침/천식에서는 기침 억제가 부적절할 수 있음."),
            "hepatic_mild": ("warning", "간대사 약물: 간기능 저하 시 농도 상승."),
            "hepatic_severe": ("warning", "중증 간기능 이상: 축적 위험."),
            "pregnant": ("safe", "임신 중 단기 사용 경험은 있으나 의료진 확인 권장."),
        },
        food={
            "alcohol": ("warning", "알코올과 중추억제·어지러움 증가."),
            "grapefruit": ("warning", "자몽은 대사효소를 억제해 혈중농도를 높일 수 있음."),
        },
        note="가래 없는 마른기침에 사용합니다.",
    ),
    "guaifenesin": dict(
        name="구아이페네신", brand="거담제", cls="거담제(가래약)", icon="🫁",
        tags={"expectorant", "coldmed", "guaifenesin"}, aliases=["구아이페네신", "guaifenesin"],
        moa="기도 분비물의 점도를 낮추고 섬모운동을 도와 가래 배출을 쉽게 함.",
        t_half=1.0, tmax=0.5, interval=6, max_doses=4, clearance="hepatic", meal="any",
        rules={
            "pregnant": ("warning", "임신 초기 안전성 자료가 제한적이므로 의료진 확인."),
            "asthma": ("safe", "가래 배출에 도움 — 호흡곤란이 있으면 의료진 진료."),
        },
        food={"alcohol": ("safe", "물을 충분히(하루 1.5~2L) 마시면 거담 효과가 좋아집니다.")},
        note="수분 섭취가 효과에 직접적인 영향을 줍니다.",
    ),
    "famotidine": dict(
        name="파모티딘", brand="가스터 등", cls="H2 수용체 차단제(위산 억제)", icon="🔥",
        tags={"h2blocker", "gi", "famotidine"}, aliases=["파모티딘", "가스터", "famotidine", "gaster"],
        moa="위벽세포의 H2 수용체 차단 → 위산 분비 감소. 효과가 서서히 나타나고 지속시간이 긺.",
        t_half=3.0, tmax=2.0, interval=12, max_doses=2, clearance="renal", meal="any",
        rules={
            "renal_mild": ("warning", "신기능 저하: 감량 또는 간격 연장 필요(축적 시 어지러움·혼돈)."),
            "renal_severe": ("danger", "중증 신기능 저하: 중추신경계 부작용 위험 — 의료진 용량 조절 필수."),
            "pregnant": ("safe", "임신 중 속쓰림에 비교적 많이 사용되는 편(의료진 확인)."),
            "age_elder": ("warning", "고령: 신기능 저하 시 혼돈 위험."),
        },
        food={}, note="NSAIDs의 위 불편감 완화에 보조적으로 쓰일 수 있으나, 위험군은 의료진 상담이 우선입니다.",
    ),
    "antacid": dict(
        name="제산제 (Al/Mg)", brand="겔포스 등", cls="제산제(위산 중화)", icon="🔥",
        tags={"antacid", "gi", "mineral"}, aliases=["제산제", "겔포스", "알루미늄", "마그네슘", "antacid"],
        moa="위산을 직접 중화해 빠르게 증상 완화(작용시간 1~3시간). 금속 이온이 다른 약과 결합(킬레이트)해 흡수를 방해할 수 있음.",
        t_half=1.0, tmax=0.5, interval=6, max_doses=3, clearance="renal", meal="after", movable=True,
        rules={
            "renal_severe": ("danger", "중증 신기능 저하: 알루미늄·마그네슘 축적 위험."),
            "renal_mild": ("warning", "신기능 저하: 장기 복용 시 금속 이온 축적 주의."),
            "pregnant": ("safe", "단기 사용은 비교적 안전하나 고용량·장기 복용은 피함."),
        },
        food={}, note="다른 약·영양제와 2시간 이상 간격을 두는 것이 기본 원칙입니다.",
    ),
}

# 증상 → 후보 약물 (앞쪽일수록 기본 우선순위가 높음)
SYMPTOMS = {
    "pain_fever": ("🌡️ 발열·두통·근육통", ["apap", "ibuprofen", "naproxen"]),
    "menstrual": ("🩸 생리통", ["ibuprofen", "naproxen", "apap"]),
    "sore_throat": ("🗣️ 인후통", ["apap", "ibuprofen"]),
    "runny": ("💧 콧물·재채기(알레르기성)", ["cetirizine", "chlorpheniramine"]),
    "congestion": ("👃 코막힘", ["pseudoephedrine"]),
    "dry_cough": ("😮‍💨 마른기침", ["dextromethorphan"]),
    "phlegm": ("🫁 가래", ["guaifenesin"]),
    "heartburn": ("🔥 속쓰림·소화불량", ["famotidine", "antacid"]),
}
PAIN_SYMPTOMS = {"pain_fever", "menstrual", "sore_throat"}

# 구매처 정보: (구분, 안내). 구분 'both'=약국 + (일부 제품) 편의점 안전상비의약품, 'pharmacy'=약국
# ※ 편의점 판매 품목(안전상비의약품)은 2012년 13개로 지정된 뒤 거의 변동이 없으나 확대 논의가 진행 중이므로,
#    구매 전 제품 포장의 '안전상비의약품' 표시 또는 약사 확인이 필요합니다.
AVAILABILITY = {
    "apap": ("both", "타이레놀 등 일부 제품은 편의점(안전상비의약품)에서도 판매. 약국에서는 함량·제형 선택 폭이 넓음."),
    "ibuprofen": ("pharmacy", "약국 구매 권장. 편의점 판매 품목은 극히 제한적이라 제품별 확인이 필요."),
    "naproxen": ("pharmacy", "일반의약품·전문의약품 제품이 섞여 있어 약국에서 약사 확인 후 구매."),
    "pseudoephedrine": ("pharmacy", "약국에서 약사 상담 후 구매(단일제 또는 종합감기약 형태)."),
    "chlorpheniramine": ("pharmacy", "단일제보다 종합감기약·알레르기약에 포함된 경우가 많아 약국 상담 권장."),
    "cetirizine": ("pharmacy", "알레르기·비염약은 편의점 판매 품목에 포함되지 않아 약국에서 구매."),
    "dextromethorphan": ("pharmacy", "기침약·종합감기약에 포함. 제품마다 성분이 다르니 포장의 성분표 확인."),
    "guaifenesin": ("pharmacy", "거담제는 약국에서 구매. 가래 기침이면 약사에게 증상을 설명하세요."),
    "famotidine": ("pharmacy", "위산 억제제는 약국에서 구매(편의점 소화제와는 다른 계열)."),
    "antacid": ("both", "일부 제산제·소화제는 편의점에서도 판매. 약국에서는 제품 선택 폭이 넓음."),
}

# 영양제 (슬롯: 하루 중 기본 복용 시점 = (기준, 시간 오프셋))
SUPPS = {
    "iron": dict(
        name="철분제", icon="🩸", tags={"mineral", "iron"}, slot=("wake", 0.25),
        timing="공복 또는 식전(속이 불편하면 식후), 비타민C와 함께",
        moa="헤모글로빈 합성 재료. 2가철(Fe²⁺) 형태로 십이지장에서 흡수.",
        rules={"ulcer": ("warning", "위점막을 자극할 수 있어 위궤양 병력 시 주의.")},
        food={
            "dairy": ("warning", "칼슘·유제품이 철 흡수를 낮춤 — 2시간 이상 간격."),
            "greentea": ("warning", "탄닌이 철과 결합해 흡수를 낮춤."),
            "caffeine": ("warning", "커피의 폴리페놀이 철 흡수를 낮춤."),
        },
    ),
    "calcium": dict(
        name="칼슘제", icon="🦴", tags={"mineral", "calcium"}, slot=("d", 0.5),
        timing="식후(탄산칼슘은 위산이 있어야 흡수↑)",
        moa="뼈·근육·신경 기능에 필요한 무기질.",
        rules={"renal_severe": ("warning", "신기능 저하: 고칼슘혈증 위험 — 의료진 상담.")}, food={},
    ),
    "magnesium": dict(
        name="마그네슘", icon="🌙", tags={"mineral", "magnesium"}, slot=("bed", -0.5),
        timing="취침 전(근육 이완·수면 보조)",
        moa="효소 보조인자, 근육·신경 안정화.",
        rules={
            "renal_severe": ("danger", "중증 신기능 저하: 고마그네슘혈증 위험."),
            "renal_mild": ("warning", "신기능 저하: 축적 주의."),
        }, food={},
    ),
    "omega3": dict(
        name="오메가3", icon="🐟", tags={"omega3"}, slot=("l", 0.25),
        timing="식사 직후(지용성이라 지방과 함께 흡수↑)",
        moa="EPA/DHA — 중성지방 감소, 항염 작용.",
        rules={"med_warfarin": ("warning", "항응고제와 병용 시 출혈 경향 증가 가능.")}, food={},
    ),
    "ginkgo": dict(
        name="은행잎 추출물", icon="🍃", tags={"ginkgo"}, slot=("b", 0.25),
        timing="아침 식후", moa="혈소판 활성화 인자(PAF) 길항으로 혈액순환 개선.",
        rules={
            "med_warfarin": ("warning", "항응고제와 병용 시 출혈 위험↑."),
            "pregnant": ("warning", "임신 중 안전성 근거 부족."),
        }, food={},
    ),
    "vitc": dict(
        name="비타민C", icon="🍊", tags={"vitc"}, slot=("b", 0.25),
        timing="식후(위장 자극 감소)", moa="항산화, 콜라겐 합성 보조, 비헴철 흡수 촉진.",
        rules={"renal_severe": ("warning", "고용량 시 옥살산 결석 위험.")}, food={},
    ),
    "probiotic": dict(
        name="유산균", icon="🦠", tags={"probiotic"}, slot=("l", 0.5),
        timing="식후(제품 지침 우선), 항생제와는 2시간 이상 간격", moa="장내 미생물 균형 보조.",
        rules={}, food={},
    ),
}

FOODS = {
    "alcohol": "🍺 음주", "grapefruit": "🍊 자몽(주스)", "caffeine": "☕ 커피·에너지드링크",
    "dairy": "🥛 우유·유제품", "greentea": "🍵 녹차·홍차",
}
CONDITIONS = {
    "htn": "고혈압", "heart": "심장질환", "diabetes": "당뇨", "ulcer": "위궤양/위장관 출혈 병력",
    "asthma": "천식", "glaucoma_bph": "녹내장·전립선비대", "thyroid": "갑상선 질환",
}
CHRONIC_MEDS = {
    "med_warfarin": "와파린(항응고제)", "med_ssri": "SSRI 계열 항우울제", "med_maoi": "MAO 억제제",
    "med_bp": "혈압약(ACEi/ARB/이뇨제)", "med_steroid": "스테로이드제",
}
ALLERGIES = {
    "allergy_nsaid": "아스피린/NSAIDs", "allergy_apap": "아세트아미노펜", "allergy_antihist": "항히스타민제",
}

# 약물-약물/영양제 상호작용 규칙표.  a,b 는 '약물 id' 또는 '태그'. gap = 필요한 복용 간격(시간)
INTERACTIONS = [
    dict(a="nsaid", b="nsaid", sev="danger", text="NSAIDs 2종 이상 중복: 효과는 늘지 않고 위장관 출혈·신독성만 증가."),
    dict(a="apap", b="nsaid", sev="safe", text="작용 기전이 달라 병용·교차 복용 가능(시너지). 각 성분의 1일 최대 횟수는 반드시 준수."),
    dict(a="antihistamine", b="antihistamine", sev="danger", text="항히스타민제 중복: 졸림·구갈·요저류 등 항콜린 부작용 가중."),
    dict(a="pseudoephedrine", b="chlorpheniramine", sev="safe", text="종합감기약의 전형적 조합(코막힘+콧물). 졸림/불면은 서로 일부 상쇄되나 개인차."),
    dict(a="dextromethorphan", b="sedating", sev="warning", text="중추억제(졸림·어지러움) 가중 — 운전·위험작업 금지."),
    dict(a="dextromethorphan", b="guaifenesin", sev="warning", text="기침 억제(진해)와 가래 배출(거담)은 목적이 상충. 가래 기침이면 거담제 위주로."),
    dict(a="famotidine", b="antacid", sev="safe", text="위산 억제(느리고 지속) + 중화(빠르고 짧음): 속쓰림 보조 병용 가능."),
    dict(a="nsaid", b="famotidine", sev="safe", text="위 불편감 완화 목적의 보조 병용 가능(위험군은 위장 보호제 처방 상담)."),
    dict(a="nsaid", b="ginkgo", sev="warning", text="항혈소판 작용이 겹쳐 출혈 경향 증가 가능."),
    dict(a="nsaid", b="omega3", sev="warning", text="출혈 경향이 소폭 증가할 수 있음."),
    dict(a="antacid", b="iron", sev="warning", gap=2, text="제산제가 철과 결합·위산 중화로 철 흡수 감소 → 2시간 이상 간격."),
    dict(a="calcium", b="iron", sev="warning", gap=2, text="칼슘과 철은 장에서 흡수 경쟁 → 2시간 이상 간격."),
    dict(a="magnesium", b="iron", sev="warning", gap=2, text="마그네슘과 철은 흡수 경쟁 → 2시간 이상 간격."),
    dict(a="pseudoephedrine", b="antacid", sev="warning", text="제산제가 소변을 알칼리화해 슈도에페드린 배설이 감소 → 작용 지속·부작용↑ 가능."),
    dict(a="iron", b="vitc", sev="safe", text="비타민C가 비헴철 흡수를 촉진 — 함께 복용 권장."),
]

MEAL_TXT = {"after": "식후 30분 이내", "any": "식사와 무관(속이 불편하면 식후)", "before": "식전 30분"}


# ------------------------------------------------------------------------------------------
# 3. 분석 엔진
# ------------------------------------------------------------------------------------------
def build_flags(p: dict) -> set:
    """환자 프로파일 → 플래그 집합. 이후 모든 규칙은 이 '플래그'와 교집합으로 평가된다."""
    f = set()
    age = p["age"]
    if age < 2:
        f.add("age_infant")
    elif age < 12:
        f.add("age_child")
    if age >= 65:
        f.add("age_elder")
    if p["pregnant"]:
        f.add("pregnant")
    if p["lactating"]:
        f.add("lactating")
    # 신장: eGFR 기준 (>=60 정상 / 30~59 경도·중등도 저하 / <30 중증)
    egfr = None if p["egfr_unknown"] else p["egfr"]
    if egfr is not None:
        if egfr < 30:
            f.add("renal_severe")
        elif egfr < 60:
            f.add("renal_mild")
    # 간: AST/ALT 상한 대비 배수 기준
    if p["hepatic"] == "경도 이상 (AST·ALT 정상 상한의 3배 미만)":
        f.add("hepatic_mild")
    elif p["hepatic"] == "중증 이상 (3배 이상 / 간경변·황달)":
        f.add("hepatic_severe")
    f.update(p["conditions"])
    f.update(p["chronic_meds"])
    f.update(p["allergies"])
    return f


def allergy_hit(did: str, text: str) -> bool:
    """자유 입력 알레르기 문자열이 약물 이름/별칭과 겹치는지 검사(2글자 이상)."""
    toks = [t.strip().lower() for t in re.split(r"[,/·\n]", text or "") if len(t.strip()) >= 2]
    d = DRUGS[did]
    names = [a.lower() for a in d["aliases"]] + [d["name"].lower()]
    return any(t in n or n in t for t in toks for n in names)


def grade_of(findings: list) -> str:
    return max((f["sev"] for f in findings), key=lambda s: RANK[s], default="safe")


def evaluate_drug(did: str, flags: set, foods: set, profile: dict) -> list:
    """약물 1개에 대해 [환자요인 + 알레르기 + 연령 + 음식] 위험을 모두 모아 리스트로 반환."""
    d, out = DRUGS[did], []
    for flag, (sev, txt) in d["rules"].items():
        if flag in flags:
            out.append(dict(sev=sev, cat="환자 요인", text=txt))
    if allergy_hit(did, profile.get("allergy_text", "")):
        out.append(dict(sev="danger", cat="알레르기", text="입력하신 알레르기 정보와 이 약물(성분)이 일치합니다."))
    # 같은 계열(NSAIDs·항히스타민) 약물에 알레르기가 있으면 교차 과민반응 가능성으로 금기 처리
    for other, od in DRUGS.items():
        if other != did and (od["tags"] & d["tags"] & {"nsaid", "antihistamine"}) and allergy_hit(other, profile.get("allergy_text", "")):
            out.append(dict(sev="danger", cat="알레르기", text=f"{od['name']} 알레르기 → 같은 계열 약물과 교차 과민반응 가능성."))
    if "age_infant" in flags:
        sev = "danger" if "coldmed" in d["tags"] else "warning"
        out.append(dict(sev=sev, cat="연령", text="만 2세 미만: OTC 감기약은 사용 금지 수준, 해열진통제도 체중 기반 용량이 필수 — 소아과 상담."))
    elif "age_child" in flags and "coldmed" in d["tags"]:
        out.append(dict(sev="warning", cat="연령", text="만 12세 미만: 소아용 제품·체중 기반 용량 확인이 필요."))
    for fk, (sev, txt) in d["food"].items():
        if fk in foods:
            out.append(dict(sev=sev, cat="음식", text=txt))
    return out


def evaluate_supp(sid: str, flags: set, foods: set) -> list:
    s, out = SUPPS[sid], []
    for flag, (sev, txt) in s["rules"].items():
        if flag in flags:
            out.append(dict(sev=sev, cat="환자 요인", text=txt))
    for fk, (sev, txt) in s["food"].items():
        if fk in foods:
            out.append(dict(sev=sev, cat="음식", text=txt))
    return out


def item_name(i: str) -> str:
    return DRUGS[i]["name"] if i in DRUGS else SUPPS[i]["name"]


def tokens(i: str) -> set:
    """아이템 id + 태그 → 규칙 매칭용 토큰 집합"""
    return {i} | (DRUGS[i]["tags"] if i in DRUGS else SUPPS[i]["tags"])


def analyze_interactions(ids: list) -> list:
    """모든 2개 조합(nC2)에 대해 INTERACTIONS 규칙표와 매칭."""
    out = []
    for x, y in itertools.combinations(ids, 2):
        tx, ty = tokens(x), tokens(y)
        for r in INTERACTIONS:
            if (r["a"] in tx and r["b"] in ty) or (r["a"] in ty and r["b"] in tx):
                out.append(dict(sev=r["sev"], text=r["text"], pair=(x, y), gap=r.get("gap")))
    return out


def adjusted_pk(did: str, flags: set) -> dict:
    """
    [PK 보정 모델] 제거 경로(신장/간)에 맞춰 반감기를 보정 → 복용 간격 연장.
      t½_adj = t½ × k,  interval_adj = ceil(interval × k × 2)/2 (0.5시간 단위, 최대 24시간)
      k : 신장 경도 1.5 / 중증 3.0,  간 경도 1.5 / 중증 2.5,  고령 1.2 (해당 제거경로에만 적용)
    ※ 교육용 단순 모델이며, 실제 용량 조절은 약사·의사의 영역입니다.
    """
    d, k, why = DRUGS[did], 1.0, []
    if d["clearance"] in ("renal", "mixed"):
        if "renal_severe" in flags:
            k *= 3.0; why.append("중증 신기능 저하 ×3.0")
        elif "renal_mild" in flags:
            k *= 1.5; why.append("신기능 저하 ×1.5")
    if d["clearance"] in ("hepatic", "mixed"):
        if "hepatic_severe" in flags:
            k *= 2.5; why.append("중증 간기능 이상 ×2.5")
        elif "hepatic_mild" in flags:
            k *= 1.5; why.append("간기능 이상 ×1.5")
    if "age_elder" in flags:
        k *= 1.2; why.append("고령 ×1.2")
    interval_adj = min(24.0, math.ceil(d["interval"] * k * 2) / 2)
    return dict(
        k=k, why=why, t_half_adj=d["t_half"] * k, interval_adj=interval_adj,
        max_doses=max(1, min(d["max_doses"], int(24 // interval_adj))),
        residual=0.5 ** (interval_adj / (d["t_half"] * k)),            # 다음 복용 직전 잔존율
        accumulation=1 / (1 - 0.5 ** (interval_adj / (d["t_half"] * k))),  # 정상상태 축적계수 R
    )


def run_analysis(p: dict) -> dict:
    """
    ★ 종합 분석 파이프라인 ★
      1) 플래그화 → 2) 증상별 후보 평가 → 3) 금기 제외·최적 후보 선택 → 4) 시너지/위장보호 보강
      → 5) PK 보정 → 6) 약물·영양제·현재복용약 상호작용 → 7) PARS 점수
    """
    flags, foods = build_flags(p), set(p["foods"])
    plan, evals, no_option = {}, {}, []   # plan: id -> dict(role, symptoms)

    # 2~3) 증상별 후보 평가 및 선택
    for sk in p["symptoms"]:
        label, cands = SYMPTOMS[sk]
        ev = []
        for order, cid in enumerate(cands):
            fs = evaluate_drug(cid, flags, foods, p)
            ev.append(dict(id=cid, grade=grade_of(fs), findings=fs, order=order,
                           warns=sum(1 for x in fs if x["sev"] == "warning")))
        evals[sk] = ev
        ok = [e for e in ev if e["grade"] != "danger"]
        if not ok:
            no_option.append(label)
            continue
        best = min(ok, key=lambda e: (RANK[e["grade"]], e["warns"], e["order"]))
        if best["id"] in plan:
            plan[best["id"]]["symptoms"].append(label)
        else:
            plan[best["id"]] = dict(role="메인약" if not plan else "증상 대응약", symptoms=[label])

    # 4-a) 시너지약: 통증 계열에서 '완전히 안전(Safe)'한 보완 성분이 있으면 교차 복용 제안
    if p["opt_synergy"] and set(p["symptoms"]) & PAIN_SYMPTOMS:
        has_apap, has_nsaid = "apap" in plan, any("nsaid" in DRUGS[i]["tags"] for i in plan)
        partner = None
        if has_nsaid and not has_apap:
            partner = "apap"
        elif has_apap and not has_nsaid:
            partner = "ibuprofen"
        if partner and grade_of(evaluate_drug(partner, flags, foods, p)) == "safe":
            plan[partner] = dict(role="시너지약", symptoms=["통증·발열 교차 복용(시너지)"])

    # 4-b) 위장 보호약: NSAID + 위장관 위험요인(고령/스테로이드/위장 불편)
    if p["opt_gi"] and any("nsaid" in DRUGS[i]["tags"] for i in plan) and not any("gi" in DRUGS[i]["tags"] for i in plan):
        if flags & {"age_elder", "med_steroid"}:
            for gid in ("famotidine", "antacid"):
                if grade_of(evaluate_drug(gid, flags, foods, p)) != "danger":
                    plan[gid] = dict(role="위장 보호약", symptoms=["NSAIDs 위장 부담 완화"])
                    break

    # 현재 복용 중인 OTC와 같은 성분이면 '중복' 금기 처리
    duplicates = [i for i in plan if i in p["current_otc"]]

    # 5) 플랜 상세 구성 (PK 보정 포함)
    items = []
    for did, meta in plan.items():
        fs = evaluate_drug(did, flags, foods, p)
        if did in duplicates:
            fs.append(dict(sev="danger", cat="성분 중복", text="이미 복용 중인 약과 동일 성분입니다. 이중 복용 금지."))
        items.append(dict(id=did, role=meta["role"], symptoms=meta["symptoms"], findings=fs,
                          grade=grade_of(fs), pk=adjusted_pk(did, flags)))

    # 제외된 약물(금기)
    excluded, seen = [], set()
    for sk, ev in evals.items():
        for e in ev:
            if e["grade"] == "danger" and e["id"] not in seen:
                seen.add(e["id"])
                excluded.append(dict(id=e["id"], findings=[f for f in e["findings"] if f["sev"] == "danger"]))

    # 영양제 평가
    supp_items = [dict(id=s, findings=evaluate_supp(s, flags, foods), grade=grade_of(evaluate_supp(s, flags, foods)))
                  for s in p["supps"]]

    # 6) 상호작용 (플랜 + 현재복용 + 영양제)
    all_ids = list(dict.fromkeys([i["id"] for i in items] + list(p["current_otc"]) + list(p["supps"])))
    inter = analyze_interactions(all_ids)

    # 7) PARS 점수: 100 - (금기×30 + 주의×8). Safe 정보는 감점 없음
    all_f = [f for it in items for f in it["findings"]] + [f for s in supp_items for f in s["findings"]] + inter
    n_d = sum(1 for f in all_f if f["sev"] == "danger")
    n_w = sum(1 for f in all_f if f["sev"] == "warning")
    n_s = sum(1 for f in all_f if f["sev"] == "safe")
    score = max(0, 100 - n_d * 30 - n_w * 8)

    return dict(profile=p, flags=sorted(flags), items=items, excluded=excluded, no_option=no_option,
                supps=supp_items, inter=inter, evals=evals, score=score,
                counts=dict(danger=n_d, warning=n_w, safe=n_s), duplicates=duplicates,
                created=dt.datetime.now().strftime("%Y-%m-%d %H:%M"))


# ---------------------- 스케줄러 ----------------------
def fmt_time(h: float) -> str:
    m = int(round(h * 60)) % 1440
    return f"{m // 60:02d}:{m % 60:02d}"


def to_hour(t: dt.time) -> float:
    return t.hour + t.minute / 60


def build_schedule(result: dict, prefs: dict):
    """
    [복약 스케줄링 알고리즘]
     1) 약물별 첫 복용 시각에서 PK 보정 간격(interval_adj)으로 복용 시각 생성 (취침 직전·최대 횟수 제한)
     2) 식후 복용 약은 가장 가까운 '식사+30분'으로 스냅(최소 간격이 깨지지 않을 때만)
     3) 시너지(교차) 복용: NSAID를 아세트아미노펜 간격의 절반만큼 어긋나게 배치
     4) 영양제는 고정 슬롯에 배치
     5) 킬레이트 규칙(gap) 위반 시 '이동 가능한 쪽'을 30분 단위로 밀어 간격 확보
    """
    wake, bed = prefs["wake"], prefs["bed"]
    if bed <= wake:
        bed += 24
    meals = {"b": prefs["b"], "l": prefs["l"], "d": prefs["d"]}
    anchors = {"wake": wake, "bed": bed, **meals}
    sched, notes = {}, []
    ids = [i["id"] for i in result["items"]]
    pk = {i["id"]: i["pk"] for i in result["items"]}

    for did in ids:
        d = DRUGS[did]
        offset = 0.0
        if prefs["alternate"] and "nsaid" in d["tags"] and "apap" in ids:
            offset = DRUGS["apap"]["interval"] / 2
        t, doses = prefs["start"] + offset, []
        limit = bed - d.get("last_before_bed", 0.25)
        while t <= limit and len(doses) < pk[did]["max_doses"]:
            doses.append(t)
            t += pk[did]["interval_adj"]
        if not doses:
            doses = [min(prefs["start"], limit)]
        # 식후 스냅
        if d["meal"] == "after":
            snapped = []
            for x in doses:
                cand = min((m + 0.5 for m in meals.values()), key=lambda c: abs(c - x))
                y = cand if abs(cand - x) <= 1.0 else x
                if snapped and y - snapped[-1] < pk[did]["interval_adj"] * 0.75:
                    y = x
                snapped.append(y)
            doses = snapped
        sched[did] = doses

    for s in [x["id"] for x in result["supps"]]:
        anchor, off = SUPPS[s]["slot"]
        sched[s] = [anchors[anchor] + off]

    # 5) 간격 확보
    pairs = [x for x in result["inter"] if x["gap"] and x["pair"][0] in sched and x["pair"][1] in sched]
    for x in pairs:
        a, b = x["pair"]
        mover = b if (b in SUPPS or DRUGS.get(b, {}).get("movable")) else a
        fixed = a if mover == b else b
        for idx, t in enumerate(sched[mover]):
            def ok(v):
                return all(abs(v - u) >= x["gap"] for u in sched[fixed]) and wake <= v <= bed
            if ok(t):
                continue
            for step in range(1, 25):
                moved = next((c for c in (t + 0.5 * step, t - 0.5 * step) if ok(c)), None)
                if moved is not None:
                    notes.append(f"{item_name(mover)} → {item_name(fixed)}와(과) {x['gap']}시간 간격 확보를 위해 "
                                 f"{fmt_time(t)} → {fmt_time(moved)} 로 조정")
                    sched[mover][idx] = moved
                    break
    return sched, notes, wake, bed


def solve_ka(ke: float, tmax: float) -> float:
    """1구획 1차 흡수 모델에서 Tmax가 주어졌을 때 흡수속도상수 ka를 이분법으로 계산."""
    f = lambda ka: math.log(ka / ke) / (ka - ke) - tmax
    lo, hi = ke * 1.0001, 80.0
    if f(lo) <= 0:
        return ke * 6
    for _ in range(60):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if f(mid) > 0 else (lo, mid)
    return (lo + hi) / 2


def pk_curve(did: str, doses: list, t_half: float, grid: list) -> list:
    """Bateman 식: C(t)=ka/(ka-ke)·(e^{-ke t} - e^{-ka t}). 1회 복용 최고치=100%로 정규화 후 중첩(superposition)."""
    ke, tmax = math.log(2) / t_half, DRUGS[did]["tmax"]
    ka = solve_ka(ke, tmax)
    one = lambda t: 0.0 if t < 0 else ka / (ka - ke) * (math.exp(-ke * t) - math.exp(-ka * t))
    peak = one(tmax)
    return [100 * sum(one(t - d0) for d0 in doses) / peak for t in grid]


# ------------------------------------------------------------------------------------------
# 4. UI 헬퍼
# ------------------------------------------------------------------------------------------
def html(s: str):
    st.markdown(s, unsafe_allow_html=True)


def badge(sev: str) -> str:
    ko, en, ic = SEV[sev]
    return f'<span class="badge badge-{sev}">{ic} {ko} · {en}</span>'


def finding_html(f: dict, title: str = "") -> str:
    ttl = f"<b>{title}</b>" if title else ""
    return (f'<div class="finding {f["sev"]}">{badge(f["sev"])}{ttl}'
            f'<span class="cat">{f.get("cat", "")}</span><div>{f["text"]}</div></div>')


def html_table(headers, rows) -> str:
    th = "".join(f"<th>{h}</th>" for h in headers)
    trs = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows)
    return f'<div class="tbl-wrap"><table class="tl"><thead><tr>{th}</tr></thead><tbody>{trs}</tbody></table></div>'


def glass(title: str, body: str, icon: str = "") -> str:
    return f'<div class="glass"><h4>{icon} {title}</h4><p>{body}</p></div>'


def go(page: str):
    """버튼 on_click 콜백: 사이드바 라디오의 key('nav')를 바꿔 페이지를 이동."""
    st.session_state["nav"] = page


PAGES = ["🏠 대시보드", "🩺 스마트 문진 · DUR 진단", "⏰ 복약 타임라인", "📷 AI 처방전 스캐너"]

DEFAULT_PROFILE = dict(
    age=25, sex="여성", pregnant=False, lactating=False, egfr=90, egfr_unknown=True,
    hepatic="정상", conditions=[], chronic_meds=[], allergies=[], allergy_text="",
    symptoms=[], current_otc=[], supps=[], foods=[], opt_synergy=True, opt_gi=True,
)


def init_state():
    st.session_state.setdefault("nav", PAGES[0])
    st.session_state.setdefault("step", 1)
    st.session_state.setdefault("profile", dict(DEFAULT_PROFILE))
    st.session_state.setdefault("result", None)
    st.session_state.setdefault("scan", None)
    st.session_state.setdefault("api_key", "")


# ------------------------------------------------------------------------------------------
# 5-A. 대시보드
# ------------------------------------------------------------------------------------------
def page_dashboard():
    html("""
<div class="hero">
<span class="tag">🌿 20901 강은유 · 의생명과학 × 간호학 진로 프로젝트</span>
<h1>SmartMed DUR<br>나에게 맞는 OTC 조합, 먹는 시간까지</h1>
<p>나이·임신·신장/간 기능·알레르기까지 반영해 약의 위험도를 <b>금기·주의·병용가능</b>으로 분류하고,
반감기(PK)를 바탕으로 <b>몇 시간 간격으로 먹어야 안전한지</b> 24시간 복약표로 만들어 줍니다.</p>
</div>""")
    c1, c2, c3 = st.columns(3)
    c1.button("🩺 문진 시작하기", on_click=go, args=(PAGES[1],), key="cta1")
    c2.button("⏰ 복약 타임라인 보기", on_click=go, args=(PAGES[2],), key="cta2")
    c3.button("📷 처방전 스캔하기", on_click=go, args=(PAGES[3],), key="cta3")

    st.markdown("### 💡 이 앱의 기술적 차별점")
    a, b, c = st.columns(3)
    a.markdown(glass("환자 보정 안전 점수(PARS)",
                     "처방 조합 전체를 금기·주의 개수로 0~100점 환산. 같은 증상이라도 환자 프로파일에 따라 점수가 달라집니다.", "🛡️"),
               unsafe_allow_html=True)
    b.markdown(glass("PK 보정 복용 간격",
                     "신장·간 기능, 고령에 따라 반감기를 보정해 복용 간격을 자동 연장하고, 다음 복용 직전 잔존율·축적계수를 계산합니다.", "🧬"),
               unsafe_allow_html=True)
    c.markdown(glass("5축 DUR 통합 분석",
                     "약물-환자 · 약물-약물 · 약물-영양제 · 약물-음식 · 성분 중복을 하나의 규칙 엔진에서 동시에 평가합니다.", "🧩"),
               unsafe_allow_html=True)

    st.markdown("### 🔬 분석 파이프라인")
    html(html_table(
        ["① 프로파일링", "② 플래그화", "③ 규칙 엔진", "④ PK 보정", "⑤ 스케줄러", "⑥ AI 리포트"],
        [["나이·임신·eGFR·간수치·알레르기", "조건을 집합(Set)으로 변환", "금기/주의/안전 등급 산출", "t½·간격 자동 보정",
          "식사·킬레이트 간격 반영", "요약 + Gemini 쉬운 설명"]]))

    st.write("")
    t1, t2, t3 = st.tabs(["🎯 프로젝트 목표", "🧪 사용 기술", "⚖️ 한계와 윤리"])
    with t1:
        st.markdown("""
- **문제 인식**: OTC는 접근성이 높지만 성분 중복·환자 특성 무시·복용 간격 오류로 약물 이상반응이 발생합니다.
- **목표**: 환자 맞춤 약물 조합과 복약 시간표를 근거(작용 기전·반감기)와 함께 제시해 **안전한 자가 투약 교육**을 돕습니다.
- **간호학적 가치**: 복약 순응도 향상, 투약 5원칙(환자·약물·용량·경로·시간) 중 *시간*과 *환자 특성*을 시각화합니다.
""")
    with t2:
        st.markdown("""
- **Frontend/UX**: Streamlit, 커스텀 CSS(글래스모피즘), `st.session_state` 기반 페이지 이동, 단계별 `st.form`
- **Algorithm**: 규칙 기반 DUR 엔진 + 1구획 약동학(Bateman 식) + 제약 기반 스케줄러
- **AI**: Gemini Vision(처방전 OCR → 구조화 JSON) + 로컬 DUR 교차검증
""")
    with t3:
        st.warning("본 앱의 약물 DB는 교육용 요약본이며, 의료기기·진단 도구가 아닙니다. 모든 결과는 의사·약사 확인이 필요합니다. "
                   "특허 출원을 고려한다면 KIPRIS 등에서 선행기술조사와 변리사 상담이 먼저 필요합니다.")
    html('<div class="footer-note">© 2026 강은유(20901) · SmartMed DUR · 교육용 프로토타입</div>')


# ------------------------------------------------------------------------------------------
# 5-B. 스마트 문진 + DUR 진단
# ------------------------------------------------------------------------------------------
def step_header(step: int):
    names = ["기본 정보", "건강 상태", "증상·복용 습관", "AI 리포트"]
    st.progress(step / 4, text=f"STEP {step}/4 · {names[step - 1]}")


def form_step1(p):
    with st.form("form_step1"):
        c1, c2 = st.columns(2)
        age = c1.number_input("나이 (만)", 0, 110, int(p["age"]))
        sex = c2.radio("생물학적 성별", ["여성", "남성"], index=0 if p["sex"] == "여성" else 1, horizontal=True)
        st.caption("아래 항목은 여성에게만 적용됩니다.")
        c3, c4 = st.columns(2)
        preg = c3.checkbox("🤰 임신 중 / 임신 가능성", value=p["pregnant"])
        lact = c4.checkbox("🍼 수유 중", value=p["lactating"])
        if st.form_submit_button("다음 단계 ▶"):
            p.update(age=int(age), sex=sex, pregnant=preg and sex == "여성", lactating=lact and sex == "여성")
            st.session_state.step = 2
            st.rerun()


def form_step2(p):
    hepatic_opts = ["정상", "경도 이상 (AST·ALT 정상 상한의 3배 미만)", "중증 이상 (3배 이상 / 간경변·황달)"]
    with st.form("form_step2"):
        st.markdown("##### 🫘 신장 · 🫀 간 기능")
        c1, c2 = st.columns(2)
        unknown = c1.checkbox("eGFR 수치를 모릅니다 (정상으로 가정)", value=p["egfr_unknown"])
        egfr = c1.number_input("eGFR (mL/min/1.73㎡)", 5, 150, int(p["egfr"]),
                               help="≥60 정상 / 30~59 저하 / <30 중증 저하")
        hepatic = c2.selectbox("간 기능 (AST·ALT)", hepatic_opts, index=hepatic_opts.index(p["hepatic"]))
        st.markdown("##### 🏥 기저질환 · 복용 중인 약 · 알레르기")
        cond = st.multiselect("기저질환", list(CONDITIONS), default=p["conditions"], format_func=CONDITIONS.get)
        meds = st.multiselect("복용 중인 처방약", list(CHRONIC_MEDS), default=p["chronic_meds"], format_func=CHRONIC_MEDS.get)
        alg = st.multiselect("알려진 약물 알레르기", list(ALLERGIES), default=p["allergies"], format_func=ALLERGIES.get)
        alg_txt = st.text_input("그 외 알레르기 (쉼표로 구분)", value=p["allergy_text"], placeholder="예: 이부프로펜, 세티리진")
        if st.form_submit_button("다음 단계 ▶"):
            p.update(egfr_unknown=unknown, egfr=int(egfr), hepatic=hepatic, conditions=cond,
                     chronic_meds=meds, allergies=alg, allergy_text=alg_txt)
            st.session_state.step = 3
            st.rerun()


def form_step3(p):
    with st.form("form_step3"):
        sym = st.multiselect("현재 증상 (복수 선택)", list(SYMPTOMS), default=p["symptoms"],
                             format_func=lambda k: SYMPTOMS[k][0])
        cur = st.multiselect("이미 복용 중인 OTC (성분 중복 검사)", list(DRUGS), default=p["current_otc"],
                             format_func=lambda k: f"{DRUGS[k]['name']} ({DRUGS[k]['brand']})")
        sup = st.multiselect("복용 중인 영양제", list(SUPPS), default=p["supps"],
                             format_func=lambda k: f"{SUPPS[k]['icon']} {SUPPS[k]['name']}")
        fd = st.multiselect("자주 섭취하는 음식·기호식품", list(FOODS), default=p["foods"], format_func=FOODS.get)
        c1, c2 = st.columns(2)
        o1 = c1.checkbox("🤝 시너지(교차 복용) 약 제안 허용", value=p["opt_synergy"])
        o2 = c2.checkbox("🛡️ 위장 보호약 제안 허용", value=p["opt_gi"])
        if st.form_submit_button("🔬 AI DUR 분석 시작"):
            if not sym:
                st.error("증상을 한 개 이상 선택해 주세요.")
            else:
                p.update(symptoms=sym, current_otc=cur, supps=sup, foods=fd, opt_synergy=o1, opt_gi=o2)
                st.session_state.result = None
                st.session_state.step = 4
                st.rerun()


def gemini_models():
    # 1.5 Flash가 종료된 환경을 대비해 순서대로 시도(예비 모델)
    return ["gemini-1.5-flash", "gemini-2.0-flash", "gemini-2.5-flash"]


def get_api_key():
    if st.session_state.get("api_key"):
        return st.session_state["api_key"]
    try:
        return st.secrets.get("GEMINI_API_KEY", "")
    except Exception:
        return ""


def gemini_text(prompt: str) -> str:
    key = get_api_key()
    if not key or genai is None:
        raise RuntimeError("Gemini API 키가 없거나 google-generativeai가 설치되지 않았습니다.")
    genai.configure(api_key=key)
    last = None
    for name in gemini_models():
        try:
            return genai.GenerativeModel(name).generate_content(prompt).text
        except Exception as e:  # 모델 종료/한도 등 → 다음 모델 시도
            last = e
    raise RuntimeError(f"모든 모델 호출 실패: {last}")


def rule_summary(r: dict) -> str:
    """Gemini 없이도 항상 제공되는 규칙 기반 요약문."""
    names = ", ".join(f"{DRUGS[i['id']]['name']}({i['role']})" for i in r["items"]) or "추천 가능한 약 없음"
    s = f"선택된 조합: {names}. PARS 안전 점수는 {r['score']}점이며 금기 {r['counts']['danger']}건, 주의 {r['counts']['warning']}건이 확인되었습니다."
    if r["excluded"]:
        s += " 금기로 제외된 약: " + ", ".join(DRUGS[e["id"]]["name"] for e in r["excluded"]) + "."
    if r["no_option"]:
        s += " 자가 복용 후보가 없는 증상: " + ", ".join(r["no_option"]) + " → 의료진 진료를 권장합니다."
    return s


def score_style(score: int):
    if score >= 85:
        return "#2f9e6b", "안정적인 조합"
    if score >= 60:
        return "#d9822b", "주의가 필요한 조합"
    return "#d64545", "고위험 조합 · 전문가 상담 필수"


def pharmacist_script(r: dict) -> str:
    """약국에서 그대로 읽어줄 수 있는 '약사 상담 메모'를 프로파일에서 자동 생성."""
    p, parts = r["profile"], []
    parts.append(f"나이: 만 {p['age']}세 / 성별: {p['sex']}")
    if p["pregnant"]:
        parts.append("임신 중(또는 가능성 있음)")
    if p["lactating"]:
        parts.append("수유 중")
    if p["conditions"]:
        parts.append("기저질환: " + ", ".join(CONDITIONS[c] for c in p["conditions"]))
    if "renal_mild" in r["flags"] or "renal_severe" in r["flags"]:
        parts.append("신장 기능 저하")
    if "hepatic_mild" in r["flags"] or "hepatic_severe" in r["flags"]:
        parts.append("간 기능 이상")
    if p["chronic_meds"]:
        parts.append("복용 중인 약: " + ", ".join(CHRONIC_MEDS[c] for c in p["chronic_meds"]))
    if p["current_otc"]:
        parts.append("이미 복용 중인 OTC: " + ", ".join(DRUGS[c]["name"] for c in p["current_otc"]))
    if p["supps"]:
        parts.append("영양제: " + ", ".join(SUPPS[c]["name"] for c in p["supps"]))
    allergy = [ALLERGIES[a] for a in p["allergies"]] + ([p["allergy_text"]] if p["allergy_text"] else [])
    parts.append("알레르기: " + (", ".join(allergy) if allergy else "없음"))
    want = ", ".join(DRUGS[i["id"]]["name"] for i in r["items"]) or "-"
    parts.append(f"찾는 성분: {want}")
    return "\n".join(parts)


def render_buy_tab(r: dict):
    """추천된 약을 어디서 구할 수 있는지: 구매처 안내 + 지도 바로가기 + 약사 상담 메모."""
    if not r["items"]:
        st.info("추천된 약이 없어 구매처 안내를 생략합니다. 의료진 진료를 먼저 받으세요.")
        return
    rows = []
    for it in r["items"]:
        d = DRUGS[it["id"]]
        kind, desc = AVAILABILITY[it["id"]]
        where = "🏥 약국 + 🏪 일부 편의점" if kind == "both" else "🏥 약국"
        rows.append([f"{d['icon']} {d['name']}", d["brand"], f'<span class="badge badge-info">{where}</span>', desc])
    html(html_table(["성분", "대표 제품", "구매처", "안내"], rows))
    st.caption("※ 편의점 판매 가능 품목(안전상비의약품)은 제도상 제한되어 있고 변경될 수 있어요. 제품 포장 표시나 약사에게 확인하세요.")

    st.markdown("##### 📍 내 주변 약국 찾기")
    area = st.text_input("지역 (선택)", key="buy_area", placeholder="예: 수원시 영통구 (비워두면 현재 위치 기준)")
    q = quote(f"{area.strip()} 약국".strip() if area else "약국")
    c1, c2, c3 = st.columns(3)
    c1.link_button("🗺️ 네이버 지도", f"https://map.naver.com/p/search/{q}")
    c2.link_button("🗺️ 카카오맵", f"https://map.kakao.com/?q={q}")
    c3.link_button("🗺️ 구글 지도", f"https://www.google.com/maps/search/?api=1&query={q}")
    c4, c5 = st.columns(2)
    c4.link_button("🌙 심야·휴일 약국 (응급의료포털)", "https://www.e-gen.or.kr")
    c5.link_button("🔎 제품 정보 (의약품안전나라)", "https://nedrug.mfds.go.kr")

    st.markdown("##### 💬 약사에게 이렇게 말해 보세요")
    st.caption("아래 메모를 보여주거나 읽어 주면 약사가 내 상황에 맞는 제품·용량을 확인해 줍니다. (오른쪽 위 아이콘으로 복사)")
    st.code(pharmacist_script(r), language=None)


def render_result(r: dict):
    color, label = score_style(r["score"])
    c1, c2 = st.columns([1, 2])
    c1.markdown(f'<div class="glass score-ring"><div class="score-num" style="color:{color}">{r["score"]}</div>'
                f'<div class="score-lab">PARS 안전 점수 · {label}</div></div>', unsafe_allow_html=True)
    with c2:
        k1, k2, k3 = st.columns(3)
        for col, key, ic in ((k1, "danger", "🔴"), (k2, "warning", "🟠"), (k3, "safe", "🟢")):
            col.markdown(f'<div class="glass kpi"><div class="n">{r["counts"][key]}</div>'
                         f'<div class="l">{ic} {SEV[key][0]} · {SEV[key][1]}</div></div>', unsafe_allow_html=True)
        st.info(rule_summary(r))

    tabs = st.tabs(["💊 추천 약물", "🛒 구매처", "⚠️ DUR 상세", "🥗 영양제·음식", "🧠 PK/PD", "🤖 쉬운 설명"])

    with tabs[0]:
        if not r["items"]:
            st.warning("현재 프로파일에서는 자가 복용을 권할 수 있는 OTC 후보가 없습니다. 의료진 진료를 받으세요.")
        cols = st.columns(2)
        for n, it in enumerate(r["items"]):
            d = DRUGS[it["id"]]
            with cols[n % 2]:
                html(f'<div class="glass"><span class="badge badge-info">{it["role"]}</span>{badge(it["grade"])}'
                     f'<h4 style="margin-top:.5rem">{d["icon"]} {d["name"]}</h4>'
                     f'<p><b>{d["cls"]}</b> · {d["brand"]}<br>대상 증상: {", ".join(it["symptoms"])}</p></div>')
                with st.expander("작용 기전 · 복용 포인트"):
                    st.markdown(f"**작용 기전(MoA)**: {d['moa']}")
                    st.markdown(f"**복용 방법**: {MEAL_TXT[d['meal']]} · 보정 간격 **{it['pk']['interval_adj']:g}시간** "
                                f"(최대 하루 {it['pk']['max_doses']}회)")
                    st.markdown(f"💡 {d['note']}")
        if r["excluded"]:
            st.markdown("##### 🚫 금기로 후보에서 제외된 약물 (왜 안 되는지)")
            for e in r["excluded"]:
                for f in e["findings"]:
                    html(finding_html(f, DRUGS[e["id"]]["name"]))

    with tabs[1]:
        render_buy_tab(r)

    with tabs[2]:
        for it in r["items"]:
            fs = [f for f in it["findings"] if f["cat"] != "음식"]
            if fs:
                st.markdown(f"**{DRUGS[it['id']]['name']}**")
                for f in sorted(fs, key=lambda x: -RANK[x["sev"]]):
                    html(finding_html(f))
        st.markdown("##### 🔗 약물 간 상호작용")
        if not r["inter"]:
            st.success("확인된 약물 간 상호작용이 없습니다.")
        for x in sorted(r["inter"], key=lambda x: -RANK[x["sev"]]):
            html(finding_html(dict(sev=x["sev"], cat="약물-약물", text=x["text"]),
                              f"{item_name(x['pair'][0])} + {item_name(x['pair'][1])}"))

    with tabs[3]:
        any_ = False
        for it in r["items"]:
            for f in [f for f in it["findings"] if f["cat"] == "음식"]:
                any_ = True
                html(finding_html(f, DRUGS[it["id"]]["name"]))
        for s in r["supps"]:
            html(f'<div class="glass"><h4>{SUPPS[s["id"]]["icon"]} {SUPPS[s["id"]]["name"]}</h4>'
                 f'<p>복용 팁: {SUPPS[s["id"]]["timing"]}</p></div>')
            for f in s["findings"]:
                any_ = True
                html(finding_html(f, SUPPS[s["id"]]["name"]))
        if not any_:
            st.success("선택하신 음식·영양제와 관련된 특이 경고가 없습니다.")

    with tabs[4]:
        rows = []
        for it in r["items"]:
            d, pk = DRUGS[it["id"]], it["pk"]
            rows.append([d["name"], f"{d['t_half']:g}h", f"{pk['t_half_adj']:g}h", f"{d['interval']:g}h",
                         f"<b>{pk['interval_adj']:g}h</b>", f"{pk['residual'] * 100:.0f}%", f"×{pk['accumulation']:.2f}"])
        if rows:
            html(html_table(["약물", "기본 t½", "보정 t½", "기본 간격", "보정 간격", "다음 복용 직전 잔존율", "축적계수 R"], rows))
            st.write("")
            for it in r["items"]:
                pk = it["pk"]
                st.markdown(f"**{DRUGS[it['id']]['name']}** — 보정 근거: {', '.join(pk['why']) or '보정 없음'}")
                st.progress(min(1.0, pk["residual"]), text=f"다음 복용 직전 체내 잔존율 {pk['residual'] * 100:.0f}% (낮을수록 안전)")
            st.caption("잔존율 = 0.5^(간격/t½), 축적계수 R = 1/(1−잔존율). 교육용 1구획 모델이며 실제 용량 조절 기준이 아닙니다.")

    with tabs[5]:
        st.write(rule_summary(r))
        if st.button("🤖 Gemini로 쉬운 설명 생성", key="gem_sum"):
            with st.spinner("Gemini가 설명을 작성하는 중..."):
                try:
                    brief = dict(score=r["score"], plan=[(DRUGS[i["id"]]["name"], i["role"], i["grade"]) for i in r["items"]],
                                 excluded=[DRUGS[e["id"]]["name"] for e in r["excluded"]],
                                 interactions=[x["text"] for x in r["inter"]])
                    st.write(gemini_text("너는 친절한 임상약사야. 아래 DUR 분석 결과를 고등학생도 이해할 쉬운 한국어로 "
                                         "6문장 이내로 설명하고, 마지막에 '의사·약사 확인 필요'를 덧붙여줘.\n"
                                         + json.dumps(brief, ensure_ascii=False)))
                except Exception as e:
                    st.error(f"Gemini 호출 실패: {e}")


def page_diagnosis():
    st.title("🩺 스마트 문진 · DUR 진단")
    step, p = st.session_state.step, st.session_state.profile
    step_header(step)
    if step == 1:
        form_step1(p)
    elif step == 2:
        form_step2(p)
        st.button("◀ 이전", key="b2", on_click=lambda: st.session_state.update(step=1))
    elif step == 3:
        form_step3(p)
        st.button("◀ 이전", key="b3", on_click=lambda: st.session_state.update(step=2))
    else:
        if st.session_state.result is None:
            try:
                with st.status("AI DUR 엔진 분석 중...", expanded=True) as status:
                    st.write("① 환자 프로파일 플래그화"); time.sleep(0.3)
                    st.write("② 증상별 후보 약물 위험도 평가"); time.sleep(0.3)
                    st.write("③ PK 보정 및 약물·영양제·음식 상호작용 검사"); time.sleep(0.3)
                    st.session_state.result = run_analysis(p)
                    st.write("④ PARS 점수 산출"); time.sleep(0.2)
                    status.update(label="분석 완료 ✅", state="complete", expanded=False)
            except Exception as e:
                st.error(f"분석 중 오류가 발생했습니다: {e}")
                st.button("처음으로", on_click=lambda: st.session_state.update(step=1))
                return
        render_result(st.session_state.result)
        c1, c2 = st.columns(2)
        c1.button("⏰ 복약 타임라인 만들기", on_click=go, args=(PAGES[2],), key="to_tl")
        c2.button("🔄 새로 문진하기", key="reset",
                  on_click=lambda: st.session_state.update(step=1, result=None, profile=dict(DEFAULT_PROFILE)))


# ------------------------------------------------------------------------------------------
# 5-C. 복약 타임라인
# ------------------------------------------------------------------------------------------
def page_timeline():
    st.title("⏰ 복약 타임라인")
    r = st.session_state.result
    if not r or not r["items"]:
        st.info("먼저 '스마트 문진 · DUR 진단'을 완료하면 맞춤 복약표가 만들어집니다.")
        st.button("🩺 문진하러 가기", on_click=go, args=(PAGES[1],), key="tl_go")
        return

    with st.expander("🕒 내 생활 리듬 설정", expanded=True):
        c = st.columns(3)
        wake = c[0].time_input("기상", dt.time(7, 0)); bfast = c[1].time_input("아침 식사", dt.time(7, 30))
        lunch = c[2].time_input("점심 식사", dt.time(12, 30))
        c = st.columns(3)
        dinner = c[0].time_input("저녁 식사", dt.time(18, 30)); bed = c[1].time_input("취침", dt.time(23, 0))
        start = c[2].time_input("첫 복용 시각", dt.time(8, 0))
        alt = st.checkbox("🤝 아세트아미노펜·NSAIDs 교차 복용 시차 적용", value=True)

    prefs = dict(wake=to_hour(wake), b=to_hour(bfast), l=to_hour(lunch), d=to_hour(dinner),
                 bed=to_hour(bed), start=to_hour(start), alternate=alt)
    try:
        sched, notes, w, b = build_schedule(r, prefs)
    except Exception as e:
        st.error(f"스케줄 생성 오류: {e}")
        return

    # 이벤트 카드
    events = []
    for did, doses in sched.items():
        for t in doses:
            if did in DRUGS:
                d = DRUGS[did]
                events.append((t, f'{d["icon"]} {d["name"]}', f'{MEAL_TXT[d["meal"]]} · 용량은 제품 라벨/처방 기준'))
            else:
                events.append((t, f'{SUPPS[did]["icon"]} {SUPPS[did]["name"]}', SUPPS[did]["timing"]))
    events.sort()
    st.markdown("### 📋 오늘의 복약 일정")
    html("".join(f'<div class="tl-item"><div class="tl-time">{fmt_time(t)}</div>'
                 f'<div class="tl-body"><b>{n}</b><div>{desc}</div></div></div>' for t, n, desc in events))
    for n in notes:
        st.caption(f"🔧 {n}")

    # 24시간 표
    st.markdown("### 🗓️ 시간대별 한눈표")
    ids = list(sched)
    rows = []
    meal_marks = {}
    for hh, lab in ((int(w), "🌅 기상"), (int(prefs["b"]), "🍚 아침"), (int(prefs["l"]), "🍚 점심"),
                    (int(prefs["d"]), "🍚 저녁"), (int(b) % 24, "🌙 취침")):
        meal_marks[hh % 24] = (meal_marks.get(hh % 24, "") + " " + lab).strip()
    for h in range(int(w), math.ceil(b) + 1):
        row = [f"{h % 24:02d}:00", meal_marks.get(h % 24, "")]
        for i in ids:
            hit = [t for t in sched[i] if int(t) == h]
            row.append(f'<span class="dose">● {fmt_time(hit[0])}</span>' if hit else "")
        rows.append(row)
    html(html_table(["시각", "생활"] + [item_name(i) for i in ids], rows))

    # PK 그래프
    st.markdown("### 📈 혈중 농도 시뮬레이션 (상대값)")
    grid = [x * 0.25 for x in range(0, 24 * 4 + 1)]
    data = {"시각(시)": grid}
    for it in r["items"]:
        data[DRUGS[it["id"]]["name"]] = pk_curve(it["id"], sched[it["id"]], it["pk"]["t_half_adj"], grid)
    st.line_chart(pd.DataFrame(data).set_index("시각(시)"))
    st.caption("1회 복용 최고 농도를 100%로 둔 상대 곡선입니다. 곡선이 100%를 크게 넘으면 축적을 의미합니다. (교육용 모델)")

    st.markdown("### 🧑‍⚕️ 간호학적 복약 지도 포인트")
    st.markdown("- **투약 5원칙**: 올바른 환자·약·용량·경로·시간을 매번 확인\n"
                "- 복용 시각을 알람으로 고정하고, 놓쳤을 때는 **두 배로 먹지 않기**\n"
                "- 3일 이상 증상이 지속·악화되면 자가 복용을 멈추고 진료")


# ------------------------------------------------------------------------------------------
# 5-D. AI 처방전 스캐너 (Gemini Vision)
# ------------------------------------------------------------------------------------------
SCAN_PROMPT = """너는 한국 처방전/약봉투 OCR 전문가야. 이미지를 읽고 아래 JSON 스키마로만 답해.
읽을 수 없는 값은 null. 추측하거나 지어내지 마. 환자 이름 등 개인정보는 null로 둬도 돼.
{"hospital_name": str|null, "issue_date": str|null,
 "medications": [{"name": str, "ingredient": str|null, "dose": str|null, "frequency": str|null,
                  "days": str|null, "timing": str|null, "notes": str|null}]}"""

SAMPLE_SCAN = {
    "hospital_name": "샘플의원(데모)", "issue_date": "2026-11-09",
    "medications": [
        {"name": "타이레놀 8시간 ER", "ingredient": "아세트아미노펜", "dose": "650mg", "frequency": "1일 3회", "days": "3", "timing": "식후", "notes": None},
        {"name": "브루펜정", "ingredient": "이부프로펜", "dose": "200mg", "frequency": "1일 3회", "days": "3", "timing": "식후", "notes": None},
        {"name": "지르텍정", "ingredient": "세티리진", "dose": "10mg", "frequency": "1일 1회", "days": "5", "timing": "저녁", "notes": None},
        {"name": "클로르페니라민정", "ingredient": "클로르페니라민", "dose": "4mg", "frequency": "1일 3회", "days": "3", "timing": "식후", "notes": None},
        {"name": "OO정(미등록 약)", "ingredient": None, "dose": None, "frequency": None, "days": None, "timing": None, "notes": None},
    ],
}


def parse_json_text(txt: str) -> dict:
    txt = re.sub(r"^```(?:json)?|```$", "", txt.strip(), flags=re.M).strip()
    try:
        return json.loads(txt)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", txt, flags=re.S)
        if m:
            return json.loads(m.group(0))
        raise


def scan_with_gemini(img):
    key = get_api_key()
    if not key:
        raise RuntimeError("Gemini API 키가 없습니다. 사이드바에 입력하거나 Streamlit secrets에 GEMINI_API_KEY를 등록하세요.")
    if genai is None:
        raise RuntimeError("google-generativeai 패키지가 설치되어 있지 않습니다. requirements.txt를 확인하세요.")
    genai.configure(api_key=key)
    last = None
    for name in gemini_models():
        try:
            model = genai.GenerativeModel(name, generation_config={"response_mime_type": "application/json", "temperature": 0.1})
            resp = model.generate_content([SCAN_PROMPT, img])
            return name, parse_json_text(resp.text)
        except Exception as e:
            last = e
    raise RuntimeError(f"Gemini 호출 실패: {last}")


def match_drug(med: dict):
    """OCR 결과의 이름/성분을 로컬 DB 별칭과 매칭."""
    text = f"{med.get('name') or ''} {med.get('ingredient') or ''}".lower()
    for did, d in DRUGS.items():
        if any(a.lower() in text for a in d["aliases"]):
            return did
    return None


def page_scanner():
    st.title("📷 AI 처방전 스캐너")
    st.caption("Gemini Vision이 이미지를 구조화 JSON으로 변환하고, 로컬 DUR 엔진이 상호작용을 교차검증합니다.")
    st.warning("개인정보(이름·주민번호·연락처)는 가린 뒤 업로드하세요.")
    tab_up, tab_cam = st.tabs(["📁 사진 업로드", "📸 카메라 촬영"])
    img_file = None
    with tab_up:
        up = st.file_uploader("처방전/약봉투 이미지", type=["png", "jpg", "jpeg", "webp"])
        img_file = up or img_file
    with tab_cam:
        cam = st.camera_input("촬영")
        img_file = cam or img_file

    c1, c2 = st.columns(2)
    run = c1.button("🔍 AI로 분석하기", key="scan_run")
    c2.button("🧪 데모 데이터 불러오기", key="scan_demo", on_click=lambda: st.session_state.update(scan=SAMPLE_SCAN))

    if run:
        if img_file is None:
            st.error("이미지를 먼저 올려 주세요.")
        elif Image is None:
            st.error("Pillow 패키지가 필요합니다.")
        else:
            try:
                with st.status("처방전 분석 중...", expanded=True) as status:
                    st.write("이미지 불러오는 중"); img = Image.open(img_file)
                    st.write("Gemini Vision OCR → JSON 변환")
                    model, data = scan_with_gemini(img)
                    st.session_state.scan = data
                    status.update(label=f"분석 완료 ✅ ({model})", state="complete", expanded=False)
            except Exception as e:
                st.error(f"분석 실패: {e}")

    if img_file is not None and Image is not None:
        with st.expander("업로드한 이미지 보기"):
            st.image(img_file)

    data = st.session_state.scan
    if not data:
        return
    meds = data.get("medications") or []
    st.markdown(f"### 🧾 인식 결과 · {data.get('hospital_name') or '병원명 미상'} · {data.get('issue_date') or '날짜 미상'}")
    cols, matched = st.columns(2), []
    for n, m in enumerate(meds):
        did = match_drug(m)
        if did:
            matched.append(did)
        with cols[n % 2]:
            status_badge = badge("safe") if did else '<span class="badge badge-info">DB 미등록</span>'
            html(f'<div class="glass">{status_badge}<h4 style="margin-top:.4rem">{m.get("name") or "이름 미상"}</h4>'
                 f'<p>성분: {m.get("ingredient") or "-"} · 용량: {m.get("dose") or "-"}<br>'
                 f'횟수: {m.get("frequency") or "-"} · 일수: {m.get("days") or "-"} · 시점: {m.get("timing") or "-"}</p></div>')
    st.markdown("### 🛡️ DUR 교차검증")
    uniq = list(dict.fromkeys(matched))
    inter = analyze_interactions(uniq) if len(uniq) > 1 else []
    for did in uniq:
        if matched.count(did) > 1:
            html(finding_html(dict(sev="danger", cat="성분 중복", text="같은 성분이 2회 이상 처방/기재되어 있습니다."), DRUGS[did]["name"]))
    if not inter:
        st.success("DB에 등록된 약물 사이에서 확인된 상호작용이 없습니다.")
    for x in sorted(inter, key=lambda x: -RANK[x["sev"]]):
        html(finding_html(dict(sev=x["sev"], cat="약물-약물", text=x["text"]), f"{item_name(x['pair'][0])} + {item_name(x['pair'][1])}"))
    if len(uniq) < len(meds):
        st.caption("※ DB에 없는 약은 교차검증에서 제외되었습니다. 약사에게 확인하세요.")
    with st.expander("📄 구조화 JSON 원본"):
        st.json(data)


# ------------------------------------------------------------------------------------------
# 6. 사이드바 & 라우터
# ------------------------------------------------------------------------------------------
def sidebar():
    with st.sidebar:
        st.markdown("## 💊 SmartMed DUR")
        st.caption("스마트 맞춤형 OTC 약물 조합 & DUR 케어 가이드")
        st.radio("메뉴", PAGES, key="nav", label_visibility="collapsed")
        st.divider()
        st.text_input("🔑 Gemini API Key (선택)", type="password", key="api_key",
                      help="비워두면 Streamlit secrets의 GEMINI_API_KEY를 사용합니다.")
        st.caption("👩‍🎓 20901 강은유\n\n⚠️ 교육용 프로토타입입니다. 실제 복약은 의사·약사와 상의하세요.")


def main():
    init_state()
    sidebar()
    page = st.session_state["nav"]
    try:
        {PAGES[0]: page_dashboard, PAGES[1]: page_diagnosis,
         PAGES[2]: page_timeline, PAGES[3]: page_scanner}[page]()
    except Exception as e:  # 마지막 방어선: 화면이 하얗게 죽지 않도록
        st.error(f"예상치 못한 오류가 발생했습니다: {e}")
        st.exception(e)


main()

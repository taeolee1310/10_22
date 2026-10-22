import os
from datetime import timedelta, timezone
from email.utils import parsedate_to_datetime

import requests
import streamlit as st

API = {
    "환율": "https://v6.exchangerate-api.com/v6/latest/KRW",  # 🔌 ExchangeRate-API (원화 기준 환율)
}

# 1.달러 2.엔화 3.호주달러 만 표기
CURRENCIES = [
    ("USD", "1. 달러"),
    ("JPY", "2. 엔화"),
    ("AUD", "3. 호주달러"),
]

# 금액 프리셋: 작은 금액 → 큰 금액 순. 첫 번째 값이 기본 금액이다. (값, 버튼 글자, 증감 단위)
PRESETS = {
    "KRW": ([(100_000, "10만원"), (500_000, "50만원"), (1_000_000, "100만원")], 10_000),
    "USD": ([(100, "100 달러"), (500, "500 달러"), (1_000, "1,000 달러")], 10),
    "JPY": ([(10_000, "1만 엔"), (50_000, "5만 엔"), (100_000, "10만 엔")], 1_000),
    "AUD": ([(100, "100 호주달러"), (500, "500 호주달러"), (1_000, "1,000 호주달러")], 10),
}

ERROR_MESSAGES = {
    "invalid-key": "환율 키가 틀렸어요.",
    "inactive-account": "환율 사이트 가입 인증 메일을 확인해 주세요.",
    "quota-reached": "이번 달 무료 사용량(1,500번)을 다 썼어요.",
}

KST = timezone(timedelta(hours=9))

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&display=swap');

:root {
    --bg: #EDEBE6;
    --panel: #F7F6F2;
    --ink: #151515;
    --sub: #55554F;      /* 회색 배경 위 보조 글자: 대비 6.3:1 */
    --accent-ink: #C73200; /* 밝은 배경 위 주황 글자: 대비 4.5:1 이상 */
    --line: #151515;
    --accent: #FF4B12;
}

html, body, [class*="css"], .stApp, .stApp * {
    font-family: 'IBM Plex Mono', ui-monospace, Consolas, monospace;
}
.stApp { background: var(--bg); color: var(--ink); }
header[data-testid="stHeader"] { background: transparent; }
.block-container { max-width: 760px; padding-top: 2.5rem; }

.tag {
    display: inline-block;
    background: var(--accent);
    color: var(--ink);
    font-size: 12px;
    font-weight: 600;
    letter-spacing: .12em;
    padding: 2px 8px;
}
.title {
    font-size: 30px;
    font-weight: 600;
    letter-spacing: -.02em;
    margin: 10px 0 2px;
}
.caption { color: var(--sub); font-size: 13px; font-weight: 500; margin-bottom: 20px; }

.card {
    background: var(--panel);
    border: 1.5px solid var(--line);
    padding: 14px 14px 12px;
}
.card .label { font-size: 13px; font-weight: 600; letter-spacing: .06em; color: var(--ink); }
.card .code { font-size: 13px; font-weight: 600; color: var(--accent-ink); }
.card .value { font-size: 24px; font-weight: 600; letter-spacing: -.01em; margin: 8px 0 4px; word-break: break-all; }
.card .rate { font-size: 13px; font-weight: 500; color: var(--sub); }

.step { margin: 24px 0 8px; font-size: 14px; font-weight: 600; letter-spacing: .04em; color: var(--ink); }
.step b { background: var(--ink); color: var(--bg); padding: 1px 6px; margin-right: 6px; }
.sum { font-size: 15px; font-weight: 500; margin-bottom: 10px; color: var(--ink); }
.sum b { font-weight: 600; }
.sum span { color: var(--accent-ink); font-weight: 600; }
.card.big { border-width: 2px; border-left: 8px solid var(--accent); }
.card.big .value { font-size: 32px; }
.card .unit { font-size: 14px; color: var(--ink); font-weight: 600; }

.footer {
    border-top: 1.5px solid var(--line);
    margin-top: 24px;
    padding-top: 10px;
    font-size: 13px;
    font-weight: 500;
    color: var(--sub);
}

/* 스트림릿 기본 테마(다크 등)와 상관없이 위젯 글자를 어두운 색으로 고정 */
.stApp label, .stApp label p, .stApp [data-testid="stWidgetLabel"] p,
.stApp div[role="radiogroup"] label p, .stApp .stMarkdown p { color: var(--ink) !important; }
.stApp label p, .stApp [data-testid="stWidgetLabel"] p { font-weight: 600 !important; font-size: 14px !important; }
.stApp div[role="radiogroup"] label p { font-weight: 500 !important; }

div[data-testid="stNumberInput"] input {
    color: var(--ink);
    background: var(--panel);
    border: 1.5px solid var(--line);
    border-radius: 0;
    font-weight: 600;
    font-size: 16px;
}
div[data-testid="stNumberInput"] > div { border-radius: 0; }
div[data-testid="stNumberInput"] button { border-radius: 0; }
.stButton > button {
    background: var(--ink);
    color: #fff;
    border: 1.5px solid var(--ink);
    border-radius: 0;
    font-size: 13px;
    font-weight: 600;
    letter-spacing: .08em;
}
.stButton > button[kind="secondary"], .stButton > button[data-testid="stBaseButton-secondary"] {
    background: var(--panel); color: var(--ink); border: 1.5px solid var(--ink);
}
.stButton > button[data-testid="stBaseButton-primary"] {
    background: var(--accent); color: var(--ink); border: 1.5px solid var(--ink);
}
.st-key-refresh button { background: var(--ink) !important; color: #fff !important; }
.stButton > button:hover { background: var(--accent); border-color: var(--ink); color: var(--ink); }
</style>
"""


def load_env(path=".env"):
    """같은 폴더의 .env 파일을 읽어 환경변수로 등록한다. 이미 있는 환경변수는 덮어쓰지 않는다."""
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), path)
    if not os.path.exists(env_path):
        return
    with open(env_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            name, value = line.split("=", 1)
            os.environ.setdefault(name.strip(), value.strip().strip('"').strip("'"))


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_rates(api_key):
    """원화 기준 환율을 한 번 불러온다. 실패하면 (None, 한국어 안내)를 돌려준다."""
    try:
        res = requests.get(  # 🔌 API 호출
            API["환율"],
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=10,
        )
        data = res.json()
    except requests.RequestException:
        return None, "환율 서버에 연결하지 못했어요. 잠시 뒤에 다시 해 주세요."
    except ValueError:
        return None, "환율 서버 응답을 읽지 못했어요."

    if data.get("result") != "success":  # data["result"] = "success" 또는 "error"
        return None, ERROR_MESSAGES.get(data.get("error-type"), "환율을 불러오지 못했어요.")

    return {
        "rates": data["conversion_rates"],  # data["conversion_rates"] = 1원당 각 통화 값
        "updated": data["time_last_update_utc"],  # data["time_last_update_utc"] = 환율 기준 시각(UTC)
    }, None


def to_kst_text(utc_text):
    try:
        return parsedate_to_datetime(utc_text).astimezone(KST).strftime("%Y-%m-%d %H:%M KST")
    except (TypeError, ValueError):
        return utc_text


def set_amount(key, value):
    st.session_state[key] = float(value)


def amount_input(code, label):
    """금액 입력칸과 그 아래 프리셋 버튼. 통화마다 따로 값을 기억한다."""
    presets, unit_step = PRESETS[code]
    key = f"amount_{code}"
    st.session_state.setdefault(key, float(presets[0][0]))  # 기본 금액 = 첫 프리셋(10만원 등)
    amount = st.number_input(label, min_value=0.0, step=float(unit_step), format="%.0f", key=key)
    with st.container(key=f"presets_{code}"):
        cols = st.columns(len(presets))
        for col, (value, text) in zip(cols, presets):
            col.button(
                text,
                key=f"preset_{code}_{value}",
                type="primary" if amount == value else "secondary",
                use_container_width=True,
                on_click=set_amount,
                args=(key, value),
            )
    return amount


def step(num, text):
    st.markdown(f'<div class="step"><b>{num}</b> {text}</div>', unsafe_allow_html=True)


def card(label, code, value, unit, rate_text, big=False):
    st.markdown(
        f"""<div class="card{' big' if big else ''}">
        <div class="label">{label} <span class="code">{code}</span></div>
        <div class="value">{value}<span class="unit"> {unit}</span></div>
        <div class="rate">{rate_text}</div>
        </div>""",
        unsafe_allow_html=True,
    )


def main():
    st.set_page_config(page_title="환율 계산기", page_icon="💱")
    st.markdown(CSS, unsafe_allow_html=True)
    st.markdown(
        '<span class="tag">RATE-01</span>'
        '<div class="title">환율 계산기</div>'
        '<div class="caption">KRW ↔ USD / JPY / AUD</div>',
        unsafe_allow_html=True,
    )

    load_env()
    api_key = os.environ.get("EXCHANGERATE_API_KEY", "").strip()
    if not api_key:
        st.error(".env에 EXCHANGERATE_API_KEY가 없어요. .env.example을 보고 채워 주세요.")
        st.stop()

    result, error = fetch_rates(api_key)
    if error:
        st.error(error)
        st.stop()
    rates = result["rates"]

    # 01 방향: 무엇을 무엇으로 바꾸는지 먼저 고른다
    step("01", "무엇을 바꿀까요?")
    direction = st.radio("방향", ["원 → 외화", "외화 → 원"], horizontal=True, label_visibility="collapsed")
    to_foreign = direction == "원 → 외화"

    # 02 금액: 입력하는 단위를 라벨에 분명히 적는다
    step("02", "금액을 입력하세요")
    if to_foreign:
        in_code = "KRW"
        amount = amount_input(in_code, "가지고 있는 금액 (원)")
    else:
        pick = st.radio(
            "어떤 외화를 가지고 있나요?",
            CURRENCIES,
            format_func=lambda c: f"{c[1]} ({c[0]})",
            horizontal=True,
        )
        in_code = pick[0]
        amount = amount_input(in_code, f"가지고 있는 금액 ({pick[1][3:]})")

    # 03 결과: 입력 → 결과 순서로 한눈에 읽히게 한 줄 요약을 먼저 보여 준다
    step("03", "바꾼 금액")
    if st.button("새로 불러오기", key="refresh"):
        st.cache_data.clear()

    if to_foreign:
        st.markdown(
            f'<div class="sum"><b>{amount:,.0f} 원</b> <span>→</span> 달러 · 엔화 · 호주달러</div>',
            unsafe_allow_html=True,
        )
        cols = st.columns(len(CURRENCIES))
        for col, (code, label) in zip(cols, CURRENCIES):
            with col:
                per_krw = rates.get(code)  # rates["USD"] = 1원이 몇 달러인지
                if not per_krw:
                    card(label, code, "-", "", "환율 없음")
                    continue
                card(label, code, f"{amount * per_krw:,.2f}", code, f"1 {code} = {1 / per_krw:,.2f} 원")
    else:
        label = dict(CURRENCIES)[in_code]
        per_krw = rates.get(in_code)
        st.markdown(
            f'<div class="sum"><b>{amount:,.0f} {in_code}</b> <span>→</span> 원</div>',
            unsafe_allow_html=True,
        )
        if not per_krw:
            card("원", "KRW", "-", "", "환율 없음", big=True)
        else:
            card("원", "KRW", f"{amount / per_krw:,.0f}", "원", f"1 {in_code} = {1 / per_krw:,.2f} 원", big=True)

    st.markdown(
        f'<div class="footer">환율: ExchangeRate-API · 기준 시각 {to_kst_text(result["updated"])}'
        "<br>하루 한 번 갱신되는 값이라 실제 거래 환율과 다를 수 있어요.</div>",
        unsafe_allow_html=True,
    )


main()

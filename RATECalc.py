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
    font-size: 28px;
    font-weight: 600;
    letter-spacing: -.02em;
    margin: 10px 0 2px;
}
.caption { color: var(--sub); font-size: 12px; margin-bottom: 20px; }

.card {
    background: var(--panel);
    border: 1.5px solid var(--line);
    padding: 14px 14px 12px;
}
.card .label { font-size: 12px; letter-spacing: .1em; color: var(--sub); }
.card .code { font-size: 12px; font-weight: 600; color: var(--accent-ink); }
.card .value { font-size: 22px; font-weight: 600; margin: 8px 0 4px; word-break: break-all; }
.card .rate { font-size: 12px; color: var(--sub); }

.footer {
    border-top: 1.5px solid var(--line);
    margin-top: 24px;
    padding-top: 10px;
    font-size: 12px;
    color: var(--sub);
}

/* 스트림릿 기본 테마(다크 등)와 상관없이 위젯 글자를 어두운 색으로 고정 */
.stApp label, .stApp label p, .stApp [data-testid="stWidgetLabel"] p,
.stApp div[role="radiogroup"] label p, .stApp .stMarkdown p { color: var(--ink) !important; }

div[data-testid="stNumberInput"] input {
    color: var(--ink);
    background: var(--panel);
    border: 1.5px solid var(--line);
    border-radius: 0;
    font-weight: 500;
}
div[data-testid="stNumberInput"] > div { border-radius: 0; }
div[data-testid="stNumberInput"] button { border-radius: 0; }
.stButton > button {
    background: var(--ink);
    color: #fff;
    border: 1.5px solid var(--ink);
    border-radius: 0;
    font-size: 12px;
    letter-spacing: .08em;
}
.stButton > button:hover { background: var(--accent); border-color: var(--ink); color: var(--ink); }
div[role="radiogroup"] label p { font-size: 13px; }
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


def card(label, code, value, rate_text):
    st.markdown(
        f"""<div class="card">
        <div class="label">{label} <span class="code">{code}</span></div>
        <div class="value">{value}</div>
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

    direction = st.radio("방향", ["원 → 외화", "외화 → 원"], horizontal=True, label_visibility="collapsed")
    to_foreign = direction == "원 → 외화"
    amount = st.number_input(
        "금액 (원)" if to_foreign else "금액 (각 통화 기준)",
        min_value=0.0,
        value=1000.0 if to_foreign else 100.0,
        step=1000.0 if to_foreign else 10.0,
        format="%.0f",
    )

    if st.button("새로 불러오기"):
        st.cache_data.clear()

    result, error = fetch_rates(api_key)
    if error:
        st.error(error)
        st.stop()

    rates = result["rates"]
    cols = st.columns(len(CURRENCIES))
    for col, (code, label) in zip(cols, CURRENCIES):
        with col:
            per_krw = rates.get(code)  # rates["USD"] = 1원이 몇 달러인지
            if not per_krw:
                card(label, code, "-", "환율 없음")
                continue
            krw_per_unit = 1 / per_krw
            if to_foreign:
                card(label, code, f"{amount * per_krw:,.2f}", f"1 {code} = {krw_per_unit:,.2f} KRW")
            else:
                card(label, code, f"{amount * krw_per_unit:,.0f}원", f"{amount:,.0f} {code} 기준")

    st.markdown(
        f'<div class="footer">환율: ExchangeRate-API · 기준 시각 {to_kst_text(result["updated"])}'
        "<br>하루 한 번 갱신되는 값이라 실제 거래 환율과 다를 수 있어요.</div>",
        unsafe_allow_html=True,
    )


main()

import os

import requests
import streamlit as st

API = {
    "채팅": "https://api.openai.com/v1/chat/completions",  # 🔌 OpenAI Chat Completions
}


def load_env(path=".env"):
    """같은 폴더의 .env 파일을 읽어 환경변수로 등록한다. 이미 있는 환경변수는 덮어쓰지 않는다."""
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), path)
    if not os.path.exists(env_path):
        return
    with open(env_path, encoding="utf-8-sig") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            name, value = line.split("=", 1)
            value = value.strip().strip('"').strip("'")
            if value and not os.environ.get(name.strip()):
                os.environ[name.strip()] = value


load_env()

MODEL = "gpt-4o-mini"
SYSTEM_PROMPT = (
    "당신은 프로덕트 디자이너 인턴을 돕는 선배 디자이너입니다. "
    "항상 한국어로, 간결하고 정확하게 답하세요. 결론을 먼저 말하고 이유는 한두 문장으로 덧붙입니다. "
    "UI·UX, 사용자 리서치, 피그마, 디자인 시스템, 프로토타이핑 질문에는 실무 예시를 하나씩 곁들이세요. "
    "코딩이나 AI 도구 질문은 비전공자도 따라 할 수 있게 단계별로 풀어 설명하고, 전문 용어는 처음 쓸 때 뜻을 한 줄로 풀어 주세요. "
    "모르는 내용은 아는 척하지 말고 모른다고 말하세요. "
    "번역투나 '결론적으로' 같은 관용구 없이 사람이 말하듯 자연스럽게 쓰고, 이모지와 이모티콘은 쓰지 마세요."
)


def ask(messages):
    """대화 기록을 보내 답변 문자열을 받는다. 실패하면 (None, 한국어 한 줄 메시지)."""
    key = os.getenv("OPENAI_API_KEY", "").strip()
    if not key:
        return None, "OPENAI_API_KEY가 없습니다. .env 파일을 확인해 주세요."
    try:
        res = requests.post(
            API["채팅"],
            headers={"Authorization": f"Bearer {key}"},
            json={"model": MODEL, "messages": messages},
            timeout=30,
        )
    except requests.RequestException:
        return None, "OpenAI에 연결하지 못했습니다. 인터넷 연결을 확인해 주세요."
    if res.status_code == 401:
        return None, "API 키가 올바르지 않습니다. .env 파일을 확인해 주세요."
    if res.status_code == 429:
        return None, "요청이 너무 많거나 사용 한도를 넘었습니다. 잠시 후 다시 시도해 주세요."
    if not res.ok:
        return None, f"답변을 받지 못했습니다. (오류 코드 {res.status_code})"
    try:
        return res.json()["choices"][0]["message"]["content"], None
    except (ValueError, KeyError, IndexError):
        return None, "응답 형식이 예상과 달라 읽지 못했습니다. 잠시 후 다시 시도해 주세요."


st.set_page_config(page_title="챗봇")

# 틴에이지 엔지니어링 스타일: 오프화이트 바탕, 검정 선, 주황 포인트, 모노스페이스, 직각 모서리
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&display=swap');
    :root { --te-orange: #FF4B12; --te-black: #151515; --te-paper: #F7F6F2; }
    html, body, [class*="css"], .stApp, textarea, button {
        font-family: 'Space Mono', 'D2Coding', monospace !important;
    }
    header[data-testid="stHeader"] { background: transparent; }
    .block-container { max-width: 760px; padding-top: 3rem; }
    .te-title { display: flex; align-items: center; gap: 14px; margin-bottom: 4px; }
    .te-dot { width: 22px; height: 22px; border-radius: 50%; background: var(--te-orange); }
    .te-title h1 { margin: 0; padding: 0; font-size: 2rem; font-weight: 700;
                   letter-spacing: 0.04em; color: var(--te-black); }
    .te-meta { font-size: 0.72rem; letter-spacing: 0.14em; text-transform: uppercase;
               color: #6B6A66; border-top: 2px solid var(--te-black); padding-top: 6px;
               margin-bottom: 1.5rem; }
    [data-testid="stChatMessage"] { background: var(--te-paper); border: 2px solid var(--te-black);
                                    border-radius: 0; box-shadow: 4px 4px 0 var(--te-black);
                                    margin-bottom: 14px; }
    [data-testid="stChatMessageAvatarUser"], [data-testid="stChatMessageAvatarAssistant"] {
        border-radius: 0; background: var(--te-black); color: var(--te-paper); }
    [data-testid="stChatMessageAvatarAssistant"] { background: var(--te-orange); }
    [data-testid="stChatInput"] { border: 2px solid var(--te-black); border-radius: 0;
                                  background: var(--te-paper); }
    [data-testid="stChatInput"] textarea { border-radius: 0; }
    .stButton > button { border: 2px solid var(--te-black); border-radius: 0;
                         background: var(--te-paper); color: var(--te-black);
                         letter-spacing: 0.06em; }
    .stButton > button:hover { background: var(--te-orange); border-color: var(--te-black);
                               color: var(--te-black); }
    [data-testid="stSidebar"] { border-right: 2px solid var(--te-black); }
    [data-testid="stAlert"] { border-radius: 0; border: 2px solid var(--te-black); }
    [data-testid="stChatInput"]:focus-within { border-color: var(--te-orange);
                                               box-shadow: 4px 4px 0 var(--te-orange); }
    [data-testid="stSidebar"] { background: var(--te-paper); }
    .te-label { font-size: 0.68rem; letter-spacing: 0.16em; text-transform: uppercase;
                color: #6B6A66; margin-bottom: 6px; }
    .te-label b { color: var(--te-orange); }
    .te-empty { border: 2px dashed var(--te-black); padding: 28px 20px; text-align: center;
                font-size: 0.8rem; letter-spacing: 0.1em; color: #6B6A66; }
    pre, code { border-radius: 0 !important; }
    pre { border: 2px solid var(--te-black); }
    [data-testid="stSpinner"] { font-size: 0.8rem; letter-spacing: 0.1em; }
    ::selection { background: var(--te-orange); color: var(--te-black); }
    </style>
    <div class="te-title"><span class="te-dot"></span><h1>챗봇</h1></div>
    <div class="te-meta">MODEL / """ + MODEL + """</div>
    """,
    unsafe_allow_html=True,
)

if "messages" not in st.session_state:
    st.session_state.messages = []

ROLE_LABEL = {"user": "사용자", "assistant": "챗봇"}


def show(role, text, number):
    """역할 라벨(번호 / 이름)을 붙여 한 칸을 그린다."""
    with st.chat_message(role):
        st.markdown(f'<div class="te-label"><b>{number:02d}</b> / {ROLE_LABEL[role]}</div>',
                    unsafe_allow_html=True)
        st.markdown(text)


with st.sidebar:
    st.markdown('<div class="te-label">설정</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="te-label"><b>MODEL</b> / {MODEL}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="te-label"><b>대화</b> / {len(st.session_state.messages):02d}</div>',
                unsafe_allow_html=True)
    if st.button("대화 지우기"):
        st.session_state.messages = []
        st.rerun()

if not st.session_state.messages:
    st.markdown('<div class="te-empty">메시지를 입력하면 대화가 시작됩니다</div>',
                unsafe_allow_html=True)

for i, m in enumerate(st.session_state.messages, 1):
    show(m["role"], m["content"], i)

if prompt := st.chat_input("메시지를 입력하세요"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    show("user", prompt, len(st.session_state.messages))

    with st.chat_message("assistant"):
        with st.spinner("생각 중..."):
            history = [{"role": "system", "content": SYSTEM_PROMPT}] + st.session_state.messages
            answer, error = ask(history)
        if error:
            st.error(error)
            st.session_state.messages.pop()  # 실패한 질문은 기록에서 뺀다
        else:
            st.markdown(f'<div class="te-label"><b>{len(st.session_state.messages) + 1:02d}</b> / 챗봇</div>',
                        unsafe_allow_html=True)
            st.markdown(answer)
            st.session_state.messages.append({"role": "assistant", "content": answer})

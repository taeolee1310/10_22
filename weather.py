import json
import os
import urllib.error
import urllib.parse
import urllib.request

import streamlit as st

API_URL = "https://api.openweathermap.org/data/2.5/weather"
CITY = "Seoul,kr"


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


@st.cache_data(ttl=300, show_spinner=False)
def fetch_weather(api_key):
    query = urllib.parse.urlencode({
        "q": CITY,
        "APPID": api_key,
        "units": "metric",  # 섭씨
        "lang": "kr",       # 날씨 설명을 한국어로
    })
    with urllib.request.urlopen(f"{API_URL}?{query}", timeout=10) as res:
        return json.load(res)


def main():
    st.set_page_config(page_title="서울 현재 날씨", page_icon="🌤️")
    st.title("서울 현재 날씨")

    load_env()
    api_key = os.environ.get("OPENWEATHER_API_KEY", "").strip()
    if not api_key:
        api_key = st.text_input("OpenWeather API 키", type="password").strip()
    if not api_key:
        st.info("API 키를 입력하면 날씨를 보여줍니다.")
        st.stop()

    if st.button("새로고침"):
        fetch_weather.clear()

    try:
        data = fetch_weather(api_key)
    except urllib.error.HTTPError as e:
        if e.code == 401:
            st.error("API 키가 올바르지 않습니다. (새로 발급한 키는 활성화에 최대 몇 시간이 걸릴 수 있습니다.)")
        else:
            st.error(f"요청 실패: HTTP {e.code}")
        st.stop()
    except urllib.error.URLError as e:
        st.error(f"네트워크 오류: {e.reason}")
        st.stop()

    main_info = data["main"]
    description = data["weather"][0]["description"]

    col1, col2, col3 = st.columns(3)
    col1.metric("기온", f"{main_info['temp']:.1f}°C")
    col2.metric("체감 온도", f"{main_info['feels_like']:.1f}°C")
    col3.metric("습도", f"{main_info['humidity']}%")
    st.subheader(f"날씨: {description}")


main()

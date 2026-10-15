import streamlit as st
import random
import time
from openai import OpenAI

st.set_page_config(page_title="핫 포테이토 (Hot Potato) - AI 토론 게임", layout="wide")

# Session State 초기화
if "game_started" not in st.state_dict():
    st.session_state.game_started = False
if "current_turn" not in st.state_dict():
    st.session_state.current_turn = 0
if "bomb_timer" not in st.state_dict():
    st.session_state.bomb_timer = 0
if "messages" not in st.state_dict():
    st.session_state.messages = []
if "players" not in st.state_dict():
    st.session_state.players = []
if "game_over" not in st.state_dict():
    st.session_state.game_over = False

# AI 페르소나 정의
AI_PERSONAS = [
    {"name": "AI 1 (논리왕)", "role": "팩트와 논리로만 압박하며 상대를 몰아붙이는 냉철한 토론가"},
    {"name": "AI 2 (억지왕)", "role": "말도 안 되는 비유와 궤변으로 어떻게든 우기는 고집불통"},
    {"name": "AI 3 (유머캐)", "role": "상황을 드립과 유머로 넘어가려는 분위기 메이커"},
    {"name": "AI 4 (반골)", "role": "앞사람이 무슨 말을 하든 무조건 반대하고 시비 거는 딴지꾼"},
    {"name": "AI 5 (감성파)", "role": "공감과 감정에 호소하며 눈물겨운 설득을 시도하는 스타일"},
]

st.title("🔥 AI 5명 vs 나 1명: 핫 포테이토 (Hot Potato)")
st.caption("폭탄이 터지기 전에 뜨거운 감자(토론 주제)를 다음 사람에게 넘기세요!")

# 사이드바: 설정
with st.sidebar:
    st.header("⚙️ 게임 설정")
    api_key = st.text_input("OpenAI API Key", type="password")
    user_name = st.text_input("내 닉네임", value="플레이어")
    topic = st.text_input("토론 주제 (핫 포테이토)", value="탕수육은 부먹인가 찍먹인가?")
    max_turns = st.slider("폭탄 타이머 (최대 턴 수)", min_value=5, max_value=20, value=10)

    if st.button("게임 시작 / 리셋"):
        if not api_key:
            st.error("API Key를 입력해주세요!")
        else:
            # 플레이어 순서 섞기
            players = AI_PERSONAS.copy()
            players.append({"name": f"👤 {user_name}", "role": "Human"})
            random.shuffle(players)

            st.session_state.players = players
            st.session_state.current_turn = 0
            st.session_state.bomb_timer = random.randint(3, max_turns) # 폭탄 터지는 임의의 턴
            st.session_state.messages = []
            st.session_state.game_started = True
            st.session_state.game_over = False
            st.rerun()

# AI 응답 생성 함수
def get_ai_response(client, persona_name, persona_role, topic, conversation_history):
    system_prompt = f"""
    너는 '핫 포테이토' 토론 게임에 참여 중인 '{persona_name}'이다.
    성격/역할: {persona_role}
    현재 토론 주제: '{topic}'

    [규칙]
    1. 이전 참가자들의 발언을 받아쳐서 반박하거나 의견을 내라.
    2. 답변은 2~3문장 이내로 짧고 강렬하게 써라.
    3. 마지막에는 반드시 다음 사람에게 지목하거나 질문을 던지며 핫 포테이토(발언권)를 넘겨라.
    """
    
    formatted_messages = [{"role": "system", "content": system_prompt}]
    for msg in conversation_history[-5:]: # 최근 5개 대화만 참조
        formatted_messages.append({"role": "user" if "👤" in msg["sender"] else "assistant", "content": f"{msg['sender']}: {msg['content']}"})

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=formatted_messages,
        max_tokens=150,
        temperature=0.8
    )
    return response.choices[0].message.content

# 게임 진행 로직
if st.session_state.game_started and not st.session_state.game_over:
    client = OpenAI(api_key=api_key)
    current_player = st.session_state.players[st.session_state.current_turn]
    
    st.info(f"📌 주제: **{topic}** | 🎯 현재 턴: **{current_player['name']}**")

    # 대화 기록 출력
    for msg in st.session_state.messages:
        with st.chat_message("user" if "👤" in msg["sender"] else "assistant"):
            st.write(f"**{msg['sender']}**: {msg['content']}")

    # 턴 수 체크 (폭탄 폭발 조건)
    if len(st.session_state.messages) >= st.session_state.bomb_timer:
        st.error(f"💥 💥 💥 **폭탄이 터졌습니다!** [{current_player['name']}] 님이 뜨거운 감자를 쥐고 있다가 패배했습니다! 💥 💥 💥")
        st.session_state.game_over = True
    else:
        # AI 턴 진행
        if "👤" not in current_player["name"]:
            with st.spinner(f"{current_player['name']} 생각 중..."):
                time.sleep(1) # 몰입감을 위한 딜레이
                ai_text = get_ai_response(
                    client, 
                    current_player["name"], 
                    current_player["role"], 
                    topic, 
                    st.session_state.messages
                )
                st.session_state.messages.append({"sender": current_player["name"], "content": ai_text})
                st.session_state.current_turn = (st.session_state.current_turn + 1) % len(st.session_state.players)
                st.rerun()

        # 사람 턴 진행
        else:
            user_input = st.chat_input("뜨거운 감자를 받았습니다! 의견을 적고 빠르게 다음 사람에게 넘기세요:")
            if user_input:
                st.session_state.messages.append({"sender": current_player["name"], "content": user_input})
                st.session_state.current_turn = (st.session_state.current_turn + 1) % len(st.session_state.players)
                st.rerun()

elif st.session_state.game_over:
    st.warning("🎮 게임이 종료되었습니다. 사이드바에서 '게임 시작'을 눌러 다시 플레이하세요.")

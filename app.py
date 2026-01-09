import streamlit as st
from rag_engine import SchoolChatbot
import os

# 페이지 설정
st.set_page_config(
    page_title="성동글로벌경영고등학교 AI 안내",
    page_icon="🏫",
    layout="wide"
)

# 헤더
st.title("🏫 성글고 AI 도우미")
st.markdown("**성동글로벌경영고등학교**에 오신 것을 환영합니다! 궁금한 점을 물어보세요.")

# API 키 가져오기
try:
    api_key = st.secrets["OPENROUTER_API_KEY"]
except Exception as e:
    st.error("⚠️ API 키가 설정되지 않았습니다. Streamlit Cloud의 Secrets를 확인해주세요.")
    st.info("📌 Streamlit Cloud → App settings → Secrets에서 OPENROUTER_API_KEY를 설정하세요.")
    st.stop()

# 챗봇 초기화
@st.cache_resource
def load_chatbot():
    with st.spinner("📚 학교 자료를 불러오는 중... 잠시만 기다려주세요."):
        try:
            chatbot = SchoolChatbot(
                api_key=api_key,
                docs_path="data/school_docs"
            )
            return chatbot
        except Exception as e:
            st.error(f"❌ 챗봇 로드 실패: {e}")
            st.info("💡 data/school_docs 폴더에 PDF 파일이 있는지 확인해주세요.")
            return None

chatbot = load_chatbot()

if chatbot is None:
    st.stop()

# 채팅 히스토리 초기화
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant", 
            "content": "안녕하세요! 성동글로벌경영고등학교 AI 도우미입니다. 😊\n\n학교 교육과정, 입학 안내, 진로진학 등 궁금하신 점을 자유롭게 물어보세요!"
        }
    ]

# 채팅 메시지 표시
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 사용자 입력
if prompt := st.chat_input("예: ERP 수업은 어떻게 진행되나요?"):
    # 사용자 메시지 추가
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # 챗봇 응답
    with st.chat_message("assistant"):
        with st.spinner("💭 답변을 생성하고 있습니다..."):
            try:
                response = chatbot.ask(prompt)
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
            except Exception as e:
                error_msg = f"죄송합니다. 답변 생성 중 오류가 발생했습니다: {str(e)}"
                st.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})

# 사이드바
with st.sidebar:
    st.header("📖 이용 안내")
    
    st.markdown("""
    ### 💬 질문 예시
    - 학교 교육과정은 어떻게 되나요?
    - ERP 수업에 대해 알려주세요
    - 입학 전형은 어떻게 진행되나요?
    - 졸업 후 진로는 어떻게 되나요?
    - 학교 위치와 연락처 알려주세요
    
    ### 💡 사용 팁
    - 구체적으로 질문할수록 정확한 답변을 받을 수 있습니다
    - 여러 질문을 한 번에 해도 괜찮습니다
    - 이해가 안 되면 다시 질문해보세요
    """)
    
    st.divider()
    
    # 학교 정보
    st.markdown("""
    ### 🏫 학교 정보
    **성동글로벌경영고등학교**
    
    📍 주소  
    서울 중구 퇴계로 375 (신당동)
    
    📞 전화  
    02-2252-1932
    
    🌐 홈페이지  
    [sdglobal.sen.hs.kr](https://sdglobal.sen.hs.kr/)
    """)
    
    st.divider()
    
    # 대화 초기화 버튼
    if st.button("🔄 대화 내용 초기화", use_container_width=True):
        st.session_state.messages = [
            {
                "role": "assistant", 
                "content": "안녕하세요! 성동글로벌경영고등학교 AI 도우미입니다. 😊\n\n학교 교육과정, 입학 안내, 진로진학 등 궁금하신 점을 자유롭게 물어보세요!"
            }
        ]
        st.rerun()
    
    # 푸터
    st.markdown("---")
    st.caption("🤖 Powered by OpenRouter + Streamlit")
    st.caption("📅 2025년 성동글로벌경영고등학교")

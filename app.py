import streamlit as st
from rag_engine import SchoolChatbot
from tts_engine import text_to_speech, get_audio_base64
import os
import base64

# ============================================================
# 🔧 관리자 설정 영역 - 여기서 앱 설정을 변경하세요!
# ============================================================

# VRM 아바타 모델 URL 설정
# - 기본값: pixiv 샘플 모델
# - 커스텀: GitHub에 VRM 파일 업로드 후 raw URL 입력
#   예: "https://raw.githubusercontent.com/your-repo/main/avatar.vrm"
VRM_MODEL_URL = "https://pixiv.github.io/three-vrm/packages/three-vrm/examples/models/VRM1_Constraint_Twist_Sample.vrm"

# 음성 출력 활성화 여부
TTS_ENABLED = True

# 아바타 표시 여부
AVATAR_ENABLED = True

# ============================================================

# 페이지 설정
st.set_page_config(
    page_title="성동글로벌경영고등학교 AI 안내",
    page_icon="🏫",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS 스타일
st.markdown("""
<style>
    .main {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    }
    
    .stButton > button {
        border-radius: 25px;
        padding: 10px 25px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(0,0,0,0.2);
    }
    
    h1 {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
    }
    
    audio {
        width: 100%;
        border-radius: 30px;
        margin-top: 10px;
    }
</style>
""", unsafe_allow_html=True)

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

# VRM Viewer HTML 생성 (관리자 설정 URL 사용)
def get_vrm_viewer_html():
    return f"""
    <div style="width: 100%; height: 400px; border-radius: 20px; overflow: hidden; 
                box-shadow: 0 10px 40px rgba(0,0,0,0.15); background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);">
        <iframe 
            id="vrm-iframe"
            srcdoc='
<!DOCTYPE html>
<html>
<head>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ overflow: hidden; }}
        #container {{ width: 100%; height: 100vh; }}
        canvas {{ width: 100%; height: 100%; display: block; }}
        #loading {{
            position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);
            color: white; text-align: center; font-family: sans-serif;
        }}
        .spinner {{
            border: 3px solid rgba(255,255,255,0.3); border-top: 3px solid white;
            border-radius: 50%; width: 30px; height: 30px;
            animation: spin 1s linear infinite; margin: 0 auto 10px;
        }}
        @keyframes spin {{ 0% {{ transform: rotate(0deg); }} 100% {{ transform: rotate(360deg); }} }}
    </style>
</head>
<body>
    <div id="container">
        <canvas id="canvas"></canvas>
        <div id="loading"><div class="spinner"></div><div>아바타 로딩 중...</div></div>
    </div>
    <script type="importmap">
    {{
        "imports": {{
            "three": "https://cdn.jsdelivr.net/npm/three@0.158.0/build/three.module.js",
            "three/addons/": "https://cdn.jsdelivr.net/npm/three@0.158.0/examples/jsm/",
            "@pixiv/three-vrm": "https://cdn.jsdelivr.net/npm/@pixiv/three-vrm@3.1.3/lib/three-vrm.module.min.js"
        }}
    }}
    </script>
    <script type="module">
        import * as THREE from "three";
        import {{ GLTFLoader }} from "three/addons/loaders/GLTFLoader.js";
        import {{ OrbitControls }} from "three/addons/controls/OrbitControls.js";
        import {{ VRMLoaderPlugin, VRMUtils }} from "@pixiv/three-vrm";
        
        const canvas = document.getElementById("canvas");
        const scene = new THREE.Scene();
        scene.background = new THREE.Color(0x667eea);
        
        const camera = new THREE.PerspectiveCamera(30, window.innerWidth/window.innerHeight, 0.1, 100);
        camera.position.set(0, 1.3, -2.5);
        camera.lookAt(0, 1.0, 0);
        
        const renderer = new THREE.WebGLRenderer({{ canvas, antialias: true }});
        renderer.setSize(window.innerWidth, window.innerHeight);
        renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
        renderer.outputColorSpace = THREE.SRGBColorSpace;
        
        const controls = new OrbitControls(camera, canvas);
        controls.target.set(0, 1.0, 0);
        controls.enablePan = false;
        controls.enableDamping = true;
        controls.update();
        
        scene.add(new THREE.AmbientLight(0xffffff, 0.7));
        const light = new THREE.DirectionalLight(0xffffff, 1.0);
        light.position.set(2, 3, 2);
        scene.add(light);
        
        let vrm = null;
        let isSpeaking = false;
        const clock = new THREE.Clock();
        
        const loader = new GLTFLoader();
        loader.register((parser) => new VRMLoaderPlugin(parser));
        loader.load("{VRM_MODEL_URL}", (gltf) => {{
            vrm = gltf.userData.vrm;
            if (vrm) {{
                VRMUtils.removeUnnecessaryVertices(vrm.scene);
                VRMUtils.removeUnnecessaryJoints(vrm.scene);
                
                scene.add(vrm.scene);
                document.getElementById("loading").style.display = "none";
                
                // 자연스러운 팔 자세 설정 (T-pose 해제)
                if (vrm.humanoid) {{
                    const leftUpperArm = vrm.humanoid.getNormalizedBoneNode("leftUpperArm");
                    const rightUpperArm = vrm.humanoid.getNormalizedBoneNode("rightUpperArm");
                    
                    // 팔을 아래로 내리기 (z축 회전)
                    if (leftUpperArm) {{
                        leftUpperArm.rotation.z = 1.0;
                        leftUpperArm.rotation.x = 0.2;
                    }}
                    if (rightUpperArm) {{
                        rightUpperArm.rotation.z = -1.0;
                        rightUpperArm.rotation.x = 0.2;
                    }}
                }}
                
                // 눈 깜빡임
                setInterval(() => {{
                    if (vrm && vrm.expressionManager && !isSpeaking) {{
                        try {{
                            vrm.expressionManager.setValue("blink", 1);
                            setTimeout(() => vrm.expressionManager.setValue("blink", 0), 100);
                        }} catch(e) {{}}
                    }}
                }}, 3000 + Math.random() * 2000);
            }}
        }});
        
        // 립싱크 함수 (외부에서 호출 가능)
        window.startLipSync = function() {{
            isSpeaking = true;
        }};
        
        window.stopLipSync = function() {{
            isSpeaking = false;
            if (vrm && vrm.expressionManager) {{
                try {{
                    vrm.expressionManager.setValue("aa", 0);
                    vrm.expressionManager.setValue("oh", 0);
                }} catch(e) {{}}
            }}
        }};
        
        let lipSyncTime = 0;
        function animate() {{
            requestAnimationFrame(animate);
            const delta = clock.getDelta();
            
            if (vrm) {{
                vrm.update(delta);
                
                // 립싱크 애니메이션
                if (isSpeaking && vrm.expressionManager) {{
                    lipSyncTime += delta * 12;
                    const aa = (Math.sin(lipSyncTime) + 1) * 0.35;
                    const oh = (Math.sin(lipSyncTime * 0.7 + 1) + 1) * 0.2;
                    try {{
                        vrm.expressionManager.setValue("aa", aa);
                        vrm.expressionManager.setValue("oh", oh);
                    }} catch(e) {{}}
                }}
            }}
            
            controls.update();
            renderer.render(scene, camera);
        }}
        animate();
        
        window.addEventListener("resize", () => {{
            camera.aspect = window.innerWidth / window.innerHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(window.innerWidth, window.innerHeight);
        }});
        
        // 메시지 수신 (립싱크 제어)
        window.addEventListener("message", (e) => {{
            if (e.data === "startLipSync") window.startLipSync();
            if (e.data === "stopLipSync") window.stopLipSync();
        }});
    </script>
</body>
</html>
            '
            width="100%" 
            height="100%" 
            style="border: none;"
            allow="autoplay"
        ></iframe>
    </div>
    <div style="text-align: center; margin-top: 10px;">
        <small style="color: #666;">🎭 3D 아바타 (마우스로 드래그하여 회전)</small>
    </div>
    """

# 세션 상태 초기화
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant", 
            "content": "안녕하세요! 성동글로벌경영고등학교 AI 도우미입니다. 😊\n\n학교 교육과정, 입학 안내, 진로진학 등 궁금하신 점을 자유롭게 물어보세요!"
        }
    ]

if "last_audio" not in st.session_state:
    st.session_state.last_audio = None

# 레이아웃 설정
if AVATAR_ENABLED:
    col_chat, col_avatar = st.columns([3, 2])
else:
    col_chat = st.container()

# 왼쪽: 채팅 영역
with col_chat:
    st.title("🏫 성글고 AI 도우미")
    st.markdown("**성동글로벌경영고등학교**에 오신 것을 환영합니다!")
    
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
                    
                    # TTS 생성 (관리자 설정으로 활성화된 경우)
                    if TTS_ENABLED:
                        with st.spinner("🔊 음성을 생성하고 있습니다..."):
                            try:
                                audio_bytes = text_to_speech(response)
                                st.session_state.last_audio = audio_bytes
                                
                                # 오디오 플레이어 표시
                                audio_base64 = get_audio_base64(audio_bytes)
                                st.markdown(f"""
                                <audio controls autoplay>
                                    <source src="data:audio/mp3;base64,{audio_base64}" type="audio/mp3">
                                </audio>
                                """, unsafe_allow_html=True)
                            except Exception as e:
                                st.warning(f"⚠️ 음성 생성 실패: {str(e)}")
                                
                except Exception as e:
                    error_msg = f"죄송합니다. 답변 생성 중 오류가 발생했습니다: {str(e)}"
                    st.error(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})

# 오른쪽: VRM 아바타 영역 (활성화된 경우)
if AVATAR_ENABLED:
    with col_avatar:
        st.markdown("### 🎭 AI 도우미")
        st.components.v1.html(get_vrm_viewer_html(), height=480)
        
        # 마지막 응답 다시 듣기
        if TTS_ENABLED and st.session_state.last_audio:
            if st.button("🔄 마지막 응답 다시 듣기", use_container_width=True):
                audio_base64 = get_audio_base64(st.session_state.last_audio)
                st.markdown(f"""
                <audio controls autoplay>
                    <source src="data:audio/mp3;base64,{audio_base64}" type="audio/mp3">
                </audio>
                """, unsafe_allow_html=True)

# 사이드바
with st.sidebar:
    st.image("https://via.placeholder.com/200x80/667eea/ffffff?text=성글고", use_container_width=True)
    
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
    """)
    
    if TTS_ENABLED:
        st.markdown("- 🔊 답변을 음성으로 들을 수 있습니다")
    
    if AVATAR_ENABLED:
        st.markdown("- 🎭 아바타를 마우스로 드래그하여 회전할 수 있습니다")
    
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
        st.session_state.last_audio = None
        st.rerun()
    
    # 푸터
    st.markdown("---")
    st.caption("🤖 Powered by OpenRouter + Edge TTS")
    st.caption("📅 2025년 성동글로벌경영고등학교")

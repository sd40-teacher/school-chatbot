import streamlit as st
from rag_engine import SchoolChatbot
from tts_engine import text_to_speech, get_audio_base64
import os
import base64

# ============================================================
# 🔧 관리자 설정 영역
# ============================================================

# VRM 아바타 모델 URL (GitHub 저장소의 sdg1.vrm 파일 주소)
VRM_MODEL_URL = "https://raw.githubusercontent.com/sd40-teacher/school-chatbot/main/sdg1.vrm"

# 기능 활성화 설정
TTS_ENABLED = True
AVATAR_ENABLED = True

# ============================================================

# 페이지 설정
st.set_page_config(
    page_title="성동글로벌경영고등학교 AI 안내",
    page_icon="🏫",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS 스타일 적용
st.markdown("""
<style>
    .main { background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); }
    .stButton > button { border-radius: 25px; padding: 10px 25px; font-weight: 600; transition: all 0.3s ease; }
    .stButton > button:hover { transform: translateY(-2px); box-shadow: 0 5px 15px rgba(0,0,0,0.2); }
    h1 { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: 800; }
    audio { width: 100%; border-radius: 30px; margin-top: 10px; }
</style>
""", unsafe_allow_html=True)

# API 키 가져오기
try:
    api_key = st.secrets["OPENROUTER_API_KEY"]
except Exception as e:
    st.error("⚠️ API 키가 설정되지 않았습니다. Secrets를 확인해주세요.")
    st.stop()

# 챗봇 초기화
@st.cache_resource
def load_chatbot():
    with st.spinner("📚 학교 자료를 로드 중입니다..."):
        try:
            chatbot = SchoolChatbot(api_key=api_key, docs_path="data/school_docs")
            return chatbot
        except Exception as e:
            st.error(f"❌ 로드 실패: {e}")
            return None

chatbot = load_chatbot()
if chatbot is None: st.stop()

# VRM Viewer HTML (5개 쉐이프키 반영 버전)
def get_vrm_viewer_html():
    return f"""
    <div style="width: 100%; height: 480px; border-radius: 20px; overflow: hidden; 
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
            color: white; text-align: center; font-family: sans-serif; font-size: 14px;
        }}
    </style>
</head>
<body>
    <div id="container">
        <canvas id="canvas"></canvas>
        <div id="loading">아바타 로딩 중...</div>
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
        camera.position.set(0, 1.4, 2.3);
        
        const renderer = new THREE.WebGLRenderer({{ canvas, antialias: true }});
        renderer.setSize(window.innerWidth, window.innerHeight);
        renderer.setPixelRatio(window.devicePixelRatio);
        renderer.outputColorSpace = THREE.SRGBColorSpace;
        
        const controls = new OrbitControls(camera, canvas);
        controls.target.set(0, 1.1, 0);
        controls.enableDamping = true;
        
        scene.add(new THREE.AmbientLight(0xffffff, 0.8));
        const light = new THREE.DirectionalLight(0xffffff, 1.0);
        light.position.set(1, 2, 3);
        scene.add(light);
        
        let vrm = null;
        let isSpeaking = false;
        const clock = new THREE.Clock();
        
        const loader = new GLTFLoader();
        loader.register((parser) => new VRMLoaderPlugin(parser));
        loader.load("{VRM_MODEL_URL}", (gltf) => {{
            vrm = gltf.userData.vrm;
            if (vrm) {{
                scene.add(vrm.scene);
                vrm.scene.rotation.y = 0; // 블렌더 정면 기준
                document.getElementById("loading").style.display = "none";
                
                setInterval(() => {{
                    if (vrm && vrm.expressionManager && !isSpeaking) {{
                        vrm.expressionManager.setValue("blink", 1);
                        setTimeout(() => vrm.expressionManager.setValue("blink", 0), 120);
                    }}
                }}, 4000 + Math.random() * 2000);
            }}
        }}, undefined, (error) => console.error(error));
        
        // 립싱크 시작/정지 함수
        window.startLipSync = () => {{ isSpeaking = true; }};
        window.stopLipSync = () => {{ 
            isSpeaking = false; 
            if (vrm && vrm.expressionManager) {{
                // 모든 입 모양 초기화 (다물기)
                ["Fcl_MTH_A", "Fcl_MTH_I", "Fcl_MTH_U", "Fcl_MTH_E", "Fcl_MTH_O"].forEach(key => {{
                    vrm.expressionManager.setValue(key, 0);
                }});
            }}
        }};
        
        let lipSyncTime = 0;
        function animate() {{
            requestAnimationFrame(animate);
            const delta = clock.getDelta();
            
            if (vrm) {{
                vrm.update(delta);
                if (isSpeaking && vrm.expressionManager) {{
                    lipSyncTime += delta * 15;
                    // 5개 쉐이프키를 조합하여 자연스러운 입 움직임 생성
                    try {{
                        vrm.expressionManager.setValue("Fcl_MTH_A", (Math.sin(lipSyncTime) + 1) * 0.35);
                        vrm.expressionManager.setValue("Fcl_MTH_I", (Math.cos(lipSyncTime * 0.5) + 1) * 0.1);
                        vrm.expressionManager.setValue("Fcl_MTH_U", (Math.sin(lipSyncTime * 0.8) + 1) * 0.1);
                        vrm.expressionManager.setValue("Fcl_MTH_E", (Math.cos(lipSyncTime * 1.2) + 1) * 0.15);
                        vrm.expressionManager.setValue("Fcl_MTH_O", (Math.sin(lipSyncTime * 0.7) + 1) * 0.2);
                    } catch(e) {{}}
                }}
            }}
            controls.update();
            renderer.render(scene, camera);
        }}
        animate();

        window.addEventListener("message", (e) => {{
            if (e.data === "startLipSync") window.startLipSync();
            if (e.data === "stopLipSync") window.stopLipSync();
        }});
    </script>
</body>
</html>
            '
            width="100%" height="100%" style="border: none;" allow="autoplay"
        ></iframe>
    </div>
    """

# 메시지 기록 세션 초기화
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "안녕하세요! 성동글로벌경영고등학교 AI 도우미입니다. 😊 무엇을 도와드릴까요?"}]
if "last_audio" not in st.session_state:
    st.session_state.last_audio = None

# 레이아웃 구성
if AVATAR_ENABLED:
    col_chat, col_avatar = st.columns([3, 2])
else:
    col_chat = st.container()

with col_chat:
    st.title("🏫 성글고 AI 도우미")
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    if prompt := st.chat_input("학교에 대해 궁금한 점을 물어보세요!"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)
        
        with st.chat_message("assistant"):
            with st.spinner("생각 중..."):
                response = chatbot.ask(prompt)
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
                
                if TTS_ENABLED:
                    audio_bytes = text_to_speech(response)
                    st.session_state.last_audio = audio_bytes
                    audio_base64 = get_audio_base64(audio_bytes)
                    # 오디오 재생 시 부모 iframe에 립싱크 신호 전달
                    st.markdown(f"""
                    <audio id="tts-audio" controls autoplay style="display:none;">
                        <source src="data:audio/mp3;base64,{audio_base64}" type="audio/mp3">
                    </audio>
                    <script>
                        var audio = document.getElementById("tts-audio");
                        // 재생 시 아바타 입 움직임 시작
                        window.parent.postMessage("startLipSync", "*");
                        audio.onplay = function() {{ window.parent.postMessage("startLipSync", "*"); }};
                        // 종료/일시정지 시 아바타 입 움직임 정지
                        audio.onended = function() {{ window.parent.postMessage("stopLipSync", "*"); }};
                        audio.onpause = function() {{ window.parent.postMessage("stopLipSync", "*"); }};
                    </script>
                    """, unsafe_allow_html=True)
                    st.audio(audio_bytes) # 시각적 확인을 위한 플레이어

if AVATAR_ENABLED:
    with col_avatar:
        st.markdown("### 🎭 AI 아바타")
        st.components.v1.html(get_vrm_viewer_html(), height=500)

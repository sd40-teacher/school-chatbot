import streamlit as st
from rag_engine import SchoolChatbot
from tts_engine import text_to_speech, get_audio_base64
import os
import base64

# ============================================================
# 🔧 관리자 설정 영역
# ============================================================
VRM_MODEL_URL = "https://raw.githubusercontent.com/sd40-teacher/school-chatbot/main/sdg1.vrm"
TTS_ENABLED = True
AVATAR_ENABLED = True
# ============================================================

st.set_page_config(
    page_title="성동글로벌경영고등학교 AI 안내",
    page_icon="🏫",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS 스타일 (중괄호 이스케이프 처리 필요 없음 - 일반 문자열)
st.markdown("""
<style>
    .main { background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); }
    .stButton > button { border-radius: 25px; padding: 10px 25px; font-weight: 600; transition: all 0.3s ease; }
    .stButton > button:hover { transform: translateY(-2px); box-shadow: 0 5px 15px rgba(0,0,0,0.2); }
    h1 { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: 800; }
</style>
""", unsafe_allow_html=True)

# API 키 가져오기
try:
    api_key = st.secrets["OPENROUTER_API_KEY"]
except Exception as e:
    st.error("⚠️ API 키가 설정되지 않았습니다.")
    st.stop()

@st.cache_resource
def load_chatbot():
    with st.spinner("📚 학교 자료를 불러오는 중..."):
        try:
            return SchoolChatbot(api_key=api_key, docs_path="data/school_docs")
        except Exception as e:
            st.error(f"❌ 챗봇 로드 실패: {e}")
            return None

chatbot = load_chatbot()
if chatbot is None: st.stop()

# VRM Viewer HTML (중괄호 {{ }} 이스케이프 완료)
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
            color: white; text-align: center; font-family: sans-serif;
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
        camera.position.set(0, 1.3, 2.5);
        
        const renderer = new THREE.WebGLRenderer({{ canvas, antialias: true }});
        renderer.setSize(window.innerWidth, window.innerHeight);
        renderer.outputColorSpace = THREE.SRGBColorSpace;
        
        const controls = new OrbitControls(camera, canvas);
        controls.target.set(0, 1.0, 0);
        controls.enableDamping = true;
        
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
                scene.add(vrm.scene);
                vrm.scene.rotation.y = 0;
                document.getElementById("loading").style.display = "none";
                
                setInterval(() => {{
                    if (vrm && vrm.expressionManager && !isSpeaking) {{
                        vrm.expressionManager.setValue("blink", 1);
                        setTimeout(() => vrm.expressionManager.setValue("blink", 0), 100);
                    }}
                }}, 4000);
            }}
        }});
        
        window.startLipSync = () => {{ isSpeaking = true; }};
        window.stopLipSync = () => {{ 
            isSpeaking = false; 
            if (vrm && vrm.expressionManager) {{
                ["Fcl_MTH_A", "Fcl_MTH_I", "Fcl_MTH_U", "Fcl_MTH_E", "Fcl_MTH_O"].forEach(k => vrm.expressionManager.setValue(k, 0));
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
                    vrm.expressionManager.setValue("Fcl_MTH_A", (Math.sin(lipSyncTime) + 1) * 0.35);
                    vrm.expressionManager.setValue("Fcl_MTH_I", (Math.cos(lipSyncTime * 0.6) + 1) * 0.1);
                    vrm.expressionManager.setValue("Fcl_MTH_U", (Math.sin(lipSyncTime * 0.8) + 1) * 0.1);
                    vrm.expressionManager.setValue("Fcl_MTH_E", (Math.cos(lipSyncTime * 1.1) + 1) * 0.15);
                    vrm.expressionManager.setValue("Fcl_MTH_O", (Math.sin(lipSyncTime * 0.7) + 1) * 0.2);
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

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "안녕하세요! 성동글로벌경영고등학교 AI 도우미입니다. 😊"}]
if "last_audio" not in st.session_state:
    st.session_state.last_audio = None

if AVATAR_ENABLED:
    col_chat, col_avatar = st.columns([3, 2])
else:
    col_chat = st.container()

with col_chat:
    st.title("🏫 성글고 AI 도우미")
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]): st.markdown(msg["content"])
    
    if prompt := st.chat_input("질문을 입력하세요"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)
        
        with st.chat_message("assistant"):
            response = chatbot.ask(prompt)
            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})
            
            if TTS_ENABLED:
                audio_bytes = text_to_speech(response)
                st.session_state.last_audio = audio_bytes
                audio_base64 = get_audio_base64(audio_bytes)
                st.markdown(f"""
                <audio id="audio-player" controls autoplay style="display:none;">
                    <source src="data:audio/mp3;base64,{audio_base64}" type="audio/mp3">
                </audio>
                <script>
                    var audio = document.getElementById("audio-player");
                    window.parent.postMessage("startLipSync", "*");
                    audio.onplay = function() {{ window.parent.postMessage("startLipSync", "*"); }};
                    audio.onended = function() {{ window.parent.postMessage("stopLipSync", "*"); }};
                    audio.onpause = function() {{ window.parent.postMessage("stopLipSync", "*"); }};
                </script>
                """, unsafe_allow_html=True)
                st.audio(audio_bytes)

if AVATAR_ENABLED:
    with col_avatar:
        st.markdown("### 🎭 AI 아바타")
        st.components.v1.html(get_vrm_viewer_html(), height=500)

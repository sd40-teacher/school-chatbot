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
    layout="wide"
)

# API 키 가져오기
try:
    api_key = st.secrets["OPENROUTER_API_KEY"]
except Exception as e:
    st.error("⚠️ API 키가 설정되지 않았습니다.")
    st.stop()

@st.cache_resource
def load_chatbot():
    try:
        return SchoolChatbot(api_key=api_key, docs_path="data/school_docs")
    except Exception as e:
        return None

chatbot = load_chatbot()

def get_vrm_viewer_html():
    return f"""
    <div style="width: 100%; height: 500px; border-radius: 20px; overflow: hidden; 
                box-shadow: 0 10px 40px rgba(0,0,0,0.15); background: #667eea;">
        <iframe 
            id="vrm-iframe"
            srcdoc='
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ margin: 0; overflow: hidden; background: #667eea; }}
        #container {{ width: 100%; height: 100vh; }}
    </style>
</head>
<body>
    <div id="container"></div>
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
        import {{ VRMLoaderPlugin }} from "@pixiv/three-vrm";
        
        const scene = new THREE.Scene();
        const camera = new THREE.PerspectiveCamera(30, window.innerWidth/window.innerHeight, 0.1, 100);
        camera.position.set(0, 1.35, 2.0);
        
        const renderer = new THREE.WebGLRenderer({{ antialias: true, alpha: true }});
        renderer.setSize(window.innerWidth, window.innerHeight);
        renderer.outputColorSpace = THREE.SRGBColorSpace;
        document.getElementById("container").appendChild(renderer.domElement);
        
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
            scene.add(vrm.scene);
            vrm.scene.rotation.y = 0;
            console.log("VRM 로드 완료", vrm);
        }});
        
        // 부모 창으로부터 메시지 수신 (가장 확실한 방법)
        window.addEventListener("message", (e) => {{
            if (e.data === "startLipSync") {{ isSpeaking = true; console.log("입 움직임 시작"); }}
            if (e.data === "stopLipSync") {{ 
                isSpeaking = false; 
                if (vrm && vrm.expressionManager) {{
                    // 모든 입 모양 초기화
                    ["aa","ih","ou","ee","oh","Fcl_MTH_A","Fcl_MTH_I","Fcl_MTH_U","Fcl_MTH_E","Fcl_MTH_O"].forEach(n => {{
                        try {{ vrm.expressionManager.setValue(n, 0); }} catch(err) {{}}
                    }});
                }}
            }}
        }});

        function animate() {{
            requestAnimationFrame(animate);
            const delta = clock.getDelta();
            if (vrm) {{
                vrm.update(delta);
                if (isSpeaking && vrm.expressionManager) {{
                    const s = (Math.sin(Date.now() * 0.015) + 1) * 0.4;
                    // 표준 이름과 커스텀 이름 모두에 값 부여 (안전장치)
                    const names = ["aa", "oh", "Fcl_MTH_A", "Fcl_MTH_O"];
                    names.forEach(n => {{
                        try {{ vrm.expressionManager.setValue(n, s); }} catch(e) {{}}
                    }});
                }}
            }}
            renderer.render(scene, camera);
        }}
        animate();
    </script>
</body>
</html>
            '
            style="border: none; width: 100%; height: 100%;"
        ></iframe>
    </div>
    """

# 채팅 UI
st.title("🏫 성글고 AI 도우미")

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "안녕하세요! 무엇을 도와드릴까요?"}]

col1, col2 = st.columns([3, 2])

with col1:
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]): st.markdown(msg["content"])

    if prompt := st.chat_input("질문하세요"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)
        
        with st.chat_message("assistant"):
            response = chatbot.ask(prompt)
            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})
            
            if TTS_ENABLED:
                audio_bytes = text_to_speech(response)
                audio_base64 = get_audio_base64(audio_bytes)
                
                # JavaScript를 통한 iframe 직접 제어
                st.markdown(f"""
                <audio id="audio-tag" src="data:audio/mp3;base64,{audio_base64}" autoplay style="display:none;"></audio>
                <script>
                    var audio = document.getElementById("audio-tag");
                    var iframe = window.parent.document.querySelector("iframe[srcdoc*='vrm-iframe']");
                    
                    function send(msg) {{
                        const frames = window.parent.document.getElementsByTagName("iframe");
                        for (let f of frames) {{
                            f.contentWindow.postMessage(msg, "*");
                        }}
                    }}

                    audio.onplay = () => send("startLipSync");
                    audio.onended = () => send("stopLipSync");
                    audio.onpause = () => send("stopLipSync");
                    
                    // 재생 시작 강제 트리거
                    audio.play().then(() => send("startLipSync"));
                </script>
                """, unsafe_allow_html=True)

with col2:
    if AVATAR_ENABLED:
        st.markdown("### 🎭 AI 아바타")
        st.components.v1.html(get_vrm_viewer_html(), height=550)

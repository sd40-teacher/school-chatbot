import streamlit as st
from rag_engine import SchoolChatbot
from tts_engine import text_to_speech, get_audio_base64
import os
import base64

# ============================================================
# 🔧 1. 앱 설정
# ============================================================
VRM_MODEL_URL = "https://raw.githubusercontent.com/sd40-teacher/school-chatbot/main/sdg1.vrm"

st.set_page_config(page_title="성글고 AI 도우미", page_icon="🏫", layout="wide")

# API 키 및 챗봇 로드
try:
    api_key = st.secrets["OPENROUTER_API_KEY"]
except:
    st.error("⚠️ API 키가 설정되지 않았습니다.")
    st.stop()

@st.cache_resource
def load_chatbot():
    try:
        return SchoolChatbot(api_key=api_key, docs_path="data/school_docs")
    except:
        return None

chatbot = load_chatbot()

# ============================================================
# 🔧 2. 아바타 & 오디오 통합 컴포넌트 (신규 로직)
# ============================================================
def vrm_viewer_component(audio_base64=None, refresh_key=0):
    # 오디오 데이터가 있을 때만 재생 버튼을 표시하도록 자바스크립트 수정
    audio_js = ""
    display_button = "none"
    if audio_base64:
        display_button = "block"
        audio_js = f"""
            const audio = document.getElementById("vrm-audio");
            audio.src = "data:audio/mp3;base64,{audio_base64}";
            
            // 버튼 클릭 시 재생 (브라우저 보안 완벽 통과)
            document.getElementById("play-btn").onclick = () => {{
                audio.play();
                document.getElementById("play-btn").style.display = "none";
            }};
            
            // 자동 재생 시도 (사용자가 이미 화면을 클릭한 적이 있다면 바로 재생됨)
            audio.play().then(() => {{
                document.getElementById("play-btn").style.display = "none";
            }}).catch(() => {{
                document.getElementById("play-btn").style.display = "block";
            }});
        """

    html_code = f"""
    <div style="width: 100%; height: 550px; background: #667eea; border-radius: 15px; position: relative; overflow: hidden;">
        <canvas id="vrm-canvas" style="width: 100%; height: 100%; cursor: grab;"></canvas>
        <audio id="vrm-audio" style="display:none;"></audio>
        
        <button id="play-btn" style="display:{display_button}; position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); 
            padding: 15px 30px; font-size: 18px; cursor: pointer; background: #ff4b4b; color: white; border: none; border-radius: 50px; 
            box-shadow: 0 4px 15px rgba(0,0,0,0.3); z-index: 100;">
            ▶ 답변 듣기 (클릭)
        </button>

        <div id="loading" style="position: absolute; top: 10px; left: 10px; color: white; font-family: sans-serif; font-size: 12px;">모델 로딩 중...</div>

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
            import {{ VRMLoaderPlugin }} from "@pixiv/three-vrm";

            let vrm = null;
            const scene = new THREE.Scene();
            const camera = new THREE.PerspectiveCamera(35, window.innerWidth/window.innerHeight, 0.1, 100);
            camera.position.set(0, 1.4, 2.5);

            const renderer = new THREE.WebGLRenderer({{ canvas: document.getElementById("vrm-canvas"), antialias: true, alpha: true }});
            renderer.setSize(window.innerWidth, window.innerHeight);
            renderer.setPixelRatio(window.devicePixelRatio);
            renderer.outputColorSpace = THREE.SRGBColorSpace;

            const controls = new OrbitControls(camera, renderer.domElement);
            controls.target.set(0, 1.2, 0);
            controls.update();

            scene.add(new THREE.AmbientLight(0xffffff, 1.0));
            const light = new THREE.DirectionalLight(0xffffff, 1.0);
            light.position.set(1, 2, 3);
            scene.add(light);

            const loader = new GLTFLoader();
            loader.register((parser) => new VRMLoaderPlugin(parser));
            loader.load("{VRM_MODEL_URL}", (gltf) => {{
                vrm = gltf.userData.vrm;
                scene.add(vrm.scene);
                vrm.scene.rotation.y = Math.PI;
                document.getElementById("loading").style.display = "none";
                {audio_js}
            }});

            const audio = document.getElementById("vrm-audio");
            const clock = new THREE.Clock();

            function animate() {{
                requestAnimationFrame(animate);
                const delta = clock.getDelta();
                if (vrm) {{
                    vrm.update(delta);
                    if (!audio.paused && !audio.ended && vrm.expressionManager) {{
                        const t = Date.now() * 0.012;
                        vrm.expressionManager.setValue("Fcl_MTH_A", (Math.sin(t) + 1) * 0.4);
                        vrm.expressionManager.setValue("Fcl_MTH_O", (Math.cos(t * 0.7) + 1) * 0.3);
                    }} else if (vrm.expressionManager) {{
                        ["Fcl_MTH_A","Fcl_MTH_I","Fcl_MTH_U","Fcl_MTH_E","Fcl_MTH_O"].forEach(k => {{
                            try {{ vrm.expressionManager.setValue(k, 0); }} catch(e) {{}}
                        }});
                    }}
                }}
                controls.update();
                renderer.render(scene, camera);
            }}
            animate();
        </script>
    </div>
    """
    st.components.v1.html(html_code, height=550)

# ============================================================
# 🔧 3. 메인 화면
# ============================================================
st.title("🏫 성글고 AI 도우미")

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "안녕하세요! 궁금한 점을 물어봐 주세요. 😊"}]
if "current_audio" not in st.session_state:
    st.session_state.current_audio = None
if "refresh_count" not in st.session_state:
    st.session_state.refresh_count = 0

col_chat, col_vrm = st.columns([3, 2])

with col_chat:
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]): st.markdown(msg["content"])

    if prompt := st.chat_input("질문하세요"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)

        with st.chat_message("assistant"):
            response = chatbot.ask(prompt)
            st.markdown(response)
            
            audio_bytes = text_to_speech(response)
            audio_base64 = get_audio_base64(audio_bytes)
            
            st.session_state.messages.append({"role": "assistant", "content": response})
            st.session_state.current_audio = audio_base64
            st.session_state.refresh_count += 1
            st.rerun()

with col_vrm:
    st.subheader("🎭 AI 도우미")
    
    # 이 버튼을 누르면 refresh_count가 바뀌어 iframe이 완전히 새로 고침됩니다.
    if st.button("🔄 마지막 답변 다시 듣기", use_container_width=True):
        if st.session_state.current_audio:
            st.session_state.refresh_count += 1
            st.rerun()

    vrm_viewer_component(st.session_state.current_audio, st.session_state.refresh_count)

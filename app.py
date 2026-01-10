import streamlit as st
from rag_engine import SchoolChatbot
from tts_engine import text_to_speech, get_audio_base64
import os
import base64

# ============================================================
# 🔧 1. 앱 설정 및 스타일
# ============================================================
VRM_MODEL_URL = "https://raw.githubusercontent.com/sd40-teacher/school-chatbot/main/sdg1.vrm"

st.set_page_config(
    page_title="성동글로벌경영고등학교 AI 안내",
    page_icon="🏫",
    layout="wide"
)

st.markdown("""
<style>
    .stApp { background: #f8f9fa; }
    .stChatMessage { border-radius: 15px; margin-bottom: 10px; }
</style>
""", unsafe_allow_html=True)

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
# 🔧 2. 아바타 & 오디오 통합 뷰어 (TypeError 수정 버전)
# ============================================================
def vrm_viewer_component(audio_base64=None, refresh_count=0):
    audio_js = ""
    if audio_base64:
        audio_js = f"""
            const audio = document.getElementById("vrm-audio");
            audio.src = "data:audio/mp3;base64,{audio_base64}";
            const playAudio = () => {{
                audio.play().catch(e => {{
                    window.addEventListener("click", () => audio.play(), {{ once: true }});
                }});
            }};
            playAudio();
        """

    # key 대신 HTML 내부에 주석을 넣어 
    # 문자열이 변경될 때마다 Streamlit이 새로 그리도록 유도합니다.
    html_code = f"""
    <div style="width: 100%; height: 550px; background: #667eea; border-radius: 15px; position: relative; overflow: hidden;">
        <audio id="vrm-audio" style="display:none;"></audio>
        <canvas id="vrm-canvas" style="width: 100%; height: 100%; cursor: grab;"></canvas>
        <div id="loading" style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); color: white; font-family: sans-serif;">로딩 중...</div>
        
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

            const renderer = new THREE.WebGLRenderer({{ 
                canvas: document.getElementById("vrm-canvas"), 
                antialias: true, 
                alpha: true 
            }});
            renderer.setSize(window.innerWidth, window.innerHeight);
            renderer.setPixelRatio(window.devicePixelRatio);
            renderer.outputColorSpace = THREE.SRGBColorSpace;

            const controls = new OrbitControls(camera, renderer.domElement);
            controls.target.set(0, 1.2, 0);
            controls.enableDamping = true;

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
                        const val = (Math.sin(t) + 1) * 0.5;
                        try {{
                            vrm.expressionManager.setValue("Fcl_MTH_A", val * 0.4);
                            vrm.expressionManager.setValue("Fcl_MTH_I", (Math.cos(t*0.7)+1) * 0.1);
                            vrm.expressionManager.setValue("Fcl_MTH_U", (Math.sin(t*0.5)+1) * 0.15);
                            vrm.expressionManager.setValue("Fcl_MTH_E", (Math.cos(t*0.8)+1) * 0.2);
                            vrm.expressionManager.setValue("Fcl_MTH_O", val * 0.3);
                        }} catch(e) {{}}
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
    # key 매개변수를 제거하여 TypeError 해결
    st.components.v1.html(html_code, height=550)

# ============================================================
# 🔧 3. 메인 로직
# ============================================================
st.title("🏫 성글고 AI 도우미")

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "안녕하세요! 성글고 AI 도우미입니다. 😊"}]
if "current_audio" not in st.session_state:
    st.session_state.current_audio = None
if "refresh_count" not in st.session_state:
    st.session_state.refresh_count = 0

col_chat, col_vrm = st.columns([3, 2])

with col_chat:
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("질문하세요"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

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
    
    if st.button("🔄 마지막 답변 다시 듣기", use_container_width=True):
        if st.session_state.current_audio:
            st.session_state.refresh_count += 1
            st.rerun()
        else:
            st.warning("먼저 질문을 해서 답변을 생성해 주세요.")

    # 수정된 함수 호출
    vrm_viewer_component(
        audio_base64=st.session_state.current_audio, 
        refresh_count=st.session_state.refresh_count
    )

with st.sidebar:
    if st.button("🔄 대화 초기화"):
        st.session_state.messages = [{"role": "assistant", "content": "안녕하세요! 😊"}]
        st.session_state.current_audio = None
        st.session_state.refresh_count = 0
        st.rerun()

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

try:
    api_key = st.secrets["OPENROUTER_API_KEY"]
except:
    st.error("⚠️ API 키가 설정되지 않았습니다.")
    st.stop()

@st.cache_resource
def load_chatbot():
    try:
        return SchoolChatbot(api_key=api_key, docs_path="data/school_docs")
    except Exception as e:
        return None

chatbot = load_chatbot()

# ============================================================
# 🔧 2. 아바타 & 오디오 통합 뷰어 (카메라 유지 + Idle 복구)
# ============================================================
def vrm_viewer_component(audio_base64=None):
    audio_init_js = ""
    if audio_base64:
        audio_init_js = f"""
            const audio = document.getElementById("vrm-audio");
            audio.src = "data:audio/mp3;base64,{audio_base64}";
            const btn = document.getElementById("play-btn");
            btn.style.background = "#ff4b4b";
            btn.innerText = "▶ 답변 듣기 (클릭)";
        """

    html_code = f"""
    <div style="width: 100%; height: 620px; background: #8a94c8; border-radius: 20px; position: relative; overflow: hidden; display: flex; flex-direction: column;">
        <canvas id="vrm-canvas" style="width: 100%; height: 500px; cursor: grab;"></canvas>
        <audio id="vrm-audio" style="display:none;"></audio>
        
        <div style="height: 120px; background: #667eea; display: flex; justify-content: center; align-items: center;">
            <button id="play-btn" style="
                padding: 15px 40px; font-size: 18px; font-weight: bold; cursor: pointer; 
                background: #4CAF50; color: white; border: none; border-radius: 15px; 
                box-shadow: 0 4px 15px rgba(0,0,0,0.3); width: 85%;">
                {"🔈 질문을 입력하세요" if not audio_base64 else "▶ 답변 듣기 / 다시 듣기"}
            </button>
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
            import {{ VRMLoaderPlugin }} from "@pixiv/three-vrm";

            let vrm = null;
            const scene = new THREE.Scene();
            const canvas = document.getElementById("vrm-canvas");
            
            // [카메라 고정] 이전 버전에서 성공했던 앵글 유지
            const camera = new THREE.PerspectiveCamera(30, canvas.clientWidth / canvas.clientHeight, 0.1, 100);
            camera.position.set(0, 1.3, 2.5); 

            const renderer = new THREE.WebGLRenderer({{ canvas: canvas, antialias: true, alpha: true }});
            renderer.setSize(canvas.clientWidth, canvas.clientHeight);
            renderer.setPixelRatio(window.devicePixelRatio);

            const controls = new OrbitControls(camera, renderer.domElement);
            controls.target.set(0, 1.2, 0); 
            controls.update();

            scene.add(new THREE.AmbientLight(0xffffff, 0.7));
            const light = new THREE.DirectionalLight(0xffffff, 1.0);
            light.position.set(1, 2, 3);
            scene.add(light);

            const loader = new GLTFLoader();
            loader.register((parser) => new VRMLoaderPlugin(parser));
            loader.load("{VRM_MODEL_URL}", (gltf) => {{
                vrm = gltf.userData.vrm;
                scene.add(vrm.scene);
                vrm.scene.rotation.y = Math.PI;
                {audio_init_js}
            }});

            const audio = document.getElementById("vrm-audio");
            const btn = document.getElementById("play-btn");
            btn.onclick = () => {{ if(audio.src && audio.paused) {{ audio.currentTime = 0; audio.play(); btn.innerText = "💬 답변 중..."; }} }};
            audio.onended = () => {{ btn.innerText = "🔄 다시 듣기"; }};

            const clock = new THREE.Clock();
            function animate() {{
                requestAnimationFrame(animate);
                const delta = clock.getDelta();
                const time = clock.elapsedTime;

                if (vrm) {{
                    // --- [IDLE 동작 복구] ---
                    const spine = vrm.humanoid.getNormalizedBoneNode('spine');
                    const neck = vrm.humanoid.getNormalizedBoneNode('neck');
                    const hips = vrm.humanoid.getNormalizedBoneNode('hips');

                    // 부드러운 흔들림 효과
                    if(spine) spine.rotation.x = Math.sin(time * 1.5) * 0.03; 
                    if(neck) neck.rotation.y = Math.sin(time * 0.7) * 0.05; 
                    if(hips) hips.position.y = Math.sin(time * 1.5) * 0.005;

                    vrm.update(delta);

                    // 립싱크 (입 모양)
                    if (!audio.paused && !audio.ended && vrm.expressionManager) {{
                        const s = (Math.sin(Date.now() * 0.015) + 1) * 0.4;
                        ["aa", "oh", "Fcl_MTH_A", "Fcl_MTH_O"].forEach(k => {{
                            try {{ vrm.expressionManager.setValue(k, s); }} catch(e) {{}}
                        }});
                    }} else if (vrm.expressionManager) {{
                        ["aa","Fcl_MTH_A"].forEach(k => {{ try {{ vrm.expressionManager.setValue(k, 0); }} catch(e) {{}} }});
                    }}
                }}
                renderer.render(scene, camera);
            }}
            animate();
        </script>
    </div>
    """
    st.components.v1.html(html_code, height=640)

# (이하 메인 화면 구성 코드는 이전과 동일합니다...)
st.title("🏫 성글고 AI 도우미")

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "안녕하세요! 궁금한 점을 물어봐 주세요. 😊"}]
if "current_audio" not in st.session_state:
    st.session_state.current_audio = None

col_chat, col_vrm = st.columns([3, 2])

with col_chat:
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]): st.markdown(msg["content"])
    if prompt := st.chat_input("질문을 입력하세요..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)
        with st.chat_message("assistant"):
            if chatbot:
                response = chatbot.ask(prompt)
                st.markdown(response)
                audio_bytes = text_to_speech(response)
                audio_base64 = get_audio_base64(audio_bytes)
                st.session_state.messages.append({"role": "assistant", "content": response})
                st.session_state.current_audio = audio_base64
                st.rerun()

with col_vrm:
    st.subheader("🎭 AI 아바타")
    vrm_viewer_component(st.session_state.current_audio)

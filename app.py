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
# 🔧 2. 아바타 & 오디오 통합 뷰어
# ============================================================
def vrm_viewer_component(audio_base64=None, refresh_count=0):
    # 오디오 주입 로직
    audio_init_js = ""
    if audio_base64:
        audio_init_js = f"""
            const audio = document.getElementById("vrm-audio");
            audio.src = "data:audio/mp3;base64,{audio_base64}";
            // 새 답변이 오면 버튼을 강조
            const btn = document.getElementById("play-btn");
            btn.style.background = "#ff4b4b";
            btn.innerText = "▶ 답변 듣기";
        """

    html_code = f"""
    <div style="width: 100%; height: 580px; background: #667eea; border-radius: 20px; position: relative; overflow: hidden; display: flex; flex-direction: column;">
        <canvas id="vrm-canvas" style="flex: 1; width: 100%; cursor: grab;"></canvas>
        
        <audio id="vrm-audio" style="display:none;"></audio>
        
        <div style="padding: 15px; background: rgba(0,0,0,0.2); display: flex; justify-content: center; align-items: center;">
            <button id="play-btn" style="
                padding: 12px 25px; font-size: 16px; font-weight: bold; cursor: pointer; 
                background: #4CAF50; color: white; border: none; border-radius: 10px; 
                box-shadow: 0 4px 10px rgba(0,0,0,0.2); transition: 0.2s;">
                {"🔈 답변 대기 중" if not audio_base64 else "▶ 답변 듣기 / 다시 듣기"}
            </button>
        </div>

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
            const camera = new THREE.PerspectiveCamera(35, window.innerWidth/(window.innerHeight-60), 0.1, 100);
            camera.position.set(0, 1.4, 2.2);

            const renderer = new THREE.WebGLRenderer({{ canvas: document.getElementById("vrm-canvas"), antialias: true, alpha: true }});
            renderer.setSize(window.innerWidth, window.innerHeight - 60);
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
                {audio_init_js}
            }});

            const audio = document.getElementById("vrm-audio");
            const btn = document.getElementById("play-btn");
            
            // 버튼 클릭 이벤트
            btn.onclick = () => {{
                if(audio.src) {{
                    audio.currentTime = 0;
                    audio.play();
                    btn.style.background = "#666";
                    btn.innerText = "💬 답변 읽어주는 중...";
                }}
            }};
            
            audio.onended = () => {{
                btn.style.background = "#4CAF50";
                btn.innerText = "🔄 다시 듣기";
            }};

            const clock = new THREE.Clock();
            function animate() {{
                requestAnimationFrame(animate);
                const delta = clock.getDelta();
                if (vrm) {{
                    vrm.update(delta);
                    // 오디오가 재생 중일 때만 입 움직임
                    if (!audio.paused && !audio.ended && vrm.expressionManager) {{
                        const t = Date.now() * 0.012;
                        const s = (Math.sin(t) + 1) * 0.5;
                        
                        // 모든 가능한 쉐이프키 이름에 값 주입
                        const mouthKeys = ["aa", "oh", "Fcl_MTH_A", "Fcl_MTH_O"];
                        mouthKeys.forEach(k => {{
                            try {{ vrm.expressionManager.setValue(k, s * 0.5); }} catch(e) {{}}
                        }});
                    }} else if (vrm.expressionManager) {{
                        // 종료 시 입 다물기
                        ["aa","ih","ou","ee","oh","Fcl_MTH_A","Fcl_MTH_I","Fcl_MTH_U","Fcl_MTH_E","Fcl_MTH_O"].forEach(k => {{
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
    st.components.v1.html(html_code, height=600)

# ============================================================
# 🔧 3. 메인 화면 구성
# ============================================================
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
            response = chatbot.ask(prompt)
            st.markdown(response)
            
            # 음성 생성
            audio_bytes = text_to_speech(response)
            audio_base64 = get_audio_base64(audio_bytes)
            
            st.session_state.messages.append({"role": "assistant", "content": response})
            st.session_state.current_audio = audio_base64
            st.rerun()

with col_vrm:
    st.subheader("🎭 AI 아바타")
    # 아바타 창 내부에 재생/다시듣기 버튼이 포함되어 있습니다.
    vrm_viewer_component(st.session_state.current_audio)

    with st.expander("ℹ️ 이용 안내"):
        st.write("1. 질문을 입력하면 아바타가 답변을 준비합니다.")
        st.write("2. 답변이 완료되면 아바타 하단의 **[▶ 답변 듣기]** 버튼을 눌러주세요.")
        st.write("3. 입 모양과 함께 음성이 재생됩니다.")

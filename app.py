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
# 🔧 2. 아바타 & 오디오 통합 뷰어 (대기 동작 추가됨)
# ============================================================
def vrm_viewer_component(audio_base64=None, refresh_count=0):
    audio_init_js = ""
    if audio_base64:
        audio_init_js = f"""
            const audio = document.getElementById("vrm-audio");
            audio.src = "data:audio/mp3;base64,{audio_base64}";
            const btn = document.getElementById("play-btn");
            btn.style.background = "#ff4b4b";
            btn.innerText = "▶ 답변 듣기 (준비됨)";
        """

    html_code = f"""
    <div style="width: 100%; height: 600px; background: #667eea; border-radius: 20px; position: relative; overflow: hidden; display: flex; flex-direction: column;">
        <canvas id="vrm-canvas" style="flex: 1; width: 100%; cursor: grab;"></canvas>
        <audio id="vrm-audio" style="display:none;"></audio>
        
        <div style="padding: 15px; background: rgba(0,0,0,0.2); display: flex; justify-content: center; align-items: center;">
            <button id="play-btn" style="
                padding: 12px 30px; font-size: 16px; font-weight: bold; cursor: pointer; 
                background: #4CAF50; color: white; border: none; border-radius: 30px; 
                box-shadow: 0 4px 10px rgba(0,0,0,0.2); transition: 0.3s;">
                {"🔈 질문을 입력해주세요" if not audio_base64 else "▶ 답변 듣기 / 다시 듣기"}
            </button>
        </div>

        <div id="loading" style="position: absolute; top: 20px; left: 20px; color: white; font-family: sans-serif; font-weight: bold; text-shadow: 1px 1px 2px rgba(0,0,0,0.5);">모델 로딩 중...</div>

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
            // 배경색을 좀 더 부드럽게 변경
            scene.background = new THREE.Color(0x8a94c8); 
            const camera = new THREE.PerspectiveCamera(30, window.innerWidth/(window.innerHeight-60), 0.1, 100);
            camera.position.set(0, 1.3, 2.3);

            const renderer = new THREE.WebGLRenderer({{ canvas: document.getElementById("vrm-canvas"), antialias: true }});
            renderer.setSize(window.innerWidth, window.innerHeight - 60);
            renderer.setPixelRatio(window.devicePixelRatio);
            renderer.outputColorSpace = THREE.SRGBColorSpace;

            const controls = new OrbitControls(camera, renderer.domElement);
            controls.target.set(0, 1.1, 0);
            controls.enableDamping = true;
            controls.update();

            scene.add(new THREE.AmbientLight(0xffffff, 0.6));
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
                
                // [초기 자세 설정] 팔을 자연스럽게 내리기
                const leftArm = vrm.humanoid.getNormalizedBoneNode('leftUpperArm');
                const rightArm = vrm.humanoid.getNormalizedBoneNode('rightUpperArm');
                if(leftArm) leftArm.rotation.z = 1.2; 
                if(rightArm) rightArm.rotation.z = -1.2;

                {audio_init_js}
            }});

            const audio = document.getElementById("vrm-audio");
            const btn = document.getElementById("play-btn");
            
            btn.onclick = () => {{
                if(audio.src && audio.paused) {{
                    audio.currentTime = 0;
                    audio.play();
                    btn.style.background = "#FF9800";
                    btn.innerText = "💬 답변 말하는 중...";
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
                const time = clock.elapsedTime; // 흐른 시간 측정

                if (vrm) {{
                    // --- [1. 대기 동작 (Idle Animation)] ---
                    // 척추, 목, 팔 등의 뼈를 가져옵니다.
                    const spine = vrm.humanoid.getNormalizedBoneNode('spine');
                    const neck = vrm.humanoid.getNormalizedBoneNode('neck');
                    const hips = vrm.humanoid.getNormalizedBoneNode('hips');

                    // Math.sin(time)을 이용해 부드럽게 흔들리는 움직임을 만듭니다.
                    // 척추 앞뒤 흔들림 (숨쉬기)
                    if(spine) spine.rotation.x = Math.sin(time * 1.5) * 0.03; 
                    // 목 좌우 살짝 도리도리
                    if(neck) neck.rotation.y = Math.sin(time * 0.7) * 0.05; 
                    // 목 위아래 살짝 끄덕임
                    if(neck) neck.rotation.x = Math.sin(time * 1.2) * 0.02;
                    // 골반 살짝 위아래 (호흡)
                    if(hips) hips.position.y = Math.sin(time * 1.5) * 0.005;

                    // --- [2. 립싱크 및 업데이트] ---
                    vrm.update(delta);

                    if (!audio.paused && !audio.ended && vrm.expressionManager) {{
                        const t = Date.now() * 0.015;
                        vrm.expressionManager.setValue("Fcl_MTH_A", (Math.sin(t) + 1) * 0.4);
                        vrm.expressionManager.setValue("Fcl_MTH_O", (Math.cos(t * 0.8) + 1) * 0.3);
                        vrm.expressionManager.setValue("aa", (Math.sin(t * 1.2) + 1) * 0.3);
                    }} else if (vrm.expressionManager) {{
                        ["Fcl_MTH_A","Fcl_MTH_O","aa","ih","ou","ee","oh"].forEach(k => {{
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
    st.components.v1.html(html_code, height=620)

# ============================================================
# 🔧 3. 메인 화면 구성
# ============================================================
st.title("🏫 성글고 AI 도우미")

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "안녕하세요! 성동글로벌경영고등학교 AI 도우미입니다. 😊"}]
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
            
            audio_bytes = text_to_speech(response)
            audio_base64 = get_audio_base64(audio_bytes)
            
            st.session_state.messages.append({"role": "assistant", "content": response})
            st.session_state.current_audio = audio_base64
            st.rerun()

with col_vrm:
    st.subheader("🎭 AI 아바타")
    vrm_viewer_component(st.session_state.current_audio)

    with st.expander("ℹ️ 이용 안내"):
        st.write("아바타 하단의 **[▶ 답변 듣기]** 버튼을 눌러 음성과 입 모양을 확인하세요.")

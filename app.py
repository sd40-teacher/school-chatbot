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

# UI 스타일 개선
st.markdown("""
<style>
    .stApp { background: #f8f9fa; }
    .stChatMessage { border-radius: 15px; margin-bottom: 10px; }
    .avatar-container { border: 3px solid #667eea; border-radius: 20px; overflow: hidden; background: #667eea; }
</style>
""", unsafe_allow_html=True)

# API 키 및 챗봇 로드
try:
    api_key = st.secrets["OPENROUTER_API_KEY"]
except:
    st.error("⚠️ API 키가 없습니다.")
    st.stop()

@st.cache_resource
def load_chatbot():
    try:
        return SchoolChatbot(api_key=api_key, docs_path="data/school_docs")
    except:
        return None

chatbot = load_chatbot()

# ============================================================
# 🔧 2. 아바타 & 오디오 통합 뷰어 함수 (핵심 수정 부분)
# ============================================================
def vrm_viewer_component(audio_base64=None):
    # 오디오 데이터가 있으면 자바스크립트로 자동 재생 명령을 내립니다.
    audio_trigger = ""
    if audio_base64:
        audio_trigger = f"""
            const audio = document.getElementById("vrm-audio");
            audio.src = "data:audio/mp3;base64,{audio_base64}";
            audio.play().catch(e => console.log("자동 재생 차단됨:", e));
        """

    html_code = f"""
    <div style="width: 100%; height: 500px; background: #667eea; border-radius: 15px; position: relative;">
        <audio id="vrm-audio" style="display:none;"></audio>
        <canvas id="vrm-canvas" style="width: 100%; height: 100%; cursor: grab;"></canvas>
        <div id="loading" style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); color: white;">모델 로드 중...</div>
        
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
                vrm.scene.rotation.y = Math.PI; // 정면 설정
                document.getElementById("loading").style.display = "none";
                {audio_trigger} // 모델 로드 후 오디오 재생 실행
            }});

            const audio = document.getElementById("vrm-audio");
            const clock = new THREE.Clock();

            function animate() {{
                requestAnimationFrame(animate);
                const delta = clock.getDelta();
                if (vrm) {{
                    vrm.update(delta);
                    
                    // 오디오 재생 중일 때만 입 움직임 (5개 쉐이프키 조합)
                    if (!audio.paused && !audio.ended && vrm.expressionManager) {{
                        const t = Date.now() * 0.012;
                        const val = (Math.sin(t) + 1) * 0.5;
                        
                        try {{
                            vrm.expressionManager.setValue("Fcl_MTH_A", val * 0.4);
                            vrm.expressionManager.setValue("Fcl_MTH_I", (Math.cos(t * 0.7) + 1) * 0.1);
                            vrm.expressionManager.setValue("Fcl_MTH_U", (Math.sin(t * 0.5) + 1) * 0.15);
                            vrm.expressionManager.setValue("Fcl_MTH_E", (Math.cos(t * 0.8) + 1) * 0.2);
                            vrm.expressionManager.setValue("Fcl_MTH_O", val * 0.3);
                            vrm.expressionManager.setValue("aa", val * 0.5); // 보조용
                        }} catch(e) {{}}
                    }} else if (vrm.expressionManager) {{
                        // 소리 안 날 땐 입 다물기
                        ["Fcl_MTH_A","Fcl_MTH_I","Fcl_MTH_U","Fcl_MTH_E","Fcl_MTH_O","aa"].forEach(k => {{
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
    st.components.v1.html(html_code, height=520)

# ============================================================
# 🔧 3. 메인 레이아웃 및 로직
# ============================================================
st.title("🏫 성동글로벌경영고 AI 도우미")

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "안녕하세요! 성글고 AI 도우미입니다. 무엇을 도와드릴까요?"}]
if "current_audio" not in st.session_state:
    st.session_state.current_audio = None

col_chat, col_vrm = st.columns([3, 2])

with col_chat:
    # 채팅 내역 표시
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # 사용자 입력 처리
    if prompt := st.chat_input("학교에 대해 궁금한 점을 물어보세요!"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("생각 중..."):
                response = chatbot.ask(prompt)
                st.markdown(response)
                
                # TTS 생성
                audio_bytes = text_to_speech(response)
                audio_base64 = get_audio_base64(audio_bytes)
                
                st.session_state.messages.append({"role": "assistant", "content": response})
                st.session_state.current_audio = audio_base64
                st.rerun() # 아바타에 오디오를 전달하기 위해 재실행

with col_vrm:
    st.subheader("🎭 AI 도우미")
    # 세션에 저장된 최신 오디오 데이터를 아바타 컴포넌트로 전달
    vrm_viewer_component(st.session_state.current_audio)
    
    # 다시 듣기 버튼
    if st.session_state.current_audio:
        if st.button("🔄 마지막 답변 다시 듣기", use_container_width=True):
            st.rerun()

# 사이드바 정보
with st.sidebar:
    st.header("🏫 학교 정보")
    st.markdown("""
    **성동글로벌경영고등학교**
    - 📍 서울 중구 퇴계로 375
    - 📞 02-2252-1932
    """)
    if st.button("🔄 대화 초기화"):
        st.session_state.messages = [{"role": "assistant", "content": "안녕하세요! 무엇을 도와드릴까요?"}]
        st.session_state.current_audio = None
        st.rerun()

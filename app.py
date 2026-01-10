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
# 🔧 2. 아바타 & 오디오 통합 뷰어 (토글 + 자동재생 기능 추가)
# ============================================================
def vrm_viewer_component(audio_base64=None, auto_play=False):
    # 자동재생 모드일 때 오디오 초기화 + 자동재생 시도
    audio_init_js = ""
    if audio_base64:
        if auto_play:
            # 자동재생 모드: 로드 후 바로 재생 시도
            audio_init_js = f"""
                const audio = document.getElementById("vrm-audio");
                audio.src = "data:audio/mp3;base64,{audio_base64}";
                const btn = document.getElementById("play-btn");
                btn.style.background = "#ff4b4b";
                btn.innerText = "💬 답변 중...";
                
                // 자동재생 시도 (사용자 상호작용 후에만 동작)
                audio.play().catch(e => {{
                    btn.innerText = "▶ 답변 듣기 (클릭)";
                }});
            """
        else:
            # 수동 모드: 버튼 클릭 대기
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
        
        <div style="height: 120px; background: #667eea; display: flex; flex-direction: column; justify-content: center; align-items: center; gap: 10px; padding: 10px;">
            <button id="play-btn" style="
                padding: 12px 30px; font-size: 16px; font-weight: bold; cursor: pointer; 
                background: #4CAF50; color: white; border: none; border-radius: 15px; 
                box-shadow: 0 4px 15px rgba(0,0,0,0.3); width: 85%;">
                {"🔈 질문을 입력하세요" if not audio_base64 else "▶ 답변 듣기 (클릭)"}
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
            
            const camera = new THREE.PerspectiveCamera(30, canvas.clientWidth / canvas.clientHeight, 0.1, 100);
            camera.position.set(0, 1.1, 2.2); 

            const renderer = new THREE.WebGLRenderer({{ canvas: canvas, antialias: true, alpha: true }});
            renderer.setSize(canvas.clientWidth, canvas.clientHeight);
            renderer.setPixelRatio(window.devicePixelRatio);

            const controls = new OrbitControls(camera, renderer.domElement);
            controls.target.set(0, 1.1, 0); 
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
            
            btn.onclick = () => {{ 
                if(audio.src && audio.paused) {{ 
                    audio.currentTime = 0; 
                    audio.play(); 
                    btn.innerText = "💬 답변 중..."; 
                }} 
            }};
            
            audio.onplay = () => {{ btn.innerText = "💬 답변 중..."; }};
            audio.onended = () => {{ btn.innerText = "🔄 다시 듣기"; }};

            const clock = new THREE.Clock();
            function animate() {{
                requestAnimationFrame(animate);
                const delta = clock.getDelta();
                const time = clock.elapsedTime;

                if (vrm) {{
                    const spine = vrm.humanoid.getNormalizedBoneNode('spine');
                    const neck = vrm.humanoid.getNormalizedBoneNode('neck');
                    const hips = vrm.humanoid.getNormalizedBoneNode('hips');

                    if(spine) spine.rotation.x = Math.sin(time * 1.5) * 0.02; 
                    if(neck) neck.rotation.y = Math.sin(time * 0.7) * 0.04; 
                    if(hips) hips.position.y = Math.sin(time * 1.5) * 0.002;

                    vrm.update(delta);

                    // 립싱크
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

# ============================================================
# 🔧 3. 메인 화면 UI 구성
# ============================================================
st.title("🏫 성글고 AI 도우미")

# 세션 상태 초기화
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "안녕하세요! 궁금한 점을 물어봐 주세요. 😊"}]
if "current_audio" not in st.session_state:
    st.session_state.current_audio = None
if "auto_voice" not in st.session_state:
    st.session_state.auto_voice = False
if "user_interacted" not in st.session_state:
    st.session_state.user_interacted = False

col_chat, col_vrm = st.columns([3, 2])

with col_chat:
    # 자동 음성 토글 (상단에 배치)
    col_toggle, col_info = st.columns([1, 2])
    with col_toggle:
        auto_voice = st.toggle(
            "🔊 자동 음성", 
            value=st.session_state.auto_voice,
            help="켜면 답변이 자동으로 재생됩니다"
        )
        # 토글 상태 변경 시 사용자 상호작용으로 인정
        if auto_voice != st.session_state.auto_voice:
            st.session_state.auto_voice = auto_voice
            if auto_voice:
                st.session_state.user_interacted = True
    
    with col_info:
        if st.session_state.auto_voice:
            if st.session_state.user_interacted:
                st.caption("✅ 자동 재생 활성화됨")
            else:
                st.caption("⚠️ 토글을 다시 켜서 활성화하세요")
        else:
            st.caption("💡 자동 음성을 켜면 답변이 바로 재생됩니다")
    
    st.divider()
    
    # 채팅 메시지 표시
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]): 
            st.markdown(msg["content"])
    
    # 채팅 입력
    if prompt := st.chat_input("질문을 입력하세요..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): 
            st.markdown(prompt)
        
        with st.chat_message("assistant"):
            if chatbot:
                with st.spinner("생각 중..."):
                    response = chatbot.ask(prompt)
                st.markdown(response)
                
                # TTS 생성
                audio_bytes = text_to_speech(response)
                audio_base64 = get_audio_base64(audio_bytes)
                
                st.session_state.messages.append({"role": "assistant", "content": response})
                st.session_state.current_audio = audio_base64
                st.rerun()

with col_vrm:
    st.subheader("🎭 AI 아바타")
    # 자동재생 조건: 토글 ON + 사용자 상호작용 완료
    should_auto_play = st.session_state.auto_voice and st.session_state.user_interacted
    vrm_viewer_component(st.session_state.current_audio, auto_play=should_auto_play)

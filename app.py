def vrm_viewer_component(audio_base64=None):
    # (중략: audio_init_js 로직은 동일)
    
    html_code = f"""
    <div style="width: 100%; height: 650px; background: #8a94c8; border-radius: 20px; position: relative; overflow: hidden; display: flex; flex-direction: column;">
        <canvas id="vrm-canvas" style="width: 100%; height: 500px; cursor: grab;"></canvas>
        
        <audio id="vrm-audio" style="display:none;"></audio>
        
        <div style="height: 150px; background: #667eea; display: flex; justify-content: center; align-items: center;">
            <button id="play-btn" style="
                padding: 15px 40px; font-size: 18px; font-weight: bold; cursor: pointer; 
                background: #4CAF50; color: white; border: none; border-radius: 15px; 
                box-shadow: 0 4px 15px rgba(0,0,0,0.3); width: 80%;">
                {"🔈 질문 대기 중" if not audio_base64 else "▶ 답변 듣기 / 다시 듣기"}
            </button>
        </div>

        <script type="module">
            import * as THREE from "three";
            import {{ GLTFLoader }} from "three/addons/loaders/GLTFLoader.js";
            import {{ OrbitControls }} from "three/addons/controls/OrbitControls.js";
            import {{ VRMLoaderPlugin }} from "@pixiv/three-vrm";

            let vrm = null;
            const scene = new THREE.Scene();
            const canvas = document.getElementById("vrm-canvas");

            // 1. 시야각(FOV)을 30으로 좁혀서 모델을 더 크게 잡음
            const camera = new THREE.PerspectiveCamera(30, canvas.clientWidth / canvas.clientHeight, 0.1, 100);
            
            // 2. 카메라 위치 수정: y(높이)는 낮추고, z(거리)는 적당히 배치
            camera.position.set(0, 1.2, 2.5); 

            const renderer = new THREE.WebGLRenderer({{ canvas: canvas, antialias: true, alpha: true }});
            renderer.setSize(canvas.clientWidth, canvas.clientHeight);
            renderer.outputColorSpace = THREE.SRGBColorSpace;

            const controls = new OrbitControls(camera, renderer.domElement);
            
            // 3. 시선(Target) 수정: 아바타의 얼굴 근처(1.2)를 바라보게 고정
            controls.target.set(0, 1.2, 0); 
            controls.update();

            // (중략: 조명 및 로더 로직...)
            const loader = new GLTFLoader();
            loader.register((parser) => new VRMLoaderPlugin(parser));
            loader.load("{VRM_MODEL_URL}", (gltf) => {{
                vrm = gltf.userData.vrm;
                scene.add(vrm.scene);
                // 아바타가 정면을 보게 회전
                vrm.scene.rotation.y = Math.PI; 
            }});

            // (중략: animate 로직...)
        </script>
    </div>
    """
    st.components.v1.html(html_code, height=660)

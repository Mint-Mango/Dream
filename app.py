import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Python 3D 평지 탐험", page_icon="🎮", layout="wide")

st.title("3D 평지 탐험")
st.caption("Python + Streamlit 앱 · 브라우저에서 실행되는 1인칭 3D 프로토타입")

st.markdown(
    """
    **조작법:** 화면 안을 클릭해 마우스를 잠근 다음 `W A S D`로 이동하고 마우스로 시점을 돌려 보세요.  
    `Space`는 점프, `Shift`는 달리기, `Esc`는 마우스 잠금 해제입니다.
    """
)

game_html = r"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  html, body { margin: 0; padding: 0; overflow: hidden; background: #b8d9ef; font-family: Arial, sans-serif; }
  #game { position: relative; width: 100%; height: 620px; overflow: hidden; border-radius: 12px; background: #b8d9ef; }
  canvas { display: block; width: 100%; height: 100%; outline: none; }
  #overlay {
    position: absolute; inset: 0; display: flex; align-items: center; justify-content: center;
    background: rgba(12, 24, 34, 0.30); color: white; text-align: center; cursor: pointer;
  }
  #panel { background: rgba(10, 20, 28, .78); padding: 22px 28px; border-radius: 14px; max-width: 430px; }
  #panel h2 { margin: 0 0 10px; font-size: 24px; }
  #panel p { line-height: 1.5; margin: 7px 0; }
  #hud {
    position: absolute; top: 12px; left: 12px; color: white; background: rgba(0,0,0,.45);
    padding: 8px 11px; border-radius: 8px; font-size: 13px; pointer-events: none;
  }
  #crosshair {
    position: absolute; left: 50%; top: 50%; width: 8px; height: 8px;
    transform: translate(-50%, -50%); pointer-events: none;
  }
  #crosshair:before, #crosshair:after { content:""; position:absolute; background:rgba(255,255,255,.9); }
  #crosshair:before { width: 8px; height: 2px; top:3px; left:0; }
  #crosshair:after { width: 2px; height: 8px; top:0; left:3px; }
  #notice { position:absolute; bottom:12px; left:50%; transform:translateX(-50%); color:white;
    background:rgba(0,0,0,.45); padding:7px 10px; border-radius:7px; font-size:12px; white-space:nowrap; pointer-events:none; }
</style>
</head>
<body>
<div id="game">
  <div id="hud">위치: <span id="pos">0, 1.7, 0</span></div>
  <div id="crosshair"></div>
  <div id="notice">화면을 클릭해 시작 · Esc로 마우스 잠금 해제</div>
  <div id="overlay">
    <div id="panel">
      <h2>평평한 3D 평지</h2>
      <p>화면을 클릭하면 탐험이 시작됩니다.</p>
      <p><b>W A S D</b> 이동 · <b>마우스</b> 시점 회전</p>
      <p><b>Space</b> 점프 · <b>Shift</b> 달리기 · <b>Esc</b> 마우스 잠금 해제</p>
    </div>
  </div>
</div>
<script type="module">
import * as THREE from 'https://cdn.jsdelivr.net/npm/three@0.164.1/build/three.module.js';
import { PointerLockControls } from 'https://cdn.jsdelivr.net/npm/three@0.164.1/examples/jsm/controls/PointerLockControls.js';

const root = document.getElementById('game');
const overlay = document.getElementById('overlay');
const notice = document.getElementById('notice');
const posLabel = document.getElementById('pos');

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x9bc9e8);
scene.fog = new THREE.Fog(0x9bc9e8, 80, 260);

const camera = new THREE.PerspectiveCamera(75, root.clientWidth / root.clientHeight, 0.1, 500);
camera.position.set(0, 1.7, 5);

const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.setSize(root.clientWidth, root.clientHeight);
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
root.insertBefore(renderer.domElement, root.firstChild);

scene.add(new THREE.HemisphereLight(0xffffff, 0x6f8055, 2.0));
const sun = new THREE.DirectionalLight(0xffffff, 2.1);
sun.position.set(-35, 70, 25);
sun.castShadow = true;
sun.shadow.mapSize.set(1024, 1024);
scene.add(sun);

// 넓고 평평한 지형
const groundGeo = new THREE.PlaneGeometry(1000, 1000);
const groundMat = new THREE.MeshStandardMaterial({ color: 0x78a85a, roughness: 1 });
const ground = new THREE.Mesh(groundGeo, groundMat);
ground.rotation.x = -Math.PI / 2;
ground.receiveShadow = true;
scene.add(ground);

// 먼 곳에서 바닥의 수평감을 느낄 수 있는 은은한 격자
const grid = new THREE.GridHelper(200, 100, 0x668b4c, 0x709653);
grid.position.y = 0.012;
grid.material.transparent = true;
grid.material.opacity = 0.22;
scene.add(grid);

// 바닥 가장자리 대신 멀리 보이는 장식용 낮은 언덕을 배치해 평지의 넓이를 표현
const hillMat = new THREE.MeshStandardMaterial({ color: 0x6e9c58, roughness: 1 });
for (let i = 0; i < 18; i++) {
  const radius = 8 + (i % 4) * 5;
  const geo = new THREE.SphereGeometry(radius, 16, 10);
  const hill = new THREE.Mesh(geo, hillMat);
  const angle = (i / 18) * Math.PI * 2;
  hill.position.set(Math.cos(angle) * 190, -radius + 1, Math.sin(angle) * 190);
  hill.scale.y = 0.35;
  hill.receiveShadow = true;
  scene.add(hill);
}

const controls = new PointerLockControls(camera, renderer.domElement);
overlay.addEventListener('click', () => controls.lock());
controls.addEventListener('lock', () => {
  overlay.style.display = 'none';
  notice.textContent = 'W A S D 이동 · Space 점프 · Shift 달리기';
});
controls.addEventListener('unlock', () => {
  overlay.style.display = 'flex';
  notice.textContent = '화면을 클릭해 계속하기 · Esc로 마우스 잠금 해제';
});

const keys = {};
window.addEventListener('keydown', e => {
  keys[e.code] = true;
  if (['Space', 'ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'].includes(e.code)) e.preventDefault();
});
window.addEventListener('keyup', e => { keys[e.code] = false; });

let verticalVelocity = 0;
let onGround = true;
const clock = new THREE.Clock();
const playerHeight = 1.7;
const worldLimit = 480;

function resize() {
  const w = root.clientWidth, h = root.clientHeight;
  camera.aspect = w / h;
  camera.updateProjectionMatrix();
  renderer.setSize(w, h);
}
window.addEventListener('resize', resize);

function animate() {
  requestAnimationFrame(animate);
  const dt = Math.min(clock.getDelta(), 0.05);

  if (controls.isLocked) {
    const speed = (keys['ShiftLeft'] || keys['ShiftRight']) ? 15 : 7;
    const forward = (keys['KeyW'] ? 1 : 0) - (keys['KeyS'] ? 1 : 0);
    const sideways = (keys['KeyD'] ? 1 : 0) - (keys['KeyA'] ? 1 : 0);

    if (forward !== 0) controls.moveForward(forward * speed * dt);
    if (sideways !== 0) controls.moveRight(sideways * speed * dt);

    if (keys['Space'] && onGround) {
      verticalVelocity = 7.5;
      onGround = false;
    }
    verticalVelocity -= 19.6 * dt;
    camera.position.y += verticalVelocity * dt;
    if (camera.position.y <= playerHeight) {
      camera.position.y = playerHeight;
      verticalVelocity = 0;
      onGround = true;
    }

    camera.position.x = THREE.MathUtils.clamp(camera.position.x, -worldLimit, worldLimit);
    camera.position.z = THREE.MathUtils.clamp(camera.position.z, -worldLimit, worldLimit);
    posLabel.textContent = `${camera.position.x.toFixed(1)}, ${camera.position.y.toFixed(1)}, ${camera.position.z.toFixed(1)}`;
  }

  renderer.render(scene, camera);
}
animate();
</script>
</body>
</html>
"""

components.html(game_html, height=635, scrolling=False)

with st.expander("GitHub에 올리고 배포하는 방법"):
    st.markdown(
        """
        1. 이 프로젝트의 `app.py`와 `requirements.txt`를 GitHub 저장소에 올립니다.
        2. [Streamlit Community Cloud](https://share.streamlit.io/)에 로그인하고 GitHub 저장소를 연결합니다.
        3. 앱 파일 경로에 `app.py`를 지정하고 배포합니다.
        4. 배포가 끝나면 공유 URL로 접속할 수 있습니다.

        **참고:** 이 방식은 GitHub Pages가 아니라 Streamlit Community Cloud에서 앱을 실행합니다. GitHub는 소스 코드 저장소로 사용합니다. 브라우저가 Three.js CDN에 접속할 수 있어야 3D 화면이 표시됩니다.
        """
    )

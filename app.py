
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title="3D 이동 테스트",
    page_icon="🎮",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.title("3D 공간 이동 테스트")
st.caption("WASD 이동 | 마우스 드래그 시점 회전 | SPACE 점프")

game_html = """
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">

<style>
    body {
        margin: 0;
        overflow: hidden;
        background: #777777;
        font-family: Arial, sans-serif;
    }

    #game {
        width: 100%;
        height: 100vh;
        outline: none;
    }

    #crosshair {
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        color: #111111;
        font-size: 24px;
        pointer-events: none;
    }

    #info {
        position: absolute;
        top: 15px;
        left: 15px;
        padding: 12px;
        background: rgba(30,30,30,0.75);
        color: #dddddd;
        font-size: 14px;
        border-radius: 6px;
        pointer-events: none;
    }
</style>
</head>

<body>

<div id="game" tabindex="0"></div>
<div id="crosshair">+</div>

<div id="info">
    3D MOVEMENT TEST<br>
    WASD : 이동<br>
    Mouse Drag : 시점 회전<br>
    SPACE : 점프
</div>

<script type="module">

import * as THREE from
"https://cdn.jsdelivr.net/npm/three@0.160.1/build/three.module.js";

// ============================
// 1. 3D 환경
// ============================

const scene = new THREE.Scene();

scene.background = new THREE.Color(0x777777);

// 카메라
const camera = new THREE.PerspectiveCamera(
    75,
    window.innerWidth / window.innerHeight,
    0.1,
    2000
);

camera.position.set(0, 1.7, 5);

// 렌더러
const renderer = new THREE.WebGLRenderer({
    antialias: true
});

renderer.setSize(
    window.innerWidth,
    window.innerHeight
);

renderer.setPixelRatio(
    Math.min(window.devicePixelRatio, 2)
);

const game = document.getElementById("game");

game.appendChild(renderer.domElement);

// ============================
// 2. 회색 바닥
// ============================

const floorGeometry = new THREE.PlaneGeometry(
    2000,
    2000
);

const floorMaterial = new THREE.MeshBasicMaterial({
    color: 0x888888,
    side: THREE.DoubleSide
});

const floor = new THREE.Mesh(
    floorGeometry,
    floorMaterial
);

floor.rotation.x = -Math.PI / 2;

scene.add(floor);

// ============================
// 3. 검은색 격자선
// ============================

const grid = new THREE.GridHelper(
    2000,       // 격자 전체 크기
    2000,       // 격자 개수 (1칸 = 1m)
    0x111111,   // 중심선 색상
    0x333333    // 일반 격자선 색상
);

grid.position.y = 0.01;

scene.add(grid);

// ============================
// 4. 키보드 입력
// ============================

const keys = {};

window.addEventListener("keydown", (event) => {

    keys[event.code] = true;

    if (event.code === "Space") {
        event.preventDefault();
    }
});

window.addEventListener("keyup", (event) => {
    keys[event.code] = false;
});

window.addEventListener("blur", () => {
    for (const key in keys) {
        keys[key] = false;
    }
});

game.addEventListener("click", () => {
    game.focus();
});

// ============================
// 5. 마우스 시점 회전
// ============================

let yaw = 0;
let pitch = 0;

let dragging = false;
let previousX = 0;
let previousY = 0;

renderer.domElement.addEventListener(
    "mousedown",
    (event) => {

        dragging = true;

        previousX = event.clientX;
        previousY = event.clientY;

        game.focus();
    }
);

window.addEventListener("mouseup", () => {
    dragging = false;
});

window.addEventListener("mousemove", (event) => {

    if (!dragging) return;

    const deltaX = event.clientX - previousX;
    const deltaY = event.clientY - previousY;

    previousX = event.clientX;
    previousY = event.clientY;

    yaw -= deltaX * 0.003;
    pitch -= deltaY * 0.003;

    pitch = Math.max(
        -Math.PI / 2 + 0.05,
        Math.min(Math.PI / 2 - 0.05, pitch)
    );
});

// ============================
// 6. 플레이어 설정
// ============================

const PLAYER_HEIGHT = 1.7;

const MOVE_SPEED = 5;
const JUMP_SPEED = 6;
const GRAVITY = 16;

let verticalVelocity = 0;
let grounded = true;

// ============================
// 7. 플레이어 이동
// ============================

function updatePlayer(delta) {

    camera.rotation.order = "YXZ";

    camera.rotation.y = yaw;
    camera.rotation.x = pitch;

    // 전방 방향
    const forward = new THREE.Vector3(
        -Math.sin(yaw),
        0,
        -Math.cos(yaw)
    );

    // 오른쪽 방향
    const right = new THREE.Vector3(
        Math.cos(yaw),
        0,
        -Math.sin(yaw)
    );

    const direction = new THREE.Vector3();

    if (keys["KeyW"]) direction.add(forward);
    if (keys["KeyS"]) direction.sub(forward);

    if (keys["KeyD"]) direction.add(right);
    if (keys["KeyA"]) direction.sub(right);

    if (direction.lengthSq() > 0) {
        direction.normalize();
    }

    direction.multiplyScalar(
        MOVE_SPEED * delta
    );

    camera.position.x += direction.x;
    camera.position.z += direction.z;

    // 점프
    if (keys["Space"] && grounded) {
        verticalVelocity = JUMP_SPEED;
        grounded = false;
    }

    verticalVelocity -= GRAVITY * delta;

    camera.position.y += verticalVelocity * delta;

    // 바닥 충돌
    if (camera.position.y <= PLAYER_HEIGHT) {

        camera.position.y = PLAYER_HEIGHT;

        verticalVelocity = 0;
        grounded = true;
    }
}

// ============================
// 8. 게임 루프
// ============================

const clock = new THREE.Clock();

function animate() {

    requestAnimationFrame(animate);

    const delta = Math.min(
        clock.getDelta(),
        0.05
    );

    updatePlayer(delta);

    renderer.render(scene, camera);
}

animate();

// ============================
// 9. 화면 크기 조정
// ============================

window.addEventListener("resize", () => {

    camera.aspect =
        window.innerWidth / window.innerHeight;

    camera.updateProjectionMatrix();

    renderer.setSize(
        window.innerWidth,
        window.innerHeight
    );
});

</script>
</body>
</html>
"""

components.html(
    game_html,
    height=700,
    scrolling=False
)


import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title="3D 블록 월드",
    page_icon="🎮",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.title("🎮 3D 블록 월드")
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
        background: #87ceeb;
        font-family: Arial, sans-serif;
    }

    #game {
        width: 100%;
        height: 100vh;
        display: block;
        outline: none;
    }

    #crosshair {
        position: absolute;
        top: 50%;
        left: 50%;
        color: white;
        font-size: 26px;
        transform: translate(-50%, -50%);
        pointer-events: none;
        text-shadow: 0 0 3px black;
    }

    #info {
        position: absolute;
        top: 15px;
        left: 15px;
        padding: 12px;
        background: rgba(0,0,0,0.55);
        color: white;
        border-radius: 8px;
        font-size: 14px;
        pointer-events: none;
    }
</style>
</head>

<body>

<div id="game" tabindex="0"></div>
<div id="crosshair">+</div>
<div id="info">
    🎮 3D 블록 월드<br>
    WASD : 이동<br>
    마우스 드래그 : 시점 회전<br>
    SPACE : 점프<br>
    게임 화면 클릭 후 조작
</div>

<script type="module">

import * as THREE from
"https://cdn.jsdelivr.net/npm/three@0.160.1/build/three.module.js";

// ============================
// 1. 기본 장면 생성
// ============================

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x87ceeb);
scene.fog = new THREE.Fog(0x87ceeb, 30, 85);

const camera = new THREE.PerspectiveCamera(
    75,
    window.innerWidth / window.innerHeight,
    0.1,
    1000
);

camera.position.set(0, 1.7, 5);

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

renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;

const game = document.getElementById("game");
game.appendChild(renderer.domElement);

// ============================
// 2. 조명 설정
// ============================

const ambientLight = new THREE.AmbientLight(
    0xffffff,
    0.65
);

scene.add(ambientLight);

const sunlight = new THREE.DirectionalLight(
    0xffffff,
    1.5
);

sunlight.position.set(15, 30, 10);
sunlight.castShadow = true;

sunlight.shadow.mapSize.set(1024, 1024);
sunlight.shadow.camera.left = -40;
sunlight.shadow.camera.right = 40;
sunlight.shadow.camera.top = 40;
sunlight.shadow.camera.bottom = -40;

scene.add(sunlight);

// ============================
// 3. 블록 생성 함수
// ============================

const cubeGeometry = new THREE.BoxGeometry(1, 1, 1);

const grassMaterial = new THREE.MeshLambertMaterial({
    color: 0x59ad45
});

const dirtMaterial = new THREE.MeshLambertMaterial({
    color: 0x92633b
});

const stoneMaterial = new THREE.MeshLambertMaterial({
    color: 0x888888
});

const woodMaterial = new THREE.MeshLambertMaterial({
    color: 0x805432
});

const leafMaterial = new THREE.MeshLambertMaterial({
    color: 0x278b36
});

const obstacles = [];

function createBlock(x, y, z, material, solid = false) {

    const block = new THREE.Mesh(
        cubeGeometry,
        material
    );

    block.position.set(x, y, z);
    block.castShadow = true;
    block.receiveShadow = true;

    scene.add(block);

    if (solid) {
        obstacles.push(
            new THREE.Box3().setFromObject(block)
        );
    }

    return block;
}

// ============================
// 4. 평평한 블록 지형
// ============================

const WORLD_SIZE = 30;
const HALF_WORLD = WORLD_SIZE / 2;

for (let x = -HALF_WORLD; x < HALF_WORLD; x++) {

    for (let z = -HALF_WORLD; z < HALF_WORLD; z++) {

        createBlock(
            x,
            -0.5,
            z,
            grassMaterial
        );

        createBlock(
            x,
            -1.5,
            z,
            dirtMaterial
        );
    }
}

// ============================
// 5. 장애물 생성
// ============================

const blockPositions = [
    [4, 0.5, 4],
    [5, 0.5, 4],
    [4, 1.5, 4],
    [-4, 0.5, -3],
    [-4, 1.5, -3],
    [-4, 2.5, -3],
    [7, 0.5, -5],
    [8, 0.5, -5],
    [9, 0.5, -5],
    [7, 1.5, -5]
];

for (const position of blockPositions) {

    createBlock(
        position[0],
        position[1],
        position[2],
        stoneMaterial,
        true
    );
}

// ============================
// 6. 나무 생성
// ============================

function createTree(x, z) {

    for (let y = 0; y < 3; y++) {

        createBlock(
            x,
            y + 0.5,
            z,
            woodMaterial,
            true
        );
    }

    for (let dx = -1; dx <= 1; dx++) {

        for (let dz = -1; dz <= 1; dz++) {

            createBlock(
                x + dx,
                3.5,
                z + dz,
                leafMaterial,
                true
            );
        }
    }

    createBlock(
        x,
        4.5,
        z,
        leafMaterial,
        true
    );
}

createTree(-7, -7);
createTree(8, 8);
createTree(-8, 7);
createTree(9, -9);

// ============================
// 7. 키보드 입력
// ============================

const keys = {};

window.addEventListener("keydown", (event) => {

    keys[event.code] = true;

    if (
        [
            "Space",
            "ArrowUp",
            "ArrowDown",
            "ArrowLeft",
            "ArrowRight"
        ].includes(event.code)
    ) {
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
// 8. 마우스 시점 회전
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
// 9. 플레이어 물리 설정
// ============================

const PLAYER_HEIGHT = 1.7;
const PLAYER_RADIUS = 0.28;

const MOVE_SPEED = 5;
const JUMP_SPEED = 6;
const GRAVITY = 16;

let verticalVelocity = 0;
let grounded = true;

function collides(position) {

    const playerBox = new THREE.Box3(
        new THREE.Vector3(
            position.x - PLAYER_RADIUS,
            position.y - PLAYER_HEIGHT + 0.05,
            position.z - PLAYER_RADIUS
        ),
        new THREE.Vector3(
            position.x + PLAYER_RADIUS,
            position.y - 0.05,
            position.z + PLAYER_RADIUS
        )
    );

    return obstacles.some(
        obstacle => playerBox.intersectsBox(obstacle)
    );
}

// ============================
// 10. 플레이어 이동
// ============================

function updatePlayer(delta) {

    camera.rotation.order = "YXZ";
    camera.rotation.y = yaw;
    camera.rotation.x = pitch;

    const forward = new THREE.Vector3(
        -Math.sin(yaw),
        0,
        -Math.cos(yaw)
    );

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

    const movement = direction.multiplyScalar(
        MOVE_SPEED * delta
    );

    // X축 충돌 검사
    const nextX = camera.position.clone();
    nextX.x += movement.x;

    if (!collides(nextX)) {
        camera.position.x = nextX.x;
    }

    // Z축 충돌 검사
    const nextZ = camera.position.clone();
    nextZ.z += movement.z;

    if (!collides(nextZ)) {
        camera.position.z = nextZ.z;
    }

    // 점프
    if (keys["Space"] && grounded) {

        verticalVelocity = JUMP_SPEED;
        grounded = false;
    }

    verticalVelocity -= GRAVITY * delta;

    const nextY = camera.position.clone();
    nextY.y += verticalVelocity * delta;

    if (!collides(nextY)) {
        camera.position.y = nextY.y;
    } else {
        if (verticalVelocity < 0) {
            grounded = true;
        }
        verticalVelocity = 0;
    }

    // 지면 충돌
    if (camera.position.y <= PLAYER_HEIGHT) {

        camera.position.y = PLAYER_HEIGHT;
        verticalVelocity = 0;
        grounded = true;
    }

    // 맵 경계
    camera.position.x = THREE.MathUtils.clamp(
        camera.position.x,
        -HALF_WORLD + 0.5,
        HALF_WORLD - 0.5
    );

    camera.position.z = THREE.MathUtils.clamp(
        camera.position.z,
        -HALF_WORLD + 0.5,
        HALF_WORLD - 0.5
    );
}

// ============================
// 11. 게임 루프
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
// 12. 화면 크기 변경
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

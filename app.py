
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title="Backrooms 3D",
    page_icon="🎮",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.title("BACKROOMS - 3D EXPLORATION")
st.caption(
    "WASD 이동 | Shift 달리기 | Space 점프 | "
    "마우스 드래그 시점 회전"
)

game_html = r"""
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">

<style>
    html, body {
        margin: 0;
        width: 100%;
        height: 100%;
        overflow: hidden;
        background: #c8be91;
        font-family: Arial, sans-serif;
    }

    #game {
        width: 100%;
        height: 100vh;
        outline: none;
        position: relative;
    }

    #crosshair {
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        color: rgba(35,35,25,0.7);
        font-size: 22px;
        pointer-events: none;
    }

    #info {
        position: absolute;
        top: 15px;
        left: 15px;
        padding: 12px 16px;
        background: rgba(20,20,15,0.72);
        color: #eeeecc;
        border-radius: 6px;
        line-height: 1.7;
        font-size: 13px;
        pointer-events: none;
    }

    #status {
        position: absolute;
        right: 15px;
        top: 15px;
        background: rgba(20,20,15,0.7);
        color: #eeeecc;
        padding: 10px 14px;
        border-radius: 6px;
        font-size: 13px;
        pointer-events: none;
    }
</style>
</head>

<body>

<div id="game" tabindex="0"></div>
<div id="crosshair">+</div>

<div id="info">
    <b>BACKROOMS - LEVEL 0</b><br>
    W A S D : 이동<br>
    SHIFT : 달리기<br>
    SPACE : 점프<br>
    MOUSE DRAG : 시점 회전<br>
    R : 시작 위치로 돌아가기
</div>

<div id="status">WALK</div>

<script type="module">

import * as THREE from
"https://cdn.jsdelivr.net/npm/three@0.160.1/build/three.module.js";

// =====================================
// 1. 기본 설정
// =====================================

const scene = new THREE.Scene();

scene.background = new THREE.Color(0xc8be91);
scene.fog = new THREE.Fog(
    0xc8be91,
    18,
    65
);

const camera = new THREE.PerspectiveCamera(
    75,
    window.innerWidth / window.innerHeight,
    0.05,
    180
);

const PLAYER_HEIGHT = 1.65;
const PLAYER_RADIUS = 0.32;

camera.position.set(0, PLAYER_HEIGHT, 0);
camera.rotation.order = "YXZ";

const renderer = new THREE.WebGLRenderer({
    antialias: true
});

renderer.setPixelRatio(
    Math.min(window.devicePixelRatio, 2)
);

renderer.setSize(
    window.innerWidth,
    window.innerHeight
);

const game = document.getElementById("game");
game.appendChild(renderer.domElement);

// =====================================
// 2. 맵 크기 및 이동 설정
// =====================================

// 맵은 17 x 17개의 구역으로 구성
const MAP_SIZE = 17;

// 구역 하나의 가로, 세로 길이
const CELL_SIZE = 8;

// 전체 공간 크기: 136m x 136m
const WORLD_SIZE = MAP_SIZE * CELL_SIZE;

const WALL_HEIGHT = 3.3;
const WALL_THICKNESS = 0.28;

// 구역 간 통로 너비
const PASSAGE_WIDTH = 3.4;

const WALK_SPEED = 4;
const RUN_SPEED = 8;

const JUMP_SPEED = 5.5;
const GRAVITY = 17;

let velocityY = 0;
let grounded = true;

// =====================================
// 3. 재질
// =====================================

const wallMaterial = new THREE.MeshLambertMaterial({
    color: 0xd5ca88
});

const floorMaterial = new THREE.MeshLambertMaterial({
    color: 0x77715d
});

const ceilingMaterial = new THREE.MeshLambertMaterial({
    color: 0xc6c1a3
});

const trimMaterial = new THREE.MeshLambertMaterial({
    color: 0x9b936a
});

const lightMaterial = new THREE.MeshBasicMaterial({
    color: 0xfff4ca
});

// =====================================
// 4. 조명
// =====================================

const ambientLight = new THREE.AmbientLight(
    0xfff3cf,
    1.65
);

scene.add(ambientLight);

// =====================================
// 5. 바닥과 천장
// =====================================

const floor = new THREE.Mesh(
    new THREE.PlaneGeometry(
        WORLD_SIZE,
        WORLD_SIZE
    ),
    floorMaterial
);

floor.rotation.x = -Math.PI / 2;
floor.position.y = 0;
scene.add(floor);

const ceiling = new THREE.Mesh(
    new THREE.PlaneGeometry(
        WORLD_SIZE,
        WORLD_SIZE
    ),
    ceilingMaterial
);

ceiling.rotation.x = Math.PI / 2;
ceiling.position.y = WALL_HEIGHT;
scene.add(ceiling);

// 바닥에 희미한 타일 선 생성
const tileGrid = new THREE.GridHelper(
    WORLD_SIZE,
    MAP_SIZE * 8,
    0x565345,
    0x696554
);

tileGrid.position.y = 0.008;
scene.add(tileGrid);

// =====================================
// 6. 미로 데이터 생성
// =====================================

// 고정 시드를 사용하여 새로고침해도
// 같은 형태의 미로가 나오도록 설정

let seed = 20261030;

function random() {
    seed = (seed * 1664525 + 1013904223) >>> 0;
    return seed / 4294967296;
}

const cells = [];

for (let z = 0; z < MAP_SIZE; z++) {

    const row = [];

    for (let x = 0; x < MAP_SIZE; x++) {

        row.push({
            visited: false,
            north: true,
            south: true,
            east: true,
            west: true
        });
    }

    cells.push(row);
}

const directions = [
    {dx: 0, dz: -1, wall: "north", opposite: "south"},
    {dx: 0, dz: 1, wall: "south", opposite: "north"},
    {dx: 1, dz: 0, wall: "east", opposite: "west"},
    {dx: -1, dz: 0, wall: "west", opposite: "east"}
];

// 깊이 우선 탐색으로 연결된 미로 생성
function generateMaze() {

    const stack = [];

    const startX = Math.floor(MAP_SIZE / 2);
    const startZ = Math.floor(MAP_SIZE / 2);

    cells[startZ][startX].visited = true;
    stack.push({x: startX, z: startZ});

    while (stack.length > 0) {

        const current = stack[stack.length - 1];

        const choices = [];

        for (const direction of directions) {

            const nx = current.x + direction.dx;
            const nz = current.z + direction.dz;

            if (
                nx >= 0 &&
                nz >= 0 &&
                nx < MAP_SIZE &&
                nz < MAP_SIZE &&
                !cells[nz][nx].visited
            ) {
                choices.push({
                    ...direction,
                    nx,
                    nz
                });
            }
        }

        if (choices.length === 0) {
            stack.pop();
            continue;
        }

        const choice = choices[
            Math.floor(random() * choices.length)
        ];

        cells[current.z][current.x][choice.wall] = false;

        cells[choice.nz][choice.nx][choice.opposite] = false;

        cells[choice.nz][choice.nx].visited = true;

        stack.push({
            x: choice.nx,
            z: choice.nz
        });
    }

    // 일부 벽을 추가로 열어
    // 막다른 길이 적은 백룸 구조 생성
    for (let z = 0; z < MAP_SIZE; z++) {

        for (let x = 0; x < MAP_SIZE; x++) {

            if (x < MAP_SIZE - 1 && random() < 0.25) {
                cells[z][x].east = false;
                cells[z][x + 1].west = false;
            }

            if (z < MAP_SIZE - 1 && random() < 0.25) {
                cells[z][x].south = false;
                cells[z + 1][x].north = false;
            }
        }
    }
}

generateMaze();

// =====================================
// 7. 벽 생성 및 충돌 판정 데이터
// =====================================

const colliders = [];

function addWall(x, z, width, depth) {

    const geometry = new THREE.BoxGeometry(
        width,
        WALL_HEIGHT,
        depth
    );

    const mesh = new THREE.Mesh(
        geometry,
        wallMaterial
    );

    mesh.position.set(
        x,
        WALL_HEIGHT / 2,
        z
    );

    scene.add(mesh);

    // 벽 하단 몰딩
    const trim = new THREE.Mesh(
        new THREE.BoxGeometry(
            width + 0.02,
            0.16,
            depth + 0.02
        ),
        trimMaterial
    );

    trim.position.set(x, 0.08, z);
    scene.add(trim);

    // 충돌 검사에 사용할 영역
    colliders.push({
        minX: x - width / 2,
        maxX: x + width / 2,
        minZ: z - depth / 2,
        maxZ: z + depth / 2
    });
}

// 열려 있는 벽에는 중앙 통로를 만듦
function createBoundary(
    x,
    z,
    horizontal,
    closed
) {

    if (closed) {

        if (horizontal) {
            addWall(x, z, CELL_SIZE, WALL_THICKNESS);
        } else {
            addWall(x, z, WALL_THICKNESS, CELL_SIZE);
        }

        return;
    }

    const segmentLength =
        (CELL_SIZE - PASSAGE_WIDTH) / 2;

    const offset =
        (CELL_SIZE + PASSAGE_WIDTH) / 4;

    if (horizontal) {

        addWall(
            x - offset,
            z,
            segmentLength,
            WALL_THICKNESS
        );

        addWall(
            x + offset,
            z,
            segmentLength,
            WALL_THICKNESS
        );

    } else {

        addWall(
            x,
            z - offset,
            WALL_THICKNESS,
            segmentLength
        );

        addWall(
            x,
            z + offset,
            WALL_THICKNESS,
            segmentLength
        );
    }
}

function cellCenter(index) {
    return (
        index - Math.floor(MAP_SIZE / 2)
    ) * CELL_SIZE;
}

// =====================================
// 8. 미로 벽 배치
// =====================================

for (let z = 0; z < MAP_SIZE; z++) {

    for (let x = 0; x < MAP_SIZE; x++) {

        const centerX = cellCenter(x);
        const centerZ = cellCenter(z);

        const cell = cells[z][x];

        // 동쪽 경계
        createBoundary(
            centerX + CELL_SIZE / 2,
            centerZ,
            false,
            cell.east
        );

        // 남쪽 경계
        createBoundary(
            centerX,
            centerZ + CELL_SIZE / 2,
            true,
            cell.south
        );

        // 가장 바깥쪽 서쪽 벽
        if (x === 0) {
            createBoundary(
                centerX - CELL_SIZE / 2,
                centerZ,
                false,
                true
            );
        }

        // 가장 바깥쪽 북쪽 벽
        if (z === 0) {
            createBoundary(
                centerX,
                centerZ - CELL_SIZE / 2,
                true,
                true
            );
        }
    }
}

// =====================================
// 9. 천장 형광등
// =====================================

const lightGeometry = new THREE.BoxGeometry(
    2.8,
    0.035,
    0.55
);

for (let z = 0; z < MAP_SIZE; z++) {

    for (let x = 0; x < MAP_SIZE; x++) {

        const cx = cellCenter(x);
        const cz = cellCenter(z);

        const lightPanel = new THREE.Mesh(
            lightGeometry,
            lightMaterial
        );

        lightPanel.position.set(
            cx,
            WALL_HEIGHT - 0.025,
            cz
        );

        scene.add(lightPanel);

        // 일부 구역에만 실제 광원 배치
        // 브라우저 렌더링 부하 감소
        if (x % 4 === 0 && z % 4 === 0) {

            const pointLight = new THREE.PointLight(
                0xffe7a1,
                2.0,
                16,
                2
            );

            pointLight.position.set(
                cx,
                WALL_HEIGHT - 0.25,
                cz
            );

            scene.add(pointLight);
        }
    }
}

// =====================================
// 10. 키보드 입력
// =====================================

const keys = {};

window.addEventListener("keydown", event => {

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

    // 위치 초기화
    if (event.code === "KeyR") {

        camera.position.set(
            0,
            PLAYER_HEIGHT,
            0
        );

        velocityY = 0;
        grounded = true;
    }
});

window.addEventListener("keyup", event => {
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

// =====================================
// 11. 마우스 시점 회전
// =====================================

let yaw = 0;
let pitch = 0;

let dragging = false;
let previousX = 0;
let previousY = 0;

renderer.domElement.addEventListener(
    "mousedown",
    event => {

        dragging = true;

        previousX = event.clientX;
        previousY = event.clientY;

        game.focus();
    }
);

window.addEventListener("mouseup", () => {
    dragging = false;
});

window.addEventListener("mousemove", event => {

    if (!dragging) return;

    const deltaX = event.clientX - previousX;
    const deltaY = event.clientY - previousY;

    previousX = event.clientX;
    previousY = event.clientY;

    yaw -= deltaX * 0.003;
    pitch -= deltaY * 0.003;

    pitch = THREE.MathUtils.clamp(
        pitch,
        -Math.PI / 2 + 0.05,
        Math.PI / 2 - 0.05
    );
});

// =====================================
// 12. 벽 충돌 검사
// =====================================

function collides(x, z) {

    for (const wall of colliders) {

        if (
            x + PLAYER_RADIUS > wall.minX &&
            x - PLAYER_RADIUS < wall.maxX &&
            z + PLAYER_RADIUS > wall.minZ &&
            z - PLAYER_RADIUS < wall.maxZ
        ) {
            return true;
        }
    }

    return false;
}

// =====================================
// 13. 플레이어 이동
// =====================================

const statusElement =
    document.getElementById("status");

function updatePlayer(delta) {

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

    // =================================
    // SHIFT 달리기 기능
    // =================================

    const isRunning =
        keys["ShiftLeft"] ||
        keys["ShiftRight"];

    const speed = isRunning
        ? RUN_SPEED
        : WALK_SPEED;

    statusElement.textContent =
        isRunning ? "RUNNING" : "WALK";

    const moveX = direction.x * speed * delta;
    const moveZ = direction.z * speed * delta;

    // X축 충돌 검사
    const nextX = camera.position.x + moveX;

    if (!collides(nextX, camera.position.z)) {
        camera.position.x = nextX;
    }

    // Z축 충돌 검사
    const nextZ = camera.position.z + moveZ;

    if (!collides(camera.position.x, nextZ)) {
        camera.position.z = nextZ;
    }

    // =================================
    // 점프
    // =================================

    if (keys["Space"] && grounded) {

        velocityY = JUMP_SPEED;
        grounded = false;
    }

    velocityY -= GRAVITY * delta;

    camera.position.y += velocityY * delta;

    if (camera.position.y <= PLAYER_HEIGHT) {

        camera.position.y = PLAYER_HEIGHT;

        velocityY = 0;
        grounded = true;
    }

    // 천장보다 높게 올라가지 않도록 제한
    const maxEyeHeight = WALL_HEIGHT - 0.25;

    if (camera.position.y > maxEyeHeight) {
        camera.position.y = maxEyeHeight;
        velocityY = Math.min(velocityY, 0);
    }
}

// =====================================
// 14. 게임 루프
// =====================================

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

// =====================================
// 15. 창 크기 변경
// =====================================

function resizeGame() {

    const width = game.clientWidth;
    const height = game.clientHeight;

    camera.aspect = width / height;
    camera.updateProjectionMatrix();

    renderer.setSize(width, height);
}

window.addEventListener("resize", resizeGame);

new ResizeObserver(resizeGame).observe(game);

resizeGame();

</script>
</body>
</html>
"""

components.html(
    game_html,
    height=720,
    scrolling=False
)

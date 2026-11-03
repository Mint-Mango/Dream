import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Backrooms Exploration", page_icon="🎮", layout="wide")
st.title("BACKROOMS | Level 0")
st.caption("WASD 이동 · Shift 달리기 · Space 점프 · Q 캠코더 · 마우스 드래그 시점 회전 · R 재시작")

HTML = r"""
<!doctype html><html lang="ko"><head><meta charset="utf-8">
<style>
html,body{margin:0;width:100%;height:100%;overflow:hidden;background:#211f19;font-family:Arial,sans-serif}
#game{position:relative;width:100%;height:100vh;outline:none}
#hud{position:absolute;top:15px;left:15px;color:#eee8d2;background:#171610cc;padding:12px 16px;border-radius:7px;line-height:1.7;font-size:13px;pointer-events:none}
#status{position:absolute;top:15px;right:15px;color:#eee8d2;background:#171610cc;padding:10px 14px;border-radius:7px;font-size:13px;pointer-events:none}
#cross{position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);color:#28251b;font-size:22px;pointer-events:none}
</style>
<script type="importmap">
{
  "imports": {
    "three": "https://cdn.jsdelivr.net/npm/three@0.160.1/build/three.module.js",
    "three/addons/": "https://cdn.jsdelivr.net/npm/three@0.160.1/examples/jsm/"
  }
}
</script>
</head><body>
<div id="game" tabindex="0"></div><div id="cross">+</div>
<div id="hud"><b>BACKROOMS / LEVEL 0</b><br>WASD: 이동 · SHIFT: 달리기<br>SPACE: 점프 · 마우스 드래그: 시점<br>Q: 캠코더 ON/OFF<br>R: 시작 지점으로 복귀</div>
<div id="status">WALK | CAM OFF</div>
<script type="module">
import * as THREE from 'three';
import { mergeGeometries } from 'three/addons/utils/BufferGeometryUtils.js';

// ==================================================
// 기본 설정
// ==================================================
const N = 49;                     // 셀 개수 (49 x 49)
const CELL = 8;                   // 셀 한 변 길이
const WORLD = N * CELL;
const CEILING = 3.45;
const EYE = 1.55;                 // 플레이어 눈높이 약간 축소
const RADIUS = 0.24;              // 충돌 반경 축소
const WALK = 4.25;
const RUN = 8.6;
const JUMP = 5.4;
const GRAVITY = 17;
const MID = Math.floor(N / 2);

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x99916d);
scene.fog = new THREE.Fog(0x99916d, 26, 112);

const camera = new THREE.PerspectiveCamera(76, 1, 0.05, 130);
camera.position.set(0, EYE, 0);
camera.rotation.order = 'YXZ';

const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
renderer.outputColorSpace = THREE.SRGBColorSpace;
const host = document.getElementById('game');
host.appendChild(renderer.domElement);
const status = document.getElementById('status');

scene.add(new THREE.AmbientLight(0xffe7a3, 0.92));

let seed = 20261103;
function rand(){ seed = (Math.imul(seed,1664525) + 1013904223) >>> 0; return seed / 4294967296; }
const ri = n => Math.floor(rand() * n);
const center = i => (i - (N - 1) / 2) * CELL;
const cellKey = (x,z) => `${x},${z}`;

// ==================================================
// 절차적 텍스처
// ==================================================
function wallpaper(){
  const c = document.createElement('canvas'); c.width = 256; c.height = 256;
  const ctx = c.getContext('2d');
  ctx.fillStyle = '#c9bb79'; ctx.fillRect(0,0,256,256);
  for(let i=0;i<1400;i++){
    ctx.fillStyle = ri(2) ? 'rgba(72,62,32,0.055)' : 'rgba(252,244,191,0.065)';
    ctx.fillRect(ri(256),ri(256),1+ri(8),1+ri(12));
  }
  for(let x=10;x<256;x+=28){
    ctx.fillStyle='rgba(80,69,37,0.13)'; ctx.fillRect(x,0,2,256);
    ctx.fillStyle='rgba(255,244,181,0.17)'; ctx.fillRect(x+4,0,3,256);
    for(let y=10;y<256;y+=34){
      ctx.strokeStyle='rgba(85,73,40,0.16)'; ctx.lineWidth=1;
      ctx.strokeRect(x+8,y,12,18);
    }
  }
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.SRGBColorSpace;
  t.wrapS = t.wrapT = THREE.RepeatWrapping;
  t.anisotropy = Math.min(8, renderer.capabilities.getMaxAnisotropy());
  return t;
}
function carpet(){
  const c = document.createElement('canvas'); c.width = c.height = 128;
  const ctx = c.getContext('2d');
  ctx.fillStyle = '#77715b'; ctx.fillRect(0,0,128,128);
  for(let i=0;i<8500;i++){
    ctx.fillStyle = ri(2) ? 'rgba(17,17,13,0.09)' : 'rgba(235,222,174,0.065)';
    ctx.fillRect(ri(128),ri(128),1,1+ri(3));
  }
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.SRGBColorSpace;
  t.wrapS = t.wrapT = THREE.RepeatWrapping;
  return t;
}

const wallMat = new THREE.MeshLambertMaterial({ map: wallpaper() });
const floorMat = new THREE.MeshLambertMaterial({ map: carpet(), color: 0xb4b09b });
const ceilingMat = new THREE.MeshLambertMaterial({ color: 0xcac3a1, side: THREE.DoubleSide });
const trimMat = new THREE.MeshLambertMaterial({ color: 0x887d50 });
const holeWallMat = new THREE.MeshLambertMaterial({ color: 0x1b1712 });
const pitBottomMat = new THREE.MeshBasicMaterial({ color: 0x030303, side: THREE.DoubleSide });
const fog1Mat = new THREE.MeshBasicMaterial({ color: 0x000000, transparent:true, opacity:0.12, side: THREE.DoubleSide, depthWrite:false });
const fog2Mat = new THREE.MeshBasicMaterial({ color: 0x000000, transparent:true, opacity:0.18, side: THREE.DoubleSide, depthWrite:false });
const fog3Mat = new THREE.MeshBasicMaterial({ color: 0x000000, transparent:true, opacity:0.24, side: THREE.DoubleSide, depthWrite:false });

const wallParts=[], floorParts=[], trimParts=[], holeWallParts=[], pitBottomParts=[], fog1Parts=[], fog2Parts=[], fog3Parts=[];

function boxPart(bucket,x,y,z,w,h,d,repeat=2){
  const g = new THREE.BoxGeometry(w,h,d);
  const uv = g.attributes.uv;
  const scales = [[d,h],[d,h],[w,d],[w,d],[w,h],[w,h]];
  for(let face=0; face<6; face++){
    const [su,sv] = scales[face];
    for(let v=0; v<4; v++){
      const idx = face*4+v;
      uv.setXY(idx, uv.getX(idx)*su/repeat, uv.getY(idx)*sv/repeat);
    }
  }
  uv.needsUpdate = true;
  g.translate(x,y,z);
  bucket.push(g);
}
function planePart(bucket,x,y,z,w,h,rotX= -Math.PI/2){
  const g = new THREE.PlaneGeometry(w,h);
  g.rotateX(rotX);
  g.translate(x,y,z);
  bucket.push(g);
}
function combine(parts, mat){
  if(!parts.length) return;
  const merged = mergeGeometries(parts,false);
  scene.add(new THREE.Mesh(merged, mat));
  parts.forEach(g=>g.dispose());
}

// ==================================================
// 셀 구조 생성 - 순환형 연결이 많은 백룸 구조
// ==================================================
const cells = Array.from({length:N},()=>Array.from({length:N},()=>({n:true,s:true,e:true,w:true,seen:false})));
function carve(x,z,side){
  const dirs={n:[0,-1,'s'], s:[0,1,'n'], e:[1,0,'w'], w:[-1,0,'e']};
  const [dx,dz,other] = dirs[side];
  const nx=x+dx, nz=z+dz;
  if(nx<0||nz<0||nx>=N||nz>=N) return;
  cells[z][x][side]=false;
  cells[nz][nx][other]=false;
}

const stack=[[MID,MID]];
cells[MID][MID].seen=true;
while(stack.length){
  const [x,z]=stack[stack.length-1];
  const opts=[['n',0,-1],['s',0,1],['e',1,0],['w',-1,0]].filter(([s,dx,dz])=>{
    const nx=x+dx,nz=z+dz;
    return nx>=0&&nz>=0&&nx<N&&nz<N&&!cells[nz][nx].seen;
  });
  if(!opts.length){ stack.pop(); continue; }
  const [side,dx,dz]=opts[ri(opts.length)];
  carve(x,z,side);
  cells[z+dz][x+dx].seen=true;
  stack.push([x+dx,z+dz]);
}

// 긴 직선 복도와 큰 환형 동선
for(const z of [6, 14, 24, 33, 42]) for(let x=2;x<N-3;x++) carve(x,z,'e');
for(const x of [7, 18, 29, 39, 45]) for(let z=2;z<N-3;z++) carve(x,z,'s');

// 외곽과 중앙을 잇는 순환 루프 강화
for(let z=4;z<N-5;z++){
  carve(4,z,'s'); carve(N-6,z,'s');
}
for(let x=4;x<N-5;x++){
  carve(x,4,'e'); carve(x,N-6,'e');
}

const rooms=[
  {x:2,z:2,w:10,h:6},
  {x:15,z:3,w:14,h:6},
  {x:31,z:3,w:14,h:7},
  {x:4,z:13,w:16,h:8},
  {x:24,z:13,w:17,h:9},
  {x:38,z:13,w:8,h:11},
  {x:3,z:26,w:14,h:9},
  {x:19,z:27,w:12,h:11},
  {x:33,z:28,w:13,h:10},
  {x:6,z:39,w:18,h:7},
  {x:28,z:40,w:17,h:6},
  {x:19,z:20,w:11,h:9} // 시작 구역 주변
];
const roomCells = new Set();
for(const room of rooms){
  for(let z=room.z; z<room.z+room.h; z++) for(let x=room.x; x<room.x+room.w; x++){
    roomCells.add(cellKey(x,z));
    if(x < room.x + room.w - 1) carve(x,z,'e');
    if(z < room.z + room.h - 1) carve(x,z,'s');
  }
  for(let x=room.x; x<room.x+room.w; x+=2){
    if(room.z>0) carve(x,room.z,'n');
    if(room.z + room.h < N) carve(x,room.z+room.h-1,'s');
  }
  for(let z=room.z; z<room.z+room.h; z+=2){
    if(room.x>0) carve(room.x,z,'w');
    if(room.x + room.w < N) carve(room.x+room.w-1,z,'e');
  }
}
for(let z=1; z<N-1; z++) for(let x=1; x<N-1; x++){
  if(rand() < 0.54) carve(x,z, rand() < 0.5 ? 'e' : 's');
}
for(const side of ['n','s','e','w']) carve(MID,MID,side);

// ==================================================
// 충돌 버킷
// ==================================================
const buckets = new Map();
const bucketKey = (x,z)=>`${x},${z}`;
function addCollider(x,z,w,d){
  const b={minX:x-w/2,maxX:x+w/2,minZ:z-d/2,maxZ:z+d/2};
  const minX=Math.floor(b.minX/CELL), maxX=Math.floor(b.maxX/CELL);
  const minZ=Math.floor(b.minZ/CELL), maxZ=Math.floor(b.maxZ/CELL);
  for(let i=minX;i<=maxX;i++) for(let j=minZ;j<=maxZ;j++){
    const k=bucketKey(i,j);
    if(!buckets.has(k)) buckets.set(k,[]);
    buckets.get(k).push(b);
  }
}
function collision(x,z){
  const list = buckets.get(bucketKey(Math.floor(x/CELL), Math.floor(z/CELL))) || [];
  return list.some(b => x+RADIUS>b.minX && x-RADIUS<b.maxX && z+RADIUS>b.minZ && z-RADIUS<b.maxZ);
}

function wall(x,z,w,d){
  boxPart(wallParts, x, CEILING/2, z, w, CEILING, d);
  boxPart(trimParts, x, 0.11, z, w+0.025, 0.22, d+0.025);
  boxPart(trimParts, x, CEILING-0.085, z, w+0.035, 0.17, d+0.035);
  addCollider(x,z,w,d);
}
function boundary(x,z,horizontal,closed){
  const T=0.26, GAP=4.0;
  if(closed){ horizontal ? wall(x,z,CELL,T) : wall(x,z,T,CELL); return; }
  const piece=(CELL-GAP)/2, offset=(CELL+GAP)/4;
  if(horizontal){ wall(x-offset,z,piece,T); wall(x+offset,z,piece,T); }
  else{ wall(x,z-offset,T,piece); wall(x,z+offset,T,piece); }
}
for(let z=0;z<N;z++) for(let x=0;x<N;x++){
  const cx=center(x), cz=center(z), c=cells[z][x];
  boundary(cx + CELL/2, cz, false, c.e);
  boundary(cx, cz + CELL/2, true, c.s);
  if(x===0) boundary(cx - CELL/2, cz, false, true);
  if(z===0) boundary(cx, cz - CELL/2, true, true);
}

// ==================================================
// 기둥
// ==================================================
const pillarCells = new Set();
function pillar(x,z,width=1.55, cellX=null, cellZ=null){
  boxPart(wallParts,x,CEILING/2,z,width,CEILING,width);
  boxPart(trimParts,x,0.12,z,width+0.07,0.24,width+0.07);
  addCollider(x,z,width,width);
  if(cellX!==null && cellZ!==null) pillarCells.add(cellKey(cellX,cellZ));
}
for(const r of rooms){
  for(let z=r.z+1; z<r.z+r.h-1; z+=2) for(let x=r.x+1; x<r.x+r.w-1; x+=3){
    const px=center(x), pz=center(z);
    if(Math.hypot(px,pz)>8) pillar(px,pz,1.45,x,z);
  }
}
for(let z=2; z<N-2; z++) for(let x=2; x<N-2; x++){
  if(roomCells.has(cellKey(x,z)) || Math.abs(x-MID)+Math.abs(z-MID)<6) continue;
  if(rand()<0.038) pillar(center(x)+1.2, center(z)+1.2, 1.25, x, z);
}

// ==================================================
// 바닥 구멍 - 벽/기둥과 겹치지 않도록 열린 셀에서만 생성
// ==================================================
const pits=[];
const pitSet = new Set();
function openCell(x,z){
  if(x<1||z<1||x>=N-1||z>=N-1) return false;
  const c = cells[z][x];
  return !c.n && !c.s && !c.e && !c.w;
}
function nearBlocked(x,z){
  for(let dz=-1; dz<=1; dz++) for(let dx=-1; dx<=1; dx++){
    const nx=x+dx, nz=z+dz;
    if(nx<0||nz<0||nx>=N||nz>=N) return true;
    if(pillarCells.has(cellKey(nx,nz))) return true;
    if(pitSet.has(cellKey(nx,nz))) return true;
  }
  return false;
}
function makePit(cellX, cellZ){
  const cx = center(cellX), cz = center(cellZ);
  const size = rand()<0.35 ? 4.3 : 3.4;
  const edge = (CELL - size) / 2;
  // 상부 바닥 4조각
  boxPart(floorParts,cx-(CELL+size)/4,-0.12,cz,edge,0.24,CELL,2.5);
  boxPart(floorParts,cx+(CELL+size)/4,-0.12,cz,edge,0.24,CELL,2.5);
  boxPart(floorParts,cx,-0.12,cz-(CELL+size)/4,size,0.24,edge,2.5);
  boxPart(floorParts,cx,-0.12,cz+(CELL+size)/4,size,0.24,edge,2.5);
  // 구멍 측면 벽
  const depth = 8.2;
  const sideY = -depth/2;
  const t = 0.18;
  boxPart(holeWallParts,cx-size/2-t/2,sideY,cz,t,depth,size+t);
  boxPart(holeWallParts,cx+size/2+t/2,sideY,cz,t,depth,size+t);
  boxPart(holeWallParts,cx,sideY,cz-size/2-t/2,size,depth,t);
  boxPart(holeWallParts,cx,sideY,cz+size/2+t/2,size,depth,t);
  // 바닥과 안개 레이어
  planePart(pitBottomParts,cx,-8.15,cz,size*1.04,size*1.04);
  planePart(fog1Parts,cx,-2.2,cz,size*0.98,size*0.98);
  planePart(fog2Parts,cx,-4.3,cz,size*1.05,size*1.05);
  planePart(fog3Parts,cx,-6.7,cz,size*1.18,size*1.18);
  pits.push({x:cx, z:cz, half:size/2});
}

for(let z=0; z<N; z++) for(let x=0; x<N; x++){
  if(!openCell(x,z) || nearBlocked(x,z) || Math.abs(x-MID)+Math.abs(z-MID)<8){
    boxPart(floorParts, center(x), -0.12, center(z), CELL, 0.24, CELL, 2.5);
    continue;
  }
  if(rand() < 0.020){
    pitSet.add(cellKey(x,z));
    makePit(x,z);
  } else {
    boxPart(floorParts, center(x), -0.12, center(z), CELL, 0.24, CELL, 2.5);
  }
}

combine(floorParts, floorMat);
combine(wallParts, wallMat);
combine(trimParts, trimMat);
combine(holeWallParts, holeWallMat);
combine(pitBottomParts, pitBottomMat);
combine(fog1Parts, fog1Mat);
combine(fog2Parts, fog2Mat);
combine(fog3Parts, fog3Mat);

const roof = new THREE.Mesh(new THREE.PlaneGeometry(WORLD, WORLD), ceilingMat);
roof.rotation.x = Math.PI/2; roof.position.y = CEILING; scene.add(roof);

// ==================================================
// 조명 - 80% 정상, 10% 꺼짐, 10% 깜빡임
// ==================================================
const fixtures=[];
const fixtureGrid=Array.from({length:N},()=>Array(N));
for(let z=0; z<N; z++) for(let x=0; x<N; x++){
  const f={x:center(x), z:center(z), mode:'on', lit:true, phase:rand()*6.28};
  fixtureGrid[z][x]=f; fixtures.push(f);
}
for(let i=fixtures.length-1;i>0;i--){ const j=ri(i+1); [fixtures[i],fixtures[j]]=[fixtures[j],fixtures[i]]; }
const total=fixtures.length;
const offCount=Math.floor(total*0.1), flickerCount=Math.floor(total*0.1);
fixtures.forEach((f,i)=>{
  f.mode = i<offCount ? 'off' : i<offCount+flickerCount ? 'flicker' : 'on';
  f.lit = f.mode !== 'off';
});
const lightGeometry = new THREE.BoxGeometry(2.8,0.045,0.65);
const panels = new THREE.InstancedMesh(lightGeometry, new THREE.MeshBasicMaterial(), total);
const dummy = new THREE.Object3D();
const bright = new THREE.Color(0xfff1c6), dark = new THREE.Color(0x514c3a);
fixtures.forEach((f,i)=>{
  dummy.position.set(f.x, CEILING-0.055, f.z);
  dummy.updateMatrix();
  panels.setMatrixAt(i, dummy.matrix);
  panels.setColorAt(i, f.mode==='off' ? dark : bright);
});
panels.instanceMatrix.needsUpdate=true;
panels.instanceColor.needsUpdate=true;
scene.add(panels);

const LIGHT_POOL_SIZE=12;
const lightPool=[];
for(let i=0;i<LIGHT_POOL_SIZE;i++){
  const light=new THREE.PointLight(0xffe8ab,2.0,17,1.8);
  light.visible=false; scene.add(light); lightPool.push(light);
}
function fixtureLit(f){ return f.mode==='on' || (f.mode==='flicker' && f.lit); }
function updateNearbyLighting(){
  const px=camera.position.x, pz=camera.position.z;
  const near=[];
  const ix=Math.round(px/CELL + (N-1)/2), iz=Math.round(pz/CELL + (N-1)/2);
  for(let z=Math.max(0,iz-3); z<=Math.min(N-1,iz+3); z++){
    for(let x=Math.max(0,ix-3); x<=Math.min(N-1,ix+3); x++){
      const f=fixtureGrid[z][x];
      const d2=(px-f.x)**2 + (pz-f.z)**2;
      if(d2<500 && fixtureLit(f)) near.push({f,d2});
    }
  }
  near.sort((a,b)=>a.d2-b.d2);
  lightPool.forEach((light,i)=>{
    const v=near[i];
    light.visible=!!v;
    if(v){ light.position.set(v.f.x, CEILING-0.35, v.f.z); light.intensity=2.0; }
  });
}

// ==================================================
// 입력 / 움직임
// ==================================================
const keys={};
let yaw=0, pitch=0, dragging=false, oldX=0, oldY=0;
let vy=0, grounded=true, camcorder=false;
window.addEventListener('keydown', e=>{
  keys[e.code]=true;
  if(['Space','ArrowUp','ArrowDown','ArrowLeft','ArrowRight'].includes(e.code)) e.preventDefault();
  if(e.code==='KeyR' && !e.repeat) reset();
  if(e.code==='KeyQ' && !e.repeat) camcorder=!camcorder;
});
window.addEventListener('keyup', e=>keys[e.code]=false);
window.addEventListener('blur', ()=>{ Object.keys(keys).forEach(k=>keys[k]=false); dragging=false; });
renderer.domElement.addEventListener('mousedown', e=>{ dragging=true; oldX=e.clientX; oldY=e.clientY; host.focus(); });
window.addEventListener('mouseup', ()=>dragging=false);
window.addEventListener('mousemove', e=>{
  if(!dragging) return;
  yaw -= (e.clientX-oldX)*0.003;
  pitch = THREE.MathUtils.clamp(pitch - (e.clientY-oldY)*0.003, -1.48, 1.48);
  oldX = e.clientX; oldY = e.clientY;
});
function reset(){ camera.position.set(0,EYE,0); yaw=0; pitch=0; vy=0; grounded=true; }
function overHole(x,z){
  return pits.some(p => Math.abs(x-p.x) < p.half - RADIUS*0.45 && Math.abs(z-p.z) < p.half - RADIUS*0.45);
}
function step(dt){
  camera.rotation.y = yaw;
  camera.rotation.x = pitch;
  let ix=0, iz=0;
  if(keys.KeyW) iz -= 1;
  if(keys.KeyS) iz += 1;
  if(keys.KeyA) ix -= 1;
  if(keys.KeyD) ix += 1;
  const len=Math.hypot(ix,iz)||1; ix/=len; iz/=len;
  const running=!!(keys.ShiftLeft||keys.ShiftRight);
  const speed=running?RUN:WALK;
  status.textContent=(running?'RUNNING':'WALK')+' | CAM '+(camcorder?'ON':'OFF');
  const dx=(ix*Math.cos(yaw)+iz*Math.sin(yaw))*speed*dt;
  const dz=(-ix*Math.sin(yaw)+iz*Math.cos(yaw))*speed*dt;
  const count=Math.max(1, Math.ceil(Math.hypot(dx,dz)/0.22));
  for(let i=0;i<count;i++){
    const xx=camera.position.x+dx/count;
    if(!collision(xx,camera.position.z)) camera.position.x=xx;
    const zz=camera.position.z+dz/count;
    if(!collision(camera.position.x,zz)) camera.position.z=zz;
  }
  const hole=overHole(camera.position.x,camera.position.z);
  if(keys.Space && grounded && !hole){ vy=JUMP; grounded=false; }
  vy -= GRAVITY*dt;
  camera.position.y += vy*dt;
  if(!hole && camera.position.y<=EYE){ camera.position.y=EYE; vy=0; grounded=true; }
  else if(hole){ grounded=false; }
  if(camera.position.y>CEILING-0.2){ camera.position.y=CEILING-0.2; vy=Math.min(0,vy); }
  if(camera.position.y<-7) reset();
}

let lastBlink=0;
function updateLights(t){
  if(t-lastBlink<0.09) return; lastBlink=t;
  fixtures.forEach((f,i)=>{
    if(f.mode!=='flicker') return;
    const flick=(Math.sin(t*8+f.phase)+Math.sin(t*19+f.phase*3)>0.65)||rand()<0.12;
    f.lit=!flick;
    panels.setColorAt(i, f.lit ? bright : dark);
  });
  panels.instanceColor.needsUpdate=true;
}

// ==================================================
// 캠코더 후처리
// ==================================================
const renderTarget = new THREE.WebGLRenderTarget(1,1,{ minFilter:THREE.LinearFilter, magFilter:THREE.LinearFilter, depthBuffer:true });
const postScene = new THREE.Scene();
const postCamera = new THREE.OrthographicCamera(-1,1,1,-1,0,1);
const postMat = new THREE.ShaderMaterial({
  uniforms:{ tDiffuse:{value:renderTarget.texture}, uTime:{value:0}, uResolution:{value:new THREE.Vector2(1,1)} },
  vertexShader:`varying vec2 vUv; void main(){ vUv=uv; gl_Position=vec4(position.xy,0.0,1.0); }`,
  fragmentShader:`
    precision mediump float;
    uniform sampler2D tDiffuse;
    uniform float uTime;
    uniform vec2 uResolution;
    varying vec2 vUv;
    float noise(vec2 p){ return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453123); }
    void main(){
      vec2 uv=vUv;
      float line=floor(uv.y*uResolution.y/3.0);
      float jitter=(noise(vec2(line,floor(uTime*24.0)))-0.5)*0.0012;
      uv.x+=jitter;
      vec2 px=1.0/uResolution;
      vec3 col=texture2D(tDiffuse,uv).rgb*0.42;
      col+=texture2D(tDiffuse,uv+vec2(px.x*1.4,0.0)).rgb*0.145;
      col+=texture2D(tDiffuse,uv-vec2(px.x*1.4,0.0)).rgb*0.145;
      col+=texture2D(tDiffuse,uv+vec2(0.0,px.y*1.4)).rgb*0.145;
      col+=texture2D(tDiffuse,uv-vec2(0.0,px.y*1.4)).rgb*0.145;
      float grain=noise(uv*uResolution+vec2(uTime*97.1,uTime*53.7))-0.5;
      col+=grain*0.085;
      float scan=0.96+0.04*sin(uv.y*uResolution.y*1.9);
      col*=scan;
      vec2 p=uv*2.0-1.0;
      float vignette=1.0-0.3*pow(dot(p,p)*0.5,1.25);
      col*=vignette;
      col=mix(col,vec3(dot(col,vec3(0.299,0.587,0.114))),0.12);
      gl_FragColor=vec4(col,1.0);
    }
  `,
  depthTest:false, depthWrite:false
});
postScene.add(new THREE.Mesh(new THREE.PlaneGeometry(2,2), postMat));

const clock = new THREE.Clock();
let lightTimer=0;
function animate(){
  requestAnimationFrame(animate);
  const dt=Math.min(clock.getDelta(),0.05);
  step(dt);
  updateLights(clock.elapsedTime);
  lightTimer+=dt;
  if(lightTimer>0.18){ updateNearbyLighting(); lightTimer=0; }
  if(camcorder){
    renderer.setRenderTarget(renderTarget);
    renderer.render(scene,camera);
    renderer.setRenderTarget(null);
    postMat.uniforms.uTime.value=clock.elapsedTime;
    renderer.render(postScene,postCamera);
  } else {
    renderer.setRenderTarget(null);
    renderer.render(scene,camera);
  }
}
function resize(){
  const w=host.clientWidth, h=host.clientHeight;
  camera.aspect=w/h; camera.updateProjectionMatrix(); renderer.setSize(w,h);
  const scale=renderer.getPixelRatio();
  renderTarget.setSize(Math.max(1,Math.floor(w*scale)), Math.max(1,Math.floor(h*scale)));
  postMat.uniforms.uResolution.value.set(w*scale,h*scale);
}
new ResizeObserver(resize).observe(host);
resize();
updateNearbyLighting();
animate();
</script></body></html>
"""

components.html(HTML, height=740, scrolling=False)

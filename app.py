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

const N=49, CELL=8, WORLD=N*CELL, HALF=WORLD/2, CEILING=3.45;
const EYE=1.55, RADIUS=0.24, WALK=4.25, RUN=8.6, JUMP=5.4, GRAVITY=17;
const scene=new THREE.Scene();
scene.background=new THREE.Color(0x99916d);
scene.fog=new THREE.Fog(0x99916d,24,100);
const camera=new THREE.PerspectiveCamera(76,1,0.05,125);
camera.position.set(0,EYE,0); camera.rotation.order='YXZ';
const renderer=new THREE.WebGLRenderer({antialias:true});
renderer.setPixelRatio(Math.min(devicePixelRatio,2));
renderer.outputColorSpace=THREE.SRGBColorSpace;
const host=document.getElementById('game');host.appendChild(renderer.domElement);
const status=document.getElementById('status');
scene.add(new THREE.AmbientLight(0xffe7a3,0.95));

// 반복 가능한 의사난수: 새로고침해도 같은 구조
let seed=20261103;
function rand(){seed=(Math.imul(seed,1664525)+1013904223)>>>0;return seed/4294967296;}
const ri=(n)=>Math.floor(rand()*n);
const center=i=>(i-(N-1)/2)*CELL;

// 캔버스로 노후한 벽지 텍스처 생성 (외부 이미지 파일 불필요)
function wallpaper(){
 const c=document.createElement('canvas');c.width=256;c.height=256;
 const ctx=c.getContext('2d');ctx.fillStyle='#c9bb79';ctx.fillRect(0,0,256,256);
 for(let i=0;i<1100;i++){
   const v=ri(2)?'rgba(72,62,32,0.055)':'rgba(252,244,191,0.065)';
   ctx.fillStyle=v;ctx.fillRect(ri(256),ri(256),1+ri(8),1+ri(12));
 }
 // 백룸 느낌의 반복 세로 무늬
 for(let x=10;x<256;x+=32){
   ctx.fillStyle='rgba(80,69,37,0.12)';ctx.fillRect(x,0,2,256);
   ctx.fillStyle='rgba(255,244,181,0.16)';ctx.fillRect(x+4,0,3,256);
   for(let y=8;y<256;y+=36){
     ctx.strokeStyle='rgba(85,73,40,0.15)';ctx.lineWidth=1;
     ctx.strokeRect(x+9,y,12,20);
   }
 }
 const t=new THREE.CanvasTexture(c);t.colorSpace=THREE.SRGBColorSpace;
 t.wrapS=t.wrapT=THREE.RepeatWrapping;
 t.anisotropy=Math.min(8,renderer.capabilities.getMaxAnisotropy());
 return t;
}
function carpet(){
 const c=document.createElement('canvas');c.width=c.height=128;
 const ctx=c.getContext('2d');ctx.fillStyle='#77715b';ctx.fillRect(0,0,128,128);
 for(let i=0;i<7500;i++){
   const v=ri(2)?'rgba(17,17,13,0.09)':'rgba(235,222,174,0.065)';
   ctx.fillStyle=v;ctx.fillRect(ri(128),ri(128),1,1+ri(3));
 }
 const t=new THREE.CanvasTexture(c);t.colorSpace=THREE.SRGBColorSpace;
 t.wrapS=t.wrapT=THREE.RepeatWrapping;return t;
}
const wallMat=new THREE.MeshLambertMaterial({map:wallpaper()});
const floorMat=new THREE.MeshLambertMaterial({map:carpet(),color:0xb4b09b});
const ceilingMat=new THREE.MeshLambertMaterial({color:0xcac3a1,side:THREE.DoubleSide});
const trimMat=new THREE.MeshLambertMaterial({color:0x887d50});
const holeMat=new THREE.MeshBasicMaterial({color:0x080807,side:THREE.DoubleSide});
const wallParts=[], floorParts=[], trimParts=[], pitParts=[];

// 박스의 UV를 실제 길이에 비례해 반복: 긴 벽에서도 무늬가 늘어나지 않도록 처리
function boxPart(bucket,x,y,z,w,h,d,repeat=2){
 const g=new THREE.BoxGeometry(w,h,d);
 const uv=g.attributes.uv;
 const scales=[[d,h],[d,h],[w,d],[w,d],[w,h],[w,h]];
 for(let face=0;face<6;face++){
   const [su,sv]=scales[face];
   for(let v=0;v<4;v++){
     const idx=face*4+v;
     uv.setXY(idx,uv.getX(idx)*su/repeat,uv.getY(idx)*sv/repeat);
   }
 }
 uv.needsUpdate=true;
 g.translate(x,y,z);bucket.push(g);
}
function combine(parts,mat){
 if(!parts.length)return;
 const merged=mergeGeometries(parts,false);
 if(!merged)throw new Error('지형 병합 실패');
 scene.add(new THREE.Mesh(merged,mat));
 parts.forEach(g=>g.dispose());
}

// 미로 셀: N=31, 한 변 248m. 탐색 가능한 모든 구역 연결.
const cells=Array.from({length:N},()=>Array.from({length:N},()=>({n:true,s:true,e:true,w:true,seen:false})));
function carve(x,z,side){
 const dirs={n:[0,-1,'s'],s:[0,1,'n'],e:[1,0,'w'],w:[-1,0,'e']};
 const [dx,dz,other]=dirs[side],nx=x+dx,nz=z+dz;
 if(nx<0||nz<0||nx>=N||nz>=N)return;
 cells[z][x][side]=false;cells[nz][nx][other]=false;
}
const stack=[[Math.floor(N/2),Math.floor(N/2)]];
cells[stack[0][1]][stack[0][0]].seen=true;
while(stack.length){
 const [x,z]=stack[stack.length-1];
 const opts=[['n',0,-1],['s',0,1],['e',1,0],['w',-1,0]]
  .filter(([s,dx,dz])=>x+dx>=0&&z+dz>=0&&x+dx<N&&z+dz<N&&!cells[z+dz][x+dx].seen);
 if(!opts.length){stack.pop();continue;}
 const [side,dx,dz]=opts[ri(opts.length)];carve(x,z,side);
 cells[z+dz][x+dx].seen=true;stack.push([x+dx,z+dz]);
}
// 긴 복도는 전체 맵을 가로지르고, 교차로는 여러 번 돌아갈 수 있도록 연결
for(const z of [6,14,24,33,42])for(let x=2;x<N-3;x++)carve(x,z,'e');
for(const x of [7,18,29,39,45])for(let z=2;z<N-3;z++)carve(x,z,'s');

// 여러 칸을 하나의 큰 공간으로 합침: 기둥이 있는 홀과 열린 구역
const rooms=[
 {x:2,z:2,w:10,h:6}, {x:15,z:3,w:14,h:6},
 {x:31,z:3,w:14,h:7}, {x:4,z:13,w:16,h:8},
 {x:24,z:13,w:17,h:9}, {x:38,z:13,w:8,h:11},
 {x:3,z:26,w:14,h:9}, {x:19,z:27,w:12,h:11},
 {x:33,z:28,w:13,h:10}, {x:6,z:39,w:18,h:7},
 {x:28,z:40,w:17,h:6}, {x:19,z:20,w:11,h:9}
];
const roomCells=new Set();
for(const room of rooms){
 for(let z=room.z;z<room.z+room.h;z++)for(let x=room.x;x<room.x+room.w;x++){
  roomCells.add(`${x},${z}`);
  if(x<room.x+room.w-1)carve(x,z,'e');
  if(z<room.z+room.h-1)carve(x,z,'s');
 }
 // 방을 미로의 여러 방향과 연결 (단일 출입구 방이 되지 않게)
 for(let x=room.x;x<room.x+room.w;x+=2){
  if(room.z>0)carve(x,room.z,'n');
  if(room.z+room.h<N)carve(x,room.z+room.h-1,'s');
 }
 for(let z=room.z;z<room.z+room.h;z+=2){
  if(room.x>0)carve(room.x,z,'w');
  if(room.x+room.w<N)carve(room.x+room.w-1,z,'e');
 }
}
// DFS 기본 통로 외 벽의 상당수를 열어 루프 구조로 전환
for(let z=1;z<N-1;z++)for(let x=1;x<N-1;x++){
 if(rand()<0.47)carve(x,z,rand()<0.5?'e':'s');
}
// 지도 중앙은 시작 방으로, 네 방향 모두 연결
const MID=Math.floor(N/2);
for(const side of ['n','s','e','w'])carve(MID,MID,side);

// 충돌은 플레이어 주변의 작은 버킷만 확인
const buckets=new Map();
const key=(x,z)=>`${x},${z}`;
function collider(x,z,w,d){
 const b={minX:x-w/2,maxX:x+w/2,minZ:z-d/2,maxZ:z+d/2};
 const minX=Math.floor(b.minX/CELL),maxX=Math.floor(b.maxX/CELL);
 const minZ=Math.floor(b.minZ/CELL),maxZ=Math.floor(b.maxZ/CELL);
 for(let i=minX;i<=maxX;i++)for(let j=minZ;j<=maxZ;j++){
  const k=key(i,j);if(!buckets.has(k))buckets.set(k,[]);
  buckets.get(k).push(b);
 }
}
function wall(x,z,w,d){
 boxPart(wallParts,x,CEILING/2,z,w,CEILING,d);
 boxPart(trimParts,x,0.11,z,w+0.025,0.22,d+0.025);
 boxPart(trimParts,x,CEILING-0.085,z,w+0.035,0.17,d+0.035);
 collider(x,z,w,d);
}
// 십자가 모양을 만들던 열린 경계의 짧은 벽 조각을 생성하지 않는다.
// 닫힌 경계만 완전한 벽으로 생성하고, 일직선 벽은 하나로 병합한다.
// 연결된 교차 벽은 폭 0.65m의 연속된 두꺼운 벽으로 표시된다.
const WALL_THICKNESS=0.65;
const horiz=Array.from({length:N+1},()=>Array(N).fill(false));
const vert=Array.from({length:N},()=>Array(N+1).fill(false));
for(let z=0;z<N;z++)for(let x=0;x<N;x++){
  const c=cells[z][x];
  if(c.s)horiz[z+1][x]=true;
  if(c.e)vert[z][x+1]=true;
  if(z===0)horiz[0][x]=true;
  if(x===0)vert[z][0]=true;
}
// 단독 십자가는 열린 경계의 반쪽 벽들이 모여 발생했으므로 완전히 제거된다.
// 연결된 직선 벽은 연속 길이에 맞춰 하나의 두꺼운 벽으로 합친다.
for(let z=0;z<=N;z++){
  for(let x=0;x<N;){
    if(!horiz[z][x]){x++;continue;}
    const start=x;
    while(x<N&&horiz[z][x])x++;
    const count=x-start;
    const wallX=(center(start)+center(x-1))/2;
    const wallZ=(z-N/2)*CELL;
    wall(wallX,wallZ,count*CELL,WALL_THICKNESS);
  }
}
for(let x=0;x<=N;x++){
  for(let z=0;z<N;){
    if(!vert[z][x]){z++;continue;}
    const start=z;
    while(z<N&&vert[z][x])z++;
    const count=z-start;
    const wallX=(x-N/2)*CELL;
    const wallZ=(center(start)+center(z-1))/2;
    wall(wallX,wallZ,WALL_THICKNESS,count*CELL);
  }
}

// 넓은 방과 일부 복도의 사각 기둥
const pillars=[];
function pillar(x,z,width=1.5){
 boxPart(wallParts,x,CEILING/2,z,width,CEILING,width);
 boxPart(trimParts,x,0.12,z,width+0.07,0.24,width+0.07);
 collider(x,z,width,width);
 pillars.push([x,z]);
}
for(const r of rooms){
 for(let z=r.z+1;z<r.z+r.h-1;z+=2)for(let x=r.x+1;x<r.x+r.w-1;x+=2){
  const px=(center(x)+center(x-1))/2, pz=(center(z)+center(z-1))/2;
  if(Math.hypot(px,pz)>7)pillar(px,pz,1.45);
 }
}
for(let z=1;z<N-1;z++)for(let x=1;x<N-1;x++){
 if(roomCells.has(`${x},${z}`)||Math.abs(x-MID)+Math.abs(z-MID)<5)continue;
 if(rand()<0.055)pillar(center(x)+1.4,center(z)+1.4,1.25);
}

// 구멍은 벽/기둥과 분리된 열린 공간에서만 생성한다.
const pits=[];
const pitSet=new Set();
const pitWallParts=[], pitFogParts=[], pitBottomParts=[];
const pitWallMat=new THREE.MeshLambertMaterial({color:0x161411,side:THREE.DoubleSide});
const pitFogMat=new THREE.MeshBasicMaterial({color:0x000000,transparent:true,opacity:0.38,side:THREE.DoubleSide,depthWrite:false});
const pitBottomMat=new THREE.MeshBasicMaterial({color:0x000000,side:THREE.DoubleSide});
function pitSafe(x,z){
 if(x<2||z<2||x>=N-2||z>=N-2)return false;
 if(Math.abs(x-MID)+Math.abs(z-MID)<8)return false;
 const c=cells[z][x];
 if(c.n||c.s||c.e||c.w)return false;
 const cx=center(x),cz=center(z),radius=3.1;
 for(const [px,pz] of pillars){
  if(Math.abs(px-cx)<radius+1.2&&Math.abs(pz-cz)<radius+1.2)return false;
 }
 for(const p of pits){
  if(Math.abs(p.x-cx)<CELL*1.5&&Math.abs(p.z-cz)<CELL*1.5)return false;
 }
 return true;
}
function pit(x,z){
 const cx=center(x),cz=center(z),size=3.6,edge=(CELL-size)/2;
 boxPart(floorParts,cx-(CELL+size)/4,-0.12,cz,edge,0.24,CELL,2.5);
 boxPart(floorParts,cx+(CELL+size)/4,-0.12,cz,edge,0.24,CELL,2.5);
 boxPart(floorParts,cx,-0.12,cz-(CELL+size)/4,size,0.24,edge,2.5);
 boxPart(floorParts,cx,-0.12,cz+(CELL+size)/4,size,0.24,edge,2.5);
 const depth=8.5,th=0.15;
 boxPart(pitWallParts,cx-size/2-th/2,-depth/2,cz,th,depth,size+th);
 boxPart(pitWallParts,cx+size/2+th/2,-depth/2,cz,th,depth,size+th);
 boxPart(pitWallParts,cx,-depth/2,cz-size/2-th/2,size,depth,th);
 boxPart(pitWallParts,cx,-depth/2,cz+size/2+th/2,size,depth,th);
 // 여러 장의 반투명 검은 막을 겹쳐 깊이를 볼 수 없게 만든다.
 for(const y of [-1.6,-3.2,-5.0,-6.8]){
  const g=new THREE.PlaneGeometry(size-0.02,size-0.02);
  g.rotateX(-Math.PI/2);g.translate(cx,y,cz);
  pitFogParts.push(g);
 }
 boxPart(pitBottomParts,cx,-8.55,cz,size,0.05,size);
 pits.push({x:cx,z:cz,half:size/2});
}
for(let z=0;z<N;z++)for(let x=0;x<N;x++){
 if(rand()<0.023&&pitSafe(x,z)){
  pitSet.add(key(x,z));pit(x,z);
 }else{
  boxPart(floorParts,center(x),-0.12,center(z),CELL,0.24,CELL,2.5);
 }
}
combine(floorParts,floorMat);
combine(wallParts,wallMat);
combine(trimParts,trimMat);
combine(pitWallParts,pitWallMat);
combine(pitFogParts,pitFogMat);
combine(pitBottomParts,pitBottomMat);
const roof=new THREE.Mesh(new THREE.PlaneGeometry(WORLD,WORLD),ceilingMat);
roof.rotation.x=Math.PI/2;roof.position.y=CEILING;scene.add(roof);

// 천장 형광등: 고정된 비율로 80% 정상, 10% 소등, 10% 깜빡임
const fixtures=[];
const fixtureGrid=Array.from({length:N},()=>Array(N).fill(null));
// 전등의 실제 외곽(2.8m x 0.65m)에 여유 공간까지 포함하여 벽/기둥 겹침 방지
function lightFits(px,pz){
 const hx=1.55,hz=0.48;
 const minX=Math.floor((px-hx)/CELL),maxX=Math.floor((px+hx)/CELL);
 const minZ=Math.floor((pz-hz)/CELL),maxZ=Math.floor((pz+hz)/CELL);
 const tested=new Set();
 for(let a=minX;a<=maxX;a++)for(let b=minZ;b<=maxZ;b++){
  for(const wallBox of (buckets.get(key(a,b))||[])){
   if(tested.has(wallBox))continue;
   tested.add(wallBox);
   if(px+hx>wallBox.minX&&px-hx<wallBox.maxX&&
      pz+hz>wallBox.minZ&&pz-hz<wallBox.maxZ)return false;
  }
 }
 return true;
}
for(let z=0;z<N;z++)for(let x=0;x<N;x++){
 const cx=center(x),cz=center(z);
 // 중앙이 기둥과 겹치면 같은 방 안의 다른 위치로 이동
 const offsets=[[0,0],[-2.0,0],[2.0,0],[0,-2.0],[0,2.0],[-2,-2],[2,2],[-2,2],[2,-2]];
 let pos=null;
 for(const [ox,oz] of offsets){
  if(lightFits(cx+ox,cz+oz)){pos={x:cx+ox,z:cz+oz};break;}
 }
 if(!pos)continue; // 안전한 자리가 없다면 전등을 놓지 않음
 const f={...pos,mode:'on',lit:true};
 fixtureGrid[z][x]=f;
 fixtures.push(f);
}
// fixtureGrid는 원래 순서를 유지하고, fixtures 배열만 섞어 비율 배정
for(let i=fixtures.length-1;i>0;i--){const j=ri(i+1);[fixtures[i],fixtures[j]]=[fixtures[j],fixtures[i]];}
const total=fixtures.length;
const offCount=Math.floor(total*0.1),flickerCount=Math.floor(total*0.1);
fixtures.forEach((f,i)=>{f.mode=i<offCount?'off':i<offCount+flickerCount?'flicker':'on';f.phase=rand()*6.28;f.lit=f.mode!=='off';});
const lightGeometry=new THREE.BoxGeometry(2.8,0.045,0.65);
const panels=new THREE.InstancedMesh(lightGeometry,new THREE.MeshBasicMaterial({vertexColors:false}),total);
const dummy=new THREE.Object3D();
const bright=new THREE.Color(0xfff1c6), dark=new THREE.Color(0x514c3a);
fixtures.forEach((f,i)=>{
 dummy.position.set(f.x,CEILING-0.055,f.z);dummy.updateMatrix();panels.setMatrixAt(i,dummy.matrix);
 panels.setColorAt(i,f.mode==='off'?dark:bright);
});
panels.instanceMatrix.needsUpdate=true;panels.instanceColor.needsUpdate=true;
scene.add(panels);
// 실제 광원: 플레이어 근처의 형광등을 재활용해서 넓은 맵에서도 성능 유지
// 전체 패널 80% 정상 / 10% 꺼짐 / 10% 깜빡임
const LIGHT_POOL_SIZE=12;
const lightPool=[];
for(let i=0;i<LIGHT_POOL_SIZE;i++){
 const light=new THREE.PointLight(0xffe8ab,2.0,17,1.8);
 light.visible=false;
 scene.add(light);
 lightPool.push(light);
}
function fixtureLit(f){return f.mode==='on'||(f.mode==='flicker'&&f.lit);}
function updateNearbyLighting(){
 const px=camera.position.x,pz=camera.position.z;
 const near=[];
 // 셀 단위 탐색: 가까운 후보만 확인해서 전체 맵 스캔을 피함
 const ix=Math.round(px/CELL+(N-1)/2),iz=Math.round(pz/CELL+(N-1)/2);
 for(let z=Math.max(0,iz-3);z<=Math.min(N-1,iz+3);z++){
  for(let x=Math.max(0,ix-3);x<=Math.min(N-1,ix+3);x++){
   const f=fixtureGrid[z][x];
   if(!f)continue;
   const d2=(px-f.x)**2+(pz-f.z)**2;
   if(d2<500&&fixtureLit(f))near.push({f,d2});
  }
 }
 near.sort((a,b)=>a.d2-b.d2);
 lightPool.forEach((light,i)=>{
  const v=near[i];
  light.visible=!!v;
  if(v){light.position.set(v.f.x,CEILING-0.35,v.f.z);light.intensity=2.0;}
 });
}
// 입력
const keys={};let yaw=0,pitch=0,dragging=false,oldX=0,oldY=0;
let vy=0,grounded=true,camcorder=false;
window.addEventListener('keydown',e=>{
 keys[e.code]=true;
 if(['Space','ArrowUp','ArrowDown','ArrowLeft','ArrowRight'].includes(e.code))e.preventDefault();
 if(e.code==='KeyR'&&!e.repeat)reset();
 if(e.code==='KeyQ'&&!e.repeat)camcorder=!camcorder;
});
window.addEventListener('keyup',e=>keys[e.code]=false);
window.addEventListener('blur',()=>{Object.keys(keys).forEach(k=>keys[k]=false);dragging=false;});
renderer.domElement.addEventListener('mousedown',e=>{dragging=true;oldX=e.clientX;oldY=e.clientY;host.focus();});
window.addEventListener('mouseup',()=>dragging=false);
window.addEventListener('mousemove',e=>{
 if(!dragging)return;
 yaw-=(e.clientX-oldX)*0.003;
 pitch=THREE.MathUtils.clamp(pitch-(e.clientY-oldY)*0.003,-1.48,1.48);
 oldX=e.clientX;oldY=e.clientY;
});
function reset(){camera.position.set(0,EYE,0);yaw=0;pitch=0;vy=0;grounded=true;}
function collision(x,z){
 const list=buckets.get(key(Math.floor(x/CELL),Math.floor(z/CELL)))||[];
 return list.some(b=>x+RADIUS>b.minX&&x-RADIUS<b.maxX&&z+RADIUS>b.minZ&&z-RADIUS<b.maxZ);
}
function overHole(x,z){
 // 구멍의 안쪽으로 충분히 진입하면 바닥 지지를 잃음
 return pits.some(p=>Math.abs(x-p.x)<p.half-RADIUS*0.5&&Math.abs(z-p.z)<p.half-RADIUS*0.5);
}
function step(dt){
 camera.rotation.y=yaw;camera.rotation.x=pitch;
 let ix=0,iz=0;
 if(keys.KeyW)iz-=1;if(keys.KeyS)iz+=1;
 if(keys.KeyA)ix-=1;if(keys.KeyD)ix+=1;
 const len=Math.hypot(ix,iz)||1;ix/=len;iz/=len;
 const running=!!(keys.ShiftLeft||keys.ShiftRight);
 const speed=running?RUN:WALK;
 status.textContent=(running?'RUNNING':'WALK')+' | CAM '+(camcorder?'ON':'OFF');
 const dx=(ix*Math.cos(yaw)+iz*Math.sin(yaw))*speed*dt;
 const dz=(-ix*Math.sin(yaw)+iz*Math.cos(yaw))*speed*dt;
 // 작은 단계로 나누어 빠른 달리기에서 벽 통과 방지
 const count=Math.max(1,Math.ceil(Math.hypot(dx,dz)/0.22));
 for(let i=0;i<count;i++){
  const xx=camera.position.x+dx/count;
  if(!collision(xx,camera.position.z))camera.position.x=xx;
  const zz=camera.position.z+dz/count;
  if(!collision(camera.position.x,zz))camera.position.z=zz;
 }
 const hole=overHole(camera.position.x,camera.position.z);
 if(keys.Space&&grounded&&!hole){vy=JUMP;grounded=false;}
 vy-=GRAVITY*dt;camera.position.y+=vy*dt;
 if(!hole&&camera.position.y<=EYE){camera.position.y=EYE;vy=0;grounded=true;}
 else if(hole){grounded=false;}
 if(camera.position.y>CEILING-0.2){camera.position.y=CEILING-0.2;vy=Math.min(0,vy);}
 if(camera.position.y<-7)reset();
}
let lastBlink=0;
function updateLights(t){
 if(t-lastBlink<0.09)return;lastBlink=t;
 fixtures.forEach((f,i)=>{
  if(f.mode!=='flicker')return;
  // 각 등마다 독립적이고 불규칙한 깜빡임
  const flick=(Math.sin(t*8+f.phase)+Math.sin(t*19+f.phase*3)>0.65)||rand()<0.12;
  f.lit=!flick;
  panels.setColorAt(i,f.lit?bright:dark);
 });
 panels.instanceColor.needsUpdate=true;
 // 실시간 광원은 다음 updateNearbyLighting에서 최신 상태를 반영
}
// 캠코더 화면 후처리: 노이즈, 수평 주사선, 흐림, 비네트, 색 편차
const renderTarget=new THREE.WebGLRenderTarget(1,1,{
 minFilter:THREE.LinearFilter,magFilter:THREE.LinearFilter,
 depthBuffer:true
});
const postScene=new THREE.Scene();
const postCamera=new THREE.OrthographicCamera(-1,1,1,-1,0,1);
const postMat=new THREE.ShaderMaterial({
 uniforms:{
  tDiffuse:{value:renderTarget.texture},
  uTime:{value:0},
  uResolution:{value:new THREE.Vector2(1,1)}
 },
 vertexShader:`varying vec2 vUv;void main(){vUv=uv;gl_Position=vec4(position.xy,0.0,1.0);}`,
 fragmentShader:`
  precision mediump float;
  uniform sampler2D tDiffuse;
  uniform float uTime;
  uniform vec2 uResolution;
  varying vec2 vUv;
  float noise(vec2 p){return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453123);}
  void main(){
   vec2 uv=vUv;
   float line=floor(uv.y*uResolution.y/3.0);
   float jitter=(noise(vec2(line,floor(uTime*24.0)))-0.5)*0.0012;
   uv.x+=jitter;
   vec2 px=1.0/uResolution;
   // 작은 가우시안 유사 블러
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
 depthTest:false,depthWrite:false
});
const postQuad=new THREE.Mesh(new THREE.PlaneGeometry(2,2),postMat);
postScene.add(postQuad);
const clock=new THREE.Clock();
let lightTimer=0;
function animate(){
 requestAnimationFrame(animate);
 const dt=Math.min(clock.getDelta(),0.05);
 step(dt);updateLights(clock.elapsedTime);
 lightTimer+=dt;
 if(lightTimer>0.18){updateNearbyLighting();lightTimer=0;}
 if(camcorder){
  renderer.setRenderTarget(renderTarget);
  renderer.render(scene,camera);
  renderer.setRenderTarget(null);
  postMat.uniforms.uTime.value=clock.elapsedTime;
  renderer.render(postScene,postCamera);
 }else{
  renderer.setRenderTarget(null);
  renderer.render(scene,camera);
 }
}
function resize(){
 const w=host.clientWidth,h=host.clientHeight;
 camera.aspect=w/h;camera.updateProjectionMatrix();renderer.setSize(w,h);
 const scale=renderer.getPixelRatio();
 renderTarget.setSize(Math.max(1,Math.floor(w*scale)),Math.max(1,Math.floor(h*scale)));
 postMat.uniforms.uResolution.value.set(w*scale,h*scale);
}
new ResizeObserver(resize).observe(host);resize();updateNearbyLighting();animate();
</script></body></html>
"""

components.html(HTML, height=740, scrolling=False)

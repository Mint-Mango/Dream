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
#caught{display:none;position:absolute;inset:0;background:rgba(0,0,0,.88);align-items:center;justify-content:center;z-index:20;pointer-events:none}#caught img{max-width:72%;max-height:83%;object-fit:contain;border-radius:7px}#caught.active{display:flex}#cross{position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);color:#28251b;font-size:22px;pointer-events:none}
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
<div id="caught"><img src="__CAUGHT_IMAGE__" alt="아노코에게 잡힘"></div>
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

// 49 × 49 구역, 392m × 392m 맵. 모든 구역을 연결한다.
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
const pitWallParts=[], pitBottomParts=[];
// 구멍의 옆면 자체를 깊이에 따라 검게 만드는 셰이더.
// 검은 사각 평면을 위에 얹지 않기 때문에 겹쳐 보이는 현상을 제거한다.
const pitWallMat=new THREE.ShaderMaterial({
 side:THREE.DoubleSide,
 vertexShader:`varying float vWorldY;void main(){vec4 p=modelMatrix*vec4(position,1.0);vWorldY=p.y;gl_Position=projectionMatrix*viewMatrix*p;}`,
 fragmentShader:`precision mediump float;varying float vWorldY;void main(){float d=clamp((-vWorldY+0.15)/3.8,0.0,1.0);vec3 c=mix(vec3(0.105,0.086,0.060),vec3(0.001,0.001,0.001),d);gl_FragColor=vec4(c,1.0);}`
});
const pitBottomMat=new THREE.MeshBasicMaterial({color:0x010101,side:THREE.DoubleSide});
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
 // 입구는 정확하게 4개의 바닥 면으로만 만든다. 중간의 검은 판은 없음.
 boxPart(floorParts,cx-(CELL+size)/4,-0.12,cz,edge,0.24,CELL,2.5);
 boxPart(floorParts,cx+(CELL+size)/4,-0.12,cz,edge,0.24,CELL,2.5);
 boxPart(floorParts,cx,-0.12,cz-(CELL+size)/4,size,0.24,edge,2.5);
 boxPart(floorParts,cx,-0.12,cz+(CELL+size)/4,size,0.24,edge,2.5);
 // 안쪽 수직 벽은 입구 아래에만 있고, 깊어질수록 검어지는 셰이더 사용.
 const depth=17,th=0.12;
 boxPart(pitWallParts,cx-size/2-th/2,-depth/2,cz,th,depth,size+th);
 boxPart(pitWallParts,cx+size/2+th/2,-depth/2,cz,th,depth,size+th);
 boxPart(pitWallParts,cx,-depth/2,cz-size/2-th/2,size,depth,th);
 boxPart(pitWallParts,cx,-depth/2,cz+size/2+th/2,size,depth,th);
 // 바닥은 시야에서 훨씬 아래로 떨어뜨림.
 boxPart(pitBottomParts,cx,-17.1,cz,size-0.03,0.08,size-0.03);
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
fixtures.forEach((f,i)=>{
 f.mode=i<offCount?'off':i<offCount+flickerCount?'flicker':'on';
 f.lit=f.mode!=='off';
 // 각 전등마다 서로 다른 고장 패턴: 긴 정전 / 짧은 순간 소등 / 불규칙 깜빡임
 f.pattern=ri(3); f.nextChange=1+rand()*2.0;
 f.offDuration=0.12+rand()*0.16;
});
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
// 아노코: 제공된 이미지를 3D 공간에서 항상 플레이어 쪽을 향하는 스프라이트로 표시
const anokoTexture=new THREE.TextureLoader().load('__NORMAL_IMAGE__');
const anokoCaughtTexture=new THREE.TextureLoader().load('__CAUGHT_IMAGE__');
anokoTexture.colorSpace=THREE.SRGBColorSpace;
anokoCaughtTexture.colorSpace=THREE.SRGBColorSpace;
const anoko=new THREE.Sprite(new THREE.SpriteMaterial({map:anokoTexture,transparent:true,depthWrite:false}));
anoko.scale.set(1.65,2.35,1);anoko.position.set(30,1.2,30);scene.add(anoko);
const caughtPanel=document.getElementById('caught');
let caughtUntil=0, anokoRoute=[], routeTimer=0, freezeEnemy=false;
const enemySpeed=RUN;
const toCell=(p)=>Math.max(0,Math.min(N-1,Math.round(p/CELL+(N-1)/2)));
function safeEnemyPlace(x,z){return !collision(x,z)&&!overHole(x,z);}
function spawnAnoko(){
 let chosen=null;
 for(let i=0;i<250;i++){
   const x=2+ri(N-4),z=2+ri(N-4),px=center(x),pz=center(z);
   const distance=Math.hypot(px-camera.position.x,pz-camera.position.z);
   if(distance<45||distance>120||!safeEnemyPlace(px,pz))continue;
   chosen=[px,pz];break;
 }
 if(!chosen)chosen=[center(MID+7),center(MID+6)];
 anoko.position.set(chosen[0],1.17,chosen[1]);
 anoko.material.map=anokoTexture;anoko.material.needsUpdate=true;anoko.scale.set(1.65,2.35,1);
 anokoRoute=[];routeTimer=0;freezeEnemy=false;
}
// 맵 셀 연결을 이용한 BFS 경로 탐색. 벽을 뚫고 직선 이동하지 않는다.
function findRoute(sx,sz,tx,tz){
 const start=sz*N+sx,goal=tz*N+tx;
 if(start===goal)return [];
 const prev=new Int32Array(N*N);prev.fill(-1);
 const queue=new Int32Array(N*N);let head=0,tail=0;
 queue[tail++]=start;prev[start]=start;
 const ds=[['n',0,-1],['s',0,1],['e',1,0],['w',-1,0]];
 while(head<tail){
  const id=queue[head++], x=id%N,z=Math.floor(id/N);
  for(const [dir,dx,dz] of ds){
   if(cells[z][x][dir])continue;
   const nx=x+dx,nz=z+dz;
   if(nx<0||nx>=N||nz<0||nz>=N)continue;
   const next=nz*N+nx;
   if(prev[next]!==-1)continue;
   prev[next]=id;
   if(next===goal){head=tail;break;}
   queue[tail++]=next;
  }
 }
 if(prev[goal]===-1)return [];
 const path=[];let p=goal;
 while(p!==start&&path.length<3000){path.push(p);p=prev[p];}
 path.reverse();return path;
}
function catchPlayer(now){
 if(caughtUntil>0)return;
 caughtUntil=now+2.2;
 caughtPanel.classList.add('active');
 anoko.material.map=anokoCaughtTexture;anoko.material.needsUpdate=true;anoko.scale.set(2.5,2.5,1);
 freezeEnemy=true;
}
function updateAnoko(dt,t){
 if(caughtUntil>0){
  if(t>=caughtUntil){caughtUntil=0;caughtPanel.classList.remove('active');reset();spawnAnoko();}
  return;
 }
 routeTimer-=dt;
 const sx=toCell(anoko.position.x),sz=toCell(anoko.position.z);
 const tx=toCell(camera.position.x),tz=toCell(camera.position.z);
 if(routeTimer<=0){anokoRoute=findRoute(sx,sz,tx,tz);routeTimer=0.7;}
 let targetX=camera.position.x,targetZ=camera.position.z;
 if(sx!==tx||sz!==tz){
  if(anokoRoute.length){const id=anokoRoute[0];targetX=center(id%N);targetZ=center(Math.floor(id/N));}
  else{targetX=center(sx);targetZ=center(sz);}
 }
 const vx=targetX-anoko.position.x,vz=targetZ-anoko.position.z;
 const length=Math.hypot(vx,vz);
 if(length>0.05){
   const travel=Math.min(length,enemySpeed*dt);
   const dx=vx/length*travel,dz=vz/length*travel;
   const steps=Math.max(1,Math.ceil(travel/0.18));
   for(let i=0;i<steps;i++){
    const nx=anoko.position.x+dx/steps;
    if(safeEnemyPlace(nx,anoko.position.z))anoko.position.x=nx;
    const nz=anoko.position.z+dz/steps;
    if(safeEnemyPlace(anoko.position.x,nz))anoko.position.z=nz;
   }
 }
 if(Math.hypot(anoko.position.x-camera.position.x,anoko.position.z-camera.position.z)<1.0 && camera.position.y>0.6)catchPlayer(t);
}
spawnAnoko();

// 입력
const keys={};let yaw=0,pitch=0,dragging=false,oldX=0,oldY=0;
let vy=0,grounded=true,camcorder=false;
window.addEventListener('keydown',e=>{
 keys[e.code]=true;
 if(['Space','ArrowUp','ArrowDown','ArrowLeft','ArrowRight'].includes(e.code))e.preventDefault();
 if(e.code==='KeyR'&&!e.repeat){reset();spawnAnoko();caughtUntil=0;caughtPanel.classList.remove('active');}
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
 if(camera.position.y<-7){reset();spawnAnoko();}
}
function updateLights(t){
 let changed=false;
 fixtures.forEach((f,i)=>{
  if(f.mode!=='flicker'||t<f.nextChange)return;
  f.lit=!f.lit;
  if(f.lit){
    // 켜진 후 다음 소등까지 1~2.8초
    f.nextChange=t+1.0+rand()*1.8;
  }else{
    // 0: 1~2초 정전, 1: 0.2초 순간 소등, 2: 0.1~0.6초 변칙 소등
    const duration=f.pattern===0?1+rand():f.pattern===1?0.18+rand()*0.07:0.12+rand()*0.52;
    f.nextChange=t+duration;
  }
  panels.setColorAt(i,f.lit?bright:dark); changed=true;
 });
 if(changed)panels.instanceColor.needsUpdate=true;
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
 if(caughtUntil<=0)step(dt);updateAnoko(dt,clock.elapsedTime);updateLights(clock.elapsedTime);
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

import base64
# 아래의 이미지들은 사용자가 제공한 아노코 그림을 WebP로 압축한 데이터입니다.
# app.py 단독으로 GitHub에 올려도 캐릭터 이미지가 함께 표시됩니다.
ANOKO_NORMAL = "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"
ANOKO_CAUGHT = "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"
HTML = HTML.replace("__NORMAL_IMAGE__", "data:image/webp;base64," + ANOKO_NORMAL)
HTML = HTML.replace("__CAUGHT_IMAGE__", "data:image/webp;base64," + ANOKO_CAUGHT)
components.html(HTML, height=740, scrolling=False)

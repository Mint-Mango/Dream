import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Backrooms Exploration", page_icon="🎮", layout="wide")
st.title("BACKROOMS | Level 0")
st.caption("WASD 이동 · Shift 달리기 · Space 점프 · Q 캠코더 · T 시간정지 · 마우스 드래그 시점 회전 · R 재시작")

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
<div id="hud"><b>BACKROOMS / LEVEL 0</b><br>WASD: 이동 · SHIFT: 달리기<br>SPACE: 점프 · 마우스 드래그: 시점<br>Q: 캠코더 ON/OFF · T: 시간 정지<br>R: 시작 지점으로 복귀</div>
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
// 원본의 흰색 몸통과 배경을 그대로 표시: 투명화/알파컷 적용 금지
const anoko=new THREE.Sprite(new THREE.SpriteMaterial({map:anokoTexture,transparent:false,depthWrite:true,color:0xffffff,fog:false,toneMapped:false}));
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
let timePaused=false, gameTime=0;
let vy=0,grounded=true,camcorder=false;
window.addEventListener('keydown',e=>{
 keys[e.code]=true;
 if(['Space','ArrowUp','ArrowDown','ArrowLeft','ArrowRight'].includes(e.code))e.preventDefault();
 if(e.code==='KeyR'&&!e.repeat){reset();spawnAnoko();caughtUntil=0;caughtPanel.classList.remove('active');}
 if(e.code==='KeyQ'&&!e.repeat)camcorder=!camcorder;
 if(e.code==='KeyT'&&!e.repeat){timePaused=!timePaused;status.textContent=timePaused?'TIME STOPPED | T: RESUME':'TIME RESUMED';}
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
 // T: 게임 내부의 시간만 정지. 렌더링은 유지하여 화면이 멈춰 보인다.
 if(!timePaused){
  gameTime+=dt;
  if(caughtUntil<=0)step(dt);
  updateAnoko(dt,gameTime);
  updateLights(gameTime);
  lightTimer+=dt;
  if(lightTimer>0.18){updateNearbyLighting();lightTimer=0;}
 }else{
  status.textContent='TIME STOPPED | T: RESUME';
 }
 if(camcorder){
  renderer.setRenderTarget(renderTarget);
  renderer.render(scene,camera);
  renderer.setRenderTarget(null);
  postMat.uniforms.uTime.value=gameTime;
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
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"
ANOKO_CAUGHT = "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"
HTML = HTML.replace("__NORMAL_IMAGE__", "data:image/webp;base64," + ANOKO_NORMAL)
HTML = HTML.replace("__CAUGHT_IMAGE__", "data:image/webp;base64," + ANOKO_CAUGHT)
components.html(HTML, height=740, scrolling=False)

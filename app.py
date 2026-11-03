import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Backrooms Exploration", page_icon="🎮", layout="wide")
st.title("BACKROOMS | Level 0")
st.caption("WASD 이동 · Shift 달리기 · Space 점프 · 마우스 드래그 시점 회전 · R 재시작")

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
<div id="hud"><b>BACKROOMS / LEVEL 0</b><br>WASD: 이동 · SHIFT: 달리기<br>SPACE: 점프 · 마우스 드래그: 시점<br>R: 시작 지점으로 복귀</div>
<div id="status">WALK</div>
<script type="module">
import * as THREE from 'three';
import { mergeGeometries } from 'three/addons/utils/BufferGeometryUtils.js';

const N=31, CELL=8, WORLD=N*CELL, HALF=WORLD/2, CEILING=3.4;
const EYE=1.65, RADIUS=0.29, WALK=4.4, RUN=8.8, JUMP=5.5, GRAVITY=17;
const scene=new THREE.Scene();
scene.background=new THREE.Color(0x99916d);
scene.fog=new THREE.Fog(0x99916d,22,95);
const camera=new THREE.PerspectiveCamera(76,1,0.05,125);
camera.position.set(0,EYE,0); camera.rotation.order='YXZ';
const renderer=new THREE.WebGLRenderer({antialias:true});
renderer.setPixelRatio(Math.min(devicePixelRatio,2));
renderer.outputColorSpace=THREE.SRGBColorSpace;
const host=document.getElementById('game');host.appendChild(renderer.domElement);
const status=document.getElementById('status');
scene.add(new THREE.AmbientLight(0xffe7a3,1.55));

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
// 여러 개의 긴 직선 통로와 교차 통로
for(const z of [5,15,25])for(let x=2;x<28;x++)carve(x,z,'e');
for(const x of [7,23])for(let z=2;z<28;z++)carve(x,z,'s');
// 넓은 공간: 여러 셀의 내부 칸막이를 제거
const rooms=[{x:2,z:2,w:4,h:4},{x:11,z:4,w:5,h:4},
 {x:20,z:9,w:5,h:5},{x:3,z:19,w:6,h:5},
 {x:12,z:20,w:6,h:6},{x:24,z:23,w:5,h:5}];
const roomCells=new Set();
for(const room of rooms){
 for(let z=room.z;z<room.z+room.h;z++)for(let x=room.x;x<room.x+room.w;x++){
  roomCells.add(`${x},${z}`);
  if(x<room.x+room.w-1)carve(x,z,'e');
  if(z<room.z+room.h-1)carve(x,z,'s');
 }
}
// 추가 연결로 고리 형태 동선을 생성
for(let z=1;z<N-1;z++)for(let x=1;x<N-1;x++){
 if(rand()<0.13)carve(x,z,rand()<0.5?'e':'s');
}

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
function boundary(x,z,horizontal,closed){
 const T=0.26, GAP=3.8;
 if(closed){horizontal?wall(x,z,CELL,T):wall(x,z,T,CELL);return;}
 const piece=(CELL-GAP)/2, offset=(CELL+GAP)/4;
 if(horizontal){wall(x-offset,z,piece,T);wall(x+offset,z,piece,T);}
 else{wall(x,z-offset,T,piece);wall(x,z+offset,T,piece);}
}
for(let z=0;z<N;z++)for(let x=0;x<N;x++){
 const cx=center(x),cz=center(z),c=cells[z][x];
 boundary(cx+CELL/2,cz,false,c.e);
 boundary(cx,cz+CELL/2,true,c.s);
 if(x===0)boundary(cx-CELL/2,cz,false,true);
 if(z===0)boundary(cx,cz-CELL/2,true,true);
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
  pillar((center(x)+center(x-1))/2,(center(z)+center(z-1))/2,1.45);
 }
}
for(let z=1;z<N-1;z++)for(let x=1;x<N-1;x++){
 if(roomCells.has(`${x},${z}`)||Math.abs(x-15)+Math.abs(z-15)<3)continue;
 if(rand()<0.055)pillar(center(x)+1.4,center(z)+1.4,1.25);
}

// 추락 구덩이: 셀 바닥 일부가 실제로 뚫려 있음
const pits=[];
const pitSet=new Set();
for(let z=2;z<N-2;z++)for(let x=2;x<N-2;x++){
 if(Math.abs(x-15)+Math.abs(z-15)<4)continue;
 if(rand()<0.035){pitSet.add(key(x,z));}
}
// 일부 구덩이는 크게, 일부는 작게 설정
for(let z=0;z<N;z++)for(let x=0;x<N;x++){
 const cx=center(x),cz=center(z),hole=pitSet.has(key(x,z));
 if(!hole){boxPart(floorParts,cx,-0.12,cz,CELL,0.24,CELL,2.5);continue;}
 const size=rand()<0.3?4.0:2.8;
 const edge=(CELL-size)/2;
 // 네 개의 바닥 조각으로 가운데 정사각형을 비움
 boxPart(floorParts,cx-(CELL+size)/4,-0.12,cz,edge,0.24,CELL,2.5);
 boxPart(floorParts,cx+(CELL+size)/4,-0.12,cz,edge,0.24,CELL,2.5);
 boxPart(floorParts,cx,-0.12,cz-(CELL+size)/4,size,0.24,edge,2.5);
 boxPart(floorParts,cx,-0.12,cz+(CELL+size)/4,size,0.24,edge,2.5);
 boxPart(pitParts,cx,-9,cz,size,0.02,size,2);
 pits.push({x:cx,z:cz,half:size/2});
}

combine(floorParts,floorMat);
combine(wallParts,wallMat);
combine(trimParts,trimMat);
combine(pitParts,holeMat);
const roof=new THREE.Mesh(new THREE.PlaneGeometry(WORLD,WORLD),ceilingMat);
roof.rotation.x=Math.PI/2;roof.position.y=CEILING;scene.add(roof);

// 천장 형광등: 고정된 비율로 80% 정상, 10% 소등, 10% 깜빡임
const fixtures=[];
for(let z=0;z<N;z++)for(let x=0;x<N;x++)fixtures.push({x:center(x),z:center(z)});
for(let i=fixtures.length-1;i>0;i--){const j=ri(i+1);[fixtures[i],fixtures[j]]=[fixtures[j],fixtures[i]];}
const total=fixtures.length;
const offCount=Math.floor(total*0.1),flickerCount=Math.floor(total*0.1);
fixtures.forEach((f,i)=>{f.mode=i<offCount?'off':i<offCount+flickerCount?'flicker':'on';f.phase=rand()*6.28;});
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
// PointLight는 성능을 위해 일부에만 배치
const pool=[];
for(let i=0;i<fixtures.length;i+=30){
 const f=fixtures[i];if(f.mode==='off')continue;
 const light=new THREE.PointLight(0xffe4a5,1.1,21,2);
 light.position.set(f.x,CEILING-0.25,f.z);scene.add(light);
 pool.push({light,f});
}

// 입력
const keys={};let yaw=0,pitch=0,dragging=false,oldX=0,oldY=0;
let vy=0,grounded=true;
window.addEventListener('keydown',e=>{
 keys[e.code]=true;
 if(['Space','ArrowUp','ArrowDown','ArrowLeft','ArrowRight'].includes(e.code))e.preventDefault();
 if(e.code==='KeyR'&&!e.repeat)reset();
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
 status.textContent=running?'RUNNING':'WALK';
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
 pool.forEach(({light,f})=>{if(f.mode==='flicker')light.intensity=f.lit?1.1:0;});
}
const clock=new THREE.Clock();
function animate(){
 requestAnimationFrame(animate);
 const dt=Math.min(clock.getDelta(),0.05);
 step(dt);updateLights(clock.elapsedTime);
 renderer.render(scene,camera);
}
function resize(){
 const w=host.clientWidth,h=host.clientHeight;
 camera.aspect=w/h;camera.updateProjectionMatrix();renderer.setSize(w,h);
}
new ResizeObserver(resize).observe(host);resize();animate();
</script></body></html>
"""

components.html(HTML, height=740, scrolling=False)

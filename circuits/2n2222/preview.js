const NS = 'http://www.w3.org/2000/svg';
const parts = Object.entries(layout.parts);
const netColors = {'+5':'#c72b35', GND:'#485964', OUT:'#b74f10', 'L+':'#a55212', 'L-':'#49626f',
  LIN:'#624db0', VOL:'#91610a', FB:'#237c79', PLUS:'#6c54a5', DRV:'#3555a1', BUF:'#946521',
  MID:'#7b5095', ACREF:'#428340', BN:'#13688f', BP:'#176a53', EN:'#814726', EP:'#8e6161'};
let active = '';
let view = 'top';

function svgElement(parent, name, attributes, label) {
  const element = document.createElementNS(NS, name);
  for (const [key, value] of Object.entries(attributes)) element.setAttribute(key, value);
  if (label !== undefined) element.textContent = label;
  parent.append(element);
  return element;
}
function line(parent, start, end, attributes = {}) {
  return svgElement(parent, 'line', {x1:start[0], y1:start[1], x2:end[0], y2:end[1], ...attributes});
}
function circle(parent, point, r, attributes = {}) {
  return svgElement(parent, 'circle', {cx:point[0], cy:point[1], r, ...attributes});
}
function textAt(parent, point, label, attributes = {}) {
  return svgElement(parent, 'text', {x:point[0], y:point[1], fill:'#222d26',
    'text-anchor':'middle', 'font-size':11, ...attributes}, label);
}
function group(parent, key, title) {
  const g = svgElement(parent, 'g', {'data-key':key, tabindex:0, role:'button', 'aria-label':title});
  svgElement(g, 'title', {}, title);
  return g;
}
function chart(parent, width, height, label) {
  const svg = document.createElementNS(NS, 'svg');
  svg.setAttribute('viewBox', '0 0 ' + width + ' ' + height);
  svg.setAttribute('aria-label', label);
  parent.replaceChildren(svg);
  return svg;
}
function fillRow(target, values, key) {
  const row = document.getElementById(target).insertRow();
  if (key) {
    row.dataset.key = key;
    row.tabIndex = 0;
  }
  for (const value of values) row.insertCell().textContent = value;
}
function breadPoint(hole) {
  if (hole.includes(':')) {
    const [rail, position] = hole.split(':');
    return [46 + (Number(position) - 1) * 22, rail === '+5' ? 28 : 302];
  }
  const index = 'abcdefghij'.indexOf(hole[0]);
  return [46 + (Number(hole.slice(1)) - 1) * 22, 64 + index * 21 + (index >= 5 ? 26 : 0)];
}
function isElectrolytic(ref) {
  return /^C[2456]$/.test(ref);
}
function padLabel(ref, index) {
  if (ref[0] === 'D') return index === 1 ? 'K' : 'A';
  if (isElectrolytic(ref)) return index ? '−' : '+';
  if (ref[0] === 'Q') return 'CBE'[index];
  return String(index + 1);
}
function partBody(g, ref, points, board = false) {
  const [first, second] = points;
  const last = points.at(-1);
  const cx = (first[0] + last[0]) / 2;
  const cy = (first[1] + last[1]) / 2;
  const prefix = ref[0];
  const bounds = (width, height, fill, rx = 3) =>
    svgElement(g, 'rect', {x:cx-width/2, y:cy-height/2, width, height, rx, fill, stroke:'#222a26', 'stroke-width':.8});

  if (ref === 'U1') {
    const columns = points.map(point => point[0]), rows = points.map(point => point[1]);
    const left = Math.min(...columns), right = Math.max(...columns);
    const top = Math.min(...rows), bottom = Math.max(...rows);
    const middleX = (left + right) / 2, middleY = (top + bottom) / 2;
    const width = right - left + (board ? -8 : 20), height = bottom - top + (board ? 19 : -8);
    svgElement(g, 'rect', {x:middleX-width/2, y:middleY-height/2, width, height, rx:4, fill:'#333c3b'});
    if (board) circle(g, [middleX,middleY-height/2], 5, {fill:'#b9ceac'});
    else circle(g, [middleX-width/2,middleY], 5, {fill:'#e3e5d8'});
    textAt(g, [middleX,middleY+4], 'U1', {fill:'#fff9ed', 'font-weight':700});
  } else if (prefix === 'J') {
    bounds(last[0]-first[0] + 18, 18, '#33423e', 2);
  } else if (prefix === 'Q') {
    bounds(board ? 45 : 58, board ? 24 : 23, '#37483e', 8);
  } else if (isElectrolytic(ref)) {
    const radius = board ? (ref === 'C6' ? 38 : 23) : (ref === 'C6' ? 19 : 14);
    line(g, first, second, {stroke:'#83877f','stroke-width':2});
    circle(g, [cx,cy], radius, {fill:'#31546a','fill-opacity':.88,stroke:'#223d4b'});
  } else {
    const angle = Math.atan2(second[1]-first[1], second[0]-first[0]) * 180 / Math.PI;
    const horizontal = svgElement(g, 'g', {transform:'translate(' + cx + ' ' + cy + ') rotate(' + angle + ')'});
    line(g, first, second, {stroke:prefix === 'W' ? '#d38822' : '#6b746b', 'stroke-width':prefix === 'W' ? 4 : 2});
    if (prefix !== 'W') {
      const width = prefix === 'R' ? (board ? 44 : 35) : prefix === 'D' ? (board ? 23 : 29) : 28;
      svgElement(horizontal, 'rect', {x:-width/2, y:-6, width, height:12, rx:3,
        fill:prefix === 'R' ? '#ddba73' : prefix === 'D' ? '#d38b5d' : '#819dbc', stroke:'#535a4d'});
      if (prefix === 'D') svgElement(horizontal, 'rect', {x:width/2-7,y:-5.5,width:3,height:11,fill:'#251c1a'});
    }
  }
}

function drawBreadboard() {
  const svg = chart(document.getElementById('bread-drawing'), 1040, 332, 'Breadboard holes, component leads and colored jumpers');
  svg.setAttribute('viewBox', '0 -97 1040 429');
  svgElement(svg, 'rect', {x:12,y:9,width:1015,height:311,rx:13,fill:'#e5e6db',stroke:'#a0aa9c'});
  svgElement(svg, 'rect', {x:22,y:160,width:991,height:19,rx:3,fill:'#c8cec1'});
  for (let column = 1; column <= 44; column++) {
    const x = breadPoint('a'+column)[0];
    textAt(svg,[x,51],column,{'font-size':9,fill:'#47534e'});
    textAt(svg,[x,316],column,{'font-size':9,fill:'#47534e'});
    for (const firstLetter of ['a','f']) {
      const start = breadPoint(firstLetter+column);
      line(svg,start,[x,start[1]+84],{stroke:'#d1d4c8','stroke-width':7});
    }
    for (const letter of 'abcdefghij') {
      const point = breadPoint(letter + column);
      circle(svg,point,3,{fill:'#899387',stroke:'#f5f4ec','stroke-width':1});
      if (column === 1) textAt(svg,[point[0]-22,point[1]+3],letter,{'font-size':9});
    }
  }
  for (const rail of ['+5','GND']) {
    const start = breadPoint(rail+':1'), end = breadPoint(rail+':44');
    const color = netColors[rail];
    line(svg,start,end,{stroke:color,'stroke-width':2,opacity:.6});
    for(let hole=1;hole<=44;hole++) circle(svg,breadPoint(rail+':'+hole),3,{fill:color});
    textAt(svg,[995,start[1]+4],rail,{fill:color,'font-weight':800});
  }
  const wires = svgElement(svg,'g',{id:'bread-wires'});
  layout.wires.forEach(([net, from, to], index) => {
    const key = 'wire-' + (index+1);
    const g = group(wires,key,from+' to '+to+' · '+net);
    const start = breadPoint(from), end = breadPoint(to);
    const color = netColors[net] || '#68766a';
    const bend = Math.min(44,Math.abs(end[0]-start[0])*.1);
    const path = 'M '+start.join(' ')+' Q '+((start[0]+end[0])/2)+' '+((start[1]+end[1])/2-bend)+' '+end.join(' ');
    svgElement(g,'path',{d:path,stroke:color,fill:'none',opacity:.65,'stroke-width':2.4,class:'wire'});
    svgElement(g,'path',{d:path,stroke:'transparent',fill:'none','stroke-width':9});
    for (const point of [start,end]) circle(g,point,3.6,{fill:color,stroke:'#fff','stroke-width':.7});
  });
  for (const [ref,[value, nets, holes]] of parts) {
    const points = holes.split(' ').map(breadPoint);
    const g = group(svg,ref,ref+' · '+value+' · '+holes);
    if (ref === 'RV1') {
      drawBreadPot(g, points, nets.split(' '));
      continue;
    }
    if (ref !== 'J1') partBody(g,ref,points);
    points.forEach((point,i) => {
      if (ref === 'J1') {
        svgElement(g,'rect',{x:point[0]-6,y:point[1]-6,width:12,height:12,rx:2,fill:'#43584d'});
      }
      circle(g,point,3.5,{fill:'#fcf8df',stroke:'#28332c','stroke-width':1});
      if (isElectrolytic(ref) || ref[0] === 'D') drawPolarity(g, point, ref, i);
      if (ref[0] === 'J' || ref[0] === 'Q' || ref === 'U1') {
        const verticalOffset = ref === 'U1' && i < 4 ? -6 : 12;
        const label = ref === 'J1' ? 'J1.' + (i+1) : padLabel(ref,i);
        textAt(g,[point[0],point[1]+verticalOffset],label,{'font-size':8,
          stroke:'#e5e6db','stroke-width':2,'paint-order':'stroke'});
      }
    });
    if (ref !== 'U1' && ref !== 'J1') {
      const first = points[0], last = points.at(-1);
      textAt(g,[(first[0]+last[0])/2,(first[1]+last[1])/2-9],ref,
        {class:'label','font-size':9,'font-weight':800,stroke:'#f9f6e7','stroke-width':2.5,'paint-order':'stroke'});
    }
  }
}

function drawPolarity(g, [x,y], ref, index) {
  const label = padLabel(ref,index);
  const direction = y === breadPoint("j1")[1] ? 1 : -1;
  const badge = [x,y+(direction === 1 ? 12 : -17)];
  const color = label === '+' ? '#a8222c' : '#253c4d';
  line(g,[x,y+4*direction],[x,badge[1]-8*direction],{stroke:color,'stroke-width':1.5});
  svgElement(g,'rect',{x:x-8,y:badge[1]-8,width:16,height:16,rx:4,fill:color,stroke:'#fff','stroke-width':1});
  textAt(g,[x,badge[1]+4],label,{fill:'#fff','font-size':12,'font-weight':900});
}

function drawBreadPot(g, points, nets) {
  const lugs = [[111,-25],[154,-25],[197,-25]];
  potentiometerBody(g, 96, -86, 116, 51);
  textAt(g,[224,-62],'RV1 · audio-taper pot',{'text-anchor':'start','font-weight':800});
  lugs.forEach(([x,y], index) => {
    const target = points[index];
    const color = netColors[nets[index]];
    const d = 'M '+x+' '+y+' C '+x+' 9 '+target[0]+' 11 '+target.join(' ');
    svgElement(g, 'path', {d, fill:'none', stroke:color, 'stroke-width':2.3});
    circle(g, [x,y],4,{fill:color});
    circle(g, target,4,{fill:color,stroke:'#fff'});
    textAt(g,[x,y-8],['CCW','WIPER','CW'][index],
      {'font-size':8,fill:'#fff',stroke:'#3e5148','stroke-width':2,'paint-order':'stroke'});
  });
}

function potentiometerBody(g, x, y, width, height) {
  svgElement(g,'rect',{x,y,width,height,rx:7,fill:'#3e5148',stroke:'#202b26'});
  const center = [x+width/2,y+height/2];
  const radius = Math.min(width,height)*.32;
  circle(g,center,radius,{fill:'#e7d8b7',stroke:'#24342b','stroke-width':1.5});
  line(g,center,[center[0]+radius*.5,center[1]-radius*.66],{stroke:'#24342b','stroke-width':2.5});
}

function drawPCB() {
  const bottom = view === 'bottom';
  const margin = 28, scale = 15;
  const point = ([x,y]) => [margin + (bottom ? layout.width-x : x)*scale, margin + y*scale];
  const svg = chart(document.getElementById('pcb-drawing'), layout.width*scale+margin*2, layout.height*scale+margin*2,
    bottom ? 'Mirrored copper from the solder side' : 'Through-hole component placement from the top');
  svgElement(svg,'rect',{x:margin,y:margin,width:layout.width*scale,height:layout.height*scale,rx:3,
    fill:bottom ? '#e9e4d4' : '#b9ceac',stroke:'#46574b','stroke-width':2});
  for (const [net, path] of layout.routes) {
    svgElement(svg,'polyline',{points:path.map(p=>point(p).join(',')).join(' '),fill:'none',
      stroke:bottom ? '#762e17' : (netColors[net] || '#3c644b'),opacity:bottom ? 1 : .29,
      'stroke-width':5.9,'stroke-linejoin':'round','stroke-linecap':'round'});
  }
  const pcbParts = parts.map(([ref,[value,nets,holes,positions]])=>[ref,value,nets,positions]);
  for (const [ref,nets,positions] of layout.jumpers) pcbParts.push([ref,'Insulated feedback jumper',nets.join(' '),positions]);
  for (const [ref,value,nets,positions] of pcbParts) {
    const pot = ref === 'RV1';
    const points = positions.map((position,i) => pot
      ? point([position[0],positions[0][1]-2.5*i/1.27]) : point(position));
    const g = group(svg,ref,ref+' · '+value+' · '+nets);
    if (pot) {
      const [x,y] = points[0];
      const unit = scale/1.27;
      if (!bottom) potentiometerBody(g,x+unit,y-7.35*unit,12*unit,9.7*unit);
      for (const [dx,dy] of layout.potMounts) {
        const mount = [x+(bottom ? -1 : 1)*dx*unit,y+dy*unit];
        circle(g,mount,1.8*unit,{fill:bottom ? '#762e17' : '#e5c272',stroke:'#60513b'});
        circle(g,mount,1.1*unit,{fill:bottom ? '#fbf6e8' : '#263830'});
      }
    } else if (!bottom) {
      partBody(g,ref,points,true);
    }
    points.forEach(([x,y],i)=>{
      const color = bottom ? '#762e17' : '#e5c272';
      if (i === 0) svgElement(g,'rect',{x:x-9.15,y:y-9.15,width:18.3,height:18.3,fill:color,stroke:'#60513b'});
      else circle(g,[x,y],9.15,{fill:color,stroke:'#60513b'});
      circle(g,[x,y],(ref === 'J1' || pot) ? 5.9 : 4.7,{fill:bottom ? '#fbf6e8' : '#263830'});
      if (pot) textAt(g,[x+(bottom ? 20 : -20),y+4],String(i+1),{'font-size':10,'font-weight':800});
      if (ref === 'J1') textAt(g,[x,y+26],nets.split(' ')[i],{'font-size':11,'font-weight':800});
      if (!bottom && (isElectrolytic(ref) || /^[DQ]/.test(ref) || ref === 'U1')) {
        textAt(g,[x,y+(ref === 'U1' ? 15 : -13)],padLabel(ref,i),
          {'font-size':9,'font-weight':800,stroke:'#f6f4ec','stroke-width':2,'paint-order':'stroke'});
      }
    });
    if (ref !== 'U1' || bottom) {
      const [first,last] = [points[0],points.at(-1)];
      const offset = ref === 'W1' || ref === 'J1' ? -13 : -19;
      const labelX = ref === 'W2' ? first[0]+16 : (first[0]+last[0])/2;
      const labelY = ref === 'W2' ? first[1]+3 : pot ? first[1]+22 : (first[1]+last[1])/2+offset;
      textAt(g,[labelX,labelY],ref,{class:'label','font-weight':800,stroke:'#f4f1e1','stroke-width':2.5,'paint-order':'stroke'});
    }
  }
  document.getElementById('pcb-caption').textContent = bottom
    ? 'Looking directly at the solder side. J1 pin 1 is at the right. The drawn view is for inspection.'
    : 'Looking down from the component side. The faint traces run underneath. Fit W1 for the mono return and W2 as an insulated wire for output feedback. W2 may arch over nearby parts.';
  updateHighlight();
}
function updateHighlight() {
  for (const element of document.querySelectorAll('[data-key]')) {
    element.classList.toggle('selected', !!active && element.dataset.key === active);
  }
}

const bom = new Map();
for (const [ref,[value,nets,holes]] of parts) {
  if (!bom.has(value)) bom.set(value,[]);
  bom.get(value).push(ref);
  const terminals = holes.split(' ').map((hole,index) =>
    isElectrolytic(ref) || ref[0] === 'D' ? hole + ' (' + padLabel(ref,index) + ')' : hole);
  fillRow('placement',[ref,terminals.join(' · '),nets.replaceAll(' ',' · ')],ref);
}
for (const [value,references] of bom) fillRow('bom',[references.join(', '),references.length,value]);
for (const [ref,,positions] of layout.jumpers) {
  fillRow('bom',[ref,1,'Insulated jumper · PCB feedback · '+
    (Math.hypot(positions[1][0]-positions[0][0],positions[1][1]-positions[0][1])*1.27).toFixed(1)+' mm hole spacing']);
}
layout.wires.forEach(([net,from,to],index) => fillRow('jumpers',[index+1,from,to,net],'wire-'+(index+1)));
document.getElementById('board-size').textContent = (layout.width*1.27).toFixed(2)+' × '+(layout.height*1.27).toFixed(2)+' mm';
drawBreadboard();
drawPCB();
document.addEventListener('click',event => {
  const selectedSide=event.target.closest('[data-view]');
  if (selectedSide) {
    view=selectedSide.dataset.view;
    for (const button of document.querySelectorAll('[data-view]')) {
      button.setAttribute('aria-pressed',button === selectedSide);
    }
    drawPCB();
  }
  const item=event.target.closest('[data-key]');
  if (item) {
    active=active === item.dataset.key ? '' : item.dataset.key;
    updateHighlight();
  }
});
document.addEventListener('keydown',event => {
  if (['Enter',' '].includes(event.key) && event.target.closest('[data-key]')) {
    event.preventDefault();
    event.target.dispatchEvent(new MouseEvent('click',{bubbles:true}));
  }
});
document.getElementById('show-wires').addEventListener('change',event => {
  document.getElementById('bread-wires').style.display = event.target.checked ? '' : 'none';
});

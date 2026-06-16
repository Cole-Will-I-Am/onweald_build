const fs = require('fs');
const msgs = fs.readFileSync('/srv/onweald/commons/messages.jsonl','utf8')
  .split('\n').filter(Boolean).map(JSON.parse);

function parseTs(s){ return new Date(s).getTime()/1000; }
function silenceGenome(msgs){
  const times = msgs.filter(m => m.ts).map(m => parseTs(m.ts)).filter(t => !isNaN(t)).sort((a,b)=>a-b);
  const gaps=[];
  for(let i=1;i<times.length;i++) gaps.push(times[i]-times[i-1]);
  if(!gaps.length) return {genes:[0.5], stats:{count:times.length, gaps:0}};
  const cap=2*3600, clipped=gaps.map(g=>Math.min(g,cap));
  const mn=Math.min(...clipped), mx=Math.max(...clipped);
  const genes=mx===mn?clipped.map(()=>0.5):clipped.map(g=>(g-mn)/(mx-mn));
  return {genes, stats:{count:times.length, gaps:gaps.length, mean:gaps.reduce((a,b)=>a+b,0)/gaps.length}};
}
function expandLsystem(seed, genes, maxLen=6000){
  const vowels=new Set('aeiouAEIOU'); let g=genes[0]||0.5;
  let out=[];
  for(const ch of seed){ if(/\s/.test(ch)) out.push('-'); else if(vowels.has(ch)) out.push('F[+F]F[-F]'); else out.push('FF[+F][-F]'); }
  let s=out.join(''); let iters=1;
  while(s.length<maxLen){
    g=genes[iters%genes.length]||0.5; const nxt=[];
    for(const sym of s){
      if(sym==='F'){ if(g<0.33)nxt.push('F[+F]F[-F]'); else if(g<0.66)nxt.push('F[+F][-F]'); else nxt.push('[+F]F[-F]'); }
      else if('+-[]'.includes(sym)) nxt.push(sym);
    }
    const nxtS=nxt.join(''); if(nxtS.length>maxLen) break; s=nxtS; iters++;
  }
  return {s,iters};
}
function lsystemToSvg(lstring, gene, maxSegments=12000){
  let x=0,y=0,angle=-90, stack=[], path=['M0,0'], segments=0, minx=0,maxx=0,miny=0,maxy=0;
  const RAD=Math.PI/180, delta=gene*60+15, step=Math.max(2,gene*6+2);
  for(const sym of lstring){
    if(sym==='F'){
      const nx=x+step*Math.cos(angle*RAD), ny=y+step*Math.sin(angle*RAD);
      path.push('L'+nx.toFixed(2)+','+ny.toFixed(2));
      x=nx; y=ny; minx=Math.min(minx,x); maxx=Math.max(maxx,x); miny=Math.min(miny,y); maxy=Math.max(maxy,y);
      if(++segments >= maxSegments) break;
    } else if(sym==='+') angle+=delta; else if(sym==='-') angle-=delta; else if(sym==='[') stack.push([x,y,angle]); else if(sym===']'&&stack.length){[x,y,angle]=stack.pop(); path.push('M'+x.toFixed(2)+','+y.toFixed(2));}
  }
  return {pathLen:path.length, segments, view:[minx,maxx,miny,maxy]};
}

const genome=silenceGenome(msgs);
const avg=genome.genes.reduce((a,b)=>a+b,0)/genome.genes.length;
const {s,iters}=expandLsystem('silence',genome.genes);
const svg=lsystemToSvg(s,avg);
console.log('stats',genome.stats,'avg gene',avg,'iters',iters,'ls len',s.length,'svg',svg);

"""
DevVerse — Smart Hero Component v3
- Shows full cinematic sci-fi hero UNTIL user clicks "Initialize Dev Pod"
- Once project_initialized = True in session state, morphs into live agent terminal
- Call render_hero() once at top of DevVerse.py
- Call log_activity(agent_key, message) inside each agent step
- Call mark_agent_done(agent_key) when agent finishes
"""

import streamlit as st
import streamlit.components.v1 as components
import time

# ─────────────────────────────────────────────────────────────
# Agent registry
# ─────────────────────────────────────────────────────────────
AGENTS = {
    "ba":     {"icon": "🧠", "label": "Business Analyst", "color": "#a78bfa"},
    "design": {"icon": "🎨", "label": "Architect",         "color": "#67e8f9"},
    "dev":    {"icon": "💻", "label": "Developer",         "color": "#34d399"},
    "test":   {"icon": "🧪", "label": "Tester",            "color": "#fb923c"},
    "report": {"icon": "📑", "label": "Report Agent",      "color": "#f472b6"},
}

def _init():
    for k, v in {
        "dv_log":     [],
        "dv_active":  None,
        "dv_started": False,
    }.items():
        if k not in st.session_state:
            st.session_state[k] = v

def log_activity(agent_key: str, message: str):
    """Push a status message from an agent into the live feed."""
    _init()
    info = AGENTS.get(agent_key, {"icon": "⚙️", "label": agent_key, "color": "#94a3b8"})
    st.session_state.dv_log.append({
        "agent":   agent_key,
        "icon":    info["icon"],
        "label":   info["label"],
        "color":   info["color"],
        "message": message,
        "ts":      time.strftime("%H:%M:%S"),
        "done":    False,
    })
    st.session_state.dv_active  = agent_key
    st.session_state.dv_started = True

def mark_agent_done(agent_key: str):
    """Mark an agent as completed in the live feed."""
    _init()
    info = AGENTS.get(agent_key, {"icon": "⚙️", "label": agent_key, "color": "#94a3b8"})
    st.session_state.dv_log.append({
        "agent":   agent_key,
        "icon":    info["icon"],
        "label":   info["label"],
        "color":   info["color"],
        "message": "COMPLETE",
        "ts":      time.strftime("%H:%M:%S"),
        "done":    True,
    })
    st.session_state.dv_active = None


# ─────────────────────────────────────────────────────────────
# Shared JS — Particles + Radar (used in static hero only)
# ─────────────────────────────────────────────────────────────
_FONTS = "@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700;900&family=Rajdhani:wght@400;500;600&family=Share+Tech+Mono&display=swap');"

_PARTICLE_JS = """
(function(){
  const cv=document.getElementById('cv-p');
  if(!cv)return;
  const cx=cv.getContext('2d');
  const wr=document.getElementById('hero-wrap');
  function rsz(){cv.width=wr.offsetWidth;cv.height=wr.offsetHeight;}
  rsz();window.addEventListener('resize',rsz);
  const C=['#00d4ff','#06ffd6','#7c3aed','#ff2d78','#ffb700','#00ff88'];
  class P{
    reset(i){
      this.x=Math.random()*cv.width;
      this.y=i?Math.random()*cv.height:cv.height+5;
      this.vx=(Math.random()-.5)*.45;this.vy=-(Math.random()*.9+.2);
      this.r=Math.random()*1.8+.4;this.c=C[Math.floor(Math.random()*C.length)];
      this.a=Math.random()*.55+.2;this.life=0;this.max=Math.random()*400+200;
      this.star=Math.random()>.82;this.tw=Math.random()*.06+.01;this.to=Math.random()*6.28;
    }
    constructor(){this.reset(1);}
    tick(){this.x+=this.vx;this.y+=this.vy;this.life++;if(this.y<-10||this.life>this.max)this.reset();}
    draw(){
      const f=this.life<40?this.life/40:this.life>this.max-40?(this.max-this.life)/40:1;
      const tw=.5+.5*Math.sin(this.life*this.tw+this.to);
      cx.save();cx.globalAlpha=this.a*f*tw;
      if(this.star){
        cx.strokeStyle=this.c;cx.lineWidth=.7;cx.shadowColor=this.c;cx.shadowBlur=5;
        cx.beginPath();cx.moveTo(this.x-this.r*2,this.y);cx.lineTo(this.x+this.r*2,this.y);
        cx.moveTo(this.x,this.y-this.r*2);cx.lineTo(this.x,this.y+this.r*2);cx.stroke();
      }else{
        cx.shadowColor=this.c;cx.shadowBlur=this.r*5;cx.fillStyle=this.c;
        cx.beginPath();cx.arc(this.x,this.y,this.r,0,Math.PI*2);cx.fill();
      }
      cx.restore();
    }
  }
  class S{
    reset(i){
      this.x=Math.random()*cv.width;this.y=i?Math.random()*cv.height:-20;
      this.sp=Math.random()*2+1;this.len=Math.random()*60+20;
      this.c=Math.random()>.5?'#00d4ff':'#06ffd6';this.a=Math.random()*.13+.04;this.w=Math.random()*.8+.3;
    }
    constructor(){this.reset(1);}
    tick(){this.y+=this.sp;if(this.y>cv.height+this.len)this.reset();}
    draw(){
      const g=cx.createLinearGradient(this.x,this.y-this.len,this.x,this.y);
      g.addColorStop(0,'transparent');g.addColorStop(1,this.c);
      cx.save();cx.globalAlpha=this.a;cx.strokeStyle=g;cx.lineWidth=this.w;
      cx.beginPath();cx.moveTo(this.x,this.y-this.len);cx.lineTo(this.x,this.y);cx.stroke();cx.restore();
    }
  }
  const ps=Array.from({length:80},()=>new P());
  const ss=Array.from({length:16},()=>new S());
  function conn(){
    for(let i=0;i<ps.length;i++)for(let j=i+1;j<ps.length;j++){
      const dx=ps[i].x-ps[j].x,dy=ps[i].y-ps[j].y,d=Math.sqrt(dx*dx+dy*dy);
      if(d<80){cx.save();cx.globalAlpha=(1-d/80)*.07;cx.strokeStyle='#00d4ff';cx.lineWidth=.35;
        cx.beginPath();cx.moveTo(ps[i].x,ps[i].y);cx.lineTo(ps[j].x,ps[j].y);cx.stroke();cx.restore();}
    }
  }
  function frame(){
    cx.clearRect(0,0,cv.width,cv.height);
    ss.forEach(s=>{s.tick();s.draw();});conn();
    ps.forEach(p=>{p.tick();p.draw();});
    requestAnimationFrame(frame);
  }
  frame();
})();
"""

_RADAR_JS = """
(function(){
  const cv=document.getElementById('cv-r');
  if(!cv)return;
  const cx=cv.getContext('2d');
  const wr=document.getElementById('hero-wrap');
  function rsz(){cv.width=wr.offsetWidth;cv.height=wr.offsetHeight;}
  rsz();window.addEventListener('resize',rsz);
  let ang=0;const R=185;
  const bl=Array.from({length:6},()=>({
    a:Math.random()*6.28,r:Math.random()*R*.8+R*.12,lit:0,
    c:['#00d4ff','#06ffd6','#00ff88'][Math.floor(Math.random()*3)]
  }));
  function frame(){
    const W=cv.width,H=cv.height,X=W/2,Y=H/2;
    cx.clearRect(0,0,W,H);
    [.3,.6,1].forEach(f=>{
      cx.save();cx.globalAlpha=.05;cx.strokeStyle='#00d4ff';cx.lineWidth=.8;
      cx.beginPath();cx.arc(X,Y,R*f,0,Math.PI*2);cx.stroke();cx.restore();
    });
    for(let i=0;i<12;i++){
      const a=i/12*6.28;
      cx.save();cx.globalAlpha=.09;cx.strokeStyle='#00d4ff';cx.lineWidth=.6;
      cx.beginPath();cx.moveTo(X+Math.cos(a)*(R-7),Y+Math.sin(a)*(R-7));
      cx.lineTo(X+Math.cos(a)*R,Y+Math.sin(a)*R);cx.stroke();cx.restore();
    }
    cx.save();cx.beginPath();cx.moveTo(X,Y);cx.arc(X,Y,R,ang-1.1,ang,false);cx.closePath();
    const sg=cx.createRadialGradient(X,Y,0,X,Y,R);
    sg.addColorStop(0,'rgba(0,212,255,0)');sg.addColorStop(.7,'rgba(0,212,255,.03)');
    sg.addColorStop(1,'rgba(0,212,255,.09)');cx.fillStyle=sg;cx.fill();cx.restore();
    cx.save();cx.strokeStyle='#00d4ff';cx.lineWidth=1.2;cx.globalAlpha=.42;
    cx.shadowColor='#00d4ff';cx.shadowBlur=6;cx.beginPath();cx.moveTo(X,Y);
    cx.lineTo(X+Math.cos(ang)*R,Y+Math.sin(ang)*R);cx.stroke();cx.restore();
    bl.forEach(b=>{
      let d=ang-b.a;while(d<0)d+=6.28;
      if(d<.14)b.lit=1;
      if(b.lit>0){
        const bx=X+Math.cos(b.a)*b.r,by=Y+Math.sin(b.a)*b.r;
        cx.save();cx.globalAlpha=b.lit*.85;cx.fillStyle=b.c;cx.shadowColor=b.c;cx.shadowBlur=10;
        cx.beginPath();cx.arc(bx,by,3,0,6.28);cx.fill();cx.restore();b.lit=Math.max(0,b.lit-.007);
      }
    });
    ang+=.013;requestAnimationFrame(frame);
  }
  frame();
})();
"""

# ─────────────────────────────────────────────────────────────
# Static Hero HTML  (shown BEFORE pipeline starts)
# ─────────────────────────────────────────────────────────────
STATIC_HTML = """<!DOCTYPE html><html><head><style>
{FONTS}
*{{margin:0;padding:0;box-sizing:border-box;}} body{{background:transparent;overflow:hidden;}}
#hero-wrap{{
  position:relative;width:100%;height:500px;
  display:flex;flex-direction:column;align-items:center;justify-content:center;
  overflow:hidden;
}}
#cv-p{{position:absolute;inset:0;z-index:1;}}
#cv-r{{position:absolute;inset:0;z-index:2;pointer-events:none;}}

/* Rings */
.ring{{position:absolute;border-radius:50%;border:1px solid;pointer-events:none;z-index:3;top:50%;left:50%;}}
.r1{{width:420px;height:420px;border-color:rgba(0,212,255,.07);transform:translate(-50%,-50%);animation:rot 18s linear infinite;}}
.r2{{width:310px;height:310px;border-color:rgba(124,58,237,.09);transform:translate(-50%,-50%);animation:rot 12s linear infinite reverse;}}
.r3{{width:470px;height:470px;border:1px dashed rgba(0,212,255,.09);transform:translate(-50%,-50%);animation:rot 28s linear infinite reverse;}}
@keyframes rot{{from{{transform:translate(-50%,-50%) rotate(0)}}to{{transform:translate(-50%,-50%) rotate(360deg)}}}}

/* Beam cross */
.vb{{position:absolute;top:0;left:50%;transform:translateX(-50%);width:1px;height:100%;background:linear-gradient(180deg,transparent,rgba(0,212,255,.12) 40%,rgba(6,255,214,.16) 50%,rgba(0,212,255,.12) 60%,transparent);z-index:4;animation:bb 4s ease-in-out infinite;}}
.hb{{position:absolute;top:50%;left:0;transform:translateY(-50%);width:100%;height:1px;background:linear-gradient(90deg,transparent,rgba(0,212,255,.09) 30%,rgba(0,212,255,.14) 50%,rgba(0,212,255,.09) 70%,transparent);z-index:4;animation:bb 4s ease-in-out 2s infinite;}}
@keyframes bb{{0%,100%{{opacity:.5}}50%{{opacity:1}}}}

/* Energy pulses */
.ep{{position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);width:10px;height:10px;border-radius:50%;z-index:5;}}
.ep1{{background:rgba(0,212,255,.7);animation:eb1 3.5s ease-out infinite;}}
.ep2{{background:rgba(124,58,237,.7);animation:eb2 3.5s ease-out 1.75s infinite;}}
@keyframes eb1{{0%{{width:10px;height:10px;opacity:.8;box-shadow:0 0 20px #00d4ff}}70%{{width:460px;height:460px;opacity:0}}100%{{width:10px;height:10px;opacity:0}}}}
@keyframes eb2{{0%{{width:10px;height:10px;opacity:.6;box-shadow:0 0 20px #7c3aed}}70%{{width:380px;height:380px;opacity:0}}100%{{width:10px;height:10px;opacity:0}}}}

/* Corners */
.co{{position:absolute;width:20px;height:20px;z-index:10;opacity:0;animation:ca .5s ease forwards;}}
.c1{{top:16px;left:16px;border-top:2px solid #00d4ff;border-left:2px solid #00d4ff;animation-delay:.7s}}
.c2{{top:16px;right:16px;border-top:2px solid #00d4ff;border-right:2px solid #00d4ff;animation-delay:.9s}}
.c3{{bottom:16px;left:16px;border-bottom:2px solid #00d4ff;border-left:2px solid #00d4ff;animation-delay:1s}}
.c4{{bottom:16px;right:16px;border-bottom:2px solid #00d4ff;border-right:2px solid #00d4ff;animation-delay:1.1s}}
@keyframes ca{{from{{opacity:0;transform:scale(.5)}}to{{opacity:1;transform:scale(1)}}}}

/* HUD labels */
.hl{{position:absolute;font-family:'Share Tech Mono',monospace;font-size:.57rem;letter-spacing:.12em;color:rgba(0,212,255,.3);z-index:10;animation:hb2 5s ease-in-out infinite;}}
.hl1{{top:24px;left:48px}}.hl2{{top:24px;right:48px;text-align:right}}
.hl3{{bottom:24px;left:48px}}.hl4{{bottom:24px;right:48px;text-align:right}}
@keyframes hb2{{0%,88%,100%{{opacity:1}}90%{{opacity:.15}}93%{{opacity:1}}96%{{opacity:.35}}}}

/* Hero content */
.hc{{position:relative;z-index:20;display:flex;flex-direction:column;align-items:center;text-align:center;}}
.badge{{
  display:inline-flex;align-items:center;gap:8px;
  padding:5px 18px;background:rgba(0,212,255,.06);
  border:1px solid rgba(0,212,255,.22);border-radius:100px;
  font-family:'Share Tech Mono',monospace;font-size:.62rem;letter-spacing:.2em;
  color:#00d4ff;text-transform:uppercase;margin-bottom:1.4rem;
  box-shadow:0 0 24px rgba(0,212,255,.1),inset 0 1px 0 rgba(255,255,255,.05);
  opacity:0;animation:ri .8s cubic-bezier(.34,1.56,.64,1) .3s forwards;
}}
.bd{{width:6px;height:6px;border-radius:50%;background:#06ffd6;box-shadow:0 0 10px #06ffd6;animation:dp 1.5s ease-in-out infinite;}}
@keyframes dp{{0%,100%{{transform:scale(1);opacity:1}}50%{{transform:scale(.5);opacity:.3}}}}

.title{{
  font-family:'Orbitron',sans-serif;font-size:clamp(1.7rem,4vw,2.8rem);
  font-weight:900;text-transform:uppercase;letter-spacing:.06em;
  line-height:1.2;color:#e8f4ff;margin-bottom:1.1rem;
  opacity:0;animation:fg 1s cubic-bezier(.22,1,.36,1) .5s forwards;position:relative;
}}
@keyframes fg{{from{{opacity:0;transform:translateY(22px) skewX(-2deg);filter:blur(10px)}}to{{opacity:1;transform:translateY(0);filter:blur(0);text-shadow:0 0 50px rgba(0,212,255,.18)}}}}

.tg{{
  background:linear-gradient(135deg,#00d4ff 0%,#06ffd6 30%,#7c3aed 65%,#ff2d78 100%);
  background-size:300% 300%;-webkit-background-clip:text;-webkit-text-fill-color:transparent;
  background-clip:text;animation:pl 5s ease infinite;filter:drop-shadow(0 0 18px rgba(0,212,255,.28));
}}
@keyframes pl{{0%{{background-position:0% 50%}}50%{{background-position:100% 50%}}100%{{background-position:0% 50%}}}}

/* Glitch layers on title */
.title::before,.title::after{{
  content:attr(data-text);position:absolute;top:0;left:0;width:100%;
  font-family:'Orbitron',sans-serif;font-size:inherit;font-weight:900;
  text-transform:uppercase;letter-spacing:.06em;pointer-events:none;
}}
.title::before{{-webkit-text-fill-color:#ff2d78;color:#ff2d78;animation:gl 6s steps(1) infinite;opacity:.7;clip-path:polygon(0 20%,100% 20%,100% 38%,0 38%);}}
.title::after{{-webkit-text-fill-color:#00d4ff;color:#00d4ff;animation:gr 6s steps(1) infinite .2s;opacity:.7;clip-path:polygon(0 60%,100% 60%,100% 78%,0 78%);}}
@keyframes gl{{0%,87%,100%{{transform:none;opacity:0}}89%{{transform:translateX(-3px) skewX(-5deg);opacity:.7}}91%{{transform:translateX(2px);opacity:.3}}93%{{opacity:0}}}}
@keyframes gr{{0%,87%,100%{{transform:none;opacity:0}}89%{{transform:translateX(3px) skewX(5deg);opacity:.7}}91%{{transform:translateX(-2px);opacity:.3}}93%{{opacity:0}}}}

.sub{{
  font-family:'Rajdhani',sans-serif;font-size:.98rem;
  color:rgba(139,163,199,.82);max-width:500px;line-height:1.75;letter-spacing:.03em;
  opacity:0;animation:ri .8s cubic-bezier(.34,1.56,.64,1) .85s forwards;
}}
.cur{{color:#00d4ff;animation:cu 1s step-end infinite;}}
@keyframes cu{{0%,100%{{opacity:1}}50%{{opacity:0}}}}
@keyframes ri{{from{{opacity:0;transform:translateY(-14px) scale(.9)}}to{{opacity:1;transform:translateY(0) scale(1)}}}}
</style></head><body>
<div id="hero-wrap">
  <canvas id="cv-p"></canvas><canvas id="cv-r"></canvas>
  <div class="ring r1"></div><div class="ring r2"></div><div class="ring r3"></div>
  <div class="vb"></div><div class="hb"></div>
  <div class="ep ep1"></div><div class="ep ep2"></div>
  <div class="co c1"></div><div class="co c2"></div><div class="co c3"></div><div class="co c4"></div>
  <div class="hl hl1">SYS_VER: 4.2.1 // READY</div>
  <div class="hl hl2">UPTIME: <span id="ut">00:00:00</span></div>
  <div class="hl hl3">AGENTS: 5 // STANDBY</div>
  <div class="hl hl4">NEURAL-CORE: ACTIVE</div>
  <div class="hc">
    <div class="badge"><div class="bd"></div>✦ AI-Powered Development</div>
    <div class="title" data-text="YOUR VIRTUAL DEV POD  SHIPS CODE AUTONOMOUSLY">
      YOUR <span class="tg">VIRTUAL DEV POD</span><br>SHIPS CODE AUTONOMOUSLY
    </div>
    <div class="sub">
      Upload your RFP and watch as AI agents — Business Analyst, Designer,
      Developer &amp; Tester — collaborate to deliver production-ready software.
      <span class="cur">_</span>
    </div>
  </div>
</div>
<script>
const s=Date.now();
setInterval(()=>{{
  const d=Math.floor((Date.now()-s)/1000);
  const el=document.getElementById('ut');
  if(el)el.textContent=String(Math.floor(d/3600)).padStart(2,'0')+':'+String(Math.floor((d%3600)/60)).padStart(2,'0')+':'+String(d%60).padStart(2,'0');
}},1000);
{PARTICLE_JS}
{RADAR_JS}
</script></body></html>"""


# ─────────────────────────────────────────────────────────────
# Live Activity Feed HTML  (shown AFTER pipeline starts)
# ─────────────────────────────────────────────────────────────
def _build_live_html(log, active):
    """Build terminal activity feed from log entries."""

    rows = ""
    seen_agents_done = set()
    prev_agent = None

    for entry in log:
        ak = entry["agent"]
        is_done = entry["done"]

        # Print agent section header when agent changes
        if ak != prev_agent:
            done_badge = "<span class='done-badge'>✓ DONE</span>" if (is_done or ak in seen_agents_done) else ""
            rows += f"""
            <div class="agent-hdr" style="--ac:{entry['color']}">
              <span class="ai">{entry['icon']}</span>
              <span class="al">{entry['label']}</span>
              {done_badge}
            </div>"""

        if is_done:
            seen_agents_done.add(ak)
        else:
            rows += f"""
            <div class="lr">
              <span class="ts">{entry['ts']}</span>
              <span class="msg">{entry['message']}</span>
            </div>"""

        prev_agent = ak

    # Blinking "processing" line for currently active agent
    if active and active not in seen_agents_done:
        info = AGENTS.get(active, {})
        rows += f"""
        <div class="typing">
          <span class="tc">▋</span>
          <span class="tl" style="color:{info.get('color','#94a3b8')}">
            {info.get('icon','')} {info.get('label','')} processing...
          </span>
        </div>"""

    pct   = min(int(len(seen_agents_done) / 5 * 100), 100)
    count = len(log)

    return f"""<!DOCTYPE html><html><head><style>
{_FONTS}
*{{margin:0;padding:0;box-sizing:border-box;}} body{{background:transparent;overflow:hidden;}}

#wrap{{
  position:relative;width:100%;
  background:rgba(4,6,15,.97);
  border:1px solid rgba(0,212,255,.14);
  border-radius:14px;overflow:hidden;
  font-family:'Share Tech Mono',monospace;
  box-shadow:0 0 40px rgba(0,0,0,.7),0 0 20px rgba(0,212,255,.04);
  animation:wi .5s cubic-bezier(.22,1,.36,1) forwards;
}}
@keyframes wi{{from{{opacity:0;transform:translateY(12px)}}to{{opacity:1;transform:translateY(0)}}}}

/* Travelling scan line */
.scan{{
  position:absolute;top:0;left:-60%;width:60%;height:2px;
  background:linear-gradient(90deg,transparent,rgba(0,212,255,.45),transparent);
  animation:sc 2.8s linear infinite;z-index:20;
}}
@keyframes sc{{from{{left:-60%}}to{{left:160%}}}}

/* Corner brackets */
.co{{position:absolute;width:14px;height:14px;z-index:10;opacity:.5;}}
.c1{{top:6px;left:6px;border-top:1px solid #00d4ff;border-left:1px solid #00d4ff;}}
.c2{{top:6px;right:6px;border-top:1px solid #00d4ff;border-right:1px solid #00d4ff;}}
.c3{{bottom:6px;left:6px;border-bottom:1px solid #00d4ff;border-left:1px solid #00d4ff;}}
.c4{{bottom:6px;right:6px;border-bottom:1px solid #00d4ff;border-right:1px solid #00d4ff;}}

/* Top bar */
.topbar{{
  display:flex;align-items:center;justify-content:space-between;
  padding:9px 16px;background:rgba(0,212,255,.04);
  border-bottom:1px solid rgba(0,212,255,.09);
}}
.tbl{{display:flex;align-items:center;gap:7px;font-size:.58rem;letter-spacing:.18em;color:rgba(0,212,255,.55);text-transform:uppercase;}}
.dot{{width:7px;height:7px;border-radius:50%;background:#00ff88;box-shadow:0 0 8px #00ff88;animation:dp 1.4s ease-in-out infinite;}}
@keyframes dp{{0%,100%{{opacity:1;transform:scale(1)}}50%{{opacity:.3;transform:scale(.5)}}}}
.tbr{{font-size:.56rem;letter-spacing:.12em;color:rgba(0,212,255,.28);}}

/* Log scroll area */
.log{{
  padding:12px 18px 14px;
  max-height:360px;overflow-y:auto;
  display:flex;flex-direction:column;gap:0px;
}}
.log::-webkit-scrollbar{{width:2px;}}
.log::-webkit-scrollbar-thumb{{background:rgba(0,212,255,.22);border-radius:1px;}}

/* Agent section header */
.agent-hdr{{
  display:flex;align-items:center;gap:8px;
  font-family:'Rajdhani',sans-serif;
  font-size:.88rem;font-weight:600;letter-spacing:.1em;text-transform:uppercase;
  color:var(--ac, #00d4ff);
  margin-top:12px;margin-bottom:4px;
  padding-bottom:5px;
  border-bottom:1px solid rgba(255,255,255,.05);
  animation:ri .35s ease forwards;opacity:0;
}}
.agent-hdr:first-child{{margin-top:2px;}}
.ai{{font-size:.95rem;flex-shrink:0;}}
.al{{flex:1;}}
.done-badge{{
  font-size:.52rem;letter-spacing:.16em;
  padding:2px 8px;border-radius:100px;
  background:rgba(0,255,136,.07);border:1px solid rgba(0,255,136,.25);
  color:#00ff88;
}}

/* Log rows */
.lr{{
  display:flex;align-items:baseline;gap:10px;
  padding:3px 0 3px 26px;
  animation:ri .3s ease forwards;opacity:0;
}}
@keyframes ri{{from{{opacity:0;transform:translateX(-6px)}}to{{opacity:1;transform:translateX(0)}}}}

.ts{{font-size:.56rem;color:rgba(0,212,255,.28);letter-spacing:.06em;flex-shrink:0;min-width:56px;}}
.msg{{font-size:.72rem;color:rgba(175,215,255,.72);letter-spacing:.04em;line-height:1.6;}}

/* Typing indicator */
.typing{{
  display:flex;align-items:center;gap:8px;
  padding:7px 0 5px 26px;margin-top:4px;
}}
.tc{{color:#00d4ff;animation:tc .7s step-end infinite;font-size:.9rem;}}
@keyframes tc{{0%,100%{{opacity:1}}50%{{opacity:0}}}}
.tl{{font-family:'Rajdhani',sans-serif;font-size:.75rem;letter-spacing:.06em;opacity:.75;}}

/* Bottom bar */
.botbar{{
  display:flex;align-items:center;justify-content:space-between;
  padding:7px 16px;background:rgba(0,0,0,.3);
  border-top:1px solid rgba(0,212,255,.07);
  font-size:.53rem;letter-spacing:.14em;color:rgba(0,212,255,.22);text-transform:uppercase;
}}
.pt{{width:110px;height:3px;border-radius:2px;background:rgba(255,255,255,.06);overflow:hidden;}}
.pf{{
  height:100%;border-radius:2px;
  background:linear-gradient(90deg,#00d4ff,#06ffd6);
  box-shadow:0 0 8px rgba(0,212,255,.45);
  transition:width .6s ease;
}}
</style></head><body>
<div id="wrap">
  <div class="scan"></div>
  <div class="co c1"></div><div class="co c2"></div>
  <div class="co c3"></div><div class="co c4"></div>
  <div class="topbar">
    <div class="tbl"><div class="dot"></div>NEURAL FORGE // PIPELINE ACTIVE</div>
    <div class="tbr" id="clk">--:--:--</div>
  </div>
  <div class="log" id="log">
    {rows}
  </div>
  <div class="botbar">
    <span>DEVVERSE OS</span>
    <div class="pt"><div class="pf" style="width:{pct}%"></div></div>
    <span>{count} EVENTS</span>
  </div>
</div>
<script>
  const la=document.getElementById('log');
  if(la) la.scrollTop=la.scrollHeight;
  setInterval(()=>{{
    const el=document.getElementById('clk');
    if(el) el.textContent=new Date().toLocaleTimeString('en-GB');
  }},1000);
</script>
</body></html>"""


# ─────────────────────────────────────────────────────────────
# Public render function
# ─────────────────────────────────────────────────────────────
def render_hero():
    """
    Call this ONCE near the top of DevVerse.py (after session state init).

    Logic:
      • project_initialized == False  →  show full cinematic sci-fi hero
      • project_initialized == True   →  show live agent activity terminal
    """
    _init()

    # KEY GATE: only switch to live feed after "Initialize Dev Pod" is clicked
    pipeline_active = st.session_state.get("project_initialized", False)

    if not pipeline_active:
        # ── Full cinematic hero with particles + radar ─────────
        html = STATIC_HTML.format(
            FONTS=_FONTS,
            PARTICLE_JS=_PARTICLE_JS,
            RADAR_JS=_RADAR_JS,
        )
        components.html(html, height=510, scrolling=False)

    else:
        # ── Live agent terminal ────────────────────────────────
        log    = st.session_state.get("dv_log", [])
        active = st.session_state.get("dv_active", None)
        html   = _build_live_html(log, active)
        # Height scales with number of log entries, min 220, max 520
        h = max(220, min(170 + len(log) * 30, 520))
        components.html(html, height=h, scrolling=False)
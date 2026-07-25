from __future__ import annotations

import hmac
import json
import secrets
import time
from hashlib import sha256
from pathlib import Path
from typing import Any

from aiohttp import web

from app.config import Settings


SESSION_COOKIE = "nazorat_admin"
SESSION_TTL_SECONDS = 12 * 60 * 60

PERMISSION_NAMES = {
    "1": "Обязателно",
    "2": "Не обязательно",
    "3": "Запрещен",
}

DUES_NAMES = {
    "0": "-не выбрано-",
    "1": "Сбор обязательно",
    "2": "Сбор не обязательно",
    "3": "Сбор зависит от вида разрешения",
}


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    tmp_path.replace(path)


def _code(value: object) -> str:
    text = str(value or "").strip()
    if not text.isdigit():
        raise web.HTTPBadRequest(text="Davlat kodi faqat raqam bo'lishi kerak.")
    return text.zfill(3)


def _vid(value: object) -> str:
    text = str(value or "").strip()
    if text not in {str(i) for i in range(1, 9)}:
        raise web.HTTPBadRequest(text="Tashuv turi 1-8 oralig'ida bo'lishi kerak.")
    return text


def _signed_token(settings: Settings) -> str:
    issued_at = str(int(time.time()))
    nonce = secrets.token_urlsafe(12)
    payload = f"{settings.admin_username}:{issued_at}:{nonce}"
    signature = hmac.new(settings.admin_session_secret.encode(), payload.encode(), sha256).hexdigest()
    return f"{payload}:{signature}"


def _is_authenticated(request: web.Request, settings: Settings) -> bool:
    token = request.cookies.get(SESSION_COOKIE, "")
    parts = token.split(":")
    if len(parts) != 4:
        return False
    username, issued_at, nonce, signature = parts
    if username != settings.admin_username:
        return False
    try:
        age = time.time() - int(issued_at)
    except ValueError:
        return False
    if age < 0 or age > SESSION_TTL_SECONDS:
        return False
    payload = f"{username}:{issued_at}:{nonce}"
    expected = hmac.new(settings.admin_session_secret.encode(), payload.encode(), sha256).hexdigest()
    return hmac.compare_digest(signature, expected)


def _require_admin(request: web.Request, settings: Settings) -> None:
    if not _is_authenticated(request, settings):
        raise web.HTTPUnauthorized(text="Admin login talab qilinadi.")


def _json_error(message: str, status: int = 400) -> web.Response:
    return web.json_response({"ok": False, "error": message}, status=status)


def _rule_payload(data: dict[str, Any], rules_data: dict[str, Any]) -> dict[str, str]:
    vid_cd = _vid(data.get("vid_cd"))
    permission_cd = str(data.get("permission_cd") or "2").strip()
    dues_cd = str(data.get("dues_cd") or "2").strip()
    if permission_cd not in PERMISSION_NAMES:
        raise web.HTTPBadRequest(text="Ruxsatnoma qiymati noto'g'ri.")
    if dues_cd not in DUES_NAMES:
        raise web.HTTPBadRequest(text="Yig'im qiymati noto'g'ri.")
    return {
        "vid_cd": vid_cd,
        "vid_name_ru": rules_data.get("vid_types", {}).get(vid_cd, ""),
        "permission_cd": permission_cd,
        "permission_name_ru": PERMISSION_NAMES[permission_cd],
        "exception_cd": str(data.get("exception_cd") or "0").strip(),
        "exception_name_ru": str(data.get("exception_name_ru") or "-не выбрано-").strip(),
        "dues_cd": dues_cd,
        "dues_name_ru": DUES_NAMES[dues_cd],
        "source": "web-admin-panel",
        "admin_note": str(data.get("admin_note") or "").strip(),
    }


def _login_page() -> str:
    return """<!doctype html>
<html lang="uz">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>NazoratBot Admin Login</title>
  <style>
    :root{--ink:#112033;--muted:#64748b;--line:rgba(15,23,42,.12);--blue:#0e63b6;--green:#0f8d69;--glass:rgba(255,255,255,.70)}
    *{box-sizing:border-box} body{margin:0;min-height:100vh;font-family:Inter,Segoe UI,Arial,sans-serif;color:var(--ink);background:linear-gradient(135deg,#edf8ff,#ffffff 54%,#f0fff8);overflow:hidden}
    body:before,body:after{content:"";position:fixed;border-radius:50%;filter:blur(10px);pointer-events:none}
    body:before{width:460px;height:460px;left:-140px;top:-120px;background:radial-gradient(circle,rgba(14,99,182,.24),transparent 68%)}
    body:after{width:420px;height:420px;right:-120px;bottom:-140px;background:radial-gradient(circle,rgba(15,141,105,.20),transparent 68%)}
    .shell{position:relative;min-height:100vh;display:grid;grid-template-columns:1.1fr .9fr;align-items:center;gap:36px;padding:46px;max-width:1180px;margin:auto}
    .hero{padding:36px}.badge{display:inline-flex;align-items:center;gap:10px;padding:10px 14px;border-radius:999px;background:rgba(255,255,255,.76);border:1px solid var(--line);box-shadow:inset 0 1px 0 rgba(255,255,255,.9);font-weight:900;color:var(--green);backdrop-filter:blur(16px)}
    h1{font-size:54px;line-height:1.02;margin:22px 0 14px;letter-spacing:0}.lead{font-size:18px;color:var(--muted);line-height:1.6;max-width:560px;margin:0}.chips{display:flex;flex-wrap:wrap;gap:10px;margin-top:24px}.chip{padding:10px 13px;border-radius:16px;background:rgba(255,255,255,.72);border:1px solid var(--line);box-shadow:8px 10px 22px rgba(15,23,42,.06)}
    .card{padding:30px;border:1px solid var(--line);border-radius:30px;background:var(--glass);box-shadow:0 34px 90px rgba(14,99,182,.16),inset 0 1px 0 rgba(255,255,255,.95);backdrop-filter:blur(22px)}
    .logo{width:70px;height:70px;border-radius:24px;display:grid;place-items:center;font-size:34px;background:linear-gradient(145deg,#fff,#dff1ff);box-shadow:12px 16px 28px rgba(14,99,182,.15),inset -6px -6px 14px rgba(14,99,182,.09);margin-bottom:16px}
    h2{font-size:28px;margin:0 0 8px}.sub{color:var(--muted);margin:0 0 20px}.field{display:grid;gap:8px;margin:15px 0}label{font-size:13px;font-weight:900;color:#334155}
    input{border:1px solid var(--line);border-radius:18px;padding:14px 15px;font-size:15px;background:rgba(255,255,255,.86);outline:none;box-shadow:inset 4px 5px 10px rgba(15,23,42,.035)}
    button{width:100%;border:0;border-radius:18px;padding:15px 16px;font-weight:950;background:linear-gradient(135deg,var(--blue),var(--green));color:white;box-shadow:0 14px 32px rgba(14,99,182,.24);cursor:pointer;margin-top:8px}
    .hint{font-size:12px;color:var(--muted);line-height:1.5;margin-top:14px;padding:12px;border-radius:16px;background:rgba(255,255,255,.58);border:1px solid var(--line)}
    @media(max-width:900px){body{overflow:auto}.shell{grid-template-columns:1fr;padding:24px}.hero{padding:0}h1{font-size:38px}}
  </style>
</head>
<body><main class="shell">
  <section class="hero">
    <div class="badge">● Browser admin dashboard</div>
    <h1>NazoratBot qoidalar markazi</h1>
    <p class="lead">Dazvol bitimlari, davlatlar, kirish-tranzit yig'imlari, BHM va huquqiy asoslarni Render orqali web paneldan boshqaring.</p>
    <div class="chips"><span class="chip">📄 Dazvol</span><span class="chip">💰 Chegaradagi yig'imlar</span><span class="chip">🌍 Davlatlar</span><span class="chip">⚖️ Huquqiy asoslar</span></div>
  </section>
  <form class="card" method="post" action="/admin/login">
    <div class="logo">🛃</div>
    <h2>Admin login</h2>
    <p class="sub">Dashboardga kirish uchun login va parolni kiriting.</p>
    <div class="field"><label>Login</label><input name="username" autocomplete="username" required /></div>
    <div class="field"><label>Parol</label><input name="password" type="password" autocomplete="current-password" required /></div>
    <button type="submit">Dashboardga kirish</button>
    <p class="hint">Xavfsizlik uchun Render Environment Variables ichida <b>ADMIN_USERNAME</b>, <b>ADMIN_PASSWORD</b> va <b>ADMIN_SESSION_SECRET</b> qiymatlarini o'zgartiring.</p>
  </form>
</main></body></html>"""


def _admin_page() -> str:
    return """<!doctype html>
<html lang="uz">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>NazoratBot Admin Dashboard</title>
  <style>
    :root{--ink:#122033;--muted:#64748b;--line:rgba(15,23,42,.11);--blue:#1261a6;--green:#138a63;--amber:#b7791f;--red:#c24135;--glass:rgba(255,255,255,.72);--soft:#f6fbff}
    *{box-sizing:border-box}body{margin:0;font-family:Inter,Segoe UI,Arial,sans-serif;color:var(--ink);background:linear-gradient(145deg,#eef8ff,#ffffff 46%,#f5fbf8);min-height:100vh}
    body:before{content:"";position:fixed;inset:0;background:radial-gradient(circle at 12% 8%,rgba(18,97,166,.18),transparent 28%),radial-gradient(circle at 90% 14%,rgba(19,138,99,.14),transparent 26%);pointer-events:none}
    .wrap{position:relative;max-width:1240px;margin:0 auto;padding:24px}.top{display:flex;justify-content:space-between;gap:16px;align-items:center;margin-bottom:18px}
    .brand{display:flex;gap:14px;align-items:center}.logo{width:52px;height:52px;border-radius:18px;background:linear-gradient(145deg,#fff,#dff1ff);box-shadow:10px 12px 28px rgba(18,97,166,.16),inset -4px -4px 12px rgba(18,97,166,.08);display:grid;place-items:center;font-size:25px}
    h1{font-size:30px;margin:0}.sub{margin:4px 0 0;color:var(--muted)}.glass{background:var(--glass);border:1px solid var(--line);border-radius:24px;box-shadow:0 24px 70px rgba(15,23,42,.10),inset 0 1px 0 rgba(255,255,255,.85);backdrop-filter:blur(18px)}
    .stats{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px;margin-bottom:16px}.stat{padding:16px}.stat b{font-size:24px}.stat span{display:block;color:var(--muted);font-size:13px;margin-top:4px}
    .tabs{display:flex;flex-wrap:wrap;gap:10px;margin:16px 0}.tab{border:1px solid var(--line);background:rgba(255,255,255,.78);border-radius:16px;padding:11px 14px;font-weight:800;cursor:pointer}.tab.active{background:linear-gradient(135deg,var(--blue),var(--green));color:#fff}
    .grid{display:grid;grid-template-columns:360px 1fr;gap:16px}.panel{padding:18px}.panel h2{font-size:18px;margin:0 0 14px}.row{display:grid;grid-template-columns:1fr 1fr;gap:10px}.field{display:grid;gap:6px;margin-bottom:10px}
    label{font-size:12px;color:var(--muted);font-weight:800}input,select,textarea{width:100%;border:1px solid var(--line);border-radius:14px;padding:11px 12px;background:rgba(255,255,255,.9);font:inherit;outline:none}textarea{min-height:270px;font-family:Consolas,monospace;font-size:13px}
    button{border:0;border-radius:14px;padding:11px 14px;font-weight:900;cursor:pointer}.primary{background:linear-gradient(135deg,var(--blue),var(--green));color:white}.ghost{background:white;border:1px solid var(--line);color:var(--ink)}.danger{background:#fff0ef;color:var(--red);border:1px solid rgba(194,65,53,.2)}
    .list{display:grid;gap:10px;max-height:560px;overflow:auto;padding-right:4px}.item{padding:13px;border:1px solid var(--line);border-radius:18px;background:rgba(255,255,255,.68);display:flex;justify-content:space-between;gap:10px;align-items:center}.item strong{display:block}.pill{display:inline-flex;padding:5px 8px;border-radius:999px;font-size:12px;background:#eaf5ff;color:var(--blue);font-weight:800;margin:3px 4px 0 0}.ok{background:#eafaf2;color:var(--green)}.warn{background:#fff7e5;color:var(--amber)}.bad{background:#fff0ef;color:var(--red)}
    .hidden{display:none}.actions{display:flex;gap:8px;flex-wrap:wrap}.toast{position:fixed;right:20px;bottom:20px;padding:14px 16px;border-radius:16px;background:#102033;color:#fff;box-shadow:0 18px 45px rgba(0,0,0,.18);display:none}.small{font-size:12px;color:var(--muted);line-height:1.45}.full{grid-column:1/-1}
    @media(max-width:900px){.stats{grid-template-columns:1fr 1fr}.grid{grid-template-columns:1fr}.top{align-items:flex-start;flex-direction:column}}
  </style>
</head>
<body><div class="wrap">
  <header class="top">
    <div class="brand"><div class="logo">🛃</div><div><h1>NazoratBot Admin</h1><p class="sub">Dazvol va chegaradagi yig'im qoidalarini boshqarish</p></div></div>
    <div class="actions"><button class="ghost" onclick="loadAll()">Yangilash</button><button class="danger" onclick="logout()">Chiqish</button></div>
  </header>

  <section class="stats">
    <div class="stat glass"><b id="countryCount">0</b><span>Davlatlar</span></div>
    <div class="stat glass"><b id="ruleCount">0</b><span>Dazvol qoidalari</span></div>
    <div class="stat glass"><b id="exceptionCount">0</b><span>Istisnolar</span></div>
    <div class="stat glass"><b id="bhmValue">0</b><span>BHM</span></div>
  </section>

  <nav class="tabs">
    <button class="tab active" data-tab="overview">Bosh sahifa</button>
    <button class="tab" data-tab="rules">Dazvol qoidalari</button>
    <button class="tab" data-tab="countries">Davlatlar</button>
    <button class="tab" data-tab="fees">Chegaradagi yig'imlar</button>
    <button class="tab" data-tab="raw">Raw JSON</button>
  </nav>

  <section id="overview" class="screen grid">
    <div class="panel glass">
      <h2>Admin panel ishlash tartibi</h2>
      <p class="small">1. Dazvol qoidalari bo'limida davlatni toping.</p>
      <p class="small">2. Tashuv turini tanlab, ruxsatnoma va kirish/tranzit yig'imi holatini belgilang.</p>
      <p class="small">3. Chegaradagi yig'imlar bo'limida BHM, aniq stavkalar va huquqiy asoslarni yangilang.</p>
      <p class="small">4. Saqlangan o'zgarishlar botga avtomatik qo'llanadi.</p>
    </div>
    <div class="panel glass">
      <h2>Botga ta'siri</h2>
      <div class="item"><div><strong>📄 Dazvol</strong><span class="small">Davlatlar kesimidagi bitimlar va tashuv turi qoidalari</span></div></div>
      <div class="item"><div><strong>💰 Chegaradagi yig'imlar</strong><span class="small">BHM, tranzit deklaratsiyasi, muddat, OSAGO va boshqa to'lovlar</span></div></div>
      <div class="item"><div><strong>⚡ Avtomatik reload</strong><span class="small">JSON o'zgarsa, bot keyingi so'rovda yangi qoidani o'qiydi</span></div></div>
    </div>
  </section>

  <section id="rules" class="screen grid hidden">
    <div class="panel glass">
      <h2>Qidirish</h2>
      <div class="field"><label>Davlat nomi yoki kodi</label><input id="ruleSearch" placeholder="Masalan: Xitoy, 156" oninput="loadRules()" /></div>
      <p class="small">Davlatni tanlang, keyin 1-8 tashuv turi bo'yicha ruxsatnoma va yig'im holatini o'zgartiring.</p>
      <div id="ruleList" class="list"></div>
    </div>
    <div class="panel glass">
      <h2>Dazvol qoidasi</h2>
      <div class="row">
        <div class="field"><label>Davlat kodi</label><input id="ruleCode" placeholder="156" /></div>
        <div class="field"><label>Tashuv turi</label><select id="ruleVid"></select></div>
      </div>
      <div class="row">
        <div class="field"><label>Ruxsatnoma</label><select id="permissionCd"><option value="1">Majburiy</option><option value="2">Kerak emas</option><option value="3">Taqiqlangan</option></select></div>
        <div class="field"><label>Kirish/tranzit yig'imi</label><select id="duesCd"><option value="1">Undiriladi</option><option value="2">Undirilmaydi</option><option value="3">Ruxsat turiga qarab</option><option value="0">Belgilanmagan</option></select></div>
      </div>
      <div class="row">
        <div class="field"><label>Istisno kodi</label><input id="exceptionCd" placeholder="0 / 1 / 2" /></div>
        <div class="field"><label>Istisno nomi</label><input id="exceptionName" placeholder="Perечень..." /></div>
      </div>
      <div class="field"><label>Admin izoh</label><input id="adminNote" placeholder="Qisqa izoh" /></div>
      <div class="actions"><button class="primary" onclick="saveRule()">Saqlash</button><button class="danger" onclick="deleteRule()">Qoidani o'chirish</button></div>
    </div>
  </section>

  <section id="countries" class="screen grid hidden">
    <div class="panel glass">
      <h2>Davlat qo'shish yoki o'zgartirish</h2>
      <div class="field"><label>Kod</label><input id="countryCode" placeholder="156" /></div>
      <div class="field"><label>Nomi</label><input id="countryName" placeholder="XITOY" /></div>
      <div class="actions"><button class="primary" onclick="saveCountry()">Saqlash</button><button class="danger" onclick="deleteCountry()">Davlatni o'chirish</button></div>
    </div>
    <div class="panel glass">
      <h2>Davlatlar ro'yxati</h2>
      <div class="field"><label>Qidirish</label><input id="countrySearch" placeholder="Davlat yoki kod" oninput="loadCountries()" /></div>
      <div id="countryList" class="list"></div>
    </div>
  </section>

  <section id="fees" class="screen grid hidden">
    <div class="panel glass">
      <h2>Tez sozlamalar</h2>
      <div class="field"><label>BHM qiymati</label><input id="feeBhm" type="number" /></div>
      <div class="row">
        <div class="field"><label>Tranzit deklaratsiyasi BHM</label><input id="transitDeclBhm" type="number" step="0.01" /></div>
        <div class="field"><label>TD o'zgartirish BHM</label><input id="transitChangeBhm" type="number" step="0.01" /></div>
      </div>
      <div class="field"><label>Yuk kechikishi BHM / kun</label><input id="deliveryOverdueBhm" type="number" step="0.01" /></div>
      <div class="field"><label>Default xorijiy transport yig'imi USD</label><input id="defaultForeignUsd" type="number" /></div>
      <div class="field"><label>Turkmaniston qo'shimcha yig'imi USD</label><input id="turkmenExtraUsd" type="number" /></div>
      <div class="field"><label>Kirish/tranzit yig'imi huquqiy asosi</label><input id="basisEntry" /></div>
      <div class="field"><label>Tranzit deklaratsiyasi huquqiy asosi</label><input id="basisTransit" /></div>
      <button class="primary" onclick="saveFeeQuick()">Tez sozlamalarni saqlash</button>
      <p class="small">Murakkab stavkalar va huquqiy asoslar o'ng tomondagi JSON orqali to'liq tahrirlanadi.</p>
    </div>
    <div class="panel glass">
      <h2>Chegaradagi yig'imlar JSON</h2>
      <textarea id="feesJson"></textarea>
      <div class="actions"><button class="primary" onclick="saveFees()">JSONni saqlash</button><button class="ghost" onclick="loadFees()">Qayta yuklash</button></div>
    </div>
  </section>

  <section id="raw" class="screen grid hidden">
    <div class="panel glass full">
      <h2>Permission rules JSON</h2>
      <textarea id="permissionJson"></textarea>
      <div class="actions"><button class="primary" onclick="savePermissionJson()">To'liq JSONni saqlash</button><button class="ghost" onclick="loadRaw()">Qayta yuklash</button></div>
      <p class="small">Ehtiyot bo'ling: noto'g'ri JSON botning Dazvol tekshiruvini buzishi mumkin.</p>
    </div>
  </section>
</div><div class="toast" id="toast"></div>

<script>
const vidLabels = {
  "1":"1 - Ikki tomonlama, O'zbekistondan",
  "2":"2 - Ikki tomonlama, O'zbekistonga",
  "3":"3 - Tranzit",
  "4":"4 - Uchinchi davlatga",
  "5":"5 - Uchinchi davlatdan",
  "6":"6 - Ichki tashuv",
  "7":"7 - Yuksiz kirish",
  "8":"8 - Yuksiz tranzit"
};
let currentPermission = null;

function toast(text){const el=document.getElementById('toast');el.textContent=text;el.style.display='block';setTimeout(()=>el.style.display='none',2600)}
async function api(path, opts={}){const r=await fetch(path,{headers:{'Content-Type':'application/json'},...opts}); if(r.status===401){location.href='/admin';return} const text=await r.text(); let data; try{data=JSON.parse(text)}catch(e){data={ok:false,error:text||'Server javobi noto‘g‘ri'}} if(!r.ok||data.ok===false) throw new Error(data.error||'Xatolik'); return data}
function setTab(name){document.querySelectorAll('.tab').forEach(b=>b.classList.toggle('active',b.dataset.tab===name));document.querySelectorAll('.screen').forEach(s=>s.classList.toggle('hidden',s.id!==name))}
document.querySelectorAll('.tab').forEach(b=>b.onclick=()=>setTab(b.dataset.tab));
function initVid(){const sel=document.getElementById('ruleVid');sel.innerHTML=Object.entries(vidLabels).map(([k,v])=>`<option value="${k}">${v}</option>`).join('')}

async function loadSummary(){const d=await api('/admin/api/summary');countryCount.textContent=d.countries;ruleCount.textContent=d.rules;exceptionCount.textContent=d.exceptions;bhmValue.textContent=String(d.bhm).replace(/\\B(?=(\\d{3})+(?!\\d))/g,' ')}
async function loadRules(){const q=encodeURIComponent(ruleSearch.value||'');const d=await api('/admin/api/permission?q='+q);currentPermission=d;ruleList.innerHTML=d.countries.map(c=>`<div class="item"><div><strong>${c.code} — ${c.name}</strong><div>${Object.entries(c.rules).map(([vid,r])=>pill(vid,r)).join('')}</div></div><button class="ghost" onclick="pickCountry('${c.code}')">Tanlash</button></div>`).join('')||'<p class="small">Maʼlumot topilmadi.</p>'}
function pill(vid,r){const p=r.permission_cd==='1'?'warn':r.permission_cd==='3'?'bad':'ok';const y=r.dues_cd==='1'?'warn':r.dues_cd==='2'?'ok':'';return `<span class="pill ${p}">${vid}: R ${r.permission_cd}</span><span class="pill ${y}">Y ${r.dues_cd}</span>`}
function pickCountry(code){ruleCode.value=code;countryCode.value=code;const c=currentPermission.countries.find(x=>x.code===code);if(c){countryName.value=c.name;const first=Object.keys(c.rules)[0]||'1';ruleVid.value=first;fillRule(c.rules[first]||{})}}
function fillRule(r){permissionCd.value=r.permission_cd||'2';duesCd.value=r.dues_cd||'2';exceptionCd.value=r.exception_cd||'0';exceptionName.value=r.exception_name_ru||'';adminNote.value=r.admin_note||''}
ruleVid.addEventListener('change',()=>{const c=currentPermission?.countries?.find(x=>x.code===ruleCode.value);fillRule((c?.rules||{})[ruleVid.value]||{})});
async function saveRule(){await api('/admin/api/rule',{method:'POST',body:JSON.stringify({country_code:ruleCode.value,vid_cd:ruleVid.value,permission_cd:permissionCd.value,dues_cd:duesCd.value,exception_cd:exceptionCd.value,exception_name_ru:exceptionName.value,admin_note:adminNote.value})});toast('Dazvol qoidasi saqlandi');await loadAll()}
async function deleteRule(){if(!confirm('Ushbu qoidani o‘chirasizmi?'))return;await api(`/admin/api/rule/${ruleCode.value}/${ruleVid.value}`,{method:'DELETE'});toast('Qoida o‘chirildi');await loadAll()}

async function loadCountries(){const q=encodeURIComponent(countrySearch.value||'');const d=await api('/admin/api/permission?q='+q);countryList.innerHTML=d.countries.map(c=>`<div class="item"><div><strong>${c.code}</strong><span> ${c.name}</span></div><button class="ghost" onclick="countryCode.value='${c.code}';countryName.value='${String(c.name).replaceAll("'","&#39;")}'">Tanlash</button></div>`).join('')}
async function saveCountry(){await api('/admin/api/country',{method:'POST',body:JSON.stringify({code:countryCode.value,name:countryName.value})});toast('Davlat saqlandi');await loadAll()}
async function deleteCountry(){if(!confirm('Davlat, qoidalar va istisnolar o‘chiriladi. Davom etasizmi?'))return;await api(`/admin/api/country/${countryCode.value}`,{method:'DELETE'});toast('Davlat o‘chirildi');await loadAll()}

async function loadFees(){const d=await api('/admin/api/fees');feesJson.value=JSON.stringify(d.fees,null,2);feeBhm.value=d.fees.bhm?.value||'';transitDeclBhm.value=d.fees.fixed?.transit_declaration_bhm||'';transitChangeBhm.value=d.fees.fixed?.transit_declaration_change_bhm||'';deliveryOverdueBhm.value=d.fees.fixed?.delivery_overdue_bhm_per_day||'';defaultForeignUsd.value=d.fees.entry_fee?.default_foreign_usd||'';turkmenExtraUsd.value=d.fees.entry_fee?.turkmenistan_extra_usd||'';basisEntry.value=d.fees.legal_basis?.entry_transit_fee||'';basisTransit.value=d.fees.legal_basis?.transit_declaration||''}
async function saveFees(){let parsed;try{parsed=JSON.parse(feesJson.value)}catch(e){toast('JSON xato: '+e.message);return}await api('/admin/api/fees',{method:'POST',body:JSON.stringify({fees:parsed})});toast('Yig‘imlar saqlandi');await loadAll()}
async function saveFeeQuick(){const d=JSON.parse(feesJson.value||'{}');d.bhm=d.bhm||{};d.fixed=d.fixed||{};d.entry_fee=d.entry_fee||{};d.legal_basis=d.legal_basis||{};d.bhm.value=Number(feeBhm.value);d.fixed.transit_declaration_bhm=Number(transitDeclBhm.value);d.fixed.transit_declaration_change_bhm=Number(transitChangeBhm.value);d.fixed.delivery_overdue_bhm_per_day=Number(deliveryOverdueBhm.value);d.entry_fee.default_foreign_usd=Number(defaultForeignUsd.value);d.entry_fee.turkmenistan_extra_usd=Number(turkmenExtraUsd.value);d.legal_basis.entry_transit_fee=basisEntry.value;d.legal_basis.transit_declaration=basisTransit.value;feesJson.value=JSON.stringify(d,null,2);await saveFees()}
async function loadRaw(){const d=await api('/admin/api/permission/full');permissionJson.value=JSON.stringify(d.permission,null,2)}
async function savePermissionJson(){let parsed;try{parsed=JSON.parse(permissionJson.value)}catch(e){toast('JSON xato: '+e.message);return}await api('/admin/api/permission/full',{method:'POST',body:JSON.stringify({permission:parsed})});toast('Permission JSON saqlandi');await loadAll()}
async function logout(){await fetch('/admin/logout',{method:'POST'});location.href='/admin'}
async function loadAll(){await loadSummary();await loadRules();await loadCountries();await loadFees();await loadRaw()}
initVid();loadAll().catch(e=>toast(e.message));
</script></body></html>"""


def setup_admin_routes(app: web.Application, settings: Settings) -> None:
    async def admin_index(request: web.Request) -> web.Response:
        if not _is_authenticated(request, settings):
            return web.Response(text=_login_page(), content_type="text/html")
        return web.Response(text=_admin_page(), content_type="text/html")

    async def login(request: web.Request) -> web.Response:
        form = await request.post()
        username = str(form.get("username") or "")
        password = str(form.get("password") or "")
        if not (
            hmac.compare_digest(username, settings.admin_username)
            and hmac.compare_digest(password, settings.admin_password)
        ):
            return web.Response(text=_login_page(), content_type="text/html", status=403)
        response = web.HTTPFound("/admin/dashboard")
        response.set_cookie(
            SESSION_COOKIE,
            _signed_token(settings),
            max_age=SESSION_TTL_SECONDS,
            httponly=True,
            secure=bool(settings.webhook_url.startswith("https://")),
            samesite="Lax",
        )
        raise response

    async def logout(_: web.Request) -> web.Response:
        response = web.json_response({"ok": True})
        response.del_cookie(SESSION_COOKIE)
        return response

    async def summary(request: web.Request) -> web.Response:
        _require_admin(request, settings)
        permission = _read_json(settings.permission_rules_path)
        fees = _read_json(settings.fees_rules_path)
        rule_count = sum(len(v) for v in permission.get("rules", {}).values())
        exception_count = sum(len(v) for v in permission.get("exceptions", {}).values())
        return web.json_response(
            {
                "ok": True,
                "countries": len(permission.get("countries", {})),
                "rules": rule_count,
                "exceptions": exception_count,
                "bhm": fees.get("bhm", {}).get("value", settings.bhm_value),
            }
        )

    async def permission_list(request: web.Request) -> web.Response:
        _require_admin(request, settings)
        data = _read_json(settings.permission_rules_path)
        query = str(request.query.get("q") or "").strip().lower()
        countries = []
        for code, name in sorted(data.get("countries", {}).items()):
            haystack = f"{code} {name}".lower()
            if query and query not in haystack:
                continue
            countries.append({"code": code, "name": name, "rules": data.get("rules", {}).get(code, {})})
            if len(countries) >= 80:
                break
        return web.json_response({"ok": True, "countries": countries, "vid_types": data.get("vid_types", {})})

    async def permission_full(request: web.Request) -> web.Response:
        _require_admin(request, settings)
        return web.json_response({"ok": True, "permission": _read_json(settings.permission_rules_path)})

    async def save_permission_full(request: web.Request) -> web.Response:
        _require_admin(request, settings)
        body = await request.json()
        permission = body.get("permission")
        if not isinstance(permission, dict) or "countries" not in permission or "rules" not in permission:
            return _json_error("Permission JSON tuzilmasi noto'g'ri.")
        permission.setdefault("source", {})["last_admin_update"] = int(time.time())
        _write_json(settings.permission_rules_path, permission)
        return web.json_response({"ok": True})

    async def save_country(request: web.Request) -> web.Response:
        _require_admin(request, settings)
        body = await request.json()
        code = _code(body.get("code"))
        name = str(body.get("name") or "").strip()
        if len(name) < 2:
            return _json_error("Davlat nomi kiritilmadi.")
        data = _read_json(settings.permission_rules_path)
        data.setdefault("countries", {})[code] = name
        data.setdefault("rules", {}).setdefault(code, {})
        data.setdefault("source", {})["last_admin_update"] = int(time.time())
        _write_json(settings.permission_rules_path, data)
        return web.json_response({"ok": True, "code": code})

    async def delete_country(request: web.Request) -> web.Response:
        _require_admin(request, settings)
        code = _code(request.match_info["code"])
        data = _read_json(settings.permission_rules_path)
        data.get("countries", {}).pop(code, None)
        data.get("rules", {}).pop(code, None)
        data.get("exceptions", {}).pop(code, None)
        data.setdefault("source", {})["last_admin_update"] = int(time.time())
        _write_json(settings.permission_rules_path, data)
        return web.json_response({"ok": True})

    async def save_rule(request: web.Request) -> web.Response:
        _require_admin(request, settings)
        body = await request.json()
        code = _code(body.get("country_code"))
        data = _read_json(settings.permission_rules_path)
        if code not in data.get("countries", {}):
            return _json_error("Avval davlatni qo'shing.")
        rule = _rule_payload(body, data)
        data.setdefault("rules", {}).setdefault(code, {})[rule["vid_cd"]] = rule
        data.setdefault("source", {})["last_admin_update"] = int(time.time())
        _write_json(settings.permission_rules_path, data)
        return web.json_response({"ok": True, "rule": rule})

    async def delete_rule(request: web.Request) -> web.Response:
        _require_admin(request, settings)
        code = _code(request.match_info["code"])
        vid_cd = _vid(request.match_info["vid"])
        data = _read_json(settings.permission_rules_path)
        data.setdefault("rules", {}).setdefault(code, {}).pop(vid_cd, None)
        data.setdefault("source", {})["last_admin_update"] = int(time.time())
        _write_json(settings.permission_rules_path, data)
        return web.json_response({"ok": True})

    async def fees(request: web.Request) -> web.Response:
        _require_admin(request, settings)
        return web.json_response({"ok": True, "fees": _read_json(settings.fees_rules_path)})

    async def save_fees(request: web.Request) -> web.Response:
        _require_admin(request, settings)
        body = await request.json()
        fees_data = body.get("fees")
        if not isinstance(fees_data, dict) or "entry_fee" not in fees_data:
            return _json_error("Yig'im JSON tuzilmasi noto'g'ri.")
        fees_data.setdefault("source", {})["last_admin_update"] = int(time.time())
        _write_json(settings.fees_rules_path, fees_data)
        return web.json_response({"ok": True})

    app.router.add_get("/admin", admin_index)
    app.router.add_get("/admin/dashboard", admin_index)
    app.router.add_post("/admin/login", login)
    app.router.add_post("/admin/logout", logout)
    app.router.add_get("/admin/api/summary", summary)
    app.router.add_get("/admin/api/permission", permission_list)
    app.router.add_get("/admin/api/permission/full", permission_full)
    app.router.add_post("/admin/api/permission/full", save_permission_full)
    app.router.add_post("/admin/api/country", save_country)
    app.router.add_delete("/admin/api/country/{code}", delete_country)
    app.router.add_post("/admin/api/rule", save_rule)
    app.router.add_delete("/admin/api/rule/{code}/{vid}", delete_rule)
    app.router.add_get("/admin/api/fees", fees)
    app.router.add_post("/admin/api/fees", save_fees)

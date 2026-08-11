from __future__ import annotations

import asyncio
import hmac
import json
import logging
import secrets
import time
import uuid
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
from typing import Any

from aiohttp import web

from app.config import Settings
from app.metrics import metrics
from app.rule_versions import RuleVersionStore
from app.services.permission_import import (
    PermissionImportError,
    apply_permission_import_changes,
    build_permission_import_preview,
)
from app.services.permit import COUNTRY_LABELS, transliterate_cyrillic_to_latin


SESSION_COOKIE = "nazorat_admin"
SESSION_TTL_SECONDS = 12 * 60 * 60
MAX_IMPORT_FILE_BYTES = 10 * 1024 * 1024
IMPORT_JOB_TTL_SECONDS = 60 * 60
MAX_IMPORT_JOBS = 10
IMPORT_JOBS: dict[str, dict[str, Any]] = {}
IMPORT_TASKS: set[asyncio.Task[Any]] = set()
logger = logging.getLogger(__name__)

PERMISSION_NAMES = {
    "1": "Обязательно",
    "2": "Не обязательно",
    "3": "Запрещен",
}

DUES_NAMES = {
    "0": "-не выбрано-",
    "1": "Сбор обязательно",
    "2": "Сбор не обязательно",
    "3": "Сбор зависит от вида разрешения",
}

DEFAULT_FEE_ITEMS = {
    "import": [
        {
            "id": "transit_declaration_import",
            "title": "Tranzit deklaratsiyasi",
            "amount": "103 000 so'm",
            "condition": "Yuk bojxona nazoratiga qo'yilganda",
            "basis": "VMning 31.01.2025 y. 55-son qarori, 1-ilova",
            "enabled": True,
        },
        {
            "id": "osago_import",
            "title": "OSAGO sug'urta",
            "amount": "Tarif bo'yicha",
            "condition": "Xorijiy transportda xalqaro sug'urta polisi bo'lmasa",
            "basis": "VMning 30.12.2021 y. 790-son qarori",
            "enabled": True,
        },
        {
            "id": "quarantine_import",
            "title": "Karantin/veterinariya/fitosanitariya",
            "amount": "Preyskurant bo'yicha",
            "condition": "Tovar nazoratdagi tovar turiga kirsa",
            "basis": "Vakolatli organlarning amaldagi preyskuranti",
            "enabled": True,
        },
    ],
    "export": [
        {
            "id": "cargo_declaration_export",
            "title": "Eksport/yuk deklaratsiyasi",
            "amount": "1-25 BHM",
            "condition": "Yuk deklaratsiyasi rasmiylashtirilganda",
            "basis": "VMning 31.01.2025 y. 55-son qarori, 1-ilova",
            "enabled": True,
        },
        {
            "id": "delivery_overdue_export",
            "title": "Yukni kech yetkazish",
            "amount": "412 000 so'm / kun",
            "condition": "Bojxona nazoratidagi yuk muddati o'tsa",
            "basis": "VMning 31.12.2022 y. 737-son qarori",
            "enabled": True,
        },
    ],
    "transit": [
        {
            "id": "transit_declaration",
            "title": "Tranzit deklaratsiyasi",
            "amount": "103 000 so'm",
            "condition": "Har bir tranzit deklaratsiyasi uchun",
            "basis": "VMning 31.01.2025 y. 55-son qarori, 1-ilova",
            "enabled": True,
        },
        {
            "id": "transit_declaration_change",
            "title": "TD o'zgartirish",
            "amount": "41 200 so'm",
            "condition": "Deklarant murojaati bilan o'zgartirilsa",
            "basis": "VMning 31.01.2025 y. 55-son qarori, 1-ilova",
            "enabled": True,
        },
        {
            "id": "delivery_overdue_transit",
            "title": "Yukni kech yetkazish",
            "amount": "412 000 so'm / kun",
            "condition": "Har bir kechikkan kun uchun",
            "basis": "VMning 31.12.2022 y. 737-son qarori",
            "enabled": True,
        },
    ],
}

_JSON_CACHE: dict[Path, tuple[int, int, dict[str, Any]]] = {}


def _read_json(path: Path) -> dict[str, Any]:
    stat = path.stat()
    cached = _JSON_CACHE.get(path)
    if cached and cached[0] == stat.st_mtime_ns and cached[1] == stat.st_size:
        return deepcopy(cached[2])
    data = json.loads(path.read_text(encoding="utf-8"))
    _JSON_CACHE[path] = (stat.st_mtime_ns, stat.st_size, data)
    return deepcopy(data)


def _read_json_view(path: Path) -> dict[str, Any]:
    """Returns the cached object for read-only handlers without a large deepcopy."""
    stat = path.stat()
    cached = _JSON_CACHE.get(path)
    if cached and cached[0] == stat.st_mtime_ns and cached[1] == stat.st_size:
        return cached[2]
    data = json.loads(path.read_text(encoding="utf-8"))
    _JSON_CACHE[path] = (stat.st_mtime_ns, stat.st_size, data)
    return data


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    tmp_path.replace(path)
    stat = path.stat()
    _JSON_CACHE[path] = (stat.st_mtime_ns, stat.st_size, deepcopy(data))


def _draft_path(path: Path) -> Path:
    return path.with_name(path.stem + ".draft" + path.suffix)


def _ensure_draft(path: Path) -> Path:
    draft = _draft_path(path)
    if not draft.exists():
        _write_json(draft, _read_json(path))
    return draft


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


def _cleanup_import_jobs() -> None:
    cutoff = time.time() - IMPORT_JOB_TTL_SECONDS
    expired = [job_id for job_id, job in IMPORT_JOBS.items() if float(job.get("created_at", 0)) < cutoff]
    for job_id in expired:
        IMPORT_JOBS.pop(job_id, None)
    if len(IMPORT_JOBS) > MAX_IMPORT_JOBS:
        removable = sorted(
            (
                (job_id, job) for job_id, job in IMPORT_JOBS.items()
                if job.get("status") not in {"queued", "processing"}
            ),
            key=lambda item: float(item[1].get("created_at", 0)),
        )
        for job_id, _ in removable[: max(0, len(IMPORT_JOBS) - MAX_IMPORT_JOBS)]:
            IMPORT_JOBS.pop(job_id, None)


def _import_job_response(job: dict[str, Any]) -> dict[str, Any]:
    response = {
        "ok": True,
        "job_id": job["job_id"],
        "status": job["status"],
        "progress": job.get("progress", 0),
        "message": job.get("message", ""),
        "filename": job.get("filename", ""),
        "summary": job.get("summary", {}),
        "error": job.get("error", ""),
    }
    if job.get("status") in {"ready", "applied"}:
        response["changes"] = job.get("changes", [])
    if job.get("status") == "applied":
        response["applied_count"] = job.get("applied_count", 0)
    return response


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
        "dues_amount_usd": str(data.get("dues_amount_usd") or "").strip() if dues_cd == "1" else "",
        "dues_amount_note_uz": str(data.get("dues_amount_note_uz") or "").strip(),
        "dues_amount_note_ru": str(data.get("dues_amount_note_ru") or "").strip(),
        "dues_amount_note_en": str(data.get("dues_amount_note_en") or "").strip(),
        "source": "web-admin-panel",
        "admin_note": str(data.get("admin_note") or "").strip(),
    }


def _country_uz_name(data: dict[str, Any], code: str, fallback: str) -> str:
    labels = data.get("country_labels", {}).get(code, {})
    if isinstance(labels, dict) and labels.get("uz"):
        return str(labels["uz"])
    builtin = COUNTRY_LABELS.get(code, {})
    if builtin.get("uz"):
        return str(builtin["uz"])
    latin = transliterate_cyrillic_to_latin(fallback)
    if latin and latin != fallback.lower():
        return latin.title()
    return fallback.title() if fallback.isupper() else fallback


def _fee_items(fees_data: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    items = fees_data.setdefault("admin_fee_items", {})
    for direction, defaults in DEFAULT_FEE_ITEMS.items():
        items.setdefault(direction, defaults)
    return items


def _fee_direction(value: object) -> str:
    direction = str(value or "").strip().lower()
    if direction not in {"import", "export", "transit"}:
        raise web.HTTPBadRequest(text="Yig'im yo'nalishi noto'g'ri.")
    return direction


def _fee_item_payload(data: dict[str, Any]) -> dict[str, Any]:
    item_id = str(data.get("id") or "").strip()
    if not item_id:
        item_id = secrets.token_urlsafe(8)
    title = str(data.get("title") or "").strip()
    if len(title) < 2:
        raise web.HTTPBadRequest(text="Yig'im nomi kiritilmadi.")
    return {
        "id": item_id,
        "title": title,
        "amount": str(data.get("amount") or "").strip(),
        "condition": str(data.get("condition") or "").strip(),
        "basis": str(data.get("basis") or "").strip(),
        "enabled": bool(data.get("enabled", True)),
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
    return _admin_page_v2()
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


def _admin_page_v2() -> str:
    return """<!doctype html>
<html lang="uz">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>NazoratBot Web Admin</title>
  <style>
    :root{--ink:#102033;--muted:#64748b;--line:rgba(15,23,42,.12);--blue:#1064b0;--green:#0f8f70;--red:#c43b32;--amber:#b7791f;--glass:rgba(255,255,255,.74)}
    *{box-sizing:border-box}body{margin:0;font-family:Inter,Segoe UI,Arial,sans-serif;color:var(--ink);background:linear-gradient(135deg,#eef8ff,#fff 48%,#effcf7);min-height:100vh}
    body:before{content:"";position:fixed;inset:0;background:radial-gradient(circle at 10% 5%,rgba(16,100,176,.18),transparent 30%),radial-gradient(circle at 92% 18%,rgba(15,143,112,.17),transparent 30%);pointer-events:none}
    button,input,select,textarea{font:inherit}button{cursor:pointer}.app{position:relative;display:grid;grid-template-columns:280px 1fr;gap:18px;min-height:100vh;padding:18px}
    .glass{background:var(--glass);border:1px solid var(--line);border-radius:26px;box-shadow:0 24px 80px rgba(15,23,42,.10),inset 0 1px 0 rgba(255,255,255,.88);backdrop-filter:blur(18px)}
    .side{padding:18px;position:sticky;top:18px;height:calc(100vh - 36px)}.brand{display:flex;gap:12px;align-items:center;margin-bottom:18px}.logo{width:50px;height:50px;border-radius:18px;display:grid;place-items:center;background:linear-gradient(145deg,#fff,#e0f2ff);box-shadow:10px 12px 24px rgba(16,100,176,.14),inset -5px -5px 12px rgba(16,100,176,.08);font-size:25px}
    h1{font-size:20px;margin:0}.hint{color:var(--muted);font-size:12px;line-height:1.45}.nav{display:grid;gap:8px;margin-top:20px}.nav button{border:1px solid var(--line);background:rgba(255,255,255,.7);border-radius:18px;padding:13px;text-align:left;font-weight:900}.nav button.active{background:linear-gradient(135deg,var(--blue),var(--green));color:white;box-shadow:0 12px 28px rgba(16,100,176,.18)}
    .main{display:grid;gap:16px}.top{display:flex;justify-content:space-between;gap:12px;align-items:center;padding:18px}.top h2{margin:0;font-size:28px}.actions{display:flex;gap:9px;flex-wrap:wrap}
    .btn{border:0;border-radius:16px;padding:11px 14px;font-weight:900;background:white;border:1px solid var(--line)}.btn.primary{background:linear-gradient(135deg,var(--blue),var(--green));color:white;border:0}.btn.danger{background:#fff0ef;color:var(--red);border-color:rgba(196,59,50,.18)}
    .stats{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}.stat{padding:16px}.stat b{display:block;font-size:26px}.stat span{font-size:12px;color:var(--muted);font-weight:800}
    .screen{display:none}.screen.active{display:grid;gap:16px}.toolbar{display:flex;gap:10px;align-items:center;justify-content:space-between;padding:14px}.search{width:min(420px,100%);border:1px solid var(--line);border-radius:18px;padding:13px 14px;background:rgba(255,255,255,.84);outline:none}
    .cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(270px,1fr));gap:14px}.card{padding:16px}.card h3{margin:0 0 6px;font-size:17px}.muted{color:var(--muted);font-size:13px}.pill{display:inline-flex;padding:6px 9px;border-radius:999px;font-size:12px;font-weight:900;margin:4px 4px 0 0}.ok{background:#e8f8ef;color:var(--green)}.warn{background:#fff7df;color:var(--amber)}.bad{background:#fff0ef;color:var(--red)}.info{background:#eaf4ff;color:var(--blue)}
    .fee-tabs{display:flex;gap:8px;flex-wrap:wrap}.fee-tab{border:1px solid var(--line);background:white;border-radius:16px;padding:11px 14px;font-weight:900}.fee-tab.active{background:var(--ink);color:white}
    .form-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px}.field{display:grid;gap:6px;margin-bottom:10px}.field.full{grid-column:1/-1}label{font-size:12px;color:#52627a;font-weight:900}input,select,textarea{width:100%;border:1px solid var(--line);border-radius:16px;padding:12px;background:rgba(255,255,255,.88);outline:none}textarea{min-height:90px}
    .detail-head{display:grid;grid-template-columns:auto 1fr auto;gap:14px;align-items:center;padding:16px}.detail-head h2{margin:0;font-size:25px}.detail-block{padding:16px}.section-title{display:flex;justify-content:space-between;gap:12px;align-items:end;padding:4px 2px}.section-title h3{font-size:22px;margin:0}.rule-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(330px,1fr));gap:14px}.rule-card{padding:16px}.rule-card-head{display:flex;justify-content:space-between;gap:10px;align-items:flex-start;margin-bottom:12px}.rule-title{display:flex;gap:10px;align-items:flex-start}.transport-icon{width:44px;height:44px;border-radius:16px;display:grid;place-items:center;font-size:22px;background:linear-gradient(145deg,#fff,#e7f6ff);box-shadow:8px 10px 20px rgba(16,100,176,.12),inset -4px -4px 10px rgba(16,100,176,.08)}.rule-card h4{margin:0;font-size:17px}.rule-card .mini{font-size:12px;color:var(--muted);font-weight:900}.status-row{display:flex;flex-wrap:wrap;gap:6px;margin:8px 0 2px}.note-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:8px}.text-edit-btn{width:100%;border:1px solid var(--line);border-radius:15px;padding:11px 12px;background:rgba(255,255,255,.76);text-align:left;font-weight:900;color:#334155}.text-edit-btn.has-text{background:#edf9f4;color:var(--green);border-color:rgba(15,143,112,.22)}.text-edit-btn.empty{background:#f8fafc;color:#64748b}.back-link{white-space:nowrap}
    .modal{position:fixed;inset:0;background:rgba(16,32,51,.28);display:none;place-items:center;padding:20px;z-index:50}.modal.show{display:grid}.dialog{width:min(980px,100%);max-height:92vh;overflow:auto;padding:20px}.dialog.text-dialog{width:min(760px,100%)}.dialog-head{display:flex;justify-content:space-between;gap:12px;align-items:center;border-bottom:1px solid var(--line);padding-bottom:12px;margin-bottom:14px}.dialog h3{font-size:24px;margin:0}.large-text{min-height:310px;resize:vertical;line-height:1.5;font-size:15px}
    table{width:100%;border-collapse:separate;border-spacing:0 8px}td,th{text-align:left;padding:10px;background:rgba(255,255,255,.72);font-size:13px;vertical-align:top}th{color:#52627a;background:transparent}.toast{position:fixed;right:20px;bottom:20px;padding:14px 16px;border-radius:16px;background:#102033;color:white;display:none;z-index:80}
    .import-box{padding:18px;display:grid;gap:14px}.file-row{display:flex;gap:10px;align-items:end;flex-wrap:wrap}.file-row .field{flex:1;min-width:240px}.progress-box{display:none;gap:8px}.progress-box.show{display:grid}.progress-track{height:14px;border-radius:999px;background:#e5edf5;overflow:hidden;border:1px solid var(--line)}.progress-bar{height:100%;width:0;background:linear-gradient(90deg,var(--blue),var(--green));transition:width .25s ease}.progress-meta{display:flex;justify-content:space-between;gap:10px;font-size:13px;font-weight:900}.import-summary{display:grid;grid-template-columns:repeat(auto-fit,minmax(145px,1fr));gap:10px}.import-summary div{padding:12px;border-radius:18px;background:rgba(255,255,255,.72);border:1px solid var(--line)}.import-summary b{display:block;font-size:22px}.compare-wrap{overflow:visible}.compare-table td:first-child,.compare-table th:first-child{width:44px;text-align:center}.compare-table input[type=checkbox]{width:20px;height:20px;accent-color:var(--green)}.compare-table tr.not-selected{opacity:.48}.change-text{min-width:190px;line-height:1.45;white-space:normal}.change-code{font-family:Consolas,monospace;font-weight:900}.import-empty{text-align:center;padding:28px;color:var(--muted)}
    @media(max-width:900px){.app{grid-template-columns:1fr}.side{position:relative;height:auto}.stats,.import-summary{grid-template-columns:1fr 1fr}.form-grid,.detail-head,.note-grid{grid-template-columns:1fr}.top{align-items:flex-start;flex-direction:column}.compare-table thead{display:none}.compare-table,.compare-table tbody,.compare-table tr,.compare-table td{display:block;width:100%}.compare-table tr{margin-bottom:12px;padding:10px;background:rgba(255,255,255,.72);border:1px solid var(--line);border-radius:18px}.compare-table td{background:transparent;padding:7px}.compare-table td:before{content:attr(data-label);display:block;font-size:11px;color:var(--muted);font-weight:900;margin-bottom:4px}.compare-table td:first-child{text-align:left;width:100%}}
  </style>
</head>
<body>
<div class="app">
  <aside class="side glass">
    <div class="brand"><div class="logo">🛃</div><div><h1>NazoratBot Admin</h1><div class="hint">Web dashboard</div></div></div>
    <div class="hint">Texnik sozlamalar yashirilgan. Qoidalar oddiy forma, karta va alohida sahifalar orqali boshqariladi.</div>
    <nav class="nav">
      <button class="active" data-screen="home">🏠 Bosh sahifa</button>
      <button data-screen="dazvol">📄 Dazvol</button>
      <button data-screen="importRules">📥 Qoidalarni import qilish</button>
      <button data-screen="fees">💰 Chegaradagi yig'imlar</button>
      <button data-screen="countries">🌍 Davlatlar</button>
      <button data-screen="governance">🕘 Versiyalar va audit</button>
    </nav>
  </aside>
  <main class="main">
    <header class="top glass">
      <div><h2 id="pageTitle">Bosh sahifa</h2><div class="muted">Qoidalarni sodda tahrirlash paneli</div></div>
      <div class="actions"><span id="draftBadge" class="pill info">Tekshirilmoqda</span><button class="btn primary" onclick="publishDraft()">🚀 E'lon qilish</button><button class="btn" onclick="discardDraft()">↩️ Qoralamani bekor qilish</button><button class="btn" onclick="loadAll()">🔄 Yangilash</button><button class="btn danger" onclick="logout()">🚪 Chiqish</button></div>
    </header>
    <section class="stats">
      <div class="stat glass"><b id="countryCount">0</b><span>Davlatlar</span></div>
      <div class="stat glass"><b id="ruleCount">0</b><span>Dazvol qoidalari</span></div>
      <div class="stat glass"><b id="exceptionCount">0</b><span>Istisnolar</span></div>
      <div class="stat glass"><b id="bhmValue">0</b><span>BHM</span></div>
    </section>
    <section class="stats">
      <div class="stat glass"><b id="startCount">0</b><span>Botni ishga tushirish</span></div>
      <div class="stat glass"><b id="permitCheckCount">0</b><span>Dazvol tekshiruvi</span></div>
      <div class="stat glass"><b id="feeCheckCount">0</b><span>Yig'im hisobi</span></div>
      <div class="stat glass"><b id="errorCount">0</b><span>Texnik xatolar</span></div>
    </section>

    <section id="home" class="screen active">
      <div class="cards">
        <div class="card glass"><h3>📄 Dazvol</h3><p class="muted">Davlatni tanlang, alohida sahifada barcha tashuv turlari, ruxsatnoma va yig'im holatlarini ko'ring yoki o'zgartiring.</p></div>
        <div class="card glass"><h3>💰 Chegaradagi yig'imlar</h3><p class="muted">Import, eksport va tranzit yo'nalishlari bo'yicha yig'imlarni alohida ro'yxatlarda boshqaring.</p></div>
        <div class="card glass"><h3>🌍 Davlatlar</h3><p class="muted">Davlat kodi, ruscha nomi va o'zbekcha nomini saqlang. Qidiruv o'zbekcha nom bilan ham ishlaydi.</p></div>
      </div>
    </section>

    <section id="dazvol" class="screen">
      <div class="toolbar glass"><input id="dazvolSearch" class="search" placeholder="Davlat nomi yoki kodi: Qirg'iziston, 417..." oninput="queueSearch('dazvol')" /><button class="btn primary" onclick="openCountryPage()">➕ Davlat qo'shish</button></div>
      <div id="dazvolCards" class="cards"></div>
    </section>

    <section id="fees" class="screen">
      <div class="toolbar glass">
        <div class="fee-tabs">
          <button class="fee-tab active" data-direction="import">Import</button>
          <button class="fee-tab" data-direction="export">Eksport</button>
          <button class="fee-tab" data-direction="transit">Tranzit</button>
        </div>
        <button class="btn primary" onclick="openFeeModal()">➕ Yig'im qo'shish</button>
      </div>
      <div id="feeCards" class="cards"></div>
    </section>

    <section id="countries" class="screen">
      <div class="toolbar glass"><input id="countrySearch" class="search" placeholder="Davlatni qidiring..." oninput="queueSearch('countries')" /><button class="btn primary" onclick="openCountryPage()">➕ Davlat qo'shish</button></div>
      <div id="countryCards" class="cards"></div>
    </section>

    <section id="importRules" class="screen">
      <div class="import-box glass">
        <div>
          <h3 style="margin:0 0 6px">📥 Excel orqali qoidalarni yangilash</h3>
          <div class="muted">Excel avval tahlil qilinadi. Hech bir qoida tasdiqlashdan oldin o'zgarmaydi.</div>
        </div>
        <div class="file-row">
          <div class="field">
            <label>📊 Dazvol qoidalari Excel fayli (.xlsx)</label>
            <input id="permissionImportFile" type="file" accept=".xlsx,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" />
          </div>
          <button id="startImportButton" class="btn primary" onclick="startPermissionImport()">🔍 Tahlil qilish</button>
        </div>
        <div id="importProgress" class="progress-box">
          <div class="progress-meta"><span id="importProgressText">Tayyorlanmoqda</span><span id="importProgressPercent">0%</span></div>
          <div class="progress-track"><div id="importProgressBar" class="progress-bar"></div></div>
        </div>
      </div>
      <div id="importPreview" style="display:none;gap:14px">
        <div id="importSummary" class="import-summary"></div>
        <div class="toolbar glass">
          <div class="actions">
            <button class="btn" onclick="selectImportChanges(true)">☑️ Barchasini tanlash</button>
            <button class="btn" onclick="selectSafeImportChanges()">🛡️ Faqat xavfsizlari</button>
            <button class="btn" onclick="selectImportChanges(false)">⬜ Tanlovni bekor qilish</button>
          </div>
          <div class="actions">
            <select id="importActionFilter" onchange="renderImportChanges()"><option value="all">Barcha o'zgarishlar</option><option value="add">Qo'shiladigan</option><option value="update">Yangilanadigan</option><option value="delete">O'chiriladigan</option></select>
            <button id="applyImportButton" class="btn primary" onclick="applyPermissionImport()">💾 Tanlanganlarni qo'llash</button>
          </div>
        </div>
        <div class="glass detail-block compare-wrap">
          <table class="compare-table">
            <thead><tr><th>Tanlash</th><th>Davlat / tashuv</th><th>Amal</th><th>Avvalgi holat</th><th>Excel bo'yicha yangi holat</th><th>Tahrirlash</th></tr></thead>
            <tbody id="importChangesBody"></tbody>
          </table>
        </div>
      </div>
    </section>

    <section id="governance" class="screen">
      <div class="toolbar glass"><div><h3 style="margin:0">🕘 Qoidalar tarixi</h3><div class="muted">Faol versiyani kuzatish va oldingi versiyani qayta e'lon qilish</div></div><button class="btn" onclick="loadGovernance()">🔄 Yangilash</button></div>
      <div class="section-title"><h3>📚 Versiyalar</h3><span class="muted">Rollback yangi faol versiya yaratadi</span></div>
      <div id="versionsBox" class="cards"></div>
      <div class="section-title"><h3>🧾 Audit jurnali</h3><span class="muted">Admin amallari</span></div>
      <div class="glass detail-block"><table><thead><tr><th>Vaqt</th><th>Amal</th><th>Admin</th><th>Tafsilot</th></tr></thead><tbody id="auditBody"></tbody></table></div>
    </section>

    <section id="countryDetail" class="screen">
      <div class="detail-head glass">
        <button class="btn" onclick="backToCountryList()">⬅️ Ro'yxatga qaytish</button>
        <div><h2 id="countryPageTitle">🌍 Davlat</h2><div class="muted">📄 Dazvol qoidalarini alohida kartalar orqali tahrirlash</div></div>
        <div class="actions"><button class="btn primary" onclick="saveCountry()">💾 Davlatni saqlash</button><button class="btn danger" onclick="deleteCountry()">🗑️ Davlatni o'chirish</button></div>
      </div>
      <div class="glass detail-block">
        <div class="form-grid">
          <div class="field"><label>🔢 Kod</label><input id="countryCode" /></div>
          <div class="field"><label>🇺🇿 O'zbekcha nom</label><input id="countryNameUz" /></div>
          <div class="field full"><label>🌐 Asosiy/Ruscha nom</label><input id="countryName" /></div>
        </div>
      </div>
      <div class="section-title"><h3>📄 Dazvol qoidalari</h3><span class="muted">🚚 Har bir tashuv turi alohida saqlanadi</span></div>
      <div id="rulesTable" class="rule-grid"></div>
      <div class="section-title"><h3>🧾 Istisnolar</h3><span class="muted">📌 Spravochnikdan olingan istisno holatlar</span></div>
      <div id="exceptionsBox" class="cards"></div>
    </section>
  </main>
</div>

<div id="feeModal" class="modal">
  <div class="dialog glass">
    <div class="dialog-head"><h3 id="feeModalTitle">Yig'im</h3><button class="btn" onclick="closeModal('feeModal')">Yopish</button></div>
    <input id="feeId" type="hidden" />
    <div class="form-grid">
      <div class="field"><label>Yo'nalish</label><select id="feeDirection"><option value="import">Import</option><option value="export">Eksport</option><option value="transit">Tranzit</option></select></div>
      <div class="field"><label>Yig'im nomi</label><input id="feeTitle" /></div>
      <div class="field"><label>Miqdor</label><input id="feeAmount" placeholder="103 000 so'm / 1 BHM / tarif bo'yicha" /></div>
      <div class="field"><label>Holati</label><select id="feeEnabled"><option value="true">Faol</option><option value="false">O'chirilgan</option></select></div>
      <div class="field full"><label>Qaysi holatda qo'llaniladi</label><textarea id="feeCondition"></textarea></div>
      <div class="field full"><label>Huquqiy asosi</label><textarea id="feeBasis"></textarea></div>
    </div>
    <div class="actions"><button class="btn primary" onclick="saveFeeItem()">Yig'imni saqlash</button><button class="btn danger" onclick="deleteFeeItem()">Yig'imni o'chirish</button></div>
  </div>
</div>

<div id="textModal" class="modal">
  <div class="dialog glass text-dialog">
    <div class="dialog-head"><h3 id="textModalTitle">Izoh matni</h3><button class="btn" onclick="closeModal('textModal')">Yopish</button></div>
    <textarea id="textModalValue" class="large-text" placeholder="Matnni shu yerga yozing. Bu maydonga uzun izoh, huquqiy asos yoki foydalanuvchiga chiqadigan qo'shimcha eslatma kiritish mumkin."></textarea>
    <div class="actions"><button class="btn primary" onclick="saveTextModal()">Matnni qo'llash</button><button class="btn" onclick="closeModal('textModal')">Bekor qilish</button></div>
  </div>
</div>

<div id="importEditModal" class="modal">
  <div class="dialog glass text-dialog">
    <div class="dialog-head"><h3 id="importEditTitle">Import o'zgarishini tahrirlash</h3><button class="btn" onclick="closeModal('importEditModal')">Yopish</button></div>
    <input id="importEditId" type="hidden" />
    <div id="importCountryFields" class="form-grid">
      <div class="field full"><label>Davlat nomi</label><input id="importCountryName" /></div>
    </div>
    <div id="importRuleFields" class="form-grid">
      <div class="field"><label>Ruxsatnoma</label><select id="importPermission"><option value="1">Majburiy</option><option value="2">Kerak emas</option><option value="3">Taqiqlangan</option></select></div>
      <div class="field"><label>Yig'im</label><select id="importDues" onchange="toggleImportAmount()"><option value="0">Belgilanmagan</option><option value="1">Undiriladi</option><option value="2">Undirilmaydi</option><option value="3">Ruxsat turiga bog'liq</option></select></div>
      <div id="importAmountField" class="field"><label>USD stavka</label><input id="importAmount" placeholder="400 yoki 100/150/200" /></div>
      <div class="field"><label>Tashuv turi (ruscha)</label><input id="importVidName" /></div>
      <div class="field full"><label>Admin izohi</label><textarea id="importAdminNote"></textarea></div>
      <div class="field full"><label>Foydalanuvchiga izoh (UZ)</label><textarea id="importNoteUz"></textarea></div>
      <div class="field full"><label>Foydalanuvchiga izoh (RU)</label><textarea id="importNoteRu"></textarea></div>
      <div class="field full"><label>Foydalanuvchiga izoh (EN)</label><textarea id="importNoteEn"></textarea></div>
    </div>
    <div class="actions"><button class="btn primary" onclick="saveImportEdit()">✅ Tahrirni saqlash</button><button class="btn" onclick="closeModal('importEditModal')">Bekor qilish</button></div>
  </div>
</div>

<div class="toast" id="toast"></div>
<script>
const vidLabels={"1":"Ikki tomonlama: O'zbekistondan","2":"Ikki tomonlama: O'zbekistonga","3":"Tranzit","4":"Uchinchi davlatga","5":"Uchinchi davlatdan","6":"Ichki tashuv","7":"Yuksiz kirish","8":"Yuksiz tranzit"};
const vidIcons={"1":"🚚🇺🇿","2":"🏁🇺🇿","3":"🔁🚛","4":"🌍➡️","5":"🌍⬅️","6":"🚫🛣️","7":"⭕🚚","8":"⭕🔁"};
const permissionText={"1":"⚠️ ruxsat kerak","2":"✅ ruxsat kerak emas","3":"⛔ taqiqlangan"};
const duesText={"0":"⚪ belgilanmagan","1":"💵 yig'im bor","2":"✅ yig'im yo'q","3":"🔎 ruxsat turiga bog'liq"};
let permissionData={countries:[]}; let countryCache={}; let activeDirection='import'; let feeItems=[]; let selectedCountry=null; let lastCountryListScreen='dazvol'; let editingTextFieldId='';
let importJobId=''; let importChanges=[]; let importPollTimer=null;
const searchTimers={dazvol:null,countries:null};
function queueSearch(section){clearTimeout(searchTimers[section]);searchTimers[section]=setTimeout(()=>{(section==='dazvol'?loadDazvol():loadCountries()).catch(e=>toast(e.message))},300)}
const esc=v=>String(v??'').replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]));
function toast(t){const el=document.getElementById('toast');el.textContent=t;el.style.display='block';setTimeout(()=>el.style.display='none',2500)}
async function api(path,opts={}){const r=await fetch(path,{headers:{'Content-Type':'application/json'},...opts}); if(r.status===401){location.href='/admin';return} const text=await r.text(); let d; try{d=JSON.parse(text)}catch(e){d={ok:false,error:text||'Server javobi xato'}} if(!r.ok||d.ok===false) throw new Error(d.error||'Xatolik'); return d}
function showScreen(name,title=''){document.querySelectorAll('.screen').forEach(s=>s.classList.remove('active'));document.getElementById(name).classList.add('active');pageTitle.textContent=title||document.querySelector(`.nav button[data-screen="${name}"]`)?.textContent.trim()||'Davlat';document.querySelectorAll('.nav button').forEach(x=>x.classList.toggle('active',x.dataset.screen===name));if(name==='fees')loadFeeItems();if(name==='governance')loadGovernance();}
document.querySelectorAll('.nav button').forEach(b=>b.onclick=()=>showScreen(b.dataset.screen,b.textContent.trim()));
document.querySelectorAll('.fee-tab').forEach(b=>b.onclick=()=>{document.querySelectorAll('.fee-tab').forEach(x=>x.classList.remove('active'));b.classList.add('active');activeDirection=b.dataset.direction;loadFeeItems();});
function closeModal(id){document.getElementById(id).classList.remove('show')}
function backToCountryList(){showScreen(lastCountryListScreen,lastCountryListScreen==='dazvol'?'📄 Dazvol':'🌍 Davlatlar');(lastCountryListScreen==='dazvol'?loadDazvol():loadCountries()).catch(e=>toast(e.message))}
function pill(text,kind){return `<span class="pill ${kind}">${esc(text)}</span>`}
function rulePills(rules){return Object.entries(rules||{}).map(([vid,r])=>pill(`${vid}: R${r.permission_cd}`,r.permission_cd==='1'?'warn':r.permission_cd==='3'?'bad':'ok')+pill(`Y${r.dues_cd}`,r.dues_cd==='1'?'warn':r.dues_cd==='2'?'ok':'info')).join('')}
function rememberCountries(rows){(rows||[]).forEach(c=>{countryCache[c.code]=c})}
async function loadSummary(){const d=await api('/admin/api/summary');countryCount.textContent=d.countries;ruleCount.textContent=d.rules;exceptionCount.textContent=d.exceptions;bhmValue.textContent=d.bhm;const c=d.metrics?.counters||{};startCount.textContent=c.starts||0;permitCheckCount.textContent=c.permit_checks||0;feeCheckCount.textContent=c.fee_checks||0;errorCount.textContent=c.errors||0}
async function loadDazvol(){const q=encodeURIComponent(dazvolSearch.value||'');permissionData=await api('/admin/api/permission?q='+q);rememberCountries(permissionData.countries);dazvolCards.innerHTML=permissionData.countries.map(countryCard).join('')||'<div class="card glass">Maʼlumot topilmadi</div>'}
async function loadCountrySections(){const dq=dazvolSearch.value||'',cq=countrySearch.value||'';if(dq!==cq){await Promise.all([loadDazvol(),loadCountries()]);return}const d=await api('/admin/api/permission?q='+encodeURIComponent(dq));permissionData=d;rememberCountries(d.countries);const cards=d.countries.map(countryCard).join('')||'<div class="card glass">Maʼlumot topilmadi</div>';dazvolCards.innerHTML=cards;countryCards.innerHTML=cards}
function countryCard(c){return `<button class="card glass" style="text-align:left" onclick="openCountryPage('${esc(c.code)}')"><h3>${esc(c.name_uz)} <span class="muted">(${esc(c.code)})</span></h3><div class="muted">${esc(c.name)}</div><div>${rulePills(c.rules)}</div></button>`}
async function openCountryPage(code=''){const active=document.querySelector('.screen.active');if(active&&active.id!=='countryDetail')lastCountryListScreen=active.id;if(code&&!(countryCache[code]&&countryCache[code]._detail)){try{const d=await api('/admin/api/country/'+encodeURIComponent(code));countryCache[code]=d.country}catch(e){toast(e.message);return}}selectedCountry=countryCache[code]||permissionData.countries.find(c=>c.code===code)||{code:'',name:'',name_uz:'',rules:{},exceptions:[],_detail:true};countryCode.value=selectedCountry.code;countryName.value=selectedCountry.name;countryNameUz.value=selectedCountry.name_uz;countryPageTitle.textContent=selectedCountry.code?`${selectedCountry.name_uz} (${selectedCountry.code})`:'Yangi davlat';renderRulesTable();renderExceptions();showScreen('countryDetail',selectedCountry.code?'Davlat tafsiloti':'Yangi davlat');window.scrollTo({top:0,behavior:'smooth'});}
function textButton(fieldId,label,value){const has=String(value||'').trim().length>0;return `<button type="button" class="text-edit-btn ${has?'has-text':'empty'}" data-target="${esc(fieldId)}" data-label="${esc(label)}">${has?'📝':'✍️'} ${esc(label)}${has?'':' yozish'}</button>`}
function bindTextButtons(){document.querySelectorAll('.text-edit-btn').forEach(btn=>{btn.onclick=()=>openTextEditor(btn.dataset.target,btn.dataset.label)})}
function openTextEditor(fieldId,title){editingTextFieldId=fieldId;textModalTitle.textContent=title||'Izoh matni';const el=document.getElementById(fieldId);textModalValue.value=el?el.value:'';textModal.classList.add('show');setTimeout(()=>textModalValue.focus(),60)}
function saveTextModal(){const el=document.getElementById(editingTextFieldId);if(el)el.value=textModalValue.value;const btn=document.querySelector('[data-target="'+editingTextFieldId+'"]');if(btn){const has=textModalValue.value.trim().length>0;const label=btn.dataset.label||'Izoh';btn.textContent=(has?'📝 ':'✍️ ')+label+(has?'':' yozish');btn.classList.toggle('has-text',has);btn.classList.toggle('empty',!has)}closeModal('textModal');toast("Izoh matni qo'llandi")}
function ruleStatus(r){const p=r.permission_cd||'2';const d=r.dues_cd||'2';const amount=r.dues_amount_usd?` · ${r.dues_amount_usd} USD`:'';return `<div class="status-row">${pill(permissionText[p]||"⚪ ruxsat holati yo'q",p==='1'?'warn':p==='3'?'bad':'ok')}${pill((duesText[d]||"⚪ yig'im holati yo'q")+amount,d==='1'?'warn':d==='2'?'ok':'info')}</div>`}
function renderRulesTable(){const rules=selectedCountry.rules||{};rulesTable.innerHTML=Object.keys(vidLabels).map(vid=>{const r=rules[vid]||{};return `<div class="rule-card glass"><div class="rule-card-head"><div class="rule-title"><div class="transport-icon">${vidIcons[vid]||'🚛'}</div><div><span class="mini">Tashuv turi ${vid}</span><h4>${esc(vidLabels[vid])}</h4>${ruleStatus(r)}</div></div><button class="btn primary" onclick="saveRule('${vid}')">💾 Saqlash</button></div><div class="form-grid"><div class="field"><label>📄 Ruxsatnoma</label>${selectHtml('p'+vid,r.permission_cd||'2',{1:'Majburiy',2:'Kerak emas',3:'Taqiqlangan'})}</div><div class="field"><label>💵 Yig'im</label>${selectHtml('d'+vid,r.dues_cd||'2',{1:'Undiriladi',2:'Undirilmaydi',3:'Ruxsat turiga qarab',0:'Belgilanmagan'})}</div><div class="field"><label>💲 USD stavka</label><input id="a${vid}" value="${esc(r.dues_amount_usd||'')}" placeholder="400 / 100/150/200" /></div><div class="field"><label>🧑‍💼 Admin izoh</label><input type="hidden" id="n${vid}" value="${esc(r.admin_note||'')}" />${textButton('n'+vid,'Admin izoh',r.admin_note)}</div><div class="field full"><label>💬 Foydalanuvchiga chiqadigan izohlar</label><input type="hidden" id="uz${vid}" value="${esc(r.dues_amount_note_uz||'')}" /><input type="hidden" id="ru${vid}" value="${esc(r.dues_amount_note_ru||'')}" /><input type="hidden" id="en${vid}" value="${esc(r.dues_amount_note_en||'')}" /><div class="note-grid">${textButton('uz'+vid,'UZ izoh',r.dues_amount_note_uz)}${textButton('ru'+vid,'RU izoh',r.dues_amount_note_ru)}${textButton('en'+vid,'EN izoh',r.dues_amount_note_en)}</div></div></div></div>`}).join('');Object.keys(vidLabels).forEach(vid=>{const dues=document.getElementById('d'+vid);if(dues)dues.onchange=()=>toggleFeeFields(vid);toggleFeeFields(vid)});bindTextButtons()}
function selectHtml(id,val,opts,onchange=''){return `<select id="${id}" ${onchange?`onchange="${onchange}"`:''}>`+Object.entries(opts).map(([k,v])=>`<option value="${k}" ${String(val)===String(k)?'selected':''}>${v}</option>`).join('')+'</select>'}
function toggleFeeFields(vid){const show=document.getElementById('d'+vid)?.value==='1';const amount=document.getElementById('a'+vid);if(amount)amount.closest('.field').style.display=show?'grid':'none';}
function renderExceptions(){const list=selectedCountry.exceptions||[];exceptionsBox.innerHTML=list.length?list.slice(0,12).map(x=>`<div class="card glass"><b>${esc(x.exception_cd||'')}</b><p class="muted">${esc(x.exception_desc||'')}</p></div>`).join(''):'<div class="card glass muted">Istisno kiritilmagan</div>'}
async function refreshCountry(code){const d=await api('/admin/api/country/'+encodeURIComponent(code));countryCache[code]=d.country;return d.country}
async function saveRule(vid){await api('/admin/api/rule',{method:'POST',body:JSON.stringify({country_code:countryCode.value,vid_cd:vid,permission_cd:document.getElementById('p'+vid).value,dues_cd:document.getElementById('d'+vid).value,dues_amount_usd:document.getElementById('a'+vid).value,dues_amount_note_uz:document.getElementById('uz'+vid).value,dues_amount_note_ru:document.getElementById('ru'+vid).value,dues_amount_note_en:document.getElementById('en'+vid).value,exception_cd:'0',exception_name_ru:'',admin_note:document.getElementById('n'+vid).value})});toast('Qoida qoralamaga saqlandi');const [c]=await Promise.all([refreshCountry(countryCode.value),loadSummary(),loadVersionStatus()]);if(c)openCountryPage(countryCode.value)}
async function saveCountry(){await api('/admin/api/country',{method:'POST',body:JSON.stringify({code:countryCode.value,name:countryName.value,name_uz:countryNameUz.value})});toast('Davlat qoralamaga saqlandi');const [c]=await Promise.all([refreshCountry(countryCode.value),loadSummary(),loadVersionStatus()]);if(c)openCountryPage(countryCode.value)}
async function deleteCountry(){if(!countryCode.value||!confirm('Davlatni o‘chirasizmi?'))return;await api('/admin/api/country/'+countryCode.value,{method:'DELETE'});toast('Davlat o‘chirildi');await loadAll();backToCountryList()}
async function loadCountries(){const q=encodeURIComponent(countrySearch.value||'');const d=await api('/admin/api/permission?q='+q);rememberCountries(d.countries);countryCards.innerHTML=d.countries.map(countryCard).join('')||'<div class="card glass">Maʼlumot topilmadi</div>'}
async function loadFeeItems(){const d=await api('/admin/api/fee-items?direction='+activeDirection);feeItems=d.items;feeCards.innerHTML=feeItems.map(feeCard).join('')||'<div class="card glass">Bu yo‘nalishda yig‘im yo‘q</div>'}
function feeCard(f){return `<button class="card glass" style="text-align:left" onclick="openFeeModal('${esc(f.id)}')"><h3>${esc(f.title)}</h3><div>${pill(f.enabled?'Faol':'O‘chirilgan',f.enabled?'ok':'bad')} ${pill(activeDirection,'info')}</div><p><b>${esc(f.amount)}</b></p><p class="muted">${esc(f.condition)}</p><p class="muted">${esc(f.basis)}</p></button>`}
function openFeeModal(id=''){const f=feeItems.find(x=>x.id===id)||{id:'',title:'',amount:'',condition:'',basis:'',enabled:true};feeId.value=f.id;feeDirection.value=activeDirection;feeTitle.value=f.title;feeAmount.value=f.amount;feeCondition.value=f.condition;feeBasis.value=f.basis;feeEnabled.value=String(f.enabled!==false);feeModalTitle.textContent=f.id?'Yig‘imni tahrirlash':'Yangi yig‘im';feeModal.classList.add('show')}
async function saveFeeItem(){await api('/admin/api/fee-item',{method:'POST',body:JSON.stringify({id:feeId.value,direction:feeDirection.value,title:feeTitle.value,amount:feeAmount.value,condition:feeCondition.value,basis:feeBasis.value,enabled:feeEnabled.value==='true'})});activeDirection=feeDirection.value;closeModal('feeModal');toast('Yig‘im qoralamaga saqlandi');await Promise.all([loadFeeItems(),loadVersionStatus()])}
async function deleteFeeItem(){if(!feeId.value||!confirm('Yig‘imni o‘chirasizmi?'))return;await api(`/admin/api/fee-item/${feeDirection.value}/${feeId.value}`,{method:'DELETE'});closeModal('feeModal');toast('Yig‘im o‘chirildi');await loadFeeItems()}
function setImportProgress(percent,message){const value=Math.max(0,Math.min(100,Math.round(percent)));importProgress.classList.add('show');importProgressBar.style.width=value+'%';importProgressPercent.textContent=value+'%';importProgressText.textContent=message||'Tahlil qilinmoqda'}
function importActionLabel(action){return action==='add'?'➕ Qo\'shiladi':action==='delete'?'🗑️ O\'chiriladi':'🔄 Yangilanadi'}
function importActionKind(action){return action==='add'?'ok':action==='delete'?'bad':'warn'}
function importValueText(change,side){const value=change[side]||{};if(change.kind==='country')return value.name||'—';if(side==='after'&&change.action==='delete')return 'Qoida o\'chiriladi';const permission={1:'Ruxsat majburiy',2:'Ruxsat kerak emas',3:'Tashuv taqiqlangan'};const dues={0:'Yig\'im belgilanmagan',1:'Yig\'im undiriladi',2:'Yig\'im undirilmaydi',3:'Yig\'im ruxsat turiga bog\'liq'};const amount=value.dues_amount_usd?` · ${value.dues_amount_usd} USD`:'';return `${permission[value.permission_cd]||'Ruxsat: —'}<br>${dues[value.dues_cd]||'Yig\'im: —'}${esc(amount)}`}
function renderImportChanges(){const filter=importActionFilter.value||'all';const rows=importChanges.filter(change=>filter==='all'||change.action===filter);importChangesBody.innerHTML=rows.length?rows.map(change=>`<tr class="${change.selected?'':'not-selected'}"><td data-label="Tanlash"><input type="checkbox" ${change.selected?'checked':''} onchange="toggleImportChange('${esc(change.id)}',this.checked)" title="Ushbu o'zgarishni qo'llash" /></td><td data-label="Davlat / tashuv"><div class="change-code">${esc(change.country_code)} · ${esc(change.country_name)}</div><div class="muted">${change.kind==='country'?'Davlat ma\'lumoti':`Tashuv ${esc(change.vid_cd)} · ${esc(change.vid_name)}`}</div></td><td data-label="Amal">${pill(importActionLabel(change.action),importActionKind(change.action))}</td><td data-label="Avvalgi holat"><div class="change-text">${importValueText(change,'before')}</div></td><td data-label="Yangi holat"><div class="change-text">${importValueText(change,'after')}</div></td><td data-label="Tahrirlash">${change.action==='delete'?'<span class="muted">Checkboxni olib tashlab bekor qiling</span>':`<button class="btn" onclick="editImportChange('${esc(change.id)}')">✏️ Tahrirlash</button>`}</td></tr>`).join(''):'<tr><td colspan="6" class="import-empty">Tanlangan filtr bo\'yicha o\'zgarish topilmadi.</td></tr>'}
function toggleImportChange(id,selected){const change=importChanges.find(item=>item.id===id);if(change)change.selected=selected;renderImportChanges()}
function selectImportChanges(selected){importChanges.forEach(change=>change.selected=selected);renderImportChanges()}
function selectSafeImportChanges(){importChanges.forEach(change=>change.selected=change.action!=='delete');renderImportChanges()}
function renderImportPreview(job){importChanges=(job.changes||[]).map(change=>({...change,selected:change.selected!==false,after:{...(change.after||{})}}));const s=job.summary||{};importSummary.innerHTML=`<div class="glass"><b>${s.countries||0}</b><span>Excel davlatlari</span></div><div class="glass"><b>${s.active_rules||0}</b><span>Faol qoidalar</span></div><div class="glass"><b>${s.unchanged_rules||0}</b><span>O'zgarmagan</span></div><div class="glass"><b>${s.add||0}</b><span>Qo'shiladi</span></div><div class="glass"><b>${s.update||0}</b><span>Yangilanadi</span></div><div class="glass"><b>${s.delete||0}</b><span>O'chirish taklifi</span></div><div class="glass"><b>${s.invalid_rows||0}</b><span>Noto'g'ri satr</span></div><div class="glass"><b>${s.duplicates||0}</b><span>Takroriy satr</span></div>`;importPreview.style.display='grid';renderImportChanges();applyImportButton.disabled=importChanges.length===0}
function editImportChange(id){const change=importChanges.find(item=>item.id===id);if(!change||change.action==='delete')return;importEditId.value=id;importEditTitle.textContent=`${change.country_code} · ${change.kind==='country'?'Davlat nomi':'Tashuv '+change.vid_cd}`;const isCountry=change.kind==='country';importCountryFields.style.display=isCountry?'grid':'none';importRuleFields.style.display=isCountry?'none':'grid';if(isCountry){importCountryName.value=change.after.name||''}else{const value=change.after||{};importPermission.value=value.permission_cd||'2';importDues.value=value.dues_cd||'2';importAmount.value=value.dues_amount_usd||'';importVidName.value=value.vid_name_ru||'';importAdminNote.value=value.admin_note||'';importNoteUz.value=value.dues_amount_note_uz||'';importNoteRu.value=value.dues_amount_note_ru||'';importNoteEn.value=value.dues_amount_note_en||'';toggleImportAmount()}importEditModal.classList.add('show')}
function toggleImportAmount(){importAmountField.style.display=importDues.value==='1'?'grid':'none'}
function saveImportEdit(){const change=importChanges.find(item=>item.id===importEditId.value);if(!change)return;if(change.kind==='country'){change.after.name=importCountryName.value.trim()}else{const permissionNames={1:'Обязательно',2:'Не обязательно',3:'Запрещен'};const duesNames={0:'-не выбрано-',1:'Сбор обязательно',2:'Сбор не обязательно',3:'Сбор зависит от вида разрешения'};change.after.permission_cd=importPermission.value;change.after.permission_name_ru=permissionNames[importPermission.value];change.after.dues_cd=importDues.value;change.after.dues_name_ru=duesNames[importDues.value];change.after.dues_amount_usd=importDues.value==='1'?importAmount.value.trim():'';change.after.vid_name_ru=importVidName.value.trim();change.after.admin_note=importAdminNote.value.trim();change.after.dues_amount_note_uz=importNoteUz.value.trim();change.after.dues_amount_note_ru=importNoteRu.value.trim();change.after.dues_amount_note_en=importNoteEn.value.trim()}change.selected=true;closeModal('importEditModal');renderImportChanges();toast('Import o\'zgarishi tahrirlandi')}
function startPermissionImport(){const file=permissionImportFile.files?.[0];if(!file){toast('Avval .xlsx faylni tanlang');return}if(!file.name.toLowerCase().endsWith('.xlsx')){toast('Faqat .xlsx fayl tanlang');return}if(file.size>10*1024*1024){toast('Fayl 10 MB dan oshmasligi kerak');return}clearTimeout(importPollTimer);importPreview.style.display='none';startImportButton.disabled=true;setImportProgress(1,'Excel serverga yuklanmoqda');const form=new FormData();form.append('file',file);const xhr=new XMLHttpRequest();xhr.open('POST','/admin/api/permission-import');xhr.upload.onprogress=event=>{if(event.lengthComputable)setImportProgress(Math.max(1,event.loaded/event.total*20),'Excel serverga yuklanmoqda')};xhr.onerror=()=>{startImportButton.disabled=false;setImportProgress(0,'Faylni yuborib bo\'lmadi');toast('Server bilan aloqa xatosi')};xhr.onload=()=>{let data;try{data=JSON.parse(xhr.responseText)}catch(e){data={ok:false,error:xhr.responseText||'Server javobi xato'}}if(xhr.status===401){location.href='/admin';return}if(xhr.status<200||xhr.status>=300||data.ok===false){startImportButton.disabled=false;setImportProgress(0,data.error||'Import boshlanmadi');toast(data.error||'Import boshlanmadi');return}importJobId=data.job_id;setImportProgress(20,'Excel qoidalari o\'qilmoqda');pollPermissionImport()};xhr.send(form)}
async function pollPermissionImport(){try{const job=await api('/admin/api/permission-import/'+importJobId);if(job.status==='queued'||job.status==='processing'){setImportProgress(20+(job.progress||0)*.8,job.message);importPollTimer=setTimeout(pollPermissionImport,500);return}startImportButton.disabled=false;if(job.status==='error'){setImportProgress(0,job.error||job.message);toast(job.error||'Import tahlilida xatolik');return}setImportProgress(100,job.message||'Taqqoslash tayyor');renderImportPreview(job)}catch(e){startImportButton.disabled=false;setImportProgress(0,e.message);toast(e.message)}}
async function applyPermissionImport(){const selected=importChanges.filter(change=>change.selected);if(!selected.length){toast('Kamida bitta o\'zgarishni tanlang');return}const deletes=selected.filter(change=>change.action==='delete').length;if(deletes&&!confirm(`${deletes} ta qoida o'chiriladi. Davom etasizmi?`))return;applyImportButton.disabled=true;try{const result=await api('/admin/api/permission-import/'+importJobId+'/apply',{method:'POST',body:JSON.stringify({changes:selected.map(change=>({id:change.id,after:change.after}))})});setImportProgress(100,`${result.applied_count} ta o'zgarish qo'llandi`);toast(`${result.applied_count} ta o'zgarish muvaffaqiyatli qo'llandi`);importChanges.forEach(change=>change.selected=false);renderImportChanges();await loadAll()}catch(e){toast(e.message)}finally{applyImportButton.disabled=false}}
async function loadVersionStatus(){const d=await api('/admin/api/rule-version/status');const storage=d.persistent?'':' · mahalliy saqlash';draftBadge.textContent=(d.dirty?`🟡 Qoralama · faol v${d.active_version||0}`:`🟢 E'lon qilingan · v${d.active_version||0}`)+storage;draftBadge.className='pill '+(d.dirty||!d.persistent?'warn':'ok');return d}
async function publishDraft(){const status=await loadVersionStatus();if(!status.dirty){toast('E\'lon qilinmagan o\'zgarish yo\'q');return}if(!confirm('Qoralamadagi barcha o\'zgarishlar bot foydalanuvchilariga e\'lon qilinsinmi?'))return;const d=await api('/admin/api/rule-version/publish',{method:'POST',body:JSON.stringify({source:'admin-panel'})});toast(`v${d.version_no} faol qoida sifatida e'lon qilindi`);await Promise.all([loadVersionStatus(),loadGovernance()])}
async function discardDraft(){const status=await loadVersionStatus();if(!status.dirty){toast('Bekor qilinadigan qoralama yo\'q');return}if(!confirm('Qoralamadagi barcha e\'lon qilinmagan o\'zgarishlar bekor qilinsinmi?'))return;await api('/admin/api/rule-version/discard',{method:'POST',body:'{}'});toast('Qoralama bekor qilindi');countryCache={};await loadAll()}
async function loadGovernance(){const [versions,audit]=await Promise.all([api('/admin/api/rule-versions'),api('/admin/api/audit')]);versionsBox.innerHTML=versions.versions.map(v=>`<div class="card glass"><h3>${v.status==='active'?'🟢':'⚪'} Versiya ${esc(v.version_no)}</h3><div class="muted">${esc(v.created_at||'')} · ${esc(v.created_by||'')}</div><p>${esc(v.source||'')}</p>${v.status==='active'?pill('Faol','ok'):`<button class="btn" onclick="rollbackVersion(${Number(v.version_no)})">↩️ Qayta e'lon qilish</button>`}</div>`).join('')||'<div class="card glass muted">Versiya topilmadi</div>';auditBody.innerHTML=audit.items.map(item=>`<tr><td>${esc(item.created_at||'')}</td><td>${esc(item.action||'')}</td><td>${esc(item.actor||'')}</td><td><code>${esc(JSON.stringify(item.details||{}))}</code></td></tr>`).join('')||'<tr><td colspan="4">Audit yozuvi yo\'q</td></tr>'}
async function rollbackVersion(version){if(!confirm(`Versiya ${version} qoidalarini qayta faol qilishni tasdiqlaysizmi?`))return;const d=await api('/admin/api/rule-versions/'+version+'/rollback',{method:'POST',body:'{}'});toast(`Rollback bajarildi. Yangi faol versiya: ${d.version_no}`);countryCache={};await loadAll();await loadGovernance()}
async function logout(){await fetch('/admin/logout',{method:'POST'});location.href='/admin'}
async function loadAll(){await Promise.all([loadSummary(),loadCountrySections(),loadFeeItems(),loadVersionStatus()])}
loadAll().catch(e=>toast(e.message));
</script>
</body></html>"""


def setup_admin_routes(app: web.Application, settings: Settings) -> None:
    permission_write_lock = asyncio.Lock()
    version_store = RuleVersionStore(settings.user_database_url, settings.permission_rules_path.parent)

    def permission_admin_path() -> Path:
        return _ensure_draft(settings.permission_rules_path)

    def fees_admin_path() -> Path:
        return _ensure_draft(settings.fees_rules_path)

    async def initialize_rule_versions(_: web.Application) -> None:
        try:
            await version_store.initialize(settings.permission_rules_path, settings.fees_rules_path)
        except Exception:
            logger.exception("PostgreSQL rule version storage failed; local version storage will be used")
            await version_store.close()
            version_store.database_url = ""
            version_store.pool = None
            await version_store.initialize(settings.permission_rules_path, settings.fees_rules_path)
        permission_admin_path()
        fees_admin_path()

    async def close_rule_versions(_: web.Application) -> None:
        await version_store.close()

    async def audit(action: str, details: dict[str, Any]) -> None:
        try:
            await version_store.audit(action, settings.admin_username, details)
        except Exception:
            logger.exception("Admin audit could not be saved: %s", action)

    async def admin_index(request: web.Request) -> web.Response:
        if not _is_authenticated(request, settings):
            return web.Response(text=_login_page(), content_type="text/html")
        return web.Response(text=_admin_page_v2(), content_type="text/html")

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
        permission = _read_json_view(permission_admin_path())
        fees = _read_json_view(fees_admin_path())
        rule_count = sum(len(v) for v in permission.get("rules", {}).values())
        exception_count = sum(len(v) for v in permission.get("exceptions", {}).values())
        return web.json_response(
            {
                "ok": True,
                "countries": len(permission.get("countries", {})),
                "rules": rule_count,
                "exceptions": exception_count,
                "bhm": fees.get("bhm", {}).get("value", settings.bhm_value),
                "metrics": metrics.snapshot(),
            }
        )

    async def permission_list(request: web.Request) -> web.Response:
        _require_admin(request, settings)
        data = _read_json_view(permission_admin_path())
        query = str(request.query.get("q") or "").strip().lower()
        countries = []
        for code, name in sorted(data.get("countries", {}).items()):
            name_uz = _country_uz_name(data, code, name)
            name_latin = transliterate_cyrillic_to_latin(str(name))
            haystack = f"{code} {name} {name_uz} {name_latin}".lower()
            if query and query not in haystack:
                continue
            countries.append(
                {
                    "code": code,
                    "name": name,
                    "name_uz": name_uz,
                    "rules": {
                        vid: {
                            "permission_cd": rule.get("permission_cd", "2"),
                            "dues_cd": rule.get("dues_cd", "2"),
                            "dues_amount_usd": rule.get("dues_amount_usd", ""),
                        }
                        for vid, rule in data.get("rules", {}).get(code, {}).items()
                    },
                    "_detail": False,
                }
            )
            if len(countries) >= 80:
                break
        return web.json_response({"ok": True, "countries": countries, "vid_types": data.get("vid_types", {})})

    async def country_detail(request: web.Request) -> web.Response:
        _require_admin(request, settings)
        code = _code(request.match_info["code"])
        data = _read_json_view(permission_admin_path())
        name = data.get("countries", {}).get(code)
        if not name:
            return _json_error("Davlat topilmadi.", 404)
        return web.json_response(
            {
                "ok": True,
                "country": {
                    "code": code,
                    "name": name,
                    "name_uz": _country_uz_name(data, code, name),
                    "rules": data.get("rules", {}).get(code, {}),
                    "exceptions": data.get("exceptions", {}).get(code, []),
                    "_detail": True,
                },
            }
        )

    async def permission_full(request: web.Request) -> web.Response:
        _require_admin(request, settings)
        return web.json_response({"ok": True, "permission": _read_json_view(permission_admin_path())})

    async def save_permission_full(request: web.Request) -> web.Response:
        _require_admin(request, settings)
        body = await request.json()
        permission = body.get("permission")
        if not isinstance(permission, dict) or "countries" not in permission or "rules" not in permission:
            return _json_error("Permission JSON tuzilmasi noto'g'ri.")
        permission.setdefault("source", {})["last_admin_update"] = int(time.time())
        _write_json(permission_admin_path(), permission)
        await audit("draft_permission_full", {})
        return web.json_response({"ok": True})

    async def save_country(request: web.Request) -> web.Response:
        _require_admin(request, settings)
        body = await request.json()
        code = _code(body.get("code"))
        name = str(body.get("name") or "").strip()
        name_uz = str(body.get("name_uz") or "").strip()
        if len(name) < 2:
            return _json_error("Davlat nomi kiritilmadi.")
        data = _read_json(permission_admin_path())
        data.setdefault("countries", {})[code] = name
        if name_uz:
            data.setdefault("country_labels", {}).setdefault(code, {})["uz"] = name_uz
        data.setdefault("rules", {}).setdefault(code, {})
        data.setdefault("source", {})["last_admin_update"] = int(time.time())
        _write_json(permission_admin_path(), data)
        await audit("draft_country_save", {"country_code": code})
        return web.json_response({"ok": True, "code": code})

    async def delete_country(request: web.Request) -> web.Response:
        _require_admin(request, settings)
        code = _code(request.match_info["code"])
        data = _read_json(permission_admin_path())
        data.get("countries", {}).pop(code, None)
        data.get("rules", {}).pop(code, None)
        data.get("exceptions", {}).pop(code, None)
        data.setdefault("source", {})["last_admin_update"] = int(time.time())
        _write_json(permission_admin_path(), data)
        await audit("draft_country_delete", {"country_code": code})
        return web.json_response({"ok": True})

    async def save_rule(request: web.Request) -> web.Response:
        _require_admin(request, settings)
        body = await request.json()
        code = _code(body.get("country_code"))
        data = _read_json(permission_admin_path())
        if code not in data.get("countries", {}):
            return _json_error("Avval davlatni qo'shing.")
        rule = _rule_payload(body, data)
        data.setdefault("rules", {}).setdefault(code, {})[rule["vid_cd"]] = rule
        data.setdefault("source", {})["last_admin_update"] = int(time.time())
        _write_json(permission_admin_path(), data)
        await audit("draft_rule_save", {"country_code": code, "vid_cd": rule["vid_cd"]})
        return web.json_response({"ok": True, "rule": rule})

    async def delete_rule(request: web.Request) -> web.Response:
        _require_admin(request, settings)
        code = _code(request.match_info["code"])
        vid_cd = _vid(request.match_info["vid"])
        data = _read_json(permission_admin_path())
        data.setdefault("rules", {}).setdefault(code, {}).pop(vid_cd, None)
        data.setdefault("source", {})["last_admin_update"] = int(time.time())
        _write_json(permission_admin_path(), data)
        await audit("draft_rule_delete", {"country_code": code, "vid_cd": vid_cd})
        return web.json_response({"ok": True})

    async def fees(request: web.Request) -> web.Response:
        _require_admin(request, settings)
        return web.json_response({"ok": True, "fees": _read_json_view(fees_admin_path())})

    async def save_fees(request: web.Request) -> web.Response:
        _require_admin(request, settings)
        body = await request.json()
        fees_data = body.get("fees")
        if not isinstance(fees_data, dict) or "entry_fee" not in fees_data:
            return _json_error("Yig'im JSON tuzilmasi noto'g'ri.")
        fees_data.setdefault("source", {})["last_admin_update"] = int(time.time())
        _write_json(fees_admin_path(), fees_data)
        await audit("draft_fees_full", {})
        return web.json_response({"ok": True})

    async def fee_items(request: web.Request) -> web.Response:
        _require_admin(request, settings)
        direction = _fee_direction(request.query.get("direction") or "import")
        fees_data = _read_json(fees_admin_path())
        before = json.dumps(fees_data, ensure_ascii=False, sort_keys=True)
        items = _fee_items(fees_data)
        if json.dumps(fees_data, ensure_ascii=False, sort_keys=True) != before:
            _write_json(fees_admin_path(), fees_data)
        return web.json_response({"ok": True, "direction": direction, "items": items[direction]})

    async def save_fee_item(request: web.Request) -> web.Response:
        _require_admin(request, settings)
        body = await request.json()
        direction = _fee_direction(body.get("direction"))
        item = _fee_item_payload(body)
        fees_data = _read_json(fees_admin_path())
        items = _fee_items(fees_data)
        current = [row for row in items[direction] if row.get("id") != item["id"]]
        current.append(item)
        items[direction] = current
        fees_data.setdefault("source", {})["last_admin_update"] = int(time.time())
        _write_json(fees_admin_path(), fees_data)
        await audit("draft_fee_save", {"direction": direction, "item_id": item["id"]})
        return web.json_response({"ok": True, "item": item})

    async def delete_fee_item(request: web.Request) -> web.Response:
        _require_admin(request, settings)
        direction = _fee_direction(request.match_info["direction"])
        item_id = str(request.match_info["item_id"])
        fees_data = _read_json(fees_admin_path())
        items = _fee_items(fees_data)
        items[direction] = [row for row in items[direction] if str(row.get("id")) != item_id]
        fees_data.setdefault("source", {})["last_admin_update"] = int(time.time())
        _write_json(fees_admin_path(), fees_data)
        await audit("draft_fee_delete", {"direction": direction, "item_id": item_id})
        return web.json_response({"ok": True})

    async def rule_version_status(request: web.Request) -> web.Response:
        _require_admin(request, settings)
        active = await version_store.get_active()
        draft_permission = _read_json_view(permission_admin_path())
        draft_fees = _read_json_view(fees_admin_path())
        dirty = not active or (
            draft_permission != active.get("permission")
            or draft_fees != active.get("fees")
        )
        return web.json_response(
            {
                "ok": True,
                "dirty": dirty,
                "active_version": active.get("version_no") if active else None,
                "active_source": active.get("source") if active else "",
                "active_at": active.get("created_at") if active else "",
                "persistent": version_store.pool is not None,
            }
        )

    async def publish_rule_draft(request: web.Request) -> web.Response:
        _require_admin(request, settings)
        body = await request.json() if request.can_read_body else {}
        source = str(body.get("source") or "admin-panel").strip()[:200]
        async with permission_write_lock:
            permission = _read_json(permission_admin_path())
            fees_data = _read_json(fees_admin_path())
            summary = {
                "countries": len(permission.get("countries", {})),
                "rules": sum(len(item) for item in permission.get("rules", {}).values()),
                "fee_items": sum(len(item) for item in fees_data.get("admin_fee_items", {}).values()),
            }
            snapshot = await version_store.publish(
                permission,
                fees_data,
                actor=settings.admin_username,
                source=source,
                summary=summary,
            )
        return web.json_response(
            {"ok": True, "version_no": snapshot["version_no"], "message": "Qoidalar e'lon qilindi."}
        )

    async def discard_rule_draft(request: web.Request) -> web.Response:
        _require_admin(request, settings)
        async with permission_write_lock:
            active = await version_store.get_active()
            if not active:
                return _json_error("Faol qoida versiyasi topilmadi.", 404)
            _write_json(permission_admin_path(), active["permission"])
            _write_json(fees_admin_path(), active["fees"])
            await audit("discard_draft", {"active_version": active.get("version_no")})
        return web.json_response({"ok": True})

    async def rule_versions(request: web.Request) -> web.Response:
        _require_admin(request, settings)
        return web.json_response({"ok": True, "versions": await version_store.list_versions(30)})

    async def rollback_rule_version(request: web.Request) -> web.Response:
        _require_admin(request, settings)
        try:
            version_no = int(request.match_info["version_no"])
        except ValueError:
            return _json_error("Versiya raqami noto'g'ri.")
        async with permission_write_lock:
            try:
                snapshot = await version_store.rollback(version_no, settings.admin_username)
            except ValueError as exc:
                return _json_error(str(exc), 404)
            _write_json(permission_admin_path(), snapshot["permission"])
            _write_json(fees_admin_path(), snapshot["fees"])
        return web.json_response({"ok": True, "version_no": snapshot["version_no"]})

    async def admin_audit(request: web.Request) -> web.Response:
        _require_admin(request, settings)
        return web.json_response({"ok": True, "items": await version_store.list_audit(80)})

    async def start_permission_import(request: web.Request) -> web.Response:
        _require_admin(request, settings)
        _cleanup_import_jobs()
        draft_path = permission_admin_path()
        if not request.content_type.startswith("multipart/"):
            return _json_error("Excel fayli multipart shaklida yuborilishi kerak.")

        reader = await request.multipart()
        field = await reader.next()
        if field is None or field.name != "file":
            return _json_error("Import uchun Excel fayli tanlanmagan.")
        filename = Path(field.filename or "qoidalar.xlsx").name
        if Path(filename).suffix.lower() != ".xlsx":
            return _json_error("Faqat .xlsx formatidagi fayl qabul qilinadi.")

        import_dir = settings.permission_rules_path.parent / ".imports"
        import_dir.mkdir(parents=True, exist_ok=True)
        job_id = uuid.uuid4().hex
        temp_path = import_dir / f"{job_id}.xlsx"
        size = 0
        try:
            with temp_path.open("wb") as output:
                while True:
                    chunk = await field.read_chunk(size=64 * 1024)
                    if not chunk:
                        break
                    size += len(chunk)
                    if size > MAX_IMPORT_FILE_BYTES:
                        raise PermissionImportError("Excel fayli 10 MB dan oshmasligi kerak.")
                    output.write(chunk)
        except Exception as exc:
            temp_path.unlink(missing_ok=True)
            if isinstance(exc, PermissionImportError):
                return _json_error(str(exc), 413)
            raise
        if size == 0:
            temp_path.unlink(missing_ok=True)
            return _json_error("Tanlangan Excel fayli bo'sh.")

        job: dict[str, Any] = {
            "job_id": job_id,
            "status": "queued",
            "progress": 0,
            "message": "Import navbatga qo'yildi",
            "filename": filename,
            "created_at": time.time(),
            "base_mtime_ns": draft_path.stat().st_mtime_ns,
            "changes": [],
            "summary": {},
            "error": "",
        }
        IMPORT_JOBS[job_id] = job

        async def process_import() -> None:
            job["status"] = "processing"

            def update_progress(percent: int, message: str) -> None:
                job["progress"] = percent
                job["message"] = message

            try:
                preview = await asyncio.to_thread(
                    build_permission_import_preview,
                    temp_path,
                    draft_path,
                    filename,
                    update_progress,
                )
                job["changes"] = preview["changes"]
                job["summary"] = preview["summary"]
                job["status"] = "ready"
                job["progress"] = 100
                job["message"] = "Taqqoslash tayyor"
            except Exception as exc:
                job["status"] = "error"
                job["error"] = str(exc)
                job["message"] = "Import tahlilida xatolik"
            finally:
                temp_path.unlink(missing_ok=True)

        task = asyncio.create_task(process_import())
        IMPORT_TASKS.add(task)
        task.add_done_callback(IMPORT_TASKS.discard)
        return web.json_response({"ok": True, "job_id": job_id, "filename": filename}, status=202)

    async def permission_import_status(request: web.Request) -> web.Response:
        _require_admin(request, settings)
        _cleanup_import_jobs()
        job = IMPORT_JOBS.get(request.match_info["job_id"])
        if not job:
            return _json_error("Import jarayoni topilmadi yoki muddati tugagan.", 404)
        return web.json_response(_import_job_response(job))

    async def apply_permission_import(request: web.Request) -> web.Response:
        _require_admin(request, settings)
        job = IMPORT_JOBS.get(request.match_info["job_id"])
        if not job:
            return _json_error("Import jarayoni topilmadi yoki muddati tugagan.", 404)
        if job.get("status") != "ready":
            return _json_error("Import natijasi hali qo'llashga tayyor emas.", 409)
        body = await request.json()
        submitted_changes = body.get("changes")
        if not isinstance(submitted_changes, list) or not submitted_changes:
            return _json_error("Kamida bitta o'zgarishni tanlang.")
        if len(submitted_changes) > len(job.get("changes", [])):
            return _json_error("Tanlangan o'zgarishlar soni noto'g'ri.")

        async with permission_write_lock:
            draft_path = permission_admin_path()
            current_mtime_ns = draft_path.stat().st_mtime_ns
            if current_mtime_ns != job.get("base_mtime_ns"):
                return _json_error(
                    "Taqqoslashdan keyin qoidalar o'zgargan. Excelni qayta tahlil qiling.",
                    409,
                )
            data = _read_json(draft_path)
            backup_path = draft_path.with_name(
                draft_path.stem + ".before-import.json"
            )
            _write_json(backup_path, data)
            try:
                applied_count = apply_permission_import_changes(
                    data,
                    job.get("changes", []),
                    submitted_changes,
                    str(job.get("filename") or "import.xlsx"),
                )
            except PermissionImportError as exc:
                return _json_error(str(exc))
            data.setdefault("source", {})["last_admin_update"] = int(time.time())
            _write_json(draft_path, data)
            await audit(
                "draft_excel_import",
                {"filename": job.get("filename"), "applied_count": applied_count},
            )
            job["status"] = "applied"
            job["message"] = "Tanlangan o'zgarishlar qo'llandi"
            job["applied_count"] = applied_count
            job["base_mtime_ns"] = draft_path.stat().st_mtime_ns
        return web.json_response(_import_job_response(job))

    app.router.add_get("/admin", admin_index)
    app.router.add_get("/admin/dashboard", admin_index)
    app.router.add_post("/admin/login", login)
    app.router.add_post("/admin/logout", logout)
    app.router.add_get("/admin/api/summary", summary)
    app.router.add_get("/admin/api/permission", permission_list)
    app.router.add_get("/admin/api/country/{code}", country_detail)
    app.router.add_get("/admin/api/permission/full", permission_full)
    app.router.add_post("/admin/api/permission/full", save_permission_full)
    app.router.add_post("/admin/api/country", save_country)
    app.router.add_delete("/admin/api/country/{code}", delete_country)
    app.router.add_post("/admin/api/rule", save_rule)
    app.router.add_delete("/admin/api/rule/{code}/{vid}", delete_rule)
    app.router.add_get("/admin/api/fees", fees)
    app.router.add_post("/admin/api/fees", save_fees)
    app.router.add_get("/admin/api/fee-items", fee_items)
    app.router.add_post("/admin/api/fee-item", save_fee_item)
    app.router.add_delete("/admin/api/fee-item/{direction}/{item_id}", delete_fee_item)
    app.router.add_post("/admin/api/permission-import", start_permission_import)
    app.router.add_get("/admin/api/permission-import/{job_id}", permission_import_status)
    app.router.add_post("/admin/api/permission-import/{job_id}/apply", apply_permission_import)
    app.router.add_get("/admin/api/rule-version/status", rule_version_status)
    app.router.add_post("/admin/api/rule-version/publish", publish_rule_draft)
    app.router.add_post("/admin/api/rule-version/discard", discard_rule_draft)
    app.router.add_get("/admin/api/rule-versions", rule_versions)
    app.router.add_post("/admin/api/rule-versions/{version_no}/rollback", rollback_rule_version)
    app.router.add_get("/admin/api/audit", admin_audit)
    app.on_startup.append(initialize_rule_versions)
    app.on_cleanup.append(close_rule_versions)

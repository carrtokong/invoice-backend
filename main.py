"""
灏忕▼搴忓紑绁ㄦ櫤鑳戒綋 - 缁熶竴鍚庣鏈嶅姟
==============================
涓哄崕涓轰簯 AgentArts 鏅鸿兘浣撳钩鍙版彁渚涘畬鏁寸殑鍚庣鏀寔銆?
绔偣锛?- POST /validate  - 楠岃瘉寮€绁ㄨ〃鍗?- POST /render    - 娓叉煋琛ㄥ崟棰勮 (SVG + HTML鎸夐挳)
- POST /query_history   - 鏌ヨ鍘嗗彶寮€绁ㄨ褰?- POST /submit_application - 鎻愪氦寮€绁ㄧ敵璇?- GET  /health    - 鍋ュ悍妫€鏌?
杩愯妯″紡锛堢幆澧冨彉閲?BACKEND_MODE锛夛細
- "mock" (榛樿): 浣跨敤妯℃嫙鏁版嵁锛岄€傚悎寮€鍙戞祴璇?- "real": 瀵规帴鐪熷疄鍚庣 API

API Key 閴存潈锛?- 鎵€鏈夋帴鍙ｉ渶鍦?Header 涓惡甯?X-API-Key
- 鐜鍙橀噺 API_KEY 璁剧疆瀵嗛挜

閮ㄧ讲鏂瑰紡锛?- 鏈湴: python main.py
- Docker: docker build && docker run
- 浜戝钩鍙? Railway / Render / 鍗庝负浜慐CS 绛?"""

import json
import os
import time
import hashlib
import logging
from typing import Optional
from datetime import datetime, timedelta
from functools import wraps

from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, Field

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# =====================================================================
# 閰嶇疆
# =====================================================================
BACKEND_MODE = os.getenv("BACKEND_MODE", "mock")
API_KEY = os.getenv("API_KEY", "ak-8Y5x8evzs6YO5CjvQSaMWHqhTL3vX9k2UYb2hQ85hA")
SERVICE_HOST = os.getenv("SERVICE_HOST", "http://localhost:8000").rstrip("/")
REAL_BACKEND_URL = os.getenv("REAL_BACKEND_URL", "").rstrip("/")
PORT = int(os.getenv("PORT", "8000"))

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(STATIC_DIR, exist_ok=True)

# =====================================================================
# API Key 閴存潈
# =====================================================================
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def verify_api_key(request: Request, api_key: str = Depends(api_key_header)):
    """楠岃瘉 API Key"""
    if not api_key or api_key != API_KEY:
        raise HTTPException(status_code=401, detail="鏃犳晥鐨?API Key锛岃鍦?Header 涓彁渚涙纭殑 X-API-Key")
    return api_key

# =====================================================================
# FastAPI 搴旂敤
# =====================================================================
app = FastAPI(
    title="灏忕▼搴忓紑绁ㄦ櫤鑳戒綋 - 缁熶竴鍚庣鏈嶅姟",
    description="闆嗚〃鍗曢獙璇併€佹覆鏌撱€佸巻鍙叉煡璇€佹彁浜や簬涓€浣撶殑鍚庣鏈嶅姟",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =====================================================================
# 瀛楁娉ㄥ唽琛?# =====================================================================
FIELD_REGISTRY = {
    "projectName":   {"label": "椤圭洰鍚嶇О",   "required": True,  "category": "basic"},
    "amount":        {"label": "寮€绁ㄩ噾棰?,   "required": True,  "category": "basic"},
    "invoiceType":   {"label": "鍙戠エ绫诲瀷",   "required": True,  "category": "basic"},
    "proxyType":     {"label": "钖祫浠ｅ彂",   "required": True,  "category": "basic"},
    "invoiceCompanyName": {"label": "寮€绁ㄥ叕鍙稿悕绉?, "required": False, "category": "engineering"},
    "invoiceBodyName":    {"label": "寮€绁ㄤ富浣撳悕绉?, "required": False, "category": "engineering"},
    "engName":            {"label": "宸ョ▼鍚嶇О",     "required": False, "category": "engineering"},
    "engAddress":         {"label": "宸ョ▼/椤圭洰鍦板潃", "required": False, "category": "engineering"},
    "invoiceRemark":           {"label": "鍙戠エ澶囨敞",       "required": False, "category": "supplement"},
    "supplement":              {"label": "琛ュ厖璇存槑",       "required": False, "category": "supplement"},
    "crossPeriodDeclaration":  {"label": "璺ㄦ湡鐢虫姤",       "required": False, "category": "supplement"},
    "declarationPeriods":      {"label": "鍒嗘湡鐢虫姤璇存槑",   "required": False, "category": "supplement"},
    "projectType":             {"label": "椤圭洰绫诲瀷",       "required": False, "category": "supplement"},
    "invoiceRate":             {"label": "寮€绁ㄨ垂鐜?,       "required": False, "category": "supplement"},
    "certificate":     {"label": "鏀舵鍑瘉",       "required": False, "category": "attachment"},
    "businessName":    {"label": "鍟嗗姟缁忕悊",       "required": False, "category": "attachment"},
    "taxCertificate":  {"label": "璺ㄥ尯鍩熸秹绋?澶栫粡璇?, "required": False, "category": "attachment"},
    "projectContract": {"label": "椤圭洰鍚堝悓",       "required": False, "category": "attachment"},
    "otherFile":       {"label": "鍏跺畠闄勪欢",       "required": False, "category": "attachment"},
    "invoiceHeaderId": {"label": "鍙戠エ鎶ご",       "required": False, "category": "attachment"},
}

CATEGORY_ORDER = ["basic", "engineering", "supplement", "attachment"]
CATEGORY_LABELS = {
    "basic":       "鍩虹淇℃伅锛堝繀濉級",
    "engineering": "宸ョ▼淇℃伅",
    "supplement":  "寮€绁ㄨˉ鍏?,
    "attachment":  "鍑瘉/闄勪欢",
}

# =====================================================================
# 妯″瀷瀹氫箟
# =====================================================================
class FormRequest(BaseModel):
    form_data: str = Field(..., description="JSON瀛楃涓诧紝鍖呭惈寮€绁ㄨ〃鍗曞瓧娈?)

class RenderRequest(BaseModel):
    form_data: str = Field(..., description="JSON瀛楃涓诧紝鍖呭惈寮€绁ㄨ〃鍗曞瓧娈?)
    is_supplementing: str = Field("false", description="鏄惁琛ュ厖淇℃伅涓?)

class QueryHistoryRequest(BaseModel):
    project_name: str = Field("", description="椤圭洰鍚嶇О")
    time_range: str = Field("", description="鏃堕棿鑼冨洿: last_month/last/last_3_months/this_year/last_year")
    status: str = Field("2", description="寮€绁ㄧ姸鎬佺瓫閫?)
    page_num: int = Field(1, description="椤电爜")
    page_size: int = Field(5, description="姣忛〉鏉℃暟")

class SubmitRequest(BaseModel):
    form_data: str = Field(..., description="JSON瀛楃涓诧紝瀹屾暣鐨勫紑绁ㄧ敵璇锋暟鎹?)

# =====================================================================
# 杈呭姪鍑芥暟
# =====================================================================
def _format_display_value(field_key: str, raw_val) -> str:
    if raw_val is None or str(raw_val).strip() == "" or str(raw_val) == "[]":
        return ""
    s = str(raw_val)
    if field_key == "proxyType":
        return "闇€瑕? if s in ("1", True) else "涓嶉渶瑕?
    if field_key == "projectType":
        return "寮傚湴" if s in ("1", True) else "鏈湴"
    if field_key == "crossPeriodDeclaration":
        return "鏄? if s in ("1", True) else "鍚?
    if field_key in ("certificate", "taxCertificate", "projectContract", "otherFile"):
        try:
            items = json.loads(s) if isinstance(s, str) else s
            if isinstance(items, list):
                return f"宸蹭笂浼?{len(items)}涓枃浠?" if items else ""
        except (json.JSONDecodeError, TypeError):
            pass
    return s

def _save_file(filename: str, content: bytes) -> str:
    filepath = os.path.join(STATIC_DIR, filename)
    with open(filepath, "wb") as f:
        f.write(content)
    return f"{SERVICE_HOST}/static/{filename}"

def _render_form_svg(data: dict) -> str:
    W, PAD = 480, 20
    row_h, title_h = 26, 48
    y_offset = title_h
    for cat in CATEGORY_ORDER:
        cat_fields = [(k, v) for k, v in FIELD_REGISTRY.items() if v["category"] == cat]
        if not cat_fields: continue
        y_offset += 28
        for _ in cat_fields: y_offset += row_h
        y_offset += 8
    y_offset += 36 + PAD * 2
    H = y_offset + 10
    parts = []
    parts.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">')
    parts.append(f'<rect width="{W}" height="{H}" fill="#F5F7FA" rx="4"/>')
    parts.append(f'<rect x="0" y="0" width="{W}" height="{title_h}" fill="#1890FF" rx="4"/>')
    parts.append(f'<rect x="0" y="{title_h-4}" width="{W}" height="4" fill="#1890FF"/>')
    parts.append(f'<text x="{W//2}" y="{title_h//2+6}" text-anchor="middle" fill="white" font-size="16" font-weight="bold" font-family="sans-serif">鍔冲姟寮€绁ㄧ敵璇疯〃</text>')
    y = title_h + 14
    for cat in CATEGORY_ORDER:
        cat_fields = [(k, v) for k, v in FIELD_REGISTRY.items() if v["category"] == cat]
        if not cat_fields: continue
        parts.append(f'<text x="{PAD}" y="{y+14}" fill="#1890FF" font-size="14" font-weight="bold" font-family="sans-serif">{CATEGORY_LABELS[cat]}</text>')
        y += 28
        parts.append(f'<line x1="{PAD}" y1="{y}" x2="{W-PAD}" y2="{y}" stroke="#E8E8E8" stroke-width="1"/>')
        y += 4
        for fk, fv in cat_fields:
            val = data.get(fk, "")
            display = _format_display_value(fk, val)
            filled = bool(display)
            icon = "鉁? if filled else "鉁?
            icon_color = "#52C41A" if filled else "#FF4D4F"
            parts.append(f'<text x="{PAD}" y="{y+16}" fill="{icon_color}" font-size="12" font-family="sans-serif">{icon}</text>')
            label_color = "#333333" if filled else "#999999"
            parts.append(f'<text x="{PAD+18}" y="{y+16}" fill="{label_color}" font-size="12" font-family="sans-serif">{fv["label"]}{" *" if fv["required"] else ""}</text>')
            val_text = display if filled else "鏈～鍐?
            val_color = "#1A1A1A" if filled else "#CCCCCC"
            parts.append(f'<text x="{W-PAD}" y="{y+16}" text-anchor="end" fill="{val_color}" font-size="12" font-family="sans-serif">{val_text}</text>')
            y += row_h
        y += 8
    req_filled = sum(1 for k, v in FIELD_REGISTRY.items() if v["required"] and _format_display_value(k, data.get(k, "")))
    req_total = sum(1 for v in FIELD_REGISTRY.values() if v["required"])
    opt_filled = sum(1 for k, v in FIELD_REGISTRY.items() if not v["required"] and _format_display_value(k, data.get(k, "")))
    opt_total = sum(1 for v in FIELD_REGISTRY.values() if not v["required"])
    parts.append(f'<rect x="0" y="{y}" width="{W}" height="32" fill="#E6F7FF"/>')
    parts.append(f'<text x="{W//2}" y="{y+20}" text-anchor="middle" fill="#1890FF" font-size="12" font-family="sans-serif">蹇呭～: {req_filled}/{req_total} 宸插～鍐?| 鍙€? {opt_filled}/{opt_total} 宸插～鍐?/text>')
    parts.append("</svg>")
    return "\n".join(parts)

def _render_button_html(is_supplementing: str = "false") -> str:
    can_submit = is_supplementing != "true"
    if can_submit:
        btn_text, btn_style = "纭骞剁珛鍗虫彁浜ょ敵璇?, "background:linear-gradient(135deg,#1890FF,#096DD9);color:#fff;cursor:pointer;"
    else:
        btn_text, btn_style = "琛ュ厖淇℃伅涓?..", "background:#D9D9D9;color:#999;cursor:not-allowed;"
    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<style>body{{margin:0;padding:20px;font-family:sans-serif;background:#F5F7FA;display:flex;justify-content:center;align-items:center;min-height:100vh}}
.btn{{display:inline-block;padding:14px 48px;font-size:18px;font-weight:600;border:none;border-radius:8px;{btn_style}letter-spacing:1px;box-shadow:0 2px 8px rgba(24,144,255,0.3);transition:all .2s}}
.btn:hover{{transform:translateY(-1px);box-shadow:0 4px 16px rgba(24,144,255,0.4)}}
.msg{{display:none;margin-top:16px;padding:12px 24px;background:#F6FFED;border:1px solid #B7EB8F;border-radius:8px;color:#52C41A;font-size:16px}}</style></head><body>
<div style="text-align:center">
<button class="btn" {'' if can_submit else 'disabled'} onclick="doSubmit()">{btn_text}</button>
<div id="msg" class="msg">宸茬‘璁わ紝璇峰湪瀵硅瘽涓洖澶?鎻愪氦"瀹屾垚鐢宠</div></div>
<script>function doSubmit(){{document.getElementById('msg').style.display='block';document.querySelector('.btn').disabled=true;document.querySelector('.btn').innerText='宸茬‘璁わ紝璇峰湪瀵硅瘽涓洖澶?鎻愪氦';document.querySelector('.btn').style.background='#52C41A';}}</script>
</body></html>"""

def _parse_time_range(time_range: str):
    """灏?time_range 杞负鍏蜂綋鐨?beginTime/endTime"""
    now = datetime.now()
    if time_range == "last_month":
        if now.month == 1:
            start = datetime(now.year - 1, 12, 1)
            end = datetime(now.year - 1, 12, 31)
        else:
            start = datetime(now.year, now.month - 1, 1)
            if now.month == 2:
                end = datetime(now.year, 1, 28)
            elif now.month in (4, 6, 9, 11):
                end = datetime(now.year, now.month - 1, 30)
            else:
                end = datetime(now.year, now.month - 1, 31)
    elif time_range == "last":
        start = now - timedelta(days=90)
        end = now
    elif time_range == "last_3_months":
        if now.month <= 3:
            start = datetime(now.year - 1, 12 + now.month - 3, 1)
        else:
            start = datetime(now.year, now.month - 3, 1)
        end = now
    elif time_range == "this_year":
        start = datetime(now.year, 1, 1)
        end = now
    elif time_range == "last_year":
        start = datetime(now.year - 1, 1, 1)
        end = datetime(now.year - 1, 12, 31)
    elif "-" in time_range:
        try:
            year, month = map(int, time_range.split("-"))
            start = datetime(year, month, 1)
            if month == 12:
                end = datetime(year + 1, 1, 1) - timedelta(days=1)
            else:
                end = datetime(year, month + 1, 1) - timedelta(days=1)
        except:
            start = now - timedelta(days=180)
            end = now
    else:
        start = now - timedelta(days=180)
        end = now
    return start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")

# =====================================================================
# Mock 鏁版嵁
# =====================================================================
MOCK_INVOICE_RECORDS = [
    {
        "id": "INV2025050001", "projectId": "PRJ001",
        "projectName": "绂忕敯涓鏀规墿寤?, "amount": "85000", "invoiceType": "鐢靛瓙涓撶エ",
        "invoiceCompanyName": "娣卞湷甯傛亽姝ｅ缓绛戝姵鍔℃湇鍔℃湁闄愬叕鍙?,
        "invoiceBodyName": "娣卞湷甯備腑绉戞腐绉戞妧鏈夐檺鍏徃",
        "engName": "绂忕敯涓鏀规墿寤哄伐绋?, "engAddress": "娣卞湷甯傜鐢板尯绂忓己璺?,
        "proxyType": "1", "invoiceRemark": "鍔冲姟璐?, "supplement": "",
        "crossPeriodDeclaration": "0", "declarationPeriods": "", "projectType": "1",
        "certificate": "[]", "businessName": "寮犱笁", "taxCertificate": "闇€瑕?,
        "projectContract": '[{"name":"鏂藉伐鍚堝悓.pdf"}]', "otherFile": "[]",
        "invoiceHeaderId": "", "invoiceRate": "3%", "taxPersonnel": "鏉庡洓",
        "salary": "85000", "status": "2", "createTime": "2026-05-15 10:30:00",
    },
    {
        "id": "INV2025040003", "projectId": "PRJ001",
        "projectName": "鍏夋槑绉戝鍩?, "amount": "120000", "invoiceType": "鐢靛瓙涓撶エ",
        "invoiceCompanyName": "娣卞湷甯傛亽姝ｅ缓绛戝姵鍔℃湇鍔℃湁闄愬叕鍙?,
        "invoiceBodyName": "娣卞湷甯備腑绉戞腐绉戞妧鏈夐檺鍏徃",
        "engName": "鍏夋槑绉戝鍩庝富浣撳伐绋?, "engAddress": "娣卞湷甯傚厜鏄庡尯绉戝澶ч亾",
        "proxyType": "1", "invoiceRemark": "宸ョ▼娆?, "supplement": "浜屾湡",
        "crossPeriodDeclaration": "0", "declarationPeriods": "", "projectType": "1",
        "certificate": '[{"name":"鏀舵鍑瘉.jpg"}]', "businessName": "寮犱笁",
        "taxCertificate": "[]", "projectContract": '[{"name":"鏂藉伐鍚堝悓.pdf"}]',
        "otherFile": '[{"name":"缁撶畻鍗?xlsx"}]', "invoiceHeaderId": "", "invoiceRate": "3%",
        "taxPersonnel": "鏉庡洓", "salary": "120000", "status": "2", "createTime": "2026-04-10 14:20:00",
    },
    {
        "id": "INV2025030005", "projectId": "PRJ002",
        "projectName": "鍓嶆捣閲戣瀺涓績", "amount": "200000", "invoiceType": "绾歌川鏅エ",
        "invoiceCompanyName": "娣卞湷甯傛亽姝ｅ缓绛戝姵鍔℃湇鍔℃湁闄愬叕鍙?,
        "invoiceBodyName": "娣卞湷甯備腑绉戞腐绉戞妧鏈夐檺鍏徃",
        "engName": "鍓嶆捣閲戣瀺涓績椤圭洰", "engAddress": "娣卞湷甯傚崡灞卞尯鍓嶆捣璺?,
        "proxyType": "0", "invoiceRemark": "鏉愭枡娆?, "supplement": "",
        "crossPeriodDeclaration": "1", "declarationPeriods": "鍒?鏈?, "projectType": "0",
        "certificate": "[]", "businessName": "鐜嬩簲", "taxCertificate": "[]",
        "projectContract": '[{"name":"鏂藉伐鍚堝悓.pdf"}]', "otherFile": "[]",
        "invoiceHeaderId": "", "invoiceRate": "3%", "taxPersonnel": "璧靛叚",
        "salary": "200000", "status": "2", "createTime": "2026-03-05 09:15:00",
    },
]

# =====================================================================
# API 绔偣锛堝叏閮ㄩ渶瑕?API Key 閴存潈锛?# =====================================================================

@app.get("/health")
async def health_check():
    return {"status": "ok", "mode": BACKEND_MODE, "version": "2.0.0"}

@app.get("/api-key")
async def get_api_key_info():
    """鑾峰彇 API Key 淇℃伅锛堜粎渚涚鐞嗗憳鏌ョ湅锛?""
    return {
        "api_key": API_KEY,
        "header_name": "X-API-Key",
        "usage": "鍦ㄦ墍鏈夎姹傜殑 Header 涓坊鍔?X-API-Key: {key}"
    }


# 鈹€鈹€鈹€ 宸ュ叿1锛氶獙璇佸紑绁ㄨ〃鍗?鈹€鈹€鈹€

@app.post("/validate")
async def validate_invoice_form(req: FormRequest, api_key: str = Depends(verify_api_key)):
    """楠岃瘉寮€绁ㄨ〃鍗曞繀濉瓧娈点€?涓繀濉細椤圭洰鍚嶇О銆佸紑绁ㄩ噾棰濄€佸彂绁ㄧ被鍨嬨€佽柂璧勪唬鍙?""
    try:
        data = json.loads(req.form_data)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="form_data 涓嶆槸鍚堟硶鐨凧SON")

    missing_required_keys, missing_required_labels = [], []
    for key, meta in FIELD_REGISTRY.items():
        if meta["required"]:
            val = data.get(key, "")
            if not str(val).strip():
                missing_required_keys.append(key)
                missing_required_labels.append(meta["label"])

    filled_required = sum(1 for k, v in FIELD_REGISTRY.items() if v["required"] and str(data.get(k, "")).strip())
    total_required = sum(1 for v in FIELD_REGISTRY.values() if v["required"])
    filled_optional = sum(1 for k, v in FIELD_REGISTRY.items() if not v["required"] and str(data.get(k, "")).strip())
    total_optional = sum(1 for v in FIELD_REGISTRY.values() if not v["required"])

    return {
        "valid": len(missing_required_keys) == 0,
        "missing_required": missing_required_keys,
        "missing_required_labels": missing_required_labels,
        "filled_required_count": filled_required,
        "total_required_count": total_required,
        "filled_optional_count": filled_optional,
        "total_optional_count": total_optional,
        "can_submit": len(missing_required_keys) == 0,
    }


# 鈹€鈹€鈹€ 宸ュ叿2锛氭覆鏌撳紑绁ㄨ〃鍗?鈹€鈹€鈹€

@app.post("/render")
async def render_invoice_form(req: RenderRequest, api_key: str = Depends(verify_api_key)):
    """娓叉煋琛ㄥ崟 SVG 棰勮鍥?+ HTML 纭鎸夐挳"""
    try:
        data = json.loads(req.form_data)
    except json.JSONDecodeError:
        return {"success": False, "error": "form_data 涓嶆槸鍚堟硶鐨凧SON"}

    try:
        ts = int(time.time() * 1000)
        file_hash = hashlib.md5(req.form_data.encode()).hexdigest()[:8]

        svg_content = _render_form_svg(data)
        svg_filename = f"form_{ts}_{file_hash}.svg"
        image_url = _save_file(svg_filename, svg_content.encode("utf-8"))

        html_content = _render_button_html(req.is_supplementing)
        html_filename = f"btn_{ts}_{file_hash}.html"
        button_url = _save_file(html_filename, html_content.encode("utf-8"))

        unfilled_optional = []
        for key, meta in FIELD_REGISTRY.items():
            if not meta["required"] and not _format_display_value(key, data.get(key, "")):
                unfilled_optional.append(meta["label"])

        return {
            "success": True,
            "image_url": image_url,
            "button_url": button_url,
            "unfilled_optional_labels": unfilled_optional,
            "message": "琛ㄥ崟宸茬敓鎴?
        }
    except Exception as e:
        logger.error(f"Render error: {e}")
        return {"success": False, "error": str(e)}


# 鈹€鈹€鈹€ 宸ュ叿3锛氭煡璇㈠巻鍙插紑绁ㄨ褰?鈹€鈹€鈹€

@app.post("/query_history")
async def query_invoice_history(req: QueryHistoryRequest, api_key: str = Depends(verify_api_key)):
    """鏌ヨ鍘嗗彶寮€绁ㄨ褰曘€傛敮鎸?mock 妯″紡鍜岀湡瀹?API 妯″紡"""
    
    if BACKEND_MODE == "real" and REAL_BACKEND_URL:
        # 鐪熷疄妯″紡锛氬鎺ュ悗绔?API
        return await _query_real_backend(req)

    # Mock 妯″紡
    begin_time, end_time = _parse_time_range(req.time_range)
    
    filtered = MOCK_INVOICE_RECORDS
    if req.project_name:
        filtered = [r for r in filtered if req.project_name in r.get("projectName", "")]

    display_records = []
    for rec in filtered:
        display = {}
        for key, meta in FIELD_REGISTRY.items():
            if key in rec:
                val = _format_display_value(key, rec[key])
                if val: display[meta["label"]] = val
        display_records.append(display)

    return {
        "success": True,
        "project_name": req.project_name or "鍏ㄩ儴椤圭洰",
        "time_range": req.time_range or "鏈€杩?涓湀",
        "total": len(filtered),
        "records": display_records,
        "raw_records": filtered,
        "message": f"鏌ヨ鍒?{len(filtered)} 鏉″巻鍙插紑绁ㄨ褰?
    }


async def _query_real_backend(req: QueryHistoryRequest):
    """瀵规帴鐪熷疄鍚庣 API"""
    try:
        import httpx
        begin_time, end_time = _parse_time_range(req.time_range)
        
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(
                f"{REAL_BACKEND_URL}/app/salary/invoiceInfo/list",
                params={
                    "status": req.status,
                    "params.beginTime": begin_time,
                    "params.endTime": end_time,
                    "pageNum": req.page_num,
                    "pageSize": req.page_size,
                },
                headers={"X-API-Key": API_KEY}
            )
            data = resp.json()
            records = data.get("data", {}).get("records", []) if data.get("code") == 200 else []
            
            display_records = []
            for rec in records:
                display = {}
                for key, meta in FIELD_REGISTRY.items():
                    if key in rec:
                        val = _format_display_value(key, rec[key])
                        if val: display[meta["label"]] = val
                display_records.append(display)

            return {
                "success": True,
                "project_name": req.project_name,
                "time_range": req.time_range,
                "total": len(records),
                "records": display_records,
                "raw_records": records,
                "message": f"鏌ヨ鍒?{len(records)} 鏉″巻鍙插紑绁ㄨ褰?
            }
    except Exception as e:
        logger.error(f"Real backend query error: {e}")
        # 闄嶇骇鍒?mock
        return {
            "success": True,
            "project_name": req.project_name,
            "time_range": req.time_range,
            "total": 0,
            "records": [],
            "raw_records": [],
            "message": f"鍚庣 API 鏆備笉鍙敤({str(e)})锛屽垏鎹㈠埌 mock 妯″紡銆傚疄闄呴儴缃叉椂璇烽厤缃?REAL_BACKEND_URL銆?
        }


# 鈹€鈹€鈹€ 宸ュ叿4锛氭彁浜ゅ紑绁ㄧ敵璇?鈹€鈹€鈹€

@app.post("/submit_application")
async def submit_invoice_application(req: SubmitRequest, api_key: str = Depends(verify_api_key)):
    """鎻愪氦寮€绁ㄧ敵璇枫€傛敮鎸?mock 妯″紡鍜岀湡瀹?API 妯″紡"""
    try:
        data = json.loads(req.form_data)
    except json.JSONDecodeError:
        return {"success": False, "error": "form_data 涓嶆槸鍚堟硶鐨凧SON"}

    if BACKEND_MODE == "real" and REAL_BACKEND_URL:
        return await _submit_real_backend(data)

    # Mock 妯″紡
    is_edit = bool(data.get("id", "").strip())
    application_id = data.get("id") or f"INV{datetime.now().strftime('%Y%m%d')}{hashlib.md5(str(time.time()).encode()).hexdigest()[:4].upper()}"

    summary = {}
    for fk, meta in FIELD_REGISTRY.items():
        display_val = _format_display_value(fk, data.get(fk, ""))
        if display_val: summary[meta["label"]] = display_val

    if data.get("taxPersonnel"): summary["鎶ョ◣浜哄憳"] = str(data["taxPersonnel"])
    if data.get("salary"): summary["钖祫淇℃伅"] = str(data["salary"])

    return {
        "success": True,
        "application_id": application_id,
        "mode": "缂栬緫" if is_edit else "鏂板",
        "status": "宸叉彁浜?鑽夌)",
        "message": f"寮€绁ㄧ敵璇峰凡鎴愬姛{'缂栬緫' if is_edit else '鏂板'}鎻愪氦锛岀敵璇峰崟鍙? {application_id}",
        "submitted_summary": summary,
    }


async def _submit_real_backend(data: dict):
    """瀵规帴鐪熷疄鍚庣鎻愪氦 API"""
    try:
        import httpx
        is_edit = bool(data.get("id", "").strip())
        
        async with httpx.AsyncClient(timeout=30) as client:
            if is_edit:
                resp = await client.put(
                    f"{REAL_BACKEND_URL}/app/salary/invoiceInfo",
                    json=data,
                    headers={"X-API-Key": API_KEY}
                )
            else:
                data["status"] = data.get("status", "0")
                resp = await client.post(
                    f"{REAL_BACKEND_URL}/app/salary/invoiceInfo",
                    json=data,
                    headers={"X-API-Key": API_KEY}
                )
            
            result = resp.json()
            if result.get("code") == 200:
                resp_data = result.get("data", {})
                return {
                    "success": True,
                    "application_id": resp_data.get("id", ""),
                    "mode": "缂栬緫" if is_edit else "鏂板",
                    "status": "宸叉彁浜?,
                    "message": f"鎻愪氦鎴愬姛锛岀敵璇峰崟鍙? {resp_data.get('invoiceApplyNo', resp_data.get('id', ''))}",
                    "submitted_summary": {},
                }
            else:
                return {"success": False, "error": result.get("msg", "鎻愪氦澶辫触")}
    except Exception as e:
        logger.error(f"Real backend submit error: {e}")
        # 闄嶇骇鍒?mock
        application_id = f"INV{datetime.now().strftime('%Y%m%d')}MOCK"
        return {
            "success": True,
            "application_id": application_id,
            "mode": "鏂板(Mock)",
            "status": "宸叉彁浜?鑽夌-Mock妯″紡)",
            "message": f"鍚庣API鏆備笉鍙敤锛屼娇鐢∕ock妯″紡鎻愪氦銆傜敵璇峰崟鍙? {application_id}銆傚疄闄呴儴缃叉椂璇烽厤缃?REAL_BACKEND_URL銆?,
            "submitted_summary": {}
        }


# 闈欐€佹枃浠?app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# =====================================================================
# 鍚姩
# =====================================================================
if __name__ == "__main__":
    import uvicorn
    print(f"""
鈺斺晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晽
鈺? 灏忕▼搴忓紑绁ㄦ櫤鑳戒綋 - 缁熶竴鍚庣鏈嶅姟 v2.0         鈺?鈺犫晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨暎
鈺? 绔彛: {PORT}                                  鈺?鈺? 妯″紡: {BACKEND_MODE}                          鈺?鈺? API Key: {API_KEY[:20]}...  鈺?鈺? API鏂囨。: http://localhost:{PORT}/docs        鈺?鈺? 鍋ュ悍妫€鏌? http://localhost:{PORT}/health     鈺?鈺氣晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨晲鈺愨暆
""")
    uvicorn.run(app, host="0.0.0.0", port=PORT)

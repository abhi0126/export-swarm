"""Taku web layer: demo runner page + generated storefront page."""

import json
import threading
import uuid
from pathlib import Path

from flask import Flask, jsonify, render_template, request
from werkzeug.utils import secure_filename

from orchestrator import run_swarm

app = Flask(__name__)

UPLOAD_DIR = Path(__file__).parent / "static" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
ALLOWED_IMAGE_EXT = {"jpg", "jpeg", "png", "webp", "gif"}

SAMPLE = {
    "image_url": "https://images.unsplash.com/photo-1593618998160-e34014e67546",
    "note": (
        "手打ちの三徳包丁、約30,000円。岐阜県関市で製作。"
        "VG-10ステンレスの芯にダマスカス積層。"
        "工房は1954年創業、三代目の刀鍛冶。"
    ),
    "buyer_country": "Germany",
}

COUNTRIES = ["Germany", "USA", "France", "UK", "Australia"]

SPONSORS = [
    ("Intake", "Qwen Cloud"),
    ("Merchandising", "GMI Cloud"),
    ("Verification", "ai&"),
    ("Export Intelligence", "Daytona"),
]

STATE = {
    "status": "idle",  # idle | running | done | failed
    "agents": {},      # agent name -> running | done | failed
    "context": {},     # latest snapshot of the shared swarm context
    "error": None,
}


def on_event(event, agent_name, context):
    STATE["agents"][agent_name] = event
    STATE["context"] = json.loads(json.dumps(context))  # snapshot


def run_in_background(initial_context):
    STATE.update(status="running", agents={}, context={}, error=None)
    try:
        run_swarm(initial_context, on_event=on_event)
        failed = any(s == "failed" for s in STATE["agents"].values())
        STATE["status"] = "failed" if failed else "done"
    except Exception as e:
        STATE["status"] = "failed"
        STATE["error"] = str(e)


@app.route("/")
def index():
    return render_template(
        "demo.html",
        page="runner",
        sample=SAMPLE,
        countries=COUNTRIES,
        sponsors=SPONSORS,
        agent_names=[name for name, _ in SPONSORS],
    )


@app.route("/storefront")
def storefront():
    return render_template("demo.html", page="storefront", ctx=STATE["context"])


@app.route("/api/run", methods=["POST"])
def api_run():
    if STATE["status"] == "running":
        return jsonify({"error": "swarm already running"}), 409
    if request.is_json:  # plain URL submissions (curl / API clients)
        data = request.get_json(force=True)
        image_url = data["image_url"]
        note = data["note"]
        buyer_country = data["buyer_country"]
    else:  # multipart form from the demo page, may carry an uploaded photo
        image_url = request.form.get("image_url", "").strip()
        note = request.form.get("note", "")
        buyer_country = request.form.get("buyer_country", "Germany")
        photo = request.files.get("image_file")
        if photo and photo.filename:
            ext = secure_filename(photo.filename).rsplit(".", 1)[-1].lower()
            if ext not in ALLOWED_IMAGE_EXT:
                return jsonify({"error": f"unsupported image type: {ext}"}), 400
            filename = f"{uuid.uuid4().hex}.{ext}"
            photo.save(UPLOAD_DIR / filename)
            # Web path so the storefront can render it; Intake base64-encodes
            # the file bytes when calling Qwen (localhost isn't reachable).
            image_url = f"/static/uploads/{filename}"

    initial_context = {
        "image_url": image_url,
        "note": note,
        "buyer_country": buyer_country,
    }
    thread = threading.Thread(target=run_in_background, args=(initial_context,), daemon=True)
    thread.start()
    return jsonify({"ok": True})


@app.route("/api/status")
def api_status():
    return jsonify(STATE)


if __name__ == "__main__":
    app.run(port=5000)

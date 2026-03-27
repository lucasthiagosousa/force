"""
FORGE — Personal Trainer IA
Servidor Python Flask
"""
import os
import sys
import json
import threading
import webbrowser
from pathlib import Path
from flask import Flask, send_from_directory, jsonify, request

# ─────────────────────────────────────────────
#  Resolve base path (works both dev and .exe)
# ─────────────────────────────────────────────
if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys._MEIPASS)
else:
    BASE_DIR = Path(__file__).parent

STATIC_DIR = BASE_DIR / "static"
PORT = 5050

app = Flask(__name__, static_folder=str(STATIC_DIR))


# ─────────────────────────────────────────────
#  Routes
# ─────────────────────────────────────────────
@app.route("/")
def index():
    return send_from_directory(str(STATIC_DIR), "index.html")


@app.route("/<path:filename>")
def serve_static(filename):
    return send_from_directory(str(STATIC_DIR), filename)


@app.route("/api/generate", methods=["POST"])
def generate_plan():
    """
    Proxy para a API da Anthropic — evita expor a API key no frontend.
    Configure ANTHROPIC_API_KEY como variável de ambiente ou no .env
    """
    import urllib.request
    import urllib.error

    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return jsonify({
            "error": "ANTHROPIC_API_KEY não configurada. "
                     "Defina a variável de ambiente ou edite forge_server.py."
        }), 400

    body = request.get_json()
    payload = json.dumps({
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 1000,
        "messages": body.get("messages", [])
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01"
        },
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
            return jsonify(data)
    except urllib.error.HTTPError as e:
        return jsonify({"error": e.read().decode()}), e.code
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/health")
def health():
    return jsonify({"status": "ok", "app": "FORGE", "version": "2.0"})


# ─────────────────────────────────────────────
#  Startup
# ─────────────────────────────────────────────
def open_browser():
    import time
    time.sleep(1.2)
    webbrowser.open(f"http://localhost:{PORT}")


def main():
    print("=" * 50)
    print("  FORGE — Personal Trainer IA")
    print(f"  Servidor: http://localhost:{PORT}")
    print("  Pressione Ctrl+C para encerrar")
    print("=" * 50)

    # Abre o navegador automaticamente
    t = threading.Thread(target=open_browser, daemon=True)
    t.start()

    app.run(host="0.0.0.0", port=PORT, debug=False, use_reloader=False)


if __name__ == "__main__":
    main()

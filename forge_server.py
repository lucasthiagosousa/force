"""
FORGE — Personal Trainer IA
Servidor Flask com autenticação, código por e-mail e banco de dados
"""
import os, sys, json, sqlite3, hashlib, secrets, smtplib, threading, webbrowser, time
from datetime import datetime, timedelta
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import Flask, send_from_directory, jsonify, request, session

# ─────────────────────────────────────────────
#  Paths
# ─────────────────────────────────────────────
if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys._MEIPASS)
    DATA_DIR = Path(sys.executable).parent / "data"
else:
    BASE_DIR = Path(__file__).parent
    DATA_DIR = BASE_DIR / "data"

STATIC_DIR = BASE_DIR / "static"
DATA_DIR.mkdir(exist_ok=True)
DB_PATH = DATA_DIR / "forge.db"
PORT = int(os.environ.get("PORT", 5050))

# ─────────────────────────────────────────────
#  Config (pode vir de variáveis de ambiente)
# ─────────────────────────────────────────────
SECRET_KEY   = os.environ.get("SECRET_KEY", secrets.token_hex(32))
ADMIN_USER   = os.environ.get("ADMIN_USER", "admin")
ADMIN_PASS   = os.environ.get("ADMIN_PASS", "forge123")
SMTP_HOST    = os.environ.get("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT    = int(os.environ.get("SMTP_PORT", 587))
SMTP_USER    = os.environ.get("SMTP_USER", "")          # seu email
SMTP_PASS    = os.environ.get("SMTP_PASS", "")          # senha de app Gmail
EMAIL_FROM   = os.environ.get("EMAIL_FROM", SMTP_USER)
ANTHROPIC_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

app = Flask(__name__, static_folder=str(STATIC_DIR))
app.secret_key = SECRET_KEY

# ─────────────────────────────────────────────
#  Banco de Dados (SQLite local / PostgreSQL produção)
# ─────────────────────────────────────────────
def get_db():
    """Retorna conexão com banco. Suporta PostgreSQL (produção) e SQLite (local)."""
    db_url = os.environ.get("DATABASE_URL", "")
    if db_url:
        # PostgreSQL via psycopg2 (Render, Railway, Supabase)
        try:
            import psycopg2
            conn = psycopg2.connect(db_url)
            conn.autocommit = False
            return conn, "pg"
        except ImportError:
            pass
    # SQLite padrão (local / .exe)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn, "sqlite"


def init_db():
    """Cria tabelas se não existirem."""
    conn, mode = get_db()
    cur = conn.cursor()
    ph = "%s" if mode == "pg" else "?"

    cur.execute(f"""
        CREATE TABLE IF NOT EXISTS users (
            id        {'SERIAL' if mode == 'pg' else 'INTEGER'} PRIMARY KEY {'AUTOINCREMENT' if mode == 'sqlite' else ''},
            name      TEXT NOT NULL,
            email     TEXT UNIQUE NOT NULL,
            password  TEXT NOT NULL,
            role      TEXT DEFAULT 'user',
            active    INTEGER DEFAULT 1,
            plan      TEXT,
            created_at TEXT,
            last_login TEXT
        )
    """)

    cur.execute(f"""
        CREATE TABLE IF NOT EXISTS email_codes (
            id        {'SERIAL' if mode == 'pg' else 'INTEGER'} PRIMARY KEY {'AUTOINCREMENT' if mode == 'sqlite' else ''},
            email     TEXT NOT NULL,
            code      TEXT NOT NULL,
            expires   TEXT NOT NULL,
            used      INTEGER DEFAULT 0
        )
    """)

    cur.execute(f"""
        CREATE TABLE IF NOT EXISTS sessions_log (
            id        {'SERIAL' if mode == 'pg' else 'INTEGER'} PRIMARY KEY {'AUTOINCREMENT' if mode == 'sqlite' else ''},
            user_id   INTEGER,
            action    TEXT,
            at        TEXT
        )
    """)

    cur.execute(f"""
        CREATE TABLE IF NOT EXISTS workout_logs (
            id        {'SERIAL' if mode == 'pg' else 'INTEGER'} PRIMARY KEY {'AUTOINCREMENT' if mode == 'sqlite' else ''},
            user_id   INTEGER,
            data      TEXT,
            logged_at TEXT
        )
    """)

    cur.execute(f"""
        CREATE TABLE IF NOT EXISTS measures (
            id        {'SERIAL' if mode == 'pg' else 'INTEGER'} PRIMARY KEY {'AUTOINCREMENT' if mode == 'sqlite' else ''},
            user_id   INTEGER,
            data      TEXT,
            logged_at TEXT
        )
    """)

    conn.commit()
    conn.close()
    print(f"  DB inicializado: {'PostgreSQL' if mode == 'pg' else 'SQLite'}")


# ─────────────────────────────────────────────
#  Helpers
# ─────────────────────────────────────────────
def hash_pass(password):
    salt = secrets.token_hex(16)
    h = hashlib.sha256((salt + password).encode()).hexdigest()
    return f"{salt}:{h}"

def check_pass(stored, password):
    try:
        salt, h = stored.split(":")
        return hashlib.sha256((salt + password).encode()).hexdigest() == h
    except Exception:
        return False

def now_str():
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

def require_login(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("user_id"):
            return jsonify({"error": "Não autenticado"}), 401
        return f(*args, **kwargs)
    return decorated

def require_admin(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get("role") != "admin":
            return jsonify({"error": "Acesso negado"}), 403
        return f(*args, **kwargs)
    return decorated

# ─────────────────────────────────────────────
#  E-mail
# ─────────────────────────────────────────────
def send_email(to_email, subject, html_body):
    """Envia e-mail via SMTP. Retorna True se OK."""
    if not SMTP_USER or not SMTP_PASS:
        print(f"  [EMAIL SIMULADO] Para: {to_email} | Assunto: {subject}")
        return True
    try:
        msg = MIMEMultipart("alternative")
        msg["From"] = EMAIL_FROM
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(html_body, "html"))
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as s:
            s.starttls()
            s.login(SMTP_USER, SMTP_PASS)
            s.send_message(msg)
        return True
    except Exception as e:
        print(f"  [EMAIL ERRO] {e}")
        return False

def email_code_html(code, name=""):
    return f"""
<div style="font-family:Arial,sans-serif;max-width:480px;margin:0 auto;padding:32px;background:#0b0b12;color:#f0f0f6;border-radius:16px">
  <div style="font-size:42px;font-weight:900;letter-spacing:6px;color:#e8ff47;margin-bottom:6px">FORGE</div>
  <div style="font-size:12px;color:#676786;letter-spacing:3px;text-transform:uppercase;margin-bottom:28px">Personal Trainer IA</div>
  <p style="font-size:16px;margin-bottom:12px">Olá{' ' + name if name else ''}! 👋</p>
  <p style="color:#b0b0c8;margin-bottom:24px">Seu código de acesso ao FORGE:</p>
  <div style="background:#1b1b28;border:2px solid #e8ff47;border-radius:12px;padding:24px;text-align:center;margin-bottom:24px">
    <div style="font-size:42px;font-weight:900;letter-spacing:10px;color:#e8ff47">{code}</div>
    <div style="font-size:12px;color:#676786;margin-top:8px">Válido por 15 minutos</div>
  </div>
  <p style="color:#676786;font-size:13px">Se você não solicitou este código, ignore este e-mail.</p>
</div>"""

# ─────────────────────────────────────────────
#  ROTAS — Estático
# ─────────────────────────────────────────────
@app.route("/")
def index():
    return send_from_directory(str(STATIC_DIR), "index.html")

@app.route("/<path:filename>")
def serve_static(filename):
    return send_from_directory(str(STATIC_DIR), filename)

@app.route("/api/health")
def health():
    conn, mode = get_db()
    conn.close()
    return jsonify({"status": "ok", "app": "FORGE", "version": "2.1", "db": mode})

# ─────────────────────────────────────────────
#  ROTAS — Autenticação
# ─────────────────────────────────────────────
@app.route("/api/auth/register", methods=["POST"])
def register():
    d = request.get_json() or {}
    name  = (d.get("name") or "").strip()
    email = (d.get("email") or "").strip().lower()
    pwd   = d.get("password") or ""

    if not name or not email or not pwd:
        return jsonify({"error": "Preencha todos os campos"}), 400
    if len(pwd) < 6:
        return jsonify({"error": "Senha mínima: 6 caracteres"}), 400

    conn, mode = get_db()
    ph = "%s" if mode == "pg" else "?"
    cur = conn.cursor()
    try:
        cur.execute(f"SELECT id FROM users WHERE email={ph}", (email,))
        if cur.fetchone():
            return jsonify({"error": "E-mail já cadastrado"}), 409
        cur.execute(
            f"INSERT INTO users (name,email,password,role,active,created_at) VALUES ({ph},{ph},{ph},{ph},1,{ph})",
            (name, email, hash_pass(pwd), "user", now_str())
        )
        conn.commit()
        # Loga sessão
        cur.execute(f"SELECT id FROM users WHERE email={ph}", (email,))
        uid = cur.fetchone()[0]
        session["user_id"] = uid
        session["name"] = name
        session["role"] = "user"
        # Envia e-mail de boas vindas (background)
        threading.Thread(target=send_email, args=(
            email, "Bem-vindo ao FORGE! 🔱",
            f"<div style='font-family:Arial;padding:24px;background:#0b0b12;color:#f0f0f6;border-radius:12px'><h1 style='color:#e8ff47'>FORGE</h1><p>Olá {name}! Seu cadastro foi realizado com sucesso. 💪</p></div>"
        ), daemon=True).start()
        return jsonify({"ok": True, "name": name, "role": "user"})
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


@app.route("/api/auth/login", methods=["POST"])
def login():
    d = request.get_json() or {}
    email = (d.get("email") or "").strip().lower()
    pwd   = d.get("password") or ""

    # Admin especial
    if email == ADMIN_USER and pwd == ADMIN_PASS:
        session["user_id"] = 0
        session["name"] = "Admin"
        session["role"] = "admin"
        return jsonify({"ok": True, "name": "Admin", "role": "admin"})

    conn, mode = get_db()
    ph = "%s" if mode == "pg" else "?"
    cur = conn.cursor()
    try:
        cur.execute(f"SELECT id,name,password,role,active FROM users WHERE email={ph}", (email,))
        row = cur.fetchone()
        if not row:
            return jsonify({"error": "E-mail não encontrado"}), 401
        uid, name, stored, role, active = row[0], row[1], row[2], row[3], row[4]
        if not active:
            return jsonify({"error": "Conta suspensa. Contate o admin."}), 403
        if not check_pass(stored, pwd):
            return jsonify({"error": "Senha incorreta"}), 401
        cur.execute(f"UPDATE users SET last_login={ph} WHERE id={ph}", (now_str(), uid))
        conn.commit()
        session["user_id"] = uid
        session["name"] = name
        session["role"] = role
        return jsonify({"ok": True, "name": name, "role": role})
    finally:
        conn.close()


@app.route("/api/auth/send-code", methods=["POST"])
def send_code():
    """Envia código de 6 dígitos por e-mail para acesso sem senha."""
    d = request.get_json() or {}
    email = (d.get("email") or "").strip().lower()
    if not email:
        return jsonify({"error": "E-mail obrigatório"}), 400

    conn, mode = get_db()
    ph = "%s" if mode == "pg" else "?"
    cur = conn.cursor()
    try:
        cur.execute(f"SELECT id,name,active FROM users WHERE email={ph}", (email,))
        row = cur.fetchone()
        if not row:
            return jsonify({"error": "E-mail não cadastrado"}), 404
        uid, name, active = row[0], row[1], row[2]
        if not active:
            return jsonify({"error": "Conta suspensa"}), 403

        code = str(secrets.randbelow(900000) + 100000)  # 6 dígitos
        expires = (datetime.utcnow() + timedelta(minutes=15)).strftime("%Y-%m-%d %H:%M:%S")
        # Remove códigos antigos
        cur.execute(f"DELETE FROM email_codes WHERE email={ph}", (email,))
        cur.execute(f"INSERT INTO email_codes (email,code,expires,used) VALUES ({ph},{ph},{ph},0)", (email, code, expires))
        conn.commit()

        ok = send_email(email, "Seu código FORGE 🔱", email_code_html(code, name))
        if not ok:
            return jsonify({"error": "Falha ao enviar e-mail. Verifique SMTP_USER e SMTP_PASS no servidor."}), 500
        return jsonify({"ok": True, "message": f"Código enviado para {email}"})
    finally:
        conn.close()


@app.route("/api/auth/verify-code", methods=["POST"])
def verify_code():
    """Verifica o código e faz login."""
    d = request.get_json() or {}
    email = (d.get("email") or "").strip().lower()
    code  = (d.get("code") or "").strip()

    conn, mode = get_db()
    ph = "%s" if mode == "pg" else "?"
    cur = conn.cursor()
    try:
        cur.execute(f"SELECT code,expires,used FROM email_codes WHERE email={ph} ORDER BY id DESC LIMIT 1", (email,))
        row = cur.fetchone()
        if not row:
            return jsonify({"error": "Nenhum código encontrado. Solicite um novo."}), 404
        stored_code, expires, used = row[0], row[1], row[2]
        if used:
            return jsonify({"error": "Código já utilizado. Solicite um novo."}), 400
        if datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S") > expires:
            return jsonify({"error": "Código expirado. Solicite um novo."}), 400
        if code != stored_code:
            return jsonify({"error": "Código incorreto."}), 401

        # Marca como usado
        cur.execute(f"UPDATE email_codes SET used=1 WHERE email={ph}", (email,))
        cur.execute(f"SELECT id,name,role FROM users WHERE email={ph}", (email,))
        urow = cur.fetchone()
        uid, name, role = urow[0], urow[1], urow[2]
        cur.execute(f"UPDATE users SET last_login={ph} WHERE id={ph}", (now_str(), uid))
        conn.commit()
        session["user_id"] = uid
        session["name"] = name
        session["role"] = role
        return jsonify({"ok": True, "name": name, "role": role})
    finally:
        conn.close()


@app.route("/api/auth/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"ok": True})


@app.route("/api/auth/me")
def me():
    if not session.get("user_id") and session.get("user_id") != 0:
        return jsonify({"logged": False})
    return jsonify({"logged": True, "name": session.get("name"), "role": session.get("role")})

# ─────────────────────────────────────────────
#  ROTAS — Dados do Usuário
# ─────────────────────────────────────────────
@app.route("/api/user/plan", methods=["GET"])
@require_login
def get_plan():
    uid = session["user_id"]
    conn, mode = get_db()
    ph = "%s" if mode == "pg" else "?"
    cur = conn.cursor()
    cur.execute(f"SELECT plan FROM users WHERE id={ph}", (uid,))
    row = cur.fetchone()
    conn.close()
    plan = json.loads(row[0]) if row and row[0] else None
    return jsonify({"plan": plan})


@app.route("/api/user/plan", methods=["POST"])
@require_login
def save_plan():
    uid = session["user_id"]
    plan = request.get_json()
    conn, mode = get_db()
    ph = "%s" if mode == "pg" else "?"
    cur = conn.cursor()
    cur.execute(f"UPDATE users SET plan={ph} WHERE id={ph}", (json.dumps(plan), uid))
    conn.commit()
    conn.close()
    return jsonify({"ok": True})


@app.route("/api/user/workout-log", methods=["POST"])
@require_login
def save_workout_log():
    uid = session["user_id"]
    data = request.get_json()
    conn, mode = get_db()
    ph = "%s" if mode == "pg" else "?"
    cur = conn.cursor()
    cur.execute(f"INSERT INTO workout_logs (user_id,data,logged_at) VALUES ({ph},{ph},{ph})", (uid, json.dumps(data), now_str()))
    conn.commit()
    conn.close()
    return jsonify({"ok": True})


@app.route("/api/user/workout-log", methods=["GET"])
@require_login
def get_workout_logs():
    uid = session["user_id"]
    conn, mode = get_db()
    ph = "%s" if mode == "pg" else "?"
    cur = conn.cursor()
    cur.execute(f"SELECT data,logged_at FROM workout_logs WHERE user_id={ph} ORDER BY id DESC LIMIT 50", (uid,))
    rows = cur.fetchall()
    conn.close()
    return jsonify({"logs": [{"data": json.loads(r[0]), "at": r[1]} for r in rows]})


@app.route("/api/user/measures", methods=["POST"])
@require_login
def save_measures():
    uid = session["user_id"]
    data = request.get_json()
    conn, mode = get_db()
    ph = "%s" if mode == "pg" else "?"
    cur = conn.cursor()
    cur.execute(f"INSERT INTO measures (user_id,data,logged_at) VALUES ({ph},{ph},{ph})", (uid, json.dumps(data), now_str()))
    conn.commit()
    conn.close()
    return jsonify({"ok": True})


@app.route("/api/user/measures", methods=["GET"])
@require_login
def get_measures():
    uid = session["user_id"]
    conn, mode = get_db()
    ph = "%s" if mode == "pg" else "?"
    cur = conn.cursor()
    cur.execute(f"SELECT data,logged_at FROM measures WHERE user_id={ph} ORDER BY id DESC LIMIT 20", (uid,))
    rows = cur.fetchall()
    conn.close()
    return jsonify({"measures": [{"data": json.loads(r[0]), "at": r[1]} for r in rows]})

# ─────────────────────────────────────────────
#  ROTAS — Admin
# ─────────────────────────────────────────────
@app.route("/api/admin/users")
@require_admin
def admin_users():
    conn, mode = get_db()
    ph = "%s" if mode == "pg" else "?"
    cur = conn.cursor()
    cur.execute("SELECT id,name,email,role,active,created_at,last_login FROM users ORDER BY id DESC")
    rows = cur.fetchall()
    conn.close()
    users = [{"id":r[0],"name":r[1],"email":r[2],"role":r[3],"active":r[4],"created":r[5],"last_login":r[6]} for r in rows]
    return jsonify({"users": users})


@app.route("/api/admin/users/<int:uid>/toggle", methods=["POST"])
@require_admin
def toggle_user(uid):
    conn, mode = get_db()
    ph = "%s" if mode == "pg" else "?"
    cur = conn.cursor()
    cur.execute(f"SELECT active FROM users WHERE id={ph}", (uid,))
    row = cur.fetchone()
    if not row:
        return jsonify({"error": "Usuário não encontrado"}), 404
    new_active = 0 if row[0] else 1
    cur.execute(f"UPDATE users SET active={ph} WHERE id={ph}", (new_active, uid))
    conn.commit()
    conn.close()
    return jsonify({"ok": True, "active": new_active})


@app.route("/api/admin/users/<int:uid>", methods=["DELETE"])
@require_admin
def delete_user(uid):
    conn, mode = get_db()
    ph = "%s" if mode == "pg" else "?"
    cur = conn.cursor()
    cur.execute(f"DELETE FROM users WHERE id={ph}", (uid,))
    conn.commit()
    conn.close()
    return jsonify({"ok": True})


@app.route("/api/admin/stats")
@require_admin
def admin_stats():
    conn, mode = get_db()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM users WHERE role!='admin'")
    total = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM users WHERE active=1 AND role!='admin'")
    active = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM workout_logs")
    logs = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM users WHERE active=0")
    suspended = cur.fetchone()[0]
    conn.close()
    return jsonify({"total":total,"active":active,"logs":logs,"suspended":suspended})

# ─────────────────────────────────────────────
#  Proxy API Anthropic
# ─────────────────────────────────────────────
@app.route("/api/generate", methods=["POST"])
@require_login
def generate():
    import urllib.request, urllib.error
    if not ANTHROPIC_KEY:
        return jsonify({"error": "ANTHROPIC_API_KEY não configurada"}), 400
    body = request.get_json()
    payload = json.dumps({"model":"claude-sonnet-4-20250514","max_tokens":1000,"messages":body.get("messages",[])}).encode()
    req = urllib.request.Request("https://api.anthropic.com/v1/messages", data=payload, headers={"Content-Type":"application/json","x-api-key":ANTHROPIC_KEY,"anthropic-version":"2023-06-01"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return jsonify(json.loads(r.read()))
    except urllib.error.HTTPError as e:
        return jsonify({"error":e.read().decode()}), e.code
    except Exception as e:
        return jsonify({"error":str(e)}), 500

# ─────────────────────────────────────────────
#  Start
# ─────────────────────────────────────────────
def open_browser_delayed():
    time.sleep(1.3)
    webbrowser.open(f"http://localhost:{PORT}")

def main():
    init_db()
    print("=" * 52)
    print("  FORGE — Personal Trainer IA v2.1")
    print(f"  URL:   http://localhost:{PORT}")
    print(f"  DB:    {DB_PATH}")
    print(f"  Email: {'configurado ✓' if SMTP_USER else 'não configurado (simulado)'}")
    print(f"  AI:    {'configurada ✓' if ANTHROPIC_KEY else 'usando mock'}")
    print("  Ctrl+C para encerrar")
    print("=" * 52)
    if not os.environ.get("NO_BROWSER"):
        threading.Thread(target=open_browser_delayed, daemon=True).start()
    app.run(host="0.0.0.0", port=PORT, debug=False, use_reloader=False)

if __name__ == "__main__":
    main()

from flask import Flask, request, make_response
import traceback
from datetime import datetime
import vercel_blob

try:
    import telebot
    TELEBOT_OK = True
except ImportError:
    TELEBOT_OK = False

app = Flask(__name__)

logs = []  # basit in-memory log

def add_log(msg):
    ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    logs.append(f"[{ts}] {msg}")
    if len(logs) > 50: logs.pop(0)

@app.route('/', methods=['GET', 'POST'])
def home():
    current_logs = logs.copy()
    message = ""
    pip_message = ""

    # Dosya upload kısmı (önceki gibi)
    if request.method == 'POST' and 'file' in request.files:
        file = request.files['file']
        if file.filename:
            try:
                blob = vercel_blob.put(file.filename, file.read(), access='public', add_random_suffix=True)
                add_log(f"Upload OK: {blob['url']}")
                message = f"Yüklendi! Link: <a href='{blob['url']}' target='_blank'>{blob['url']}</a>"
            except Exception as e:
                add_log(f"Upload hata: {str(e)}")
                message = f"Hata: {str(e)}"
        else:
            message = "Dosya adı boş!"

    # Yeni: Pip simülasyon formu (en altta)
    if request.method == 'POST' and 'pip_package' in request.form:
        package = request.form['pip_package'].strip()
        if package:
            add_log(f"Kullanıcı paket istedi: {package}")
            pip_message = f"""
            <div style="background:#1f6feb22; padding:15px; border-radius:8px; margin-top:20px;">
                <strong>Ne yapman lazım:</strong><br>
                GitHub'da <code>requirements.txt</code>'ye şunu ekle:<br>
                <pre style="background:#000; padding:10px; border-radius:6px;">{package}</pre>
                Sonra commit & push at → Vercel otomatik redeploy eder (30-60 sn).<br>
                Paket yüklendikten sonra logda "yüklü ✓" göreceksin!
            </div>
            """
        else:
            pip_message = "<p style='color:red;'>Paket adı gir lan!</p>"

    # Paket kontrolleri
    if not TELEBOT_OK:
        add_log("TELEBOT EKSİK! requirements.txt'ye pyTelegramBotAPI ekle → redeploy")
    else:
        add_log("telebot yüklü ✓")

    add_log("Site yüklendi")

    html = f"""
    <!DOCTYPE html>
    <html lang="tr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Kerem'in Vercel Sitesi</title>
        <style>
            body {{ font-family: Arial; background:#0d1117; color:#c9d1d9; margin:0; padding:20px; }}
            h1 {{ color:#58a6ff; text-align:center; }}
            .container {{ max-width:800px; margin:auto; background:#161b22; padding:25px; border-radius:12px; }}
            form {{ margin:30px 0; }}
            input, button {{ width:100%; padding:12px; margin:8px 0; border-radius:6px; border:1px solid #30363d; background:#21262d; color:white; }}
            button {{ background:#238636; border:none; cursor:pointer; }}
            button:hover {{ background:#2ea043; }}
            pre {{ background:#010409; padding:15px; border-radius:8px; overflow:auto; white-space:pre-wrap; }}
            .msg {{ padding:15px; background:#1f6feb22; border:1px solid #1f6feb; border-radius:8px; margin:20px 0; text-align:center; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Dosya Yükle + Log</h1>
            
            <form method="post" enctype="multipart/form-data">
                <input type="file" name="file" required>
                <button type="submit">Yükle</button>
            </form>
            {f'<div class="msg">{message}</div>' if message else ''}
            
            <h2>Loglar</h2>
            <pre>{'\n'.join(current_logs) or 'Log boş – bi şey yap!'}</pre>
            
            <h2>Pip Paket İndir (Simüle)</h2>
            <p>Buraya paket adı yaz (örn: telebot), butona bas → sana talimat vereyim, sen ekle redeploy et.</p>
            <form method="post">
                <input type="text" name="pip_package" placeholder="örn: requests veya telebot" required>
                <button type="submit">Pip İndir!</button>
            </form>
            {pip_message}
            
            <p style="text-align:center; color:#8b949e; font-size:0.9em; margin-top:30px;">
                Gerçek pip install runtime'da olmaz (Vercel serverless limit), ama bu şekilde ekle → 1 dk'da yüklü olur!
            </p>
        </div>
    </body>
    </html>
    """

    resp = make_response(html)
    return resp

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)

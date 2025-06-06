from flask import Flask, render_template
import socket

app = Flask(__name__)

# 📡 Liste des pylônes et leurs adresses IP
pylones = {
    "Pylône 1": "192.168.1.10",
    "Pylône 2": "192.168.1.20",

}

def verifier_pylones():
    etats = {}
    for nom, ip in pylones.items():
        try:
            socket.create_connection((ip, 80), timeout=3)
            etats[nom] = "🟢 En ligne"
        except:
            etats[nom] = "🔴 Hors ligne"
    return etats

@app.route("/")
def index():
    etats = verifier_pylones()
    return render_template("index.html", pylones=etats)

if __name__ == "__main__":
    app.run(debug=True)
from flask import Flask, render_template, jsonify
from flask_socketio import SocketIO
import socket
import time
import os
import threading
import pusher
import json
import pandas as pd
from datetime import datetime
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Autoriser les requêtes cross-origin
socketio = SocketIO(app, cors_allowed_origins="*")

@app.route("/")
def home():
    return "Socket.io Flask Server is running!"

@app.route("/dashboard")
def dashboard():
    return render_template("index.html")

@app.route("/historique")
def historique_alertes():
    try:
        with open("alerte.json", "r", encoding="utf-8") as fichier:
            historique = json.load(fichier)
    except FileNotFoundError:
        historique = []
    return render_template("index.html", historique=historique)

pylones = {
    "Pylône 1": "10.10.21.105",
    "Pylône 2": "10.10.24.132",
    "Pylône 3": "10.10.18.110",
}

pusher_client = pusher.Pusher(
    app_id="2001377",
    key="15855bf1583d7c1e77e4",
    secret="12b8051324f92937e48b",
    cluster="eu",
    ssl=True
)

def verifier_pylones():
    etats = {}
    for nom, ip in pylones.items():
        try:
            socket.create_connection((ip, 80), timeout=3)
            etats[nom] = "🟢 En ligne"
        except:
            etats[nom] = "🔴 Hors ligne"
            enregistrer_alerte(nom, "Hors ligne")
    return etats

def enregistrer_alerte(nom_pylone, statut):
    try:
        with open("alerte.json", "r", encoding="utf-8") as fichier:
            historique = json.load(fichier)
    except (FileNotFoundError, json.JSONDecodeError):
        historique = []
    
    historique.append({
        "pylone": nom_pylone,
        "statut": statut,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })
    
    with open("alerte.json", "w", encoding="utf-8") as fichier:
        json.dump(historique, fichier, indent=4)

@app.route("/data")
def get_pylones_data():
    etats = verifier_pylones()
    data = [
        {
            "nom": nom,
            "lat": 48.8566,
            "lon": 2.3522,
            "statut": etats[nom]
        }
        for nom, ip in pylones.items()
    ]
    return jsonify(data)

data = pd.read_csv("coupures.csv", encoding="utf-8")
X = data[["température", "vent", "charge_reseau"]]
y = data["coupure_probable"]

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)
model = RandomForestClassifier()
model.fit(X_train, y_train)

@app.route("/predictions")
def get_predictions():
    predictions = model.predict(X_test)
    pylones_a_risque = [{"nom": X_test.iloc[i]["nom"]} for i, valeur in enumerate(predictions) if valeur == 1]
    return jsonify(pylones_a_risque)

def surveillance_en_temps_reel():
    while True:
        etats = verifier_pylones()
        socketio.emit("mise_a_jour", etats)
        time.sleep(5)

threading.Thread(target=surveillance_en_temps_reel).start()

@socketio.on("connect")
def handle_connect():
    print("📡 Client connecté !")

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
from flask import Flask, render_template
from flask_socketio import SocketIO
import socket
import time
import os
import threading
import pusher
import json
from datetime import datetime
import threading
from flask import jsonify
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier

app = Flask(__name__)
socketio = SocketIO(app)

from flask import Flask
import os  # 💡 Importer os pour gérer les variables d'environnement

app = Flask(__name__)

# 🔥 Définir le port au début
port = int(os.environ.get("PORT", 5000))  # Render définit automatiquement le port

@app.route('/')
def home():
    return "Hello World!"

# 🚀 Lancer l'application Flask
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=port)

# 📡 Liste des pylônes et leurs adresses IP
pylones = {
    "Pylône 1": "10.10.21.105",
    "Pylône 2": "10.10.24.132",
    "Pylône 3": "10.10.18.110",
    "Pylône 4": "10.10.21.105",
    "Pylône 5": "10.10.24.132",
    "Pylône 6": "10.10.18.110",
    "Pylône 7": "10.10.21.105",
    "Pylône 8": "10.10.24.132",
    "Pylône 9": "10.10.18.110",
    "Pylône 10": "10.10.21.105",
    "Pylône 11": "10.10.24.132",
    "Pylône 12": "10.10.18.110",
    "Pylône 13": "10.10.21.105",
    "Pylône 14": "10.10.24.132",
    "Pylône 15": "10.10.18.110",
}

# 🔔 Configurer Pusher (remplace par tes propres clés API)
pusher_client = pusher.Pusher(
    app_id = "2001377",
    key = "15855bf1583d7c1e77e4",
    secret = "12b8051324f92937e48b",
    cluster = "eu",
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
            # 🔔 Envoyer une notification push via Pusher
            pusher_client.trigger("alerte-channel", "pylone-hors-ligne", {"message": f"⚠️ {nom} est hors ligne !"})
    return etats

@app.route("/")
def index():
    return render_template("index.html")

def surveillance_en_temps_reel():
    while True:
        etats = verifier_pylones()
        socketio.emit("mise_a_jour", etats)
        time.sleep(5)  # Mise à jour toutes les 5 secondes

thread_surveillance = threading.Thread(target=surveillance_en_temps_reel)
thread_surveillance.start()       

@socketio.on("connect")
def handle_connect():
    print("📡 Client connecté !")


def enregistrer_alerte(nom_pylone, statut):
    # Charger l'historique actuel
    try:
        with open("alerte.json", "r", encoding="utf-8") as fichier:
            historique = json.load(fichier)
    except (FileNotFoundError, json.JSONDecodeError):
        historique = []

    # Ajouter une nouvelle entrée
    historique.append({
        "pylone": nom_pylone,
        "statut": statut,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })

    # Sauvegarder dans le fichier
    with open("alerte.json", "w", encoding="utf-8") as fichier:
        json.dump(historique, fichier, indent=4)

def verifier_pylones():
    etats = {}
    for nom, ip in pylones.items():
        try:
            socket.create_connection((ip, 80), timeout=3)
            etats[nom] = "🟢 En ligne"
        except:
            etats[nom] = "🔴 Hors ligne"
            enregistrer_alerte(nom, "Hors ligne")  # 📌 Enregistrer l'alerte
    return etats

@app.route("/historique")
def historique_alertes():
    try:
        with open("alerte.json", "r", encoding="utf-8") as fichier:
            historique = json.load(fichier)
    except FileNotFoundError:
        historique = []

    return render_template("index.html", historique=historique)

def charger_historique():
    try:
        with open("alerte.json", "r", encoding="utf-8") as fichier:
            return json.load(fichier)  # 📌 Chargement sécurisé
    except (FileNotFoundError, json.JSONDecodeError):
        return []  # 📌 Si erreur, retourne une liste vide

@app.route("/data")
def get_pylones_data():
    etats = verifier_pylones()  # 📡 Vérifier les statuts des pylônes
    data = []

    for nom, ip in pylones.items():
        statut = etats[nom]
        data.append({
            "nom": nom,
            "lat": 48.8566,  # Exemple de latitude, remplace par les vraies coordonnées
            "lon": 2.3522,   # Exemple de longitude, remplace par les vraies coordonnées
            "statut": statut
        })
    
    return jsonify(data)  # 🔄 Retourne les données en JSON


# 📊 Sélectionner les caractéristiques utiles
# 🔄 Charger les données historiques

data = pd.read_csv(r"C:\Users\mouna\env\mon projet\.venv\env\coupures.csv", encoding="utf-8")
X = data[["température", "vent", "charge_reseau"]]
y = data["coupure_probable"]

# 🚀 Diviser en données d’entraînement et de test
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

# 🎯 Créer un modèle de prédiction
model = RandomForestClassifier()
model.fit(X_train, y_train)

# 🔍 Prédire les pannes futures
predictions = model.predict(X_test)

@app.route("/predictions")
def get_predictions():
    predictions = model.predict(X_test)  # 📊 Utilisation du modèle IA
    pylones_a_risque = []

    for i, valeur in enumerate(predictions):
        if valeur == 1:  # 📌 1 signifie "Risque de panne"
            pylones_a_risque.append({"nom": X_test.iloc[i]["nom"]})

        return jsonify(pylones_a_risque)
    
if __name__ == "__main__":
    threading.Thread(target=surveillance_en_temps_reel).start()
    socketio.run(app, debug=True),

import os
from flask import Flask, jsonify, request, Response
from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST
from sklearn.datasets import load_iris
from sklearn.ensemble import RandomForestClassifier

app = Flask(__name__)
VERSION = os.getenv("APP_VERSION", "dev")

# Modèle ML : entraîné une fois au démarrage (jeu de données iris, très petit)
iris = load_iris()
model = RandomForestClassifier(n_estimators=50, random_state=42)
model.fit(iris.data, iris.target)

REQUESTS = Counter(
    "app_requests_total",
    "Nombre de requêtes reçues",
    ["method", "route", "status"],
)
PREDICTIONS = Counter(
    "app_predictions_total",
    "Nombre de prédictions par espèce",
    ["espece"],
)

CHAMPS = ("sepal_length", "sepal_width", "petal_length", "petal_width")


@app.after_request
def compter_requetes(response):
    route = request.url_rule.rule if request.url_rule else "inconnue"
    REQUESTS.labels(request.method, route, response.status_code).inc()
    return response


@app.get("/")
def accueil():
    return jsonify(message="API de prédiction d'espèces d'iris", route="/predict")


@app.get("/health")
def health():
    return jsonify(status="ok")


@app.get("/version")
def version():
    return jsonify(version=VERSION)


@app.get("/predict")
def predict():
    try:
        valeurs = [float(request.args[nom]) for nom in CHAMPS]
    except (KeyError, ValueError):
        return jsonify(error="Paramètres numériques requis", champs=list(CHAMPS)), 400

    probas = model.predict_proba([valeurs])[0]
    indice = int(probas.argmax())
    espece = str(iris.target_names[indice])
    PREDICTIONS.labels(espece).inc()
    return jsonify(espece=espece, confiance=round(float(probas[indice]), 3))


@app.get("/metrics")
def metrics():
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
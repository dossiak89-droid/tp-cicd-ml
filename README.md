# TP CI/CD : API de prédiction (machine learning) déployée sur Kubernetes

Petite API Flask qui prédit l'espèce d'une fleur d'iris avec un modèle scikit-learn.
Le projet montre le parcours complet : application, Git, conteneur Docker, déploiement
Kubernetes et monitoring avec Prometheus et Grafana.

## Contenu du dépôt

| Fichier ou dossier | Rôle |
|---|---|
| `app.py` | API Flask (modèle RandomForest entraîné au démarrage) |
| `requirements.txt` | Dépendances Python |
| `Dockerfile` | Construction de l'image (python:3.12-slim, gunicorn, utilisateur non-root) |
| `.dockerignore`, `.gitignore` | Fichiers exclus de l'image et du dépôt |
| `k8s/deployment.yaml` | Deployment : 2 réplicas, sondes sur `/health` |
| `k8s/service.yaml` | Service NodePort (port 30080) |
| `k8s/monitoring/prometheus.yaml` | Prometheus (port 30090) |
| `k8s/monitoring/grafana.yaml` | Grafana (port 30030) |

## Routes de l'API

| Route | Description |
|---|---|
| `/` | Message d'accueil |
| `/predict` | Prédiction : paramètres `sepal_length`, `sepal_width`, `petal_length`, `petal_width` |
| `/health` | État de l'application (utilisé par les sondes Kubernetes) |
| `/version` | Version déployée (variable `APP_VERSION`) |
| `/metrics` | Métriques au format Prometheus |

## 1. Lancer en local (Windows PowerShell)

Prérequis : Python 3.12 (scikit-learn n'était pas fiable avec Python 3.14).

```powershell
python -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python app.py
```

Test :

```powershell
curl.exe "http://localhost:8000/predict?sepal_length=5.1&sepal_width=3.5&petal_length=1.4&petal_width=0.2"
```

Résultat attendu : `{"confiance":1.0,"espece":"setosa"}`.

## 2. Construire et lancer l'image Docker

```powershell
docker build --build-arg APP_VERSION=1.0.0 -t tp-cicd-ml:1.0.0 .
docker run -d --name tp-cicd-ml -p 8080:8000 tp-cicd-ml:1.0.0
curl.exe http://localhost:8080/version
docker stop tp-cicd-ml
docker rm tp-cicd-ml
```

## 3. Déployer sur Kubernetes (Docker Desktop)

Activer Kubernetes dans Docker Desktop (Settings, Kubernetes), puis :

```powershell
kubectl get nodes
kubectl apply -f k8s/
kubectl get pods
curl.exe http://localhost:30080/health
```

L'image `tp-cicd-ml:1.0.0` doit exister localement : le cluster de Docker Desktop
réutilise les images construites sur le poste.

## 4. Monitoring

Prometheus découvre automatiquement les pods `tp-cicd-ml` et collecte `/metrics`
toutes les 15 secondes. Son accès est limité à la lecture des pods du namespace `default`.

Le mot de passe de Grafana est créé dans le cluster et n'est pas stocké dans Git :

```powershell
kubectl apply -f k8s/monitoring/prometheus.yaml
kubectl create secret generic grafana-admin -n monitoring --from-literal=password='CHOISIR_UN_MOT_DE_PASSE'
kubectl apply -f k8s/monitoring/grafana.yaml
```

- Prometheus : http://localhost:30090
- Grafana : http://localhost:30030 (utilisateur `admin`)

Requêtes PromQL utilisées dans les panneaux Grafana :

```
sum(rate(app_requests_total{route!="/health"}[1m])) by (route)
sum(increase(app_predictions_total[$__range])) by (espece)
count(up{job="tp-cicd-ml"} == 1)
```

## 5. Mise à jour et retour arrière

```powershell
docker build --build-arg APP_VERSION=1.1.0 -t tp-cicd-ml:1.1.0 .
kubectl set image deployment/tp-cicd-ml tp-cicd-ml=tp-cicd-ml:1.1.0
kubectl rollout status deployment/tp-cicd-ml

# Retour à la version précédente en cas de problème
kubectl rollout undo deployment/tp-cicd-ml

# Réaligner le cluster sur les fichiers du dépôt
kubectl apply -f k8s/
```

Si la nouvelle image échoue (par exemple une image inexistante), les anciens pods
continuent de servir l'application : Kubernetes ne les arrête que lorsque les nouveaux
sont prêts.

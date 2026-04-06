# 🛡️ CheckIA : Détecteur Local de Textes Générés par IA

**CheckIA** est une application web éducative conçue pour analyser la probabilité qu'un texte soit écrit par une intelligence artificielle (comme GPT-4, Claude ou Gemini). 

L'objectif principal est de fournir une solution **100% gratuite, locale et confidentielle** pour les institutions académiques, sans dépendre d'abonnements coûteux.

---

## 🏗️ Architecture du Projet

Le projet est divisé en deux parties principales communiquant via une API interne :

1.  **Plateforme Web (Port 8000) :** Laravel 11 + Vue.js 3 (Inertia.js). Gère l'interface utilisateur et la logique métier.
2.  **Moteur d'Analyse (Port 8001) :** Python FastAPI + Hugging Face Transformers. Exécute le modèle de Machine Learning en local.

---

## 🛠️ Stack Technique

| Composant | Technologie |
| :--- | :--- |
| **Frontend** | Vue.js 3, Tailwind CSS, Inertia.js |
| **Backend** | Laravel 11 (PHP 8.2+) |
| **Service IA** | Python 3.9+, FastAPI, Uvicorn |
| **Modèle NLP** | `roberta-base-openai-detector` (via Hugging Face) |
| **Deep Learning** | PyTorch / Transformers |

---

## 📂 Structure du Dossier `check-ia/`

```text
check-ia/
├── app/                # Logique Laravel (Controllers, Services)
├── ai-service/         # Micro-service Python (Moteur IA)
│   ├── main.py         # Point d'entrée FastAPI
│   └── requirements.txt# Dépendances Python
├── resources/
│   └── js/             # Composants Vue.js (Interface)
├── routes/             # Définition des routes Web et API
└── README.md           # Documentation (Ce fichier)
```

---

## 🚀 Installation et Configuration

### 1. Prérequis Système (Linux/Ubuntu)
Assurez-vous d'avoir installé les outils suivants sur votre machine :

```bash
sudo apt update
sudo apt install php-cli php-curl python3-venv python3-pip nodejs npm composer
```

### 2. Configuration du Backend Laravel
À la racine du dossier `check-ia/` :

```bash
composer install
npm install && npm run build
cp .env.example .env
php artisan key:generate
```

### 3. Configuration du Service IA (Python)
Dans le dossier `ai-service/` :

```bash
cd ai-service
python3 -m venv venv
source venv/bin/activate
pip install fastapi uvicorn transformers torch
```

---

## 🏃 Lancement de l'Application

Vous devez lancer **deux terminaux** simultanément :

### Terminal 1 : Le Moteur IA (Python)
```bash
cd ai-service
source venv/bin/activate
uvicorn main:app --host 127.0.0.1 --port 8001
```
*(Note : Au premier lancement, le modèle de 500 Mo sera téléchargé automatiquement).*

### Terminal 2 : L'Interface Web (Laravel)
```bash
php artisan serve
```
L'application sera accessible sur : **http://127.0.0.1:8000**

---

## 🔍 Fonctionnement de la Détection

L'analyse repose sur le modèle **RoBERTa-base-OpenAI-Detector**. Contrairement à une simple recherche de mots-clés, il analyse :

*   **La Perplexité :** Le degré de surprise du texte pour un modèle de langue.
*   **La Constance :** L'uniformité des probabilités de mots (typique des IA).

### Interprétation des résultats :
*   🟢 **0% - 35%** : Probablement écrit par un Humain.
*   🟡 **35% - 70%** : Texte ambigu (possiblement édité par IA ou humain très scolaire).
*   🔴 **70% - 100%** : Très forte probabilité de génération par IA.

---

## ⚠️ Limites Importantes

*   **Taille du texte :** Pour une précision optimale, le texte doit contenir au moins **200 caractères**.
*   **Langue :** Le modèle actuel est optimisé pour l'anglais et le français standard.
*   **Éthique :** Ce score est une **estimation statistique**. Il ne doit jamais être la seule preuve pour sanctionner un étudiant.

---

## 👨‍💻 Développeur
**M. Florent BEZARA**  
*Enseignant-Chercheur & Développeur Backend*  
Mahajanga, Madagascar.
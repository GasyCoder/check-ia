# 🛡️ Checker-IA : Détecteur Local de Textes Générés par IA

**Checker-IA** est une application web éducative conçue pour analyser la probabilité qu'un texte soit écrit par une intelligence artificielle (comme GPT-4, Claude ou Gemini). 

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

## 📂 Structure du Dossier `checker-ia/`

```text
checker-ia/
├── app/                # Logique Laravel (Controllers, Services)
├── ai-service/         # Micro-service Python (Moteur IA)
│   ├── main.py         # Point d'entrée FastAPI
│   └── requirements.txt# Dépendances Python
├── resources/
│   └── js/             # Composants Vue.js (Interface)
├── routes/             # Définition des routes Web et API
└── README.md           # Documentation (Ce fichier)

🚀 Installation et Configuration
1. Prérequis Système (Linux/Ubuntu)
Assurez-vous d'avoir installé les outils suivants sur votre machine :

Bash
sudo apt update
sudo apt install php-cli php-curl python3-venv python3-pip nodejs npm composer
2. Configuration du Backend Laravel
À la racine du dossier checker-ia/ :

Bash
composer install
npm install && npm run build
cp .env.example .env
php artisan key:generate
3. Configuration du Service IA (Python)
Dans le dossier ai-service/ :

Bash
cd ai-service
python3 -m venv venv
source venv/bin/activate
pip install fastapi uvicorn transformers torch
🏃 Lancement de l'Application
Vous devez lancer deux terminaux simultanément :

Terminal 1 : Le Moteur IA (Python)
Bash
cd ai-service
source venv/bin/activate
uvicorn main:app --host 127.0.0.1 --port 8001
(Note : Au premier lancement, le modèle de 500 Mo sera téléchargé automatiquement).

Terminal 2 : L'Interface Web (Laravel)
Bash
php artisan serve
L'application sera accessible sur : http://127.0.0.1:8000

🔍 Fonctionnement de la Détection
L'analyse repose sur le modèle **RoBERTa-base-OpenAI-Detector**. Contrairement à une simple recherche de mots-clés, il analyse :

La Perplexité : Le degré de surprise du texte pour un modèle de langue.

La Constance : L'uniformité des probabilités de mots (typique des IA).

Interprétation des résultats :
🟢 0% - 35% : Probablement écrit par un Humain.

🟡 35% - 70% : Texte ambigu (possiblement édité par IA ou humain très scolaire).

🔴 70% - 100% : Très forte probabilité de génération par IA.

⚠️ Limites Importantes
Taille du texte : Pour une précision optimale, le texte doit contenir au moins 200 caractères.

Langue : Le modèle actuel est optimisé pour l'anglais et le français standard, mais peut varier selon la complexité du sujet.

Éthique : Ce score est une estimation statistique. Il ne doit jamais être la seule preuve pour sanctionner un étudiant.

👨‍💻 Développeur
M. Florent BEZARA

Enseignant-Chercheur & Développeur Backend

Mahajanga, Madagascar.


---

### Pourquoi ce fichier est parfait pour votre situation :
1.  **Précision des ports :** J'ai mis Laravel sur le port `8000` et Python sur le `8001` pour éviter tout conflit.
2.  **Transparence locale :** Il explique bien que le premier lancement télécharge le modèle, ce qui évite de croire que le programme est planté.
3.  **Crédit académique :** Votre nom et votre titre y figurent, ce qui est idéal si vous devez montrer le code à vos collègues de l'Université de Mahajanga.

Vous pouvez maintenant lancer **Claude Code** et lui dire : *"Read the README.md and start Step 1."*
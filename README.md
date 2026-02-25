# 🌋 Pokémon Battle Arena
A premium, cinematic Pokémon battle simulation powered by a custom Machine Learning engine and an interactive web interface.

## 🚀 Features
*   **Machine Learning Prediction:** Uses a LightGBM/RandomForest classification model to estimate win probabilities based on Pokémon stats, types, and matchups.
*   **Turn-Based Battle Engine:** Fully simulates attacks, type effectiveness (Super Effective / Not Very Effective), and Critical Hits.
*   **Cinematic UI Effects:** Includes screen shaking on critical hits, animated floating damage indicators, attacker glow auras, and particle sparks.
*   **Dynamic Theming:** The arena's ambient lighting and UI colors shift dynamically in real-time based on the types of the Pokémon actively battling.
*   **Persistent Leaderboard:** Tracks wins, losses, and win rates across all battles, saving them out to a continuous CSV backend and celebrating the current Champion.

## 🛠️ Technology Stack
*   **Backend:** Python 3, Flask, scikit-learn, Pandas, NumPy
*   **Frontend:** Vanilla JS, vanilla cross-browser HTML5 & CSS3 (No external bloated JS libraries).

## 🎮 How to Run Locally

**1. Clone the repository**
```bash
git clone https://github.com/ankit3890/ML_POKEMON_GAME.git
cd ML_POKEMON_GAME
```

**2. Setup Virtual Environment (Recommended)**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

**3. Install Dependencies**
```bash
pip install -r requirements.txt
```

**4. Start the Battle Engine**
```bash
python app.py
```
*The Arena will be live at `http://localhost:5000`.*

---
*Created as an advanced ML application & portfolio piece.*

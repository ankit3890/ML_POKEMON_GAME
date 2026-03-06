from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import pandas as pd
import numpy as np
import os
from pokemon_analysis import prepare_data, simulate_turn_battle
import pickle
import gzip

app = Flask(__name__)
CORS(app)

# ===============================
# DATA LOAD & INITIALIZATION
# ===============================
print("Loading Pokémon data...")
bk, encoded_df, df_ml, _ = prepare_data()
print("Data loaded successfully!")

LEADERBOARD_FILE = "leaderboard.csv"

def init_leaderboard(bk):
    if not os.path.exists(LEADERBOARD_FILE):
        lb = pd.DataFrame({
            "name": bk["name"],
            "wins": 0,
            "losses": 0
        })
        lb.to_csv(LEADERBOARD_FILE, index=False)

def update_leaderboard(winner_name, loser_name):
    lb = pd.read_csv(LEADERBOARD_FILE)
    lb.loc[lb["name"] == winner_name, "wins"] += 1
    lb.loc[lb["name"] == loser_name, "losses"] += 1
    lb.to_csv(LEADERBOARD_FILE, index=False)

def get_sorted_leaderboard():
    lb = pd.read_csv(LEADERBOARD_FILE)
    lb["total_matches"] = lb["wins"] + lb["losses"]
    lb["win_rate"] = np.where(
        lb["total_matches"] > 0,
        lb["wins"] / lb["total_matches"],
        0
    )
    lb = lb.sort_values(by=["wins", "win_rate"], ascending=False)
    return lb

init_leaderboard(bk)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/pokemon')
def get_pokemon():
    pokemon_list = []
    # Use bk for original names and pokedex numbers
    for idx, row in bk.iterrows():
        pokemon_list.append({
            "name": row['name'],
            "pokedex_number": int(row['pokedex_number']),
            "type1": str(row['type1']).lower(),
            "type2": str(row['type2']).lower() if pd.notna(row['type2']) else "none",
            "hp": int(row['hp']),
            "attack": int(row['attack']),
            "defense": int(row['defense']),
            "sp_attack": int(row["sp_attack"]),
            "sp_defense": int(row["sp_defense"]),
            "speed": int(row["speed"]),
            "height_m": float(row["height_m"]) if "height_m" in row and pd.notna(row["height_m"]) else 0.0,
            "weight_kg": float(row["weight_kg"]) if "weight_kg" in row and pd.notna(row["weight_kg"]) else 0.0,
            "bmi": float(row["bmi"]) if "bmi" in row and pd.notna(row["bmi"]) else 0.0
        })
    return jsonify(sorted(pokemon_list, key=lambda x: x['name']))

@app.route('/api/predict', methods=['POST'])
def predict():
    data = request.json
    p1_name = data.get('p1')
    p2_name = data.get('p2')

    p1_data = encoded_df[encoded_df["name"] == p1_name].iloc[0]
    p2_data = encoded_df[encoded_df["name"] == p2_name].iloc[0]

    # Heuristic probability calculation
    p1_total = p1_data['hp'] + p1_data['attack'] + p1_data['defense'] + p1_data['sp_attack'] + p1_data['sp_defense'] + p1_data['speed']
    p2_total = p2_data['hp'] + p2_data['attack'] + p2_data['defense'] + p2_data['sp_attack'] + p2_data['sp_defense'] + p2_data['speed']
    
    total = p1_total + p2_total
    p1_prob = p1_total / total if total > 0 else 0.5
    p2_prob = p2_total / total if total > 0 else 0.5
    
    # Adjust slightly based on speed
    if p1_data['speed'] > p2_data['speed']:
        p1_prob = min(0.99, p1_prob + 0.05)
        p2_prob = max(0.01, p2_prob - 0.05)
    elif p2_data['speed'] > p1_data['speed']:
        p2_prob = min(0.99, p2_prob + 0.05)
        p1_prob = max(0.01, p1_prob - 0.05)
    
    return jsonify({
        "p1_prob": float(p1_prob),
        "p2_prob": float(p2_prob)
    })

@app.route('/api/battle', methods=['POST'])
def battle():
    data = request.json
    p1_name = data.get('p1')
    p2_name = data.get('p2')

    p1_data = encoded_df[encoded_df["name"] == p1_name].iloc[0]
    p2_data = encoded_df[encoded_df["name"] == p2_name].iloc[0]

    winner, history = simulate_turn_battle(p1_data, p2_data, bk)
    
    if winner == 1:
        update_leaderboard(p1_name, p2_name)
    else:
        update_leaderboard(p2_name, p1_name)
    
    return jsonify({
        "winner": int(winner),
        "history": history,
        "p1_stats": {k: int(v) for k, v in p1_data[['hp', 'attack', 'defense', 'sp_attack', 'sp_defense', 'speed']].to_dict().items()},
        "p2_stats": {k: int(v) for k, v in p2_data[['hp', 'attack', 'defense', 'sp_attack', 'sp_defense', 'speed']].to_dict().items()}
    })

@app.route('/api/leaderboard')
def leaderboard():
    lb = get_sorted_leaderboard()
    # Replace NaN or infinites if any just in case, though handled by np.where
    # Convert dataframe back to dictionary array
    return jsonify(lb.head(20).to_dict(orient='records'))


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

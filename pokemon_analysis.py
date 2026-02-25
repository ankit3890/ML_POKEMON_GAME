import kagglehub
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import os
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier

def prepare_data():
    # Prefer local CSV for deployment
    if os.path.exists("pokemon.csv"):
        bk = pd.read_csv("pokemon.csv")
    else:
        # Download latest version as fallback
        path = kagglehub.dataset_download("maca11/all-pokemon-dataset")
        df1 = pd.read_csv(os.path.join(path, "All_Pokemon.csv"))
        df1.columns = df1.columns.str.strip()
        df_new = df1.rename(columns={
            "Number": "pokedex_number", "Name": "name", "Type 1": "type1", "Type 2": "type2",
            "HP": "hp", "Att": "attack", "Def": "defense", "Spa": "sp_attack", "Spd": "sp_defense", "Spe": "speed",
            "Legendary": "is_legendary", "Height": "height_m", "Weight": "weight_kg", "Catch Rate": "capture_rate"
        })
        df_new.columns = df_new.columns.str.replace("Against ", "against_", regex=False).str.lower().str.replace(" ", "_")
        df_new["type2"] = df_new["type2"].fillna("none")
        df_new = df_new.rename(columns={"bst": "base_total"})
        
        df_new["height_m"] = pd.to_numeric(df_new["height_m"], errors="coerce")
        df_new["weight_kg"] = pd.to_numeric(df_new["weight_kg"], errors="coerce")
        df_new["height_m"] = df_new["height_m"].fillna(df_new["height_m"].median())
        df_new["weight_kg"] = df_new["weight_kg"].fillna(df_new["weight_kg"].median())
        df_new["bmi"] = df_new["weight_kg"] / (df_new["height_m"] ** 2)
        df_new["bmi"] = df_new["bmi"].fillna(0)
        
        bk = df_new.copy()
        bk.to_csv("pokemon.csv", index=False)
    
    df = bk.copy()

    # Feature Engineering
    df["physical_power"] = df["attack"] + df["defense"]
    df["special_power"] = df["sp_attack"] + df["sp_defense"]
    df["total_combat"] = df["physical_power"] + df["special_power"] + df["speed"]
    df["speed_ratio"] = df["speed"] / df["base_total"]
    df["bulk"] = df["hp"] + df["defense"] + df["sp_defense"]

    type_cols = [col for col in df.columns if "against_" in col]
    df["avg_type_resistance"] = df[type_cols].mean(axis=1)
    df["max_weakness"] = df[type_cols].max(axis=1)

    # Cleaning
    drop_cols = ["japanese_name", "pokedex_number", "classfication", "abilities"] # Kept 'name' for lookup
    df = df.drop(columns=[col for col in drop_cols if col in df.columns])
    df["type2"] = df["type2"].fillna("None")
    if 'percentage_male' in df.columns:
        df = df.drop(['percentage_male'], axis=1)
    df["capture_rate"] = pd.to_numeric(df["capture_rate"], errors="coerce")
    df["capture_rate"] = df["capture_rate"].fillna(df["capture_rate"].median())
    df = df.drop_duplicates()

    # Handle Outliers
    numeric_cols = df.select_dtypes(include=["int64","float64"]).columns
    for col in numeric_cols:
        q1 = df[col].quantile(0.25)
        q3 = df[col].quantile(0.75)
        iqr = q3 - q1
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
        df[col] = df[col].clip(lower, upper)

    # Pre-encoding data for lookup
    pre_encoded_df = df.copy()

    # Encoding for ML
    df_ml = pd.get_dummies(df.drop(columns=['name']), columns=["type1","type2","generation"], drop_first=True)
    df_ml["is_legendary"] = df_ml["is_legendary"].astype(int)
    bool_cols = df_ml.select_dtypes(include=["bool"]).columns
    df_ml[bool_cols] = df_ml[bool_cols].astype(int)
    
    # Drop all unused text strings from the maca11 dataset (Dex Entry, Growth Rate, etc.)
    df_ml = df_ml.select_dtypes(exclude=['object', 'string'])

    # Train Model
    battle_df = generate_battles(df_ml, bk, n_battles=5000)
    X = battle_df.drop("winner", axis=1)
    y = battle_df["winner"]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    model = RandomForestClassifier(n_estimators=200, random_state=42)
    model.fit(X_train, y_train)

    return bk, pre_encoded_df, df_ml, model

def simulate_battle(p1, p2, bk):
    # Base damage
    p1_damage = (p1["attack"] / p2["defense"]) * p1["speed"]
    p2_damage = (p2["attack"] / p1["defense"]) * p2["speed"]

    p1_name_idx = bk[bk["name"] == p1.name].index[0] if isinstance(p1.name, str) else p1.name
    p2_name_idx = bk[bk["name"] == p2.name].index[0] if isinstance(p2.name, str) else p2.name

    p1_types = [str(bk.loc[p1_name_idx, "type1"]).lower(), str(bk.loc[p1_name_idx, "type2"]).lower()]
    p2_types = [str(bk.loc[p2_name_idx, "type1"]).lower(), str(bk.loc[p2_name_idx, "type2"]).lower()]

    type_mapping = {"fighting": "fight"}

    p1_multiplier = 1
    for t in p1_types:
        if t not in ["nan", "none"]:
            col = f"against_{type_mapping.get(t, t)}"
            p1_multiplier = max(p1_multiplier, p2.get(col, 1))

    p2_multiplier = 1
    for t in p2_types:
        if t not in ["nan", "none"]:
            col = f"against_{type_mapping.get(t, t)}"
            p2_multiplier = max(p2_multiplier, p1.get(col, 1))

    p1_damage *= p1_multiplier
    p2_damage *= p2_multiplier
    p1_damage *= np.random.uniform(0.85, 1.2)
    p2_damage *= np.random.uniform(0.85, 1.2)

    p1_score = p1_damage + (p1["hp"] + p1["sp_defense"])
    p2_score = p2_damage + (p2["hp"] + p2["sp_defense"])

    return 1 if p1_score > p2_score else 0

def generate_battles(df_ml, bk, n_battles=5000):
    battles = []
    for _ in range(n_battles):
        p1 = df_ml.sample(1).iloc[0]
        p2 = df_ml.sample(1).iloc[0]
        winner = simulate_battle(p1, p2, bk)
        battle_features = {}
        for col in df_ml.columns:
            if col != "is_legendary":
                battle_features[f"p1_{col}"] = p1[col]
                battle_features[f"p2_{col}"] = p2[col]
        battle_features["winner"] = winner
        battles.append(battle_features)
    return pd.DataFrame(battles)

def simulate_turn_battle(p1, p2, bk):
    p1_hp = p1["hp"]
    p2_hp = p2["hp"]
    max_p1_hp = p1["hp"]
    max_p2_hp = p2["hp"]
    
    log = []
    history = []
    
    type_mapping = {"fighting": "fight"}

    if p1["speed"] >= p2["speed"]:
        first, second = p1, p2
        first_id, second_id = "P1", "P2"
    else:
        first, second = p2, p1
        first_id, second_id = "P2", "P1"

    round_num = 1
    while p1_hp > 0 and p2_hp > 0 and round_num <= 100:
        round_log = []
        
        # First attacks
        phys = np.random.rand() < 0.5
        attack_type = "Physical" if phys else "Special"
        damage = (first["attack"] / second["defense"]) * 10 if phys else (first["sp_attack"] / second["sp_defense"]) * 10
        
        first_idx = bk[bk["name"] == first["name"]].index[0]
        second_idx = bk[bk["name"] == second["name"]].index[0]
        first_types = [str(bk.loc[first_idx, "type1"]).lower(), str(bk.loc[first_idx, "type2"]).lower()]
        second_types = [str(bk.loc[second_idx, "type1"]).lower(), str(bk.loc[second_idx, "type2"]).lower()]

        multiplier = 1
        for t in first_types:
            if t not in ["nan", "none"]:
                col = f"against_{type_mapping.get(t, t)}"
                multiplier = max(multiplier, bk.loc[second_idx, col])
        
        damage *= multiplier
        damage *= np.random.uniform(0.85, 1.0)
        crit = False
        if np.random.rand() < 0.06:
            damage *= 1.5
            crit = True

        msg = f"{first['name']} uses {attack_type}! "
        if multiplier > 1: msg += "✨ Super effective! "
        elif multiplier < 1 and multiplier != 0: msg += "🍃 Not very effective... "
        elif multiplier == 0: msg += "😶 No effect! "
        if crit: msg += "💥 Critical hit! "
        msg += f"({damage:.1f} damage)"

        if first_id == "P1":
            p2_hp -= damage
        else:
            p1_hp -= damage
        
        round_log.append(msg)
        
        if p1_hp <= 0 or p2_hp <= 0:
            history.append({"round": int(round_num), "log": round_log, "p1_hp": float(max(0, p1_hp)), "p2_hp": float(max(0, p2_hp))})
            break

        # Second attacks
        phys = np.random.rand() < 0.5
        attack_type = "Physical" if phys else "Special"
        damage = (second["attack"] / first["defense"]) * 10 if phys else (second["sp_attack"] / first["sp_defense"]) * 10
        
        multiplier = 1
        for t in second_types:
            if t not in ["nan", "none"]:
                col = f"against_{type_mapping.get(t, t)}"
                multiplier = max(multiplier, bk.loc[first_idx, col])
        
        damage *= multiplier
        damage *= np.random.uniform(0.85, 1.0)
        crit = False
        if np.random.rand() < 0.06:
            damage *= 1.5
            crit = True

        msg = f"{second['name']} uses {attack_type}! "
        if multiplier > 1: msg += "✨ Super effective! "
        elif multiplier < 1 and multiplier != 0: msg += "🍃 Not very effective... "
        elif multiplier == 0: msg += "😶 No effect! "
        if crit: msg += "💥 Critical hit! "
        msg += f"({damage:.1f} damage)"

        if first_id == "P1":
            p1_hp -= damage
        else:
            p2_hp -= damage
            
        round_log.append(msg)
        history.append({"round": int(round_num), "log": round_log, "p1_hp": float(max(0, p1_hp)), "p2_hp": float(max(0, p2_hp))})
        round_num += 1

    winner = 1 if p1_hp > 0 else 0
    return winner, history

if __name__ == "__main__":
    bk, encoded_df, df_ml, model = prepare_data()
    print("Data Prepared!")
    p1 = encoded_df[encoded_df["name"] == "Pikachu"].iloc[0]
    p2 = encoded_df[encoded_df["name"] == "Charizard"].iloc[0]
    winner, history = simulate_turn_battle(p1, p2, bk)
    print(f"Winner: {winner}")
    for h in history:
        print(f"Round {h['round']}: {h['log']}")

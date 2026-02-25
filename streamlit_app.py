import streamlit as st
import pandas as pd
import numpy as np
import os
from pokemon_analysis import prepare_data, simulate_turn_battle

# Page Config
st.set_page_config(page_title="Pokémon Battle Arena", page_icon="⚡", layout="wide")

# Custom CSS for basic styling
st.markdown("""
<style>
    .stButton>button {
        width: 100%;
        height: 60px;
        font-size: 24px;
        font-weight: bold;
        background: linear-gradient(45deg, #FF416C, #FF4B2B);
        color: white;
        border-radius: 10px;
        border: none;
    }
    .stButton>button:hover {
        background: linear-gradient(45deg, #FF4B2B, #FF416C);
    }
    .stat-box {
        background-color: #1e1e1e;
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

# Application Header
st.title("⚡ Pokémon Battle Arena")
st.markdown("Select two Pokémon and watch them battle using Machine Learning heuristics!")

# Load Data
@st.cache_data
def load_pokemon_data():
    bk, encoded_df, df_ml, _ = prepare_data()
    pokemon_list = bk.sort_values(by="name").to_dict('records')
    return bk, encoded_df, df_ml, pokemon_list

try:
    bk, encoded_df, df_ml, pokemon_list = load_pokemon_data()
    pokemon_names = [p["name"] for p in pokemon_list]
except Exception as e:
    st.error(f"Failed to load dataset: {e}")
    st.stop()

# Layout
col1, col2 = st.columns(2)

with col1:
    st.subheader("Player 1")
    p1_name = st.selectbox("Select Pokémon 1", pokemon_names, index=pokemon_names.index("Pikachu") if "Pikachu" in pokemon_names else 0)
    p1_data = next(p for p in pokemon_list if p["name"] == p1_name)
    
    st.image(f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/{int(p1_data['pokedex_number'])}.png", width=250)
    
    st.markdown(f"""
    <div class="stat-box">
        <h4>{p1_name}</h4>
        <b>Type:</b> {p1_data['type1'].capitalize()} {('/ ' + p1_data['type2'].capitalize()) if p1_data['type2'] != 'none' else ''}<br>
        <b>HP:</b> {p1_data['hp']} | <b>Speed:</b> {p1_data['speed']}<br>
        <b>Attack:</b> {p1_data['attack']} | <b>Defense:</b> {p1_data['defense']}<br>
        <b>Sp. Atk:</b> {p1_data['sp_attack']} | <b>Sp. Def:</b> {p1_data['sp_defense']}<br>
        <hr>
        <b>Height:</b> {p1_data.get('height_m', 0)}m | <b>Weight:</b> {p1_data.get('weight_kg', 0)}kg | <b>BMI:</b> {p1_data.get('bmi', 0):.1f}
    </div>
    """, unsafe_allow_html=True)


with col2:
    st.subheader("Player 2")
    p2_name = st.selectbox("Select Pokémon 2", pokemon_names, index=pokemon_names.index("Charizard") if "Charizard" in pokemon_names else 1)
    p2_data = next(p for p in pokemon_list if p["name"] == p2_name)
    
    st.image(f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/{int(p2_data['pokedex_number'])}.png", width=250)
    
    st.markdown(f"""
    <div class="stat-box">
        <h4>{p2_name}</h4>
        <b>Type:</b> {p2_data['type1'].capitalize()} {('/ ' + p2_data['type2'].capitalize()) if p2_data['type2'] != 'none' else ''}<br>
        <b>HP:</b> {p2_data['hp']} | <b>Speed:</b> {p2_data['speed']}<br>
        <b>Attack:</b> {p2_data['attack']} | <b>Defense:</b> {p2_data['defense']}<br>
        <b>Sp. Atk:</b> {p2_data['sp_attack']} | <b>Sp. Def:</b> {p2_data['sp_defense']}<br>
        <hr>
        <b>Height:</b> {p2_data.get('height_m', 0)}m | <b>Weight:</b> {p2_data.get('weight_kg', 0)}kg | <b>BMI:</b> {p2_data.get('bmi', 0):.1f}
    </div>
    """, unsafe_allow_html=True)

# Battle Heuristics Prediction
st.markdown("---")
st.subheader("🔮 Pre-Battle Prediction")

# Match Vercel's fast heuristic math
p1_total = p1_data['hp'] + p1_data['attack'] + p1_data['defense'] + p1_data['sp_attack'] + p1_data['sp_defense'] + p1_data['speed']
p2_total = p2_data['hp'] + p2_data['attack'] + p2_data['defense'] + p2_data['sp_attack'] + p2_data['sp_defense'] + p2_data['speed']
total = p1_total + p2_total
p1_prob = p1_total / total if total > 0 else 0.5
p2_prob = p2_total / total if total > 0 else 0.5

if p1_data['speed'] > p2_data['speed']:
    p1_prob = min(0.99, p1_prob + 0.05)
    p2_prob = max(0.01, p2_prob - 0.05)
elif p2_data['speed'] > p1_data['speed']:
    p2_prob = min(0.99, p2_prob + 0.05)
    p1_prob = max(0.01, p1_prob - 0.05)

st.progress(float(p1_prob), text=f"Win Probability: {p1_name} ({p1_prob*100:.1f}%) vs {p2_name} ({p2_prob*100:.1f}%)")

# Battle Execution
st.markdown("<br>", unsafe_allow_html=True)
if st.button("⚔️ START BATTLE ⚔️"):
    p1_enc = encoded_df[encoded_df["name"] == p1_name].iloc[0]
    p2_enc = encoded_df[encoded_df["name"] == p2_name].iloc[0]
    
    with st.spinner("Simulating battle..."):
        winner, history = simulate_turn_battle(p1_enc, p2_enc, bk)
        
        st.success(f"🏆 {p1_name if winner == 1 else p2_name} wins the battle!")
        
        st.subheader("Battle Log")
        for log_entry in history:
            st.markdown(f"**Round {log_entry['round']}**")
            for msg in log_entry['log']:
                st.write(f"- {msg}")
            
            # Display remaining HP
            hp_col1, hp_col2 = st.columns(2)
            with hp_col1:
                st.caption(f"{p1_name} HP: {max(0, log_entry['p1_hp']):.1f} / {p1_data['hp']}")
            with hp_col2:
                st.caption(f"{p2_name} HP: {max(0, log_entry['p2_hp']):.1f} / {p2_data['hp']}")
            st.divider()

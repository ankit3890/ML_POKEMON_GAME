import pickle
from pokemon_analysis import prepare_data

print("Training model and saving to cache...")
bk, encoded_df, df_ml, model = prepare_data()

with open("model_cache.pkl", "wb") as f:
    pickle.dump({
        "bk": bk,
        "encoded_df": encoded_df,
        "df_ml": df_ml,
        "model": model
    }, f)

print("model_cache.pkl generated successfully!")

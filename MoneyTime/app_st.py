import os
import numpy as np
import keras.losses
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from keras.models import load_model
from keras.utils import get_custom_objects
from sklearn.preprocessing import MinMaxScaler
from Utils import fetch_binance_data, enrich_features

# ----------------------------------------------------------------------------------------------------------------------------------------------------

get_custom_objects().update({"mse": keras.losses.mean_squared_error})

st.set_page_config(page_title="🔮 Prédiction Crypto - LSTM", layout="wide")
st.title("Prédiction Crypto - LSTM")

crypto_symbol = st.selectbox("Choisir une cryptomonnaie", ["BTCUSDT"])
prediction_type = st.selectbox("Choisir l'horizon de prédiction", ["Court Terme", "Moyen Terme", "Long Terme"])
predict_button = st.button("Prédire")

horizons = {
    "Court Terme": {
        "model": "lstm_btc_usdt_1h_CT.h5",
        "interval": "1h",
        "seq_len": 24,
        "suffix": "_CT"
    },
    "Moyen Terme": {
        "model": "lstm_btc_usdt_1d_MT.h5",
        "interval": "1d",
        "seq_len": 14,
        "suffix": "_MT"
    },
    "Long Terme": {
        "model": "lstm_btc_usdt_1M_LT.h5",
        "interval": "1M",
        "seq_len": 60,
        "suffix": "_LT"
    }
}

if predict_button:
    st.info(f"📡 Récupération des données pour {crypto_symbol}...")
    params = horizons[prediction_type]
    df = fetch_binance_data(crypto_symbol, params["interval"], 300)
    df = enrich_features(df)

    if df.shape[0] < params["seq_len"]:
        st.error("Pas assez de données pour générer une prédiction.")
    else:
        # Normalisation et séquencage
        features = df.drop(columns=["date"]).values
        scaler = MinMaxScaler()
        features_scaled = scaler.fit_transform(features)


        def create_sequence(X, seq_len):
            return np.array([X[i - seq_len:i] for i in range(seq_len, len(X))])


        X_seq = create_sequence(features_scaled, params["seq_len"])
        dates = df["date"].values[params["seq_len"]:]

        model_path = os.path.join("modeles", params["model"])

        if not os.path.exists(model_path):
            st.error(f"Modèle introuvable : {model_path}")
        else:
            try:
                model = load_model(model_path)
                preds = model.predict(X_seq)

                reg_pred = preds[0][-1][0] if isinstance(preds, list) else preds[-1][0]
                class_pred = preds[1][-1][0] if isinstance(preds, list) and len(preds) > 1 else None

                st.success(f"Prédiction pour {crypto_symbol} ({prediction_type}) terminée.")
                st.metric("🔢 % Évolution prédite", f"{reg_pred:.2f}%")
                if class_pred is not None:
                    tendance = "📉 Baisse probable" if class_pred < 0.5 else "📈 Hausse probable"
                    st.write(f"Prédiction de tendance : **{tendance}**")


                fig = go.Figure()
                # df = df.iloc[-params["seq_len"]:]
                df = df.iloc[-150:]
                fig.add_trace(go.Scatter(x=df["date"], y=df["close"], mode='lines', name='Prix réel'))
                last_price = df["close"].iloc[-1]
                predicted_price = last_price * (1 + reg_pred / 100)
                days_ahead = 1 if prediction_type == "Court Terme" else (7 if prediction_type == "Moyen Terme" else 30)
                fig.add_trace(go.Scatter(
                    x=[df["date"].iloc[-1], df["date"].iloc[-1] + pd.Timedelta(days=days_ahead)],
                    y=[last_price, predicted_price],
                    mode='lines+markers',
                    name='Prédiction',
                    line=dict(dash='dash', color='orange')
                ))
                fig.update_layout(title="Prix réel et prédiction",
                                  xaxis_title="Date", yaxis_title="Prix (USDT)", height=500)
                # st.plotly_chart(fig, use_container_width=True)
                st.plotly_chart(fig, width="stretch")

                st.subheader("Dernières données enrichies utilisées")
                st.dataframe(df.tail(10).style.format("{:.4f}"),width="stretch")

                csv = df.to_csv(index=False).encode("utf-8")
                st.download_button("Télécharger les données enrichies (CSV)", csv,
                                   file_name=f"{crypto_symbol}_features.csv",
                                   mime="text/csv")

            except Exception as e:
                st.error(f"Erreur lors de la prédiction : {e}")

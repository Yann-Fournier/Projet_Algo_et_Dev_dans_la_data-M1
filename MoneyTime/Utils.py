import ta
import requests
import numpy as np
import pandas as pd
import mplfinance as mpf
from keras.models import Sequential
from sklearn.preprocessing import MinMaxScaler
from keras.layers import LSTM, Dense, Dropout, Input

# TA-lib
from ta.trend import MACD, EMAIndicator
from ta.momentum import RSIIndicator, StochasticOscillator
from ta.volatility import BollingerBands, AverageTrueRange
from ta.volume import OnBalanceVolumeIndicator, AccDistIndexIndicator


# Indicateurs techniques ------------------------------------------------------------------------------------------------------
def rsi(df: pd.DataFrame) -> pd.DataFrame:
    """
    Fonction pour calculer l'indicateur RSI (Relative Strength Index) et sa moyenne sur 14 unitées de temps.

    Args:
        df (pd.Dataframe): dataframe contenant les données de prix avec une colonne 'close'.

    Returns:
        pd.Dataframe: retourne le dataframe avec les colonnes 'rsi' et 'rsima' ajoutées.
    """
    df["rsi"] = ta.momentum.rsi(df['close'], 14) # rsi avec une periode de 14 unitées de temps
    df['rsima'] = df['rsi'].rolling(14).mean() # une moyenne des 14 dernières unitées de temps
    return df

def macd(df: pd.DataFrame) -> pd.DataFrame:
    """
    Fonction pour calculer l'indicateur MACD (Moving Average Convergence Divergence) et ses composantes.

    Args:
        df (pd.Dataframe): dataframe contenant les données de prix avec une colonne 'close'.

    Returns:
        pd.Dataframe: retourne le dataframe avec les colonnes 'macd', 'macd_diff' et 'macd_signal' ajoutées.
    """
    # macd avec une période lente de 26 unitées de temps et une période rapide de 12 unitées de temps
    df["macd"] = ta.trend.macd(close=df["close"], window_slow=26, window_fast=12)
    # macd différence avec une période lente de 26 unitées de temps et une période rapide de 12 unitées de temps
    df["macd_diff"] = ta.trend.macd_diff(close=df["close"], window_slow=26, window_fast=12)
    # macd signal avec une période lente de 26 unitées de temps et une période rapide de 12 unitées de temps
    df["macd_signal"] = ta.trend.macd_signal(close=df["close"], window_slow=26, window_fast=12, window_sign=9, fillna=False)
    return df

def stochastique(df: pd.DataFrame) -> pd.DataFrame:
    """
    Fonction pour calculer l'indicateur Stochastique et ses moyennes.

    Args:
        df (pd.Dataframe): dataframe contenant les données de prix avec une colonne 'close'.

    Returns:
        pd.Dataframe: retourne le dataframe avec les colonnes 'stock_%K' et 'stock_%D' ajoutées.
    """
    # Stochastique avec une periode de 14 unitées de temps
    df["stoch_%K"] = ta.momentum.stoch(high=df["high"], low=df["low"], close=df["close"], window= 14,smooth_window=3, fillna=False)
    # moyenne des trois dernières unitées de temps du Stochastique
    df["stoch_%D"] = df['stoch_%K'].rolling(3).mean()
    return df

def bollinger_bands(df: pd.DataFrame) -> pd.DataFrame:
    """
    Fonction pour calculer les bandes de Bollinger et les ajouter au dataframe.

    Args:
        df (pd.Dataframe): dataframe contenant les données de prix avec une colonne 'close'.

    Returns:
        pd.Dataframe: retourne le dataframe avec les colonnes 'lower_band', 'higher_band' et 'ma_band' ajoutées.
    """
    # Bandes de Bollinger effectuer sur une période de 20 unitées de temps
    bol_band = ta.volatility.BollingerBands(close=df["close"], window=20, window_dev=2.25)
    df["lower_band"] = bol_band.bollinger_lband()
    df["higher_band"] = bol_band.bollinger_hband()
    df["ma_band"] = bol_band.bollinger_mavg()
    return df

def moyenne_mobile(df: pd.DataFrame) -> pd.DataFrame:
    """
    Fonction pour calculer les moyennes mobiles et les ajouter au dataframe.

    Args:
        df (pd.Dataframe): dataframe contenant les données de prix avec une colonne 'close'.

    Returns:
        pd.Dataframe: retourne le dataframe avec les colonnes 'sma9' et 'sma21' ajoutées.
    """
    df["sma9"] = df['close'].rolling(9).mean() # moyenne des 9 dernières unitées de temps du prix de fermeture de session
    df["sma21"] = df['close'].rolling(21).mean() # moyenne des 21 dernières unitées de temps du prix de fermeture de session
    return df


# Graphiques ------------------------------------------------------------------------------------------------------
def simple_plot(df: pd.DataFrame, val: str) -> None: # création d'un graphique simple (que la valeur)
    """
    Fonction pour tracer un graphique simple avec les données de prix.

    Args:
        df (pd.Dataframe): dataframe contenant les données de prix.
        val (str): titre du graphique.
    """
    df_plot = df.copy().iloc[-150:] # on prend les 150 dernières valeurs du dataset.
    s = mpf.make_mpf_style(base_mpf_style='charles', rc={'font.size': 6}) # on indique le style du graphique
    fig = mpf.figure(2, figsize=(20, 15), style=s) # création de la figure
    ax1 = fig.add_subplot(2,1,1, title=val) # ajout d'un graphique
    mpf.plot(df_plot, type='candle', ax=ax1) # ajout des données dans le graphique
    ax1.yaxis.set_label_position('left')  # positionnement du label des ordonnées à gauche (style)
    ax1.yaxis.tick_left() # positionnement de l'axe des ordonnées à gauche (style)
    
    
def plot_rsi(df: pd.DataFrame, val: str) -> None:
    """
    Fonction pour tracer un graphique avec l'indicateur RSI (Relative Strength Index).

    Args:
        df (pd.Dataframe): dataframe contenant les données de prix avec des colonnes 'rsi' et 'rsima'.
        val (str): titre du graphique.
    """
    df_plot = df.copy().iloc[-150:] # on prend les 150 dernières valeurs du dataset.
    s = mpf.make_mpf_style(base_mpf_style='charles', rc={'font.size': 6}) # on indique le style du graphique
    fig1 = mpf.figure(1, figsize=(20, 15), style=s) # création de la figure
    ax1 = fig1.add_subplot(2,1,1,title=val) # ajout d'un graphique
    ax2 = fig1.add_subplot(2,1,2, sharex=ax1, title="RSI") # ajout d'un deuxieme graphique
    ap0 = [ # Les sous graphiques doivent être stockés dans un tableau. c'est le parametre 'ax' qui defini sur quelle graphique ils sont ajouter
        mpf.make_addplot(df_plot["rsi"], color='purple', panel=0, ylabel='Points', ax=ax2), # ajout d'un sous graphique sur le deuxieme graphique
        mpf.make_addplot(df_plot["rsima"], color='blue', panel=0,ax=ax2) # ajout d'un sous graphique sur le deuxieme graphique
    ]
    mpf.plot(df_plot, type='candle', ax=ax1, addplot=ap0) # ajout des données dans le graphique + ajout des sous graphiques
    ax1.yaxis.set_label_position('left') # positionnement du label des ordonnées à gauche (style)
    ax1.yaxis.tick_left() # positionnement de l'axe des ordonnées à gauche (style)
    ax2.axhline(30, color='black', linestyle='--') # ajout d'une ligne pointillé sur le deuxieme graphique sur l'ordonnée 30
    ax2.axhline(50, color='black', linestyle='--') # ajout d'une ligne pointillé sur le deuxieme graphique sur l'ordonnée 50
    ax2.axhline(70, color='black', linestyle='--') # ajout d'une ligne pointillé sur le deuxieme graphique sur l'ordonnée 70 
    
    
def plot_macd(df: pd.DataFrame, val: str) -> None:
    """
    Fonction pour tracer un graphique avec l'indicateur MACD (Moving Average Convergence Divergence).

    Args:
        df (pd.Dataframe): dataframe contenant les données de prix avec des colonnes 'macd', 'macd_diff' et 'macd_signal'.
        val (str): titre du graphique.
    """
    df_plot = df.copy().iloc[-150:] # on prend les 150 dernières valeurs du dataset.
    s = mpf.make_mpf_style(base_mpf_style='charles', rc={'font.size': 10})# on indique le style du graphique
    fig2 = mpf.figure(2, figsize=(20, 15), style=s) # création de la figure
    ax1 = fig2.add_subplot(2,1,1, title=val) # ajout d'un graphique
    ax2 = fig2.add_subplot(2,1,2, sharex=ax1, title="MACD") # ajout d'un deuxieme graphique
    ap0 = [ # Les sous graphiques doivent être stockés dans un tableau. c'est le parametre 'ax' qui defini sur quelle graphique ils sont ajouter
        mpf.make_addplot(df_plot["macd"]/10, color='blue', panel=0, ylabel='Points', ax=ax2), # ajout d'un sous graphique sur le deuxieme graphique
        mpf.make_addplot(df_plot["macd_signal"]/10, color='orange', panel=0, ax=ax2), # ajout d'un sous graphique sur le deuxieme graphique
        mpf.make_addplot(df_plot["macd_diff"]/10, panel=0, ax=ax2, type='bar', color='lightblue') # ajout d'un sous graphique sur le deuxieme graphique
    ]
    mpf.plot(df_plot, type='candle', ax=ax1, addplot=ap0) # ajout des données dans le graphique + ajout des sous graphiques
    ax1.yaxis.set_label_position('left') # positionnement du label des ordonnées à gauche (style)
    ax1.yaxis.tick_left() # positionnement de l'axe des ordonnées à gauche (style)
    ax2.axhline(0, color='black', linestyle='--') # ajout d'une ligne pointillé sur le deuxieme graphique sur l'ordonnée 0


def plot_stochastique(df: pd.DataFrame, val: str) -> None:
    """
    Fonction pour tracer un graphique avec l'indicateur Stochastique.

    Args:
        df (pd.Dataframe): dataframe contenant les données de prix avec des colonnes 'stoch_%K' et 'stoch_%D'.
        val (str): titre du graphique.
    """
    df_plot = df.copy().iloc[-150:] # on prend les 150 dernières valeurs du dataset.
    s = mpf.make_mpf_style(base_mpf_style='charles', rc={'font.size': 10}) # on indique le style du graphique
    fig3 = mpf.figure(3, figsize=(20, 15), style=s) # création de la figure
    ax1 = fig3.add_subplot(2,1,1, title=val) # ajout d'un graphique
    ax2 = fig3.add_subplot(2,1,2, sharex=ax1, title="Stochastic") # ajout d'un deuxieme graphique
    ap0 = [ # Les sous graphiques doivent être stockés dans un tableau. c'est le parametre 'ax' qui defini sur quelle graphique ils sont ajouter
        mpf.make_addplot(df_plot["stoch_%K"], color='blue', panel=0, ylabel='Points', ax=ax2), # ajout d'un sous graphique sur le deuxieme graphique
        mpf.make_addplot(df_plot["stoch_%D"], color='orange', panel=0, ax=ax2) # ajout d'un sous graphique sur le deuxieme graphique
    ]
    mpf.plot(df_plot, type='candle', ax=ax1, addplot=ap0) # ajout des données dans le graphique + ajout des sous graphiques
    ax1.yaxis.set_label_position('left') # positionnement du label des ordonnées à gauche (style)
    ax1.yaxis.tick_left() # positionnement de l'axe des ordonnées à gauche (style)
    ax2.axhline(20, color='black', linestyle='--') # ajout d'une ligne pointillé sur le deuxieme graphique sur l'ordonnée 20
    ax2.axhline(50, color='black', linestyle='--') # ajout d'une ligne pointillé sur le deuxieme graphique sur l'ordonnée 30
    ax2.axhline(80, color='black', linestyle='--') # ajout d'une ligne pointillé sur le deuxieme graphique sur l'ordonnée 80


def plot_bollinger_bands(df: pd.DataFrame, val: str) -> None:
    """
    Fonction pour tracer un graphique avec les bandes de Bollinger.

    Args:
        df (pd.Dataframe): dataframe contenant les données de prix avec des colonnes 'lower_band', 'higher_band' et 'ma_band'.
        val (str): titre du graphique.
    """
    df_plot = df.copy().iloc[-150:] # on prend les 150 dernières valeurs du dataset.
    s = mpf.make_mpf_style(base_mpf_style='charles', rc={'font.size': 10}) # on indique le style du graphique
    fig4 = mpf.figure(4, figsize=(20, 15), style=s) # création de la figure
    ax1 = fig4.add_subplot(2,1,1, title=val + " / Bollinger Bands") # ajout d'un graphique
    ap0 = [ # Les sous graphiques doivent être stockés dans un tableau. c'est le parametre 'ax' qui defini sur quelle graphique ils sont ajouter
        mpf.make_addplot(df_plot["lower_band"], color='blue', panel=0, ax=ax1), # ajout d'un sous graphique sur le graphique
        mpf.make_addplot(df_plot["higher_band"], color='blue', panel=0, ax=ax1), # ajout d'un sous graphique sur le graphique
        mpf.make_addplot(df_plot["ma_band"], color='orange', panel=0, ax=ax1) # ajout d'un sous graphique sur le graphique
    ]
    mpf.plot(df_plot, type='candle', ax=ax1, addplot=ap0) # ajout des données dans le graphique + ajout des sous graphiques
    ax1.yaxis.set_label_position('left') # positionnement du label des ordonnées à gauche (style)
    ax1.yaxis.tick_left() # positionnement de l'axe des ordonnées à gauche (style)


def plot_moyenne_mobile(df: pd.DataFrame, val: str) -> None:
    """
    Fonction pour tracer un graphique avec les moyennes mobiles.

    Args:
        df (pd.Dataframe): dataframe contenant les données de prix avec des colonnes 'sma9' et 'sma21'.
        val (str): titre du graphique.
    """
    df_plot = df.copy().iloc[-150:] # on prend les 150 dernières valeurs du dataset.
    s = mpf.make_mpf_style(base_mpf_style='charles', rc={'font.size': 10}) # on indique le style du graphique
    fig5 = mpf.figure(5, figsize=(20, 15), style=s) # création de la figure
    ax1 = fig5.add_subplot(2,1,1, title=val + " / Moyenne Mobile") # ajout d'un graphique
    ap0 = [ # Les sous graphiques doivent être stockés dans un tableau. c'est le parametre 'ax' qui defini sur quelle graphique ils sont ajouter
        mpf.make_addplot(df_plot["sma9"], color='blue', panel=0, ylabel='Points', ax=ax1), # ajout d'un sous graphique sur le graphique
        mpf.make_addplot(df_plot["sma21"], color='orange', panel=0, ax=ax1), # ajout d'un sous graphique sur le graphique
    ]     
    mpf.plot(df_plot, type='candle', ax=ax1, addplot=ap0) # ajout des données dans le graphique + ajout des sous graphiques
    ax1.yaxis.set_label_position('left') # positionnement du label des ordonnées à gauche (style)
    ax1.yaxis.tick_left() # positionnement de l'axe des ordonnées à gauche (style)
    

# Add indicators to dataframe ------------------------------------------------------------------------------------------------------
def add_indicators(df: pd.DataFrame, tf: str) -> pd.DataFrame:
    """
    Fonction pour ajouter des indicateurs techniques au dataframe.

    Args:
        df (pd.Dataframe): dataframe contenant les données de prix avec des colonnes 'open', 'close', 'high', 'low'.

    Returns:
        pd.Dataframe: retourne le dataframe avec les indicateurs techniques ajoutés.
    """
    
    # Ajout des indicateurs techniques au dataframe
    df = rsi(df) # ajout de l'indicateur RSI
    df = macd(df) # ajout de l'indicateur MACD
    df = stochastique(df) # ajout de l'indicateur Stochastique
    df = bollinger_bands(df) # ajout des bandes de Bollinger
    df = moyenne_mobile(df) # ajout des moyennes mobiles
    
    df['Avg_day'] = ((df['close'] + df['open'] + df['high'] + df['low']) / 4).round(2) # calcul de la moyenne du prix de la bougie (open, close, high, low)
    df['Avg_corps'] = ((df['close'] + df['open']) / 2).round(2) # calcul de la moyenne du prix du corps de la bougie (open, close)
    df['Avg_meches'] = ((df['high'] + df['low']) / 2).round(2) # calcul de la moyenne du prix des mèches de la bougie (high, low)
    
    # Ajout du label pour la classification des variations de prix
    if tf == '1h':
        df['Pourc_Price_Evol_CT'] = ((100 * df['Avg_day'].shift(-24) / df['Avg_day']) - 100).round(2) # calcul de l'évolution du prix sur 14 jours en pourcentage
        df['Label_CT'] = np.where(df['Pourc_Price_Evol_CT'] > 5, 1,np.where(df['Pourc_Price_Evol_CT'] < -5, -1, 0)) # création de la colonne Label qui indique si le prix a augmenté de plus de 5% (1), diminué de plus de 5% (-1) ou est resté stable (0)
    elif tf == '2h':
        df['Pourc_Price_Evol_CT'] = ((100 * df['Avg_day'].shift(-12) / df['Avg_day']) - 100).round(2) # calcul de l'évolution du prix sur 14 jours en pourcentage
        df['Label_CT'] = np.where(df['Pourc_Price_Evol_CT'] > 5, 1,np.where(df['Pourc_Price_Evol_CT'] < -5, -1, 0)) # création de la colonne Label qui indique si le prix a augmenté de plus de 5% (1), diminué de plus de 5% (-1) ou est resté stable (0)
    elif tf == '4h':
        df['Pourc_Price_Evol_CT'] = ((100 * df['Avg_day'].shift(-6) / df['Avg_day']) - 100).round(2) # calcul de l'évolution du prix sur 14 jours en pourcentage
        df['Label_CT'] = np.where(df['Pourc_Price_Evol_CT'] > 5, 1,np.where(df['Pourc_Price_Evol_CT'] < -5, -1, 0)) # création de la colonne Label qui indique si le prix a augmenté de plus de 5% (1), diminué de plus de 5% (-1) ou est resté stable (0)
    elif tf == '12h':
        df['Pourc_Price_Evol_MT'] = ((100 * df['Avg_day'].shift(-35) / df['Avg_day']) - 100).round(2) # calcul de l'évolution du prix sur 14 jours en pourcentage
        df['Label_MT'] = np.where(df['Pourc_Price_Evol_MT'] > 5, 1,np.where(df['Pourc_Price_Evol_MT'] < -5, -1, 0)) # création de la colonne Label qui indique si le prix a augmenté de plus de 5% (1), diminué de plus de 5% (-1) ou est resté stable (0)
    elif tf == '1d':
        df['Pourc_Price_Evol_MT'] = ((100 * df['Avg_day'].shift(-42) / df['Avg_day']) - 100).round(2) # calcul de l'évolution du prix sur 14 jours en pourcentage
        df['Label_MT'] = np.where(df['Pourc_Price_Evol_MT'] > 5, 1,np.where(df['Pourc_Price_Evol_MT'] < -5, -1, 0)) # création de la colonne Label qui indique si le prix a augmenté de plus de 5% (1), diminué de plus de 5% (-1) ou est resté stable (0)

        df['Pourc_Price_Evol_LT'] = ((100 * df['Avg_day'].shift(-90) / df['Avg_day']) - 100).round(2) # calcul de l'évolution du prix sur 14 jours en pourcentage
        df['Label_LT'] = np.where(df['Pourc_Price_Evol_LT'] > 5, 1,np.where(df['Pourc_Price_Evol_LT'] < -5, -1, 0)) # création de la colonne Label qui indique si le prix a augmenté de plus de 5% (1), diminué de plus de 5% (-1) ou est resté stable (0)
    elif tf == '1w':
        df['Pourc_Price_Evol_MT'] = ((100 * df['Avg_day'].shift(-3) / df['Avg_day']) - 100).round(2) # calcul de l'évolution du prix sur 14 jours en pourcentage
        df['Label_MT'] = np.where(df['Pourc_Price_Evol_MT'] > 5, 1,np.where(df['Pourc_Price_Evol_MT'] < -5, -1, 0)) # création de la colonne Label qui indique si le prix a augmenté de plus de 5% (1), diminué de plus de 5% (-1) ou est resté stable (0)
        
        df['Pourc_Price_Evol_LT'] = ((100 * df['Avg_day'].shift(-12) / df['Avg_day']) - 100).round(2) # calcul de l'évolution du prix sur 14 jours en pourcentage
        df['Label_LT'] = np.where(df['Pourc_Price_Evol_LT'] > 5, 1,np.where(df['Pourc_Price_Evol_LT'] < -5, -1, 0)) # création de la colonne Label qui indique si le prix a augmenté de plus de 5% (1), diminué de plus de 5% (-1) ou est resté stable (0)
    elif tf == '1M':
        df['Pourc_Price_Evol_LT'] = ((100 * df['Avg_day'].shift(-3) / df['Avg_day']) - 100).round(2) # calcul de l'évolution du prix sur 14 jours en pourcentage
        df['Label_LT'] = np.where(df['Pourc_Price_Evol_LT'] > 5, 1,np.where(df['Pourc_Price_Evol_LT'] < -5, -1, 0)) # création de la colonne Label qui indique si le prix a augmenté de plus de 5% (1), diminué de plus de 5% (-1) ou est resté stable (0)
    
    # Suppression des lignes avec des valeurs manquantes
    df = df.dropna() # suppression des lignes avec des valeurs manquantes
    #df = df.reset_index() # réinitialisation de l'index du dataframe
    
    return df

# Prétraitement des données pour les modèles de machine learning ------------------------------------------------------------------------------------------------------
def preprocess(df: pd.DataFrame, features: list, label: str, time_steps: int = 60) -> tuple:
    """
    Prétraitement des données : nettoyage, normalisation et création de séquences pour LSTM.

    Args :
        df (pd.DataFrame) : DataFrame contenant les données brutes
        features (list) : liste des colonnes à utiliser comme caractéristiques
        label (str) : nom de la colonne cible
        time_steps (int) : nombre de pas de temps pour les séquences LSTM

    Returns :
        X_seq (np.ndarray) : tableau numpy des séquences d'entrée pour LSTM
        y_seq (np.ndarray) : tableau numpy des étiquettes correspondantes
    """
    df = df.dropna()
    X = df[features]
    y = df[label]

    scaler = MinMaxScaler()
    X_scaled = scaler.fit_transform(X)

    X_seq, y_seq = [], []
    for i in range(time_steps, len(X_scaled)):
        X_seq.append(X_scaled[i-time_steps:i])
        y_seq.append(y.iloc[i])
    return np.array(X_seq), np.array(y_seq)

# Construction du modèle LSTM ------------------------------------------------------------------------------------------------------
def build_lstm_model(input_shape: tuple) -> Sequential:
    """
    Construit un modèle LSTM pour la classification binaire.

    Args:
        input_shape (tuple): La forme des données d'entrée (timesteps, features).

    Returns:
        Sequential: Le modèle LSTM compilé.
    """
    model = Sequential()
    model.add(Input(shape=input_shape))
    model.add(LSTM(64, return_sequences=True))
    model.add(Dropout(0.2))
    model.add(LSTM(32))
    model.add(Dropout(0.2))
    model.add(Dense(1, activation='sigmoid'))
    model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
    return model

# Récupération des données depuis l'API de Binance ------------------------------------------------------------------------------------------------------
def fetch_binance_data(symbol: str, interval: str, limit: int = 300) -> pd.DataFrame:
    """
    Récupère les données de prix depuis l'API de Binance et les formate en DataFrame.

    Args:
        symbol (str): Le symbole de trading (ex: 'BTCUSDT').
        interval (str): L'intervalle de temps (ex: '1h', '4h', '1d').
        limit (int): Le nombre de données à récupérer.

    Returns:
        pd.DataFrame: Un DataFrame contenant les données de prix formatées.
    """
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
    response = requests.get(url)
    data = response.json()
    df = pd.DataFrame(data, columns=[
        "date", "open", "high", "low", "close", "volume", "close_time",
        "quote_asset_volume", "number_of_trades", "taker_buy_base_volume",
        "taker_buy_quote_volume", "ignore"
    ])
    df = df[["date", "open", "high", "low", "close", "volume"]]
    df["date"] = pd.to_datetime(df["date"], unit='ms')
    df[["open", "high", "low", "close", "volume"]] = df[["open", "high", "low", "close", "volume"]].astype(float)
    return df


# Enrichissement des données avec des indicateurs techniques supplémentaires ------------------------------------------------------------------------------------------------------
def enrich_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Enrichit le DataFrame avec des indicateurs techniques supplémentaires.
    Args:
        df (pd.DataFrame): DataFrame contenant les données de prix avec des colonnes 'open', 'high', 'low', 'close', 'volume'.
    Returns:
        pd.DataFrame: DataFrame enrichi avec de nouveaux indicateurs techniques."""
    df = df.copy()

    # Indicateurs techniques
    df['rsi'] = RSIIndicator(close=df['close']).rsi()
    df['macd'] = MACD(close=df['close']).macd_diff()

    stoch = StochasticOscillator(high=df['high'], low=df['low'], close=df['close'])
    df['stoch_%K'] = stoch.stoch()
    df['stoch_%D'] = stoch.stoch_signal()

    boll = BollingerBands(close=df['close'])
    df['lower_band'] = boll.bollinger_lband()
    df['higher_band'] = boll.bollinger_hband()

    df['ema_10'] = EMAIndicator(close=df['close'], window=10).ema_indicator()
    df['ema_20'] = EMAIndicator(close=df['close'], window=20).ema_indicator()
    df['atr'] = AverageTrueRange(high=df['high'], low=df['low'], close=df['close']).average_true_range()
    df['obv'] = OnBalanceVolumeIndicator(close=df['close'], volume=df['volume']).on_balance_volume()
    df['adi'] = AccDistIndexIndicator(high=df['high'], low=df['low'], close=df['close'],
                                      volume=df['volume']).acc_dist_index()

    df['hl_ratio'] = df['high'] / df['low']
    df['oc_ratio'] = df['open'] / df['close']
    df['vol_change'] = df['volume'].pct_change()
    df['price_change'] = df['close'].pct_change()

    df = df.dropna()

    feature_cols = ['open', 'high', 'low', 'close', 'volume', 'rsi', 'macd',
                    'stoch_%K', 'stoch_%D', 'lower_band', 'higher_band',
                    'ema_10', 'ema_20', 'atr', 'obv', 'adi',
                    'hl_ratio', 'oc_ratio', 'vol_change', 'price_change']

    return df[['date'] + feature_cols]
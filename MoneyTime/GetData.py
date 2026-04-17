import asyncio
import pandas as pd
from pathlib import Path
from tqdm.auto import tqdm
from asyncio import Semaphore
import ccxt.async_support as ccxt
from datetime import datetime, timedelta

sem = Semaphore(500) # 500 concurrent requests

class GetData:
    
    # Liste des exchanges supportés et de leurs limites de requêtes
    CCXT_EXCHANGES = {
        "binance": {
            "ccxt_object": ccxt.binance(config={'enableRateLimit': True}),
            "limit_size_request": 1000
        },
        "binanceusdm": {
            "ccxt_object": ccxt.binanceusdm(config={'enableRateLimit': True}),
            "limit_size_request": 1000
        },
        "kucoin": {
            "ccxt_object": ccxt.kucoin(config={'enableRateLimit': True}),
            "limit_size_request": 200
        },
        "kucoinfutures": {
            "ccxt_object": ccxt.kucoinfutures(config={'enableRateLimit': True}),
            "limit_size_request": 200
        },
        "okx": {
            "ccxt_object": ccxt.okx(config={'enableRateLimit': True}),
            "limit_size_request": 100
        },
        "bitget": {
            "ccxt_object": ccxt.bitget(config={'enableRateLimit': True}),
            "limit_size_request": 200
        },
        "bybit": {
            "ccxt_object": ccxt.bybit(config={'enableRateLimit': True}),
            "limit_size_request": 1000
        }
    }

    # Liste des intervalles supportés et de leurs équivalents en millisecondes
    INTERVALS = {
        "1m": {
            "timedelta": timedelta(minutes=1),
            "interval_ms": 60000
        },
        "2m": {
            "timedelta": timedelta(minutes=2),
            "interval_ms": 120000
        },
        "5m": {
            "timedelta": timedelta(minutes=5),
            "interval_ms": 300000
        },
        "15m": {
            "timedelta": timedelta(minutes=15),
            "interval_ms": 900000
        },
        "30m": {
            "timedelta": timedelta(minutes=30),
            "interval_ms": 1800000
        },
        "1h": {
            "timedelta": timedelta(hours=1),
            "interval_ms": 3600000
        },
        "2h": {
            "timedelta": timedelta(hours=2),
            "interval_ms": 7200000
        },
        "4h": {
            "timedelta": timedelta(hours=4),
            "interval_ms": 14400000
        },
        "12h": {
            "timedelta": timedelta(hours=12),
            "interval_ms": 43200000
        },
        "1d": {
            "timedelta": timedelta(days=1),
            "interval_ms": 86400000
        },
        "1w": {
            "timedelta": timedelta(weeks=1),
            "interval_ms": 604800000
        },
        "1M": {
            "timedelta": timedelta(days=30),
            "interval_ms": 2629746000
        }
    }
    
    def __init__(
        self,
        pair: str,
        tf: str,
        exchange: str = "binance",
        start_date: str | datetime = "2017-01-01 00:00:00",
        end_date: str | datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ) -> None:
        """
        Cette fonction sert a initialiser l'objet GetData.

        Parameters:
            exchange (str): Le nom de l'échange. Par défaut, "binance".
            pair (str): La paire de trading
            tf (str): L'intervalle de temps
            start_date (str | datetime, optional): La date de début. Par défaut, "2017-01-01 00:00:00".
            end_date (str | datetime, optional): La date de fin. Par défaut, la date actuelle.

        Raises:
            NotImplementedError: Si l'échange n'est pas supporté, une erreur est levée. 
            NotImplementedError: Si l'intervalle de temps n'est pas supporté, une erreur est levée. 
        """
        # Test de la prise en charge de l'exchange
        self.exchange = exchange.lower()
        try:
            self.exchange_dict = GetData.CCXT_EXCHANGES[self.exchange]
        except Exception:
            raise NotImplementedError(f"L'échange {self.exchange} n'est pas supporté")
            
        # Test de la prise en charge de l'intervalle
        self.tf = tf.lower()
        try:
            self.interval_dict = GetData.INTERVALS[self.tf]
        except Exception:
            raise NotImplementedError(f"L'intervalle {self.tf} n'est pas supporté")
        
        # Initialisation des autres variables
        self.pair = pair
        if isinstance(start_date, str):
            self.start_date = datetime.strptime(start_date, "%Y-%m-%d %H:%M:%S")
        else:
            self.start_date = start_date
        if isinstance(end_date, str):
            self.end_date = datetime.strptime(end_date, "%Y-%m-%d %H:%M:%S")
        else:
            self.end_date = end_date
        self.pbar = None # Progress bar pour le téléchargement des données
        self.data = None # DataFrame contenant les données récupérées
        
    def return_data(self) -> pd.DataFrame:
        """
        Cette fonction sert a retourner les données qui ont été téléchargées.

        Raises:
            ValueError: Si aucune donnée n'a été téléchargée, une erreur est levée. 

        Returns:
            pd.DataFrame: Le DataFrame contenant les données récupérées.
        """
        if self.data is None:
            raise ValueError("Aucune donnée n'a été téléchargée. Veuillez exécuter la méthode download_data() avant de récupérer les données.")
        return self.data

    async def download_data(self) -> None:
        """
        Cette fonction sert à télécharger les données de la paire voulu.

        Raises:
            ValueError: Si la paire n'est pas disponible, une erreur est levée.
        """
        # Charger les marchés pour vérifier que le pair est disponible
        await self.exchange_dict["ccxt_object"].load_markets()
        if self.pair not in self.exchange_dict["ccxt_object"].markets:
            # Test du deuxième format de pair (ex: BTC/USDT => BTC/USDT:USDT)
            self.pair = self.pair + ":" + self.pair.split("/")[1]
            if self.pair not in self.exchange_dict["ccxt_object"].markets:
                # Fermer la connexion à l'exchange avant de lever l'erreur
                await self.exchange_dict["ccxt_object"].close()
                raise ValueError(f"Le pair {self.pair} n'est pas disponible sur l'échange {self.exchange}")

        print(f"Récupération pour la paire {self.pair} en timeframe {self.tf} sur l'exchange {self.exchange}")

        # Création de la liste des tasks à effectuer pour récupérer toutes les données entre start_date et end_date
        tasks = []
        current_timestamp = int(self.start_date.timestamp() * 1000) # Convertir en millisecondes
        end_timestamp = int(self.end_date.timestamp() * 1000) # Convertir en millisecondes
        while current_timestamp < end_timestamp:
            tasks.append(self.download_tf_with_semaphore(self.pair, self.tf, current_timestamp, sem))
            current_timestamp = min([current_timestamp + self.exchange_dict["limit_size_request"] * self.interval_dict["interval_ms"], end_timestamp])
        
        self.pbar = tqdm(total=len(tasks)) # Initialiser la progress bar avec le nombre total de tâches
        results = await asyncio.gather(*tasks) # Lancement des requêtes de manière asynchrone
        await self.exchange_dict["ccxt_object"].close() # Fermer la connexion à l'exchange
        self.pbar.close() # Fermer la progress bar
        
        # Filtrer les résultats vides pour éviter les erreurs lors de la concaténation des DataFrames
        all_data = [
            pd.DataFrame(r, columns=["date", "open", "high", "low", "close", "volume"])
            for r in results
            if len(r) > 0
        ]
        
        # Concaténer les résultats dans un seul DataFrame et supprimer les doublons
        self.data = pd.concat(all_data, ignore_index=True)
        self.data.set_index("date", inplace=True) # Mettre la colonne "date" en index
        self.data.index = pd.to_datetime(self.data.index, unit='ms') # Convertir l'index en datetime
        self.data.sort_index(inplace=True) # Trier les données par date
        self.data = self.data[~self.data.index.duplicated(keep='first')] # Supprimer les doublons d'index

    async def download_tf_with_semaphore(self, coin: str, interval: str, current_timestamp: int, sem: Semaphore) -> list:
        """
        Cette fonction sert a ...

        Parameters:
            coin (str): pair de trading
            interval (str): intervalle de temps
            current_timestamp (int): timestamp de départ
            sem (Semaphore): sémaphore pour la gestion des ressources

        Returns:
            list: liste des données récupérées pour le pair, l'intervalle et le timestamp donné
        """
        async with sem:
            return await self.download_tf(coin, interval, current_timestamp)
    
    async def download_tf(self, coin: str, interval: str, start_timestamp: int) -> list:
        """
        Télécharge les données de l'API et les stocke dans une trame de données.

        Parameters:
            coin (str): pair de trading
            interval (str): intervalle de temps
            start_timestamp (int): timestamp de départ
        Returns:
            list: liste des données récupérées pour le pair, l'intervalle et le timestamp
        """
        tests = 1
        while tests < 3:
            try:
                if self.exchange == "bitget":
                    r = await self.exchange_dict["ccxt_object"].fetch_ohlcv(coin, timeframe=interval, limit=self.exchange_dict["limit_size_request"], params={"method": "publicMixGetV2MixMarketHistoryCandles", "until": start_timestamp + (self.INTERVALS[interval]["interval_ms"] * self.exchange_dict["limit_size_request"])})
                else:
                    r = await self.exchange_dict["ccxt_object"].fetch_ohlcv(symbol=coin, timeframe=interval, since=start_timestamp, limit=self.exchange_dict["limit_size_request"])

                self.pbar.update(1)
                return r
            except Exception as e:
                tests += 1
                if tests == 3:
                    print(f"Error during download {coin} {interval} {start_timestamp} {e}")
        return []
                    
    def save_data(self, dir: str = "./"):
        """
        Cette fonction sert à sauvegarder les données téléchargées dans un fichier CSV.

        Parameters:
            dir (str, optional): Chemin du dossier de destination. Par défaut, "./".

        Raises:
            ValueError: Si aucune donnée n'a été téléchargée, une erreur est levée.
        """
        if self.data is None:
            raise ValueError("Aucune donnée n'a été téléchargée. Veuillez exécuter la méthode download_data() avant de sauvegarder les données.")
        
        # Créer le dossier de destination s'il n'existe pas
        path = Path(f"{dir}/{self.exchange}/{self.tf}")
        path.mkdir(parents=True, exist_ok=True)
        
        # Enregistrer les données dans un fichier CSV
        print(f"Sauvegarde des données dans : {path}")
        self.data.to_csv(f"{path}/{self.pair.replace('/', '-')}.csv", index=True)




        
if __name__ == "__main__":
    print()
    print("Test de la classe GetData")
    print()
    
    # Test de la recuperation des données sur Binance => OK
    print("Test de la récupération des données sur Binance")
    get_data_binance = GetData(
        exchange="binance",
        pair="BTC/USDT",
        tf="1d",
    )
    asyncio.run(get_data_binance.download_data())
    get_data_binance.save_data(dir="MoneyTime")
    
    # Test de la recuperation des données sur BinanceUSDM => OK
    # print("Test de la récupération des données sur BinanceUSDM")
    # get_data_binanceusdm = GetData(
    #     exchange="binanceusdm",
    #     pair="BTC/USDT",
    #     tf="1d",
    # )
    # asyncio.run(get_data_binanceusdm.download_data())
    
    # Test de la recuperation des données sur kucoin => OK
    # print("Test de la récupération des données sur kucoin")
    # get_data_kucoin = GetData(
    #     exchange="kucoin",
    #     pair="BTC/USDT",
    #     tf="1d",
    # )
    # asyncio.run(get_data_kucoin.download_data())
    
    # Test de la recuperation des données sur kucoinfutures => OK
    # print("Test de la récupération des données sur kucoinfutures")
    # get_data_kucoinfutures = GetData(
    #     exchange="kucoinfutures",
    #     pair="BTC/USDT",
    #     tf="1d",
    # )
    # asyncio.run(get_data_kucoinfutures.download_data())
    
    # Test de la recuperation des données sur okx => OK
    # print("Test de la récupération des données sur okx")
    # get_data_okx = GetData(
    #     exchange="okx",
    #     pair="BTC/USDT",
    #     tf="1d",
    # )
    # asyncio.run(get_data_okx.download_data())
    
    # Test de la recuperation des données sur bitget => OK
    # print("Test de la récupération des données sur bitget")
    # get_data_bitget = GetData(
    #     exchange="bitget",
    #     pair="BTC/USDT",
    #     tf="1d",
    # )
    # asyncio.run(get_data_bitget.download_data())
    
    # Test de la recuperation des données sur bybit => OK
    # print("Test de la récupération des données sur bybit")
    # get_data_bybit = GetData(
    #     exchange="bybit",
    #     pair="BTC/USDT",
    #     tf="1d",
    # )
    # asyncio.run(get_data_bybit.download_data())
        
        
        
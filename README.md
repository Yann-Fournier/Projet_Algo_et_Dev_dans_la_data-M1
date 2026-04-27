# Projet final – Data & IA, optimization, orientées objet
---

***Participants:***
- Yann Fournier
- Elodie Senel

[Github du projet](https://github.com/Yann-Fournier/Projet_Algo_et_Dev_dans_la_data-M1)

Notre projet à pour but de prédire le cours du Bitcoin. Nous avons décidé de l'appeler `MoneyTime`.

## Prérequis

Python >= 3.10, Git

## Setup du Projet

Téléchargement initial du projet
```bash
$ git clone https://github.com/Yann-Fournier/Projet_Algo_et_Dev_dans_la_data-M1
```

Placer ensuite le terminal à l'intérieur du dossier MoneyTime 

Mise en place de l'environnement virtuel (très recommandé):
```bash
$ python -m venv .venv  
$ .venv\Scripts\activate  
$ pip install -r .\requirements.txt
```

## MoneyTime
---

***Explication du dossier :***

- modeles : Dossier avec tous les modèles dont nous aurons besoin pour ce projet. Nous avons décidé de les envoyer dans le github pour que vous n'ayez pas à les recréer.
- app_st.py : C'est le fichier python qui permet de lancer notre petite application pour ce projet. Plus de détails seront fournis plus bas...
- creation_modeles.ipynb : Fichier permettant de faire la création et l'entraînement de tous nos modèles.
- GetData.py : Ce fichier contient l'objet `GetData()` qui permet de récupérer les données qui permettrons d'entraîner nos modèles.
- Infos.md : C'est un fichier explicatifs sur les différents indicateurs techniques utilisé et d'autre infos en plus.
- Utils.py : Ce sont toutes les fonctions qu'on utilise tout au long du projet. On les a regrouper en un seul fichier pour ne pas polluer les fichiers d'exécutions.
- Visualise_indicators.ipynb : Ce fichier permet juste d'avoir un visuel sur les indicateurs techniques utilisés pour mieux les comprendres.

***Application Streamlit :***

Comment exécuter l'application ? Commencez par vous rendre dans le dossier `MoneyTime` puis exécuter la commande de lancement de l'app :
```bash
$ cd MoneyTime
$ streamlit run app_st.py
```

L'application s'ouvrira automatiquement dans votre navigateur par défaut.

On vous propose de choisir entre trois prédictions :
- Court terme
- Moyen terme
- Long terme

Un fois choisi, appuyer sur le bouton `prédire` et laissez la magie oppérer !

## Web scraping
---

Notre projet n'a pas besoin de faire de scrapping alors nous avons rajouter le dossier `Scraping`, à la racine du projet, avec un scraping des livres d'amazon.fr.

Ce dossier est organisé comme suit :

- Un fichier Objet_Scrap.py qui contient l'objet `ScrapLivreAmazon` qui contient toutes les méthodes utiles pour rendre ce scraping possible
- Un dossier CSV qui contient :
    - Les fichiers CSV générer par le scraping (si le code à déjà été lancé)
- Un dossier JSON qui contient :
    - Un premier fichier json (1_Categorie.json) : C'est la liste de toutes les catégories de livres présent sur le site
    - Un deuxième fichier json (1_Pages.json) : C'est la liste des pages qui n'ont pas été scraper par catégorie (une sorte de log des pb)

Notre code ne scrap qu'une seule page par catégorie. Ce n'est qu'un code de démonstration. Il est déjà assez long comme ça mais libre à vous d'augmenter à votre guise le nombre de page.

Le code dur une bonne vaingtaine de minutes en ne scrapant qu'une seul page. Nous vous conseillons de le laisser tourner 5 minutes puis de l'arrêter.

Pour le lancer, vous n'avez qu'a exécuter le fichier Objet_Scrap.py.

## Planning
---

- Création du scrapping (2 jours)
- Création de la récupération des données (1 jours)
- Création des modèles (3 jours)
    - réflexion
    - création
    - comparaisons
- Création de l'application Streamlit (2 jours)

# Projet final – Data & IA, optimization, orientées objet
---

## To do list

- Transformer le code de scrapping en Objet
- Refaire MoneyTime
- Faire le code du planning

Notre projet à pour but de prédire le cours du Bitcoin. Nous avons décidé de l'appeler `MoneyTime`.

## MoneyTime


## Web scraping
---

Notre projet n'a pas besoin de faire de scrapping alors nous avons rajouter le dossier `Scraping`, à la racine du projet, avec un scraping des livres d'amazon.fr.

Ce dossier est organisé comme suit :

- Un fichier Scrap.py qui execute le scraping du site amazon.fr
- Un fichier Clean.py qui permet de nettoyer et de concatener les différents CSV des livre en un seul
- Un dossier CSV qui contient :
    - Un premier fichier json (1_Categorie.json) : C'est la liste de toutes les catégories de livres présent sur le site
    - Un deuxième fichier json (1_Pages.json) : C'est la liste des pages qui n'ont pas été scraper par catégorie (une sorte de log des pb)
    - Les fichiers CSV générer par le scraping (si le code à déjà été lancé)

Notre code ne scrap qu'une seule page par catégorie. Ce n'est qu'un code de démonstration. Il est déjà assez long comme ça mais libre à vous d'augmenter à votre guise le nombre de page.



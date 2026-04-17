import glob
import os
import time
import json
import numpy as np
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from urllib.robotparser import RobotFileParser
from selenium.webdriver.chrome.options import Options

class ScrapLivreAmazon:

    def __init__(self):
        """
        Initialisation de toutes les variables dont on a besoin pour le scraping.
        """

        # Chemin absolu du fichier en cours d'exécution
        self.current_file_path = os.path.abspath(__file__)
        self.current_dir = os.path.dirname(self.current_file_path)

        # Options pour réduire les logs et les notifications de Chrome
        self.navigateur_options = Options()
        self.navigateur_options.add_argument("--log-level=3")  # réduit les logs
        self.navigateur_options.add_argument("--disable-notifications")
        self.navigateur_options.add_argument("--disable-background-networking")
        # self.navigateur_options.add_argument("--headless=new")  # mode headless moderne
        self.navigateur_options.add_argument("--disable-gpu")   # option utile sur Windows

        self.base_url = "https://www.amazon.fr"

        # Récupération des fichiers JSON
        self.fichier_json_url_Categories = os.path.join(self.current_dir, 'JSON/1_Categories.json')
        self.fichier_json_Pages = os.path.join(self.current_dir, 'JSON/1_Pages.json')
        with open(self.fichier_json_url_Categories, 'r') as fichier_Categories:
            contenuCategories = fichier_Categories.read()  # Le code bug si je ne transforme pas le json en str en premier
            self.urlCategories = json.loads(contenuCategories)
        with open(self.fichier_json_Pages, 'r') as fichier_Pages:
            contenuPages = fichier_Pages.read()  # Le code bug si je ne transforme pas le json en str en premier
            self.indicesPagesPasPrises = json.loads(contenuPages)  # Les indices des pages qui n'ont pas été scrapper à cause de PB
    
    def run_scraping_all(self):
        """
        Fonction all-in-one qui lance tout le processus de scraping.
        """
        # Récupération du contrôle du navigateur
        self.get_driver()

        # Robot.txt
        self.verif_robot_txt()

        # Refus des cookies
        self.decline_cookies()

        # Run du scraping
        self.run_scraping()

        # Fermeture du driver
        self.quit_driver()

    def get_driver(self):
        """
        Récupération du contrôle du navigateur Chrome avec les options définies.
        """
        # Créez une instance de navigateur Chrome
        self.driver = webdriver.Chrome(options=self.navigateur_options)

    def verif_robot_txt(self):
        """
        Vérification du fichier robots.txt pour s'assurer que le scraping est autorisé sur les pages ciblées.
        Cela permet de respecter les règles définies par le site web et d'éviter les problèmes juridiques ou techniques liés au scraping.
        """
        # Vérification du fichier robots.txt --------------------------------------------------------------------------------
        # Charger robots.txt
        self.rp = RobotFileParser()
        self.rp.set_url(self.base_url + "/robots.txt")
        self.rp.read()

        print()
        print("Vérification du fichier robots.txt :")
        print("Peut-on scraper la page d'accueil ? ", self.rp.can_fetch("*", self.base_url + "/")) # True
        print("delay entre les requêtes : ", self.rp.crawl_delay("*")) # None
        print()

    def decline_cookies(self):
        """
        Refus des cookies sur la page d'accueil pour éviter les pop-ups qui bloquent le scraping.
        Cela permet de garantir que le scraper peut accéder au contenu de la page sans être interrompu par des demandes de consentement aux cookies, ce qui est essentiel pour un scraping efficace et fluide.
        """
        self.driver.get(self.base_url)
        time.sleep(5)

        # Refuser les cookies ---------------------------------------------------------------------------------------------------
        doit_verife_cookie = True
        try:
            self.driver.find_element(By.XPATH, '/html/body/div[1]/div[1]/form/div[2]/div/span[2]/span/span/input').click()
        except:
            doit_verife_cookie = False
            pass
        if doit_verife_cookie:
            try:
                self.driver.find_element(By.XPATH, '//*[@id="sp-cc-rejectall-link"]').click()
            except:
                doit_verife_cookie = False
                pass
        if doit_verife_cookie:
            try:
                self.driver.find_element(By.CSS_SELECTOR, '#sp-cc-rejectall-link').click()
            except:
                print("Veuillez accepter les cookies à la mains pour continuer le scrap !!")
                time.sleep(30) # laisser le temps de cliquer sur refuser les cookies
                pass

    def quit_driver(self):
        """
        Fermeture du navigateur pour libérer les ressources système.
        Cela permet de s'assurer que le navigateur ne reste pas ouvert inutilement après la fin du scraping, ce qui peut consommer des ressources et potentiellement causer des problèmes de performance ou de sécurité.
        """
        # Fermer le navigateur
        self.driver.quit()

    def run_scraping(self):
        """
        Fonction principale qui effectue le scraping des livres sur Amazon en parcourant les catégories et les pages définies.
        Elle récupère les informations des livres (nom, description, photo, ISBN, éditeur, prix, catégorie) et les stocke dans des fichiers CSV.
        """
        print()
        print("Le scrap commence !!!!!!!!!!!!!!!!!")
        print()
        #  Boucle des catégories --------------------------------------------------------------------
        for key, value in self.urlCategories.items():
            print(key)
            
            indicesPagesPasPrises2 = []
            
            #  Boucle des pages ------------------------------------------------------------------------------------------------
            for i in range(1, 2): # On ne scrap que 5 page par ce que ce n'est qu'un exemple de code
                
                # Initialisation tableaux à chaque nouvelle page ---------------------------------------------------------------
                nom = []
                description = []
                photo = []
                isbn = []
                editeur = []
                prix = []
                categorie = []
                prix = []

                try:
                    # On va sur chacune des pages
                    url_page = value.format(i, i)
                    if not self.rp.can_fetch("*", url_page):
                        print(f"Interdiction par le fichier robots.txt !")
                        indicesPagesPasPrises2.append(i)
                        continue
                    
                    self.driver.get(url_page)

                    #  Page simple ---------------------------------------------------------------------------------------------
                    # Je divise la recupération des liens en deux requêtes, car sinon les xpath est trop grand et l'IDE n'est pas content
                    divPrincipal = self.driver.find_element(By.XPATH, '/html/body/div[1]/div[1]/div[1]/div[1]/div/span[1]/div[1]')
                    divs = divPrincipal.find_elements(By.CLASS_NAME, 's-widget-spacing-small')
                    linksInPage = []  # tableau des liens des livres de la page actuelle

                    for div in divs:  # recuperation des liens des livres de la page actuelle
                        try:
                            elm = div.find_element(By.XPATH, './div/div/span/div/div/div/div[2]/div/div/div[3]/div[1]/div/div[1]/div[1]/a').text  # chemin relatif
                        except:
                            elm = ""  # chemin complet
                        if elm == "":
                            try:
                                elm = div.find_element(By.XPATH, '/html/body/div[1]/div[1]/div[1]/div[1]/div/span[1]/div[1]/div[3]/div/div/span/div/div/div/div[2]/div/div/div[3]/div[1]/div/div[1]/div[1]/a').text  # chemin complet
                            except:
                                elm = ""
                        if elm == "":
                            try:
                                elm = div.find_element(By.XPATH, '/html/body/div[1]/div[1]/div[1]/div[1]/div/span[1]/div[1]/div[9]/div/div/span/div/div/div/div[2]/div/div/div[3]/div[1]/div/div[1]/div[1]/a').text  # chemin complet
                            except:
                                elm = ""

                        if elm == "Poche" or elm == "Relié" or elm == "Broché" or elm == "Carte":
                            try:
                                linksInPage.append(div.find_element(By.XPATH, './div/div/span/div/div/div/div[1]/div/div[2]/div/span/a').get_attribute('href'))  # chemin relatif
                            except:
                                linksInPage.append(div.find_element(By.XPATH, '/html/body/div[1]/div[1]/div[1]/div[1]/div/span[1]/div[1]/div[2]/div/div/div/div/span/div/div/div/div[1]/div/div[2]/div/span/a').get_attribute('href'))  # chemin complet
                    
                    print(i, ":", len(linksInPage), "--------------------------------------------------------------------------------------")

                    cpt = 0  # tkt compteur pour l'affichage
                    for link in linksInPage:
                        cpt += 1  # tkt
                        
                        # On va sur chacune des pages des livres pour récupérer les infos qui nous interesse.
                        if not self.rp.can_fetch("*", link):
                            print(f"Interdiction par le fichier robots.txt !")
                            continue
                        self.driver.get(link)

                        # Nom --------------------------------------------------------------------------------------------------
                        try:
                            name = self.driver.find_element(By.CSS_SELECTOR, '#productTitle').text
                        except:
                            name = ""
                        if name == "":
                            try:
                                name = self.driver.find_element(By.XPATH, '//*[@id="productTitle"]').text
                            except:
                                name = ""
                        if name == "":
                            try:
                                name = self.driver.find_element(By.XPATH, '/html/body/div[2]/div/div[4]/div[1]/div[8]/div[2]/div/h1/span[1]').text
                            except:
                                name = ""
                        if name == "":
                            try:
                                name = self.driver.find_element(By.XPATH, '/html/body/div[2]/div/div[4]/div[1]/div[7]/div[2]/div/h1/span[1]').text
                            except:
                                name = ""
                        name = name.replace("'", "&#39")
                        nom.append(name)

                        # Description ------------------------------------------------------------------------------------------
                        try:
                            desc = self.driver.find_element(By.CSS_SELECTOR,'#bookDescription_feature_div > div > div.a-expander-content.a-expander-partial-collapse-content > span').text
                        except:
                            desc = ""
                        if desc == "":
                            try:
                                desc = self.driver.find_element(By.XPATH,'///*[@id="bookDescription_feature_div"]/div/div[1]/span').text
                            except:
                                desc = ""
                        if desc == "":
                            try:
                                desc = self.driver.find_element(By.XPATH,'/html/body/div[2]/div/div[4]/div[1]/div[7]/div[28]/div/div[1]').text
                            except:
                                desc = ""
                        desc = desc.replace("'", "&#39").replace("\n", " ").replace("\r", " ").replace(";", "&#59").replace("\t", " ").replace("  ", " ").replace('"', '&#34')
                        description.append(desc)

                        #  Photo -----------------------------------------------------------------------------------------------
                        try:
                            pic = self.driver.find_element(By.XPATH,'/html/body/div[2]/div/div[4]/div[1]/div[7]/div[1]/div[1]/div/div/div/div[1]/div[1]/ul/li[1]/span/span/div/img').get_attribute('src')
                        except:
                            pic = ""
                        if pic == "":
                            try:
                                pic = self.driver.find_element(By.XPATH,'/html/body/div[2]/div/div[4]/div[1]/div[6]/div[1]/div[1]/div/div/div/div[1]/div[1]/ul/li[1]/span/span/div/img').get_attribute('src')
                            except:
                                pic = ""
                        if pic == "":
                            try:
                                pic = self.driver.find_element(By.XPATH,'//*[@id="landingImage"]').get_attribute('src')
                            except:
                                pic = ""
                        if pic == "":
                            try:
                                pic = self.driver.find_element(By.CSS_SELECTOR,'#landingImage').get_attribute('src')
                            except:
                                pic = ""
                        photo.append(pic)

                        # Detail -----------------------------------------------------------------------------------------------
                        Isbn = ""
                        edit = ""
                        try:
                            details = self.driver.find_elements(By.XPATH, '/html/body/div[2]/div/div[4]/div[26]/div/div[1]/ul/li')                                     
                            for det in details:
                                truc = det.find_element(By.XPATH, './span/span[1]').text
                                if truc.__contains__("ISBN-13"):
                                    Isbn = det.find_element(By.XPATH, './span/span[2]').text
                                elif truc.__contains__("Éditeur"):
                                    edit = det.find_element(By.XPATH, './span/span[2]').text
                        except:
                            pass
                        try:
                            details = self.driver.find_elements(By.XPATH, '/html/body/div[1]/div[2]/div/div[26]/div/div[1]/ul/li')                                     
                            for det in details:
                                truc = det.find_element(By.XPATH, './span/span[1]').text
                                if truc.__contains__("ISBN-13"):
                                    Isbn = det.find_element(By.XPATH, './span/span[2]').text
                                elif truc.__contains__("Éditeur"):
                                    edit = det.find_element(By.XPATH, './span/span[2]').text
                        except:
                            pass
                        try:
                            details = self.driver.find_elements(By.XPATH, '//*[@id="detailBullets_feature_div"]/ul/li')                                     
                            for det in details:
                                truc = det.find_element(By.XPATH, './span/span[1]').text
                                if truc.__contains__("ISBN-13"):
                                    Isbn = det.find_element(By.XPATH, './span/span[2]').text
                                elif truc.__contains__("Éditeur"):
                                    edit = det.find_element(By.XPATH, './span/span[2]').text
                        except:
                            pass
                        Isbn = Isbn.replace("'", "&#39")
                        edit = edit.replace("'", "&#39")
                        isbn.append(Isbn)
                        editeur.append(edit)
                        
                        #  Prix ------------------------------------------------------------------------------------------------
                        price = 0.0
                        try:
                            priceInt = self.driver.find_element(By.XPATH, '/html/body/div[2]/div/div[4]/div[1]/div[5]/div[4]/div[4]/div/div[1]/div/div[1]/div/div/div/div[1]/div/div/div[1]/div/div[2]/div/form/div/div/div[2]/div[1]/div[1]/span[2]/span[2]/span[1]').text
                            priceFloat = self.driver.find_element(By.XPATH, '/html/body/div[2]/div/div[4]/div[1]/div[5]/div[4]/div[4]/div/div[1]/div/div[1]/div/div/div/div[1]/div/div/div[1]/div/div[2]/div/form/div/div/div[2]/div[1]/div[1]/span[2]/span[2]/span[2]').text
                            price = priceInt + "." + priceFloat
                            price = float(price)
                        except:
                            price = 0.0
                        if price == 0.0:
                            try:
                                priceInt = self.driver.find_element(By.XPATH, '/html/body/div[2]/div/div[4]/div[1]/div[5]/div[4]/div[4]/div/div[1]/div/div/div/form/div/div/div/div/div[4]/div/div[2]/div[1]/div[1]/span[2]/span[2]/span[1]').text
                                priceFloat = self.driver.find_element(By.XPATH, '/html/body/div[2]/div/div[4]/div[1]/div[5]/div[4]/div[4]/div/div[1]/div/div/div/form/div/div/div/div/div[4]/div/div[2]/div[1]/div[1]/span[2]/span[2]/span[2]').text
                                price = priceInt + "." + priceFloat
                                price = float(price)
                            except:
                                price = 0.0
                        if price == 0.0:
                            try:
                                priceInt = self.driver.find_element(By.XPATH, '/html/body/div[2]/div/div[4]/div[1]/div[5]/div[4]/div[4]/div/div[1]/div/div[2]/div/div/div/div/div/form/div/div/div/div/div[4]/div/div[2]/div[1]/div[1]/span[2]/span[2]/span[1]').text
                                priceFloat = self.driver.find_element(By.XPATH, '/html/body/div[2]/div/div[4]/div[1]/div[5]/div[4]/div[4]/div/div[1]/div/div[2]/div/div/div/div/div/form/div/div/div/div/div[4]/div/div[2]/div[1]/div[1]/span[2]/span[2]/span[2]').text
                                price = priceInt + "." + priceFloat
                                price = float(price)
                            except:
                                price = 0.0
                        if price == 0.0:
                            try:
                                priceSTR = self.driver.find_element(By.XPATH, '/html/body/div[2]/div/div[4]/div[1]/div[5]/div[4]/div[2]/div/div/div/div[2]/span/span/a/span[2]/span').text
                                priceSTR = priceSTR[:-2]
                                priceSTR = priceSTR.replace(',', '.')
                                price = float(priceSTR)
                            except:
                                price = 0.0
                        if price == 0.0:
                            try:
                                priceSTR = self.driver.find_element(By.XPATH, '/html/body/div[2]/div/div[4]/div[1]/div[5]/div[4]/div[2]/div/div/div[2]/div[2]/span/span/a/span[2]/span').text
                                priceSTR = priceSTR[:-2]
                                priceSTR = priceSTR.replace(',', '.')
                                price = float(priceSTR)
                            except:
                                price = 0.0
                        if price == 0.0:
                            try:
                                priceSTR = self.driver.find_element(By.XPATH, '//*[@id="corePriceDisplay_desktop_feature_div"]/div[1]/span[2]/span[2]/span[1]').text
                                priceFloat = self.driver.find_element(By.XPATH, '//*[@id="corePriceDisplay_desktop_feature_div"]/div[1]/span[2]/span[2]/span[2]').text
                                price = priceSTR + "." + priceFloat
                                price = float(priceSTR)
                            except:
                                price = 0.0
                        if price == 0.0:
                            try:
                                priceSTR = self.driver.find_element(By.CSS_SELECTOR, '#corePriceDisplay_desktop_feature_div > div.a-section.a-spacing-none.aok-align-center.aok-relative.apex-core-price-identifier > span.a-price.aok-align-center.reinventPricePriceToPayMargin.priceToPay.apex-pricetopay-value > span:nth-child(2) > span.a-price-whole').text
                                priceFloat = self.driver.find_element(By.CSS_SELECTOR, '#corePriceDisplay_desktop_feature_div > div.a-section.a-spacing-none.aok-align-center.aok-relative.apex-core-price-identifier > span.a-price.aok-align-center.reinventPricePriceToPayMargin.priceToPay.apex-pricetopay-value > span:nth-child(2) > span.a-price-fraction').text
                                price = priceSTR + "." + priceFloat
                                price = float(priceSTR)
                            except:
                                price = 0.0
                        if price == 0.0:
                            nombre_aleatoire = np.random.uniform(5.0, 20.0)
                            price = round(nombre_aleatoire, 2)
                        prix.append(price)

                        # Catégorie --------------------------------------------------------------------------------------------
                        categorie.append(key)

                        print(cpt, "/", len(linksInPage))

                    #  Ajout des données dans la CSV ---------------------------------------------------------------------------
                    if len(nom) == len(description) == len(photo) == len(isbn) == len(editeur) == len(prix) == len(categorie):
                        time.sleep(1)
                        dfLivres = pd.DataFrame({
                            "Nom": nom, 
                            "Prix": prix, 
                            "Description": description, 
                            "Isbn": isbn, 
                            "Photo": photo,
                            "Editeur": editeur,
                            "Categorie": categorie
                        })
                        fileNameLivres = os.path.join(self.current_dir, 'JSON/Livres' + key + '.csv')
                        if i == 1:
                            dfLivres.to_csv(fileNameLivres, index=False, encoding='utf-8', sep=';')
                        else:
                            dfLivres.to_csv(fileNameLivres, mode='a', index=False, header=False, encoding='utf-8', sep=';')
                    else:
                        print("Len livres pas OK")
                        print("Nom", len(nom))
                        print("Description", len(description))
                        print("Photo", len(photo))
                        print("ISBN", len(isbn))
                        print("Editeur", len(editeur))
                        print("Prix", len(prix))
                        print("Categorie", len(categorie))
                        indicesPagesPasPrises2.append(i)
                        
                except:
                    print("PB recupération des liens des livres")

                    indicesPagesPasPrises2.append(i)

                #  Sauvegarde des pages qui n'ont pas été scrapper par catégories-----------------------------------------------
                self.indicesPagesPasPrises[key] = indicesPagesPasPrises2
            with open(self.fichier_json_Pages, 'w') as fichier:
                json.dump(self.indicesPagesPasPrises, fichier, indent=4)

            print() # pour séparer les catégories dans l'affichage
        
        print()
        print("Le scrap est fini !!!!!!!!!!!!!!!!!")
        print()

    def concat_livre_csv(self):
        """
        Concaténation de tous les fichiers CSV des livres en un seul fichier CSV combiné.
        Cette fonction lit tous les fichiers CSV individuels des livres, les combine en un seul DataFrame, supprime les lignes avec des noms vides ou des doublons, et sauvegarde le résultat dans un nouveau fichier CSV.
        """
        self.fichiers_csv_livres = glob.glob(self.current_dir + '/CSV/Livres*.csv')
        self.dataframes_livres = [pd.read_csv(fichier_livres, sep=';', encoding='utf-8', header=0) for fichier_livres in self.fichiers_csv_livres]
        self.dataframe_combine_livres = pd.concat(self.dataframes_livres, ignore_index=True)

        # On supprime les lignes ou le nom est vide
        self.dataframe_combine_livres = self.dataframe_combine_livres.dropna(subset=['Nom'])
        # On supprime les lignes ou les noms sont en double
        self.dataframe_combine_livres = self.dataframe_combine_livres.drop_duplicates(subset=['Nom'])
        self.dataframe_combine_livres.to_csv(self.current_dir + '/CSV/Combined_Books.csv', index=False, encoding='utf-8')


if __name__ == "__main__":
    print()
    print("Test de la classe ScrapLivreAmazon")
    print()

    scraping = ScrapLivreAmazon()

    # Utilisation de la fonction all-in-one ------------------------------------------------------------------------------------------------------------------------------------------
    scraping.run_scraping_all()
    # La fonction de concaténation des CSV n'est pas dans la fonction all-in-one !!!

    # Utilisation des fonctions une part une ------------------------------------------------------------------------------------------------------------------------------------------
    # scraping.get_driver()
    # scraping.verif_robot_txt()
    # scraping.decline_cookies()
    # scraping.run_scraping()
    # scraping.quit_driver()

    # Concaténation des CSV ----------------------------------------------------------------------------------------------------------------------------------------------------------
    # scraping.concat_livre_csv()





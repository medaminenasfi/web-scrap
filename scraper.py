"""
Script de Web Scraping
Ce script permet de scraper des données depuis des sites web
"""

import requests
from bs4 import BeautifulSoup
import json
import csv
from urllib.parse import urljoin
import time
import os


class WebScraper:
    def __init__(self, base_url, delay=1, output_folder='results'):
        """
        Initialise le scraper
        
        Args:
            base_url: URL de base du site à scraper
            delay: Délai entre les requêtes (en secondes) pour être respectueux
            output_folder: Dossier où sauvegarder les résultats (par défaut: 'results')
        """
        self.base_url = base_url
        self.delay = delay
        self.output_folder = output_folder
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Créer le dossier de sortie s'il n'existe pas
        if self.output_folder and not os.path.exists(self.output_folder):
            os.makedirs(self.output_folder)
            print(f"Dossier de sortie créé: {self.output_folder}")
    
    def get_page(self, url):
        """
        Récupère le contenu HTML d'une page
        
        Args:
            url: URL de la page à récupérer
            
        Returns:
            BeautifulSoup object ou None en cas d'erreur
        """
        try:
            # Construire l'URL complète si c'est une URL relative
            full_url = urljoin(self.base_url, url)
            
            print(f"Récupération de: {full_url}")
            response = self.session.get(full_url, timeout=10)
            response.raise_for_status()
            
            # Respecter le délai entre les requêtes
            time.sleep(self.delay)
            
            return BeautifulSoup(response.content, 'html.parser')
        except requests.exceptions.RequestException as e:
            print(f"Erreur lors de la récupération de {url}: {e}")
            return None
    
    def scrape_links(self, url, selector='a'):
        """
        Scrape tous les liens d'une page
        
        Args:
            url: URL de la page
            selector: Sélecteur CSS pour les liens (par défaut 'a')
            
        Returns:
            Liste de dictionnaires avec 'text' et 'url'
        """
        soup = self.get_page(url)
        if not soup:
            return []
        
        links = []
        for link in soup.select(selector):
            href = link.get('href', '')
            text = link.get_text(strip=True)
            if href:
                full_url = urljoin(self.base_url, href)
                links.append({
                    'text': text,
                    'url': full_url
                })
        
        return links
    
    def scrape_text(self, url, selectors):
        """
        Scrape du texte depuis une page avec des sélecteurs CSS
        
        Args:
            url: URL de la page
            selectors: Dictionnaire avec les noms de champs et leurs sélecteurs CSS
                      Exemple: {'title': 'h1', 'description': '.description'}
            
        Returns:
            Dictionnaire avec les données extraites
        """
        soup = self.get_page(url)
        if not soup:
            return {}
        
        data = {}
        for field, selector in selectors.items():
            element = soup.select_one(selector)
            if element:
                data[field] = element.get_text(strip=True)
            else:
                data[field] = None
        
        return data
    
    def scrape_table(self, url, table_selector='table'):
        """
        Scrape une table HTML
        
        Args:
            url: URL de la page
            table_selector: Sélecteur CSS de la table
            
        Returns:
            Liste de dictionnaires (chaque ligne = un dictionnaire)
        """
        soup = self.get_page(url)
        if not soup:
            return []
        
        table = soup.select_one(table_selector)
        if not table:
            return []
        
        # Récupérer les en-têtes
        headers = []
        header_row = table.select_one('thead tr') or table.select_one('tr')
        if header_row:
            headers = [th.get_text(strip=True) for th in header_row.select('th, td')]
        
        # Récupérer les données
        rows = []
        # Chercher d'abord les lignes dans tbody, sinon toutes les lignes (en sautant la première si c'est un header)
        tbody_rows = table.select('tbody tr')
        if tbody_rows:
            data_rows = tbody_rows
        else:
            all_rows = table.select('tr')
            # Si on a trouvé un header, sauter la première ligne
            data_rows = all_rows[1:] if header_row and len(all_rows) > 1 else all_rows
        
        for tr in data_rows:
            cells = [td.get_text(strip=True) for td in tr.select('td, th')]
            if cells:
                if headers:
                    row_dict = dict(zip(headers, cells))
                else:
                    row_dict = {f'col_{i}': cell for i, cell in enumerate(cells)}
                rows.append(row_dict)
        
        return rows
    
    def save_to_json(self, data, filename='scraped_data.json'):
        """Sauvegarde les données en JSON"""
        # Créer le chemin complet avec le dossier de sortie
        if self.output_folder:
            filepath = os.path.join(self.output_folder, filename)
        else:
            filepath = filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"Données sauvegardées dans {filepath}")
    
    def save_to_csv(self, data, filename='scraped_data.csv'):
        """Sauvegarde les données en CSV"""
        if not data:
            print("Aucune donnée à sauvegarder")
            return
        
        # Créer le chemin complet avec le dossier de sortie
        if self.output_folder:
            filepath = os.path.join(self.output_folder, filename)
        else:
            filepath = filename
        
        if isinstance(data, list) and len(data) > 0:
            fieldnames = data[0].keys()
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(data)
            print(f"Données sauvegardées dans {filepath}")
        else:
            print("Format de données non supporté pour CSV")


def example_scrape_news():
    """Exemple: Scraper des articles de nouvelles"""
    # Exemple avec un site de test (remplacez par votre URL)
    scraper = WebScraper("https://example.com", output_folder='results')
    
    # Scraper les liens
    links = scraper.scrape_links("/")
    print(f"Trouvé {len(links)} liens")
    
    # Sauvegarder (sera sauvegardé dans le dossier 'results')
    scraper.save_to_json(links, 'links.json')
    scraper.save_to_csv(links, 'links.csv')


def example_scrape_product():
    """Exemple: Scraper des informations de produit"""
    scraper = WebScraper("https://example.com", output_folder='results')
    
    # Définir les sélecteurs pour extraire les données
    selectors = {
        'title': 'h1',
        'price': '.price',
        'description': '.description'
    }
    
    data = scraper.scrape_text("/product", selectors)
    print(data)
    scraper.save_to_json(data, 'product.json')


if __name__ == "__main__":
    print("=== Script de Web Scraping ===\n")
    print("Ce script contient des fonctions utilitaires pour le web scraping.")
    print("Consultez le README.md pour des exemples d'utilisation.\n")
    
    # Exemple basique
    print("Exemple: Scraping de liens depuis une page")
    print("-" * 50)
    
    # Vous pouvez modifier cette URL pour tester
    url = input("Entrez une URL à scraper (ou appuyez sur Entrée pour utiliser example.com): ").strip()
    if not url:
        url = "https://example.com"
    
    scraper = WebScraper(url, output_folder='results')
    
    # Scraper les liens
    links = scraper.scrape_links("/")
    
    if links:
        print(f"\nTrouvé {len(links)} liens:")
        for i, link in enumerate(links[:10], 1):  # Afficher les 10 premiers
            print(f"{i}. {link['text'][:50]} -> {link['url']}")
        
        if len(links) > 10:
            print(f"... et {len(links) - 10} autres")
        
        # Sauvegarder (sera sauvegardé dans le dossier 'results')
        scraper.save_to_json(links, 'scraped_links.json')
        scraper.save_to_csv(links, 'scraped_links.csv')
        print(f"\nFichiers sauvegardés dans le dossier 'results'")
    else:
        print("Aucun lien trouvé")


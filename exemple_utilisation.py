"""
Exemples d'utilisation du script de web scraping
"""

from scraper import WebScraper


def exemple_1_liens_simples():
    """Exemple 1: Scraper tous les liens d'une page"""
    print("=== Exemple 1: Scraping de liens ===\n")
    
    scraper = WebScraper("https://example.com", delay=1, output_folder='results')
    links = scraper.scrape_links("/")
    
    print(f"Nombre de liens trouvés: {len(links)}\n")
    for i, link in enumerate(links[:5], 1):
        print(f"{i}. {link['text'][:40]} -> {link['url']}")
    
    scraper.save_to_json(links, 'exemple_liens.json')
    print("\nFichier sauvegardé dans: results/exemple_liens.json")


def exemple_2_texte_cible():
    """Exemple 2: Extraire du texte spécifique avec sélecteurs CSS"""
    print("\n=== Exemple 2: Extraction de texte ciblé ===\n")
    
    scraper = WebScraper("https://example.com", delay=1, output_folder='results')
    
    # Définir les sélecteurs pour extraire des données spécifiques
    # Remplacez ces sélecteurs par ceux de votre site cible
    selectors = {
        'titre_principal': 'h1',
        'premier_paragraphe': 'p',
        # Ajoutez d'autres sélecteurs selon vos besoins
    }
    
    data = scraper.scrape_text("/", selectors)
    print("Données extraites:")
    for key, value in data.items():
        print(f"  {key}: {value}")
    
    scraper.save_to_json(data, 'exemple_texte.json')
    print("\nFichier sauvegardé dans: results/exemple_texte.json")


def exemple_3_table():
    """Exemple 3: Scraper une table HTML"""
    print("\n=== Exemple 3: Scraping de table ===\n")
    
    scraper = WebScraper("https://example.com", delay=1, output_folder='results')
    
    # Scraper une table (si elle existe sur la page)
    table_data = scraper.scrape_table("/", table_selector='table')
    
    if table_data:
        print(f"Nombre de lignes: {len(table_data)}")
        print("\nPremières lignes:")
        for row in table_data[:3]:
            print(row)
        
        scraper.save_to_csv(table_data, 'exemple_table.csv')
        print("\nFichier sauvegardé dans: results/exemple_table.csv")
    else:
        print("Aucune table trouvée sur cette page")


def exemple_4_pages_multiples():
    """Exemple 4: Scraper plusieurs pages"""
    print("\n=== Exemple 4: Scraping de plusieurs pages ===\n")
    
    scraper = WebScraper("https://example.com", delay=1, output_folder='results')
    all_data = []
    
    # Liste des pages à scraper
    pages = ["/", "/about", "/contact"]  # Remplacez par vos URLs
    
    for page in pages:
        print(f"Scraping de {page}...")
        selectors = {
            'titre': 'h1',
            'url': page
        }
        data = scraper.scrape_text(page, selectors)
        all_data.append(data)
    
    print(f"\nDonnées de {len(all_data)} pages collectées")
    scraper.save_to_json(all_data, 'exemple_pages_multiples.json')
    print("\nFichier sauvegardé dans: results/exemple_pages_multiples.json")


def exemple_personnalise():
    """Exemple personnalisé - Modifiez selon vos besoins"""
    print("\n=== Exemple personnalisé ===\n")
    
    # 1. Définir l'URL de base
    base_url = "https://example.com"
    
    # 2. Créer le scraper avec un délai approprié et un dossier de sortie
    scraper = WebScraper(base_url, delay=2, output_folder='results')  # 2 secondes entre chaque requête
    
    # 3. Définir ce que vous voulez extraire
    selectors = {
        'titre': 'h1',
        'description': 'meta[name="description"]',
        # Ajoutez vos propres sélecteurs ici
    }
    
    # 4. Scraper
    data = scraper.scrape_text("/", selectors)
    
    # 5. Traiter les données si nécessaire
    # Par exemple, nettoyer le texte, extraire des nombres, etc.
    
    # 6. Sauvegarder (les fichiers seront dans le dossier 'results')
    scraper.save_to_json(data, 'donnees_personnalisees.json')
    scraper.save_to_csv([data], 'donnees_personnalisees.csv')
    
    print("Scraping terminé!")
    print("Fichiers sauvegardés dans: results/")


if __name__ == "__main__":
    print("=" * 60)
    print("EXEMPLES D'UTILISATION DU WEB SCRAPER")
    print("=" * 60)
    
    # Décommentez l'exemple que vous voulez tester:
    
    # exemple_1_liens_simples()
    # exemple_2_texte_cible()
    # exemple_3_table()
    # exemple_4_pages_multiples()
    # exemple_personnalise()
    
    print("\n" + "=" * 60)
    print("Pour utiliser ces exemples, décommentez-les dans le code")
    print("=" * 60)


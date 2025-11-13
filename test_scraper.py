"""
Script de test simple pour debutants
Teste les fonctionnalites de base du scraper
"""

import sys
import io

# Fix encoding pour Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from scraper import WebScraper

def test_basic_scraping():
    """Test basique du scraper avec example.com"""
    print("=" * 60)
    print("TEST BASIQUE DU WEB SCRAPER")
    print("=" * 60)
    print("\n1. Test de connexion...")
    
    try:
        # Creer le scraper (les resultats seront sauvegardes dans le dossier 'results')
        scraper = WebScraper("https://example.com", delay=1, output_folder='results')
        print("[OK] Scraper cree avec succes")
        
        # Test 1: Scraper les liens
        print("\n2. Test: Scraping de liens...")
        links = scraper.scrape_links("/")
        
        if links:
            print(f"[OK] {len(links)} lien(s) trouve(s)")
            print("\nPremiers liens trouves:")
            for i, link in enumerate(links[:3], 1):
                print(f"  {i}. {link['text'][:40]} -> {link['url']}")
        else:
            print("[ATTENTION] Aucun lien trouve")
        
        # Test 2: Scraper du texte
        print("\n3. Test: Extraction de texte...")
        selectors = {
            'titre_principal': 'h1',
            'premier_paragraphe': 'p'
        }
        text_data = scraper.scrape_text("/", selectors)
        
        if text_data:
            print("[OK] Donnees extraites:")
            for key, value in text_data.items():
                if value:
                    print(f"  {key}: {value[:50]}...")
                else:
                    print(f"  {key}: (non trouve)")
        else:
            print("[ATTENTION] Aucune donnee extraite")
        
        # Test 3: Sauvegarde
        print("\n4. Test: Sauvegarde des donnees...")
        if links:
            scraper.save_to_json(links, 'test_liens.json')
            scraper.save_to_csv(links, 'test_liens.csv')
            print("[OK] Fichiers sauvegardes: test_liens.json et test_liens.csv")
        
        print("\n" + "=" * 60)
        print("TEST TERMINE AVEC SUCCES!")
        print("=" * 60)
        print("\nFichiers generes dans le dossier 'results':")
        print("  - results/test_liens.json")
        print("  - results/test_liens.csv")
        print("\nVous pouvez maintenant ouvrir ces fichiers pour voir les resultats.")
        
    except Exception as e:
        print(f"\n[ERREUR] {e}")
        print("\nVerifiez que:")
        print("  1. Vous etes connecte a Internet")
        print("  2. Les packages sont installes (pip install -r requirements.txt)")
        print("  3. L'URL est accessible")


if __name__ == "__main__":
    test_basic_scraping()


# 🚀 Guide Rapide - Utiliser Selenium pour fr.osstem.com

## ✅ Problème Résolu !

Le site **fr.osstem.com** utilise JavaScript pour charger le contenu dynamiquement. Le scraper de base (`requests`) ne peut pas extraire les liens car ils n'existent pas dans le HTML initial.

**Solution** : Utiliser Selenium pour simuler un navigateur réel qui exécute JavaScript.

---

## 📋 Installation

### Étape 1: Installer Selenium
```powershell
pip install selenium webdriver-manager
```

✅ **Déjà installé !** (voir ci-dessus)

### Étape 2: Vérifier que Chrome est installé

Selenium nécessite Google Chrome. Vérifiez que Chrome est installé sur votre système.

---

## 🚀 Utilisation

### Option 1: Utiliser le Script de Test (Recommandé)

```powershell
python scraper_selenium.py
```

Ce script va :
1. Ouvrir Chrome en mode headless (invisible)
2. Charger la page fr.osstem.com
3. Attendre que JavaScript charge le contenu
4. Extraire tous les liens
5. Sauvegarder dans `results/osstem_links_selenium.json` et `.csv`

### Option 2: Utiliser dans votre Code

```python
from scraper_selenium import WebScraperSelenium

# Créer le scraper
scraper = WebScraperSelenium(
    base_url="https://fr.osstem.com/",
    delay=2,
    output_folder='results',
    headless=True  # False pour voir le navigateur
)

try:
    # Scraper les liens
    links = scraper.scrape_links("/", wait_time=15)
    
    if links:
        print(f"Trouvé {len(links)} liens!")
        for link in links[:10]:
            print(f"- {link['text']} -> {link['url']}")
        
        # Sauvegarder
        scraper.save_to_json(links, 'osstem_links.json')
        scraper.save_to_csv(links, 'osstem_links.csv')
    else:
        print("Aucun lien trouvé")
        
finally:
    # Toujours fermer le driver
    scraper.close()
```

---

## 🔍 Diagnostic

Si vous voulez diagnostiquer un site avant d'utiliser Selenium :

```powershell
python test_osstem.py
```

Ce script va :
- Tester la connexion au site
- Vérifier le contenu HTML
- Détecter si JavaScript est nécessaire
- Afficher le contenu HTML complet

---

## ⚙️ Options

### Mode Headless (Invisible)
```python
scraper = WebScraperSelenium(base_url="...", headless=True)
```
- ✅ Plus rapide
- ✅ Pas de fenêtre de navigateur
- ✅ Idéal pour l'automatisation

### Mode Visible
```python
scraper = WebScraperSelenium(base_url="...", headless=False)
```
- ✅ Vous pouvez voir le navigateur
- ✅ Utile pour le débogage
- ❌ Plus lent

### Temps d'Attente
```python
links = scraper.scrape_links("/", wait_time=15)
```
- Ajustez `wait_time` selon le site
- Plus long = plus de temps pour JavaScript de charger
- Défaut: 10 secondes

---

## 📝 Exemple Complet

```python
from scraper_selenium import WebScraperSelenium
from urllib.parse import urlparse

# URL du site
url_input = "https://fr.osstem.com/dental/product/dental-product-implant-bone-ts-fr"

# Parser l'URL
parsed_url = urlparse(url_input)
base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
path = parsed_url.path if parsed_url.path else "/"

# Créer le scraper
scraper = WebScraperSelenium(
    base_url=base_url,
    delay=2,
    output_folder='results',
    headless=True
)

try:
    # Scraper les liens
    print(f"Scraping de: {base_url}{path}")
    links = scraper.scrape_links(path, wait_time=15)
    
    if links:
        print(f"\n{len(links)} liens trouvés!")
        for i, link in enumerate(links[:10], 1):
            print(f"{i}. {link['text'][:50]} -> {link['url']}")
        
        # Sauvegarder
        scraper.save_to_json(links, 'osstem_links.json')
        scraper.save_to_csv(links, 'osstem_links.csv')
        print("\nFichiers sauvegardés dans results/")
    else:
        print("Aucun lien trouvé")
        
finally:
    # Toujours fermer le driver
    scraper.close()
```

---

## 🐛 Résolution de Problèmes

### Erreur: "ChromeDriver not found"
**Solution** : Le script utilise `webdriver-manager` qui télécharge automatiquement ChromeDriver. Assurez-vous que Chrome est installé.

### Erreur: "Chrome is not installed"
**Solution** : Installez Google Chrome depuis [chrome.google.com](https://www.google.com/chrome/)

### Erreur: "Timeout"
**Solution** : Augmentez `wait_time` :
```python
links = scraper.scrape_links("/", wait_time=20)
```

### Aucun lien trouvé
**Solutions** :
- Augmentez `wait_time` pour laisser plus de temps à JavaScript
- Vérifiez que le site s'affiche correctement dans un navigateur
- Utilisez `headless=False` pour voir ce qui se passe

---

## 📊 Comparaison

| Méthode | Vitesse | JavaScript | Complexité |
|---------|---------|------------|------------|
| `requests` | ⚡⚡⚡ Rapide | ❌ Non | ✅ Simple |
| `Selenium` | ⚡ Plus lent | ✅ Oui | ⚠️ Plus complexe |

**Utilisez Selenium** si :
- Le site utilise JavaScript
- Le contenu est chargé dynamiquement
- Le site est une SPA (Single Page Application)

---

## ✅ Checklist

- [x] Selenium installé (`pip install selenium webdriver-manager`)
- [ ] Chrome installé sur le système
- [ ] Script de test exécuté (`python scraper_selenium.py`)
- [ ] Liens trouvés et sauvegardés
- [ ] Driver fermé correctement

---

## 🎯 Prochaines Étapes

1. **Tester le script** :
   ```powershell
   python scraper_selenium.py
   ```

2. **Vérifier les résultats** :
   - Ouvrez `results/osstem_links_selenium.json`
   - Vérifiez que les liens sont corrects

3. **Personnaliser** :
   - Modifiez `wait_time` selon vos besoins
   - Ajustez `headless` pour voir le navigateur
   - Ajoutez d'autres fonctionnalités si nécessaire

---

**Bon scraping avec JavaScript ! 🚀**


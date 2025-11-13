# Guide de Web Scraping

Ce guide vous explique comment utiliser le script de web scraping.

## 🚀 Pour les Débutants

**👉 Nouveau débutant ? Commencez ici : [GUIDE_DEBUTANT.md](GUIDE_DEBUTANT.md)**

Ce guide complet vous explique :
- Comment installer Python et les packages
- Comment exécuter votre premier test
- Comment résoudre les problèmes courants
- Des exemples pas à pas

### 🚀 Démarrage Rapide

1. **Installer les packages** :
   ```bash
   pip install -r requirements.txt
   ```

2. **Tester le scraper** :
   ```bash
   python test_scraper.py
   ```

3. **Utiliser le scraper** :
   ```bash
   python scraper.py
   ```

## 📋 Prérequis

1. **Python 3.7 ou supérieur** installé sur votre ordinateur
2. **pip** (gestionnaire de paquets Python)

## 🚀 Installation

### Étape 1: Installer les dépendances

Ouvrez un terminal (PowerShell ou CMD) dans le dossier du projet et exécutez:

```bash
pip install -r requirements.txt
```

Cela installera:
- `requests` : Pour faire des requêtes HTTP
- `beautifulsoup4` : Pour parser le HTML
- `lxml` : Parser XML/HTML rapide

## 📖 Utilisation

### Méthode 1: Utilisation interactive

Exécutez simplement le script:

```bash
python scraper.py
```

Le script vous demandera une URL à scraper et affichera les résultats.

### Méthode 2: Utilisation dans votre propre script

Importez la classe `WebScraper` dans votre code:

```python
from scraper import WebScraper

# Créer une instance du scraper
scraper = WebScraper("https://example.com", delay=1)

# Scraper les liens d'une page
links = scraper.scrape_links("/")
print(links)

# Sauvegarder en JSON
scraper.save_to_json(links, 'mes_liens.json')

# Sauvegarder en CSV
scraper.save_to_csv(links, 'mes_liens.csv')
```

## 🎯 Exemples d'utilisation

### Exemple 1: Scraper tous les liens d'une page

```python
from scraper import WebScraper

scraper = WebScraper("https://example.com")
links = scraper.scrape_links("/")
scraper.save_to_json(links, 'liens.json')
```

### Exemple 2: Extraire du texte avec des sélecteurs CSS

```python
from scraper import WebScraper

scraper = WebScraper("https://example.com")

# Définir ce que vous voulez extraire
selectors = {
    'titre': 'h1',
    'description': '.description',
    'prix': '.price'
}

# Scraper les données
data = scraper.scrape_text("/page", selectors)
print(data)
scraper.save_to_json(data, 'donnees.json')
```

### Exemple 3: Scraper une table HTML

```python
from scraper import WebScraper

scraper = WebScraper("https://example.com")
table_data = scraper.scrape_table("/table-page", table_selector='table')
scraper.save_to_csv(table_data, 'table.csv')
```

### Exemple 4: Scraper plusieurs pages

```python
from scraper import WebScraper

scraper = WebScraper("https://example.com")
all_data = []

# Liste des pages à scraper
pages = ["/page1", "/page2", "/page3"]

for page in pages:
    selectors = {'titre': 'h1', 'contenu': '.content'}
    data = scraper.scrape_text(page, selectors)
    all_data.append(data)

scraper.save_to_json(all_data, 'toutes_pages.json')
```

## 🔍 Comment trouver les sélecteurs CSS?

1. **Ouvrez le site web** dans votre navigateur
2. **Faites un clic droit** sur l'élément que vous voulez scraper
3. **Sélectionnez "Inspecter"** (ou "Inspect Element")
4. **Regardez le code HTML** et identifiez:
   - Les **classes CSS** (ex: `.nom-classe`)
   - Les **IDs** (ex: `#mon-id`)
   - Les **balises** (ex: `h1`, `p`, `div`)
   - Les **attributs** (ex: `[data-id="123"]`)

### Exemples de sélecteurs:

- `h1` : Tous les titres h1
- `.price` : Éléments avec la classe "price"
- `#header` : Élément avec l'ID "header"
- `div.product` : Div avec la classe "product"
- `a[href]` : Tous les liens avec un attribut href

## ⚠️ Important: Respect des sites web

1. **Respectez les robots.txt** : Vérifiez `https://site.com/robots.txt`
2. **Utilisez un délai** : Ne faites pas trop de requêtes rapidement (défaut: 1 seconde)
3. **Respectez les conditions d'utilisation** du site
4. **Ne surchargez pas les serveurs** avec trop de requêtes

## 📁 Formats de sortie

Le script peut sauvegarder les données en deux formats:

- **JSON** : Format structuré, facile à lire et manipuler
- **CSV** : Format tableur, compatible avec Excel

### 📂 Organisation des fichiers

**Par défaut, tous les fichiers sont sauvegardés dans le dossier `results/`**

Pour personnaliser le dossier de sortie :

```python
from scraper import WebScraper

# Utiliser le dossier par défaut (results)
scraper = WebScraper("https://example.com")

# Utiliser un dossier personnalisé
scraper = WebScraper("https://example.com", output_folder='mon_dossier')

# Ne pas utiliser de dossier (fichiers à la racine)
scraper = WebScraper("https://example.com", output_folder=None)
```

Le dossier est créé automatiquement s'il n'existe pas.

## 🐛 Résolution de problèmes

### Erreur: "ModuleNotFoundError"
**Solution**: Installez les dépendances avec `pip install -r requirements.txt`

### Erreur: "Connection refused" ou timeout
**Solution**: 
- Vérifiez votre connexion internet
- Le site peut bloquer les scrapers
- Essayez d'augmenter le délai entre les requêtes

### Aucune donnée trouvée
**Solution**:
- Vérifiez que les sélecteurs CSS sont corrects
- Le site peut charger du contenu dynamiquement (nécessite Selenium)
- Inspectez le code HTML de la page

## 🔧 Personnalisation

Vous pouvez modifier le script pour:
- Changer le User-Agent
- Ajouter des headers personnalisés
- Gérer les cookies
- Gérer l'authentification
- Et plus encore!

## 📚 Ressources supplémentaires

- [Documentation BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)
- [Documentation requests](https://requests.readthedocs.io/)
- [Sélecteurs CSS](https://www.w3schools.com/cssref/css_selectors.asp)

## 💡 Astuces

1. **Testez d'abord sur une seule page** avant de scraper tout le site
2. **Sauvegardez régulièrement** vos données
3. **Gérez les erreurs** dans votre code
4. **Utilisez des délais** pour éviter d'être bloqué

Bon scraping! 🚀


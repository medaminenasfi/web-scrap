# Guide de Web Scraping

Ce guide vous explique comment utiliser le script de web scraping.

## 🚀 Démarrage Rapide

1. **Installer les packages** :
   ```bash
   pip install -r requirements.txt
   ```

2. **Lancer le scraper universel** :
   ```bash
   python universal_scraper.py https://example.com
   ```

Le script détecte automatiquement le type de page (statique ou JavaScript) et sauvegarde les résultats dans un dossier organisé sous `results/`.

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

### Méthode 1: Utilisation via la ligne de commande

Exécutez simplement le script avec l’URL cible :

```bash
python universal_scraper.py https://example.com
```

Vous pouvez omettre l’URL pour utiliser la valeur par défaut (`https://fr.osstem.com/`).

### Méthode 2: Utilisation dans votre propre script

Importez la fonction `scrape_universal` depuis `universal_scraper.py` :

```python
from universal_scraper import scrape_universal

result = scrape_universal("https://example.com", output_dir="results")

# Accéder aux données extraites
links = result["result"]["links"]
tables = result["result"]["tables"]
manifest_path = result["output"]["root"] / "manifest.json"
```

## 🎯 Exemples d'utilisation

### Exemple 1: Scraper tous les liens d'une page

```python
from universal_scraper import scrape_universal

data = scrape_universal("https://example.com")
links = data["result"]["links"]
print(f"{len(links)} liens trouvés")
tables = data["result"]["tables"]
print(f"{len(tables)} tables détectées")
```

### Exemple 2: Extraire du texte avec des sélecteurs CSS

```python
from universal_scraper import scrape_universal

data = scrape_universal("https://example.com/page")
text = data["result"]["text"]
print(text["page_title"])
print(text["paragraphs"][:3])
videos = data["result"]["media"]["videos"]
print(f"{len(videos)} vidéos téléchargées automatiquement")
```

### Exemple 3: Scraper une table HTML

```python
from universal_scraper import scrape_universal

data = scrape_universal("https://example.com/table-page")
tables = data["result"]["tables"]
print(f"{len(tables)} tables détectées")
```

### Exemple 4: Scraper plusieurs pages

```python
from universal_scraper import scrape_universal

pages = [
    "https://example.com/page1",
    "https://example.com/page2",
    "https://example.com/page3",
]

results = [scrape_universal(page)["result"]["text"] for page in pages]
print(f"{len(results)} pages traitées")
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

Chaque exécution crée un dossier dédié :

```
results/<domaine>/<cheminHorodaté>/
│
├── raw/content.json        # Réponse complète
├── text/                   # all_text.txt, titles.json, etc.
├── links/links.csv
├── tables/table_*.csv      # + tables.json et tables_summary.csv
├── images/images.csv
├── images/files/           # Fichiers téléchargés
├── media/videos.csv        # + media/videos/ pour les fichiers
├── media/audios.csv        # + media/audios/ pour les fichiers
├── downloads/documents.csv # + fichiers PDF/ZIP/etc.
├── summary.json            # Indicateurs clés
└── manifest.json           # Récapitulatif des sorties
```

Utilisez le paramètre `output_dir` de `scrape_universal` pour changer l'emplacement racine.

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


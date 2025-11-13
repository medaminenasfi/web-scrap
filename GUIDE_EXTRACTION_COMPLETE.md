# 📖 Guide d'Extraction Complète - Texte, Images, Tables, Liens

## ✅ Solution Complète

Le script `scraper_complete_osstem.py` extrait **tout le contenu** d'une page web :
- ✅ **Texte** : Tout le texte de la page
- ✅ **Images** : Toutes les images avec leurs URLs
- ✅ **Tables** : Toutes les tables HTML
- ✅ **Liens** : Tous les liens

---

## 🚀 Utilisation

### Option 1: Utiliser le Script Complet (Recommandé)

```powershell
python scraper_complete_osstem.py
```

Puis entrez l'URL (ou appuyez sur Entrée pour utiliser fr.osstem.com/)

### Option 2: Utiliser dans votre Code

```python
from scraper_selenium import WebScraperSelenium

# Créer le scraper
scraper = WebScraperSelenium(
    base_url="https://fr.osstem.com/",
    delay=2,
    output_folder='results',
    headless=True
)

try:
    # Scraper tout le contenu
    complete_data = scraper.scrape_complete("/", wait_time=20)
    
    if complete_data:
        # Sauvegarder
        scraper.save_to_json(complete_data, 'complete_data.json')
        
        # Sauvegarder les images
        if complete_data.get('images'):
            scraper.save_to_csv(complete_data['images'], 'images.csv')
        
        # Sauvegarder les tables
        if complete_data.get('tables'):
            for table in complete_data['tables']:
                scraper.save_to_csv(table['rows'], f'table_{table["table_index"]}.csv')
        
        # Sauvegarder les liens
        if complete_data.get('links'):
            scraper.save_to_csv(complete_data['links'], 'links.csv')
        
        # Sauvegarder le texte
        if complete_data.get('text'):
            with open('text.txt', 'w', encoding='utf-8') as f:
                f.write(complete_data['text']['all_text'])
        
        print("Extraction complète terminée!")
finally:
    scraper.close()
```

---

## 📊 Résultats de l'Extraction

### Exemple avec fr.osstem.com

- ✅ **Texte** : 1312 caractères
- ✅ **Images** : 27 images
- ✅ **Tables** : 1 table
- ✅ **Liens** : 14 liens

### Fichiers Générés

1. **JSON complet** : `osstem_complete_fr_osstem_comhome.json`
   - Contient tout le contenu (texte, images, tables, liens)

2. **Images CSV** : `osstem_complete_fr_osstem_comhome_images.csv`
   - Colonnes : `src`, `alt`, `title`, `width`, `height`
   - URLs des images

3. **Tables CSV** : `osstem_complete_fr_osstem_comhome_table_1.csv`
   - Données de chaque table
   - Un fichier par table

4. **Liens CSV** : `osstem_complete_fr_osstem_comhome_links.csv`
   - Colonnes : `text`, `url`
   - Tous les liens de la page

5. **Texte TXT** : `osstem_complete_fr_osstem_comhome_text.txt`
   - Tout le texte de la page
   - Titres (h1, h2, h3, etc.)
   - Paragraphes
   - Listes

---

## 📝 Structure des Données

### Texte

```json
{
  "page_title": "Osstem Implant France",
  "all_text": "Tout le texte de la page...",
  "titles": {
    "h1": ["Titre 1", "Titre 2"],
    "h2": ["Sous-titre 1"],
    ...
  },
  "paragraphs": ["Paragraphe 1", "Paragraphe 2", ...],
  "lists": ["Item 1", "Item 2", ...],
  "text_length": 1312
}
```

### Images

```json
[
  {
    "src": "https://fr.osstem.com/img/image.jpg",
    "alt": "Description de l'image",
    "title": "Titre de l'image",
    "width": "1920",
    "height": "960"
  },
  ...
]
```

### Tables

```json
[
  {
    "table_index": 1,
    "headers": ["Colonne 1", "Colonne 2", ...],
    "rows": [
      {"Colonne 1": "Valeur 1", "Colonne 2": "Valeur 2"},
      ...
    ],
    "row_count": 10
  },
  ...
]
```

### Liens

```json
[
  {
    "text": "Texte du lien",
    "url": "https://fr.osstem.com/page"
  },
  ...
]
```

---

## 🔧 Fonctions Disponibles

### 1. `scrape_all_text(url, wait_time=10)`
Extrait tout le texte de la page :
- Titre de la page
- Tout le texte du body
- Titres (h1-h6)
- Paragraphes
- Listes

### 2. `scrape_images(url, wait_time=10)`
Extrait toutes les images :
- URL (src)
- Texte alternatif (alt)
- Titre (title)
- Dimensions (width, height)

### 3. `scrape_tables(url, wait_time=10)`
Extrait toutes les tables :
- En-têtes
- Données de chaque ligne
- Nombre de lignes

### 4. `scrape_links(url, wait_time=10)`
Extrait tous les liens :
- Texte du lien
- URL

### 5. `scrape_complete(url, wait_time=15)`
Extrait tout le contenu en une seule fois :
- Texte
- Images
- Tables
- Liens
- Résumé

---

## 📋 Exemples d'Utilisation

### Exemple 1: Extraire Tout le Contenu

```python
from scraper_selenium import WebScraperSelenium

scraper = WebScraperSelenium(
    base_url="https://fr.osstem.com/",
    delay=2,
    output_folder='results',
    headless=True
)

try:
    # Extraire tout
    complete_data = scraper.scrape_complete("/", wait_time=20)
    
    # Sauvegarder
    scraper.save_to_json(complete_data, 'complete.json')
finally:
    scraper.close()
```

### Exemple 2: Extraire Seulement le Texte

```python
from scraper_selenium import WebScraperSelenium

scraper = WebScraperSelenium(
    base_url="https://fr.osstem.com/",
    delay=2,
    output_folder='results',
    headless=True
)

try:
    # Extraire le texte
    text_data = scraper.scrape_all_text("/", wait_time=15)
    
    # Sauvegarder
    scraper.save_to_json(text_data, 'text.json')
    
    # Afficher
    print(f"Titre: {text_data['page_title']}")
    print(f"Texte: {text_data['all_text'][:200]}...")
finally:
    scraper.close()
```

### Exemple 3: Extraire Seulement les Images

```python
from scraper_selenium import WebScraperSelenium

scraper = WebScraperSelenium(
    base_url="https://fr.osstem.com/",
    delay=2,
    output_folder='results',
    headless=True
)

try:
    # Extraire les images
    images = scraper.scrape_images("/", wait_time=15)
    
    # Sauvegarder
    scraper.save_to_csv(images, 'images.csv')
    
    # Afficher
    print(f"{len(images)} images trouvées:")
    for img in images[:5]:
        print(f"  - {img['src']}")
finally:
    scraper.close()
```

### Exemple 4: Extraire Seulement les Tables

```python
from scraper_selenium import WebScraperSelenium

scraper = WebScraperSelenium(
    base_url="https://fr.osstem.com/",
    delay=2,
    output_folder='results',
    headless=True
)

try:
    # Extraire les tables
    tables = scraper.scrape_tables("/", wait_time=15)
    
    # Sauvegarder chaque table
    for table in tables:
        scraper.save_to_csv(table['rows'], f'table_{table["table_index"]}.csv')
        print(f"Table {table['table_index']}: {table['row_count']} lignes")
finally:
    scraper.close()
```

---

## 📁 Fichiers Générés

### Structure des Fichiers

```
results/
├── osstem_complete_fr_osstem_comhome.json      # Tout le contenu
├── osstem_complete_fr_osstem_comhome_images.csv # Images
├── osstem_complete_fr_osstem_comhome_table_1.csv # Tables
├── osstem_complete_fr_osstem_comhome_links.csv  # Liens
└── osstem_complete_fr_osstem_comhome_text.txt   # Texte
```

### Format des Fichiers

1. **JSON** : Format structuré, facile à manipuler
2. **CSV** : Format tableur, compatible avec Excel
3. **TXT** : Format texte, facile à lire

---

## 🔍 Utilisation des Données

### Lire les Données JSON

```python
import json

with open('results/osstem_complete_fr_osstem_comhome.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Accéder aux données
print(f"Texte: {data['text']['all_text']}")
print(f"Images: {len(data['images'])}")
print(f"Tables: {len(data['tables'])}")
print(f"Liens: {len(data['links'])}")
```

### Lire les Données CSV

```python
import csv

# Lire les images
with open('results/osstem_complete_fr_osstem_comhome_images.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    images = list(reader)

# Afficher les images
for img in images:
    print(f"Image: {img['src']}")
    print(f"Alt: {img['alt']}")
```

### Lire le Texte

```python
# Lire le texte
with open('results/osstem_complete_fr_osstem_comhome_text.txt', 'r', encoding='utf-8') as f:
    text = f.read()

print(text)
```

---

## 💡 Conseils

### 1. **Attente Intelligente**
- Utilisez `wait_time=20` pour les sites lents
- Le script attend automatiquement que JavaScript charge le contenu

### 2. **Mode Headless**
- `headless=True` : Plus rapide, invisible
- `headless=False` : Visible, utile pour le débogage

### 3. **Gestion des Images**
- Les images sont sauvegardées avec leurs URLs
- Pour télécharger les images, utilisez `requests` ou `urllib`

### 4. **Gestion des Tables**
- Chaque table est sauvegardée séparément
- Les en-têtes sont détectés automatiquement

---

## 🐛 Résolution de Problèmes

### Aucune Donnée Extraite
**Solutions** :
- Augmentez `wait_time` (20 secondes ou plus)
- Vérifiez que le site s'affiche dans un navigateur
- Utilisez `headless=False` pour voir ce qui se passe

### Images Manquantes
**Solutions** :
- Certaines images peuvent être chargées dynamiquement
- Augmentez `wait_time` pour laisser le temps aux images de charger
- Vérifiez les URLs dans le CSV

### Tables Vides
**Solutions** :
- La table peut être chargée dynamiquement
- Vérifiez le site dans un navigateur
- La table peut utiliser JavaScript pour générer les données

---

## ✅ Checklist

- [x] Selenium installé (`pip install selenium webdriver-manager`)
- [x] Chrome installé sur le système
- [x] Script de test exécuté (`python scraper_complete_osstem.py`)
- [x] Données extraites et sauvegardées
- [x] Fichiers JSON, CSV, TXT générés
- [x] Driver fermé correctement

---

## 🎯 Prochaines Étapes

1. **Télécharger les Images** : Utiliser les URLs pour télécharger les images
2. **Analyser les Données** : Utiliser les données pour l'analyse
3. **Scraper Plusieurs Pages** : Scraper plusieurs pages du site
4. **Automatiser** : Créer un script pour scraper automatiquement

---

**Bon scraping ! 🚀**


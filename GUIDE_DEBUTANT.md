# 🚀 Guide Débutant - Installation et Utilisation

## 📋 Table des Matières
1. [Prérequis](#prérequis)
2. [Installation](#installation)
3. [Premier Test](#premier-test)
4. [Exemples d'Utilisation](#exemples-dutilisation)
5. [Résolution de Problèmes](#résolution-de-problèmes)

---

## 📋 Prérequis

### Vérifier que Python est installé

1. **Ouvrez PowerShell** (ou CMD)
2. **Tapez cette commande** :
   ```powershell
   python --version
   ```
3. **Vous devriez voir** quelque chose comme : `Python 3.8.x` ou plus récent

   ❌ **Si vous voyez une erreur** : 
   - Téléchargez Python depuis [python.org](https://www.python.org/downloads/)
   - ⚠️ **Important** : Cochez "Add Python to PATH" lors de l'installation

### Vérifier que pip est installé

1. **Tapez cette commande** :
   ```powershell
   pip --version
   ```
2. **Vous devriez voir** : `pip 20.x.x` ou plus récent

---

## 🔧 Installation

### Étape 1: Ouvrir le Terminal

1. **Ouvrez PowerShell** ou **CMD**
2. **Naviguez vers le dossier du projet** :
   ```powershell
   cd C:\Users\Medam\Desktop\scrap
   ```

### Étape 2: Créer un Environnement Virtuel (Recommandé)

**Option A: Avec venv (Recommandé)**
```powershell
python -m venv venv
venv\Scripts\activate
```

**Option B: Sans environnement virtuel**
Vous pouvez installer directement, mais c'est moins recommandé.

### Étape 3: Installer les Packages

**Tapez cette commande** :
```powershell
pip install -r requirements.txt
```

**Vous devriez voir** :
```
Collecting requests==2.31.0
Collecting beautifulsoup4==4.12.2
Collecting lxml==4.9.3
Installing collected packages: ...
Successfully installed requests-2.31.0 beautifulsoup4-4.12.2 lxml-4.9.3
```

✅ **Si tout s'est bien passé**, vous êtes prêt !

---

## 🧪 Premier Test

### Test Simple

1. **Exécutez le script de test** :
   ```powershell
   python test_scraper.py
   ```

2. **Ce script va** :
   - Tester la connexion à Internet
   - Scraper des liens depuis example.com
   - Extraire du texte
   - Sauvegarder les résultats dans des fichiers JSON et CSV

3. **Résultats attendus** :
   ```
   ============================================================
   TEST BASIQUE DU WEB SCRAPER
   ============================================================
   
   1. Test de connexion...
   ✓ Scraper créé avec succès
   
   2. Test: Scraping de liens...
   ✓ X lien(s) trouvé(s)
   ...
   ```

4. **Fichiers générés** :
   - `test_liens.json` - Données au format JSON
   - `test_liens.csv` - Données au format CSV (ouvrable avec Excel)

---

## 📖 Exemples d'Utilisation

### Exemple 1: Scraper les Liens d'une Page

**Créez un fichier `mon_test.py`** :
```python
from scraper import WebScraper

# Créer le scraper
scraper = WebScraper("https://example.com", delay=1)

# Scraper les liens
links = scraper.scrape_links("/")

# Afficher les résultats
print(f"Nombre de liens trouvés: {len(links)}")
for link in links[:5]:  # Afficher les 5 premiers
    print(f"- {link['text']} -> {link['url']}")

# Sauvegarder
scraper.save_to_json(links, 'mes_liens.json')
```

**Exécutez** :
```powershell
python mon_test.py
```

### Exemple 2: Extraire du Texte Spécifique

```python
from scraper import WebScraper

scraper = WebScraper("https://example.com", delay=1)

# Définir ce que vous voulez extraire
selectors = {
    'titre': 'h1',
    'paragraphe': 'p'
}

# Scraper
data = scraper.scrape_text("/", selectors)

# Afficher
print(data)
# Résultat: {'titre': 'Example Domain', 'paragraphe': '...'}

# Sauvegarder
scraper.save_to_json(data, 'mes_donnees.json')
```

### Exemple 3: Utiliser les Exemples Prédéfinis

**Ouvrez `exemple_utilisation.py`** et décommentez un exemple :

```python
# Décommentez cette ligne :
exemple_1_liens_simples()
```

**Exécutez** :
```powershell
python exemple_utilisation.py
```

---

## 🎯 Guide Pas à Pas pour Scraper un Site

### Étape 1: Choisir un Site

**Commencez par un site simple** comme :
- `https://example.com` (pour tester)
- `https://quotes.toscrape.com` (site de test pour scraping)

### Étape 2: Inspecter la Page

1. **Ouvrez le site** dans votre navigateur
2. **Faites clic droit** sur l'élément que vous voulez scraper
3. **Sélectionnez "Inspecter"** (ou "Inspect Element")
4. **Regardez le code HTML** pour trouver :
   - Les **classes CSS** (ex: `.price`, `.title`)
   - Les **IDs** (ex: `#header`)
   - Les **balises** (ex: `h1`, `p`, `div`)

### Étape 3: Créer votre Script

```python
from scraper import WebScraper

# 1. Définir l'URL
base_url = "https://quotes.toscrape.com"

# 2. Créer le scraper
scraper = WebScraper(base_url, delay=2)  # 2 secondes entre chaque requête

# 3. Définir les sélecteurs (remplacez par ceux de votre site)
selectors = {
    'citation': '.text',
    'auteur': '.author',
    'tags': '.tag'
}

# 4. Scraper
data = scraper.scrape_text("/", selectors)

# 5. Afficher
print(data)

# 6. Sauvegarder
scraper.save_to_json(data, 'citation.json')
```

### Étape 4: Exécuter et Vérifier

```powershell
python mon_script.py
```

**Note** : Les fichiers de résultats sont automatiquement sauvegardés dans le dossier `results/`

---

## 📂 Organisation des Fichiers

### Dossier de Résultats

**Par défaut, tous les fichiers sont sauvegardés dans le dossier `results/`**

Le dossier est créé automatiquement lors de la première exécution.

### Personnaliser le Dossier de Sortie

```python
from scraper import WebScraper

# Utiliser le dossier par défaut (results)
scraper = WebScraper("https://example.com")

# Utiliser un dossier personnalisé
scraper = WebScraper("https://example.com", output_folder='mon_dossier')

# Ne pas utiliser de dossier (fichiers à la racine)
scraper = WebScraper("https://example.com", output_folder=None)
```

### Structure du Dossier

```
scrap/
├── results/          # Dossier de résultats (créé automatiquement)
│   ├── test_liens.json
│   ├── test_liens.csv
│   └── ...
├── scraper.py
├── test_scraper.py
└── ...
```

---

## 🐛 Résolution de Problèmes

### Erreur: "ModuleNotFoundError: No module named 'requests'"

**Solution** :
```powershell
pip install -r requirements.txt
```

**Si ça ne marche pas** :
```powershell
pip install requests beautifulsoup4 lxml
```

---

### Erreur: "python : Le terme 'python' n'est pas reconnu"

**Solutions** :

1. **Vérifiez que Python est installé** :
   ```powershell
   py --version
   ```
   Si ça marche, utilisez `py` au lieu de `python`

2. **Ajoutez Python au PATH** :
   - Réinstallez Python et cochez "Add Python to PATH"
   - Ou ajoutez manuellement Python au PATH système

---

### Erreur: "Connection refused" ou "Timeout"

**Solutions** :

1. **Vérifiez votre connexion Internet**
2. **Vérifiez l'URL** (elle doit être accessible)
3. **Augmentez le délai** :
   ```python
   scraper = WebScraper("https://example.com", delay=3)  # 3 secondes
   ```
4. **Le site peut bloquer les scrapers** - Essayez avec un autre site

---

### Aucune Donnée Trouvée

**Solutions** :

1. **Vérifiez les sélecteurs CSS** :
   - Inspectez la page dans le navigateur
   - Vérifiez que les sélecteurs sont corrects
   - Testez avec des sélecteurs simples d'abord (`h1`, `p`, etc.)

2. **Le contenu peut être chargé dynamiquement** :
   - Certains sites utilisent JavaScript pour charger le contenu
   - Dans ce cas, vous aurez besoin de Selenium (plus avancé)

3. **Vérifiez que l'URL est correcte** :
   ```python
   # Testez d'abord avec une URL simple
   scraper = WebScraper("https://example.com")
   links = scraper.scrape_links("/")
   print(links)  # Vérifiez si des liens sont trouvés
   ```

---

### Erreur lors de la Sauvegarde

**Solutions** :

1. **Vérifiez les permissions** :
   - Assurez-vous d'avoir les droits d'écriture dans le dossier

2. **Vérifiez le format des données** :
   - Pour CSV, les données doivent être une liste de dictionnaires
   - Pour JSON, n'importe quelle structure est acceptée

---

## 📚 Commandes Utiles

### Installer les packages
```powershell
pip install -r requirements.txt
```

### Exécuter le script principal
```powershell
python scraper.py
```

### Exécuter les exemples
```powershell
python exemple_utilisation.py
```

### Exécuter le test
```powershell
python test_scraper.py
```

### Vérifier les packages installés
```powershell
pip list
```

### Mettre à jour pip
```powershell
python -m pip install --upgrade pip
```

---

## ✅ Checklist de Démarrage

- [ ] Python 3.7+ installé
- [ ] pip installé
- [ ] Packages installés (`pip install -r requirements.txt`)
- [ ] Test exécuté avec succès (`python test_scraper.py`)
- [ ] Compris comment utiliser les sélecteurs CSS
- [ ] Testé sur un site simple (example.com)

---

## 🎓 Prochaines Étapes

1. **Testez sur différents sites** :
   - Commencez par des sites simples
   - Puis essayez des sites plus complexes

2. **Apprenez les sélecteurs CSS** :
   - `.class` pour les classes
   - `#id` pour les IDs
   - `tag` pour les balises
   - `tag.class` pour combiner

3. **Explorez les exemples** :
   - Ouvrez `exemple_utilisation.py`
   - Décommentez et testez chaque exemple

4. **Lisez la documentation** :
   - [BeautifulSoup Documentation](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)
   - [Requests Documentation](https://requests.readthedocs.io/)

---

## 💡 Astuces

1. **Commencez simple** : Testez d'abord avec `example.com`
2. **Utilisez des délais** : Respectez les serveurs (delay=2 secondes minimum)
3. **Sauvegardez régulièrement** : Ne perdez pas vos données
4. **Testez les sélecteurs** : Vérifiez dans le navigateur avant de scraper
5. **Gérez les erreurs** : Ajoutez des try/except dans votre code

---

## 🆘 Besoin d'Aide ?

1. **Vérifiez les erreurs** : Lisez les messages d'erreur attentivement
2. **Testez étape par étape** : Ne testez pas tout d'un coup
3. **Utilisez le script de test** : `python test_scraper.py`
4. **Consultez la documentation** : README.md et ce guide

---

**Bon scraping ! 🚀**


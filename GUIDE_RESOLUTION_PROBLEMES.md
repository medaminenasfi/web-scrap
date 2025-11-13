# 🔧 Guide de Résolution des Problèmes

## ❌ Problème : "Aucun lien trouvé"

### Symptômes
- Le script affiche "Aucun lien trouvé"
- L'URL semble correcte
- Le site s'affiche normalement dans le navigateur

### ✅ Solutions Appliquées

#### 1. **Correction de l'Extraction d'URL**
- **Avant** : Le script utilisait toujours "/" même avec une URL complète
- **Après** : Le script extrait maintenant correctement le chemin de l'URL fournie
- **Exemple** : 
  - URL fournie: `https://fr.osstem.com/dental/product/dental-product-implant-bone-ts-fr`
  - Base URL: `https://fr.osstem.com`
  - Chemin: `/dental/product/dental-product-implant-bone-ts-fr`

#### 2. **Amélioration des Headers HTTP**
- User-Agent mis à jour (Chrome 120)
- Ajout de headers réalistes (Accept, Accept-Language, etc.)
- Meilleure compatibilité avec les sites modernes

#### 3. **Meilleure Gestion des Erreurs**
- Détection des codes de statut HTTP (403, 404, 503)
- Messages d'erreur plus informatifs
- Diagnostic des problèmes de connexion

#### 4. **Augmentation du Délai**
- Délai par défaut augmenté à 2 secondes
- Réduit les risques de blocage par les serveurs
- Plus respectueux des sites web

---

## 🔍 Diagnostic des Problèmes

### 1. Site Bloque les Scrapers (403 Forbidden)

**Symptômes** :
- Code HTTP 403
- Message "Le site bloque probablement les scrapers"

**Solutions** :
- Augmenter le délai (`delay=3` ou plus)
- Utiliser un User-Agent différent
- Ajouter des cookies si nécessaire
- Utiliser un proxy (avancé)
- Utiliser Selenium pour simuler un navigateur réel

### 2. Contenu Chargé Dynamiquement (JavaScript)

**Symptômes** :
- Page vide ou peu de contenu
- Le contenu s'affiche dans le navigateur mais pas dans le scraper

**Solutions** :
- Utiliser Selenium avec un navigateur headless
- Attendre le chargement du JavaScript
- Utiliser des outils comme Playwright ou Puppeteer

### 3. Authentification Requise

**Symptômes** :
- Page de connexion
- Contenu protégé

**Solutions** :
- Ajouter des cookies de session
- Utiliser l'authentification HTTP
- Se connecter manuellement et copier les cookies

### 4. Timeout ou Erreur de Connexion

**Symptômes** :
- Timeout
- Erreur de connexion

**Solutions** :
- Vérifier la connexion Internet
- Augmenter le timeout (défaut: 15 secondes)
- Vérifier que le site est accessible
- Essayer plus tard si le serveur est surchargé

---

## 💡 Conseils d'Utilisation

### 1. **Tester d'Abord avec des Sites Simples**
```python
# Commencez par des sites de test
scraper = WebScraper("https://example.com")
links = scraper.scrape_links("/")
```

### 2. **Augmenter le Délai pour les Sites Sensibles**
```python
# Utiliser un délai plus long
scraper = WebScraper("https://example.com", delay=3)
```

### 3. **Vérifier le Site dans un Navigateur**
- Ouvrez le site dans votre navigateur
- Vérifiez que le contenu s'affiche
- Inspectez le code HTML (F12)
- Vérifiez si le contenu est chargé via JavaScript

### 4. **Utiliser les Sélecteurs CSS Corrects**
```python
# Inspecter le site pour trouver les bons sélecteurs
selectors = {
    'titre': 'h1',           # Balise
    'prix': '.price',        # Classe
    'description': '#desc'   # ID
}
```

---

## 🚀 Exemple d'Utilisation Corrigé

```python
from scraper import WebScraper
from urllib.parse import urlparse

# URL complète
url_input = "https://fr.osstem.com/dental/product/dental-product-implant-bone-ts-fr"

# Parser l'URL
parsed_url = urlparse(url_input)
base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
path = parsed_url.path if parsed_url.path else "/"

# Créer le scraper avec un délai approprié
scraper = WebScraper(base_url, delay=2, output_folder='results')

# Scraper la page spécifique
links = scraper.scrape_links(path)

# Afficher les résultats
if links:
    print(f"Trouvé {len(links)} liens")
    for link in links[:10]:
        print(f"- {link['text']} -> {link['url']}")
else:
    print("Aucun lien trouvé")
    print("Le site peut bloquer les scrapers ou utiliser JavaScript")
```

---

## 📝 Checklist de Diagnostic

- [ ] L'URL est correcte et accessible dans un navigateur
- [ ] Le contenu s'affiche dans le navigateur (pas de JavaScript requis)
- [ ] Le délai est approprié (2-3 secondes minimum)
- [ ] Les sélecteurs CSS sont corrects
- [ ] Le site ne bloque pas les scrapers (pas de 403)
- [ ] La connexion Internet fonctionne
- [ ] Le site n'exige pas d'authentification

---

## 🆘 Si le Problème Persiste

1. **Vérifier les Logs** : Regardez les messages d'erreur dans la console
2. **Tester avec un Site Simple** : Utilisez `https://example.com` pour vérifier que le scraper fonctionne
3. **Inspecter le HTML** : Utilisez les outils de développement du navigateur (F12)
4. **Vérifier robots.txt** : Visitez `https://site.com/robots.txt`
5. **Contacter le Support** : Si le site a une API, utilisez-la plutôt que le scraping

---

## 📚 Ressources

- [BeautifulSoup Documentation](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)
- [Requests Documentation](https://requests.readthedocs.io/)
- [Selenium Documentation](https://www.selenium.dev/documentation/) (pour JavaScript)
- [Web Scraping Best Practices](https://www.scrapehero.com/web-scraping-best-practices/)

---

**Bon scraping ! 🚀**


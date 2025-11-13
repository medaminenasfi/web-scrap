"""
Universal web scraper for static & JavaScript-driven sites.

Usage:
    python universal_scraper.py https://example.com/page

Exports per run:
    results/<domain>/<path_timestamp>/
        raw/content.json         -> données complètes (mode utilisé, résumé, etc.)
        text/                    -> textes séparés (all_text, titres, paragraphes, listes)
        links/links.csv          -> liens uniques
        tables/table_X.csv       -> tables individuelles + tables_summary.csv + tables.json
        images/images.csv        -> métadonnées images + téléchargement dans images/files/
        media/videos.csv         -> vidéos détectées + téléchargement dans media/videos/
        media/audios.csv         -> audios détectés + téléchargement dans media/audios/
        downloads/documents.csv  -> pièces jointes (PDF, etc.) téléchargées
        summary.json             -> synthèse des volumes
        manifest.json            -> récapitulatif des fichiers générés
"""

import sys
import io
import os
import json
import csv
import time
from datetime import datetime
from typing import Dict, List, Tuple

import requests
from urllib.parse import urljoin, urlparse
from pathlib import Path

from bs4 import BeautifulSoup

# Optional: Selenium fallback for JavaScript content
SELENIUM_AVAILABLE = True
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException
    from webdriver_manager.chrome import ChromeDriverManager
except ImportError:
    SELENIUM_AVAILABLE = False

# Ensure UTF-8 stdout on Windows
if sys.platform == "win32":
    if hasattr(sys.stdout, "buffer"):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)

# ----------------------------------------------------------------------
# Utility functions
# ----------------------------------------------------------------------
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
    "Connection": "keep-alive",
}

DOWNLOAD_TIMEOUT = 20
DOCUMENT_EXTENSIONS = {".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".zip", ".rar", ".csv"}


def slugify(value: str) -> str:
    cleaned = "".join(c if c.isalnum() else "_" for c in value)
    return cleaned.strip("_") or "home"


def create_run_dirs(target_url: str, base_dir: str = "results") -> Dict[str, Path]:
    parsed = urlparse(target_url)
    domain = slugify(parsed.netloc or "site")
    path = slugify(parsed.path.strip("/") or "home")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    root = Path(base_dir) / domain / f"{path}_{timestamp}"
    folders = {
        "root": root,
        "raw": root / "raw",
        "text": root / "text",
        "links": root / "links",
        "tables": root / "tables",
        "images": root / "images",
        "image_files": root / "images" / "files",
        "media": root / "media",
        "videos": root / "media" / "videos",
        "audios": root / "media" / "audios",
        "downloads": root / "downloads",
    }
    for folder in folders.values():
        folder.mkdir(parents=True, exist_ok=True)
    return folders

def save_json(data, filepath: Path):
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def save_csv(rows: List[Dict[str, str]], filepath: Path, fieldnames=None):
    if not rows:
        return
    if fieldnames is None:
        fieldnames = rows[0].keys()
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_text(text: str, filepath: Path):
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(text)


def infer_filename(url: str, fallback_prefix: str, position: int, default_ext: str = "") -> str:
    parsed = urlparse(url)
    filename = os.path.basename(parsed.path)
    if not filename or "." not in filename:
        suffix = f".{default_ext.lstrip('.')}" if default_ext else ""
        filename = f"{fallback_prefix}_{position}{suffix}"
    return filename


def download_assets(
    items: List[Dict[str, str]],
    output_folder: Path,
    url_key: str = "src",
    fallback_prefix: str = "asset",
    default_ext: str = "",
    skip_data_uri: bool = True,
) -> Tuple[int, int, int]:
    downloaded, skipped, errors = 0, 0, 0
    for idx, item in enumerate(items, 1):
        target_url = item.get(url_key)
        if not target_url:
            skipped += 1
            continue
        if skip_data_uri and target_url.startswith("data:"):
            skipped += 1
            continue
        try:
            filename = infer_filename(target_url, fallback_prefix, idx, default_ext=default_ext)
            filepath = output_folder / filename
            resp = requests.get(target_url, headers=HEADERS, timeout=DOWNLOAD_TIMEOUT, stream=True)
            resp.raise_for_status()
            with open(filepath, "wb") as out:
                for chunk in resp.iter_content(chunk_size=8192):
                    out.write(chunk)
            item["local_path"] = str(filepath)
            downloaded += 1
            print(f"[DL] {idx}/{len(items)} -> {filepath.name}")
        except Exception as e:
            item["error"] = str(e)
            errors += 1
            print(f"[DL] erreur {target_url}: {e}")
    return downloaded, skipped, errors


def download_images(images, output_folder: Path):
    downloaded, skipped, errors = download_assets(
        images, output_folder, url_key="src", fallback_prefix="image", default_ext="jpg"
    )
    print(f"[IMG] Téléchargées: {downloaded} | Ignorées: {skipped} | Erreurs: {errors}")

# ----------------------------------------------------------------------
# Static scraper (requests + BeautifulSoup)
# ----------------------------------------------------------------------
def scrape_static(base_url, path="/", session=None):
    session = session or requests.Session()
    session.headers.update(HEADERS)
    full_url = urljoin(base_url, path)
    print(f"[STATIC] Récupération: {full_url}")
    resp = session.get(full_url, timeout=15)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    # Text
    body = soup.body or soup
    all_text = body.get_text("\n", strip=True)
    titles = {f"h{i}": [h.get_text(strip=True) for h in soup.find_all(f"h{i}")]
              for i in range(1, 7)}
    paragraphs = [p.get_text(strip=True) for p in soup.find_all("p") if p.get_text(strip=True)]
    lists = [li.get_text(strip=True) for li in soup.find_all("li") if li.get_text(strip=True)]

    text_data = {
        "page_title": soup.title.string.strip() if soup.title and soup.title.string else "",
        "all_text": all_text,
        "titles": titles,
        "paragraphs": paragraphs,
        "lists": lists,
        "text_length": len(all_text),
    }

    # Links
    links = []
    for a in soup.find_all("a", href=True):
        href = urljoin(base_url, a["href"])
        links.append({"text": a.get_text(strip=True) or href, "url": href})
    # Deduplicate
    seen = set()
    unique_links = []
    for link in links:
        if link["url"] not in seen:
            seen.add(link["url"])
            unique_links.append(link)

    # Images
    images = []
    for img in soup.find_all("img"):
        src = img.get("src") or img.get("data-src")
        if not src:
            continue
        src = urljoin(base_url, src)
        images.append({
            "src": src,
            "alt": img.get("alt", ""),
            "title": img.get("title", ""),
            "width": img.get("width", ""),
            "height": img.get("height", "")
        })
    # Deduplicate
    seen_img = set()
    unique_images = []
    for img in images:
        if img["src"] not in seen_img:
            seen_img.add(img["src"])
            unique_images.append(img)

    # Tables
    tables = []
    for idx, table in enumerate(soup.find_all("table"), 1):
        headers = []
        header_row = table.find("thead") or table.find("tr")
        if header_row:
            headers = [th.get_text(strip=True) for th in header_row.find_all(["th", "td"])]

        rows = []
        tbodies = table.find_all("tbody") or [table]
        for tbody in tbodies:
            for tr in tbody.find_all("tr"):
                cells = [td.get_text(strip=True) for td in tr.find_all(["td", "th"])]
                if not cells:
                    continue
                if headers and len(headers) == len(cells):
                    row_dict = dict(zip(headers, cells))
                else:
                    row_dict = {f"col_{i}": cell for i, cell in enumerate(cells)}
                rows.append(row_dict)

        tables.append({
            "table_index": idx,
            "headers": headers,
            "rows": rows,
            "row_count": len(rows)
        })

    # Media: videos & audio
    videos = []
    for video in soup.find_all("video"):
        sources = [video.get("src")] + [s.get("src") for s in video.find_all("source")]
        for src in sources:
            if not src:
                continue
            abs_src = urljoin(base_url, src)
            videos.append({
                "src": abs_src,
                "type": video.get("type") or "",
                "width": video.get("width") or "",
                "height": video.get("height") or "",
                "attributes": {k: v for k, v in video.attrs.items() if k not in {"src", "width", "height", "type"}},
            })

    audios = []
    for audio in soup.find_all("audio"):
        sources = [audio.get("src")] + [s.get("src") for s in audio.find_all("source")]
        for src in sources:
            if not src:
                continue
            abs_src = urljoin(base_url, src)
            audios.append({
                "src": abs_src,
                "type": audio.get("type") or "",
                "attributes": {k: v for k, v in audio.attrs.items() if k not in {"src", "type"}},
            })

    documents = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        abs_href = urljoin(base_url, href)
        parsed = urlparse(abs_href)
        ext = Path(parsed.path).suffix.lower()
        if ext in DOCUMENT_EXTENSIONS:
            documents.append({
                "href": abs_href,
                "extension": ext,
                "text": a.get_text(strip=True),
            })

    summary = {
        "text_length": text_data["text_length"],
        "images_count": len(unique_images),
        "tables_count": len(tables),
        "links_count": len(unique_links),
        "videos_count": len(videos),
        "audios_count": len(audios),
        "documents_count": len(documents),
        "size_bytes": len(resp.content)
    }

    return {
        "mode": "static",
        "url": full_url,
        "text": text_data,
        "images": unique_images,
        "tables": tables,
        "links": unique_links,
        "media": {
            "videos": videos,
            "audios": audios,
            "documents": documents,
        },
        "summary": summary,
        "html_preview": resp.text[:2000]
    }

# ----------------------------------------------------------------------
# Selenium scraper (JavaScript)
# ----------------------------------------------------------------------
class SeleniumScraper:
    def __init__(self, base_url, delay=2, headless=True):
        if not SELENIUM_AVAILABLE:
            raise RuntimeError("Selenium non installé. pip install selenium webdriver-manager")

        self.base_url = base_url
        self.delay = delay
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option("useAutomationExtension", False)
        chrome_options.add_argument(f"user-agent={USER_AGENT}")

        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    def load_page(self, url, wait_time=10):
        full_url = urljoin(self.base_url, url)
        print(f"[SELENIUM] Chargement: {full_url}")
        self.driver.get(full_url)
        WebDriverWait(self.driver, wait_time).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        time.sleep(self.delay)
        return full_url

    def extract_all(self, url="/", wait_time=15):
        full_url = self.load_page(url, wait_time)
        body = self.driver.find_element(By.TAG_NAME, "body")
        all_text = body.text.strip()

        titles = {}
        for i in range(1, 7):
            elements = self.driver.find_elements(By.CSS_SELECTOR, f"h{i}")
            titles[f"h{i}"] = [el.text.strip() for el in elements if el.text.strip()]

        paragraphs = [p.text.strip() for p in self.driver.find_elements(By.TAG_NAME, "p") if p.text.strip()]
        lists = [li.text.strip() for li in self.driver.find_elements(By.TAG_NAME, "li") if li.text.strip()]

        text_data = {
            "page_title": self.driver.title,
            "all_text": all_text,
            "titles": titles,
            "paragraphs": paragraphs,
            "lists": lists,
            "text_length": len(all_text)
        }

        # Links
        links = []
        for a in self.driver.find_elements(By.TAG_NAME, "a"):
            href = a.get_attribute("href")
            if href:
                href = urljoin(self.base_url, href)
                text = a.text.strip() or href
                links.append({"text": text, "url": href})
        seen = set()
        unique_links = []
        for link in links:
            if link["url"] not in seen:
                seen.add(link["url"])
                unique_links.append(link)

        # Images
        images = []
        for img in self.driver.find_elements(By.TAG_NAME, "img"):
            src = img.get_attribute("src") or img.get_attribute("data-src")
            if src:
                src = urljoin(self.base_url, src)
                images.append({
                    "src": src,
                    "alt": img.get_attribute("alt") or "",
                    "title": img.get_attribute("title") or "",
                    "width": img.get_attribute("width") or "",
                    "height": img.get_attribute("height") or ""
                })
        seen_img = set()
        unique_images = []
        for img in images:
            if img["src"] not in seen_img:
                seen_img.add(img["src"])
                unique_images.append(img)

        # Tables
        tables = []
        table_elements = self.driver.find_elements(By.TAG_NAME, "table")
        for idx, table in enumerate(table_elements, 1):
            headers = []
            try:
                header_row = table.find_element(By.TAG_NAME, "thead")
                if header_row:
                    headers = [th.text.strip() for th in header_row.find_elements(By.TAG_NAME, "th")]
            except:
                pass

            rows = []
            try:
                tbody = table.find_elements(By.TAG_NAME, "tbody")
                tbodies = tbody if tbody else [table]
                for tb in tbodies:
                    tr_elements = tb.find_elements(By.TAG_NAME, "tr")
                    for tr in tr_elements:
                        cells = [td.text.strip() for td in tr.find_elements(By.TAG_NAME, "td")]
                        if not cells:
                            continue
                        if headers and len(headers) == len(cells):
                            row_dict = dict(zip(headers, cells))
                        else:
                            row_dict = {f"col_{i}": cell for i, cell in enumerate(cells)}
                        rows.append(row_dict)
            except:
                pass

            tables.append({
                "table_index": idx,
                "headers": headers,
                "rows": rows,
                "row_count": len(rows)
            })

        # Media
        videos = []
        video_elements = self.driver.find_elements(By.TAG_NAME, "video")
        for video in video_elements:
            candidates = [video.get_attribute("src")]
            candidates.extend(
                source.get_attribute("src") for source in video.find_elements(By.TAG_NAME, "source")
            )
            for src in candidates:
                if src:
                    src = urljoin(self.base_url, src)
                    videos.append({
                        "src": src,
                        "type": video.get_attribute("type") or "",
                        "width": video.get_attribute("width") or "",
                        "height": video.get_attribute("height") or "",
                        "attributes": {},
                    })

        audios = []
        audio_elements = self.driver.find_elements(By.TAG_NAME, "audio")
        for audio in audio_elements:
            candidates = [audio.get_attribute("src")]
            candidates.extend(
                source.get_attribute("src") for source in audio.find_elements(By.TAG_NAME, "source")
            )
            for src in candidates:
                if src:
                    src = urljoin(self.base_url, src)
                    audios.append({
                        "src": src,
                        "type": audio.get_attribute("type") or "",
                        "attributes": {},
                    })

        documents = []
        for a in self.driver.find_elements(By.TAG_NAME, "a"):
            href = a.get_attribute("href")
            if not href:
                continue
            href = urljoin(self.base_url, href)
            ext = Path(urlparse(href).path).suffix.lower()
            if ext in DOCUMENT_EXTENSIONS:
                documents.append({
                    "href": href,
                    "extension": ext,
                    "text": a.text.strip(),
                })

        summary = {
            "text_length": text_data["text_length"],
            "images_count": len(unique_images),
            "tables_count": len(tables),
            "links_count": len(unique_links),
            "videos_count": len(videos),
            "audios_count": len(audios),
            "documents_count": len(documents),
        }

        return {
            "mode": "selenium",
            "url": full_url,
            "text": text_data,
            "images": unique_images,
            "tables": tables,
            "links": unique_links,
            "media": {
                "videos": videos,
                "audios": audios,
                "documents": documents,
            },
            "summary": summary
        }

    def close(self):
        self.driver.quit()

# ----------------------------------------------------------------------
# Universal scraper
# ----------------------------------------------------------------------
def scrape_universal(url, output_dir="results", headless=True):
    parsed = urlparse(url)
    base_url = f"{parsed.scheme}://{parsed.netloc}"
    path = parsed.path or "/"
    if parsed.query:
        path += f"?{parsed.query}"
    if parsed.fragment:
        path += f"#{parsed.fragment}"

    output_dirs = create_run_dirs(url, output_dir)
    session = requests.Session()

    try:
        static_data = scrape_static(base_url, path, session=session)
        if static_data["summary"]["text_length"] > 800 or static_data["summary"]["links_count"] > 10:
            print("[UNIVERSAL] Contenu riche détecté en mode statique, pas de Selenium nécessaire.")
            result = static_data
        else:
            if not SELENIUM_AVAILABLE:
                print("[UNIVERSAL] Selenium indisponible, conservation des données statiques.")
                result = static_data
            else:
                print("[UNIVERSAL] Contenu léger détecté, tentative avec Selenium pour contenu dynamique.")
                driver = SeleniumScraper(base_url, headless=headless)
                try:
                    result = driver.extract_all(path)
                finally:
                    driver.close()
    except Exception:
        if not SELENIUM_AVAILABLE:
            raise
        print("[UNIVERSAL] Échec du mode statique, bascule vers Selenium.")
        driver = SeleniumScraper(base_url, headless=headless)
        try:
            result = driver.extract_all(path)
        finally:
            driver.close()

    result.setdefault("media", {"videos": [], "audios": [], "documents": []})
    for key in ("videos", "audios", "documents"):
        result["media"].setdefault(key, [])

    save_json(result, output_dirs["raw"] / "content.json")

    text_data = result.get("text", {})
    all_text = text_data.get("all_text", "")
    exports = {}

    if all_text:
        write_text(all_text, output_dirs["text"] / "all_text.txt")
        exports["text_all"] = str(output_dirs["text"] / "all_text.txt")

    titles = text_data.get("titles")
    if titles:
        save_json(titles, output_dirs["text"] / "titles.json")
        exports["text_titles"] = str(output_dirs["text"] / "titles.json")

    paragraphs = text_data.get("paragraphs")
    if paragraphs:
        write_text("\n\n".join(paragraphs), output_dirs["text"] / "paragraphs.txt")
        exports["text_paragraphs"] = str(output_dirs["text"] / "paragraphs.txt")

    lists = text_data.get("lists")
    if lists:
        write_text("\n".join(f"- {item}" for item in lists), output_dirs["text"] / "lists.txt")
        exports["text_lists"] = str(output_dirs["text"] / "lists.txt")

    if result["links"]:
        save_csv(result["links"], output_dirs["links"] / "links.csv")
        exports["links"] = str(output_dirs["links"] / "links.csv")

    if result["tables"]:
        for table in result["tables"]:
            filename = output_dirs["tables"] / f"table_{table['table_index']}.csv"
            save_csv(table["rows"], filename)
            exports[f"table_{table['table_index']}"] = str(filename)
        save_json(result["tables"], output_dirs["tables"] / "tables.json")
        exports["tables_json"] = str(output_dirs["tables"] / "tables.json")
        summary_tables = [
            {
                "table_index": table["table_index"],
                "row_count": table["row_count"],
                "headers": ", ".join(table["headers"]),
            }
            for table in result["tables"]
        ]
        save_csv(summary_tables, output_dirs["tables"] / "tables_summary.csv")
        exports["tables_summary"] = str(output_dirs["tables"] / "tables_summary.csv")

    if result["images"]:
        save_csv(result["images"], output_dirs["images"] / "images.csv")
        exports["images_metadata"] = str(output_dirs["images"] / "images.csv")
        download_images(result["images"], output_dirs["image_files"])
        exports["images_files"] = str(output_dirs["image_files"])

    media = result.get("media", {})

    videos = media.get("videos", [])
    if videos:
        save_csv(videos, output_dirs["media"] / "videos.csv")
        exports["videos_metadata"] = str(output_dirs["media"] / "videos.csv")
        download_assets(videos, output_dirs["videos"], url_key="src", fallback_prefix="video", default_ext="mp4", skip_data_uri=False)
        exports["videos_files"] = str(output_dirs["videos"])

    audios = media.get("audios", [])
    if audios:
        save_csv(audios, output_dirs["media"] / "audios.csv")
        exports["audios_metadata"] = str(output_dirs["media"] / "audios.csv")
        download_assets(audios, output_dirs["audios"], url_key="src", fallback_prefix="audio", default_ext="mp3", skip_data_uri=False)
        exports["audios_files"] = str(output_dirs["audios"])

    documents = media.get("documents", [])
    if documents:
        save_csv(documents, output_dirs["downloads"] / "documents.csv")
        exports["documents_metadata"] = str(output_dirs["downloads"] / "documents.csv")
        download_assets(documents, output_dirs["downloads"], url_key="href", fallback_prefix="document", default_ext="")
        exports["documents_files"] = str(output_dirs["downloads"])

    summary = result["summary"]
    summary_path = output_dirs["root"] / "summary.json"
    save_json(summary, summary_path)
    exports["summary"] = str(summary_path)
    exports["raw_content"] = str(output_dirs["raw"] / "content.json")

    manifest = {
        "url": result["url"],
        "mode": result["mode"],
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "summary": summary,
        "folders": {name: str(path) for name, path in output_dirs.items()},
        "exports": exports,
    }
    save_json(manifest, output_dirs["root"] / "manifest.json")

    print("=" * 60)
    print("RÉSUMÉ")
    print(f"Mode: {result['mode']}")
    print(f"Texte: {summary['text_length']} caractères")
    print(f"Images: {summary['images_count']}")
    print(f"Tables: {summary['tables_count']}")
    print(f"Liens: {summary['links_count']}")
    print(f"Vidéos: {summary.get('videos_count', 0)}")
    print(f"Audios: {summary.get('audios_count', 0)}")
    print(f"Documents: {summary.get('documents_count', 0)}")
    print()
    print(f"Résultats organisés dans: {output_dirs['root']}")
    print("=" * 60)

    return {"result": result, "output": output_dirs}

# ----------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------
if __name__ == "__main__":
    if len(sys.argv) > 1:
        target_url = sys.argv[1]
    else:
        try:
            target_url = input("Entrez l'URL à scraper (ou Entrée pour https://fr.osstem.com/): ").strip()
        except (EOFError, KeyboardInterrupt):
            target_url = ""
    if not target_url:
        target_url = "https://fr.osstem.com/"

    print(f"URL cible: {target_url}")
    job = scrape_universal(target_url, output_dir="results", headless=True)
    if isinstance(job, dict) and "output" in job:
        manifest_path = job["output"]["root"] / "manifest.json"
        print(f"Manifest: {manifest_path}")
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
import re
from datetime import datetime
from typing import Dict, List, Tuple, Set, Optional

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
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".svg", ".webp", ".bmp", ".ico", ".tiff", ".tif"}
VIDEO_EXTENSIONS = {".mp4", ".webm", ".mov", ".mkv", ".m4v", ".avi", ".m3u8", ".ts", ".ogg"}


def slugify(value: str) -> str:
    cleaned = "".join(c if c.isalnum() else "_" for c in value)
    return cleaned.strip("_") or "home"


def is_unresolved_video_url(src: str, base_url: str) -> bool:
    """Detects blob/data/about or empty/root placeholders that are not directly downloadable."""
    if not src:
        return True
    if src.startswith(("blob:", "data:", "about:")):
        return True
    parsed = urlparse(src)
    if parsed.scheme in {"http", "https"}:
        path = parsed.path or ""
        if not path.strip("/"):
            return True
        ext = Path(path).suffix.lower()
        if not ext and not parsed.query:
            return False
        if ext and ext not in VIDEO_EXTENSIONS:
            return False
    return False


def get_best_video_source(sources: List[Dict], base_url: str) -> List[Dict]:
    """Prioritize desktop/higher quality video sources"""
    if not sources:
        return sources
    
    # Sort by priority indicators
    def source_priority(source):
        src = source.get("src", "").lower()
        priority = 0
        
        # Prefer higher resolution indicators
        if any(x in src for x in ["1080", "720", "hd", "high"]):
            priority += 10
        elif any(x in src for x in ["480", "360", "sd", "low"]):
            priority -= 5
            
        # Prefer mp4 over other formats
        if src.endswith(".mp4"):
            priority += 5
        elif src.endswith(".webm"):
            priority += 3
            
        # Avoid mobile indicators
        if any(x in src for x in ["mobile", "mobi", "small", "low"]):
            priority -= 10
            
        # Prefer direct URLs over blob/data
        if not src.startswith(("blob:", "data:")):
            priority += 20
            
        return priority
    
    # Sort sources by priority (highest first)
    sorted_sources = sorted(sources, key=source_priority, reverse=True)
    
    # Return all sources in priority order
    return sorted_sources


def videos_unresolved(videos: List[Dict[str, str]], base_url: str) -> bool:
    return bool(videos) and all(is_unresolved_video_url(v.get("src", ""), base_url) for v in videos)


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
        "scripts": root / "scripts",
        "styles": root / "styles",
        "fonts": root / "fonts",
        "iframes": root / "iframes",
        "forms": root / "forms",
        "metadata": root / "metadata",
        "svg": root / "svg",
        "svg_files": root / "svg" / "files",
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
        if target_url.startswith("blob:") or target_url.startswith("about:blank"):
            item["skip_reason"] = "unsupported_scheme"
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

    # Images - Extraction COMPLÈTE de TOUTES les images
    images = []
    
    # 1. Images dans <img> avec TOUS les attributs lazy-load
    for img in soup.find_all("img"):
        src = (img.get("src") or 
               img.get("data-src") or 
               img.get("data-lazy-src") or 
               img.get("data-original") or 
               img.get("data-url") or
               img.get("data-image") or
               img.get("data-srcset") or
               img.get("data-lazy") or
               img.get("data-lazy-loaded-src") or
               img.get("data-lazy-srcset") or
               img.get("data-retina") or
               img.get("data-normal"))
        
        # Extraire depuis srcset
        if not src:
            srcset = img.get("srcset") or img.get("data-srcset")
            if srcset:
                src = srcset.split(",")[0].strip().split()[0] if srcset else None
        
        if not src or src.startswith("data:") or src.startswith("javascript:"):
            continue
        
        src = urljoin(base_url, src)
        
        # Type d'image
        img_type = "image"
        src_lower = src.lower()
        if any(ext in src_lower for ext in [".jpg", ".jpeg"]):
            img_type = "image/jpeg"
        elif ".png" in src_lower:
            img_type = "image/png"
        elif ".gif" in src_lower:
            img_type = "image/gif"
        elif ".svg" in src_lower:
            img_type = "image/svg+xml"
        elif ".webp" in src_lower:
            img_type = "image/webp"
        elif ".ico" in src_lower:
            img_type = "image/x-icon"
        
        images.append({
            "src": src,
            "alt": img.get("alt", ""),
            "title": img.get("title", ""),
            "width": img.get("width", ""),
            "height": img.get("height", ""),
            "type": img_type,
            "is_image": True,
            "source": "img_tag",
            "loading": img.get("loading", ""),
            "class": " ".join(img.get("class", []))
        })
    
    # 2. Images dans <picture> et <source>
    for picture in soup.find_all("picture"):
        for source in picture.find_all("source"):
            srcset = source.get("srcset") or source.get("data-srcset")
            if srcset:
                urls = [url.strip().split()[0] for url in srcset.split(",") if url.strip()]
                for url in urls:
                    if url and not url.startswith("data:"):
                        url = urljoin(base_url, url)
                        images.append({
                            "src": url,
                            "alt": "",
                            "title": "",
                            "type": source.get("type", "image"),
                            "is_image": True,
                            "source": "picture_source"
                        })
    
    # 3. Images dans backgrounds CSS (style="background-image: url(...)")
    for element in soup.find_all(style=True):
        style = element.get("style", "")
        bg_matches = re.findall(r'background-image\s*:\s*url\(["\']?([^"\'()]+)["\']?\)', style, re.IGNORECASE)
        for bg_url in bg_matches:
            if bg_url and not bg_url.startswith("data:"):
                bg_url = urljoin(base_url, bg_url.strip())
                images.append({
                    "src": bg_url,
                    "alt": element.get("alt", ""),
                    "title": element.get("title", ""),
                    "type": "image",
                    "is_image": True,
                    "source": "css_background",
                    "element_tag": element.name,
                    "element_class": " ".join(element.get("class", []))
                })
    
    # 4. Images dans les attributs data-* avec "image" ou "img" dans le nom
    for element in soup.find_all(attrs=lambda x: x and any(
        k.startswith("data-") and ("image" in k.lower() or "img" in k.lower()) 
        for k in x.keys()
    )):
        for attr, value in element.attrs.items():
            if ("image" in attr.lower() or "img" in attr.lower()) and isinstance(value, str):
                if ("http" in value or value.startswith("/")) and not value.startswith("data:"):
                    img_url = urljoin(base_url, value)
                    images.append({
                        "src": img_url,
                        "alt": element.get("alt", ""),
                        "title": element.get("title", ""),
                        "type": "image",
                        "is_image": True,
                        "source": f"data_attribute_{attr}",
                        "element_tag": element.name
                    })
    
    # 5. Images dans les liens avec extensions d'images
    for link in soup.find_all("a", href=True):
        href = link.get("href", "")
        if href:
            parsed = urlparse(href)
            ext = Path(parsed.path).suffix.lower()
            if ext in IMAGE_EXTENSIONS:
                img_url = urljoin(base_url, href)
                images.append({
                    "src": img_url,
                    "alt": link.get_text(strip=True),
                    "title": link.get("title", ""),
                    "type": "image",
                    "is_image": True,
                    "source": "link_image"
                })
    
    # Deduplicate
    seen_img = set()
    unique_images = []
    for img in images:
        if img["src"] not in seen_img:
            seen_img.add(img["src"])
            unique_images.append(img)
    
    print(f"[IMAGES] {len(unique_images)} images uniques trouvées")

    # Tables - Extraction COMPLÈTE avec images et HTML
    tables = []
    for idx, table in enumerate(soup.find_all("table"), 1):
        headers = []
        # Chercher dans thead puis première tr
        header_row = None
        thead = table.find("thead")
        if thead:
            header_row = thead.find("tr")
        if not header_row:
            first_tr = table.find("tr")
            if first_tr and first_tr.find_all(["th"]):
                header_row = first_tr
        
        if header_row:
            for th in header_row.find_all(["th", "td"]):
                header_text = th.get_text(strip=True)
                header_imgs = []
                for img in th.find_all("img"):
                    src = (img.get("src") or img.get("data-src") or 
                           img.get("data-lazy-src") or img.get("data-original"))
                    if src:
                        src = urljoin(base_url, src)
                        header_imgs.append({
                            "src": src,
                            "alt": img.get("alt", ""),
                            "title": img.get("title", "")
                        })
                headers.append({
                    "text": header_text,
                    "images": header_imgs,
                    "html": "".join(str(c) for c in th.children) or str(th)
                })

        rows = []
        tbodies = table.find_all("tbody") or [table]
        for tbody in tbodies:
            for tr in tbody.find_all("tr"):
                if tr == header_row:
                    continue
                
                cells_data = []
                for td in tr.find_all(["td", "th"]):
                    cell_text = td.get_text(separator="\n", strip=True)
                    cell_images = []
                    for img in td.find_all("img"):
                        src = (img.get("src") or img.get("data-src") or 
                               img.get("data-lazy-src") or img.get("data-original"))
                        if src:
                            src = urljoin(base_url, src)
                            cell_images.append({
                                "src": src,
                                "alt": img.get("alt", ""),
                                "title": img.get("title", ""),
                                "width": img.get("width", ""),
                                "height": img.get("height", "")
                            })
                    
                    cell_html = "".join(str(c) for c in td.children) or str(td)
                    cells_data.append({
                        "text": cell_text,
                        "images": cell_images,
                        "html": cell_html
                    })
                
                if not cells_data:
                    continue
                
                # Créer le dictionnaire de ligne
                if headers and len(headers) > 0:
                    row_dict = {}
                    for i, header in enumerate(headers):
                        header_key = header.get("text", "") if isinstance(header, dict) else str(header)
                        if i < len(cells_data):
                            row_dict[header_key or f"col_{i}"] = cells_data[i]
                        else:
                            row_dict[header_key or f"col_{i}"] = {"text": "", "images": [], "html": ""}
                    if len(cells_data) > len(headers):
                        for i in range(len(headers), len(cells_data)):
                            row_dict[f"col_{i}"] = cells_data[i]
                else:
                    row_dict = {f"col_{i}": cell for i, cell in enumerate(cells_data)}
                rows.append(row_dict)

        if rows or headers:
            tables.append({
                "table_index": idx,
                "headers": headers,
                "rows": rows,
                "row_count": len(rows)
            })
            print(f"[TABLE] Table {idx}: {len(headers)} en-têtes, {len(rows)} lignes")

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
    
    # Scripts
    scripts = []
    for script in soup.find_all("script"):
        src = script.get("src")
        script_content = script.string or ""
        scripts.append({
            "src": urljoin(base_url, src) if src else "",
            "type": script.get("type", ""),
            "async": script.get("async", False),
            "defer": script.get("defer", False),
            "content_length": len(script_content),
            "has_content": bool(script_content)
        })
    
    # Styles (CSS)
    styles = []
    for style in soup.find_all("style"):
        styles.append({
            "type": style.get("type", "text/css"),
            "content_length": len(style.string or ""),
            "content": (style.string or "")[:1000]  # Preview
        })
    
    # Links vers CSS
    css_links = []
    for link in soup.find_all("link", rel="stylesheet"):
        href = link.get("href")
        if href:
            css_links.append({
                "href": urljoin(base_url, href),
                "type": link.get("type", "text/css"),
                "media": link.get("media", "")
            })
    
    # Iframes
    iframes = []
    for iframe in soup.find_all("iframe"):
        src = iframe.get("src")
        if src:
            iframes.append({
                "src": urljoin(base_url, src),
                "title": iframe.get("title", ""),
                "width": iframe.get("width", ""),
                "height": iframe.get("height", ""),
                "sandbox": iframe.get("sandbox", "")
            })
    
    # Formulaires
    forms = []
    for form in soup.find_all("form"):
        form_data = {
            "action": urljoin(base_url, form.get("action", "")),
            "method": form.get("method", "get"),
            "enctype": form.get("enctype", ""),
            "fields": []
        }
        for input_elem in form.find_all(["input", "textarea", "select"]):
            form_data["fields"].append({
                "type": input_elem.get("type", input_elem.name),
                "name": input_elem.get("name", ""),
                "id": input_elem.get("id", ""),
                "placeholder": input_elem.get("placeholder", ""),
                "required": input_elem.has_attr("required")
            })
        forms.append(form_data)
    
    # Métadonnées
    metadata = {
        "title": soup.title.string.strip() if soup.title and soup.title.string else "",
        "meta_tags": {},
        "og_tags": {},
        "twitter_tags": {},
        "schema_org": []
    }
    
    # Meta tags standards
    for meta in soup.find_all("meta"):
        name = meta.get("name") or meta.get("property") or meta.get("http-equiv")
        content = meta.get("content", "")
        if name:
            metadata["meta_tags"][name] = content
            if name.startswith("og:"):
                metadata["og_tags"][name] = content
            elif name.startswith("twitter:"):
                metadata["twitter_tags"][name] = content
    
    # Schema.org JSON-LD
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            schema_data = json.loads(script.string or "{}")
            metadata["schema_org"].append(schema_data)
        except:
            pass
    
    # Fonts
    fonts = []
    for link in soup.find_all("link", rel=lambda x: x and "font" in str(x).lower()):
        href = link.get("href")
        if href:
            fonts.append({
                "href": urljoin(base_url, href),
                "type": link.get("type", ""),
                "family": link.get("data-font-family", "")
            })
    
    # Icons
    icons = []
    for link in soup.find_all("link", rel=lambda x: x and ("icon" in str(x).lower() or "apple" in str(x).lower())):
        href = link.get("href")
        if href:
            icons.append({
                "href": urljoin(base_url, href),
                "type": link.get("type", ""),
                "sizes": link.get("sizes", ""),
                "rel": link.get("rel", [])
            })
    
    # SVG - Extraction complète
    svg_inline = []
    svg_files = []
    
    # 1. SVG inline dans le HTML (<svg> tags)
    for svg in soup.find_all("svg"):
        svg_content = str(svg)
        svg_id = svg.get("id", f"svg_{len(svg_inline) + 1}")
        svg_class = " ".join(svg.get("class", []))
        svg_viewbox = svg.get("viewBox", "")
        svg_width = svg.get("width", "")
        svg_height = svg.get("height", "")
        
        svg_inline.append({
            "id": svg_id,
            "class": svg_class,
            "viewBox": svg_viewbox,
            "width": svg_width,
            "height": svg_height,
            "content": svg_content,
            "content_length": len(svg_content),
            "source": "inline_svg"
        })
    
    # 2. Fichiers SVG externes (déjà dans images, mais on les sépare)
    for img in unique_images:
        if img.get("type") == "image/svg+xml" or img["src"].lower().endswith(".svg"):
            svg_files.append({
                "src": img["src"],
                "alt": img.get("alt", ""),
                "title": img.get("title", ""),
                "source": "external_file"
            })
    
    # 3. SVG dans les liens directs
    for link in soup.find_all("a", href=True):
        href = link.get("href", "")
        if href.lower().endswith(".svg"):
            svg_url = urljoin(base_url, href)
            if svg_url not in [s["src"] for s in svg_files]:
                svg_files.append({
                    "src": svg_url,
                    "alt": link.get_text(strip=True),
                    "title": link.get("title", ""),
                    "source": "link_svg"
                })
    
    # 4. SVG dans les backgrounds CSS (déjà détectés dans images, mais on les marque)
    for img in unique_images:
        if img.get("source") == "css_background" and (img["src"].lower().endswith(".svg") or "svg" in img.get("type", "").lower()):
            if img["src"] not in [s["src"] for s in svg_files]:
                svg_files.append({
                    "src": img["src"],
                    "alt": img.get("alt", ""),
                    "title": img.get("title", ""),
                    "source": "css_background_svg"
                })

    summary = {
        "text_length": text_data["text_length"],
        "images_count": len(unique_images),
        "tables_count": len(tables),
        "links_count": len(unique_links),
        "videos_count": len(videos),
        "audios_count": len(audios),
        "documents_count": len(documents),
        "scripts_count": len(scripts),
        "styles_count": len(styles),
        "css_files_count": len(css_links),
        "iframes_count": len(iframes),
        "forms_count": len(forms),
        "fonts_count": len(fonts),
        "icons_count": len(icons),
        "svg_inline_count": len(svg_inline),
        "svg_files_count": len(svg_files),
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
        "scripts": scripts,
        "styles": styles,
        "css_links": css_links,
        "iframes": iframes,
        "forms": forms,
        "metadata": metadata,
        "fonts": fonts,
        "icons": icons,
        "svg": {
            "inline": svg_inline,
            "files": svg_files
        },
        "summary": summary,
        "html_preview": resp.text[:50000],
        "html_full": resp.text  # HTML complet
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
        # Force desktop viewport and disable mobile optimizations
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--force-device-scale-factor=1")
        chrome_options.add_argument("--disable-mobile-viewport")
        chrome_options.add_argument("--disable-touch-events")
        chrome_options.add_argument("--disable-smooth-scrolling")
        # Enable performance logging to capture network requests
        try:
            chrome_options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
        except Exception:
            pass

        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    def load_page(self, url, wait_time=10):
        full_url = urljoin(self.base_url, url)
        print(f"[SELENIUM] Chargement: {full_url}")
        self.driver.get(full_url)
        WebDriverWait(self.driver, wait_time).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        time.sleep(self.delay)
        
        # Wait for page load and force desktop rendering
        try:
            # Set desktop viewport before content loads
            self.driver.execute_script("""
                Object.defineProperty(navigator, 'userAgent', {
                    get: function() { return 'arguments[0]'; }
                });
                // Force desktop viewport
                var meta = document.querySelector('meta[name="viewport"]');
                if (meta) meta.remove();
                // Set desktop screen size
                Object.defineProperty(screen, 'width', {get: function(){ return 1920; }});
                Object.defineProperty(screen, 'height', {get: function(){ return 1080; }});
                Object.defineProperty(window, 'innerWidth', {get: function(){ return 1920; }});
                Object.defineProperty(window, 'innerHeight', {get: function(){ return 1080; }});
            """, USER_AGENT)
        except Exception:
            pass
        
        # Scroll for lazy loading with desktop behavior
        try:
            # Scroll for desktop-style lazy loading
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(1)
            
            # Attendre que les images se chargent
            WebDriverWait(self.driver, 10).until(
                lambda driver: driver.execute_script("""
                    var images = document.querySelectorAll('img');
                    if (images.length === 0) return true;
                    var loaded = 0;
                    for (var i = 0; i < images.length; i++) {
                        if (images[i].complete && images[i].naturalHeight !== 0) {
                            loaded++;
                        }
                    }
                    return loaded >= images.length * 0.7;
                """)
            )
        except:
            pass
        
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

        # Images - Extraction COMPLÈTE avec Selenium
        images = []
        
        # 1. Images dans <img>
        for img in self.driver.find_elements(By.TAG_NAME, "img"):
            src = (img.get_attribute("src") or 
                   img.get_attribute("data-src") or 
                   img.get_attribute("data-lazy-src") or 
                   img.get_attribute("data-original") or
                   img.get_attribute("data-url") or
                   img.get_attribute("data-image"))
            
            if not src:
                srcset = img.get_attribute("srcset") or img.get_attribute("data-srcset")
                if srcset:
                    src = srcset.split(",")[0].strip().split()[0] if srcset else None
            
            if src and not src.startswith("data:") and not src.startswith("javascript:"):
                src = urljoin(self.base_url, src)
                
                # Type d'image
                img_type = "image"
                src_lower = src.lower()
                if any(ext in src_lower for ext in [".jpg", ".jpeg"]):
                    img_type = "image/jpeg"
                elif ".png" in src_lower:
                    img_type = "image/png"
                elif ".gif" in src_lower:
                    img_type = "image/gif"
                elif ".svg" in src_lower:
                    img_type = "image/svg+xml"
                elif ".webp" in src_lower:
                    img_type = "image/webp"
                
                images.append({
                    "src": src,
                    "alt": img.get_attribute("alt") or "",
                    "title": img.get_attribute("title") or "",
                    "width": img.get_attribute("width") or "",
                    "height": img.get_attribute("height") or "",
                    "type": img_type,
                    "is_image": True,
                    "source": "img_tag"
                })
        
        # 2. Images dans backgrounds CSS via JavaScript
        try:
            bg_images = self.driver.execute_script("""
                var images = [];
                var elements = document.querySelectorAll('[style*="background-image"], [class*="bg-"]');
                for (var i = 0; i < elements.length; i++) {
                    var style = window.getComputedStyle(elements[i]);
                    var bgImage = style.backgroundImage;
                    if (bgImage && bgImage !== 'none') {
                        var urlMatch = bgImage.match(/url\\(["']?([^"']+)["']?\\)/);
                        if (urlMatch && urlMatch[1]) {
                            images.push(urlMatch[1]);
                        }
                    }
                }
                return images;
            """)
            for bg_url in bg_images:
                if bg_url and not bg_url.startswith("data:"):
                    bg_url = urljoin(self.base_url, bg_url)
                    images.append({
                        "src": bg_url,
                        "alt": "",
                        "title": "",
                        "type": "image",
                        "is_image": True,
                        "source": "css_background"
                    })
        except:
            pass
        
        # Deduplicate
        seen_img = set()
        unique_images = []
        for img in images:
            if img["src"] not in seen_img:
                seen_img.add(img["src"])
                unique_images.append(img)
        
        print(f"[IMAGES] {len(unique_images)} images uniques trouvées (Selenium)")

        # Tables - Extraction COMPLÈTE avec images
        tables = []
        table_elements = self.driver.find_elements(By.TAG_NAME, "table")
        for idx, table in enumerate(table_elements, 1):
            headers = []
            try:
                header_row = table.find_element(By.TAG_NAME, "thead")
                if header_row:
                    header_elements = header_row.find_elements(By.TAG_NAME, "th")
                    for th in header_elements:
                        header_text = th.text.strip()
                        header_imgs = []
                        try:
                            imgs = th.find_elements(By.TAG_NAME, "img")
                            for img in imgs:
                                src = (img.get_attribute("src") or 
                                       img.get_attribute("data-src") or 
                                       img.get_attribute("data-lazy-src"))
                                if src:
                                    src = urljoin(self.base_url, src)
                                    header_imgs.append({
                                        "src": src,
                                        "alt": img.get_attribute("alt") or "",
                                        "title": img.get_attribute("title") or ""
                                    })
                        except:
                            pass
                        headers.append({
                            "text": header_text,
                            "images": header_imgs,
                            "html": th.get_attribute("outerHTML") or ""
                        })
            except:
                pass

            rows = []
            try:
                tbody = table.find_elements(By.TAG_NAME, "tbody")
                tbodies = tbody if tbody else [table]
                for tb in tbodies:
                    tr_elements = tb.find_elements(By.TAG_NAME, "tr")
                    for tr in tr_elements:
                        cell_elements = tr.find_elements(By.TAG_NAME, "td")
                        cells_data = []
                        for td in cell_elements:
                            cell_text = td.text.strip()
                            cell_imgs = []
                            try:
                                imgs = td.find_elements(By.TAG_NAME, "img")
                                for img in imgs:
                                    src = (img.get_attribute("src") or 
                                           img.get_attribute("data-src") or 
                                           img.get_attribute("data-lazy-src"))
                                    if src:
                                        src = urljoin(self.base_url, src)
                                        cell_imgs.append({
                                            "src": src,
                                            "alt": img.get_attribute("alt") or "",
                                            "title": img.get_attribute("title") or "",
                                            "width": img.get_attribute("width") or "",
                                            "height": img.get_attribute("height") or ""
                                        })
                            except:
                                pass
                            cells_data.append({
                                "text": cell_text,
                                "images": cell_imgs,
                                "html": td.get_attribute("outerHTML") or ""
                            })
                        
                        if not cells_data:
                            continue
                        
                        if headers and len(headers) > 0:
                            row_dict = {}
                            for i, header in enumerate(headers):
                                header_key = header.get("text", "") if isinstance(header, dict) else str(header)
                                if i < len(cells_data):
                                    row_dict[header_key or f"col_{i}"] = cells_data[i]
                                else:
                                    row_dict[header_key or f"col_{i}"] = {"text": "", "images": [], "html": ""}
                            if len(cells_data) > len(headers):
                                for i in range(len(headers), len(cells_data)):
                                    row_dict[f"col_{i}"] = cells_data[i]
                        else:
                            row_dict = {f"col_{i}": cell for i, cell in enumerate(cells_data)}
                        rows.append(row_dict)
            except:
                pass

            if rows or headers:
                tables.append({
                    "table_index": idx,
                    "headers": headers,
                    "rows": rows,
                    "row_count": len(rows)
                })
                print(f"[TABLE] Table {idx}: {len(headers)} en-têtes, {len(rows)} lignes")

        # Media
        videos = []
        seen_video_src = set()
        video_elements = self.driver.find_elements(By.TAG_NAME, "video")
        for video in video_elements:
            candidates = [video.get_attribute("src")]
            candidates.extend(
                source.get_attribute("src") for source in video.find_elements(By.TAG_NAME, "source")
            )
            # Try currentSrc resolved by the browser
            try:
                current_src = self.driver.execute_script("return arguments[0].currentSrc || '';", video)
                if current_src:
                    candidates.append(current_src)
            except Exception:
                pass
            for src in candidates:
                if src:
                    src = urljoin(self.base_url, src)
                    if is_unresolved_video_url(src, self.base_url):
                        continue
                    if src in seen_video_src:
                        continue
                    seen_video_src.add(src)
                    videos.append({
                        "src": src,
                        "type": video.get_attribute("type") or "",
                        "width": video.get_attribute("width") or "",
                        "height": video.get_attribute("height") or "",
                        "attributes": {"source": "dom", "quality": "auto"},
                    })

        # Augment videos with network-captured media URLs
        try:
            perf_logs = self.driver.get_log('performance')
            for entry in perf_logs:
                try:
                    msg = json.loads(entry.get('message'))
                    inner = msg.get('message', {})
                    method = inner.get('method')
                    params = inner.get('params', {})
                    if method == 'Network.responseReceived':
                        response = params.get('response', {})
                        url = response.get('url')
                        mime = response.get('mimeType', '')
                        if not url:
                            continue
                        if url.startswith('data:') or url.startswith('blob:'):
                            continue
                        url_lower = url.lower()
                        ext = Path(urlparse(url).path).suffix.lower()
                        is_video_mime = mime.startswith('video/') or 'mpegurl' in mime or 'application/vnd.apple.mpegurl' in mime
                        is_video_ext = (ext in VIDEO_EXTENSIONS) or ('.m3u8' in url_lower) or ('.mp4' in url_lower) or ('.webm' in url_lower)
                        if is_video_mime or is_video_ext:
                            abs_url = urljoin(self.base_url, url)
                            if abs_url in seen_video_src:
                                continue
                            seen_video_src.add(abs_url)
                            videos.append({
                                "src": abs_url,
                                "type": mime or "",
                                "width": "",
                                "height": "",
                                "attributes": {"source": "network", "quality": "auto"},
                            })
                except Exception:
                    continue
        except Exception:
            pass

        # Apply video quality prioritization
        videos = get_best_video_source(videos, self.base_url)
        print(f"[VIDEOS] {len(videos)} prioritized video sources found")

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
        
        # Scripts
        scripts = []
        try:
            script_elements = self.driver.find_elements(By.TAG_NAME, "script")
            for script in script_elements:
                src = script.get_attribute("src")
                scripts.append({
                    "src": urljoin(self.base_url, src) if src else "",
                    "type": script.get_attribute("type") or "",
                    "async": script.get_attribute("async") or False,
                    "defer": script.get_attribute("defer") or False
                })
        except:
            pass
        
        # Styles
        styles = []
        css_links = []
        try:
            style_elements = self.driver.find_elements(By.TAG_NAME, "style")
            for style in style_elements:
                styles.append({
                    "type": style.get_attribute("type") or "text/css",
                    "content_length": len(style.get_attribute("innerHTML") or "")
                })
            
            link_elements = self.driver.find_elements(By.CSS_SELECTOR, "link[rel='stylesheet']")
            for link in link_elements:
                href = link.get_attribute("href")
                if href:
                    css_links.append({
                        "href": urljoin(self.base_url, href),
                        "type": link.get_attribute("type") or "text/css"
                    })
        except:
            pass
        
        # Iframes
        iframes = []
        try:
            iframe_elements = self.driver.find_elements(By.TAG_NAME, "iframe")
            for iframe in iframe_elements:
                src = iframe.get_attribute("src")
                if src:
                    iframes.append({
                        "src": urljoin(self.base_url, src),
                        "title": iframe.get_attribute("title") or "",
                        "width": iframe.get_attribute("width") or "",
                        "height": iframe.get_attribute("height") or ""
                    })
        except:
            pass
        
        # Formulaires
        forms = []
        try:
            form_elements = self.driver.find_elements(By.TAG_NAME, "form")
            for form in form_elements:
                form_data = {
                    "action": urljoin(self.base_url, form.get_attribute("action") or ""),
                    "method": form.get_attribute("method") or "get",
                    "fields_count": len(form.find_elements(By.CSS_SELECTOR, "input, textarea, select"))
                }
                forms.append(form_data)
        except:
            pass
        
        # Métadonnées
        metadata = {
            "title": self.driver.title,
            "meta_tags": {},
            "og_tags": {},
            "twitter_tags": {}
        }
        try:
            meta_elements = self.driver.find_elements(By.TAG_NAME, "meta")
            for meta in meta_elements:
                name = meta.get_attribute("name") or meta.get_attribute("property") or meta.get_attribute("http-equiv")
                content = meta.get_attribute("content") or ""
                if name:
                    metadata["meta_tags"][name] = content
                    if name.startswith("og:"):
                        metadata["og_tags"][name] = content
                    elif name.startswith("twitter:"):
                        metadata["twitter_tags"][name] = content
        except:
            pass
        
        # SVG - Extraction avec Selenium
        svg_inline = []
        svg_files = []
        
        # 1. SVG inline
        try:
            svg_elements = self.driver.find_elements(By.TAG_NAME, "svg")
            for svg in svg_elements:
                svg_content = svg.get_attribute("outerHTML") or ""
                svg_id = svg.get_attribute("id") or f"svg_{len(svg_inline) + 1}"
                svg_class = svg.get_attribute("class") or ""
                svg_viewbox = svg.get_attribute("viewBox") or ""
                svg_width = svg.get_attribute("width") or ""
                svg_height = svg.get_attribute("height") or ""
                
                svg_inline.append({
                    "id": svg_id,
                    "class": svg_class,
                    "viewBox": svg_viewbox,
                    "width": svg_width,
                    "height": svg_height,
                    "content": svg_content,
                    "content_length": len(svg_content),
                    "source": "inline_svg"
                })
        except:
            pass
        
        # 2. Fichiers SVG externes
        for img in unique_images:
            if img.get("type") == "image/svg+xml" or img["src"].lower().endswith(".svg"):
                svg_files.append({
                    "src": img["src"],
                    "alt": img.get("alt", ""),
                    "title": img.get("title", ""),
                    "source": "external_file"
                })
        
        # 3. SVG dans les liens
        try:
            link_elements = self.driver.find_elements(By.TAG_NAME, "a")
            for link in link_elements:
                href = link.get_attribute("href")
                if href and href.lower().endswith(".svg"):
                    svg_url = urljoin(self.base_url, href)
                    if svg_url not in [s["src"] for s in svg_files]:
                        svg_files.append({
                            "src": svg_url,
                            "alt": link.text.strip(),
                            "title": link.get_attribute("title") or "",
                            "source": "link_svg"
                        })
        except:
            pass

        summary = {
            "text_length": text_data["text_length"],
            "images_count": len(unique_images),
            "tables_count": len(tables),
            "links_count": len(unique_links),
            "videos_count": len(videos),
            "audios_count": len(audios),
            "documents_count": len(documents),
            "scripts_count": len(scripts),
            "styles_count": len(styles),
            "css_files_count": len(css_links),
            "iframes_count": len(iframes),
            "forms_count": len(forms),
            "svg_inline_count": len(svg_inline),
            "svg_files_count": len(svg_files),
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
            "scripts": scripts,
            "styles": styles,
            "css_links": css_links,
            "iframes": iframes,
            "forms": forms,
            "metadata": metadata,
            "svg": {
                "inline": svg_inline,
                "files": svg_files
            },
            "summary": summary,
            "html_full": self.driver.page_source  # HTML complet
        }

    def close(self):
        self.driver.quit()

# ----------------------------------------------------------------------
# Export des tables en HTML
# ----------------------------------------------------------------------
def export_table_html(table: Dict, filepath: Path):
    """Exporte une table en format HTML avec images"""
    headers = table.get("headers", [])
    rows = table.get("rows", [])
    
    html = ["<!DOCTYPE html>", "<html>", "<head>", "<meta charset='utf-8'>", 
            "<title>Table {}</title>".format(table.get("table_index", "")),
            "<style>",
            "table { border-collapse: collapse; width: 100%; margin: 20px 0; }",
            "th, td { border: 1px solid #ddd; padding: 12px; text-align: left; vertical-align: top; }",
            "th { background-color: #4CAF50; color: white; font-weight: bold; }",
            "tr:nth-child(even) { background-color: #f2f2f2; }",
            "tr:hover { background-color: #f5f5f5; }",
            "td img { max-width: 300px; height: auto; margin: 5px 0; display: block; }",
            "td ul { margin: 5px 0; padding-left: 20px; }",
            "</style>", "</head>", "<body>", "<table>"]
    
    # En-tête
    if headers:
        html.append("<thead><tr>")
        for header in headers:
            if isinstance(header, dict):
                header_content = header.get("text", "")
                for img in header.get("images", []):
                    header_content += f'<br><img src="{img["src"]}" alt="{img.get("alt", "")}" title="{img.get("title", "")}">'
                html.append(f"<th>{header_content}</th>")
            else:
                html.append(f"<th>{header}</th>")
        html.append("</tr></thead>")
    
    # Corps
    html.append("<tbody>")
    for row in rows:
        html.append("<tr>")
        if headers:
            for header in headers:
                header_key = header.get("text", "") if isinstance(header, dict) else str(header)
                cell_data = row.get(header_key, {})
                
                if isinstance(cell_data, dict):
                    cell_content = cell_data.get("text", "")
                    for img in cell_data.get("images", []):
                        cell_content += f'<br><img src="{img["src"]}" alt="{img.get("alt", "")}" title="{img.get("title", "")}">'
                    if not cell_content and cell_data.get("html"):
                        cell_html = cell_data["html"]
                        if cell_html.strip().startswith("<td") or cell_html.strip().startswith("<th"):
                            try:
                                soup_cell = BeautifulSoup(cell_html, "html.parser")
                                td_tag = soup_cell.find("td") or soup_cell.find("th")
                                if td_tag:
                                    cell_content = "".join(str(child) for child in td_tag.children)
                                else:
                                    cell_content = cell_html
                            except:
                                cell_content = re.sub(r'^<t[dh][^>]*>', '', cell_html)
                                cell_content = re.sub(r'</t[dh]>$', '', cell_content)
                        else:
                            cell_content = cell_html
                    html.append(f"<td>{cell_content}</td>")
                else:
                    html.append(f"<td>{cell_data}</td>")
        else:
            for cell_data in row.values():
                if isinstance(cell_data, dict):
                    cell_content = cell_data.get("text", "")
                    for img in cell_data.get("images", []):
                        cell_content += f'<br><img src="{img["src"]}" alt="{img.get("alt", "")}" title="{img.get("title", "")}">'
                    if not cell_content and cell_data.get("html"):
                        cell_html = cell_data["html"]
                        if cell_html.strip().startswith("<td") or cell_html.strip().startswith("<th"):
                            try:
                                soup_cell = BeautifulSoup(cell_html, "html.parser")
                                td_tag = soup_cell.find("td") or soup_cell.find("th")
                                if td_tag:
                                    cell_content = "".join(str(child) for child in td_tag.children)
                                else:
                                    cell_content = cell_html
                            except:
                                cell_content = re.sub(r'^<t[dh][^>]*>', '', cell_html)
                                cell_content = re.sub(r'</t[dh]>$', '', cell_content)
                        else:
                            cell_content = cell_html
                    html.append(f"<td>{cell_content}</td>")
                else:
                    html.append(f"<td>{cell_data}</td>")
        html.append("</tr>")
    html.append("</tbody>")
    
    html.extend(["</table>", "</body>", "</html>"])
    write_text("\n".join(html), filepath)

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

    def run_selenium():
        driver = SeleniumScraper(base_url, headless=headless)
        try:
            return driver.extract_all(path)
        finally:
            driver.close()

    try:
        static_data = scrape_static(base_url, path, session=session)
        unresolved_static_videos = videos_unresolved(static_data.get("media", {}).get("videos", []), base_url)

        if static_data["summary"]["text_length"] > 800 or static_data["summary"]["links_count"] > 10:
            if unresolved_static_videos and SELENIUM_AVAILABLE:
                print("[UNIVERSAL] Vidéos non résolues en statique, tentative Selenium.")
                result = run_selenium()
            else:
                print("[UNIVERSAL] Contenu riche détecté en mode statique, pas de Selenium nécessaire.")
                result = static_data
        else:
            if not SELENIUM_AVAILABLE:
                print("[UNIVERSAL] Selenium indisponible, conservation des données statiques.")
                result = static_data
            else:
                print("[UNIVERSAL] Contenu léger détecté, tentative avec Selenium pour contenu dynamique.")
                result = run_selenium()
    except Exception:
        if not SELENIUM_AVAILABLE:
            raise
        print("[UNIVERSAL] Échec du mode statique, bascule vers Selenium.")
        result = run_selenium()

    result.setdefault("media", {"videos": [], "audios": [], "documents": []})
    for key in ("videos", "audios", "documents"):
        result["media"].setdefault(key, [])
    
    # Initialiser exports
    exports = {}
    
    # Sauvegarder le HTML complet
    if "html_full" in result:
        write_text(result["html_full"], output_dirs["raw"] / "page.html")
        exports["html_full"] = str(output_dirs["raw"] / "page.html")
    
    save_json(result, output_dirs["raw"] / "content.json")

    text_data = result.get("text", {})
    all_text = text_data.get("all_text", "")

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
            table_idx = table['table_index']
            
            # CSV - Flatten les données
            csv_rows = []
            headers = table.get("headers", [])
            for row in table.get("rows", []):
                csv_row = {}
                if headers:
                    for header in headers:
                        header_key = header.get("text", "") if isinstance(header, dict) else str(header)
                        cell_data = row.get(header_key, {})
                        if isinstance(cell_data, dict):
                            csv_row[header_key] = cell_data.get("text", "")
                            if cell_data.get("images"):
                                img_urls = ", ".join([img.get("src", "") for img in cell_data["images"]])
                                csv_row[f"{header_key}_images"] = img_urls
                        else:
                            csv_row[header_key] = str(cell_data)
                else:
                    for key, cell_data in row.items():
                        if isinstance(cell_data, dict):
                            csv_row[key] = cell_data.get("text", "")
                            if cell_data.get("images"):
                                img_urls = ", ".join([img.get("src", "") for img in cell_data["images"]])
                                csv_row[f"{key}_images"] = img_urls
                        else:
                            csv_row[key] = str(cell_data)
                csv_rows.append(csv_row)
            
            filename_csv = output_dirs["tables"] / f"table_{table_idx}.csv"
            if csv_rows:
                save_csv(csv_rows, filename_csv)
                exports[f"table_{table_idx}_csv"] = str(filename_csv)
            
            # HTML avec images
            filename_html = output_dirs["tables"] / f"table_{table_idx}.html"
            export_table_html(table, filename_html)
            exports[f"table_{table_idx}_html"] = str(filename_html)
        
        save_json(result["tables"], output_dirs["tables"] / "tables.json")
        exports["tables_json"] = str(output_dirs["tables"] / "tables.json")
        summary_tables = []
        for table in result["tables"]:
            headers = table.get("headers", [])
            header_texts = []
            for h in headers:
                if isinstance(h, dict):
                    header_texts.append(h.get("text", ""))
                else:
                    header_texts.append(str(h))
            summary_tables.append({
                "table_index": table["table_index"],
                "row_count": table["row_count"],
                "headers": ", ".join(header_texts),
            })
        if summary_tables:
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
    
    # Scripts
    if result.get("scripts"):
        save_json(result["scripts"], output_dirs["scripts"] / "scripts.json")
        save_csv(result["scripts"], output_dirs["scripts"] / "scripts.csv")
        exports["scripts"] = str(output_dirs["scripts"] / "scripts.json")
    
    # Styles
    if result.get("styles"):
        save_json(result["styles"], output_dirs["styles"] / "styles.json")
        exports["styles"] = str(output_dirs["styles"] / "styles.json")
    
    if result.get("css_links"):
        save_csv(result["css_links"], output_dirs["styles"] / "css_links.csv")
        exports["css_links"] = str(output_dirs["styles"] / "css_links.csv")
    
    # Iframes
    if result.get("iframes"):
        save_csv(result["iframes"], output_dirs["iframes"] / "iframes.csv")
        exports["iframes"] = str(output_dirs["iframes"] / "iframes.csv")
    
    # Formulaires
    if result.get("forms"):
        save_json(result["forms"], output_dirs["forms"] / "forms.json")
        save_csv(result["forms"], output_dirs["forms"] / "forms.csv")
        exports["forms"] = str(output_dirs["forms"] / "forms.json")
    
    # Métadonnées
    if result.get("metadata"):
        save_json(result["metadata"], output_dirs["metadata"] / "metadata.json")
        exports["metadata"] = str(output_dirs["metadata"] / "metadata.json")
    
    # Fonts
    if result.get("fonts"):
        save_csv(result["fonts"], output_dirs["fonts"] / "fonts.csv")
        exports["fonts"] = str(output_dirs["fonts"] / "fonts.csv")
    
    # Icons
    if result.get("icons"):
        save_csv(result["icons"], output_dirs["fonts"] / "icons.csv")
        exports["icons"] = str(output_dirs["fonts"] / "icons.csv")
    
    # SVG
    if result.get("svg"):
        svg_data = result["svg"]
        
        # SVG inline - Sauvegarder chaque SVG dans un fichier séparé
        if svg_data.get("inline"):
            svg_inline = svg_data["inline"]
            for idx, svg in enumerate(svg_inline, 1):
                svg_id = svg.get("id", f"svg_{idx}")
                # Nettoyer l'ID pour le nom de fichier
                safe_id = "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in svg_id)
                filename = output_dirs["svg"] / f"{safe_id}.svg"
                write_text(svg.get("content", ""), filename)
            
            # Métadonnées des SVG inline
            save_json(svg_inline, output_dirs["svg"] / "svg_inline.json")
            save_csv(svg_inline, output_dirs["svg"] / "svg_inline.csv")
            exports["svg_inline"] = str(output_dirs["svg"] / "svg_inline.json")
        
        # SVG fichiers externes
        if svg_data.get("files"):
            svg_files = svg_data["files"]
            save_csv(svg_files, output_dirs["svg"] / "svg_files.csv")
            exports["svg_files_metadata"] = str(output_dirs["svg"] / "svg_files.csv")
            
            # Télécharger les fichiers SVG externes
            download_assets(svg_files, output_dirs["svg_files"], url_key="src", fallback_prefix="svg", default_ext="svg", skip_data_uri=True)
            exports["svg_files_downloaded"] = str(output_dirs["svg_files"])

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
    print(f"Scripts: {summary.get('scripts_count', 0)}")
    print(f"Styles CSS: {summary.get('styles_count', 0)}")
    print(f"Fichiers CSS: {summary.get('css_files_count', 0)}")
    print(f"Iframes: {summary.get('iframes_count', 0)}")
    print(f"Formulaires: {summary.get('forms_count', 0)}")
    print(f"SVG inline: {summary.get('svg_inline_count', 0)}")
    print(f"SVG fichiers: {summary.get('svg_files_count', 0)}")
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
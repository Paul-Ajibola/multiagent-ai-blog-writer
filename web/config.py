from __future__ import annotations


from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent    # project root

TEMPLATE_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"
IMAGES_DIR = BASE_DIR / "images"
OUTPUTS_DIR = BASE_DIR / "outputs"


for directory in (TEMPLATES_DIR, STATIC_DIR, IMAGES_DIR, OUTPUTS_DIR):
    directorymkdir(parents=True, exist_ok=True)


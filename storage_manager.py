# -*- coding: utf-8 -*-
"""
Central de Resolução de Caminhos e Gerenciamento de Armazenamento por Livro.
Organiza todas as saídas na hierarquia oficial:
output/<slug-do-devocional>--<book-id>/<idioma>/<run-id>/
com subpastas dedicadas (content, metadata, assets, paperback, hardcover, ebook, reports, previews, logs, tmp).
Garante isolamento entre execuções, prevenção contra path traversal e suporte a retomada de runs.
"""

import os
import re
import json
import uuid
import shutil
import pathlib
import datetime
from dataclasses import dataclass
from typing import Optional, List, Dict, Any

from book_config import BookConfig, slugify

BASE_DIR = pathlib.Path(__file__).parent.resolve()
DEFAULT_OUTPUT_DIR = BASE_DIR / "output"

def sanitize_path_component(component: str, default: str = "item") -> str:
    """Higieniza componentes de caminho para evitar path traversal ou caracteres inválidos no SO."""
    cleaned = re.sub(r"[^\w\.-]", "-", component.strip()).strip("-.")
    return cleaned if cleaned else default

@dataclass
class BookRunPaths:
    book_id: str
    run_id: str
    language: str
    slug: str
    root_dir: pathlib.Path
    content_dir: pathlib.Path
    metadata_dir: pathlib.Path
    assets_dir: pathlib.Path
    paperback_dir: pathlib.Path
    hardcover_dir: pathlib.Path
    ebook_dir: pathlib.Path
    reports_dir: pathlib.Path
    previews_dir: pathlib.Path
    logs_dir: pathlib.Path
    tmp_dir: pathlib.Path

    @property
    def manifest_path(self) -> pathlib.Path:
        return self.reports_dir / "manifest.json"

    @property
    def config_path(self) -> pathlib.Path:
        return self.reports_dir / "applied_config.json"

    def clean_tmp(self):
        """Remove arquivos temporários da execução sem afetar os artefatos finais."""
        if self.tmp_dir.exists():
            for item in self.tmp_dir.iterdir():
                try:
                    if item.is_file():
                        item.unlink()
                    elif item.is_dir():
                        shutil.rmtree(item)
                except Exception:
                    pass

class StorageManager:
    def __init__(self, base_output_dir: Optional[pathlib.Path] = None):
        self.base_output_dir = (base_output_dir or DEFAULT_OUTPUT_DIR).resolve()
        self.base_output_dir.mkdir(parents=True, exist_ok=True)

    def _resolve_book_dir(self, slug: str, book_id: str) -> pathlib.Path:
        safe_slug = sanitize_path_component(slug, "devocional")
        safe_book_id = sanitize_path_component(book_id, "book")
        folder_name = f"{safe_slug}--{safe_book_id}"
        resolved = (self.base_output_dir / folder_name).resolve()
        
        # Proteção contra escape de diretório (Path Traversal)
        if not resolved.is_relative_to(self.base_output_dir):
            raise ValueError(f"Caminho inválido detectado fora de output: {resolved}")
        return resolved

    def generate_run_id(self) -> str:
        now_str = datetime.datetime.now().strftime("run_%Y%m%d_%H%M%S")
        rand_suffix = uuid.uuid4().hex[:6]
        return f"{now_str}_{rand_suffix}"

    def get_or_create_run(self, config: BookConfig, run_id: Optional[str] = None) -> BookRunPaths:
        """
        Cria ou recupera a estrutura de pastas para uma execução específica.
        Se run_id não for informado, gera um novo exclusivo.
        """
        book_dir = self._resolve_book_dir(config.folder_slug, config.book_id)
        safe_lang = sanitize_path_component(config.normalized_language, "en-US")
        
        active_run_id = sanitize_path_component(run_id or self.generate_run_id(), "run_default")
        run_root = (book_dir / safe_lang / active_run_id).resolve()
        
        if not run_root.is_relative_to(self.base_output_dir):
            raise ValueError(f"Caminho de execução escapou do diretório base: {run_root}")

        paths = BookRunPaths(
            book_id=config.book_id,
            run_id=active_run_id,
            language=safe_lang,
            slug=config.folder_slug,
            root_dir=run_root,
            content_dir=run_root / "content",
            metadata_dir=run_root / "metadata",
            assets_dir=run_root / "assets",
            paperback_dir=run_root / "paperback",
            hardcover_dir=run_root / "hardcover",
            ebook_dir=run_root / "ebook",
            reports_dir=run_root / "reports",
            previews_dir=run_root / "previews",
            logs_dir=run_root / "logs",
            tmp_dir=run_root / "tmp"
        )

        # Garante a criação de todas as subpastas oficiais
        for sub_dir in [
            paths.root_dir, paths.content_dir, paths.metadata_dir, paths.assets_dir,
            paths.paperback_dir, paths.hardcover_dir, paths.ebook_dir, paths.reports_dir,
            paths.previews_dir, paths.logs_dir, paths.tmp_dir
        ]:
            sub_dir.mkdir(parents=True, exist_ok=True)

        # Salva o arquivo de configuração aplicado
        config.save_json(paths.config_path)

        # Copia assets básicos do projeto se existirem
        src_assets = BASE_DIR / "assets"
        if src_assets.exists():
            for asset_file in src_assets.glob("*.*"):
                dest = paths.assets_dir / asset_file.name
                if not dest.exists():
                    try:
                        shutil.copy2(asset_file, dest)
                    except Exception:
                        pass

        return paths

    def list_books(self) -> List[str]:
        """Lista todas as pastas de devocionais existentes em output/."""
        books = []
        if not self.base_output_dir.exists():
            return books
        for item in self.base_output_dir.iterdir():
            if item.is_dir() and "--" in item.name:
                books.append(item.name)
        return sorted(books)

    def list_runs_for_book(self, slug: str, book_id: str, language: Optional[str] = None) -> List[Dict[str, Any]]:
        """Lista todas as execuções de um determinado devocional e idioma."""
        book_dir = self._resolve_book_dir(slug, book_id)
        if not book_dir.exists():
            return []

        runs = []
        lang_dirs = [book_dir / language] if language else [d for d in book_dir.iterdir() if d.is_dir()]

        for ldir in lang_dirs:
            if not ldir.exists() or not ldir.is_dir():
                continue
            for rdir in ldir.iterdir():
                if rdir.is_dir():
                    manifest_file = rdir / "reports" / "manifest.json"
                    has_manifest = manifest_file.exists()
                    runs.append({
                        "language": ldir.name,
                        "run_id": rdir.name,
                        "path": str(rdir),
                        "has_manifest": has_manifest,
                        "created_at": datetime.datetime.fromtimestamp(rdir.stat().st_ctime).isoformat()
                    })

        return sorted(runs, key=lambda x: x["run_id"], reverse=True)

    def migrate_legacy_output(self, target_config: BookConfig, dry_run: bool = True) -> Dict[str, Any]:
        """
        Modo de migração seguro: inspeciona arquivos soltos na raiz de output/
        e os organiza na pasta estruturada da execução sem excluir arquivos antigos.
        """
        report = {
            "dry_run": dry_run,
            "found_files": [],
            "actions": []
        }

        paths = self.get_or_create_run(target_config)

        # Identifica arquivos na raiz de output/
        for f in self.base_output_dir.iterdir():
            if f.is_file():
                report["found_files"].append(f.name)
                dest = None
                if f.suffix.lower() == ".pdf":
                    dest = paths.paperback_dir / f.name
                elif f.suffix.lower() == ".epub":
                    dest = paths.ebook_dir / f.name
                elif f.suffix.lower() in [".png", ".jpg", ".jpeg"]:
                    dest = paths.previews_dir / f.name

                if dest:
                    action_desc = f"Copiar '{f.name}' -> '{dest.relative_to(self.base_output_dir)}'"
                    report["actions"].append(action_desc)
                    if not dry_run:
                        shutil.copy2(f, dest)

        return report

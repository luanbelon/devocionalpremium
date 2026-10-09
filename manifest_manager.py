# -*- coding: utf-8 -*-
"""
Gerador e Gerenciador de Manifesto de Execução (manifest.json).
Registra com integridade criptográfica (SHA-256):
- Identificação do livro, run-id, autor, idioma
- Configurações solicitadas vs efetivamente aplicadas
- Versão e data das regras KDP oficiais
- Paginação física final de cada edição
- Margens, dimensões, sangria, papel e tinta
- Caminhos relativos de todos os artefatos produzidos
- Status de validação, avisos, erros e pendências para o KDP Print Previewer
"""

import json
import hashlib
import pathlib
import datetime
from typing import Dict, Any, List, Optional

from book_config import BookConfig
from kdp_specs import get_kdp_rules

def calculate_file_hash(path: pathlib.Path) -> str:
    """Calcula hash SHA-256 de um arquivo em disco."""
    if not path.exists():
        return ""
    sha = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            sha.update(chunk)
    return sha.hexdigest()

class ManifestManager:
    def __init__(self, run_root_dir: pathlib.Path):
        self.run_root_dir = pathlib.Path(run_root_dir).resolve()

    def build_manifest(
        self,
        config: BookConfig,
        run_id: str,
        interior_validation: Dict[str, Any],
        cover_info: Optional[Dict[str, Any]] = None,
        epub_files: Optional[List[pathlib.Path]] = None,
        extra_files: Optional[List[pathlib.Path]] = None
    ) -> Dict[str, Any]:
        """Constrói e salva o manifest.json da execução."""
        rules = get_kdp_rules()
        now_iso = datetime.datetime.now().isoformat()
        
        final_page_count = interior_validation.get("total_pages", config.estimated_pages)
        applied_margins = config.get_effective_margins(final_page_count)
        geometry = config.get_geometry()

        # Coleta arquivos produzidos e seus hashes
        produced_files = []
        
        def add_file_entry(f_path: pathlib.Path, category: str):
            if f_path and f_path.exists():
                try:
                    rel_p = str(f_path.relative_to(self.run_root_dir)).replace("\\", "/")
                except ValueError:
                    rel_p = f_path.name
                produced_files.append({
                    "category": category,
                    "filename": f_path.name,
                    "relative_path": rel_p,
                    "size_bytes": f_path.stat().st_size,
                    "sha256": calculate_file_hash(f_path)
                })

        interior_pdf = interior_validation.get("file_path")
        if interior_pdf:
            add_file_entry(pathlib.Path(interior_pdf), f"{config.edition_type}_interior")

        if cover_info and "output_path" in cover_info:
            add_file_entry(pathlib.Path(cover_info["output_path"]), f"{config.edition_type}_cover")

        if epub_files:
            for ep in epub_files:
                add_file_entry(ep, "ebook_epub")

        if extra_files:
            for ef in extra_files:
                add_file_entry(ef, "artifact")

        # Determina o status geral
        has_errors = len(interior_validation.get("errors", [])) > 0
        status = "failed" if has_errors else "validated"
        
        manifest = {
            "book_id": config.book_id,
            "run_id": run_id,
            "title": config.title,
            "subtitle": config.subtitle,
            "author": config.author,
            "language": config.normalized_language,
            "edition_type": config.edition_type,
            "marketplace": config.marketplace,
            "generated_at": now_iso,
            "status": status,
            "kdp_rules": {
                "version": rules["version"],
                "verified_date": rules["verified_date"],
                "sources_count": len(rules["sources"])
            },
            "configuration": {
                "requested": {
                    "trim_size": config.trim_size,
                    "paper_type": config.paper_type,
                    "ink_type": config.ink_type,
                    "bleed": config.bleed,
                    "estimated_pages": config.estimated_pages,
                    "reading_opening_rule": config.reading_opening_rule,
                    "editorial_margin_inside_in": config.editorial_margin_inside,
                    "editorial_margin_outside_in": config.editorial_margin_outside,
                    "editorial_margin_top_in": config.editorial_margin_top,
                    "editorial_margin_bottom_in": config.editorial_margin_bottom
                },
                "effectively_applied": {
                    "final_physical_pages": final_page_count,
                    "trim_dimensions_in": [geometry["trim_width_in"], geometry["trim_height_in"]],
                    "page_dimensions_in": [geometry["page_width_in"], geometry["page_height_in"]],
                    "page_dimensions_pt": [geometry["page_width_pt"], geometry["page_height_pt"]],
                    "bleed_applied": geometry["bleed"],
                    "margins_effective_in": {
                        "inside": applied_margins["inside_in"],
                        "outside": applied_margins["outside_in"],
                        "top": applied_margins["top_in"],
                        "bottom": applied_margins["bottom_in"]
                    },
                    "margins_effective_pt": {
                        "inside": applied_margins["inside_pt"],
                        "outside": applied_margins["outside_pt"],
                        "top": applied_margins["top_pt"],
                        "bottom": applied_margins["bottom_pt"]
                    }
                }
            },
            "validation": {
                "interior_checks": interior_validation.get("checks", {}),
                "errors": interior_validation.get("errors", []),
                "warnings": interior_validation.get("warnings", []),
                "pending_reviews": interior_validation.get("pending_reviews", []),
                "disclaimer": interior_validation.get("disclaimer", "")
            },
            "cover": cover_info if cover_info else {},
            "files": produced_files
        }

        # Salva manifest em reports/manifest.json e na raiz do run
        reports_dir = self.run_root_dir / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = reports_dir / "manifest.json"
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, ensure_ascii=False, indent=2)

        root_manifest = self.run_root_dir / "manifest.json"
        with open(root_manifest, "w", encoding="utf-8") as f:
            json.dump(manifest, f, ensure_ascii=False, indent=2)

        return manifest

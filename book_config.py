# -*- coding: utf-8 -*-
"""
Módulo de Configuração de Livro / Devocional para Amazon KDP.
Permite definir identificador estável, parâmetros editoriais, perfil de impressão,
faixas de páginas e regras de abertura de leitura (nova página ou página ímpar/recto).
"""

import json
import pathlib
import re
from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, Any

from kdp_specs import (
    get_trim_dimensions,
    calculate_effective_margins,
    calculate_page_geometry,
    validate_kdp_profile
)

def slugify(text: str) -> str:
    """Converte um título ou nome em um slug limpo e seguro para diretórios."""
    text = text.strip().lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return text.strip("-") or "livro"

@dataclass
class BookConfig:
    book_id: str = "30-days-closer-to-god"
    title: str = "30 DAYS CLOSER TO GOD"
    subtitle: str = "A daily journey of faith, prayer, and intimacy with God"
    author: str = "Lyan Davis"
    language: str = "en"               # "en" ou "pt" (normalizado para en-US / pt-BR)
    edition_type: str = "paperback"    # "paperback" ou "hardcover"
    marketplace: str = "amazon.com"    # "amazon.com", "amazon.com.br", etc.
    trim_size: str = "6x9"             # "6x9", "5.5x8.5", etc.
    paper_type: str = "cream"          # "cream" ou "white"
    ink_type: str = "black_and_white"  # "black_and_white", "standard_color", "premium_color"
    bleed: bool = False
    
    # Parâmetros tipográficos e diagramação
    font_family: str = "EB Garamond"
    font_size_pt: float = 10.5
    line_height: float = 1.35
    
    # Preferências editoriais de margem (em polegadas)
    editorial_margin_top: float = 0.55
    editorial_margin_bottom: float = 0.55
    editorial_margin_inside: float = 0.75
    editorial_margin_outside: float = 0.65
    
    # Paginação e regras de abertura
    estimated_pages: int = 104
    min_pages: Optional[int] = None
    max_pages: Optional[int] = None
    reading_opening_rule: str = "new_page"  # "new_page" ou "recto" (página ímpar)
    start_page_number: int = 15             # Primeira página do primeiro dia após o front matter
    
    # Custom metadata adicional
    custom_metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def normalized_language(self) -> str:
        lang = self.language.lower().strip()
        if lang in ["en", "en-us", "eng"]:
            return "en-US"
        if lang in ["pt", "pt-br", "por"]:
            return "pt-BR"
        return lang

    @property
    def folder_slug(self) -> str:
        return slugify(self.title)

    @property
    def trim_dimensions(self) -> tuple[float, float]:
        return get_trim_dimensions(self.trim_size, self.edition_type)

    def get_effective_margins(self, page_count: int) -> Dict[str, float]:
        """Calcula margens considerando o maior valor entre o mínimo KDP e a preferência editorial."""
        return calculate_effective_margins(
            page_count=page_count,
            bleed=self.bleed,
            editorial_margins={
                "margin_inside": self.editorial_margin_inside,
                "margin_outside": self.editorial_margin_outside,
                "margin_top": self.editorial_margin_top,
                "margin_bottom": self.editorial_margin_bottom
            }
        )

    def get_geometry(self) -> Dict[str, Any]:
        w, h = self.trim_dimensions
        return calculate_page_geometry(w, h, self.bleed)

    def validate_profile(self, page_count: Optional[int] = None) -> Dict[str, Any]:
        count = page_count or self.estimated_pages
        res = validate_kdp_profile(
            edition_type=self.edition_type,
            trim_size=self.trim_size,
            ink_type=self.ink_type,
            paper_type=self.paper_type,
            page_count=count,
            bleed=self.bleed
        )
        # Checa faixa desejada opcional
        if self.min_pages is not None and count < self.min_pages:
            res["warnings"].append(f"Contagem ({count}) abaixo da faixa desejada mínima configurada ({self.min_pages}).")
        if self.max_pages is not None and count > self.max_pages:
            res["warnings"].append(f"Contagem ({count}) acima da faixa desejada máxima configurada ({self.max_pages}).")
            
        return res

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BookConfig":
        valid_keys = cls.__dataclass_fields__.keys()
        filtered = {k: v for k, v in data.items() if k in valid_keys}
        return cls(**filtered)

    def save_json(self, path: pathlib.Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)

    @classmethod
    def load_json(cls, path: pathlib.Path) -> "BookConfig":
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.from_dict(data)

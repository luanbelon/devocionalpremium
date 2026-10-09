# -*- coding: utf-8 -*-
"""
Gerador e Validador de Capas Oficiais Amazon KDP (Paperback e Hardcover).
Gera especificações exatas e PDF de capa baseado na contagem real e final de páginas do miolo.
Implementa invalidação automática de capa quando a paginação ou perfil de papel mudar.
Mantém miolo e capa estritamente em arquivos separados.
"""

import os
import json
import hashlib
import pathlib
from typing import Dict, Any, Optional
import pymupdf

from kdp_specs import (
    calculate_paperback_cover,
    calculate_hardcover_cover,
    inches_to_pt
)
from book_config import BookConfig

class CoverGenerator:
    def __init__(self, config: BookConfig):
        self.config = config

    def calculate_cover_dimensions(self, final_page_count: int) -> Dict[str, Any]:
        """Calcula as dimensões exatas da capa com base na contagem física final do miolo."""
        trim_w, trim_h = self.config.trim_dimensions
        if self.config.edition_type == "hardcover":
            return calculate_hardcover_cover(
                trim_width_in=trim_w,
                trim_height_in=trim_h,
                page_count=final_page_count,
                paper_type=self.config.paper_type,
                ink_type=self.config.ink_type
            )
        else:
            return calculate_paperback_cover(
                trim_width_in=trim_w,
                trim_height_in=trim_h,
                page_count=final_page_count,
                paper_type=self.config.paper_type,
                ink_type=self.config.ink_type
            )

    def generate_cover_spec_hash(self, final_page_count: int) -> str:
        """Gera hash único do perfil da capa para invalidação automática se a paginação mudar."""
        spec_str = f"{self.config.edition_type}|{self.config.trim_size}|{self.config.paper_type}|{self.config.ink_type}|{final_page_count}"
        return hashlib.sha256(spec_str.encode("utf-8")).hexdigest()

    def generate_cover_pdf(
        self,
        final_page_count: int,
        output_path: pathlib.Path,
        cover_title: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Gera o PDF da capa com dimensões oficiais milimétricas, respeitando sangria, lombada e dobras.
        """
        cov_dims = self.calculate_cover_dimensions(final_page_count)
        width_pt = cov_dims["total_width_pt"]
        height_pt = cov_dims["total_height_pt"]
        spine_pt = cov_dims["spine_width_pt"]
        
        output_path = pathlib.Path(output_path).resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Cria documento PDF vetorial limpo com PyMuPDF
        doc = pymupdf.open()
        page = doc.new_page(width=width_pt, height=height_pt)

        # Cor de fundo editorial clássico (creme nobre / branco limpo)
        bg_rect = pymupdf.Rect(0, 0, width_pt, height_pt)
        page.draw_rect(bg_rect, color=(0.1, 0.1, 0.1), fill=(0.98, 0.97, 0.95))

        # Posições calculadas
        # Capa: [Quarta Capa (Back)] | [Lombada (Spine)] | [Primeira Capa (Front)]
        if self.config.edition_type == "hardcover":
            wrap_pt = inches_to_pt(cov_dims["wrap_in"])
            hinge_pt = inches_to_pt(cov_dims["hinge_in"])
            trim_w_pt = inches_to_pt(cov_dims["trim_width_in"])
            
            back_x0 = wrap_pt
            back_x1 = back_x0 + trim_w_pt
            
            spine_x0 = back_x1 + hinge_pt
            spine_x1 = spine_x0 + spine_pt
            
            front_x0 = spine_x1 + hinge_pt
            front_x1 = front_x0 + trim_w_pt
        else:
            bleed_pt = inches_to_pt(cov_dims["bleed_in"])
            trim_w_pt = inches_to_pt(cov_dims["trim_width_in"])
            
            back_x0 = bleed_pt
            back_x1 = back_x0 + trim_w_pt
            
            spine_x0 = back_x1
            spine_x1 = spine_x0 + spine_pt
            
            front_x0 = spine_x1
            front_x1 = front_x0 + trim_w_pt

        # Linhas de guia sutis para visualização da lombada
        page.draw_line(pymupdf.Point(spine_x0, 0), pymupdf.Point(spine_x0, height_pt), color=(0.7, 0.7, 0.7), width=0.5)
        page.draw_line(pymupdf.Point(spine_x1, 0), pymupdf.Point(spine_x1, height_pt), color=(0.7, 0.7, 0.7), width=0.5)

        # Título na Primeira Capa (Front Cover)
        front_center_x = (front_x0 + front_x1) / 2.0
        title_text = cover_title or self.config.title
        
        # Caixa de título
        page.insert_text(
            pymupdf.Point(front_center_x - 120, height_pt * 0.35),
            title_text,
            fontsize=20,
            fontname="helv",
            color=(0.1, 0.1, 0.1)
        )
        # Autor
        page.insert_text(
            pymupdf.Point(front_center_x - 60, height_pt * 0.75),
            self.config.author.upper(),
            fontsize=12,
            fontname="helv",
            color=(0.3, 0.3, 0.3)
        )

        # Texto da Lombada se permitido (mínimo 79 páginas)
        if cov_dims["allow_spine_text"]:
            spine_center_x = (spine_x0 + spine_x1) / 2.0
            spine_text = f"{title_text} • {self.config.author}"
            # No KDP, texto de lombada é lido de cima para baixo ou impresso na vertical
            page.insert_text(
                pymupdf.Point(spine_center_x - 3, height_pt * 0.5),
                spine_text,
                fontsize=8,
                rotate=270,
                color=(0.2, 0.2, 0.2)
            )

        # Quarta capa (Back cover) - Descrição breve
        back_center_x = (back_x0 + back_x1) / 2.0
        subtitle_text = self.config.subtitle
        page.insert_text(
            pymupdf.Point(back_center_x - 100, height_pt * 0.45),
            subtitle_text[:60] + "...",
            fontsize=11,
            color=(0.3, 0.3, 0.3)
        )

        doc.save(str(output_path))
        doc.close()

        spec_hash = self.generate_cover_spec_hash(final_page_count)
        
        meta = {
            "output_path": str(output_path),
            "spec_hash": spec_hash,
            "dimensions": cov_dims,
            "is_valid": True,
            "generated_for_page_count": final_page_count
        }

        # Salva metadados da capa para verificação de invalidação futura
        meta_path = output_path.with_suffix(".json")
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)

        return meta

    def is_cover_stale(self, cover_meta_path: pathlib.Path, current_page_count: int) -> bool:
        """Verifica se a capa existente precisa ser invalidada por divergência na paginação ou perfil."""
        if not cover_meta_path.exists():
            return True
        try:
            with open(cover_meta_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            current_hash = self.generate_cover_spec_hash(current_page_count)
            return data.get("spec_hash") != current_hash
        except Exception:
            return True

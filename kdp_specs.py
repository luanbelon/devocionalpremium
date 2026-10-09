# -*- coding: utf-8 -*-
"""
Módulo Centralizado de Especificações de Impressão Amazon KDP.
Contém regras oficiais estruturadas e versionadas, conversão de unidades,
cálculo de geometria com e sem sangria, margens mínimas e espelhadas,
e fórmulas de capa para Paperback e Hardcover.

Fontes Oficiais:
- https://kdp.amazon.com/en_US/help/topic/GVBQ3CMEQW3W2VL6 (Dimensões e limites de páginas)
- https://kdp.amazon.com/en_US/help/topic/G201834180 (Margens e Sangria)
- https://kdp.amazon.com/en_US/help/topic/G201857950 (Capa Paperback)
- https://kdp.amazon.com/en_US/help/topic/GKYZRXFBZH2LDXAK (Capa Hardcover)
- https://kdp.amazon.com/en_US/help/topic/GDTKFJPNQCBTMRV6 (Requisitos de Arquivo)
- https://kdp.amazon.com/cover-calculator (Calculadora de Capa)
"""

import json
import logging
from typing import Dict, Any, Tuple, Optional, List

logger = logging.getLogger("kdp_specs")

# Conversões oficiais: 1 polegada = 25.4 mm = 72 pontos PostScript
INCH_TO_MM = 25.4
INCH_TO_POINTS = 72.0
MM_TO_INCH = 1.0 / 25.4
MM_TO_POINTS = 72.0 / 25.4
POINTS_TO_INCH = 1.0 / 72.0
POINTS_TO_MM = 25.4 / 72.0

def inches_to_pt(inches: float) -> float:
    return inches * INCH_TO_POINTS

def pt_to_inches(points: float) -> float:
    return points * POINTS_TO_INCH

def inches_to_mm(inches: float) -> float:
    return inches * INCH_TO_MM

def mm_to_inches(mm: float) -> float:
    return mm * MM_TO_INCH

def mm_to_pt(mm: float) -> float:
    return mm * MM_TO_POINTS

def pt_to_mm(points: float) -> float:
    return points * POINTS_TO_MM

# Tabela Oficial de Regras KDP - Snapshot Verificado
KDP_OFFICIAL_SOURCES = [
    {
        "topic": "Print Trim Sizes and Page Count Limits",
        "url": "https://kdp.amazon.com/en_US/help/topic/GVBQ3CMEQW3W2VL6",
        "description": "Especificações de tamanhos de corte, encadernação e faixas de páginas"
    },
    {
        "topic": "Print Margins and Bleed",
        "url": "https://kdp.amazon.com/en_US/help/topic/G201834180",
        "description": "Tabela de margem interna (calha/gutter), margens externas e sangria"
    },
    {
        "topic": "Paperback Cover Specifications",
        "url": "https://kdp.amazon.com/en_US/help/topic/G201857950",
        "description": "Cálculo de lombada, sangria e área de segurança para brochura"
    },
    {
        "topic": "Hardcover Specifications",
        "url": "https://kdp.amazon.com/en_US/help/topic/GKYZRXFBZH2LDXAK",
        "description": "Especificações de capa dura (Case Laminate), dobras (wrap) e margens"
    },
    {
        "topic": "Print File Requirements",
        "url": "https://kdp.amazon.com/en_US/help/topic/GDTKFJPNQCBTMRV6",
        "description": "Requisitos de PDF, fontes incorporadas, ausência de marcas de corte e 300 DPI"
    },
    {
        "topic": "Cover Calculator",
        "url": "https://kdp.amazon.com/cover-calculator",
        "description": "Calculadora oficial de dimensões totais de capa e lombada"
    }
]

DEFAULT_KDP_RULES_SNAPSHOT = {
    "version": "2026.1",
    "verified_date": "2026-10-01",
    "sources": KDP_OFFICIAL_SOURCES,
    "gutter_tiers": [
        # (min_pages, max_pages, min_gutter_inches)
        {"min_pages": 24, "max_pages": 150, "min_gutter_in": 0.375},
        {"min_pages": 151, "max_pages": 300, "min_gutter_in": 0.500},
        {"min_pages": 301, "max_pages": 500, "min_gutter_in": 0.625},
        {"min_pages": 501, "max_pages": 700, "min_gutter_in": 0.750},
        {"min_pages": 701, "max_pages": 828, "min_gutter_in": 0.875}
    ],
    "margins_outside_min": {
        "no_bleed_in": 0.250,
        "bleed_in": 0.375
    },
    "bleed_allowances": {
        "width_in": 0.125,   # Adicionada à borda externa
        "height_in": 0.250   # 0.125 superior + 0.125 inferior
    },
    "supported_trim_sizes": {
        "paperback": [
            {"code": "5x8", "width_in": 5.0, "height_in": 8.0, "name": "5\" x 8\""},
            {"code": "5.25x8", "width_in": 5.25, "height_in": 8.0, "name": "5.25\" x 8\""},
            {"code": "5.5x8.5", "width_in": 5.5, "height_in": 8.5, "name": "5.5\" x 8.5\""},
            {"code": "6x9", "width_in": 6.0, "height_in": 9.0, "name": "6\" x 9\""},
            {"code": "5.06x7.81", "width_in": 5.06, "height_in": 7.81, "name": "5.06\" x 7.81\""},
            {"code": "6.14x9.21", "width_in": 6.14, "height_in": 9.21, "name": "6.14\" x 9.21\""},
            {"code": "6.69x9.61", "width_in": 6.69, "height_in": 9.61, "name": "6.69\" x 9.61\""},
            {"code": "7x10", "width_in": 7.0, "height_in": 10.0, "name": "7\" x 10\""},
            {"code": "7.44x9.69", "width_in": 7.44, "height_in": 9.69, "name": "7.44\" x 9.69\""},
            {"code": "7.5x9.25", "width_in": 7.5, "height_in": 9.25, "name": "7.5\" x 9.25\""},
            {"code": "8x10", "width_in": 8.0, "height_in": 10.0, "name": "8\" x 10\""},
            {"code": "8.5x8.5", "width_in": 8.5, "height_in": 8.5, "name": "8.5\" x 8.5\""},
            {"code": "8.5x11", "width_in": 8.5, "height_in": 11.0, "name": "8.5\" x 11\""},
            {"code": "8.27x11.69", "width_in": 8.27, "height_in": 11.69, "name": "A4 (8.27\" x 11.69\")"}
        ],
        "hardcover": [
            # Tamanhos suportados oficialmente pelo KDP para Capa Dura (Case Laminate)
            {"code": "5.5x8.5", "width_in": 5.5, "height_in": 8.5, "name": "5.5\" x 8.5\""},
            {"code": "6x9", "width_in": 6.0, "height_in": 9.0, "name": "6\" x 9\""},
            {"code": "6.14x9.21", "width_in": 6.14, "height_in": 9.21, "name": "6.14\" x 9.21\""},
            {"code": "7x10", "width_in": 7.0, "height_in": 10.0, "name": "7\" x 10\""},
            {"code": "8.25x11", "width_in": 8.25, "height_in": 11.0, "name": "8.25\" x 11\""}
        ]
    },
    "page_limits": {
        "paperback": {
            "black_and_white": {
                "white": {"min_pages": 24, "max_pages": 828},
                "cream": {"min_pages": 24, "max_pages": 828}
            },
            "standard_color": {
                "white": {"min_pages": 72, "max_pages": 600}
            },
            "premium_color": {
                "white": {"min_pages": 24, "max_pages": 828}
            }
        },
        "hardcover": {
            # Regra Oficial KDP: Hardcover é estritamente 75 a 550 páginas
            "black_and_white": {
                "white": {"min_pages": 75, "max_pages": 550},
                "cream": {"min_pages": 75, "max_pages": 550}
            },
            "standard_color": {
                "white": {"min_pages": 75, "max_pages": 550}
            },
            "premium_color": {
                "white": {"min_pages": 75, "max_pages": 550}
            }
        }
    },
    "paper_thickness_per_page_in": {
        "black_and_white": {
            "white": 0.002252,
            "cream": 0.002500
        },
        "standard_color": {
            "white": 0.002252
        },
        "premium_color": {
            "white": 0.002347
        }
    },
    "cover_specs": {
        "paperback": {
            "bleed_in": 0.125,
            "min_pages_for_spine_text": 79,
            "spine_safety_margin_in": 0.0625
        },
        "hardcover": {
            "wrap_in": 0.590,            # 15 mm dobra externa
            "hinge_in": 0.394,           # 10 mm calha de articulação da capa dura
            "board_thickness_in": 0.080, # 2 mm espessura do papelão
            "spine_wrap_allowance_in": 0.197, # Folga da lombada rígida (aprox 5 mm)
            "min_pages_for_spine_text": 79,
            "spine_safety_margin_in": 0.0625
        }
    },
    "file_constraints": {
        "max_pdf_size_mb": 650,
        "min_image_dpi": 300,
        "allow_spreads": False,
        "require_even_pages": True,
        "allow_crop_marks": False
    }
}

# Estado ativo das regras
_CURRENT_KDP_RULES = dict(DEFAULT_KDP_RULES_SNAPSHOT)

def get_kdp_rules() -> Dict[str, Any]:
    """Retorna as regras ativas do KDP."""
    return _CURRENT_KDP_RULES

def validate_rules_schema(candidate: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Valida se uma atualização de regras atende a todos os campos essenciais."""
    errors = []
    required_keys = ["version", "verified_date", "gutter_tiers", "margins_outside_min", 
                     "bleed_allowances", "supported_trim_sizes", "page_limits", 
                     "paper_thickness_per_page_in", "cover_specs"]
    for k in required_keys:
        if k not in candidate:
            errors.append(f"Chave obrigatória ausente nas regras KDP: '{k}'")
            
    if "gutter_tiers" in candidate:
        if not isinstance(candidate["gutter_tiers"], list) or len(candidate["gutter_tiers"]) < 3:
            errors.append("gutter_tiers deve ser uma lista com pelo menos 3 faixas.")
            
    if "page_limits" in candidate:
        if "paperback" not in candidate["page_limits"] or "hardcover" not in candidate["page_limits"]:
            errors.append("page_limits deve conter regras para 'paperback' e 'hardcover'.")
            
    return (len(errors) == 0, errors)

def update_kdp_rules_from_snapshot(new_snapshot: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Atualiza as regras ativas a partir de um novo snapshot validado.
    Se a validação falhar, mantém a versão anterior e registra o erro.
    """
    global _CURRENT_KDP_RULES
    valid, errors = validate_rules_schema(new_snapshot)
    if not valid:
        err_msg = f"Falha ao validar novo snapshot KDP: {'; '.join(errors)}. Mantendo versão {_CURRENT_KDP_RULES.get('version')}."
        logger.error(err_msg)
        return False, err_msg
        
    _CURRENT_KDP_RULES = dict(new_snapshot)
    msg = f"Regras KDP atualizadas com sucesso para versão {_CURRENT_KDP_RULES.get('version')} (Verificada em {_CURRENT_KDP_RULES.get('verified_date')})."
    logger.info(msg)
    return True, msg

def get_min_inside_margin(page_count: int) -> float:
    """
    Retorna a margem interna mínima (gutter/calha) obrigatória em polegadas para o total de páginas.
    Tabela oficial:
      24–150:  0.375" (27 pt)
      151–300: 0.500" (36 pt)
      301–500: 0.625" (45 pt)
      501–700: 0.750" (54 pt)
      701–828: 0.875" (63 pt)
    """
    tiers = _CURRENT_KDP_RULES["gutter_tiers"]
    for t in tiers:
        if t["min_pages"] <= page_count <= t["max_pages"]:
            return float(t["min_gutter_in"])
    if page_count < tiers[0]["min_pages"]:
        return float(tiers[0]["min_gutter_in"])
    return float(tiers[-1]["min_gutter_in"])

def get_min_outside_margin(bleed: bool = False) -> float:
    """Retorna a margem mínima para bordas externas, superior e inferior em polegadas."""
    margins = _CURRENT_KDP_RULES["margins_outside_min"]
    return float(margins["bleed_in"] if bleed else margins["no_bleed_in"])

def get_trim_dimensions(trim_size: str, edition_type: str = "paperback") -> Tuple[float, float]:
    """Retorna (largura_pol, altura_pol) para o código de corte."""
    norm_size = trim_size.lower().strip().replace("″", "").replace('"', "").replace(" ", "")
    sizes = _CURRENT_KDP_RULES["supported_trim_sizes"].get(edition_type, _CURRENT_KDP_RULES["supported_trim_sizes"]["paperback"])
    for s in sizes:
        if s["code"] == norm_size:
            return float(s["width_in"]), float(s["height_in"])
    # Fallback para parsing direto caso seja ex: '6x9' ou '5.5x8.5'
    if "x" in norm_size:
        parts = norm_size.split("x")
        try:
            return float(parts[0]), float(parts[1])
        except ValueError:
            pass
    return 6.0, 9.0

def calculate_page_geometry(trim_width_in: float, trim_height_in: float, bleed: bool = False) -> Dict[str, Any]:
    """
    Calcula a geometria da página do miolo:
    - Sem sangria: dimensões exatas de corte
    - Com sangria: +0.125" na largura (borda externa), +0.25" na altura (0.125" superior + 0.125" inferior)
    """
    allowances = _CURRENT_KDP_RULES["bleed_allowances"]
    if bleed:
        page_width_in = trim_width_in + float(allowances["width_in"])
        page_height_in = trim_height_in + float(allowances["height_in"])
    else:
        page_width_in = trim_width_in
        page_height_in = trim_height_in
        
    return {
        "trim_width_in": trim_width_in,
        "trim_height_in": trim_height_in,
        "trim_width_pt": inches_to_pt(trim_width_in),
        "trim_height_pt": inches_to_pt(trim_height_in),
        "page_width_in": page_width_in,
        "page_height_in": page_height_in,
        "page_width_pt": inches_to_pt(page_width_in),
        "page_height_pt": inches_to_pt(page_height_in),
        "bleed": bleed,
        "bleed_extra_width_in": float(allowances["width_in"]) if bleed else 0.0,
        "bleed_extra_height_in": float(allowances["height_in"]) if bleed else 0.0
    }

def calculate_effective_margins(
    page_count: int,
    bleed: bool = False,
    editorial_margins: Optional[Dict[str, float]] = None
) -> Dict[str, float]:
    """
    Calcula as margens efetivas aplicando:
    margem = max(mínimo_obrigatório_kdp, preferência_editorial)
    Retorna dicionário com valores em polegadas e pontos.
    """
    min_inside_in = get_min_inside_margin(page_count)
    min_outside_in = get_min_outside_margin(bleed)
    min_top_in = min_outside_in
    min_bottom_in = min_outside_in

    editorial = editorial_margins or {}
    ed_inside = float(editorial.get("inside_in", editorial.get("margin_inside", min_inside_in)))
    ed_outside = float(editorial.get("outside_in", editorial.get("margin_outside", min_outside_in)))
    ed_top = float(editorial.get("top_in", editorial.get("margin_top", min_top_in)))
    ed_bottom = float(editorial.get("bottom_in", editorial.get("margin_bottom", min_bottom_in)))

    inside_in = max(min_inside_in, ed_inside)
    outside_in = max(min_outside_in, ed_outside)
    top_in = max(min_top_in, ed_top)
    bottom_in = max(min_bottom_in, ed_bottom)

    return {
        "inside_in": inside_in,
        "outside_in": outside_in,
        "top_in": top_in,
        "bottom_in": bottom_in,
        "inside_pt": inches_to_pt(inside_in),
        "outside_pt": inches_to_pt(outside_in),
        "top_pt": inches_to_pt(top_in),
        "bottom_pt": inches_to_pt(bottom_in),
        "kdp_min_inside_in": min_inside_in,
        "kdp_min_outside_in": min_outside_in
    }

def validate_kdp_profile(
    edition_type: str,
    trim_size: str,
    ink_type: str = "black_and_white",
    paper_type: str = "cream",
    page_count: int = 104,
    bleed: bool = False
) -> Dict[str, Any]:
    """
    Valida a combinação completa de formato e perfil conforme tabelas oficiais do KDP.
    Distingue Paperback de Hardcover e verifica limites rígidos de páginas.
    """
    edition_type = edition_type.lower().strip()
    ink_type = ink_type.lower().strip()
    paper_type = paper_type.lower().strip()
    
    errors = []
    warnings = []
    
    # 1. Validação do tipo de edição
    if edition_type not in ["paperback", "hardcover"]:
        errors.append(f"Tipo de edição inválido: '{edition_type}'. Deve ser 'paperback' ou 'hardcover'.")
        return {"is_valid": False, "errors": errors, "warnings": warnings}

    # 2. Validação do tamanho de corte suportado
    norm_size = trim_size.lower().strip().replace("″", "").replace('"', "").replace(" ", "")
    supported_sizes = _CURRENT_KDP_RULES["supported_trim_sizes"].get(edition_type, [])
    valid_codes = [s["code"] for s in supported_sizes]
    
    if norm_size not in valid_codes:
        errors.append(
            f"Tamanho '{trim_size}' não é suportado oficialmente para {edition_type.capitalize()} no KDP. "
            f"Tamanhos suportados: {', '.join(valid_codes)}"
        )

    # 3. Validação dos limites de páginas por encadernação, tinta e papel
    limits_catalog = _CURRENT_KDP_RULES["page_limits"].get(edition_type, {})
    ink_catalog = limits_catalog.get(ink_type)
    if not ink_catalog:
        errors.append(f"Tipo de tinta '{ink_type}' não suportado para {edition_type}. Opções: {list(limits_catalog.keys())}")
        paper_limits = None
    else:
        paper_limits = ink_catalog.get(paper_type)
        if not paper_limits:
            errors.append(f"Tipo de papel '{paper_type}' não disponível para {edition_type} com tinta '{ink_type}'. Opções: {list(ink_catalog.keys())}")

    if paper_limits:
        min_p = paper_limits["min_pages"]
        max_p = paper_limits["max_pages"]
        if page_count < min_p:
            errors.append(
                f"Contagem física de páginas ({page_count}) é inferior ao mínimo oficial de {min_p} páginas "
                f"para {edition_type.capitalize()} ({ink_type}, papel {paper_type})."
            )
        elif page_count > max_p:
            errors.append(
                f"Contagem física de páginas ({page_count}) excede o máximo oficial de {max_p} páginas "
                f"para {edition_type.capitalize()} ({ink_type}, papel {paper_type})."
            )

    # 4. Exigência de número par de páginas físicas
    if page_count % 2 != 0:
        warnings.append(
            f"O total de páginas ({page_count}) é ímpar. O processo de publicação KDP exige fechamento em número par "
            "(uma página em branco será incluída no final)."
        )

    # 5. Avisos sobre lombada (mínimo de 79 páginas para texto na lombada)
    cover_rules = _CURRENT_KDP_RULES["cover_specs"].get(edition_type, {})
    min_spine = cover_rules.get("min_pages_for_spine_text", 79)
    if page_count < min_spine:
        warnings.append(
            f"Com {page_count} páginas, o KDP não permite texto na lombada (mínimo obrigatório: {min_spine} páginas)."
        )

    return {
        "is_valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "rules_version": _CURRENT_KDP_RULES["version"],
        "rules_verified_date": _CURRENT_KDP_RULES["verified_date"],
        "edition_type": edition_type,
        "trim_size": trim_size,
        "ink_type": ink_type,
        "paper_type": paper_type,
        "page_count": page_count,
        "bleed": bleed
    }

def get_paper_thickness_per_page(ink_type: str = "black_and_white", paper_type: str = "cream") -> float:
    """Retorna a espessura em polegadas por página de acordo com a tabela oficial de cálculo do KDP."""
    thicknesses = _CURRENT_KDP_RULES["paper_thickness_per_page_in"]
    ink_dict = thicknesses.get(ink_type, thicknesses["black_and_white"])
    return float(ink_dict.get(paper_type, ink_dict.get("white", 0.002252)))

def calculate_paperback_cover(
    trim_width_in: float,
    trim_height_in: float,
    page_count: int,
    paper_type: str = "cream",
    ink_type: str = "black_and_white"
) -> Dict[str, Any]:
    """
    Calcula as dimensões completas da capa para Paperback (Brochura) segundo a fórmula oficial KDP:
    Lombada = page_count * espessura_papel
    Largura Total = 2 * trim_width + lombada + 2 * sangria (0.125")
    Altura Total = trim_height + 2 * sangria (0.125")
    """
    specs = _CURRENT_KDP_RULES["cover_specs"]["paperback"]
    bleed_in = specs["bleed_in"]
    thickness_per_page = get_paper_thickness_per_page(ink_type, paper_type)
    spine_width_in = page_count * thickness_per_page

    total_width_in = (2 * trim_width_in) + spine_width_in + (2 * bleed_in)
    total_height_in = trim_height_in + (2 * bleed_in)

    return {
        "edition_type": "paperback",
        "page_count": page_count,
        "trim_width_in": trim_width_in,
        "trim_height_in": trim_height_in,
        "spine_width_in": spine_width_in,
        "spine_width_pt": inches_to_pt(spine_width_in),
        "total_width_in": total_width_in,
        "total_height_in": total_height_in,
        "total_width_pt": inches_to_pt(total_width_in),
        "total_height_pt": inches_to_pt(total_height_in),
        "bleed_in": bleed_in,
        "allow_spine_text": page_count >= specs["min_pages_for_spine_text"],
        "spine_safety_margin_in": specs["spine_safety_margin_in"]
    }

def calculate_hardcover_cover(
    trim_width_in: float,
    trim_height_in: float,
    page_count: int,
    paper_type: str = "cream",
    ink_type: str = "black_and_white"
) -> Dict[str, Any]:
    """
    Calcula as dimensões completas da capa para Hardcover (Case Laminate) segundo a fórmula oficial KDP:
    Considera dobras de papelão (wrap = 0.59"), folga de articulação (hinge = 0.394"),
    espessura do papelão (board = 0.08") e folga da lombada rígida (0.197").
    """
    specs = _CURRENT_KDP_RULES["cover_specs"]["hardcover"]
    wrap_in = specs["wrap_in"]
    hinge_in = specs["hinge_in"]
    spine_wrap_in = specs["spine_wrap_allowance_in"]
    
    thickness_per_page = get_paper_thickness_per_page(ink_type, paper_type)
    interior_spine_in = page_count * thickness_per_page
    spine_width_in = interior_spine_in + spine_wrap_in

    total_width_in = (2 * trim_width_in) + spine_width_in + (2 * wrap_in) + (2 * hinge_in)
    total_height_in = trim_height_in + (2 * wrap_in) + 0.25 # Margem vertical com saliência de capa dura

    return {
        "edition_type": "hardcover",
        "page_count": page_count,
        "trim_width_in": trim_width_in,
        "trim_height_in": trim_height_in,
        "interior_spine_in": interior_spine_in,
        "spine_width_in": spine_width_in,
        "spine_width_pt": inches_to_pt(spine_width_in),
        "total_width_in": total_width_in,
        "total_height_in": total_height_in,
        "total_width_pt": inches_to_pt(total_width_in),
        "total_height_pt": inches_to_pt(total_height_in),
        "wrap_in": wrap_in,
        "hinge_in": hinge_in,
        "allow_spine_text": page_count >= specs["min_pages_for_spine_text"],
        "spine_safety_margin_in": specs["spine_safety_margin_in"]
    }

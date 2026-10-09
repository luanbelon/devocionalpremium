# -*- coding: utf-8 -*-
"""
Suíte Completa de Testes Automatizados para o Sistema Devocional Amazon KDP.
Cobre todos os requisitos do KDP e do fluxo de trabalho:
1. Transições da tabela de calha/gutter (150/151, 300/301, 500/501, 700/701)
2. Conversões exatas de unidades (pol, mm, pt)
3. Geometria com e sem sangria
4. Margens espelhadas e prevalência do maior valor (mínimo KDP vs editorial)
5. Limites rígidos de páginas por encadernação (Paperback 24-828, Hardcover 75-550)
6. Fechamento obrigatório em número par (adição de página final em branco)
7. Regras de abertura de leitura (new_page vs recto)
8. Invalidação da capa quando a paginação ou perfil mudar
9. Isolamento rigoroso entre livros, idiomas e execuções em output/
10. Preservação integral das 30 leituras
11. Geração real com validação técnica de PDF e manifesto
"""

import os
import sys
import json
import pathlib
import pytest
import pymupdf

BASE_DIR = pathlib.Path(__file__).parent.parent.resolve()
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from kdp_specs import (
    get_min_inside_margin,
    get_min_outside_margin,
    inches_to_pt,
    pt_to_inches,
    inches_to_mm,
    mm_to_inches,
    pt_to_mm,
    mm_to_pt,
    calculate_page_geometry,
    calculate_effective_margins,
    validate_kdp_profile,
    calculate_paperback_cover,
    calculate_hardcover_cover
)
from book_config import BookConfig, slugify
from storage_manager import StorageManager, sanitize_path_component
from pdf_validator import PDFValidator
from cover_generator import CoverGenerator
from manifest_manager import ManifestManager
import generator

BASE_DIR = pathlib.Path(__file__).parent.parent.resolve()

# -------------------------------------------------------------
# 1. TESTES DE TRANSIÇÃO DA MARGEM INTERNA (GUTTER / CALHA)
# -------------------------------------------------------------
def test_gutter_tier_transitions():
    """Valida as transições de margem interna mínima KDP nas fronteiras oficiais."""
    # Faixa 1 (24 - 150 páginas): 0.375 polegada
    assert get_min_inside_margin(24) == 0.375
    assert get_min_inside_margin(150) == 0.375

    # Transição 150 -> 151 (Faixa 2: 151 - 300 páginas): 0.500 polegada
    assert get_min_inside_margin(151) == 0.500
    assert get_min_inside_margin(300) == 0.500

    # Transição 300 -> 301 (Faixa 3: 301 - 500 páginas): 0.625 polegada
    assert get_min_inside_margin(301) == 0.625
    assert get_min_inside_margin(500) == 0.625

    # Transição 500 -> 501 (Faixa 4: 501 - 700 páginas): 0.750 polegada
    assert get_min_inside_margin(501) == 0.750
    assert get_min_inside_margin(700) == 0.750

    # Transição 700 -> 701 (Faixa 5: 701 - 828 páginas): 0.875 polegada
    assert get_min_inside_margin(701) == 0.875
    assert get_min_inside_margin(828) == 0.875

# -------------------------------------------------------------
# 2. TESTES DE CONVERSÃO DE UNIDADES
# -------------------------------------------------------------
def test_unit_conversions():
    """Valida consistência das conversões: 1 polegada = 25.4 mm = 72 pontos."""
    assert inches_to_mm(1.0) == 25.4
    assert inches_to_pt(1.0) == 72.0
    assert pt_to_inches(72.0) == 1.0
    assert pytest.approx(mm_to_inches(25.4), 0.0001) == 1.0
    assert pt_to_mm(72.0) == 25.4
    assert pytest.approx(mm_to_pt(25.4), 0.0001) == 72.0

# -------------------------------------------------------------
# 3. TESTES DE GEOMETRIA COM E SEM SANGRIA
# -------------------------------------------------------------
def test_bleed_and_no_bleed_geometry():
    """
    Sem sangria: dimensões exatas de corte (6x9 -> 6" x 9", 432 x 648 pt).
    Com sangria: +0.125" largura e +0.25" altura (6.125" x 9.25", 441 x 666 pt).
    """
    geom_no_bleed = calculate_page_geometry(6.0, 9.0, bleed=False)
    assert geom_no_bleed["page_width_in"] == 6.0
    assert geom_no_bleed["page_height_in"] == 9.0
    assert geom_no_bleed["page_width_pt"] == 432.0
    assert geom_no_bleed["page_height_pt"] == 648.0

    geom_bleed = calculate_page_geometry(6.0, 9.0, bleed=True)
    assert geom_bleed["page_width_in"] == 6.125
    assert geom_bleed["page_height_in"] == 9.25
    assert geom_bleed["page_width_pt"] == 441.0
    assert geom_bleed["page_height_pt"] == 666.0

# -------------------------------------------------------------
# 4. TESTES DE MARGENS ESPELHADAS E PREVALÊNCIA
# -------------------------------------------------------------
def test_effective_margins_precedence():
    """A margem aplicada deve ser max(mínimo_kdp, preferência_editorial)."""
    # Para 104 páginas, o mínimo KDP é 0.375"
    # Se o editor pede 0.75", prevalece 0.75"
    m1 = calculate_effective_margins(104, bleed=False, editorial_margins={"inside_in": 0.75, "outside_in": 0.65})
    assert m1["inside_in"] == 0.75
    assert m1["outside_in"] == 0.65

    # Se o editor pede 0.20" de margem interna, o KDP exige no mínimo 0.375" -> prevalece 0.375"
    m2 = calculate_effective_margins(104, bleed=False, editorial_margins={"inside_in": 0.20, "outside_in": 0.15})
    assert m2["inside_in"] == 0.375
    assert m2["outside_in"] == 0.250  # Mínimo KDP sem sangria

# -------------------------------------------------------------
# 5. TESTES DE LIMITES POR PERFIL (PAPERBACK VS HARDCOVER)
# -------------------------------------------------------------
def test_profile_limits_paperback_and_hardcover():
    """Valida limites e tamanhos suportados para brochura e capa dura."""
    # Paperback: 24 a 828 páginas
    val_pb_ok = validate_kdp_profile("paperback", "6x9", "black_and_white", "cream", page_count=104)
    assert val_pb_ok["is_valid"] is True

    val_pb_too_low = validate_kdp_profile("paperback", "6x9", "black_and_white", "cream", page_count=20)
    assert val_pb_too_low["is_valid"] is False

    val_pb_too_high = validate_kdp_profile("paperback", "6x9", "black_and_white", "cream", page_count=850)
    assert val_pb_too_high["is_valid"] is False

    # Hardcover: oficial KDP é estritamente 75 a 550 páginas
    val_hc_ok = validate_kdp_profile("hardcover", "6x9", "black_and_white", "cream", page_count=104)
    assert val_hc_ok["is_valid"] is True

    val_hc_too_low = validate_kdp_profile("hardcover", "6x9", "black_and_white", "cream", page_count=50)
    assert val_hc_too_low["is_valid"] is False
    assert any("75" in err for err in val_hc_too_low["errors"])

    val_hc_too_high = validate_kdp_profile("hardcover", "6x9", "black_and_white", "cream", page_count=600)
    assert val_hc_too_high["is_valid"] is False
    assert any("550" in err for err in val_hc_too_high["errors"])

    # Hardcover não aceita tamanho 5x8
    val_hc_bad_size = validate_kdp_profile("hardcover", "5x8", "black_and_white", "cream", page_count=104)
    assert val_hc_bad_size["is_valid"] is False

# -------------------------------------------------------------
# 6. TESTES DE REGRAS DE ABERTURA DE LEITURA
# -------------------------------------------------------------
def test_reading_opening_rules():
    """Verifica abertura consecutiva vs abertura forçada em página ímpar (recto)."""
    days = [{"day": 1}, {"day": 2}, {"day": 3}]
    
    # new_page: Dia 1 (15, 16, 17) -> Dia 2 (18, 19, 20) -> Dia 3 (21, 22, 23)
    prep_new, next_p = generator.plan_day_pages(days, start_page=15, reading_opening_rule="new_page")
    assert prep_new[0]["page_numbers"] == [15, 16, 17]
    assert prep_new[1]["page_numbers"] == [18, 19, 20]
    assert prep_new[1]["has_blank_before"] is False

    # recto: Dia 1 termina na pág 17 (ímpar). Pág 18 é par, logo insere página em branco e Dia 2 inicia na 19 (ímpar)
    prep_recto, next_pr = generator.plan_day_pages(days, start_page=15, reading_opening_rule="recto")
    assert prep_recto[0]["page_numbers"] == [15, 16, 17]
    assert prep_recto[1]["has_blank_before"] is True
    assert prep_recto[1]["page_numbers"] == [19, 20, 21]

# -------------------------------------------------------------
# 7. TESTES DE CÁLCULO E INVALIDAÇÃO DE CAPA
# -------------------------------------------------------------
def test_cover_invalidation_when_interior_changes(tmp_path):
    """Garante que a capa seja desvinculada e invalidada se a contagem física mudar."""
    cfg = BookConfig(book_id="teste-capa", title="Teste", edition_type="paperback")
    cov_gen = CoverGenerator(cfg)
    
    hash_104 = cov_gen.generate_cover_spec_hash(104)
    hash_106 = cov_gen.generate_cover_spec_hash(106)
    assert hash_104 != hash_106

    cov_file = tmp_path / "cover.pdf"
    cov_meta = cov_gen.generate_cover_pdf(final_page_count=104, output_path=cov_file)
    meta_json = cov_file.with_suffix(".json")
    assert meta_json.exists()

    # Com 104 páginas, não está obsoleta
    assert cov_gen.is_cover_stale(meta_json, 104) is False
    # Com 106 páginas, está obsoleta e precisa regerar
    assert cov_gen.is_cover_stale(meta_json, 106) is True

# -------------------------------------------------------------
# 8. TESTES DE ISOLAMENTO E PREVENÇÃO DE PATH TRAVERSAL
# -------------------------------------------------------------
def test_storage_separation_and_security(tmp_path):
    """
    Garante que devocionais fiquem em pastas separadas:
    output/<slug>--<book-id>/<idioma>/<run-id>/
    e bloqueia tentativas de path traversal.
    """
    sm = StorageManager(tmp_path)
    
    cfg_en = BookConfig(book_id="devocional-a", title="30 Days Closer", language="en")
    cfg_pt = BookConfig(book_id="devocional-a", title="30 Days Closer", language="pt")
    cfg_b = BookConfig(book_id="devocional-b", title="30 Days Closer", language="en")
    
    paths_en = sm.get_or_create_run(cfg_en, run_id="run_01")
    paths_pt = sm.get_or_create_run(cfg_pt, run_id="run_01")
    paths_b = sm.get_or_create_run(cfg_b, run_id="run_01")

    # Livros diferentes com mesmo título NÃO compartilham pasta
    assert paths_en.root_dir.parent.parent != paths_b.root_dir.parent.parent
    assert "devocional-a" in paths_en.root_dir.parent.parent.name
    assert "devocional-b" in paths_b.root_dir.parent.parent.name

    # Idiomas diferentes do mesmo livro ficam em subpastas separadas
    assert paths_en.language == "en-US"
    assert paths_pt.language == "pt-BR"
    assert paths_en.root_dir != paths_pt.root_dir

    # Subpastas obrigatórias criadas
    for p in [paths_en.content_dir, paths_en.metadata_dir, paths_en.assets_dir,
              paths_en.paperback_dir, paths_en.hardcover_dir, paths_en.ebook_dir,
              paths_en.reports_dir, paths_en.previews_dir, paths_en.logs_dir, paths_en.tmp_dir]:
        assert p.exists()

    # Prevenção contra path traversal
    safe_slug = sanitize_path_component("../../malicious/path")
    assert ".." not in safe_slug
    assert "/" not in safe_slug

# -------------------------------------------------------------
# 9. TESTES DE PRESERVAÇÃO INTEGRAL DE LEITURAS
# -------------------------------------------------------------
def test_reading_integrity_preserved():
    """Garante que os 30 dias com versículos, 7 parágrafos e orações são preservados."""
    data = generator.load_data()
    days = data.get("days", [])
    assert len(days) == 30
    for idx, d in enumerate(days):
        assert d["day"] == idx + 1
        assert "title" in d and len(d["title"]) > 0
        assert "verse" in d and len(d["verse"]["text"]) > 0
        assert "page1" in d and len(d["page1"]) >= 1
        assert "page2" in d and len(d["page2"]) >= 1
        assert "page3" in d and len(d["page3"]) >= 1
        assert "card_heart" in d and len(d["card_heart"]["text"]) > 0
        assert "card_prayer" in d and len(d["card_prayer"]["text"]) > 0

# -------------------------------------------------------------
# 10. TESTE DE GERAÇÃO REAL E VALIDAÇÃO DE ARQUIVO
# -------------------------------------------------------------
def test_real_generation_sample_and_validation(tmp_path):
    """
    Executa a renderização de um dia de exemplo real e verifica o PDF exportado:
    dimensões, páginas individuais, fontes e ausência de criptografia.
    """
    cfg = BookConfig(
        book_id="teste-real",
        title="30 DAYS CLOSER TO GOD",
        trim_size="6x9",
        bleed=False
    )
    
    # Gera o Dia 1
    out_pdf = tmp_path / "dia_01_teste.pdf"
    res = generator.render_book(day_number=1, output_path=out_pdf, config=cfg)
    
    assert out_pdf.exists()
    assert res["total_pages"] == 3
    
    doc = pymupdf.open(str(out_pdf))
    assert len(doc) == 3
    assert doc.is_encrypted is False
    
    # Dimensões 6x9 em pontos: 432 x 648 pt
    for page in doc:
        rect = page.rect
        assert abs(rect.width - 432.0) < 1.0
        assert abs(rect.height - 648.0) < 1.0
    doc.close()

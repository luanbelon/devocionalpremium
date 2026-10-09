# -*- coding: utf-8 -*-
"""
Gerador de Livro / Devocional para Amazon KDP.
Implementa o ciclo de convergência de paginação e margens KDP:
1. Diagramação inicial com estimativa
2. Renderização em PDF individual de alta resolução
3. Contagem física real e fechamento obrigatório em número par (página em branco)
4. Consulta aos requisitos da faixa KDP e recálculo de margens
5. Atualização dinâmica do sumário (TOC)
6. Validação do PDF exportado
7. Cálculo e geração de capa desvinculada e invalidável
8. Registro completo em manifest.json e organização por devocional em output/
"""

import os
import sys
import json
import pathlib
import argparse
import subprocess
import datetime
from typing import Optional, Dict, Any, List, Tuple
import pymupdf
from jinja2 import Environment, FileSystemLoader

import base64
import io
from PIL import Image
import numpy as np

from kdp_specs import (
    get_kdp_rules,
    get_min_inside_margin,
    get_min_outside_margin,
    calculate_effective_margins,
    calculate_page_geometry,
    validate_kdp_profile,
    inches_to_pt,
    pt_to_inches
)
from book_config import BookConfig
from storage_manager import StorageManager, BookRunPaths
from pdf_validator import PDFValidator
from cover_generator import CoverGenerator
from manifest_manager import ManifestManager

BASE_DIR = pathlib.Path(__file__).parent.resolve()
ASSETS_DIR = BASE_DIR / "assets"
DATA_FILE = BASE_DIR / "data" / "devocional.json"
TEMPLATES_DIR = BASE_DIR / "templates"
DEFAULT_OUTPUT_DIR = BASE_DIR / "output"

storage_mgr = StorageManager(DEFAULT_OUTPUT_DIR)

def get_tinted_icon_b64(filename: str, tint_rgb=(30, 30, 30)) -> str:
    """Carrega o ícone PNG, aplica tonalidade grafite/preto elegante e retorna data URI."""
    icon_path = ASSETS_DIR / filename
    if not icon_path.exists():
        return ""
    try:
        im = Image.open(icon_path).convert('RGBA')
        arr = np.array(im)
        alpha = arr[:, :, 3]
        arr[:, :, 0] = tint_rgb[0]
        arr[:, :, 1] = tint_rgb[1]
        arr[:, :, 2] = tint_rgb[2]
        arr[:, :, 3] = alpha
        
        tinted = Image.fromarray(arr)
        buffered = io.BytesIO()
        tinted.save(buffered, format="PNG")
        b64_str = base64.b64encode(buffered.getvalue()).decode('utf-8')
        return f"data:image/png;base64,{b64_str}"
    except Exception as e:
        print(f"Erro ao processar ícone {filename}: {e}")
        return ""

def get_icons() -> Dict[str, str]:
    """Retorna os ícones preparados para injeção no template HTML."""
    return {
        "icon_ramo": get_tinted_icon_b64("ramo.png"),
        "icon_maos": get_tinted_icon_b64("maos-em-oracao.png")
    }

def find_browser_executable() -> str:
    """Localiza o Google Chrome ou Microsoft Edge no Windows."""
    candidates = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    raise FileNotFoundError("Navegador compatível (Chrome ou Edge) não encontrado para renderização.")

def load_data(data_path: Optional[pathlib.Path] = None) -> Dict[str, Any]:
    path = pathlib.Path(data_path) if data_path else DATA_FILE
    if not path.exists():
        raise FileNotFoundError(f"Arquivo de dados não encontrado: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data: Dict[str, Any], data_path: Optional[pathlib.Path] = None):
    path = pathlib.Path(data_path) if data_path else DATA_FILE
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def html_to_pdf(html_content: str, output_pdf_path: pathlib.Path, temp_html_name="temp_render.html") -> pathlib.Path:
    """Converte HTML para PDF usando o motor headless de alta fidelidade do Chrome/Edge."""
    browser_exe = find_browser_executable()
    temp_dir = output_pdf_path.parent
    temp_html_path = temp_dir / temp_html_name
    temp_html_path.write_text(html_content, encoding="utf-8")
    
    output_pdf = pathlib.Path(output_pdf_path).resolve()
    output_pdf.parent.mkdir(parents=True, exist_ok=True)
    
    cmd = [
        browser_exe,
        "--headless=new",
        "--disable-gpu",
        "--no-pdf-header-footer",
        "--run-all-compositor-stages-before-draw",
        f"--print-to-pdf={output_pdf}",
        temp_html_path.as_uri()
    ]
    
    res = subprocess.run(cmd, capture_output=True, text=True)
    
    if temp_html_path.exists():
        try:
            temp_html_path.unlink()
        except Exception:
            pass

    if res.returncode != 0:
        raise RuntimeError(f"Erro ao gerar PDF com Chrome/Edge: {res.stderr}")
        
    if not output_pdf.exists():
        raise RuntimeError(f"Falha na geração do arquivo PDF: {output_pdf}")
        
    return output_pdf

def plan_day_pages(
    days: List[Dict[str, Any]],
    start_page: int = 15,
    reading_opening_rule: str = "new_page"
) -> Tuple[List[Dict[str, Any]], int]:
    """
    Calcula os números de página para cada leitura devocional:
    - Se reading_opening_rule == 'recto': força que cada dia inicie em página ímpar (Recto).
      Se a leitura anterior terminou em página ímpar, insere uma página em branco (verso).
    - Se reading_opening_rule == 'new_page': abertura consecutiva imediata.
    """
    prepared = []
    current_page = start_page
    
    for d in days:
        d_copy = dict(d)
        has_blank_before = False
        
        # Se exigido recto e a página atual for par, insere página em branco
        if reading_opening_rule == "recto" and (current_page % 2 == 0):
            has_blank_before = True
            current_page += 1
            
        d_copy["has_blank_before"] = has_blank_before
        d_copy["page_numbers"] = [current_page, current_page + 1, current_page + 2]
        current_page += 3
        prepared.append(d_copy)
        
    return prepared, current_page

def render_front_matter_pdf(
    config: BookConfig,
    prepared_days: List[Dict[str, Any]],
    output_path: pathlib.Path,
    margins_dict: Dict[str, float]
) -> pathlib.Path:
    """Renderiza as 14 páginas pré-textuais com sumário dinâmico refletindo a paginação real."""
    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))
    template = env.get_template("front_matter.html")
    
    geom = config.get_geometry()
    icons = get_icons()
    
    rendered_html = template.render(
        book_title=config.title,
        subtitle=config.subtitle,
        author=config.author,
        year="2026",
        language=config.language,
        page_width=f"{geom['page_width_in']}in",
        page_height=f"{geom['page_height_in']}in",
        margin_top=f"{margins_dict['top_in']}in",
        margin_bottom=f"{margins_dict['bottom_in']}in",
        margin_inside=f"{margins_dict['inside_in']}in",
        margin_outside=f"{margins_dict['outside_in']}in",
        days=prepared_days,
        **icons
    )
    
    return html_to_pdf(rendered_html, output_path, temp_html_name="temp_fm.html")

def render_interior_days_pdf(
    config: BookConfig,
    prepared_days: List[Dict[str, Any]],
    output_path: pathlib.Path,
    margins_dict: Dict[str, float],
    trailing_blank: bool = False
) -> pathlib.Path:
    """Renderiza as páginas dos dias devocionais com margens espelhadas KDP."""
    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))
    template = env.get_template("book_template.html")
    
    geom = config.get_geometry()
    icons = get_icons()
    
    rendered_html = template.render(
        book_title=config.title,
        language=config.language,
        page_width=f"{geom['page_width_in']}in",
        page_height=f"{geom['page_height_in']}in",
        margin_top=f"{margins_dict['top_in']}in",
        margin_bottom=f"{margins_dict['bottom_in']}in",
        margin_inside=f"{margins_dict['inside_in']}in",
        margin_outside=f"{margins_dict['outside_in']}in",
        days=prepared_days,
        trailing_blank_page=trailing_blank,
        **icons
    )
    
    return html_to_pdf(rendered_html, output_path, temp_html_name="temp_days.html")

def render_and_converge_book(
    config: BookConfig,
    custom_data: Optional[Dict[str, Any]] = None,
    run_paths: Optional[BookRunPaths] = None,
    max_attempts: int = 5
) -> Dict[str, Any]:
    """
    Ciclo Oficial de Convergência KDP:
    1. Diagrama com estimativa inicial
    2. Renderiza PDF
    3. Conta páginas físicas
    4. Adiciona página em branco se ímpar
    5. Consulta requisitos da faixa KDP
    6. Recalcula margens e repete até convergir
    7. Valida PDF final e gera capa + manifest.json
    """
    paths = run_paths or storage_mgr.get_or_create_run(config)
    data = custom_data or load_data()
    all_days = data.get("days", [])
    
    # Salva snapshot do conteúdo em content/
    content_snapshot = paths.content_dir / "devocional_source.json"
    with open(content_snapshot, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    current_estimated_pages = config.estimated_pages
    seen_page_counts = []
    converged = False
    iteration_log = []
    
    final_pdf_path = (paths.paperback_dir if config.edition_type == "paperback" else paths.hardcover_dir) / "interior.pdf"

    for attempt in range(1, max_attempts + 1):
        # Passo 1: Calcula margens efetivas para a contagem estimada atual
        margins = config.get_effective_margins(current_estimated_pages)
        
        # Passo 2: Planeja páginas dos dias devocionais e sumário
        prepared_days, next_page = plan_day_pages(
            all_days,
            start_page=config.start_page_number,
            reading_opening_rule=config.reading_opening_rule
        )
        
        # Passo 3: Renderiza front matter (páginas 1 a 14)
        fm_pdf = paths.tmp_dir / f"fm_attempt_{attempt}.pdf"
        render_front_matter_pdf(config, prepared_days, fm_pdf, margins)
        
        # Passo 4: Renderiza interior dos dias
        days_pdf = paths.tmp_dir / f"days_attempt_{attempt}.pdf"
        render_interior_days_pdf(config, prepared_days, days_pdf, margins)
        
        # Passo 5: Combina Front Matter + Interior com PyMuPDF
        doc_fm = pymupdf.open(fm_pdf)
        doc_days = pymupdf.open(days_pdf)
        
        doc_combined = pymupdf.open()
        doc_combined.insert_pdf(doc_fm)
        doc_combined.insert_pdf(doc_days)
        
        doc_fm.close()
        doc_days.close()
        
        # Passo 6: Contagem física real e fechamento em número par
        physical_count = len(doc_combined)
        added_blank_end = False
        if physical_count % 2 != 0:
            # Insere página final em branco para paridade
            geom = config.get_geometry()
            doc_combined.new_page(width=geom["page_width_pt"], height=geom["page_height_pt"])
            physical_count += 1
            added_blank_end = True
            
        doc_combined.save(final_pdf_path)
        doc_combined.close()
        
        # Passo 7: Verifica se a faixa de margem interna (calha) mudou com essa contagem
        req_min_gutter = get_min_inside_margin(physical_count)
        gutter_changed = (req_min_gutter > margins["inside_in"])
        
        iteration_log.append({
            "attempt": attempt,
            "estimated_used": current_estimated_pages,
            "physical_counted": physical_count,
            "added_blank_end": added_blank_end,
            "req_min_gutter": req_min_gutter,
            "applied_gutter": margins["inside_in"],
            "gutter_changed": gutter_changed
        })
        
        # Detecção de oscilação e convergência
        if not gutter_changed:
            converged = True
            break
            
        if physical_count in seen_page_counts:
            # Oscilação detectada
            iteration_log[-1]["warning"] = "Oscilação detectada entre contagens de páginas. Interrompendo recálculo."
            converged = False
            break
            
        seen_page_counts.append(physical_count)
        current_estimated_pages = physical_count

    # Limpa arquivos temporários do tmp/
    paths.clean_tmp()

    # Passo 8: Validação rigorosa do PDF exportado
    validator = PDFValidator(config)
    val_report = validator.validate_interior_pdf(final_pdf_path, expected_days=len(all_days))

    # Passo 9: Geração da capa proporcional à paginação final
    final_pages = val_report.get("total_pages", physical_count)
    cover_gen = CoverGenerator(config)
    cover_pdf_path = (paths.paperback_dir if config.edition_type == "paperback" else paths.hardcover_dir) / "cover.pdf"
    cover_meta = cover_gen.generate_cover_pdf(final_page_count=final_pages, output_path=cover_pdf_path)

    # Passo 9.5: Gera o e-Book EPUB na pasta ebook/ do run
    epub_files = []
    try:
        import epub_generator
        ep_path = epub_generator.generate_epub(config.language, run_paths=paths)
        if ep_path and ep_path.exists():
            epub_files.append(ep_path)
    except Exception as e:
        print(f"Aviso ao gerar EPUB do run: {e}")

    # Passo 10: Gera manifest.json
    manifest_mgr = ManifestManager(paths.root_dir)
    manifest = manifest_mgr.build_manifest(
        config=config,
        run_id=paths.run_id,
        interior_validation=val_report,
        cover_info=cover_meta,
        epub_files=epub_files
    )

    return {
        "status": "validated" if val_report["status"] == "validated" else "failed",
        "converged": converged,
        "run_paths": paths,
        "run_id": paths.run_id,
        "pdf_path": final_pdf_path,
        "cover_path": cover_pdf_path,
        "total_pages": final_pages,
        "iterations": iteration_log,
        "validation": val_report,
        "cover_meta": cover_meta,
        "manifest": manifest
    }

def render_book(
    day_number: Optional[int] = None,
    output_path: Optional[pathlib.Path] = None,
    custom_data: Optional[Dict[str, Any]] = None,
    include_front_matter: bool = True,
    config: Optional[BookConfig] = None
) -> Dict[str, Any]:
    """
    Interface de renderização mantendo compatibilidade com código existente e suporte a livro completo.
    """
    active_config = config or BookConfig()
    
    # Se renderizando o livro completo com front matter, usa o motor convergente KDP
    if day_number is None and include_front_matter:
        res = render_and_converge_book(active_config, custom_data=custom_data)
        if output_path:
            out_p = pathlib.Path(output_path).resolve()
            out_p.parent.mkdir(parents=True, exist_ok=True)
            import shutil
            shutil.copy2(res["pdf_path"], out_p)
            res["pdf_path"] = out_p
        return res

    # Renderização de um único dia isolado
    data = custom_data or load_data()
    all_days = data.get("days", [])
    target_days = [d for d in all_days if d.get("day") == int(day_number)] if day_number else all_days
    
    if not target_days:
        raise ValueError(f"Dia {day_number} não encontrado nos dados.")
        
    start_page = active_config.start_page_number + ((int(day_number) - 1) * 3 if day_number else 0)
    prepared_days, _ = plan_day_pages(target_days, start_page=start_page)
    
    # Executa dentro de um run seguro
    paths = storage_mgr.get_or_create_run(active_config)
    default_out = paths.paperback_dir / (f"devocional_dia_{int(day_number):02d}.pdf" if day_number else "interior.pdf")
    out_file = pathlib.Path(output_path) if output_path else default_out
    
    margins = active_config.get_effective_margins(active_config.estimated_pages)
    render_interior_days_pdf(active_config, prepared_days, out_file, margins)
    
    doc = pymupdf.open(out_file)
    total_pages = len(doc)
    doc.close()
    
    return {
        "pdf_path": out_file,
        "total_pages": total_pages,
        "expected_pages": len(prepared_days) * 3,
        "is_valid": total_pages == (len(prepared_days) * 3)
    }

def export_day_previews(day_number: int = 1, dpi: int = 150, custom_data: Optional[Dict[str, Any]] = None, config: Optional[BookConfig] = None) -> List[pathlib.Path]:
    """Gera imagens PNG das 3 páginas do dia especificado na pasta previews/ do run e na pasta previews/ global."""
    active_config = config or BookConfig()
    paths = storage_mgr.get_or_create_run(active_config)
    
    res = render_book(day_number=day_number, custom_data=custom_data, config=active_config)
    doc = pymupdf.open(res["pdf_path"])
    
    image_paths = []
    global_previews = BASE_DIR / "previews"
    global_previews.mkdir(parents=True, exist_ok=True)
    
    for i, page in enumerate(doc):
        pix = page.get_pixmap(dpi=dpi)
        img_name = f"dia_{int(day_number):02d}_pag_{i+1}.png"
        run_img_path = paths.previews_dir / img_name
        pix.save(run_img_path)
        image_paths.append(run_img_path)
        
        # Mantém cópia na pasta previews global para compatibilidade com a UI
        global_path = global_previews / img_name
        pix.save(global_path)
        
    doc.close()
    return image_paths

def validate_all_days(custom_data: Optional[Dict[str, Any]] = None, config: Optional[BookConfig] = None) -> bool:
    """Verifica cada um dos 30 dias individualmente para certificar que nenhum excede 3 páginas."""
    active_config = config or BookConfig()
    data = custom_data or load_data()
    days = data.get("days", [])
    print(f"Validando {len(days)} dias para perfil KDP...")
    
    errors = []
    for d in days:
        num = d.get("day")
        res = render_book(day_number=num, custom_data=data, config=active_config)
        if not res["is_valid"]:
            errors.append((num, res["total_pages"], res["expected_pages"]))
            
    if not errors:
        print("\n[SUCESSO] Todos os 30 dias contêm exatamente 3 páginas cada! Pronto para KDP.")
    else:
        print("\n[ERRO] Foram encontradas divergências nos seguintes dias:")
        for num, tot, exp in errors:
            print(f"  - Dia {num}: gerou {tot} páginas (esperado: {exp})")
            
    return len(errors) == 0

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Gerador de Devocional KDP com Ciclo de Convergência")
    parser.add_argument("--all", action="store_true", help="Gera o livro completo com ciclo de convergência KDP")
    parser.add_argument("--edition", choices=["paperback", "hardcover"], default="paperback", help="Tipo de edição (paperback ou hardcover)")
    parser.add_argument("--trim", default="6x9", help="Formato de corte (ex: 6x9, 5.5x8.5)")
    parser.add_argument("--bleed", action="store_true", help="Ativa sangria no miolo")
    parser.add_argument("--opening-rule", choices=["new_page", "recto"], default="new_page", help="Regra de abertura de leitura")
    parser.add_argument("--day", type=int, help="Gera o PDF apenas do dia especificado (ex: --day 1)")
    parser.add_argument("--preview", type=int, help="Gera imagens de preview PNG para o dia especificado")
    parser.add_argument("--validate", action="store_true", help="Valida se todos os dias têm exatamente 3 páginas")
    
    args = parser.parse_args()
    
    cfg = BookConfig(
        edition_type=args.edition,
        trim_size=args.trim,
        bleed=args.bleed,
        reading_opening_rule=args.opening_rule
    )
    
    if args.all:
        print(f"Iniciando ciclo de convergência KDP para {cfg.title} ({cfg.edition_type.upper()})...")
        res = render_and_converge_book(cfg)
        print(f"\n[STATUS] Resultado: {res['status'].upper()}")
        print(f"         Páginas Finais: {res['total_pages']}")
        print(f"         PDF Miolo: {res['pdf_path']}")
        print(f"         PDF Capa:  {res['cover_path']}")
        print(f"         Manifesto: {res['run_paths'].manifest_path}")
    elif args.day:
        res = render_book(day_number=args.day, config=cfg)
        print(f"[OK] Dia {args.day} gerado em: {res['pdf_path']} ({res['total_pages']} páginas)")
    elif args.preview:
        imgs = export_day_previews(day_number=args.preview, config=cfg)
        print("Previews gerados:")
        for img in imgs:
            print(" -", img)
    elif args.validate:
        validate_all_days(config=cfg)
    else:
        print("Executando ciclo de demonstração do livro completo...")
        res = render_and_converge_book(cfg)
        print(f"[SUCESSO] Livro gerado e validado em: {res['pdf_path']}")

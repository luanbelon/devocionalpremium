# -*- coding: utf-8 -*-
"""
Gerador de PDF de Alta Precisão para Livro Devocional KDP (Amazon).
Gera exatamente 3 páginas por dia com tipografia elegante e especificações KDP.
"""

import os
import sys
import json
import pathlib
import argparse
import subprocess
import pymupdf
from jinja2 import Environment, FileSystemLoader

import base64
import io
from PIL import Image
import numpy as np

BASE_DIR = pathlib.Path(__file__).parent.resolve()
ASSETS_DIR = BASE_DIR / "assets"
DATA_FILE = BASE_DIR / "data" / "devocional.json"
TEMPLATES_DIR = BASE_DIR / "templates"
OUTPUT_DIR = BASE_DIR / "output"
PREVIEWS_DIR = BASE_DIR / "previews"

OUTPUT_DIR.mkdir(exist_ok=True)
PREVIEWS_DIR.mkdir(exist_ok=True)

def get_tinted_icon_b64(filename, tint_rgb=(30, 30, 30)):
    """Carrega o ícone PNG fornecido pelo usuário, aplica a tonalidade preto/grafite e retorna data URI base64."""
    icon_path = ASSETS_DIR / filename
    if not icon_path.exists():
        return ""
    try:
        im = Image.open(icon_path).convert('RGBA')
        arr = np.array(im)
        alpha = arr[:, :, 3]
        # Aplica a cor em tons de grafite/preto preservando o canal alfa
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

def get_icons():
    """Retorna os ícones de ramo e mãos em oração em preto/grafite elegante."""
    return {
        "icon_ramo": get_tinted_icon_b64("ramo.png"),
        "icon_maos": get_tinted_icon_b64("maos-em-oracao.png")
    }

def find_browser_executable():
    """Localiza o executável do Google Chrome ou Microsoft Edge no Windows."""
    candidates = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    raise FileNotFoundError("Nem o Google Chrome nem o Microsoft Edge foram encontrados no sistema.")

def load_data(data_path=None):
    path = pathlib.Path(data_path) if data_path else DATA_FILE
    if not path.exists():
        raise FileNotFoundError(f"Arquivo de dados não encontrado: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data, data_path=None):
    path = pathlib.Path(data_path) if data_path else DATA_FILE
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def prepare_days_data(days, start_page=15):
    """Calcula os números de página para cada dia (3 páginas por dia)."""
    prepared = []
    current_page = start_page
    for d in days:
        d_copy = dict(d)
        d_copy["page_numbers"] = [current_page, current_page + 1, current_page + 2]
        current_page += 3
        prepared.append(d_copy)
    return prepared

def html_to_pdf(html_content, output_pdf_path, temp_html_name="temp_render.html"):
    """Converte HTML para PDF usando o motor headless de alta fidelidade do Chrome/Edge."""
    browser_exe = find_browser_executable()
    temp_html_path = BASE_DIR / temp_html_name
    temp_html_path.write_text(html_content, encoding="utf-8")
    
    output_pdf = pathlib.Path(output_pdf_path).resolve()
    
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
    
    # Limpa o arquivo HTML temporário
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

def render_front_matter(data, output_path=None):
    """Gera as 14 páginas pré-textuais (falso rosto, folha de rosto, ficha, dedicatória, intro, sumário)."""
    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))
    template = env.get_template("front_matter.html")
    
    trim_size = data.get("trim_size", "6x9")
    page_width, page_height = ("5.5in", "8.5in") if trim_size == "5.5x8.5" else ("6in", "9in")
    
    all_days = data.get("days", [])
    prepared_days = prepare_days_data(all_days, start_page=data.get("start_page_number", 15))
    
    icons = get_icons()
    rendered_html = template.render(
        book_title=data.get("book_title", "30 DAYS CLOSER TO GOD"),
        subtitle=data.get("subtitle", "A daily journey of faith, prayer, and intimacy with God"),
        author=data.get("author", "Lyan Davis"),
        year="2026",
        language=data.get("language", "en"),
        page_width=page_width,
        page_height=page_height,
        days=prepared_days,
        **icons
    )
    
    out_file = pathlib.Path(output_path) if output_path else OUTPUT_DIR / "front_matter.pdf"
    pdf_path = html_to_pdf(rendered_html, out_file, temp_html_name="temp_fm.html")
    return pdf_path

def render_book(day_number=None, output_path=None, custom_data=None, include_front_matter=False):
    """
    Renderiza o livro completo (todos os 30 dias) ou apenas um dia específico.
    day_number: int (1 a 30) ou None para todos os dias.
    include_front_matter: bool, inclui páginas 1 a 14 se True.
    """
    data = custom_data or load_data()
    all_days = data.get("days", [])
    
    if day_number is not None:
        target_days = [d for d in all_days if d.get("day") == int(day_number)]
        if not target_days:
            raise ValueError(f"Dia {day_number} não encontrado nos dados.")
        start_page = data.get("start_page_number", 15) + (int(day_number) - 1) * 3
        prepared_days = prepare_days_data(target_days, start_page=start_page)
        default_out = OUTPUT_DIR / f"devocional_dia_{int(day_number):02d}.pdf"
    else:
        prepared_days = prepare_days_data(all_days, start_page=data.get("start_page_number", 15))
        default_out = OUTPUT_DIR / "devocional_30_dias_kdp.pdf"

    out_file = pathlib.Path(output_path) if output_path else default_out
    
    # Setup Jinja2
    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))
    template = env.get_template("book_template.html")
    
    trim_size = data.get("trim_size", "6x9")
    page_width, page_height = ("5.5in", "8.5in") if trim_size == "5.5x8.5" else ("6in", "9in")
    
    icons = get_icons()
    rendered_html = template.render(
        book_title=data.get("book_title", "30 DAYS CLOSER TO GOD"),
        language=data.get("language", "en"),
        page_width=page_width,
        page_height=page_height,
        days=prepared_days,
        **icons
    )
    
    # Se solicitado front matter e for o livro completo, junta os dois
    if include_front_matter and day_number is None:
        temp_interior = OUTPUT_DIR / "temp_interior.pdf"
        html_to_pdf(rendered_html, temp_interior, temp_html_name="temp_book.html")
        fm_pdf = render_front_matter(data)
        
        doc_fm = pymupdf.open(fm_pdf)
        doc_int = pymupdf.open(temp_interior)
        
        doc_final = pymupdf.open()
        doc_final.insert_pdf(doc_fm)
        doc_final.insert_pdf(doc_int)
        
        doc_final.save(out_file)
        
        doc_fm.close()
        doc_int.close()
        doc_final.close()
        
        for p in (fm_pdf, temp_interior):
            if p.exists():
                try:
                    p.unlink()
                except Exception:
                    pass
    else:
        temp_name = f"temp_day_{day_number}.html" if day_number else "temp_book.html"
        html_to_pdf(rendered_html, out_file, temp_html_name=temp_name)

    # Validação com PyMuPDF
    doc = pymupdf.open(out_file)
    total_pages = len(doc)
    page_width = doc[0].rect.width
    page_height = doc[0].rect.height
    doc.close()
    
    expected_pages = (14 if (include_front_matter and day_number is None) else 0) + len(prepared_days) * 3
    is_valid = (total_pages == expected_pages)
    
    print(f"[OK] PDF gerado em: {out_file}")
    print(f"     Páginas geradas: {total_pages} (Esperado: {expected_pages})")
    print(f"     Dimensões da página: {page_width:.1f} x {page_height:.1f} pt")
    
    if not is_valid:
        print(f"[ALERTA] Divergência na contagem de páginas! Esperado {expected_pages}, mas foram geradas {total_pages}.")
        
    return {
        "pdf_path": out_file,
        "total_pages": total_pages,
        "expected_pages": expected_pages,
        "is_valid": is_valid
    }

def export_day_previews(day_number=1, dpi=150, custom_data=None):
    """Gera imagens PNG das 3 páginas do dia especificado para preview visual imediato."""
    result = render_book(day_number=day_number, custom_data=custom_data)
    pdf_path = result["pdf_path"]
    doc = pymupdf.open(pdf_path)
    
    image_paths = []
    for i, page in enumerate(doc):
        pix = page.get_pixmap(dpi=dpi)
        img_name = f"dia_{int(day_number):02d}_pag_{i+1}.png"
        img_path = PREVIEWS_DIR / img_name
        pix.save(img_path)
        image_paths.append(img_path)
    doc.close()
        
    return image_paths

def validate_all_days(custom_data=None):
    """Verifica cada um dos 30 dias individualmente para certificar que nenhum excede 3 páginas."""
    data = custom_data or load_data()
    days = data.get("days", [])
    print(f"Validando {len(days)} dias...")
    
    errors = []
    for d in days:
        num = d.get("day")
        res = render_book(day_number=num, custom_data=data)
        if not res["is_valid"]:
            errors.append((num, res["total_pages"], res["expected_pages"]))
            
    if not errors:
        print("\n[SUCESSO] Todos os 30 dias têm exatamente 3 páginas cada! Pronto para KDP.")
    else:
        print("\n[ERRO] Foram encontradas divergências nos seguintes dias:")
        for num, tot, exp in errors:
            print(f"  - Dia {num}: gerou {tot} páginas (esperado: {exp})")
            
    return len(errors) == 0

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Gerador de Devocional KDP 30 Dias (3 Páginas/Dia)")
    parser.add_argument("--all", action="store_true", help="Gera o PDF completo com todos os 30 dias")
    parser.add_argument("--front-matter", action="store_true", help="Inclui páginas pré-textuais (1 a 14) junto com o livro completo")
    parser.add_argument("--day", type=int, help="Gera o PDF apenas do dia especificado (ex: --day 1)")
    parser.add_argument("--preview", type=int, help="Gera imagens de preview PNG para o dia especificado")
    parser.add_argument("--validate", action="store_true", help="Valida se todos os dias têm exatamente 3 páginas")
    
    args = parser.parse_args()
    
    if args.all:
        render_book(include_front_matter=args.front_matter)
    elif args.day:
        render_book(day_number=args.day)
    elif args.preview:
        imgs = export_day_previews(day_number=args.preview)
        print("Imagens de preview geradas:")
        for img in imgs:
            print(" -", img)
    elif args.validate:
        validate_all_days()
    else:
        print("Gerando Exemplo 1 (Dia 1 - 3 páginas)...")
        res = render_book(day_number=1, output_path=OUTPUT_DIR / "devocional_exemplo_1.pdf")
        imgs = export_day_previews(day_number=1)
        print(f"[OK] Exemplo 1 gerado com sucesso em: {res['pdf_path']}")
        print("Páginas geradas:")
        for img in imgs:
            print(" -", img)

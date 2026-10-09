# -*- coding: utf-8 -*-
"""
Gerador de e-Book EPUB de Alta Fidelidade para Amazon Kindle / KDP e Leitores Digitais.
Suporta edições em Inglês e Português com navegação estruturada (EPUB 3 + NCX).
"""

import os
import io
import json
import uuid
import pathlib
import argparse
from ebooklib import epub
from PIL import Image
import numpy as np

BASE_DIR = pathlib.Path(__file__).parent.resolve()
DATA_DIR = BASE_DIR / "data"
ASSETS_DIR = BASE_DIR / "assets"
OUTPUT_DIR = BASE_DIR / "output"

OUTPUT_DIR.mkdir(exist_ok=True)

def get_tinted_png_bytes(filename, tint_rgb=(30, 30, 30)):
    """Carrega o ícone PNG e aplica a tonalidade preto/grafite elegante."""
    icon_path = ASSETS_DIR / filename
    if not icon_path.exists():
        return None
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
        return buffered.getvalue()
    except Exception as e:
        print(f"Erro ao processar ícone {filename}: {e}")
        return None

EPUB_CSS = """
@charset "utf-8";

body {
    margin: 5% 8%;
    padding: 0;
    font-family: "EB Garamond", Garamond, Georgia, "Times New Roman", serif;
    color: #1a1a1a;
    background-color: transparent;
    line-height: 1.65;
    text-rendering: optimizeLegibility;
}

h1, h2, h3, h4 {
    font-weight: 600;
    line-height: 1.25;
    text-align: center;
    color: #111111;
}

.title-page-container {
    text-align: center;
    margin-top: 15%;
    margin-bottom: 20%;
}

.main-book-title {
    font-size: 2.2em;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    margin-bottom: 0.4em;
    color: #000000;
}

.main-subtitle {
    font-size: 1.15em;
    font-style: italic;
    color: #444444;
    margin-bottom: 2em;
}

.main-author {
    font-size: 1.1em;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: #222222;
    margin-top: 2em;
}

.day-badge-container {
    text-align: center;
    margin-top: 1em;
    margin-bottom: 0.8em;
}

.day-badge {
    display: inline-block;
    padding: 3px 18px;
    border: 1px solid #888888;
    border-radius: 9px;
    background-color: #f2f2f2;
    font-size: 0.8em;
    font-weight: bold;
    letter-spacing: 0.18em;
    color: #111111;
    text-transform: uppercase;
}

.day-title {
    font-size: 1.85em;
    margin-bottom: 0.5em;
    color: #000000;
}

.title-ornament {
    text-align: center;
    margin-bottom: 1.2em;
}

.title-ornament img {
    width: 32px;
    height: auto;
    display: inline-block;
}

.scripture-card {
    background-color: #f5f5f5;
    border: 1px solid #dddddd;
    border-radius: 8px;
    padding: 1.2em 1.5em;
    margin: 1.4em 0 1.8em 0;
    text-align: center;
}

.scripture-text {
    font-style: italic;
    font-size: 1.05em;
    line-height: 1.5;
    color: #111111;
    margin-bottom: 0.6em;
}

.scripture-ref {
    font-size: 0.8em;
    font-weight: bold;
    letter-spacing: 0.2em;
    color: #444444;
    text-transform: uppercase;
}

.paragraph {
    text-align: justify;
    text-indent: 1.5em;
    margin: 0 0 0.8em 0;
    line-height: 1.7;
}

.paragraph-first {
    text-indent: 0;
}

.dropcap {
    float: left;
    font-size: 3.2em;
    line-height: 0.75;
    padding-top: 4px;
    padding-right: 8px;
    padding-bottom: 2px;
    color: #000000;
    font-weight: bold;
}

.action-cards {
    margin-top: 2em;
    margin-bottom: 2em;
}

.action-card {
    background-color: #f5f5f5;
    border: 1px solid #dddddd;
    border-radius: 8px;
    padding: 1.1em 1.3em;
    margin-bottom: 1.2em;
}

.action-header {
    margin-bottom: 0.5em;
    display: flex;
    align-items: center;
}

.action-icon-img {
    width: 24px;
    height: auto;
    vertical-align: middle;
    margin-right: 10px;
    display: inline-block;
}

.action-title {
    font-size: 0.8em;
    font-weight: bold;
    letter-spacing: 0.16em;
    color: #111111;
    text-transform: uppercase;
    display: inline-block;
    vertical-align: middle;
}

.action-desc {
    font-size: 0.98em;
    line-height: 1.55;
    color: #222222;
    font-style: italic;
    text-align: justify;
    margin: 0;
    text-indent: 0;
}

.copyright-box {
    margin-top: 25%;
    font-size: 0.85em;
    line-height: 1.6;
    color: #444444;
    text-align: center;
}

.dedication-box {
    margin-top: 30%;
    font-style: italic;
    font-size: 1.15em;
    line-height: 1.7;
    text-align: center;
    color: #222222;
    padding: 0 10%;
}

.epigraph-box {
    margin-top: 30%;
    text-align: center;
    padding: 0 8%;
}

.epigraph-text {
    font-style: italic;
    font-size: 1.25em;
    line-height: 1.6;
    margin-bottom: 0.8em;
}

.epigraph-ref {
    font-size: 0.85em;
    letter-spacing: 0.2em;
    color: #555555;
    text-transform: uppercase;
}

.intro-heading {
    font-size: 1.5em;
    margin-top: 1.5em;
    margin-bottom: 0.8em;
    text-align: center;
}
"""

def generate_epub(language="en", output_path=None, run_paths=None):
    """Gera o arquivo EPUB profissional completo para o idioma especificado ('en' ou 'pt')."""
    data_file = DATA_DIR / ("devocional_en.json" if language == "en" else "devocional_pt.json")
    if not data_file.exists():
        data_file = DATA_DIR / "devocional.json"
        
    with open(data_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    book = epub.EpubBook()
    
    book_id = str(uuid.uuid4())
    book.set_identifier(book_id)
    
    title = data.get("book_title", "30 Days Closer to God" if language == "en" else "30 Dias Mais Perto de Deus")
    # Title Case para metadados
    title_display = title.title()
    subtitle = data.get("subtitle", "A daily journey of faith, prayer, and intimacy with God" if language == "en" else "Uma jornada diária de fé, oração e intimidade com Deus")
    author = data.get("author", "Lyan Davis")
    
    book.set_title(title_display)
    book.set_language(language)
    book.add_author(author)
    book.add_metadata('DC', 'description', subtitle)
    book.add_metadata('DC', 'publisher', author)
    book.add_metadata('DC', 'subject', 'Christian Devotional')

    # CSS
    css_item = epub.EpubItem(
        uid="style_default",
        file_name="style/style.css",
        media_type="text/css",
        content=EPUB_CSS
    )
    book.add_item(css_item)

    # Imagens dos Ícones
    ramo_bytes = get_tinted_png_bytes("ramo.png")
    maos_bytes = get_tinted_png_bytes("maos-em-oracao.png")
    
    if ramo_bytes:
        img_ramo = epub.EpubItem(
            uid="img_ramo",
            file_name="images/ramo.png",
            media_type="image/png",
            content=ramo_bytes
        )
        book.add_item(img_ramo)
        
    if maos_bytes:
        img_maos = epub.EpubItem(
            uid="img_maos",
            file_name="images/maos.png",
            media_type="image/png",
            content=maos_bytes
        )
        book.add_item(img_maos)

    spine = ['nav']
    toc = []

    # 1. PÁGINA DE TÍTULO (Folha de Rosto)
    c_title = epub.EpubHtml(title="Title Page" if language == "en" else "Folha de Rosto", file_name="titlepage.xhtml", lang=language)
    c_title.add_item(css_item)
    c_title.content = f"""
    <div class="title-page-container">
        <h1 class="main-book-title">{title}</h1>
        <p class="main-subtitle">{subtitle}</p>
        <div class="title-ornament"><img src="images/ramo.png" alt="Ornament"/></div>
        <p class="main-author">{author}</p>
    </div>
    """
    book.add_item(c_title)
    spine.append(c_title)

    # 2. PÁGINA DE COPYRIGHT
    c_copy = epub.EpubHtml(title="Copyright", file_name="copyright.xhtml", lang=language)
    c_copy.add_item(css_item)
    if language == "en":
        copy_html = f"""
        <div class="copyright-box">
            <p><strong>Copyright &copy; 2026 by {author}</strong></p>
            <p>All rights reserved. No part of this publication may be reproduced, distributed, or transmitted in any form or by any means without the prior written permission of the author.</p>
            <p>Scripture summaries and paraphrases are authorial reflections designed for personal devotional reading, unless otherwise noted.</p>
        </div>
        """
    else:
        copy_html = f"""
        <div class="copyright-box">
            <p><strong>Copyright &copy; 2026 por {author}</strong></p>
            <p>Todos os direitos reservados. Nenhuma parte desta publicação pode ser reproduzida, distribuída ou transmitida por qualquer meio sem prévia autorização por escrito do autor.</p>
            <p>Textos bíblicos citados com base na versão Almeida Revista e Atualizada (ARA) e Nova Versão Internacional (NVI), salvo indicação em contrário.</p>
        </div>
        """
    c_copy.content = copy_html
    book.add_item(c_copy)
    spine.append(c_copy)

    # 3. DEDICATÓRIA
    c_ded = epub.EpubHtml(title="Dedication" if language == "en" else "Dedicatória", file_name="dedication.xhtml", lang=language)
    c_ded.add_item(css_item)
    ded_text = (
        "“To all who seek a daily refuge of peace and renewal in the presence of the Father. May every page of this devotional be a loving invitation to walk closer with God.”"
        if language == "en" else
        "“A todos os que buscam um refúgio diário de paz e renovação na presença do Pai. Que cada página deste devocional seja um convite amoroso a caminhar mais perto de Deus.”"
    )
    c_ded.content = f"""
    <div class="dedication-box">
        <p>{ded_text}</p>
    </div>
    """
    book.add_item(c_ded)
    spine.append(c_ded)

    # 4. EPÍGRAFE
    c_epi = epub.EpubHtml(title="Epigraph" if language == "en" else "Epígrafe", file_name="epigraph.xhtml", lang=language)
    c_epi.add_item(css_item)
    if language == "en":
        c_epi.content = """
        <div class="epigraph-box">
            <p class="epigraph-text">“Your word is a lamp to my feet and a light to my path.”</p>
            <p class="epigraph-ref">PSALM 119:105</p>
        </div>
        """
    else:
        c_epi.content = """
        <div class="epigraph-box">
            <p class="epigraph-text">“Lâmpada para os meus pés é a tua palavra e luz, para o meu caminho.”</p>
            <p class="epigraph-ref">SALMO 119:105</p>
        </div>
        """
    book.add_item(c_epi)
    spine.append(c_epi)

    # 5. INTRODUÇÃO
    c_intro = epub.EpubHtml(title="Introduction" if language == "en" else "Introdução", file_name="introduction.xhtml", lang=language)
    c_intro.add_item(css_item)
    if language == "en":
        c_intro.content = """
        <div>
            <h2 class="intro-heading">How to Use This Devotional</h2>
            <p class="paragraph paragraph-first">The Christian life is not a sprint, but a pilgrimage of steady faithfulness. In a daily routine filled with demands, noise, and distractions, setting aside a quiet moment alone with God is the secret to keeping your heart anchored in peace.</p>
            <p class="paragraph">This devotional is crafted with a thoughtful 30-day journey, where each day guides your spirit through three essential steps:</p>
            <p class="paragraph"><strong>1. Scripture Foundation:</strong> Each day opens with a central verse and reflection that invites you to draw near to God exactly where you are.</p>
            <p class="paragraph"><strong>2. Deeper Reflection:</strong> Timeless biblical truth meets the real dilemmas, quiet anxieties, and honest questions of everyday life through the lens of divine grace.</p>
            <p class="paragraph"><strong>3. Heart Takeaway and Prayer:</strong> Each day concludes with a memorable truth to keep in your heart, alongside an honest prayer to seal your daily dialogue with the Creator.</p>
            
            <h2 class="intro-heading" style="margin-top: 2em;">Guidance for Your Journey</h2>
            <p class="paragraph paragraph-first">• <strong>Set aside a dedicated time:</strong> Whether early in the morning or before resting at night, reserve ten to fifteen quiet minutes away from screens and notifications.</p>
            <p class="paragraph">• <strong>Read unhurriedly:</strong> Allow the words to resonate quietly in your mind. It is far better to meditate deeply on a single thought than to rush through without absorbing it.</p>
            <p class="paragraph">• <strong>Pray in your own words:</strong> The prayer provided at the end of each day is a starting point. Feel free to open your heart to God with complete honesty.</p>
            <p class="paragraph" style="margin-top: 1.5em; font-style: italic; text-align: center;">May the Lord enlighten the eyes of your heart and renew your strength each morning of this blessed journey.</p>
        </div>
        """
    else:
        c_intro.content = """
        <div>
            <h2 class="intro-heading">Como usar este devocional</h2>
            <p class="paragraph paragraph-first">A vida cristã não é uma corrida de velocidade, mas uma peregrinação de constância e fidelidade. Em um cotidiano repleto de demandas, ruídos e preocupações, cultivar um momento diário a sós com Deus é o segredo para manter o coração ancorado na paz.</p>
            <p class="paragraph">Este devocional foi concebido com uma estrutura cuidadosa de 30 dias, onde cada dia guia o seu espírito em três etapas essenciais:</p>
            <p class="paragraph"><strong>1. Ancoragem Bíblica:</strong> Cada dia começa com um versículo central e uma reflexão que convida você a se aproximar de Deus exatamente onde você está.</p>
            <p class="paragraph"><strong>2. Aprofundamento e Conexão:</strong> A verdade bíblica confronta dilemas cotidianos e ansiedades com promessas eternas da graça divina.</p>
            <p class="paragraph"><strong>3. Aplicação e Oração:</strong> Fechamos o dia com uma mensagem memorável para guardar no coração, além de uma oração sincera com o Criador.</p>
            
            <h2 class="intro-heading" style="margin-top: 2em;">Dicas para sua jornada</h2>
            <p class="paragraph paragraph-first">• <strong>Escolha um momento sagrado:</strong> Seja pela manhã cedo ou antes de dormir, separe de dez a quinze minutos sem interrupções de telas ou notificações.</p>
            <p class="paragraph">• <strong>Leia sem pressa:</strong> Permita que as palavras ecoem em sua mente. Mais vale meditar profundamente em um único parágrafo do que ler apressadamente sem absorver.</p>
            <p class="paragraph">• <strong>Ore com as suas próprias palavras:</strong> A oração sugerida ao final de cada dia serve como ponto de partida. Sinta-se livre para derramar seu coração diante de Deus.</p>
            <p class="paragraph" style="margin-top: 1.5em; font-style: italic; text-align: center;">Que o Senhor ilumine os seus olhos espirituais e renove as suas forças a cada manhã desta abençoada caminhada.</p>
        </div>
        """
    book.add_item(c_intro)
    spine.append(c_intro)
    toc.append(c_intro)

    # 6. CAPÍTULOS DOS 30 DIAS
    badge_label = "DAY" if language == "en" else "DIA"
    
    # Ingestão de todos os 7 parágrafos
    for day_data in data.get("days", []):
        day_num = day_data["day"]
        day_title = day_data["title"]
        verse = day_data["verse"]
        card_heart = day_data["card_heart"]
        card_prayer = day_data["card_prayer"]
        
        # Junta todos os parágrafos de reflexão mantendo a ordem rigorosa
        all_paragraphs = []
        if "page1" in day_data and "page2" in day_data and "page3" in day_data:
            all_paragraphs = day_data["page1"] + day_data["page2"] + day_data["page3"]
        elif "reflexao" in day_data:
            all_paragraphs = day_data["reflexao"]
            
        day_html = []
        day_html.append(f"""
        <div class="day-badge-container">
            <span class="day-badge">{badge_label} {day_num}</span>
        </div>
        <h1 class="day-title">{day_title}</h1>
        <div class="title-ornament"><img src="images/ramo.png" alt="Ramo"/></div>
        
        <div class="scripture-card">
            <div class="scripture-text">“{verse['text']}”</div>
            <div class="scripture-ref">{verse['reference']}</div>
        </div>
        """)
        
        # Parágrafos
        for idx, p in enumerate(all_paragraphs):
            if idx == 0:
                first_letter = p[0]
                rest = p[1:]
                day_html.append(f'<p class="paragraph paragraph-first"><span class="dropcap">{first_letter}</span>{rest}</p>')
            else:
                day_html.append(f'<p class="paragraph">{p}</p>')
                
        # Boxes de Ação
        day_html.append(f"""
        <div class="action-cards">
            <div class="action-card">
                <div class="action-header">
                    <img src="images/ramo.png" class="action-icon-img" alt="Icon"/>
                    <span class="action-title">{card_heart['title']}</span>
                </div>
                <p class="action-desc">{card_heart['text']}</p>
            </div>
            
            <div class="action-card">
                <div class="action-header">
                    <img src="images/maos.png" class="action-icon-img" alt="Icon"/>
                    <span class="action-title">{card_prayer['title']}</span>
                </div>
                <p class="action-desc">{card_prayer['text']}</p>
            </div>
        </div>
        """)
        
        chapter_title = f"{badge_label} {day_num}: {day_title}"
        c_day = epub.EpubHtml(
            title=chapter_title,
            file_name=f"day_{day_num:02d}.xhtml",
            lang=language
        )
        c_day.add_item(css_item)
        c_day.content = "".join(day_html)
        
        book.add_item(c_day)
        spine.append(c_day)
        toc.append(c_day)

    # Configuração de Navegação e Sumário
    book.toc = tuple(toc)
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    book.spine = spine

    # Caminho final
    filename = "30_Days_Closer_to_God.epub" if language == "en" else "30_Dias_Mais_Perto_de_Deus.epub"
    if output_path:
        out_file = pathlib.Path(output_path).resolve()
    elif run_paths:
        out_file = run_paths.ebook_dir / filename
    else:
        out_file = OUTPUT_DIR / filename
        
    out_file.parent.mkdir(parents=True, exist_ok=True)
    epub.write_epub(str(out_file), book, {})
    print(f"[OK] e-Book EPUB ({language.upper()}) gerado com sucesso em:\n     {out_file}")
    return out_file

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Gerador de e-Book EPUB para Amazon KDP")
    parser.add_argument("--lang", choices=["en", "pt", "all"], default="all", help="Idioma do EPUB ('en', 'pt' ou 'all')")
    parser.add_argument("--output", type=str, help="Caminho de saída personalizado")
    
    args = parser.parse_args()
    
    if args.lang in ["en", "all"]:
        generate_epub("en", args.output if args.lang == "en" else None)
    if args.lang in ["pt", "all"]:
        generate_epub("pt", args.output if args.lang == "pt" else None)

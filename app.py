# -*- coding: utf-8 -*-
"""
Painel Interativo de Gestão, Configuração KDP e Geração de Devocionais.
Implementa:
- Especificações oficiais da Amazon KDP com validação por formato e páginas reais
- Organização em pasta própria por devocional: output/<slug>--<book-id>/<idioma>/<run-id>/
- Ciclo de convergência de margens espelhadas e paginação com fechamento par
- Geração de miolo, capa calculada e e-Books EPUB preservados
- Inspeção e download de manifest.json com hashes SHA-256
"""

import os
import json
import pathlib
import streamlit as st
import pymupdf

import generator
import epub_generator
from book_config import BookConfig
from storage_manager import StorageManager, sanitize_path_component
from kdp_specs import get_kdp_rules

BASE_DIR = pathlib.Path(__file__).parent.resolve()
OUTPUT_DIR = BASE_DIR / "output"
PREVIEWS_DIR = BASE_DIR / "previews"
storage_mgr = StorageManager(OUTPUT_DIR)

st.set_page_config(
    page_title="Sistema Devocional KDP - 30 Dias",
    page_icon="📖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilização visual acolhedora e profissional
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@500;700&family=Cormorant+Garamond:wght@400;600&family=Inter:wght@300;400;500;600&display=swap');

    .main {
        background-color: #FAF8F5;
    }
    
    .stApp {
        background-color: #FAF8F5;
    }
    
    h1, h2, h3 {
        font-family: 'Cormorant Garamond', Georgia, serif;
        color: #2D231E;
    }

    .main-title {
        font-family: 'Cormorant Garamond', Georgia, serif;
        font-size: 2.8rem;
        font-weight: 700;
        color: #2D231E;
        text-align: center;
        margin-bottom: 0.2rem;
    }
    
    .main-subtitle {
        font-family: 'Inter', sans-serif;
        font-size: 1.05rem;
        color: #7D6B5D;
        text-align: center;
        margin-bottom: 2rem;
    }

    .metric-card {
        background-color: #FFFFFF;
        border: 1px solid #E8DFD5;
        border-radius: 12px;
        padding: 1.2rem;
        text-align: center;
        box-shadow: 0 2px 8px rgba(0,0,0,0.03);
    }
    
    .metric-value {
        font-family: 'Cinzel', serif;
        font-size: 2rem;
        font-weight: 700;
        color: #AF885E;
    }
    
    .metric-label {
        font-size: 0.85rem;
        color: #6E5F55;
        text-transform: uppercase;
        letter-spacing: 0.08em;
    }

    .stButton > button {
        background-color: #AF885E;
        color: white;
        font-weight: 600;
        border-radius: 8px;
        border: none;
        padding: 0.6rem 1.2rem;
        transition: all 0.2s ease;
    }
    
    .stButton > button:hover {
        background-color: #967046;
        color: white;
        box-shadow: 0 4px 12px rgba(175, 136, 94, 0.3);
    }

    .kdp-badge {
        background-color: #EFE8DC;
        border: 1px solid #D5C7B3;
        border-radius: 8px;
        padding: 8px 12px;
        font-size: 0.85rem;
        color: #4A3B32;
        margin-bottom: 12px;
    }
</style>
""", unsafe_allow_html=True)

# Carrega os dados atuais
data = generator.load_data()
all_days = data.get("days", [])
rules = get_kdp_rules()

# ==================== SIDEBAR ====================
with st.sidebar:
    st.markdown("### ⚙️ Configurações KDP do Livro")
    
    book_id = st.text_input("Identificador Estável (Book ID)", value=data.get("book_id", "30-days-closer-to-god"))
    book_title = st.text_input("Título da Obra", value=data.get("book_title", "30 DAYS CLOSER TO GOD"))
    subtitle = st.text_input("Subtítulo", value=data.get("subtitle", "A daily journey of faith, prayer, and intimacy with God"))
    author = st.text_input("Autor", value=data.get("author", "Lyan Davis"))
    language = st.selectbox("Idioma Principal", options=["en", "pt"], index=0 if data.get("language", "en") == "en" else 1)
    
    col_ed1, col_ed2 = st.columns(2)
    with col_ed1:
        edition_type = st.selectbox("Encadernação", options=["paperback", "hardcover"], index=0)
    with col_ed2:
        trim_options = ["6x9", "5.5x8.5", "6.14x9.21", "7x10"] if edition_type == "hardcover" else ["6x9", "5.5x8.5", "5x8", "5.25x8", "7x10", "8.5x11"]
        trim_size = st.selectbox("Formato (Corte)", options=trim_options, index=0)

    col_pp1, col_pp2 = st.columns(2)
    with col_pp1:
        paper_type = st.selectbox("Papel", options=["cream", "white"], index=0)
    with col_pp2:
        ink_type = st.selectbox("Tinta", options=["black_and_white", "standard_color", "premium_color"], index=0)

    col_bl1, col_bl2 = st.columns(2)
    with col_bl1:
        bleed = st.checkbox("Sangria (Bleed)", value=False)
    with col_bl2:
        opening_rule = st.selectbox("Abertura Leitura", options=["new_page", "recto"], index=0, help="new_page: página consecutiva; recto: sempre página ímpar")

    st.markdown("##### 📐 Margens Editoriais Desejadas (pol)")
    cm1, cm2 = st.columns(2)
    with cm1:
        ed_inside = st.number_input("Interna (Calha)", min_value=0.375, max_value=1.5, value=0.75, step=0.025)
        ed_top = st.number_input("Superior", min_value=0.25, max_value=1.5, value=0.55, step=0.025)
    with cm2:
        ed_outside = st.number_input("Externa", min_value=0.25, max_value=1.5, value=0.65, step=0.025)
        ed_bottom = st.number_input("Inferior", min_value=0.25, max_value=1.5, value=0.55, step=0.025)

    if st.button("💾 Salvar Configurações", use_container_width=True):
        data["book_id"] = book_id
        data["book_title"] = book_title
        data["subtitle"] = subtitle
        data["author"] = author
        data["language"] = language
        data["trim_size"] = trim_size
        data["edition_type"] = edition_type
        data["paper_type"] = paper_type
        data["ink_type"] = ink_type
        data["bleed"] = bleed
        data["reading_opening_rule"] = opening_rule
        generator.save_data(data)
        st.success("Configurações salvas no projeto!")

    # Monta objeto BookConfig ativo
    current_config = BookConfig(
        book_id=book_id,
        title=book_title,
        subtitle=subtitle,
        author=author,
        language=language,
        edition_type=edition_type,
        trim_size=trim_size,
        paper_type=paper_type,
        ink_type=ink_type,
        bleed=bleed,
        editorial_margin_inside=ed_inside,
        editorial_margin_outside=ed_outside,
        editorial_margin_top=ed_top,
        editorial_margin_bottom=ed_bottom,
        reading_opening_rule=opening_rule
    )

    st.markdown("---")
    st.markdown("### 📱 Exportação e-Book (Kindle / EPUB)")
    col_ep1, col_ep2 = st.columns(2)
    with col_ep1:
        if st.button("📱 Gerar EPUB (EN)", use_container_width=True):
            epub_file = epub_generator.generate_epub("en")
            st.session_state["epub_en_path"] = str(epub_file)
            st.success("EPUB Inglês gerado!")
    with col_ep2:
        if st.button("📱 Gerar EPUB (PT)", use_container_width=True):
            epub_file = epub_generator.generate_epub("pt")
            st.session_state["epub_pt_path"] = str(epub_file)
            st.success("EPUB Português gerado!")

    st.markdown("---")
    st.markdown(f"""
    <div class='kdp-badge'>
        <strong>Regras KDP:</strong> v{rules['version']} ({rules['verified_date']})<br>
        <strong>Calha Ativa:</strong> {ed_inside:.3f}″ mín.<br>
        <strong>Paridade:</strong> Páginas Pares Obrigatórias
    </div>
    """, unsafe_allow_html=True)

# ==================== MAIN CONTENT ====================
st.markdown("<h1 class='main-title'>Sistema Gerador de Devocional KDP</h1>", unsafe_allow_html=True)
st.markdown("<p class='main-subtitle'>Diagramação Profissional KDP • Ciclo de Convergência & Validação por Livro</p>", unsafe_allow_html=True)

# Métricas no topo
m1, m2, m3, m4 = st.columns(4)
with m1:
    st.markdown(f"""
    <div class='metric-card'>
        <div class='metric-value'>{len(all_days)}</div>
        <div class='metric-label'>Dias Devocionais</div>
    </div>
    """, unsafe_allow_html=True)
with m2:
    st.markdown(f"""
    <div class='metric-card'>
        <div class='metric-value'>{edition_type.upper()}</div>
        <div class='metric-label'>Encadernação</div>
    </div>
    """, unsafe_allow_html=True)
with m3:
    st.markdown(f"""
    <div class='metric-card'>
        <div class='metric-value'>{trim_size}″</div>
        <div class='metric-label'>Tamanho de Corte</div>
    </div>
    """, unsafe_allow_html=True)
with m4:
    st.markdown(f"""
    <div class='metric-card'>
        <div class='metric-value'>{'SANGRA' if bleed else 'SEM'}</div>
        <div class='metric-label'>Sangria Miolo</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ==================== SEÇÃO GERAÇÃO COMPLETA & CONVERGÊNCIA ====================
with st.expander("🚀 Geração Completa do Livro & Ciclo de Convergência KDP", expanded=True):
    st.markdown("""
    Esta operação executa o **ciclo oficial KDP**: renderiza com as margens espelhadas calculadas,
    inspeciona a contagem física real de páginas, garante fechamento em número par, atualiza o sumário dinâmico,
    gera a capa desvinculada milimétrica e valida o PDF resultante.
    """)
    
    col_gen1, col_gen2 = st.columns([2, 1])
    with col_gen1:
        if st.button("📘 Gerar Livro Completo & Validar KDP", use_container_width=True):
            with st.spinner("Executando ciclo de convergência e validação KDP..."):
                res_book = generator.render_and_converge_book(current_config, custom_data=data)
                st.session_state["latest_book_run"] = res_book
                st.success("Livro gerado e validado com sucesso!")

    if "latest_book_run" in st.session_state:
        run_data = st.session_state["latest_book_run"]
        val = run_data["validation"]
        man = run_data["manifest"]
        rpaths = run_data["run_paths"]
        
        st.markdown(f"#### 📁 Pasta da Execução: `{rpaths.root_dir.name}`")
        st.caption(f"Caminho completo: `{rpaths.root_dir}`")
        
        col_res1, col_res2, col_res3 = st.columns(3)
        with col_res1:
            st.metric("Status KDP", run_data["status"].upper(), delta="Validado" if run_data["status"] == "validated" else "Atenção")
        with col_res2:
            st.metric("Páginas Físicas Finais", run_data["total_pages"], delta="Número Par")
        with col_res3:
            st.metric("Iterações de Margem", len(run_data["iterations"]))

        # Botões de download dos arquivos gerados na pasta do run
        c_dl1, c_dl2, c_dl3 = st.columns(3)
        with c_dl1:
            if os.path.exists(run_data["pdf_path"]):
                with open(run_data["pdf_path"], "rb") as f:
                    st.download_button(
                        label="⬇️ Baixar Miolo (Interior PDF)",
                        data=f.read(),
                        file_name=f"{book_id}_interior.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
        with c_dl2:
            if os.path.exists(run_data["cover_path"]):
                with open(run_data["cover_path"], "rb") as f:
                    st.download_button(
                        label="⬇️ Baixar Capa (Cover PDF)",
                        data=f.read(),
                        file_name=f"{book_id}_cover.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
        with c_dl3:
            manifest_file = rpaths.manifest_path
            if manifest_file.exists():
                with open(manifest_file, "rb") as f:
                    st.download_button(
                        label="⬇️ Baixar Manifesto (manifest.json)",
                        data=f.read(),
                        file_name="manifest.json",
                        mime="application/json",
                        use_container_width=True
                    )

        if val.get("warnings"):
            with st.expander("⚠️ Avisos e Observações Técnicas"):
                for w in val["warnings"]:
                    st.write(f"- {w}")

        with st.expander("📋 Conferências Obrigatórias no KDP Print Previewer"):
            st.info(val.get("disclaimer", ""))
            for pr in val.get("pending_reviews", []):
                st.write(f"• {pr}")

st.markdown("<br>", unsafe_allow_html=True)

# Seletor de dia para visualização e edição
day_options = [f"Dia {d.get('day')}: {d.get('title')}" for d in all_days]
selected_idx = st.selectbox("Selecione o Dia para Visualizar e Editar:", range(len(day_options)), format_func=lambda x: day_options[x])

current_day_data = all_days[selected_idx]
day_number = current_day_data.get("day")

# Abas principais: Visualização vs Edição
tab_preview, tab_editor = st.tabs(["👁️ Visualização das 3 Páginas (Mockup Real)", "✏️ Editor de Conteúdo do Dia"])

# ==================== TAB VISUALIZAÇÃO ====================
with tab_preview:
    st.markdown(f"### Visualização das Páginas do Dia {day_number}: *{current_day_data.get('title')}*")
    
    col_btn1, col_btn2 = st.columns([2, 2])
    with col_btn1:
        if st.button(f"🔄 Renderizar Preview em Alta Resolução (Dia {day_number})"):
            with st.spinner("Renderizando páginas..."):
                generator.export_day_previews(day_number=day_number, custom_data=data, config=current_config)
                st.success("Preview atualizado!")
    with col_btn2:
        if st.button(f"📄 Gerar PDF do Dia {day_number} (3 Páginas)"):
            with st.spinner("Gerando PDF do dia..."):
                res_day = generator.render_book(day_number=day_number, custom_data=data, config=current_config)
                st.session_state[f"day_pdf_{day_number}"] = str(res_day["pdf_path"])
                st.success(f"PDF do Dia {day_number} gerado!")

    if f"day_pdf_{day_number}" in st.session_state and os.path.exists(st.session_state[f"day_pdf_{day_number}"]):
        with open(st.session_state[f"day_pdf_{day_number}"], "rb") as f:
            st.download_button(
                label=f"⬇️ Baixar PDF do Dia {day_number}",
                data=f.read(),
                file_name=f"devocional_dia_{day_number:02d}.pdf",
                mime="application/pdf"
            )

    # Verifica se as imagens de preview existem, senão gera
    p1_img = PREVIEWS_DIR / f"dia_{day_number:02d}_pag_1.png"
    p2_img = PREVIEWS_DIR / f"dia_{day_number:02d}_pag_2.png"
    p3_img = PREVIEWS_DIR / f"dia_{day_number:02d}_pag_3.png"
    
    if not (p1_img.exists() and p2_img.exists() and p3_img.exists()):
        generator.export_day_previews(day_number=day_number, custom_data=data, config=current_config)

    calc_p1 = current_config.start_page_number + (day_number - 1) * 3
    
    col_p1, col_p2, col_p3 = st.columns(3)
    with col_p1:
        st.markdown(f"**Página 1 (Pág. {calc_p1}) - Abertura & Versículo**")
        if p1_img.exists():
            st.image(str(p1_img), use_container_width=True)
    with col_p2:
        st.markdown(f"**Página 2 (Pág. {calc_p1+1}) - Aprofundamento**")
        if p2_img.exists():
            st.image(str(p2_img), use_container_width=True)
    with col_p3:
        st.markdown(f"**Página 3 (Pág. {calc_p1+2}) - Aplicação & Oração**")
        if p3_img.exists():
            st.image(str(p3_img), use_container_width=True)

# ==================== TAB EDITOR ====================
with tab_editor:
    st.markdown(f"### Editar Conteúdo do Dia {day_number}")
    
    with st.form(key=f"form_day_{day_number}"):
        st.markdown("#### 1. Cabeçalho e Passagem Bíblica")
        e_title = st.text_input("Título do Devocional", value=current_day_data.get("title", ""))
        
        c_v1, c_v2 = st.columns([3, 1])
        with c_v1:
            e_verse_text = st.text_area("Texto do Versículo Chave", value=current_day_data.get("verse", {}).get("text", ""), height=70)
        with c_v2:
            e_verse_ref = st.text_input("Referência Bíblica", value=current_day_data.get("verse", {}).get("reference", ""))

        st.markdown("#### 2. Página 1 - Introdução e Reflexão Inicial (com Letra Capitular)")
        p1_list = current_day_data.get("page1", [])
        e_p1_text = st.text_area(
            "Parágrafos da Página 1 (separe cada parágrafo com uma linha em branco):",
            value="\n\n".join(p1_list),
            height=140
        )

        st.markdown("#### 3. Página 2 - Reflexão Aprofundada")
        p2_list = current_day_data.get("page2", [])
        e_p2_text = st.text_area(
            "Parágrafos da Página 2 (separe cada parágrafo com uma linha em branco):",
            value="\n\n".join(p2_list),
            height=180
        )

        st.markdown("#### 4. Página 3 - Conclusão, Caixa de Destaque e Oração")
        p3_list = current_day_data.get("page3", [])
        e_p3_text = st.text_area(
            "Parágrafos da Página 3 (separe cada parágrafo com uma linha em branco):",
            value="\n\n".join(p3_list),
            height=130
        )
        
        c_box1, c_box2 = st.columns(2)
        with c_box1:
            st.markdown("##### 🌿 Para Guardar no Coração")
            e_heart_title = st.text_input("Título do Box 1", value=current_day_data.get("card_heart", {}).get("title", "PARA GUARDAR NO CORAÇÃO"))
            e_heart_text = st.text_area("Mensagem de Destaque", value=current_day_data.get("card_heart", {}).get("text", ""), height=80)
            
        with c_box2:
            st.markdown("##### 🙏 Oração de Hoje")
            e_prayer_title = st.text_input("Título do Box 2", value=current_day_data.get("card_prayer", {}).get("title", "ORAÇÃO DE HOJE"))
            e_prayer_text = st.text_area("Texto da Oração", value=current_day_data.get("card_prayer", {}).get("text", ""), height=80)

        submit_btn = st.form_submit_button("💾 Salvar Alterações deste Dia", use_container_width=True)
        if submit_btn:
            current_day_data["title"] = e_title
            current_day_data["verse"] = {
                "text": e_verse_text.strip(),
                "reference": e_verse_ref.strip()
            }
            current_day_data["page1"] = [p.strip() for p in e_p1_text.split("\n\n") if p.strip()]
            current_day_data["page2"] = [p.strip() for p in e_p2_text.split("\n\n") if p.strip()]
            current_day_data["page3"] = [p.strip() for p in e_p3_text.split("\n\n") if p.strip()]
            current_day_data["card_heart"] = {
                "title": e_heart_title.strip(),
                "text": e_heart_text.strip()
            }
            current_day_data["card_prayer"] = {
                "title": e_prayer_title.strip(),
                "text": e_prayer_text.strip()
            }
            
            all_days[selected_idx] = current_day_data
            data["days"] = all_days
            generator.save_data(data)
            generator.export_day_previews(day_number=day_number, custom_data=data, config=current_config)
            st.success(f"Dia {day_number} atualizado com sucesso e novos previews gerados!")
            st.rerun()

# -*- coding: utf-8 -*-
"""
Painel Interativo de Gestão e Geração de Devocionais para Amazon KDP.
Permite editar os 30 dias, visualizar as 3 páginas de cada dia lado a lado
e gerar os PDFs de alta precisão prontos para impressão.
"""

import os
import json
import pathlib
import streamlit as st
import pymupdf

import generator

BASE_DIR = pathlib.Path(__file__).parent.resolve()
OUTPUT_DIR = BASE_DIR / "output"
PREVIEWS_DIR = BASE_DIR / "previews"

st.set_page_config(
    page_title="Sistema Devocional KDP - 30 Dias",
    page_icon="📖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilização visual acolhedora e profissional inspirada no layout devocional
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

    .page-preview-box {
        background: #FFFFFF;
        border: 1px solid #E0D6CB;
        border-radius: 10px;
        padding: 10px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.06);
        text-align: center;
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
</style>
""", unsafe_allow_html=True)

# Carrega os dados atuais
data = generator.load_data()
all_days = data.get("days", [])

# ==================== SIDEBAR ====================
with st.sidebar:
    st.markdown("### ⚙️ Configurações do Livro")
    
    book_title = st.text_input("Título no Cabeçalho", value=data.get("book_title", "30 DIAS MAIS PERTO DE DEUS"))
    subtitle = st.text_input("Subtítulo", value=data.get("subtitle", "Um guia diário de fé e oração"))
    author = st.text_input("Autor", value=data.get("author", "Lyan Davis"))
    
    col_t1, col_t2 = st.columns(2)
    with col_t1:
        trim_size = st.selectbox("Formato KDP", options=["6x9", "5.5x8.5"], index=0 if data.get("trim_size") == "6x9" else 1)
    with col_t2:
        start_page = st.number_input("Página Inicial", min_value=1, max_value=100, value=int(data.get("start_page_number", 15)))

    if st.button("💾 Salvar Configurações", use_container_width=True):
        data["book_title"] = book_title
        data["subtitle"] = subtitle
        data["author"] = author
        data["trim_size"] = trim_size
        data["start_page_number"] = start_page
        generator.save_data(data)
        st.success("Configurações salvas com sucesso!")

    st.markdown("---")
    st.markdown("### 🚀 Exportação para KDP")
    
    include_fm = st.checkbox("Incluir Páginas Iniciais (1 a 14)", value=True, help="Adiciona Folha de Rosto, Ficha Catalográfica, Dedicatória, Introdução e Sumário dos 30 Dias para o livro completo ter 104 páginas.")
    
    btn_label = "📚 Gerar Livro Completo (104 Págs)" if include_fm else "📚 Gerar Miolo dos 30 Dias (90 Págs)"
    
    if st.button(btn_label, use_container_width=True):
        with st.spinner("Gerando o PDF completo em alta resolução (isto leva alguns segundos)..."):
            res = generator.render_book(custom_data=data, include_front_matter=include_fm)
            pdf_path = res["pdf_path"]
            st.session_state["full_pdf_ready"] = str(pdf_path)
            st.session_state["full_pdf_pages"] = res['total_pages']
            st.success(f"PDF KDP pronto! {res['total_pages']} páginas geradas com sucesso.")
            
    if "full_pdf_ready" in st.session_state and os.path.exists(st.session_state["full_pdf_ready"]):
        with open(st.session_state["full_pdf_ready"], "rb") as f:
            pdf_bytes = f.read()
        p_count = st.session_state.get("full_pdf_pages", 104)
        st.download_button(
            label=f"⬇️ Baixar Livro Completo ({p_count} Páginas - KDP)",
            data=pdf_bytes,
            file_name="devocional_30_dias_kdp.pdf",
            mime="application/pdf",
            use_container_width=True
        )

    st.markdown("---")
    st.markdown("""
    **📐 Especificações KDP Atendidas:**
    - Formato: 6" x 9" (15.24 x 22.86 cm)
    - Sem Sangria (No Bleed)
    - Margens de Segurança e Calha
    - Exatamente 3 Páginas por Dia
    - Fontes Vetoriais Nítidas (300+ DPI)
    """)

# ==================== MAIN CONTENT ====================
st.markdown("<h1 class='main-title'>Sistema Gerador de Devocional KDP</h1>", unsafe_allow_html=True)
st.markdown("<p class='main-subtitle'>30 Dias de Intimidade com Deus • Estrutura de Exatamente 3 Páginas por Dia</p>", unsafe_allow_html=True)

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
    st.markdown("""
    <div class='metric-card'>
        <div class='metric-value'>3</div>
        <div class='metric-label'>Págs por Dia (Máx)</div>
    </div>
    """, unsafe_allow_html=True)
with m3:
    st.markdown(f"""
    <div class='metric-card'>
        <div class='metric-value'>{len(all_days) * 3}</div>
        <div class='metric-label'>Total de Páginas</div>
    </div>
    """, unsafe_allow_html=True)
with m4:
    st.markdown(f"""
    <div class='metric-card'>
        <div class='metric-value'>{trim_size}″</div>
        <div class='metric-label'>Tamanho KDP</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Seletor de dia
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
                generator.export_day_previews(day_number=day_number, custom_data=data)
                st.success("Preview atualizado!")
    with col_btn2:
        if st.button(f"📄 Gerar PDF do Dia {day_number} (3 Páginas)"):
            with st.spinner("Gerando PDF do dia..."):
                res_day = generator.render_book(day_number=day_number, custom_data=data)
                st.session_state[f"day_pdf_{day_number}"] = str(res_day["pdf_path"])
                st.success(f"PDF do Dia {day_number} gerado com sucesso!")

    if f"day_pdf_{day_number}" in st.session_state and os.path.exists(st.session_state[f"day_pdf_{day_number}"]):
        with open(st.session_state[f"day_pdf_{day_number}"], "rb") as f:
            day_bytes = f.read()
        st.download_button(
            label=f"⬇️ Baixar PDF do Dia {day_number} (3 Páginas)",
            data=day_bytes,
            file_name=f"devocional_dia_{day_number:02d}.pdf",
            mime="application/pdf"
        )

    # Verifica se as imagens de preview existem, senão gera
    p1_img = PREVIEWS_DIR / f"dia_{day_number:02d}_pag_1.png"
    p2_img = PREVIEWS_DIR / f"dia_{day_number:02d}_pag_2.png"
    p3_img = PREVIEWS_DIR / f"dia_{day_number:02d}_pag_3.png"
    
    if not (p1_img.exists() and p2_img.exists() and p3_img.exists()):
        generator.export_day_previews(day_number=day_number, custom_data=data)

    calc_p1 = data.get("start_page_number", 15) + (day_number - 1) * 3
    
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
            
            # Atualiza no array e salva
            all_days[selected_idx] = current_day_data
            data["days"] = all_days
            generator.save_data(data)
            
            # Regera previews
            generator.export_day_previews(day_number=day_number, custom_data=data)
            st.success(f"Dia {day_number} atualizado com sucesso e novos previews gerados!")
            st.rerun()

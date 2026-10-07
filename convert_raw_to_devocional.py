# -*- coding: utf-8 -*-
"""
Converte o arquivo data/devocional_raw.json (fornecido pelo usuário com os 30 dias completos)
para o formato estruturado consumido pelo gerador de PDF e app Streamlit.
"""

import json
import pathlib

BASE_DIR = pathlib.Path(__file__).parent.resolve()
RAW_FILE = BASE_DIR / "data" / "devocional_raw.json"
OUT_FILE = BASE_DIR / "data" / "devocional.json"

def convert():
    with open(RAW_FILE, "r", encoding="utf-8") as f:
        raw = json.load(f)

    book_title = raw.get("titulo", "30 Dias Mais Perto de Deus").upper()
    subtitle = raw.get("subtitulo", "Uma jornada diária de fé, oração e intimidade com Deus")
    
    formatted_days = []
    
    for d in raw.get("dias", []):
        day_num = d["dia"]
        title = d["titulo"]
        ref = d.get("referencia_biblica", "").upper()
        verse_text = d.get("parafrase_biblica", "")
        refl = d.get("reflexao", [])
        
        # 7 parágrafos distribuídos em 2 + 3 + 2
        p1 = refl[:2] if len(refl) >= 2 else refl
        p2 = refl[2:5] if len(refl) >= 5 else refl[2:]
        p3 = refl[5:] if len(refl) >= 6 else refl[5:]
        
        card_heart = {
            "title": "PARA GUARDAR NO CORAÇÃO",
            "text": d.get("para_guardar_no_coracao", "")
        }
        card_prayer = {
            "title": "ORAÇÃO DE HOJE",
            "text": d.get("oracao", "")
        }
        
        formatted_days.append({
            "day": day_num,
            "title": title,
            "verse": {
                "text": verse_text,
                "reference": ref
            },
            "page1": p1,
            "page2": p2,
            "page3": p3,
            "card_heart": card_heart,
            "card_prayer": card_prayer
        })
        
    final_data = {
        "book_title": book_title,
        "subtitle": subtitle,
        "author": "Lyan Davis",
        "trim_size": "6x9",
        "start_page_number": 15,
        "days": formatted_days
    }
    
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(final_data, f, ensure_ascii=False, indent=2)
        
    print(f"Sucesso! {len(formatted_days)} dias convertidos e salvos em {OUT_FILE}")

if __name__ == "__main__":
    convert()

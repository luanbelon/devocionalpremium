# -*- coding: utf-8 -*-
"""
Converte o arquivo data/devocional_en_raw.json (versão em inglês com os 30 dias completos)
para o formato estruturado consumido pelo gerador de PDF e app Streamlit.
"""

import json
import pathlib

BASE_DIR = pathlib.Path(__file__).parent.resolve()
RAW_FILE = BASE_DIR / "data" / "devocional_en_raw.json"
OUT_EN_FILE = BASE_DIR / "data" / "devocional_en.json"
OUT_ACTIVE_FILE = BASE_DIR / "data" / "devocional.json"

def convert():
    with open(RAW_FILE, "r", encoding="utf-8") as f:
        raw = json.load(f)

    book_title = raw.get("titulo", "30 Days Closer to God").upper()
    subtitle = raw.get("subtitulo", "A daily journey of faith, prayer, and intimacy with God")
    
    formatted_days = []
    
    for d in raw.get("dias", []):
        day_num = d["dia"]
        title = d["titulo"]
        ref = d.get("referencia_biblica", "").upper()
        verse_text = d.get("parafrase_biblica", "")
        refl = d.get("reflexao", [])
        
        # 7 parágrafos distribuídos perfeitamente em 2 + 4 + 1
        p1 = refl[:2] if len(refl) >= 2 else refl
        p2 = refl[2:6] if len(refl) >= 6 else refl[2:]
        p3 = refl[6:] if len(refl) >= 7 else refl[6:]
        
        card_heart = {
            "title": "TO KEEP IN YOUR HEART",
            "text": d.get("para_guardar_no_coracao", "")
        }
        card_prayer = {
            "title": "TODAY'S PRAYER",
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
        "language": "en",
        "book_title": book_title,
        "subtitle": subtitle,
        "author": "Lyan Davis",
        "trim_size": "6x9",
        "start_page_number": 15,
        "days": formatted_days
    }
    
    with open(OUT_EN_FILE, "w", encoding="utf-8") as f:
        json.dump(final_data, f, ensure_ascii=False, indent=2)
        
    with open(OUT_ACTIVE_FILE, "w", encoding="utf-8") as f:
        json.dump(final_data, f, ensure_ascii=False, indent=2)
        
    print(f"Sucesso! {len(formatted_days)} dias convertidos em inglês e salvos em {OUT_EN_FILE} e {OUT_ACTIVE_FILE}")

if __name__ == "__main__":
    convert()

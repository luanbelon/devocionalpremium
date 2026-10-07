# 📖 Sistema Gerador de Devocional KDP (Amazon) - 30 Dias

Sistema completo de alta precisão tipográfica para geração de livros devocionais para o **Amazon Kindle Direct Publishing (KDP)**.

Reprodução fiel do modelo de **3 páginas por dia**, com diagramação profissional, fontes serifadas clássicas, letra capitular, versículo destacado, caixas de reflexão e oração com ícones vetoriais.

---

## 🌟 Estrutura de Cada Dia (Exatamente 3 Páginas)

| Página | Conteúdo e Elementos |
|---|---|
| **Página 1** (Abertura) | • Cabeçalho corrente (*30 DIAS MAIS PERTO DE DEUS*) com linha sutil<br>• Badge estilizado (*DIA X*) em moldura arredondada<br>• Título principal com tipografia serifada nobre (*Cormorant Garamond*)<br>• Ornamento floral delicado em vetor bronze<br>• Caixa de destaque em tom areia com o **Versículo Chave** e referência<br>• Reflexão inicial com **Letra Capitular** (*Drop Cap*)<br>• Numeração de página centralizada |
| **Página 2** (Aprofundamento) | • Cabeçalho corrente com linha de divisão<br>• Reflexão teológica e devocional aprofundada em parágrafos justificados<br>• Numeração de página centralizada |
| **Página 3** (Aplicação & Oração) | • Cabeçalho corrente<br>• Parágrafos de conclusão e aplicação prática cotidiana<br>• **Box 1: "PARA GUARDAR NO CORAÇÃO"** (com ícone de ramo de oliveira)<br>• **Box 2: "ORAÇÃO DE HOJE"** (com ícone de mãos em oração)<br>• Numeração de página centralizada |

---

## 📂 Estrutura de Pastas do Projeto

```
Devocional/
├── data/
│   └── devocional.json          # Banco de dados com todos os 30 dias estruturados
├── templates/
│   ├── book_template.html       # Template dos 30 dias (3 páginas por dia)
│   └── front_matter.html        # Páginas 1 a 14 (Capa interna, ficha, dedicatória, sumário)
├── output/
│   ├── devocional_30_dias_kdp.pdf  # Livro completo gerado em alta resolução
│   └── devocional_dia_XX.pdf       # PDFs individuais de cada dia
├── previews/                    # Imagens PNG de alta resolução para inspeção visual
├── generator.py                 # Motor principal de renderização e validação
├── app.py                       # Painel Web interativo (Streamlit)
├── iniciar_sistema.bat          # Inicializador com 1 clique para Windows
└── README.md                    # Este manual
```

---

## 🚀 Como Usar o Sistema

### Opção 1: Painel Visual Interativo (Recomendado)
Você pode usar a interface gráfica completa no navegador:

1. Dê um duplo clique no arquivo:
   ```cmd
   iniciar_sistema.bat
   ```
   *Ou execute no terminal:*
   ```powershell
   streamlit run app.py
   ```
2. No painel, você pode:
   - **Visualizar lado a lado** as 3 páginas de qualquer um dos 30 dias em alta resolução.
   - **Editar em tempo real** títulos, versículos, parágrafos, takeaways e orações.
   - **Personalizar** o título do livro, autor, tamanho KDP (6"x9" ou 5.5"x8.5") e página inicial.
   - **Baixar o PDF completo** (104 páginas com páginas pré-textuais ou 90 páginas de miolo) ou o PDF de dias individuais.

---

### Opção 2: Linha de Comando (CLI)
Você também pode gerar e validar diretamente pelo terminal:

- **Gerar livro completo para o KDP (104 páginas com sumário e pré-textuais):**
  ```powershell
  python generator.py --all --front-matter
  ```

- **Gerar apenas o miolo dos 30 dias (90 páginas, a partir da pág. 15):**
  ```powershell
  python generator.py --all
  ```

- **Gerar o PDF de um dia específico (ex: Dia 1 - 3 páginas):**
  ```powershell
  python generator.py --day 1
  ```

- **Exportar imagens PNG de preview para um dia:**
  ```powershell
  python generator.py --preview 1
  ```

- **Validar todos os 30 dias (garantir que nenhum texto transborda para uma 4ª página):**
  ```powershell
  python generator.py --validate
  ```

---

## 🖨️ Diretrizes de Publicação no Amazon KDP

Ao cadastrar seu livro no Amazon KDP (Kindle Direct Publishing):

1. **Tamanho do Corte (Trim Size):** Selecione **6 x 9 polegadas (15,24 x 22,86 cm)**.
2. **Sangria (Bleed):** Selecione **Sem sangria (No Bleed)**. O layout já foi dimensionado com margens de segurança e calha apropriadas.
3. **Tipo de Papel:**
   - **Preto e branco com papel creme** (confere um visual clássico e acolhedor).
   - **Cor padrão** (imprime os tons areia e bronze com suavidade).
4. **Cálculo da Lombada (Spine Width):**
   - Com 104 páginas em papel creme (50 lb):
     `Espessura da lombada = 104 * 0,00225" ≈ 0,234" (5,94 mm)`

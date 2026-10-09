# 📖 Sistema Gerador de Devocional KDP (Amazon)

Sistema avançado de diagramação editorial e conformidade de impressão para o **Amazon Kindle Direct Publishing (KDP)**.
Produz livros impressos (**Paperback** e **Hardcover**), e-Books (**EPUB 3 / Kindle**) e validações técnicas com auditoria de integridade.

---

## 🚀 Principais Melhorias Implementadas

1. **Configuração e Validação Oficial KDP por Livro**:
   - Módulo centralizado de especificações KDP ([kdp_specs.py](file:///c:/Users/luan.santos/Documents/Robôs/Low%20content/Devocional/kdp_specs.py)) versionado e auditado contra as fontes oficiais da Amazon.
   - Cálculo automático de margens espelhadas (*recto* vs *verso*) e calha (*gutter*) conforme a faixa real de páginas (24–150, 151–300, 301–500, 501–700, 701–828).
   - Prevalência do maior valor: `max(mínimo_obrigatório_kdp, preferência_editorial)`.
   - Limites rígidos de páginas por encadernação: **Brochura (24 a 828 páginas)** e **Capa Dura (75 a 550 páginas)**.
   - Geometria precisa com e sem sangria (+0.125" largura, +0.25" altura).
   - Fechamento obrigatório em número par (adição automática de página final em branco).
   - Regra de abertura de leitura configurável: nova página consecutiva ou sempre página ímpar (*recto*).

2. **Ciclo de Convergência da Paginação**:
   - Diagrama com a estimativa inicial -> Renderiza o PDF -> Conta páginas físicas reais -> Ajusta paridade -> Consulta a faixa de calha necessária -> Recalcula margens se o patamar mudou -> Atualiza o sumário dinâmico -> Valida e emite manifesto.
   - Detecção automática de oscilação e limite de tentativas (máx. 5 iterações).

3. **Organização Isolada por Devocional em `output/`**:
   - Estrutura oficial hierárquica por livro, idioma e execução:
     ```
     output/<slug-do-devocional>--<book-id>/<idioma>/<run-id>/
     ├── content/      # Manuscrito-fonte e snapshot dos dados
     ├── metadata/     # Metadados editoriais
     ├── assets/       # Imagens e ornamentos utilizados
     ├── paperback/    # Miolo (interior.pdf) e Capa (cover.pdf)
     ├── hardcover/    # Miolo e Capa da edição capa dura
     ├── ebook/        # Arquivo Kindle/EPUB reflowable
     ├── reports/      # manifest.json e applied_config.json
     ├── previews/     # Imagens PNG de conferência
     ├── logs/         # Registros da execução
     └── tmp/          # Arquivos intermediários (limpos ao final)
     ```
   - Resolução centralizada no [storage_manager.py](file:///c:/Users/luan.santos/Documents/Robôs/Low%20content/Devocional/storage_manager.py) com sanitização contra *path traversal*.
   - Livros diferentes com mesmo título não compartilham pastas.
   - Retomada de execuções existentes via `run_id`.
   - Preservação de arquivos legados existentes em `output/`.

4. **Manifesto e Auditoria Criptográfica (`manifest.json`)**:
   - Salvo em `reports/manifest.json` com status (`validated`, `failed`), configurações solicitadas vs efetivamente aplicadas, páginas físicas reais, caminhos relativos e hashes **SHA-256** de todos os artefatos.

5. **Cálculo Desvinculado e Invalidação de Capa**:
   - Módulo [cover_generator.py](file:///c:/Users/luan.santos/Documents/Robôs/Low%20content/Devocional/cover_generator.py) com cálculos oficiais de lombada baseados no papel (creme: 0.0025"/pág, branco: 0.002252"/pág).
   - Capa dura calcula dobra externa (*wrap* 0.59"), articulação (*hinge* 0.394") e espessura de papelão.
   - Detecção de invalidação: se a paginação ou perfil do miolo mudar, a capa anterior é marcada como obsoleta.

6. **Validador Técnico com PyMuPDF**:
   - Módulo [pdf_validator.py](file:///c:/Users/luan.santos/Documents/Robôs/Low%20content/Devocional/pdf_validator.py) inspeciona o PDF exportado: dimensões, páginas individuais (sem spreads), margens seguras de texto, resolução de imagens (mínimo 300 DPI), fontes incorporadas, ausência de senha/criptografia e tamanho de arquivo <= 650 MB.
   - Lembrete explícito de que a aprovação local é técnica e ainda requer conferência no **KDP Print Previewer**.

---

## 🛠️ Arquitetura dos Módulos

- [kdp_specs.py](file:///c:/Users/luan.santos/Documents/Robôs/Low%20content/Devocional/kdp_specs.py): Regras oficiais KDP, tabela de calha, conversões e fórmulas.
- [book_config.py](file:///c:/Users/luan.santos/Documents/Robôs/Low%20content/Devocional/book_config.py): Dataclass de configuração por devocional e regras de abertura.
- [storage_manager.py](file:///c:/Users/luan.santos/Documents/Robôs/Low%20content/Devocional/storage_manager.py): Gestor de armazenamento, isolamento de pastas e sanitização.
- [pdf_validator.py](file:///c:/Users/luan.santos/Documents/Robôs/Low%20content/Devocional/pdf_validator.py): Validador exaustivo de PDF com PyMuPDF.
- [cover_generator.py](file:///c:/Users/luan.santos/Documents/Robôs/Low%20content/Devocional/cover_generator.py): Gerador e calculador de capa KDP.
- [manifest_manager.py](file:///c:/Users/luan.santos/Documents/Robôs/Low%20content/Devocional/manifest_manager.py): Emissor de `manifest.json` com hashes SHA-256.
- [generator.py](file:///c:/Users/luan.santos/Documents/Robôs/Low%20content/Devocional/generator.py): Motor do ciclo de convergência e renderizador Chrome/Edge.
- [epub_generator.py](file:///c:/Users/luan.santos/Documents/Robôs/Low%20content/Devocional/epub_generator.py): Exportador de e-Books EPUB 3 + NCX para Kindle.
- [app.py](file:///c:/Users/luan.santos/Documents/Robôs/Low%20content/Devocional/app.py): Interface Web Streamlit com painel de controle KDP.
- [tests/test_kdp_system.py](file:///c:/Users/luan.santos/Documents/Robôs/Low%20content/Devocional/tests/test_kdp_system.py): Suíte com 10 testes cobrindo todas as regras KDP.

---

## 💻 Comandos e Como Utilizar

### 1. Interface Web (Streamlit)
```powershell
streamlit run app.py
```
Acesse no navegador para:
- Ajustar encadernação (Paperback ou Hardcover), formato de corte, papel e margens.
- Clicar em **"📘 Gerar Livro Completo & Validar KDP"** para rodar o ciclo de convergência.
- Baixar Miolo (`interior.pdf`), Capa (`cover.pdf`), Manifesto (`manifest.json`) e EPUBs.
- Editar os 30 dias individualmente com preview de 3 páginas.

### 2. Linha de Comando (CLI)

- **Gerar livro completo Paperback (Brochura 6" x 9"):**
  ```powershell
  python generator.py --all --edition paperback --trim 6x9
  ```

- **Gerar livro completo Hardcover (Capa Dura 6" x 9"):**
  ```powershell
  python generator.py --all --edition hardcover --trim 6x9
  ```

- **Gerar com regra de abertura em página ímpar (*recto*):**
  ```powershell
  python generator.py --all --opening-rule recto
  ```

- **Gerar com sangria (*bleed*):**
  ```powershell
  python generator.py --all --bleed
  ```

- **Exportar e-Books EPUB (Inglês e Português):**
  ```powershell
  python epub_generator.py --lang all
  ```

- **Executar a suíte completa de testes:**
  ```powershell
  pytest tests/test_kdp_system.py -v
  ```

---

## 📋 Tabela Oficial KDP de Margem Interna (Calha / Gutter)

| Total de Páginas Físicas | Margem Interna Mínima (pol) | Margem Interna Mínima (pt) | Margem Interna Mínima (mm) |
|---|---|---|---|
| **24 a 150 páginas** | 0.375" | 27.0 pt | 9.5 mm |
| **151 a 300 páginas** | 0.500" | 36.0 pt | 12.7 mm |
| **301 a 500 páginas** | 0.625" | 45.0 pt | 15.9 mm |
| **501 a 700 páginas** | 0.750" | 54.0 pt | 19.1 mm |
| **701 a 828 páginas** | 0.875" | 63.0 pt | 22.2 mm |

*Margens externas, superior e inferior mínimas: 0.250" sem sangria; 0.375" com sangria.*

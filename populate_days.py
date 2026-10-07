# -*- coding: utf-8 -*-
"""
Script para gerar o banco de dados inicial completo dos 30 dias de devocional
estruturado rigorosamente para 3 páginas por dia no formato KDP.
"""

import json
import pathlib

DAYS_DATA = [
    {
        "day": 1,
        "title": "Comece onde você está",
        "verse": {
            "text": "O Senhor está perto dos que têm o coração quebrantado e salva os de espírito abatido.",
            "reference": "SALMO 34:18"
        },
        "page1": [
            "Talvez você tenha começado este livro esperando encontrar uma versão melhor de si mesmo ao final destes trinta dias. Mais disciplinado. Mais fiel. Mais tranquilo. Mais próximo de Deus. Talvez você tenha prometido a si mesmo que desta vez seria diferente.",
            "Mas a verdade é que a sua história não precisa começar de um ponto perfeito. Deus não espera que você chegue a Ele com a vida organizada, com todas as respostas certas e com tudo em ordem. Ele se aproxima de você exatamente onde você está.",
            "Muitas vezes acreditamos que só podemos buscar a Deus depois de resolver nossos problemas, superar nossas falhas e colocar tudo no lugar. Mas o Evangelho nos mostra o contrário: foi quando estávamos fracos, confusos e necessitados que Cristo nos alcançou.",
            "Você não precisa esperar um momento ideal. Você pode começar hoje. Aqui. Agora."
        ],
        "page2": [
            "Começar onde você está não significa aceitar a estagnação, mas reconhecer com sinceridade a sua realidade diante de Deus. É olhar para a sua vida com honestidade, com todas as suas lutas, limitações e perguntas, e dizer: “Senhor, é aqui que eu estou. E eu quero caminhar com o Senhor a partir daqui”.",
            "Deus não se assusta com as suas dúvidas. Ele não se afasta das suas fraquezas. Pelo contrário, Ele se revela justamente aos que têm um coração sincero e reconhecem que precisam dEle. O Salmo 34:18 nos lembra que o Senhor está perto dos que têm o coração quebrantado e salva os de espírito abatido. Essa é uma das verdades mais belas das Escrituras: Deus não rejeita os corações feridos; Ele se aproxima deles.",
            "Talvez você esteja enfrentando um tempo difícil. Talvez se sinta cansado, inseguro ou decepcionado. Talvez tenha se afastado de Deus e não saiba como recomeçar. Tudo bem. Você pode começar onde você está. O importante não é o ponto de partida, mas a direção. E quando você decide dar o primeiro passo, mesmo que pequeno, você já está se movendo em direção a uma vida mais perto de Deus.",
            "Lembre-se: a vida cristã não é uma linha reta, mas uma caminhada. E cada dia é uma nova oportunidade de se aproximar de Deus. Hoje, você pode escolher entregar a Ele o que está em seu coração, confiar em Sua graça e permitir que Ele guie os seus próximos passos.",
            "Comece com sinceridade. Fale com Deus. Leia a Sua Palavra. Abra o seu coração. Não importa como foi o seu ontem, hoje é um novo dia. E Deus está com você."
        ],
        "page3": [
            "Você não precisa ter todas as respostas para começar. Às vezes, o que você mais precisa é apenas estar presente diante de Deus, com um coração disposto. A caminhada com Ele não exige perfeição, mas sinceridade. Não exige força própria, mas dependência diária.",
            "Deus é paciente. Ele conhece o seu ritmo. Ele entende as suas limitações e ainda assim escolhe caminhar com você. Mesmo quando você se sente longe, Ele continua perto. Mesmo quando você não consegue orar como gostaria, Ele ouve o seu coração. Mesmo quando você não entende o que está acontecendo, Ele está no controle.",
            "Hoje, faça uma escolha: não adie mais a sua caminhada com Deus. Comece onde você está. Com o que você tem. Com o coração que você possui agora. Dê o primeiro passo e confie que Ele vai te acompanhar. O Deus que se aproxima dos quebrantados continua sendo o mesmo hoje: um Deus fiel, amoroso e presente, que deseja caminhar com você todos os dias."
        ],
        "card_heart": {
            "title": "PARA GUARDAR NO CORAÇÃO",
            "text": "Você não precisa ter tudo em ordem para começar a caminhar com Deus. Ele se aproxima de você exatamente onde você está."
        },
        "card_prayer": {
            "title": "ORAÇÃO DE HOJE",
            "text": "Senhor, eu me apresento diante de Ti exatamente como estou. Com as minhas dúvidas, fraquezas e medos. Obrigado por Te aproximares de mim e por me receberes com amor. Ajuda-me a dar o primeiro passo, mesmo que pequeno, e a confiar que Tu estás comigo em cada etapa. Guia o meu coração hoje e me ajuda a caminhar mais perto de Ti. Amém."
        }
    }
]

# Dados dos temas dos 30 dias para gerar conteúdo rico e completo
DEVOTIONAL_THEMES = [
    (2, "O poder da quietude", "Aquietai-vos e sabei que eu sou Deus; sou exaltado entre as nações.", "SALMO 46:10",
     "Vivemos em um mundo barulhento, onde o silêncio é raro e a pressa se tornou rotina. Somos bombardeados por notificações, prazos e preocupações constantes que nos roubam a paz interior.",
     "Aquietar o coração diante do Senhor não é passividade, mas um ato de suprema confiança.",
     "Hoje, separe alguns minutos para desligar os ruídos exteriores e apenas ouvir o sussurro do Espírito."),
     
    (3, "A graça que te basta", "A minha graça te basta, porque o meu poder se aperfeiçoa na fraqueza.", "2 CORÍNTIOS 12:9",
     "Muitas vezes nos sentimos insuficientes diante das exigências da vida diária e dos padrões que impomos a nós mesmos.",
     "A graça de Deus não é um prêmio para os fortes, mas um sustento vivo para os que reconhecem sua fragilidade.",
     "Descanse no favor imerecido de Deus e permita que o poder dEle se revele em suas limitações."),

    (4, "Renovando a mente", "Não vos conformeis com este século, mas transformai-vos pela renovação da vossa mente.", "ROMANOS 12:2",
     "Nossos pensamentos moldam nossas atitudes, nossos sentimentos e a forma como enxergamos a vida.",
     "Permitir que a Palavra de Deus filtre aquilo em que pensamos é o segredo para experimentar a boa, agradável e perfeita vontade do Pai.",
     "Hoje, substitua pensamentos de derrota por promessas eternas gravadas nas Escrituras."),

    (5, "Confiança nas tempestades", "Ele se levantou, repreendeu o vento e disse ao mar: Aquieta-te! E houve grande bonança.", "MARCOS 4:39",
     "As tempestades da vida têm a capacidade de nos fazer questionar se Deus realmente Se importa conosco.",
     "Mesmo quando parece que Jesus está dormindo no barco, Ele permanece a bordo e tem total autoridade sobre as ondas.",
     "Lembre-se de que a tempestade não tem poder para afundar o barco que carrega o Autor da vida."),

    (6, "O descanso da alma", "Vinde a mim, todos os que estais cansados e sobrecarregados, e eu vos aliviarei.", "MATEUS 11:28",
     "Existe um cansaço que uma boa noite de sono não consegue curar: o cansaço da alma carregada de culpas e fardos alheios.",
     "Jesus não nos convida a cumprir mais tarefas religiosas, mas a trocar nosso jugo pesado pela Sua leveza e paz.",
     "Deposite aos pés da cruz hoje todo o peso que você não foi chamado para carregar sozinho."),

    (7, "Amor que nunca falha", "O amor jamais acaba; mas, havendo profecias, desaparecerão; havendo línguas, cessarão.", "1 CORÍNTIOS 13:8",
     "O amor humano é frequentemente condicional, oscilante e suscetível às circunstâncias do momento.",
     "O amor de Deus por você é eterno, inabalável e foi provado na cruz de uma vez por todas.",
     "Permita-se ser amado por Deus hoje e seja um canal desse mesmo amor para os que estão ao seu redor."),

    (8, "A bússola da oração", "Não andeis ansiosos de coisa alguma; em tudo, porém, sejam conhecidas as vossas petições.", "FILIPENSES 4:6",
     "A oração não é uma tentativa de mudar a vontade de Deus, mas de alinhar o nosso coração ao coração do Pai.",
     "Quando oramos em gratidão, desarmamos as armadilhas do medo e abrimos espaço para a paz que guarda nossa mente.",
     "Fale com Deus com a naturalidade de um filho que sabe que seu Pai está sempre pronto a ouvir."),

    (9, "Vencendo a ansiedade", "Lançando sobre ele toda a vossa ansiedade, porque ele tem cuidado de vós.", "1 PEDRO 5:7",
     "A ansiedade tenta antecipar dores do amanhã que talvez nunca aconteçam, roubando a força necessária para o hoje.",
     "Deus cuida detalhadamente de cada área de sua vida, desde as aves do céu até os fios de cabelo de sua cabeça.",
     "Entregue o controle do seu futuro Àquele que já conhece o fim desde o princípio."),

    (10, "Raízes profundas na fé", "Será como a árvore plantada junto às águas, que estende as suas raízes para o ribeiro.", "JEREMIAS 17:8",
     "Árvores com raízes superficiais não resistem aos ventos fortes nem às secas prolongadas do verão.",
     "Nossa fé precisa mergulhar profundamente na verdade de Deus para que permaneçamos frutíferos mesmo em tempos difíceis.",
     "Alimente hoje suas raízes espirituais por meio da oração constante e da meditação bíblica."),

    (11, "O valor da paciência", "Bom é o Senhor para os que esperam por ele, para a alma que o busca.", "LAMENTAÇÕES 3:25",
     "Esperar é uma das disciplinas mais difíceis para a natureza humana, especialmente em uma era de respostas instantâneas.",
     "O tempo de espera de Deus nunca é tempo perdido; é nele que nosso caráter é forjado e nossa fé amadurece.",
     "Confie no cronograma divino, sabendo que os planos de Deus nunca se atrasam."),

    (12, "Luz para o seu caminho", "Lâmpada para os meus pés é a tua palavra e luz, para o meu caminho.", "SALMO 119:105",
     "Muitas vezes gostaríamos que Deus iluminasse todo o horizonte dos próximos dez anos de nossa vida.",
     "Mas a Bíblia é descrita como uma lâmpada para os pés: ela ilumina o próximo passo que devemos dar com fidelidade.",
     "Dê o passo de obediência que está claro diante de você hoje e deixe o restante nas mãos do Senhor."),

    (13, "Perdão que liberta", "Assim como o Senhor vos perdoou, assim perdoai vós também.", "COLOSSENSES 3:13",
     "Guardar ressentimento é como beber veneno esperando que a outra pessoa sofra o dano.",
     "O perdão não justifica o erro alheio, mas quebra as correntes do passado e liberta o seu coração para viver o presente.",
     "Escolha perdoar hoje, lembrando-se do imenso perdão que você mesmo recebeu de Deus."),

    (14, "Força na fraqueza", "Os que esperam no Senhor renovam as suas forças, sobem com asas como águias.", "ISAÍAS 40:31",
     "Todos nós temos dias em que o ânimo parece esgotado e a vontade de prosseguir diminui consideravelmente.",
     "A força do cristão não nasce da autossuficiência, mas da dependência diária daquele cujo vigor nunca se esgota.",
     "Aproxime-se do trono da graça hoje para receber a renovação espiritual de que necessita."),

    (15, "Gratidão em todo tempo", "Em tudo dai graças, porque esta é a vontade de Deus em Cristo Jesus para convosco.", "1 TESSALONICENSES 5:18",
     "É fácil agradecer quando tudo corre bem e os planos dão certo conforme o que idealizamos.",
     "A verdadeira gratidão, no entanto, olha além das circunstâncias e enxerga a bondade imutável do Criador.",
     "Liste hoje três bênçãos pelas quais você é profundamente grato e louve a Deus por elas."),

    (16, "A presença invisível", "Não temas, nem te espantes, porque o Senhor, teu Deus, é contigo por onde quer que andares.", "JOSUÉ 1:9",
     "A solidão e o medo são inimigos sutis que tentam sussurrar que fomos abandonados à própria sorte.",
     "A promessa da companhia de Deus não é poética, é um compromisso aliançado pelo próprio Criador.",
     "Caminhe com confiança hoje, sabendo que você nunca entra em uma sala vazia quando Deus está com você."),

    (17, "O propósito no deserto", "Se a visão ainda tarda, espera-a, porque certamente virá, não tardará.", "HABACUQUE 2:3",
     "Os períodos de deserto espiritual costumam ser dolorosos, silenciosos e repletos de indagações.",
     "Deus não nos leva ao deserto para nos destruir, mas para falar ao nosso coração longe das distrações do mundo.",
     "Mantenha os olhos na promessa e creia que os dias de escassez darão lugar a colheitas abundantes."),

    (18, "Coração generoso", "A alma generosa prosperará, e quem dá a beber será dessedentado.", "PROVÉRBIOS 11:25",
     "A cultura do mundo nos ensina a reter, acumular e focar exclusivamente nas próprias necessidades.",
     "O Reino de Deus opera na lógica oposta: é repartindo que multiplicamos e servindo que encontramos realização.",
     "Procure abençoar alguém com seu tempo, suas palavras ou seus recursos ao longo do dia de hoje."),

    (19, "Esperança viva", "O Deus da esperança vos encha de todo o gozo e paz no vosso crer.", "ROMANOS 15:13",
     "A esperança bíblica não é um desejo incerto de que algo bom aconteça, mas uma âncora firme na fidelidade de Deus.",
     "Quando nossa esperança está ancorada em Cristo, nenhuma tempestade terrena pode nos desestabilizar.",
     "Reafirme sua confiança nas promessas divinas e deixe que a alegria celestial inunde o seu ser."),

    (20, "Caminhando em integridade", "Quem anda em integridade anda seguro, mas o que perverte os seus caminhos será conhecido.", "PROVÉRBIOS 10:9",
     "Integridade é ser a mesma pessoa no secreto que somos em público diante de todos os olhares.",
     "A verdadeira paz de consciência é um tesouro inestimável que nenhuma riqueza material pode comprar.",
     "Tome decisões hoje pautadas na verdade e na retidão, agradando primeiramente ao Senhor."),

    (21, "O bom pastor", "O Senhor é o meu pastor; nada me faltará. Ele me faz repousar em pastos verdejantes.", "SALMO 23:1-2",
     "Ovelhas são animais vulneráveis que dependem inteiramente do cuidado atento e amoroso de seu pastor.",
     "Jesus é o Bom Pastor que conhece cada uma de suas ovelhas pelo nome e deu Sua vida por elas.",
     "Deixe-se conduzir pelo Bom Pastor e descanse na certeza de que Ele proverá tudo de que você precisa."),

    (22, "A alegria da salvação", "Não vos entristeçais, porque a alegria do Senhor é a vossa força.", "NEEMIAS 8:10",
     "Felicidade depende de acontecimentos favoráveis, mas a alegria do Senhor brota de dentro para fora.",
     "Mesmo diante de lutas e provações, a certeza de nossa redenção em Cristo sustenta um sorriso no coração.",
     "Escolha hoje se alegrar naquilo que Deus é e nas maravilhas que Ele já realizou por você."),

    (23, "Coragem para recomeçar", "Eis que faço coisa nova, que está saindo à luz; porventura não o percebeis?", "ISAÍAS 43:19",
     "O medo de falhar novamente muitas vezes nos aprisiona em ciclos de inércia e lamentação pelo passado.",
     "Deus é especialista em transformar páginas em branco e recomeços humildes em histórias de vitória.",
     "Deixe para trás o que ficou no ontem e avance corajosamente rumo ao futuro que Deus preparou."),

    (24, "Palavras que edificam", "Não saia da vossa boca nenhuma palavra torpe, mas só a que for boa para edificação.", "EFÉSIOS 4:29",
     "As palavras têm o tremendo poder de construir esperança ou de destruir a autoestima de alguém.",
     "Como seguidores de Cristo, somos chamados a semear encorajamento, consolo e graça com nossa fala.",
     "Use suas palavras hoje para levantar quem caiu e para inspirar quem precisa de ânimo."),

    (25, "Refúgio seguro", "O que habita no esconderijo do Altíssimo e descansa à sombra do Onipotente.", "SALMO 91:1",
     "O mundo exterior oferece muitas promessas falsas de segurança financeira, social e emocional.",
     "O único refúgio inabalável contra os perigos visíveis e invisíveis é a presença protetora do Todo-Poderoso.",
     "Faça da presença de Deus a sua morada diária e desfrute da cobertura do Seu amor soberano."),

    (26, "Fé em ação", "A fé, se não tiver obras, por si só está morta. Mostra-me a tua fé pelas tuas obras.", "TIAGO 2:17",
     "A fé verdadeira não é apenas uma concordância mental com doutrinas, mas uma atitude prática de vida.",
     "Quando confiamos verdadeiramente em Deus, nossas escolhas diárias refletem essa confiança incondicional.",
     "Coloque sua fé em prática hoje por meio de um gesto concreto de amor, obediência ou compaixão."),

    (27, "A beleza da simplicidade", "O que o Senhor requer de ti: senão que pratiques a justiça, e ames a misericórdia.", "MIQUEIAS 6:8",
     "Muitas vezes complicamos a vida espiritual criando exigências e rituais que Deus nunca pediu de nós.",
     "O que o Senhor busca é um coração simples, que ame a justiça, viva a misericórdia e ande com humildade.",
     "Simplifique sua rotina espiritual hoje focando no essencial: amar a Deus e amar o próximo."),

    (28, "Construindo sobre a rocha", "Todo aquele que ouve estas minhas palavras e as pratica será comparado a um homem prudente.", "MATEUS 7:24",
     "A estabilidade de um edifício não depende da beleza de sua fachada, mas da solidez de seus alicerces.",
     "Quando construímos nossos sonhos sobre os ensinamentos eternos de Jesus, nenhuma crise pode nos derrubar.",
     "Examine onde você tem colocado sua confiança e certifique-se de que sua casa está sobre a Rocha eterna."),

    (29, "Paz que excede o entendimento", "Deixo-vos a paz, a minha paz vos dou; não vo-la dou como a dá o mundo.", "JOÃO 14:27",
     "A paz do mundo é a ausência temporária de conflitos externos, frágil e dependente dos eventos ao redor.",
     "A paz de Cristo é uma tranquilidade sobrenatural que permanece firme mesmo no meio do caos.",
     "Receba a paz de Jesus em seu coração hoje e não permita que o medo domine seus sentimentos."),

    (30, "Perseverando até o fim", "Corramos com perseverança a carreira que nos está proposta, olhando para Jesus.", "HEBREUS 12:1-2",
     "Chegar ao final desta jornada de trinta dias é um marco importante, mas a caminhada com Deus continua.",
     "A vida cristã é uma maratona de perseverança diária, onde o alvo supremo é a semelhança com Cristo Jesus.",
     "Mantenha os olhos fitos em Jesus, renove sua aliança diária e prossiga firme até o grande encontro face a face.")
]

def generate_day_paragraphs(day_num, title, verse_text, verse_ref, intro_theme, deepen_theme, concl_theme):
    # Página 1: Introdução rica e acolhedora (4 parágrafos - ~145-160 palavras)
    p1 = [
        f"Ao acordar para mais um dia de jornada, somos frequentemente confrontados com a intensidade de nossas próprias expectativas. {intro_theme} É natural buscar clareza em meio a tantas vozes que disputam nossa atenção, mas a Palavra de Deus permanece como nossa âncora mais segura.",
        f"Quando olhamos com sinceridade para as Escrituras, compreendemos que o Senhor não nos chama para viver de aparências. {deepen_theme} Ele deseja alcançar o mais íntimo do nosso coração, transformando nossa mentalidade e alinhando nossos passos à Sua perfeita vontade.",
        "Muitas vezes esquecemos que cada detalhe de nossa caminhada está debaixo da soberania divina. Não há surpresas para o Criador; aquilo que parece incerto aos nossos olhos já foi contemplado pelo olhar amoroso e protetor do nosso Pai celestial.",
        "Você não precisa carregar o peso do mundo sobre os ombros hoje. O mesmo Deus que sustentou gerações passadas caminha ao seu lado agora, oferecendo graça abundante e direção segura para cada instante."
    ]

    # Página 2: Reflexão aprofundada (5 parágrafos substanciais - ~270-290 palavras, preenchendo a página inteira)
    p2 = [
        f"Aprofundar nossa comunhão com Deus exige intencionalidade de coração. Não se trata apenas de cumprir uma leitura diária rápida ou riscar uma tarefa de nossa lista, mas de permitir que a verdade bíblica penetre em cada decisão, conversa e pensamento que cultivamos ao longo do dia.",
        f"O versículo que meditamos hoje ({verse_ref}) nos recorda de uma verdade transformadora: “{verse_text}”. Essas palavras sagradas não foram registradas para meramente nos trazer um alívio passageiro, mas para estabelecer um alicerce inabalável sob os nossos pés em tempos de incerteza.",
        "Em momentos de adversidade ou cansaço, nossa tendência natural é buscar saídas rápidas e apoios humanos transitórios. No entanto, a verdadeira paz e segurança residem em nos abrigarmos debaixo das asas do Altíssimo, aprendendo a confiar mesmo quando os caminhos parecem difíceis e as respostas demoram a chegar.",
        "A maturidade espiritual floresce no silêncio da perseverança diária. É quando decidimos ser fiéis nas pequenas coisas, orar mesmo quando as palavras parecem escassear e permanecer firmes na esperança que o poder extraordinário de Deus se manifesta em nossa fraqueza.",
        "Abra o seu entendimento para o agir suave do Espírito Santo neste instante. Deixe que Ele dissipe toda a ansiedade acumulada, renove as suas motivações e preencha o seu íntimo com a alegria do Senhor, que é a força verdadeira que sustenta cada passo de sua caminhada."
    ]

    # Página 3: Aplicação prática e conclusão (3 parágrafos - ~160 palavras)
    p3 = [
        f"Chegamos agora ao momento de transformar a reflexão bíblica em atitude prática no cotidiano. {concl_theme} Não basta apenas admirar a bondade divina à distância; é indispensável permitir que ela transborde em gestos concretos de fé, generosidade, perdão e compaixão com as pessoas ao seu redor.",
        "A cada novo amanhecer, a misericórdia do Senhor se renova com fidelidade sobre a sua vida. Isso significa que as falhas ou frustrações do passado não possuem autoridade para aprisionar o seu futuro quando você está genuinamente firmado na graça perdoadora de Cristo.",
        "Viva o restante deste dia com os olhos fitos naquilo que é eterno. Caminhe com determinação santa, fale palavras que tragam vida e encorajamento aos cansados e guarde no coração a certeza absoluta de que Deus continua guiando cada uma das suas veredas."
    ]

    card_heart = {
        "title": "PARA GUARDAR NO CORAÇÃO",
        "text": f"A presença de Deus é o refúgio mais seguro para a sua alma. Firme os seus passos na promessa de {verse_ref} e desfrute da paz soberana que excede todo entendimento."
    }

    card_prayer = {
        "title": "ORAÇÃO DE HOJE",
        "text": f"Pai celestial, eu me apresento diante de Ti neste dia com um coração aberto e agradecido. Entrego em Tuas mãos os meus planos, anseios e preocupações. Concede-me sensibilidade espiritual para ouvir a Tua voz e coragem para praticar a Tua Palavra. Que a Tua santa paz guarde a minha mente e as minhas emoções ao longo de toda a jornada. Em nome de Jesus, amém."
    }

    return {
        "day": day_num,
        "title": title,
        "verse": {
            "text": verse_text,
            "reference": verse_ref
        },
        "page1": p1,
        "page2": p2,
        "page3": p3,
        "card_heart": card_heart,
        "card_prayer": card_prayer
    }

def main():
    all_days = [DAYS_DATA[0]] # Dia 1 exato do mockup
    
    for theme in DEVOTIONAL_THEMES:
        d = generate_day_paragraphs(*theme)
        all_days.append(d)
        
    book_data = {
        "book_title": "30 DIAS MAIS PERTO DE DEUS",
        "subtitle": "Um guia diário de fé, renovação e intimidade com Deus",
        "author": "Luan Santos",
        "trim_size": "6x9",
        "start_page_number": 15,
        "days": all_days
    }
    
    out_file = pathlib.Path("data/devocional.json")
    out_file.write_text(json.dumps(book_data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Salvo {len(all_days)} dias em {out_file.resolve()}")

if __name__ == "__main__":
    main()

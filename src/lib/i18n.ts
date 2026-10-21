import type { FrontMatter, Language } from "./types";

export interface Labels {
  day: string;
  contents: string;
  heart: string;
  prayer: string;
}

export const LABELS: Record<Language, Labels> = {
  en: { day: "Day", contents: "Contents", heart: "To keep in your heart", prayer: "Today's prayer" },
  pt: { day: "Dia", contents: "Sumário", heart: "Para guardar no coração", prayer: "Oração de hoje" },
};

export function defaultFrontMatter(lang: Language, opts: { days: number; author: string; year: string }): FrontMatter {
  const { days, author, year } = opts;

  if (lang === "pt") {
    return {
      copyright: [
        author ? `Copyright © ${year} por ${author}` : `Copyright © ${year}`,
        "Todos os direitos reservados. Nenhuma parte desta publicação pode ser reproduzida, distribuída ou transmitida por qualquer meio sem prévia autorização por escrito do autor.",
        "As sínteses bíblicas são paráfrases autorais elaboradas para a leitura devocional, salvo indicação em contrário.",
      ],
      dedication:
        "Dedicado a todos os corações que anseiam por uma caminhada mais íntima e sincera com Deus em meio à agitação dos dias modernos.",
      epigraph: { text: "Acheguem-se a Deus, e ele se achegará a vocês.", reference: "Tiago 4:8" },
      introTitle: "Introdução",
      intro: [
        "A vida com Deus não se constrói em passos apressados, mas na perseverança calma de cada amanhecer. Este devocional foi concebido como um refúgio diário para a sua alma: um espaço sagrado onde o ruído do cotidiano cede lugar à voz mansa do Espírito Santo.",
        `Ao longo dos próximos ${days} dias, você é convidado a percorrer uma trajetória intencional de renovação espiritual. Cada reflexão foi cuidadosamente estruturada para ancorar sua fé nas Escrituras, desafiar seus pensamentos e conduzi-lo a uma oração sincera.`,
      ],
      guidanceTitle: "Orientações para a Jornada",
      guidanceIntro: "Para colher os melhores frutos desta caminhada diária, recomendamos algumas práticas simples:",
      guidance: [
        {
          title: "Separe um horário sagrado",
          text: "Seja nas primeiras horas da manhã ou antes do repouso noturno, dedique dez a quinze minutos de serenidade, longe de distrações digitais.",
        },
        {
          title: "Medite sem pressa",
          text: "Permita que a mensagem penetre seu coração. Mais vale absorver uma única verdade com profundidade do que ler apressadamente.",
        },
        {
          title: "Converse com Deus",
          text: "A oração proposta ao final de cada dia é um ponto de partida. Abra seu coração com transparência e sinceridade.",
        },
      ],
      journeyLabel: `Jornada de ${days} Dias`,
    };
  }

  return {
    copyright: [
      author ? `Copyright © ${year} by ${author}` : `Copyright © ${year}`,
      "All rights reserved. No part of this publication may be reproduced, distributed, or transmitted in any form or by any means without the prior written permission of the author.",
      "Scripture summaries and paraphrases are authorial reflections designed for personal devotional reading, unless otherwise noted.",
    ],
    dedication:
      "Dedicated to every heart longing for a deeper, more intimate walk with God amidst the noise of the modern world.",
    epigraph: { text: "Draw near to God, and He will draw near to you.", reference: "James 4:8" },
    introTitle: "Introduction",
    intro: [
      "A meaningful life with God is not built on hurried steps, but on the quiet faithfulness of each new morning. This devotional was crafted as a daily sanctuary for your spirit: a sacred moment where everyday noise yields to the gentle stillness of God's presence.",
      `Over the next ${days} days, you are invited on an intentional journey of spiritual renewal. Each reading is anchored in Scripture, designed to challenge your perspective, and lead your heart into honest, transformative prayer.`,
    ],
    guidanceTitle: "Guidance for Your Journey",
    guidanceIntro: `To receive the fullest fruit from these ${days} days, consider these simple practices:`,
    guidance: [
      {
        title: "Set aside a dedicated time",
        text: "Whether early in the morning or before resting at night, reserve quiet minutes away from screens and notifications.",
      },
      {
        title: "Read unhurriedly",
        text: "Allow the words to resonate quietly in your mind. It is far better to meditate deeply on a single thought than to rush through without absorbing it.",
      },
      {
        title: "Pray in your own words",
        text: "The prayer provided at the end of each day is a starting point. Feel free to pour out your heart before God with complete honesty.",
      },
    ],
    journeyLabel: `${days}-Day Journey`,
  };
}

export const dictionaries = {
  en: {
    watchlist: "Watchlist",
  },
  ko: {
    watchlist: "관심 목록",
  },
};

export type Locale = keyof typeof dictionaries;

export function getDictionary(locale: Locale) {
  return dictionaries[locale];
}

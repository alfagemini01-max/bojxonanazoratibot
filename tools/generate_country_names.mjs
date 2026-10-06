import fs from 'node:fs';

const source = fs.readFileSync('app/webapp.py', 'utf8');
const pairs = [...source.matchAll(/(\d{3}):([A-Z]{2})/g)];
const codes = new Map(pairs.map(([, numeric, alpha2]) => [numeric, alpha2]));
const displayNames = Object.fromEntries(
  ['uz', 'ru', 'en'].map((language) => [
    language,
    new Intl.DisplayNames([language], { type: 'region' }),
  ]),
);

const result = {
  '000': {
    uz: "Noma'lum davlat",
    ru: 'Неизвестное государство',
    en: 'Unknown country',
  },
};

for (const [numeric, alpha2] of [...codes].sort(([a], [b]) => a.localeCompare(b))) {
  result[numeric] = Object.fromEntries(
    Object.entries(displayNames).map(([language, formatter]) => [language, formatter.of(alpha2)]),
  );
}

fs.writeFileSync('data/country_names.json', `${JSON.stringify(result, null, 2)}\n`, 'utf8');

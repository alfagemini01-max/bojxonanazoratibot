'use strict';

/* ============================================================
   E-Bojxona Inspector Document JS v6
   - Mobile-First Road24 Auto App Style UI
   - Pure Modern SVG Icons (Zero Emojis!)
   - Top-Right Language Dropdown with Animated Transitions & Flags
   - Dynamic Realistic License Plate Generator (UZ, KZ, RU, KG, TJ, etc.)
   - Single Sticky Bottom Unified Payment Dock (1 bitta to'lash tugmasi!)
   - Working Interactive Payment Flow (Click, Payme, Uzum, Munis, Uzcard, Humo)
   - Official 3-Language PDF Generation with Stamps & Watermarks
   ============================================================ */

const dictionary = {
  uz: {
    service: 'Davlat bojxona xizmati',
    loading: 'Hujjat tekshirilmoqda…',
    loadingDesc: 'Bojxona tizimidan ma\'lumotlar olinmoqda',
    notFound: 'Hujjat topilmadi',
    notFoundHelp: 'QR-kod to\'g\'riligini tekshiring yoki bojxona xodimiga murojaat qiling.',
    verified: 'HUJJAT TASDIQLANGAN',
    revoked: 'HUJJAT BEKOR QILINGAN',
    verifiedHelp: 'Ma\'lumotlar bojxona tizimidagi yozuvga mos',
    revokedHelp: 'Bu hujjat amalda emas. Bojxona xodimiga murojaat qiling.',
    welcome: 'O\'ZBEKISTON RESPUBLIKASIGA XUSH KELIBSIZ!',
    docNumber: 'Hujjat raqami',
    vehicleSection: 'TRANSPORT VOSITASI',
    vehicleInspection: 'Nazoratdan o\'tgan',
    cleared: 'Nazoratdan o\'tgan',
    personalData: 'Shaxsiy ma\'lumotlar',
    journeyData: 'Safar ma\'lumotlari',
    officialDocs: 'RASMIY HUJJATLAR',
    registeredDocs: 'Nomingizga rasmiylashtirilgan hujjatlar',
    additionalInfo: 'Qo\'shimcha ma\'lumot',
    lawTitle: 'Qonunchilik talablariga rioya qiling',
    lawText: 'O\'zbekiston Respublikasi hududida amaldagi bojxona va yo\'l harakati xavfsizligi qoidalariga qat\'iy amal qilishingiz shart.',
    issuedBy: 'HUJJATNI RASMIYLASHTIRGAN INSPEKTOR',
    nationality: 'Fuqaroligi',
    passport: 'Pasport raqami',
    phone: 'Telefon',
    plate: 'Transport raqami',
    vehicleCountry: 'Transport davlati',
    post: 'Chegara posti',
    time: 'O\'tish vaqti',
    location: 'Yo\'nalish / joy',
    cargo: 'Yuk turi',
    status: 'Holati',
    downloadLang: 'Hujjat tili:',
    download: 'PDF yuklab olish',
    totalToPay: 'Jami to\'lov miqdori:',
    totalAmount: 'Jami to\'lov:',
    documentPayment: 'Hujjat bo\'yicha to\'lov',
    unpaidStatus: 'To\'lov kutilmoqda',
    paidStatus: 'To\'langan',
    payNow: 'To\'lash',
    allPaid: 'Barcha to\'lovlar to\'langan',
    paidBadge: 'To\'langan',
    unpaidBadge: 'To\'lov kutilmoqda',
    feeLabel: 'Yig\'im:',
    stateLabel: 'Holati:',
    completedStatus: 'Rasmiylashtirilgan',
    paymentVia: 'orqali avtomatik to\'lov',
    processing: 'To\'lov tasdiqlanmoqda…',
    paymentFailed: 'To\'lovni tasdiqlab bo\'lmadi. Qayta urinib ko\'ring.',
    inspectorDefault: 'Bojxona inspektori',
    footerAgency: 'O\'ZBEKISTON RESPUBLIKASI DAVLAT BOJXONA QO\'MITASI',
    footerSystem: 'Yagona axborot tizimi · Ishonch telefoni: 1108',
    supportPhone: '1108 · Ishonch telefoni',
    paymentBreakdown: 'Bojxona to\'lovlari',
    paymentBreakdownDesc: 'Quyidagi xizmatlar va yig\'imlar uchun to\'lov amalga oshiriladi',
    choosePaymentSystem: 'To\'lov usulini tanlash',
    chooseMethod: 'To\'lov tizimini tanlang',
    chooseMethodDesc: 'To\'lovni amalga oshirish uchun qulay usulni tanlang',
    cardDetails: 'Karta ma\'lumotlarini kiriting',
    cardNumber: 'Karta raqami',
    expiry: 'Amal qilish muddati',
    cardHolder: 'Karta egasining FISh',
    confirmPay: 'Sinov jarayonini tekshirish',
    back: 'Orqaga',
    close: 'Yopish va qaytish',
    paymentSuccess: 'To\'lov qabul qilindi',
    paymentSuccessDesc: 'To\'lov sinov tartibida avtomatik tasdiqlandi. Haqiqiy bank tranzaksiyasi amalga oshirilmadi.',
    transactionId: 'Tranzaksiya ID:',
    paidAt: 'To\'langan vaqt:',
    paidAmount: 'Tasdiqlangan summa:',
    transitDeclaration: 'Tranzit Majburiyatnomasi',
    insurancePolicy: 'Sug\'urta Polisi',
    paymentInvoice: 'Bojxona To\'lov Invoysi',
    active: 'Amalda',
    docType: 'Hujjat turi',
    issueDate: 'Rasmiylashtirilgan sana',
    validUntil: 'Amal qilish muddati',
    officialSeal: 'Rasmiy muhr',
    digitalSign: 'Elektron raqamli imzo',
    verifiedSystem: 'Tizim tekshiruvi',
    unpaidWarning: 'DIQQAT: Ushbu hujjat uchun to\'lov amalga oshirilmagan!',
    demoPaymentTitle: 'Sinov to\'lov oynasi',
    demoPaymentHelp: 'Bu bosqich interfeysni tekshirish uchun. Karta ma\'lumoti so\'ralmaydi va pul yechilmaydi. Haqiqiy to\'lov uchun bank provayderining merchant API kalitlari ulanishi kerak.',
    demoStatus: '✓ TO\'LOV QABUL QILINDI',
  },
  ru: {
    service: 'Государственная таможенная служба',
    loading: 'Документ проверяется…',
    loadingDesc: 'Получение данных из таможенной системы',
    notFound: 'Документ не найден',
    notFoundHelp: 'Проверьте QR-код или обратитесь к сотруднику таможни.',
    verified: 'ДОКУМЕНТ ПОДТВЕРЖДЁН',
    revoked: 'ДОКУМЕНТ АННУЛИРОВАН',
    verifiedHelp: 'Данные соответствуют записи в таможенной системе',
    revokedHelp: 'Документ недействителен. Обратитесь к сотруднику таможни.',
    welcome: 'ДОБРО ПОЖАЛОВАТЬ В РЕСПУБЛИКУ УЗБЕКИСТАН!',
    docNumber: 'Номер документа',
    vehicleSection: 'ТРАНСПОРТНОЕ СРЕДСТВО',
    vehicleInspection: 'Контроль пройден',
    cleared: 'Контроль пройден',
    personalData: 'Личные данные',
    journeyData: 'Данные поездки',
    officialDocs: 'ОФИЦИАЛЬНЫЕ ДОКУМЕНТЫ',
    registeredDocs: 'Документы, оформленные на ваше имя',
    additionalInfo: 'Дополнительная информация',
    lawTitle: 'Соблюдайте требования законодательства',
    lawText: 'На территории Республики Узбекистан строго соблюдайте таможенные правила и правила дорожного движения.',
    issuedBy: 'ИНСПЕКТОР, ОФОРМИВШИЙ ДОКУМЕНТ',
    nationality: 'Гражданство',
    passport: 'Паспорт',
    phone: 'Телефон',
    plate: 'Госномер',
    vehicleCountry: 'Страна транспорта',
    post: 'Пограничный пост',
    time: 'Время пересечения',
    location: 'Маршрут / место',
    cargo: 'Груз',
    status: 'Статус',
    downloadLang: 'Язык документа:',
    download: 'Скачать PDF',
    totalToPay: 'Итого к оплате:',
    totalAmount: 'Общая сумма:',
    documentPayment: 'Платёж по документу',
    unpaidStatus: 'Ожидает оплаты',
    paidStatus: 'Оплачено',
    payNow: 'Оплатить',
    allPaid: 'Все платежи оплачены',
    paidBadge: 'Оплачено',
    unpaidBadge: 'Ожидает оплаты',
    feeLabel: 'Сбор:',
    stateLabel: 'Статус:',
    completedStatus: 'Оформлено',
    paymentVia: '— автоматическая оплата',
    processing: 'Платёж подтверждается…',
    paymentFailed: 'Не удалось подтвердить платёж. Попробуйте ещё раз.',
    inspectorDefault: 'Таможенный инспектор',
    footerAgency: 'ГОСУДАРСТВЕННЫЙ ТАМОЖЕННЫЙ КОМИТЕТ РЕСПУБЛИКИ УЗБЕКИСТАН',
    footerSystem: 'Единая информационная система · Телефон доверия: 1108',
    supportPhone: '1108 · Телефон доверия',
    paymentBreakdown: 'Таможенные платежи',
    paymentBreakdownDesc: 'Оплата за следующие услуги и таможенные сборы',
    choosePaymentSystem: 'Выбрать способ оплаты',
    chooseMethod: 'Выберите платёжную систему',
    chooseMethodDesc: 'Выберите удобный способ для совершения платежа',
    cardDetails: 'Введите данные карты',
    cardNumber: 'Номер карты',
    expiry: 'Срок действия',
    cardHolder: 'Имя держателя карты',
    confirmPay: 'Проверить тестовый процесс',
    back: 'Назад',
    close: 'Закрыть и вернуться',
    paymentSuccess: 'Платёж принят',
    paymentSuccessDesc: 'Платёж автоматически подтверждён в тестовом режиме. Реальная банковская операция не выполнялась.',
    transactionId: 'ID транзакции:',
    paidAt: 'Время оплаты:',
    paidAmount: 'Подтверждённая сумма:',
    transitDeclaration: 'Транзитное Обязательство',
    insurancePolicy: 'Страховой Полис',
    paymentInvoice: 'Таможенный Платёжный Инвойс',
    active: 'Действует',
    docType: 'Тип документа',
    issueDate: 'Дата оформления',
    validUntil: 'Срок действия',
    officialSeal: 'Официальная печать',
    digitalSign: 'Электронная подпись',
    verifiedSystem: 'Проверка системы',
    unpaidWarning: 'ВНИМАНИЕ: Оплата по данному документу не произведена!',
    demoPaymentTitle: 'Тестовое платёжное окно',
    demoPaymentHelp: 'Этот этап предназначен для проверки интерфейса. Данные карты не запрашиваются, деньги не списываются. Для реальной оплаты необходимо подключить merchant API платёжного провайдера.',
    demoStatus: '✓ ПЛАТЁЖ ПРИНЯТ',
  },
  en: {
    service: 'State Customs Service',
    loading: 'Verifying document…',
    loadingDesc: 'Fetching data from the customs system',
    notFound: 'Document not found',
    notFoundHelp: 'Check the QR code or contact a customs officer.',
    verified: 'DOCUMENT VERIFIED',
    revoked: 'DOCUMENT REVOKED',
    verifiedHelp: 'The data matches the record in the customs system',
    revokedHelp: 'This document is no longer valid. Contact a customs officer.',
    welcome: 'WELCOME TO THE REPUBLIC OF UZBEKISTAN!',
    docNumber: 'Document number',
    vehicleSection: 'VEHICLE DETAILS',
    vehicleInspection: 'Control Passed',
    cleared: 'Control Passed',
    personalData: 'Personal details',
    journeyData: 'Journey details',
    officialDocs: 'OFFICIAL DOCUMENTS',
    registeredDocs: 'Documents issued in your name',
    additionalInfo: 'Additional information',
    lawTitle: 'Comply with legislation',
    lawText: 'You must strictly comply with customs and road safety regulations in the Republic of Uzbekistan.',
    issuedBy: 'DOCUMENT ISSUED BY INSPECTOR',
    nationality: 'Nationality',
    passport: 'Passport',
    phone: 'Phone',
    plate: 'Vehicle plate',
    vehicleCountry: 'Vehicle country',
    post: 'Border post',
    time: 'Crossing time',
    location: 'Route / destination',
    cargo: 'Cargo type',
    status: 'Status',
    downloadLang: 'Document language:',
    download: 'Download PDF',
    totalToPay: 'Total to pay:',
    totalAmount: 'Total amount:',
    documentPayment: 'Document payment',
    unpaidStatus: 'Awaiting payment',
    paidStatus: 'Paid',
    payNow: 'Pay Now',
    allPaid: 'All payments completed',
    paidBadge: 'Paid',
    unpaidBadge: 'Payment pending',
    feeLabel: 'Fee:',
    stateLabel: 'Status:',
    completedStatus: 'Issued',
    paymentVia: '- automatic payment',
    processing: 'Confirming payment…',
    paymentFailed: 'Payment could not be confirmed. Please try again.',
    inspectorDefault: 'Customs inspector',
    footerAgency: 'STATE CUSTOMS COMMITTEE OF THE REPUBLIC OF UZBEKISTAN',
    footerSystem: 'Unified information system · Hotline: 1108',
    supportPhone: '1108 · Hotline',
    paymentBreakdown: 'Customs Fees & Dues',
    paymentBreakdownDesc: 'Payment breakdown for registered customs services and fees',
    choosePaymentSystem: 'Choose payment method',
    chooseMethod: 'Select payment system',
    chooseMethodDesc: 'Select your preferred payment method',
    cardDetails: 'Enter card details',
    cardNumber: 'Card number',
    expiry: 'Expiry date',
    cardHolder: 'Cardholder name',
    confirmPay: 'Verify test flow',
    back: 'Back',
    close: 'Close and return',
    paymentSuccess: 'Payment accepted',
    paymentSuccessDesc: 'Payment was confirmed automatically in test mode. No real banking transaction was performed.',
    transactionId: 'Transaction ID:',
    paidAt: 'Paid at:',
    paidAmount: 'Confirmed amount:',
    transitDeclaration: 'Transit Declaration',
    insurancePolicy: 'Insurance Policy',
    paymentInvoice: 'Customs Payment Invoice',
    active: 'Active',
    docType: 'Document type',
    issueDate: 'Issue date',
    validUntil: 'Valid until',
    officialSeal: 'Official seal',
    digitalSign: 'Digital signature',
    verifiedSystem: 'System verification',
    unpaidWarning: 'WARNING: Payment for this document has not been made!',
    demoPaymentTitle: 'Test payment window',
    demoPaymentHelp: 'This step verifies the interface. Card details are not requested and no money is charged. A real payment requires the provider merchant API credentials.',
    demoStatus: '✓ PAYMENT ACCEPTED',
  }
};

/* ── Application State ── */
let lang = 'uz';
let record = null;
let selectedDlLang = 'uz';
let allPaymentsPaid = false;
let paidDocs = {}; // doc.code -> boolean
let selectedPayMethod = 'payme';

const DEFAULT_PAYMENT_ITEMS = [
  { code: 'customs-entry', title_uz: "Bojxona yig'imi (kirish)", title_ru: 'Таможенный сбор (въезд)', title_en: 'Customs entry fee', amount_uzs: 110000 },
  { code: 'veterinary-control', title_uz: 'Veterinariya nazorati', title_ru: 'Ветеринарный контроль', title_en: 'Veterinary control', amount_uzs: 93632 },
  { code: 'osago-insurance', title_uz: "OSAGO sug'urta polisi", title_ru: 'Страховой полис ОСАГО', title_en: 'OSAGO insurance policy', amount_uzs: 308000 },
  { code: 'terminal-warehouse', title_uz: "Terminal / ombor yig'imi", title_ru: 'Терминальный / складской сбор', title_en: 'Terminal / warehouse fee', amount_uzs: 110000 }
];

const VEHICLE_CATALOG = {
  sedan: 'Yengil sedan', hatchback: 'Xetchbek', suv: 'Krossover / SUV', minivan: 'Miniven', pickup: 'Pikap',
  microbus: 'Mikroavtobus', 'city-bus': 'Shahar avtobusi', 'coach-bus': 'Sayohat avtobusi', 'cargo-van': 'Yuk furgoni',
  'box-truck': 'Yopiq kuzovli yuk mashinasi', 'dump-truck': 'Samosval', 'tanker-truck': 'Sisterna',
  'refrigerated-truck': 'Refrejerator', 'flatbed-truck': 'Bortli yuk mashinasi', 'tractor-unit': 'Tyagach',
  'box-semitrailer': 'Fura / yarim tirkama', 'curtain-semitrailer': 'Tentli yarim tirkama',
  'container-truck': 'Konteyner tashuvchi', 'car-carrier': 'Avtomobil tashuvchi', 'heavy-haul-lowboy': 'Og\'ir yuk trali'
};

const VEHICLE_LABELS = {
  ru: {
    sedan: 'Легковой седан', hatchback: 'Хэтчбек', suv: 'Кроссовер / SUV', minivan: 'Минивэн', pickup: 'Пикап',
    microbus: 'Микроавтобус', 'city-bus': 'Городской автобус', 'coach-bus': 'Туристический автобус', 'cargo-van': 'Грузовой фургон',
    'box-truck': 'Фургон-грузовик', 'dump-truck': 'Самосвал', 'tanker-truck': 'Цистерна', 'refrigerated-truck': 'Рефрижератор',
    'flatbed-truck': 'Бортовой грузовик', 'tractor-unit': 'Тягач', 'box-semitrailer': 'Фура / полуприцеп',
    'curtain-semitrailer': 'Тентованный полуприцеп', 'container-truck': 'Контейнеровоз', 'car-carrier': 'Автовоз', 'heavy-haul-lowboy': 'Тяжёлый трал'
  },
  en: {
    sedan: 'Passenger sedan', hatchback: 'Hatchback', suv: 'Crossover / SUV', minivan: 'Minivan', pickup: 'Pickup',
    microbus: 'Minibus', 'city-bus': 'City bus', 'coach-bus': 'Coach bus', 'cargo-van': 'Cargo van',
    'box-truck': 'Box truck', 'dump-truck': 'Dump truck', 'tanker-truck': 'Tanker truck', 'refrigerated-truck': 'Refrigerated truck',
    'flatbed-truck': 'Flatbed truck', 'tractor-unit': 'Tractor unit', 'box-semitrailer': 'Box semi-trailer',
    'curtain-semitrailer': 'Curtain semi-trailer', 'container-truck': 'Container truck', 'car-carrier': 'Car carrier', 'heavy-haul-lowboy': 'Heavy-haul lowboy'
  }
};

function vehicleTypeLabel(type) {
  return VEHICLE_LABELS[lang]?.[type] || VEHICLE_CATALOG[type] || VEHICLE_CATALOG.sedan;
}

function localizedDocumentTitle(doc, idx) {
  const raw = String(doc?.title || doc?.type || doc?.code || '').toLowerCase();
  if (raw.includes('invoys') || raw.includes('invoice') || idx === 0) return t('paymentInvoice');
  if (raw.includes('sug\'urta') || raw.includes('insurance') || raw.includes('страх') || doc?.code?.startsWith('ETSD') || idx === 2) return t('insurancePolicy');
  if (raw.includes('majbur') || raw.includes('transit') || raw.includes('обяз') || idx === 1) return t('transitDeclaration');
  return doc?.[`title_${lang}`] || doc?.title || t('registeredDocs');
}

function localizedInspectorName(value) {
  const raw = String(value || '').trim();
  if (!raw || /^(bojxona inspektori|navbatchi inspektor)$/i.test(raw)) return t('inspectorDefault');
  return raw;
}

function inferVehicleImageType(payload) {
  const explicit = String(payload.vehicle_image_type || '').trim();
  if (VEHICLE_CATALOG[explicit]) return explicit;
  const text = `${payload.vehicle_model || ''} ${payload.cargo || ''} ${payload.trailer_plate || ''}`.toLowerCase();
  const rules = [
    ['heavy-haul-lowboy', /lowboy|low.loader|tral|трал|og['’]?ir yuk/],
    ['car-carrier', /car.?carrier|avto.?tash|avtovoz|автовоз/],
    ['container-truck', /container|konteyner|контейнер/],
    ['tanker-truck', /tanker|sisterna|цистерн/],
    ['refrigerated-truck', /refriger|reefer|refri|sovut|холодиль/],
    ['dump-truck', /dump|samosval|tipper|самосвал/],
    ['curtain-semitrailer', /curtain|tautliner|tentli|tentov|тент/],
    ['box-semitrailer', /semi.?trailer|yarim.?tirkama|pritsep|прицеп|fura|фура/],
    ['tractor-unit', /tractor|tyagach|тягач|scania|volvo|daf|actros|iveco/],
    ['flatbed-truck', /flatbed|bortli|борт/],
    ['coach-bus', /coach|turist|sayohat|междугород/],
    ['city-bus', /city.?bus|shahar.?avtobus|автобус/],
    ['microbus', /microbus|mikroavtobus|sprinter|hiace|damas|микроавтобус/],
    ['cargo-van', /cargo.?van|furgon|transit|фургон/],
    ['pickup', /pickup|pikap|hilux|пикап/],
    ['minivan', /minivan|staria|carnival|sienna|минивэн/],
    ['suv', /suv|crossover|krossover|captiva|tracker|land.?cruiser|tahoe|rav4|джип/],
    ['hatchback', /hatch|spark|matiz|хэтчбек/],
    ['box-truck', /box.?truck|isuzu|fuso|yuk.?mash|грузов/]
  ];
  const matched = rules.find(([, pattern]) => pattern.test(text));
  if (matched?.[0] === 'tractor-unit' && String(payload.trailer_plate || '').trim()) {
    return 'box-semitrailer';
  }
  if (!matched && String(payload.trailer_plate || '').trim()) return 'box-semitrailer';
  return matched ? matched[0] : 'sedan';
}

/* ── DOM & i18n Helpers ── */
const $ = id => document.getElementById(id);
const t = key => dictionary[lang]?.[key] || dictionary.uz[key] || key;
function setText(id, val) { const el = $(id); if (el) el.textContent = val || '—'; }
function escapeHTML(value) {
  return String(value ?? '').replace(/[&<>'"]/g, char => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;'
  }[char]));
}

function paymentItems() {
  const stored = record?.payload?.payments;
  return Array.isArray(stored) && stored.length ? stored : DEFAULT_PAYMENT_ITEMS;
}

function paymentTotalUzs() {
  const listedTotal = paymentItems().reduce((sum, item) => sum + Math.max(0, Number(item?.amount_uzs) || 0), 0);
  const storedTotal = Number(record?.payload?.payment_total_uzs || 0);
  return Math.round(listedTotal || (Number.isFinite(storedTotal) ? storedTotal : 0));
}

function formatUzs(value = paymentTotalUzs()) {
  const amount = new Intl.NumberFormat('ru-RU').format(Math.round(Number(value) || 0)).replace(/\u00a0/g, ' ');
  return `${amount} UZS`;
}

function renderPaymentBreakdown() {
  const container = $('payment-fee-list');
  if (!container) return;
  container.replaceChildren();
  paymentItems().forEach(item => {
    const row = document.createElement('div');
    row.className = 'fee-row-item';
    const info = document.createElement('div');
    const title = document.createElement('b');
    title.textContent = item[`title_${lang}`] || item.title_uz || item.code || t('documentPayment');
    const status = document.createElement('small');
    status.textContent = t(allPaymentsPaid ? 'paidStatus' : 'unpaidStatus');
    info.append(title, status);
    const amount = document.createElement('span');
    amount.textContent = formatUzs(item.amount_uzs);
    row.append(info, amount);
    container.appendChild(row);
  });
}

function formatDate(val) {
  const d = new Date(val);
  if (isNaN(d.getTime())) return String(val || '—');
  const locales = { uz: 'uz-UZ', ru: 'ru-RU', en: 'en-GB' };
  return new Intl.DateTimeFormat(locales[lang] || 'uz-UZ', { dateStyle: 'long', timeStyle: 'short' }).format(d);
}

function formatDateSimple(val) {
  const d = new Date(val);
  if (isNaN(d.getTime())) return String(val || '');
  return d.toLocaleDateString('ru-RU');
}

/* Country flag SVG markup */
function countryFlagImg(iso, alt = '') {
  const code = String(iso || '').toLowerCase().trim();
  if (!code || !/^[a-z]{2}$/.test(code)) {
    return `<svg class="detail-flag-fallback" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>`;
  }
  return `<img src="/static/webapp/flags/${code}.svg" alt="${alt || code}" class="detail-flag">`;
}

/* Helper to map country names to ISO codes */
function getCountryIso(nameOrCode) {
  const str = String(nameOrCode || '').toLowerCase().trim();
  if (str.length === 2) return str;
  if (str.includes('o\'zbek') || str.includes('uzbek') || str.includes('узбек')) return 'uz';
  if (str.includes('qozog') || str.includes('kazakh') || str.includes('казах')) return 'kz';
  if (str.includes('rossi') || str.includes('russia') || str.includes('росси')) return 'ru';
  if (str.includes('qirg') || str.includes('kyrgyz') || str.includes('кыргыз')) return 'kg';
  if (str.includes('tojik') || str.includes('tajik') || str.includes('таджик')) return 'tj';
  if (str.includes('turkman') || str.includes('turkmen') || str.includes('туркмен')) return 'tm';
  if (str.includes('turki') || str.includes('turkey') || str.includes('турци')) return 'tr';
  if (str.includes('xitoy') || str.includes('china') || str.includes('китай')) return 'cn';
  if (str.includes('afg') || str.includes('afghan') || str.includes('афган')) return 'af';
  if (str.includes('ozar') || str.includes('azer') || str.includes('азерб')) return 'az';
  if (str.includes('eron') || str.includes('iran') || str.includes('иран')) return 'ir';
  if (str.includes('belarus') || str.includes('беларус')) return 'by';
  return 'uz';
}

/* Detail Row Component */
function renderDetailRow(label, value, flagIso = null) {
  const row = document.createElement('div');
  row.className = 'detail-row';

  const lbl = document.createElement('span');
  lbl.className = 'detail-label';
  lbl.textContent = label;

  const val = document.createElement('span');
  val.className = 'detail-value';

  if (flagIso) {
    val.innerHTML = `${countryFlagImg(flagIso)} <span>${value || '—'}</span>`;
  } else {
    val.textContent = value || '—';
  }

  row.append(lbl, val);
  return row;
}

/* ── Language Switcher Dropdown Logic ── */
function initLanguageDropdown() {
  const trigger = $('lang-trigger');
  const menu = $('lang-menu');
  if (!trigger || !menu) return;

  trigger.addEventListener('click', (e) => {
    e.stopPropagation();
    const isOpen = menu.classList.contains('open');
    if (isOpen) {
      closeLangDropdown();
    } else {
      openLangDropdown();
    }
  });

  document.querySelectorAll('.lang-option').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      const newLang = btn.dataset.lang;
      if (newLang) {
        setLanguage(newLang);
        closeLangDropdown();
      }
    });
  });

  // Close on outside click
  document.addEventListener('click', (e) => {
    if (!e.target.closest('.lang-dropdown-wrapper')) {
      closeLangDropdown();
    }
  });
}

function openLangDropdown() {
  const trigger = $('lang-trigger');
  const menu = $('lang-menu');
  if (trigger && menu) {
    menu.classList.add('open');
    trigger.setAttribute('aria-expanded', 'true');
  }
}

function closeLangDropdown() {
  const trigger = $('lang-trigger');
  const menu = $('lang-menu');
  if (trigger && menu) {
    menu.classList.remove('open');
    trigger.setAttribute('aria-expanded', 'false');
  }
}

function setLanguage(newLang) {
  lang = newLang;
  selectedDlLang = newLang;
  document.documentElement.lang = lang;

  // Update trigger UI
  const flagMap = { uz: '/static/webapp/flags/uz.svg', ru: '/static/webapp/flags/ru.svg', en: '/static/webapp/flags/gb.svg' };
  const textMap = { uz: "O'zbek", ru: "Русский", en: "English" };

  const curFlag = $('lang-cur-flag');
  const curText = $('lang-cur-text');
  if (curFlag) curFlag.src = flagMap[lang] || flagMap.uz;
  if (curText) curText.textContent = textMap[lang] || textMap.uz;

  // Update active state in dropdown
  document.querySelectorAll('.lang-option').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.lang === lang);
  });
  document.querySelectorAll('.pdf-lang-chip').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.dlang === selectedDlLang);
  });

  // Re-translate all elements with data-i18n
  applyLanguage();
}

function applyLanguage() {
  document.querySelectorAll('[data-i18n]').forEach(el => {
    const key = el.dataset.i18n;
    if (key && dictionary[lang]?.[key]) {
      el.textContent = dictionary[lang][key];
    }
  });

  if (record) {
    render(record);
  }
}

/* ── Dynamic Authentic License Plate ── */
function renderVehiclePlate(plateRaw, countryRaw) {
  const container = $('plate-wrapper');
  if (!container) return;

  const plate = String(plateRaw || '').toUpperCase().trim();
  const countryIso = getCountryIso(countryRaw);

  let html = '';

  if (countryIso === 'uz') {
    // Uzbek Plate Style: [ 01 | E 685 YB | [🇺🇿 UZ] ]
    const match = plate.match(/^(\d{2})\s*(.*)$/);
    const region = match ? match[1] : '01';
    const numPart = match ? match[2].trim() : plate;

    html = `
      <div class="license-plate plate-uz">
        <span class="reg-code">${region}</span>
        <div class="plate-divider"></div>
        <span class="main-number">${escapeHTML(numPart || '777 ZAA')}</span>
        <div class="flag-box">
          <img src="/static/webapp/flags/uz.svg" alt="UZ">
          <span class="country-code">UZ</span>
        </div>
      </div>
    `;
  } else if (countryIso === 'kz') {
    // Kazakh Plate Style: [ 🇰🇿 KZ | 123 ABC | 02 ]
    const parts = plate.split(/\s+/);
    let numPart = plate;
    let region = '02';
    if (parts.length >= 2 && /^\d{2}$/.test(parts[parts.length - 1])) {
      region = parts[parts.length - 1];
      numPart = parts.slice(0, -1).join(' ');
    }

    html = `
      <div class="license-plate plate-kz">
        <div class="flag-box-left">
          <img src="/static/webapp/flags/kz.svg" alt="KZ">
          <span class="country-code">KZ</span>
        </div>
        <span class="main-number">${escapeHTML(numPart)}</span>
        <div class="plate-divider"></div>
        <span class="reg-code">${region}</span>
      </div>
    `;
  } else if (countryIso === 'ru') {
    // Russian Plate Style: [ A 123 AA | 777 RUS 🇷🇺 ]
    const parts = plate.split(/\s+/);
    let numPart = plate;
    let region = '777';
    if (parts.length >= 2 && /^\d{2,3}$/.test(parts[parts.length - 1])) {
      region = parts[parts.length - 1];
      numPart = parts.slice(0, -1).join(' ');
    }

    html = `
      <div class="license-plate plate-ru">
        <span class="main-number">${escapeHTML(numPart)}</span>
        <div class="plate-divider"></div>
        <div class="reg-box-ru">
          <span class="reg-code">${region}</span>
          <div class="ru-footer">
            <span>RUS</span>
            <img src="/static/webapp/flags/ru.svg" alt="RUS">
          </div>
        </div>
      </div>
    `;
  } else {
    // Generic International Plate
    html = `
      <div class="license-plate plate-generic">
        <img src="/static/webapp/flags/${countryIso}.svg" alt="${countryIso}">
        <span class="main-number">${escapeHTML(plate || 'AA 001 AA')}</span>
        <span class="country-code">${countryIso.toUpperCase()}</span>
      </div>
    `;
  }

  container.innerHTML = html;
}

/* ── Main Render Function ── */
function render(item) {
  record = item;
  const payload = item.payload || {};
  const isActive = item.status === 'active';
  allPaymentsPaid = payload.payment_status === 'paid';

  // Verified Status Pill
  const chip = $('verified-chip');
  if (chip) {
    chip.classList.toggle('revoked', !isActive);
    chip.classList.toggle('verified', isActive);
    const chipText = $('status-chip-text');
    if (chipText) chipText.textContent = t(isActive ? 'verified' : 'revoked');
  }

  // Driver Name & Document Number
  setText('driver-name', item.driver_name);
  setText('document-number', item.document_no);
  const totalLabel = formatUzs();
  setText('modal-total', totalLabel);
  setText('confirm-total', totalLabel);
  setText('success-total', totalLabel);
  renderPaymentBreakdown();

  // Vehicle Hero Card
  renderVehiclePlate(item.vehicle_plate, payload.vehicle_country);
  setText('quick-post-name', item.post_name);
  setText('quick-crossing-time', formatDate(item.crossing_at));

  // Choose the matching lightweight vehicle asset from the stored type or model keywords.
  const modelLabel = $('vehicle-model-label');
  const vehicleType = inferVehicleImageType(payload);
  if (modelLabel) {
    modelLabel.textContent = String(payload.vehicle_model || '').trim() || vehicleTypeLabel(vehicleType);
  }
  const vehicleImage = $('vehicle-profile-img');
  if (vehicleImage) {
    vehicleImage.src = `/static/webapp/vehicles/${vehicleType}.webp`;
    vehicleImage.alt = `${modelLabel?.textContent || vehicleTypeLabel(vehicleType)} - ${item.vehicle_plate || ''}`.trim();
  }

  // Identity / Personal Details
  const identity = $('identity-list');
  if (identity) {
    const natIso = getCountryIso(payload.nationality);
    identity.replaceChildren(
      renderDetailRow(t('nationality'), payload.nationality, natIso),
      renderDetailRow(t('passport'), payload.passport),
      renderDetailRow(t('phone'), payload.phone)
    );
  }

  // Journey Details
  const journey = $('journey-list');
  if (journey) {
    const vCountryIso = getCountryIso(payload.vehicle_country);
    journey.replaceChildren(
      renderDetailRow(t('plate'), item.vehicle_plate),
      renderDetailRow(t('vehicleSection'), String(payload.vehicle_model || '').trim() || vehicleTypeLabel(vehicleType)),
      renderDetailRow(t('vehicleCountry'), payload.vehicle_country, vCountryIso),
      renderDetailRow(t('post'), item.post_name),
      renderDetailRow(t('time'), formatDate(item.crossing_at)),
      renderDetailRow(t('location'), payload.location),
      renderDetailRow(t('cargo'), payload.cargo)
    );
  }

  // Official Documents List
  renderDocuments(payload.documents || []);

  // Additional Note
  const info = String(payload.additional_info || '').trim();
  const noteCard = $('note-card');
  if (noteCard) {
    noteCard.hidden = !info;
    setText('additional-info', info);
  }

  // Inspector Details
  setText('inspector-name', localizedInspectorName(item.inspector_name));
  setText('issued-at', `${item.post_name} · ${formatDate(item.crossing_at)}`);

  // Update Single Bottom Pay Dock
  updateStickyPayDock();
}

/* ── Render Documents (NO ugly buttons!) ── */
function renderDocuments(docs) {
  const container = $('doc-cards-list');
  if (!container) return;

  const defaultDocs = [
    { code: record?.document_no || 'DOC', title: t('registeredDocs'), type: 'document' },
  ];

  const listToRender = (docs && docs.length) ? docs : defaultDocs;

  container.innerHTML = '';

  listToRender.forEach((doc, idx) => {
    const isPaid = allPaymentsPaid || paidDocs[doc.code] || doc.paid;

    // SVG icon by document type
    let iconSvg = '';
    if (doc.code?.startsWith('AT') || idx === 0) {
      // Invoice icon
      iconSvg = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="1" y="4" width="22" height="16" rx="2" ry="2"/><line x1="1" y1="10" x2="23" y2="10"/></svg>`;
    } else if (doc.code?.startsWith('ETSD') || idx === 2) {
      // Insurance shield icon
      iconSvg = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>`;
    } else {
      // Transit file-check icon
      iconSvg = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><polyline points="9 15 11 17 15 13"/></svg>`;
    }

    const docCard = document.createElement('article');
    docCard.className = 'doc-item-card';

    docCard.innerHTML = `
      <div class="doc-item-top">
        <div class="doc-type-info">
          <div class="doc-type-icon">
            ${iconSvg}
          </div>
          <div class="doc-meta">
            <b>${escapeHTML(localizedDocumentTitle(doc, idx))}</b>
            <small>${escapeHTML(doc.code || 'DOC')}</small>
          </div>
        </div>
        <div class="doc-status-badge ${isPaid ? 'paid' : 'unpaid'}">
          ${isPaid
            ? `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><polyline points="20 6 9 17 4 12"/></svg> <span>${t('paidBadge')}</span>`
            : `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg> <span>${t('unpaidBadge')}</span>`
          }
        </div>
      </div>
      <div class="doc-item-actions">
        <div class="doc-fee-preview">
          <span>${t(isPaid ? 'stateLabel' : 'feeLabel')}</span>
          <strong>${isPaid ? t('paidStatus') : t('completedStatus')}</strong>
        </div>
        <button type="button" class="doc-download-btn" data-doc-idx="${idx}">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
            <polyline points="7 10 12 15 17 10"/>
            <line x1="12" y1="15" x2="12" y2="3"/>
          </svg>
          <span>${t('download')}</span>
        </button>
      </div>
    `;

    // Download click handler
    const dlBtn = docCard.querySelector('.doc-download-btn');
    if (dlBtn) {
      dlBtn.addEventListener('click', () => downloadDocumentPDF(doc, selectedDlLang, idx));
    }

    container.appendChild(docCard);
  });
}

/* ── Update Single Bottom Pay Dock ── */
function updateStickyPayDock() {
  const dock = $('sticky-pay-dock');
  const btn = $('dock-pay-btn');
  const btnLabel = $('dock-btn-label');
  const badge = $('dock-status-badge');
  const amount = $('dock-amount-val');

  if (!dock) return;
  dock.hidden = paymentTotalUzs() <= 0;
  if (dock.hidden) return;

  if (allPaymentsPaid) {
    if (btn) {
      btn.className = 'dock-pay-btn all-paid';
      btn.disabled = true;
    }
    if (btnLabel) btnLabel.textContent = t('allPaid');
    if (badge) {
      badge.className = 'dock-status-badge paid';
      badge.textContent = t('paidStatus');
    }
    if (amount) amount.textContent = '0 UZS';
  } else {
    if (btn) {
      btn.className = 'dock-pay-btn';
      btn.disabled = false;
    }
    if (btnLabel) btnLabel.textContent = t('payNow');
    if (badge) {
      badge.className = 'dock-status-badge';
      badge.textContent = t('unpaidStatus');
    }
    if (amount) amount.textContent = formatUzs();
  }
}

/* ── Unified Payment Modal Flow ── */
function currentPublicToken() {
  const pathParts = location.pathname.split('/').filter(Boolean);
  const token = pathParts[pathParts.length - 1];
  return token && token !== 'visit' ? token : '';
}

async function openUnifiedPayModal() {
  if (allPaymentsPaid || !record) return;
  const total = paymentTotalUzs();
  allPaymentsPaid = true;
  record.payload = { ...(record.payload || {}), payment_status: 'paid', paid_at: new Date().toISOString() };
  renderDocuments(record.payload.documents || []);
  updateStickyPayDock();

  const modal = $('payment-modal');
  if (modal) {
    modal.hidden = false;
    document.body.style.overflow = 'hidden';
  }
  const txId = $('tx-id-val');
  const txTime = $('tx-time-val');
  if (txId) txId.textContent = 'AUTO-' + new Date().getFullYear() + '-' + Math.floor(10000000 + Math.random() * 90000000);
  if (txTime) {
    const locales = { uz: 'uz-UZ', ru: 'ru-RU', en: 'en-GB' };
    txTime.textContent = new Date().toLocaleString(locales[lang] || 'uz-UZ');
  }
  setText('success-total', formatUzs(total));
  togglePaySteps(4);

  try {
    const token = currentPublicToken();
    if (!token) throw new Error('missing-token');
    const response = await fetch(`/api/inspector/documents/${encodeURIComponent(token)}/payments/accept`, {
      method: 'POST',
      headers: { Accept: 'application/json' },
      cache: 'no-store'
    });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const result = await response.json();
    if (result.paid_at) record.payload.paid_at = result.paid_at;
  } catch (error) {
    console.error('Automatic payment confirmation failed:', error);
    allPaymentsPaid = false;
    record.payload.payment_status = 'pending';
    renderDocuments(record.payload.documents || []);
    updateStickyPayDock();
    closePayModal();
    alert(t('paymentFailed'));
  }
}

function closePayModal() {
  const modal = $('payment-modal');
  if (modal) {
    modal.hidden = true;
    document.body.style.overflow = '';
  }
}

function showPayStep1() { togglePaySteps(1); }
function showPayStep2() { togglePaySteps(2); }

function showPayStep3(method) {
  selectedPayMethod = method;
  const names = {
    payme: 'Payme',
    click: 'Click Up',
    uzum: 'Uzum Bank',
    munis: 'Munis DBQ',
    uzcard: 'Uzcard',
    humo: 'Humo Card'
  };
  const banner = $('selected-method-banner');
  if (banner) banner.textContent = `${names[method] || method} ${t('paymentVia')}`;

  const btn = $('pay-submit-text');
  if (btn) btn.textContent = `${t('confirmPay')} · ${formatUzs()}`;

  togglePaySteps(3);
}

function togglePaySteps(step) {
  [1, 2, 3, 4].forEach(n => {
    const el = $(`pay-step-${n}`);
    if (el) el.hidden = n !== step;
  });
}

function processUnifiedPayment() {
  return openUnifiedPayModal();
}

/* ── PDF Generation Logic ── */
async function downloadDocumentPDF(doc, dlLang, fallbackIdx = 0) {
  if (!record) return;
  const token = currentPublicToken();
  if (!token) return;
  const link = document.createElement('a');
  link.href = `/api/inspector/documents/${encodeURIComponent(token)}/documents/${fallbackIdx}.pdf?lang=${encodeURIComponent(dlLang || 'uz')}`;
  link.download = `bojxona-${record.document_no || 'hujjat'}-${fallbackIdx + 1}.pdf`;
  link.hidden = true;
  document.body.appendChild(link);
  link.click();
  link.remove();
}

function getLogoSvg() {
  return `<img src="/static/webapp/customs-emblem.png" width="56" height="56" style="object-fit:contain" alt="DBQ">`;
}

/* 1. Tranzit Majburiyatnomasi PDF */
function buildTransitPDF(item, doc, L, isPaid) {
  const payload = item.payload || {};
  const docNo = doc ? doc.code : item.document_no;
  const paymentStatus = isPaid
    ? `<span style="background:#ecfdf5;color:#065f46;border:1px solid #a7f3d0;padding:4px 12px;border-radius:20px;font-weight:800;font-size:11px;">✓ TO'LANGAN / PAID</span>`
    : `<span style="background:#fffbeb;color:#92400e;border:1px solid #fde68a;padding:4px 12px;border-radius:20px;font-weight:800;font-size:11px;">⏳ KUTILMOQDA</span>`;

  return `<!DOCTYPE html><html lang="${lang}"><head><meta charset="UTF-8">
  <title>${L.transitDeclaration} — ${docNo}</title>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800;900&family=Space+Mono:wght@400;700&display=swap');
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: 'Inter', Arial, sans-serif; background: #525659; color: #1a1c1e; }
    .no-print { background: #063c32; color: #fff; padding: 12px 20px; display: flex; justify-content: space-between; align-items: center; }
    .no-print button { background: #0b5949; color: #fff; border: 1px solid #d8ad58; padding: 10px 22px; border-radius: 8px; font-weight: 700; cursor: pointer; display: flex; align-items: center; gap: 8px; font-size: 13px; }
    .a4 { width: 210mm; min-height: 297mm; margin: 20px auto; background: #fff; padding: 12mm; box-shadow: 0 8px 30px rgba(0,0,0,.3); display: flex; flex-direction: column; justify-content: space-between; }
    .header { display: flex; justify-content: space-between; align-items: flex-start; border-bottom: 2px solid #0b4f35; padding-bottom: 12px; margin-bottom: 16px; }
    .brand { display: flex; align-items: center; gap: 12px; }
    .brand-text h1 { font-size: 13px; font-weight: 900; text-transform: uppercase; color: #0b4f35; letter-spacing: .05em; }
    .brand-text p { font-size: 10px; color: #6b7280; margin-top: 2px; }
    .status-badge { border: 2px solid #0b4f35; background: #ecfdf5; color: #0b4f35; padding: 4px 14px; border-radius: 6px; font-size: 11px; font-weight: 800; text-transform: uppercase; }
    .title-bar { background: linear-gradient(135deg, #063c32, #0b5949); color: #fff; padding: 12px 18px; border-radius: 8px; display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px; border-left: 4px solid #d8ad58; }
    .title-bar h2 { font-family: 'Space Mono', monospace; font-size: 16px; font-weight: 700; }
    .title-bar small { font-size: 10px; color: #86efac; }
    .grid2 { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 14px; }
    .box { border: 1px solid #e5e7eb; border-radius: 6px; padding: 12px; background: #f9fafb; }
    .box h4 { font-size: 9px; text-transform: uppercase; letter-spacing: .1em; color: #6b7280; font-weight: 700; border-bottom: 1px solid #e5e7eb; padding-bottom: 6px; margin-bottom: 8px; }
    .row { display: flex; justify-content: space-between; padding: 4px 0; font-size: 11px; border-bottom: 1px dashed #f3f4f6; }
    .row:last-child { border: none; }
    .row span { color: #6b7280; }
    .row strong { font-family: 'Space Mono', monospace; font-size: 10px; color: #1a1c1e; }
    .obligations { border: 1px solid #e5e7eb; border-radius: 6px; padding: 12px; background: #fafafa; margin-bottom: 14px; }
    .obligations h4 { font-size: 9px; text-transform: uppercase; letter-spacing: .1em; color: #6b7280; font-weight: 700; border-bottom: 1px solid #e5e7eb; padding-bottom: 6px; margin-bottom: 8px; }
    .obl-item { display: flex; gap: 8px; font-size: 10px; color: #374151; margin-bottom: 6px; line-height: 1.4; }
    .obl-check { color: #0b5949; font-weight: 900; flex-shrink: 0; }
    .stamp-row { display: flex; justify-content: space-between; align-items: center; border: 2px dashed #d1d5db; border-radius: 8px; padding: 12px; }
    .stamp-circle { width: 72px; height: 72px; border-radius: 50%; border: 2px solid #0b4f35; display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; background: #f0fdf4; color: #0b4f35; padding: 4px; }
    .stamp-circle span { font-size: 6px; font-weight: 800; text-transform: uppercase; line-height: 1.2; }
    .eri-text small { font-size: 9px; color: #6b7280; display: block; margin-top: 2px; font-family: 'Space Mono', monospace; }
    .footer-doc { border-top: 1px solid #d1d5db; padding-top: 10px; margin-top: 16px; display: flex; justify-content: space-between; font-size: 9px; color: #6b7280; }
    @media print { body { background: none; } .no-print { display: none !important; } .a4 { box-shadow: none; margin: 0; width: 100%; min-height: auto; } }
    @page { size: A4; margin: 10mm; }
  </style></head><body>
  <div class="no-print">
    <div style="display:flex;align-items:center;gap:10px">
      <span style="width:10px;height:10px;border-radius:50%;background:#34d399;display:inline-block"></span>
      <span style="font-size:13px;font-weight:600">${L.transitDeclaration} · A4</span>
    </div>
    <span>PDF / Chop etish oynasi</span>
  </div>
  <div class="a4">
    <div>
      <div class="header">
        <div class="brand">
          ${getLogoSvg()}
          <div class="brand-text">
            <small style="font-size:10px;color:#6b7280;text-transform:uppercase;font-weight:600">O'zbekiston Respublikasi</small>
            <h1>Davlat Bojxona Qo'mitasi</h1>
            <p>Bojxona tranziti nazorati va kafolati bosh boshqarmasi</p>
          </div>
        </div>
        <div style="text-align:right">
          <div class="status-badge">● AMALDA / FAOL</div>
          <div style="font-size:9px;color:#6b7280;margin-top:6px;font-family:'Space Mono',monospace">
            Guvohnoma: № 2026-UZ-MB<br>Ro'yxat: #UZ-DBQ-84920
          </div>
          <div style="margin-top:6px">${paymentStatus}</div>
        </div>
      </div>

      <div class="title-bar">
        <div>
          <small>${L.transitDeclaration?.toUpperCase() || 'TRANZIT MAJBURIYATNOMASI'}</small>
          <h2>${docNo || item.document_no}</h2>
        </div>
        <div style="text-align:right;font-size:10px;color:#86efac">
          <div>${L.issueDate || 'Rasmiylashtirilgan'}:</div>
          <strong style="font-family:'Space Mono',monospace">${formatDateSimple(item.crossing_at)}</strong>
        </div>
      </div>

      <div class="grid2">
        <div class="box">
          <h4>${L.personalData || 'Shaxsiy ma\'lumotlar'}</h4>
          <div class="row"><span>${L.passport || 'Pasport'}:</span><strong>${payload.passport || '—'}</strong></div>
          <div class="row"><span>${L.nationality || 'Fuqaroligi'}:</span><strong>${payload.nationality || '—'}</strong></div>
          <div class="row"><span>${L.phone || 'Telefon'}:</span><strong>${payload.phone || '—'}</strong></div>
        </div>
        <div class="box">
          <h4>${L.journeyData || 'Safar ma\'lumotlari'}</h4>
          <div class="row"><span>${L.plate || 'Transport'}:</span><strong>${item.vehicle_plate || '—'}</strong></div>
          <div class="row"><span>${L.vehicleCountry || 'Davlat'}:</span><strong>${payload.vehicle_country || '—'}</strong></div>
          <div class="row"><span>${L.post || 'Post'}:</span><strong>${item.post_name || '—'}</strong></div>
        </div>
      </div>

      <div class="obligations">
        <h4>${L.lawTitle || 'Majburiyatlar'}</h4>
        <div class="obl-item"><span class="obl-check">✓</span><div>Bojxona identifikatsiya vositalari butunligini saqlash va ruxsatsiz buzmaslik.</div></div>
        <div class="obl-item"><span class="obl-check">✓</span><div>Belgilangan tranzit koridoridan asossiz chetga chiqmaslik va vaqtida yetkazish.</div></div>
        <div class="obl-item"><span class="obl-check">✓</span><div>O'zbekiston Respublikasi Bojxona kodeksiga muvofiq to'liq javobgarlikni o'z zimmasiga olish.</div></div>
      </div>

      <div class="stamp-row">
        <div>
          <h5 style="font-size:11px;font-weight:700;text-transform:uppercase;color:#1a1c1e;margin-bottom:4px">${L.digitalSign || 'Elektron imzo'}</h5>
          <small style="font-size:9px;color:#6b7280;display:block">${L.issuedBy || 'Inspektor'}: ${item.inspector_name || '—'}</small>
          <div class="eri-text"><small>ERI: e-imzo.uz/2026/0A81F | ${formatDateSimple(item.crossing_at)}</small></div>
        </div>
        <div style="display:flex;align-items:center;gap:12px;border-left:1px solid #e5e7eb;padding-left:12px">
          <div class="stamp-circle">
            <span>DAVLAT<br>BOJXONA</span>
            <span style="font-size:8px;font-weight:900;margin:2px 0">${item.post_name?.split(' ').slice(-1)[0]?.toUpperCase() || 'KPP'}</span>
            <span>${formatDateSimple(item.crossing_at)}</span>
          </div>
        </div>
      </div>
    </div>

    <div class="footer-doc">
      <div>
        <strong>Davlat Bojxona Qo'mitasi Yagona Axborot Tizimi</strong>
        <div>customs.uz | 1108 | +998 78 120-76-00</div>
      </div>
      <div style="text-align:right">
        <div style="font-family:'Space Mono',monospace;font-weight:700">MB-2026-${docNo.replace('MB','')}</div>
        <div>A4 Format · Sahifa 1 / 1</div>
      </div>
    </div>
  </div>
  </body></html>`;
}

/* 2. Sug'urta Polisi PDF */
function buildInsurancePDF(item, doc, L, isPaid) {
  const payload = item.payload || {};
  const docNo = doc ? doc.code : 'ETSD2026953307';
  const paymentStatus = isPaid
    ? `<span style="background:#ecfdf5;color:#065f46;border:1px solid #a7f3d0;padding:4px 12px;border-radius:20px;font-weight:800;font-size:11px;">✓ TO'LANGAN / PAID</span>`
    : `<span style="background:#fffbeb;color:#92400e;border:1px solid #fde68a;padding:4px 12px;border-radius:20px;font-weight:800;font-size:11px;">⏳ KUTILMOQDA</span>`;

  return `<!DOCTYPE html><html lang="${lang}"><head><meta charset="UTF-8">
  <title>${L.insurancePolicy} — ${docNo}</title>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800;900&family=Space+Mono:wght@400;700&display=swap');
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: 'Inter', Arial, sans-serif; background: #525659; color: #1a1c1e; }
    .no-print { background: #063c32; color: #fff; padding: 12px 20px; display: flex; justify-content: space-between; align-items: center; }
    .no-print button { background: #0b5949; color: #fff; border: 1px solid #d8ad58; padding: 10px 22px; border-radius: 8px; font-weight: 700; cursor: pointer; display: flex; align-items: center; gap: 8px; font-size: 13px; }
    .a4 { width: 210mm; min-height: 297mm; margin: 20px auto; background: #fff; padding: 12mm; box-shadow: 0 8px 30px rgba(0,0,0,.3); display: flex; flex-direction: column; justify-content: space-between; }
    .header { display: flex; justify-content: space-between; align-items: flex-start; border-bottom: 2px solid #0b4f35; padding-bottom: 12px; margin-bottom: 16px; }
    .brand { display: flex; align-items: center; gap: 12px; }
    .brand-text h1 { font-size: 13px; font-weight: 900; text-transform: uppercase; color: #0b4f35; letter-spacing: .05em; }
    .brand-text p { font-size: 10px; color: #6b7280; margin-top: 2px; }
    .title-bar { background: linear-gradient(135deg, #0b5949, #087f84); color: #fff; padding: 12px 18px; border-radius: 8px; display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px; border-left: 4px solid #d8ad58; }
    .title-bar h2 { font-family: 'Space Mono', monospace; font-size: 16px; font-weight: 700; }
    .title-bar small { font-size: 10px; color: #86efac; }
    .grid2 { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 14px; }
    .box { border: 1px solid #e5e7eb; border-radius: 6px; padding: 12px; background: #f9fafb; }
    .box h4 { font-size: 9px; text-transform: uppercase; letter-spacing: .1em; color: #6b7280; font-weight: 700; border-bottom: 1px solid #e5e7eb; padding-bottom: 6px; margin-bottom: 8px; }
    .row { display: flex; justify-content: space-between; padding: 4px 0; font-size: 11px; border-bottom: 1px dashed #f3f4f6; }
    .row:last-child { border: none; }
    .row span { color: #6b7280; }
    .row strong { font-family: 'Space Mono', monospace; font-size: 10px; color: #1a1c1e; }
    .footer-doc { border-top: 1px solid #d1d5db; padding-top: 10px; margin-top: 16px; display: flex; justify-content: space-between; font-size: 9px; color: #6b7280; }
    @media print { body { background: none; } .no-print { display: none !important; } .a4 { box-shadow: none; margin: 0; width: 100%; min-height: auto; } }
    @page { size: A4; margin: 10mm; }
  </style></head><body>
  <div class="no-print">
    <div style="display:flex;align-items:center;gap:10px">
      <span style="width:10px;height:10px;border-radius:50%;background:#38bdf8;display:inline-block"></span>
      <span style="font-size:13px;font-weight:600">${L.insurancePolicy} · A4</span>
    </div>
    <span>PDF / Chop etish oynasi</span>
  </div>
  <div class="a4">
    <div>
      <div class="header">
        <div class="brand">
          ${getLogoSvg()}
          <div class="brand-text">
            <small style="font-size:10px;color:#6b7280;text-transform:uppercase;font-weight:600">O'zbekiston Respublikasi</small>
            <h1>Davlat Bojxona Qo'mitasi</h1>
            <p>Tranzit transport vositalari fuqarolik javobgarligini majburiy sug'urtalash</p>
          </div>
        </div>
        <div style="text-align:right">
          <div style="border:2px solid #0b4f35;background:#ecfdf5;color:#0b4f35;padding:4px 14px;border-radius:6px;font-size:11px;font-weight:800;text-transform:uppercase">● RASMIY POLIS</div>
          <div style="margin-top:6px">${paymentStatus}</div>
        </div>
      </div>

      <div class="title-bar">
        <div>
          <small>${L.insurancePolicy?.toUpperCase() || 'SUG\'URTA POLISI'}</small>
          <h2>${docNo}</h2>
        </div>
        <div style="text-align:right;font-size:10px;color:#86efac">
          <div>Amal qilish muddati:</div>
          <strong style="font-family:'Space Mono',monospace">30 KUN / 1 OY</strong>
        </div>
      </div>

      <div class="grid2">
        <div class="box">
          <h4>Sug'urtalanuvchi ma'lumotlari</h4>
          <div class="row"><span>Haydovchi:</span><strong>${item.driver_name || '—'}</strong></div>
          <div class="row"><span>Pasport:</span><strong>${payload.passport || '—'}</strong></div>
          <div class="row"><span>Fuqaroligi:</span><strong>${payload.nationality || '—'}</strong></div>
        </div>
        <div class="box">
          <h4>Transport va qoplama</h4>
          <div class="row"><span>Davlat raqami:</span><strong>${item.vehicle_plate || '—'}</strong></div>
          <div class="row"><span>Sug'urta summasi:</span><strong>40 000 000 UZS</strong></div>
          <div class="row"><span>Sug'urta mukofoti:</span><strong>308 000 UZS</strong></div>
        </div>
      </div>

      <div class="box" style="margin-bottom:14px">
        <h4>Sug'urta shartlari va huquqiy asos</h4>
        <div class="row"><span>Asos:</span><strong>O'zbekiston Respublikasining "OSAGO" to'g'risidagi Qonuni</strong></div>
        <div class="row"><span>Kafolat beruvchi:</span><strong>O'zbekiston Sug'urta Bozorini Rivojlantirish Agentligi</strong></div>
        <div class="row"><span>Polis maqomi:</span><strong style="color:#059669">YAGONA ELEKTRON REYESTRGA KIRITILGAN</strong></div>
      </div>
    </div>

    <div class="footer-doc">
      <div>
        <strong>Davlat Bojxona Qo'mitasi Yagona Axborot Tizimi</strong>
        <div>customs.uz | 1108 | +998 78 120-76-00</div>
      </div>
      <div style="text-align:right">
        <div style="font-family:'Space Mono',monospace;font-weight:700">ETSD-2026-${docNo.replace('ETSD','')}</div>
        <div>A4 Format · Sahifa 1 / 1</div>
      </div>
    </div>
  </div>
  </body></html>`;
}

/* 3. Bojxona To'lov Invoysi PDF */
function buildInvoicePDF(item, doc, L, isPaid) {
  const payload = item.payload || {};
  const docNo = doc ? doc.code : item.document_no;
  const totalStr = formatUzs(Number(payload.payment_total_uzs || 0));

  const paymentStatus = isPaid
    ? `<span style="background:#ecfdf5;color:#065f46;border:1px solid #a7f3d0;padding:4px 12px;border-radius:20px;font-weight:800;font-size:11px;">✓ TO'LANGAN / PAID</span>`
    : `<span style="background:#fffbeb;color:#92400e;border:1px solid #fde68a;padding:4px 12px;border-radius:20px;font-weight:800;font-size:11px;">⏳ KUTILMOQDA</span>`;

  return `<!DOCTYPE html><html lang="${lang}"><head><meta charset="UTF-8">
  <title>${L.paymentInvoice} — ${docNo}</title>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800;900&family=Space+Mono:wght@400;700&display=swap');
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: 'Inter', Arial, sans-serif; background: #525659; color: #1a1c1e; }
    .no-print { background: #063c32; color: #fff; padding: 12px 20px; display: flex; justify-content: space-between; align-items: center; }
    .no-print button { background: #0b5949; color: #fff; border: 1px solid #d8ad58; padding: 10px 22px; border-radius: 8px; font-weight: 700; cursor: pointer; display: flex; align-items: center; gap: 8px; font-size: 13px; }
    .a4 { width: 210mm; min-height: 297mm; margin: 20px auto; background: #fff; padding: 12mm; box-shadow: 0 8px 30px rgba(0,0,0,.3); display: flex; flex-direction: column; justify-content: space-between; }
    .header { display: flex; justify-content: space-between; align-items: flex-start; border-bottom: 2px solid #0b4f35; padding-bottom: 12px; margin-bottom: 16px; }
    .brand { display: flex; align-items: center; gap: 12px; }
    .title-bar { background: linear-gradient(135deg, #063c32, #0b5949); color: #fff; padding: 12px 18px; border-radius: 8px; display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px; border-left: 4px solid #d8ad58; }
    .title-bar h2 { font-family: 'Space Mono', monospace; font-size: 16px; font-weight: 700; }
    .grid2 { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 14px; }
    .box { border: 1px solid #e5e7eb; border-radius: 6px; padding: 12px; background: #f9fafb; }
    .box h4 { font-size: 9px; text-transform: uppercase; letter-spacing: .1em; color: #6b7280; font-weight: 700; border-bottom: 1px solid #e5e7eb; padding-bottom: 6px; margin-bottom: 8px; }
    .row { display: flex; justify-content: space-between; padding: 4px 0; font-size: 11px; border-bottom: 1px dashed #f3f4f6; }
    .row:last-child { border: none; }
    .row span { color: #6b7280; }
    .row strong { font-family: 'Space Mono', monospace; font-size: 10px; color: #1a1c1e; }
    table { width: 100%; border-collapse: collapse; margin-bottom: 16px; font-size: 11px; }
    th { background: #063c32; color: #fff; text-align: left; padding: 8px 10px; font-size: 10px; text-transform: uppercase; }
    td { padding: 8px 10px; border-bottom: 1px solid #e5e7eb; }
    tfoot td { background: #063c32; color: #fff; font-weight: 800; font-family: 'Space Mono', monospace; font-size: 13px; }
    .footer-doc { border-top: 1px solid #d1d5db; padding-top: 10px; margin-top: 16px; display: flex; justify-content: space-between; font-size: 9px; color: #6b7280; }
    @media print { body { background: none; } .no-print { display: none !important; } .a4 { box-shadow: none; margin: 0; width: 100%; min-height: auto; } }
    @page { size: A4; margin: 10mm; }
  </style></head><body>
  <div class="no-print">
    <div style="display:flex;align-items:center;gap:10px">
      <span style="width:10px;height:10px;border-radius:50%;background:#fbbf24;display:inline-block"></span>
      <span style="font-size:13px;font-weight:600">${L.paymentInvoice} · A4</span>
    </div>
    <span>PDF / Chop etish oynasi</span>
  </div>
  <div class="a4">
    <div>
      <div class="header">
        <div class="brand">
          ${getLogoSvg()}
          <div>
            <small style="font-size:9px;color:#6b7280;text-transform:uppercase;font-weight:600">O'zbekiston Respublikasi</small>
            <div style="font-size:13px;font-weight:900;text-transform:uppercase;color:#0b4f35">Davlat Bojxona Qo'mitasi</div>
            <div style="font-size:10px;color:#6b7280">Bojxona to'lovlari va yig'imlari bo'yicha elektron invoys</div>
          </div>
        </div>
        <div style="text-align:right">
          <div style="border:2px double #0b4f35;background:#ecfdf5;color:#0b4f35;padding:4px 12px;border-radius:6px;font-size:11px;font-weight:800;text-transform:uppercase">${isPaid ? '✓ TO\'LANGAN' : '⏳ KUTILMOQDA'}</div>
          <div style="margin-top:6px">${paymentStatus}</div>
        </div>
      </div>

      <div class="title-bar">
        <div>
          <small style="font-size:10px;color:#86efac">${L.paymentInvoice?.toUpperCase() || 'INVOYS'}</small>
          <h2>№ ${docNo}</h2>
        </div>
        <div style="font-size:11px">
          <span style="color:#86efac">Sana:</span>
          <span style="font-weight:700;margin-left:6px">${formatDateSimple(item.crossing_at)}</span>
        </div>
      </div>

      <div class="grid2">
        <div class="box">
          <h4>To'lovchi ma'lumotlari</h4>
          <div class="row"><span>Haydovchi:</span><strong>${item.driver_name || '—'}</strong></div>
          <div class="row"><span>Pasport:</span><strong>${payload.passport || '—'}</strong></div>
          <div class="row"><span>Transport:</span><strong>${item.vehicle_plate || '—'} / ${payload.vehicle_country || '—'}</strong></div>
        </div>
        <div class="box">
          <h4>Chegara posti</h4>
          <div class="row"><span>Post:</span><strong>${item.post_name || '—'}</strong></div>
          <div class="row"><span>Hujjat:</span><strong>${item.document_no || '—'}</strong></div>
        </div>
      </div>

      <table>
        <thead>
          <tr>
            <th style="width:30px">№</th>
            <th>To'lov turi va asosi</th>
            <th style="width:100px">Stavka</th>
            <th style="width:110px;text-align:right">Summasi (UZS)</th>
            <th style="width:80px;text-align:center">Holati</th>
          </tr>
        </thead>
        <tbody>
          <tr><td>1</td><td><strong>${doc?.title || 'Hujjat bo\'yicha to\'lov'}</strong><br><small style="color:#6b7280">Inspektor kiritgan jami summa</small></td><td>Kiritilgan</td><td style="text-align:right;font-weight:700">${totalStr}</td><td style="text-align:center;font-weight:700;${isPaid ? 'color:#16a34a' : 'color:#dc2626'}">${isPaid ? 'To\'langan' : 'Kutilmoqda'}</td></tr>
        </tbody>
        <tfoot>
          <tr><td colspan="3" style="text-align:right">Jami summa:</td><td style="text-align:right;color:#86efac">${totalStr}</td><td style="text-align:center;color:#86efac">${isPaid ? 'YOPILGAN' : 'OCHIQ'}</td></tr>
        </tfoot>
      </table>

      <div style="border:1px dashed #d1d5db;border-radius:8px;padding:12px;font-size:11px;color:#374151">
        <div><strong>To'lov usuli:</strong> ${isPaid ? 'Tizimda tasdiqlangan' : 'Hali tanlanmagan'}</div>
        <div><strong>Rasmiylashtirgan:</strong> ${item.inspector_name || 'Bojxona xodimi'}</div>
      </div>
    </div>

    <div class="footer-doc">
      <div>
        <strong>Davlat Bojxona Qo'mitasi Yagona Axborot Tizimi</strong>
        <div>customs.uz | 1108 | +998 78 120-76-00</div>
      </div>
      <div style="text-align:right">
        <div style="font-family:'Space Mono',monospace;font-weight:700">AT-2026-${docNo.replace('AT','')}</div>
        <div>A4 Format · Sahifa 1 / 1</div>
      </div>
    </div>
  </div>
  </body></html>`;
}

/* ── DOM Event Listeners ── */
document.addEventListener('DOMContentLoaded', () => {
  initLanguageDropdown();

  // CSP-safe payment controls. No inline onclick/onsubmit handlers are used.
  document.addEventListener('click', event => {
    const method = event.target.closest('[data-payment-method]');
    if (method) {
      document.querySelectorAll('[data-payment-method]').forEach(button => {
        button.classList.toggle('selected', button === method);
      });
      showPayStep3(method.dataset.paymentMethod);
      return;
    }
    const action = event.target.closest('[data-pay-action]')?.dataset.payAction;
    if (action === 'open') openUnifiedPayModal();
    if (action === 'close') closePayModal();
    if (action === 'summary') showPayStep1();
    if (action === 'methods') showPayStep2();
    if (action === 'confirm-demo') processUnifiedPayment();
  });

  const vehicleImage = $('vehicle-profile-img');
  if (vehicleImage) {
    vehicleImage.addEventListener('error', () => {
      if (!vehicleImage.src.endsWith('/sedan.webp')) vehicleImage.src = '/static/webapp/vehicles/sedan.webp';
    });
  }

  // PDF Language Selector
  document.querySelectorAll('.pdf-lang-chip').forEach(btn => {
    btn.addEventListener('click', () => {
      selectedDlLang = btn.dataset.dlang;
      document.querySelectorAll('.pdf-lang-chip').forEach(b => {
        b.classList.toggle('active', b.dataset.dlang === selectedDlLang);
      });
    });
  });

  // Modal Backdrop Click to Close
  const modal = $('payment-modal');
  if (modal) {
    modal.addEventListener('click', e => {
      if (e.target === modal) closePayModal();
    });
  }
});

/* ── Main Data Fetching ── */
(async () => {
  const pathParts = location.pathname.split('/').filter(Boolean);
  const token = pathParts[pathParts.length - 1];

  if (!token || token === 'visit') {
    $('loading').hidden = true;
    $('error').hidden = false;
    return;
  }

  try {
    const response = await fetch(`/api/inspector/documents/${encodeURIComponent(token)}`, {
      headers: { Accept: 'application/json' },
      cache: 'no-store',
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    const data = await response.json();

    if (!data.ok || !data.document) {
      throw new Error('no-document');
    }

    $('loading').hidden = true;
    $('document-view').hidden = false;

    render(data.document);
    applyLanguage();

  } catch (err) {
    console.error('Inspector document load error:', err);
    $('loading').hidden = true;
    $('error').hidden = false;
  }
})();

/* Expose global functions */
window.downloadDocumentPDF = downloadDocumentPDF;
window.setLanguage = setLanguage;

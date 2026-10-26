'use strict';

/* ============================================================
   Inspector Document JS v5
   - QR xatoligi tuzatildi (to'g'ri API endpoint ishlatildi)
   - PDF yuklab olish (3 tilda: UZ, RU, EN)
   - To'lov tizimi (6 ta to'lov usuli, karta kiritish, tasdiqlash)
   - Zamonaviy animatsiyalar
   - Bojxona logosi
   ============================================================ */

const dictionary = {
  uz: {
    service: 'Davlat bojxona xizmati',
    loading: 'Hujjat tekshirilmoqda…',
    loadingDesc: 'Tizimdan ma\'lumot olinmoqda',
    notFound: 'Hujjat topilmadi',
    notFoundHelp: 'QR-kod to\'g\'riligini tekshiring yoki bojxona xodimiga murojaat qiling.',
    verified: 'HUJJAT TASDIQLANGAN',
    revoked: 'HUJJAT BEKOR QILINGAN',
    verifiedHelp: 'Ma\'lumotlar bojxona tizimidagi yozuvga mos',
    revokedHelp: 'Bu hujjat amalda emas. Bojxona xodimiga murojaat qiling.',
    welcome: 'O\'ZBEKISTON RESPUBLIKASIGA XUSH KELIBSIZ!',
    docNumber: 'Hujjat raqami',
    visitorData: 'TASHRIF BUYURUVCHI',
    personalData: 'Shaxsiy ma\'lumotlar',
    crossing: 'CHEGARADAN O\'TISH',
    journeyData: 'Safar ma\'lumotlari',
    officialDocs: 'RASMIY HUJJATLAR',
    registeredDocs: 'Nomingizga rasmiylashtirilgan hujjatlar',
    additional: 'QO\'SHIMCHA',
    additionalInfo: 'Qo\'shimcha ma\'lumot',
    lawTitle: 'Qonunchilik talablariga rioya qiling',
    lawText: 'O\'zbekiston Respublikasi hududida amaldagi bojxona va yo\'l harakati qoidalariga amal qilishingiz shart.',
    issuedBy: 'HUJJATNI RASMIYLASHTIRGAN INSPEKTOR',
    privacy: 'Ushbu sahifa QR orqali berilgan hujjatni tekshirish uchun mo\'ljallangan.',
    nationality: 'Fuqaroligi',
    passport: 'Pasport',
    phone: 'Telefon',
    plate: 'Transport raqami',
    vehicleCountry: 'Transport davlati',
    post: 'Chegara posti',
    time: 'O\'tish vaqti',
    location: 'Yo\'nalish / joy',
    cargo: 'Yuk',
    status: 'Holati',
    downloadTitle: 'Hujjatlarni PDF yuklab olish',
    downloadDesc: 'Barcha hujjatlarni rasmiy PDF formatida yuklab oling',
    downloadLang: 'Yuklab olish tili:',
    download: 'PDF Yuklab olish',
    paymentRequired: 'To\'lov talab etiladi',
    paymentStatus: 'To\'lov holati:',
    unpaid: '❌ TO\'LANMAGAN',
    paid: '✅ TO\'LANGAN',
    amount: 'Summa:',
    payNow: 'To\'lash',
    chooseMethod: 'To\'lov tizimini tanlang',
    cardDetails: 'Karta ma\'lumotlarini kiriting',
    cardNumber: 'Karta raqami',
    expiry: 'Amal qilish muddati',
    cardHolder: 'Karta egasining ismi',
    totalAmount: 'Jami to\'lov:',
    confirmPay: 'To\'lovni tasdiqlash',
    back: 'Orqaga',
    paymentSuccess: 'To\'lov qabul qilindi!',
    paymentSuccessDesc: 'Sizning to\'lovingiz muvaffaqiyatli amalga oshirildi.',
    transactionId: 'Tranzaksiya ID:',
    paidAt: 'To\'langan vaqt:',
    close: 'Yopish',
    transitDeclaration: 'Tranzit Majburiyatnomasi',
    insurancePolicy: 'Sug\'urta Polisi',
    paymentInvoice: 'To\'lov Invoysi',
    active: 'Faol',
    docType: 'Hujjat turi',
    issueDate: 'Rasmiylashtirilgan sana',
    validUntil: 'Amal qilish muddati',
    officialSeal: 'Rasmiy muhr',
    digitalSign: 'Elektron imzo',
    verifiedSystem: 'Tizim tekshiruvi',
    unpaidWarning: '⚠️ DIQQAT: Ushbu hujjat uchun to\'lov amalga oshirilmagan!',
  },
  ru: {
    service: 'Государственная таможенная служба',
    loading: 'Документ проверяется…',
    loadingDesc: 'Получение данных из системы',
    notFound: 'Документ не найден',
    notFoundHelp: 'Проверьте QR-код или обратитесь к сотруднику таможни.',
    verified: 'ДОКУМЕНТ ПОДТВЕРЖДЁН',
    revoked: 'ДОКУМЕНТ АННУЛИРОВАН',
    verifiedHelp: 'Данные соответствуют записи в таможенной системе',
    revokedHelp: 'Документ недействителен. Обратитесь к сотруднику таможни.',
    welcome: 'ДОБРО ПОЖАЛОВАТЬ В РЕСПУБЛИКУ УЗБЕКИСТАН!',
    docNumber: 'Номер документа',
    visitorData: 'ПОСЕТИТЕЛЬ',
    personalData: 'Личные данные',
    crossing: 'ПЕРЕСЕЧЕНИЕ ГРАНИЦЫ',
    journeyData: 'Данные поездки',
    officialDocs: 'ОФИЦИАЛЬНЫЕ ДОКУМЕНТЫ',
    registeredDocs: 'Документы, оформленные на ваше имя',
    additional: 'ДОПОЛНИТЕЛЬНО',
    additionalInfo: 'Дополнительная информация',
    lawTitle: 'Соблюдайте требования законодательства',
    lawText: 'На территории Республики Узбекистан необходимо соблюдать таможенные правила и правила дорожного движения.',
    issuedBy: 'ИНСПЕКТОР, ОФОРМИВШИЙ ДОКУМЕНТ',
    privacy: 'Страница предназначена для проверки документа по QR-коду.',
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
    downloadTitle: 'Скачать документы в PDF',
    downloadDesc: 'Скачайте все документы в официальном формате PDF',
    downloadLang: 'Язык загрузки:',
    download: 'Скачать PDF',
    paymentRequired: 'Требуется оплата',
    paymentStatus: 'Статус оплаты:',
    unpaid: '❌ НЕ ОПЛАЧЕНО',
    paid: '✅ ОПЛАЧЕНО',
    amount: 'Сумма:',
    payNow: 'Оплатить',
    chooseMethod: 'Выберите способ оплаты',
    cardDetails: 'Введите данные карты',
    cardNumber: 'Номер карты',
    expiry: 'Срок действия',
    cardHolder: 'Имя держателя карты',
    totalAmount: 'Итого к оплате:',
    confirmPay: 'Подтвердить оплату',
    back: 'Назад',
    paymentSuccess: 'Платёж принят!',
    paymentSuccessDesc: 'Ваш платёж успешно обработан.',
    transactionId: 'ID транзакции:',
    paidAt: 'Время оплаты:',
    close: 'Закрыть',
    transitDeclaration: 'Транзитное Обязательство',
    insurancePolicy: 'Страховой Полис',
    paymentInvoice: 'Платёжный Инвойс',
    active: 'Активен',
    docType: 'Тип документа',
    issueDate: 'Дата оформления',
    validUntil: 'Срок действия',
    officialSeal: 'Официальная печать',
    digitalSign: 'Электронная подпись',
    verifiedSystem: 'Проверка системы',
    unpaidWarning: '⚠️ ВНИМАНИЕ: Оплата по данному документу не произведена!',
  },
  en: {
    service: 'State Customs Service',
    loading: 'Verifying document…',
    loadingDesc: 'Fetching data from the system',
    notFound: 'Document not found',
    notFoundHelp: 'Check the QR code or contact a customs officer.',
    verified: 'DOCUMENT VERIFIED',
    revoked: 'DOCUMENT REVOKED',
    verifiedHelp: 'The data matches the record in the customs system',
    revokedHelp: 'This document is no longer valid. Contact a customs officer.',
    welcome: 'WELCOME TO THE REPUBLIC OF UZBEKISTAN!',
    docNumber: 'Document number',
    visitorData: 'VISITOR',
    personalData: 'Personal details',
    crossing: 'BORDER CROSSING',
    journeyData: 'Journey details',
    officialDocs: 'OFFICIAL DOCUMENTS',
    registeredDocs: 'Documents issued in your name',
    additional: 'ADDITIONAL',
    additionalInfo: 'Additional information',
    lawTitle: 'Comply with the law',
    lawText: 'You must comply with customs and traffic regulations in the Republic of Uzbekistan.',
    issuedBy: 'DOCUMENT ISSUED BY INSPECTOR',
    privacy: 'This page is intended to verify the QR-linked document.',
    nationality: 'Nationality',
    passport: 'Passport',
    phone: 'Phone',
    plate: 'Vehicle plate',
    vehicleCountry: 'Vehicle country',
    post: 'Border post',
    time: 'Crossing time',
    location: 'Route / location',
    cargo: 'Cargo',
    status: 'Status',
    downloadTitle: 'Download Documents as PDF',
    downloadDesc: 'Download all documents in official PDF format',
    downloadLang: 'Download language:',
    download: 'Download PDF',
    paymentRequired: 'Payment required',
    paymentStatus: 'Payment status:',
    unpaid: '❌ UNPAID',
    paid: '✅ PAID',
    amount: 'Amount:',
    payNow: 'Pay now',
    chooseMethod: 'Choose payment method',
    cardDetails: 'Enter card details',
    cardNumber: 'Card number',
    expiry: 'Expiry date',
    cardHolder: 'Cardholder name',
    totalAmount: 'Total to pay:',
    confirmPay: 'Confirm payment',
    back: 'Back',
    paymentSuccess: 'Payment accepted!',
    paymentSuccessDesc: 'Your payment has been successfully processed.',
    transactionId: 'Transaction ID:',
    paidAt: 'Paid at:',
    close: 'Close',
    transitDeclaration: 'Transit Declaration',
    insurancePolicy: 'Insurance Policy',
    paymentInvoice: 'Payment Invoice',
    active: 'Active',
    docType: 'Document type',
    issueDate: 'Issue date',
    validUntil: 'Valid until',
    officialSeal: 'Official seal',
    digitalSign: 'Digital signature',
    verifiedSystem: 'System verification',
    unpaidWarning: '⚠️ WARNING: Payment for this document has not been made!',
  }
};

/* ── State ── */
let lang = 'uz';
let record = null;
let selectedDlLang = 'uz';
let currentDocForPayment = null;
let selectedPayMethod = null;
let paidDocs = {}; // track paid doc IDs

/* ── Helpers ── */
const $ = id => document.getElementById(id);
const t = key => dictionary[lang][key] || dictionary.uz[key] || key;
function setText(id, val) { const n = $(id); if (n) n.textContent = val || '—'; }

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

function dlRow(label, value) {
  const div = document.createElement('div');
  const dt = document.createElement('dt');
  const dd = document.createElement('dd');
  dt.textContent = label;
  dd.textContent = value || '—';
  div.append(dt, dd);
  return div;
}

/* ── Particles ── */
function initParticles() {
  const container = $('particles');
  if (!container) return;
  for (let i = 0; i < 18; i++) {
    const p = document.createElement('div');
    p.className = 'particle';
    const size = Math.random() * 120 + 40;
    p.style.cssText = `
      width:${size}px; height:${size}px;
      left:${Math.random() * 100}%;
      animation-duration:${Math.random() * 20 + 15}s;
      animation-delay:${Math.random() * -20}s;
      opacity:${Math.random() * 0.4 + 0.1};
    `;
    container.appendChild(p);
  }
}

/* ── i18n apply ── */
function applyLanguage() {
  document.documentElement.lang = lang;
  document.querySelectorAll('[data-i18n]').forEach(n => n.textContent = t(n.dataset.i18n));
  document.querySelectorAll('[data-lang]').forEach(b => b.classList.toggle('active', b.dataset.lang === lang));
  if (record) render(record);
}

/* ── Render document ── */
function render(item) {
  record = item;
  const payload = item.payload || {};
  const isActive = item.status === 'active';
  const badge = $('verified');
  badge.classList.toggle('revoked', !isActive);

  const icon = badge.querySelector('.verified-icon svg');
  if (!isActive) {
    icon.innerHTML = '<line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>';
  } else {
    icon.innerHTML = '<polyline points="20 6 9 17 4 12"/>';
  }

  badge.querySelector('b').textContent = t(isActive ? 'verified' : 'revoked');
  badge.querySelector('small').textContent = t(isActive ? 'verifiedHelp' : 'revokedHelp');

  setText('driver-name', item.driver_name);
  setText('document-number', item.document_no);

  // Identity
  const identity = $('identity-list');
  identity.replaceChildren(
    dlRow(t('nationality'), payload.nationality),
    dlRow(t('passport'), payload.passport),
    dlRow(t('phone'), payload.phone)
  );

  // Journey
  const journey = $('journey-list');
  journey.replaceChildren(
    dlRow(t('plate'), item.vehicle_plate),
    dlRow(t('vehicleCountry'), payload.vehicle_country),
    dlRow(t('post'), item.post_name),
    dlRow(t('time'), formatDate(item.crossing_at)),
    dlRow(t('location'), payload.location),
    dlRow(t('cargo'), payload.cargo)
  );

  // Documents
  renderDocuments(payload.documents || []);

  // Additional
  const info = String(payload.additional_info || '').trim();
  $('note-card').hidden = !info;
  setText('additional-info', info);

  // Inspector
  setText('inspector-name', item.inspector_name);
  setText('issued-at', `${item.post_name} · ${formatDate(item.crossing_at)}`);

  // Downloads
  renderDownloadButtons(payload.documents || []);

  // Animate cards in sequence
  animateCards();
}

function renderDocuments(docs) {
  const container = $('documents');
  if (!docs.length) {
    container.innerHTML = '<p style="color:var(--muted);grid-column:1/-1">—</p>';
    return;
  }
  container.replaceChildren(...docs.map((doc, idx) => {
    const article = document.createElement('article');
    article.className = 'document-item';
    article.style.animationDelay = `${idx * 0.1}s`;

    const code = document.createElement('small');
    code.textContent = doc.code;

    const title = document.createElement('b');
    title.textContent = doc.title;

    const status = document.createElement('span');
    status.textContent = doc.status || t('status');

    // Payment status badge
    const isPaid = paidDocs[doc.code] || doc.paid;
    const payBadge = document.createElement('div');
    payBadge.className = `doc-payment-status ${isPaid ? 'paid' : 'unpaid'}`;
    payBadge.id = `pay-badge-${doc.code}`;
    payBadge.textContent = isPaid ? t('paid') : t('unpaid');

    // Download button
    const dlBtn = document.createElement('button');
    dlBtn.className = 'doc-download-btn';
    dlBtn.innerHTML = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg><span>${t('download')}</span>`;
    dlBtn.onclick = () => downloadDocumentPDF(doc, selectedDlLang);

    // Pay button if unpaid
    if (!isPaid) {
      const payBtn = document.createElement('button');
      payBtn.className = 'doc-download-btn';
      payBtn.style.background = 'linear-gradient(135deg, #dc2626, #ef4444)';
      payBtn.style.marginTop = '6px';
      payBtn.innerHTML = `💳 <span>${t('payNow')}</span>`;
      payBtn.onclick = () => openPayModal(doc);
      article.append(code, title, status, payBadge, dlBtn, payBtn);
    } else {
      article.append(code, title, status, payBadge, dlBtn);
    }

    return article;
  }));
}

function renderDownloadButtons(docs) {
  const container = $('download-buttons');
  const docTypes = [
    { key: 'transit', icon: '📋', titleKey: 'transitDeclaration', defaultCode: 'MB' },
    { key: 'insurance', icon: '🛡️', titleKey: 'insurancePolicy', defaultCode: 'ETSD' },
    { key: 'invoice', icon: '💰', titleKey: 'paymentInvoice', defaultCode: 'AT' },
  ];

  const buttons = [];

  // Add buttons for each actual document
  if (docs.length) {
    docs.forEach((doc, idx) => {
      const docType = docTypes[idx] || { icon: '📄', titleKey: null, defaultCode: '' };
      const btn = document.createElement('button');
      btn.className = 'dl-btn';
      btn.innerHTML = `
        <div class="dl-btn-icon">${docType.icon}</div>
        <div>
          <b>${docType.titleKey ? t(docType.titleKey) : doc.title}</b>
          <small>${doc.code}</small>
        </div>
      `;
      btn.onclick = () => downloadDocumentPDF(doc, selectedDlLang);
      buttons.push(btn);
    });
  } else {
    // Fallback buttons
    docTypes.forEach((dt, idx) => {
      const btn = document.createElement('button');
      btn.className = 'dl-btn';
      btn.innerHTML = `
        <div class="dl-btn-icon">${dt.icon}</div>
        <div>
          <b>${t(dt.titleKey)}</b>
          <small data-i18n="download">${t('download')}</small>
        </div>
      `;
      btn.onclick = () => downloadDocumentPDF(null, selectedDlLang, idx);
      buttons.push(btn);
    });
  }

  container.replaceChildren(...buttons);
}

/* ── PDF Generation ── */
async function downloadDocumentPDF(doc, dlLang, fallbackIdx = 0) {
  const L = dictionary[dlLang] || dictionary.uz;
  const item = record;
  if (!item) return;

  const isPaid = doc ? (paidDocs[doc.code] || doc.paid) : false;
  const docTypes = ['transit', 'insurance', 'invoice'];
  const docType = doc ? docTypes.indexOf(doc.type || '') : fallbackIdx;

  // Build the right PDF content
  let htmlContent;
  if (fallbackIdx === 2 || (doc && doc.code && doc.code.startsWith('AT'))) {
    htmlContent = buildInvoicePDF(item, doc, L, isPaid);
  } else if (fallbackIdx === 1 || (doc && doc.code && doc.code.startsWith('ETSD'))) {
    htmlContent = buildInsurancePDF(item, doc, L, isPaid);
  } else {
    htmlContent = buildTransitPDF(item, doc, L, isPaid);
  }

  openPrintWindow(htmlContent);
}

function openPrintWindow(html) {
  const w = window.open('', '_blank', 'width=900,height=700');
  if (!w) { alert('Pop-up bloklangan. Brauzer sozlamalarini tekshiring.'); return; }
  w.document.write(html);
  w.document.close();
  setTimeout(() => { w.focus(); w.print(); }, 800);
}

function getLogoSvg() {
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" width="64" height="64">
    <polygon points="50,2 61,35 97,35 68,57 79,91 50,70 21,91 32,57 3,35 39,35" fill="#1a5c40" stroke="#d8ad58" stroke-width="2"/>
    <circle cx="50" cy="50" r="22" fill="#0b5949" stroke="#d8ad58" stroke-width="2"/>
    <text x="50" y="56" text-anchor="middle" font-family="Georgia,serif" font-weight="bold" font-size="10" fill="#d8ad58">DBQ</text>
  </svg>`;
}

function buildTransitPDF(item, doc, L, isPaid) {
  const payload = item.payload || {};
  const docNo = doc ? doc.code : item.document_no;
  const paymentWarning = !isPaid ? `<div style="background:#fef2f2;border:2px solid #dc2626;border-radius:8px;padding:12px;margin:16px 0;color:#dc2626;font-weight:bold;font-size:12px;text-align:center;">${L.unpaidWarning || '⚠️ TO\'LOV AMALGA OSHIRILMAGAN'}</div>` : '';
  const paymentStatus = isPaid
    ? `<span style="background:#dcfce7;color:#16a34a;padding:3px 10px;border-radius:20px;font-weight:bold;font-size:11px;">✅ ${L.paid || 'TO\'LANGAN'}</span>`
    : `<span style="background:#fee2e2;color:#dc2626;padding:3px 10px;border-radius:20px;font-weight:bold;font-size:11px;">❌ ${L.unpaid || 'TO\'LANMAGAN'}</span>`;

  return `<!DOCTYPE html><html lang="${lang}"><head><meta charset="UTF-8">
  <title>${L.transitDeclaration} — ${docNo}</title>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800;900&family=Space+Mono:wght@400;700&display=swap');
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: 'Inter', Arial, sans-serif; background: #525659; color: #1a1c1e; }
    .no-print { background: #1e293b; color: #fff; padding: 12px 20px; display: flex; justify-content: space-between; align-items: center; }
    .no-print button { background: #059669; color: #fff; border: none; padding: 10px 22px; border-radius: 8px; font-weight: 700; cursor: pointer; display: flex; align-items: center; gap: 8px; font-size: 13px; }
    .a4 { width: 210mm; min-height: 297mm; margin: 20px auto; background: #fff; padding: 12mm; box-shadow: 0 8px 30px rgba(0,0,0,.3); display: flex; flex-direction: column; justify-content: space-between; }
    .header { display: flex; justify-content: space-between; align-items: flex-start; border-bottom: 2px solid #0b4f35; padding-bottom: 12px; margin-bottom: 16px; }
    .brand { display: flex; align-items: center; gap: 12px; }
    .brand-text h1 { font-size: 13px; font-weight: 900; text-transform: uppercase; color: #0b4f35; letter-spacing: .05em; }
    .brand-text p { font-size: 10px; color: #6b7280; margin-top: 2px; }
    .status-badge { border: 2px solid #0b4f35; background: #ecfdf5; color: #0b4f35; padding: 4px 14px; border-radius: 6px; font-size: 11px; font-weight: 800; text-transform: uppercase; }
    .title-bar { background: linear-gradient(135deg, #042e27, #0a5545); color: #fff; padding: 12px 18px; border-radius: 8px; display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px; border-left: 4px solid #d8ad58; }
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
    .obl-check { color: #059669; font-weight: 900; flex-shrink: 0; }
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
    <button onclick="window.print()">🖨️ PDF / Chop etish</button>
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

      ${paymentWarning}

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
        <div class="obl-item"><span class="obl-check">☑</span><div>Bojxona identifikatsiya vositalari butunligini saqlash va ruxsatsiz buzmaslik.</div></div>
        <div class="obl-item"><span class="obl-check">☑</span><div>Belgilangan tranzit koridoridan asossiz chetga chiqmaslik va vaqtida yetkazish.</div></div>
        <div class="obl-item"><span class="obl-check">☑</span><div>O'zbekiston Respublikasi Bojxona kodeksiga muvofiq to'liq javobgarlikni o'z zimmasiga olish.</div></div>
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
        <strong style="color:#374151">O'zbekiston Respublikasi Davlat Bojxona Xizmati</strong>
        <div>customs.uz | 1108 | +998 78 120-76-00</div>
      </div>
      <div style="text-align:right">
        <div style="font-family:'Space Mono',monospace;font-weight:700;color:#374151">${docNo || item.document_no}</div>
        <div>A4 Format · ${formatDateSimple(item.crossing_at)}</div>
      </div>
    </div>
  </div>
  </body></html>`;
}

function buildInsurancePDF(item, doc, L, isPaid) {
  const payload = item.payload || {};
  const docNo = doc ? doc.code : 'ETSD' + Math.floor(Math.random() * 1000000);
  const paymentWarning = !isPaid ? `<div style="background:#fef2f2;border:2px solid #dc2626;border-radius:8px;padding:12px;margin:16px 0;color:#dc2626;font-weight:bold;font-size:12px;text-align:center;">${L.unpaidWarning || '⚠️ TO\'LOV AMALGA OSHIRILMAGAN'}</div>` : '';
  const paymentStatus = isPaid
    ? `<span style="background:#dcfce7;color:#16a34a;padding:3px 10px;border-radius:20px;font-weight:bold;font-size:11px;">✅ ${L.paid || 'TO\'LANGAN'}</span>`
    : `<span style="background:#fee2e2;color:#dc2626;padding:3px 10px;border-radius:20px;font-weight:bold;font-size:11px;">❌ ${L.unpaid || 'TO\'LANMAGAN'}</span>`;

  return `<!DOCTYPE html><html lang="${lang}"><head><meta charset="UTF-8">
  <title>${L.insurancePolicy} — ${docNo}</title>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800;900&family=Space+Mono:wght@400;700&display=swap');
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: 'Inter', Arial, sans-serif; background: #525659; color: #1a1c1e; }
    .no-print { background: #1e293b; color: #fff; padding: 12px 20px; display: flex; justify-content: space-between; align-items: center; }
    .no-print button { background: #059669; color: #fff; border: none; padding: 10px 22px; border-radius: 8px; font-weight: 700; cursor: pointer; font-size: 13px; }
    .a4 { width: 210mm; min-height: 297mm; margin: 20px auto; background: #fff; padding: 12mm; box-shadow: 0 8px 30px rgba(0,0,0,.3); display: flex; flex-direction: column; justify-content: space-between; }
    .header { display: flex; justify-content: space-between; align-items: flex-start; border-bottom: 2px solid #0b4f35; padding-bottom: 12px; margin-bottom: 16px; }
    .brand { display: flex; align-items: center; gap: 12px; }
    .title-bar { background: linear-gradient(135deg, #042e27, #1e3a8a); color: #fff; padding: 12px 18px; border-radius: 8px; display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px; border-left: 4px solid #60a5fa; }
    .title-bar h2 { font-family: 'Space Mono', monospace; font-size: 15px; font-weight: 700; }
    .grid2 { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 14px; }
    .box { border: 1px solid #e5e7eb; border-radius: 6px; padding: 12px; background: #f9fafb; }
    .box h4 { font-size: 9px; text-transform: uppercase; color: #6b7280; font-weight: 700; border-bottom: 1px solid #e5e7eb; padding-bottom: 6px; margin-bottom: 8px; }
    .row { display: flex; justify-content: space-between; padding: 4px 0; font-size: 11px; border-bottom: 1px dashed #f3f4f6; }
    .row:last-child { border: none; }
    .row span { color: #6b7280; }
    .row strong { font-family: 'Space Mono', monospace; font-size: 10px; }
    .coverage-box { border: 2px solid rgba(11,89,73,.3); border-radius: 8px; padding: 14px; background: #f0fdf4; margin-bottom: 14px; }
    .coverage-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-top: 10px; }
    .cov-item { background: #fff; border: 1px solid #86efac; border-radius: 6px; padding: 10px; }
    .cov-label { font-size: 9px; color: #6b7280; text-transform: uppercase; font-weight: 700; }
    .cov-amount { font-family: 'Space Mono', monospace; font-size: 16px; font-weight: 700; color: #0b4f35; margin-top: 4px; }
    .cov-desc { font-size: 9px; color: #6b7280; margin-top: 4px; line-height: 1.4; }
    .stamp-row { display: flex; justify-content: space-between; align-items: center; border: 2px dashed #d1d5db; border-radius: 8px; padding: 12px; }
    .stamp-circle { width: 72px; height: 72px; border-radius: 50%; border: 2px solid #1e40af; display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; background: #eff6ff; color: #1e40af; padding: 4px; }
    .stamp-circle span { font-size: 6px; font-weight: 800; text-transform: uppercase; line-height: 1.3; }
    .footer-doc { border-top: 1px solid #d1d5db; padding-top: 10px; margin-top: 16px; display: flex; justify-content: space-between; font-size: 9px; color: #6b7280; }
    @media print { body { background: none; } .no-print { display: none !important; } .a4 { box-shadow: none; margin: 0; width: 100%; min-height: auto; } }
    @page { size: A4; margin: 10mm; }
  </style></head><body>
  <div class="no-print">
    <span style="font-size:13px;font-weight:600">🛡️ ${L.insurancePolicy} · A4</span>
    <button onclick="window.print()">🖨️ PDF / Chop etish</button>
  </div>
  <div class="a4">
    <div>
      <div class="header">
        <div class="brand">
          ${getLogoSvg()}
          <div>
            <small style="font-size:9px;color:#6b7280;text-transform:uppercase;font-weight:600">O'zbekiston Respublikasi Sug'urta Bozori</small>
            <div style="font-size:13px;font-weight:900;text-transform:uppercase;color:#0b4f35;letter-spacing:.04em">Yagona Sug'urta Axborot Tizimi</div>
            <div style="font-size:10px;color:#6b7280">Davlat Bojxona Qo'mitasi va IIV YHXBB integratsiyalashgan bazasi</div>
          </div>
        </div>
        <div style="text-align:right">
          <div style="border:2px solid #0b4f35;background:#ecfdf5;color:#0b4f35;padding:4px 12px;border-radius:6px;font-size:11px;font-weight:800;text-transform:uppercase">✓ KUCHDA (FAOL)</div>
          <div style="font-size:9px;color:#6b7280;margin-top:6px;font-family:'Space Mono',monospace">SERIYA: ETSD-2026<br>E-KAFOLAT ID: #UZ-${docNo}</div>
          <div style="margin-top:6px">${paymentStatus}</div>
        </div>
      </div>

      ${paymentWarning}

      <div class="title-bar">
        <div>
          <small style="font-size:10px;color:#93c5fd">${L.insurancePolicy?.toUpperCase() || 'SUG\'URTA POLISI'}</small>
          <h2>№ ${docNo}</h2>
        </div>
        <div style="text-align:right;font-size:10px;color:#93c5fd">
          <div>Amal qilish muddati:</div>
          <strong style="font-family:'Space Mono',monospace;color:#fff">${formatDateSimple(item.crossing_at)} (30 Kun)</strong>
        </div>
      </div>

      <div class="grid2">
        <div class="box">
          <h4>${L.personalData || 'Sug\'urtalanuvchi'}</h4>
          <div class="row"><span>${L.passport || 'Pasport'}:</span><strong>${payload.passport || '—'}</strong></div>
          <div class="row"><span>${L.nationality || 'Fuqaroligi'}:</span><strong>${payload.nationality || '—'}</strong></div>
          <div class="row"><span>${L.plate || 'Transport'}:</span><strong>${item.vehicle_plate || '—'}</strong></div>
        </div>
        <div class="box">
          <h4>${L.journeyData || 'Transport'}</h4>
          <div class="row"><span>Model:</span><strong>Yuk avtomobili</strong></div>
          <div class="row"><span>${L.vehicleCountry || 'Davlat'}:</span><strong>${payload.vehicle_country || 'UZ'}</strong></div>
          <div class="row"><span>${L.post || 'Post'}:</span><strong>${item.post_name || '—'}</strong></div>
        </div>
      </div>

      <div class="coverage-box">
        <h4 style="font-size:11px;font-weight:800;text-transform:uppercase;color:#0b4f35;display:flex;align-items:center;gap:6px">🛡️ Sug'urta Qoplami va To'langan Tarif</h4>
        <div class="coverage-grid">
          <div class="cov-item">
            <div class="cov-label">Jami Sug'urta Qoplami:</div>
            <div class="cov-amount">40 000 000 UZS</div>
            <div class="cov-desc">Uchinchi shaxslarning hayoti va mol-mulkiga yetkazilgan zarar qoplamasi.</div>
          </div>
          <div class="cov-item">
            <div class="cov-label">Sug'urta Mukofoti:</div>
            <div class="cov-amount">308 000 UZS</div>
            <div class="cov-desc">0.700 raz. BHM. Invoys tarkibida to'liq to'langan.</div>
          </div>
        </div>
      </div>

      <div class="stamp-row">
        <div>
          <h5 style="font-size:11px;font-weight:700;text-transform:uppercase;color:#1a1c1e;margin-bottom:4px">Sug'urtalovchi Tashkilot</h5>
          <div style="font-size:11px;font-weight:700;color:#374151">«O'zbekinvest» AJ</div>
          <small style="font-size:9px;color:#6b7280;display:block;margin-top:2px;font-family:'Space Mono',monospace">ERI: 6B8A91209FF412 | ${formatDateSimple(item.crossing_at)}</small>
        </div>
        <div style="display:flex;align-items:center;gap:12px;border-left:1px solid #e5e7eb;padding-left:12px">
          <div class="stamp-circle">
            <span>O'ZBEKINVEST<br>ELEKTRON<br>MUHR</span>
            <span style="font-size:7px;margin-top:2px">${formatDateSimple(item.crossing_at)}</span>
          </div>
        </div>
      </div>
    </div>

    <div class="footer-doc">
      <div><strong>O'zbekiston Respublikasi Transport Vazirligi & DBQ</strong><div>YPX va DBQ postlarida 100% onlayn tekshiriladi (1162)</div></div>
      <div style="text-align:right"><div style="font-family:'Space Mono',monospace;font-weight:700">POLIS-${docNo}-OK</div><div>A4 Format</div></div>
    </div>
  </div>
  </body></html>`;
}

function buildInvoicePDF(item, doc, L, isPaid) {
  const payload = item.payload || {};
  const docNo = doc ? doc.code : 'AT' + Math.floor(Math.random() * 10000000);
  const paymentWarning = !isPaid ? `<div style="background:#fef2f2;border:2px solid #dc2626;border-radius:8px;padding:12px;margin:16px 0;color:#dc2626;font-weight:bold;font-size:12px;text-align:center;">${L.unpaidWarning || '⚠️ TO\'LOV AMALGA OSHIRILMAGAN'}</div>` : '';
  const paymentStatus = isPaid
    ? `<span style="background:#dcfce7;color:#16a34a;padding:3px 10px;border-radius:20px;font-weight:bold;font-size:11px;">✅ ${L.paid || 'TO\'LANGAN'}</span>`
    : `<span style="background:#fee2e2;color:#dc2626;padding:3px 10px;border-radius:20px;font-weight:bold;font-size:11px;">❌ ${L.unpaid || 'TO\'LANMAGAN'}</span>`;

  const totalUZS = 621632;
  const totalStr = totalUZS.toLocaleString('uz-UZ') + ' UZS';
  const paymentStatusRow = isPaid
    ? `<span style="color:#16a34a;font-weight:800;text-transform:uppercase">Muvaffaqiyatli o'tkazildi</span>`
    : `<span style="color:#dc2626;font-weight:800;text-transform:uppercase">Kutilmoqda / To'lanmagan</span>`;

  return `<!DOCTYPE html><html lang="${lang}"><head><meta charset="UTF-8">
  <title>${L.paymentInvoice} — ${docNo}</title>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800;900&family=Space+Mono:wght@400;700&display=swap');
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: 'Inter', Arial, sans-serif; background: #525659; color: #1a1c1e; }
    .no-print { background: #1e293b; color: #fff; padding: 12px 20px; display: flex; justify-content: space-between; align-items: center; }
    .no-print button { background: #059669; color: #fff; border: none; padding: 10px 22px; border-radius: 8px; font-weight: 700; cursor: pointer; font-size: 13px; }
    .a4 { width: 210mm; min-height: 297mm; margin: 20px auto; background: #fff; padding: 12mm; box-shadow: 0 8px 30px rgba(0,0,0,.3); display: flex; flex-direction: column; justify-content: space-between; }
    .header { display: flex; justify-content: space-between; align-items: flex-start; border-bottom: 2px solid #0b4f35; padding-bottom: 12px; margin-bottom: 16px; }
    .brand { display: flex; align-items: center; gap: 12px; }
    .title-bar { background: #0b4f35; color: #fff; padding: 10px 16px; border-radius: 6px; display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px; }
    .title-bar h2 { font-family: 'Space Mono', monospace; font-size: 15px; font-weight: 700; }
    .grid2 { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 14px; }
    .box { border: 1px solid #e5e7eb; border-radius: 6px; padding: 12px; background: #f9fafb; }
    .box h4 { font-size: 9px; text-transform: uppercase; color: #6b7280; font-weight: 700; border-bottom: 1px solid #e5e7eb; padding-bottom: 6px; margin-bottom: 8px; }
    .row { display: flex; justify-content: space-between; padding: 4px 0; font-size: 11px; }
    .row span { color: #6b7280; }
    .row strong { font-family: 'Space Mono', monospace; font-size: 10px; }
    table { width: 100%; border-collapse: collapse; font-size: 11px; margin-bottom: 14px; }
    th { background: #f1f5f9; color: #6b7280; font-size: 9px; text-transform: uppercase; text-align: left; padding: 8px; border: 1px solid #e5e7eb; }
    td { padding: 8px; border: 1px solid #e5e7eb; color: #374151; }
    tr:nth-child(even) td { background: #f9fafb; }
    tfoot td { background: #0b4f35; color: #fff; font-weight: 700; font-family: 'Space Mono', monospace; padding: 10px 8px; }
    .pay-row { display: flex; justify-content: space-between; align-items: center; padding: 10px 14px; background: #f9fafb; border: 1px solid #e5e7eb; border-radius: 8px; margin-bottom: 14px; font-size: 11px; }
    .stamp-row { display: flex; justify-content: space-between; align-items: center; border: 2px dashed #d1d5db; border-radius: 8px; padding: 12px; }
    .stamp-circle { width: 72px; height: 72px; border-radius: 50%; border: 2px solid #0b4f35; display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; background: #f0fdf4; color: #0b4f35; padding: 4px; }
    .stamp-circle span { font-size: 6px; font-weight: 800; text-transform: uppercase; line-height: 1.3; }
    .footer-doc { border-top: 1px solid #d1d5db; padding-top: 10px; margin-top: 16px; display: flex; justify-content: space-between; font-size: 9px; color: #6b7280; align-items: flex-end; }
    @media print { body { background: none; } .no-print { display: none !important; } .a4 { box-shadow: none; margin: 0; width: 100%; min-height: auto; } }
    @page { size: A4; margin: 10mm; }
  </style></head><body>
  <div class="no-print">
    <span style="font-size:13px;font-weight:600">💰 ${L.paymentInvoice} · A4</span>
    <button onclick="window.print()">🖨️ PDF / Chop etish</button>
  </div>
  <div class="a4">
    <div>
      <div class="header">
        <div class="brand">
          ${getLogoSvg()}
          <div>
            <small style="font-size:9px;color:#6b7280;text-transform:uppercase;font-weight:600">O'zbekiston Respublikasi</small>
            <div style="font-size:13px;font-weight:900;text-transform:uppercase;color:#0b4f35">Davlat Bojxona Qo'mitasi</div>
            <div style="font-size:10px;color:#6b7280">Bojxona to'lovlari va yig'imlari hisobi bo'yicha elektron invoys</div>
          </div>
        </div>
        <div style="text-align:right">
          <div style="border:2px double #0b4f35;background:#ecfdf5;color:#0b4f35;padding:4px 12px;border-radius:6px;font-size:11px;font-weight:800;text-transform:uppercase">${isPaid ? '✓ TO\'LANGAN / PAID' : '⚠ KUTILMOQDA'}</div>
          <div style="font-size:9px;color:#6b7280;margin-top:6px;font-family:'Space Mono',monospace">TIZIM KODI: UZ-TR-90412883-26<br>SANA: ${formatDateSimple(item.crossing_at)}</div>
          <div style="margin-top:6px">${paymentStatus}</div>
        </div>
      </div>

      ${paymentWarning}

      <div class="title-bar">
        <div>
          <small style="font-size:10px;color:#86efac">${L.paymentInvoice?.toUpperCase() || 'INVOYS'}</small>
          <h2>№ ${docNo}</h2>
        </div>
        <div style="font-size:11px">
          <span style="color:#86efac">Deklaratsiya maqomi:</span>
          <span style="background:#16a34a;color:#fff;padding:3px 10px;border-radius:4px;font-size:10px;margin-left:6px">Yakunlandi</span>
        </div>
      </div>

      <div class="grid2">
        <div class="box">
          <h4>To'lovchi ma'lumotlari</h4>
          <div class="row"><span>${L.passport || 'Pasport'}:</span><strong>${payload.passport || '—'}</strong></div>
          <div class="row"><span>${L.nationality || 'Fuqaroligi'}:</span><strong>${payload.nationality || '—'}</strong></div>
          <div class="row"><span>Transport:</span><strong>${item.vehicle_plate || '—'} / ${payload.vehicle_country || '—'}</strong></div>
        </div>
        <div class="box">
          <h4>Chegara posti va kurslar</h4>
          <div class="row"><span>Post:</span><strong>${item.post_name || '—'}</strong></div>
          <div class="row"><span>1 BHM:</span><strong>375 000 UZS</strong></div>
          <div class="row"><span>1 USD:</span><strong>11 838.92 UZS</strong></div>
        </div>
      </div>

      <table>
        <thead>
          <tr>
            <th style="width:30px">№</th>
            <th>To'lov turi va asosi</th>
            <th style="width:100px">Stavka</th>
            <th style="width:50px;text-align:center">Miqdori</th>
            <th style="width:110px;text-align:right">Summasi (UZS)</th>
            <th style="width:80px;text-align:center">Holati</th>
          </tr>
        </thead>
        <tbody>
          <tr><td style="text-align:center;font-family:'Space Mono',monospace;font-weight:700">1</td><td><strong>Bojxona yig'imlari (Kirish)</strong><br><span style="font-size:9px;color:#6b7280">Tranzit rejimiga bojxona rasmiylashtiruvi</span></td><td style="font-size:10px;color:#6b7280">25% BHM</td><td style="text-align:center;font-family:'Space Mono',monospace">1</td><td style="text-align:right;font-family:'Space Mono',monospace;font-weight:700">110 000.00</td><td style="text-align:center;font-size:10px;${isPaid ? 'color:#16a34a;background:#f0fdf4' : 'color:#dc2626;background:#fef2f2'};font-weight:700">${isPaid ? 'To\'langan' : 'Kutilmoqda'}</td></tr>
          <tr><td style="text-align:center;font-family:'Space Mono',monospace;font-weight:700">2</td><td><strong>Veterinariya nazorati</strong><br><span style="font-size:9px;color:#6b7280">Sanitariya-ishlovidan o'tkazish</span></td><td style="font-size:10px;color:#6b7280">Maxsus stavka</td><td style="text-align:center;font-family:'Space Mono',monospace">1</td><td style="text-align:right;font-family:'Space Mono',monospace;font-weight:700">93 632.00</td><td style="text-align:center;font-size:10px;${isPaid ? 'color:#16a34a;background:#f0fdf4' : 'color:#dc2626;background:#fef2f2'};font-weight:700">${isPaid ? 'To\'langan' : 'Kutilmoqda'}</td></tr>
          <tr><td style="text-align:center;font-family:'Space Mono',monospace;font-weight:700">3</td><td><strong>Sug'urta mukofoti</strong><br><span style="font-size:9px;color:#6b7280">0.700 raz. BHM (68 km magistral)</span></td><td style="font-size:10px;color:#6b7280">0.700 BHM</td><td style="text-align:center;font-family:'Space Mono',monospace">68 km</td><td style="text-align:right;font-family:'Space Mono',monospace;font-weight:700">308 000.00</td><td style="text-align:center;font-size:10px;${isPaid ? 'color:#16a34a;background:#f0fdf4' : 'color:#dc2626;background:#fef2f2'};font-weight:700">${isPaid ? 'To\'langan' : 'Kutilmoqda'}</td></tr>
          <tr><td style="text-align:center;font-family:'Space Mono',monospace;font-weight:700">4</td><td><strong>Terminal yig'imlari</strong><br><span style="font-size:9px;color:#6b7280">Bojxona ombori xizmati</span></td><td style="font-size:10px;color:#6b7280">1 kun</td><td style="text-align:center;font-family:'Space Mono',monospace">1</td><td style="text-align:right;font-family:'Space Mono',monospace;font-weight:700">110 000.00</td><td style="text-align:center;font-size:10px;${isPaid ? 'color:#16a34a;background:#f0fdf4' : 'color:#dc2626;background:#fef2f2'};font-weight:700">${isPaid ? 'To\'langan' : 'Kutilmoqda'}</td></tr>
        </tbody>
        <tfoot>
          <tr><td colspan="4" style="text-align:right;font-size:11px;text-transform:uppercase;letter-spacing:.05em">Jami To'langan Mablag':</td><td style="text-align:right;font-size:14px;color:#86efac">${totalStr}</td><td style="text-align:center;font-size:10px;color:#86efac">${isPaid ? 'YOPILGAN' : 'OCHIQ'}</td></tr>
        </tfoot>
      </table>

      <div class="pay-row">
        <div><span style="color:#6b7280">To'lov usuli:</span> <strong>Elektron Bank Kliringi (Munis / Payme Gov)</strong> <span style="color:#d1d5db">|</span> <span style="color:#6b7280">TX:</span> <span style="font-family:'Space Mono',monospace;font-size:10px">TX-2026-${Math.floor(Math.random()*99999999)}-PAY</span></div>
        <div>${paymentStatusRow}</div>
      </div>

      <div class="stamp-row">
        <div>
          <h5 style="font-size:11px;font-weight:700;text-transform:uppercase;color:#1a1c1e;margin-bottom:4px">Elektron Raqamli Imzo (ERI)</h5>
          <p style="font-size:9px;color:#6b7280;line-height:1.4;max-width:300px">Ushbu hujjat qonunchilik asosida yaratilgan bo'lib, muhrlangan kvitansiya bilan teng yuridik kuchga ega.</p>
          <div style="font-size:9px;color:#6b7280;margin-top:4px;font-family:'Space Mono',monospace">ERI: ${item.inspector_name || 'Inspektor'} | Kalit: 6B8A91209FF412</div>
        </div>
        <div style="display:flex;align-items:center;gap:12px;border-left:1px solid #e5e7eb;padding-left:12px">
          <div class="stamp-circle">
            <span>DAVLAT BOJXONA QO'MITASI</span>
            <span style="font-size:7px;margin-top:2px">${formatDateSimple(item.crossing_at)}</span>
          </div>
        </div>
      </div>
    </div>

    <div class="footer-doc">
      <div>
        <strong style="color:#374151">Davlat Bojxona Qo'mitasi Yagona Axborot Tizimi</strong>
        <div>customs.uz | 1108 | +998 78 120-76-00</div>
      </div>
      <div style="text-align:right">
        <div style="font-family:'Space Mono',monospace;font-weight:700;color:#374151">AT-2026-${docNo.replace('AT','')}-DOC</div>
        <div>A4 Format · Sahifa 1 / 1</div>
      </div>
    </div>
  </div>
  </body></html>`;
}

/* ── Payment Modal ── */
function openPayModal(doc) {
  currentDocForPayment = doc;
  const modalDocName = $('modal-doc-name');
  if (modalDocName) modalDocName.textContent = doc.title || doc.code;
  const modalAmount = $('modal-amount');
  if (modalAmount) modalAmount.textContent = '621 632 UZS';
  const payTotal = $('pay-total');
  if (payTotal) payTotal.textContent = '621 632 UZS';

  showPayStep1();
  const modal = $('payment-modal');
  if (modal) { modal.hidden = false; document.body.style.overflow = 'hidden'; }
}

function closePayModal() {
  const modal = $('payment-modal');
  if (modal) { modal.hidden = true; document.body.style.overflow = ''; }
  showPayStep1();
}

function showPayStep1() { togglePaySteps(1); }
function showPayStep2() { togglePaySteps(2); }
function showPayStep3(method) {
  selectedPayMethod = method;
  const methodNames = { payme: 'Payme', click: 'Click', uzum: 'Uzum Bank', munis: 'Munis', uzcard: 'UzCard', humo: 'Humo' };
  const methodName = $('selected-method-name');
  if (methodName) methodName.textContent = methodNames[method] || method;
  togglePaySteps(3);
}
function togglePaySteps(step) {
  [1,2,3,4].forEach(n => {
    const el = $(`pay-step-${n}`);
    if (el) el.hidden = n !== step;
  });
}

function processPayment(e) {
  e.preventDefault();
  const num = $('card-number')?.value || '';
  if (num.replace(/\s/g,'').length < 16) { alert(t('cardNumber') + ' to\'liq emas!'); return; }

  // Simulate payment processing
  const btn = e.target.querySelector('[type="submit"]');
  if (btn) { btn.disabled = true; btn.textContent = '⏳...'; }

  setTimeout(() => {
    if (currentDocForPayment) paidDocs[currentDocForPayment.code] = true;

    const txId = $('tx-id');
    const paidAt = $('paid-at');
    if (txId) txId.textContent = 'TX-' + Date.now();
    if (paidAt) paidAt.textContent = new Date().toLocaleString();

    togglePaySteps(4);

    // Update doc payment badges
    if (record) renderDocuments(record.payload?.documents || []);
  }, 1500);
}

/* ── Card number formatting ── */
document.addEventListener('DOMContentLoaded', () => {
  const cardNum = $('card-number');
  if (cardNum) {
    cardNum.addEventListener('input', e => {
      let v = e.target.value.replace(/\D/g, '').slice(0, 16);
      e.target.value = v.replace(/(.{4})/g, '$1 ').trim();
    });
  }

  const cardExpiry = $('card-expiry');
  if (cardExpiry) {
    cardExpiry.addEventListener('input', e => {
      let v = e.target.value.replace(/\D/g, '').slice(0, 4);
      if (v.length >= 2) v = v.slice(0, 2) + '/' + v.slice(2);
      e.target.value = v;
    });
  }

  const cardCvv = $('card-cvv');
  if (cardCvv) {
    cardCvv.addEventListener('input', e => {
      e.target.value = e.target.value.replace(/\D/g, '').slice(0, 3);
    });
  }

  // Modal close on backdrop click
  const modal = $('payment-modal');
  if (modal) {
    modal.addEventListener('click', e => { if (e.target === modal) closePayModal(); });
  }
  $('modal-close')?.addEventListener('click', closePayModal);

  // Language download buttons
  document.querySelectorAll('.lang-dl').forEach(btn => {
    btn.addEventListener('click', () => {
      selectedDlLang = btn.dataset.dlang;
      document.querySelectorAll('.lang-dl').forEach(b => b.classList.toggle('active', b.dataset.dlang === selectedDlLang));
    });
  });
});

/* ── Language switcher ── */
document.querySelectorAll('[data-lang]').forEach(btn => {
  btn.addEventListener('click', () => { lang = btn.dataset.lang; applyLanguage(); });
});

/* ── Card animation ── */
function animateCards() {
  const cards = document.querySelectorAll('.card, .law-card, .official, .download-section');
  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry, idx) => {
      if (entry.isIntersecting) {
        setTimeout(() => {
          entry.target.style.opacity = '1';
          entry.target.style.transform = 'translateY(0)';
        }, idx * 80);
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.1 });

  cards.forEach(card => {
    card.style.opacity = '0';
    card.style.transform = 'translateY(20px)';
    card.style.transition = 'opacity .5s ease, transform .5s ease';
    observer.observe(card);
  });
}

/* ── Main: load document ── */
(async () => {
  initParticles();

  // Get token from URL path — /visit/{token}
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
    console.error('Document load error:', err);
    $('loading').hidden = true;
    $('error').hidden = false;
  }
})();

// Expose payment functions globally
window.openPayModal = openPayModal;
window.closePayModal = closePayModal;
window.showPayStep1 = showPayStep1;
window.showPayStep2 = showPayStep2;
window.showPayStep3 = showPayStep3;
window.processPayment = processPayment;
window.downloadDocumentPDF = downloadDocumentPDF;

// Inspector Workstation Script · E-Bojxona
const COUNTRIES_CLASSIFIER = [
  { code: "AF", num: "004", name: "Afg'oniston" },
  { code: "AX", num: "248", name: "Aland Orollari" },
  { code: "AL", num: "008", name: "Albaniya" },
  { code: "US", num: "840", name: "AQSH" },
  { code: "AS", num: "016", name: "Amerika Samoasi" },
  { code: "AD", num: "020", name: "Andorra" },
  { code: "AI", num: "660", name: "Angilya" },
  { code: "AO", num: "024", name: "Angola" },
  { code: "AQ", num: "010", name: "Antarktida" },
  { code: "AG", num: "028", name: "Antigua va Barbuda" },
  { code: "AR", num: "032", name: "Argentina" },
  { code: "AM", num: "051", name: "Armaniston" },
  { code: "AW", num: "533", name: "Aruba" },
  { code: "AU", num: "036", name: "Avstraliya" },
  { code: "AT", num: "040", name: "Avstriya" },
  { code: "BS", num: "044", name: "Bagam Orollari" },
  { code: "BH", num: "048", name: "Bahrayn" },
  { code: "BD", num: "050", name: "Bangladesh" },
  { code: "BB", num: "052", name: "Barbados" },
  { code: "BY", num: "112", name: "Belarus" },
  { code: "BE", num: "056", name: "Belgiya" },
  { code: "BZ", num: "084", name: "Beliz" },
  { code: "BJ", num: "204", name: "Benin" },
  { code: "BM", num: "060", name: "Bermud Orollari" },
  { code: "AE", num: "784", name: "Birlashgan Arab Amirliklari" },
  { code: "GB", num: "826", name: "Buyuk Britaniya" },
  { code: "BG", num: "100", name: "Bolgariya" },
  { code: "BO", num: "068", name: "Boliviya" },
  { code: "BQ", num: "535", name: "Boneyr, Sint-Estatius" },
  { code: "BA", num: "070", name: "Bosniya va Gersegovina" },
  { code: "BW", num: "072", name: "Botsvana" },
  { code: "BR", num: "076", name: "Braziliya" },
  { code: "IO", num: "086", name: "Britan Hududlari" },
  { code: "BN", num: "096", name: "Bruney-Dorussalom" },
  { code: "BV", num: "074", name: "Buve Oroli" },
  { code: "BF", num: "854", name: "Burkina-Faso" },
  { code: "BI", num: "108", name: "Burundi" },
  { code: "BT", num: "064", name: "Butan" },
  { code: "VU", num: "548", name: "Vanuatu" },
  { code: "VA", num: "336", name: "Vatikan" },
  { code: "HU", num: "348", name: "Vengriya" },
  { code: "VE", num: "862", name: "Venesuela" },
  { code: "VI", num: "850", name: "Virgin Orollari (AQSH)" },
  { code: "VG", num: "092", name: "Virgin Orollari (Brit.)" },
  { code: "VN", num: "704", name: "Vyetnam" },
  { code: "GA", num: "266", name: "Gabon" },
  { code: "HT", num: "332", name: "Gaiti" },
  { code: "GM", num: "270", name: "Gambiya" },
  { code: "GH", num: "288", name: "Gana" },
  { code: "GY", num: "328", name: "Gayana" },
  { code: "GP", num: "312", name: "Gvadelupa" },
  { code: "GT", num: "320", name: "Gvatemala" },
  { code: "GN", num: "324", name: "Gvineya" },
  { code: "GW", num: "624", name: "Gvineya-Bisau" },
  { code: "DE", num: "276", name: "Germaniya" },
  { code: "GG", num: "831", name: "Gernsi" },
  { code: "GI", num: "292", name: "Gibraltar" },
  { code: "HN", num: "340", name: "Gonduras" },
  { code: "HK", num: "344", name: "Gonkong" },
  { code: "GD", num: "308", name: "Grenada" },
  { code: "GL", num: "304", name: "Grenlandiya" },
  { code: "GR", num: "300", name: "Gretsiya" },
  { code: "GE", num: "268", name: "Gruziya" },
  { code: "GU", num: "316", name: "Guam" },
  { code: "DK", num: "208", name: "Daniya" },
  { code: "JE", num: "832", name: "Djersi" },
  { code: "DJ", num: "262", name: "Djibuti" },
  { code: "DM", num: "212", name: "Dominika" },
  { code: "DO", num: "214", name: "Dominika Respublikasi" },
  { code: "DZ", num: "012", name: "Jazoir" },
  { code: "ZA", num: "710", name: "Janubiy Afrika" },
  { code: "SS", num: "728", name: "Janubiy Sudan" },
  { code: "GS", num: "239", name: "Janubiy Jorjiya" },
  { code: "ZM", num: "894", name: "Zambiya" },
  { code: "ZW", num: "716", name: "Zimbabve" },
  { code: "IL", num: "376", name: "Isroil" },
  { code: "IN", num: "356", name: "Hindiston" },
  { code: "ID", num: "360", name: "Indoneziya" },
  { code: "JO", num: "400", name: "Iordaniya" },
  { code: "IQ", num: "368", name: "Iroq" },
  { code: "IR", num: "364", name: "Eron" },
  { code: "IE", num: "372", name: "Irlandiya" },
  { code: "IS", num: "352", name: "Islandiya" },
  { code: "ES", num: "724", name: "Ispaniya" },
  { code: "IT", num: "380", name: "Italiya" },
  { code: "YE", num: "887", name: "Yaman" },
  { code: "CV", num: "132", name: "Kabo-Verde" },
  { code: "KZ", num: "398", name: "Qozog'iston" },
  { code: "KY", num: "136", name: "Kayman" },
  { code: "KH", num: "116", name: "Kamboja" },
  { code: "CM", num: "120", name: "Kamerun" },
  { code: "CA", num: "124", name: "Kanada" },
  { code: "QA", num: "634", name: "Qatar" },
  { code: "KE", num: "404", name: "Keniya" },
  { code: "CY", num: "196", name: "Kipr" },
  { code: "KI", num: "296", name: "Kiribati" },
  { code: "CN", num: "156", name: "Xitoy" },
  { code: "CC", num: "166", name: "Kokos Orollari" },
  { code: "CO", num: "170", name: "Kolumbiya" },
  { code: "KM", num: "174", name: "Komor Orollari" },
  { code: "CG", num: "178", name: "Kongo" },
  { code: "CD", num: "180", name: "Kongo (KDR)" },
  { code: "KR", num: "410", name: "Koreya Respublikasi" },
  { code: "KP", num: "408", name: "Koreya (KXDR)" },
  { code: "CR", num: "188", name: "Kosta-Rika" },
  { code: "CI", num: "384", name: "Kot-d'Ivuar" },
  { code: "CU", num: "192", name: "Kuba" },
  { code: "KW", num: "414", name: "Quvayt" },
  { code: "KG", num: "417", name: "Qirg'iziston" },
  { code: "CW", num: "531", name: "Kyurasao" },
  { code: "LA", num: "418", name: "Laos" },
  { code: "LV", num: "428", name: "Latviya" },
  { code: "LS", num: "426", name: "Lesoto" },
  { code: "LR", num: "430", name: "Liberiya" },
  { code: "LB", num: "422", name: "Livan" },
  { code: "LY", num: "434", name: "Liviya" },
  { code: "LT", num: "440", name: "Litva" },
  { code: "LI", num: "438", name: "Lixtenshteyn" },
  { code: "LU", num: "442", name: "Lyuksemburg" },
  { code: "MU", num: "480", name: "Mavrikiy" },
  { code: "MR", num: "478", name: "Mavritaniya" },
  { code: "MG", num: "450", name: "Madagaskar" },
  { code: "YT", num: "175", name: "Mayotta" },
  { code: "MO", num: "446", name: "Makao" },
  { code: "MK", num: "807", name: "Makedoniya" },
  { code: "MW", num: "454", name: "Malavi" },
  { code: "MY", num: "458", name: "Malayziya" },
  { code: "ML", num: "466", name: "Mali" },
  { code: "MV", num: "462", name: "Maldiv" },
  { code: "MT", num: "470", name: "Malta" },
  { code: "MP", num: "580", name: "Marian Orollari" },
  { code: "MA", num: "504", name: "Marokash" },
  { code: "MQ", num: "474", name: "Martinika" },
  { code: "MH", num: "584", name: "Marshall Orollari" },
  { code: "MX", num: "484", name: "Meksika" },
  { code: "FM", num: "583", name: "Mikroneziya" },
  { code: "EG", num: "818", name: "Misr" },
  { code: "MZ", num: "508", name: "Mozambik" },
  { code: "MD", num: "498", name: "Moldova" },
  { code: "MC", num: "492", name: "Monako" },
  { code: "MN", num: "496", name: "Mo'g'uliston" },
  { code: "MS", num: "500", name: "Montserrat" },
  { code: "MM", num: "104", name: "Myanma" },
  { code: "NA", num: "516", name: "Namibiya" },
  { code: "NR", num: "520", name: "Nauru" },
  { code: "NP", num: "524", name: "Nepal" },
  { code: "NE", num: "562", name: "Niger" },
  { code: "NG", num: "566", name: "Nigeriya" },
  { code: "NL", num: "528", name: "Niderlandiya" },
  { code: "NI", num: "558", name: "Nikaragua" },
  { code: "NU", num: "570", name: "Niue" },
  { code: "NO", num: "578", name: "Norvegiya" },
  { code: "NF", num: "574", name: "Norfolk" },
  { code: "AZ", num: "031", name: "Ozarbayjon" },
  { code: "UZ", num: "860", name: "O'zbekiston" },
  { code: "OM", num: "512", name: "Ummon" },
  { code: "PK", num: "586", name: "Pokiston" },
  { code: "PW", num: "585", name: "Palau" },
  { code: "PS", num: "275", name: "Falastin" },
  { code: "PA", num: "591", name: "Panama" },
  { code: "PG", num: "598", name: "Papua - Yangi Gvineya" },
  { code: "PY", num: "600", name: "Paragvay" },
  { code: "PE", num: "604", name: "Peru" },
  { code: "PN", num: "612", name: "Pitkern" },
  { code: "PL", num: "616", name: "Polsha" },
  { code: "PT", num: "620", name: "Portugaliya" },
  { code: "PR", num: "630", name: "Puerto-Riko" },
  { code: "RE", num: "638", name: "Reyunon" },
  { code: "RU", num: "643", name: "Rossiya" },
  { code: "RW", num: "646", name: "Ruanda" },
  { code: "RO", num: "642", name: "Ruminiya" },
  { code: "SV", num: "222", name: "Salvador" },
  { code: "WS", num: "882", name: "Samoa" },
  { code: "SM", num: "674", name: "San-Marino" },
  { code: "ST", num: "678", name: "San-Tome va Prinsipi" },
  { code: "SA", num: "682", name: "Saudiya Arabistoni" },
  { code: "SZ", num: "748", name: "Svazilend (Esvatini)" },
  { code: "SC", num: "690", name: "Seyshel" },
  { code: "SN", num: "686", name: "Senegal" },
  { code: "RS", num: "688", name: "Serbiya" },
  { code: "SG", num: "702", name: "Singapur" },
  { code: "SY", num: "760", name: "Suriya" },
  { code: "SK", num: "703", name: "Slovakiya" },
  { code: "SI", num: "705", name: "Sloveniya" },
  { code: "SO", num: "706", name: "Somali" },
  { code: "SD", num: "736", name: "Sudan" },
  { code: "SR", num: "740", name: "Surinam" },
  { code: "SL", num: "694", name: "Syerra-Leone" },
  { code: "TJ", num: "762", name: "Tojikiston" },
  { code: "TH", num: "764", name: "Tailand" },
  { code: "TW", num: "158", name: "Tayvan" },
  { code: "TZ", num: "834", name: "Tanzaniya" },
  { code: "TL", num: "626", name: "Timor-Leste" },
  { code: "TG", num: "768", name: "Togo" },
  { code: "TO", num: "776", name: "Tonga" },
  { code: "TT", num: "780", name: "Trinidad va Tobago" },
  { code: "TN", num: "788", name: "Tunis" },
  { code: "TM", num: "795", name: "Turkmaniston" },
  { code: "TR", num: "792", name: "Turkiya" },
  { code: "UG", num: "800", name: "Uganda" },
  { code: "UA", num: "804", name: "Ukraina" },
  { code: "UY", num: "858", name: "Urugvay" },
  { code: "FJ", num: "242", name: "Fiji" },
  { code: "PH", num: "608", name: "Filippin" },
  { code: "FI", num: "246", name: "Finlyandiya" },
  { code: "FR", num: "250", name: "Fransiya" },
  { code: "HR", num: "191", name: "Xorvatiya" },
  { code: "TD", num: "148", name: "Chad" },
  { code: "ME", num: "499", name: "Chernogoriya" },
  { code: "CZ", num: "203", name: "Chexiya" },
  { code: "CL", num: "152", name: "Chili" },
  { code: "CH", num: "756", name: "Shveysariya" },
  { code: "SE", num: "752", name: "Shvetsiya" },
  { code: "LK", num: "144", name: "Shri-Lanka" },
  { code: "EC", num: "218", name: "Ekvador" },
  { code: "GQ", num: "226", name: "Ekvatorial Gvineya" },
  { code: "ER", num: "232", name: "Eritreya" },
  { code: "EE", num: "233", name: "Estoniya" },
  { code: "ET", num: "231", name: "Efiopiya" },
  { code: "JM", num: "388", name: "Yamayka" },
  { code: "JP", num: "392", name: "Yaponiya" },
  { code: "NZ", num: "554", name: "Yangi Zelandiya" }
];

let allCustomsPosts = [];
let activePickerTarget = null; // 'driver' or 'vehicle'
let currentGeneratedDocument = null;

// DOM Elements
const postCodeSelect = document.getElementById('post-code');
const crossingTimeInput = document.getElementById('crossing-time');
const driverCountryInput = document.getElementById('driver-country-code');
const vehicleCountryInput = document.getElementById('vehicle-country-code');
const driverNameInput = document.getElementById('driver-name');
const driverPassportInput = document.getElementById('driver-passport');
const driverPhoneInput = document.getElementById('driver-phone');
const vehiclePlateInput = document.getElementById('vehicle-plate');
const vehicleModelInput = document.getElementById('vehicle-model');
const vehicleImageTypeInput = document.getElementById('vehicle-image-type');
const trailerPlateInput = document.getElementById('trailer-plate');
const cargoDescInput = document.getElementById('cargo-desc');
const inspectorNameInput = document.getElementById('inspector-name');
const directionSelect = document.getElementById('direction-type');
const destinationInput = document.getElementById('destination-name');
const docsTableBody = document.getElementById('docs-table-body');
const issuanceForm = document.getElementById('issuance-form');
const countryModal = document.getElementById('country-modal');
const modalCountrySearch = document.getElementById('modal-country-search');
const modalCountryList = document.getElementById('modal-country-list');
const journalTableBody = document.getElementById('journal-table-body');
const journalSearchInput = document.getElementById('journal-search');

// Toast helper
function showToast(msg, isError = false) {
  const toast = document.getElementById('toast');
  if (!toast) return;
  toast.textContent = msg;
  toast.className = 'toast-msg' + (isError ? ' error' : '');
  toast.style.display = 'flex';
  setTimeout(() => { toast.style.display = 'none'; }, 3200);
}

// Live Clock
function updateClock() {
  const el = document.getElementById('live-clock');
  if (!el) return;
  const now = new Date();
  const pad = n => String(n).padStart(2, '0');
  el.textContent = `${now.getFullYear()}-${pad(now.getMonth()+1)}-${pad(now.getDate())} ${pad(now.getHours())}:${pad(now.getMinutes())}:${pad(now.getSeconds())}`;
}
setInterval(updateClock, 1000);
updateClock();

// Initialize default date
function setDefaultDate() {
  const now = new Date();
  now.setMinutes(now.getMinutes() - now.getTimezoneOffset());
  if (crossingTimeInput) crossingTimeInput.value = now.toISOString().slice(0, 16);
}
setDefaultDate();

// Flag URL helper
function getFlagUrl(code) {
  return `/static/webapp/flags/${String(code || 'uz').toLowerCase()}.svg`;
}

// Populate customs posts dropdown
async function loadPosts() {
  try {
    const res = await fetch('/admin/api/posts');
    const data = await res.json();
    if (data.ok && Array.isArray(data.items) && data.items.length) {
      allCustomsPosts = data.items;
    }
  } catch (e) {
    console.warn("Could not fetch remote posts, waiting for fallback", e);
  }

  if (!allCustomsPosts.length) {
    // If empty, will populate when server returns or fallback
    return;
  }

  // Group by region
  const grouped = {};
  allCustomsPosts.forEach(post => {
    const reg = post.region || "Boshqa hududlar";
    if (!grouped[reg]) grouped[reg] = [];
    grouped[reg].push(post);
  });

  postCodeSelect.innerHTML = '<option value="">-- Bojxona postini tanlang (93 ta post) --</option>';
  for (const [region, posts] of Object.entries(grouped)) {
    const optgroup = document.createElement('optgroup');
    optgroup.label = `📍 ${region}`;
    posts.forEach(p => {
      const opt = document.createElement('option');
      opt.value = p.code;
      opt.textContent = `${p.code} — ${p.name_uz || p.name_ru || p.name_en}`;
      optgroup.appendChild(opt);
    });
    postCodeSelect.appendChild(optgroup);
  }

  // Pre-select popular post if available (e.g. Yallama or G'ishtko'prik)
  const defaultPost = allCustomsPosts.find(p => p.code === '27001' || p.code === '27021' || p.code === '03002');
  if (defaultPost) {
    postCodeSelect.value = defaultPost.code;
    updateReceiptPreview();
  }
}

// Country Picker logic
function openCountryPicker(target) {
  activePickerTarget = target;
  modalCountrySearch.value = "";
  renderModalCountries(COUNTRIES_CLASSIFIER);
  countryModal.classList.add('open');
  setTimeout(() => modalCountrySearch.focus(), 80);
}

function closeCountryPicker() {
  countryModal.classList.remove('open');
  activePickerTarget = null;
}

function renderModalCountries(list) {
  modalCountryList.innerHTML = list.map(c => `
    <button type="button" class="country-item-btn" onclick="selectCountry('${c.code}', '${c.name.replace(/'/g, "\\'")}')">
      <img src="${getFlagUrl(c.code)}" alt="${c.name}" onerror="this.onerror=null;this.src='/static/webapp/flags/uz.svg'">
      <div class="name-wrap">
        <div class="c-name">${c.name}</div>
        <div class="c-code">${c.code} · ${c.num}</div>
      </div>
    </button>
  `).join('') || '<div style="grid-column:1/-1;text-align:center;padding:20px;color:var(--muted);">Davlat topilmadi</div>';
}

modalCountrySearch.addEventListener('input', (e) => {
  const q = e.target.value.trim().toLowerCase();
  if (!q) {
    renderModalCountries(COUNTRIES_CLASSIFIER);
    return;
  }
  const filtered = COUNTRIES_CLASSIFIER.filter(c =>
    c.name.toLowerCase().includes(q) ||
    c.code.toLowerCase().includes(q) ||
    c.num.includes(q)
  );
  renderModalCountries(filtered);
});

function selectCountry(code, name) {
  if (activePickerTarget === 'driver') {
    driverCountryInput.value = code;
    document.getElementById('driver-country-flag').src = getFlagUrl(code);
    document.getElementById('driver-country-name').textContent = name;
    document.getElementById('driver-country-pill').textContent = code;
  } else if (activePickerTarget === 'vehicle') {
    vehicleCountryInput.value = code;
    document.getElementById('vehicle-country-flag').src = getFlagUrl(code);
    document.getElementById('vehicle-country-name').textContent = name;
    document.getElementById('vehicle-country-pill').textContent = code;
  }
  closeCountryPicker();
  updateReceiptPreview();
}

// Quick chips handler
window.setQuickCountry = function(target, code, name) {
  activePickerTarget = target;
  selectCountry(code, name);
};

// Document Table row logic
function addDocumentRow(docType = "Invoys", docNo = "", docDate = "", note = "") {
  const tr = document.createElement('tr');
  tr.innerHTML = `
    <td>
      <select class="doc-type-sel">
        <option value="Invoys" ${docType === 'Invoys' ? 'selected' : ''}>Invoys (Hisob-faktura)</option>
        <option value="Majburiyatnoma" ${docType === 'Majburiyatnoma' ? 'selected' : ''}>Majburiyatnoma</option>
        <option value="Sug'urta polisi" ${docType === 'Sug\'urta polisi' ? 'selected' : ''}>OSAGO Sug'urta</option>
        <option value="CMR / Yuk xati" ${docType.includes('CMR') ? 'selected' : ''}>CMR / Yuk xati</option>
        <option value="TIR Carnet" ${docType === 'TIR Carnet' ? 'selected' : ''}>TIR Carnet</option>
        <option value="Tranzit deklaratsiyasi" ${docType.includes('Tranzit') ? 'selected' : ''}>Tranzit deklaratsiyasi</option>
        <option value="Karantin ruxsatnomasi" ${docType.includes('Karantin') ? 'selected' : ''}>Karantin dalolatnomasi</option>
        <option value="Boshqa hujjat" ${docType === 'Boshqa hujjat' ? 'selected' : ''}>Boshqa hujjat</option>
      </select>
    </td>
    <td><input type="text" class="doc-no-inp" placeholder="№ 12345/26" value="${docNo}"></td>
    <td><input type="text" class="doc-date-inp" placeholder="Sanasi" value="${docDate}"></td>
    <td><input type="text" class="doc-note-inp" placeholder="Qo'shimcha izoh" value="${note}"></td>
    <td style="text-align:center;">
      <button type="button" class="btn-row-del" onclick="this.closest('tr').remove(); updateReceiptPreview();">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polyline points="3 6 5 6 21 6"></polyline>
          <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
        </svg>
      </button>
    </td>
  `;
  tr.querySelectorAll('input, select').forEach(el => el.addEventListener('input', updateReceiptPreview));
  docsTableBody.appendChild(tr);
  updateReceiptPreview();
}

function getDocumentsPayload() {
  const rows = docsTableBody.querySelectorAll('tr');
  const list = [];
  rows.forEach((tr, index) => {
    const type = tr.querySelector('.doc-type-sel')?.value || 'Invoys';
    const no = tr.querySelector('.doc-no-inp')?.value.trim() || '';
    const date = tr.querySelector('.doc-date-inp')?.value.trim() || '';
    const note = tr.querySelector('.doc-note-inp')?.value.trim() || '';
    const code = no || `DOC-${index + 1}`;
    const title = type + (no ? ` № ${no}` : '');
    list.push({
      code: code,
      title: title,
      status: "Rasmiylashtirilgan",
      description: note || date || "Tekshirildi",
      type: type,
      number: no,
      date: date,
      note: note
    });
  });
  if (list.length === 0) {
    list.push({
      code: "INV",
      title: "Invoys / Yuk xati",
      status: "Rasmiylashtirilgan",
      description: "Asosiy invoys hujjati",
      type: "Invoys",
      number: "1",
      date: "",
      note: ""
    });
  }
  return list;
}

// Receipt Live Preview
function updateReceiptPreview() {
  const postCode = postCodeSelect.value;
  const postObj = allCustomsPosts.find(p => p.code === postCode);
  const postName = postObj ? (postObj.name_uz || postObj.name_ru || postCode) : (postCode || "Post belgilanmagan");

  const plate = vehiclePlateInput.value.trim().toUpperCase() || "—";
  const driver = driverNameInput.value.trim() || "—";
  const driverCountry = driverCountryInput.value || "UZ";
  const vehicleCountry = vehicleCountryInput.value || "UZ";
  const cargo = cargoDescInput.value.trim() || "Standart yuk";
  const time = crossingTimeInput.value || "—";

  document.getElementById('rcpt-post').textContent = `${postCode ? postCode + ' · ' : ''}${postName}`;
  document.getElementById('rcpt-plate').textContent = `${plate} (${vehicleCountry})`;
  document.getElementById('rcpt-driver').textContent = `${driver} (${driverCountry})`;
  document.getElementById('rcpt-cargo').textContent = cargo;
  document.getElementById('rcpt-time').textContent = time;
  const dateLabel = time === '—' ? 'shu kuni' : time.replace('T', ' ');
  ['uz', 'ru', 'en'].forEach(code => {
    const nameNode = document.getElementById(`rcpt-name-${code}`);
    const dateNode = document.getElementById(`rcpt-date-${code}`);
    const borderNode = document.getElementById(`rcpt-border-${code}`);
    if (nameNode) nameNode.textContent = driver === '—' ? (code === 'ru' ? 'посетитель' : code === 'en' ? 'visitor' : 'tashrif buyuruvchi') : driver;
    if (dateNode) dateNode.textContent = dateLabel;
    if (borderNode) borderNode.textContent = postName;
  });

  const docs = getDocumentsPayload();
  const rcptDocsWrap = document.getElementById('rcpt-docs-list');
  if (docs.length) {
    rcptDocsWrap.innerHTML = docs.map(d => `<div>• ${d.type} ${d.number ? '№ ' + d.number : ''}</div>`).join('');
  } else {
    rcptDocsWrap.innerHTML = `<span style="color:var(--muted)">Hujjatlar kiritilmadi</span>`;
  }
}

// Bind live updates
[driverNameInput, vehiclePlateInput, vehicleModelInput, vehicleImageTypeInput, cargoDescInput, crossingTimeInput, postCodeSelect].forEach(el => {
  if (el) el.addEventListener('input', updateReceiptPreview);
});

// Form Submit -> Create Document
issuanceForm.addEventListener('submit', async (e) => {
  e.preventDefault();

  const postCode = postCodeSelect.value;
  if (!postCode) {
    showToast("Iltimos, bojxona postini tanlang!", true);
    postCodeSelect.focus();
    return;
  }

  const plate = vehiclePlateInput.value.trim().toUpperCase();
  if (!plate) {
    showToast("Transport vositasi davlat raqamini kiriting!", true);
    vehiclePlateInput.focus();
    return;
  }

  const driverName = driverNameInput.value.trim();
  if (!driverName) {
    showToast("Haydovchi ism-familiyasini kiriting!", true);
    driverNameInput.focus();
    return;
  }

  const submitBtn = document.getElementById('btn-issue-submit');
  submitBtn.disabled = true;
  submitBtn.innerHTML = `<span>Shakllantirilmoqda...</span>`;

  const postObj = allCustomsPosts.find(p => p.code === postCode);
  const postName = postObj ? (postObj.name_uz || postObj.name_ru || postCode) : `Bojxona posti ${postCode}`;

  const payload = {
    post_code: postCode,
    post_name: postName,
    crossing_at: crossingTimeInput.value || "",
    crossing_time: crossingTimeInput.value || "",
    direction: directionSelect.value,
    destination: destinationInput.value.trim(),
    location: destinationInput.value.trim(),
    driver_name: driverName,
    driver_passport: driverPassportInput.value.trim().toUpperCase(),
    passport: driverPassportInput.value.trim().toUpperCase(),
    driver_phone: driverPhoneInput.value.trim(),
    phone: driverPhoneInput.value.trim(),
    driver_country: driverCountryInput.value,
    nationality: driverCountryInput.value,
    vehicle_plate: plate,
    vehicle_model: vehicleModelInput.value.trim(),
    vehicle_image_type: vehicleImageTypeInput.value || "auto",
    trailer_plate: trailerPlateInput.value.trim().toUpperCase(),
    vehicle_country: vehicleCountryInput.value,
    cargo_description: cargoDescInput.value.trim(),
    cargo: cargoDescInput.value.trim(),
    inspector_name: inspectorNameInput.value.trim() || "Navbatchi inspektor",
    service_note: document.getElementById('service-note')?.value.trim() || "",
    documents: getDocumentsPayload()
  };

  try {
    const res = await fetch('/admin/api/inspector-documents', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRF-Token': getCookie('nazorat_csrf') || ''
      },
      body: JSON.stringify(payload)
    });

    const data = await res.json();
    if (res.ok && data.ok && data.document) {
      currentGeneratedDocument = data.document;
      showToast("Bojxona tekshiruv hujjati muvaffaqiyatli shakllantirildi!");
      displayGeneratedReceipt(data.document);
      loadJournal();
    } else {
      showToast(data.error || "Hujjatni shakllantirishda xatolik yuz berdi.", true);
    }
  } catch (err) {
    showToast("Server bilan aloqa xatosi: " + err.message, true);
  } finally {
    submitBtn.disabled = false;
    submitBtn.innerHTML = `
      <span>QR-kodli hujjatni shakllantirish</span>
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
        <path d="M5 12h14"></path>
        <path d="m12 5 7 7-7 7"></path>
      </svg>
    `;
  }
});

function displayGeneratedReceipt(doc) {
  const details = doc.payload || {};
  if (doc.post_name) document.getElementById('rcpt-post').textContent = doc.post_name;
  if (doc.crossing_at) document.getElementById('rcpt-time').textContent = String(doc.crossing_at).replace('T', ' ').slice(0, 19);
  if (doc.vehicle_plate) document.getElementById('rcpt-plate').textContent = `${doc.vehicle_plate} (${details.vehicle_country || 'UZ'})`;
  if (doc.driver_name) document.getElementById('rcpt-driver').textContent = `${doc.driver_name} (${details.nationality || 'UZ'})`;
  if (details.cargo) document.getElementById('rcpt-cargo').textContent = details.cargo;
  ['uz', 'ru', 'en'].forEach(code => {
    const nameNode = document.getElementById(`rcpt-name-${code}`);
    const dateNode = document.getElementById(`rcpt-date-${code}`);
    const borderNode = document.getElementById(`rcpt-border-${code}`);
    if (nameNode) nameNode.textContent = doc.driver_name || (code === 'ru' ? 'посетитель' : code === 'en' ? 'visitor' : 'tashrif buyuruvchi');
    if (dateNode) dateNode.textContent = String(doc.crossing_at || '').replace('T', ' ').slice(0, 16) || '—';
    if (borderNode) borderNode.textContent = doc.post_name || '—';
  });
  if (Array.isArray(details.documents) && details.documents.length) {
    document.getElementById('rcpt-docs-list').replaceChildren(...details.documents.map(item => {
      const row = document.createElement('div');
      row.textContent = `• ${item.title || item.type || 'Hujjat'} ${item.code ? '№ ' + item.code : ''}`;
      return row;
    }));
  }
  document.getElementById('rcpt-doc-no').textContent = doc.document_no || "№ " + (doc.public_token || "").slice(0, 8).toUpperCase();
  const qrImage = document.getElementById('rcpt-qr-img');
  qrImage.src = doc.qr_url || `/api/inspector/documents/${doc.public_token}/qr.svg`;
  qrImage.classList.remove('preview-placeholder');
  document.getElementById('rcpt-stamp').style.display = 'block';
  document.getElementById('rcpt-actions').style.display = 'flex';

  const viewBtn = document.getElementById('btn-rcpt-view');
  if (viewBtn) viewBtn.href = doc.public_url;

  window.scrollTo({ top: 120, behavior: 'smooth' });
}

// Print Handler
window.printReceipt = function() {
  window.print();
};

// Copy Public Link
window.copyReceiptLink = function() {
  if (!currentGeneratedDocument || !currentGeneratedDocument.public_url) {
    showToast("Hujjat havolasi mavjud emas", true);
    return;
  }
  navigator.clipboard.writeText(currentGeneratedDocument.public_url)
    .then(() => showToast("Havola nusxalandi!"))
    .catch(() => showToast("Nusxalab bo'lmadi", true));
};

// Journal loader
async function loadJournal() {
  try {
    const res = await fetch('/admin/api/inspector-documents?limit=100');
    const data = await res.json();
    if (data.ok && Array.isArray(data.items)) {
      renderJournal(data.items);
    }
  } catch (err) {
    console.error("Journal loading error:", err);
  }
}

function renderJournal(items) {
  const q = (journalSearchInput?.value || "").trim().toLowerCase();
  const filtered = items.filter(item => {
    if (!q) return true;
    return (
      (item.document_no || "").toLowerCase().includes(q) ||
      (item.vehicle_plate || "").toLowerCase().includes(q) ||
      (item.driver_name || "").toLowerCase().includes(q) ||
      (item.post_code || "").toLowerCase().includes(q)
    );
  });

  if (!filtered.length) {
    journalTableBody.innerHTML = `<tr><td colspan="7" style="text-align:center;padding:24px;color:#94a3b8;">Hujjatlar topilmadi</td></tr>`;
    return;
  }

  journalTableBody.innerHTML = filtered.map(item => {
    const isActive = item.status === 'active' || item.status === 'valid' || !item.status;
    return `
      <tr>
        <td><b>${item.document_no || '№ ' + (item.public_token || '').slice(0, 8)}</b></td>
        <td>${(item.crossing_time || item.created_at || '').replace('T', ' ').slice(0, 16)}</td>
        <td><b>${item.post_code || '—'}</b></td>
        <td>
          <span style="font-weight:700;">${item.vehicle_plate || '—'}</span>
          <span style="color:#94a3b8;font-size:11px;">(${item.vehicle_country || 'UZ'})</span>
        </td>
        <td>${item.driver_name || '—'}</td>
        <td>
          <span class="status-pill ${isActive ? 'active' : 'revoked'}">
            ${isActive ? '🟢 Faol' : '🔴 Bekor'}
          </span>
        </td>
        <td>
          <div class="table-actions">
            <button class="btn-mini" onclick="previewFromJournal('${item.public_token}')">Chek</button>
            <a class="btn-mini" href="${item.public_url}" target="_blank">Ochish</a>
            <button class="btn-mini ${isActive ? 'danger' : ''}" onclick="toggleStatus('${item.public_token}', '${isActive ? 'revoked' : 'active'}')">
              ${isActive ? 'Bekor qilish' : 'Faollashtirish'}
            </button>
          </div>
        </td>
      </tr>
    `;
  }).join('');
}

journalSearchInput?.addEventListener('input', () => {
  loadJournal();
});

window.previewFromJournal = async function(token) {
  try {
    const res = await fetch(`/api/inspector/documents/${token}`);
    const data = await res.json();
    if (data.ok && data.document) {
      currentGeneratedDocument = {
        ...data.document,
        public_token: token,
        qr_url: `/api/inspector/documents/${token}/qr.svg`,
        public_url: window.location.origin + `/visit/${token}`
      };
      displayGeneratedReceipt(currentGeneratedDocument);
      showToast("Kvitansiya prevyuga yuklandi");
    }
  } catch (err) {
    showToast("Hujjatni yuklab bo'lmadi", true);
  }
};

window.toggleStatus = async function(token, newStatus) {
  if (!confirm(`Hujjat holatini "${newStatus === 'active' ? 'Faol' : 'Bekor qilingan'}" ga o'zgartirishni tasdiqlaysizmi?`)) return;
  try {
    const res = await fetch(`/admin/api/inspector-documents/${token}/status`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRF-Token': getCookie('nazorat_csrf') || ''
      },
      body: JSON.stringify({ status: newStatus })
    });
    const data = await res.json();
    if (res.ok && data.ok) {
      showToast("Holat yangilandi");
      loadJournal();
    } else {
      showToast(data.error || "Holatni o'zgartirib bo'lmadi", true);
    }
  } catch (e) {
    showToast("Aloqa xatosi", true);
  }
};

function getCookie(name) {
  const match = document.cookie.match(new RegExp('(^| )' + name + '=([^;]+)'));
  return match ? match[2] : null;
}

// Initial setup
document.addEventListener('DOMContentLoaded', () => {
  loadPosts();
  loadJournal();
  // Add default document rows
  addDocumentRow("Invoys", "", "", "Asosiy invoys");
  addDocumentRow("Majburiyatnoma", "", "", "Yetkazib berish majburiyati");
  addDocumentRow("Sug'urta polisi", "", "", "OSAGO sug'urta");
});

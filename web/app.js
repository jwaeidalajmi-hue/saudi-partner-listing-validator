/* Listing Photo Validator: demo page. Plain JS, no build step. */
const T = {
  ar: {
    title: 'فحص صور العرض', crumb1: 'الملف التعريفي', crumb2: 'فحص الصور مقابل الوصف',
    intro: 'اكتب وصف العرض وأضف صوره. يقارن الفحص كل صورة بما يذكره الوصف، ويتحقق من الدقة والوضوح وشروط الصور لكل فئة.',
    listing: 'العرض', ptype: 'فئة مزوّد الخدمة', activities: 'الأنشطة', accommodation: 'الإقامة', fnb: 'الأطعمة والمشروبات', shopping: 'التسوق',
    sample: 'مثال جاهز', sampleNone: 'بدون مثال', desc: 'الوصف', descHint: 'بالعربية أو الإنجليزية. اذكر ما سيراه الزائر: المرافق والغرف والأطباق والمنتجات.',
    photos: 'الصور', photosHint: 'JPEG أو PNG أو WebP. الصورة الأولى هي صورة الغلاف. يمكنك جعل أي صورة الأولى.',
    check: 'فحص العرض', checking: 'جارٍ الفحص', addPhoto: 'إضافة صور', remove: 'حذف', makeFirst: 'اجعلها الأولى',
    needPhotos: 'أضف صورة واحدة على الأقل.', failed: 'تعذّر الفحص', ready: 'جاهز للمراجعة', needs_changes: 'يحتاج إلى تعديل',
    technical: 'الجودة الفنية', coverage: 'مطابقة الوصف', relevance: 'صلة الصور بالعرض', completeness: 'الصور المطلوبة',
    claimsTitle: 'ما يذكره الوصف', setTitle: 'الصور المطلوبة لهذه الفئة', fixTitle: 'يجب إصلاحه قبل المراجعة', tipTitle: 'اقتراحات',
    eachPhoto: 'كل صورة', json: 'تنزيل التقرير (JSON)', core: 'أساسي', extra: 'إضافي', shownIn: 'في الصورة', notShown: 'لا توجد صورة',
    minPhotos: '{min} صور على الأقل ({have} حاليًا)', cover: 'الصورة الأولى تُظهر {s}', none: 'لا شيء', noClaims: 'لم يُذكر في الوصف شيء يمكن تصويره.',
    shows: 'تُظهر', sharp: 'الوضوح', mock: 'وضع تجريبي بلا ذكاء اصطناعي: تُستنتج محتويات الصور من أسماء الملفات فقط. أضف مفتاح API للفحص الحقيقي.',
    tiers: { below_hd: 'أقل من HD', hd: 'HD', full_hd: 'Full HD', '4k': '4K' }, other: 'محتوى آخر', photo: 'صورة', meta: 'المحرّك: {e} · المعيار: {v} · {ms} ث'
  },
  en: {
    title: 'Listing Photo Check', crumb1: 'My Profile', crumb2: 'Photos vs description',
    intro: 'Write the listing description and add its photos. The check compares every photo with what the description says, and checks resolution, sharpness and the photo standard for the provider type.',
    listing: 'Listing', ptype: 'Provider type', activities: 'Activities', accommodation: 'Accommodation', fnb: 'Food & Beverages', shopping: 'Shopping',
    sample: 'Sample listing', sampleNone: 'No sample', desc: 'Description', descHint: 'Arabic or English. Name what guests will see: facilities, rooms, dishes, products.',
    photos: 'Photos', photosHint: 'JPEG, PNG or WebP. The first photo is the cover; you can make any photo first.',
    check: 'Check listing', checking: 'Checking', addPhoto: 'Add photos', remove: 'Remove', makeFirst: 'Make first',
    needPhotos: 'Add at least one photo.', failed: 'The check failed', ready: 'Ready for review', needs_changes: 'Needs changes',
    technical: 'Technical quality', coverage: 'Matches the description', relevance: 'Photos are relevant', completeness: 'Required photos',
    claimsTitle: 'What the description claims', setTitle: 'Required photos for this type', fixTitle: 'Fix before review', tipTitle: 'Suggestions',
    eachPhoto: 'Each photo', json: 'Download report (JSON)', core: 'core', extra: 'extra', shownIn: 'in photo', notShown: 'no photo',
    minPhotos: 'At least {min} photos ({have} now)', cover: 'The first photo shows {s}', none: 'Nothing', noClaims: 'The description names nothing a photo can show.',
    shows: 'Shows', sharp: 'Sharpness', mock: 'Mock mode, no AI: photo contents are guessed from file names only. Add an API key for the real check.',
    tiers: { below_hd: 'Below HD', hd: 'HD', full_hd: 'Full HD', '4k': '4K' }, other: 'other content', photo: 'Photo', meta: 'Engine: {e} · Standard: {v} · {ms} s'
  }
};
const NAV = [
  ['تقويم الحجوزات', 'My Calendar', '<rect x="4" y="5" width="16" height="15" rx="2"/><path d="M4 9h16"/>'],
  ['لوحة التحكم', 'My Dashboard', '<path d="M4 19h16M6 15l4-4 3 3 5-6"/>'],
  ['الأنشطة التجارية', 'My Business', '<path d="M4 11l8-6 8 6v8H4z"/><path d="M10 19v-5h4v5"/>'],
  ['قنوات التوزيع', 'My Channels', '<circle cx="6" cy="12" r="2.2"/><circle cx="18" cy="6" r="2.2"/><circle cx="18" cy="18" r="2.2"/><path d="M8 11l8-4M8 13l8 4"/>'],
  ['الملف التعريفي', 'My Profile', '<circle cx="12" cy="9" r="3.5"/><path d="M5 20c1.5-3.5 4-5 7-5s5.5 1.5 7 5"/>', true],
  ['حسابي', 'My Account', '<rect x="4" y="7" width="16" height="12" rx="2"/><path d="M9 7V5h6v2M4 12h16"/>'],
  ['المستخدمون', 'My Users', '<circle cx="9" cy="9" r="3"/><circle cx="16.5" cy="10" r="2.5"/><path d="M3.5 19c1-3 3-4.5 5.5-4.5S13.5 16 14.5 19M14 15c2.5-.5 5 .5 6.5 4"/>'],
  ['دليل المستخدم', 'User Guide', '<circle cx="12" cy="12" r="9"/><path d="M9.5 9.5a2.5 2.5 0 1 1 3.5 2.3c-.7.3-1 .8-1 1.5M12 16.5v.5"/>']
];

let L = 'ar', STD = null, SAMPLES = [], photos = [], lastReport = null;
const $ = s => document.querySelector(s);
const t = (k, v = {}) => String(T[L][k] ?? k).replace(/\{(\w+)\}/g, (_, x) => v[x] ?? '');
const el = (tag, a = {}, ...kids) => { const e = document.createElement(tag); for (const [k, v] of Object.entries(a)) { if (k === 'class') e.className = v; else if (k === 'text') e.textContent = v; else if (k === 'html') e.innerHTML = v; else e.setAttribute(k, v); } for (const c of kids) if (c != null && c !== '') e.append(c); return e; };
const sceneLabel = (type, key) => STD?.provider_types?.[type]?.scenes?.[key]?.[L] || t('other');

function renderStatic() {
  const tx = $('#tx'); tx.dir = L === 'ar' ? 'rtl' : 'ltr'; tx.lang = L; document.documentElement.lang = L;
  $('#langLbl').textContent = L === 'ar' ? 'AR-SA' : 'EN-GB';
  document.querySelectorAll('[data-t]').forEach(n => { n.textContent = t(n.dataset.t); });
  const nav = $('#nav'); nav.replaceChildren();
  for (const [ar, en, ico, on] of NAV) nav.append(el('li', {}, el('a', { href: '#', class: on ? 'on' : '', html: `<svg viewBox="0 0 24 24" aria-hidden="true">${ico}</svg><span>${L === 'ar' ? ar : en}</span>` })));
  const s = $('#sample'); const keep = s.value; s.replaceChildren(el('option', { value: '', text: t('sampleNone') }));
  SAMPLES.forEach((x, i) => s.append(el('option', { value: String(i), text: x.name[L] })));
  s.value = keep;
  renderGrid(); if (lastReport) renderReport(lastReport);
  if (!$('#engine').hidden) $('#engine').textContent = t('mock');
}

/* photos */
function renderGrid() {
  const g = $('#grid'); g.replaceChildren();
  photos.forEach((p, i) => {
    const ph = el('div', { class: 'ph' }, el('img', { src: p.url, alt: `${t('photo')} ${i + 1}` }), el('span', { class: 'n', text: String(i + 1) }));
    const x = el('button', { class: 'x', type: 'button', 'aria-label': `${t('remove')} ${i + 1}`, text: '×' });
    x.onclick = () => { URL.revokeObjectURL(p.url); photos.splice(i, 1); renderGrid(); };
    ph.append(x);
    const acts = el('div', { class: 'acts' });
    if (i > 0) { const mf = el('button', { class: 'lnk', type: 'button', text: t('makeFirst') }); mf.onclick = () => { photos.unshift(photos.splice(i, 1)[0]); renderGrid(); }; acts.append(mf); }
    g.append(el('div', { class: 'tile' }, ph, el('div', { class: 't', text: p.file.name }), acts));
  });
  const add = el('button', { class: 'add', type: 'button', 'aria-label': t('addPhoto'), text: '+' });
  add.onclick = () => $('#file').click();
  add.ondragover = e => { e.preventDefault(); add.classList.add('over'); };
  add.ondragleave = () => add.classList.remove('over');
  add.ondrop = e => { e.preventDefault(); add.classList.remove('over'); addFiles([...e.dataTransfer.files]); };
  g.append(el('div', { class: 'tile' }, add));
}
function addFiles(files) {
  for (const f of files) if (/^image\/(jpeg|png|webp)$/.test(f.type)) photos.push({ file: f, url: URL.createObjectURL(f) });
  renderGrid();
}
$('#file').onchange = () => { const fs = [...$('#file').files]; $('#file').value = ''; addFiles(fs); };

/* samples */
$('#sample').onchange = () => {
  const s = SAMPLES[Number($('#sample').value)]; if (!s) return;
  $('#ptype').value = s.provider_type; $('#desc').value = s.description[L] || s.description.en;
};

/* submit */
$('#form').onsubmit = async e => {
  e.preventDefault();
  const st = $('#status');
  if (!photos.length) { st.textContent = t('needPhotos'); return; }
  const fd = new FormData();
  fd.append('provider_type', $('#ptype').value);
  fd.append('description', $('#desc').value);
  photos.forEach(p => fd.append('photos', p.file, p.file.name));
  $('#checkBtn').disabled = true; st.className = 'status pulse'; st.textContent = t('checking');
  try {
    const r = await fetch('/api/validate', { method: 'POST', body: fd });
    const body = await r.json();
    if (!r.ok) throw new Error(body.detail ? (typeof body.detail === 'string' ? body.detail : JSON.stringify(body.detail)) : r.statusText);
    lastReport = body; renderReport(body); st.className = 'status'; st.textContent = '';
    $('#report').scrollIntoView({ behavior: 'smooth', block: 'start' });
  } catch (err) { st.className = 'status'; st.textContent = `${t('failed')}: ${err.message}`; }
  finally { $('#checkBtn').disabled = false; }
};

/* report */
function renderReport(r) {
  $('#report').hidden = false;
  const ring = $('#ring'); ring.style.setProperty('--v', r.score); ring.style.setProperty('--c', r.verdict === 'ready' ? 'var(--ok)' : r.score >= 60 ? 'var(--warn)' : 'var(--bad)');
  $('#score').textContent = r.score;
  const vp = $('#vpill'); vp.className = 'vpill ' + r.verdict; vp.textContent = t(r.verdict);
  $('#summary').textContent = L === 'ar' ? r.summary_ar : r.summary_en;
  const bars = $('#bars'); bars.replaceChildren();
  for (const [k, max] of [['technical', 30], ['coverage', 35], ['relevance', 20], ['completeness', 15]]) {
    const v = r.breakdown[k]; const b = el('div', { class: 'bar' }, el('i'));
    b.firstChild.style.width = (100 * v / max) + '%';
    bars.append(el('span', { text: t(k) }), b, el('span', { class: 'num', text: `${Math.round(v)}/${max}` }));
  }
  const cl = $('#claims'); cl.replaceChildren();
  if (!r.claims.length) cl.append(el('li', { class: 'soft' }, el('span', { class: 'ic', text: '!' }), el('span', { text: t('noClaims') })));
  for (const c of r.claims) {
    const label = L === 'ar' ? c.claim.label_ar : c.claim.label_en;
    const state = c.shown ? 'yes' : (c.claim.core ? 'no' : 'soft');
    cl.append(el('li', { class: state }, el('span', { class: 'ic', text: c.shown ? '✓' : (c.claim.core ? '✕' : '–') }),
      el('span', {}, el('span', { text: label + ' ' }), el('span', { class: 'tag' + (c.claim.core ? ' core' : ''), text: c.claim.core ? t('core') : t('extra') }),
        el('span', { class: 'num', text: ' · ' + (c.shown ? `${t('shownIn')} ${c.photos.join(', ')}` : t('notShown')) }))));
  }
  const set = $('#set'); set.replaceChildren();
  for (const s of r.required) set.append(el('li', { class: s.present ? 'yes' : 'no' }, el('span', { class: 'ic', text: s.present ? '✓' : '✕' }), el('span', { text: (L === 'ar' ? s.label_ar : s.label_en) + (s.present ? ` · ${t('shownIn')} ${s.photos.join(', ')}` : '') })));
  set.append(el('li', { class: r.photo_count >= r.min_photos ? 'yes' : 'no' }, el('span', { class: 'ic', text: r.photo_count >= r.min_photos ? '✓' : '✕' }), el('span', { text: t('minPhotos', { min: r.min_photos, have: r.photo_count }) })));
  const coverKey = STD?.provider_types?.[r.provider_type]?.cover?.[0];
  set.append(el('li', { class: r.cover_ok ? 'yes' : 'soft' }, el('span', { class: 'ic', text: r.cover_ok ? '✓' : '–' }), el('span', { text: t('cover', { s: sceneLabel(r.provider_type, coverKey) }) })));
  const fix = $('#fix'), tips = $('#tips'); fix.replaceChildren(); tips.replaceChildren();
  for (const i of r.issues) (i.severity === 'block' ? fix : tips).append(el('li', { class: i.severity, text: L === 'ar' ? i.message_ar : i.message_en }));
  if (!fix.childElementCount) fix.append(el('li', { class: 'info', text: t('none') }));
  if (!tips.childElementCount) tips.append(el('li', { class: 'info', text: t('none') }));
  const pc = $('#pcards'); pc.replaceChildren();
  r.photos.forEach((p, idx) => {
    const src = photos[idx]?.url || '';
    const a = p.analysis, tch = p.technical;
    const chips = el('div', { class: 'chips' });
    for (const i of p.issues) chips.append(el('span', { class: 'chip ' + i.severity, text: shortCode(i.code) }));
    if (!p.issues.length) chips.append(el('span', { class: 'chip ok', text: '✓' }));
    const supports = r.claims.filter(c => c.photos.includes(p.index)).map(c => L === 'ar' ? c.claim.label_ar : c.claim.label_en);
    pc.append(el('div', { class: 'pc' },
      el('div', { class: 'ph' }, el('img', { src, alt: `${t('photo')} ${p.index}` }), el('span', { class: 'n', text: String(p.index) })),
      el('div', { class: 'body' },
        el('h3', { text: sceneLabel(r.provider_type, a.scene) }),
        el('div', { class: 'chips' }, el('span', { class: 'tier ' + (tch.tier === '4k' ? 'k4' : tch.tier), text: T[L].tiers[tch.tier] }), el('span', { class: 'num', text: `${tch.width}×${tch.height} · ${(tch.bytes / 1048576).toFixed(1)} MB · ${t('sharp')} ${Math.round(tch.sharpness)}` })),
        el('div', { text: (L === 'ar' ? a.caption_ar : a.caption_en) || '' }),
        supports.length ? el('div', { class: 'num', text: `${t('shows')}: ${supports.join('، ')}` }) : '',
        chips)));
  });
  $('#meta').textContent = t('meta', { e: r.engine, v: r.standard_version, ms: (r.duration_ms / 1000).toFixed(1) });
  const eng = $('#engine'); eng.hidden = r.engine !== 'mock'; eng.textContent = t('mock');
}
const CODES = {
  ar: { below_hd: 'أقل من HD', hd_not_full_hd: 'ليست Full HD', too_large: 'أكبر من 3MB', portrait: 'طولية', square: 'مربعة', blurry: 'غير واضحة', slightly_soft: 'وضوح أقل', too_dark: 'معتمة', too_bright: 'إضاءة زائدة', black_and_white: 'أبيض وأسود', exact_duplicate: 'مكررة', near_duplicate: 'شبه مكررة', overlay: 'إضافات على الصورة', collage: 'مجمّعة', screenshot: 'لقطة شاشة', stock_or_ai: 'جاهزة أو مولّدة', unrelated: 'لا تخص العرض', contradicts: 'تخالف الوصف', people_consent: 'أشخاص', children: 'أطفال', licence_plate: 'لوحة سيارة', low_quality: 'جودة منخفضة', not_checked: 'لم تُفحص' },
  en: { below_hd: 'below HD', hd_not_full_hd: 'not Full HD', too_large: 'over 3 MB', portrait: 'portrait', square: 'square', blurry: 'blurry', slightly_soft: 'slightly soft', too_dark: 'too dark', too_bright: 'over-exposed', black_and_white: 'black & white', exact_duplicate: 'duplicate', near_duplicate: 'near-duplicate', overlay: 'overlay', collage: 'collage', screenshot: 'screenshot', stock_or_ai: 'stock / AI', unrelated: 'unrelated', contradicts: 'contradicts description', people_consent: 'people', children: 'children', licence_plate: 'licence plate', low_quality: 'low quality', not_checked: 'not checked' }
};
const shortCode = c => CODES[L][c] || c;
$('#jsonBtn').onclick = () => {
  if (!lastReport) return;
  const a = el('a', { href: URL.createObjectURL(new Blob([JSON.stringify(lastReport, null, 2)], { type: 'application/json' })), download: 'listing-photo-report.json' });
  document.body.append(a); a.click(); a.remove();
};
$('#langBtn').onclick = () => { L = L === 'ar' ? 'en' : 'ar'; renderStatic(); };

(async () => {
  try { STD = await (await fetch('/api/standards')).json(); } catch {}
  try { SAMPLES = await (await fetch('/web/samples.json')).json(); } catch {}
  try { const h = await (await fetch('/api/health')).json(); if (h.engine === 'mock') { $('#engine').hidden = false; $('#engine').textContent = t('mock'); } } catch {}
  renderStatic();
})();

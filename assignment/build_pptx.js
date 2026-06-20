const pptxgen = require("pptxgenjs");
const p = new pptxgen();
p.defineLayout({ name: "W", width: 13.333, height: 7.5 });
p.layout = "W";

// ── Brand tokens ──────────────────────────────────────────────
const C = {
  paper: "FAF7F2", surface: "FFFEFB", ink: "241F18", soft: "6B6155", faint: "9A8F80",
  line: "E7DFD3", amber: "B5701A", amberInk: "9A5E12", wash: "FBF1E2",
  asphalt: "241F18", danger: "B23A2E", ok: "3F7A52", violet: "6E5AA8",
  cream: "FBF7F0", creamSoft: "C9BEB0", amberLite: "D9A24E",
};
const F = "Plus Jakarta Sans";
const MARGIN = 0.62;

function eyebrow(s, txt, color = C.amberInk) {
  s.addText(txt.toUpperCase(), { x: MARGIN, y: 0.5, w: 12, h: 0.4, fontFace: F,
    fontSize: 12, bold: true, color, charSpacing: 3 });
}
function title(s, txt, opt = {}) {
  s.addText(txt, { x: MARGIN, y: 0.95, w: 12.1, h: 0.95, fontFace: F, fontSize: 32,
    bold: true, color: C.ink, ...opt });
}
function quote(s, parts) {
  // parts: array of {text, amber?:bool}
  const runs = parts.map(pt => ({ text: pt.text, options: { color: pt.amber ? C.amberInk : C.ink, bold: true } }));
  s.addText(runs, { x: MARGIN, y: 6.55, w: 12.1, h: 0.6, fontFace: F, fontSize: 19 });
}
function foot(s, n) {
  s.addText("JalanKita", { x: MARGIN, y: 7.0, w: 4, h: 0.3, fontFace: F, fontSize: 11, bold: true, color: C.faint });
  s.addText(n, { x: 11.7, y: 7.0, w: 1, h: 0.3, fontFace: F, fontSize: 11, bold: true, color: C.faint, align: "right" });
}
function roadDashes(s, color = C.amber) {
  for (let i = 0; i < 19; i++) {
    s.addShape(p.ShapeType.rect, { x: MARGIN + i * 0.68, y: 7.34, w: 0.4, h: 0.1, fill: { color } });
  }
}
function iconCircle(s, x, y, emoji, fill) {
  s.addShape(p.ShapeType.ellipse, { x, y, w: 0.66, h: 0.66, fill: { color: fill } });
  s.addText(emoji, { x, y, w: 0.66, h: 0.66, align: "center", valign: "middle", fontSize: 20 });
}

// ── Slide 1: TITLE ────────────────────────────────────────────
let s = p.addSlide(); s.background = { color: C.asphalt };
eyebrow(s, "Pitch Startup · UAS Inovasi & Entrepreneur AI", C.amberLite);
s.addText("🛣️", { x: MARGIN, y: 1.55, w: 1, h: 1, fontSize: 48 });
s.addText("JalanKita", { x: 1.55, y: 1.45, w: 11, h: 1.2, fontFace: F, fontSize: 60, bold: true, color: C.cream });
s.addText("Dari foto, menjadi perbaikan.", { x: MARGIN, y: 2.95, w: 12, h: 0.6, fontFace: F, fontSize: 26, bold: true, color: C.amberLite });
s.addText("Platform pelaporan infrastruktur jalan berbasis AI — mendeteksi kerusakan dan menghitung anggaran perbaikan secara otomatis, transparan, dan partisipatif.",
  { x: MARGIN, y: 3.75, w: 10.8, h: 1, fontFace: F, fontSize: 18, color: C.creamSoft, lineSpacingMultiple: 1.3 });
s.addText("[Nama Anda] · Master Kecerdasan Artifisial, FMIPA UGM · 2026",
  { x: MARGIN, y: 6.45, w: 11, h: 0.4, fontFace: F, fontSize: 14, bold: true, color: "B7AB9C" });
roadDashes(s);

// ── Slide 2: MASALAH ──────────────────────────────────────────
s = p.addSlide(); s.background = { color: C.paper };
eyebrow(s, "01 — Masalah");
title(s, "Jalan rusak mahal. Birokrasinya lebih mahal.");
const probs = [
  ["🚧", "Bahaya & rugi", "Ribuan kecelakaan dan kerusakan kendaraan tiap tahun akibat jalan rusak."],
  ["📥", "Laporan menumpuk", "Pengaduan masuk tanpa klasifikasi, tenggelam, dan sering tak ditindaklanjuti."],
  ["🕳️", "Anggaran gelap", "Estimasi biaya perbaikan tidak transparan dan rawan markup."],
];
probs.forEach(([ic, t, d], i) => {
  const x = MARGIN + i * 4.07;
  s.addShape(p.ShapeType.roundRect, { x, y: 2.2, w: 3.8, h: 2.9, rectRadius: 0.14, fill: { color: C.surface }, line: { color: C.line, width: 1 }, shadow: { type: "outer", color: "241F18", opacity: 0.12, blur: 12, offset: 4, angle: 90 } });
  iconCircle(s, x + 0.35, y2 = 2.55, ic, "FBEAE7");
  s.addText(t, { x: x + 0.32, y: 3.35, w: 3.2, h: 0.5, fontFace: F, fontSize: 19, bold: true, color: C.ink });
  s.addText(d, { x: x + 0.32, y: 3.85, w: 3.2, h: 1.1, fontFace: F, fontSize: 14.5, color: C.soft, lineSpacingMultiple: 1.3 });
});
quote(s, [{ text: "Masalahnya bukan lubangnya — " }, { text: "tapi apa yang terjadi setelah warga melapor.", amber: true }]);
foot(s, "02");

// ── Slide 3: PELUANG ──────────────────────────────────────────
s = p.addSlide(); s.background = { color: C.paper };
eyebrow(s, "02 — Peluang Pasar");
title(s, "Pasar sebesar jaringan jalan Indonesia.");
const stats = [["540rb+ km", "panjang jalan yang harus dipelihara di Indonesia."],
  ["Rp puluhan T", "anggaran pemeliharaan jalan per tahun (pusat + daerah)."]];
stats.forEach(([n, u], i) => {
  const x = MARGIN + i * 6.1;
  s.addText(n, { x, y: 2.5, w: 5.7, h: 1.3, fontFace: F, fontSize: 60, bold: true, color: C.amberInk });
  s.addText(u, { x, y: 3.9, w: 5.2, h: 1, fontFace: F, fontSize: 17, color: C.soft, lineSpacingMultiple: 1.25 });
});
quote(s, [{ text: "Setiap rupiah yang salah prioritas adalah " }, { text: "jalan yang dibiarkan rusak.", amber: true }]);
foot(s, "03");

// ── Slide 4: SOLUSI / FLOW ────────────────────────────────────
s = p.addSlide(); s.background = { color: C.paper };
eyebrow(s, "03 — Solusi");
title(s, "Warga jadi sensor. AI jadi surveyor.");
const steps = [
  ["📸", "Foto", "Warga memotret jalan rusak — sekali klik.", false],
  ["🤖", "AI Computer Vision", "Deteksi jenis, keparahan & dimensi.", true],
  ["💰", "LLM susun RAB", "Estimasi anggaran otomatis & transparan.", true],
  ["🗺️", "Feed publik", "Skor prioritas + pelacakan SLA.", false],
  ["🏛️", "Ditindaklanjuti", "Dinas PU & mitra CSR.", false],
];
const sw = 2.13, gap = 0.36; let sx = MARGIN;
steps.forEach(([ic, t, d, ai], i) => {
  s.addShape(p.ShapeType.roundRect, { x: sx, y: 2.6, w: sw, h: 2.5, rectRadius: 0.12,
    fill: { color: ai ? C.asphalt : C.surface }, line: { color: ai ? C.asphalt : C.line, width: 1 } });
  s.addText(ic, { x: sx, y: 2.8, w: sw, h: 0.6, align: "center", fontSize: 26 });
  s.addText(t, { x: sx + 0.1, y: 3.45, w: sw - 0.2, h: 0.6, align: "center", fontFace: F, fontSize: 15, bold: true, color: ai ? C.cream : C.ink });
  s.addText(d, { x: sx + 0.12, y: 4.05, w: sw - 0.24, h: 0.95, align: "center", fontFace: F, fontSize: 12, color: ai ? C.creamSoft : C.soft, lineSpacingMultiple: 1.2 });
  if (i < steps.length - 1) s.addText("→", { x: sx + sw - 0.02, y: 2.6, w: gap, h: 2.5, align: "center", valign: "middle", fontSize: 22, bold: true, color: C.amber });
  sx += sw + gap;
});
quote(s, [{ text: "Cukup satu foto. " }, { text: "AI yang menilai dan menghitung.", amber: true }]);
foot(s, "04");

// ── Slide 5: MVP MOCK ─────────────────────────────────────────
s = p.addSlide(); s.background = { color: C.paper };
eyebrow(s, "04 — MVP (sudah berjalan)");
title(s, "Produk nyata, bukan konsep.");
// browser frame
const bx = MARGIN, by = 1.95, bw = 12.1;
s.addShape(p.ShapeType.roundRect, { x: bx, y: by, w: bw, h: 4.4, rectRadius: 0.12, fill: { color: C.surface }, line: { color: C.line, width: 1 }, shadow: { type: "outer", color: "241F18", opacity: 0.18, blur: 16, offset: 5, angle: 90 } });
s.addShape(p.ShapeType.rect, { x: bx, y: by, w: bw, h: 0.5, fill: { color: "EFE8DD" } });
["E0897F", "E6C06A", "86B796"].forEach((c, i) => s.addShape(p.ShapeType.ellipse, { x: bx + 0.25 + i * 0.26, y: by + 0.18, w: 0.15, h: 0.15, fill: { color: c } }));
s.addText("jalankita.app / feed", { x: bx + 1.3, y: by + 0.08, w: 4, h: 0.34, fontFace: F, fontSize: 12, color: C.soft, fill: { color: "FFFFFF" }, align: "left", valign: "middle" });
// report card inside
const cx = bx + 0.45, cy = by + 0.85, cw = bw - 0.9;
s.addShape(p.ShapeType.roundRect, { x: cx, y: cy, w: cw, h: 3.2, rectRadius: 0.1, fill: { color: C.surface }, line: { color: C.line, width: 1 } });
s.addText("RPT-001 · 15 Jun 2026", { x: cx + 0.3, y: cy + 0.2, w: 6, h: 0.3, fontFace: F, fontSize: 11, bold: true, color: C.faint });
s.addText("Jl. Kaliurang KM 12, Sleman, DIY", { x: cx + 0.3, y: cy + 0.46, w: 7, h: 0.4, fontFace: F, fontSize: 18, bold: true, color: C.ink });
s.addShape(p.ShapeType.ellipse, { x: cx + 0.3, y: cy + 0.95, w: 0.3, h: 0.3, fill: { color: C.amber } });
s.addText("B", { x: cx + 0.3, y: cy + 0.95, w: 0.3, h: 0.3, align: "center", valign: "middle", fontFace: F, fontSize: 12, bold: true, color: "FFFFFF" });
s.addText("Budi Santoso", { x: cx + 0.68, y: cy + 0.96, w: 3, h: 0.3, fontFace: F, fontSize: 13, bold: true, color: C.soft, valign: "middle" });
// badges right
s.addShape(p.ShapeType.roundRect, { x: cx + cw - 2.0, y: cy + 0.22, w: 1.7, h: 0.36, rectRadius: 0.18, fill: { color: "FBEAE7" }, line: { color: "E7C3BC", width: 1 } });
s.addText("PRIORITAS PUBLIK", { x: cx + cw - 2.0, y: cy + 0.22, w: 1.7, h: 0.36, align: "center", valign: "middle", fontFace: F, fontSize: 9, bold: true, color: C.danger });
s.addShape(p.ShapeType.roundRect, { x: cx + cw - 1.5, y: cy + 0.66, w: 1.2, h: 0.34, rectRadius: 0.17, fill: { color: "FBEAE7" }, line: { color: "E7C3BC", width: 1 } });
s.addText("🚦 Kritis · 100", { x: cx + cw - 1.5, y: cy + 0.66, w: 1.2, h: 0.34, align: "center", valign: "middle", fontFace: F, fontSize: 9.5, bold: true, color: C.danger });
// detection grid
const dgY = cy + 1.45, dw = (cw - 0.6) / 4;
[["TIPE", "Lubang", C.ink], ["TINGKAT", "Berat", C.danger], ["DIMENSI", "1.2×0.8×0.15 m", C.ink], ["CONFIDENCE", "92%", C.ink]].forEach(([l, v, col], i) => {
  s.addText(l, { x: cx + 0.3 + i * dw, y: dgY, w: dw, h: 0.25, fontFace: F, fontSize: 9, bold: true, color: C.faint, charSpacing: 1 });
  s.addText(v, { x: cx + 0.3 + i * dw, y: dgY + 0.24, w: dw, h: 0.3, fontFace: F, fontSize: 13, bold: true, color: col });
});
// RAB bar
s.addShape(p.ShapeType.roundRect, { x: cx + 0.3, y: cy + 2.2, w: cw - 0.6, h: 0.5, rectRadius: 0.08, fill: { color: "F6F0E7" }, line: { color: "DBCFBE", width: 1 } });
s.addText("Estimasi Anggaran Perbaikan (AI)", { x: cx + 0.5, y: cy + 2.2, w: 6, h: 0.5, valign: "middle", fontFace: F, fontSize: 13, color: C.soft });
s.addText("Rp 2.200.000", { x: cx + cw - 2.5, y: cy + 2.2, w: 2.2, h: 0.5, valign: "middle", align: "right", fontFace: F, fontSize: 17, bold: true, color: C.ink });
s.addText([{ text: "❤️ 134 dukungan      ", options: {} }, { text: "💬 8 komentar      ", options: {} }, { text: "📋 3 update", options: {} }],
  { x: cx + 0.3, y: cy + 2.78, w: cw - 0.6, h: 0.32, fontFace: F, fontSize: 12, bold: true, color: C.soft });
s.addText([{ text: "Live web app: ", options: { color: C.ink, bold: true } }, { text: "deteksi AI · estimasi RAB · feed sosial · dashboard analitik.", options: { color: C.amberInk, bold: true } }],
  { x: MARGIN, y: 6.55, w: 12.1, h: 0.4, fontFace: F, fontSize: 16 });
foot(s, "05");

// ── Slide 6: DIFERENSIASI (table) ─────────────────────────────
s = p.addSlide(); s.background = { color: C.paper };
eyebrow(s, "05 — Diferensiasi");
title(s, "Yang lain berhenti di kotak masuk.");
const hdr = ["Aplikasi", "Lapor foto + lokasi", "Penilaian AI otomatis", "Estimasi biaya transparan", "Lapisan sosial & prioritas"];
const rows = [
  ["JAKI / Qlue (Jakarta)", "✓y", "✕n", "✕n", "±p"],
  ["SP4N-LAPOR! (nasional)", "✓y", "✕n", "✕n", "✕n"],
  ["Jalan Cantik (Jateng)", "✓y", "✕n", "✕n", "✕n"],
  ["Jalan Kita / Bina Marga PUPR", "✓y", "✕n", "✕n", "✕n"],
  ["🛣️ JalanKita (AI)", "✓y", "✓y", "✓y", "✓y"],
];
const tRows = [];
tRows.push(hdr.map((h, i) => ({ text: h, options: { fontFace: F, fontSize: 12, bold: true, color: C.faint, align: i === 0 ? "left" : "center", valign: "middle", fill: { color: C.paper } } })));
rows.forEach((r, ri) => {
  const isUs = ri === rows.length - 1;
  const cells = r.map((c, ci) => {
    if (ci === 0) return { text: c, options: { fontFace: F, fontSize: 13.5, bold: true, color: C.ink, align: "left", valign: "middle", fill: { color: isUs ? C.wash : C.surface } } };
    const mark = c[0], kind = c[1];
    const col = kind === "y" ? C.ok : kind === "n" ? C.danger : C.amberInk;
    return { text: mark, options: { fontFace: F, fontSize: 16, bold: true, color: col, align: "center", valign: "middle", fill: { color: isUs ? C.wash : C.surface } } };
  });
  tRows.push(cells);
});
s.addTable(tRows, { x: MARGIN, y: 2.15, w: 12.1, colW: [3.7, 2.1, 2.1, 2.1, 2.1], rowH: 0.62, border: { type: "solid", color: C.line, pt: 1 }, autoPage: false });
quote(s, [{ text: "Kami otomasi " }, { text: "penilaian teknis + anggaran", amber: true }, { text: " — mengubah pengaduan jadi keputusan siap eksekusi." }]);
foot(s, "06");

// ── Slide 7: PELANGGAN & MODEL ────────────────────────────────
s = p.addSlide(); s.background = { color: C.paper };
eyebrow(s, "06 — Pelanggan & Model Bisnis");
title(s, "Tiga pihak, satu platform.");
const pers = [
  ["🧑‍🤝‍🧑", "Warga", "Sensor di lapangan. Melapor, mendukung, mengawasi — gratis.", C.amber],
  ["🏛️", "Dinas PU / Pemda", "Pelaksana. Berlangganan dashboard analitik & prioritas.", C.amber],
  ["🤝", "Mitra CSR", "Pendana. Fee penyaluran dana perbaikan ke titik prioritas.", C.amber],
];
pers.forEach(([ic, t, d, ac], i) => {
  const x = MARGIN + i * 4.07;
  s.addShape(p.ShapeType.roundRect, { x, y: 2.15, w: 3.8, h: 2.55, rectRadius: 0.14, fill: { color: C.surface }, line: { color: C.line, width: 1 }, shadow: { type: "outer", color: "241F18", opacity: 0.1, blur: 12, offset: 4, angle: 90 } });
  iconCircle(s, x + 0.35, 2.5, ic, C.wash);
  s.addText(t, { x: x + 0.32, y: 3.3, w: 3.2, h: 0.45, fontFace: F, fontSize: 18, bold: true, color: C.ink });
  s.addText(d, { x: x + 0.32, y: 3.78, w: 3.25, h: 0.9, fontFace: F, fontSize: 14, color: C.soft, lineSpacingMultiple: 1.25 });
});
const chips = ["💼  Lisensi B2G dashboard", "🤝  Fee CSR penyaluran dana", "📊  Layanan data anggaran"];
let chx = MARGIN;
chips.forEach((c) => {
  const w = 0.35 + c.length * 0.115;
  s.addShape(p.ShapeType.roundRect, { x: chx, y: 5.05, w, h: 0.55, rectRadius: 0.27, fill: { color: C.asphalt } });
  s.addText(c, { x: chx, y: 5.05, w, h: 0.55, align: "center", valign: "middle", fontFace: F, fontSize: 14, bold: true, color: C.cream });
  chx += w + 0.3;
});
quote(s, [{ text: "Mereka bayar karena kami " }, { text: "mempercepat penanganan, menekan markup, dan memberi transparansi.", amber: true }]);
foot(s, "07");

// ── Slide 8: TRAKSI & ROADMAP ─────────────────────────────────
s = p.addSlide(); s.background = { color: C.paper };
eyebrow(s, "07 — Traksi & Langkah Berikutnya");
title(s, "Sudah jalan. Siap di-scale.");
const panels = [
  ["Saat ini — MVP live", C.ok, ["Deteksi AI (computer vision) + estimasi RAB otomatis", "Feed komunitas sosial: dukungan, komentar, follow", "Dashboard analitik + skor prioritas + SLA", "Sistem akun & peran (warga / admin Dinas PU)", "Validasi awal: [X] pengguna diuji (lihat Portofolio B)"]],
  ["Berikutnya — 6–12 bulan", C.amber, ["Pilot bersama satu Dinas PU / pemda", "Model CV di-fine-tune khusus jalan Indonesia", "Versi mobile / PWA untuk warga lapangan", "Integrasi dengan sistem anggaran pemerintah", "Penajaman posisi sebagai lapisan AI untuk kanal yang ada"]],
];
panels.forEach(([h, ac, items], i) => {
  const x = MARGIN + i * 6.2;
  s.addShape(p.ShapeType.roundRect, { x, y: 2.15, w: 5.9, h: 4.1, rectRadius: 0.14, fill: { color: C.surface }, line: { color: C.line, width: 1 } });
  s.addShape(p.ShapeType.ellipse, { x: x + 0.4, y: 2.5, w: 0.28, h: 0.28, fill: { color: ac } });
  s.addText(h.toUpperCase(), { x: x + 0.8, y: 2.45, w: 5, h: 0.4, fontFace: F, fontSize: 14, bold: true, color: C.faint, charSpacing: 1, valign: "middle" });
  const body = items.map(t => ({ text: t, options: { bullet: { code: "203A", indent: 18 }, color: C.ink, fontSize: 15, paraSpaceAfter: 9 } }));
  s.addText(body, { x: x + 0.4, y: 3.05, w: 5.2, h: 3, fontFace: F, lineSpacingMultiple: 1.15 });
});
foot(s, "08");

// ── Slide 9: CLOSING ──────────────────────────────────────────
s = p.addSlide(); s.background = { color: C.asphalt };
eyebrow(s, "Ajak Bergabung", C.amberLite);
s.addText("Mari benahi jalan Indonesia, bersama.", { x: MARGIN, y: 1.4, w: 9.5, h: 2, fontFace: F, fontSize: 50, bold: true, color: C.cream, lineSpacingMultiple: 1.05 });
s.addText("Kami mencari mitra untuk mendanai pilot pertama.", { x: MARGIN, y: 3.7, w: 10, h: 0.6, fontFace: F, fontSize: 22, bold: true, color: C.amberLite });
// QR placeholder
s.addShape(p.ShapeType.roundRect, { x: MARGIN, y: 4.6, w: 1.5, h: 1.5, rectRadius: 0.1, fill: { color: C.cream } });
s.addText("[ QR ke\ndemo / repo ]", { x: MARGIN, y: 4.6, w: 1.5, h: 1.5, align: "center", valign: "middle", fontFace: F, fontSize: 11, bold: true, color: C.ink });
s.addText([
  { text: "🔗 Demo: ", options: { color: C.creamSoft } }, { text: "[tautan demo Anda]\n\n", options: { color: C.cream, bold: true } },
  { text: "💻 GitHub: ", options: { color: C.creamSoft } }, { text: "[tautan repo]\n\n", options: { color: C.cream, bold: true } },
  { text: "✉️ ", options: { color: C.creamSoft } }, { text: "[email Anda]", options: { color: C.cream, bold: true } },
], { x: 2.4, y: 4.65, w: 7, h: 1.5, fontFace: F, fontSize: 16, lineSpacingMultiple: 1.1 });
s.addText("🛣️ JalanKita — Dari foto, menjadi perbaikan.", { x: MARGIN, y: 6.55, w: 11, h: 0.4, fontFace: F, fontSize: 14, bold: true, color: "B7AB9C" });
roadDashes(s);

p.writeFile({ fileName: "JalanKita_Pitch_Deck.pptx" }).then(f => console.log("WROTE", f));

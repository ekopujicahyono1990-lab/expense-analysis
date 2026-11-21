import csv
from collections import defaultdict
from datetime import datetime

# ─── Helpers ────────────────────────────────────────────────────────────────

def fmt_rp(amount):
    """Format integer to Rupiah string with dot-thousands separator."""
    return "Rp " + "{:,.0f}".format(amount).replace(",", ".")


def categorize(deskripsi):
    d = deskripsi.lower()
    # Makanan & Minuman
    if any(k in d for k in [
        "makan", "kopi", "sarapan", "warteg", "makanan", "ayam", "camilan",
        "buah", "air galon", "gas", "beli buah", "beli air"
    ]):
        return "Makanan & Minuman"
    # Tagihan & Utilitas
    if any(k in d for k in [
        "tagihan", "internet", "listrik", "pln", "pdam", "air", "token",
        "paket data", "pulsa", "iuran", "cloud storage"
    ]):
        return "Tagihan & Utilitas"
    # Transportasi
    if any(k in d for k in [
        "bensin", "ojek", "transportasi", "parkir", "tol", "cuci kendaraan",
        "servis", "ganti ban"
    ]):
        return "Transportasi"
    # Hiburan & Langganan
    if any(k in d for k in [
        "spotify", "youtube", "bioskop", "nonton", "langganan", "streaming",
        "game", "hiburan"
    ]):
        return "Hiburan & Langganan"
    # Belanja (default untuk sisanya)
    if any(k in d for k in [
        "belanja", "minimarket", "supermarket", "beli", "dapur", "perlengkapan",
        "buku", "alat tulis", "monitor", "sepatu", "flash sale", "promo"
    ]):
        return "Belanja"
    return "Lain-lain"


# ─── Load CSV ────────────────────────────────────────────────────────────────

rows = []
with open("data_pengeluaran.csv", newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        rows.append({
            "tanggal": row["Tanggal"].strip(),
            "deskripsi": row["Deskripsi"].strip(),
            "nominal": int(row["Nominal_IDR"].strip()),
            "metode": row["Metode_Pembayaran"].strip(),
        })

# Tambahkan kategori
for r in rows:
    r["kategori"] = categorize(r["deskripsi"])

# ─── Statistik Umum ─────────────────────────────────────────────────────────

total_transaksi = len(rows)
total_nominal = sum(r["nominal"] for r in rows)
rata_rata = total_nominal / total_transaksi
nominal_max = max(r["nominal"] for r in rows)
nominal_min = min(r["nominal"] for r in rows)

# ─── Breakdown per Kategori ──────────────────────────────────────────────────

kategori_data = defaultdict(lambda: {"jumlah": 0, "total": 0})
for r in rows:
    kategori_data[r["kategori"]]["jumlah"] += 1
    kategori_data[r["kategori"]]["total"] += r["nominal"]

kategori_sorted = sorted(kategori_data.items(), key=lambda x: x[1]["total"], reverse=True)

# ─── Breakdown per Metode Pembayaran ─────────────────────────────────────────

metode_data = defaultdict(lambda: {"jumlah": 0, "total": 0})
for r in rows:
    metode_data[r["metode"]]["jumlah"] += 1
    metode_data[r["metode"]]["total"] += r["nominal"]

metode_sorted = sorted(metode_data.items(), key=lambda x: x[1]["total"], reverse=True)

# ─── Deteksi Anomali ─────────────────────────────────────────────────────────

# 1. Duplikat: transaksi dengan (tanggal, deskripsi, nominal, metode) sama
seen = {}
duplikat = []
for i, r in enumerate(rows):
    key = (r["tanggal"], r["deskripsi"], r["nominal"], r["metode"])
    if key in seen:
        duplikat.append((seen[key] + 2, i + 2, r))  # +2 karena header + 0-index
    else:
        seen[key] = i

# 2. Outlier: IQR method pada nominal
nominals_sorted = sorted(r["nominal"] for r in rows)
n = len(nominals_sorted)
q1 = nominals_sorted[n // 4]
q3 = nominals_sorted[(3 * n) // 4]
iqr = q3 - q1
upper_fence = q3 + 1.5 * iqr
lower_fence = q1 - 1.5 * iqr

outliers = [r for r in rows if r["nominal"] > upper_fence or r["nominal"] < lower_fence]

# ─── Statistik tambahan untuk rekomendasi ────────────────────────────────────

# Total per kategori untuk rekomendasi
kat_total = {k: v["total"] for k, v in kategori_data.items()}

# Hitung frekuensi kopi/sarapan
kopi_rows = [r for r in rows if "kopi" in r["deskripsi"].lower()]
kopi_total = sum(r["nominal"] for r in kopi_rows)
kopi_count = len(kopi_rows)

# Hitung frekuensi makanan online
online_rows = [r for r in rows if "pesan makanan online" in r["deskripsi"].lower()]
online_total = sum(r["nominal"] for r in online_rows)
online_count = len(online_rows)

# Total hiburan & langganan
hiburan_total = kat_total.get("Hiburan & Langganan", 0)

# Total belanja besar (non-rutin) di Belanja
belanja_rows = [r for r in rows if r["kategori"] == "Belanja"]
belanja_besar = [r for r in belanja_rows if r["nominal"] >= 1000000]
belanja_besar_total = sum(r["nominal"] for r in belanja_besar)

# Rata-rata harian
tanggal_unik = set(r["tanggal"] for r in rows)
n_hari = len(tanggal_unik)
rata_harian = total_nominal / n_hari

# ─── Build laporan string ────────────────────────────────────────────────────

lines = []

lines.append("# Laporan Analisis Pengeluaran Bulanan")
lines.append("")
lines.append(f"**Periode Data:** Oktober – November 2026  ")
lines.append(f"**Tanggal Laporan:** {datetime.now().strftime('%d %B %Y')}  ")
lines.append(f"**Sumber Data:** `data_pengeluaran.csv`  ")
lines.append("")
lines.append("---")
lines.append("")

# ── Ringkasan Eksekutif ──────────────────────────────────────────────────────
lines.append("## 📊 Ringkasan Eksekutif")
lines.append("")
lines.append(f"| Metrik | Nilai |")
lines.append(f"|--------|-------|")
lines.append(f"| Total Transaksi | {total_transaksi} transaksi |")
lines.append(f"| Total Pengeluaran | {fmt_rp(total_nominal)} |")
lines.append(f"| Rata-rata per Transaksi | {fmt_rp(int(rata_rata))} |")
lines.append(f"| Rata-rata Pengeluaran Harian | {fmt_rp(int(rata_harian))} |")
lines.append(f"| Transaksi Nominal Tertinggi | {fmt_rp(nominal_max)} |")
lines.append(f"| Transaksi Nominal Terendah | {fmt_rp(nominal_min)} |")
lines.append(f"| Jumlah Hari Aktif Transaksi | {n_hari} hari |")
lines.append("")
lines.append("---")
lines.append("")

# ── Breakdown per Kategori ───────────────────────────────────────────────────
lines.append("## 🗂️ Breakdown Pengeluaran per Kategori")
lines.append("")
lines.append("| No | Kategori | Jumlah Transaksi | Total Nominal | Persentase |")
lines.append("|----|----------|-----------------|---------------|------------|")
for i, (kat, data) in enumerate(kategori_sorted, 1):
    pct = data["total"] / total_nominal * 100
    lines.append(
        f"| {i} | {kat} | {data['jumlah']} transaksi | {fmt_rp(data['total'])} | {pct:.1f}% |"
    )
lines.append("")

# Detail per kategori
lines.append("### Detail Transaksi per Kategori")
lines.append("")
for kat, _ in kategori_sorted:
    kat_rows = [r for r in rows if r["kategori"] == kat]
    lines.append(f"#### {kat}")
    lines.append("")
    lines.append("| Tanggal | Deskripsi | Nominal | Metode |")
    lines.append("|---------|-----------|---------|--------|")
    for r in kat_rows:
        lines.append(
            f"| {r['tanggal']} | {r['deskripsi']} | {fmt_rp(r['nominal'])} | {r['metode']} |"
        )
    lines.append("")

lines.append("---")
lines.append("")

# ── Breakdown per Metode Pembayaran ──────────────────────────────────────────
lines.append("## 💳 Breakdown per Metode Pembayaran")
lines.append("")
lines.append("| No | Metode Pembayaran | Jumlah Transaksi | Total Nominal | Persentase |")
lines.append("|----|-------------------|-----------------|---------------|------------|")
for i, (met, data) in enumerate(metode_sorted, 1):
    pct = data["total"] / total_nominal * 100
    lines.append(
        f"| {i} | {met} | {data['jumlah']} transaksi | {fmt_rp(data['total'])} | {pct:.1f}% |"
    )
lines.append("")
lines.append("---")
lines.append("")

# ── Deteksi Anomali ───────────────────────────────────────────────────────────
lines.append("## ⚠️ Temuan Anomali")
lines.append("")

lines.append("### 1. Indikasi Transaksi Duplikat")
lines.append("")
lines.append(
    f"> Duplikat didefinisikan sebagai transaksi dengan kombinasi **Tanggal, Deskripsi, Nominal, dan Metode Pembayaran** yang identik."
)
lines.append("")
if duplikat:
    lines.append("| Baris Pertama | Baris Duplikat | Tanggal | Deskripsi | Nominal | Metode |")
    lines.append("|--------------|---------------|---------|-----------|---------|--------|")
    for baris1, baris2, r in duplikat:
        lines.append(
            f"| Baris {baris1} | Baris {baris2} | {r['tanggal']} | {r['deskripsi']} | {fmt_rp(r['nominal'])} | {r['metode']} |"
        )
    lines.append("")
    lines.append(f"**Total potensi kelebihan bayar dari duplikat: {fmt_rp(sum(r['nominal'] for _, _, r in duplikat))}**")
else:
    lines.append("*Tidak ditemukan transaksi duplikat.*")
lines.append("")

lines.append("### 2. Lonjakan Pengeluaran Tidak Wajar (Outlier)")
lines.append("")
lines.append(
    f"> Metode deteksi: **IQR (Interquartile Range)**  \n"
    f"> Q1 = {fmt_rp(q1)} | Q3 = {fmt_rp(q3)} | IQR = {fmt_rp(iqr)}  \n"
    f"> Batas atas outlier: {fmt_rp(int(upper_fence))}"
)
lines.append("")
if outliers:
    lines.append("| Tanggal | Deskripsi | Nominal | Metode | Kategori |")
    lines.append("|---------|-----------|---------|--------|----------|")
    for r in outliers:
        lines.append(
            f"| {r['tanggal']} | {r['deskripsi']} | {fmt_rp(r['nominal'])} | {r['metode']} | {r['kategori']} |"
        )
    lines.append("")
    outlier_total = sum(r["nominal"] for r in outliers)
    outlier_pct = outlier_total / total_nominal * 100
    lines.append(
        f"**{len(outliers)} transaksi outlier** menyumbang **{fmt_rp(outlier_total)}** "
        f"({outlier_pct:.1f}% dari total pengeluaran)."
    )
else:
    lines.append("*Tidak ditemukan transaksi outlier.*")
lines.append("")
lines.append("---")
lines.append("")

# ── Rekomendasi Penghematan ───────────────────────────────────────────────────
lines.append("## 💡 Rekomendasi Penghematan")
lines.append("")

# Rekomendasi 1: Kopi & Sarapan
lines.append("### Rekomendasi 1 — Kurangi Frekuensi Pembelian Kopi & Camilan di Luar")
lines.append("")
lines.append(
    f"Selama periode ini terdapat **{kopi_count} transaksi** terkait kopi, sarapan, dan camilan "
    f"dengan total **{fmt_rp(kopi_total)}**. "
    f"Rata-rata per transaksi sebesar **{fmt_rp(int(kopi_total / kopi_count) if kopi_count else 0)}**."
)
lines.append("")
lines.append(
    "**Aksi konkret:** Siapkan kopi di rumah atau bawa bekal sarapan setidaknya 3 hari dalam seminggu. "
    f"Potensi penghematan estimasi **30–40%** dari kategori ini, atau sekitar "
    f"**{fmt_rp(int(kopi_total * 0.35))}** per periode."
)
lines.append("")

# Rekomendasi 2: Pesan Makanan Online
lines.append("### Rekomendasi 2 — Batasi Pesan Makanan Online (Food Delivery)")
lines.append("")
lines.append(
    f"Terdapat **{online_count} transaksi** pesan makanan online senilai total **{fmt_rp(online_total)}**, "
    f"dengan biaya rata-rata **{fmt_rp(int(online_total / online_count) if online_count else 0)}** per pesanan. "
    "Biaya layanan, ongkir, dan markup harga restoran biasanya menambah 25–40% di atas harga normal."
)
lines.append("")
lines.append(
    "**Aksi konkret:** Batasi pemesanan online maksimal 2× per minggu dan manfaatkan promo gratis ongkir. "
    f"Potensi penghematan **{fmt_rp(int(online_total * 0.40))}** per periode dengan mengganti sebagian ke makan langsung di warung."
)
lines.append("")

# Rekomendasi 3: Rencanakan Pengeluaran Besar (Outlier / Belanja Non-rutin)
outlier_non_servis = [r for r in outliers if r["kategori"] != "Transportasi"]
outlier_non_servis_total = sum(r["nominal"] for r in outlier_non_servis)
lines.append("### Rekomendasi 3 — Anggarkan & Rencanakan Pengeluaran Tidak Rutin Sejak Awal Bulan")
lines.append("")
lines.append(
    f"Ditemukan **{len(outliers)} transaksi besar tidak rutin** (outlier) senilai "
    f"**{fmt_rp(sum(r['nominal'] for r in outliers))}** yang terdiri dari:"
)
lines.append("")
for r in outliers:
    lines.append(f"- **{r['tanggal']}** — {r['deskripsi']}: {fmt_rp(r['nominal'])}")
lines.append("")
lines.append(
    "Pengeluaran besar impulsif (seperti Flash Sale dan promo 11.11) tidak tercatat dalam anggaran rutin "
    "sehingga menyebabkan lonjakan signifikan di bulan November."
)
lines.append("")
lines.append(
    "**Aksi konkret:** Buat pos anggaran khusus 'Dana Tak Terduga & Belanja Besar' di awal setiap bulan "
    "sebesar **Rp 500.000–Rp 750.000**. Untuk pembelian >Rp 500.000, terapkan aturan *waiting 48 jam* "
    "sebelum melakukan transaksi agar terhindar dari pembelian impulsif."
)
lines.append("")
lines.append("---")
lines.append("")
lines.append("*Laporan ini dihasilkan secara otomatis oleh `analyze_expenses.py` berdasarkan data `data_pengeluaran.csv`.*")

report = "\n".join(lines)
print(report)

# ─── Simpan ke file ──────────────────────────────────────────────────────────
with open("laporan_analisis_pengeluaran.md", "w", encoding="utf-8") as f:
    f.write(report)

print("\n✅ Laporan berhasil disimpan ke: laporan_analisis_pengeluaran.md")

import pandas as pd
from pathlib import Path

# =========================================================
# YTD LEARNING - MODEL VERİ SETİ
# Kaynak: ex_data.xlsx
# Tüm satırlar kullanılır (şebeke unsurları)
# Bütçe: 60 Birim
# =========================================================

BASE_DIR = Path(__file__).resolve().parent
EXCEL_PATH = BASE_DIR / "ex_data.xlsx"

# Excel'i oku
df = pd.read_excel(EXCEL_PATH)

# ID'yi string/int çatışması yaşamayalım diye string yapalım
df["Şebeke Unsuru"] = df["Şebeke Unsuru"].astype(str)

# --- TEMEL SETLER ---

# Şebeke unsuru listesi (Excel sırasıyla)
I = df["Şebeke Unsuru"].tolist()

# SAIDI, SAIFI, HI sözlükleri
SAIDI = df.set_index("Şebeke Unsuru")["SAIDI"].astype(float).to_dict()
SAIFI = df.set_index("Şebeke Unsuru")["SAIFI"].astype(float).to_dict()
HI    = df.set_index("Şebeke Unsuru")["HI"].astype(float).to_dict()

# Maliyet = MALIYET kolonu
C = (
    df.set_index("Şebeke Unsuru")["MALIYET"]
      .fillna(1)
      .astype(float)
      .to_dict()
)

# Grup (Trafo / Kesici / Kablo ...)
TYPE = df.set_index("Şebeke Unsuru")["GRUP"].to_dict()

# Kategori: 1 = Kurum (kritik), 0 = Özel (kritik değil)
K = (
    df.set_index("Şebeke Unsuru")["Kategori"]
      .fillna(0)
      .astype(int)
      .to_dict()
)

# Yatırım / Bakım bilgisi: 1 = Yatırım, 0 = Bakım
YB = (
    df.set_index("Şebeke Unsuru")["YB"]
      .fillna(0)
      .astype(int)
      .to_dict()
)

# Bütçe
B = 60

# Skorlamada kullanılacak ağırlıklar
w1 = 0.25  # SAIDI
w2 = 0.25  # SAIFI
w3 = 0.10  # Maliyet
w4 = 0.40  # Sağlık / risk

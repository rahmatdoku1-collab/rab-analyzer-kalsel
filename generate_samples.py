import pandas as pd
import os

# Data untuk Vendor A (Normal / Sesuai Budget)
data_vendor_a = {
    "No": [1, 2, 3, 4, 5],
    "Uraian Pekerjaan": [
        "Semen Portland 50kg",
        "Pasir Pasang (m3)",
        "Batu Bata Merah",
        "Besi Beton Polos 10mm",
        "Cat Tembok Interior (Pail)"
    ],
    "Volume": [100, 15, 5000, 200, 5],
    "Satuan": ["Zak", "m3", "Bh", "Btg", "Pail"],
    "Harga Satuan (Rp)": [75000, 250000, 900, 65000, 850000]
}

# Data untuk Vendor B (Murah / Underbudget)
data_vendor_b = {
    "No": [1, 2, 3, 4, 5],
    "Uraian Pekerjaan": [
        "Semen Portland 50kg",
        "Pasir Pasang (m3)",
        "Batu Bata Merah",
        "Besi Beton Polos 10mm",
        "Cat Tembok Interior (Pail)"
    ],
    "Volume": [100, 15, 5000, 200, 5],
    "Satuan": ["Zak", "m3", "Bh", "Btg", "Pail"],
    "Harga Satuan (Rp)": [72000, 240000, 850, 62000, 800000]
}

# Data untuk Vendor C (Mahal / Overbudget / Indikasi Markup)
data_vendor_c = {
    "No": [1, 2, 3, 4, 5],
    "Uraian Pekerjaan": [
        "Semen Portland 50kg",
        "Pasir Pasang (m3)",
        "Batu Bata Merah",
        "Besi Beton Polos 10mm",
        "Cat Tembok Interior (Pail)"
    ],
    "Volume": [100, 15, 5000, 200, 5],
    "Satuan": ["Zak", "m3", "Bh", "Btg", "Pail"],
    "Harga Satuan (Rp)": [95000, 320000, 1200, 85000, 1200000] # Harga dimarkup
}

def create_rab_excel(data, filename):
    filepath = os.path.join(r"C:\Agent RAB Analyzer", filename)
    df = pd.DataFrame(data)
    # Kalkulasi total harga
    df["Total Harga (Rp)"] = df["Volume"] * df["Harga Satuan (Rp)"]
    df.to_excel(filepath, index=False)
    print(f"File {filepath} berhasil dibuat!")

if __name__ == "__main__":
    create_rab_excel(data_vendor_a, "RAB_Tender_Vendor_A.xlsx")
    create_rab_excel(data_vendor_b, "RAB_Tender_Vendor_B.xlsx")
    create_rab_excel(data_vendor_c, "RAB_Tender_Vendor_C.xlsx")

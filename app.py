from flask import Flask, render_template, jsonify
from pathlib import Path
import model_data as md

BASE_DIR = Path(__file__).resolve().parent

app = Flask(
    __name__,
    template_folder=str(BASE_DIR),   # index (1).html bu klasörde
    static_folder=str(BASE_DIR)
)

# ----------------------------------------------------------
# Yardımcı fonksiyonlar
# ----------------------------------------------------------
# Bu doküman, Selinay'ın YTD Learning projesi için app.py içindeki
# build_assets ve optimize_assets fonksiyonlarının temizlenmiş/derli
# toplu halini tutar. Sohbette paylaşılan son sürümle aynı mantığı
# içerir: Excel'den gelen HI'yi min-max ile 0-100'e ölçekler, risk
# etiketini 30/70 eşiklerine göre verir, cost alanını kullanır ve
# optimize_assets içinde bu cost'a göre skor/bütçe oranıyla seçim yapar.

import model_data as md


def build_assets():
    """model_data içindeki sözlüklerden tek bir varlık listesi üretir."""
    assets = []

    # Sağlık skorunu 0-100 bandına ölçeklemek için min-max
    hi_values = [md.HI[i] for i in md.I if i in md.HI]
    hi_min = min(hi_values)
    hi_max = max(hi_values)
    hi_span = max(hi_max - hi_min, 1e-6)

    for i in md.I:
        saidi = float(md.SAIDI.get(i, 0.0))
        saifi = float(md.SAIFI.get(i, 0.0))
        cost = float(md.C.get(i, 1.0))
        hi_raw = float(md.HI.get(i, hi_min))
        grup = md.TYPE.get(i, "Bilinmiyor")
        kategori_flag = int(md.K.get(i, 0))   # 1 = kurum, 0 = özel
        yb_flag = int(md.YB.get(i, 0))        # 1 = yatırım, 0 = bakım

        # 0-100 arası sağlık skoru (yüksek = iyi)
        health_ui = int(round((hi_raw - hi_min) / hi_span * 100))
        health_ui = max(0, min(100, health_ui))

        # Risk etiketi (sağlığı ters çevirerek)
        if health_ui < 30:
            risk = "Yüksek"
        elif health_ui < 70:
            risk = "Orta"
        else:
            risk = "Düşük"

        # Operasyon türü artık Excel'deki YB kolonundan geliyor
        operation_type = "Yatırım" if yb_flag == 1 else "Bakım"

        asset = {
            "id": i,
            "talep_no": i,
            "saidi": saidi,
            "saifi": saifi,
            "cost": cost,
            "group": grup,
            "is_public": bool(kategori_flag),
            "category_label": "Kurum (Kritik)" if kategori_flag == 1 else "Özel (Kritik Değil)",
            "raw_health": hi_raw,
            "health_ui": health_ui,
            "risk_label": risk,
            "operation_type": operation_type,
        }
        assets.append(asset)

    return assets

def optimize_assets(max_items: int = 20):
    """Sezgisel optimizasyon: skor/bütçe oranına göre seçim.

    Amaç: SAIDI, SAIFI ve sağlık riski yüksek olan varlıkları seçmek.
    Kısıtlar:
      - Toplam maliyet <= B (md.B)
      - En fazla max_items adet varlık
      - Aday kümesi: Excel'deki ilk 20 şebeke unsuru
    """
    # Tüm varlıkları kur
    all_assets = build_assets()

    # Optimizasyonda sadece ilk 20 şebeke unsurunu kullan
    first_20_ids = set(md.I[:20])   # Excel sırasına göre ilk 20
    assets = [a for a in all_assets if a["id"] in first_20_ids]

    # Hiç veri yoksa
    if not assets:
        return {
            "status": "Empty",
            "selected": [],
            "selected_count": 0,
            "used_budget": 0.0,
            "budget": md.B,
            "objective_value": 0.0,
        }

    # Normalizasyon için maksimum değerler
    max_saidi = max(a["saidi"] for a in assets) or 1.0
    max_saifi = max(a["saifi"] for a in assets) or 1.0
    max_cost  = max(a["cost"]  for a in assets) or 1.0

    scored = []
    for a in assets:
        norm_saidi       = a["saidi"] / max_saidi
        norm_saifi       = a["saifi"] / max_saifi
        norm_health_risk = (100.0 - a["health_ui"]) / 100.0  # sağlık düşükse risk yüksek
        norm_cost        = a["cost"] / max_cost

        # Birleşik skor
        score = (
            md.w1 * norm_saidi +
            md.w2 * norm_saifi +
            md.w3 * norm_cost +
            md.w4 * norm_health_risk
        )

        scored.append({**a, "score": float(score)})

    # Skor/birim maliyet oranına göre sırala (büyükten küçüğe)
    scored.sort(key=lambda x: x["score"] / max(x["cost"], 0.1), reverse=True)

    selected = []
    used_budget = 0.0
    total_objective_val = 0.0
    budget = float(md.B)

    for item in scored:
        # En fazla max_items tane al
        if len(selected) >= max_items:
            break

        cost = float(item["cost"])
        # Bütçeyi aşma
        if used_budget + cost > budget:
            continue

        selected.append({
            "talep_no": int(item["talep_no"]),
            "group": item["group"],
            "operation_type": item["operation_type"],
            "risk_label": item["risk_label"],
            "cost": cost,
            "score": round(item["score"], 4),
        })
        used_budget += cost
        total_objective_val += item["score"]

    return {
        "status": "OK",
        "selected": selected,
        "selected_count": len(selected),
        "used_budget": used_budget,
        "budget": budget,
        "objective_value": round(total_objective_val, 4),
    }

# ----------------------------------------------------------
# Rotalar
# ----------------------------------------------------------
@app.route("/")
def index():
    # index (1).html'i olduğu gibi render et
    return render_template("index.html")


@app.route("/api/assets")
def api_assets():
    assets = build_assets()
    return jsonify({
        "budget": md.B,
        "count": len(assets),
        "assets": assets,
    })


@app.route("/api/optimize")
def api_optimize():
    result = optimize_assets(max_items=20)
    return jsonify(result)


if __name__ == "__main__":
    app.run(debug=True, port=5000)

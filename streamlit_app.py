# streamlit_app.py
import io
import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
import base64, pathlib

# --- Les logo som base64 (trygt for Streamlit Cloud) ---
logo_path = pathlib.Path("EnergiPartner_RGB-300x140.png")
logo_b64 = None
if logo_path.exists():
    logo_b64 = base64.b64encode(logo_path.read_bytes()).decode("utf-8")

# --- CSS + HTML for logo over tittel ---
st.markdown(f"""
<style>
.ep-header {{
  display: flex;
  flex-direction: column;          /* logo over teksten */
  align-items: flex-start;         /* venstrejustert */
  padding-bottom: 10px;
  border-bottom: 2px solid #097E3E; /* grønn linje under */
  margin-bottom: 10px;
}}
.ep-logo img {{
  display: block;
  max-width: 180px;                /* juster størrelse her */
  margin-bottom: 4px;              /* litt luft mellom logo og tittel */
}}
.ep-headings h1 {{
  color: #097E3E;
  font-weight: 700;
  margin: 0;
  line-height: 1.2;
}}
.ep-headings h4 {{
  color: #097E3E;
  margin: 2px 0 0 0;
  line-height: 1.25;
}}
@media (max-width: 600px){{
  .ep-logo img {{ max-width: 130px; }}
  .ep-headings h1 {{ font-size: 1.6rem; }}
  .ep-headings h4 {{ font-size: 1.0rem; }}
}}
</style>

<div class="ep-header">
  <div class="ep-logo">
    {"<img src='data:image/png;base64," + logo_b64 + "' alt='EnergiPartner logo'/>" if logo_b64 else ""}
  </div>
  <div class="ep-headings">
    <h1>💡 Energisjekk</h1>
    <h4>Rask vurdering av energibruk og energikarakter</h4>
  </div>
</div>
""", unsafe_allow_html=True)

# --- Farger / profil ---
PRIMARY   = "#097E3E"   # mørk grønn
SECONDARY = "#33C831"   # lys grønn
BAR_LIGHT = "#A8E6A1"   # historikkstolper
BAR_DARK  = PRIMARY     # "AKTUELT BYGG"
BADGE_COLORS = {
    "A": "#2E7D32", "B": "#4CAF50", "C": "#9CCC65",
    "D": "#FFEB3B", "E": "#FFC107", "F": "#FF9800", "G": "#F44336"
}

# --- Hjelpere ---
def fmt_int(x: float) -> str:
    return f"{x:,.0f}".replace(",", " ")

def energy_label(sp_kwh_m2: float, thresholds: dict[str, float]) -> str:
    for letter in ["A", "B", "C", "D", "E", "F"]:
        if sp_kwh_m2 <= thresholds[letter]:
            return letter
    return "G"

def parse_int_with_spaces(text: str, default=0):
    try:
        return int(text.replace(" ", "").replace(",", ""))
    except ValueError:
        return default

# --- Inndata ---
CATEGORIES = [
    "Barnehage","Kontorbygning","Skolebygning","Universitets- og høgskolebygning",
    "Sykehus","Sykehjem","Hotellbygning","Idrettsbygning",
    "Forretningsbygning","Kulturbygning","Lett industribygning, verksted","Kombinasjon",
]

c1, c2, c3 = st.columns([1.2, 1, 1])
with c1:
    kategori = st.selectbox("Bygningskategori", CATEGORIES, index=1)
with c2:
    arsforbruk_txt = st.text_input("Årsforbruk (kWh)", fmt_int(500_900))
    arsforbruk = parse_int_with_spaces(arsforbruk_txt, 500_900)
with c3:
    areal_txt = st.text_input("Oppvarmet areal (m² BRA)", fmt_int(3000))
    areal = parse_int_with_spaces(areal_txt, 3000)

sp = arsforbruk / areal

# --- Formålsdeling (prosent) ---
SHARES = {
    "Barnehage":{"Oppvarming":61,"Tappevann":5,"Ventilasjon":14,"Belysning":9,"El.spesifikk":13,"Kjøling":0},
    "Kontorbygning":{"Oppvarming":31,"Tappevann":5,"Ventilasjon":10,"Belysning":16,"El.spesifikk":31,"Kjøling":7},
    "Skolebygning":{"Oppvarming":58,"Tappevann":4,"Ventilasjon":8,"Belysning":15,"El.spesifikk":15,"Kjøling":0},
    "Universitets- og høgskolebygning":{"Oppvarming":37,"Tappevann":7,"Ventilasjon":14,"Belysning":15,"El.spesifikk":19,"Kjøling":8},
    "Sykehus":{"Oppvarming":33,"Tappevann":8,"Ventilasjon":0,"Belysning":0,"El.spesifikk":45,"Kjøling":14},
    "Sykehjem":{"Oppvarming":52,"Tappevann":10,"Ventilasjon":12,"Belysning":10,"El.spesifikk":15,"Kjøling":0},
    "Hotellbygning":{"Oppvarming":42,"Tappevann":16,"Ventilasjon":13,"Belysning":13,"El.spesifikk":15,"Kjøling":1},
    "Idrettsbygning":{"Oppvarming":36,"Tappevann":10,"Ventilasjon":14,"Belysning":15,"El.spesifikk":16,"Kjøling":10},
    "Forretningsbygning":{"Oppvarming":22,"Tappevann":3,"Ventilasjon":11,"Belysning":0,"El.spesifikk":58,"Kjøling":6},
    "Kulturbygning":{"Oppvarming":68,"Tappevann":1,"Ventilasjon":9,"Belysning":9,"El.spesifikk":12,"Kjøling":1},
    "Lett industribygning, verksted":{"Oppvarming":63,"Tappevann":2,"Ventilasjon":5,"Belysning":13,"El.spesifikk":15,"Kjøling":2},
    "Kombinasjon":{"Oppvarming":61,"Tappevann":5,"Ventilasjon":10,"Belysning":15,"El.spesifikk":9,"Kjøling":0},
}

# --- Enova-referanser (kWh/m²·år) til søylediagram ---
REF = {
    "labels":["1950 og eldre","1951–1970","1971–1988","1989–1998","1999–2008","2009–2020"],
    "Barnehage":[407.1,374.5,263.4,231.6,190.0,157.5],
    "Kontorbygning":[303.1,282.4,240.8,202.6,174.0,156.4],
    "Skolebygning":[317.2,293.3,237.8,204.3,172.7,143.8],
    "Universitets- og høgskolebygning":[318.5,297.5,255.7,217.4,189.4,171.4],
    "Sykehus":[507.6,485.2,440.8,400.9,372.7,355.6],
    "Sykehjem":[473.3,448.6,389.4,354.0,320.1,290.9],
    "Hotellbygning":[405.7,380.8,322.0,286.7,254.1,225.2],
    "Idrettsbygning":[462.7,425.8,360.5,289.4,249.2,202.6],
    "Forretningsbygning":[405.7,383.6,338.1,297.8,269.5,252.7],
    "Kulturbygning":[350.8,324.0,264.7,230.2,199.2,171.5],
    "Lett industribygning, verksted":[462.7,427.7,357.9,285.5,241.6,212.4],
    "Kombinasjon":[350.8,324.0,264.7,230.2,199.2,171.5],
}

# --- Energikarakter terskler (kWh/m²·år) ---
THRESH = {
    "Barnehage":dict(A=85,B=115,C=145,D=180,E=220,F=275),
    "Kontorbygning":dict(A=90,B=115,C=145,D=180,E=220,F=275),
    "Skolebygning":dict(A=75,B=105,C=135,D=175,E=220,F=280),
    "Universitets- og høgskolebygning":dict(A=90,B=125,C=160,D=200,E=240,F=300),
    "Sykehus":dict(A=175,B=240,C=305,D=360,E=415,F=505),
    "Sykehjem":dict(A=145,B=195,C=240,D=295,E=355,F=440),
    "Hotellbygning":dict(A=140,B=190,C=240,D=290,E=340,F=415),
    "Idrettsbygning":dict(A=125,B=165,C=205,D=275,E=345,F=440),
    "Forretningsbygning":dict(A=115,B=160,C=210,D=255,E=300,F=375),
    "Kulturbygning":dict(A=95,B=135,C=175,D=215,E=255,F=320),
    "Lett industribygning, verksted":dict(A=105,B=145,C=185,D=250,E=315,F=405),
    "Kombinasjon":dict(A=95,B=135,C=175,D=215,E=255,F=320),
}

label = energy_label(sp, THRESH.get(kategori, THRESH["Kombinasjon"]))
badge_color = BADGE_COLORS[label]

# --- Layout ---
left, right = st.columns([1.05, 1])

# ========== VENSTRE ==========
with left:
    # Nøkkeltall
    st.markdown(f"<h3 style='color:{PRIMARY};margin-bottom:0;'>Årsforbruk</h3>", unsafe_allow_html=True)
    st.markdown(f"<div style='font-size:42px;color:{SECONDARY};font-weight:700'>{fmt_int(arsforbruk)} kWh</div>", unsafe_allow_html=True)

    st.markdown(f"<h3 style='color:{PRIMARY};margin-bottom:0;'>Spesifikt årsforbruk</h3>", unsafe_allow_html=True)
    st.markdown(f"<div style='font-size:42px;color:{SECONDARY};font-weight:700'>{sp:.0f} kWh/m² BRA</div>", unsafe_allow_html=True)

    st.markdown(f"<h3 style='color:{PRIMARY};margin-bottom:6px;'>Kalkulert energikarakter*</h3>", unsafe_allow_html=True)
    st.markdown(
        f"<div style='display:inline-block;padding:.8rem 1.4rem;border-radius:1rem;"
        f"background:{badge_color};color:white;font-weight:900;font-size:40px;margin-bottom:8px;'>"
        f"{label}</div>",
        unsafe_allow_html=True
    )

    # Overskrift + søylediagram (kompakt)
    st.markdown(f"<h3 style='color:{PRIMARY};margin-bottom:6px;'>Energibruk pr. m² (referanse vs. bygg)</h3>", unsafe_allow_html=True)

    cols = REF["labels"] + ["AKTUELT BYGG"]
    vals = REF[kategori] + [sp]

    fig2, ax2 = plt.subplots(figsize=(4.2, 2.2))
    colors = [BAR_LIGHT] * (len(vals) - 1) + [BAR_DARK]
    bars = ax2.bar(cols, vals, color=colors, width=0.55)

    ax2.set_ylabel("kWh/m²", fontsize=10, color=PRIMARY, labelpad=4)
    ax2.set_ylim(0, max(vals) * 1.25)
    ax2.spines["top"].set_visible(False)
    ax2.spines["right"].set_visible(False)

    for t in ax2.get_xticklabels():
        t.set_rotation(20)
        t.set_ha("right")

    for b, v in zip(bars, vals):
        ax2.text(b.get_x() + b.get_width()/2, v + 3, f"{v:.1f}",
                 ha="center", va="bottom", fontsize=8, color=PRIMARY)

    # Uten kantlinje rundt "AKTUELT BYGG"
    bars[-1].set_linewidth(0)
    bars[-1].set_alpha(0.95)

    # Vises i fast bredde slik at den ikke blåses opp
    buf = io.BytesIO()
    fig2.savefig(buf, format="png", bbox_inches="tight", dpi=200)
    buf.seek(0)
    st.image(buf, width=480)  # juster 380–460 ved behov

# ========== HØYRE ==========
with right:
    st.markdown(f"<h3 style='color:{PRIMARY};margin-bottom:4px;'>Energiforbruk formålsfordelt</h3>", unsafe_allow_html=True)

    # klargjør data (din logikk som før)
    pct = SHARES[kategori].copy()
    # ev. spesialhåndtering for forretningsbygg/sykehus her ...

    FORMAL_ORDER = ["Oppvarming","Tappevann","Ventilasjon","Belysning",
                    "El.spesifikk (inkl. belysning)","El.spesifikk","Kjøling"]
    FORMAL_COLORS = {
        "Oppvarming":  "#33C831",
        "Tappevann":   "#097E3E",
        "Ventilasjon": "#74D680",
        "Belysning":   "#FFC107",
        "El.spesifikk":"#2E7BB4",
        "El.spesifikk (inkl. belysning)":"#2E7BB4",
        "Kjøling":     "#00ACC1",
    }

    ordered_pct = {k: pct[k] for k in FORMAL_ORDER if k in pct and pct[k] > 0}
    values = [arsforbruk * (v/100) for v in ordered_pct.values()]
    labels = [f"{k}\n{fmt_int(val)} kWh" for k, val in zip(ordered_pct.keys(), values)]
    colors = [FORMAL_COLORS.get(k, "#999999") for k in ordered_pct.keys()]

    # tegn pie med kontrollert størrelse
    fig, ax = plt.subplots(figsize=(5.2, 4.8))  # ikke for bred/høy
    ax.pie(values, labels=labels, colors=colors,
           autopct=lambda p: f"{p:.1f}%", startangle=90, counterclock=False)
    ax.axis("equal")

    # vis som bilde i fast bredde → holder seg i kolonnen
    import io
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=160)
    buf.seek(0)
    st.image(buf, width=480)   # juster 420–460 for å matche venstre figur



with st.expander("Kilder og forutsetninger", expanded=False):
    st.markdown("""
    - **Formålsdeling:** NVE Rapport 2016:24  
    - **Referanseverdier pr m² / tiltak:** Enova (veiledere og kunnskapsartikler)  
    - **Energikarakter:** Enova – Karakterskalaen  
    """)

# streamlit_app.py
import math
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="Energisjekk", layout="wide")

# ---------- Hjelpere ----------
def fmt_int(x: float) -> str:
    return f"{x:,.0f}".replace(",", " ")

def energy_label(sp_kwh_m2: float, thresholds: dict[str, float]) -> tuple[str, str]:
    """Returnerer (bokstav, hex-farge)."""
    # terskler er øvre grenser for A..F. Alt over => G
    for letter in ["A", "B", "C", "D", "E", "F"]:
        if sp_kwh_m2 <= thresholds[letter]:
            color = {
                "A": "#4CAF50",  # grønn
                "B": "#2E7D32",
                "C": "#9CCC65",
                "D": "#FFEB3B",
                "E": "#FFC107",
                "F": "#FF9800",
            }[letter]
            return letter, color
    return "G", "#F44336"  # rød

# ---------- Inndata ----------
CATS = [
    "Barnehage", "Kontorbygning", "Skolebygning",
    "Universitets- og høgskolebygning", "Sykehus", "Sykehjem",
    "Hotellbygning", "Idrettsbygning", "Forretningsbygning",
    "Kulturbygning", "Lett industribygning, verksted", "Kombinasjon",
]

col1, col2, col3 = st.columns([1.2, 1, 1])
with col1:
    kategori = st.selectbox("Velg bygningskategori", CATS, index=1)
with col2:
    arsforbruk = st.number_input("Årsforbruk (kWh)", value=400_000, min_value=0, step=10_000, format="%i")
with col3:
    areal = st.number_input("Oppvarmet areal BRA (m²)", value=2_000, min_value=1, step=50, format="%i")

sp = arsforbruk / areal

# ---------- Formålsdeling (prosent) ----------
# Kilde: tabellen du la inn (NVE 2016). "Verdier som brukes" + kategorispesifikke.
SHARES = {
    "Barnehage": {"Oppvarming":61, "Tappevann":5, "Ventilasjon":14, "Belysning":9,  "El.spesifikk":13, "Kjøling":0},
    "Kontorbygning": {"Oppvarming":31, "Tappevann":5, "Ventilasjon":10, "Belysning":16, "El.spesifikk":31, "Kjøling":9},
    "Skolebygning": {"Oppvarming":58, "Tappevann":4, "Ventilasjon":8,  "Belysning":15, "El.spesifikk":15, "Kjøling":0},
    "Universitets- og høgskolebygning": {"Oppvarming":37, "Tappevann":7, "Ventilasjon":14, "Belysning":15, "El.spesifikk":19, "Kjøling":8},
    "Sykehus": {"Oppvarming":33, "Tappevann":8, "Ventilasjon":0,  "Belysning":0,  "El.spesifikk":45, "Kjøling":14},
    "Sykehjem": {"Oppvarming":52, "Tappevann":10, "Ventilasjon":12, "Belysning":10, "El.spesifikk":15, "Kjøling":0},
    "Hotellbygning": {"Oppvarming":42, "Tappevann":16, "Ventilasjon":13, "Belysning":13, "El.spesifikk":15, "Kjøling":1},
    "Idrettsbygning": {"Oppvarming":36, "Tappevann":10, "Ventilasjon":14, "Belysning":15, "El.spesifikk":16, "Kjøling":10},
    "Forretningsbygning": {"Oppvarming":22, "Tappevann":3,  "Ventilasjon":11, "Belysning":0,  "El.spesifikk":58, "Kjøling":6},
    "Kulturbygning": {"Oppvarming":68, "Tappevann":1,  "Ventilasjon":9,  "Belysning":9,  "El.spesifikk":12, "Kjøling":1},
    "Lett industribygning, verksted": {"Oppvarming":63, "Tappevann":2, "Ventilasjon":5, "Belysning":13, "El.spesifikk":15, "Kjøling":2},
    "Kombinasjon": {"Oppvarming":61, "Tappevann":5, "Ventilasjon":10, "Belysning":15, "El.spesifikk":9, "Kjøling":0},  # fallback
}

# ---------- Referanseverdier pr byggeår (kWh/m²/år) ----------
REF = {
    "labels": ["1950 og eldre","1951–1970","1971–1988","1989–1998","1999–2008","2009–2020"],
    "Barnehage":                 [407.1, 374.5, 263.4, 231.6, 190.0, 157.5],
    "Kontorbygning":             [303.1, 282.4, 240.8, 202.6, 174.0, 156.4],
    "Skolebygning":              [317.2, 293.3, 237.8, 204.3, 172.7, 143.8],
    "Universitets- og høgskolebygning": [318.5, 297.5, 255.7, 217.4, 189.4, 171.4],
    "Sykehus":                   [507.6, 485.2, 440.8, 400.9, 372.7, 355.6],
    "Sykehjem":                  [473.3, 448.6, 389.4, 354.0, 320.1, 290.9],
    "Hotellbygning":             [405.7, 380.8, 322.0, 286.7, 254.1, 225.2],
    "Idrettsbygning":            [462.7, 425.8, 360.5, 289.4, 249.2, 202.6],
    "Forretningsbygning":        [405.7, 383.6, 338.1, 297.8, 269.5, 252.7],
    "Kulturbygning":             [350.8, 324.0, 264.7, 230.2, 199.2, 171.5],
    "Lett industribygning, verksted": [462.7, 427.7, 357.9, 285.5, 241.6, 212.4],
    "Kombinasjon":               [350.8, 324.0, 264.7, 230.2, 199.2, 171.5],
}

# ---------- Energikarakter (kWh/m²/år) ----------
# Tabell «Levert energi pr m² oppvarmet BRA»
THRESH = {
    "Småhus": dict(A=95,B=135,C=175,D=215,E=255,F=320),
    "Leiligheter (boligblokk)": dict(A=85,B=95,C=110,D=135,E=160,F=200),
    "Barnehage": dict(A=85,B=115,C=145,D=180,E=220,F=275),
    "Kontorbygning": dict(A=90,B=115,C=145,D=180,E=220,F=275),
    "Skolebygning": dict(A=75,B=105,C=135,D=175,E=220,F=280),
    "Universitets- og høgskolebygning": dict(A=90,B=125,C=160,D=200,E=240,F=300),
    "Sykehus": dict(A=175,B=240,C=305,D=360,E=415,F=505),
    "Sykehjem": dict(A=145,B=195,C=240,D=295,E=355,F=440),
    "Hotellbygning": dict(A=140,B=190,C=240,D=290,E=340,F=415),
    "Idrettsbygning": dict(A=125,B=165,C=205,D=275,E=345,F=440),
    "Forretningsbygning": dict(A=115,B=160,C=210,D=255,E=300,F=375),
    "Kulturbygning": dict(A=95,B=135,C=175,D=215,E=255,F=320),
    "Lett industribygning, verksted": dict(A=105,B=145,C=185,D=250,E=315,F=405),
    "Kombinasjon": dict(A=95,B=135,C=175,D=215,E=255,F=320),
}
label, label_color = energy_label(sp, THRESH.get(kategori, THRESH["Kombinasjon"]))

# ---------- Toppfelt ----------
left, right = st.columns([1.1, 1])
with left:
    st.subheader(f"{kategori}")
    st.markdown(
        f"""
**Årsforbruk:** {fmt_int(arsforbruk)} kWh  
**Oppvarmet areal (BRA):** {fmt_int(areal)} m²  
**Spesifikt energibruk:** **{sp:.1f} kWh/m²·år**
"""
    )
    st.markdown(
        f"""<div style="display:inline-block;padding:.35rem .8rem;border-radius:.6rem;background:{label_color};color:white;font-weight:700">
        Energikarakter: {label}</div>""",
        unsafe_allow_html=True,
    )

with right:
    # Formålsfordeling – kakediagram
    shares = SHARES[kategori]
    vals = [arsforbruk * (p/100) for p in shares.values()]
    fig, ax = plt.subplots()
    ax.pie(vals, labels=list(shares.keys()), autopct="%1.0f%%", startangle=90)
    ax.set_title("Energibruk formålsfordelt")
    st.pyplot(fig, use_container_width=True)

st.divider()

# ---------- Søyle: referanser + «AKTUELT BYGG» ----------
cols = REF["labels"] + ["AKTUELT BYGG"]
vals = REF[kategori] + [sp]

fig2, ax2 = plt.subplots(figsize=(7, 3.8))
bars = ax2.bar(cols, vals)
# highlight siste bar
for i, b in enumerate(bars):
    if i == len(bars)-1:
        b.set_color("#1976D2")       # blå
        b.set_linewidth(3)
        b.set_edgecolor("#0D47A1")
    else:
        b.set_alpha(0.75)
ax2.set_ylabel("kWh/m²·år")
ax2.set_ylim(0, max(vals)*1.25)
for tick in ax2.get_xticklabels():
    tick.set_rotation(20)
    tick.set_ha("right")
ax2.spines["top"].set_visible(False)
ax2.spines["right"].set_visible(False)
ax2.set_title("Gjennomsnittlig årlig energibruk pr m² (referanser)")

st.pyplot(fig2, use_container_width=True)

# ---------- Kompakt tabell nederst ----------
# Bygg tabell med formålsfordelt kWh + andeler
rows = []
for k, p in shares.items():
    kwh = arsforbruk * (p/100)
    rows.append([k, fmt_int(kwh), f"{p:.0f} %"])
df = pd.DataFrame(rows, columns=["Formål", "kWh/år", "Andel"])

# Formatering + markering
st.markdown("##### Fordeling pr formål")
st.dataframe(
    df,
    use_container_width=True,
    height=320,
    column_config={
        "Formål": st.column_config.TextColumn("Formål"),
        "kWh/år": st.column_config.TextColumn("kWh/år"),
        "Andel":  st.column_config.TextColumn("Andel"),
    }
)

st.caption(f"Spesifikt energibruk: {sp:.1f} kWh/m²·år  •  Energikarakter {label}")


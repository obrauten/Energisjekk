# streamlit_app.py
import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd

st.set_page_config(page_title="Energisjekk", page_icon="💡", layout="wide")
st.title("💡 Energisjekk – oppsummering")

# -----------------------------
# INPUT (kun 3 felt – som i Excel-fanen)
# -----------------------------
KATEGORIER = ["Kontorbygning", "Skolebygning", "Forretningsbygning", "Hotellbygning"]
colA, colB, colC = st.columns([1.2,1,1])
with colA:
    kat = st.selectbox("Bygningskategori", KATEGORIER, index=0)
with colB:
    arsforbruk = st.number_input("Totalt årsforbruk (kWh)", min_value=0.0, value=500_900.0, step=10_000.0, format="%.0f")
with colC:
    areal = st.number_input("Oppvarmet areal (m² BRA)", min_value=1.0, value=3000.0, step=100.0, format="%.0f")

spesifikt = arsforbruk / areal

# -----------------------------
# DATA: Formålsfordeling (NVE 2016 – forenklet startset) og
# Enova benchmark pr byggeår (verdier fra tabellen din)
# -----------------------------
FORMALS_PCT = {
    # Summer ~100 %. Juster etter din Excel ved behov.
    "Kontorbygning":       {"Oppvarming":31, "Tappevann":5, "Ventilasjon":10, "Belysning":16, "El.spesifikk":31, "Kjøling":7},
    "Skolebygning":        {"Oppvarming":58, "Tappevann":4, "Ventilasjon":8,  "Belysning":15, "El.spesifikk":15, "Kjøling":0},
    "Forretningsbygning":  {"Oppvarming":22, "Tappevann":3, "Ventilasjon":11, "Belysning":0,  "El.spesifikk":58, "Kjøling":6},
    "Hotellbygning":       {"Oppvarming":36, "Tappevann":10,"Ventilasjon":14, "Belysning":15, "El.spesifikk":16, "Kjøling":9},
}

# Enova – gjennomsnitt kWh/m² etter byggeår (fra tabellen din)
BENCH_ENOVA = {
    "Kontorbygning":      [407.1, 374.5, 263.4, 231.6, 190.0, 157.5],
    "Skolebygning":       [303.1, 282.4, 240.8, 202.6, 174.0, 156.4],
    "Forretningsbygning": [462.7, 425.8, 360.5, 289.4, 249.2, 202.6],
    "Hotellbygning":      [473.3, 448.6, 389.4, 354.0, 320.1, 290.9],
}
BENCH_ÅR = ["≤1950", "1951–70", "1971–88", "1989–98", "1999–08", "2009–20"]

# Energikarakterterskler A–F (≤ grense gir bokstav; >F blir G)
KARAKTER_GRENSE = {
    "Kontorbygning":      {"A":90,  "B":115, "C":145, "D":180, "E":220, "F":275},
    "Skolebygning":       {"A":75,  "B":105, "C":135, "D":175, "E":220, "F":280},
    "Forretningsbygning": {"A":115, "B":160, "C":210, "D":255, "E":300, "F":375},
    "Hotellbygning":      {"A":140, "B":190, "C":240, "D":290, "E":340, "F":415},
}

def energikarakter(sp, grenser: dict) -> str:
    for bokstav, grense in grenser.items():
        if sp <= grense:
            return bokstav
    return "G"

kar = energikarakter(spesifikt, KARAKTER_GRENSE[kat])

# -----------------------------
# LAYOUT – venstre: tall & energikarakter, høyre: kakediagram
# -----------------------------
venstre, høyre = st.columns([1.05,1])

with venstre:
    st.subheader("Oppsummering")
    st.markdown(f"**Årsforbruk**\n\n<span style='font-size:34px;color:#138a36'><b>{arsforbruk:,.0f} kWh</b></span>", unsafe_allow_html=True)
    st.markdown(f"**Spesifikt årsforbruk**\n\n<span style='font-size:34px;color:#138a36'><b>{spesifikt:.0f} kWh/m² BRA</b></span>", unsafe_allow_html=True)
    # Vis energikarakter
    farger = {"A":"#009E3B","B":"#7BC043","C":"#F1C40F","D":"#F39C12","E":"#E67E22","F":"#D35400","G":"#C0392B"}
    st.markdown("**Kalkulert energikarakter (faktisk levert energi):**")
    st.markdown(
        f"<div style='display:inline-block;padding:10px 18px;border-radius:6px;background:{farger[kar]};color:white;font-weight:700;font-size:22px;'>"
        f"{kar}</div>", unsafe_allow_html=True
    )
    st.caption("Grensene følger tersklene du har i Excel-arket (A–F pr. kategori; >F = G).")

with høyre:
    st.subheader("Energiforbruk formålsfordelt")
    pct = FORMALS_PCT[kat]
    kwh = {k: arsforbruk*(v/100) for k,v in pct.items()}
    fig, ax = plt.subplots()
    ax.pie(kwh.values(), labels=[f"{k}\n{v:,.0f} kWh" for k,v in kwh.items()], autopct="%1.1f%%")
    ax.axis("equal")
    st.pyplot(fig)

# -----------------------------
# Benchmark søylediagram (Enova) + “aktuelt bygg”
# -----------------------------
st.subheader("Gjennomsnittlig årlig energibruk pr. m² oppvarmet areal (Enova) – inkl. ditt bygg")
bench = BENCH_ENOVA[kat][:]
år = BENCH_ÅR[:]
bench.append(spesifikt)
år.append("AKTUELT BYGG")

df = pd.DataFrame({"Byggeår": år, "kWh/m²": bench})
fig2 = plt.figure()
ax2 = fig2.gca()
ax2.bar(df["Byggeår"], df["kWh/m²"])
ax2.set_ylabel("kWh/m²")
for x,y in zip(df["Byggeår"], df["kWh/m²"]):
    ax2.text(x, y+5, f"{y:.1f}", ha="center", va="bottom", fontsize=8)
st.pyplot(fig2)

st.info("Endre kun tre inputfelter øverst. Øvrige felt fra A1:A19 i Excel er utelatt nå.")

# (valgfritt) eksport av nøkkeltall
with st.expander("⬇️ Last ned nøkkeltall (CSV)"):
    rows = {
        "Kategori":[kat],
        "Areal_m2":[areal],
        "Årsforbruk_kWh":[arsforbruk],
        "Spesifikt_kWh_per_m2":[spesifikt],
        "Energikarakter":[kar],
    }
    st.download_button("Last ned", pd.DataFrame(rows).to_csv(index=False).encode("utf-8"),
                       file_name="energisjekk_nokkeldata.csv", mime="text/csv")


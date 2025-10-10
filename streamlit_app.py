# streamlit_app.py
import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd

# ---------- UI ----------
st.set_page_config(page_title="Energisjekk", page_icon="💡", layout="wide")
st.title("💡 Energisjekk")

# ---------- helpers ----------
def fmt0(x):  # heltall med mellomrom
    return f"{x:,.0f}".replace(",", " ")
def fmt1(x):  # 1 desimal, mellomrom
    s = f"{x:,.1f}"
    return s.replace(",", " ")
def space_fmt_series(s, decimals=0):
    if decimals == 0:
        return s.apply(lambda v: fmt0(float(v)))
    return s.apply(lambda v: fmt1(float(v)))

# ---------- input ----------
KATEGORIER = ["Kontorbygning", "Skolebygning", "Forretningsbygning", "Hotellbygning"]
colA, colB, colC = st.columns([1.2,1,1])
with colA:
    kat = st.selectbox("Bygningskategori", KATEGORIER, index=0)
with colB:
    arsforbruk = st.number_input("Totalt årsforbruk (kWh)", min_value=0.0, value=500_900.0, step=10_000.0, format="%.0f")
with colC:
    areal = st.number_input("Oppvarmet areal (m² BRA)", min_value=1.0, value=3000.0, step=100.0, format="%.0f")

spesifikt = arsforbruk / areal

# ---------- data ----------
FORMALS_PCT = {
    "Kontorbygning":       {"Oppvarming":31, "Tappevann":5, "Ventilasjon":10, "Belysning":16, "El.spesifikk":31, "Kjøling":7},
    "Skolebygning":        {"Oppvarming":58, "Tappevann":4, "Ventilasjon":8,  "Belysning":15, "El.spesifikk":15, "Kjøling":0},
    "Forretningsbygning":  {"Oppvarming":22, "Tappevann":3, "Ventilasjon":11, "Belysning":0,  "El.spesifikk":58, "Kjøling":6},
    "Hotellbygning":       {"Oppvarming":36, "Tappevann":10,"Ventilasjon":14, "Belysning":15, "El.spesifikk":16, "Kjøling":9},
}
BENCH_ENOVA = {
    "Kontorbygning":      [407.1, 374.5, 263.4, 231.6, 190.0, 157.5],
    "Skolebygning":       [303.1, 282.4, 240.8, 202.6, 174.0, 156.4],
    "Forretningsbygning": [462.7, 425.8, 360.5, 289.4, 249.2, 202.6],
    "Hotellbygning":      [473.3, 448.6, 389.4, 354.0, 320.1, 290.9],
}
BENCH_ÅR = ["≤1950", "1951–70", "1971–88", "1989–98", "1999–08", "2009–20"]
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
farger = {"A":"#009E3B","B":"#7BC043","C":"#F1C40F","D":"#F39C12","E":"#E67E22","F":"#D35400","G":"#C0392B"}

# ---------- layout: venstre tall + karakter, høyre kakediagram ----------
venstre, høyre = st.columns([1.05,1])

with venstre:
    st.subheader("Nøkkeltall")
    st.markdown(f"**Årsforbruk**  \n<span style='font-size:34px;color:#138a36'><b>{fmt0(arsforbruk)} kWh</b></span>", unsafe_allow_html=True)
    st.markdown(f"**Spesifikt årsforbruk**  \n<span style='font-size:34px;color:#138a36'><b>{fmt0(spesifikt)} kWh/m² BRA</b></span>", unsafe_allow_html=True)
    st.markdown("**Kalkulert energikarakter (faktisk levert energi):**")
    st.markdown(
        f"<div style='display:inline-block;padding:10px 18px;border-radius:6px;background:{farger[kar]};color:white;font-weight:700;font-size:22px;'>{kar}</div>",
        unsafe_allow_html=True
    )

with høyre:
    st.subheader("Energiforbruk formålsfordelt")
    pct = FORMALS_PCT[kat]
    kwh = {k: arsforbruk*(v/100) for k,v in pct.items()}
    fig, ax = plt.subplots()
    # pie labels med mellomrom som tusenskiller
    labels = [f"{k}\n{fmt0(v)} kWh" for k,v in kwh.items()]
    ax.pie(kwh.values(), labels=labels, autopct=lambda p: f"{p:.1f}%")
    ax.axis("equal")
    st.pyplot(fig)

# ---------- benchmark: tydelig "AKTUELT BYGG" ----------
st.subheader("Gjennomsnittlig årlig energibruk pr. m² oppvarmet areal (Enova) – inkl. ditt bygg")

bench_vals = BENCH_ENOVA[kat][:]
år = BENCH_ÅR[:]
bench_vals.append(spesifikt)
år.append("AKTUELT BYGG")

# plot med siste stolpe uthevet
colors = ["#88b7d8"]*len(bench_vals)
colors[-1] = "#1f77b4"  # aktuell bygg farge
fig2, ax2 = plt.subplots()
bars = ax2.bar(år, bench_vals, color=colors, edgecolor=["#88b7d8"]*(len(bench_vals)-1)+["#000"], linewidth=[0]*(len(bench_vals)-1)+[2])
ax2.set_ylabel("kWh/m²")
# etiketter med mellomrom
for rect, y in zip(bars, bench_vals):
    ax2.text(rect.get_x()+rect.get_width()/2, y+5, fmt1(y), ha="center", va="bottom", fontsize=8)
# gjør “AKTUELT BYGG” fet i x-aksen
ticks = ax2.get_xticklabels()
ticks[-1].set_fontweight("bold")
st.pyplot(fig2)

# tabell med uthevet rad og riktig formatering
df = pd.DataFrame({"Byggeår": år, "kWh/m²": bench_vals})
df_fmt = df.copy()
df_fmt["kWh/m²"] = space_fmt_series(df_fmt["kWh/m²"], decimals=1)
def highlight_last_row(s):
    is_last = [False]*(len(s)-1) + [True]
    return ["background-color: #e8f2ff; font-weight: 700" if v else "" for v in is_last]
st.dataframe(df_fmt.style.apply(highlight_last_row, subset=["Byggeår","kWh/m²"]), use_container_width=True)

st.caption("Tall med mellomrom som tusenskiller. ‘AKTUELT BYGG’ er markert med blå stolpe, tykk kant og uthevet tabellrad.")

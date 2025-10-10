import streamlit as st
import math
import matplotlib.pyplot as plt

st.set_page_config(page_title="Energisjekk", page_icon="💡")

st.title("💡 Energisjekk – rask vurdering")

# --- konfig ---
CATEGORIES = {
    "Kontor": {
        "benchmarks": {
            "Ambisiøst (nZEB/ZEB)": 100,
            "TEK17-nivå": 120,
            "2000–2010": 170,
            "Eldre (før ~1990)": 250,
        },
        "formalsdeling_pct": {
            "Romoppvarming": 35,
            "Ventilasjonsvarme": 10,
            "Vifter/pumper": 10,
            "Belysning": 15,
            "Utstyr/IT": 20,
            "Tappevann": 5,
            "Kjøling": 5,
        },
    },
    "Skole": {
        "benchmarks": {
            "Ambisiøst (nZEB/ZEB)": 95,
            "TEK17-nivå": 110,
            "2000–2010": 160,
            "Eldre (før ~1990)": 220,
        },
        "formalsdeling_pct": {
            "Romoppvarming": 40,
            "Ventilasjonsvarme": 10,
            "Vifter/pumper": 10,
            "Belysning": 18,
            "Utstyr": 12,
            "Tappevann": 7,
            "Kjøling": 3,
        },
    },
    "Forretning": {
        "benchmarks": {
            "Ambisiøst (nZEB/ZEB)": 115,
            "TEK17-nivå": 140,
            "2000–2010": 200,
            "Eldre (før ~1990)": 300,
        },
        "formalsdeling_pct": {
            "Romoppvarming": 30,
            "Ventilasjonsvarme": 10,
            "Vifter/pumper": 10,
            "Belysning": 20,
            "Kjøl/frys/utstyr": 20,
            "Tappevann": 5,
            "Kjøling": 5,
        },
    },
    "Hotell": {
        "benchmarks": {
            "Ambisiøst (nZEB/ZEB)": 120,
            "TEK17-nivå": 140,
            "2000–2010": 200,
            "Eldre (før ~1990)": 280,
        },
        "formalsdeling_pct": {
            "Romoppvarming": 32,
            "Ventilasjonsvarme": 10,
            "Vifter/pumper": 8,
            "Belysning": 12,
            "Kjøkken/utstyr": 12,
            "Tappevann": 20,
            "Kjøling": 6,
        },
    },
}

# --- inputfelt ---
cat = st.selectbox("Velg bygningskategori", list(CATEGORIES.keys()))
forbruk = st.number_input("Totalt årsforbruk (kWh)", 0.0, 1_000_000.0, 250_000.0, step=10_000.0)
areal = st.number_input("Oppvarmet areal (m²)", 1.0, 50_000.0, 2000.0, step=100.0)

cfg = CATEGORIES[cat]
sp = forbruk / areal

# --- vurdering ---
def vurdering(sp, refs):
    for label, limit in refs.items():
        if sp <= limit:
            if "Ambisiøst" in label: return f"🟢 Svært godt (≤ {limit} kWh/m²/år, {label})"
            if "TEK17" in label:    return f"🟡 Bra (≤ {limit} kWh/m²/år, {label})"
            if "2000–2010" in label:return f"🟠 Ok (≤ {limit} kWh/m²/år, {label})"
    return f"🔴 Over {list(refs.values())[-1]} kWh/m²/år (eldre byggnivå)"

# --- beregning ---
st.subheader("🔹 Resultat")
st.write(f"**Spesifikt energibruk:** {sp:.1f} kWh/m²/år")
st.write(f"**Vurdering:** {vurdering(sp, cfg['benchmarks'])}")

# --- referanser ---
st.subheader("📊 Referansenivåer")
st.table(cfg["benchmarks"])

# --- formålsfordeling ---
bd = {k: forbruk * (v/100.0) for k, v in cfg["formalsdeling_pct"].items()}
st.subheader("⚙️ Formålsfordeling")
st.table({k: f"{v:,.0f} kWh ({cfg['formalsdeling_pct'][k]} %)" for k, v in bd.items()})

# --- kakediagram ---
fig, ax = plt.subplots()
ax.pie(bd.values(), labels=bd.keys(), autopct="%1.1f%%")
ax.set_title(f"Formålsfordeling – {cat}")
st.pyplot(fig)

st.info("Endre verdiene øverst for å se hvordan resultatet påvirkes.")

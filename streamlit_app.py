# streamlit_app.py
import io
import base64
import pathlib
import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st
st.set_page_config(page_title="Energisjekk", page_icon="🔎", layout="wide")

# ---------- LAST LOGO ----------
logo_path = pathlib.Path("EnergiPartner_RGB-300x140.png")
logo_b64 = None
if logo_path.exists():
    logo_b64 = base64.b64encode(logo_path.read_bytes()).decode("utf-8")

# ---------- LOGO OG TOPP (uten lenker på tittel) ----------
st.markdown(f"""
<style>
.ep-header {{
  display:flex; flex-direction:column; align-items:flex-start;
  padding-bottom:10px; border-bottom:2px solid #097E3E; margin-bottom:10px;
}}
.ep-logo img {{ display:block; max-width:180px; margin-bottom:6px; }}
.ep-title   {{ color:#097E3E; font-weight:700; font-size:28px; line-height:1.2; margin:0; }}
.ep-sub     {{ color:#097E3E; font-size:16px;  line-height:1.25; margin:2px 0 0 0; }}
@media (max-width:600px){{
  .ep-logo img {{ max-width:130px; }}
  .ep-title   {{ font-size:26px; }}
  .ep-sub     {{ font-size:15px;  }}
}}
</style>

<div class="ep-header">
  <div class="ep-logo">
    {"<img src='data:image/png;base64," + logo_b64 + "' alt='EnergiPartner logo'/>" if logo_b64 else ""}
  </div>
  <div class="ep-title">Energisjekk</div>
  <div class="ep-sub">Rask vurdering av energibruk og energikarakter</div>
</div>
""", unsafe_allow_html=True)

# --- Fjern eller oversett "Press Enter to apply" ---
st.markdown("""
<script>
window.addEventListener('load', function() {
  const applyHints = document.querySelectorAll('span[data-testid="stNumberInputInstructions"]');
  applyHints.forEach(el => {
    el.innerText = "Trykk Enter for å oppdatere";
  });
});
</script>
""", unsafe_allow_html=True)


# ---------- FARGER ----------
PRIMARY   = "#097E3E"
SECONDARY = "#33C831"
BAR_LIGHT = "#A8E6A1"
BAR_DARK  = PRIMARY
BADGE_COLORS = {
    "A": "#2E7D32", "B": "#4CAF50", "C": "#9CCC65",
    "D": "#FFEB3B", "E": "#FFC107", "F": "#FF9800", "G": "#F44336"
}


# ---------- HJELPERE ----------
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

# Felles tittel-stil uten klikkbare lenker
def title(text: str):
    st.markdown(
        f"<div style='color:{PRIMARY}; font-size:20px; font-weight:700; margin-bottom:6px;'>{text}</div>",
        unsafe_allow_html=True
    )


# ---------- INPUT ----------
CATEGORIES = [
    "Barnehage","Kontorbygning","Skolebygning","Universitets- og høgskolebygning",
    "Sykehus","Sykehjem","Hotellbygning","Idrettsbygning",
    "Forretningsbygning","Kulturbygning","Lett industribygning, verksted","Kombinasjon",
]

c1, c2, c3 = st.columns([1.2, 1, 1])

with c1:
    kategori = st.selectbox("Bygningskategori", CATEGORIES, index=1)

with c2:
    arsforbruk = st.number_input(
        "Årsforbruk (kWh)",
        min_value=0,
        value=500_000,
        step=1_000,
        format="%i",
    )

with c3:
    areal = st.number_input(
        "Oppvarmet areal (m² BRA)",
        min_value=1,
        value=3_000,
        step=100,
        format="%i",
    )

sp = arsforbruk / areal

# ---------- FORMÅLSFORDELING ----------
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


# ---------- REFERANSER TIL SØYLE ----------
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


# ---------- ENERGIKARAKTER ----------
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


# ---------- LAYOUT ----------
left, right = st.columns([1, 1.5])
with left:
    title("Årsforbruk")
    st.markdown(f"<div style='font-size:42px;color:{SECONDARY};font-weight:700'>{fmt_int(arsforbruk)} kWh</div>", unsafe_allow_html=True)
    st.markdown("<div style='height:35px;'></div>", unsafe_allow_html=True)

    title("Spesifikt årsforbruk")
    st.markdown(
        f"<div style='font-size:42px;color:{SECONDARY};font-weight:700'>{sp:.0f} kWh/m² BRA</div>",
        unsafe_allow_html=True
    )

    # --- TEK17-referansetall pr kategori ---
    TEK17_REF = {
        "Barnehage": 135,
        "Kontorbygning": 115,
        "Skolebygning": 110,
        "Universitets- og høgskolebygning": 125,
        "Sykehus": 225,                             # alternativt nivå: 265
        "Sykehjem": 195,                            # alternativt nivå: 230
        "Hotellbygning": 170,
        "Idrettsbygning": 145,
        "Forretningsbygning": 180,
        "Kulturbygning": 130,
        "Lett industribygning, verksted": 140,      # alternativt nivå: 160
        "Kombinasjon": 135,
    }

    # Parentesverdier der TEK17 oppgir to tall (vises i grått som "ev. XXX")
    TEK17_ALT = {
        "Sykehus": 265,
        "Sykehjem": 230,
        "Lett industribygning, verksted": 160,
}

    ref_tek17 = TEK17_REF.get(kategori)
    alt_tek17 = TEK17_ALT.get(kategori)

    # beregn differanse mot TEK17
    spes = sp  # du har allerede beregnet sp = arsforbruk / areal
    diff = spes - ref_tek17 if ref_tek17 else 0
    diff_pct = (diff / ref_tek17) * 100 if ref_tek17 else 0

    farge = "#2e8b57" if diff <= 0 else ("#e6a700" if diff_pct < 10 else "#cc4444")
    vurdering = (
        "under TEK17-nivå – svært effektivt bygg" if diff <= 0 else
        "omtrent på nivå med TEK17" if diff_pct < 10 else
        "over TEK17-nivå – potensial for reduksjon"
    )

    st.markdown(
        f"""
        <div style='font-size:13px; color:#555; margin-top:2px;'>
            Referansenivå TEK17: <b>{ref_tek17} kWh/m²</b><br>
            <span style='color:{farge};'>{vurdering}</span>
        </div>
        <div style='font-size:11px; color:#777; margin-top:6px;'>
            Kilde: <a href="https://www.dibk.no/regelverk/byggteknisk-forskrift-tek17/14/14-2"
            target="_blank" style="color:#777; text-decoration:none;">
            TEK17 § 14-2 – Krav til energieffektivitet (energirammer)</a>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("<div style='height:35px;'></div>", unsafe_allow_html=True)

    title("Kalkulert energikarakter")
    st.markdown(
    f"<div style='display:inline-block;padding:.8rem 1.4rem;border-radius:1rem;"
    f"background:{badge_color};color:white;font-weight:900;font-size:40px;'>"
    f"{label}</div>",
    unsafe_allow_html=True
)

    st.markdown(
    """
    <div style='font-size:12.5px;color:#666;margin-top:4px;'>
       Denne bokstaven er en forenklet vurdering basert på faktisk forbruk. Den offisielle energikarakteren beregnes etter NS 3031 og kan avvike.
    </div>
    """,
    unsafe_allow_html=True
)


# ---------- HØYRE: formålsfordelt forbruk ----------
with right:
    # ---------- PIE: formålsfordelt forbruk ----------
    title("Energiforbruk formålsfordelt*")

    pct = SHARES[kategori].copy()

    # Korreksjoner (NVE 2016:24)
    note_text = None
    if kategori == "Forretningsbygning":
        pct["El.spesifikk"] += pct.get("Belysning", 0)
        pct["Belysning"] = 0
        note_text = "For <b>Forretningsbygning</b> er belysning inkludert i <b>El.spesifikk</b> (NVE 2016:24)."
    elif kategori == "Sykehus":
        pct["El.spesifikk"] += pct.get("Ventilasjon", 0) + pct.get("Belysning", 0)
        pct["Ventilasjon"] = 0
        pct["Belysning"] = 0
        note_text = "For <b>Sykehus</b> er ventilasjon og belysning inkludert i <b>El.spesifikk</b> (NVE 2016:24)."

    FORMAL_ORDER  = ["Oppvarming","Tappevann","Ventilasjon","Belysning","El.spesifikk","Kjøling"]
    FORMAL_COLORS = {
        "Oppvarming":"#33C831","Tappevann":"#097E3E","Ventilasjon":"#74D680",
        "Belysning":"#FFC107","El.spesifikk":"#2E7BB4","Kjøling":"#00ACC1"
    }

    def disp(name: str) -> str:
        if name == "El.spesifikk" and kategori == "Forretningsbygning":
            return "El.spesifikk (inkl. belysning)"
        if name == "El.spesifikk" and kategori == "Sykehus":
            return "El.spesifikk (inkl. ventilasjon og belysning)"
        return name

    ordered      = [(k, pct[k]) for k in FORMAL_ORDER if k in pct and pct[k] > 0]
    pie_values   = [arsforbruk * (v/100) for _, v in ordered]
    pie_labels   = [f"{disp(k)}\n{fmt_int(val)} kWh" for k, val in zip([k for k,_ in ordered], pie_values)]
    pie_colors   = [FORMAL_COLORS[k] for k,_ in ordered]

    fig_pie, ax_pie = plt.subplots(figsize=(5.2, 4.8))
    ax_pie.pie(pie_values, labels=pie_labels, colors=pie_colors,
               autopct=lambda p: f"{p:.1f}%", startangle=90, counterclock=False)
    ax_pie.axis("equal")

    buf_pie = io.BytesIO()
    fig_pie.savefig(buf_pie, format="png", bbox_inches="tight", dpi=160)
    buf_pie.seek(0)
    st.image(buf_pie, width=580)

    st.markdown(
        f"<div style='font-size:12px;color:#666;margin-top:6px;'>* {note_text if note_text else 'Kategorier følger NVE 2016:24.'}</div>",
        unsafe_allow_html=True
    )

    # Litt luft mellom figurene
    st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)

    # ---------- BAR: referanse vs. bygg ----------
    title("Energibruk pr. m² BRA (referanse vs. bygg)")

    cols = REF["labels"] + ["AKTUELT BYGG"]
    vals = REF[kategori] + [sp]

    fig_bar, ax_bar = plt.subplots(figsize=(4.6, 2.3))
    bar_colors = [BAR_LIGHT] * (len(vals)-1) + [BAR_DARK]
    bars = ax_bar.bar(cols, vals, color=bar_colors, width=0.55)

    ax_bar.set_ylabel("kWh/m² BRA", fontsize=10, color=PRIMARY, labelpad=4)
    ax_bar.set_ylim(0, max(vals)*1.25)
    ax_bar.spines["top"].set_visible(False)
    ax_bar.spines["right"].set_visible(False)

    for t in ax_bar.get_xticklabels():
        t.set_rotation(20)
        t.set_ha("right")

    for b, v in zip(bars, vals):
        ax_bar.text(b.get_x()+b.get_width()/2, v+3, f"{v:.1f}",
                    ha="center", va="bottom", fontsize=8, color=PRIMARY)

    # Fremhev "AKTUELT BYGG" uten kantlinje
    bars[-1].set_linewidth(0)
    bars[-1].set_alpha(0.95)

    buf_bar = io.BytesIO()
    fig_bar.savefig(buf_bar, format="png", bbox_inches="tight", dpi=200)
    buf_bar.seek(0)
    st.image(buf_bar, width=480)


# ---------- KILDER ----------
with st.expander("Kilder og forutsetninger", expanded=False):
    st.markdown("""
    - **Formålsdeling:** NVE Rapport 2016:24  
    - **Referanseverdier pr m² / tiltak:** Enova (veiledere og kunnskapsartikler)  
    - **Energikarakter:** Enova – Karakterskalaen  
    """)




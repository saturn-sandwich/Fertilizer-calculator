import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import curve_fit

# ── 0. PAGE CONFIGURATION ──────────────────────────────────────────────────
# This must be the first Streamlit command. It sets the browser tab title and layout.
st.set_page_config(
    page_title="Optimizare Fertilizare Azot",
    page_icon="🌱",
    layout="wide"
)

# Custom CSS to make the metrics look a bit punchier
st.markdown("""
    <style>
    [data-testid="stMetricValue"] { font-size: 1.8rem; color: #2E7D32; }
    </style>
    """, unsafe_allow_html=True)

# ── 1. DATA & LOGIC ──────────────────────────────────────────────────────────

def mitscherlich(x, A, b):
    return A * (1 - np.exp(-b * x))

raw_data = {
    ("N organic", False): {"x": np.array([0, 30, 100, 170]), "y": np.array([9.81, 11.59, 16.38, 16.69])},
    ("N organic", True): {"x": np.array([0, 30, 100, 170]), "y": np.array([9.14, 11.76, 15.59, 16.96])},
    ("N organo-mineral", False): {"x": np.array([0, 30, 100, 170]), "y": np.array([9.81, 10.93, 14.02, 15.87])},
    ("N organo-mineral", True): {"x": np.array([0, 30, 100, 170]), "y": np.array([9.14, 11.19, 14.28, 14.66])},
    ("N mineral", False): {"x": np.array([0, 30, 100, 170]), "y": np.array([9.81, 10.38, 11.68, 12.17])},
    ("N mineral", True): {"x": np.array([0, 30, 100, 170]), "y": np.array([9.14, 9.89, 11.50, 11.09])},
}

@st.cache_data
def fit_all_curves(_raw_data):
    params = {}
    for key, data in _raw_data.items():
        baseline = data["y"][0]
        y_adjusted = data["y"] - baseline
        popt, _ = curve_fit(mitscherlich, data["x"], y_adjusted, p0=[10, 0.02])
        params[key] = {"A": popt[0], "b": popt[1]}
    return params

params = fit_all_curves(raw_data)

# ── 2. HEADER ────────────────────────────────────────────────────────────────
st.markdown("<h1 style='color: #2E7D32;'>Simulator de răspuns al producției de masă verde la fertilizant</h1>", unsafe_allow_html=True)
st.markdown("""
<p style='font-size: 24px;'>Acest instrument utilizează <b>Ecuația Mitscherlich</b> pentru a modela producția de masă verde în funcție de aportul de azot.
Alegeți varianta de fertilizare din stânga și ajustați parametrii pentru a vedea rezultatele.
""", unsafe_allow_html=True)

# ── 3. INPUTS (SIDEBAR) ──────────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Setări experiment")
    fertilization_type = st.selectbox(
        "Tip fertilizare",
        ["N mineral", "N organo-mineral", "N organic"]
    )
    amended = st.toggle("Aplicare amendamente", value=False)
    
    st.divider()
    st.header("📊 Parametri de calcul")
    n_input = st.slider("Cantitate N aplicată (kg/ha)", 0, 170, 30)

# Computing variables
A = params[(fertilization_type, amended)]["A"]
b = params[(fertilization_type, amended)]["b"]
y_control = raw_data[(fertilization_type, amended)]["y"][0]
y_dot = y_control + A * (1 - np.exp(-b * n_input))

# ── 4. MAIN LAYOUT ──────────────────────────────────────────────────────────
col1, col2 = st.columns([1, 2], gap="large")

with col1:
    st.subheader("📌 Rezultate estimări")
    
    # Using a container for a grouped look
    with st.container(border=True):
        st.metric("Producție estimată", f"{y_dot:.2f} t/ha", delta=f"{y_dot - y_control:.2f} t/ha")
        st.caption("Diferența indică sporul de producție față de varianta martor.")

    st.write("---")
    
    st.subheader("🎯 Calcul invers")
    y_target = st.number_input("Introdu producția dorită (t/ha)", min_value=0.0, value=12.0, step=0.5)
    
    if y_target <= y_control:
        st.info(f"Producția de {y_control:.2f} t/ha este atinsă natural (fără N).")
    elif y_target >= y_control + A:
        st.error(f"Limita biologică este {y_control + A:.2f} t/ha.")
    else:
        n_needed = -np.log(1 - (y_target - y_control) / A) / b
        if n_needed > 170:
            st.warning(f"Necesită {n_needed:.1f} kg N/ha (Depășește limita de 170 kg/ha).")
        else:
            st.success(f"Necesar azot: **{n_needed:.1f} kg/ha**")

with col2:
    # ── 5. IMPROVED GRAPH ────────────────────────────────────────────────────
    x_range = np.linspace(0, 180, 300)
    y_range = y_control + A * (1 - np.exp(-b * x_range))

    # Using a cleaner style
    plt.style.use('seaborn-v0_8-whitegrid')
    fig, ax = plt.subplots(figsize=(8, 5))
    
    # Plot the curve
    ax.plot(x_range, y_range, color="#2E7D32", linewidth=2.5, label="Curbă de răspuns")
    
    # Plot the current point
    ax.scatter([n_input], [y_dot], color="#D32F2F", s=100, zorder=5, label="Punct curent")
    
    # Labels and Titles
    ax.set_title(f"Răspunsul pentru {fertilization_type}", fontsize=14, pad=15)
    ax.set_xlabel("Azot aplicat (kg/ha)", fontsize=10)
    ax.set_ylabel("Producție (t/ha)", fontsize=10)
    
    # Clean up the spines (borders)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    # Legend and layout
    ax.legend()
    plt.tight_layout()
    
    st.pyplot(fig)

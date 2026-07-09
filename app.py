import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="SPD Coordination Simulator", layout="wide")

st.title("⚡ Multi-Stage SPD Energy Coordination Simulator")
st.markdown("""
Visualizing the cascading effect of transient overvoltage and the impact of installation lead length based on **$V = L \cdot \\frac{di}{dt}$**.
""")

# --- USER INPUTS (SIDEBAR OR COLUMNS) ---
st.sidebar.header("⚙️ Simulation Parameters")

surge_source = st.sidebar.radio(
    "Surge Source:",
    ("External Lightning (10/350 µs)", "Internal Switching (8/20 µs)")
)

st.sidebar.markdown("---")
st.sidebar.subheader("Select SPD Layers")

stage1_spd = st.sidebar.selectbox("Stage 1 (Service Entrance):", ["None", "Type 1 SPD (Up: 4.0kV)", "Type 1+2 SPD (Up: 1.5kV)"])
stage2_spd = st.sidebar.selectbox("Stage 2 (Distribution Panel):", ["None", "Type 2 SPD (Up: 2.5kV)"])
stage3_spd = st.sidebar.selectbox("Stage 3 (Sensitive Load):", ["None", "Type 3 SPD (Up: 1.5kV)"])

lead_length = st.sidebar.slider("Lead Length per SPD (meters):", 0.0, 1.5, 0.5, 0.1)

# --- PHYSICS & CALCULATION ENGINE ---
# Base parameters
if "Lightning" in surge_source:
    initial_voltage = 40.0 # kV
    di_dt = 10.0 # kA/us
else:
    initial_voltage = 6.0 # kV
    di_dt = 1.0 # kA/us

# Inductive voltage drop: V = L * di/dt (Assuming 1uH/m inductance)
lead_voltage_drop = lead_length * 1.0 * di_dt 

# Stage 1 Calculation
v1 = initial_voltage
if stage1_spd == "Type 1 SPD (Up: 4.0kV)":
    v1 = 4.0 + lead_voltage_drop
elif stage1_spd == "Type 1+2 SPD (Up: 1.5kV)":
    v1 = 1.5 + lead_voltage_drop

# Stage 2 Calculation
v2 = v1
if stage2_spd == "Type 2 SPD (Up: 2.5kV)":
    if "Lightning" in surge_source and stage1_spd == "None":
        st.error("⚠️ Warning: Type 2 SPD is absorbing direct lightning energy without upstream protection. High risk of degradation!")
    # Clamps the voltage if the incoming voltage is higher than its protective level
    clamping_voltage = 2.5 + lead_voltage_drop
    v2 = min(v1, clamping_voltage)

# Stage 3 Calculation
v3 = v2
device_failure = False

if stage3_spd == "Type 3 SPD (Up: 1.5kV)":
    if "Lightning" in surge_source and stage1_spd == "None" and stage2_spd == "None":
        device_failure = True
        st.error("💥 CATASTROPHIC FAILURE: Type 3 SPD destroyed. Cannot handle bulk lightning energy!")
        v3 = v2 # Fails to protect
    else:
        clamping_voltage = 1.5 + lead_voltage_drop
        v3 = min(v2, clamping_voltage)

# --- VISUALIZATION (PLOTLY) ---
stages = ["Source", "Stage 1 (Origin)", "Stage 2 (Panel)", "Stage 3 (Load)"]
voltages = [initial_voltage, v1, v2, v3]

fig = go.Figure(data=[
    go.Bar(
        x=stages, 
        y=voltages,
        marker_color=['#ef4444', '#f97316', '#eab308', '#22c55e' if not device_failure else '#000000'],
        text=[f"{v:.1f} kV" for v in voltages],
        textposition='auto'
    )
])

fig.update_layout(
    title="Residual Voltage Cascade (kV)",
    yaxis_title="Voltage (kV)",
    template="plotly_white",
    height=400
)

st.plotly_chart(fig, use_container_width=True)

# --- FINAL RESULTS ANALYSIS ---
st.markdown("### 📊 Protection Status")
safe_threshold = 1.5 # kV

if device_failure:
    st.error("❌ **Result:** Equipment Destroyed. Upstream energy coordination is missing.")
elif v3 <= safe_threshold:
    st.success(f"✅ **Result:** System Protected! Final residual voltage is {v3:.1f} kV (Safe for sensitive electronics).")
else:
    st.warning(f"⚠️ **Result:** Equipment at Risk. Final residual voltage is {v3:.1f} kV (Exceeds 1.5kV threshold). Try adding downstream SPDs or shortening lead lengths.")

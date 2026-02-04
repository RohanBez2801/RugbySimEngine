import random
import statistics
from dataclasses import dataclass, field
from typing import List, Dict, Callable
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO

# ==========================================
# 1. CORE LOGIC & PHYSICS ENGINE
# ==========================================

class FieldZone:
    OWN_HALF = "Own Half (0-50m)"
    OPP_HALF = "Opp Half (50-22m)"
    RED_ZONE = "Red Zone (<22m)"

ZONE_MODIFIERS = {
    FieldZone.OWN_HALF: {"gain": 0.9, "risk": 0.9},
    FieldZone.OPP_HALF: {"gain": 1.0, "risk": 1.0},
    FieldZone.RED_ZONE: {"gain": 0.6, "risk": 1.4},
}

class DefenseSystem:
    DRIFT = "Drift Defense"
    BLITZ = "Blitz Defense"
    COMPRESSED = "Compressed/Heavy Ruck"

DEFENSE_LOGIC = {
    DefenseSystem.DRIFT: {
        "weakness": "Power Pod", "strength": "Edge Sweep", "risk_mod": 0.8
    },
    DefenseSystem.BLITZ: {
        "weakness": "Tip On", "strength": "Out The Back", "risk_mod": 1.5
    },
    DefenseSystem.COMPRESSED: {
        "weakness": "Out The Back", "strength": "Power Pod", "risk_mod": 1.1
    }
}

class Source:
    OPEN_PLAY = "Open Play / Turnover"
    SCRUM = "Scrum (Stable Platform)"
    LINEOUT = "Lineout (Stable Platform)"

@dataclass
class Archetype:
    name: str
    carry_bonus: float
    decision_bonus: float

ARCHETYPES = {
    "Power 12": Archetype("Power 12", 1.3, 1.0),
    "Playmaker 10": Archetype("Playmaker 10", 0.9, 1.3),
    "Edge Finisher": Archetype("Edge Finisher", 1.2, 1.1),
    "Forward Pod": Archetype("Forward Pod", 1.1, 0.9),
}

@dataclass
class Player:
    name: str
    archetype: Archetype

@dataclass
class GameState:
    zone: str
    defense_type: str
    ruck_speed: str
    source: str
    phase: int = 1
    meters_gained: float = 0.0
    turnover: bool = False

@dataclass
class ShapeMove:
    name: str
    risk: float
    base_gain: float

    def execute(self, state: GameState, carrier: Player):
        # 1. Context Modifiers
        zone_mod = ZONE_MODIFIERS[state.zone]
        ruck_mult = {"quick": 1.2, "normal": 1.0, "slow": 0.7}[state.ruck_speed]
        
        # 2. Defense Interaction
        def_stats = DEFENSE_LOGIC[state.defense_type]
        def_mod = 1.0
        
        if self.name == def_stats["weakness"]:
            def_mod = 1.3 
        elif self.name == def_stats["strength"]:
            def_mod = 0.7
            state.turnover = True if random.random() < 0.4 else False

        # 3. Source Bonus (Set Piece Platform)
        # Structured plays (Scrum/Lineout) are 20% safer on first phase
        source_safety = 1.0
        if state.source in [Source.SCRUM, Source.LINEOUT] and state.phase == 1:
            source_safety = 0.8 # Reduces risk

        # 4. Calculate Gain
        gain = (
            self.base_gain * ruck_mult * carrier.archetype.carry_bonus * zone_mod["gain"] * def_mod
        )
        gain *= random.uniform(0.8, 1.2)
        state.meters_gained += max(0, gain)

        # 5. Calculate Risk
        error_prob = self.risk * zone_mod["risk"] * def_stats["risk_mod"] * source_safety
        error_prob /= carrier.archetype.decision_bonus

        if random.random() < error_prob:
            state.turnover = True

# ==========================================
# 2. VISUALIZATION ENGINE
# ==========================================

def draw_pitch_outcome(start_meters, gain, move_name, turnover):
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.set_facecolor('#2E8B57')
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 50)
    
    lines = [0, 22, 50, 78, 100]
    for line in lines:
        ax.axvline(x=line, color='white', linestyle='-', alpha=0.7)
    
    ax.text(50, 2, "Halfway", color='white', ha='center', alpha=0.8)
    ax.text(22, 2, "22m", color='white', ha='center', alpha=0.8)
    
    end_point = start_meters + gain
    color = 'red' if turnover else 'yellow'
    
    ax.arrow(start_meters, 25, gain, 0, head_width=2, head_length=2, fc=color, ec=color, width=0.5)
    ax.plot(start_meters, 25, 'bo', markersize=10)
    
    if turnover:
        ax.text(end_point, 28, "❌ TURNOVER", color='white', fontweight='bold')
    else:
        ax.plot(end_point, 25, 'wo', markersize=10)
        ax.text(end_point, 28, f"+{gain:.1f}m", color='white', fontweight='bold')

    ax.set_yticks([])
    ax.set_title(f"Simulation: {move_name}", color='black')
    return fig

# ==========================================
# 3. DASHBOARD INTERFACE
# ==========================================

SHAPES = {
    "Power Pod": ShapeMove("Power Pod", 0.10, 3.5),
    "Tip On": ShapeMove("Tip On", 0.15, 4.8),
    "Out The Back": ShapeMove("Out The Back", 0.25, 7.5),
    "Screen Play": ShapeMove("Screen Play", 0.20, 6.4),
    "Edge Sweep": ShapeMove("Edge Sweep", 0.18, 5.8),
}

st.set_page_config(page_title="Rugby Tactical Engine V3", layout="wide")

st.title("🏉 Elite Rugby Tactical Engine V3")
st.markdown("### Intelligent Decision Support & Visualizer")

# --- SIDEBAR ---
st.sidebar.header("1. Match Context")
source_input = st.sidebar.selectbox("Possession Source", [Source.OPEN_PLAY, Source.SCRUM, Source.LINEOUT])
zone_input = st.sidebar.selectbox("Field Position", [FieldZone.OWN_HALF, FieldZone.OPP_HALF, FieldZone.RED_ZONE])
ruck_input = st.sidebar.select_slider("Ruck Speed", options=["slow", "normal", "quick"], value="normal")

st.sidebar.header("2. Opposition")
defense_input = st.sidebar.selectbox("Defense System", [DefenseSystem.DRIFT, DefenseSystem.BLITZ, DefenseSystem.COMPRESSED])

st.sidebar.header("3. Attack Setup")
p_archetype = st.sidebar.selectbox("Ball Carrier", list(ARCHETYPES.keys()))

# --- LOGIC ---
def run_simulation(move_name, iterations=50):
    gains = []
    turnovers = 0
    player = Player("Carrier", ARCHETYPES[p_archetype])
    for _ in range(iterations):
        state = GameState(zone_input, defense_input, ruck_input, source_input)
        SHAPES[move_name].execute(state, player)
        gains.append(state.meters_gained)
        if state.turnover: turnovers += 1
    return statistics.mean(gains), (turnovers/iterations)*100

col1, col2 = st.columns([1, 1])

# --- PANEL 1: AI MATRIX ---
with col1:
    st.subheader("🤖 AI Tactical Matrix")
    
    if st.button("Analyze All Options"):
        results = []
        progress = st.progress(0)
        
        for i, (name, move) in enumerate(SHAPES.items()):
            avg_gain, risk = run_simulation(name, iterations=100)
            utility = avg_gain - (risk * 0.15)
            results.append({"Move": name, "Gain": avg_gain, "Risk": risk, "Score": utility})
            progress.progress((i + 1) / len(SHAPES))
            
        df = pd.DataFrame(results).sort_values("Score", ascending=False)
        best = df.iloc[0]
        
        st.success(f"🏆 RECOMMENDATION: **{best['Move']}**")
        st.dataframe(df.style.highlight_max(axis=0, subset=['Gain', 'Score'], color='lightgreen'))
        
        # --- NEW: EXPORT REPORT ---
        report_text = f"TACTICAL REPORT\n"
        report_text += f"Scenario: {source_input} in {zone_input}\n"
        report_text += f"Defense: {defense_input}\n"
        report_text += f"Top Recommendation: {best['Move']} (Exp. Gain: {best['Gain']:.1f}m)\n\n"
        report_text += "FULL DATA:\n" + df.to_string()
        
        st.download_button(
            label="📄 Download Match Plan",
            data=report_text,
            file_name="match_plan.txt",
            mime="text/plain"
        )

# --- PANEL 2: VISUAL SIMULATOR ---
with col2:
    st.subheader("📺 Visual Simulator")
    selected_visual = st.selectbox("Select Move to Visualize", list(SHAPES.keys()))
    
    if st.button(f"Run {selected_visual}"):
        player = Player("Carrier", ARCHETYPES[p_archetype])
        state = GameState(zone_input, defense_input, ruck_input, source_input)
        SHAPES[selected_visual].execute(state, player)
        
        start_m = 20 if zone_input == FieldZone.OWN_HALF else 60 if zone_input == FieldZone.OPP_HALF else 85
        fig = draw_pitch_outcome(start_m, state.meters_gained, selected_visual, state.turnover)
        st.pyplot(fig)
        
        if state.turnover:
            st.error("Possession Lost!")
        else:
            st.caption(f"Gain: +{state.meters_gained:.2f}m")
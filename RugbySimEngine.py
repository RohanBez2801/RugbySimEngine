import random
import statistics
from dataclasses import dataclass, field
from typing import List, Dict, Callable
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

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
    drill_name: str
    drill_desc: str
    video_url: str  # <--- NEW: Video Link Field

    def execute(self, state: GameState, carrier: Player):
        zone_mod = ZONE_MODIFIERS[state.zone]
        ruck_mult = {"quick": 1.2, "normal": 1.0, "slow": 0.7}[state.ruck_speed]
        
        def_stats = DEFENSE_LOGIC[state.defense_type]
        def_mod = 1.0
        
        if self.name == def_stats["weakness"]:
            def_mod = 1.3 
        elif self.name == def_stats["strength"]:
            def_mod = 0.7
            state.turnover = True if random.random() < 0.4 else False

        source_safety = 1.0
        if state.source in [Source.SCRUM, Source.LINEOUT] and state.phase == 1:
            source_safety = 0.8 

        gain = (
            self.base_gain * ruck_mult * carrier.archetype.carry_bonus * zone_mod["gain"] * def_mod
        )
        gain *= random.uniform(0.8, 1.2)
        state.meters_gained += max(0, gain)

        error_prob = self.risk * zone_mod["risk"] * def_stats["risk_mod"] * source_safety
        error_prob /= carrier.archetype.decision_bonus

        if random.random() < error_prob:
            state.turnover = True

# ==========================================
# 2. INTERACTIVE VISUALIZATION
# ==========================================

def create_interactive_pitch(start_meters, gain, move_name, turnover):
    fig = go.Figure()

    fig.add_shape(type="rect", x0=0, y0=0, x1=100, y1=50,
        line=dict(color="white", width=2), fillcolor="#2E8B57", layer="below")

    for x_line in [0, 22, 50, 78, 100]:
        fig.add_shape(type="line", x0=x_line, y0=0, x1=x_line, y1=50,
            line=dict(color="white", width=2, dash="dash"))
    
    fig.add_annotation(x=50, y=2, text="Halfway", showarrow=False, font=dict(color="white"))
    fig.add_annotation(x=22, y=2, text="22m", showarrow=False, font=dict(color="white"))

    end_point = start_meters + gain
    arrow_color = "red" if turnover else "yellow"
    
    fig.add_annotation(
        x=end_point, y=25, ax=start_meters, ay=25,
        xref="x", yref="y", axref="x", ayref="y",
        arrowhead=2, arrowwidth=4, arrowcolor=arrow_color,
        text=f"+{gain:.1f}m" if not turnover else "TURNOVER",
        font=dict(size=14, color="white", family="Arial Black"),
        bgcolor="black"
    )

    fig.add_trace(go.Scatter(
        x=[start_meters], y=[25],
        mode='markers+text',
        marker=dict(size=15, color='blue', line=dict(width=2, color='white')),
        text=["Ruck"], textposition="top center",
        name="Start"
    ))

    fig.update_layout(
        title=f"Simulation: {move_name}",
        xaxis=dict(range=[-5, 105], showgrid=False, zeroline=False, visible=False, fixedrange=False),
        yaxis=dict(range=[0, 50], showgrid=False, zeroline=False, visible=False),
        height=300,
        margin=dict(l=10, r=10, t=40, b=10),
        plot_bgcolor="rgba(0,0,0,0)",
        dragmode="pan"
    )
    return fig

# ==========================================
# 3. DATA & VIDEOS
# ==========================================

SHAPES = {
    "Power Pod": ShapeMove(
        "Power Pod", 0.10, 3.5, 
        "2v1 Contact Box", 
        "Set up a 5m square. 2 Defenders with pads vs 3 Attackers. Aim is to win the collision line.",
        "https://www.youtube.com/watch?v=3JDPoVFQNu4" # Pod work drill
    ),
    "Tip On": ShapeMove(
        "Tip On", 0.15, 4.8, 
        "Square Drill - Late Pass", 
        "First receiver commits the defender and passes LATE (just before contact) to the short runner.",
        "https://www.youtube.com/shorts/9IQOqVD7DLA" # 2v1 High Tempo drill
    ),
    "Out The Back": ShapeMove(
        "Out The Back", 0.25, 7.5, 
        "L-Shape Wave Passing", 
        "Use 3 groups of 3. Ball starts at one end. Middle man creates the 'back door' option.",
        "https://www.youtube.com/shorts/BSBupzALOKg" # The user's specific request
    ),
    "Screen Play": ShapeMove(
        "Screen Play", 0.20, 6.4, 
        "Blocker & Slider", 
        "Front runner runs a hard line to 'block' (legally) the drift defense, while the 10 slides behind.",
        "https://www.youtube.com/watch?v=WBHeYJtrpVA" # Screen pass analysis
    ),
    "Edge Sweep": ShapeMove(
        "Edge Sweep", 0.18, 5.8, 
        "Touchline Sprint 2v1", 
        "Use the 15m channel. Winger and Fullback vs 1 Defender. Practice preserving space.",
        "https://www.youtube.com/shorts/OqzahAKVBII" # Edge attack drill
    ),
}

# ==========================================
# 4. DASHBOARD
# ==========================================

st.set_page_config(page_title="Rugby Tactical Engine", layout="wide")

st.title("🏉 Elite Rugby Tactical Engine")
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

# --- PANEL 1: AI MATRIX & VIDEO ---
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
        best_row = df.iloc[0]
        best_move_name = best_row['Move']
        best_move_data = SHAPES[best_move_name]
        
        st.success(f"🏆 RECOMMENDATION: **{best_move_name}**")
        st.dataframe(df[['Move', 'Gain', 'Risk', 'Score']].style.highlight_max(axis=0, subset=['Gain', 'Score'], color='lightgreen'))
        
        # --- NEW: VIDEO PLAYER ---
        st.info(f"👨‍🏫 **Coaching Focus: {best_move_name}**")
        st.write(f"**Drill:** {best_move_data.drill_name}")
        st.write(f"**Description:** {best_move_data.drill_desc}")
        
        st.markdown("---")
        st.markdown("**📺 Watch Drill Video:**")
        st.video(best_move_data.video_url)

# --- PANEL 2: INTERACTIVE VISUAL SIMULATOR ---
with col2:
    st.subheader("📺 Visual Simulator")
    selected_visual = st.selectbox("Select Move to Visualize", list(SHAPES.keys()))
    
    if st.button(f"Run {selected_visual}"):
        player = Player("Carrier", ARCHETYPES[p_archetype])
        state = GameState(zone_input, defense_input, ruck_input, source_input)
        SHAPES[selected_visual].execute(state, player)
        
        start_m = 20 if zone_input == FieldZone.OWN_HALF else 60 if zone_input == FieldZone.OPP_HALF else 85
        
        fig = create_interactive_pitch(start_m, state.meters_gained, selected_visual, state.turnover)
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        
        if state.turnover:
            st.error("Possession Lost!")
        else:
            st.success(f"Gain: +{state.meters_gained:.2f}m")
import random
import statistics
from dataclasses import dataclass, field
from typing import List, Dict, Optional
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# ==========================================
# 1. NEW: COMPETITION & DEFENSE MODELS
# ==========================================

class CompetitionLevel:
    U15 = "U15 School"
    U18 = "U18 Academy"
    SENIOR = "Senior Club"
    PRO = "Professional"

# How the level affects the game physics
LEVEL_TUNING = {
    CompetitionLevel.U15: {"speed_mod": 0.8, "error_margin": 1.3, "fatigue": 0.9},
    CompetitionLevel.U18: {"speed_mod": 0.9, "error_margin": 1.1, "fatigue": 1.0},
    CompetitionLevel.SENIOR: {"speed_mod": 1.0, "error_margin": 1.0, "fatigue": 1.1},
    CompetitionLevel.PRO: {"speed_mod": 1.2, "error_margin": 0.7, "fatigue": 1.3},
}

@dataclass
class DefensiveProfile:
    name: str
    line_speed: float  # Multiplier for risk
    bite_prob: float   # Chance they over-commit (creating space)
    width_hold: float  # How well they cover the edge

DEFENSE_SYSTEMS = {
    "Drift": DefensiveProfile("Drift", 0.9, 0.25, 0.8),
    "Blitz": DefensiveProfile("Blitz", 1.3, 0.75, 0.2), # High speed, high bite (risky but aggressive)
    "Compressed": DefensiveProfile("Compressed", 1.1, 0.4, 0.9),
}

# ==========================================
# 2. CORE LOGIC & PLAYBOOK STRUCTURES
# ==========================================

@dataclass
class PlayerKPI:
    role: str
    target: str

@dataclass
class ShapeMove:
    name: str
    risk: float
    base_gain: float
    drill_name: str
    drill_desc: str
    video_url: str
    kpis: Dict[int, List[PlayerKPI]] = field(default_factory=dict) # NEW: Jersey specific goals

@dataclass
class PhaseNode:
    phase: int
    move_name: str
    # Logic: If Defense does X -> We go to Node Y
    triggers: Dict[str, str] 

class FieldZone:
    OWN_HALF = "Own Half"
    OPP_HALF = "Opp Half"
    RED_ZONE = "Red Zone"

ZONE_MODIFIERS = {
    FieldZone.OWN_HALF: {"gain": 0.9, "risk": 0.9},
    FieldZone.OPP_HALF: {"gain": 1.0, "risk": 1.0},
    FieldZone.RED_ZONE: {"gain": 0.6, "risk": 1.4},
}

# ==========================================
# 3. THE PLAYBOOK DATABASE (MERGED)
# ==========================================

SHAPES = {
    "Power Pod": ShapeMove(
        "Power Pod", 0.10, 3.5, 
        "2v1 Contact Box", "Set up a 5m square. Aim to win the collision line.",
        "https://www.youtube.com/watch?v=3JDPoVFQNu4",
        kpis={
            12: [PlayerKPI("Carrier", "Dominant Collision > 1m")],
            9: [PlayerKPI("Scrumhalf", "Pass speed < 0.8s")]
        }
    ),
    "Tip On": ShapeMove(
        "Tip On", 0.15, 4.8, 
        "Square Drill - Late Pass", "First receiver passes LATE (just before contact).",
        "https://www.youtube.com/shorts/9IQOqVD7DLA",
        kpis={
            10: [PlayerKPI("First Receiver", "Fix defender hips square")],
            12: [PlayerKPI("Tip Runner", "Change of angle pre-catch")]
        }
    ),
    "Out The Back": ShapeMove(
        "Out The Back", 0.25, 7.5, 
        "L-Shape Wave Passing", "Middle man creates the 'back door' option.",
        "https://www.youtube.com/shorts/BSBupzALOKg",
        kpis={
            10: [PlayerKPI("Playmaker", "Look inside before passing out")],
            15: [PlayerKPI("Second Receiver", "Depth > 3m from gainline")]
        }
    ),
    "Edge Sweep": ShapeMove(
        "Edge Sweep", 0.18, 5.8, 
        "Touchline Sprint 2v1", "Preserve space on the outside.",
        "https://www.youtube.com/shorts/OqzahAKVBII",
        kpis={
            11: [PlayerKPI("Winger", "Stay wide until ball release")],
            15: [PlayerKPI("Fullback", "Call play early")]
        }
    ),
}

# A predefined Decision Tree for the "Playbook" tab
ATTACK_TREE = {
    "start": PhaseNode(1, "Power Pod", {"Defense Narrows": "wide", "Defense Drifts": "tight"}),
    "wide": PhaseNode(2, "Out The Back", {"Winger Bites": "edge", "Winger Drifts": "cutback"}),
    "tight": PhaseNode(2, "Tip On", {"Gap Opens": "break", "Contact Made": "recycle"}),
    "edge": PhaseNode(3, "Edge Sweep", {}),
}

# ==========================================
# 4. SIMULATION ENGINE
# ==========================================

def run_simulation(move_name, zone, defense_name, level_name, iterations=50):
    move = SHAPES[move_name]
    defense = DEFENSE_SYSTEMS[defense_name]
    level_stats = LEVEL_TUNING[level_name]
    
    gains = []
    turnovers = 0
    
    for _ in range(iterations):
        # Physics Calculation
        zone_mod = ZONE_MODIFIERS[zone]
        
        # Defense Interaction (New Logic)
        def_impact = 1.0
        # If Blitz (high line speed), wide moves are riskier but shorter moves gain more if successful
        if defense.line_speed > 1.1 and "Wide" in move.name:
            def_impact = 0.6 # Blitz kills wide play
        elif defense.name == "Drift" and "Pod" in move.name:
            def_impact = 0.8 # Drift absorbs power
            
        # Level Impact
        # Pro level means tighter margins (higher risk) but faster execution (more gain)
        level_gain_bonus = level_stats["speed_mod"]
        
        # Final Gain Calc
        gain = (move.base_gain * zone_mod["gain"] * def_impact * level_gain_bonus)
        gain *= random.uniform(0.8, 1.2)
        
        # Risk Calc
        risk_threshold = move.risk * zone_mod["risk"] * defense.line_speed / level_stats["error_margin"]
        
        if random.random() < risk_threshold:
            turnovers += 1
            gains.append(0)
        else:
            gains.append(max(0, gain))
            
    return statistics.mean(gains), (turnovers/iterations)*100

def create_interactive_pitch(gain, move_name, turnover):
    fig = go.Figure()
    # Green Pitch
    fig.add_shape(type="rect", x0=0, y0=0, x1=100, y1=50, line=dict(color="white"), fillcolor="#2E8B57", layer="below")
    # Lines
    for x in [0, 22, 50, 78, 100]:
        fig.add_shape(type="line", x0=x, y0=0, x1=x, y1=50, line=dict(color="white", dash="dash"))
    
    start_m = 50 # Simplified start for visualization
    end_m = start_m + gain
    color = "red" if turnover else "yellow"
    
    # Arrow
    fig.add_annotation(x=end_m, y=25, ax=start_m, ay=25, xref="x", yref="y", axref="x", ayref="y",
                       arrowhead=2, arrowwidth=4, arrowcolor=color,
                       text=f"+{gain:.1f}m" if not turnover else "TURNOVER",
                       font=dict(size=14, color="white"), bgcolor="black")
    
    fig.update_layout(xaxis=dict(visible=False, range=[0,100]), yaxis=dict(visible=False, range=[0,50]), 
                      margin=dict(l=0,r=0,t=0,b=0), height=250, plot_bgcolor="rgba(0,0,0,0)")
    return fig

# ==========================================
# 5. UI INTERFACE (STREAMLIT)
# ==========================================

st.set_page_config(page_title="Universal Rugby Platform", layout="wide")
st.title("🏉 Universal Coaching Platform V6")

# --- SIDEBAR CONFIG ---
st.sidebar.header("Match Configuration")
level_input = st.sidebar.selectbox("Competition Level", list(LEVEL_TUNING.keys()), index=2)
st.sidebar.caption(f"Physics Mode: {level_input}")

# --- TABS FOR DIFFERENT MODES ---
tab1, tab2, tab3 = st.tabs(["🎮 Simulator", "📖 Digital Playbook", "📝 Game Review"])

# --- TAB 1: SIMULATOR (The V5 Tool) ---
with tab1:
    col1, col2 = st.columns([1,1])
    
    with col1:
        st.subheader("Predictive Engine")
        zone_in = st.selectbox("Zone", list(ZONE_MODIFIERS.keys()))
        def_in = st.selectbox("Opponent Defense", list(DEFENSE_SYSTEMS.keys()))
        
        if st.button("Run Prediction"):
            results = []
            for name in SHAPES.keys():
                avg, risk = run_simulation(name, zone_in, def_in, level_input)
                # Smart Score
                score = avg - (risk * 0.2)
                results.append({"Move": name, "Gain": avg, "Risk": risk, "Score": score})
            
            df = pd.DataFrame(results).sort_values("Score", ascending=False)
            best = df.iloc[0]
            
            st.success(f"Best Call: **{best['Move']}**")
            st.dataframe(df[['Move', 'Gain', 'Risk']].style.format("{:.1f}"))
            
            # Show Video for Best Move
            st.markdown("---")
            st.video(SHAPES[best['Move']].video_url)

    with col2:
        st.subheader("Visualizer")
        move_to_viz = st.selectbox("Select Move", list(SHAPES.keys()))
        if st.button(f"Visualize {move_to_viz}"):
            avg, risk = run_simulation(move_to_viz, zone_in, def_in, level_input)
            is_turnover = random.random() < (risk/100)
            fig = create_interactive_pitch(avg, move_to_viz, is_turnover)
            st.plotly_chart(fig, use_container_width=True)
            
            # Show KPIs
            st.info("🎯 **Player KPIs for this move:**")
            kpis = SHAPES[move_to_viz].kpis
            for num, goals in kpis.items():
                for g in goals:
                    st.write(f"**#{num} ({g.role}):** {g.target}")

# --- TAB 2: DIGITAL PLAYBOOK (Phase Trees) ---
with tab2:
    st.header("Phase Decision Trees")
    st.markdown("Structure your attack based on triggers, not just memorization.")
    
    col_a, col_b = st.columns(2)
    
    with col_a:
        st.subheader("Phase 1: Setup")
        st.markdown(f"**Call: {ATTACK_TREE['start'].move_name}**")
        trigger = st.radio("What did the defense do?", list(ATTACK_TREE['start'].triggers.keys()))
        
    with col_b:
        st.subheader("Phase 2: Reaction")
        next_key = ATTACK_TREE['start'].triggers[trigger]
        next_node = ATTACK_TREE[next_key]
        st.markdown(f"**Call: {next_node.move_name}**")
        
        if next_node.triggers:
            st.write("Next Triggers:")
            for t, k in next_node.triggers.items():
                st.write(f"- If {t} -> Go to Phase 3")
        else:
            st.success("✅ Line Break / Try Time")

# --- TAB 3: GAME REVIEW (Validation Mode) ---
with tab3:
    st.header("Post-Match Validator")
    st.write("Input a scenario from Saturday's game to see if the decision aligned with the system.")
    
    with st.form("review_form"):
        r_phase = st.number_input("Phase Number", 1, 10)
        r_call = st.selectbox("Call Made", list(SHAPES.keys()))
        r_def = st.selectbox("Defense Seen", ["Drift", "Blitz", "Narrow"])
        r_outcome = st.selectbox("Outcome", ["Gainline", "Turnover", "Clean Break"])
        
        submitted = st.form_submit_button("Analyze Decision")
        
        if submitted:
            st.divider()
            # Simple Logic Check
            if r_def == "Blitz" and "Wide" in r_call:
                st.error("❌ **Tactical Mismatch:** Running Wide against a Blitz is high risk. Recommended: Short/Tip On.")
            elif r_def == "Drift" and "Pod" in r_call:
                 st.warning("⚠️ **Inefficient:** Pods into a Drift defense often stall. Better to attack the edge.")
            else:
                st.success("✅ **Good Decision:** The call matched the defensive profile.")
            
            st.caption(f"Logged Event: Phase {r_phase} | {r_call} vs {r_def}")


import random
import statistics
from dataclasses import dataclass, field
from typing import List, Dict, Callable
import streamlit as st
import pandas as pd

# ==========================================
# CORE LOGIC (UNCHANGED)
# ==========================================

class FieldZone:
    OWN_HALF = "own_half"
    OPP_HALF = "opp_half"
    RED_ZONE = "red_zone"

ZONE_MODIFIERS = {
    FieldZone.OWN_HALF: {"gain": 0.9, "risk": 0.9},
    FieldZone.OPP_HALF: {"gain": 1.0, "risk": 1.0},
    FieldZone.RED_ZONE: {"gain": 0.6, "risk": 1.4},
}

PHASE_DECAY_START = 4

@dataclass
class Archetype:
    name: str
    carry_bonus: float
    distribution_bonus: float
    collision_resistance: float
    decision_bonus: float

ARCHETYPES = {
    "power_12": Archetype("Power 12", 1.3, 0.9, 1.3, 1.0),
    "playmaker_10": Archetype("Playmaker 10", 0.9, 1.4, 0.9, 1.3),
    "edge_finisher": Archetype("Edge Finisher", 1.2, 0.8, 1.0, 1.1),
    "workhorse_cleaner": Archetype("Cleaner", 1.0, 0.8, 1.4, 0.9),
}

@dataclass
class Player:
    name: str
    archetype: Archetype
    stamina: float = 100.0

    def fatigue(self, amount: float):
        self.stamina = max(0, self.stamina - amount)

@dataclass
class Team:
    name: str
    players: List[Player]

@dataclass
class Ruck:
    speed: str = "quick"

@dataclass
class Ball:
    carrier: Player

@dataclass
class GameState:
    attack: Team
    defense: Team
    ball: Ball
    zone: str = FieldZone.OPP_HALF
    phase: int = 1
    meters: float = 0.0
    turnover: bool = False
    ruck: Ruck = field(default_factory=Ruck)

@dataclass
class ShapeMove:
    name: str
    risk: float
    base_gain: float

    def execute(self, state: GameState):
        carrier = state.ball.carrier
        
        # Physics calculations
        decay = 1.0
        if state.phase >= PHASE_DECAY_START:
            decay -= 0.1 * (state.phase - PHASE_DECAY_START + 1)

        zone_mod = ZONE_MODIFIERS[state.zone]
        ruck_mult = {"quick": 1.2, "normal": 1.0, "slow": 0.7}[state.ruck.speed]

        # Calculate Gain
        gain = (
            self.base_gain * decay * ruck_mult * carrier.archetype.carry_bonus * zone_mod["gain"]
        )
        gain *= random.uniform(0.8, 1.2)
        state.meters += max(0, gain)

        # Calculate Risk
        error = self.risk * zone_mod["risk"]
        error /= carrier.archetype.decision_bonus

        if random.random() < error:
            state.turnover = True

        # Update Game State
        if state.meters > 50: state.zone = FieldZone.RED_ZONE
        
        roll = random.random()
        state.ruck.speed = "quick" if roll > 0.6 else "normal" if roll > 0.25 else "slow"
        state.phase += 1

class RugbySimulator:
    def __init__(self, moves: Dict[str, ShapeMove]):
        self.moves = moves

    def simulate(self, state: GameState, plan: List[str]):
        for name in plan:
            if state.turnover: break
            self.moves[name].execute(state)
        return state

class Recommender:
    def __init__(self, simulator: RugbySimulator):
        self.sim = simulator

    def recommend(self, state_factory: Callable[[], GameState], candidates: List[str], runs=200):
        scores = {}
        for move in candidates:
            meters = []
            turnovers = 0
            for _ in range(runs):
                state = state_factory()
                end = self.sim.simulate(state, [move])
                meters.append(end.meters)
                if end.turnover: turnovers += 1
            
            avg_meters = statistics.mean(meters)
            risk_pct = (turnovers / runs) * 100
            # A simple "Utility Score": Meters minus penalty for high risk
            scores[move] = {"avg_meters": avg_meters, "risk": risk_pct}
        return scores

# ==========================================
# DASHBOARD INTERFACE (STREAMLIT)
# ==========================================

# 1. Setup Data
SHAPES = {
    "Power Pod": ShapeMove("Power Pod", 0.15, 4.2),
    "Tip On": ShapeMove("Tip On", 0.18, 4.8),
    "Out The Back": ShapeMove("Out The Back", 0.25, 7.0),
    "Screen Play": ShapeMove("Screen Play", 0.22, 6.4),
    "Edge Sweep": ShapeMove("Edge Sweep", 0.18, 6.6),
}

# 2. Sidebar Controls
st.set_page_config(page_title="Rugby Tactical Engine", layout="wide")
st.sidebar.title("🏉 Match Context")

st.sidebar.subheader("Field State")
zone_input = st.sidebar.selectbox("Current Zone", [FieldZone.OWN_HALF, FieldZone.OPP_HALF, FieldZone.RED_ZONE])
ruck_input = st.sidebar.select_slider("Ball Speed", options=["slow", "normal", "quick"], value="normal")

st.sidebar.subheader("Key Player Stats")
p_archetype = st.sidebar.selectbox("Ball Carrier Type", list(ARCHETYPES.keys()))
p_form = st.sidebar.slider("Player Form (Carry Bonus)", 0.8, 1.5, ARCHETYPES[p_archetype].carry_bonus)

# 3. Main Helper to create state
def create_current_state():
    # Update the archetype with the slider value
    base_arch = ARCHETYPES[p_archetype]
    modified_arch = Archetype(base_arch.name, p_form, base_arch.distribution_bonus, base_arch.collision_resistance, base_arch.decision_bonus)
    
    player = Player("Carrier", modified_arch)
    ball = Ball(player)
    ruck = Ruck(ruck_input)
    return GameState(Team("Att", [player]), Team("Def", []), ball, zone=zone_input, ruck=ruck)

# 4. Main Page Layout
st.title("Elite Rugby Tactical Engine")
st.markdown("### AI-Powered Decision Support System")

col1, col2 = st.columns(2)

# --- PANEL 1: SINGLE PLAY SIMULATOR ---
with col1:
    st.info("🧪 Single Play Simulator")
    selected_move = st.selectbox("Select a Move to Test", list(SHAPES.keys()))
    
    if st.button("Run Simulation (50 times)"):
        sim = RugbySimulator(SHAPES)
        results = []
        turnovers = 0
        
        for _ in range(50):
            st_state = create_current_state()
            outcome = sim.simulate(st_state, [selected_move])
            results.append(outcome.meters)
            if outcome.turnover: turnovers += 1
            
        avg = statistics.mean(results)
        st.metric(label=f"Avg Gain ({selected_move})", value=f"{avg:.2f}m", delta=f"{turnovers/50*100:.0f}% Risk")
        st.success(f"Simulated 50 runs. Max gain: {max(results):.1f}m")

# --- PANEL 2: AI RECOMMENDER ---
with col2:
    st.warning("🤖 AI Assistant Coach")
    st.write("Ask the engine to scan all moves and recommend the best option for this specific field position.")
    
    if st.button("Find Best Play"):
        sim = RugbySimulator(SHAPES)
        rec = Recommender(sim)
        
        with st.spinner("Running Monte Carlo Simulations..."):
            scores = rec.recommend(create_current_state, list(SHAPES.keys()))
        
        # Convert to DataFrame for chart
        data = []
        for name, stats in scores.items():
            data.append({"Move": name, "Meters": stats["avg_meters"], "Risk": stats["risk"]})
        
        df = pd.DataFrame(data).set_index("Move")
        
        # Find winner
        best_move = df["Meters"].idxmax()
        
        st.subheader(f"Recommended: **{best_move}**")
        st.bar_chart(df["Meters"])
        st.table(df)
# 🏉 Elite Rugby Union Tactical Engine

### AI-Powered Decision Support System for Rugby Union

The **Elite Rugby Union Tactical Engine** is a sophisticated simulation tool designed to assist coaches and analysts in making data-driven tactical decisions. By utilizing **Monte Carlo simulations**, the engine models the physics of a rugby match—including field position, player fatigue, momentum, and risk—to predict the outcome of specific offensive shapes.

## 🚀 Features

### 1. Match Context Modeling
The engine doesn't just guess; it adapts to the specific reality of the match moment:
* **Field Zones:** Adjusts risk/reward ratios based on territory (Own Half, Opp Half, Red Zone).
* **Momentum (Ruck Speed):** Models the critical impact of "Quick Ball" (1.2x gain) vs. "Slow Ball" (0.7x gain).
* **Phase Decay:** Simulates the "law of diminishing returns" as attack phases extend beyond 4+, modeling defense reorganization.

### 2. Player Archetypes
Customizable player profiles that influence the success of specific moves:
* **Power 12:** High collision dominance (e.g., for "Power Pods").
* **Playmaker 10:** High distribution and decision-making skills (e.g., for "Screen Plays").
* **Edge Finisher:** Speed and finishing ability.

### 3. The AI Assistant Coach
* **Monte Carlo Simulation:** Runs 50-300 iterations of a play in milliseconds to determine statistical probability.
* **Best Next Play Recommender:** Automatically scans the entire playbook and identifies the move with the highest "Utility Score" (Maximum Meters Gained - Risk Penalty).

---

## 🛠️ Installation & Setup

### Prerequisites
* **Python 3.8+** must be installed on your system.

### 1. Install Dependencies
Open your terminal (or Command Prompt) and run the following command to install the required visualization libraries:

```bash
pip install streamlit pandas

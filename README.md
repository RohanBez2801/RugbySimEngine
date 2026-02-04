Here is a professional `README.md` file tailored for your project. You can copy and paste this text directly into a new file named `README.md` in your project folder.

This documentation is written to help both you (the developer) and your brother (the user) understand how to install, run, and interpret the application.

---

```markdown
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

```

### 2. Run the Application

Navigate to the project folder in your terminal and execute:

```bash
streamlit run RugbySimEngine.py

```

*Note: This will automatically open the dashboard in your default web browser.*

---

## 📖 User Guide

### The Dashboard Interface

#### 1. Left Sidebar: Match Context

Use this panel to "set the scene" before running a simulation.

* **Current Zone:** Where is the ball? (Red Zone = higher turnover risk, compressed defense).
* **Ball Speed:** How quick was the ruck? (Quick ball massively increases potential gains).
* **Player Stats:** Adjust the form of your key ball carrier.

#### 2. Single Play Simulator (Testing Lab)

* **Goal:** Test a specific hunch (e.g., "Is a 'Tip On' safe to run on our own 5m line?").
* **Action:** Select a move and click "Run Simulation."
* **Output:** Shows the average meters gained and the calculated risk percentage based on 50 simulated attempts.

#### 3. AI Assistant Coach (Recommender)

* **Goal:** Ask the computer for the optimal strategy.
* **Action:** Click "Find Best Play."
* **Output:** The system runs hundreds of simulations for *every* move in the playbook and produces a ranked bar chart showing the most effective options for the current game state.

---

## 🧠 The Math Behind the Engine

The simulator uses a probabilistic model defined by the following logic:

* **Variance:** A random noise factor (0.8 to 1.2) is applied to every single run to mimic the unpredictability of live sport.
* **Risk Calculation:** The probability of a turnover is weighed against the ball carrier's `Decision Bonus`. A "Playmaker" is less likely to knock on during a complex move than a "Power" player.

---

## 🔮 Future Roadmap

* [ ] **Visual Field:** Graphical representation of the pitch showing the gain line.
* [ ] **Defensive Systems:** Add a selector for "Blitz", "Drift", or "Soft" defenses to counter specific shapes.
* [ ] **Set Piece:** Modeling outcomes from Scrums and Lineouts.
* [ ] **PDF Export:** Save simulation reports for post-match analysis.

---

## License

This project is open for educational and analytical use.

```

```

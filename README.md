# NBA Salary Audit V19: The Sniper Factor 🏀📊

This project provides a comprehensive data-driven audit of NBA salaries. By crossing real-time statistics from the `nba_api` with current contract data, it calculates a custom **Value Score** to categorize players into five distinct financial tiers.

## 🚀 The Final Formula

Unlike traditional box-score metrics, the **Score V19** weights efficiency, team impact, and spacing value:

$$SCORE = (PIE \times 100) + REL\_NET + (TS\% - 0.58) \times 100 + (USG\% \times 20) + \text{Sniper Factor}$$

### Key Components:
* **PIE (Player Impact Estimate):** Overall statistical floor.
* **REL_NET (Relative Net Rating):** How much better the team is when the player is on the court vs. on the bench.
* **TS% (True Shooting):** Efficiency benchmarked against the league average (0.58).
* **Sniper Factor:** A custom bonus/penalty based on 3PT volume and accuracy:
    $$\text{Sniper Factor} = (3P\% - 0.36) \times \text{3P Attempts/Game} \times 15$$

## 📂 Contract Categorization

The algorithm automatically flags contracts into 5 tiers:
1.  **Elite:** Max salaries with historic production (e.g., Jokić, Giannis).
2.  **Bargains (Max ROI):** Low-cost or rookie contracts with high-impact output.
3.  **Toxic Contracts:** High usage and high salary with negative team impact.
4.  **Silent Killers (Albatross):** High-paid role players who actively decrease team efficiency.
5.  **Fading Stars:** High-salary players with declining efficiency or "empty" stats.

## 🛠️ Tech Stack
* **Python 3.x**
* **nba_api:** Real-time stats fetching.
* **Pandas & NumPy:** Data wrangling and normalization.
* **Matplotlib & Seaborn:** Professional data visualization.
* **Difflib & Unicodedata:** Advanced fuzzy name-matching for disparate data sources.

## 📊 Visualizations
The tool generates automated high-resolution plots for data storytelling:
* **Salary vs. Performance Scatter:** Mapping the ROI landscape of the league.
* **ROI Contrast Bars:** Top 10 vs. Bottom 10 value comparison.
* **3PT Impact Analysis:** Visualizing the weight of the "Sniper Factor".

---
*Developed by Jose Santana*

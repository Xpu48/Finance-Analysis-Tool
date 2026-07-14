# Lab Note: Real-Time Risk Simulation Engine
> Status: Experimental Prototyping (Production-Ready Backend Core)

This repository serves as an active sandbox for exploring high-performance quantitative finance mechanics. It interfaces directly with live market feeds to run real-time multi-variable stress-testing models via a lightweight web GUI.

---

## Technical Stack (The Sandbox)
* Mathematical Core: NumPy (Matrix Vectorization), Pandas (Time-Series Alignment), SciPy (Statistical Curves)
* Streaming Protocol: Yahoo Finance API (yfinance)
* Persistence Layer: SQLite3 (Local ACID-compliant staging engine)
* Interface Layer: Streamlit and Plotly (Interactive data rendering)

---

## Core Engineering Experiments

### 1. The Data Lineage and Alignment Dilemma
When compiling a multi-asset matrix from raw API endpoints, localized market closures and timezone mismatches create structural data gaps (NaN). Running standard drops would obliterate entire trading days across the portfolio. 
* The Fix: Implemented a pre-merge timestamp sanitization loop combined with an active .ffill().bfill() data interpolation matrix strategy to keep the 5-year pipeline unified.

### 2. Algorithmic Data Governance
To prevent local data corruption while maintaining historical tracking, the persistence layer utilizes a compound Primary Key (ticker, date). 
* Staging Layer: Incoming streams are isolated inside an ACID-compliant temporary SQL table (temp_staging), processed through an INSERT OR IGNORE pipeline, and logged to an independent data_governance_log audit trail for compliance verification.

### 3. Mitigating Mathematical Drift in Crash Modeling
Standard Monte Carlo simulations rely heavily on historical drift parameters, which completely fails to account for black-swan liquidity freezes or infrastructure collapses.
* The Fix: Introduced an active Systemic Stress Drag to the Geometric Brownian Motion logic, introducing an artificial annual macroeconomic drag (e.g., 20%) scaled linearly across 252 trading days (0.20 / 252) to project extreme market drawdowns.

---

## Spin Up the Environment

1. Isolate the environment:
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```
2. Ingest the dependency tree:
   ```powershell
   pip install -r requirements.txt
   ```
3. Launch the sandbox UI:
   ```powershell
   streamlit run gui_app.py
   ```

# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

BuildingPulse is a Python ML project that predicts a building's **Energy Use Intensity (EUI)** — kBTU/sqft/year — from physical characteristics (type, size, age, location). The goal is to flag buildings that consume more energy than similar buildings as retrofit priorities, motivated by NYC Local Law 97 carbon caps.

- **ML Task:** Regression (predict Site EUI)
- **Primary Metric:** R² (variance explained)
- **Secondary Metric:** RMSE in kBTU/sqft
- **Primary Dataset:** NYC LL84 Energy and Water Data Disclosure (~35K properties/year)

## Setup

```bash
pip install pandas numpy matplotlib seaborn scikit-learn jupyterlab
```

Optional serving dependencies: `fastapi`, `streamlit`, `joblib`.

## Architecture

The project follows a 4-phase ML workflow:

1. **Exploration** — Load NYC LL84 CSV, inspect distributions, correlations, outliers
2. **Baseline** — Clean data, one-hot encode property types, train plain LinearRegression, record baseline R²/RMSE
3. **Primary Model** — Feature engineering (building age, log-transform EUI, interaction terms, borough), compare Ridge/Lasso with cross-validation
4. **Iteration** — Residual analysis, polynomial features, multi-city generalization

**Key modeling decisions:**
- Target (Site EUI) is right-skewed → use `np.log1p()` transform, `np.expm1()` to invert
- Categorical features (property type, borough) → one-hot encoding
- Regularization via Ridge (L2) and Lasso (L1) to handle many one-hot columns
- Outlier removal: EUI > 1000 or < 1 are likely data errors

## Deployment Path

- Model persistence via `joblib.dump()`/`joblib.load()`
- Serving options: batch script, FastAPI REST API, or Streamlit dashboard

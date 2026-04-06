# BuildingPulse — Complete Project Plan

## What BuildingPulse Is

A model that predicts a building's **Energy Use Intensity (EUI)** — kBTU per square foot per year — from its physical characteristics. Buildings that consume more energy than similar buildings should are flagged as retrofit priorities. With NYC Local Law 97 imposing carbon caps on large buildings, owners face real fines — BuildingPulse tells them how bad it is and what to fix.

**Domain:** Energy / Climate Policy
**ML Task:** Regression (predict Site EUI from building characteristics)
**Primary Metric:** R² (variance explained)
**Secondary Metric:** RMSE in kBTU/sqft (directly interpretable)

---

## The Problem

Buildings account for 40% of US energy consumption. Every building in New York City over 25,000 sqft must report its annual energy consumption under Local Law 84. The data is public.

If you can predict EUI from building type, age, and size alone, you can flag buildings that use *more* energy than similar buildings — those are the ones where retrofits will have the highest impact.

---

## Dataset

### Primary: NYC LL84 Energy and Water Data Disclosure
- **Source:** https://data.cityofnewyork.us — search "Energy and Water Data Disclosure for Local Law 84"
- **Size:** ~35,000 properties per year
- **Format:** CSV, single download
- **Key columns:**
  - Property Type (Office, Multifamily, Retail, Hotel, Hospital, etc.)
  - Gross Floor Area (sqft)
  - Year Built
  - Number of Buildings
  - Site EUI (kBTU/sqft — **the target**)
  - Source EUI
  - Electricity Use (kWh)
  - Natural Gas Use (therms)
  - ENERGY STAR Score
  - GHG Emissions (metric tons CO2e)
  - Weather Normalized EUI

### Starter Alternative (ultra-clean, for first day): UCI Energy Efficiency Dataset
- **Source:** https://archive.ics.uci.edu/dataset/242/energy+efficiency
- **Size:** 768 samples, 8 features
- **Features:** Relative Compactness, Surface Area, Wall Area, Roof Area, Overall Height, Orientation, Glazing Area, Glazing Area Distribution
- **Targets:** Heating Load, Cooling Load

### Stretch (multi-city):
- Chicago Energy Benchmarking: https://data.cityofchicago.org
- Seattle Building Energy: https://data.seattle.gov
- San Francisco: https://datasf.org
- ASHRAE Kaggle: https://www.kaggle.com/c/ashrae-energy-prediction

---

## ML Task Definition

**Input features:**
- Property type (categorical: Office, Multifamily Housing, Hotel, etc.)
- Gross floor area (continuous, sqft)
- Year built (continuous — derive building age)
- Number of buildings on the property (integer)
- Borough (categorical: Manhattan, Brooklyn, etc.)

**Target:** Site EUI (kBTU/sqft/year) — continuous

---

## Evaluation Criteria

| Level | R² | RMSE (kBTU/sqft) | What it means |
|-------|-----|-------------------|---------------|
| Beginner | > 0.30 | < 120 | Model beats guessing the average |
| Good | > 0.50 | < 90 | Captures the main drivers (building type, size) |
| Excellent | > 0.65 | < 70 | Strong feature engineering, regularization working |

---

## Prerequisites

- Python: comfortable with functions, loops, lists, dicts
- Libraries: `pandas`, `numpy`, `matplotlib`, `seaborn`, `scikit-learn`, `jupyterlab`
- No prior ML or statistics knowledge required

```bash
pip install pandas numpy matplotlib seaborn scikit-learn jupyterlab
```

---

## Foundations — What You Need to Know First

### The Equation

```
y_hat = w1*x1 + w2*x2 + ... + wn*xn + b
```

| Symbol | Name | What it means |
|--------|------|---------------|
| `y_hat` | y-hat | The model's prediction (e.g., predicted energy use) |
| `x1, x2, ... xn` | Features | Input values for one observation (e.g., sqft=50000, floors=3, year_built=1985) |
| `w1, w2, ... wn` | Weights (coefficients) | How much each feature matters. Learned from data. |
| `b` | Bias (intercept) | The prediction when all features are zero |

### Loss Function — Mean Squared Error (MSE)

```
MSE = (1/m) * SUM( (yi - y_hat_i)^2 )
```

For every data point, calculate how far off the prediction is. Square it (so negatives become positive and big misses get amplified). Average all the squared errors. The model finds weights that make MSE as small as possible.

**Real-life analogy:** You're playing darts. MSE is the average squared distance from the bullseye across all throws. A lower score = a better player. Squaring penalizes big misses disproportionately — a prediction off by 200 kBTU is much worse than two predictions each off by 100 kBTU.

### How the Model Learns

**Method 1 — Normal Equation (exact, fast for small data):**
```
w = (X^T X)^-1 X^T y
```
Scikit-learn does this for you. It's why linear regression trains instantly.

**Method 2 — Gradient Descent (the universal method):**
```
wj <- wj - alpha * (dMSE/dwj)
```

**Analogy:** Blindfolded in a hilly landscape. You can't see the valley bottom. But you can feel the slope under your feet. You take a step downhill. Feel the slope again. Step again. The learning rate (alpha) controls step size — too big = overshoot, too small = takes forever.

Gradient descent is the algorithm that trains neural networks, transformers, GPT — everything. Learning it here prepares you for all of it.

### Train/Test Split

Split your data before training:
- **Training set (80%):** Model learns from this
- **Test set (20%):** Evaluate on this. Model has never seen these rows.

**Analogy:** Memorizing practice exam answers vs. actually learning the subject. High training score + low test score = overfitting (memorized, didn't learn).

### R-Squared (R²)

```
R² = 1 - (model's errors) / (baseline errors)
```

Where baseline = "just guess the average every time." R² = 0.65 means your model explains 65% of the variation in building energy use. The remaining 35% is explained by things you don't have data for (HVAC type, occupancy hours, tenant behavior).

### Regularization

When you have many features, the model can overfit. Regularization penalizes large weights.

**Ridge (L2):** `Loss = MSE + lambda * SUM(wj^2)` — shrinks all weights, keeps everything.
**Lasso (L1):** `Loss = MSE + lambda * SUM(|wj|)` — can push weights to exactly zero (automatic feature selection).

**Analogy:** Packing for a trip. Ridge = bring everything but pack light. Lasso = strict carry-on only, leave non-essentials behind.

### Feature Engineering

Raw data is rarely the best input. Transforming features often matters more than the model you choose:

- **Log transform:** Compresses skewed targets (energy use has many small values, few huge ones)
- **Interaction terms:** `sqft * floors` captures effects neither feature captures alone
- **Polynomial features:** `sqft^2` captures non-linear relationships
- **One-hot encoding:** Convert categories ("Office", "Hospital") into binary columns

---

## Implementation — 4 Phases

### Phase 1: Exploration (Day 1)

1. Download NYC LL84 data (most recent year)
2. Load with pandas. Check shape, dtypes, missing values
3. Look at the target distribution: `df['Site EUI (kBtu/ft²)'].hist()` — it will be skewed (log-transform will help)
4. Check correlations: `df[numeric_cols].corr()` — which features correlate with EUI?
5. Visualize: scatter plots of EUI vs sqft, EUI vs year_built. Box plots of EUI by property_type.
6. Key questions to answer:
   - How many property types are there? Which have the highest/lowest median EUI?
   - Is there a relationship between building age and energy use?
   - Are there obvious outliers? (A building with EUI of 5,000 is probably a data entry error)

### Phase 2: Baseline (Day 2)

1. **Clean:** Remove rows with missing EUI. Drop obvious outliers (EUI > 1000 or < 1). Handle missing features.
2. **Encode:** One-hot encode Property Type. Keep sqft and year_built as-is.
3. **Split:** 80/20 train/test split
4. **Train a plain linear regression:**
   ```python
   from sklearn.linear_model import LinearRegression
   from sklearn.metrics import mean_squared_error, r2_score

   model = LinearRegression()
   model.fit(X_train, y_train)
   y_pred = model.predict(X_test)

   print(f"R²: {r2_score(y_test, y_pred):.3f}")
   print(f"RMSE: {mean_squared_error(y_test, y_pred, squared=False):.1f}")
   ```
5. **Interpret coefficients:** `pd.Series(model.coef_, index=feature_names).sort_values()` — which features have the largest positive/negative weights?
6. Record your baseline R² and RMSE. This is what you'll improve on.

### Phase 3: Primary Model (Days 3-4)

1. **Feature engineering:**
   - Building age: `current_year - year_built`
   - Log-transform the target: `np.log1p(eui)` — often improves R² significantly for skewed targets
   - Interaction: `sqft * num_buildings` (campus-style properties behave differently)
   - Borough as a feature (location affects energy use — Manhattan differs from outer boroughs)
2. **Try Ridge and Lasso:**
   ```python
   from sklearn.linear_model import Ridge, Lasso
   from sklearn.model_selection import cross_val_score

   for alpha in [0.01, 0.1, 1.0, 10.0, 100.0]:
       ridge = Ridge(alpha=alpha)
       scores = cross_val_score(ridge, X_train, y_train, cv=5, scoring='r2')
       print(f"Ridge alpha={alpha}: R² = {scores.mean():.3f} +/- {scores.std():.3f}")
   ```
3. **Lasso for feature selection:** Check which features Lasso zeros out. These are noise.
4. **Compare:** Plain LR vs Ridge vs Lasso. Which gives best test R²?

### Phase 4: Iteration (Day 5)

1. **Residual analysis:** Plot `y_test - y_pred` vs `y_pred`. Is there a pattern? (Curved residuals = non-linear relationship you're missing)
2. **Residuals by property type:** Which building types does the model get wrong most? Maybe hospitals need a separate model.
3. **Add polynomial features:** `sqft^2`, `age^2` — does this improve R²?
4. **Try multi-city:** Download Chicago or Seattle benchmarking data. Does a model trained on NYC generalize to Chicago? (Probably not perfectly — climate differences. This teaches domain shift.)
5. **Final report:** Your best model, its R², its top-5 most important features, and what they mean for energy policy.

---

## Teaching Approach — Real Life First, Math Second

Each concept has a real-world analogy. The analogy comes first; the equation is a precise description of something you already intuitively understand.

| Concept | Real-Life Analogy |
|---------|-------------------|
| What is a model? | Walking into a restaurant and predicting the bill from the neighborhood, decor, and crowd |
| Features & weights | Estimating commute time — time of day (heavy weight), weather (moderate), day of week (light) |
| Loss function (MSE) | Playing darts — average distance from the bullseye |
| Gradient descent | Blindfolded on a hill, feeling the slope, stepping downhill |
| Overfitting | Memorizing practice exam answers vs. actually learning the subject |
| Regularization | Packing a suitcase with a weight limit |
| R² | Percentage of a pie chart you can explain |
| Interaction terms | Rain alone is manageable, darkness alone is manageable, rain AND darkness together is multiplicatively worse |
| One-hot encoding | Airport departure board: JFK=Yes, LAX=No, ORD=No |
| Coefficient interpretation | Salary negotiation: "$80K base + $5K per year of experience + $10K for a master's degree" |
| Residual analysis | Doctor checking which patients didn't respond to treatment |
| Ridge vs Lasso | Gentle tree pruning (Ridge) vs aggressive branch cutting (Lasso) |

---

## What You Learn from This Project

| Concept | How it shows up |
|---------|----------------|
| Features & target | Building characteristics -> energy use |
| Train/test split | 80/20 split, evaluate on unseen buildings |
| Loss function (MSE) | What the model minimizes |
| R² interpretation | "My model explains X% of energy use variation" |
| Coefficient interpretation | "Hospitals use Y more kBTU/sqft than offices, all else equal" |
| Log transform | Handling skewed EUI distribution |
| One-hot encoding | Converting building type categories to numbers |
| Regularization | Ridge/Lasso to prevent overfitting with many building types |
| Feature engineering | Building age, interactions, polynomials |
| Residual analysis | Finding where the model fails and why |

---

## Deployment — Notebook to Production

### Save the Model

```python
import joblib
joblib.dump(model, 'energy_model.pkl')
joblib.dump(scaler, 'scaler.pkl')  # if you used feature scaling
```

### Build a Prediction Function

```python
def predict_eui(building_type: str, sqft: float, year_built: int, floors: int) -> float:
    """Predict Energy Use Intensity for a building."""
    features = encode_features(building_type, sqft, year_built, floors)
    log_eui = model.predict([features])[0]
    return np.expm1(log_eui)
```

### Serving Options

| Option | Best For | Stack |
|--------|----------|-------|
| **Script** | Batch predictions (score all buildings once/year) | Python script on CSV |
| **REST API** | Real-time predictions, integrations | FastAPI or Flask |
| **Dashboard** | Demo, learning, stakeholder-facing | Streamlit |

**FastAPI example:**
```python
from fastapi import FastAPI
app = FastAPI()

@app.post("/predict")
def predict(building_type: str, sqft: float, year_built: int, floors: int):
    eui = predict_eui(building_type, sqft, year_built, floors)
    return {"predicted_eui": round(eui, 1)}
```

**Streamlit example:**
```python
import streamlit as st
building_type = st.selectbox("Building Type", ["Office", "Multifamily", "Hotel"])
sqft = st.number_input("Square Footage", value=50000)
# ... predict and display
```

### Monitoring & Retraining

- **Prediction drift:** Are predictions shifting systematically over time?
- **Feature drift:** Are incoming feature distributions changing?
- **Retrain cadence:** Annually, when new LL84 data drops
- **Don't worry about yet:** Kubernetes, Docker, MLflow, A/B testing, GPU inference

---

## Key scikit-learn Imports

```python
# Models
from sklearn.linear_model import LinearRegression, Ridge, Lasso, ElasticNet

# Preprocessing
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler, OneHotEncoder, PolynomialFeatures

# Metrics
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
```

---

## Resources

### Video
- **3Blue1Brown: Essence of Linear Algebra** — YouTube playlist. Makes linear algebra visual and intuitive.
- **StatQuest with Josh Starmer: Linear Regression** — Explains MSE, R², gradient descent with simple visuals.

### Textbook
- **An Introduction to Statistical Learning (ISLR)** — Free PDF at https://www.statlearning.com/. Chapter 3 covers linear regression. The gold standard for applied ML with minimal math prerequisites.

### Interactive
- **Kaggle Learn: Intro to Machine Learning** — Free, browser-based exercises with real datasets.

---

## Estimated Timeline

| Phase | Duration |
|-------|----------|
| Foundations (theory + intuition) | 3-5 days |
| Phase 1: Exploration | 1 day |
| Phase 2: Baseline | 1 day |
| Phase 3: Primary Model | 2 days |
| Phase 4: Iteration | 1 day |
| **Total** | **~2-3 weeks at ~2 hours/day** |

---

## What Comes After BuildingPulse

This is Project 1 of a 3-project linear regression learning path:

| # | Project | Data | Difficulty |
|---|---------|------|-----------|
| 1 | **BuildingPulse** (this) | NYC LL84 — 35K buildings | Beginner |
| 2 | Restaurant Health Inspections | Chicago Open Data — 250K inspections | Intermediate |
| 3 | Crop Yield Prediction | USDA + NOAA + Satellite — multi-source | Advanced |

After all 3: **logistic regression** (classification) -> **gradient boosting** -> **time-series** -> **deep learning** (CNNs for computer vision, transformers for NLP).


# Synthetic Data Generator — Malaysia‑tuned (Profiles & Transactions)

Generate **two synthetic datasets** using your Excel rules file `rule_to_observe.xlsx` (sheets: `requirement`, `profile_tbl`, `transaction_tbl`, `occu`, `state`).  
This generator produces realistic **customer profiles** and **transactions** with:

- 🇲🇾 **Malaysian counterparty names** (Malay/Chinese/Indian personal names plus local business styles)
- 💳 **Channel‑aware amounts** (P2P small, POS small, Credit Transfer mixed incl. salary)
- 📅 **Non‑uniform monthly activity** (30% high, 60% low, 10% sparse by default)
- 💰 **Balances linked to behaviour** and demographics (occupation, age, tenure, outflows)
- ⚙️ **Configurable flags** to tune realism without editing code

**Last updated:** 2025-09-25

---

## 1) Quick Start

```bash
# 1) Create & activate a virtual environment
python -m venv .venv          # or: python3 -m venv .venv
# Windows PowerShell:
.\.venv\Scripts\Activate.ps1
# macOS/Linux:
# source .venv/bin/activate

# 2) Install dependencies
pip install -r requirements.txt

# 3) Generate data (defaults preserve previous behaviour)
python generate_synth_data.py --rules rule_to_observe.xlsx --profiles 1000 --avg_txn 15 --seed 42 --outdir output
```

**Outputs** → `output/`  
- `CUSTOMER_PROFILE_YYYYMMDD.csv`  
- `CUSTOMER_TXN_YYYYMMDD.csv`

> Put `rule_to_observe.xlsx` next to the script or pass an absolute path to `--rules`.

---

## 2) How to run — examples (copy‑paste)

> Make sure your venv is active and requirements are installed.

### Example A — Baseline (defaults; previous behaviour)
**Windows PowerShell**
```powershell
python generate_synth_data.py --rules rule_to_observe.xlsx --profiles 1000 --avg_txn 15 --seed 42 --outdir output
```
**macOS/Linux**
```bash
python3 generate_synth_data.py --rules rule_to_observe.xlsx --profiles 1000 --avg_txn 15 --seed 42 --outdir output
```

### Example B — Retail‑like QR tickets (allow sub‑RM100 on QR channels)
**Windows PowerShell**
```powershell
python generate_synth_data.py --rules rule_to_observe.xlsx --profiles 1000 --avg_txn 15 --seed 42 --outdir output --txn_floor_qr 10
```
**macOS/Linux**
```bash
python3 generate_synth_data.py --rules rule_to_observe.xlsx --profiles 1000 --avg_txn 15 --seed 42 --outdir output --txn_floor_qr 10
```

### Example C — Busier portfolio + stronger mid‑life balances
(40% High activity, 50% Low, 10% Sparse; steeper age curve)
**Windows PowerShell**
```powershell
python generate_synth_data.py --rules rule_to_observe.xlsx --profiles 1000 --avg_txn 15 --seed 42 --outdir output --segment_split "40,50,10" --age_curve steeper
```
**macOS/Linux**
```bash
python3 generate_synth_data.py --rules rule_to_observe.xlsx --profiles 1000 --avg_txn 15 --seed 42 --outdir output --segment_split "40,50,10" --age_curve steeper
```
## more examples:

### Example 1: allow small QR tickets, keep default segments & age curve
```powershell
python generate_synth_data.py --rules rule_to_observe.xlsx --profiles 1000 --avg_txn 15 --seed 42 --outdir output --txn_floor_qr 10
```
### Example 2: more high-activity users, steeper age effect
```powershell
python generate_synth_data.py --rules rule_to_observe.xlsx --profiles 1000 --avg_txn 15 --seed 42 --outdir output --segment_split "40,50,10" --age_curve steeper
```
### Example 3: flatter age curve + small QR floor + different segment mix
```powershell
python generate_synth_data.py --rules rule_to_observe.xlsx --profiles 1000 --avg_txn 15 --seed 42 --outdir output --txn_floor_qr 5 --segment_split "25,65,10" --age_curve flatter
```
---

## 3) CLI Reference

| Flag | Default | Meaning |
|---|---:|---|
| `--rules PATH` | — | Path to your Excel rules. Reads **`occu`** & **`state`** as value lists. |
| `--profiles INT` | 1000 | Number of customers to generate. |
| `--avg_txn INT` | 15 | Kept for back‑compat; intensity now comes from monthly segments (see §6). |
| `--seed INT` | 42 | RNG seed for reproducibility. |
| `--outdir PATH` | `output` | Output folder for CSVs. |
| **`--txn_floor_qr FLOAT`** | **100.0** | **Min amount for QR channels** (QR P2P / QR POS / P2P‑like DuitNOW). Set to **10** or **5** for small retail tickets. |
| **`--segment_split "H,L,S"`** | **"30,60,10"** | Percent split of monthly activity: **High, Low, Sparse**. Any numbers accepted; normalized to 100. |
| **`--age_curve {base,steeper,flatter}`** | **base** | Strength of **age effect** on balances. `steeper` = bigger 40–55 hump; `flatter` = softer differences. |

---

## 4) Excel Rules & What’s Used

- **Required sheets for value lists**: `occu`, `state`  
  (every non‑empty cell is read as a candidate value)
- **Schema sheets**: `profile_tbl`, `transaction_tbl` can document your target columns and ranges; the generator already enforces the constraints listed below.  
- You can extend rules/columns by editing the script (functions `generate_profiles`, `generate_txns`, `compute_avg_balances`).

---

## 5) Data Model

### Profile CSV (`CUSTOMER_PROFILE_YYYYMMDD.csv`)

| No | Field | Type | Notes |
|---:|---|---|---|
| 1 | `Customer_ID` | string | Unique `CUST_...` |
| 2 | `Customer_Acc` | string | Unique `CACC_...` |
| 3 | `Age` | int | 10–99 |
| 4 | `Stated_Occupation` | string | From `occu` sheet (uppercased) |
| 5 | `Location_State` | string | From `state` sheet |
| 6 | `Account_Tenure_Months` | int | 5–240 |
| 7 | `Account_Type` | string | `CA` or `SA` |
| 8 | `Avg_Balance` | decimal(2) | Computed (see formula in §7) |

### Transaction CSV (`CUSTOMER_TXN_YYYYMMDD.csv`)

| No | Field | Type | Notes |
|---:|---|---|---|
| 1 | `Customer_Acc` | string | FK to profile |
| 2 | `Transaction_ID` | string | Unique `TXN_...` |
| 3 | `Timestamp` | ISO 8601 | Between **2024‑01‑01** and **2025‑09‑24** (UTC) |
| 4 | `Amount` | decimal(2) | Per‑channel distributions, clamped; QR floors via `--txn_floor_qr` |
| 5 | `Type` | string | **`credit` = outgoing**, **`debit` = incoming** (by design) |
| 6 | `Channel` | string | `{{QR P2P, DuitNOW, Credit Transfer, QR POS, Other}}` |
| 7 | `Counterparty_Name` | string | Malaysian personal or local business name |
| 8 | `Counterparty_Account` | string | `CACC_...` |

> **Referential integrity**: every transaction references a generated `Customer_Acc`.

---

## 6) Monthly Activity (non‑uniform)

Customers are segmented up front:

- **High (≈30%)** → λ ~ **4–10** transactions **per month** (Poisson per month)  
- **Low (≈60%)** → λ ~ **0.2–1.8** (many months with **0–2** txns)  
- **Sparse (≈10%)** → only **~5 ±2 txns per year**; many months are **0**

Tune with `--segment_split "H,L,S"` (we normalize automatically).

---

## 7) Balance Model (occupation, age, tenure, outflows)

Balances follow a life‑cycle + profession shape and react to outflows.

```
Avg_Balance
  = Base(AccountType) × TenureFactor × OccupationFactor × AgeFactor × (1 − 0.4 × OutflowRatio)
```

- **Base(AccountType)**: log‑normal; **SA** < **CA**.  
- **TenureFactor**: linear lift up to **+15%** at 240 months.  
- **OccupationFactor** (substring match on `Stated_Occupation`):  
  - Lucrative → **DOCTOR / DENTIST / SPECIALIST / LAWYER / ENGINEER / CONSULTANT → ×2.2**  
  - Mid → **TEACHER / LECTURER / NURSE / POLICE / CHEF / DRIVER / TECHNICIAN / EXECUTIVE / OFFICER / ADMIN / CLERK → ×1.0**  
  - Low → **CASHIER / FARMER / HOUSEWIFE / STUDENT / RETIREE / CLEANER / LABOUR / WORKER → ×0.75**
- **AgeFactor** (`--age_curve`):  
  - `base` (default): rises into **45–54**, softens after **55**.  
  - `steeper`: stronger mid‑life hump.  
  - `flatter`: softer differences.  
- **OutflowRatio** uses the convention **`credit` = OUT**; heavier outflows depress balances.

> If your downstream expects banking semantics where `credit` means **inflow**, swap the mapping in `sample_type_amount()`.

---

## 8) Amounts by Channel (realistic ranges)

- **QR POS**: small tickets; median ≈ **RM110**, p95 ≈ **RM260** (use `--txn_floor_qr` to allow sub‑RM100).  
- **QR P2P / DuitNOW (P2P‑like)**: low–mid; median ≈ **RM150–RM250**.  
- **DuitNOW (bill/merchant branch)**: median ≈ **RM250**, p95 up to ≈ **RM1,500**.  
- **Credit Transfer**: mix of **salary inflow** (median ≈ **RM3,000**) and outgoing bill/interbank (median ≈ **RM450–2,500**).  
- All channels are clamped to sensible minima/maxima.

---

## 9) Tuning Recipes

- **Truer retail QR tickets** → `--txn_floor_qr 10`  
- **Quiet dataset (many zeros)** → `--segment_split "15,70,15"`  
- **Wealthier portfolio** → `--segment_split "40,50,10" --age_curve steeper`  
- **Stress test high outflows** → keep defaults; balances fall for heavy `credit` totals

---

## 10) Project Structure

```
.
├─ generate_synth_data.py
├─ requirements.txt
├─ .gitignore
├─ rule_to_observe.xlsx         # your rules file (keep beside the script)
└─ output/
   ├─ CUSTOMER_PROFILE_YYYYMMDD.csv
   └─ CUSTOMER_TXN_YYYYMMDD.csv
```

---

## 11) Push to GitHub

1. Create an **empty** GitHub repo (no README).  
2. In your project folder:

```bash
git init
git add .
git commit -m "Initial commit: Malaysia-tuned synthetic data generator"
git branch -M main
git remote add origin https://github.com/<your-username>/synthetic-customer-data.git
git push -u origin main
```

> If the remote already has a README, run `git pull --rebase origin main` first or clone the repo and copy files in.

---

## 12) Reproducibility

- All randomness comes from **NumPy**’s Generator. Use `--seed` to reproduce exactly the same outputs given the same inputs/flags.  
- CSV filenames are date‑stamped in **UTC** (`YYYYMMDD`).

---

## 13) Troubleshooting

- **Excel not found** → pass absolute path to `--rules`.  
- **No values in `occu`/`state`** → we fall back to built‑ins; fill the sheets to control distributions.  
- **Amounts too large/small** → adjust `--txn_floor_qr` and/or edit the per‑channel medians/p95 in the script.  
- **Too many transactions** → tune `--segment_split` (e.g., increase `Sparse` or decrease `High`).

---

## 14) License

MIT (adjust as needed)

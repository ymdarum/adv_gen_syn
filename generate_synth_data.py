#!/usr/bin/env python3
import argparse, os, random, string, math
from datetime import datetime, timedelta, timezone
import pandas as pd
import numpy as np

# ---------- Malaysian names ----------
FIRST_NAMES = ["Adam","Aisyah","Aisha","Hana","Irfan","Nurul","Zara","Farid","Azlan","Siti","Ali","Fatimah","Amir","Syafiq","Liyana","Farah","Nadia","Aqil","Khalid","Hafiz","Amirah","Mei Ling","Wei","Chong","Jia Wei","Xin Yi","Hui Min","Zhi Hao","Li Wei","Yong Jun","Pei Wen","Kumar","Rajesh","Suresh","Vijaya","Anand","Arun","Priya","Deepa","Nisha","Karthik","Daniel","John","Jane","Zack","Hannah"]
LAST_NAMES = ["Rahman","Abdullah","Ismail","Hussin","Hashim","Mohamed","Salleh","Ahmad","Yusof","Talib","Tan","Lim","Lee","Ng","Wong","Chan","Ong","Goh","Chin","Teo","Gopal","Subramaniam","Pillai","Krishnan","Kaur","Singh","Ramasamy","Muniandy","Doe"]
COMPANY_PREFIX = ["Kedai","Restoran","Warung","Syarikat","Perusahaan","Bengkel","Koperasi","Farmasi","Klinik","Pasaraya","Gerai","Butik"]
COMPANY_SUFFIX = ["Maju","Jaya","Sentosa","Makmur","Bestari","Sejahtera","Indah","Harapan","Impian","Idaman","Perdana","Gemilang"]
COMPANY_TAIL = ["Enterprise","Resources","Trading","Sdn Bhd","Holdings"]

def random_person_name(rng): return f"{rng.choice(FIRST_NAMES)} {rng.choice(LAST_NAMES)}"
def random_company_name(rng):
    if rng.random() < 0.5:
        return f"{rng.choice(COMPANY_PREFIX)} {rng.choice(COMPANY_SUFFIX)}"
    else:
        return f"{rng.choice(COMPANY_PREFIX)} {rng.choice(COMPANY_SUFFIX)} {rng.choice(COMPANY_TAIL)}"

# ---------- Utils ----------
def rand_alnum(n, rng): return ''.join(rng.choice(list("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"), size=n))
def make_customer_id(rng): return "CUST_" + rand_alnum(max(1, 10-len("CUST_")), rng)
def make_account_id(rng): return "CACC_" + rand_alnum(max(1, 12-len("CACC_")), rng)
def make_txn_id(rng): return "TXN_" + rand_alnum(max(1, 15-len("TXN_")), rng)

def month_range(start_dt, end_dt):
    cur = datetime(start_dt.year, start_dt.month, 1, tzinfo=start_dt.tzinfo)
    while cur <= end_dt:
        if cur.month == 12:
            nxt = datetime(cur.year+1, 1, 1, tzinfo=cur.tzinfo)
        else:
            nxt = datetime(cur.year, cur.month+1, 1, tzinfo=cur.tzinfo)
        yield (cur, min(end_dt, nxt - timedelta(seconds=1)))
        cur = nxt

def random_timestamp_utc(start_dt, end_dt, rng):
    delta = int((end_dt - start_dt).total_seconds())
    sec = int(rng.integers(0, max(1, delta)))
    ts = start_dt + timedelta(seconds=sec)
    return ts.isoformat().replace("+00:00","Z")

def clipped_lognormal(rng, median, p95, vmin, vmax):
    mu = math.log(max(median, 1e-6))
    sigma = max(0.1, (math.log(max(p95, 1e-6)) - mu) / 1.64485)
    val = rng.lognormal(mean=mu, sigma=sigma)
    if val < vmin: val = vmin * (1 + rng.random()*0.1)
    if val > vmax: val = vmax * (0.8 + 0.2*rng.random())
    return round(float(val), 2)

# ---------- Rules ----------
def read_rules(path):
    xls = pd.ExcelFile(path)
    sheets = {name: pd.read_excel(path, sheet_name=name) for name in xls.sheet_names}
    occu, states = [], []
    if "occu" in sheets:
        for c in sheets["occu"].columns:
            occu += [str(v).strip() for v in sheets["occu"][c].dropna().tolist() if str(v).strip()]
    if "state" in sheets:
        for c in sheets["state"].columns:
            states += [str(v).strip() for v in sheets["state"][c].dropna().tolist() if str(v).strip()]
    txn_start = datetime(2024,1,1, tzinfo=timezone.utc)
    txn_end   = datetime(2025,9,24, tzinfo=timezone.utc)
    channels = ["QR P2P", "DuitNOW", "Credit Transfer", "QR POS", "Other"]
    return {"occu": occu or ["TEACHER/LECTURER","ENGINEER","DOCTOR","NURSE","DRIVER","HOUSEWIFE","STUDENT","CHEF","POLICE","ARMY","CASHIER","FARMER","RETIREE","CLERK","TECHNICIAN","CLEANER","LAWYER","DENTIST","SPECIALIST"],
            "states": states or ["Johor","Kedah","Kelantan","Melaka","Negeri Sembilan","Pahang","Pulau Pinang","Perak","Perlis","Selangor","Terengganu","Sabah","Sarawak","WP KL","WP Labuan","WP Putrajaya"],
            "txn_start": txn_start,"txn_end": txn_end,"channels": channels}

# ---------- Amount & type per channel ----------
def sample_type_amount(channel, rng, txn_floor_qr=100.0):
    MIN_AMT, MAX_AMT = 1.0, 1_000_000.0  # base min is 1, we will apply floor per channel
    
    if channel == "QR POS":
        floor = max(txn_floor_qr, 1.0)
        amt = clipped_lognormal(rng, 110, 260, floor, 5_000); ttype = "credit" if rng.random() < 0.95 else "debit"; return ttype, amt, True
    if channel == "QR P2P":
        floor = max(txn_floor_qr, 1.0)
        amt = clipped_lognormal(rng, 150, 800, floor, 5_000); ttype = "credit" if rng.random() < 0.7 else "debit"; return ttype, amt, False
    if channel == "DuitNOW":
        if rng.random() < 0.6:
            floor = max(txn_floor_qr, 1.0)
            amt = clipped_lognormal(rng, 150, 900, floor, 6_000); ttype = "credit" if rng.random() < 0.6 else "debit"; return ttype, amt, False
        else:
            amt = clipped_lognormal(rng, 250, 1500, 100.0, 10_000); ttype = "credit" if rng.random() < 0.7 else "debit"; return ttype, amt, True
    if channel == "Credit Transfer":
        if rng.random() < 0.3:
            amt = clipped_lognormal(rng, 3000, 15000, 100.0, 50_000); ttype = "debit"; return ttype, amt, True
        else:
            amt = clipped_lognormal(rng, 450, 2500, 100.0, 20_000); ttype = "credit" if rng.random() < 0.7 else "debit"; return ttype, amt, True
    amt = clipped_lognormal(rng, 200, 1500, 100.0, 10_000); ttype = "credit" if rng.random() < 0.6 else "debit"; return ttype, amt, rng.random() < 0.5

# ---------- Activity Segments ----------
def parse_segment_split(text):
    try:
        parts = [float(x) for x in str(text).split(',')]
        if len(parts) != 3:
            return 30.0, 60.0, 10.0
        total = sum(parts)
        if total <= 0:
            return 30.0, 60.0, 10.0
        parts = [x * 100.0 / total for x in parts]
        return parts[0], parts[1], parts[2]
    except Exception:
        return 30.0, 60.0, 10.0

def assign_activity_segments(profile_df, rng, split=(30.0,60.0,10.0)):
    n = len(profile_df); idx = np.arange(n); rng.shuffle(idx)
    high_pct, low_pct, sparse_pct = split
    high_pct = max(0.0, high_pct); low_pct = max(0.0, low_pct); sparse_pct = max(0.0, sparse_pct)
    total_pct = high_pct + low_pct + sparse_pct if (high_pct + low_pct + sparse_pct) > 0 else 100.0
    high_pct, low_pct, sparse_pct = [p * 100.0/total_pct for p in (high_pct, low_pct, sparse_pct)]
    n_high = int(round((high_pct/100.0) * n)); n_sparse = int(round((sparse_pct/100.0) * n))
    high_idx = set(idx[:n_high]); sparse_idx = set(idx[n_high:n_high+n_sparse])
    out = {}
    for i, (_, row) in enumerate(profile_df.iterrows()):
        acc = row["Customer_Acc"]
        if i in high_idx:
            lam = float(rng.uniform(4.0, 10.0)); out[acc] = {"segment": "high", "lambda": lam}
        elif i in sparse_idx:
            target = int(np.clip(rng.normal(5, 2), 1, 8)); out[acc] = {"segment": "sparse", "target_year": target}
        else:
            lam = float(rng.uniform(0.2, 1.8)); out[acc] = {"segment": "low", "lambda": lam}
    return out

# ---------- Generation ----------
def generate_profiles(n, rules, rng):
    used_c, used_a = set(), set(); rows = []
    for _ in range(n):
        cid = make_customer_id(rng); 
        while cid in used_c: cid = make_customer_id(rng)
        used_c.add(cid)
        acc = make_account_id(rng)
        while acc in used_a: acc = make_account_id(rng)
        used_a.add(acc)
        rows.append({"Customer_ID": cid,"Customer_Acc": acc,"Age": int(rng.integers(10,100)),
                     "Stated_Occupation": str(rng.choice(rules["occu"])).upper(),
                     "Location_State": str(rng.choice(rules["states"])),
                     "Account_Tenure_Months": int(rng.integers(5,241)),
                     "Account_Type": str(rng.choice(["CA","SA"]))})
    return pd.DataFrame(rows)

def generate_txns(profile_df, avg_txn, rules, rng, txn_floor_qr=100.0, segment_split="30,60,10"):
    start_dt, end_dt = rules["txn_start"], rules["txn_end"]
    segments = assign_activity_segments(profile_df, rng, split=parse_segment_split(segment_split))
    rows = []; months = list(month_range(start_dt, end_dt))
    for _, p in profile_df.iterrows():
        acc = p["Customer_Acc"]; seg = segments[acc]
        if seg["segment"] == "sparse":
            N = len(months); target_total = int(np.clip(round(seg["target_year"] * (N/12.0)), 1, max(5, N)))
            active_months = int(np.clip(round(target_total / 1.0), 1, N))
            active_idx = rng.choice(np.arange(N), size=active_months, replace=False)
            for j in range(N):
                mstart, mend = months[j]
                if j in active_idx:
                    k = int(rng.poisson(1.0))
                    for _ in range(k):
                        channel = str(rng.choice(rules["channels"])); ttype, amt, is_biz = sample_type_amount(channel, rng, txn_floor_qr)
                        cp_name = random_company_name(rng) if is_biz else random_person_name(rng)
                        rows.append({"Customer_Acc": acc,"Transaction_ID": make_txn_id(rng),"Timestamp": random_timestamp_utc(mstart, mend, rng),
                                     "Amount": amt,"Type": ttype,"Channel": channel,"Counterparty_Name": cp_name,"Counterparty_Account": make_account_id(rng)})
        else:
            lam = seg["lambda"]
            for mstart, mend in months:
                k = int(rng.poisson(lam))
                for _ in range(k):
                    channel = str(rng.choice(rules["channels"])); ttype, amt, is_biz = sample_type_amount(channel, rng, txn_floor_qr)
                    cp_name = random_company_name(rng) if is_biz else random_person_name(rng)
                    rows.append({"Customer_Acc": acc,"Transaction_ID": make_txn_id(rng),"Timestamp": random_timestamp_utc(mstart, mend, rng),
                                 "Amount": amt,"Type": ttype,"Channel": channel,"Counterparty_Name": cp_name,"Counterparty_Account": make_account_id(rng)})
    return pd.DataFrame(rows)

# ---------- Balance modelling with Occupation & Age ----------
def occu_factor(occupation: str):
    if occupation is None: return 1.0
    o = occupation.upper()
    lucrative = ["DOCTOR","DENTIST","SPECIALIST","LAWYER","ENGINEER","CONSULTANT"]
    mid = ["TEACHER","LECTURER","NURSE","POLICE","CHEF","DRIVER","TECHNICIAN","EXECUTIVE","OFFICER","ADMIN","CLERK"]
    low = ["CASHIER","FARMER","HOUSEWIFE","STUDENT","RETIREE","CLEANER","LABOUR","WORKER"]
    if any(x in o for x in lucrative): return 2.2
    if any(x in o for x in mid): return 1.0
    if any(x in o for x in low): return 0.75
    return 1.0

def age_factor(age: int, curve: str = 'base'):
    if curve == 'steeper':
        if age < 20: return 0.35
        if 20 <= age <= 24: return 0.45
        if 25 <= age <= 34: return 0.85
        if 35 <= age <= 44: return 1.30
        if 45 <= age <= 54: return 1.70
        if 55 <= age <= 64: return 1.30
        return 0.85
    elif curve == 'flatter':
        if age < 20: return 0.60
        if 20 <= age <= 24: return 0.70
        if 25 <= age <= 34: return 0.95
        if 35 <= age <= 44: return 1.10
        if 45 <= age <= 54: return 1.25
        if 55 <= age <= 64: return 1.05
        return 0.90
    else:
        if age < 20: return 0.45
        if 20 <= age <= 24: return 0.50
        if 25 <= age <= 34: return 0.90
        if 35 <= age <= 44: return 1.20
        if 45 <= age <= 54: return 1.50
        if 55 <= age <= 64: return 1.20
        return 0.90

def clipped_base(acct_type, rng):
    base_params = {"SA": {"median":1500, "p95":10000}, "CA":{"median":2500, "p95":15000}}
    p = base_params.get(acct_type, base_params["SA"])
    mu = math.log(p["median"]); sigma = (math.log(p["p95"]) - mu) / 1.64485
    val = rng.lognormal(mean=mu, sigma=max(0.1, sigma))
    return max(100.0, min(100_000.0, val))

def compute_avg_balances(profile_df, txn_df, rng, age_curve='base'):
    g = txn_df.groupby("Customer_Acc").agg(
        credit_total=("Amount", lambda s: float(s[txn_df.loc[s.index,'Type'].eq('credit')].sum())),
        debit_total=("Amount",  lambda s: float(s[txn_df.loc[s.index,'Type'].eq('debit')].sum())),
        txn_count=("Amount","size")
    ).reset_index()
    stats = {r["Customer_Acc"]: r for _, r in g.iterrows()}

    balances = []
    for _, p in profile_df.iterrows():
        acc = p["Customer_Acc"]
        base = clipped_base(p["Account_Type"], rng)
        tenure_factor = 1.0 + 0.15*min(1.0, p["Account_Tenure_Months"]/240.0)
        st = stats.get(acc, {"credit_total":0.0,"debit_total":0.0})
        denom = st["credit_total"] + st["debit_total"] + 1.0
        outflow_ratio = st["credit_total"]/denom  # higher -> lower balances
        occu_mult = occu_factor(p["Stated_Occupation"])
        age_mult = age_factor(int(p["Age"]), age_curve)
        bal = base * tenure_factor * occu_mult * age_mult * (1.0 - 0.4*min(1.0, outflow_ratio))
        balances.append(max(100.0, round(bal,2)))
    out = profile_df.copy(); out["Avg_Balance"] = balances; return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rules", required=True)
    ap.add_argument("--profiles", type=int, default=1000)
    ap.add_argument("--avg_txn", type=int, default=15)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--outdir", default="output")
    ap.add_argument("--txn_floor_qr", type=float, default=100.0, help="Min amount for QR channels (QR P2P/QR POS/DuitNOW-P2P-like)")
    ap.add_argument("--segment_split", type=str, default="30,60,10", help="Percent split of activity segments as high,low,sparse")
    ap.add_argument("--age_curve", type=str, default="base", choices=["base","steeper","flatter"], help="Age multiplier curve")
    args = ap.parse_args()

    rng = np.random.default_rng(args.seed)
    rules = read_rules(args.rules)
    os.makedirs(args.outdir, exist_ok=True)

    profiles = generate_profiles(args.profiles, rules, rng)
    txns = generate_txns(profiles, args.avg_txn, rules, rng, txn_floor_qr=args.txn_floor_qr, segment_split=args.segment_split)
    profiles = compute_avg_balances(profiles, txns, rng, age_curve=args.age_curve)

    today = datetime.utcnow().strftime("%Y%m%d")
    p_path = os.path.join(args.outdir, f"CUSTOMER_PROFILE_{today}.csv")
    t_path = os.path.join(args.outdir, f"CUSTOMER_TXN_{today}.csv")
    profiles.to_csv(p_path, index=False)
    txns.to_csv(t_path, index=False)
    print(f"Generated {len(profiles)} profiles -> {p_path}")
    print(f"Generated {len(txns)} transactions -> {t_path}")
    print("Done.")

if __name__ == "__main__":
    main()

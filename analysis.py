import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

# styling
plt.rcParams.update({
    "font.family": "sans-serif",
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.titlesize": 13,
    "axes.titleweight": "bold",
    "axes.labelsize": 11,
    "xtick.labelsize": 9,
    "ytick.labelsize": 9,
    "figure.dpi": 120,
})
BLUE  = "#003d8f"
RED   = "#d4281e"
AMBER = "#e07b00"
GREY  = "#6c757d"
LIGHT = "#ccd9f0"

# load and parse data from 4 csv files

# 1. food businesses by risk classification
raw_biz = pd.read_csv(
    "2023-24-number-of-sa-food-businesses-per-risk-classification.csv",
    skiprows=4, header=0
)
raw_biz.columns = ["metric", "P1", "P2", "P3", "P4", "Total"]
raw_biz = raw_biz.dropna(subset=["metric"])

# extract rows of interest by position
businesses_row   = raw_biz.iloc[0]
inspections_row  = raw_biz.iloc[1]
followup_row     = raw_biz.iloc[2]
complaints_row   = raw_biz.iloc[3]

df_businesses = pd.DataFrame({
    "Risk Class":      ["P1 (Highest)", "P2", "P3", "P4 (Lowest)"],
    "Businesses":      [int(businesses_row[c])  for c in ["P1","P2","P3","P4"]],
    "Inspections":     [int(inspections_row[c]) for c in ["P1","P2","P3","P4"]],
    "Follow-up":       [int(followup_row[c])    for c in ["P1","P2","P3","P4"]],
    "From Complaints": [int(complaints_row[c])  for c in ["P1","P2","P3","P4"]],
})
df_businesses["Inspection Rate (%)"] = (
    df_businesses["Inspections"] / df_businesses["Businesses"] * 100
).round(1)

# 2. food audits by sector
raw_aud = pd.read_csv(
    "2023-24-number-of-food-business-audits-by-local-government.csv",
    skiprows=3, header=0
)
raw_aud.columns = ["metric", "Aged Care", "Child Care", "Private Hospitals", "Others", "Total"]
raw_aud = raw_aud[raw_aud["metric"].notna()]

# remove the notes row at the bottom
raw_aud = raw_aud[~raw_aud["metric"].str.startswith("Note", na=True)]

# strip percentage signs from audit rate row and convert to numeric
def clean_int(val):
    return int(str(val).replace("%", "").strip())

sectors = ["Aged Care", "Child Care", "Private Hospitals", "Others"]
df_audits = pd.DataFrame({
    "Sector":           sectors,
    "Businesses":       [clean_int(raw_aud.iloc[0][s]) for s in sectors],
    "Audits Conducted": [clean_int(raw_aud.iloc[1][s]) for s in sectors],
})
df_audits["Audit Rate (%)"] = (
    df_audits["Audits Conducted"] / df_audits["Businesses"] * 100
).round(1)

# 3. food recalls
raw_rec = pd.read_csv(
    "2023-24-food-recalls-data.csv",
    header=None, names=["label", "value"]
)
raw_rec = raw_rec.dropna(subset=["label"])
raw_rec["label"] = raw_rec["label"].str.strip()

# find where each section starts
reason_start = raw_rec[raw_rec["label"] == "Reason for Recall"].index[0] + 1
reason_end   = raw_rec[raw_rec["label"] == "TOTAL"].index[1]  # second TOTAL row

reason_rows = raw_rec.loc[reason_start:reason_end - 1]
reason_rows = reason_rows[reason_rows["label"] != "Reason for Recall"]

df_recall_reason = pd.DataFrame({
    "Reason": reason_rows["label"].str.strip().values,
    "Count":  reason_rows["value"].astype(int).values,
})

# clean up labels for display
df_recall_reason["Reason"] = df_recall_reason["Reason"].replace({
    "Microbiological contamination": "Microbiological\ncontamination",
    "Chemical contamination":        "Chemical\ncontamination",
})
df_recall_reason = df_recall_reason.sort_values("Count", ascending=True)

# 4. food complaints
raw_comp = pd.read_csv(
    "2023-24-food-complaints-actioned-by-local-government.csv",
    skiprows=2, header=0
)
raw_comp.columns = ["Complaint Type", "Received", "Justified"]

# drop total row and any blank rows
raw_comp = raw_comp[raw_comp["Complaint Type"].notna()]
raw_comp = raw_comp[raw_comp["Complaint Type"].str.strip() != "Total"]

raw_comp["Received"]  = pd.to_numeric(raw_comp["Received"],  errors="coerce")
raw_comp["Justified"] = pd.to_numeric(raw_comp["Justified"], errors="coerce")
raw_comp = raw_comp.dropna(subset=["Received", "Justified"])
raw_comp["Received"]  = raw_comp["Received"].astype(int)
raw_comp["Justified"] = raw_comp["Justified"].astype(int)

# clean up labels for display
raw_comp["Complaint Type"] = raw_comp["Complaint Type"].str.strip().replace({
    "Personal hygiene or food handling": "Personal hygiene /\nfood handling",
    "Allergen":                          "Allergen",
})

df_complaints = raw_comp.sort_values("Received", ascending=True).reset_index(drop=True)
df_complaints["Justification Rate (%)"] = (
    df_complaints["Justified"] / df_complaints["Received"] * 100
).round(1)

# summary statistics
print("=" * 60)
print("SA Food Safety EDA — 2023-24 Annual Food Act Report")
print("=" * 60)

total_biz  = df_businesses["Businesses"].sum()
total_insp = df_businesses["Inspections"].sum()
print(f"\n1. FOOD BUSINESSES & INSPECTIONS")
print(f"   Total businesses registered: {total_biz:,}")
print(f"   Total inspections conducted: {total_insp:,}  ({total_insp/total_biz*100:.1f}% overall rate)")
print(f"   P1 (highest risk) inspection rate: {df_businesses.iloc[0]['Inspection Rate (%)']}%")
print(f"   P4 (lowest risk) inspection rate:  {df_businesses.iloc[3]['Inspection Rate (%)']}%")

print(f"\n2. SA HEALTH FACILITY AUDITS")
for _, row in df_audits.iterrows():
    print(f"   {row['Sector']}: {row['Audits Conducted']}/{row['Businesses']} audited ({row['Audit Rate (%)']}%)")

total_recalls = df_recall_reason["Count"].sum()
top_reason = df_recall_reason.iloc[-1]
print(f"\n3. FOOD RECALLS (Total: {total_recalls})")
print(f"   Most common reason: {top_reason['Reason'].replace(chr(10),' ')} ({top_reason['Count']} of {total_recalls}, {top_reason['Count']/total_recalls*100:.0f}%)")
print(f"   Recalls affecting SA: 73 of {total_recalls} (88%)")

total_received  = df_complaints["Received"].sum()
total_justified = df_complaints["Justified"].sum()
overall_just    = round(total_justified / total_received * 100, 1)
print(f"\n4. FOOD COMPLAINTS (Total: {total_received:,})")
print(f"   Overall justification rate: {overall_just}%")
highest = df_complaints.nlargest(1, "Justification Rate (%)")
print(f"   Highest rate: {highest.iloc[0]['Complaint Type'].replace(chr(10),' ')} ({highest.iloc[0]['Justification Rate (%)']}%)")
lowest = df_complaints[df_complaints["Received"] > 20].nsmallest(1, "Justification Rate (%)")
print(f"   Lowest rate:  {lowest.iloc[0]['Complaint Type'].replace(chr(10),' ')} ({lowest.iloc[0]['Justification Rate (%)']}%)")

# plots
fig, axes = plt.subplots(2, 2, figsize=(14, 11))
fig.suptitle(
    "SA Food Safety Overview — 2023–24 Annual Food Act Report",
    fontsize=15, fontweight="bold", y=1.01
)

# plot 1: inspections vs businesses by risk class
ax1 = axes[0, 0]
x = np.arange(len(df_businesses))
w = 0.35
ax1.bar(x - w/2, df_businesses["Businesses"],  w, label="Businesses",  color=LIGHT, edgecolor=BLUE)
ax1.bar(x + w/2, df_businesses["Inspections"], w, label="Inspections", color=BLUE,  alpha=0.85)
ax1.set_xticks(x)
ax1.set_xticklabels(df_businesses["Risk Class"], fontsize=9)
ax1.set_ylabel("Count")
ax1.set_title("Figure 1: Businesses vs Inspections by Risk Class")
ax1.legend(frameon=False)
for i, row in df_businesses.iterrows():
    ax1.text(i + w/2, row["Inspections"] + 80, f"{row['Inspection Rate (%)']}%",
             ha="center", fontsize=8, color=BLUE, fontweight="bold")

# plot 2: recall reasons
ax2 = axes[0, 1]
colors_r = [RED if v == df_recall_reason["Count"].max() else LIGHT
            for v in df_recall_reason["Count"]]
bars2 = ax2.barh(df_recall_reason["Reason"], df_recall_reason["Count"],
                 color=colors_r, edgecolor=BLUE, linewidth=0.5)
ax2.set_xlabel("Number of Recalls")
ax2.set_title(f"Figure 2: Food Recalls by Reason (Total: {total_recalls})")
for bar, val in zip(bars2, df_recall_reason["Count"]):
    ax2.text(bar.get_width() + 0.3, bar.get_y() + bar.get_height()/2,
             str(val), va="center", fontsize=9)
ax2.set_xlim(0, df_recall_reason["Count"].max() * 1.2)

# plot 3: complaints received vs justified
ax3 = axes[1, 0]
ax3.barh(df_complaints["Complaint Type"], df_complaints["Received"],
         color=LIGHT, edgecolor=BLUE, label="Received")
ax3.barh(df_complaints["Complaint Type"], df_complaints["Justified"],
         color=BLUE, alpha=0.85, label="Justified")
ax3.set_xlabel("Number of Complaints")
ax3.set_title(f"Figure 3: Food Complaints: Received vs Justified (Total: {total_received:,})")
ax3.legend(frameon=False)

# plot 4: justification rate by complaint type
ax4 = axes[1, 1]
just_sorted = df_complaints.sort_values("Justification Rate (%)", ascending=True)
colors_j = [RED if v >= 40 else AMBER if v >= 25 else LIGHT
            for v in just_sorted["Justification Rate (%)"]]
bars4 = ax4.barh(just_sorted["Complaint Type"], just_sorted["Justification Rate (%)"],
                 color=colors_j, edgecolor="white")
ax4.axvline(overall_just, color=GREY, linestyle="--", linewidth=1.2,
            label=f"Overall avg ({overall_just}%)")
ax4.set_xlabel("Justification Rate (%)")
ax4.set_title("Figure 4: What % of Complaints Were Justified?")
for bar, val in zip(bars4, just_sorted["Justification Rate (%)"]):
    ax4.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height()/2,
             f"{val}%", va="center", fontsize=8)
ax4.set_xlim(0, 60)
high = mpatches.Patch(color=RED,   label="≥40% justified")
med  = mpatches.Patch(color=AMBER, label="25–39% justified")
low  = mpatches.Patch(color=LIGHT, label="<25% justified")
ax4.legend(handles=[high, med, low], frameon=False, fontsize=8, loc="lower right")

plt.tight_layout()
plt.savefig("sa_food_safety_eda.png", bbox_inches="tight", dpi=150)
plt.close()
print("\nPlot saved: sa_food_safety_eda.png")
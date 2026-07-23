import streamlit as st
import pandas as pd
import numpy as np
from scipy.stats import norm
import matplotlib.pyplot as plt
from datetime import date

# ==========================================
# Data & Helper Functions
# ==========================================

# MoCA Normative Data from Rossetti et al., 2011 (Dallas Heart Study).
# Neurology 77(13):1272-1275. doi:10.1212/WNL.0b013e318230208a
# Table 2 provides stratified means and SDs in overlapping 10-year age bins,
# each centered on the midpoint shown in BRACKET_CENTERS below.
moca_norms = pd.DataFrame({
    'Age_Bracket': ["<35", "30-40", "35-45", "40-50", "45-55", "50-60", "55-65", "60-70", "65-75", "70-80"],
    'lt12_mean': [22.80, 22.84, 22.11, 21.36, 20.75, 19.94, 19.60, 19.30, 18.37, 16.07],
    'lt12_sd':   [3.38,  3.18,  3.33,  3.73,  3.80,  4.34,  4.14,  3.79,  3.87,  3.17],
    'eq12_mean': [24.46, 23.99, 23.02, 22.26, 21.87, 22.25, 21.58, 20.89, 20.57, 20.35],
    'eq12_sd':   [3.49,  2.93,  3.67,  3.94,  3.95,  3.46,  3.93,  4.50,  4.79,  4.91],
    'gt12_mean': [25.93, 25.81, 25.38, 25.09, 24.70, 24.34, 24.43, 24.32, 24.00, 23.60],
    'gt12_sd':   [2.48,  2.64,  3.05,  3.16,  3.24,  3.38,  3.31,  3.04,  3.35,  3.47]
})

# Representative center age for each overlapping bracket. Used to map an exact
# age to the single most appropriate normative bracket (nearest center wins),
# removing the ambiguity of the overlapping bins.
BRACKET_CENTERS = [
    (30, "<35"), (35, "30-40"), (40, "35-45"), (45, "40-50"), (50, "45-55"),
    (55, "50-60"), (60, "55-65"), (65, "60-70"), (70, "65-75"), (75, "70-80"),
]

VALID_BRACKETS = set(moca_norms['Age_Bracket'])
EDUCATION_OPTIONS = ["<12", "12", ">12"]
EDUCATION_LABELS = {
    "<12": "<12 (less than high school)",
    "12": "12 (high school)",
    ">12": ">12 (some college or more)",
}
REQUIRED_BATCH_COLUMNS = ["MoCA_Raw"]  # Age_Bracket OR Age is also required (checked per row)


def age_to_bracket(age):
    """Map an exact age (years) to the nearest normative bracket by center age."""
    if age is None or pd.isna(age):
        return None
    age = float(age)
    return min(BRACKET_CENTERS, key=lambda c: abs(c[0] - age))[1]


def get_moca_norm(age_bracket, edu_bracket):
    """Return (mean, sd) for a bracket/education pair, or (nan, nan) if invalid."""
    row = moca_norms[moca_norms['Age_Bracket'] == age_bracket]

    if row.empty:
        return np.nan, np.nan

    if edu_bracket == "<12":
        return row['lt12_mean'].values[0], row['lt12_sd'].values[0]
    elif edu_bracket == "12":
        return row['eq12_mean'].values[0], row['eq12_sd'].values[0]
    elif edu_bracket == ">12":
        return row['gt12_mean'].values[0], row['gt12_sd'].values[0]
    else:
        return np.nan, np.nan


def compute_scores(raw, age_bracket, edu_bracket):
    """Compute mean, sd, z-score, percentile, classification for one assessment.

    Returns a dict; z/percentile/classification are None if inputs are invalid.
    """
    mean, sd = get_moca_norm(age_bracket, edu_bracket)
    if pd.isna(mean) or pd.isna(sd) or sd == 0 or pd.isna(raw):
        return {"mean": mean, "sd": sd, "z": None, "percentile": None,
                "classification": None, "color": "gray"}
    z = (float(raw) - mean) / sd
    percentile = float(norm.cdf(z) * 100)
    classification, color = interpret_percentile(percentile)
    return {"mean": mean, "sd": sd, "z": z, "percentile": percentile,
            "classification": classification, "color": color}


def interpret_percentile(percentile):
    if pd.isna(percentile):
        return None, "gray"

    if percentile >= 98:
        return "Exceptionally High", "#00008B"
    elif percentile >= 90:
        return "Above Average", "#0000FF"
    elif percentile >= 75:
        return "High Average", "#00FFFF"
    elif percentile >= 25:
        return "Average", "#00FF00"
    elif percentile >= 9:
        return "Low Average", "#FFD700"
    elif percentile >= 2:
        return "Below Average", "#FF4500"
    else:
        return "Exceptionally Low", "#FF0000"


def plot_normal_distribution(z_score, measure_name, percentile, classification, color):
    x_vals = np.linspace(-4, 4, 400)
    y_vals = norm.pdf(x_vals)
    point_y = norm.pdf(z_score)

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(x_vals, y_vals, color='black', alpha=0.7)

    # Shade the proportion of the reference population scoring at or below the patient.
    shade_mask = x_vals <= z_score
    ax.fill_between(x_vals[shade_mask], y_vals[shade_mask], color=color, alpha=0.25)

    # Plot the specific patient's score.
    ax.scatter([z_score], [point_y], color=color, s=120, zorder=5)

    label_text = f"Z = {z_score:.2f}\nP = {percentile:.1f}%\n{classification}"
    ax.text(z_score, point_y + 0.03, label_text, ha='center', va='bottom',
            fontsize=10, bbox=dict(facecolor='white', alpha=0.8, edgecolor='none'))

    ax.set_title(f"Normative Distribution for {measure_name}\nRossetti et al. (2011) Table 2 Reference")
    ax.set_xlabel("Z-score (standard deviations from the expected mean)")
    ax.set_ylabel("Probability Density")
    ax.set_ylim(0, max(y_vals) + 0.15)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    return fig


def generate_csv_template():
    template = pd.DataFrame({
        'PatientName': ["Example (by bracket)", "Example (by age)"],
        'Age_Bracket': ["60-70", ""],
        'Age': ["", 72],
        'Education_Bracket': [">12", "12"],
        'TestDate': [date.today().strftime("%Y-%m-%d")] * 2,
        'MoCA_Raw': [24, 21],
    })
    return template


def _resolve_bracket(row):
    """Resolve a normative bracket for a batch row from Age_Bracket or Age.

    Returns (bracket_or_None, note). Note is empty on clean success.
    """
    ab = row.get('Age_Bracket')
    if pd.notna(ab) and str(ab).strip():
        text = str(ab).strip()
        if text in VALID_BRACKETS:
            return text, ""
        # Someone may have put a raw age in the bracket column.
        try:
            mapped = age_to_bracket(float(text))
            return mapped, f"Age_Bracket '{text}' read as age -> {mapped}"
        except (ValueError, TypeError):
            return None, f"Unknown Age_Bracket '{text}'"

    age = row.get('Age')
    if pd.notna(age) and str(age).strip():
        try:
            return age_to_bracket(float(age)), ""
        except (ValueError, TypeError):
            return None, f"Invalid Age '{age}'"

    return None, "Missing Age_Bracket and Age"


def process_batch(df):
    """Score an uploaded dataframe. Raises ValueError if required columns are absent."""
    missing = [c for c in REQUIRED_BATCH_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"CSV is missing required column(s): {', '.join(missing)}")
    if 'Age_Bracket' not in df.columns and 'Age' not in df.columns:
        raise ValueError("CSV must contain an 'Age_Bracket' column or an 'Age' column.")

    results = df.copy()
    means, sds, zs, percs, classes, notes = [], [], [], [], [], []

    for _, row in results.iterrows():
        bracket, note = _resolve_bracket(row)
        edu = str(row.get('Education_Bracket', '')).strip()

        if bracket is None:
            mean = sd = z = p = np.nan
            c = None
        elif edu not in EDUCATION_OPTIONS:
            mean = sd = z = p = np.nan
            c = None
            note = f"Unknown Education_Bracket '{edu}' (use <12, 12, or >12)"
        else:
            raw = pd.to_numeric(row.get('MoCA_Raw'), errors='coerce')
            if pd.isna(raw):
                mean = sd = z = p = np.nan
                c = None
                note = f"Invalid MoCA_Raw '{row.get('MoCA_Raw')}'"
            elif not (0 <= raw <= 30):
                mean = sd = z = p = np.nan
                c = None
                note = f"MoCA_Raw '{raw}' out of range (0-30)"
            else:
                s = compute_scores(raw, bracket, edu)
                mean, sd = s['mean'], s['sd']
                z, p, c = s['z'], s['percentile'], s['classification']

        means.append(mean)
        sds.append(sd)
        zs.append(round(z, 3) if pd.notna(z) else np.nan)
        percs.append(round(p, 1) if pd.notna(p) else np.nan)
        classes.append(c)
        notes.append(note)

    results['Expected_Mean'] = means
    results['Expected_SD'] = sds
    results['MoCA_Z'] = zs
    results['MoCA_Percentile'] = percs
    results['Classification'] = classes
    results['Note'] = notes

    return results


# ==========================================
# UI & App Logic
# ==========================================

st.set_page_config(page_title="MoCA Normative Calculator", layout="wide")
st.title("MoCA Normative Calculator")
st.caption(
    "Norm-referenced Z-scores and percentiles for the Montreal Cognitive Assessment (MoCA), "
    "based on Rossetti et al. (2011), *Neurology* 77(13):1272-1275."
)

tab1, tab2 = st.tabs(["Individual Assessment", "Batch Processing"])

# --- TAB 1: Individual Assessment ---
with tab1:
    col1, col2 = st.columns([1, 2])

    with col1:
        st.header("Patient Data")
        patient_name = st.text_input("Patient Name or ID", value="Example Patient")

        age = st.number_input("Age (years)", min_value=18, max_value=85, value=65, step=1,
                              help="Reference sample age range was 18-85 (Rossetti et al., 2011).")
        age_bracket = age_to_bracket(age)
        st.caption(f"Normative bracket used: **{age_bracket}**")

        edu_bracket = st.selectbox(
            "Education (years completed)",
            EDUCATION_OPTIONS,
            index=2,
            format_func=lambda x: EDUCATION_LABELS[x],
        )
        test_date = st.date_input("Test Date", value=date.today())

        st.divider()
        st.subheader("MoCA Score")
        moca_input_method = st.radio("Input Method:", ["Slider", "Type"], horizontal=True)

        if moca_input_method == "Slider":
            moca_raw = st.slider("Total Score", min_value=0, max_value=30, value=24)
        else:
            moca_raw = st.number_input("Total Score", min_value=0, max_value=30, value=24)

    with col2:
        st.header("Assessment Results")

        scores = compute_scores(moca_raw, age_bracket, edu_bracket)

        if scores['z'] is not None:
            z_score = scores['z']
            percentile = scores['percentile']
            classification = scores['classification']
            color = scores['color']

            m1, m2, m3 = st.columns(3)
            m1.metric("Raw Score", f"{moca_raw}")
            m2.metric("Z-score", f"{z_score:.2f}")
            m3.metric("Percentile", f"{percentile:.1f}%")

            st.markdown(
                f"**Expected (mean ± SD) for this age/education:** "
                f"`{scores['mean']:.2f} ± {scores['sd']:.2f}`  \n"
                f"**Classification:** `{classification}`  \n"
                f"This score is at or above approximately **{percentile:.0f}%** of the "
                f"demographically matched reference sample."
            )

            fig = plot_normal_distribution(z_score, "MoCA", percentile, classification, color)
            st.pyplot(fig)
            plt.close(fig)
        else:
            st.error("Invalid age or education bracket selected.")

# --- TAB 2: Batch Processing ---
with tab2:
    st.header("Batch Processing")

    st.subheader("1. Download CSV Template")
    st.info(
        "Provide either an **Age_Bracket** column (exactly matching a bracket such as `60-70`) "
        "or a numeric **Age** column (which is mapped to the nearest bracket automatically). "
        "Education_Bracket must be one of `<12`, `12`, or `>12`."
    )

    template_df = generate_csv_template()
    csv_template = template_df.to_csv(index=False).encode('utf-8')

    st.download_button(
        label="Download Template",
        data=csv_template,
        file_name=f"MoCA_Template_{date.today()}.csv",
        mime='text/csv',
    )

    st.divider()
    st.subheader("2. Upload Completed CSV")
    uploaded_file = st.file_uploader("Choose CSV File", type="csv")

    if uploaded_file is not None:
        try:
            input_df = pd.read_csv(uploaded_file)
        except Exception as e:
            st.error(f"Could not read the CSV file: {e}")
            input_df = None

        if input_df is not None:
            try:
                processed_df = process_batch(input_df)
            except ValueError as e:
                st.error(str(e))
                processed_df = None

            if processed_df is not None:
                scored = processed_df['MoCA_Z'].notna().sum()
                total = len(processed_df)
                if scored == total:
                    st.success(f"Scored all {total} row(s).")
                else:
                    st.warning(
                        f"Scored {scored} of {total} row(s). "
                        f"See the **Note** column for rows that could not be scored."
                    )

                st.dataframe(processed_df)

                st.divider()
                st.subheader("3. Export Results")

                csv_results = processed_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="Download Processed Data",
                    data=csv_results,
                    file_name=f"MoCA_Results_{date.today()}.csv",
                    mime='text/csv',
                )

st.divider()
st.caption(
    "For research and educational use. Norm-referenced scores support, but do not replace, "
    "clinical judgment and are not diagnostic. The Rossetti et al. (2011) cutoff of <26 has a high "
    "false-positive rate in the general population; demographically adjusted percentiles are "
    "reported here to aid interpretation."
)

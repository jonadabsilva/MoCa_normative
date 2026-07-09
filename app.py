import streamlit as st
import pandas as pd
import numpy as np
from scipy.stats import norm
import matplotlib.pyplot as plt
from datetime import date

# ==========================================
# Data & Helper Functions
# ==========================================

# MoCA Normative Data from Rossetti et al., 2011 (Dallas Heart Study)
# Table 2 provides stratified means and standard deviations in overlapping 10-year age bins.
moca_norms = pd.DataFrame({
    'Age_Bracket': ["<35", "30-40", "35-45", "40-50", "45-55", "50-60", "55-65", "60-70", "65-75", "70-80"],
    'lt12_mean': [22.80, 22.84, 22.11, 21.36, 20.75, 19.94, 19.60, 19.30, 18.37, 16.07],
    'lt12_sd':   [3.38,  3.18,  3.33,  3.73,  3.80,  4.34,  4.14,  3.79,  3.87,  3.17],
    'eq12_mean': [24.46, 23.99, 23.02, 22.26, 21.87, 22.25, 21.58, 20.89, 20.57, 20.35],
    'eq12_sd':   [3.49,  2.93,  3.67,  3.94,  3.95,  3.46,  3.93,  4.50,  4.79,  4.91],
    'gt12_mean': [25.93, 25.81, 25.38, 25.09, 24.70, 24.34, 24.43, 24.32, 24.00, 23.60],
    'gt12_sd':   [2.48,  2.64,  3.05,  3.16,  3.24,  3.38,  3.31,  3.04,  3.35,  3.47]
})

def get_moca_norm(age_bracket, edu_bracket):
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
    x_vals = np.linspace(-4, 4, 200)
    y_vals = norm.pdf(x_vals)
    point_y = norm.pdf(z_score)
    
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(x_vals, y_vals, color='black', alpha=0.7)
    
    # Plot the specific patient's score
    ax.scatter([z_score], [point_y], color=color, s=120, zorder=5)
    
    # Label the point
    label_text = f"Z = {z_score:.2f}\nP = {percentile:.1f}%\n{classification}"
    ax.text(z_score, point_y + 0.03, label_text, ha='center', va='bottom', 
            fontsize=10, bbox=dict(facecolor='white', alpha=0.8, edgecolor='none'))
    
    ax.set_title(f"Normative Distribution for {measure_name}\nRossetti et al. (2011) Table 2 Reference")
    ax.set_xlabel("Z-score")
    ax.set_ylabel("Probability Density")
    ax.set_ylim(0, max(y_vals) + 0.15)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    return fig

def generate_csv_template():
    template = pd.DataFrame({
        'PatientName': ["Example Patient"],
        'Age_Bracket': ["60-70"],
        'Education_Bracket': [">12"],
        'TestDate': [date.today().strftime("%Y-%m-%d")],
        'MoCA_Raw': [24]
    })
    return template

def process_batch(df):
    results = df.copy()
    
    means, sds, zs, percs, classes = [], [], [], [], []
    
    for _, row in results.iterrows():
        try:
            raw = float(row['MoCA_Raw'])
            age_b = str(row['Age_Bracket']).strip()
            edu_b = str(row['Education_Bracket']).strip()
            
            mean, sd = get_moca_norm(age_b, edu_b)
            
            if pd.notna(mean) and pd.notna(raw):
                z = (raw - mean) / sd
                p = norm.cdf(z) * 100
                c, _ = interpret_percentile(p)
            else:
                z, p, c = np.nan, np.nan, None
                
        except:
            mean, sd, z, p, c = np.nan, np.nan, np.nan, np.nan, None
            
        means.append(mean)
        sds.append(sd)
        zs.append(z)
        percs.append(p)
        classes.append(c)
        
    results['Expected_Mean'] = means
    results['Expected_SD'] = sds
    results['MoCA_Z'] = zs
    results['MoCA_Percentile'] = percs
    results['Classification'] = classes
    
    return results

# ==========================================
# UI & App Logic
# ==========================================

st.set_page_config(page_title="MoCA Normative Calculator", layout="wide")
st.title("MoCA Normative Calculator")

tab1, tab2 = st.tabs(["Individual Assessment", "Batch Processing"])

# --- TAB 1: Individual Assessment ---
with tab1:
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.header("Patient Data")
        patient_name = st.text_input("Patient Name or ID", value="Example Patient")
        age_bracket = st.selectbox("Age Bracket (from Table 2)", moca_norms['Age_Bracket'].tolist(), index=7)
        edu_bracket = st.selectbox("Education (years)", ["<12", "12", ">12"], index=2)
        test_date = st.date_input("Test Date", value=date.today())
        
        st.divider()
        st.subheader("MoCA Score")
        moca_input_method = st.radio("Input Method:", ["Slider", "Type"])
        
        if moca_input_method == "Slider":
            moca_raw = st.slider("Total Score", min_value=0, max_value=30, value=24)
        else:
            moca_raw = st.number_input("Total Score", min_value=0, max_value=30, value=24)
            
    with col2:
        st.header("Assessment Results")
        
        mean, sd = get_moca_norm(age_bracket, edu_bracket)
        
        if pd.notna(mean):
            z_score = (moca_raw - mean) / sd
            percentile = norm.cdf(z_score) * 100
            classification, color = interpret_percentile(percentile)
            
            st.markdown(f"""
            **Raw Score:** `{moca_raw}`  
            **Expected Mean:** `{mean:.2f}`  
            **Expected SD:** `{sd:.2f}`  
            **Z-score:** `{z_score:.2f}`  
            **Percentile:** `{percentile:.1f}%`  
            **Classification:** `{classification}`
            """)
            
            fig = plot_normal_distribution(z_score, "MoCA", percentile, classification, color)
            st.pyplot(fig)
        else:
            st.error("Invalid age or education bracket selected.")

# --- TAB 2: Batch Processing ---
with tab2:
    st.header("Batch Processing")
    
    st.subheader("1. Download CSV Template")
    st.info("Important: The Age_Bracket and Education_Bracket columns in your CSV must exactly match the strings in the dropdowns (e.g., '60-70' and '>12').")
    
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
        input_df = pd.read_csv(uploaded_file)
        
        st.write("Processing Data...")
        processed_df = process_batch(input_df)
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

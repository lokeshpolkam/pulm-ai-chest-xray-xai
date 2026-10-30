"""
PULM-AI: Explainable Chest Radiograph Pathology & Oncology Diagnostic Platform
Deep DenseNet-121 Architecture with Grad-CAM Feature Attribution Engine
Streamlit Clinical & Oncology Dashboard for 6th Semester Capstone Project
"""

import os
import streamlit as st
import numpy as np
import cv2
from PIL import Image
import torch
import torch.nn.functional as F

from model import get_trained_pipeline, CLASSES, CLASS_DETAILS
from report_generator import generate_html_report

# Page Configuration
st.set_page_config(
    page_title="PULM-AI | Thoracic Pathology & Oncology XAI Platform",
    page_icon="🫁",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling (Dark Clinical & Oncology Theme)
st.markdown("""
<style>
    .main-title {
        font-size: 28px;
        font-weight: 800;
        color: #64b5f6;
        margin-bottom: 2px;
        letter-spacing: -0.5px;
    }
    .sub-title {
        font-size: 14px;
        color: #90caf9;
        margin-bottom: 20px;
    }
    .metric-card {
        background-color: #1a2332;
        border: 1px solid #2d3748;
        border-radius: 8px;
        padding: 16px 20px;
        margin-bottom: 15px;
    }
    .badge-normal {
        background-color: #1b5e20;
        color: #81c784;
        padding: 4px 10px;
        border-radius: 4px;
        font-weight: 700;
        font-size: 13px;
    }
    .badge-acute {
        background-color: #b71c1c;
        color: #ef9a9a;
        padding: 4px 10px;
        border-radius: 4px;
        font-weight: 700;
        font-size: 13px;
    }
    .badge-moderate {
        background-color: #e65100;
        color: #ffcc80;
        padding: 4px 10px;
        border-radius: 4px;
        font-weight: 700;
        font-size: 13px;
    }
    .badge-cancer {
        background-color: #4a148c;
        color: #e1bee7;
        padding: 4px 10px;
        border-radius: 4px;
        font-weight: 700;
        font-size: 13px;
        border: 1px solid #ba68c8;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def load_cached_engine(weights_timestamp):
    """Caches model and engine; automatically invalidates when weights change."""
    model, engine = get_trained_pipeline()
    return engine

weights_file = "c:/tx_dmv/chest_xray_xai/weights_calibrated.pth"
weights_mtime = os.path.getmtime(weights_file) if os.path.exists(weights_file) else 0
engine = load_cached_engine(weights_mtime)

# ----------------- SIDEBAR -----------------
st.sidebar.image("https://img.icons8.com/fluency/96/lungs.png", width=64)
st.sidebar.title("Radiology & Oncology Control")

st.sidebar.markdown("### 1. Select Diagnostic Scan")
mode = st.sidebar.radio("Input Source:", ["Pre-Loaded Verified Scans", "Upload New Radiograph"])

samples_dir = "c:/tx_dmv/chest_xray_xai/samples"
current_image = None
sample_name = ""

if mode == "Pre-Loaded Verified Scans":
    available_samples = {
        "NORMAL: Case 01 - Healthy Adult (Clear Fields)": "NORMAL_01_Healthy_Adult.png",
        "NORMAL: Case 02 - Normal Bilateral Radiograph": "NORMAL_02_Clear_Lungs.png",
        "PNEUMONIA: Bacterial Lobar Consolidation (Right Base)": "PNEUMONIA_01_Bacterial_Lobar.png",
        "COVID-19 / VIRAL: Bilateral Ground-Glass Opacities": "PNEUMONIA_02_Viral_Bilateral_GGO.png",
        "LUNG CANCER: Solitary Malignant Nodule (Right Upper Lobe)": "CANCER_01_Solitary_Malignant_Nodule.png",
        "LUNG CANCER: Central Bronchogenic Carcinoma Mass": "CANCER_02_Bronchogenic_Carcinoma_Mass.png"
    }
    selected_key = st.sidebar.selectbox("Choose Sample Case:", list(available_samples.keys()))
    sample_file = os.path.join(samples_dir, available_samples[selected_key])
    if os.path.exists(sample_file):
        current_image = Image.open(sample_file).convert("RGB")
        sample_name = available_samples[selected_key]
else:
    uploaded = st.sidebar.file_uploader("Upload Chest X-Ray (PNG, JPG, JPEG):", type=["png", "jpg", "jpeg"])
    if uploaded is not None:
        current_image = Image.open(uploaded).convert("RGB")
        sample_name = uploaded.name

st.sidebar.markdown("---")
st.sidebar.markdown("### 2. Patient Demographics")
p_id = st.sidebar.text_input("Accession ID:", "ONC-2026-9042")
p_name = st.sidebar.text_input("Patient Name:", "Subject_Alpha")
p_age = st.sidebar.slider("Age:", min_value=18, max_value=90, value=56)
p_sex = st.sidebar.selectbox("Sex:", ["Male", "Female", "Other"])

st.sidebar.markdown("---")
st.sidebar.markdown("### 3. Explainability (XAI) Tuner")
alpha_val = st.sidebar.slider("Heatmap Blending Ratio (α):", 0.1, 0.9, 0.45, 0.05)
colormap_name = st.sidebar.selectbox("Feature Colormap:", ["COLORMAP_JET", "COLORMAP_TURBO", "COLORMAP_INFERNO", "COLORMAP_VIRIDIS"])
thresh_slider = st.sidebar.slider("Lesion/Tumor Attention Cutoff:", 0.40, 0.85, 0.58, 0.02)

if st.sidebar.button("🔄 Clear Cache & Reload Model"):
    st.cache_resource.clear()
    st.rerun()


# ----------------- MAIN VIEW -----------------
st.markdown("<div class='main-title'>PULM-AI: Thoracic Pathology & Pulmonary Oncology Diagnostic Suite</div>", unsafe_allow_html=True)
st.markdown("<div class='sub-title'>Deep DenseNet-121 Multi-Task Architecture &bull; PyTorch Grad-CAM Feature Attribution Engine &bull; Automated Lesion Caliber Telemetry</div>", unsafe_allow_html=True)

if current_image is None:
    st.info("Please select or upload a chest radiograph from the sidebar to begin analysis.")
    st.stop()

# Run Inference & Grad-CAM Analysis
with st.spinner("Executing Deep Feature Attribution & Gradient Propagation..."):
    results = engine.analyze(current_image)

pred_idx = results["predicted_idx"]
conf = results["confidence"]
details = CLASS_DETAILS[pred_idx]
conf_pct = round(conf * 100, 1)

# Status Badge
if pred_idx == 0:
    badge_html = f"<span class='badge-normal'>STATUS: {details['severity'].upper()}</span>"
elif pred_idx == 1:
    badge_html = f"<span class='badge-acute'>STATUS: {details['severity'].upper()}</span>"
elif pred_idx == 2:
    badge_html = f"<span class='badge-moderate'>STATUS: {details['severity'].upper()}</span>"
else:
    badge_html = f"<span class='badge-cancer'>ONCOLOGY ALERT: {details['severity'].upper()}</span>"

# Primary Diagnostic Header Card
st.markdown(f"""
<div class='metric-card' style='border-left: 6px solid {details.get("badge_color", "#1976d2")};'>
    <div style='display: flex; justify-content: space-between; align-items: center;'>
        <div>
            <span style='font-size: 13px; color: #90caf9; text-transform: uppercase; font-weight: 600;'>Diagnostic Finding &bull; {details.get('category', 'Pathology')}</span>
            <div style='font-size: 24px; font-weight: 800; color: #ffffff; margin-top: 2px;'>{details['title']}</div>
        </div>
        <div style='text-align: right;'>
            {badge_html}
            <div style='font-size: 22px; font-weight: 800; color: #64b5f6; margin-top: 4px;'>{conf_pct}% <span style='font-size: 13px; color: #aaa;'>Confidence</span></div>
        </div>
    </div>
    <div style='margin-top: 10px; font-size: 14px; color: #cfd8dc; line-height: 1.5;'>
        {details['description']}
    </div>
    <div style='margin-top: 10px; font-size: 13px; color: #81d4fa; font-weight: 600;'>
        🎯 Action: {details.get('action', 'Clinical review indicated.')}
    </div>
</div>
""", unsafe_allow_html=True)

# ----------------- 3-COLUMN RADIOLOGY & ONCOLOGY VIEWPORT -----------------
st.markdown("### Clinical Visualization & Attention Decomposition")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("**1. Original Radiograph (PA CXR)**")
    st.image(current_image, use_column_width=True, caption=f"Scan: {sample_name} | 512x512 Grayscale")

with col2:
    st.markdown("**2. Grad-CAM Feature Attribution**")
    cv_cmap = getattr(cv2, colormap_name, cv2.COLORMAP_JET)
    norm_cam = results["raw_heatmap"]
    cam_uint8 = np.uint8(255 * norm_cam)
    heatmap_colored = cv2.applyColorMap(cam_uint8, cv_cmap)
    heatmap_colored = cv2.cvtColor(heatmap_colored, cv2.COLOR_BGR2RGB)
    
    orig_np = np.array(current_image)
    if len(orig_np.shape) == 2:
        orig_np = cv2.cvtColor(orig_np, cv2.COLOR_GRAY2RGB)
        
    blended = cv2.addWeighted(orig_np, 1.0 - alpha_val, heatmap_colored, alpha_val, 0)
    st.image(blended, use_column_width=True, caption=f"Colormap: {colormap_name.replace('COLORMAP_', '')} | α={alpha_val}")

with col3:
    st.markdown("**3. Localized Lesions & Tumor ROIs**")
    thresh_mask = np.uint8(norm_cam >= thresh_slider) * 255
    contours, _ = cv2.findContours(thresh_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    roi_custom = orig_np.copy()
    h_img, w_img = roi_custom.shape[:2]
    total_pix = h_img * w_img
    active_rois = []
    
    # Color coding
    box_color = (175, 82, 222) if pred_idx == 3 else ((255, 60, 60) if pred_idx != 0 else (60, 220, 100))
    
    for i, c in enumerate(contours):
        x, y, w, h = cv2.boundingRect(c)
        area = w * h
        if area > (total_pix * 0.004):
            area_pct = round((area / total_pix) * 100, 1)
            peak_val = round(float(np.max(norm_cam[y:y+h, x:x+w])), 2)
            est_diam_mm = round((max(w, h) / w_img) * 400.0, 1)
            
            cv2.rectangle(roi_custom, (x, y), (x + w, y + h), box_color, 2)
            type_tag = "TUMOR" if pred_idx == 3 else "LESION"
            lbl = f"ROI #{i+1} [{type_tag}]: ~{est_diam_mm}mm"
            cv2.rectangle(roi_custom, (x, max(0, y - 18)), (x + 130, max(18, y)), box_color, -1)
            cv2.putText(roi_custom, lbl, (x + 3, max(13, y - 4)), cv2.FONT_HERSHEY_SIMPLEX, 0.38, (255, 255, 255), 1)
            active_rois.append({
                "id": i+1, "x": x, "y": y, "w": w, "h": h, 
                "peak": peak_val, "area": area_pct, "diam_mm": est_diam_mm
            })
            
    st.image(roi_custom, use_column_width=True, caption=f"Identified {len(active_rois)} Active Focal ROI Targets (Cutoff ≥ {thresh_slider})")

# ----------------- DIAGNOSTIC TELEMETRY & QUANTITATIVE FINDINGS -----------------
st.markdown("---")
row_a, row_b = st.columns([1.2, 1.0])

with row_a:
    st.markdown("#### Differential Diagnostic & Oncology Distribution")
    for cname, prob in results["predictions"]:
        p_pct = prob * 100
        st.write(f"**{cname}**: `{p_pct:.2f}%`")
        st.progress(float(prob))

with row_b:
    st.markdown("#### Localized Target Caliber & Telemetry")
    if active_rois:
        roi_table = [{
            "Target": f"ROI #{r['id']}", 
            "Est. Diameter": f"{r['diam_mm']} mm",
            "Coordinates": f"[{r['x']}, {r['y']}]", 
            "Peak Density": f"{r['peak']}", 
            "Field Coverage": f"{r['area']}%"
        } for r in active_rois]
        st.dataframe(roi_table, use_container_width=True)
    else:
        st.success("Physiologic Negative Finding: No pathological consolidation or malignant nodule clusters detected.")

# ----------------- REPORT EXPORT -----------------
st.markdown("---")
st.markdown("### Clinical Documentation & Report Export")

patient_meta = {
    "id": p_id,
    "name": p_name,
    "age": p_age,
    "sex": p_sex
}
report_html = generate_html_report(patient_meta, results, CLASS_DETAILS)

col_dl, col_preview = st.columns([1, 3])
with col_dl:
    st.download_button(
        label="📥 Download Official PACS Radiology & Oncology Report",
        data=report_html,
        file_name=f"Oncology_Radiology_Report_{p_id}.html",
        mime="text/html"
    )

with col_preview:
    with st.expander("👁️ Preview PACS Clinical Report Document"):
        st.components.v1.html(report_html, height=520, scrolling=True)

# ----------------- VIVA & TECHNICAL SPECIFICATIONS -----------------
with st.expander("📘 Technical Architecture & Mathematical Formulations (Examiner Reference)"):
    st.markdown("""
    #### 1. DenseNet-121 Dense Connectivity Formulation
    Unlike standard ResNets with additive residual connections ($x_l = H_l(x_{l-1}) + x_{l-1}$), DenseNet utilizes direct concatenated feature-reuse connections:
    $$x_l = H_l([x_0, x_1, \\dots, x_{l-1}])$$
    Where $[x_0, x_1, \\dots, x_{l-1}]$ denotes the channel-wise concatenation of feature maps from all prior layers. This alleviates the vanishing-gradient problem and maximizes gradient reuse across multi-scale pulmonary lesions.

    #### 2. Gradient-Weighted Class Activation Mapping (Grad-CAM)
    The class-discriminative localization map $L_{\\text{Grad-CAM}}^c \\in \\mathbb{R}^{u \\times v}$ of width $u$ and height $v$ for target class $c$ is computed by taking the gradient of score $Y^c$ with respect to feature activation maps $A^k$ of the last convolutional layer:
    $$\\alpha_k^c = \\frac{1}{Z} \\sum_{i=1}^u \\sum_{j=1}^v \\frac{\\partial Y^c}{\\partial A_{i,j}^k}$$
    The weights $\\alpha_k^c$ capture the target importance of feature map $k$. The heat map is a rectified weighted combination:
    $$L_{\\text{Grad-CAM}}^c = \\text{ReLU}\\left(\\sum_k \\alpha_k^c A^k\\right)$$
    The $\\text{ReLU}$ non-linearity ensures that only features that have a positive influence on the target class $c$ (e.g., solitary nodule opacity or lobar consolidation) are retained.
    """)

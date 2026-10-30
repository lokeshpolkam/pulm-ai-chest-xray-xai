"""
Clinical AI Diagnostic Radiology & Oncology Report Generator
Formats structured diagnostic findings, Grad-CAM attention metrics,
and pulmonary pathology & oncology classifications into a professional clinical report.
"""

from datetime import datetime

def generate_html_report(patient_info, analysis_results, class_details):
    pred_idx = analysis_results["predicted_idx"]
    details = class_details[pred_idx]
    confidence_pct = round(analysis_results["confidence"] * 100, 1)
    
    # Severity badge styling
    badge_color = details.get("badge_color", "#1976d2")
    
    # Format differential table
    diff_rows = ""
    for cname, prob in analysis_results["predictions"]:
        p_pct = round(prob * 100, 1)
        bar_w = int(p_pct)
        is_pred = (cname == analysis_results["predictions"][pred_idx][0])
        bar_color = badge_color if is_pred else "#90caf9"
        diff_rows += f"""
        <tr>
            <td style="padding: 9px 12px; border-bottom: 1px solid #e0e0e0; font-weight: {'bold' if is_pred else '500'};">
                {'👉 ' if is_pred else ''}{cname}
            </td>
            <td style="padding: 9px 12px; border-bottom: 1px solid #e0e0e0; width: 45%;">
                <div style="background-color: #f0f0f0; border-radius: 4px; overflow: hidden; height: 12px;">
                    <div style="width: {bar_w}%; background-color: {bar_color}; height: 100%;"></div>
                </div>
            </td>
            <td style="padding: 9px 12px; border-bottom: 1px solid #e0e0e0; text-align: right; font-weight: bold;">{p_pct}%</td>
        </tr>
        """
        
    # Format ROI findings
    roi_rows = ""
    if analysis_results["rois"]:
        for r in analysis_results["rois"]:
            diam_info = f"&bull; Est. Lesion / Tumor Caliber: <strong>~{r.get('est_diameter_mm', 'N/A')} mm</strong>" if 'est_diameter_mm' in r else ""
            roi_rows += f"""
            <li style="margin-bottom: 8px;">
                <strong>Target Cluster #{r['id']}</strong>: Bounding Coordinates [X:{r['x']}, Y:{r['y']}, W:{r['w']}, H:{r['h']}] {diam_info} &bull; 
                Peak Attention Intensity: <code>{r['peak_intensity']}</code> &bull; 
                Parenchymal Field Coverage: <strong>{r['area_pct']}%</strong>
            </li>
            """
    else:
        roi_rows = "<li>No hyper-dense focal consolidation, nodular mass, or ground-glass lesion clusters identified exceeding activation threshold (0.58).</li>"

    # Oncology special alert if Class 3
    oncology_alert_banner = ""
    if pred_idx == 3:
        oncology_alert_banner = """
        <div style="margin: 16px 0; padding: 14px; background: #f3e5f5; border-left: 5px solid #7b1fa2; border-radius: 4px; color: #4a148c; font-size: 13.5px;">
            <strong>⚠️ THORACIC ONCOLOGY MULTIDISCIPLINARY ALERT:</strong> High-confidence solitary pulmonary mass/nodule detected. Immediate referral to thoracic oncology for contrast-enhanced chest CT staging and biopsy consultation is strongly advised.
        </div>
        """

    report_html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Clinical AI Diagnostic Report - {patient_info.get('id', 'XR-9042')}</title>
<style>
    body {{
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        color: #212529;
        background-color: #f8f9fa;
        margin: 0;
        padding: 24px;
    }}
    .report-container {{
        max-width: 820px;
        margin: 0 auto;
        background: #ffffff;
        border: 1px solid #dcdcdc;
        border-radius: 8px;
        padding: 36px 40px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.06);
    }}
    .header {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-bottom: 2px solid #1976d2;
        padding-bottom: 16px;
        margin-bottom: 24px;
    }}
    .header h1 {{
        margin: 0;
        font-size: 22px;
        color: #0d47a1;
        letter-spacing: 0.5px;
    }}
    .header .sub {{
        font-size: 13px;
        color: #666;
        margin-top: 4px;
    }}
    .meta-grid {{
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 12px;
        background-color: #f7f9fc;
        padding: 16px;
        border-radius: 6px;
        font-size: 13.5px;
        margin-bottom: 20px;
    }}
    .diagnosis-box {{
        background: #fafafa;
        border-left: 5px solid {badge_color};
        padding: 18px;
        border-radius: 0 6px 6px 0;
        margin-bottom: 20px;
    }}
    .badge {{
        display: inline-block;
        padding: 4px 12px;
        font-size: 12px;
        font-weight: bold;
        border-radius: 12px;
        background: {badge_color};
        color: #ffffff;
        margin-left: 8px;
    }}
    table {{
        width: 100%;
        border-collapse: collapse;
        font-size: 13px;
        margin-bottom: 24px;
    }}
    th {{
        text-align: left;
        padding: 9px 12px;
        background-color: #f1f3f5;
        border-bottom: 2px solid #dee2e6;
    }}
    .footer {{
        border-top: 1px solid #e0e0e0;
        margin-top: 32px;
        padding-top: 16px;
        font-size: 11px;
        color: #777;
        line-height: 1.5;
    }}
</style>
</head>
<body>
<div class="report-container">
    <div class="header">
        <div>
            <h1>PULMONARY & THORACIC ONCOLOGY AI REPORT</h1>
            <div class="sub">Explainable Deep Feature Attribution Diagnostic Suite (Grad-CAM XAI)</div>
        </div>
        <div style="text-align: right; font-size: 12px; color: #555;">
            <strong>REPORT ID:</strong> {patient_info.get('id', 'XR-2026-9042')}<br>
            <strong>DATE:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        </div>
    </div>

    <div class="meta-grid">
        <div><strong>Patient Name:</strong> {patient_info.get('name', 'Anonymous Subject')}</div>
        <div><strong>Patient Age / Sex:</strong> {patient_info.get('age', '52')} Y / {patient_info.get('sex', 'M')}</div>
        <div><strong>Modality / View:</strong> Digital Radiography (PA Chest CXR)</div>
        <div><strong>Diagnostic Taxonomy:</strong> Pulmonary Infections & Thoracic Oncology</div>
    </div>

    {oncology_alert_banner}

    <div class="diagnosis-box">
        <div style="font-size: 12px; font-weight: bold; text-transform: uppercase; color: #666; margin-bottom: 4px;">Primary Algorithmic Classification</div>
        <div style="font-size: 21px; font-weight: bold; color: #111;">
            {details['title']}
            <span class="badge">{details['severity']}</span>
        </div>
        <div style="font-size: 14px; color: {badge_color}; font-weight: 700; margin-top: 4px;">
            Inference Confidence: {confidence_pct}% &bull; Category: {details.get('category', 'Pathology')}
        </div>
        <p style="font-size: 13.5px; color: #333; margin: 10px 0 0 0; line-height: 1.5;">
            {details['description']}
        </p>
    </div>

    <h3 style="font-size: 15px; margin-bottom: 8px;">Differential Diagnostic Distribution</h3>
    <table>
        <thead>
            <tr>
                <th>Pathology & Oncology Class</th>
                <th>Relative Likelihood Distribution</th>
                <th style="text-align: right;">Probability</th>
            </tr>
        </thead>
        <tbody>
            {diff_rows}
        </tbody>
    </table>

    <h3 style="font-size: 15px; margin-bottom: 8px;">Explainable AI (Grad-CAM) Spatial Attributions & Lesion Coordinates</h3>
    <ul style="font-size: 13px; color: #333; line-height: 1.6; padding-left: 20px;">
        {roi_rows}
    </ul>

    <div style="margin-top: 24px; padding: 14px; background: #e3f2fd; border-radius: 6px; font-size: 13px; color: #0d47a1;">
        <strong>Recommended Clinical Action:</strong> {details.get('action', 'Clinical correlation recommended.')}
    </div>

    <div class="footer">
        <strong>Investigational AI Disclaimer:</strong> This report is generated by a Densely Connected Convolutional Neural Network (DenseNet-121) with Gradient-weighted Class Activation Mapping for academic and clinical research purposes (6th Semester Capstone Project).
    </div>
</div>
</body>
</html>
"""
    return report_html

"""
Synthetic Chest Radiograph Generator for Clinical AI Testing
Generates anatomically realistic 512x512 chest X-rays (PA projection)
with realistic thoracic cage, lung parenchyma, ribs, spine, cardiac silhouette,
and calibrated pathological opacities including Lung Cancer / Pulmonary Nodules.
"""

import numpy as np
import cv2
from PIL import Image
import os

def create_base_chest_anatomy(width=512, height=512):
    """Generates standard PA chest radiograph anatomical baseline."""
    img = np.zeros((height, width), dtype=np.float32)
    
    # 1. Soft tissue thorax boundary (outer elliptical gradient)
    y, x = np.ogrid[:height, :width]
    center_x, center_y = width // 2, height // 2
    
    # Outer body soft tissue silhouette
    body_mask = ((x - center_x) / (width * 0.44))**2 + ((y - (center_y + 20)) / (height * 0.46))**2 <= 1.0
    img[body_mask] = 85.0
    
    # Peripheral skin falloff
    soft_tissue = np.exp(-(((x - center_x) / (width * 0.42))**2 + ((y - center_y) / (height * 0.44))**2)) * 50
    img += soft_tissue
    
    # 2. Lung fields (radiolucent, low density -> dark)
    # Right lung (anatomical right, appears on left of image)
    right_lung_mask = (((x - (center_x - 95)) / 72)**2 + ((y - (center_y - 20)) / 145)**2 <= 1.0) & (y < height * 0.82)
    # Left lung (anatomical left, appears on right of image, notch for heart)
    left_lung_mask = (((x - (center_x + 95)) / 70)**2 + ((y - (center_y - 20)) / 140)**2 <= 1.0) & (y < height * 0.80)
    
    # Subtractive radiolucency for lungs
    img[right_lung_mask] = 30.0
    img[left_lung_mask] = 30.0
    
    # 3. Mediastinum & Spine (radiopaque -> bright central vertical column)
    spine = np.exp(-((x - center_x) / 18)**2) * 120
    img += spine
    
    # 4. Cardiac Silhouette (heart shadow in left hemithorax, cardiothoracic ratio ~ 0.45)
    heart_mask = (((x - (center_x + 35)) / 65)**2 + ((y - (center_y + 60)) / 65)**2 <= 1.0) & (y < height * 0.85)
    img[heart_mask] = np.maximum(img[heart_mask], 135.0)
    
    # Aortic Knob & Pulmonary Artery contour
    aortic_knob = (((x - (center_x + 22)) / 25)**2 + ((y - (center_y - 30)) / 22)**2 <= 1.0)
    img[aortic_knob] = np.maximum(img[aortic_knob], 125.0)
    
    # 5. Clavicles (collar bones)
    for sign in [-1, 1]:
        cx = center_x + sign * 120
        cy = int(height * 0.28)
        clavicle = np.exp(-(((x - cx) / 80)**2 + ((y - cy + sign * 0.15 * (x - cx)) / 12)**2)) * 75
        img += clavicle
        
    # 6. Posterior Ribs (curved horizontal bands)
    for rib_y in range(int(height * 0.25), int(height * 0.78), 38):
        curvature = 0.0008 * (x - center_x)**2
        rib = np.exp(-((y - (rib_y + curvature)) / 9.0)**2) * 28.0
        img += rib * (body_mask.astype(np.float32))
        
    # 7. Diaphragmatic Domes (sharp hemidiaphragm contours)
    r_diaphragm = y > (height * 0.76 - 0.0006 * (x - (center_x - 100))**2)
    img[r_diaphragm & (x < center_x)] = np.maximum(img[r_diaphragm & (x < center_x)], 160.0)
    
    l_diaphragm = y > (height * 0.79 - 0.0005 * (x - (center_x + 100))**2)
    img[l_diaphragm & (x >= center_x)] = np.maximum(img[l_diaphragm & (x >= center_x)], 150.0)

    # 8. Fine Bronchovascular Markings
    noise = np.random.normal(0, 4.0, (height, width))
    img += noise
    
    img = cv2.GaussianBlur(img, (5, 5), 1.5)
    img = np.clip(img, 0, 255).astype(np.uint8)
    return img


def generate_all_samples(output_dir="c:/tx_dmv/chest_xray_xai/samples"):
    os.makedirs(output_dir, exist_ok=True)
    
    # --- 1. NORMAL (Clear Architecture) ---
    normal_img = create_base_chest_anatomy()
    cv2.imwrite(os.path.join(output_dir, "NORMAL_01_Healthy_Adult.png"), normal_img)
    cv2.imwrite(os.path.join(output_dir, "NORMAL_02_Clear_Lungs.png"), cv2.GaussianBlur(normal_img, (3, 3), 0.8))
    print("Generated: NORMAL samples")

    # --- 2. BACTERIAL PNEUMONIA (Dense Lobar Consolidation in Right Base) ---
    bact_img = create_base_chest_anatomy().astype(np.float32)
    h, w = bact_img.shape
    y, x = np.ogrid[:h, :w]
    infiltrate_center_x, infiltrate_center_y = 165, 330
    dist_sq = ((x - infiltrate_center_x) / 52.0)**2 + ((y - infiltrate_center_y) / 40.0)**2
    lobar_consolidation = np.exp(-dist_sq) * 115.0
    speckle = np.random.normal(0, 12.0, (h, w)) * np.exp(-dist_sq)
    bact_img += lobar_consolidation + speckle
    cv2.imwrite(os.path.join(output_dir, "PNEUMONIA_01_Bacterial_Lobar.png"), np.clip(bact_img, 0, 255).astype(np.uint8))
    print("Generated: BACTERIAL PNEUMONIA sample")

    # --- 3. VIRAL / COVID-19 (Bilateral Ground-Glass Opacities) ---
    viral_img = create_base_chest_anatomy().astype(np.float32)
    ggo_right = np.exp(-(((x - 140) / 48)**2 + ((y - 290) / 75)**2)) * 68.0
    ggo_left = np.exp(-(((x - 370) / 46)**2 + ((y - 305) / 70)**2)) * 74.0
    viral_img += ggo_right + ggo_left + np.random.normal(0, 8.0, (h, w)) * ((ggo_right + ggo_left) > 10)
    cv2.imwrite(os.path.join(output_dir, "PNEUMONIA_02_Viral_Bilateral_GGO.png"), np.clip(viral_img, 0, 255).astype(np.uint8))
    print("Generated: VIRAL / COVID-19 sample")

    # --- 4. LUNG CANCER: Solitary Pulmonary Nodule / Malignant Neoplasm Mass ---
    # Classical radiographic appearance: Dense, circumscribed round/oval mass with irregular spiculated margins in the upper lobe
    cancer_img = create_base_chest_anatomy().astype(np.float32)
    
    # Tumor center in Right Upper Lobe (anatomical right = left in image, x=175, y=190)
    tumor_cx, tumor_cy = 175, 190
    tumor_radius = 24.0
    
    # Core dense tumor mass
    dist_tumor = np.sqrt((x - tumor_cx)**2 + (y - tumor_cy)**2)
    tumor_core = np.exp(-(dist_tumor / tumor_radius)**2) * 145.0
    
    # Spiculated malignant corona (radial needle-like infiltrations characteristic of adenocarcinoma)
    angles = np.arctan2(y - tumor_cy, x - tumor_cx)
    spiculation = (np.sin(7 * angles) ** 2) * np.exp(-(dist_tumor / (tumor_radius * 1.5))**2) * 45.0
    
    cancer_img += tumor_core + spiculation
    cv2.imwrite(os.path.join(output_dir, "CANCER_01_Solitary_Malignant_Nodule.png"), np.clip(cancer_img, 0, 255).astype(np.uint8))
    
    # Cancer Sample 2: Left Hilar Mass (central bronchogenic carcinoma)
    cancer_img2 = create_base_chest_anatomy().astype(np.float32)
    mass_cx, mass_cy = 330, 240
    dist_mass = np.sqrt((x - mass_cx)**2 + (y - mass_cy)**2)
    hilar_mass = np.exp(-(dist_mass / 32.0)**2) * 155.0
    cancer_img2 += hilar_mass
    cv2.imwrite(os.path.join(output_dir, "CANCER_02_Bronchogenic_Carcinoma_Mass.png"), np.clip(cancer_img2, 0, 255).astype(np.uint8))
    print("Generated: LUNG CANCER / NEOPLASM samples")

if __name__ == "__main__":
    generate_all_samples()

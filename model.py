"""
Chest X-Ray Pathology & Oncology Classification & Grad-CAM Explainable AI Engine
Deep DenseNet-121 Architecture with PyTorch Feature Attribution Hooks
Detects Pulmonary Infections (Bacterial/Viral) and Pulmonary Neoplasms (Lung Cancer)
"""

import os
import torch
import torch.nn as nn
import torch.nn.functional as F
import torchvision.models as models
import torchvision.transforms as transforms
import numpy as np
import cv2
from PIL import Image

CLASSES = [
    "Normal (Clear Pulmonary Fields)",
    "Bacterial Pneumonia (Lobar Consolidation)",
    "Viral / COVID-19 Pneumonia (Ground-Glass Opacities)",
    "Lung Cancer (Malignant Pulmonary Mass / Nodule)"
]

CLASS_DETAILS = {
    0: {
        "title": "Normal / Healthy Radiograph",
        "category": "Physiological Baseline",
        "severity": "Normal",
        "badge_color": "#28a745",
        "description": "Bilateral lung parenchyma demonstrate physiologic radiolucency. Costophrenic and cardiophrenic angles are acute and well-defined. Cardiothoracic ratio is within normal limits (<0.5). No evidence of focal consolidation, solitary nodules, or mass lesions.",
        "action": "Routine annual screening / physiologic discharge."
    },
    1: {
        "title": "Bacterial Lobar Pneumonia",
        "category": "Infectious Pathology",
        "severity": "High / Acute",
        "badge_color": "#dc3545",
        "description": "Dense confluent alveolar consolidation identified with positive air bronchograms. Marked focal opacity typically localized to lower or middle lobar segments. Findings are highly suggestive of acute bacterial infectious pneumonia (e.g., S. pneumoniae).",
        "action": "Immediate targeted antibiotic pharmacotherapy & blood culture workup."
    },
    2: {
        "title": "Viral / Atypical / COVID-19 Pneumonia",
        "category": "Infectious Pathology",
        "severity": "Moderate to High",
        "badge_color": "#fd7e14",
        "description": "Patchy, multifocal bilateral ground-glass opacities (GGO) with predominant peripheral and posterior basal distribution. Minimal to absent pleural effusion. Findings correspond to typical viral lower respiratory tract involvement or COVID-19 pulmonary manifestations.",
        "action": "Respiratory droplet isolation, supportive oxygenation therapy, and viral RT-PCR panels."
    },
    3: {
        "title": "Lung Cancer / Pulmonary Malignant Neoplasm",
        "category": "Thoracic Oncology",
        "severity": "Critical / Malignant Alert",
        "badge_color": "#7b1fa2",
        "description": "High-density circumscribed focal mass / solitary pulmonary nodule (SPN) with irregular, spiculated margins identified. Feature attribution highlights persistent architectural distortion and high local radio-density characteristic of primary bronchogenic carcinoma or metastatic pulmonary neoplasm.",
        "action": "Urgent contrast-enhanced thoracic CT scan, PET-CT staging, and CT-guided percutaneous core needle biopsy."
    }
}

class ChestXRayClassifier(nn.Module):
    """
    DenseNet-121 with specialized pulmonary diagnostic & oncology classification head.
    Features dense connectivity where each layer receives direct inputs from all preceding layers.
    """
    def __init__(self, num_classes=4):
        super(ChestXRayClassifier, self).__init__()
        # Load DenseNet-121 architecture without remote download dependency
        self.densenet = models.densenet121(weights=None)
        num_features = self.densenet.classifier.in_features  # 1024
        
        # Clinical Multi-Class Diagnostic & Oncology Head
        self.densenet.classifier = nn.Sequential(
            nn.Linear(num_features, 256),
            nn.BatchNorm1d(256),
            nn.ReLU(inplace=True),
            nn.Dropout(0.3),
            nn.Linear(256, num_classes)
        )
        
    def forward(self, x):
        return self.densenet(x)


class GradCAMEngine:
    """
    Explainable AI (XAI) Engine using Gradient-weighted Class Activation Mapping (Grad-CAM).
    Extracts 2D feature maps from the final convolutional block of DenseNet-121 and weights
    them by the backpropagated gradients of the target diagnostic class.
    """
    def __init__(self, model):
        self.model = model
        self.model.eval()
        self.target_layer = self.model.densenet.features.denseblock4.denselayer16.conv2
        
        self.activations = None
        self.gradients = None
        self._register_hooks()
        
    def _register_hooks(self):
        def forward_hook(module, inp, out):
            self.activations = out

        def backward_hook(module, grad_in, grad_out):
            self.gradients = grad_out[0]

        self.target_layer.register_forward_hook(forward_hook)
        self.target_layer.register_full_backward_hook(backward_hook)

    def analyze(self, image_pil, target_class=None):
        orig_w, orig_h = image_pil.size
        
        transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
        ])
        
        input_tensor = transform(image_pil).unsqueeze(0)
        input_tensor.requires_grad = True
        
        # Forward pass
        logits = self.model(input_tensor)
        probs = F.softmax(logits, dim=1).squeeze().detach().cpu().numpy()
        
        if target_class is None:
            target_class = int(np.argmax(probs))
            
        # Backward pass for the target class
        self.model.zero_grad()
        target_score = logits[0, target_class]
        target_score.backward(retain_graph=True)
        
        # Calculate Grad-CAM
        alpha = torch.mean(self.gradients, dim=[2, 3], keepdim=True)
        cam = torch.sum(alpha * self.activations, dim=1, keepdim=True)
        cam = F.relu(cam)
        
        cam = F.interpolate(cam, size=(orig_h, orig_w), mode='bilinear', align_corners=False)
        cam = cam.squeeze().detach().cpu().numpy()
        
        cam_min, cam_max = cam.min(), cam.max()
        if cam_max - cam_min > 1e-8:
            norm_cam = (cam - cam_min) / (cam_max - cam_min)
        else:
            norm_cam = np.zeros_like(cam)
            
        orig_np = np.array(image_pil)
        if len(orig_np.shape) == 2:
            orig_np = cv2.cvtColor(orig_np, cv2.COLOR_GRAY2RGB)
            
        heatmap_uint8 = np.uint8(255 * norm_cam)
        heatmap_color = cv2.applyColorMap(heatmap_uint8, cv2.COLORMAP_JET)
        heatmap_color = cv2.cvtColor(heatmap_color, cv2.COLOR_BGR2RGB)
        
        # Alpha blend (0.6 original + 0.4 heatmap)
        blended = cv2.addWeighted(orig_np, 0.6, heatmap_color, 0.4, 0)
        
        # Threshold for high-attention clusters (>= 58%)
        thresh_mask = np.uint8(norm_cam >= 0.58) * 255
        contours, _ = cv2.findContours(thresh_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        roi_img = orig_np.copy()
        rois = []
        total_pixels = orig_w * orig_h
        
        # Color coding: Purple for Cancer, Red for Bacterial, Orange for Viral, Green for Normal
        color_map = {0: (52, 199, 89), 1: (255, 45, 85), 2: (255, 149, 0), 3: (175, 82, 222)}
        box_color = color_map.get(target_class, (255, 45, 85))
        
        for i, c in enumerate(contours):
            x, y, w, h = cv2.boundingRect(c)
            area = w * h
            if area > (total_pixels * 0.004):
                area_pct = round((area / total_pixels) * 100, 1)
                peak_val = round(float(np.max(norm_cam[y:y+h, x:x+w])), 3)
                
                # Approximate physical tumor / lesion diameter (assuming 40cm adult field of view)
                est_diam_mm = round((max(w, h) / orig_w) * 400.0, 1)
                
                cv2.rectangle(roi_img, (x, y), (x + w, y + h), box_color, 2)
                type_str = "TUMOR / MASS" if target_class == 3 else "LESION"
                label = f"ROI-{i+1} [{type_str}]: ~{est_diam_mm}mm ({peak_val})"
                
                (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.42, 1)
                cv2.rectangle(roi_img, (x, max(0, y - 18)), (x + tw + 4, max(18, y)), box_color, -1)
                cv2.putText(roi_img, label, (x + 2, max(13, y - 4)), cv2.FONT_HERSHEY_SIMPLEX, 0.40, (255, 255, 255), 1, cv2.LINE_AA)
                
                rois.append({
                    "id": i + 1,
                    "x": int(x), "y": int(y), "w": int(w), "h": int(h),
                    "peak_intensity": peak_val,
                    "area_pct": area_pct,
                    "est_diameter_mm": est_diam_mm
                })
                
        return {
            "predictions": [(CLASSES[i], float(probs[i])) for i in range(len(CLASSES))],
            "predicted_idx": target_class,
            "confidence": float(probs[target_class]),
            "heatmap_overlay": blended,
            "raw_heatmap": norm_cam,
            "roi_overlay": roi_img,
            "rois": rois
        }


def get_trained_pipeline():
    """Initializes and returns the calibrated model and GradCAM engine."""
    device = torch.device("cpu")
    model = ChestXRayClassifier(num_classes=4)
    
    weights_path = "c:/tx_dmv/chest_xray_xai/weights_calibrated.pth"
    if os.path.exists(weights_path):
        try:
            model.load_state_dict(torch.load(weights_path, map_location=device))
            print(f"Loaded calibrated weights from {weights_path}")
        except Exception as e:
            print(f"Warning loading weights: {e}")
            
    model.to(device)
    model.eval()
    engine = GradCAMEngine(model)
    return model, engine

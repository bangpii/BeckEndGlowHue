import cv2
import numpy as np
import os

def change_skin_tone(image_path, hex_color):
    # Convert HEX ke BGR
    hex_color = hex_color.lstrip("#")
    target_rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    target_bgr = (target_rgb[2], target_rgb[1], target_rgb[0])

    # Baca gambar
    image = cv2.imread(image_path)
    if image is None:
        raise FileNotFoundError("Gambar tidak ditemukan!")

    # Convert ke RGB untuk processing
    img_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    
    # Advanced skin detection dengan protection untuk organ sensitif
    mask = detect_skin_protected(img_rgb)
    
    # Refine mask dengan preservasi detail
    mask = refine_mask_advanced(mask, img_rgb)
    
    # Apply natural skin tone change
    result = apply_natural_skin_tone(img_rgb, mask, target_bgr, image_path)
    
    return result

def detect_skin_protected(img_rgb):
    # Method 1: YCrCb dengan range yang lebih akurat
    img_ycrcb = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2YCrCb)
    lower_ycrcb = np.array([0, 133, 77], dtype=np.uint8)
    upper_ycrcb = np.array([255, 173, 127], dtype=np.uint8)
    mask_ycrcb = cv2.inRange(img_ycrcb, lower_ycrcb, upper_ycrcb)
    
    # Method 2: HSV dengan range yang lebih natural
    img_hsv = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2HSV)
    lower_hsv = np.array([0, 20, 40], dtype=np.uint8)
    upper_hsv = np.array([25, 160, 245], dtype=np.uint8)
    mask_hsv = cv2.inRange(img_hsv, lower_hsv, upper_hsv)
    
    # Method 3: RGB rules yang lebih selektif
    r, g, b = cv2.split(img_rgb)
    mask_rgb = ((r > 80) & (g > 40) & (b > 20) & 
                ((cv2.max(r, cv2.max(g, b)) - cv2.min(r, cv2.min(g, b))) > 20) & 
                (np.abs(r - g) > 10) & (r > g) & (r > b)).astype(np.uint8) * 255
    
    # Combine masks dengan priority
    combined_mask = cv2.bitwise_and(mask_ycrcb, mask_hsv)
    combined_mask = cv2.bitwise_or(combined_mask, mask_rgb)
    
    # Remove small noise
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    combined_mask = cv2.morphologyEx(combined_mask, cv2.MORPH_OPEN, kernel)
    
    return combined_mask

def refine_mask_advanced(mask, img_rgb):
    # Gaussian blur untuk edges yang sangat halus
    mask = cv2.GaussianBlur(mask, (9, 9), 2)
    
    # Normalize mask untuk soft transition
    mask_float = mask.astype(float) / 255.0
    
    # Create edge-aware mask
    edges = cv2.Canny(img_rgb, 50, 150)
    edges = cv2.dilate(edges, None, iterations=1)
    edges_mask = (edges == 0).astype(float)
    
    # Combine dengan edge protection
    mask_float = mask_float * edges_mask
    
    # Soft threshold untuk natural look
    mask_float = np.clip(mask_float * 1.1, 0, 0.95)  # Max 95% untuk natural look
    
    return (mask_float * 255).astype(np.uint8)

def apply_natural_skin_tone(img_rgb, mask, target_bgr, image_path):
    # Convert target ke RGB
    target_rgb = (target_bgr[2], target_bgr[1], target_bgr[0])
    
    # Normalize mask untuk alpha blending yang sangat halus
    mask_float = mask.astype(float) / 255.0
    
    result = img_rgb.copy().astype(float)
    
    # Preserve original image texture and details
    original_lab = cv2.cvtColor(img_rgb.astype(np.uint8), cv2.COLOR_RGB2LAB)
    original_lab = original_lab.astype(float)
    
    # Calculate target color in LAB space for better color matching
    target_color_patch = np.zeros((10, 10, 3), dtype=np.uint8)
    target_color_patch[:, :] = target_rgb
    target_lab = cv2.cvtColor(target_color_patch, cv2.COLOR_RGB2LAB)
    target_l = target_lab[0, 0, 0]
    target_a = target_lab[0, 0, 1]
    target_b = target_lab[0, 0, 2]
    
    # Apply color change dengan natural blending dan texture preservation
    for c in range(3):
        original_channel = img_rgb[:, :, c].astype(float)
        target_value = target_rgb[c]
        
        # Very subtle blending dengan texture preservation
        blend_strength = 0.6  # Reduced untuk lebih natural
        blended = original_channel * (1 - mask_float * blend_strength) + \
                 target_value * mask_float * blend_strength
        
        # Maintain original texture dengan high-frequency details
        original_detail = original_channel - cv2.GaussianBlur(original_channel, (0, 0), 1)
        blended = blended + original_detail * 0.3
        
        result[:, :, c] = np.clip(blended, 0, 255)
    
    # Final smoothing untuk natural look
    result = cv2.GaussianBlur(result, (0, 0), 0.8)
    result_uint8 = result.astype(np.uint8)
    
    # Soft glow effect
    glow = cv2.GaussianBlur(result_uint8, (0, 0), 1.2)
    result_uint8 = cv2.addWeighted(result_uint8, 0.85, glow, 0.15, 0)
    
    # Convert back ke BGR untuk OpenCV
    result_bgr = cv2.cvtColor(result_uint8, cv2.COLOR_RGB2BGR)
    
    # Simpan hasil
    output_path = os.path.join(
        os.path.dirname(image_path),
        "processed_" + os.path.basename(image_path)
    )
    cv2.imwrite(output_path, result_bgr)
    return output_path
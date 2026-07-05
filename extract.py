import os
import sys
import pydicom
from llama_cpp import Llama

def get_model_path():
    if getattr(sys, 'frozen', False):
        base_dir = os.path.dirname(sys.executable)
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, "Llama-3.2-3B-Instruct-Q4_K_M.gguf")

_llm = None

def get_llm():
    global _llm
    if _llm is None:
        model_path = get_model_path()
        if not os.path.exists(model_path):
            raise FileNotFoundError(
                f"Model file not found at: {model_path}\n"
                f"Download Llama-3.2-3B-Instruct-Q4_K_M.gguf from HuggingFace "
                f"and place it in the gridsift folder."
            )
        _llm = Llama(model_path=model_path, n_ctx=2048, verbose=False)
    return _llm

def normalize_with_rules(series_description):
    if not series_description:
        return "unknown"
    text = series_description.lower()
    if any(k in text for k in ["flair", "stir", "fluid"]):
        return "FLAIR"
    if any(k in text for k in ["dwi", "diffusion", "dti", "adc"]):
        return "DWI"
    if any(k in text for k in ["dce", "perfusion", "dynamic contrast", "contrast"]):
        return "DCE"
    if any(k in text for k in ["t1", "mprage", "spgr", "tfe", "bravo", "vibe"]):
        return "T1"
    if any(k in text for k in ["t2"]):
        return "T2"
    if any(k in text for k in ["localizer", "localiser", "scout", "survey", "loc"]):
        return "localizer"
    return "unknown"

def normalize_with_llm(series_description):
    truncated = series_description[:100] if series_description else ""
    prompt = f"""<|start_header_id|>system<|end_header_id|>
You are a medical imaging classifier. Classify MRI series descriptions into exactly one of these labels: T1, T2, FLAIR, DWI, DCE, localizer, unknown.
DCE includes any contrast-enhanced, dynamic, or perfusion sequences.
DWI includes diffusion, DTI, ADC, and any sequence with DIFFUSION in the name.
Respond with only the label, nothing else.<|eot_id|><|start_header_id|>user<|end_header_id|>
Series: {truncated}<|eot_id|><|start_header_id|>assistant<|end_header_id|>
"""
    output = get_llm()(prompt, max_tokens=10, stop=["<|eot_id|>", "\n"])
    label = output["choices"][0]["text"].strip()
    if label not in ["T1", "T2", "FLAIR", "DWI", "DCE", "localizer", "unknown"]:
        return "unknown"
    return label

def extract_metadata(filepath):
    ds = pydicom.dcmread(filepath)
    return {
        "series_uid": ds.get("SeriesInstanceUID", None),
        "modality": ds.get("Modality", None),
        "series_description": ds.get("SeriesDescription", None),
        "echo_time": float(ds.get("EchoTime", 0) or 0),
        "repetition_time": float(ds.get("RepetitionTime", 0) or 0),
        "flip_angle": float(ds.get("FlipAngle", 0) or 0),
        "inversion_time": float(ds.get("InversionTime", 0) or 0),
        "slice_thickness": ds.get("SliceThickness", None),
        "field_strength": ds.get("MagneticFieldStrength", None),
    }

def physics_filter(meta):
    modality = meta["modality"]
    TE = meta["echo_time"]
    TR = meta["repetition_time"]
    FA = meta["flip_angle"]
    TI = meta["inversion_time"]

    if modality == "CT":
        return "CT", 0.99

    if modality != "MR":
        return "unknown", 0.0

    if TI > 0 and TR > 2000 and TE > 50:
        return "FLAIR", 0.90

    if TE > 0 and TR > 0:
        if TE < 30 and TR < 1000:
            return "T1", 0.85
        if TE > 60 and TR > 2000:
            return "T2", 0.85

    if FA > 0 and FA < 30 and TR < 50:
        return "T1", 0.75

    return "ambiguous", 0.0

def classify_series(filepath):
    meta = extract_metadata(filepath)
    label, confidence = physics_filter(meta)

    if label == "ambiguous":
        label = normalize_with_rules(meta["series_description"] or "")
        if label == "unknown":
            try:
                label = normalize_with_llm(meta["series_description"] or "")
            except FileNotFoundError:
                label = "unknown"
        confidence = 0.6 if label != "unknown" else 0.0

    return {
        "series_uid": meta["series_uid"],
        "series_description": meta["series_description"],
        "label": label,
        "confidence": confidence,
        "decision_path": "physics" if confidence >= 0.75 else "rules/llm"
    }

if __name__ == "__main__":
    meta = extract_metadata(r"C:\Users\Joseph Choi\Downloads\mrbrain.dcm")
    label, confidence = physics_filter(meta)
    print(f"Series: {meta['series_description']}")
    print(f"Label: {label}")
    print(f"Confidence: {confidence}")

    print("\nRule-based normalization test:")
    print(f"flair ax 3: {normalize_with_rules('flair ax 3')}")
    print(f"sag t1 mprage: {normalize_with_rules('sag t1 mprage')}")
    print(f"AX DIFFUSION: {normalize_with_rules('AX DIFFUSION')}")
    print(f"survey: {normalize_with_rules('survey')}")
    print(f"Coronal two-phase IV contrast: {normalize_with_rules('Coronal two-phase IV contrast fat suppressed; temp posn, stacks')}")

    print("\nFull pipeline test:")
    result = classify_series(r"C:\Users\Joseph Choi\Downloads\ct-pancreas-pancreas-ct-instance.dcm")
    for key, value in result.items():
        print(f"{key}: {value}")
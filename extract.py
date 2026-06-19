import pydicom
from llama_cpp import Llama

llm = Llama(
    model_path=r"C:\Users\Joseph Choi\Documents\dicom_classifier\Phi-3-mini-4k-instruct-q4.gguf",
    n_ctx=512,
    verbose=False
)

def normalize_with_llm(series_description):
    truncated = series_description[:100] if series_description else ""
    prompt = f"""Classify this MRI series into exactly one label: T1, T2, FLAIR, DWI, DCE, localizer, unknown.
Series: {truncated}
Label:"""
    
    output = llm(prompt, max_tokens=10, stop=["\n"])
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
        label = normalize_with_llm(meta["series_description"] or "")
        confidence = 0.6 if label != "unknown" else 0.0
    
    return {
        "series_uid": meta["series_uid"],
        "series_description": meta["series_description"],
        "label": label,
        "confidence": confidence,
        "decision_path": "physics" if confidence >= 0.75 else "llm"
    }

if __name__ == "__main__":
    meta = extract_metadata(r"C:\Users\Joseph Choi\Downloads\mrbrain.dcm")
    label, confidence = physics_filter(meta)
    print(f"Series: {meta['series_description']}")
    print(f"Label: {label}")
    print(f"Confidence: {confidence}")

    ambiguous_meta = {
        "series_uid": "1.2.3.4.5",
        "modality": "MR",
        "series_description": "flair ax 3",
        "echo_time": 0.0,
        "repetition_time": 0.0,
        "flip_angle": 0.0,
        "inversion_time": 0.0,
        "slice_thickness": None,
        "field_strength": None,
    }

    label, confidence = physics_filter(ambiguous_meta)
    print(f"\nAmbiguous test:")
    print(f"Series: {ambiguous_meta['series_description']}")
    print(f"Label: {label}")
    print(f"Confidence: {confidence}")

    print("\nLLM normalization test:")
    result = normalize_with_llm("flair ax 3")
    print(f"Input: 'flair ax 3'")
    print(f"Output: {result}")

    print(normalize_with_llm("sag t1 mprage"))
    print(normalize_with_llm("AX DIFFUSION"))
    print(normalize_with_llm("survey"))
    print(normalize_with_llm("Coronal two-phase IV contrast fat suppressed; temp posn, stacks"))

    print("\nFull pipeline test:")
    result = classify_series(r"C:\Users\Joseph Choi\Downloads\ct-pancreas-pancreas-ct-instance.dcm")
    for key, value in result.items():
        print(f"{key}: {value}")
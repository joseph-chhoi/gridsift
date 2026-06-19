import os
import csv
import shutil
import pydicom
from extract import extract_metadata, physics_filter, classify_series

def find_dcm_files(folder_path):
    dcm_files = []
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if file.lower().endswith(".dcm"):
                dcm_files.append(os.path.join(root, file))
    return dcm_files

def group_by_series(dcm_files):
    groups = {}
    for filepath in dcm_files:
        try:
            ds = pydicom.dcmread(filepath, stop_before_pixels=True)
            uid = str(ds.get("SeriesInstanceUID", "unknown"))
            if uid not in groups:
                groups[uid] = []
            groups[uid].append(filepath)
        except Exception as e:
            print(f"Skipping unreadable file: {filepath}")
    return groups

def process_folder(folder_path, output_csv="results.csv"):
    print(f"Scanning folder: {folder_path}")
    
    dcm_files = find_dcm_files(folder_path)
    print(f"Found {len(dcm_files)} .dcm files")
    
    groups = group_by_series(dcm_files)
    print(f"Grouped into {len(groups)} series")
    
    results = []
    for uid, files in groups.items():
        representative_file = files[0]
        try:
            result = classify_series(representative_file)
            result["file_count"] = len(files)
            results.append(result)
            print(f"Series: {result['series_description']} → {result['label']} ({result['confidence']})")
        except Exception as e:
            print(f"Failed to classify series {uid}: {e}")
    
    with open(output_csv, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["series_uid", "series_description", "label", "confidence", "decision_path", "file_count"])
        writer.writeheader()
        writer.writerows(results)
    
    print(f"\nDone. Results saved to {output_csv}")
    return results

def sort_into_folders(folder_path, output_folder="output"):
    dcm_files = find_dcm_files(folder_path)
    groups = group_by_series(dcm_files)
    
    os.makedirs(output_folder, exist_ok=True)
    
    for uid, files in groups.items():
        representative_file = files[0]
        try:
            result = classify_series(representative_file)
            label = result["label"]
            confidence = result["confidence"]
            
            if confidence == 0.0 or label == "unknown":
                dest_folder = os.path.join(output_folder, "flagged_for_review")
            else:
                dest_folder = os.path.join(output_folder, label)
            
            os.makedirs(dest_folder, exist_ok=True)
            
            series_folder = os.path.join(dest_folder, uid)
            os.makedirs(series_folder, exist_ok=True)
            
            for filepath in files:
                filename = os.path.basename(filepath)
                dest_path = os.path.join(series_folder, filename)
                if not os.path.exists(dest_path):
                    shutil.copy2(filepath, dest_path)
            
            print(f"Sorted: {result['series_description']} → {label}/")
        
        except Exception as e:
            print(f"Failed to sort series {uid}: {e}")
    
    print(f"\nDone. Sorted output in: {output_folder}/")

if __name__ == "__main__":
    sort_into_folders(r"C:\Users\Joseph Choi\Downloads", output_folder=r"C:\Users\Joseph Choi\Documents\dicom_classifier\output")
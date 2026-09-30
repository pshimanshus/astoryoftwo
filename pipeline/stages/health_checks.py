from __future__ import annotations
import json
import re
from pathlib import Path
from typing import Any

def check_identity_loop(workspace_root: Path, carousel_dir: Path):
    print(f"🔍 auditing identity loop for: {carousel_dir.name}")
    
    # 1. Load Rules
    rules_path = workspace_root / "config/rules/identity.md"
    rules_text = rules_path.read_text(encoding="utf-8")
    
    # 2. Load Dossier
    dossier_path = workspace_root / "config/references/identity/_dossier/identity-dossier.json"
    dossier = json.loads(dossier_path.read_text(encoding="utf-8"))
    contract = dossier.get("face_identity_contract", {})
    
    # 3. Load Compiled Prompts (from a dummy run or existing output)
    # In a real scenario, we'd find the compiled prompts in the carousel dir.
    # For this health check, we'll assume there's a 'prompts.json' or similar.
    prompt_file = carousel_dir / "compiled_prompts.json"
    if not prompt_file.exists():
        print("❌ Error: compiled_prompts.json not found in carousel dir. Cannot verify prompt injection.")
        return
    
    prompts = json.loads(prompt_file.read_text(encoding="utf-8"))
    
    # 4. Load Pixel QA
    pixel_qa_file = carousel_dir / "pixel_qa.json"
    if not pixel_qa_file.exists():
        print("❌ Error: pixel_qa.json not found. Cannot verify pixel evidence.")
        return
    pixel_qa = json.loads(pixel_qa_file.read_text(encoding="utf-8"))
    
    # Trace loop for each subject
    for subject, details in contract.items():
        print(f"\nChecking loop for {subject}...")
        non_negotiables = details.get("non_negotiable", [])
        
        for desc in non_negotiables:
            # Rule -> Dossier (already implied by how we got non_negotiables)
            # Dossier -> Prompt
            found_in_prompt = False
            for slide_id, prompt_data in prompts.items():
                if desc.lower() in prompt_data.get("final_prompt", "").lower():
                    found_in_prompt = True
                    break
            
            # Prompt -> Pixel
            found_in_pixel = False
            for slide_record in pixel_qa.get("slides", []):
                reviews = slide_record.get("reviews", {})
                for fmt, review in reviews.items():
                    evidence = str(review.get("checks", {}).get("identity_wardrobe_accessories", {}).get("evidence", "")).lower()
                    if desc.lower() in evidence:
                        found_in_pixel = True
                        break
            
            status = "✅" if (found_in_prompt and found_in_pixel) else "❌"
            print(f"  {status} {desc[:40]}... [Prompt: {found_in_prompt}, Pixel: {found_in_pixel}]")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", type=str, default="/Users/himanshusharma/astoryoftwo-analysis")
    parser.add_argument("--carousel", type=str, required=True)
    args = parser.parse_args()
    check_identity_loop(Path(args.workspace), Path(args.carousel))

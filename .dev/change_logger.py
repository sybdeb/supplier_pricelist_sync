#!/usr/bin/env python3
"""
Development Change Logger
Houdt bij welke bestanden zijn gewijzigd tijdens development
"""
import os
import json
import hashlib
from datetime import datetime
from pathlib import Path

# Configuratie
MAX_LOGS = 50  # Bewaar maximaal 50 wijzigingen
LOG_FILE = Path(__file__).parent / "change_log.json"
WATCH_EXTENSIONS = ['.py', '.xml', '.csv', '.js', '.css']
PROJECT_ROOT = Path(__file__).parent.parent

def get_file_hash(filepath):
    """Bereken MD5 hash van bestand"""
    try:
        with open(filepath, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
    except:
        return None

def load_logs():
    """Laad bestaande logs"""
    if LOG_FILE.exists():
        with open(LOG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"changes": [], "file_hashes": {}}

def save_logs(data):
    """Bewaar logs"""
    LOG_FILE.parent.mkdir(exist_ok=True)
    with open(LOG_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def scan_changes():
    """Scan voor gewijzigde bestanden"""
    logs = load_logs()
    changes_found = []
    
    # Scan alle relevante bestanden
    for ext in WATCH_EXTENSIONS:
        for filepath in PROJECT_ROOT.rglob(f'*{ext}'):
            # Skip __pycache__ en .git
            if '__pycache__' in str(filepath) or '.git' in str(filepath):
                continue
            
            rel_path = str(filepath.relative_to(PROJECT_ROOT))
            current_hash = get_file_hash(filepath)
            
            if current_hash is None:
                continue
            
            # Controleer of bestand gewijzigd is
            old_hash = logs["file_hashes"].get(rel_path)
            if old_hash != current_hash:
                change_type = "modified" if old_hash else "new"
                changes_found.append({
                    "timestamp": datetime.now().isoformat(),
                    "file": rel_path,
                    "type": change_type,
                    "old_hash": old_hash,
                    "new_hash": current_hash
                })
                logs["file_hashes"][rel_path] = current_hash
    
    # Voeg nieuwe wijzigingen toe
    if changes_found:
        logs["changes"].extend(changes_found)
        
        # Cleanup oude logs (bewaar alleen laatste MAX_LOGS wijzigingen)
        if len(logs["changes"]) > MAX_LOGS:
            logs["changes"] = logs["changes"][-MAX_LOGS:]
        
        save_logs(logs)
        return changes_found
    
    return []

def show_deployments():
    """Toon beschikbare deployment snapshots"""
    logs = load_logs()
    deployments = [c for c in logs["changes"] if c.get("type") == "deployment"]
    
    if not deployments:
        print("❌ Geen deployment snapshots gevonden")
        return
    
    print(f"\n{'='*70}")
    print(f"Beschikbare Deployment Snapshots:")
    print(f"{'='*70}\n")
    
    for i, dep in enumerate(reversed(deployments), 1):
        dep_id = dep.get("deployment_id", "unknown")
        dep_time = dep.get("deployment_time", "unknown")
        print(f"{i}. 🚀 [{dep_time}] Deployment: {dep_id}")
        print(f"   Command: python change_logger.py revert {dep_id}")
        print()

def show_recent_changes(count=10):
    """Toon recente wijzigingen"""
    logs = load_logs()
    recent = logs["changes"][-count:]
    
    print(f"\n{'='*70}")
    print(f"Laatste {len(recent)} wijzigingen in supplier_pricelist_sync:")
    print(f"{'='*70}\n")
    
    for i, change in enumerate(reversed(recent), 1):
        timestamp = datetime.fromisoformat(change["timestamp"])
        time_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")
        
        if change["type"] == "deployment":
            icon = "🚀"
            dep_id = change.get("deployment_id", "unknown")
            print(f"{i}. {icon} [{time_str}] DEPLOYMENT: {dep_id}")
        else:
            icon = "📝" if change["type"] == "modified" else "✨"
            print(f"{i}. {icon} [{time_str}] {change['file']}")
            print(f"   Type: {change['type']}")
            if change.get('old_hash'):
                print(f"   Hash: {change['old_hash'][:8]} → {change['new_hash'][:8]}")
        print()

def create_deployment_snapshot():
    """Creëer deployment snapshot met wijzigings-ID"""
    import uuid
    deployment_id = str(uuid.uuid4())[:8]
    timestamp = datetime.now()
    
    logs = load_logs()
    
    # Voeg deployment marker toe
    deployment_marker = {
        "timestamp": timestamp.isoformat(),
        "file": "DEPLOYMENT",
        "type": "deployment",
        "deployment_id": deployment_id,
        "deployment_time": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
        "old_hash": None,
        "new_hash": deployment_id
    }
    
    logs["changes"].append(deployment_marker)
    save_logs(logs)
    
    print(f"\n🚀 DEPLOYMENT SNAPSHOT CREATED")
    print(f"   ID: {deployment_id}")
    print(f"   Time: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   Ready for Odoo deployment!")
    
    return deployment_id

def revert_to_deployment(deployment_id=None):
    """Revert naar een specifieke deployment of de laatste"""
    logs = load_logs()
    
    # Vind deployment markers
    deployments = [c for c in logs["changes"] if c.get("type") == "deployment"]
    
    if not deployments:
        print("❌ Geen deployment snapshots gevonden")
        return False
    
    # Selecteer deployment
    if deployment_id:
        target_deployment = None
        for dep in deployments:
            if dep.get("deployment_id", "").startswith(deployment_id):
                target_deployment = dep
                break
        if not target_deployment:
            print(f"❌ Deployment {deployment_id} niet gevonden")
            return False
    else:
        target_deployment = deployments[-1]  # Laatste deployment
    
    deployment_time = target_deployment["timestamp"]
    dep_id = target_deployment.get("deployment_id", "unknown")
    
    print(f"\n🔄 REVERTING TO DEPLOYMENT: {dep_id}")
    print(f"   Time: {target_deployment.get('deployment_time', 'unknown')}")
    
    # Vind alle wijzigingen sinds die deployment
    target_index = logs["changes"].index(target_deployment)
    changes_since = logs["changes"][target_index + 1:]
    
    reverted_files = []
    for change in reversed(changes_since):  # Revert in omgekeerde volgorde
        if change["type"] in ["modified", "new"] and change.get("old_hash"):
            file_path = PROJECT_ROOT / change["file"]
            if file_path.exists():
                # Hier zouden we de oude versie kunnen herstellen
                # Voor nu markeren we alleen wat gerevert zou worden
                reverted_files.append(change["file"])
    
    if reverted_files:
        print(f"\n📝 Bestanden die gerevert zouden worden:")
        for file in reverted_files:
            print(f"   - {file}")
        print(f"\n⚠️  REVERT FUNCTIE NOG NIET GEÏMPLEMENTEERD")
        print(f"   Gebruik git reset of handmatige restore voor nu")
    else:
        print("✅ Geen wijzigingen sinds deployment - niets te reverten")
    
    return True

def clear_old_logs():
    """Verwijder alle logs (reset)"""
    if LOG_FILE.exists():
        LOG_FILE.unlink()
    print("✓ Alle logs gewist")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "show":
            count = int(sys.argv[2]) if len(sys.argv) > 2 else 10
            show_recent_changes(count)
        elif sys.argv[1] == "clear":
            clear_old_logs()
        elif sys.argv[1] == "deploy":
            create_deployment_snapshot()
        elif sys.argv[1] == "revert":
            deployment_id = sys.argv[2] if len(sys.argv) > 2 else None
            revert_to_deployment(deployment_id)
        elif sys.argv[1] == "deployments":
            show_deployments()
        else:
            print("Gebruik: python change_logger.py [show|clear|deploy|revert|deployments] [deployment_id]")
    else:
        # Scan voor wijzigingen
        changes = scan_changes()
        if changes:
            print(f"\n✓ {len(changes)} wijziging(en) gedetecteerd:")
            for change in changes:
                icon = "📝" if change["type"] == "modified" else "✨"
                print(f"  {icon} {change['file']}")
        else:
            print("\n✓ Geen wijzigingen gedetecteerd")

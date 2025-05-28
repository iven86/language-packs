#!/usr/bin/env python3

import json
import os
import hashlib
from datetime import datetime
import sys

def calculate_sha256(file_path):
    """Calculate SHA-256 checksum of a file"""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        print(f"Warning: File not found: {file_path}")
        return None

def get_file_size(file_path):
    """Get file size in bytes"""
    try:
        return os.path.getsize(file_path)
    except FileNotFoundError:
        return 0

def count_cards_in_content(content_path):
    """Count total number of cards in content.json"""
    try:
        with open(content_path, 'r', encoding='utf-8') as f:
            content = json.load(f)
        
        total_cards = 0
        if 'categories' in content:
            for category in content['categories']:
                if 'cards' in category:
                    total_cards += len(category['cards'])
        return total_cards
    except (FileNotFoundError, json.JSONDecodeError):
        return 0

def get_language_from_metadata(metadata_path):
    """Extract source and target languages from metadata.json"""
    try:
        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        
        source_lang = metadata.get('source_language', '')
        target_lang = metadata.get('target_language', '')
        pack_id = metadata.get('pack_id', '')
        version = metadata.get('version', '1.0.0')
        
        return source_lang, target_lang, pack_id, version
    except (FileNotFoundError, json.JSONDecodeError):
        return '', '', '', '1.0.0'

def generate_pack_name(source_lang, target_lang, pack_id=''):
    """Generate a human-readable pack name"""
    lang_names = {
        'DE': 'German',
        'EN': 'English',
        'AR': 'Arabic'
    }
    
    source_name = lang_names.get(source_lang, source_lang)
    target_name = lang_names.get(target_lang, target_lang)
    
    # Determine if it's a phrases pack or basic pack
    if 'phrases' in pack_id.lower():
        return f"{source_name}-{target_name} Phrases"
    else:
        return f"{source_name}-{target_name} Basics"

def get_flag_url(lang_code):
    """Generate flag URL for a language code"""
    return f"https://raw.githubusercontent.com/iven86/language-packs/main/flags/{lang_code.lower()}.png"

def update_manifest():
    """Update manifest.json based on available language packs"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    manifest_path = os.path.join(base_dir, 'manifest.json')
    checksums_path = os.path.join(base_dir, 'checksums.sha256')
    
    # Load existing manifest or create new one
    try:
        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest = json.load(f)
    except FileNotFoundError:
        manifest = {
            "last_updated": "",
            "packs": []
        }
    
    # Scan for language pack directories
    packs = []
    checksums = []
    
    for item in os.listdir(base_dir):
        item_path = os.path.join(base_dir, item)
        
        # Skip if not a directory or if it's a known non-pack directory
        if not os.path.isdir(item_path) or item.startswith('.') or item in ['__pycache__']:
            continue
        
        content_path = os.path.join(item_path, 'content.json')
        metadata_path = os.path.join(item_path, 'metadata.json')
        
        # Skip if no content.json exists
        if not os.path.exists(content_path):
            continue
        
        print(f"Processing language pack: {item}")
        
        # Calculate checksum
        checksum = calculate_sha256(content_path)
        if checksum is None:
            continue
        
        # Get file size
        file_size = get_file_size(content_path)
        
        # Count cards
        card_count = count_cards_in_content(content_path)
        
        # Get language info from metadata
        source_lang, target_lang, pack_id, version = get_language_from_metadata(metadata_path)
        
        # Generate pack info
        if not pack_id:
            pack_id = f"{source_lang.lower()}_{target_lang.lower()}_A1"
        
        pack_name = generate_pack_name(source_lang, target_lang, pack_id)
        
        # Build pack entry
        pack_entry = {
            "pack_id": pack_id,
            "name": pack_name,
            "version": version,
            "languages": [source_lang, target_lang],
            "flag_urls": {
                source_lang: get_flag_url(source_lang),
                target_lang: get_flag_url(target_lang)
            },
            "size": card_count,
            "fileSize": file_size,
            "download_url": f"https://raw.githubusercontent.com/iven86/language-packs/refs/heads/main/{item}/content.json",
            "metadata_url": f"https://raw.githubusercontent.com/iven86/language-packs/refs/heads/main/{item}/metadata.json",
            "checksum": checksum
        }
        
        packs.append(pack_entry)
        
        # Add to checksums list
        checksums.append(f"{checksum}  {item}/content.json")
        
        print(f"  - Pack ID: {pack_id}")
        print(f"  - Languages: {source_lang} -> {target_lang}")
        print(f"  - Cards: {card_count}")
        print(f"  - File size: {file_size} bytes")
        print(f"  - Checksum: {checksum}")
    
    # Update manifest
    manifest["last_updated"] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    manifest["packs"] = sorted(packs, key=lambda x: x["pack_id"])
    
    # Write updated manifest
    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    
    print(f"\nManifest updated: {manifest_path}")
    print(f"Found {len(packs)} language packs")
    
    # Write checksums file
    if checksums:
        with open(checksums_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(sorted(checksums)) + '\n')
        
        print(f"Checksums updated: {checksums_path}")
    
    return True

if __name__ == "__main__":
    try:
        success = update_manifest()
        if success:
            print("\n✅ Manifest and checksums updated successfully!")
        else:
            print("\n❌ Failed to update manifest")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)

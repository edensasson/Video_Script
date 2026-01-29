import json
import os

from datetime import datetime

USER_DB_PATH = "user_profiles.json"

def get_voice_id_for_user(username):
    if not os.path.exists(USER_DB_PATH):
        return None
    
    with open(USER_DB_PATH, "r") as f:
        profiles = json.load(f)
    
    if username in profiles:
        user_data = profiles[username]
        
        if isinstance(user_data, str):
            return user_data  
        
        elif isinstance(user_data, dict):
            return user_data.get("voice_id")  # Extract "voice_id" from the object
        
        else:
            return None
    
    return None

def save_user_profile(username, voice_id):
    profiles = {}
    if os.path.exists(USER_DB_PATH):
        with open(USER_DB_PATH, "r") as f:
            profiles = json.load(f)
    
    # Save an OBJECT with metadata
    profiles[username] = {
        "voice_id": voice_id,
        "created_at": datetime.now().isoformat(),
        "last_updated": datetime.now().isoformat()
    }
    
    with open(USER_DB_PATH, "w") as f:
        json.dump(profiles, f, indent=4)
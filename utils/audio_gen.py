import os
from elevenlabs.client import ElevenLabs
from elevenlabs import save

import os
from elevenlabs.client import ElevenLabs
from elevenlabs import save

import requests

def create_instant_clone(name, file_path):
    """Clone a voice via the ElevenLabs REST API"""
    api_key = os.getenv("Eleven_Labs_Api_Key")
    
    if not api_key:
        print("❌ Missing API key!")
        return None
    
    url = "https://api.elevenlabs.io/v1/voices/add"
    headers = {"xi-api-key": api_key}
    
    data = {
        "name": name,
        "description": f"Clone for {name}",
        "labels": '{"source": "api_upload"}'
    }
    
    try:
        # Open the file and send it in the same context
        with open(file_path, "rb") as f:
            files = {
                "files": (os.path.basename(file_path), f, "audio/wav")
            }
            
            response = requests.post(url, headers=headers, data=data, files=files)
        
        if response.status_code == 200:
            voice_id = response.json().get("voice_id")
            print(f"✅ Voice ID created: {voice_id}")
            return voice_id
        else:
            print(f"❌ API Error (Code {response.status_code})")
            print(f"   Details: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None
        
def generate_final_audio(text, voice_id, settings):
    """
    Generates the final voiceover MP3 using the latest SDK syntax (v2.30.0).
    """
    client = ElevenLabs(api_key=os.getenv("Eleven_Labs_Api_Key"))
    
    # Default values if settings is None
    s = settings if settings else {"stability": 0.5, "similarity": 0.75, "style": 0.0}
    
    print(f"🎙️ Generating final audio with voice {voice_id}...")
    
    try:
        # New official SDK syntax v2.x
        audio = client.text_to_speech.convert(
            voice_id=voice_id,
            text=text,
            model_id="eleven_multilingual_v2",
            voice_settings={
                "stability": s.get("stability", 0.5),
                "similarity_boost": s.get("similarity", 0.75),
                "style": s.get("style", 0.0),
                "use_speaker_boost": True
            }
        )
        
        output_path = "final_voiceover.mp3"
        
        # The ElevenLabs save function knows how to handle this.
        save(audio, output_path)
        
        print(f"✅ Audio successfully saved to {output_path}")
        return output_path

    except Exception as e:
        print(f"❌ Generation Error: {e}")
        return None
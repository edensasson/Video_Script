import json
import os
from state import ProjectState
from config import GEMINI_CLIENT, GEMINI_MODEL
from utils.audio_gen import generate_final_audio  

def voice_expert_node(state: ProjectState):
    print("\n--- 🎙️ ELEVENLABS VOICE EXPERT ---")

    # 1. RETRIEVAL OF DATA
    action = state.get("force_action")
    messages = state.get("messages", [])
    current_script = state.get("script", "")
    iteration = state.get("iteration_count", 0)
    video_analysis = state.get("video_analysis", {})
    audio_path = state.get("audio_path")
    pending = state.get("pending_audio_feedback")
    user_input = state.get("user_instructions", "")
    
    # --- NEW TEXT EXTRACTION LOGIC ---
    target_text = current_script
    print("DEBUG: script received in Voice Expert:", current_script)
   
    if action in ["CHOOSE_A", "CHOOSE_B"]:
        # We use current_script directly which comes from res["clean_script"]
        if current_script:
            try:
                if action == "CHOOSE_A":
                    # We split between Variant A and B
                    target_text = current_script.split("Variant A")[1].split("Variant B")[0].strip(" :*\"")
                elif action == "CHOOSE_B":
                    # We take everything after Variant B (there are no more polite phrases here!)
                    target_text = current_script.split("Variant B")[1].strip(" :*\"")
                
                print(f"✅ Extraction successful from clean_script: '{target_text}'")
            except Exception as e:
                print(f"❌ Error during split of clean_script: {e}")
                target_text = current_script # Fallback
                
        else:
            print("❌ current_script is empty.")
            target_text = "Script not found."
                
    elif action == "VALIDATE":
        # If it's a simple validation, keep the current script
        target_text = current_script
    
    
    print(f"📝 FINAL TEXT SENT TO GEMINI: '{target_text}'")
    # TICKET MANAGEMENT
    # If there is a ticket (audio request waiting for the end of the script), we prioritize it
    user_input = pending if pending else state.get("user_instructions", "Suggest settings.")

    visual_style = video_analysis.get("semantic", {}).get("visual_style", {})
    energy = video_analysis.get("semantic", {}).get("energy_metrics", {})

    # 2. DYNAMIC MISSION 
    if state.get("voice_config") is None:
        current_mission = (
            "MISSION: AUDIO PROPOSAL. Analyze the script and video energy. "
            "Suggest specific ElevenLabs parameters (stability, similarity, style). "
            "Explain your reasoning based on the visual pacing (e.g., fast cuts need clearer, faster voice)."
        )
    else:
        current_mission = (
            "MISSION: AUDIO & SCRIPT REFINEMENT. The user is giving feedback on the voice settings "
            "Adjust the parameters . "
        )

    # 3. SYSTEM INSTRUCTION 
    system_instruction = f"""{current_mission}

[EXPERT ROLE]
You are a Senior Sound Designer. Your goal is to find the perfect vocal match for the visual content.

[VIDEO CONTEXT]
- Visual Style: {json.dumps(visual_style)}
- Energy Metrics: {json.dumps(energy)}
- Current Script: {target_text}

[OPERATIONAL RULES]
1. PARAMETER SETTINGS:
   - Stability (0.0 to 1.0): Lower is more emotive/variable, higher is more consistent.
   - Similarity Boost (0.0 to 1.0): Higher makes it closer to the original voice clone.
   - Style Exaggeration (0.0 to 1.0): Amplifies the specific style of the speaker.
2. FEEDBACK HANDLING: If the user wants to change a word in the script AND a voice setting, do both.
3. OUTPUT: Return ONLY a JSON object. Use the user's language for the 'explanation' field.
4.In your JSON response, the 'final_script' field MUST contain ONLY the 
spoken narration. Remove any conversational filler like "Here is your script", 
"I've polished it".

[OUTPUT SCHEMA]
Return a JSON with:
- 'explanation': Your human response explaining the choice of settings without mentioning technical details and numbers. MAXIMUM 3 sentences.
- 'suggested_voice': A descriptive name (e.g., 'Professional Male', 'Energetic Female').
- 'settings': {{ 'stability': float, 'similarity': float, 'style': float }}
- 'final_script': The script (updated or original).
"""

    # 4. SCHEMA 
    schema = {
        "type": "object",
        "properties": {
            "explanation": {"type": "string"},
            "suggested_voice": {"type": "string"},
            "settings": {
                "type": "object",
                "properties": {
                    "stability": {"type": "number"},
                    "similarity": {"type": "number"},
                    "style": {"type": "number"}
                },
                "required": ["stability", "similarity", "style"]
            },
            "final_script": {"type": "string"}
        },
        "required": ["explanation", "suggested_voice", "settings", "final_script"]
    }

    try:
        messages = state.get("messages", [])
        gemini_history = []
        for m in messages:
            role = "user" if (hasattr(m, 'type') and m.type == "human") else "model"
            content = m.content if hasattr(m, 'content') else str(m)
            gemini_history.append({"role": role, "parts": [{"text": content}]})
        
        # Inject user feedback or instructions
        gemini_history.append({"role": "user", "parts": [{"text": f"USER FEEDBACK: {user_input}"}]})

        response = GEMINI_CLIENT.models.generate_content(
            model=GEMINI_MODEL,
            contents=gemini_history,
            config={
                "system_instruction": system_instruction,
                "response_mime_type": "application/json",
                "response_schema": schema
            }
        )
        if not response.text:
            raise ValueError("Gemini returned an empty response")
        

        res = json.loads(response.text)
        print(f"📊 Audio settings: {res['settings']}")

        print(res.get('explanation'))
        audio_file = generate_final_audio(
            text=res['final_script'],
            voice_id=state.get("voice_id"),
            settings=res['settings']
        )
        # 5. RETURN STATE AND CLEAR TICKET
        return {
            **state,
            "audio_config": res['settings'],
            "script": res['final_script'],
            "audio_path": audio_file,       
            "force_action": None,
            "user_instructions": "",
            "pending_audio_feedback": None,
            "messages": [("assistant", res["explanation"])],
            "iteration_count": iteration + 1,
            "audio_explanation": res["explanation"], 

        
        }

    except Exception as e:
        print(f"❌ VoiceExpert Error: {e}")
        return {
            **state,
            "messages": [("assistant", "Sorry, I had a problem generating the audio.")]
        }
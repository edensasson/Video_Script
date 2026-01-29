import json
from state import ProjectState
from config import GEMINI_CLIENT, GEMINI_MODEL

def script_writer_node(state: ProjectState):
    """
    Agentic Node: Professional Scriptwriter acting as a Creative Partner.
    Follows a 4-phase collaborative workflow: Greeting -> Recap -> Variants -> Refinement.
    """  
    if state.get("force_action") in ["CHOOSE_A", "CHOOSE_B", "VALIDATE"]:
        return state
    print("\n--- 🧠 CREATIVE PARTNER SCRIPTWRITER ---")
    
    # 1. RETRIEVE STATE DATA
    video_analysis = state.get("video_analysis")
    user_input = state.get("user_instructions", "INIT_START")
    chat_history = state.get("messages", [])
    iteration = state.get("iteration_count", 0)
    username = state.get("username", "Partner") 
    
    if not video_analysis:
        print("❌ Error: No video analysis found.")
        return state

    # 2. DETERMINISTIC CONSTRAINTS
    duration_sec = video_analysis.get("technical", {}).get("duration_sec", 30)
    target_word_count = int((duration_sec / 60) * 150)

    # 3. PREPARE DATA LIBRARY
    context_library = {
        "CURRENT_BASE_SCRIPT": state.get("script", ""), 
        "technical_specs": {
            "duration_sec": duration_sec,
            "target_word_count": target_word_count,
            "total_cuts": video_analysis.get("technical", {}).get("total_cuts")
        },
        "visual_style": video_analysis.get("semantic", {}).get("visual_style", {}),
        "global_summary": video_analysis.get("global_summary", "Not provided"),
        "full_chronological_timeline": video_analysis.get("semantic", {}).get("timeline", [])
    }

    # 4. DYNAMIC MISSION DEFINITION 
    if iteration == 0:
        # PHASE 1: INITIAL QUESTIONS
        current_mission = (
            f"MISSION: Skip greetings. Start with a 4-word catchy sentence about the video. "
            "Ask 3 VERY BRIEF open-ended questions to understand the project. "
            "The questions must cover: 1. The Story/Memory, 2. The Audience, 3. The Visual Style/Pacing. "
            "CONSTRAINTS: USE BULLET POINT. EACH POINT MUST BE ON A NEW LINE. "
            "Be conversational and inspiring, not formal."
        )
    
    elif iteration == 1:
         # PHASE 2: ALIGNMENT & RECAP
        current_mission = (
            f"MISSION: ALIGNMENT. Start by telling {username} you want to make sure you're on the same page. "
            "Provide exactly VERY BRIEF bullet points summarizing your understanding of: "
            "1. The key visual moments from the video analysis. "
            "2. The specific tone requested in the user's prompt. "
            "3. The core message or goal of this video. "
            "Finish by asking {username} for a 'Go' to start writing the scripts. "
            "Keep it concise and professional."
        )
    elif iteration == 2:
         # PHASE 3: SCRIPT VARIATIONS - One shot 
        current_mission = ( 
            f"MISSION: VARIATIONS. Generate 2 distinct script variants (A and B) with different emotional styles. "
            f"Follow the {target_word_count} word limit per script. "
            f"EMOTIONAL STYLES: Choose from: Joyful, Funny, Serious, Salesy, Dramatic, Calm, Energetic, Inspirational, Mysterious, Educational. "
            f"Each variant MUST have a DIFFERENT style that matches the video content. "
            f"OUTPUT FORMAT: "
            f"1. 'chat_message': A warm 2-3 sentence message for {username}. NOTHING ELSE. No variants, no technical data. "
            f"2. 'clean_script': ONLY the structured technical format below (no conversational text): "
            f"   VARIANTE_A: [style name]|CONTENT_A: [full script text] "
            f"   VARIANTE_B: [style name]|CONTENT_B: [full script text] "
            f"CRITICAL: Keep 'chat_message' and 'clean_script' COMPLETELY SEPARATE. "
            f"Example chat_message: 'I've crafted two beautiful options for your pasta video, {username}! Let me know which vibe resonates with you.' "
            f"Example clean_script: 'VARIANTE_A: Energetic|CONTENT_A: Mix eggs with flour! Knead until smooth. Create magic! "
            f"VARIANTE_B: Calm|CONTENT_B: Gently whisk the eggs. Feel the texture. Take your time.' "
        )
        
    else:
        # PHASE 4+: REFINEMENT
        current_mission = (
            f"MISSION: REFINEMENT. Polish the chosen script based on feedback from {username}. "
            f"Ensure the pacing matches the {duration_sec}s duration."
        )

    # 5. SYSTEM INSTRUCTIONS
    system_instruction = f"""{current_mission}

[EXPERT ROLE]
You are a High-End Creative Director. Use a warm, professional, and empathetic tone. 
NEVER sound like a repetitive robot. Use {username}'s name naturally.

[DATA LIBRARY]
{json.dumps(context_library, indent=2)}

[OPERATIONAL RULES]
- USER EDITS ARE LAW: If 'CURRENT_BASE_SCRIPT' exists, you MUST use it as your ONLY starting point for any refinement.
-- Ignore older versions of the script found in the chat history if they differ from 'CURRENT_BASE_SCRIPT'.
- FEASIBILITY: Compare user intent with the {target_word_count} word limit. Use 'expert_warning' if requests are too long for {duration_sec}s.
- CONTINUITY: Reference previous chat history to show you are listening.
- PROPORTIONAL EDITING:
  * If the user asks for a specific change (ex: "change the first sentence"), you MUST keep 100% of the other sentences identical.
  * If the user asks for a global stylistic change (ex: "make it more childish", "more energetic"), you ARE allowed to rewrite the whole script to match that vibe.
- OUTPUT FORMATTING (CRITICAL):
  * 'chat_message': ONLY friendly conversational text for the user. NO variants, NO technical data, NO script content. This is what appears in the chat UI.
  * 'clean_script': ONLY structured technical data. At iteration 2 (variants), use the EXACT format: 'VARIANTE_A: [style]|CONTENT_A: [text]\nVARIANTE_B: [style]|CONTENT_B: [text]'. For refinements (iteration 3+), use ONLY the final narration text with no labels.
  * NEVER mix conversational language with technical data. Keep them COMPLETELY SEPARATE.

[OUTPUT]
Return ONLY a JSON object with these exact fields: source, raisonnement, expert_warning, chat_message, clean_script."""

    # 6. CONSTRUCT CONVERSATION HISTORY
    gemini_history = []
    for m in chat_history:
        role = "user" if m.type == "user" else "model"
        gemini_history.append({"role": role, "parts": [{"text": m.content}]})
    
    gemini_history.append({"role": "user", "parts": [{"text": f"USER DIRECTION: {user_input}"}]})
    
    # 7. RESPONSE SCHEMA (Enhanced for Human interaction)
    schema = {
        "type": "object",
        "properties": {
            "source": {"type": "string", "enum": ["summary", "timeline"]},
            "raisonnement": {"type": "string"},
            "expert_warning": {"type": "string"},
            "chat_message": {
                "type": "string", 
                "description": "ONLY the friendly conversational message for the user. NO technical data, NO variants text here."
            },
            "clean_script": {
                "type": "string", 
                "description": "The technical structured data with variants in the exact format required."
            }
        },
        "required": ["source", "raisonnement", "expert_warning", "chat_message", "clean_script"]
    }

    try:
        response = GEMINI_CLIENT.models.generate_content(
            model=GEMINI_MODEL,
            contents=gemini_history,
            config={
                "system_instruction": system_instruction,
                "response_mime_type": "application/json",
                "response_schema": schema
            }
        )
        
        res = json.loads(response.text)
        
        # LOGGING
        print(f"--- Strategy: {res['source']} ---")

        # 8. UPDATE STATE
        return {
            **state,
            "script": res["clean_script"], 
            "messages": [("assistant", res["chat_message"])],
            "iteration_count": iteration + 1,
            "user_instructions": "",
            "audio_path": None
        }

    except Exception as e:
        print(f"❌ ScriptWriter Error: {e}")
        return {**state, "script": f" Error is : {e}"}
import json
from langgraph.graph import StateGraph, START, END
from state import ProjectState
from nodes.video_analyzer import analyze_video_node
from nodes.script_writer import script_writer_node
from nodes.summarizer import global_summarizer_node
from nodes.voice_expert import voice_expert_node
from nodes.video_compositing import video_compositing_node
from config import GEMINI_CLIENT, GEMINI_MODEL


def get_next_step(state: ProjectState) -> str:
    
    action = state.get("force_action")
    print(f"DEBUG: [get_next_step] force_action is: '{action}'")
    audio_buffer = state.get("pending_audio_feedback")
    iteration = state.get("iteration_count", 0)
    user_input = state.get("user_instructions", "")
    has_output = state.get("output_video_path") is not None
    has_audio = state.get("audio_path") is not None
    print(f"DEBUG: input='{user_input}' | has_audio={has_audio} | has_output={has_output}")
    if action in ["CHOOSE_A", "CHOOSE_B"]:
        print(f"🚀 [get_next_step] Choice '{action}' -> Routing to Voice Expert")
        return "voice_expert"
    
    # --- CASE 1: "VALIDATE" BUTTON CLICKED ---
    if action == "VALIDATE":
        # If there is audio feedback pending (e.g., "faster"), we MUST go to voice expert
        if audio_buffer:
            print("🔘 Validation with audio feedback pending -> To Voice Expert")
            return "voice_expert"
        
        # If there is no audio yet
        if not state.get("audio_path"):
            return "voice_expert"
            
        # Otherwise, it's a final validation
        return "end"    
   
    if action == "SAVE":
        print("💾 Saving project and ending workflow.")
        return "end"
    messages = state.get("messages", [])
    last_is_human = messages and hasattr(messages[-1], 'type') and messages[-1].type == "human"
    
    if last_is_human or (user_input and user_input != "INIT_START"):
        print(f"🧠 New user message detected: '{user_input}'")
    
    elif messages:
        last_msg = messages[-1]
        if hasattr(last_msg, 'type') and last_msg.type == "ai":
            print("--- ✋ The AI has responded, stopping to wait for the user ---")
            return "wait"
        
    if iteration <= 2:
        print(f"🛠️ Design phase (Iter {iteration}) -> ScriptWriter")
        return "script_writer"
    
    iteration = state.get("iteration_count", 0)
    script = state.get("script", "")
    script_preview = script[:300] if script else "EMPTY"
    has_audio_config = state.get("audio_config") is not None
    # FORCE the passage through script_writer at the beginning
    if iteration == 0 or not script or user_input == "INIT_START":
        return "script_writer"
    
    print(f"🔍 DEBUG ROUTER - Input: '{user_input}'")
    print(f"🔍 DEBUG ROUTER - Script Length: {len(script) if script else 0}")
    print(f"🔍 DEBUG ROUTER - Has Audio Config: {has_audio}")

    system_prompt = f"""
    You are the Studio Director.
    CONTEXT:
    - Script preview : {script_preview}
    - Voice settings already defined: {has_audio_config}
    Analyze this user message: "{user_input}"
    
    ROUTING LOGIC:
    1. PRE-PRODUCTION PHASE (If Video/Audio produced is False):
    ALWAYS route to 'script_writer'. Any user text is for improving the script before validation.

    2. RECTIFICATION PHASE (If Video/Audio produced is True):
    - If change is ONLY about text/words: route to 'script_writer'.
    - If change is ONLY about voice (tone, speed, pitch, voice): route to 'voice_expert'.
    - If BOTH: route to 'script_writer' and extract the audio request.

    OUTPUT FORMAT:
    Return ONLY a JSON object:
    {{
      "decision": "script_writer" | "voice_expert" ,
      "is_mixed": boolean,
      "audio_extraction": "The specific audio part of the request, or null"
    }}
    """
    gemini_history = []
    for m in messages[-3:]: # We provide at least the last 3 exchanges for context
        role = "user" if (hasattr(m, 'type') and m.type == "human") else "model"
        content = m.content if hasattr(m, 'content') else str(m)
        gemini_history.append({"role": role, "parts": [{"text": content}]})

    # Add the current message
    gemini_history.append({"role": "user", "parts": [{"text": system_prompt}]})
    # Structured request to Gemini
    response = GEMINI_CLIENT.models.generate_content(
        model=GEMINI_MODEL,
        contents=gemini_history,
        config={"response_mime_type": "application/json"}
    )
    
    try:
        res = json.loads(response.text)
        decision = res.get("decision", "script_writer")
        
        # --- BUFFER MANAGEMENT (MEMORY) ---
        # Only fill the buffer if the request is mixed
        if res.get("is_mixed") and res.get("audio_extraction"):
            state["pending_audio_feedback"] = res["audio_extraction"]
            print(f"📌 Memory: Audio request saved for later: {res['audio_extraction']}")
        
        return decision if decision in ["script_writer", "voice_expert", "end"] else "script_writer"
    
    except Exception as e:
        print(f"⚠️ Router Error: {e}")
        return "script_writer"
    
    
def compile_graph() -> object:
    workflow = StateGraph(ProjectState)

    # 1. Nodes registration 
    workflow.add_node("video_analyzer", analyze_video_node)
    workflow.add_node("summarizer", global_summarizer_node) 
    workflow.add_node("script_writer", script_writer_node)
    workflow.add_node("voice_expert", voice_expert_node) 
    workflow.add_node("video_compositing", video_compositing_node)

    # 2. Linear Start
    workflow.add_edge(START, "video_analyzer")
    workflow.add_edge("video_analyzer", "summarizer")

    workflow.add_conditional_edges(
        "summarizer",
        get_next_step,
        {
            "script_writer": "script_writer",
            "voice_expert": "voice_expert",
            "end": END,
            "wait": END
        }
    )
    # 3. Intelligent Feedback Loops
    workflow.add_conditional_edges(
        "script_writer",
        get_next_step, 
        {
            "script_writer": "script_writer",
            "voice_expert": "voice_expert",
            "end": END,
            "wait": END
        }
    )

    workflow.add_edge("voice_expert", "video_compositing")

    workflow.add_conditional_edges(
        "video_compositing",
        get_next_step,
        {
            "script_writer": "script_writer",
            "voice_expert": "voice_expert",
            "end": END,
            "wait" : END
        }
    )

    return workflow.compile()
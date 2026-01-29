import json
from state import ProjectState
from config import GEMINI_CLIENT, GEMINI_MODEL

def global_summarizer_node(state: ProjectState):
    """
    Summarization Node: Synthesizes the full timeline into a core narrative.
    """
    print("\n--- 📝 GLOBAL SUMMARIZER ---")
    
    video_analysis = state.get("video_analysis", {})    
    if video_analysis.get("global_summary"):
        print("--- ⏭️ SUMMARY ALREADY EXISTS, SKIPPING ---")
        return state
    timeline = video_analysis.get("semantic", {}).get("timeline", [])
    
    if not timeline:
        return {"video_analysis": video_analysis} # Return current state if no data

    prompt = f"""Based on this video timeline, provide a concise 3-line global summary 
    covering the main topic, the vibe, and key visual beats.
    
    DATA: {json.dumps(timeline)}
    OUTPUT: 3 sentences maximum."""
    
    try:
        response = GEMINI_CLIENT.models.generate_content(
            model=GEMINI_MODEL,
            contents=[{"role": "user", "parts": [{"text": prompt}]}]
        )
        summary = response.text.strip()
        
        # We create a deep copy to respect immutability
        updated_analysis = json.loads(json.dumps(video_analysis)) 
        updated_analysis["global_summary"] = summary
        
        return {**state,
                "video_analysis": updated_analysis}
        
    except Exception as e:
        print(f"❌ Summarizer Error: {e}")
        return state
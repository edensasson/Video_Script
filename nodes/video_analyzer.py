import os
import json
import time
from scenedetect import detect, ContentDetector
from moviepy import VideoFileClip
from state import ProjectState
from config import GEMINI_CLIENT, GEMINI_MODEL 

def analyze_video_node(state: ProjectState):
    """
    Extracts structural metrics (PySceneDetect) and semantic context (Gemini).
    """
    video_analysis = state.get("video_analysis")
    if video_analysis is not None and len(video_analysis) > 0:
        print("--- ⏭️ ANALYSIS ALREADY DONE, SKIPPING ---")
        return state
    print("--- STARTING VIDEO CONTEXT EXTRACTION ---")
    
    video_path = state.get("video_path")
    
    if not video_path or not os.path.exists(video_path):
        return {"messages": [("system", "Error: Video file not found.")]}

    # --- PART 1: STRUCTURAL ANALYSIS ---
    scene_list = detect(video_path, ContentDetector(threshold=27.0))
    num_cuts = len(scene_list)
    
    clip = VideoFileClip(video_path)
    duration_sec = clip.duration
    clip.close()
    
    technical_stats = {
        "duration_sec": round(duration_sec, 2),
        "total_cuts": num_cuts,
        "cuts_per_minute": round((num_cuts / duration_sec) * 60, 2) if duration_sec > 0 else 0,
        "avg_shot_duration": round(duration_sec / num_cuts, 2) if num_cuts > 0 else duration_sec
    }

    # --- PART 2: SEMANTIC ANALYSIS  ---
    
    #  Upload video
    print("Uploading video to Gemini...")
    video_file = GEMINI_CLIENT.files.upload(file=video_path)
    print("Waiting for Gemini to process the video...")
    while video_file.state.name == "PROCESSING":
        time.sleep(2)
        video_file = GEMINI_CLIENT.files.get(name=video_file.name)
    
    if video_file.state.name == "FAILED":
        raise ValueError("Gemini video processing failed.")
    print("✅ Video ready for analysis.")

    tech_context = f"""
    [SYSTEM METRICS]
    - Total Duration: {technical_stats['duration_sec']}s
    - Cut Density: {technical_stats['cuts_per_minute']} cuts/min
    - Average Shot Pace: {technical_stats['avg_shot_duration']}s
    """

    # CoT and role prompting 
    prompt = f"""
    Act as a Dual-Core Visual Analyst. Use the provided technical metadata to anchor your analysis:
    {tech_context}

    ### STEP 1: FACTUAL OBSERVATION (TIMELINE)
    Analyze the video to create a precise chronological breakdown. 
    - Focus strictly on visible actions, subjects, and camera changes.
    - Ensure the start/end timestamps are realistic based on the total duration provided.

    ### STEP 2: CREATIVE DIRECTION (STYLE & ENERGY)
    Interpret the visual style and movement dynamics by focusing on these 5 specific metrics:
    1. CAMERA WORK: Identify the behavior (static, drone, handheld, etc.).
    2. LIGHTING VIBE: Define the aesthetic (e.g., studio, cinematic dark, natural).
    3. VISUAL COMPLEXITY: Rate 1-10 how "busy" or crowded the frames are.
    4. VISUAL ENERGY: Rate 1-10 the intensity of movement and editing.
    5. PACING EVOLUTION: Determine if the rhythm is Consistent, Accelerating, or Decelerating based on the Cut Density.

    ---

    ### OUTPUT RULES
    - Return ONLY a raw JSON object.
    - No markdown formatting, no conversational text.

    ### JSON SCHEMA
    {{
    "timeline": [
        {{
        "start": 0.0,
        "end": 0.0,
        "visual_summary": "string"
        }}
    ],
    "visual_style": {{
        "camera_work": "string",
        "lighting_vibe": "string",
        "visual_complexity_score": "1-10"
    }},
    "energy_metrics": {{
        "visual_energy": "1-10",
        "pacing_evolution": "string"
    }}
    }}
    """

    # Response from Gemini
    print(f"🎬 Analyzing video with {GEMINI_MODEL}...")
    response = GEMINI_CLIENT.models.generate_content(
        model=GEMINI_MODEL,
        contents=[video_file, prompt]
    )
    
    text_response = response.text
    # Clean JSON
    clean_json = text_response.replace('```json', '').replace('```', '').strip()
    
    try:
        semantic_analysis = json.loads(clean_json)
        analysis_result = {
            "semantic": semantic_analysis,
            "technical": technical_stats
        }
    except json.JSONDecodeError:
        print("⚠️ Failed to parse Gemini JSON. Raw response saved.")
        analysis_result = {"raw": text_response, "technical": technical_stats}

    return {
        **state, 
        "video_analysis": analysis_result,
        "messages": [("system", f"Analysis ready: {technical_stats['total_cuts']} cuts found.")]
    }
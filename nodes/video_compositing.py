import os
from moviepy import VideoFileClip, AudioFileClip
from state import ProjectState

def video_compositing_node(state):
    print("\n--- 🎬 VIDEO COMPOSITING ---")
    
    video_path = state.get("video_path")
    audio_path = state.get("audio_path")
    
    if not video_path or not audio_path:
        print("❌ Error: Missing video or audio paths.")
        return state

    video_clip = None
    audio_clip = None

    try:
# 1. Load the clips
        video_clip = VideoFileClip(video_path)
        audio_clip = AudioFileClip(audio_path)
        
        # 2. Remove existing audio from the video to avoid conflicts
        video_without_audio = video_clip.without_audio() # v2.0 syntax
        
        # 3. Add the new audio
        final_video = video_without_audio.with_audio(audio_clip)

        output_path = "final_output_project.mp4"
        
        # 4. Export the final video
        final_video.write_videofile(
            output_path, 
            codec="libx264", 
            audio_codec="libmp3lame", 
            temp_audiofile='temp-audio.mp3',
            remove_temp=True,
            fps=video_clip.fps 
        )
        
        print(f"✅ Video generated: {output_path}")
        
        username = state.get("username")
        final_msg = (
            f"✨ **Video Ready!** I've combined everything for you, {username}.\n\n"
            "How do you like it? \n"
            "👉 Select 'Download' to **Save** and finish.\n"
            "👉 Or tell me if you want to **modify** the script or the voice settings."
        )
        
        if "messages" not in state or state["messages"] is None:
            state["messages"] = []
            
        state["messages"].append(("system", f"Compositing successful: {output_path}"))
        return {
                    **state,
                    "force_action": None,
                    "user_instructions": "", 
                    "messages": [("assistant", final_msg)], 
                    "iteration_count": state.get("iteration_count", 0) + 1,
                    "output_video_path": output_path
        }
    except Exception as e:
        print(f"❌ Error during compositing: {e}")
        if "messages" not in state or state["messages"] is None:
            state["messages"] = []
        state["messages"].append(("system", f"Error: {str(e)}"))
        return state
    finally:
        if video_clip: video_clip.close()
        if audio_clip: audio_clip.close()
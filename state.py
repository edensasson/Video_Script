from typing import Annotated, TypedDict, List, Optional
from langgraph.graph.message import add_messages

def merge_force_action(left: Optional[str], right: Optional[str]) -> Optional[str]:
    return right

class ProjectState(TypedDict):
    
    messages: Annotated[List, add_messages] # Chat history: accumulates all interaction
    force_action: Annotated[Optional[str], merge_force_action]    # Current user intent or revision request
    user_instructions: Optional[str]   # Latest user input or instructions
    username: str 
    video_path: Optional[str]   # Path to the uploaded video file
    output_video_path: str   # Path to the final output video
    video_analysis: Optional[dict] # Video content analysis
    script: Optional[str] # The generated script text
    iteration_count: int     # Counter to track revisions

        # Audio generation details
    pending_audio_feedback: Optional[str] 
    audio_config: Optional[dict] 
    voice_id: Optional[str]
    audio_path: Optional[str]
    audio_explanation: Optional[str]


# 🎬 Video Script AI Generator

An intelligent and interactive video scriptwriting system that analyzes video content and helps users create professional narration scripts with AI-generated voiceovers. The system is designed as a co-creative partner, keeping the user in control at every key creative decision.
---

## 💡 Overview

**Input**: Video file (MP4/MOV) - silent or with existing audio (will be replaced)
**Output**: Video with AI-generated voiceover matching the user's cloned voice (or ElevenLabs presets)

**Key design principle**: Human-in-the-loop validation at each stage rather than single-pass generation.

---

## 🛠️ System Architecture

This system uses **LangGraph** to implement a **conversational state machine** where the user progresses through stages but can refine outputs iteratively before moving forward.

### Workflow Pipeline

1. **Video Analysis**
   - **Scene Detection**: PySceneDetect extracts cuts and pacing
   - **Semantic Analysis**: Gemini analyzes visual content and context
   - Output: Structured scene data with timing and descriptions

2. **Script Generation** (4-phase dialogue)
   - **Discovery**: User answers questions about audience, tone, key message
   - **Alignment**: System confirms understanding of requirements
   - **Variants**: Generates 2 script options (A/B) with different approaches
   - **Refinement**: User selects variant OR provides feedback for iteration and continues until user clicks VALIDATE

3. **Voice Synthesis**
   - **Voice Cloning**: ElevenLabs creates voice model from user sample
   - **Parameter Tuning**: AI suggests style/similarity/stability  based on video energy
   - **Audio Generation**: Synthesizes narration with tuned parameters

4. **Compositing & Routing**
   - **Video Assembly**: MoviePy merges audio with original video
   - **Feedback Analysis**: Gemini interprets user comments to determine next action
   - **Routing Logic**: Returns to script/voice nodes or finalizes based on feedback

### Key Mechanisms

- **Intelligent Router**: After each step, analyzes user feedback (Gemini-powered) to route back to script/voice nodes or finalize
- **State Persistence**: All context maintained in `ProjectState` (chat history, iteration count, pending requests)
- **Non-linear Navigation**: Can return to any previous stage based on preview feedback

<details>
<summary>📋 View Complete ProjectState Schema</summary>

```python
{
      username: str
      video_path: Optional[str]   # Path to the uploaded video file
      video_analysis: Optional[dict] # Video content analysis
      user_instructions: Optional[str]   # Latest user input or instructions
      
      messages: Annotated[List, add_messages] # Chat history: accumulates all interaction
      force_action: Annotated[Optional[str], merge_force_action]    # Current user intent or revision request
      output_video_path: str   # Path to the final output video
      
      script: Optional[str] # The generated script text
      iteration_count: int     # Counter to track revisions

       # Audio generation details
       pending_audio_feedback: Optional[str] 
       audio_config: Optional[dict] 
       voice_id: Optional[str]
       audio_path: Optional[str]
       audio_explanation: Optional[str]
 ```
</details> 

---
## 🚀 Getting Started

### Prerequisites

Ensure you have the following installed:

- **Python 3.8+**
- **FFmpeg**
- **Google Gemini API key**
- **ElevenLabs API key**

---

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/edensasson/Video_Script.git
   cd Video_Script
   ```

2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

---

### Configuration

1. Copy the provided `.env.example` file to create your own `.env` file:
``` bash
   cp .env.example .env
```
2. Open the .env file and enter your credentials exactly as shown in the template:
 ```env  
#Google Gemini Configuration: 
GOOGLE_API_KEY=your_google_api_key_here

#ElevenLabs Configuration: 
 Eleven_Labs_Api_Key=your_elevenlabs_api_key_here
```
---

### Run the App

Start the Streamlit application:
```bash
streamlit run streamlit_app.py
```

 ---

 ## 📖 User Workflow

### First-Time Setup (One-time)
1. **Enter your username** → System checks for existing voice profile
2. **Upload video** → Analysis runs automatically
3. **Voice cloning prompt**:
   - If username not found → Option to record voice sample or skip
   - If profile exists → Uses saved `voice_id`

### Creating Your Video

1. **Discovery Phase** → Answer 3 questions about your video's story, audience, and style
2. **Script Generation** → Review 2 variants (A/B) with different tones
3. **Script Refinement**:
   - **Select a variant** (CHOOSE_A or CHOOSE_B) → Moves to voice phase
   - **OR provide feedback** → AI generates a new single refined script
   - **OR edit manually** → Direct text modification in the interface
   - Repeat until satisfied → Click **VALIDATE**
4. **Voice Preview** → AI suggests parameters → Compositor generates video preview
5. **Final Review**:
   - Watch complete result
   - Adjust voice (*"faster"*, *"more calm"*) → Regenerates audio
   - Change script → Returns to Script refinementphase (step 3) and regenerates a new audio
   - Click **SAVE** → Export final video

 **Iterative design**: You can refine script/voice 
   as many times as needed before clicking SAVE.
💡 **Key actions**: `CHOOSE_A/B` (select variant), `VALIDATE` (approve script/voice), `SAVE` (export)

⏱️ **Typical workflow**: 10-15 minutes for a 30-second video

---

## 📂 Project Structure

```
Video_Script/
├── streamlit_app.py          # Main Streamlit interface
├── graph.py                  # LangGraph workflow orchestration
├── state.py                  # Shared state definition (ProjectState)
├── config.py                 # Centralized Configuration
├── requirements.txt
├── .env.example
├── nodes/
│   ├── video_analyzer.py     # Scene + semantic analysis
│   ├── summarizer.py         # Global video summary
│   ├── script_writer.py      # Collaborative script generation
│   ├── voice_expert.py       # Audio parameter optimization
│   └── video_compositing.py  # Final video assembly
└── utils/
    ├── audio_gen.py          # ElevenLabs integration
    ├── recorder.py           # Voice recording for cloning
    └── user_manager.py       # User profiles
```

---

## 🛠️ Tech Stack

| **Category**       | **Technology**               |
| ------------------- | --------------------------- |
| **AI & LLM**       | Google Gemini 2.5 Flash     |
| **Orchestration**  | LangGraph                   |
| **Voice Synthesis**| ElevenLabs API             |
| **Video Processing**| MoviePy, PySceneDetect, OpenCV |
| **Audio Processing**| SciPy, sounddevice         |
| **UI**             | Streamlit                  |
| **State Management**| LangGraph + TypedDict         |

---

## 💾 Data Persistence & Privacy

To provide a personalized experience, the system manages local data storage:
* **`user_profiles.json`**: Automatically generated to store your unique ElevenLabs `voice_id` and metadata.
* **Privacy**: This file is excluded from version control to ensure your personal voice profiles and API usage remain local to your machine.
* **Uploads**: Video files are processed in a local `uploads/` directory.

## ⚠️ Limitations

- **Video format**: Best results with MP4/MOV, resolution 720p+, duration < 5 minutes
- **Voice cloning**: Requires 1-2 minutes of clear audio (single speaker, minimal background noise)
- **API costs**: Gemini and ElevenLabs usage may incur charges depending on your subscription
- **Processing time**: Video analysis ~30-60s per minute of footage; audio generation ~10-20s per script


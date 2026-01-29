import streamlit as st
import os
from graph import compile_graph
from utils.user_manager import get_voice_id_for_user, save_user_profile
from elevenlabs.client import ElevenLabs
from audio_recorder_streamlit import audio_recorder
import uuid
import shutil
import time

# Configuration
st.set_page_config(
    page_title="VideoScript AI",
    page_icon="✨",
    layout="wide"
)

# CSS
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #FFE5EC 0%, #E0F4FF 100%);
    }
    
    .block-container {
        padding-top: 2rem;
    }
    
    .user-message {
        background: linear-gradient(to right, #C499F3, #9BB5F3);
        color: white;
        padding: 1.2rem 1.8rem;
        border-radius: 1.5rem;
        margin: 0.5rem 0;
        margin-left: 20%;
        box-shadow: 0 2px 8px rgba(196, 153, 243, 0.3);
        font-size: 1.6rem;
    }
    
    .assistant-message {
        background: white;
        padding: 1.2rem 1.8rem;
        border-radius: 1.5rem;
        margin: 0.5rem 0;
        margin-right: 20%;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
        font-size: 1.6rem;
    }
    
    .stButton>button {
        background: linear-gradient(to right, #C499F3, #9BB5F3);
        color: white;
        border: none;
        border-radius: 2rem;
        padding: 0.9rem 2.5rem;
        font-weight: 600;
        font-size: 1.1rem;
    }
    
    /* Agrandir les champs de saisie */
    .stTextInput input {
        font-size: 1.6rem !important;
        padding: 0.75rem 1rem !important;
        height: 50px !important;
    }
    
    /* Agrandir les textes informatifs */
    .stAlert {
        font-size: 1.05rem !important;
    }
    
    /* Agrandir les titres de sections */
    h3 {
        font-size: 1.5rem !important;
    }
    
    /* Agrandir le texte dans les expanders */
    .streamlit-expanderContent {
        font-size: 1.05rem !important;
    }
</style>
""", unsafe_allow_html=True)

# =============================
# INITIALISATION
# =============================

if 'username' not in st.session_state:
    st.session_state.username = None
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'current_state' not in st.session_state:
    st.session_state.current_state = None
if 'graph' not in st.session_state:
    st.session_state.graph = None
if 'video_path' not in st.session_state:
    st.session_state.video_path = None
if 'show_voice_clone' not in st.session_state:
    st.session_state.show_voice_clone = False
if 'voice_cloning_done' not in st.session_state:
    st.session_state.voice_cloning_done = False
if 'initialized' not in st.session_state:
    st.session_state.initialized = False
if 'show_goodbye' not in st.session_state:
    st.session_state.show_goodbye = False
if 'compositing_triggered' not in st.session_state:
    st.session_state.compositing_triggered = False

# =============================
# PAGE GOODBYE
# =============================

if st.session_state.show_goodbye:
    st.markdown(f"""
    <div style='text-align: center; padding: 4rem; max-width: 600px; margin: 0 auto;'>
        <h1 style='color: #C499F3; font-size: 3.5rem; margin-bottom: 1rem;'>🎉 All Done!</h1>
        <div style='background: white; padding: 2.5rem; border-radius: 2rem; box-shadow: 0 4px 20px rgba(0,0,0,0.1);'>
            <p style='font-size: 1.5rem; color: #666; line-height: 1.8;'>
                Thanks <strong>{st.session_state.username}</strong>! 👋<br><br>
                Your video has been downloaded successfully.<br>
                See you soon for your next project! ✨
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("🏠 Start New Project", use_container_width=True, type="primary"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

# =============================
# PAGE 1 : WELCOME
# =============================

elif st.session_state.username is None:
    st.markdown("<h1 style='text-align: center; color: #C499F3; font-size: 3.5rem;'>✨ VideoScript AI</h1>", unsafe_allow_html=True)
    
    st.markdown("""
    <div style='text-align: center; padding: 2.5rem; max-width: 800px; margin: 0 auto; background: white; border-radius: 2rem; box-shadow: 0 4px 20px rgba(0,0,0,0.1);'>
        <p style='font-size: 1.6rem; color: #666; line-height: 1.8;'>
            Welcome to VideoScript AI! I'm here to help you bring your vision to life by guiding you 
            through a step-by-step collaborative process to craft the perfect script. Once our story 
            is set, I'll generate a professional voiceover and handle the final compositing for you. 
            Feel free to refine and adjust any detail along the way—we'll keep polishing until it's 
            exactly how you want it! 😉
        </p>
        <p style='font-size: 1.15rem; color: #888; margin-top: 1.5rem; font-weight: 600;'>
            Ready to start? Please enter your name and upload your video below to begin our collaboration.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        name = st.text_input("👤 Your Name", placeholder="Enter your name...")
    
    with col2:
        video_file = st.file_uploader("🎬 Upload Video", type=['mp4', 'mov', 'avi'])
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    if name and video_file:
        if st.button("🚀 Start Collaboration", use_container_width=True, type="primary"):
            video_path = f"uploads/{video_file.name}"
            os.makedirs("uploads", exist_ok=True)
            with open(video_path, "wb") as f:
                f.write(video_file.getbuffer())
            
            voice_id = get_voice_id_for_user(name)
            has_voice = voice_id is not None
            
            st.session_state.username = name
            st.session_state.video_path = video_path
            st.session_state.has_voice = has_voice
            st.session_state.voice_id = voice_id or "pNInz6obpgDQGcFmaJgB"
            
            if not has_voice:
                st.session_state.show_voice_clone = True
            else:
                st.session_state.show_voice_clone = False
                st.session_state.voice_cloning_done = True
            
            st.rerun()

# =============================
# PAGE 2 : VOICE CLONING
# =============================

elif st.session_state.show_voice_clone and not st.session_state.voice_cloning_done:
    st.markdown(f"<h1 style='text-align: center; color: #C499F3; font-size: 3.2rem;'>🎙️ Clone Your Voice</h1>", unsafe_allow_html=True)
    
    st.markdown("""
    <div style='text-align: center; padding: 2.5rem; max-width: 700px; margin: 0 auto; background: white; border-radius: 2rem; box-shadow: 0 4px 20px rgba(0,0,0,0.1);'>
        <p style='font-size: 1.25rem; color: #666; line-height: 1.8;'>
            Hi <strong>{}</strong>! 👋 Welcome!<br><br>
            Would you like to clone your voice for a more personal result? 
            It's optional but recommended!<br><br>
            Record a 60-second sample to create your unique voice profile.
        </p>
    </div>
    """.format(st.session_state.username), unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        script_text = (
            "Welcome to the voice calibration for my automated video guide. Today, we are exploring the fascinating "
            "intersection between human creativity, artificial intelligence, and digital sound design. "
            "This recording serves as a high-quality reference sample. It will allow the algorithms to analyze "
            "the unique frequency, tone, and rhythm of my voice. "
            "But why is this so important? Precision is key. By capturing these specific characteristics, "
            "the system can generate a digital clone capable of narrating all my future projects with ease. "
            "Whether I am explaining a complex technical concept or sharing an exciting story, the voice "
            "must remain consistent, clear, and full of life! "
            "I want to ensure that every syllable is captured, from the deepest tones to the highest peaks. "
            "Let's test the limits: How will this sound in a professional documentary? Or perhaps in a "
            "fast-paced tutorial? The goal is to achieve high precision, maintaining natural emotions and "
            "perfect articulation, regardless of the complexity of the script. "
            "Thank you for joining me in this experiment. Let's begin this journey into the future of "
            "content creation together."
        )
        
        with st.expander("📄 Show Script to Read"):
            # On utilise st.markdown au lieu de st.info pour avoir le contrôle total
            st.markdown(f"""
            <div style="
                background-color: #e8f4f8; 
                padding: 20px; 
                border-radius: 10px; 
                border-left: 5px solid #0077b6;
                font-size: 1.8rem; 
                line-height: 1.6;
                color: #1f1f1f;
            ">
                {script_text}
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("<p style='font-size: 1.15rem; font-weight: 600; margin-top: 1.5rem;'>🎤 Record your voice (60 seconds):</p>", unsafe_allow_html=True)
        audio_bytes = audio_recorder(text="", recording_color="#C499F3", neutral_color="#E0E0E0", icon_size="2x")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        col_rec, col_skip = st.columns(2)
        
        with col_rec:
            if st.button("✅ Use Recording", use_container_width=True, disabled=audio_bytes is None):
                if audio_bytes:
                    with st.spinner("Creating voice profile..."):
                        try:
                            from utils.audio_gen import create_instant_clone
                            
                            print("\n" + "="*70)
                            print("🎙️ CLONING DE LA VOIX")
                            print("="*70)
                            
                            # 1. Sauvegarder le fichier temporaire
                            temp_audio = f"temp_{uuid.uuid4().hex}.wav"
                            with open(temp_audio, "wb") as f:
                                f.write(audio_bytes)
                            
                            file_size = os.path.getsize(temp_audio)
                            print(f"✅ Fichier sauvegardé: {temp_audio} ({file_size} bytes)")
                            print(f"👤 Username: {st.session_state.username}")
                            
                            # 2. Cloner via l'API REST
                            voice_name = f"{st.session_state.username}_voice"
                            print(f"📝 Nom de la voix: {voice_name}")
                            print("⏳ Cloning en cours...")
                            
                            voice_id = create_instant_clone(voice_name, temp_audio)
                            
                            # 3. Vérifier le résultat
                            if voice_id:
                                print(f"🎉 CLONING RÉUSSI !")
                                print(f"🆔 Voice ID: {voice_id}")
                                
                                # 4. Sauvegarder dans user_profiles.json
                                save_user_profile(st.session_state.username, voice_id)
                                print(f"💾 Profil sauvegardé")
                                
                                # 5. Mettre à jour la session
                                st.session_state.voice_id = voice_id
                                print(f"✅ Session voice_id: {st.session_state.voice_id}")
                                
                                # 6. Nettoyage
                                os.remove(temp_audio)
                                print("🗑️ Fichier temporaire supprimé")
                                print("="*70 + "\n")
                                
                                st.success(f"✅ Voice cloned! ID: {voice_id[:8]}...")
                                
                            else:
                                print("❌ Cloning a échoué (voice_id = None)")
                                st.error("❌ Voice cloning failed. Check terminal for details.")
                                
                                # Nettoyage
                                if os.path.exists(temp_audio):
                                    os.remove(temp_audio)
                            
                        except Exception as e:
                            print(f"❌ ERREUR: {e}")
                            import traceback
                            traceback.print_exc()
                            
                            # Nettoyage
                            if 'temp_audio' in locals() and os.path.exists(temp_audio):
                                os.remove(temp_audio)
                            
                            st.error(f"Error: {e}")
                        
                        st.session_state.voice_cloning_done = True
                        st.session_state.show_voice_clone = False
                        st.rerun()
        
        with col_skip:
            if st.button("⏭️ Skip", use_container_width=True):
                st.session_state.voice_cloning_done = True
                st.session_state.show_voice_clone = False
                st.rerun()

# =============================
# PAGE 3 : WORKSPACE
# =============================

else:
    if not st.session_state.initialized:
        st.session_state.graph = compile_graph()
        
        st.session_state.current_state = {
            "username": st.session_state.username,
            "video_path": st.session_state.video_path,
            "video_analysis": {},
            "output_video_path": None,
            "user_instructions": "INIT_START",
            "messages": [],
            "iteration_count": 0,
            "script": None,
            "voice_id": st.session_state.voice_id,
            "audio_path": None,
            "audio_config": {"stability": 0.5, "similarity": 0.75, "style": 0.0},
            "pending_audio_feedback": None,
            "force_action": None
        }
        
        if st.session_state.has_voice:
            welcome_msg = f"Hi {st.session_state.username}! 👋 Great to see you again! Your voice is already cloned."
        else:
            welcome_msg = f"Hi {st.session_state.username}! 👋 Welcome! Your voice setup is complete."
        
        st.session_state.messages = [('assistant', welcome_msg)]
        
        with st.spinner("Initializing AI..."):
            st.session_state.current_state = st.session_state.graph.invoke(st.session_state.current_state)
            
            if st.session_state.current_state.get('messages'):
                last_msg = st.session_state.current_state['messages'][-1]
                content = last_msg.content if hasattr(last_msg, 'content') else last_msg[1]
                st.session_state.messages.append(('assistant', content))
        
        st.session_state.initialized = True
        st.rerun()
    
    # Header
    st.markdown(f"""
    <div style='background: white; padding: 1.3rem 2.5rem; border-radius: 1rem; margin-bottom: 1rem; box-shadow: 0 2px 8px rgba(0,0,0,0.05);'>
        <div style='display: flex; justify-content: space-between; align-items: center;'>
            <h2 style='margin: 0; color: #C499F3; font-size: 2rem;'>✨ VideoScript AI</h2>
            <div style='display: flex; align-items: center; gap: 0.7rem;'>
                <div style='width: 38px; height: 38px; border-radius: 50%; background: linear-gradient(to right, #C499F3, #9BB5F3); display: flex; align-items: center; justify-content: center; color: white; font-weight: bold; font-size: 1.1rem;'>
                    {st.session_state.username[0].upper()}
                </div>
                <span style='font-weight: 600; font-size: 1.15rem;'>{st.session_state.username}</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Variables d'état
    iteration = st.session_state.current_state.get('iteration_count', 0)
    has_audio = st.session_state.current_state.get('audio_path') is not None
    output_path = st.session_state.current_state.get('output_video_path')
    has_output = output_path and os.path.exists(output_path) if output_path else False
    
    # DÉTECTION AUTO-COMPOSITING
    audio_ready_for_compositing = (
        has_audio and 
        not has_output and 
        not st.session_state.compositing_triggered
    )
    
    # Layout
    col_video, col_chat = st.columns([4, 6])
    
    with col_video:
        st.markdown("### 🎬 Video")
        
        if has_output:
            st.success("✅ Final video ready!")
            st.video(output_path)
        elif st.session_state.video_path:
            st.info("📹 Original video")
            st.video(st.session_state.video_path)
            
                # ⭐ AFFICHER L'ANALYSE VIDÉO (si disponible)
        video_analysis = st.session_state.current_state.get('video_analysis')
        if video_analysis:
            technical = video_analysis.get('technical', {})
            semantic = video_analysis.get('semantic', {})
            visual_style = semantic.get('visual_style', {})
            energy = semantic.get('energy_metrics', {})
            global_summary = video_analysis.get('global_summary', '')
            
            # Créer l'affichage conditionnel
            with st.expander("📊 Video Analysis", expanded=False):
                # Infos techniques
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Duration", f"{technical.get('duration_sec', 0)}s")
                    st.metric("Visual Energy", f"{energy.get('visual_energy', 'N/A')}/10")
                
                with col2:
                    st.metric("Total Cuts", technical.get('total_cuts', 0))
                
                # Style visuel
                st.markdown("**🎨 Visual Style:**")
                st.markdown(f"- Camera: {visual_style.get('camera_work', 'Unknown')}")
                st.markdown(f"- Lighting: {visual_style.get('lighting_vibe', 'Unknown')}")
                st.markdown(f"- Pacing: {energy.get('pacing_evolution', 'Unknown')}")
                
                # Résumé global
                if global_summary:
                    st.markdown("**📝 Summary:**")
                    st.info(global_summary)
                    
        audio_explanation = st.session_state.current_state.get('audio_explanation')
        if audio_explanation:
            st.markdown(f"""
            <div style="
                background-color: #f0f7ff; 
                padding: 15px; 
                border-radius: 10px; 
                border-left: 5px solid #9BB5F3;
                margin-top: 10px;
                font-size: 0.95rem;
                color: #1a1a1a;
                font-style: italic;
            ">
                <strong>🎙️ Voice Note:</strong><br>{audio_explanation}
            </div>
            """, unsafe_allow_html=True)

    with col_chat:
        st.markdown("### 💬 AI Partner")
        
        # Messages
        for msg in st.session_state.messages:
            if isinstance(msg, tuple):
                role, content = msg
            else:
                role = msg.get('role', 'assistant')
                content = msg.get('content', '')
            
            # ⭐ FILTRER LA PARTIE ---DATA--- pour l'affichage chat
            display_content = content.split("---DATA---")[0].strip()
            
            if role == 'user':
                st.markdown(f'<div class="user-message"><strong>You:</strong><br>{display_content}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="assistant-message"><strong>🤖 AI:</strong><br>{display_content}</div>', unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # =============================
        # AUTO-COMPOSITING (audio prêt)
        # =============================
        
        if audio_ready_for_compositing:
            st.info("🎬 Audio ready! Starting video compositing in 2 seconds...")
            st.session_state.compositing_triggered = True
            time.sleep(2)
            
            with st.spinner("🎬 Compositing video with audio..."):
                st.session_state.current_state = st.session_state.graph.invoke(st.session_state.current_state)
                
                if st.session_state.current_state.get('messages'):
                    last_msg = st.session_state.current_state['messages'][-1]
                    content = last_msg.content if hasattr(last_msg, 'content') else last_msg[1]
                    st.session_state.messages.append(('assistant', content))
            
            st.session_state.compositing_triggered = False
            st.rerun()
        
        # =============================
        # CARTES A/B + ÉDITION (iteration 3)
        # =============================
        
        elif iteration == 3 and not has_audio:
            # Récupérer le script qui contient les 2 variants
            full_script = st.session_state.current_state.get('script', '')
            
            print(f"🔍 DEBUG - Full script from state:\n{full_script}\n")
                # === DEBUG COMPLET ===
            print("\n" + "="*80)
            print("🔍 DEBUG ITERATION 3")
            print("="*80)
            
            # 1. Vérifier le state complet
            print(f"📦 State keys: {st.session_state.current_state.keys()}")
            print(f"📝 Script value: '{st.session_state.current_state.get('script')}'")
            print(f"💬 Messages count: {len(st.session_state.messages)}")
            
            # 2. Vérifier le dernier message
            if st.session_state.messages:
                last_msg = st.session_state.messages[-1]
                print(f"📨 Last message type: {type(last_msg)}")
                print(f"📨 Last message: {last_msg}")
            
            # 3. Vérifier le script brut
            full_script = st.session_state.current_state.get('script', '')
            print(f"\n📄 FULL SCRIPT FROM STATE:")
            print(f"Type: {type(full_script)}")
            print(f"Length: {len(full_script)}")
            print(f"Content:\n{full_script}")
            print("="*80 + "\n")
                
                # Récupérer le script qui contient les 2 variants
                # ... (reste du code de parsing)
            # Parser les variants depuis le script
            try:
                # Format attendu : "VARIANTE_A: XXX|CONTENT_A: YYY VARIANTE_B: XXX|CONTENT_B: YYY"
                # Format attendu : "VARIANTE_A: XXX|CONTENT_A: YYY\nVARIANTE_B: XXX|CONTENT_B: YYY"
                if "VARIANTE_A:" not in full_script or "VARIANTE_B:" not in full_script:
                    raise ValueError("VARIANTE_A or VARIANTE_B not found in script")
                
                # Séparer par VARIANTE_B:
                parts = full_script.split("VARIANTE_B:", 1)  # maxsplit=1 pour éviter les bugs
                
                # === VARIANT A ===
                variant_a_raw = parts[0].strip()
                print(f"🔍 Variant A raw: '{variant_a_raw}'")
                
                # Enlever "VARIANTE_A:"
                variant_a_raw = variant_a_raw.replace("VARIANTE_A:", "").strip()
                
                # Vérifier qu'il y a bien un pipe |
                if "|" not in variant_a_raw:
                    raise ValueError(f"Pipe | not found in variant A: {variant_a_raw}")
                
                # Séparer style et content par |
                style_a, content_a_raw = variant_a_raw.split("|", 1)
                style_a = style_a.strip()
                
                # Enlever "CONTENT_A:"
                content_a = content_a_raw.replace("CONTENT_A:", "").strip()
                
                # === VARIANT B ===
                variant_b_raw = parts[1].strip()
                print(f"🔍 Variant B raw: '{variant_b_raw}'")
                
                # Vérifier qu'il y a bien un pipe |
                if "|" not in variant_b_raw:
                    raise ValueError(f"Pipe | not found in variant B: {variant_b_raw}")
                
                    # Séparer style et content par |
                style_b, content_b_raw = variant_b_raw.split("|", 1)
                style_b = style_b.strip()
                # Enlever "CONTENT_B:"
                content_b = content_b_raw.replace("CONTENT_B:", "").strip()
                    
                print(f"✅ Style A: {style_a}")
                print(f"✅ Style B: {style_b}")
                print(f"✅ Content A: {content_a[:50]}...")
                print(f"✅ Content B: {content_b[:50]}...")
                
                
                    
            except Exception as e:
                print(f"❌ Parsing error: {e}")
                print(f"Full script: {full_script}")
                style_a, content_a = "Variant A", "Error parsing - check terminal"
                style_b, content_b = "Variant B", "Error parsing - check terminal"
            
            # --- AFFICHAGE DES CARTES A/B ---
            st.info("💡 Choose your preferred script variant:")
            
            col_a, col_b = st.columns(2)
            
            with col_a:
                st.markdown(f"""
                <div style="background: white; border-top: 5px solid #C499F3; padding: 20px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); min-height: 280px; overflow-y: auto;">
                    <span style="background: linear-gradient(135deg, #C499F3, #A080F9); color: white; padding: 6px 16px; border-radius: 20px; font-size: 0.9rem; font-weight: bold; text-transform: uppercase; display: inline-block; margin-bottom: 12px;">
                        ✨ {style_a}
                    </span>
                    <p style="margin-top: 10px; font-size: 1.05rem; color: #333; line-height: 1.6;">{content_a}</p>
                </div>
                """, unsafe_allow_html=True)
                
                if st.button(f"✅ Select {style_a}", use_container_width=True, key="btn_a"):
                    st.session_state.current_state['script'] = content_a
                    st.session_state.current_state['force_action'] = 'CHOOSE_A'
                    st.session_state.current_state['user_instructions'] = f'CHOOSE_A'
                    st.session_state.messages.append(('user', f'I choose {style_a}'))
                    
                    with st.spinner("🎙️ Generating audio based on your choice..."):
                        st.session_state.current_state = st.session_state.graph.invoke(st.session_state.current_state)
                        
                        if st.session_state.current_state.get('messages'):
                            last_msg = st.session_state.current_state['messages'][-1]
                            content = last_msg.content if hasattr(last_msg, 'content') else last_msg[1]
                            st.session_state.messages.append(('assistant', content))
                    
                    st.rerun()
            
            with col_b:
                st.markdown(f"""
                <div style="background: white; border-top: 5px solid #9BB5F3; padding: 20px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); min-height: 280px; overflow-y: auto;">
                    <span style="background: linear-gradient(135deg, #9BB5F3, #6FA8DC); color: white; padding: 6px 16px; border-radius: 20px; font-size: 0.9rem; font-weight: bold; text-transform: uppercase; display: inline-block; margin-bottom: 12px;">
                        🌈 {style_b}
                    </span>
                    <p style="margin-top: 10px; font-size: 1.05rem; color: #333; line-height: 1.6;">{content_b}</p>
                </div>
                """, unsafe_allow_html=True)
                
                if st.button(f"✅ Select {style_b}", use_container_width=True, key="btn_b"):
                    st.session_state.current_state['script'] = content_b
                    st.session_state.current_state['force_action'] = 'CHOOSE_B'
                    st.session_state.current_state['user_instructions'] = f'CHOOSE_B'
                    st.session_state.messages.append(('user', f'I choose {style_b}'))
                    
                    with st.spinner("🎙️ Generating audio based on your choice..."):
                        st.session_state.current_state = st.session_state.graph.invoke(st.session_state.current_state)
                        
                        if st.session_state.current_state.get('messages'):
                            last_msg = st.session_state.current_state['messages'][-1]
                            content = last_msg.content if hasattr(last_msg, 'content') else last_msg[1]
                            st.session_state.messages.append(('assistant', content))
                    
                    st.rerun()
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # --- TEXT AREA POUR ÉDITION MANUELLE ---
            with st.expander("✏️ **Manual Edit & Instant Generate**", expanded=False):
                combined_text = f"**{style_a}:**\n{content_a}\n\n**{style_b}:**\n{content_b}"
                
                import hashlib
                script_hash = hashlib.md5(combined_text.encode()).hexdigest()
                
                user_edited_text = st.text_area(
                    "Edit or mix both variants before generating:",
                    value=combined_text,
                    height=200,
                    key=f"manual_edit_{script_hash}"
                )
                
                if st.button("🚀 Confirm Text & Generate Voiceover", use_container_width=True, type="primary", key="validate_combined"):
                    import re
                    final_text = re.sub(r'\*\*.*?\*\*\s*', '', user_edited_text)
                    final_text = final_text.strip()
                    
                    st.session_state.current_state['script'] = final_text
                    st.session_state.messages.append(('user', f"✨ Final Validated Script: {final_text}"))
                    st.session_state.current_state['force_action'] = 'VALIDATE'
                    st.session_state.current_state['user_instructions'] = 'VALIDATE'
                    
                    with st.spinner("🎙️ Generating audio with your final version..."):
                        st.session_state.current_state = st.session_state.graph.invoke(st.session_state.current_state)
                        
                        if st.session_state.current_state.get('messages'):
                            last_msg = st.session_state.current_state['messages'][-1]
                            content = last_msg.content if hasattr(last_msg, 'content') else last_msg[1]
                            st.session_state.messages.append(('assistant', content))
                    
                    st.rerun()
        
        # =============================
        # ÉDITION SIMPLE (iterations 4+)
        # =============================
        
        elif iteration > 3 and st.session_state.current_state.get('script') and not has_audio:
            with st.expander("✏️ **Manual Edit & Instant Generate**", expanded=True):
                current_script = st.session_state.current_state.get('script', '')
                
                import hashlib
                script_hash = hashlib.md5(current_script.encode()).hexdigest()
                
                user_edited_text = st.text_area(
                    "Fine-tune your script here before generating audio:",
                    value=current_script,
                    height=150,
                    key=f"manual_edit_{script_hash}"
                )
                
                if st.button("🚀 Confirm Text & Generate Voiceover", use_container_width=True, type="primary", key="validate_single"):
                    import re
                    final_text = re.sub(r'^(.*?):\s*', '', user_edited_text).strip()
                    final_text = final_text.replace('**', '')
                    
                    st.session_state.current_state['script'] = final_text
                    st.session_state.messages.append(('user', f"✨ Final Validated Script: {final_text}"))
                    st.session_state.current_state['force_action'] = 'VALIDATE'
                    st.session_state.current_state['user_instructions'] = 'VALIDATE'
                    
                    print(f"🎙️ [VALIDATION] Texte envoyé : {final_text}")
                    
                    with st.spinner("🎙️ Generating audio..."):
                        st.session_state.current_state = st.session_state.graph.invoke(st.session_state.current_state)
                        
                        if st.session_state.current_state.get('messages'):
                            last_msg = st.session_state.current_state['messages'][-1]
                            content = last_msg.content if hasattr(last_msg, 'content') else last_msg[1]
                            st.session_state.messages.append(('assistant', content))
                    
                    st.rerun()
        
        # =============================
        # BOUTON DOWNLOAD (vidéo finale prête)
        # =============================
        
        elif has_output:
            st.success("🎉 Your video is ready! Check the video panel on the left ←")
            
            output_name = f"FINAL_VIDEO_{st.session_state.username}.mp4"
            
            with open(output_path, "rb") as f:
                video_bytes = f.read()
            
            if st.download_button(
                label="💾 Download Video & Finish",
                data=video_bytes,
                file_name=output_name,
                mime="video/mp4",
                use_container_width=True,
                type="primary",
                key="download_finish_btn"
            ):
                st.session_state.show_goodbye = True
                st.rerun()
        
        # Input chat
        with st.form(key="chat_form", clear_on_submit=True):
            user_input = st.text_input("Message", placeholder="Type your message...", label_visibility="collapsed")
            submit = st.form_submit_button("Send ✉️", use_container_width=True)
        
        if submit and user_input:
            import hashlib
            h = hashlib.md5(st.session_state.current_state['script'].encode()).hexdigest() if st.session_state.current_state.get('script') else ''
            edit_key = f"manual_edit_{h}"
            if edit_key in st.session_state:
                st.session_state.current_state['script'] = st.session_state[edit_key]
            st.session_state.messages.append(('user', user_input))
            st.session_state.current_state['user_instructions'] = user_input
            st.session_state.current_state['force_action'] = None
            
            with st.spinner("Thinking..."):
                st.session_state.current_state = st.session_state.graph.invoke(st.session_state.current_state)
                if st.session_state.current_state.get('messages'):
                    last_msg = st.session_state.current_state['messages'][-1]
                    content = last_msg.content if hasattr(last_msg, 'content') else last_msg[1]
                    st.session_state.messages.append(('assistant', content))
            st.rerun()
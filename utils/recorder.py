import sounddevice as sd
from scipy.io.wavfile import write
import time

def record_user_live(duration=60):
    """
    Captures audio with a choice of 2 languages: English, French.
    """
    fs = 44100  
    
    print("\n--- 🎤 VOICE CLONING SETUP ---")
    print("Select your language / Choisissez votre langue :")
    print("1. English")
    print("2. Français")
    
    choice = input("Choice (1/2): ").strip()

    # Scripts
    scripts = {
        "1": (
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
        ),
        "2": (
            "Bienvenue dans cette étape de calibration pour mon guide vidéo automatisé. Aujourd'hui, nous explorons "
            "l'intersection fascinante entre la créativité humaine, l'intelligence artificielle et le design sonore numérique. "
            "Cet enregistrement n'est pas qu'un simple test, c'est un échantillon de référence de haute qualité. "
            "Il permettra aux algorithmes d'analyser avec précision la fréquence, le ton et le rythme unique de ma voix. "
            "Mais pourquoi est-ce si important ? Tout est dans le détail. En capturant ces caractéristiques spécifiques, "
            "le système pourra générer un clone numérique capable de narrer tous mes futurs projets avec un réalisme "
            "saisissant ! Que je doive expliquer un concept technique complexe ou raconter une histoire passionnante, "
            "ma voix doit rester constante, naturelle et pleine de vie. Est-ce que le rendu sera parfait ? "
            "C'est tout l'enjeu de cet exercice. Je veille à articuler chaque syllabe, des graves les plus profonds "
            "aux nuances les plus légères. L'objectif est de conserver des émotions authentiques, peu importe la "
            "complexité du texte final. Merci de m'accompagner dans cette expérience. Commençons ensemble ce "
            "voyage passionnant dans le futur de la création de contenu."
        )
    }
    

    selected_text = scripts.get(choice, scripts["1"]) # Default to English if error

    print("\n" + "-" * 50)
    print("TEXT TO READ CLEARLY:")
    print(f"\n{selected_text}")
    print("-" * 50)
    
    for i in range(3, 0, -1):
        print(f"Starting in {i}...")
        time.sleep(1)
    
    print("\n🔴 RECORDING NOW... (Speak naturally)")
    
    recording = sd.rec(int(duration * fs), samplerate=fs, channels=1)
    sd.wait() 
    
    output_path = "user_voice_sample.wav"
    write(output_path, fs, recording) 
    
    print(f"\n✅ Recording finished: {output_path}")
    return output_path
"""
gemini_service.py - Google Gemini 2.5 Flash Multimodal AI Engine + Multilingual Voice I/O
AgriAttribute AI — Syngenta Biologicals & ANNAM.AI Hack Core 2026 (Team 15)

Precision Conversational Agronomist & Field Intelligence Co-Pilot:
Natively processes Voice Notes (audio), Field Images (leaf/crop/pest), and Text Queries,
deeply synchronized with all platform modules:
1. Live Weather (OpenWeatherMap + Meteoblue)
2. Soil Health Card (DAC&FW 12-parameter standards)
3. LeafVision 2.0 Foliar Telemetry
4. Agmarknet 2.0 Live Mandi Pulse
5. Counterfactual Biological ROI & Yield Attribution
"""

import os
import requests
import base64
import html as html_mod
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

def _clean_gemini_key(k: str) -> str:
    if not k or not isinstance(k, str):
        return ""
    k = k.strip()
    if k.startswith("your_") or len(k) < 20:
        return ""
    return k

def _get_gemini_key() -> str:
    val = os.getenv("GEMINI_API_KEY", "")
    if not val:
        try:
            import streamlit as st
            if hasattr(st, "secrets") and "GEMINI_API_KEY" in st.secrets:
                val = str(st.secrets["GEMINI_API_KEY"])
        except Exception:
            pass
    return _clean_gemini_key(val)

# ─── System Prompt ────────────────────────────────────────────────────────────
AGRI_SYSTEM_PROMPT = """
You are AgriAttribute AI — a precision agronomic advisory assistant built for Indian farmers, agricultural extension workers, and field officers (Syngenta & ANNAM.AI, Hack Core PS-07).

CORE OPERATING DIRECTIVES:
1. SCIENTIFIC & ADVISORY INTEGRITY:
   • Never make claims of 'guaranteed profit', 'ensure 100% yield', or 'will definitely increase yield'.
   • Always use probabilistic, evidence-based advisory language (e.g., 'calibrated models project an estimated response of...', 'recommended best practice indicates...', 'subject to weather and field conditions').
   • Clearly distinguish measured field telemetry from modeled estimates or demonstration data.
2. SYNCHRONIZED FARM CONTEXT: Reference the contextual numbers provided in the [SYNCHRONIZED FARM TELEMETRY] block (temperature, soil parameters, Agmarknet mandi benchmarks).
3. If the user provided a VOICE NOTE (audio), transcribe their exact spoken query first under: "**🗣️ Transcribed Voice Query:** <query>".
4. If the user provided an IMAGE (leaf/crop/pest), evaluate visual symptoms and remind the user that AI visual screening is preliminary and should be verified with an agronomist or local KVK expert.
5. Prescriptions must be balanced: specify crop, dosage unit (g/L or ml/acre), application timing, safety pre-harvest interval (PHI), and non-chemical/regenerative biocontrol alternatives (*Trichoderma*, *Pseudomonas*, neem oil).
6. Deliver a clear CACP/Agmarknet economic perspective, noting market assumptions transparently.
7. Respond fluently and respectfully in the farmer's requested language.
"""

def build_context_block(ctx: dict) -> str:
    """Builds a rich structured farm context string from the full context dict."""
    if not ctx:
        return ""
    lines = ["\n[SYNCHRONIZED FARM TELEMETRY — Live Platform Telemetry]"]

    # Location & Crop
    if ctx.get("region"):      lines.append(f"• Farm Location  : {ctx['region']}")
    if ctx.get("lat") and ctx.get("lon"):
        lines.append(f"• GPS Coordinates: {ctx['lat']:.4f}°N, {ctx['lon']:.4f}°E")
    if ctx.get("crop"):        lines.append(f"• Target Crop    : {ctx['crop']}")
    if ctx.get("product"):     lines.append(f"• Biological Input: {ctx['product']} @ {ctx.get('dosage', 'recommended')} L/acre")

    # Live Weather & Stress
    if ctx.get("temp_max"):    lines.append(f"• Current Temp   : {ctx['temp_max']:.1f}°C (Max) / {ctx.get('temp_min', 0):.1f}°C (Min)")
    if ctx.get("humidity"):    lines.append(f"• Air Humidity   : {ctx['humidity']:.0f}% RH")
    if ctx.get("wind_speed"):  lines.append(f"• Wind Speed     : {ctx['wind_speed']} km/h")
    if ctx.get("rainfall"):    lines.append(f"• Season Rainfall: {ctx['rainfall']:.0f} mm")
    if ctx.get("heat_stress"): lines.append(f"• Heat Stress Days: {ctx['heat_stress']} days (>35°C thermal threshold)")

    # DAC&FW National Soil Health Card Benchmarks
    if ctx.get("nitrogen"):
        n_val = ctx['nitrogen']
        n_st = "DEFICIENT ⚠️ (<280 kg/ha)" if n_val < 280 else ("OPTIMAL ✅ (280-560)" if n_val <= 560 else "HIGH")
        lines.append(f"• Soil Nitrogen (N)  : {n_val:.0f} kg/ha [{n_st}]")
    if ctx.get("phosphorus"):
        p_val = ctx['phosphorus']
        p_st = "DEFICIENT ⚠️ (<23 kg/ha)" if p_val < 23 else ("OPTIMAL ✅ (23-56)" if p_val <= 56 else "HIGH")
        lines.append(f"• Soil Phosphorus (P): {p_val:.0f} kg/ha [{p_st}]")
    if ctx.get("potassium"):
        k_val = ctx['potassium']
        k_st = "DEFICIENT ⚠️ (<145 kg/ha)" if k_val < 145 else ("OPTIMAL ✅ (145-336)" if k_val <= 336 else "HIGH")
        lines.append(f"• Soil Potassium (K) : {k_val:.0f} kg/ha [{k_st}]")
    if ctx.get("ph"):          lines.append(f"• Soil Reaction (pH) : {ctx['ph']:.1f}")
    if ctx.get("soc"):         lines.append(f"• Organic Carbon (SOC): {ctx['soc']:.2f}% ({'Low <0.5%' if ctx['soc'] < 0.5 else 'Adequate'})")

    # Agmarknet 2.0 Live Mandi Pulse
    if ctx.get("mandi_spot"):
        lines.append(f"• Mandi Modal Spot Rate: Rs {ctx['mandi_spot']:,.0f} / quintal")
    if ctx.get("mandi_msp"):
        lines.append(f"• Govt MSP Floor Price : Rs {ctx['mandi_msp']:,.0f} / quintal")
    if ctx.get("mandi_verdict"):
        lines.append(f"• Mandi Market Verdict : {ctx['mandi_verdict']}")
    if ctx.get("mandi_trend"):
        lines.append(f"• 72h Price Momentum   : {ctx['mandi_trend']}")
    if ctx.get("quality_premium"):
        lines.append(f"• Grade-A Quality Bonus: +Rs {ctx['quality_premium']:,.0f}/quintal")

    # Outcome & Attribution
    if ctx.get("predicted_yield"):
        lines.append(f"• Total Yield Predicted : {ctx['predicted_yield']:.2f} q/acre")
    if ctx.get("yield_delta"):
        lines.append(f"• Biological Yield Boost: +{ctx['yield_delta']:.2f} q/acre")
    if ctx.get("net_profit"):
        lines.append(f"• Net Farm Profit Lift  : Rs {ctx['net_profit']:,.0f} / acre")
    if ctx.get("roi_pct"):
        lines.append(f"• Return on Investment  : {ctx['roi_pct']:.1f}%")

    lines.append("[END SYNCHRONIZED TELEMETRY]\n")
    return "\n".join(lines)


def generate_domain_expert_fallback(user_query: str, language: str, context_info: dict = None) -> str:
    """Robust offline agronomic response in the selected language."""
    ctx = context_info or {}
    crop = ctx.get("crop", "Crop")
    product = ctx.get("product", "Syngenta Quantis")
    heat_stress = ctx.get("heat_stress", 5)
    n_val = ctx.get("nitrogen", 210)
    mandi = ctx.get("mandi_spot", 5869)
    profit = ctx.get("net_profit", 14573)

    lang_lower = str(language).lower()
    if "marathi" in lang_lower or "मराठी" in lang_lower:
        return f"""
🌾 **कृषी-सल्लागार प्रत्यक्ष मार्गदर्शन ({crop}):**

1. **जैविक फवारणी वेळ:** {product} ची फवारणी सकाळी ८ ते १०:३० किंवा संध्याकाळी ४:३० नंतर करावी (दुपारचे ३२°C पेक्षा जास्त तापमान टाळा).
2. **उष्णता तणाव संरक्षण:** शेतात {heat_stress} दिवसांचा उष्णता ताण असल्याने फुलगळ रोखण्यासाठी २ मिली प्रति लिटर पाण्यात मिसळून फवारणी करा.
3. **मातीतील नत्र (N):** मातीतील नत्र {n_val:.0f} kg/ha आहे (मानक २८० kg/ha पेक्षा कमी). २५ kg/ha युरियासोबत बायो-स्टिम्युलेटर वापरल्यास अन्नद्रव्य शोषण क्षमता वाढेल.
4. **अगमार्कनेट २.० बाजारभाव:** आजचा लाइव्ह मंडी दर ₹{mandi:,.0f}/क्विंटल आहे. सिंजेंटा ग्रेड-A गुणवत्तेमुळे जास्तीचा प्रीमियम मिळेल.
5. **अपेक्षित नफा:** एकरी अंदाजे ₹{profit:,.0f} चा निव्वळ नफा शक्य आहे!
"""
    elif "hindi" in lang_lower or "हिंदी" in lang_lower:
        return f"""
🌾 **कृषि-सलाहकार वास्तविक मार्गदर्शन ({crop}):**

1. **जैविक छिड़काव का समय:** {product} का छिड़काव सुबह 8 से 10:30 बजे या शाम 4:30 बजे के बाद करें। दोपहर की 32°C से अधिक गर्मी से बचें।
2. **ताप-तनाव सुरक्षा:** खेत में {heat_stress} दिनों के अत्यधिक तापमान के कारण फूल झड़ने से रोकने हेतु 2 मिली प्रति लीटर पानी में मिलाकर छिड़कें।
3. **मिट्टी में नाइट्रोजन (N):** आपकी मिट्टी में N = {n_val:.0f} kg/ha है (सरकारी मानक 280 kg/ha से कम)। जैव-उत्तेजक जड़ों की अवशोषण क्षमता 30% तक बढ़ाते हैं।
4. **एगमार्कनेट 2.0 मंडी भाव:** आज का मंडी भाव ₹{mandi:,.0f}/क्विंटल है। ग्रेड-A गुणवत्ता से अतिरिक्त प्रीमियम मिलेगा।
5. **आर्थिक लाभ:** प्रति एकड़ लगभग ₹{profit:,.0f} का अतिरिक्त शुद्ध मुनाफा सुनिश्चित किया जा सकता है!
"""
    elif "punjabi" in lang_lower or "ਪੰਜਾਬੀ" in lang_lower or "pa" in lang_lower:
        return f"""
🌾 **ਖੇਤੀਬਾੜੀ ਸਲਾਹਕਾਰ ਲਾਈਵ ਮਾਰਗਦਰਸ਼ਨ ({crop}):**

1. **ਜੈਵਿਕ ਸਪਰੇਅ ਦਾ ਸਮਾਂ:** {product} ਦਾ ਛਿੜਕਾਅ ਸਵੇਰੇ 8 ਤੋਂ 10:30 ਵਜੇ ਜਾਂ ਸ਼ਾਮ 4:30 ਵਜੇ ਤੋਂ ਬਾਅਦ ਕਰੋ (ਦੁਪਹਿਰ ਦੀ 32°C ਤੋਂ ਵੱਧ ਗਰਮੀ ਤੋਂ ਬਚੋ)।
2. **ਗਰਮੀ ਦੇ ਤਣਾਅ ਤੋਂ ਸੁਰੱਖਿਆ:** ਖੇਤ ਵਿੱਚ {heat_stress} ਦਿਨਾਂ ਦੇ ਤੇਜ਼ ਤਾਪਮਾਨ ਕਾਰਨ ਫੁੱਲ ਡਿੱਗਣ ਤੋਂ ਰੋਕਣ ਲਈ 2 ਮਿਲੀਲੀਟਰ ਪ੍ਰਤੀ ਲੀਟਰ ਪਾਣੀ ਵਿੱਚ ਮਿਲਾ ਕੇ ਛਿੜਕੋ।
3. **ਮਿੱਟੀ ਵਿੱਚ ਨਾਈਟ੍ਰੋਜਨ (N):** ਤੁਹਾਡੀ ਮਿੱਟੀ ਵਿੱਚ N = {n_val:.0f} kg/ha ਹੈ (ਸਰਕਾਰੀ ਮਾਪਦੰਡ 280 kg/ha ਤੋਂ ਘੱਟ)। ਜੈਵਿਕ ਉਤੇਜਕ ਜੜ੍ਹਾਂ ਦੀ ਖੁਰਾਕ ਲੈਣ ਦੀ ਸਮਰੱਥਾ 30% ਤੱਕ ਵਧਾਉਂਦੇ ਹਨ।
4. **ਐਗਮਾਰਕਨੈੱਟ 2.0 ਮੰਡੀ ਭਾਅ:** ਅੱਜ ਦਾ ਲਾਈਵ ਮੰਡੀ ਭਾਅ ₹{mandi:,.0f}/ਕੁਇੰਟਲ ਹੈ। ਸਿੰਜੈਂਟਾ ਗ੍ਰੇਡ-A ਕੁਆਲਿਟੀ ਨਾਲ ਵਾਧੂ ਪ੍ਰੀਮੀਅਮ ਮਿਲੇਗਾ।
5. **ਅਨੁਮਾਨਿਤ ਮੁਨਾਫਾ:** ਪ੍ਰਤੀ ਏਕੜ ਲਗਭਗ ₹{profit:,.0f} ਦਾ ਵਾਧੂ ਸ਼ੁੱਧ ਮੁਨਾਫਾ ਸੰਭਵ ਹੈ!
"""
    elif "telugu" in lang_lower or "తెలుగు" in lang_lower:
        return f"""
🌾 **వ్యవసాయ నిపుణుల సలహా ({crop}):**

1. **పిచికారీ సమయం:** {product} ను ఉదయం 8 నుండి 10:30 గంటల మధ్య లేదా సాయంత్రం 4:30 తర్వాత పిచికారీ చేయండి (మధ్యాహ్నం 32°C ఎండను నివారించండి).
2. **ఎండ వేడిమి రక్షణ:** పొలంలో {heat_stress} రోజుల వేడి ప్రభావం వల్ల పూత రాలకుండా నివారించడానికి లీటరు నీటికి 2 మి.లీ కలిపి వాడండి.
3. **భూమిలో నత్రజని (N):** నత్రజని {n_val:.0f} kg/ha ఉంది (DAC&FW ప్రామాణికం 280 kg/ha కంటే తక్కువ).
4. **అగ్‌మార్క్‌నెట్ 2.0 మండి ధర:** ఈరోజు స్పాట్ ధర ₹{mandi:,.0f}/క్వింటాల్. గ్రేడ్-A నాణ్యతతో అదనపు ప్రీమియం పొందవచ్చు.
5. **ఆశించిన లాభం:** ఎకరానికి ₹{profit:,.0f} నికర లాభం సాధ్యమవుతుంది!
"""
    else:
        english_briefing = f"""
**AgriAttribute Field Intelligence Briefing ({crop}):**

**Core Verdict:** Your live farm telemetry indicates {f'soil nitrogen deficiency ({n_val:.0f} kg/ha vs 280 kg/ha DAC&FW benchmark)' if n_val < 280 else 'stable soil nutrients'} and {heat_stress} days of heat stress.

1. **Application Protocol:** Spray {product} at 2.0 L/acre (or 2 mL/L water) strictly between 8:00 AM – 10:30 AM or after 4:30 PM. Use 400-500 L/ha water with hollow-cone nozzles.
2. **Heat Stress Defense:** Thermal stress (>35°C) triggers ethylene release causing flower/boll abortion. Biostimulants maintain cell turgor and restore stomatal conductance.
3. **Soil Nutrient Synergy:** With soil N at {n_val:.0f} kg/ha, biostimulants improve root nutrient scavenging by up to 30%, enabling a 15% reduction in synthetic urea.
4. **Agmarknet 2.0 Market Opportunity:** Today's APMC modal spot rate is Rs {mandi:,.0f}/q. Grade-A bolder grain quality fetches an additional quality auction premium.

**Economic Bottom Line:** Total estimated net profit lift is Rs {profit:,.0f}/acre.
"""
        # If farmer selected an Indic language (Gujarati, Tamil, Kannada, Bengali, etc.), translate dynamically via IndicTrans2
        if lang_lower and lang_lower not in ["english", "en"]:
            try:
                from services import indictrans_service
                return indictrans_service.translate_en_to_indic(english_briefing, language)
            except Exception:
                pass
        return english_briefing


def ask_gemini_multimodal(
    query_text: str = None,
    audio_bytes: bytes = None,
    audio_mime: str = "audio/wav",
    image_bytes: bytes = None,
    image_mime: str = "image/jpeg",
    language: str = "English",
    context_info: dict = None
) -> dict:
    """
    Multimodal Gemini 2.5 Flash query handler:
    Accepts direct Audio Voice Notes (raw bytes from microphone), Field Photos, and Text Queries,
    fused with the synchronized live farm telemetry.
    """
    context_block = build_context_block(context_info)
    
    parts = []

    # 1. Attach Audio Voice Note if provided
    has_audio = False
    if audio_bytes and len(audio_bytes) > 100:
        has_audio = True
        try:
            b64_audio = base64.b64encode(audio_bytes).decode("utf-8")
            parts.append({
                "inline_data": {
                    "mime_type": audio_mime,
                    "data": b64_audio
                }
            })
        except Exception:
            has_audio = False

    # 2. Attach Image if provided
    has_image = False
    if image_bytes and len(image_bytes) > 100:
        has_image = True
        try:
            b64_img = base64.b64encode(image_bytes).decode("utf-8")
            parts.append({
                "inline_data": {
                    "mime_type": image_mime,
                    "data": b64_img
                }
            })
        except Exception:
            has_image = False

    # 3. Construct the comprehensive instruction prompt
    instructions = [AGRI_SYSTEM_PROMPT, context_block, f"[Target Language: {language}]"]

    if has_audio:
        instructions.append(
            "IMPORTANT: An audio voice note is attached. First, transcribe the farmer's spoken query verbatim in its original language, label it '**🗣️ Spoken Question:** <text>'. Then, formulate a direct, actionable answer in the target language referencing the synchronized telemetry."
        )
    if has_image:
        instructions.append(
            "IMPORTANT: A field photograph is attached. Diagnose any visual symptoms (chlorosis, spots, lesions, deficiency, pest infestation), correlate with the farm soil & weather, and provide treatment recommendations."
        )

    canonical_query = query_text
    is_indic = language and str(language).lower() not in ["english", "en"]
    if is_indic and query_text and query_text.strip():
        try:
            from services import indictrans_service
            translated_q = indictrans_service.translate_indic_to_en(query_text.strip(), language)
            if translated_q and translated_q != query_text.strip():
                canonical_query = translated_q
        except Exception:
            pass

    if query_text and query_text.strip():
        if canonical_query and canonical_query != query_text.strip():
            instructions.append(f"Farmer's Original Query ({language}): {query_text.strip()}")
            instructions.append(f"Canonical English Query (via AI4Bharat IndicTrans2): {canonical_query.strip()}")
        else:
            instructions.append(f"Farmer's Written Query: {query_text.strip()}")
    elif not has_audio and not has_image:
        instructions.append("Farmer requested an overall executive field advisory based on today's farm telemetry.")

    instructions.append("\nAgriAttribute AI Field Co-Pilot Response:")
    full_prompt_text = "\n".join(instructions)

    parts.append({"text": full_prompt_text})

    payload = {
        "contents": [{"parts": parts}],
        "generationConfig": {
            "temperature": 0.25,
            "maxOutputTokens": 950
        }
    }
    headers = {"Content-Type": "application/json"}

    api_key = _get_gemini_key()
    if api_key:
        endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
        try:
            res = requests.post(endpoint, json=payload, headers=headers, timeout=30)
            if res.status_code == 200:
                data = res.json()
                reply = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                if reply and len(reply.strip()) > 10:
                    final_reply = reply.strip()
                    # If target is Indic language but model responded in English, translate via IndicTrans2
                    if is_indic:
                        try:
                            from services import indictrans_service
                            ascii_chars = sum(1 for c in final_reply if ord(c) < 128)
                            if len(final_reply) > 0 and (ascii_chars / len(final_reply)) > 0.85:
                                translated_reply = indictrans_service.translate_en_to_indic(final_reply, language)
                                if translated_reply:
                                    final_reply = translated_reply
                        except Exception:
                            pass
                    return {
                        "status": "LIVE",
                        "source": "Google Gemini 2.5 Flash API + AI4Bharat IndicTrans2",
                        "translation_engine": "AI4Bharat IndicTrans2 (Distilled 200M)",
                        "response": final_reply,
                        "language": language,
                        "canonical_query": canonical_query,
                        "has_audio": has_audio,
                        "has_image": has_image
                    }
        except Exception:
            pass

    # Graceful fallback to verified agronomic rule-based expert engine + IndicTrans2
    fallback_text = generate_domain_expert_fallback(query_text or "General field advice", language, context_info)
    return {
        "status": "DEMO / SYNTHETIC",
        "source": "Offline Agronomic Expert Engine + AI4Bharat IndicTrans2",
        "translation_engine": "AI4Bharat IndicTrans2 (Distilled 200M)",
        "response": fallback_text.strip(),
        "language": language,
        "canonical_query": canonical_query,
        "has_audio": has_audio,
        "has_image": has_image
    }


def ask_gemini_agri_assistant(user_query: str, language: str = "English", context_info: dict = None) -> dict:
    """Backwards-compatible wrapper calling the multimodal engine."""
    return ask_gemini_multimodal(
        query_text=user_query,
        language=language,
        context_info=context_info
    )


def generate_voice_speech_html(text_to_speak: str, lang_code: str = "en-IN") -> str:
    """
    Browser Web Speech Synthesis widget — plays Gemini's advice aloud in native dialect.
    """
    clean_text = text_to_speak.replace('"', '\\"').replace('\n', ' ')
    clean_text = html_mod.escape(clean_text)

    lang_tag = "en-IN"
    btn_label = "🔊 Listen to Advice"
    l_low = lang_code.lower()
    if "hi" in l_low or "hindi" in l_low:
        lang_tag = "hi-IN"
        btn_label = "🔊 सलाह सुनें"
    elif "mr" in l_low or "marathi" in l_low:
        lang_tag = "mr-IN"
        btn_label = "🔊 सल्ला ऐका"
    elif "pa" in l_low or "punjabi" in l_low or "ਪੰਜਾਬੀ" in l_low:
        lang_tag = "pa-IN"
        btn_label = "🔊 ਸਲਾਹ ਸੁਣੋ"
    elif "te" in l_low or "telugu" in l_low:
        lang_tag = "te-IN"
        btn_label = "🔊 సలహా వినండి"
    elif "gu" in l_low or "gujarati" in l_low:
        lang_tag = "gu-IN"
        btn_label = "🔊 સલાહ સાંભળો"
    elif "kn" in l_low or "kannada" in l_low:
        lang_tag = "kn-IN"
        btn_label = "🔊 ಸಲಹೆ ಕೇಳಿ"
    elif "ta" in l_low or "tamil" in l_low:
        lang_tag = "ta-IN"
        btn_label = "🔊 ஆலோசனையைக் கேளுங்கள்"
    elif "bn" in l_low or "bengali" in l_low:
        lang_tag = "bn-IN"
        btn_label = "🔊 পরামর্শ শুনুন"

    return f"""
<div style="margin-top: 8px; display: flex; gap: 8px; flex-wrap: wrap;">
    <button onclick="speakAgriText()" style="background:#059669; color:white; border:none;
        padding:8px 16px; border-radius:20px; cursor:pointer; font-weight:700;
        font-size:0.85rem; display:inline-flex; align-items:center; gap:6px;
        box-shadow:0 2px 8px rgba(5,150,105,0.3);">
        {btn_label}
    </button>
    <button onclick="window.speechSynthesis.cancel()" style="background:#f1f5f9;
        color:#475569; border:1px solid #cbd5e1; padding:8px 12px;
        border-radius:20px; cursor:pointer; font-weight:600; font-size:0.85rem;">
        ⏹️ Stop
    </button>
    <script>
        function speakAgriText() {{
            if ('speechSynthesis' in window) {{
                window.speechSynthesis.cancel();
                var msg = new SpeechSynthesisUtterance("{clean_text}");
                msg.lang = "{lang_tag}";
                msg.rate = 0.92;
                window.speechSynthesis.speak(msg);
            }} else {{
                alert('Speech synthesis not supported on this browser.');
            }}
        }}
    </script>
</div>
"""

def get_engine_status() -> dict:
    """Returns the operational status of the Gemini conversational service and IndicTrans2 translation bridge."""
    key = _get_gemini_key()
    indic_status = {}
    try:
        from services import indictrans_service
        indic_status = indictrans_service.get_translation_status()
    except Exception:
        pass

    if key:
        return {
            "status": "LIVE",
            "model": "Gemini 2.5 Flash",
            "translation_engine": "AI4Bharat IndicTrans2 (Distilled 200M)",
            "api_configured": True,
            "indictrans_details": indic_status
        }
    return {
        "status": "DEMO / SYNTHETIC",
        "model": "Offline Agronomic Expert Engine",
        "translation_engine": "AI4Bharat IndicTrans2 (Distilled 200M)",
        "api_configured": False,
        "indictrans_details": indic_status
    }

def get_offline_expert_response(query: str, language: str = "English", context_info: dict = None) -> str:
    """Direct wrapper for offline expert knowledge fallback."""
    return generate_domain_expert_fallback(query, language, context_info)



import json
import html
import math
import hashlib
import base64
import requests
import streamlit as st
import streamlit.components.v1 as components

from audio_recorder_streamlit import audio_recorder


# ==========================================
# 1. PAGE CONFIGURATION
# ==========================================

st.set_page_config(
    page_title="AI Negotiation Arena",
    page_icon="🤝",
    layout="wide"
)


# ==========================================
# 2. API CONFIGURATION
# ==========================================

ELEVENLABS_API_KEY = st.secrets.get("ELEVENLABS_API_KEY", "")
MAKE_API_KEY = st.secrets.get("MAKE_API_KEY", "")

# Female Buyer voice and male Seller voice
BUYER_VOICE_ID = "hpp4J3VqNfWAUOO0d1Us"
SELLER_VOICE_ID = "JBFqnCBsd6RMkjVDRZzb"


# ==========================================
# 3. CUSTOM CSS
# ==========================================

st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #0b1020, #17152f);
    color: white;
}
.agent {
    background: #182441;
    border: 1px solid #477bc2;
    border-radius: 16px;
    padding: 20px;
    text-align: center;
}
.seller {
    border-color: #a56bd5;
}
.chat {
    background: #19243c;
    border-radius: 12px;
    padding: 14px;
    margin: 10px 0;
    border: 1px solid #293955;
}
.result {
    background: #104333;
    border: 1px solid #20c987;
    border-radius: 16px;
    padding: 22px;
    text-align: center;
    color: white;
}
.no-deal {
    background: #382c17;
    border: 1px solid #d6a62e;
    border-radius: 12px;
    padding: 16px;
    color: #ffd34e;
    text-align: center;
}
</style>
""", unsafe_allow_html=True)


# ==========================================
# 4. HEADER AND SESSION STATE
# ==========================================

st.title("🤝 AI Negotiation Arena")

st.caption(
    "Two autonomous AI agents • Voice-enabled negotiation"
)

if "result" not in st.session_state:
    st.session_state.result = None

if "product_input" not in st.session_state:
    st.session_state.product_input = "Gaming Laptop"

if "last_audio_hash" not in st.session_state:
    st.session_state.last_audio_hash = None

if "playback_id" not in st.session_state:
    st.session_state.playback_id = 0


# ==========================================
# 5. HELPER FUNCTIONS
# ==========================================

def parse_agent(value):

    if isinstance(value, dict):
        return value

    if isinstance(value, str):

        try:
            parsed = json.loads(value)

            if isinstance(parsed, dict):
                return parsed

            if isinstance(parsed, str):
                parsed = json.loads(parsed)

                if isinstance(parsed, dict):
                    return parsed

        except (TypeError, ValueError):
            pass

    return {}


def rupees(value):

    try:
        return f"₹{float(value):,.0f}"

    except (TypeError, ValueError):
        return "—"


def normalize_price(value):

    if isinstance(value, bool):
        return None

    try:
        number = float(value)

        if not math.isfinite(number):
            return None

        return number

    except (TypeError, ValueError):
        return None


# ==========================================
# 6. ELEVENLABS SPEECH-TO-TEXT
# ==========================================

def transcribe_audio(audio_bytes):

    if not ELEVENLABS_API_KEY:
        raise ValueError("ElevenLabs API key is missing.")

    response = requests.post(
        "https://api.elevenlabs.io/v1/speech-to-text",
        headers={
            "xi-api-key": ELEVENLABS_API_KEY
        },
        files={
            "file": (
                "recording.wav",
                audio_bytes,
                "audio/wav"
            )
        },
        data={
            "model_id": "scribe_v2"
        },
        timeout=90
    )

    response.raise_for_status()

    return response.json().get("text", "").strip()


# ==========================================
# 7. ELEVENLABS TEXT-TO-SPEECH
# ==========================================

@st.cache_data(show_spinner=False)
def generate_voice(text, voice_id):

    if not ELEVENLABS_API_KEY:
        raise ValueError("ElevenLabs API key is missing.")

    response = requests.post(
        f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
        params={
            "output_format": "mp3_44100_128"
        },
        headers={
            "xi-api-key": ELEVENLABS_API_KEY,
            "Content-Type": "application/json"
        },
        json={
            "text": text,
            "model_id": "eleven_multilingual_v2"
        },
        timeout=90
    )

    if not response.ok:

        try:
            error_details = response.json()

        except ValueError:
            error_details = response.text

        raise ValueError(
            f"ElevenLabs Error {response.status_code}: {error_details}"
        )

    return response.content


# ==========================================
# 8. NEGOTIATION SETUP
# ==========================================

with st.sidebar:

    st.header("Negotiation Setup")

    webhook = st.text_input(
        "Make Webhook URL",
        type="password",
        help="Paste your private Make custom webhook URL."
    )

    st.divider()

    st.subheader("🎙️ Voice Input")

    st.write(
        "Record your product name using your microphone."
    )

    audio_bytes = audio_recorder(
        text="Click to record",
        recording_color="#e74c3c",
        neutral_color="#477bc2",
        icon_name="microphone",
        icon_size="2x"
    )

    if audio_bytes:

        audio_hash = hashlib.sha256(
            audio_bytes
        ).hexdigest()

        if audio_hash != st.session_state.last_audio_hash:

            st.session_state.last_audio_hash = audio_hash

            try:

                with st.spinner("Transcribing your speech..."):

                    transcript = transcribe_audio(audio_bytes)

                if transcript:

                    st.session_state.product_input = transcript

                    st.success(
                        f"Recognized: {transcript}"
                    )

                    st.rerun()

                else:

                    st.warning(
                        "No speech detected. Please record again."
                    )

            except Exception as error:

                st.error(
                    f"Transcription failed: {error}"
                )

    st.divider()

    voice_enabled = st.checkbox(
        "🔊 Enable AI voice responses",
        value=True
    )

    with st.form("setup"):

        product = st.text_input(
            "Product",
            key="product_input"
        )

        st.subheader("🔵 Buyer AI")

        buyer_open = st.number_input(
            "Opening offer (₹)",
            min_value=1,
            value=60000,
            step=1000
        )

        buyer_max = st.number_input(
            "Maximum budget (₹)",
            min_value=1,
            value=75000,
            step=1000
        )

        st.subheader("🟣 Seller AI")

        seller_open = st.number_input(
            "Initial asking price (₹)",
            min_value=1,
            value=80000,
            step=1000
        )

        seller_min = st.number_input(
            "Minimum acceptable price (₹)",
            min_value=1,
            value=68000,
            step=1000
        )

        start = st.form_submit_button(
            "🚀 Start Negotiation",
            use_container_width=True
        )


# ==========================================
# 9. START NEGOTIATION
# ==========================================

if start:

    st.session_state.result = None

    if not product.strip():

        st.error("Please enter a product name.")

    elif not webhook.startswith("https://"):

        st.error("Enter your valid Make webhook URL.")

    elif not MAKE_API_KEY:

        st.error(
            "Make API key is missing from Streamlit Secrets."
        )

    elif buyer_open > buyer_max:

        st.error(
            "Buyer opening offer cannot exceed maximum budget."
        )

    elif seller_min > seller_open:

        st.error(
            "Seller minimum cannot exceed initial asking price."
        )

    else:

        payload = {
            "product": product.strip(),
            "buyer_opening_offer": buyer_open,
            "buyer_max_budget": buyer_max,
            "seller_initial_price": seller_open,
            "seller_minimum_price": seller_min,
            "max_rounds": 2
        }

        try:

            with st.spinner(
                "🤖 Buyer AI and Seller AI are negotiating..."
            ):

                response = requests.post(
                    webhook,
                    json=payload,
                    headers={
                        "x-make-apikey": MAKE_API_KEY
                    },
                    timeout=120
                )

                response.raise_for_status()

                result_data = response.json()

                if not isinstance(result_data, dict):

                    raise ValueError(
                        "Webhook returned an invalid JSON structure."
                    )

                st.session_state.result = result_data

                st.session_state.playback_id += 1

        except requests.exceptions.Timeout:

            st.error(
                "Negotiation timed out. Please try again."
            )

        except requests.exceptions.RequestException as error:

            st.error(
                f"Webhook connection failed: {error}"
            )

        except ValueError as error:

            st.error(
                f"Invalid webhook response: {error}"
            )


# ==========================================
# 10. AGENT LAYOUT
# ==========================================

buyer_col, conversation_col, seller_col = st.columns(
    [1, 2, 1]
)

with buyer_col:

    buyer_card = (
        '<div class="agent">'
        '<div style="font-size:65px">👩🏻‍💼</div>'
        '<h3>Buyer AI</h3>'
        '<p>🔵 Strategic · Firm</p>'
        '</div>'
    )

    st.markdown(
        buyer_card,
        unsafe_allow_html=True
    )


with seller_col:

    seller_card = (
        '<div class="agent seller">'
        '<div style="font-size:65px">🧑🏻‍💼</div>'
        '<h3>Seller AI</h3>'
        '<p>🟣 Confident · Persuasive</p>'
        '</div>'
    )

    st.markdown(
        seller_card,
        unsafe_allow_html=True
    )


# ==========================================
# 11. NEGOTIATION TRANSCRIPT
# ==========================================

with conversation_col:

    st.subheader("💬 Negotiation Transcript")

    data = st.session_state.result

    if not data:

        st.info(
            "Configure your negotiation and press Start Negotiation."
        )

    else:

        st.write(
            f"**Product:** {data.get('product', product)}"
        )

        labels = [
            (
                "Round 1 · Buyer AI",
                "buyer_round_1",
                "🔵",
                BUYER_VOICE_ID
            ),
            (
                "Round 1 · Seller AI",
                "seller_round_1",
                "🟣",
                SELLER_VOICE_ID
            ),
            (
                "Round 2 · Buyer AI",
                "buyer_round_2",
                "🔵",
                BUYER_VOICE_ID
            ),
            (
                "Round 2 · Seller AI",
                "seller_round_2",
                "🟣",
                SELLER_VOICE_ID
            )
        ]

        parsed = {}

        voice_playlist = []

        for label, key, emoji, voice_id in labels:

            agent = parse_agent(data.get(key))

            parsed[key] = agent

            if agent:

                spoken_text = str(
                    agent.get(
                        "spoken_response",
                        "No response"
                    )
                )

                spoken = html.escape(spoken_text)

                decision = html.escape(
                    str(
                        agent.get("decision", "—")
                    ).upper()
                )

                price = rupees(
                    agent.get("proposed_price")
                )

                chat_html = (
                    '<div class="chat">'
                    f'<b>{emoji} {label}</b>'
                    '<br>'
                    f'{spoken}'
                    '<br>'
                    f'<b>{price}</b> · {decision}'
                    '</div>'
                )

                st.markdown(
                    chat_html,
                    unsafe_allow_html=True
                )

                # Generate voices in chronological order
                if voice_enabled and spoken_text.strip():

                    try:

                        with st.spinner(
                            f"Generating {label} voice..."
                        ):

                            audio = generate_voice(
                                spoken_text,
                                voice_id
                            )

                        voice_playlist.append({
                            "label": label,
                            "audio": base64.b64encode(
                                audio
                            ).decode("utf-8")
                        })

                    except Exception as error:

                        st.warning(
                            f"Voice generation unavailable for "
                            f"{label}: {error}"
                        )

            else:

                st.warning(
                    f"{label}: Response missing or invalid."
                )


        # ==========================================
        # 12. AUTOMATIC PLAYBACK WITH LIVE SPEAKER GLOW
        # ==========================================

        if voice_enabled and voice_playlist:

            st.markdown("### 🎧 Automatic AI Conversation")

            playlist_json = json.dumps(voice_playlist)

            player_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
            <style>

            body {{
                background: #19243c;
                color: white;
                font-family: Arial, sans-serif;
                padding: 12px;
                margin: 0;
            }}

            .speakers {{
                display: flex;
                gap: 15px;
                justify-content: center;
                margin: 15px 0;
            }}

            .speaker {{
                flex: 1;
                text-align: center;
                padding: 18px 8px;
                border-radius: 16px;
                background: #182441;
                border: 2px solid #34415e;
                opacity: 0.55;
                transition: all 0.3s ease;
            }}

            .speaker .avatar {{
                font-size: 45px;
            }}

            .speaker.active-buyer {{
                opacity: 1;
                border-color: #3b82f6;
                box-shadow:
                    0 0 10px #3b82f6,
                    0 0 25px #3b82f6,
                    inset 0 0 15px rgba(59,130,246,0.25);
                animation: buyerGlow 1.4s infinite alternate;
            }}

            .speaker.active-seller {{
                opacity: 1;
                border-color: #a855f7;
                box-shadow:
                    0 0 10px #a855f7,
                    0 0 25px #a855f7,
                    inset 0 0 15px rgba(168,85,247,0.25);
                animation: sellerGlow 1.4s infinite alternate;
            }}

            @keyframes buyerGlow {{
                from {{ box-shadow: 0 0 8px #3b82f6; }}
                to {{ box-shadow: 0 0 28px #3b82f6; }}
            }}

            @keyframes sellerGlow {{
                from {{ box-shadow: 0 0 8px #a855f7; }}
                to {{ box-shadow: 0 0 28px #a855f7; }}
            }}

            .status {{
                text-align: center;
                font-size: 14px;
                margin: 12px 0;
                font-weight: bold;
            }}

            .progress {{
                height: 8px;
                background: #293955;
                border-radius: 10px;
                overflow: hidden;
            }}

            .progress-bar {{
                height: 8px;
                width: 0%;
                background: #20c987;
                transition: width 0.3s;
            }}

            </style>
            </head>

            <body>

            <div style="font-size:17px;font-weight:bold;">
                🔊 AI Negotiation — Live Conversation
            </div>

            <div class="speakers">

                <div id="buyer" class="speaker">
                    <div class="avatar">👩🏻‍💼</div>
                    <b>Buyer AI</b>
                    <div style="font-size:12px;">🔵 Strategic</div>
                </div>

                <div id="seller" class="speaker">
                    <div class="avatar">🧑🏻‍💼</div>
                    <b>Seller AI</b>
                    <div style="font-size:12px;">🟣 Persuasive</div>
                </div>

            </div>

            <div id="status" class="status">
                Preparing conversation...
            </div>

            <div class="progress">
                <div id="progress" class="progress-bar"></div>
            </div>

            <audio id="player" autoplay></audio>

            <script>

            const tracks = {playlist_json};

            const player = document.getElementById("player");
            const status = document.getElementById("status");
            const progress = document.getElementById("progress");

            const buyer = document.getElementById("buyer");
            const seller = document.getElementById("seller");

            let current = 0;

            function playNext() {{

                if (current >= tracks.length) {{

                    status.innerText =
                        "✅ Negotiation conversation completed!";

                    progress.style.width = "100%";

                    buyer.className = "speaker";
                    seller.className = "speaker";

                    return;
                }}

                const track = tracks[current];

                const isBuyer =
                    track.label.toLowerCase().includes("buyer");

                buyer.className = isBuyer
                    ? "speaker active-buyer"
                    : "speaker";

                seller.className = isBuyer
                    ? "speaker"
                    : "speaker active-seller";

                status.innerText =
                    "🔊 Now speaking: " + track.label +
                    " (" + (current + 1) +
                    " of " + tracks.length + ")";

                progress.style.width =
                    ((current / tracks.length) * 100) + "%";

                player.src =
                    "data:audio/mp3;base64," + track.audio;

                player.load();

                player.play().catch(function(error) {{

                    status.innerText =
                        "Browser blocked playback: " + error.message;

                }});
            }}

            player.onended = function() {{

                current++;

                playNext();

            }};

            player.onerror = function() {{

                status.innerText = "Audio playback error.";

            }};

            window.addEventListener("load", function() {{

                setTimeout(playNext, 500);

            }});

            </script>

            </body>
            </html>
            """

            components.html(
                player_html,
                height=300,
                scrolling=False
            )


        # ==========================================
        # 13. FINAL DEAL VALIDATION
        # ==========================================

        negotiation_sequence = [

            parsed.get("buyer_round_1", {}),

            parsed.get("seller_round_1", {}),

            parsed.get("buyer_round_2", {}),

            parsed.get("seller_round_2", {})

        ]

        deal = False

        agreed_price = None

        for previous, current in zip(
            negotiation_sequence,
            negotiation_sequence[1:]
        ):

            previous_price = normalize_price(
                previous.get("proposed_price")
            )

            current_price = normalize_price(
                current.get("proposed_price")
            )

            current_decision = str(
                current.get("decision", "")
            ).strip().lower()

            if previous_price is None:
                continue

            if current_price is None:
                continue

            if current_decision != "accept":
                continue

            if previous_price != current_price:
                continue

            if not (
                seller_min <= current_price <= buyer_max
            ):
                continue

            deal = True

            agreed_price = current_price

            break


        # ==========================================
        # 14. FINAL RESULT DISPLAY
        # ==========================================

        if deal:

            savings = seller_open - agreed_price

            result_html = (
                '<div class="result">'
                '<h2>🤝 DEAL REACHED!</h2>'
                f'<h1>{rupees(agreed_price)}</h1>'
                '<p>Both AI agents agreed on a valid price.</p>'
                '</div>'
            )

            st.markdown(
                result_html,
                unsafe_allow_html=True
            )

            st.metric(
                "Buyer savings from asking price",
                rupees(savings)
            )

        else:

            result_html = (
                '<div class="no-deal">'
                '<h3>NO DEAL</h3>'
                '<p>The agents did not reach a mutually '
                'accepted price within both limits.</p>'
                '</div>'
            )

            st.markdown(
                result_html,
                unsafe_allow_html=True
            )


        # ==========================================
        # 15. RAW AI RESPONSE
        # ==========================================

        with st.expander("View raw AI response"):

            st.json(data)

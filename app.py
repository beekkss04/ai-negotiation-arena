
import json
import html
import math
import requests
import streamlit as st


# ==========================================
# 1. PAGE CONFIGURATION
# ==========================================

st.set_page_config(
    page_title="AI Negotiation Arena",
    page_icon="🤝",
    layout="wide"
)


# ==========================================
# 2. CUSTOM CSS
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
# 3. HEADER
# ==========================================

st.title("🤝 AI Negotiation Arena")

st.caption(
    "Two autonomous AI agents • Real-time price negotiation"
)


# ==========================================
# 4. SESSION STATE
# ==========================================

if "result" not in st.session_state:
    st.session_state.result = None


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
# 6. NEGOTIATION SETUP
# ==========================================

with st.sidebar:

    st.header("Negotiation Setup")

    webhook = st.text_input(
        "Make Webhook URL",
        type="password",
        help="Paste your private Make custom webhook URL."
    )

    with st.form("setup"):

        product = st.text_input(
            "Product",
            "Gaming Laptop"
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
# 7. START NEGOTIATION
# ==========================================

if start:

    st.session_state.result = None

    if not product.strip():

        st.error("Please enter a product name.")

    elif not webhook.startswith("https://"):

        st.error("Enter your valid Make webhook URL.")

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
                    timeout=120
                )

                response.raise_for_status()

                result_data = response.json()

                if not isinstance(result_data, dict):

                    raise ValueError(
                        "Webhook returned an invalid JSON structure."
                    )

                st.session_state.result = result_data

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
# 8. AGENT LAYOUT
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
# 9. NEGOTIATION TRANSCRIPT
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
            ("Round 1 · Buyer AI", "buyer_round_1", "🔵"),
            ("Round 1 · Seller AI", "seller_round_1", "🟣"),
            ("Round 2 · Buyer AI", "buyer_round_2", "🔵"),
            ("Round 2 · Seller AI", "seller_round_2", "🟣")
        ]

        parsed = {}

        for label, key, emoji in labels:

            agent = parse_agent(data.get(key))

            parsed[key] = agent

            if agent:

                spoken = html.escape(
                    str(
                        agent.get(
                            "spoken_response",
                            "No response"
                        )
                    )
                )

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

            else:

                st.warning(
                    f"{label}: Response missing or invalid."
                )


        # ==========================================
        # 10. FINAL DEAL VALIDATION
        # ==========================================

        # Maintain the actual chronological order
        # of the negotiation.

        negotiation_sequence = [

            parsed.get("buyer_round_1", {}),

            parsed.get("seller_round_1", {}),

            parsed.get("buyer_round_2", {}),

            parsed.get("seller_round_2", {})

        ]

        deal = False

        agreed_price = None

        # Compare each response with the immediately
        # preceding offer.
        #
        # Buyer R1 -> Seller R1
        # Seller R1 -> Buyer R2
        # Buyer R2 -> Seller R2

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

            # The current agent must explicitly accept.

            if current_decision != "accept":
                continue

            # Accepted price must match the previous offer.

            if previous_price != current_price:
                continue

            # Both parties' limits must be respected.

            if not (
                seller_min <= current_price <= buyer_max
            ):
                continue

            deal = True

            agreed_price = current_price

            break


        # ==========================================
        # 11. FINAL RESULT DISPLAY
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
        # 12. RAW AI RESPONSE
        # ==========================================

        with st.expander("View raw AI response"):

            st.json(data)

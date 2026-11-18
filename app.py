
import json
import requests
import streamlit as st

st.set_page_config(
    page_title="AI Negotiation Arena",
    page_icon="🤝",
    layout="wide"
)

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
}
.result {
    background: #104333;
    border: 1px solid #20c987;
    border-radius: 16px;
    padding: 22px;
    text-align: center;
}
</style>
""", unsafe_allow_html=True)

st.title("🤝 AI Negotiation Arena")
st.caption("Two autonomous AI agents • Real-time price negotiation")

with st.sidebar:
    st.header("Negotiation Setup")

    webhook = st.text_input(
        "Make Webhook URL",
        type="password",
        help="Paste your private Make custom webhook URL."
    )

    with st.form("setup"):
        product = st.text_input("Product", "Gaming Laptop")

        st.subheader("🔵 Buyer AI")
        buyer_open = st.number_input(
            "Opening offer (₹)", value=60000, step=1000
        )
        buyer_max = st.number_input(
            "Maximum budget (₹)", value=75000, step=1000
        )

        st.subheader("🟣 Seller AI")
        seller_open = st.number_input(
            "Initial asking price (₹)", value=80000, step=1000
        )
        seller_min = st.number_input(
            "Minimum acceptable price (₹)", value=68000, step=1000
        )

        start = st.form_submit_button(
            "🚀 Start Negotiation",
            use_container_width=True
        )

def parse_agent(value):
    if isinstance(value, dict):
        return value
    try:
        return json.loads(value)
    except (TypeError, ValueError):
        return {}

def rupees(value):
    try:
        return f"₹{float(value):,.0f}"
    except (TypeError, ValueError):
        return "—"

if "result" not in st.session_state:
    st.session_state.result = None

if start:
    if not webhook.startswith("https://"):
        st.error("Enter your valid Make webhook URL.")
    elif buyer_open > buyer_max:
        st.error("Opening offer cannot exceed buyer's budget.")
    elif seller_min > seller_open:
        st.error("Seller minimum cannot exceed asking price.")
    else:
        payload = {
            "product": product,
            "buyer_opening_offer": buyer_open,
            "buyer_max_budget": buyer_max,
            "seller_initial_price": seller_open,
            "seller_minimum_price": seller_min,
            "max_rounds": 2
        }

        try:
            with st.spinner("🤖 Buyer AI and Seller AI are negotiating..."):
                response = requests.post(
                    webhook,
                    json=payload,
                    timeout=120
                )
                response.raise_for_status()
                st.session_state.result = response.json()
        except Exception as error:
            st.error(f"Negotiation failed: {error}")

buyer_col, conversation_col, seller_col = st.columns([1, 2, 1])

with buyer_col:
    st.markdown("""
    <div class="agent">
        <div style="font-size:65px">👩🏻‍💼</div>
        <h3>Buyer AI</h3>
        <p>🔵 Strategic · Firm</p>
    </div>
    """, unsafe_allow_html=True)

with seller_col:
    st.markdown("""
    <div class="agent seller">
        <div style="font-size:65px">🧑🏻‍💼</div>
        <h3>Seller AI</h3>
        <p>🟣 Confident · Persuasive</p>
    </div>
    """, unsafe_allow_html=True)

with conversation_col:
    st.subheader("💬 Negotiation Transcript")

    data = st.session_state.result

    if not data:
        st.info("Configure your negotiation and press Start Negotiation.")
    else:
        st.write(f"**Product:** {data.get('product', 'Product')}")

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
                st.markdown(
                    f"""<div class="chat">
                    <b>{emoji} {label}</b><br>
                    {agent.get('spoken_response', 'No response')}<br>
                    <b>{rupees(agent.get('proposed_price'))}</b>
                    · {agent.get('decision', '—').upper()}
                    </div>""",
                    unsafe_allow_html=True
                )

        buyer = parsed.get("buyer_round_2", {})
        seller = parsed.get("seller_round_2", {})

        buyer_price = buyer.get("proposed_price")
        seller_price = seller.get("proposed_price")

        buyer_accepted = buyer.get("decision") == "accept"
        seller_accepted = seller.get("decision") == "accept"

        deal = (
            buyer_accepted
            and seller_accepted
            and isinstance(buyer_price, (int, float))
            and isinstance(seller_price, (int, float))
            and buyer_price == seller_price
            and seller_min <= buyer_price <= buyer_max
        )

        if deal:
            savings = seller_open - buyer_price
            st.markdown(
                f"""<div class="result">
                <h2>🤝 DEAL REACHED!</h2>
                <h1>{rupees(buyer_price)}</h1>
                Both AI agents accepted the same valid price.
                </div>""",
                unsafe_allow_html=True
            )
            st.metric("Buyer savings from asking price", rupees(savings))
        else:
            st.warning("NO VALIDATED DEAL — the acceptance and price limits did not all match.")

        with st.expander("View raw AI response"):
            st.json(data)

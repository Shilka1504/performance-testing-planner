import streamlit as st
import base64
from openai import OpenAI
import os
from dotenv import load_dotenv

# ────────────────────────────────────────────────
# Load API key — works both on Streamlit Cloud and locally
# ────────────────────────────────────────────────
if "OPENAI_API_KEY" in st.secrets:
    api_key = st.secrets["OPENAI_API_KEY"]
    base_url = None                     # standard OpenAI endpoint
elif "XAI_API_KEY" in st.secrets:
    api_key = st.secrets["XAI_API_KEY"]
    base_url = "https://api.x.ai/v1"    # xAI endpoint
else:
    # Fallback for local development (using .env file)
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("XAI_API_KEY")
    base_url = os.getenv("BASE_URL")    # optional: set in .env if using xAI locally

if not api_key:
    st.error(
        "API key is missing!\n\n"
        "**On Streamlit Cloud**:\n"
        "→ Go to App Settings → Secrets tab\n"
        "→ Add one of these lines:\n"
        '  OPENAI_API_KEY = "sk-proj-..."\n'
        '  or\n'
        '  XAI_API_KEY = "xai-..."\n\n'
        "**Locally**:\n"
        "→ Create .env file in project folder with the same line"
    )
    st.stop()

# Initialize client
client = OpenAI(
    api_key=api_key,
    base_url=base_url,
    timeout=120.0   # Increased timeout to help with slower connections
)

# Choose model — change here depending on what you have access to / want to use
# Recommended cheap & capable option right now:
MODEL = "gpt-4o-mini"               # OpenAI - very good vision + cheap
# MODEL = "gpt-4o"                  # OpenAI - more accurate but more expensive
# MODEL = "grok-2-vision-1212"      # xAI - if you have credits and prefer Grok
# MODEL = "grok-4-1-fast-reasoning" # xAI alternative

# Helper function to encode uploaded image to base64
def encode_image(image_file):
    return base64.b64encode(image_file.read()).decode('utf-8')

# ────────────────────────────────────────────────
# Streamlit App UI
# ────────────────────────────────────────────────
st.set_page_config(page_title="Performance Testing Planner", layout="wide")
st.title("Performance Testing Plan Generator")
st.markdown(
    "Upload your **architecture diagram** (image) and **use-case / requirements document** (Markdown or text).  \n"
    "The app uses AI to generate Non-Functional Requirements, capacity estimates, testing strategy, and more."
)

# Upload sections
col1, col2 = st.columns(2)
with col1:
    diagram_file = st.file_uploader(
        "Architecture Diagram (PNG / JPG / JPEG)",
        type=["png", "jpg", "jpeg"]
    )
with col2:
    md_file = st.file_uploader(
        "Use Cases / Requirements (MD / TXT)",
        type=["md", "txt"]
    )

# Generate button
if st.button("Generate Performance Testing Plan", type="primary") and diagram_file and md_file:
    with st.spinner("Analyzing diagram + use cases and generating plan..."):
        try:
            # Read markdown / text file
            md_content = md_file.read().decode("utf-8")

            # Encode diagram image
            image_b64 = encode_image(diagram_file)

            # Multimodal prompt
            prompt = f"""
You are an experienced Performance Test Architect.

Analyze the attached **architecture diagram** and the following **use-case / functional description**:

USE CASES / REQUIREMENTS:
{md_content}

Based on the diagram and use cases, produce a realistic and professional **Performance Testing kick-off document** containing:

1. Non-Functional Performance Requirements (NFRs)
   - Response time (p50, p95, p99)
   - Throughput (requests/sec or TPS)
   - Concurrency / concurrent users
   - Error rate
   - Availability / uptime targets

2. Capacity & Scalability Estimation
   - Estimated maximum healthy load
   - Likely bottlenecks (CPU, DB, network, cache, etc.)
   - Scaling recommendations

3. Performance Test Strategy
   - Recommended test types (smoke, load, stress, soak/endurance, spike)
   - Key business scenarios to test
   - Tools recommendation (JMeter, k6, Locust, Gatling, etc.)
   - Test data strategy
   - Ramp-up / ramp-down pattern suggestions

4. Test Environment & Setup Needs
   - Recommended environment similarity to production
   - Monitoring stack suggestions (Prometheus, Grafana, New Relic, Datadog, etc.)

5. Success / Exit Criteria
   - KPIs and acceptance thresholds

6. Risks & Assumptions

Format the output using clear markdown headings, bullet points, and tables where helpful.
Be specific and realistic — do not invent unrealistic numbers without justification.
"""

            # Call API (multimodal: text + image)
            response = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}}
                        ]
                    }
                ],
                max_tokens=3500,
                temperature=0.65
            )

            generated_plan = response.choices[0].message.content.strip()

        except Exception as e:
            st.error(f"API call failed: {str(e)}\n\n"
                     f"• Check if you have credits/balance\n"
                     f"• Verify API key is correct in Secrets\n"
                     f"• Try a different model if needed")
            st.stop()

    # ── Results ───────────────────────────────────────
    st.success("Performance Testing Plan generated!")

    # Show the plan
    st.markdown(generated_plan)

    # Download button
    st.download_button(
        label="📥 Download Plan as Markdown",
        data=generated_plan,
        file_name="performance-test-plan.md",
        mime="text/markdown"
    )

# ── Sidebar help ─────────────────────────────────────
st.sidebar.header("Quick Guide")
st.sidebar.markdown("""
1. Upload one architecture diagram  
2. Upload use-case / requirements document (markdown preferred)  
3. Click **Generate**  
4. Review → download the result  

**Tip**: The better structured your markdown file is, the more accurate & detailed the output will be.
""")

st.sidebar.info(f"Using model: **{MODEL}**")

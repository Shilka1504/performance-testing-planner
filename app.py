import streamlit as st
import base64
from openai import OpenAI
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()
api_key = os.getenv("XAI_API_KEY")
if not api_key:
    st.error("Missing XAI_API_KEY in .env file. Add it and restart the app.")
    st.stop()

# Initialize Grok API client (compatible with OpenAI SDK)
client = OpenAI(base_url="https://api.x.ai/v1", api_key=api_key)
MODEL = "grok-beta"  # Use a multimodal model like grok-beta for image + text analysis

# Helper function to encode image to base64 for API
def encode_image(image_file):
    return base64.b64encode(image_file.read()).decode('utf-8')

# Streamlit App Configuration
st.set_page_config(page_title="Performance Testing Planner", layout="wide")
st.title("Performance Testing Application")
st.markdown("Upload your architecture diagram and use case MD file. The app will generate NFRs, capacity planning, strategy, and PT essentials using AI analysis.")

# File Uploads
col1, col2 = st.columns(2)
with col1:
    diagram_file = st.file_uploader("Upload Architecture Diagram (PNG/JPG)", type=["png", "jpg", "jpeg"])
with col2:
    md_file = st.file_uploader("Upload Use Case MD File", type=["md", "txt"])

if st.button("Generate PT Plan") and diagram_file and md_file:
    with st.spinner("Analyzing uploads and generating plan..."):
        # Read MD file content
        md_content = md_file.read().decode("utf-8")
        
        # Encode diagram image
        image_base64 = encode_image(diagram_file)
        
        # Prepare multimodal prompt for Grok API
        prompt = f"""
        Analyze the following architecture diagram (image) and use case description from the MD file.
        
        Architecture Diagram: [Image attached]
        
        Use Cases (MD Content): {md_content}
        
        Based on this, generate a complete Performance Testing (PT) plan including:
        1. **Non-Functional Requirements (NFRs)**: Focus on performance aspects like response time, throughput, scalability, reliability, availability. Provide examples with metrics (e.g., <2s response time under 1000 users).
        2. **PT Capacity Planning**: Estimate max concurrent users, load thresholds, bottlenecks, and scaling needs based on the architecture.
        3. **PT Strategy**: Outline test types (load, stress, endurance), tools (e.g., JMeter), scenarios, execution steps, entry/exit criteria.
        4. **Everything Needed to Start PT**: Objectives, scope, test environment setup, data preparation, KPIs (e.g., CPU <80%), monitoring, risks/assumptions, reporting template.
        
        Structure the output in clear sections with bullet points or tables for readability.
        """
        
        # API Call (multimodal: text + image)
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "user", "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
                    ]}
                ],
                max_tokens=2000,
                temperature=0.7
            )
            generated_plan = response.choices[0].message.content
        except Exception as e:
            st.error(f"Error generating plan: {str(e)}")
            st.stop()
    
    # Display Results
    st.success("PT Plan Generated!")
    st.markdown(generated_plan)

# Run instructions
st.sidebar.header("How to Use")
st.sidebar.markdown("""
1. Upload files.
2. Click 'Generate PT Plan'.
3. Review the AI-generated output.
4. Refine prompts or inputs if needed.
""")
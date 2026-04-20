import streamlit as st
import google.generativeai as genai
import pandas as pd
import json
import io

# --- 1. SETUP ---
st.set_page_config(page_title="AI Statement Extractor", layout="wide")
st.title("📄 Smart AI Statement Extractor")

# --- 2. SIDEBAR ---
with st.sidebar:
    st.header("Authentication")
    api_key = st.text_input("Enter Gemini API Key", type="password")
    st.info("The app will automatically find the best model for your key.")

# --- 3. UPLOADER ---
uploaded_file = st.file_uploader("Upload Statement (PDF or Image)", type=['pdf', 'png', 'jpg', 'jpeg'])

# --- 4. THE AUTO-MODEL FINDER ---
def get_best_model():
    """Automatically finds an available Flash model for this API key."""
    try:
        available_models = genai.list_models()
        # Look for a model that supports 'generateContent' and has 'flash' in the name
        for m in available_models:
            if 'generateContent' in m.supported_generation_methods:
                if 'gemini-1.5-flash' in m.name:
                    return m.name
        # Fallback to any model that supports generateContent if flash isn't found
        for m in available_models:
            if 'generateContent' in m.supported_generation_methods:
                return m.name
    except Exception as e:
        st.error(f"Could not list models: {e}")
    return None

# --- 5. MAIN LOGIC ---
if uploaded_file and api_key:
    if st.button("🚀 Process Document"):
        with st.spinner("AI is analyzing..."):
            try:
                # Configure AI
                genai.configure(api_key=api_key)
                
                # Automatically find the correct model ID (Fixes 404 error)
                model_id = get_best_model()
                
                if not model_id:
                    st.error("No compatible models found for this API Key.")
                    st.stop()
                
                st.toast(f"Using model: {model_id}")
                model = genai.GenerativeModel(model_id)

                # Prepare file and prompt
                file_bytes = uploaded_file.getvalue()
                prompt = """
                Extract the following into a JSON format:
                - Vendor Name
                - Statement Date
                - Total Debits
                - Total Credits
                - Final Balance
                - List of individual transactions with: Date, Description, Debit, Credit, Balance.
                Return ONLY the JSON.
                """

                # Send request
                response = model.generate_content([
                    {"mime_type": uploaded_file.type, "data": file_bytes},
                    prompt
                ])

                # Clean JSON response
                raw_text = response.text.replace('```json', '').replace('```', '').strip()
                data = json.loads(raw_text)

                # Display Results
                st.success(f"Extraction Successful for {data.get('Vendor Name')}")
                
                # Show summary
                c1, c2, c3 = st.columns(3)
                c1.metric("Debits", data.get("Total Debits"))
                c2.metric("Credits", data.get("Total Credits"))
                c3.metric("Final Balance", data.get("Final Balance"))

                # Show table
                df = pd.DataFrame(data.get('transactions', []))
                st.dataframe(df, use_container_width=True)

                # Export
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df.to_excel(writer, index=False)
                
                st.download_button(
                    label="📥 Download Excel",
                    data=output.getvalue(),
                    file_name=f"Extract_{data.get('Vendor Name')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

            except Exception as e:
                st.error("Processing Error")
                st.expander("Details").write(str(e))
else:
    if not api_key:
        st.warning("Please enter your API Key in the sidebar.")
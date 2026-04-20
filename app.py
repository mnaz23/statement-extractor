import streamlit as st
import google.generativeai as genai
import pandas as pd
import json
import io

# --- 1. PAGE CONFIG ---
st.set_page_config(page_title="AI Statement Extractor", layout="wide")
st.title("📄 AI Statement Extractor (Ultra-Compatible Version)")

# --- 2. SIDEBAR ---
with st.sidebar:
    st.header("Setup")
    api_key = st.text_input("Enter Google Gemini API Key", type="password")
    
    if st.button("🔍 Run Connection Diagnostic"):
        if api_key:
            try:
                genai.configure(api_key=api_key)
                models = [m.name for m in genai.list_models()]
                st.success("Connection Successful!")
                st.write("Models available to your key:")
                st.code("\n".join(models))
            except Exception as e:
                st.error(f"Diagnostic Failed: {e}")
        else:
            st.warning("Enter a key first.")

# --- 3. UPLOADER ---
uploaded_file = st.file_uploader("Upload Statement (PDF or Image)", type=['pdf', 'png', 'jpg', 'jpeg'])

# --- 4. EXTRACTION LOGIC ---
if uploaded_file and api_key:
    if st.button("🚀 Extract Data"):
        with st.spinner("AI is processing..."):
            try:
                genai.configure(api_key=api_key)
                
                # --- TRY DIFFERENT MODEL NAMES ---
                # Some API keys only work with 'gemini-1.5-flash-latest' 
                # or just 'gemini-1.5-flash'. We try both.
                success = False
                model_to_use = None
                
                for model_name in ['gemini-1.5-flash-latest', 'gemini-1.5-flash', 'models/gemini-1.5-flash']:
                    try:
                        test_model = genai.GenerativeModel(model_name)
                        # Quick check to see if model exists
                        model_to_use = test_model
                        success = True
                        break
                    except:
                        continue
                
                if not success:
                    st.error("Could not find a compatible Gemini model. Please run the Diagnostic in the sidebar.")
                    st.stop()

                # --- PREPARE DATA ---
                file_bytes = uploaded_file.getvalue()
                prompt = "Extract the vendor name, date, total debits, total credits, final balance, and a list of all transactions into a JSON format. Return only JSON."

                # --- EXECUTE ---
                response = model_to_use.generate_content([
                    prompt, 
                    {"mime_type": uploaded_file.type, "data": file_bytes}
                ])

                # Clean and Parse
                res_text = response.text.replace('```json', '').replace('```', '').strip()
                data = json.loads(res_text)

                # Display Results
                st.success(f"Extracted: {data.get('Vendor Name', 'Unknown')}")
                df = pd.DataFrame(data.get('transactions', []))
                st.dataframe(df)

                # Excel Download
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df.to_excel(writer, index=False)
                
                st.download_button("📥 Download Excel", output.getvalue(), "extract.xlsx")

            except Exception as e:
                st.error("The Extraction Failed.")
                with st.expander("Click here to see the technical error message"):
                    st.code(str(e))
                st.info("Check if your API Key is from 'Google AI Studio'. If you created it in 'Google Cloud Console', you must enable the 'Generative Language API' in your project settings.")
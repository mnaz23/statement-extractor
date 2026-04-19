import streamlit as st
import google.generativeai as genai
import pandas as pd
import json
import io

# 1. UI Setup
st.set_page_config(page_title="Statement AI Extractor")
st.title("📄 Statement to Excel AI")

# 2. Key Setup
api_key = st.sidebar.text_input("Enter Gemini API Key", type="password")

# 3. File Upload
uploaded_file = st.file_uploader("Upload PDF or Image", type=['pdf', 'png', 'jpg', 'jpeg'])

if uploaded_file and api_key:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')

    if st.button("Extract Data"):
        with st.spinner("Gemini is reading the statement..."):
            # Prepare the file data
            file_bytes = uploaded_file.getvalue()
            
            # The Prompt - Tell the AI exactly what to do
            prompt = """
            Extract the following from this document into a JSON format:
            - Vendor Name
            - Statement Date
            - Total Debits, Total Credits, Final Balance
            - A list of transactions with columns: Date, Doc_No, Description, Amount, Balance.
            Only return the JSON code.
            """

            # Send to Gemini
            response = model.generate_content([
                {"mime_type": uploaded_file.type, "data": file_bytes},
                prompt
            ])

            try:
                # Clean the response and convert to JSON
                raw_json = response.text.replace('```json', '').replace('```', '').strip()
                data = json.loads(raw_json)

                # Show Summary Metrics
                st.subheader(f"Vendor: {data['Vendor Name']}")
                st.write(f"Statement Date: {data['Statement Date']}")
                
                # Convert list to Table
                df = pd.DataFrame(data['transactions'])
                st.dataframe(df)

                # Create Excel Download
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                    df.to_excel(writer, index=False)
                
                st.download_button(
                    label="📥 Download Excel",
                    data=buffer.getvalue(),
                    file_name="statement.xlsx",
                    mime="application/vnd.ms-excel"
                )
            except:
                st.error("The AI had trouble formatting the data. Please try again.")
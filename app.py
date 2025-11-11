import streamlit as st
import google.generativeai as genai
import pandas as pd
import pdfplumber
import os

# --- Set Page Title and Logo ---
st.set_page_config(page_title="DataSage", page_icon="logo.png")

# --- Load Custom CSS for "Inter" Font & Centering ---
def load_css(file_name):
    try:
        with open(file_name) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        st.error(f"CSS file '{file_name}' not found. Please make sure 'style.css' is in the same folder as 'app.py'.")

load_css("style.css")

# --- Authentication ---
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
except (KeyError, AttributeError):
    st.error("⚠️ API key not found. Please set `GOOGLE_API_KEY` in Streamlit secrets.")
    st.stop()

# --- Model Selection ---
model = genai.GenerativeModel('models/gemini-2.5-flash')

# --- Function to Read All File Types ---
def read_file_content(uploaded_file):
    """Reads the content of an uploaded file and returns it as a string."""
    try:
        # Get the file extension
        file_name = uploaded_file.name
        file_extension = os.path.splitext(file_name)[1].lower()

        if file_extension == ".csv":
            df = pd.read_csv(uploaded_file)
            return df.to_string()
        
        elif file_extension in [".xlsx", ".xls"]:
            df = pd.read_excel(uploaded_file)
            return df.to_string()
        
        elif file_extension == ".pdf":
            text = ""
            with pdfplumber.open(uploaded_file) as pdf:
                for page in pdf.pages:
                    text += page.extract_text()
            return text
        
        elif file_extension == ".txt":
            # Read as a string
            string_data = uploaded_file.getvalue().decode("utf-8")
            return string_data
        
        else:
            st.error(f"Unsupported file type: {file_extension}")
            return None
            
    except Exception as e:
        st.error(f"Error reading file '{file_name}': {e}")
        return None

# --- HEADER (LOGO ABOVE TITLE) ---
st.image("logo.png", width=60)
st.title("DataSage - Data Analysis Agent")

# --- File Uploader ---
uploaded_file = st.file_uploader(
    "Upload your file to get started",
    type=["csv", "xlsx", "xls", "pdf", "txt"],
    label_visibility="collapsed"
)

# --- Initialize session state ---
if "file_data" not in st.session_state:
    st.session_state.file_data = None
if "file_name" not in st.session_state:
    st.session_state.file_name = None

# If a new file is uploaded, process and store it
if uploaded_file is not None:
    st.session_state.file_data = read_file_content(uploaded_file)
    st.session_state.file_name = uploaded_file.name
    if st.session_state.file_data:
        st.success(f"File '{st.session_state.file_name}' loaded. Ask your question below.")

# --- STACKED CHAT INTERFACE (FIXES THE GAP) ---
is_disabled = st.session_state.file_data is None 

# Create columns for the text input and the send button
input_col, button_col = st.columns([6, 1]) # 6 parts text, 1 part button

with input_col:
    user_prompt = st.text_input(
        "Ask a question about your file...",
        placeholder="Add an attachment above to begin...",
        disabled=is_disabled,
        label_visibility="collapsed" # Hides the label
    )

with button_col:
    # The 'style.css' file now handles the vertical alignment
    send_button = st.button("➤", disabled=is_disabled)

# Logic to run when the 'Send' button is clicked
if send_button:
    if user_prompt:
        with st.spinner("DataSage is thinking..."):
            try:
                # Build the prompt for the AI
                prompt_for_ai = f"""
                Here is the content of a file named '{st.session_state.file_name}':
                
                ---
                {st.session_state.file_data}
                ---
                
                Based *only* on the data above, please answer this question:
                {user_prompt}
                """
                
                # Send to AI and Get Response
                response = model.generate_content(prompt_for_ai)
                
                # Display the Response
                st.subheader("DataSage's Insights:")
                st.write(response.text)
                
            except Exception as e:
                st.error(f"An error occurred: {e}")
    else:
        st.warning("Please enter a question first.")
# --- END OF CHAT INTERFACE UPDATE ---
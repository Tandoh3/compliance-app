import os
import io
import pdfplumber
import spacy
import pandas as pd
import streamlit as st

# Cache the loaded spaCy model to speed up repeated runs
def load_model():
    return spacy.load('en_core_web_sm')

@st.cache_resource
def get_nlp():
    return load_model()

# Step 1: Extract Text from PDF using pdfplumber
@st.cache_data
def extract_text_from_pdf_bytes(pdf_bytes):
    text = ''
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text
    return text

# Step 2: Tokenize text into sentences using spaCy
def tokenize_sentences(text, nlp):
    doc = nlp(text)
    sentences = [sent.text.strip() for sent in doc.sents]
    return sentences

# Step 3: Create DataFrame for compliance checklist
def make_checklist_df(sentences):
    return pd.DataFrame({
        'Compliance Point': sentences,
        'Compliant (Yes/No)': [''] * len(sentences),
        'Comments': [''] * len(sentences)
    })

# Build the Streamlit app
st.set_page_config(page_title='PDF Compliance Checklist Generator', layout='wide')
st.title('📄 Compliance Checklist Generator')
st.markdown(
    'Upload one or more PDF files to extract sentences and generate a compliance checklist in Excel format.'
)

nlp = get_nlp()

uploaded_files = st.file_uploader(
    'Choose PDF files', type=['pdf'], accept_multiple_files=True
)

if uploaded_files:
    st.success(f'{len(uploaded_files)} file(s) uploaded.')
    all_results = []

    for pdf_file in uploaded_files:
        with st.spinner(f'Processing {pdf_file.name}...'):
            pdf_bytes = pdf_file.read()
            text = extract_text_from_pdf_bytes(pdf_bytes)
            sentences = tokenize_sentences(text, nlp)
            df = make_checklist_df(sentences)
            all_results.append((pdf_file.name, df))

    for filename, df in all_results:
        st.subheader(f'Preview: {filename}')
        st.dataframe(df.head(10), use_container_width=True)
        # Convert to Excel in-memory
        towrite = io.BytesIO()
        with pd.ExcelWriter(towrite, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Checklist')
        towrite.seek(0)
        download_name = filename.replace('.pdf', '_compliance_checklist.xlsx')
        st.download_button(
            label=f'Download {download_name}',
            data=towrite,
            file_name=download_name,
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

else:
    st.info('📥 Please upload at least one PDF to get started.')

st.sidebar.markdown('---')
st.sidebar.header('About')
st.sidebar.write(
    'This app extracts text from PDFs, splits into sentences using spaCy, and generates an Excel checklist for manual compliance review.'
)
st.sidebar.write('© 2025 Compliance Checker')

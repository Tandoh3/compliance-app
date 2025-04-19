import io
import pdfplumber
import spacy
import pandas as pd
import streamlit as st

# Initialize spaCy with a blank English model + sentencizer (no external downloads needed)
@st.cache_resource
def get_nlp():
    nlp = spacy.blank("en")
    nlp.add_pipe("sentencizer")
    return nlp

# Extract text from PDF bytes
def extract_text_from_pdf_bytes(pdf_bytes):
    text = ''
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text
    return text

# Tokenize into sentences
def tokenize_sentences(text, nlp):
    doc = nlp(text)
    return [sent.text.strip() for sent in doc.sents]

# Create compliance checklist DataFrame
def make_checklist_df(sentences):
    return pd.DataFrame({
        'Compliance Point': sentences,
        'Compliant (Yes/No)': [''] * len(sentences),
        'Comments': [''] * len(sentences)
    })

# Streamlit UI
st.set_page_config(page_title='PDF Compliance Checklist Generator', layout='wide')
st.title('📄 Compliance Checklist Generator')
st.markdown('Upload PDF files to extract sentences and generate a compliance checklist in Excel format.')

nlp = get_nlp()

uploaded_files = st.file_uploader('Choose PDF files', type=['pdf'], accept_multiple_files=True)

if uploaded_files:
    st.success(f'{len(uploaded_files)} file(s) uploaded.')
    results = []
    for pdf_file in uploaded_files:
        with st.spinner(f'Processing {pdf_file.name}...'):
            pdf_bytes = pdf_file.read()
            text = extract_text_from_pdf_bytes(pdf_bytes)
            sentences = tokenize_sentences(text, nlp)
            df = make_checklist_df(sentences)
            results.append((pdf_file.name, df))

    for filename, df in results:
        st.subheader(f'Preview: {filename}')
        st.dataframe(df.head(10), use_container_width=True)
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

# Sidebar info
st.sidebar.markdown('---')
st.sidebar.header('About')
st.sidebar.write('Extracts text from PDFs, splits into sentences, and generates an Excel checklist for compliance review.')
st.sidebar.write('© 2025 Compliance Checker')

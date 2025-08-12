import streamlit as st
import pandas as pd
import re
import spacy

try:
    nlp = spacy.load("pt_core_news_sm")
except OSError:
    with st.spinner("Downloading Portuguese language model..."):
        from spacy.cli import download
        download("pt_core_news_sm")
    nlp = spacy.load("pt_core_news_sm")

# Path to vocabulary file
VOCAB_FILE = 'palavras.txt'

# --- Data Loading ---
def load_vocabulary(filepath):
    pattern1 = re.compile(r'[A-Z]+')
    pattern2 = re.compile(r'\w+-\w+')
    pattern3 = re.compile(r'\.')

    vocabulary = []
    with open(filepath, 'r', encoding='utf-8') as file:
        for line in file:
            word = line.strip()
            if pattern1.search(word) or pattern2.search(word) or pattern3.search(word):
                continue
            if len(word) >= 4:
                vocabulary.append(word.lower())
    return vocabulary

# --- Token Validation ---
def is_valid_token(word):
    doc = nlp(word)
    if len(doc) == 1:
        token = doc[0]
        return token.is_alpha and not token.is_punct and token.pos_ not in ["PUNCT", "SYM", "NUM", "X"]
    return False

# --- Filter Logic ---
def filter_words(vocabulary, mandatory_letter, complementary_letters):
    filtered = []
    allowed_chars = set(complementary_letters + mandatory_letter)
    for word in vocabulary:
        if mandatory_letter in word and all(char in allowed_chars for char in word):
            filtered.append(word)
    return sorted(filtered, key=lambda x: (len(x), x))

# --- Highlight Mandatory Letter ---
def highlight_letter(word, letter):
    return word.replace(letter, f":red[{letter}]")

# --- Streamlit UI ---
st.set_page_config(page_title="Soletreiro", page_icon="🔤", layout="centered")

st.title("Soletreiro")
st.markdown("Encontre palavras com base na letra obrigatória e letras complementares.")

mandatory = st.text_input("Letra obrigatória (1 letra)", max_chars=1)
complementary = st.text_input("Letras complementares (6 letras)", max_chars=6)

# Slider for filtering by length
length_range = st.slider("Filtrar por tamanho da palavra", 4, 12, (4, 12))

if st.button("Encontrar palavras"):
    if not mandatory or len(mandatory) != 1 or len(complementary) != 6:
        st.error("Insira:\n• Uma letra obrigatória\n• Seis letras complementares")
    else:
        try:
            vocab = load_vocabulary(VOCAB_FILE)
            results = filter_words(vocab, mandatory.lower(), complementary.lower())

            # Remove plurals if singular exists
            singular_words = set(results)
            filtered_results = [
                w for w in results 
                if not (w.endswith("s") and w[:-1] in singular_words)
            ]

            # Apply length filter
            filtered_results = [w for w in filtered_results if length_range[0] <= len(w) <= length_range[1]]

            if filtered_results:
                # Create DataFrame
                df = pd.DataFrame({
                    "Palavra": [highlight_letter(w, mandatory.lower()) for w in filtered_results],
                    "Tamanho": [len(w) for w in filtered_results]
                })

                st.success(f"{len(filtered_results)} palavras encontradas")
                st.dataframe(df, use_container_width=True)

                # Download button
                csv = "\n".join(filtered_results)
                st.download_button(
                    label="Baixar lista",
                    data=csv,
                    file_name="palavras_encontradas.txt",
                    mime="text/plain"
                )
            else:
                st.warning("Nenhuma palavra encontrada.")
        except Exception as e:
            st.error(str(e))

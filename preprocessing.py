# --------------------------------------------------------------
# preprocessing.py
# Automated Quiz Generator - Final Robust Version with TextRank (Sumy)
# --------------------------------------------------------------
# 🧠 Features:
# - Extracts text from PDF using pdfplumber
# - Cleans, tokenizes, and lemmatizes text
# - Uses TextRank (Sumy) to rank sentences by importance
# - Saves cleaned + ranked sentences for question generation
# --------------------------------------------------------------

import pdfplumber
import nltk
import re
from nltk.corpus import stopwords
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.stem import WordNetLemmatizer
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.text_rank import TextRankSummarizer

# --- Download required NLTK data ---
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('wordnet')

# --- Step 1: Extract text from PDF ---
def extract_text_from_pdf(pdf_path):
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            page_text = page.extract_text()
            if page_text:
                # Remove headers/footers or page numbers
                page_text = re.sub(r'Page\s*\d+', '', page_text)
                text += page_text + " "
                print(f"✅ Extracted page {i+1}/{len(pdf.pages)}")
    return text


# --- Step 2: Clean and preprocess text ---
def preprocess_text(raw_text):
    # Clean up unwanted characters
    text = re.sub(r'\n+', ' ', raw_text)
    text = re.sub(r'Page\s*\d+', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    text = re.sub(r'[^a-zA-Z0-9.,!?;:\'\"()\-\s]', '', text)
    text = text.lower()

    # Sentence tokenization
    sentences = sent_tokenize(text)
    sentences = [s.strip() for s in sentences if len(s.split()) > 4]

    # --- Fallback segmentation ---
    if len(sentences) == 0:
        print("⚠ No sentences found using NLTK. Trying fallback segmentation...")
        sentences = re.split(r'[.;:\n]', text)
        sentences = [s.strip() for s in sentences if len(s.strip().split()) > 4]

    # Lemmatization
    lemmatizer = WordNetLemmatizer()
    lemmatized_sentences = []
    for s in sentences:
        words = word_tokenize(s)
        lemmas = [lemmatizer.lemmatize(w) for w in words]
        lemmatized_sentences.append(" ".join(lemmas))

    # --- TextRank summarization using Sumy ---
    print("\n⚙️ Applying TextRank for sentence importance...")
    try:
        parser = PlaintextParser.from_string(text, Tokenizer("english"))
        summarizer = TextRankSummarizer()
        # Select around top 30% of sentences
        total_sent = len(sent_tokenize(text))
        summary_sentences = summarizer(parser.document, sentences_count=max(5, total_sent // 3))

        ranked_sentences = [str(sentence) for sentence in summary_sentences]
        print(f"✅ Selected {len(ranked_sentences)} ranked sentences using TextRank.")
    except Exception as e:
        print(f"⚠ TextRank summarization failed: {e}")
        ranked_sentences = lemmatized_sentences

    # Preview
    print("\n🔍 Example Ranked Sentences:")
    for i, s in enumerate(ranked_sentences[:5], 1):
        print(f"{i}. {s[:150]}...")

    return lemmatized_sentences, ranked_sentences, text


# --- Step 3: Save outputs ---
def save_outputs(sentences, ranked_sentences, text):
    with open("cleaned_sentences.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(sentences))

    with open("ranked_sentences.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(ranked_sentences))

    with open("cleaned_text.txt", "w", encoding="utf-8") as f:
        f.write(text)

    print(f"\n🧩 Saved {len(sentences)} cleaned sentences.")
    print(f"🏆 Saved {len(ranked_sentences)} ranked sentences (TextRank).")
    print("✅ Files: cleaned_sentences.txt, ranked_sentences.txt, cleaned_text.txt")


# --- Step 4: Run full pipeline ---
if __name__ == "__main__":
    pdf_path = "sample.pdf"  # 🔁 Replace with your actual PDF file
    raw_text = extract_text_from_pdf(pdf_path)

    if len(raw_text.strip()) < 10:
        print("⚠ No readable text found. Try OCR extraction for scanned PDFs.")
    else:
        print(f"\n📘 Extracted {len(raw_text)} characters of text from PDF.")
        sentences, ranked_sentences, cleaned_text = preprocess_text(raw_text)
        save_outputs(sentences, ranked_sentences, cleaned_text)
        print("\n✨ Preprocessing + TextRank complete! Ready for question generation.")

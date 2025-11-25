import os
from typing import List

# Local module imports
import preprocessing
import question_generation as qg
import output_quiz as oq
import randomization as rz


def write_generated_questions(questions: List[dict], path: str = "generated_questions.txt") -> None:
    with open(path, "w", encoding="utf-8") as f:
        for q in questions:
            f.write(f"({q['type']}) {q['question']}\n")
            if q.get('type') == "MCQ" and q.get('options'):
                for opt in q['options']:
                    f.write(f"  - {opt}\n")
            f.write(f"Answer: {q['answer']}\n\n")


def main():
    # Inputs
    uploads_dir = "uploads"
    # default pdf path; may be overridden by last_upload recorded by the web app
    pdf_path = os.path.join(uploads_dir, "sample.pdf")
    # read last upload record if present
    last_upload_file = os.path.join(uploads_dir, "last_upload.txt")
    if os.path.exists(last_upload_file):
        try:
            with open(last_upload_file, 'r', encoding='utf-8') as f:
                last = f.read().strip()
                if last and last != 'pasted_text.txt':
                    candidate = os.path.join(uploads_dir, last)
                    if os.path.exists(candidate):
                        pdf_path = candidate
        except Exception:
            pass
    pasted_path = os.path.join(uploads_dir, "pasted_text.txt")
    selected = os.getenv("QUESTION_TYPE", "").strip().lower()
    # INPUT_SOURCE: 'pdf', 'text', or 'auto' (default auto: prefer pdf then text)
    input_source = os.getenv("INPUT_SOURCE", "auto").strip().lower()

    # 1) Preprocessing in-process
    # Prefer uploaded PDF content when present; fall back to pasted text if PDF missing.
    raw_text: str
    # Choose input according to INPUT_SOURCE
    if input_source == "pdf":
        if not os.path.exists(pdf_path):
            raise RuntimeError(f"INPUT_SOURCE=pdf but {pdf_path} not found.")
        print(f"📄 INPUT_SOURCE=pdf -> Extracting text from: {pdf_path}")
        raw_text = preprocessing.extract_text_from_pdf(pdf_path)
    elif input_source == "text":
        if not os.path.exists(pasted_path):
            raise RuntimeError(f"INPUT_SOURCE=text but {pasted_path} not found.")
        with open(pasted_path, "r", encoding="utf-8") as f:
            raw_text = f.read()
        print(f"📝 INPUT_SOURCE=text -> Using pasted text ({len(raw_text)} chars)")
        MAX_CHARS = 20000
        if len(raw_text) > MAX_CHARS:
            print(f"⚡ Input too long ({len(raw_text)}). Trimming to {MAX_CHARS} characters for speed.")
            raw_text = raw_text[:MAX_CHARS]
    else:
        # auto: prefer pdf when present
        if os.path.exists(pdf_path):
            print(f"📄 Found uploaded PDF at: {pdf_path}. Extracting text from PDF...")
            raw_text = preprocessing.extract_text_from_pdf(pdf_path)
        elif os.path.exists(pasted_path):
            with open(pasted_path, "r", encoding="utf-8") as f:
                raw_text = f.read()
            print(f"📝 Using pasted text ({len(raw_text)} chars)")
            MAX_CHARS = 20000
            if len(raw_text) > MAX_CHARS:
                print(f"⚡ Input too long ({len(raw_text)}). Trimming to {MAX_CHARS} characters for speed.")
                raw_text = raw_text[:MAX_CHARS]
        else:
            raise RuntimeError("No input found: neither uploaded PDF nor pasted text exists in 'uploads/'.")
    if len(raw_text.strip()) < 10:
        raise RuntimeError("No readable text found in the uploaded PDF.")
    sentences, ranked_sentences, cleaned_text = preprocessing.preprocess_text(raw_text)
    preprocessing.save_outputs(sentences, ranked_sentences, cleaned_text)

    # 2) Question generation filtered by type
    questions: List[dict] = []
    if selected in ("", "all"):
        questions = (
            qg.generate_mcq(sentences)
            + qg.generate_fill(sentences)
            + qg.generate_true_false(sentences)
            + qg.generate_short_answers(sentences)
        )
    elif selected == "mcq":
        questions = qg.generate_mcq(sentences)
    elif selected in ("fill", "fill_blanks", "fill-in-the-blanks", "fill in the blanks"):
        questions = qg.generate_fill(sentences)
    elif selected in ("tf", "true_false", "true/false", "truefalse", "true or false"):
        questions = qg.generate_true_false(sentences)
    elif selected in ("short", "short_answer", "short answer"):
        questions = qg.generate_short_answers(sentences)
    else:
        questions = (
            qg.generate_mcq(sentences)
            + qg.generate_fill(sentences)
            + qg.generate_true_false(sentences)
            + qg.generate_short_answers(sentences)
        )

    # Persist text representation
    write_generated_questions(questions)

    # 3) Optional randomization (only makes sense when multiple types are present)
    multi_type = any(t in selected for t in ("", "all")) or (
        len({q['type'] for q in questions}) > 1
    )

    source_content: str
    if multi_type:
        mcq, fill, tf, short = rz.load_questions("generated_questions.txt")
        shuffled = rz.randomize_within_types(mcq, fill, tf, short)
        rz.save_randomized(shuffled, "randomized_questions.txt")
        with open("randomized_questions.txt", "r", encoding="utf-8") as f:
            source_content = f.read().strip()
    else:
        with open("generated_questions.txt", "r", encoding="utf-8") as f:
            source_content = f.read().strip()

    # 4) Export PDF directly
    grouped = oq.group_by_type(source_content)
    oq.export_quiz_to_pdf(grouped, filename="Generated_Quiz.pdf")

    # 5) Provide a preview of top 10 generated questions
    try:
        paras = [p.strip() for p in source_content.split('\n\n') if p.strip()]
        preview = '\n\n'.join(paras[:10]) if paras else source_content.strip().split('\n')[:50]
        print('\n=== Top 10 Questions Preview ===\n')
        print(preview)
        with open('generated_questions_preview.txt', 'w', encoding='utf-8') as f:
            f.write(preview)
        print('\n✅ Saved preview to generated_questions_preview.txt')
    except Exception as e:
        print(f'⚠ Could not create preview: {e}')


if __name__ == "__main__":
    main()



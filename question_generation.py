# ---------------------------------------------------------
# question_generation.py - with Short Answers (Final Version)
# ---------------------------------------------------------
import random
import re
from nltk import pos_tag, word_tokenize
import os

def normalize_sentence(s):
    s = re.sub(r'\s+', ' ', s).strip()
    return s

# --- MCQ Generation ---
def generate_mcq(sentences):
    questions = []
    for s in sentences:
        s = normalize_sentence(s)
        words = word_tokenize(s)
        tagged = pos_tag(words)
        nouns = [w for w, t in tagged if t.startswith('NN')]
        if nouns:
            answer = random.choice(nouns)
            q_text = s.replace(answer, "_____")
            options = [
                answer,
                answer + "ing",
                answer + "ed",
                answer[:len(answer)//2] + "ion"
            ]
            random.shuffle(options)
            questions.append({
                "type": "MCQ",
                "question": q_text,
                "options": options,
                "answer": answer
            })
    print(f"🟩 Generated {len(questions)} MCQs.")
    return questions

# --- Fill-in-the-Blank ---
def generate_fill(sentences):
    qs = []
    for s in sentences:
        s = normalize_sentence(s)
        match = re.search(r"\b([A-Za-z]{4,})\b", s)
        if match:
            ans = match.group(1)
            q = s.replace(ans, "_____")
            qs.append({"type": "Fill-in-the-Blank", "question": q, "answer": ans})
    print(f"🟨 Generated {len(qs)} Fill-in-the-Blanks.")
    return qs

# --- True/False ---
def generate_true_false(sentences):
    qs = []
    for s in sentences:
        s = normalize_sentence(s)
        if len(s.split()) > 4:
            qs.append({"type": "True/False", "question": "True or False: " + s,
                       "answer": random.choice(["True", "False"])})
    print(f"🟦 Generated {len(qs)} True/False.")
    return qs

# --- Final Short Answer Generator: Meaningful One-Word Answers ---
def generate_short_answers(sentences):
    short_qs = []
    for s in sentences:
        s = normalize_sentence(s)

        # Skip short/irrelevant or too-long sentences
        if len(s.split()) < 6 or len(s.split()) > 25:
            continue
        if re.match(r"^\d+\.|[A-Za-z]{2,4}\d{2,}", s):
            continue

        # Clean and tag
        s = re.sub(r"^\d+\.\s*", "", s).strip(" .")
        words = word_tokenize(s)
        tagged = pos_tag(words)

        # Extract nouns and verbs
        nouns = [w for w, t in tagged if t.startswith('NN')]
        verbs = [w for w, t in tagged if t.startswith('VB')]

        if not nouns or not verbs:
            continue

        # Choose one key noun as the answer (concept)
        answer = random.choice(nouns)

        # Select a different noun or verb to form the question
        context_word = random.choice(verbs) if verbs else "used"

        # Build meaningful question using templates
        question_templates = [
            f"Which activity is responsible for {context_word} in software engineering?",
            f"Which phase deals with {context_word} during development?",
            f"What ensures {context_word} in software engineering?",
            f"What concept is related to {context_word} in software design?",
            f"Which step focuses on {context_word} within the project?"
        ]
        question = random.choice(question_templates)

        # Avoid duplication (answer shouldn’t appear in question)
        if answer.lower() in question.lower():
            continue

        short_qs.append({
            "type": "Short Answer",
            "question": question,
            "answer": answer
        })

    print(f"🟪 Generated {len(short_qs)} one-word meaningful Short Answer questions.")
    return short_qs



if __name__ == "__main__":
    with open("cleaned_sentences.txt", "r", encoding="utf-8") as f:
        sentences = [line.strip() for line in f if len(line.strip()) > 4]

    print(f"✅ Loaded {len(sentences)} sentences.")

    selected = os.getenv("QUESTION_TYPE", "").strip().lower()

    mcq = fill = tf = short = []
    if selected in ("", "all"):
        mcq = generate_mcq(sentences)
        fill = generate_fill(sentences)
        tf = generate_true_false(sentences)
        short = generate_short_answers(sentences)
        all_qs = mcq + fill + tf + short
    elif selected == "mcq":
        mcq = generate_mcq(sentences)
        all_qs = mcq
    elif selected in ("fill", "fill_blanks", "fill-in-the-blanks", "fill in the blanks"):
        fill = generate_fill(sentences)
        all_qs = fill
    elif selected in ("tf", "true_false", "true/false", "truefalse", "true or false"):
        tf = generate_true_false(sentences)
        all_qs = tf
    elif selected in ("short", "short_answer", "short answer"):
        short = generate_short_answers(sentences)
        all_qs = short
    else:
        # Fallback to all if value unrecognized
        mcq = generate_mcq(sentences)
        fill = generate_fill(sentences)
        tf = generate_true_false(sentences)
        short = generate_short_answers(sentences)
        all_qs = mcq + fill + tf + short

    print(f"\n🧾 Summary: {len(mcq)} MCQ | {len(fill)} Fill | {len(tf)} TF | {len(short)} Short")

    with open("generated_questions.txt", "w", encoding="utf-8") as f:
        counter = 1
        for q in all_qs:
            f.write(f"{counter}) ({q['type']}) {q['question']}\n")
            if q['type'] == "MCQ":
                for opt in q['options']:
                    f.write(f"  - {opt}\n")
            f.write(f"Answer: {q['answer']}\n\n")
            counter += 1

    print("✅ Saved generated_questions.txt successfully.")

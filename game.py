import os
from dotenv import load_dotenv
import streamlit as st
import sqlite3
import random
import datetime
from openai import OpenAI

load_dotenv()

client = OpenAI(api_key=os.getenv("API_KEY"))
from textdistance import levenshtein

db = "flashcards.db"
def init_db():
    conn = sqlite3.connect(db)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT, level INTEGER DEFAULT 1, coins INTEGER DEFAULT 0)''')
    c.execute('''CREATE TABLE IF NOT EXISTS flashcards (
                id INTEGER PRIMARY KEY, user_id INTEGER, question TEXT, answer TEXT, last_review DATE, 
                review_count INTEGER DEFAULT 0, FOREIGN KEY(user_id) REFERENCES users(id))''')
    conn.commit()
    conn.close()

def generate_wrong_options(correct_answer, flashcards):
    wrong_options = [c[2] for c in flashcards if c[2] != correct_answer]
    if len(wrong_options) >= 3:
        return random.sample(wrong_options, 3)
    return wrong_options + ["Generated Fake Option 1", "Generated Fake Option 2", "Generated Fake Option 3"][:3-len(wrong_options)]

def ai_generate_wrong_options(question, correct_answer):
    prompt = f"Generate three plausible incorrect multiple-choice answers for the question: '{question}' with the correct answer: '{correct_answer}'. Don't add A/B/C/D to the options."
    response = client.chat.completions.create(model="gpt-4",
    messages=[{"role": "system", "content": "You are an AI generating incorrect quiz answers."},
              {"role": "user", "content": prompt}])
    return response.choices[0].message.content.split("\n")

def ai_grade_answer(user_answer, correct_answer):
    prompt = f"Grade this response from 0 to 10 based on its correctness compared to the correct answer.\n\nCorrect Answer: {correct_answer}\nUser Answer: {user_answer}\n\nGive only the score as a number."
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "system", "content": "You are an AI that grades quiz answers."},
                  {"role": "user", "content": prompt}]
    )
    return int(response.choices[0].message.content.strip())

# User Registration/Login
def register(username, password):
    conn = sqlite3.connect(db)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        st.success("Registration successful! Please log in.")
    except:
        st.error("Username already exists.")
    conn.close()

def login(username, password):
    conn = sqlite3.connect(db)
    c = conn.cursor()
    c.execute("SELECT id FROM users WHERE username=? AND password=?", (username, password))
    user = c.fetchone()
    conn.close()
    return user[0] if user else None

def add_flashcard(user_id, question, answer):
    conn = sqlite3.connect(db)
    c = conn.cursor()
    c.execute("INSERT INTO flashcards (user_id, question, answer, last_review) VALUES (?, ?, ?, ?)",
              (user_id, question, answer, datetime.date.today()))
    conn.commit()
    conn.close()
    st.success("Flashcard added successfully!")

def get_flashcards(user_id):
    conn = sqlite3.connect(db)
    c = conn.cursor()
    c.execute("SELECT id, question, answer FROM flashcards WHERE user_id=?", (user_id,))
    cards = c.fetchall()
    conn.close()
    return cards

def review_mode(user_id):
    st.subheader("Review Mode")
    flashcards = get_flashcards(user_id)
    if not flashcards:
        st.warning("No flashcards available! Please add some first.")
        return

    if "review_index" not in st.session_state:
        st.session_state["review_index"] = 0
        st.session_state["score"] = 0

    if st.session_state["review_index"] < len(flashcards):
        card = flashcards[st.session_state["review_index"]]
        question, correct_answer = card[1], card[2]

        if "options" not in st.session_state:
            wrong_options = ai_generate_wrong_options(question, correct_answer)
            options = [correct_answer] + wrong_options
            random.shuffle(options)
            st.session_state["options"] = options

        st.write(f"Question: {question}")
        choice = st.radio("Choose the correct answer:", st.session_state["options"], key=f"choice_{st.session_state['review_index']}")

        if st.button("Submit"):
            if choice == correct_answer:
                st.success("Correct!")
                st.session_state["score"] += 1
            else:
                st.error(f"Wrong! The correct answer is: {correct_answer}")

            st.session_state["review_index"] += 1
            st.session_state.pop("options", None)
            st.rerun()
    else:
        st.write(f"Review completed! Your score: {st.session_state['score']}/{len(flashcards)}")
        st.session_state.pop("review_index")
        st.session_state.pop("score")

def ai_generate_hint(question, correct_answer):
    prompt = f"Provide a short hint for the question: '{question}' without revealing the answer."
    response = client.chat.completions.create(model="gpt-4",
    messages=[{"role": "system", "content": "You are an AI that provides helpful hints for quiz questions."},
              {"role": "user", "content": prompt}])
    return response.choices[0].message.content.strip()


def daily_challenge(user_id):
    st.subheader("Daily Challenge Mode")
    flashcards = get_flashcards(user_id)
    if not flashcards:
        st.warning("No flashcards available! Please add some first.")
        return

    if "challenge_index" not in st.session_state:
        st.session_state["challenge_index"] = 0
        st.session_state["score"] = 0
        st.session_state["lives"] = 5  # 初始生命值
        st.session_state["hint_count"] = 3  # 三次提示机会
        st.session_state["correct_streak"] = 0  # 连续正确计数

    if st.session_state["challenge_index"] < len(flashcards) and st.session_state["lives"] > 0:
        card = flashcards[st.session_state["challenge_index"]]
        question, correct_answer = card[1], card[2]

        st.write(f"\U0001F497 Lives: {st.session_state['lives']}")
        st.write(f"\U0001F4A1 Hints left: {st.session_state['hint_count']}")
        st.write(f"Question: {question}")

        user_answer = st.text_input("Type your answer:", key=f"answer_{st.session_state['challenge_index']}")

        if st.button("Get Hint") and st.session_state["hint_count"] > 0:
            hint = ai_generate_hint(question, correct_answer)
            st.session_state["hint_count"] -= 1
            st.info(f"Hint: {hint}")

        if st.button("Submit"):
            score = ai_grade_answer(user_answer, correct_answer)
            st.write(f"Score: {score}/10")
            
            if score < 5:
                st.error(f"Incorrect! The correct answer is: {correct_answer}")
                st.session_state["lives"] -= 1  # 错误减少生命
                st.session_state["correct_streak"] = 0  # 连续正确归零
            else:
                st.success("Correct!")
                st.session_state["score"] += 1
                st.session_state["correct_streak"] += 1
                
                if st.session_state["correct_streak"] == 3:
                    st.session_state["lives"] = min(st.session_state["lives"] + 1, 5)  # 生命恢复但不超过5
                    st.session_state["correct_streak"] = 0  # 重新计数

            st.session_state["challenge_index"] += 1
            st.rerun()
    else:
        st.write(f"Daily Challenge completed! Your score: {st.session_state['score']}/{len(flashcards)}")
        st.session_state.pop("challenge_index")
        st.session_state.pop("score")
        st.session_state.pop("lives")
        st.session_state.pop("hint_count")
        st.session_state.pop("correct_streak")


def main():
    init_db()
    st.title("Rogue-learning Platform")
    menu = ["Login", "Register", "Add Flashcard", "Review Mode", "Daily Challenge"]
    choice = st.sidebar.selectbox("Menu", menu)

    if choice == "Register":
        st.subheader("User Registration")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Register"):
            register(username, password)

    elif choice == "Login":
        st.subheader("User Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            user_id = login(username, password)
            if user_id:
                st.session_state["user_id"] = user_id
                st.success("Login successful!")
            else:
                st.error("Incorrect username or password.")

    elif "user_id" in st.session_state:
        user_id = st.session_state["user_id"]
        if choice == "Add Flashcard":
            st.subheader("Add Flashcard")
            question = st.text_input("Question:")
            answer = st.text_input("Answer:")
            if st.button("Add"):
                add_flashcard(user_id, question, answer)
        elif choice == "Review Mode":
            review_mode(user_id)
        elif choice == "Daily Challenge":
            daily_challenge(user_id)
    else:
        st.warning("Please log in first!")

if __name__ == "__main__":
    main()

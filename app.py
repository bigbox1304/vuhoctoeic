import os
import json
import random
import pandas as pd
from flask import Flask, render_template, request, redirect, url_for
from datetime import datetime

app = Flask(__name__)

DATA_FILE = "selected_words.json"  # File lưu danh sách từ đã chọn
EXCEL_FILE = "data/data.xlsx"  # File Excel chứa dữ liệu

def load_words():
    """ Đọc danh sách từ vựng từ file JSON nếu có, nếu không lấy ngẫu nhiên 10 từ mới """
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            if data.get("date") == datetime.today().strftime("%Y-%m-%d"):
                return data["words"]
        except (json.JSONDecodeError, KeyError):
            pass  # Nếu file lỗi, tạo danh sách mới
    
    df = pd.read_excel(EXCEL_FILE).fillna("")
    selected_words = df.sample(n=10).to_dict(orient="records")

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump({"date": datetime.today().strftime("%Y-%m-%d"), "words": selected_words}, f, ensure_ascii=False, indent=4)

    return selected_words

def generate_quiz(words):
    """ Tạo danh sách câu hỏi từ dữ liệu """
    quiz_data = []
    used_wrong_answers = set()  # Để tránh 2 câu có "Đáp án khác"
    
    for word in words:
        question = word["GOOD"].strip()
        luck = word["LUCK"].strip()
        toeic = word["TOEIC"].strip()

        if luck or toeic:
            correct_answer = f"{toeic} {luck}".strip()
        else:
            correct_answer = "Đáp án khác"

        # Tránh có 2 câu hỏi cùng đáp án "Đáp án khác"
        if correct_answer == "Đáp án khác":
            if "Đáp án khác" in used_wrong_answers:
                continue  # Bỏ qua câu hỏi này nếu đã có "Đáp án khác" trước đó
            used_wrong_answers.add("Đáp án khác")

        # Lấy ngẫu nhiên 3 đáp án sai
        all_answers = [f"{w['TOEIC']} {w['LUCK']}".strip() if w['LUCK'] or w['TOEIC'] else "Đáp án khác" for w in words]
        wrong_answers = list(set(all_answers) - {correct_answer})

        random.shuffle(wrong_answers)
        wrong_answers = wrong_answers[:3]  # Chọn 3 đáp án sai
        
        # Trộn đáp án và đảm bảo vị trí ngẫu nhiên
        options = [correct_answer] + wrong_answers
        random.shuffle(options)

        quiz_data.append({
            "question": question,
            "options": options,
            "correct": correct_answer
        })
    
    return quiz_data
@app.route("/")
def index():
    words = load_words()
    return render_template("index.html", words=words)
@app.route("/reset", methods=["POST"])
def reset_words():
    """ Reset danh sách từ vựng và chọn lại 10 từ mới """
    if os.path.exists(DATA_FILE):
        os.remove(DATA_FILE)  # Xóa file JSON để tạo danh sách mới
    return redirect(url_for("index"))
@app.route("/quiz", methods=["GET", "POST"])
def quiz():
    """ Hiển thị quiz """
    words = load_words()
    quiz_data = generate_quiz(words)
    
    question_index = int(request.args.get("q", 0))
    selected_answer = request.form.get("answer")
    
    if question_index < len(quiz_data):
        question_data = quiz_data[question_index]
        is_correct = (selected_answer == question_data["correct"]) if selected_answer else None
        return render_template("quiz.html", question_data=question_data, selected_answer=selected_answer, is_correct=is_correct, question_index=question_index)
    
    return redirect(url_for("index"))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))  # Lấy PORT từ biến môi trường, mặc định là 5000
    app.run(host='0.0.0.0', port=port, debug=False)

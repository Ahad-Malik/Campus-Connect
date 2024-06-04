import json
import time
from difflib import get_close_matches
from flask import Flask, request, jsonify, render_template
import google.generativeai as genai
from prompts import prompt, jp

genai.configure(api_key='YOUR-GEMINI-API-KEY')

model = genai.GenerativeModel('gemini-pro')



app = Flask(__name__, static_url_path='', static_folder='static', template_folder='templates')

def load_knowledge_base(file_path: str) -> dict:
    with open(file_path, 'r') as file:
        data = json.load(file)
    return data

def save_knowledge_base(file_path: str, data: dict):
    with open(file_path, 'w') as file:
        json.dump(data, file, indent=2)

def find_best_match(user_question: str, questions: list[str]) -> str | None:
    matches = get_close_matches(user_question, questions, n=1, cutoff=0.8)
    return matches[0] if matches else None

def get_answer_for_question(question: str, knowledge_base: dict) -> str | None:
    for q in knowledge_base["questions"]:
        if q["question"] == question:
            return q["answer"]

def make_conversational_with_gemini(prompt: str) -> str:
    response = model.generate_content(prompt)
    return response.text  # Access the generated text correctly

@app.route('/')
def index():
    initial_messages = ["Hey there! How can I help you?"]
    return render_template('index.html' ,initial_messages=initial_messages)

@app.route('/chat', methods=['POST'])
def chat_bot():
    user_input = request.json.get('message')
    knowledge_base = load_knowledge_base('knowledge_base.json')
    chat_history = request.json.get('chat_history', [])

    chat_history.append(f"{user_input}")

    best_match = find_best_match(user_input, [q["question"] for q in knowledge_base["questions"]])

    if best_match:
        answer = get_answer_for_question(best_match, knowledge_base)
        conversational_prompt = "\n".join(chat_history + [f"{prompt} {user_input} {answer}"])
        conversational_answer = make_conversational_with_gemini(conversational_prompt)
        chat_history.append(conversational_answer)
        response_text = conversational_answer
    else:
        prompt_text = "\n".join(chat_history + [f"{jp} {user_input}"])
        response = model.generate_content(prompt_text)
        response_text = response.text  
        chat_history.append(response_text)

    return jsonify({"role": "assistant", "content": response_text, "chat_history": chat_history})

if __name__ == '__main__':
    app.run(debug=True)

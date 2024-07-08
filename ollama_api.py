import os
import json

from langchain_community.llms import Ollama

from flask import Flask, Response, request, render_template
from flask import stream_with_context
from flask_cors import CORS
import logging

app = Flask(__name__)
CORS(app, supports_credentials=True)

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:5000")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "EEVE-Korean-10.8B:latest")

llm = Ollama(model=OLLAMA_MODEL, base_url=OLLAMA_BASE_URL)

def generate_tokens(question):
    for chunks in llm.stream(question):
        yield chunks

@app.route("/")
def hello_name():
    return render_template("ollama_template.html")

@app.route("/users/chat", methods=["POST"])
def ask_ai():
    def generate_json(question):
        # response = llm.invoke(question)
        # logging.info(response)
        # return response

        with app.app_context():  # Ensure we're within the application context
            full_content = ""
            for token in generate_tokens(question):
                full_content += token
                json_data = {
                    "model": OLLAMA_MODEL,
                    "content": token,
                    "done": False
                }
                json_str = json.dumps(json_data)  # Convert JSON data to a string
                json_bytes = json_str.encode('utf-8')  # Encode JSON string to bytes
                yield json_bytes
                yield b'\n'  # Yield newline as bytes

            # Once streaming is finished, yield one last JSON object with "done" set to True
            json_data = {
                "model": OLLAMA_MODEL,
                "full_content": full_content,
                "done": True
            }
            json_str = json.dumps(json_data)  # Convert JSON data to a string
            json_bytes = json_str.encode('utf-8')  # Encode JSON string to bytes
            yield json_bytes
    
    request_data = request.json
    question = request_data.get("question")    
    return Response(stream_with_context(generate_json(question)), status=200, mimetype='application/json')
    # return Response(generate_json(question))
    # return Response(stream_with_context(generate_json(question)))
    


if __name__ == '__main__':
    app.run('0.0.0.0',port=3001,debug=True)
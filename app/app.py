from flask import Flask, render_template

app = Flask(__name__)

# Mock data
notes = [
    {"title": "Task 3"},
    {"title": "Task 2"},
    {"title": "Task 1"}
]

@app.route('/')
def index():
    return render_template('index.html', notes=notes)

if __name__ == '__main__':
    app.run(debug=True)

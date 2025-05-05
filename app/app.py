from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)
notes = [
    {"title": "Task 3", "done": False},
    {"title": "Task 2", "done": False},
    {"title": "Task 1", "done": True}
]


@app.route('/')
def index():
    return render_template('index.html', notes=notes)


@app.route('/done/<int:index>', methods=['POST'])
def mark_done(index):
    if 0 <= index < len(notes):
        notes[index]['done'] = True
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)

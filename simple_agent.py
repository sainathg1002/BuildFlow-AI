import os
import re
from Agent.states import *
from Agent.tools import write_file, file_exists

def create_simple_app(user_prompt: str, project_name: str):
    """Create a simple web app without using LLM API"""
    
    project_folder = f"generated-projects/{project_name}"
    
    # Create directory
    os.makedirs(project_folder, exist_ok=True)
    
    # Determine app type from prompt
    app_type = "generic"
    if "todo" in user_prompt.lower():
        app_type = "todo"
    elif "calculator" in user_prompt.lower():
        app_type = "calculator"
    elif "timer" in user_prompt.lower():
        app_type = "timer"
    
    # Create HTML
    html_content = create_html_template(app_type, project_name)
    write_file.invoke({"path": f"{project_folder}/index.html", "content": html_content})
    
    # Create CSS
    css_content = create_css_template(app_type)
    write_file.invoke({"path": f"{project_folder}/style.css", "content": css_content})
    
    # Create JS
    js_content = create_js_template(app_type)
    write_file.invoke({"path": f"{project_folder}/script.js", "content": js_content})
    
    print(f"Created {app_type} app in {project_folder}")
    return project_folder

def create_html_template(app_type, project_name):
    title = project_name.replace("-", " ").title()
    
    if app_type == "todo":
        return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <div class="container">
        <h1>{title}</h1>
        <div class="input-section">
            <input type="text" id="todo-input" placeholder="Add new todo...">
            <button id="add-btn">Add</button>
        </div>
        <ul id="todo-list"></ul>
        <button id="clear-btn">Clear All</button>
    </div>
    <script src="script.js"></script>
</body>
</html>'''
    
    elif app_type == "calculator":
        return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <div class="calculator">
        <input type="text" id="display" readonly>
        <div class="buttons">
            <button onclick="clearDisplay()">C</button>
            <button onclick="appendToDisplay('/')">/</button>
            <button onclick="appendToDisplay('*')">*</button>
            <button onclick="deleteLast()">←</button>
            <button onclick="appendToDisplay('7')">7</button>
            <button onclick="appendToDisplay('8')">8</button>
            <button onclick="appendToDisplay('9')">9</button>
            <button onclick="appendToDisplay('-')">-</button>
            <button onclick="appendToDisplay('4')">4</button>
            <button onclick="appendToDisplay('5')">5</button>
            <button onclick="appendToDisplay('6')">6</button>
            <button onclick="appendToDisplay('+')">+</button>
            <button onclick="appendToDisplay('1')">1</button>
            <button onclick="appendToDisplay('2')">2</button>
            <button onclick="appendToDisplay('3')">3</button>
            <button onclick="calculate()" rowspan="2">=</button>
            <button onclick="appendToDisplay('0')" colspan="2">0</button>
            <button onclick="appendToDisplay('.')">.</button>
        </div>
    </div>
    <script src="script.js"></script>
</body>
</html>'''
    
    else:  # generic
        return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <div class="container">
        <h1>{title}</h1>
        <p>Welcome to your web application!</p>
        <button id="main-btn">Click Me</button>
    </div>
    <script src="script.js"></script>
</body>
</html>'''

def create_css_template(app_type):
    base_css = '''* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: Arial, sans-serif;
    background: #f5f5f5;
    padding: 20px;
}

.container {
    max-width: 600px;
    margin: 0 auto;
    background: white;
    padding: 30px;
    border-radius: 10px;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
}

h1 {
    text-align: center;
    color: #333;
    margin-bottom: 30px;
}

button {
    background: #007bff;
    color: white;
    border: none;
    padding: 10px 20px;
    border-radius: 5px;
    cursor: pointer;
    font-size: 16px;
}

button:hover {
    background: #0056b3;
}'''

    if app_type == "calculator":
        return base_css + '''
.calculator {
    max-width: 300px;
}

#display {
    width: 100%;
    height: 60px;
    font-size: 24px;
    text-align: right;
    padding: 10px;
    margin-bottom: 10px;
    border: 1px solid #ddd;
    border-radius: 5px;
}

.buttons {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 10px;
}

.buttons button {
    height: 60px;
    font-size: 18px;
}'''
    
    elif app_type == "todo":
        return base_css + '''
.input-section {
    display: flex;
    gap: 10px;
    margin-bottom: 20px;
}

#todo-input {
    flex: 1;
    padding: 10px;
    border: 1px solid #ddd;
    border-radius: 5px;
    font-size: 16px;
}

#todo-list {
    list-style: none;
    margin-bottom: 20px;
}

.todo-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 10px;
    margin-bottom: 5px;
    background: #f8f9fa;
    border-radius: 5px;
}

.todo-item.completed {
    text-decoration: line-through;
    opacity: 0.6;
}

.delete-btn {
    background: #dc3545;
    padding: 5px 10px;
    font-size: 14px;
}'''
    
    return base_css

def create_js_template(app_type):
    if app_type == "todo":
        return '''let todos = [];

function addTodo() {
    const input = document.getElementById('todo-input');
    const text = input.value.trim();
    if (text) {
        todos.push({ id: Date.now(), text, completed: false });
        input.value = '';
        renderTodos();
    }
}

function deleteTodo(id) {
    todos = todos.filter(todo => todo.id !== id);
    renderTodos();
}

function toggleTodo(id) {
    todos = todos.map(todo => 
        todo.id === id ? { ...todo, completed: !todo.completed } : todo
    );
    renderTodos();
}

function renderTodos() {
    const list = document.getElementById('todo-list');
    list.innerHTML = '';
    todos.forEach(todo => {
        const li = document.createElement('li');
        li.className = `todo-item ${todo.completed ? 'completed' : ''}`;
        li.innerHTML = `
            <span onclick="toggleTodo(${todo.id})">${todo.text}</span>
            <button class="delete-btn" onclick="deleteTodo(${todo.id})">Delete</button>
        `;
        list.appendChild(li);
    });
}

function clearAll() {
    todos = [];
    renderTodos();
}

document.getElementById('add-btn').addEventListener('click', addTodo);
document.getElementById('clear-btn').addEventListener('click', clearAll);
document.getElementById('todo-input').addEventListener('keypress', (e) => {
    if (e.key === 'Enter') addTodo();
});'''
    
    elif app_type == "calculator":
        return '''let display = document.getElementById('display');

function appendToDisplay(value) {
    display.value += value;
}

function clearDisplay() {
    display.value = '';
}

function deleteLast() {
    display.value = display.value.slice(0, -1);
}

function calculate() {
    try {
        display.value = eval(display.value);
    } catch (error) {
        display.value = 'Error';
    }
}'''
    
    else:  # generic
        return '''document.addEventListener('DOMContentLoaded', function() {
    const btn = document.getElementById('main-btn');
    btn.addEventListener('click', function() {
        alert('Hello from your web app!');
    });
});'''

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        prompt = sys.argv[1]
        project_name = re.sub(r'[^a-zA-Z0-9\\s]', '', prompt.lower())
        project_name = re.sub(r'\\b(create|simple|web|app|with)\\b', '', project_name)
        project_name = re.sub(r'\\s+', '-', project_name.strip()).strip('-')[:20]
        if not project_name:
            project_name = "webapp"
        create_simple_app(prompt, project_name)
    else:
        create_simple_app("Create simple todo app", "todo-app")
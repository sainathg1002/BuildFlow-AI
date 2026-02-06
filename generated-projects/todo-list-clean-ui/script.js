// Todo List App JavaScript
document.addEventListener('DOMContentLoaded', function() {
    const todoInput = document.getElementById('todo-input');
    const addBtn = document.getElementById('add-btn');
    const todoList = document.getElementById('todo-list');
    const clearBtn = document.getElementById('clear-btn');

    let todos = [];

    // Add new todo
    function addTodo() {
        const text = todoInput.value.trim();
        if (text) {
            const todo = {
                id: Date.now(),
                text: text,
                completed: false
            };
            todos.push(todo);
            todoInput.value = '';
            renderTodos();
        }
    }

    // Toggle todo completion
    function toggleTodo(id) {
        todos = todos.map(todo => 
            todo.id === id ? { ...todo, completed: !todo.completed } : todo
        );
        renderTodos();
    }

    // Delete todo
    function deleteTodo(id) {
        todos = todos.filter(todo => todo.id !== id);
        renderTodos();
    }

    // Render todos
    function renderTodos() {
        todoList.innerHTML = '';
        todos.forEach(todo => {
            const li = document.createElement('li');
            li.className = `todo-item ${todo.completed ? 'completed' : ''}`;
            li.innerHTML = `
                <span class="todo-text">${todo.text}</span>
                <div class="todo-actions">
                    <button onclick="toggleTodo(${todo.id})" class="toggle-btn">
                        ${todo.completed ? '↶' : '✓'}
                    </button>
                    <button onclick="deleteTodo(${todo.id})" class="delete-btn">×</button>
                </div>
            `;
            todoList.appendChild(li);
        });
    }

    // Clear all todos
    function clearAll() {
        todos = [];
        renderTodos();
    }

    // Event listeners
    addBtn.addEventListener('click', addTodo);
    clearBtn.addEventListener('click', clearAll);
    todoInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            addTodo();
        }
    });

    // Make functions global for onclick handlers
    window.toggleTodo = toggleTodo;
    window.deleteTodo = deleteTodo;
});
// script.js
// Todo list web app with clean UI

// Get the todo list element
const todoList = document.getElementById('todo-list')

// Function to add todo item
function addTodoItem() {
  const todoInput = document.getElementById('todo-input')
  const todoItemText = todoInput.value.trim()
  if (todoItemText !== '') {
    const todoItem = document.createElement('li')
    todoItem.textContent = todoItemText
    todoList.appendChild(todoItem)
    todoInput.value = ''
  }
}

// Function to delete todo item
function deleteTodoItem() {
  const todoItems = document.querySelectorAll('#todo-list li')
  for (let i = todoItems.length - 1; i >= 0; i--) {
    if (todoItems[i].querySelector('input[type="checkbox"]').checked) {
      todoItems[i].remove()
    }
  }
}

// Add event listener for adding todo item
document.getElementById('add-todo-btn').addEventListener('click', addTodoItem)

// Add event listener for deleting todo item
document.addEventListener('keydown', (e) => {
  if (e.key === 'Delete' && document.activeElement === document.body) {
    deleteTodoItem()
  }
})

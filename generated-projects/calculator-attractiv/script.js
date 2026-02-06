// script.js
// Calculator functionality with attractive UI support
// Handles basic arithmetic, decimal numbers, clear, backspace, and keyboard input.

// Wait for DOM content to load before attaching listeners
document.addEventListener('DOMContentLoaded', () => {
  const display = document.getElementById('display');
  const buttons = document.querySelectorAll('.btn');

  // Store current expression as a string
  let expression = '';

  // Update the calculator screen
  const updateDisplay = () => {
    display.value = expression || '0';
  };

  // Evaluate the expression safely using Function constructor
  const calculateResult = () => {
    try {
      // Replace any accidental multiple operators (e.g., ++, --) before eval
      const sanitized = expression
        .replace(/\+\+/g, '+')
        .replace(/\-\-/g, '+')
        .replace(/\*\*/g, '*')
        .replace(/\/\//g, '/');
      // eslint-disable-next-line no-new-func
      const result = Function(`'use strict'; return (${sanitized})`)();
      expression = Number.isFinite(result) ? result.toString() : 'Error';
    } catch (e) {
      expression = 'Error';
    }
    updateDisplay();
  };

  // Clear the whole expression
  const clearAll = () => {
    expression = '';
    updateDisplay();
  };

  // Remove last character (backspace)
  const backspace = () => {
    expression = expression.slice(0, -1);
    updateDisplay();
  };

  // Append a character to the expression respecting some simple rules
  const append = (char) => {
    const lastChar = expression.slice(-1);
    const operators = ['+', '-', '*', '/'];
    // Prevent two operators in a row (except for a leading minus)
    if (operators.includes(char)) {
      if (expression === '' && char !== '-') {
        return; // can't start with +, *, /
      }
      if (operators.includes(lastChar)) {
        // replace the previous operator with the new one
        expression = expression.slice(0, -1) + char;
        updateDisplay();
        return;
      }
    }
    // Prevent multiple decimals in a single number segment
    if (char === '.') {
      const parts = expression.split(/[+\-*/]/);
      const current = parts[parts.length - 1];
      if (current.includes('.')) return; // already a decimal point
    }
    expression += char;
    updateDisplay();
  };

  // Button click handling
  buttons.forEach((btn) => {
    btn.addEventListener('click', () => {
      const action = btn.dataset.action;
      const value = btn.dataset.value;

      switch (action) {
        case 'clear':
          clearAll();
          break;
        case 'backspace':
          backspace();
          break;
        case 'equals':
          calculateResult();
          break;
        case 'input':
          append(value);
          break;
        default:
          break;
      }
    });
  });

  // Keyboard support – map keys to calculator actions
  document.addEventListener('keydown', (e) => {
    const key = e.key;
    if ((key >= '0' && key <= '9') || ['+', '-', '*', '/', '.'].includes(key)) {
      e.preventDefault();
      append(key);
    } else if (key === 'Enter' || key === '=') {
      e.preventDefault();
      calculateResult();
    } else if (key === 'Backspace') {
      e.preventDefault();
      backspace();
    } else if (key === 'Escape') {
      e.preventDefault();
      clearAll();
    }
  });

  // Initialize display
  updateDisplay();
});

// script.js – Simple Calculator functionality
// This script adds event handling for the calculator UI defined in index.html.
// It supports basic arithmetic operations (+, -, *, /), decimal numbers, clear, and evaluation.

document.addEventListener('DOMContentLoaded', () => {
    const display = document.getElementById('display');
    const buttons = document.querySelectorAll('.btn');

    // Helper to append a character/value to the display
    const appendToDisplay = (value) => {
        // Prevent multiple leading zeros (e.g., "00") unless after a decimal point
        if (display.value === '0' && value !== '.' && !isOperator(value)) {
            display.value = value;
        } else {
            display.value += value;
        }
    };

    // Determine if a character is an operator
    const isOperator = (char) => ['+', '-', '*', '/'].includes(char);

    // Clear the display
    const clearDisplay = () => {
        display.value = '';
    };

    // Evaluate the expression safely
    const evaluateExpression = () => {
        const expression = display.value;
        if (!expression) return;
        // Allow only numbers, decimal points and the four operators
        if (!/^[0-9+\-*/.]+$/.test(expression)) {
            display.value = 'Error';
            return;
        }
        try {
            // Using Function constructor is slightly safer than eval because it creates a new scope
            // eslint-disable-next-line no-new-func
            const result = Function(`"use strict"; return (${expression});`)();
            display.value = Number.isFinite(result) ? result : 'Error';
        } catch (e) {
            display.value = 'Error';
        }
    };

    // Main click handler for all buttons
    buttons.forEach((btn) => {
        btn.addEventListener('click', () => {
            const id = btn.id;
            const dataValue = btn.getAttribute('data-value');

            if (id === 'clear') {
                clearDisplay();
            } else if (id === 'equals') {
                evaluateExpression();
            } else if (dataValue !== null) {
                // For numbers, decimal point and operators
                appendToDisplay(dataValue);
            }
        });
    });
});

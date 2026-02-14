// script.js – Simple Stop Watch functionality
// This script provides start, stop, and reset capabilities for the stopwatch UI defined in index.html.
// It ensures proper button state handling and updates the display every second.

document.addEventListener('DOMContentLoaded', () => {
  // Grab DOM elements
  const display = document.getElementById('display');
  const startBtn = document.getElementById('startBtn');
  const stopBtn = document.getElementById('stopBtn');
  const resetBtn = document.getElementById('resetBtn');

  // Stopwatch state variables
  let startTime = 0;      // Timestamp when the timer was (re)started
  let elapsedTime = 0;    // Milliseconds accumulated while running
  let timerId = null;     // ID returned by setInterval

  /** Helper: Pad a number to two digits */
  const pad = (num) => String(num).padStart(2, '0');

  /** Convert milliseconds to HH:MM:SS string */
  const formatTime = (ms) => {
    const totalSeconds = Math.floor(ms / 1000);
    const hours = Math.floor(totalSeconds / 3600);
    const minutes = Math.floor((totalSeconds % 3600) / 60);
    const seconds = totalSeconds % 60;
    return `${pad(hours)}:${pad(minutes)}:${pad(seconds)}`;
  };

  /** Update the displayed time */
  const updateDisplay = () => {
    const now = Date.now();
    const diff = now - startTime + elapsedTime; // total elapsed while running
    display.textContent = formatTime(diff);
  };

  /** Start the stopwatch */
  const startTimer = () => {
    if (timerId !== null) return; // already running
    // Record the moment we (re)start, factoring in any previously elapsed time
    startTime = Date.now();
    // Begin interval updates (once per second – can be finer if desired)
    timerId = setInterval(updateDisplay, 1000);
    // Immediate update so UI doesn't wait a full second
    updateDisplay();

    // Button state handling
    startBtn.disabled = true;
    stopBtn.disabled = false;
    resetBtn.disabled = false;
  };

  /** Stop/pause the stopwatch */
  const stopTimer = () => {
    if (timerId === null) return; // not running
    clearInterval(timerId);
    timerId = null;
    // Accumulate elapsed time up to the moment of stopping
    elapsedTime += Date.now() - startTime;
    // Button state handling
    startBtn.disabled = false;
    stopBtn.disabled = true;
    // Reset remains enabled so the user can clear the current value
    resetBtn.disabled = false;
  };

  /** Reset the stopwatch to 00:00:00 */
  const resetTimer = () => {
    // Stop any running interval
    if (timerId !== null) {
      clearInterval(timerId);
      timerId = null;
    }
    // Clear state
    startTime = 0;
    elapsedTime = 0;
    // Update UI
    display.textContent = '00:00:00';
    // Button state handling
    startBtn.disabled = false;
    stopBtn.disabled = true;
    resetBtn.disabled = true;
  };

  // Attach event listeners
  startBtn.addEventListener('click', startTimer);
  stopBtn.addEventListener('click', stopTimer);
  resetBtn.addEventListener('click', resetTimer);

  // Initialise UI to a clean state (in case the page is cached)
  resetTimer();
});

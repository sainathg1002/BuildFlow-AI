// script.js – Bright Stop‑Watch
// -------------------------------------------------
// Implements a simple stopwatch with start, stop and reset
// functionality. The UI is defined in index.html and styled
// in style.css. This script wires up the controls, formats the
// elapsed time and updates the display every 10 ms (centisecond).

(() => {
  // Grab UI elements
  const displayEl = document.getElementById('display');
  const startBtn = document.getElementById('startBtn');
  const stopBtn = document.getElementById('stopBtn');
  const resetBtn = document.getElementById('resetBtn');

  // Internal state
  let startTime = 0; // timestamp when the current run started
  let elapsed = 0;   // total elapsed time in ms (including paused periods)
  let timerId = null; // reference to the interval timer

  /**
   * Formats a millisecond value into a string "MM:SS:CC"
   * where MM = minutes, SS = seconds, CC = centiseconds.
   */
  const formatTime = (ms) => {
    const totalCentiseconds = Math.floor(ms / 10);
    const centiseconds = totalCentiseconds % 100;
    const totalSeconds = Math.floor(totalCentiseconds / 100);
    const seconds = totalSeconds % 60;
    const minutes = Math.floor(totalSeconds / 60);
    const pad = (n, digits = 2) => String(n).padStart(digits, '0');
    return `${pad(minutes)}:${pad(seconds)}:${pad(centiseconds)}`;
  };

  /**
   * Updates the display element with the current elapsed time.
   */
  const render = () => {
    displayEl.textContent = formatTime(elapsed);
  };

  /**
   * Starts the stopwatch.
   */
  const start = () => {
    if (timerId !== null) return; // already running
    startTime = Date.now() - elapsed; // continue from previous elapsed
    timerId = setInterval(() => {
      elapsed = Date.now() - startTime;
      render();
    }, 10);
    // UI state
    startBtn.disabled = true;
    stopBtn.disabled = false;
    resetBtn.disabled = false;
  };

  /**
   * Stops/pauses the stopwatch.
   */
  const stop = () => {
    if (timerId === null) return; // not running
    clearInterval(timerId);
    timerId = null;
    // elapsed already reflects the time up to the moment of stop
    // UI state
    startBtn.disabled = false;
    stopBtn.disabled = true;
    resetBtn.disabled = false;
  };

  /**
   * Resets the stopwatch to 0.
   */
  const reset = () => {
    // Ensure timer is stopped
    if (timerId !== null) {
      clearInterval(timerId);
      timerId = null;
    }
    elapsed = 0;
    render();
    // UI state – ready to start again
    startBtn.disabled = false;
    stopBtn.disabled = true;
    resetBtn.disabled = true;
  };

  // Attach event listeners
  startBtn.addEventListener('click', start);
  stopBtn.addEventListener('click', stop);
  resetBtn.addEventListener('click', reset);

  // Initial render (in case the page is cached)
  render();
})();

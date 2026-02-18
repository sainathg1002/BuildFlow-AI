<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Responsive Analog Clock</title>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
:root {
  --primary-color: #2563eb;
  --bg-color: #f8fafc;
  --hand-color: #1e40af;
  --clock-bg: #ffffff;
  --shadow: rgba(0, 0, 0, 0.1);
  --text-color: #111827;
}

.dark {
  --bg-color: #1e293b;
  --clock-bg: #334155;
  --hand-color: #93c5fd;
  --shadow: rgba(0, 0, 0, 0.4);
  --text-color: #f1f5f9;
}

* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

body {
  font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, "Noto Sans", sans-serif;
  background: var(--bg-color);
  color: var(--text-color);
  min-height: 100vh;
  display: grid;
  place-items: center;
  transition: background 0.3s, color 0.3s;
}

.app {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1.5rem;
}

.clock {
  position: relative;
  width: 20rem;
  height: 20rem;
  background: var(--clock-bg);
  border-radius: 12px;
  box-shadow: 0 8px 20px var(--shadow);
  display: grid;
  place-items: center;
  transition: background 0.3s, box-shadow 0.3s;
}

.hand {
  position: absolute;
  width: 50%;
  height: 0.4rem;
  background: var(--hand-color);
  border-radius: 6px;
  top: 50%;
  transform-origin: 100% 50%;
  transition: transform 0.5s cubic-bezier(0.4, 2.3, 0.3, 1);
}

.hand.hour {
  width: 35%;
  height: 0.6rem;
  background: var(--primary-color);
}

.hand.minute {
  width: 45%;
  height: 0.5rem;
  background: var(--primary-color);
}

.hand.second {
  width: 48%;
  height: 0.2rem;
  background: #ef4444;
}

.center {
  position: absolute;
  width: 1rem;
  height: 1rem;
  background: var(--primary-color);
  border-radius: 50%;
  z-index: 10;
}

.theme-toggle {
  padding: 0.6rem 1.2rem;
  background: var(--primary-color);
  color: #fff;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 1rem;
  box-shadow: 0 4px 12px var(--shadow);
  transition: background 0.3s, transform 0.2s;
}

.theme-toggle:hover {
  background: #1d4ed8;
  transform: translateY(-2px);
}
</style>
</head>
<body>
<div class="app">
  <div class="clock" aria-label="Analog Clock">
    <div class="hand hour" data-hand="hour"></div>
    <div class="hand minute" data-hand="minute"></div>
    <div class="hand second" data-hand="second"></div>
    <div class="center"></div>
  </div>
  <button class="theme-toggle">Toggle Theme</button>
</div>

<script>
(function() {
  const hourHand = document.querySelector('.hand.hour');
  const minuteHand = document.querySelector('.hand.minute');
  const secondHand = document.querySelector('.hand.second');
  const toggleBtn = document.querySelector('.theme-toggle');

  function setRotation(element, angle) {
    element.style.transform = `rotate(${angle}deg)`;
  }

  function updateClock() {
    const now = new Date();
    const seconds = now.getSeconds();
    const minutes = now.getMinutes();
    const hours = now.getHours() % 12;

    const secondAngle = seconds * 6; // 360/60
    const minuteAngle = minutes * 6 + seconds * 0.1; // 360/60 + smooth
    const hourAngle = hours * 30 + minutes * 0.5; // 360/12 + smooth

    setRotation(secondHand, secondAngle);
    setRotation(minuteHand, minuteAngle);
    setRotation(hourHand, hourAngle);
  }

  // Initial call
  updateClock();
  // Update every second
  setInterval(updateClock, 1000);

  // Theme toggle
  toggleBtn.addEventListener('click', () => {
    document.documentElement.classList.toggle('dark');
  });
})();
</script>
</body>
</html>
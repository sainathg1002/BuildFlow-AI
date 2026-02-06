class Stopwatch {
    constructor() {
        this.display = document.getElementById('display');
        this.startPauseBtn = document.getElementById('startPauseBtn');
        this.lapBtn = document.getElementById('lapBtn');
        this.resetBtn = document.getElementById('resetBtn');
        this.lapsList = document.getElementById('lapsList');

        this.startTime = 0;
        this.elapsedTime = 0;
        this.timerInterval = null;
        this.isRunning = false;
        this.laps = [];

        this.bindEvents();
        this.updateDisplay();
    }

    bindEvents() {
        this.startPauseBtn.addEventListener('click', () => this.startPause());
        this.lapBtn.addEventListener('click', () => this.recordLap());
        this.resetBtn.addEventListener('click', () => this.reset());

        document.addEventListener('keydown', (e) => {
            if (e.code === 'Space') {
                e.preventDefault();
                this.startPause();
            } else if (e.key.toLowerCase() === 'l') {
                e.preventDefault();
                this.recordLap();
            } else if (e.key.toLowerCase() === 'r') {
                e.preventDefault();
                this.reset();
            }
        });
    }

    startPause() {
        if (this.isRunning) {
            this.pause();
        } else {
            this.start();
        }
    }

    start() {
        if (!this.isRunning) {
            this.startTime = Date.now() - this.elapsedTime;
            this.timerInterval = setInterval(() => this.updateDisplay(), 10);
            this.isRunning = true;
            this.startPauseBtn.innerHTML = '<span class="btn-text">PAUSE</span>';
            this.lapBtn.disabled = false;
            this.resetBtn.disabled = false;
        }
    }

    pause() {
        if (this.isRunning) {
            clearInterval(this.timerInterval);
            this.elapsedTime = Date.now() - this.startTime;
            this.isRunning = false;
            this.startPauseBtn.innerHTML = '<span class="btn-text">RESUME</span>';
        }
    }

    reset() {
        clearInterval(this.timerInterval);
        this.startTime = 0;
        this.elapsedTime = 0;
        this.isRunning = false;
        this.laps = [];
        this.updateDisplay();
        this.startPauseBtn.innerHTML = '<span class="btn-text">START</span>';
        this.lapBtn.disabled = true;
        this.resetBtn.disabled = true;
        this.updateLapsList();
    }

    recordLap() {
        if (this.isRunning) {
            const lapTime = this.elapsedTime;
            this.laps.push(lapTime);
            this.updateLapsList();
        }
    }

    updateDisplay() {
        if (this.isRunning) {
            this.elapsedTime = Date.now() - this.startTime;
        }
        const time = this.formatTime(this.elapsedTime);
        this.display.textContent = time;
    }

    formatTime(milliseconds) {
        const totalSeconds = Math.floor(milliseconds / 1000);
        const hours = Math.floor(totalSeconds / 3600);
        const minutes = Math.floor((totalSeconds % 3600) / 60);
        const seconds = totalSeconds % 60;
        const ms = Math.floor((milliseconds % 1000) / 10);

        return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}.${ms.toString().padStart(2, '0')}`;
    }

    updateLapsList() {
        this.lapsList.innerHTML = '';
        this.laps.forEach((lap, index) => {
            const li = document.createElement('li');
            li.textContent = `Lap ${index + 1}: ${this.formatTime(lap)}`;
            this.lapsList.appendChild(li);
        });
    }
}

// Initialize the stopwatch when the page loads
document.addEventListener('DOMContentLoaded', () => {
    new Stopwatch();
});

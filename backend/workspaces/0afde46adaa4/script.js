// script.js – 2026 Calendar Web App
(() => {
    // ---------- State ----------
    const state = {
        view: 'month', // year | month | week | day
        date: new Date(), // reference date for current view
        events: [], // loaded from localStorage
        theme: 'light',
        searchQuery: '',
        editingEventId: null,
    };

    // ---------- Constants ----------
    const STORAGE_KEYS = {
        events: 'calendarEvents',
        theme: 'calendarTheme',
    };
    const HOLIDAYS = [
        { date: '2026-01-01', name: "New Year's Day" },
        { date: '2026-02-14', name: 'Valentine’s Day' },
        { date: '2026-04-21', name: 'Easter Sunday' },
        { date: '2026-05-01', name: 'International Workers’ Day' },
        { date: '2026-07-04', name: 'Independence Day (US)' },
        { date: '2026-10-31', name: 'Halloween' },
        { date: '2026-12-25', name: 'Christmas Day' },
        // add more as needed
    ];

    // ---------- Utility Functions ----------
    const fmt = (date) => date.toISOString().split('T')[0]; // YYYY-MM-DD

    const loadFromStorage = (key, fallback) => {
        const raw = localStorage.getItem(key);
        try {
            return raw ? JSON.parse(raw) : fallback;
        } catch {
            return fallback;
        }
    };

    const saveToStorage = (key, data) => {
        localStorage.setItem(key, JSON.stringify(data));
    };

    const getEventsForDate = (dateStr) => {
        return state.events.filter(ev => ev.date === dateStr && matchesSearch(ev));
    };

    const matchesSearch = (event) => {
        if (!state.searchQuery) return true;
        const q = state.searchQuery.toLowerCase();
        return (event.title && event.title.toLowerCase().includes(q)) ||
               (event.description && event.description.toLowerCase().includes(q));
    };

    const isHoliday = (dateStr) => HOLIDAYS.some(h => h.date === dateStr);

    const getHolidayName = (dateStr) => {
        const h = HOLIDAYS.find(h => h.date === dateStr);
        return h ? h.name : '';
    };

    const getMonthName = (monthIdx) => new Date(0, monthIdx).toLocaleString(undefined, { month: 'short' });

    const getWeekStart = (date) => {
        const d = new Date(date);
        const day = d.getDay(); // 0 Sun .. 6 Sat
        const diff = (day + 6) % 7; // make Monday =0
        d.setDate(d.getDate() - diff);
        d.setHours(0,0,0,0);
        return d;
    };

    const addDays = (date, n) => {
        const d = new Date(date);
        d.setDate(d.getDate() + n);
        return d;
    };

    // ---------- Theme ----------
    const applyTheme = (theme) => {
        document.documentElement.dataset.theme = theme;
        state.theme = theme;
        saveToStorage(STORAGE_KEYS.theme, theme);
    };

    const toggleTheme = () => {
        const newTheme = state.theme === 'light' ? 'dark' : 'light';
        applyTheme(newTheme);
    };

    // ---------- Rendering ----------
    const calendarEl = document.getElementById('calendar');

    const clearCalendar = () => {
        calendarEl.innerHTML = '';
    };

    const render = () => {
        clearCalendar();
        switch (state.view) {
            case 'year':
                renderYearView();
                break;
            case 'month':
                renderMonthView();
                break;
            case 'week':
                renderWeekView();
                break;
            case 'day':
                renderDayView();
                break;
        }
    };

    // ---- Year View ----
    const renderYearView = () => {
        calendarEl.className = 'calendar year-view';
        const year = state.date.getFullYear();
        for (let m = 0; m < 12; m++) {
            const cell = document.createElement('div');
            cell.className = 'day-cell';
            cell.dataset.month = m;
            const monthName = getMonthName(m);
            const label = document.createElement('div');
            label.className = 'date-label';
            label.textContent = monthName;
            cell.appendChild(label);

            // count events in month
            const monthEvents = state.events.filter(ev => {
                const evDate = new Date(ev.date);
                return evDate.getFullYear() === year && evDate.getMonth() === m && matchesSearch(ev);
            });
            if (monthEvents.length) {
                const cnt = document.createElement('div');
                cnt.style.marginTop = '0.3rem';
                cnt.style.fontSize = '0.85rem';
                cnt.style.color = 'var(--text-secondary)';
                cnt.textContent = `${monthEvents.length} event${monthEvents.length > 1 ? 's' : ''}`;
                cell.appendChild(cnt);
            }

            cell.addEventListener('click', () => {
                state.view = 'month';
                state.date = new Date(year, m, 1);
                render();
            });

            calendarEl.appendChild(cell);
        }
    };

    // ---- Month View ----
    const renderMonthView = () => {
        calendarEl.className = 'calendar month-view';
        const year = state.date.getFullYear();
        const month = state.date.getMonth();

        // First day of month
        const first = new Date(year, month, 1);
        const startDay = (first.getDay() + 6) % 7; // Monday=0

        // Days from previous month to fill first week
        const daysInPrevMonth = new Date(year, month, 0).getDate();
        for (let i = startDay - 1; i >= 0; i--) {
            const d = daysInPrevMonth - i;
            const dateObj = new Date(year, month - 1, d);
            const cell = createDayCell(dateObj, true);
            calendarEl.appendChild(cell);
        }

        // Current month days
        const daysInMonth = new Date(year, month + 1, 0).getDate();
        for (let d = 1; d <= daysInMonth; d++) {
            const dateObj = new Date(year, month, d);
            const cell = createDayCell(dateObj, false);
            calendarEl.appendChild(cell);
        }

        // Fill trailing cells to complete rows (optional)
        const totalCells = calendarEl.children.length;
        const remainder = totalCells % 7;
        if (remainder !== 0) {
            const needed = 7 - remainder;
            for (let i = 1; i <= needed; i++) {
                const dateObj = new Date(year, month + 1, i);
                const cell = createDayCell(dateObj, true);
                calendarEl.appendChild(cell);
            }
        }
    };

    // ---- Week View ----
    const renderWeekView = () => {
        calendarEl.className = 'calendar week-view';
        const start = getWeekStart(state.date);
        for (let i = 0; i < 7; i++) {
            const dateObj = addDays(start, i);
            const cell = createDayCell(dateObj, false);
            calendarEl.appendChild(cell);
        }
    };

    // ---- Day View ----
    const renderDayView = () => {
        calendarEl.className = 'calendar day-view';
        const cell = createDayCell(state.date, false, true);
        calendarEl.appendChild(cell);
    };

    // ---- Day Cell Factory ----
    const createDayCell = (dateObj, isOtherMonth = false, forceFullHeight = false) => {
        const dateStr = fmt(dateObj);
        const cell = document.createElement('div');
        cell.className = 'day-cell';
        if (isOtherMonth) cell.style.opacity = '0.5';
        if (isHoliday(dateStr)) cell.classList.add('holiday');

        const label = document.createElement('div');
        label.className = 'date-label';
        label.textContent = `${dateObj.getDate()} ${getMonthName(dateObj.getMonth())}`;
        if (isHoliday(dateStr)) {
            label.title = getHolidayName(dateStr);
        }
        cell.appendChild(label);

        // Events
        const events = getEventsForDate(dateStr);
        events.forEach(ev => {
            const evEl = document.createElement('div');
            evEl.className = 'event-item';
            evEl.textContent = ev.time ? `${ev.time} ${ev.title}` : ev.title;
            evEl.title = ev.description || '';
            evEl.dataset.eventId = ev.id;
            evEl.addEventListener('click', (e) => {
                e.stopPropagation();
                openModal(dateStr, ev.id);
            });
            cell.appendChild(evEl);
        });

        // Click on empty area to add new event
        cell.addEventListener('click', () => {
            openModal(dateStr);
        });

        // Ensure min-height for day view
        if (forceFullHeight) cell.style.minHeight = '300px';

        return cell;
    };

    // ---------- Modal ----------
    const modal = document.getElementById('event-modal');
    const form = document.getElementById('event-form');
    const titleInput = document.getElementById('event-title');
    const dateInput = document.getElementById('event-date');
    const timeInput = document.getElementById('event-time');
    const descInput = document.getElementById('event-description');
    const deleteBtn = document.getElementById('delete-event');
    const cancelBtn = document.getElementById('cancel-event');

    const openModal = (dateStr = fmt(state.date), eventId = null) => {
        state.editingEventId = eventId;
        if (eventId) {
            const ev = state.events.find(e => e.id === eventId);
            if (ev) {
                titleInput.value = ev.title;
                dateInput.value = ev.date;
                timeInput.value = ev.time || '';
                descInput.value = ev.description || '';
                deleteBtn.classList.remove('hidden');
            }
        } else {
            // new event
            form.reset();
            titleInput.value = '';
            dateInput.value = dateStr;
            deleteBtn.classList.add('hidden');
        }
        modal.showModal();
    };

    const closeModal = () => {
        modal.close();
        state.editingEventId = null;
    };

    // ---------- Form Handlers ----------
    form.addEventListener('submit', (e) => {
        e.preventDefault();
        const newEvent = {
            id: state.editingEventId || Date.now(),
            title: titleInput.value.trim(),
            date: dateInput.value,
            time: timeInput.value,
            description: descInput.value.trim(),
        };
        if (state.editingEventId) {
            // update
            const idx = state.events.findIndex(ev => ev.id === state.editingEventId);
            if (idx > -1) state.events[idx] = newEvent;
        } else {
            // add
            state.events.push(newEvent);
        }
        saveToStorage(STORAGE_KEYS.events, state.events);
        closeModal();
        render();
    });

    cancelBtn.addEventListener('click', (e) => {
        e.preventDefault();
        closeModal();
    });

    deleteBtn.addEventListener('click', (e) => {
        e.preventDefault();
        if (state.editingEventId) {
            state.events = state.events.filter(ev => ev.id !== state.editingEventId);
            saveToStorage(STORAGE_KEYS.events, state.events);
        }
        closeModal();
        render();
    });

    // ---------- Navigation ----------
    const prevBtn = document.getElementById('prev-btn');
    const nextBtn = document.getElementById('next-btn');
    const viewButtons = document.querySelectorAll('.view-btn');

    const shiftPeriod = (direction) => {
        const mul = direction === 'prev' ? -1 : 1;
        switch (state.view) {
            case 'year':
                state.date.setFullYear(state.date.getFullYear() + mul);
                break;
            case 'month':
                state.date.setMonth(state.date.getMonth() + mul);
                break;
            case 'week':
                state.date = addDays(state.date, mul * 7);
                break;
            case 'day':
                state.date = addDays(state.date, mul);
                break;
        }
        render();
    };

    prevBtn.addEventListener('click', () => shiftPeriod('prev'));
    nextBtn.addEventListener('click', () => shiftPeriod('next'));

    viewButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const newView = btn.dataset.view;
            if (newView && newView !== state.view) {
                state.view = newView;
                // reset date to today for new view
                state.date = new Date();
                render();
                // highlight active button
                viewButtons.forEach(b => b.classList.toggle('active', b === btn));
            }
        });
    });

    // ---------- Search ----------
    const searchInput = document.getElementById('search-input');
    searchInput.addEventListener('input', () => {
        state.searchQuery = searchInput.value.trim();
        render();
    });

    // ---------- Theme ----------
    const themeToggleBtn = document.getElementById('theme-toggle');
    themeToggleBtn.addEventListener('click', toggleTheme);

    // ---------- Init ----------
    const init = () => {
        // Load persisted data
        state.events = loadFromStorage(STORAGE_KEYS.events, []);
        const savedTheme = loadFromStorage(STORAGE_KEYS.theme, 'light');
        applyTheme(savedTheme);

        // Initial render
        render();

        // Set active view button
        viewButtons.forEach(b => b.classList.toggle('active', b.dataset.view === state.view));
    };

    // Run init after DOM ready (defer script ensures this)
    init();
})();
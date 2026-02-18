(function () {
  const input = document.getElementById('itemInput');
  const addBtn = document.getElementById('addBtn');
  const list = document.getElementById('list');

  if (!input || !addBtn || !list) return;

  const KEY = 'buildflow_fallback_items';
  const items = JSON.parse(localStorage.getItem(KEY) || '[]');

  function render() {
    list.innerHTML = '';
    items.forEach((text, idx) => {
      const li = document.createElement('li');
      const span = document.createElement('span');
      span.textContent = text;

      const del = document.createElement('button');
      del.textContent = 'Delete';
      del.style.marginLeft = '8px';
      del.addEventListener('click', () => {
        items.splice(idx, 1);
        localStorage.setItem(KEY, JSON.stringify(items));
        render();
      });

      li.appendChild(span);
      li.appendChild(del);
      list.appendChild(li);
    });
  }

  addBtn.addEventListener('click', () => {
    const value = input.value.trim();
    if (!value) return;
    items.push(value);
    input.value = '';
    localStorage.setItem(KEY, JSON.stringify(items));
    render();
  });

  render();
})();
function showTable(obj) {
    const tbody = document.querySelector('#scr-table tbody');
    tbody.innerHTML = '';
    for (const key in obj) {
        if (obj.hasOwnProperty(key)) {
            const tr = document.createElement('tr');
            const tdKey = document.createElement('td');
            const tdVal = document.createElement('td');
            tdKey.textContent = key;
            tdVal.textContent = obj[key];
            tr.appendChild(tdKey);
            tr.appendChild(tdVal);
            tbody.appendChild(tr);
        }
    }
}
showTable(scr);
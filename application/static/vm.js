function showTable(obj, obj2) {
    const vmTbody = document.querySelector('#vm-table tbody');
    vmTbody.innerHTML = '';
    for (const key in obj) {
        if (obj.hasOwnProperty(key)) {
            const tr = document.createElement('tr');
            const tdKey = document.createElement('td');
            const tdVal = document.createElement('td');
            tdKey.textContent = key;
            tdVal.textContent = obj[key];
            tr.appendChild(tdKey);
            tr.appendChild(tdVal);
            vmTbody.appendChild(tr);
        }
    }

    const procTbody = document.querySelector('#proc-table tbody');
    procTbody.innerHTML = '';
    for (const key in obj2) {
        if (obj2.hasOwnProperty(key)) {
            const tr = document.createElement('tr');
            const tdKey = document.createElement('td');
            const tdVal = document.createElement('td');
            tdKey.textContent = key;
            tdVal.textContent = obj2[key];
            tr.appendChild(tdKey);
            tr.appendChild(tdVal);
            procTbody.appendChild(tr);
        }
    }
}


function deleteRow(ip, name) {
    if (!confirm(`Delete process "${name}" on VM ${ip}?`)) return;
    fetch('/delete_proc', {
        method: 'DELETE',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ip: ip, name: name})
    })
    .then(resp => resp.json())
    .then(result => {
        if (result.ok) location.reload();
        else alert(result.error || "Server error: " + result.status);
    })
    .catch(e => alert("Network or JSON error: " + e));
}

function add_proc_to_monitoring(ip) {
    if (document.getElementById('add-proc-form')) {
        return;
    }
    const tbody = document.querySelector('#proc-table tbody');
    const tr = document.createElement('tr');
    tr.id = 'add-proc-form';
    tr.innerHTML = `
        <td colspan="7">
        <form onsubmit="send_proc_to_monitoring(event, this, '${ip}')">
            name <input type="text" name="name" placeholder="Name" required>
            version <input type="text" name="version" placeholder="version">
            monitoring_period <input type="text" name="monitoring_period" placeholder="monitoring_period" value="0">
            logs_path <input type="text" name="logs_path" placeholder="logs_path">
            <button type="submit">Save</button>
        </form>
        </td>
    `;
    tbody.appendChild(tr);
}

function send_proc_to_monitoring(event, form,ip) {
event.preventDefault();
    const data = {
        ip: ip,
        name: form.name.value,
        version: form.version.value,
        monitoring_period: form.monitoring_period.value,
        logs_path: form.logs_path.value,

    };
    fetch('/add_proc_monitoring', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(data),
    })
  .then(resp => resp.json()
    .then(json => ({ ok: resp.ok, status: resp.status, ...json }))
)
.then(result => {
    if (result.ok) {
        location.reload();
    } else {
        alert(result.error || `Error: ${result.status}`);
    }
})
.catch(e => {
    alert("Network or JSON error: " + e);
});
}

function showLogs(obj) {
    const tbody = document.querySelector('#log-table tbody');
    tbody.innerHTML = '';
    for (const key in obj) {
        if (obj.hasOwnProperty(key)) {
            const tr = document.createElement('tr');
            const tdKey = document.createElement('td');
            tdKey.textContent = key;
            tr.appendChild(tdKey);

            for (const elem of obj[key]) {
                const tdVal = document.createElement('td');
                tdVal.textContent = elem;
                tr.appendChild(tdVal);
            }
            tbody.appendChild(tr);
        }
    }
}

function showMonitoring(obj) {
    const tbody = document.querySelector('#proc-data-table tbody');
    tbody.innerHTML = '';


    const headerTr = document.createElement('tr');
    ['Process', 'Datetime', 'CPU', 'RAM', 'ERR'].forEach(text => {
        const th = document.createElement('th');
        th.textContent = text;
        headerTr.appendChild(th);
    });
    tbody.appendChild(headerTr);

    for (const procName in obj) {
        if (!obj.hasOwnProperty(procName)) continue;
        const dataArr = obj[procName];

        if (dataArr.length === 0) {
            const tr = document.createElement('tr');
            tr.appendChild(tdWithText(procName));
            tr.appendChild(tdWithText('nodata'));
            tr.appendChild(tdWithText('nodata'));
            tr.appendChild(tdWithText('nodata'));
            tr.appendChild(tdWithText('nodata'));
            tbody.appendChild(tr);
        } else {
            for (const elem of dataArr) {
                const tr = document.createElement('tr');
                tr.appendChild(tdWithText(procName));
                tr.appendChild(tdWithText(elem.datetime ?? ''));
                tr.appendChild(tdWithText(elem.cpu ?? ''));
                tr.appendChild(tdWithText(elem.ram ?? ''));
                tr.appendChild(tdWithText(elem.err ?? ''));
                tbody.appendChild(tr);
            }
        }
    }

    function tdWithText(text) {
        const td = document.createElement('td');
        td.textContent = text;
        return td;
    }
}

window.onload = () => showTable(vmlist,proclist);

function logs_vm_open(ip) {
    const data = { ip: vmlist['ip'] };
    fetch('/logs_vm_open', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(data),
    })
  .then(resp => resp.json()
    .then(json => ({ ok: resp.ok, status: resp.status, ...json }))
)
.then(result => {
    if (result.ok) {
        location.reload();
    } else {
        alert(result.error || `Error: ${result.status}`);
    }
})
.catch(e => {
    alert("Network or JSON error: " + e);
});
}

function monitoring_vm(ip) {
    fetch(`/monitoring_vm?ip=${ip}`)
        .then(resp => resp.json()
            .then(json => ({ ok: resp.ok, status: resp.status, ...json }))
        )
        .then(result => {
            if (result.ok || result.success) {
                showMonitoring(result.result);
            } else {
                alert(result.error || `Error: ${result.status}`);
            }
        })
        .catch(e => {
            alert("Network or JSON error: " + e);
        });
}

function addRow() {
    let ul = document.getElementById('vm-list');
    let li = document.createElement('li');
    li.innerHTML = `
        <form onsubmit="return saveRow(event, this)">
        <table>
        <tr>
           <td><input type="text" name="ip" placeholder="Enter valid IP" required
             pattern="([0-9]{1,3}[\\.]){3}[0-9]{1,3}"
             title="Enter valid IPv4 "></td>
           <td><input type="text" name="name" placeholder="Name" required></td>
            <td>
                <select name="status">
                    <option value="new">new_m</option>
                    <option value="in_progress">in_progress</option>
                    <option value="done">paudsed</option>
                </select>
            </td>
            <td>
               <td><input type="text" name="monitoring" placeholder="monitoring" value=0 ></td>
            </td>
            <td>
                <select name="category">
                    <option value="a">category A</option>
                    <option value="b">category B</option>
                    <option value="c">category C</option>
                </select>
            </td>
            <td><input type="text" name="ssh_user" placeholder="ssh_user" required></td>
            <td><input type="text" name="ssh_password" placeholder="ssh_password" required></td>
            <td><input type="text" name="ssh_port" placeholder="ssh_port" value=22></td>
            <td><button type="submit">Save</button></td>
        </tr>
        </table>
        </form>
    `;
    ul.appendChild(li);
}
function editRow(proc, ip) {
    const old = document.getElementById('edit-proc-form');
    if (old) old.remove();
    const tbody = document.querySelector('#proc-table tbody');
    const tr = document.createElement('tr');
    tr.id = 'edit-proc-form';
    tr.innerHTML = `
        <td colspan="7">
        <form onsubmit="return updateRow(event, this)">
            name <input type="text" name="name" required value="${proc.name || ''}">
            version <input type="text" name="version" value="${proc.version || ''}">
            monitoring_period <input type="text" name="monitoring_period" value="${proc.monitoring_period || ''}">
            logs_path <input type="text" name="logs_path" value="${proc.logs_path || ''}">
            <input type="hidden" name="ip" value="${ip}">
            <button type="submit">Save</button>
        </form>
        </td>
    `;
    tbody.insertBefore(tr, tbody.firstChild);
}

function updateRow(event, form) {
    event.preventDefault();
    const data = {
        ip: form.ip.value,
        name: form.name.value,
        version: form.version.value,
        monitoring_period: form.monitoring_period.value,
        logs_path: form.logs_path.value,
    };
    fetch('/update_proc', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(data),
    })
    .then(resp => resp.json()
        .then(json => ({ ok: resp.ok, status: resp.status, ...json }))
    )
    .then(result => {
        if (result.ok) {
            location.reload();
        } else {
            alert(result.error || `Error: ${result.status}`);
        }
    })
    .catch(e => {
        alert("Network or JSON error: " + e);
    });
}

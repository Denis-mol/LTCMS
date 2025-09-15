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

function editRow(ip) {

    let ul = document.getElementById('vm-list');
    let li = document.createElement('li');
    li.innerHTML = `
        <form onsubmit="return updateRow(event, this)">
        <table>
        <tr>
           <td><input type="text" name="ip" placeholder="Enter valid IP" required value=${ip}
             pattern="([0-9]{1,3}[\\.]){3}[0-9]{1,3}"
             title="Enter valid IPv4 "></td>
           <td><input type="text" name="name" placeholder="Name" required></td>
            <td>
                <select name="status">
                    <option value="new">new_m</option>
                    <option value="in_progress">in_progress</option>
                    <option value="paused">paused</option>
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
function  updateRow(event, form){
    event.preventDefault();
    const data = {
        ip: form.ip.value,
        name: form.name.value,
        status: form.status.value,
        monitoring: form.monitoring.value,
        category: form.category.value,
        ssh_user: form.ssh_user.value,
        ssh_password: form.ssh_password.value,
        ssh_port: form.ssh_port.value,
    };
    fetch('/update_vm', {
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

function saveRow(event, form) {
    event.preventDefault();
    const data = {
        ip: form.ip.value,
        name: form.name.value,
        status: form.status.value,
        monitoring: form.monitoring.value,
        category: form.category.value,
        ssh_user: form.ssh_user.value,
        ssh_password: form.ssh_password.value,
        ssh_port: form.ssh_port.value,
    };
fetch('/save_vm', {
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

function gotoRow(ip) {
    window.location = `/vm?ip=${ip}`;
}

function deleteRow(ip) {
    if (!confirm('DELETE STAND?')) return;
    fetch(`/delete/${encodeURIComponent(ip)}`, {
        method: 'DELETE'
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
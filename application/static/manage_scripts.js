function addRow() {
    let ul = document.getElementById('scripts-list');
    let li = document.createElement('li');
    li.innerHTML = `
        <form onsubmit="return saveRow(event, this)">
        <table>
        <tr>
           <td><input type="text" name="ip" placeholder="Enter IP" required
             pattern="([0-9]{1,3}[\\.]){3}[0-9]{1,3}"
             title="Ener valid IPv4 "></td>
           <td><input type="text" name="name" placeholder="Enter Name" required></td>
           <td><input type="text" name="om_dir" placeholder="Enter directory " required></td>
            <td>
                <select name="status">
                    <option value="new">new_</option>
                    <option value="in_progress">in_progress</option>
                    <option value="done">done</option>
                </select>
            </td>
            <td>
                <select name="category">
                    <option value="a">category A</option>
                    <option value="b">category B</option>
                    <option value="c">category C</option>
                </select>
            </td>
            <td>
                <button type="submit">Save</button>
            </td>
        </tr>
        </table>
        </form>
    `;
    ul.appendChild(li);
}

function saveRow(event, form) {
    event.preventDefault();
    const data = {
        ip: form.ip.value,
        name: form.name.value,
        om_dir: form.om_dir.value,
        status: form.status.value,
        category: form.category.value,
    };
    fetch('/save_vm', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(data),
    })
    .then(resp => {
        if (resp.ok) {
            location.reload();
        } else {
           .then(resp => {
    alert("saving error");

        }
    });
    return false;
}

function gotoSCR(name) {
    window.location = `/gotoscr?name=${name}`;
}

function deleteRow(name) {
    if (!confirm('Delete srcypt?')) return;
    fetch(`/delete/${encodeURIComponent(name)}`, {
        method: 'DELETE'
    })
    .then(resp => {
        if (resp.ok) {
            location.reload();
        } else {
            alert('Deleting srcypt error');
        }
    });
}
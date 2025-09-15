function addUser() {
    let ul = document.getElementById('users_list');
    let li = document.createElement('li');
    li.innerHTML = `
        <form onsubmit="return saveRow(event, this)">
        <table>
        <tr>
           <td><input type="text" name="name" placeholder="Name" required></td>
            <td>
                <select name="status">
                    <option value="Active">Active</option>
                    <option value="Blocked">Blocked</option>
                    <option value="Visitor">Visitor</option>
                </select>
            </td>
             <td><input type="text" name="password" placeholder="password" required></td>
            <td>
               <td><input type="text" name="permissions" placeholder="permissions" value=0 ></td>
            </td>
             <td>
                <select name="range">
                    <option value="Administrator">Administrator</option>
                    <option value="QA">QA</option>
                    <option value="User">User</option>
                </select>
            </td>
            <td><button type="submit">Save</button></td>
        </tr>
        </table>
        </form>
    `;
    ul.appendChild(li);
}

function editRow(name) {
    let ul = document.getElementById('users_list');
    let li = document.createElement('li');
    li.innerHTML = `
        <form onsubmit="return updateRow(event, this)">
        <table>
        <tr>
           <td>
           <input type="text" name="name" placeholder="Name" value=${name}
           </td>
            <td>
                <select name="status">
                    <option value="Active">Active</option>
                    <option value="Blocked">Blocked</option>
                    <option value="Visitor">Visitor</option>
                </select>
            </td>
             <td><input type="text" name="password" placeholder="password" required></td>
             <td><input type="text" name="permissions" placeholder="permissions" value=0 ></td>
             <td>
                <select name="range">
                    <option value="Administrator">Administrator</option>
                    <option value="QA">QA</option>
                    <option value="User">User</option>
                </select>
            </td>
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
        name: form.name.value,
        status: form.status.value,
        password: form.password.value,
        permissions: form.permissions.value,
        range: form.range.value,
    };
    fetch('/update_user', {
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
        name: form.name.value,
        status: form.status.value,
        password: form.password.value,
        permissions: form.permissions.value,
        range: form.range.value,
    };
    fetch('/save_user', {
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


function deleteRow(name) {
    if (!confirm('DELETE USER?')) return;
    fetch(`/delete_user/${name}`, {
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
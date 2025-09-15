function stands_open() {
    fetch('/manage_vm', {
        method: 'GET',
        headers: {'Content-Type': 'application/json'}
    })
    .then(html => {
 window.location = '/manage_vm';
    });
}
function users_open() {
    fetch('/manage_users', {
        method: 'GET',
        headers: {'Content-Type': 'application/json'}
    })
    .then(html => {
 window.location = '/manage_users';
    });
}



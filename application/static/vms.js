function manage_open() {
    fetch('/manage_vm', {
        method: 'GET',
        headers: {'Content-Type': 'application/json'}
    })
    .then(() => {
 window.location = `/manage_vm`;
    });
}
function mass_updates_open() {
    fetch('/manage_updates', {
        method: 'GET',
        headers: {'Content-Type': 'application/json'}
    })
    .then(html => {
 window.location = `/updates`;
    });
}
function mass_logs_open(){
 fetch('/manage_logs', {
        method: 'GET',
        headers: {'Content-Type': 'application/json'}
    })
    .then(html => {
 window.location = `/logs`;
    });
}
function manage_scripts_open(){
 fetch('/manage_scripts', {
        method: 'GET',
        headers: {'Content-Type': 'application/json'}
    })
    .then(html => {
 window.location = `/manage_scripts`;
    });

}
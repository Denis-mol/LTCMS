function sendChecked() {
    const checked = Array.from(document.querySelectorAll('input[name="vm_select"]:checked'))
        .map(el => el.value);
    const data = {ip: checked};
    fetch('/getlogsOfVMsByIps', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(data),
    })
   .then(response => response.json())
   .then(result => {
        function format(obj, indent = '') {
            if (Array.isArray(obj)) {
                return '[' + obj.map(e => format(e)).join(', ') + ']';
            }
            if (typeof obj === 'object' && obj !== null) {
                return Object.entries(obj)
                    .map(([k, v]) => indent + k + ': ' + format(v, indent + '  '))
                    .join('\n');
            }
            return String(obj);
        }
        alert("Update results:\n" + format(result));
    });
}
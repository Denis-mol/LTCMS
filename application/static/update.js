function getCheckedVMs() {
    const checked = Array.from(document.querySelectorAll('input[name="vm_select"]:checked'))
        .map(el => el.value);
    const ver = document.getElementById('torview_ver').value;
    const is_orel_repo = document.getElementById('is_orel_repo').checked;

    const data = {
        ip: checked,
        ver: ver,
        is_orel_repo: is_orel_repo
    };

    fetch('/updatetv', {
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
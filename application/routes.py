import time

from quart import Quart, render_template, request, jsonify, Response
from quart_auth import basic_auth_required

from helpers import (load_stands, save_vm_, delete_vm_by_ip, update_vm, dbs_init,
                     load_last_monitoring, load_users, add_user,
                     delete_user_by_name, current_status_messages, update_user, add_proc_to_processes,
                     get_proc_from_processes, update_process, delete_process)

app = Quart(__name__)
current_status = "redy"
app.secret_key = '123'
app.config["admin"] = "admin"
app.config["adminpass"] = "adminpass"
app.config["user"] = "user"
app.config["pass"] = "pass"


@app.before_serving
async def startup():
    """Initializes all databases at server start."""
    global current_status
    current_status = current_status_messages['dbs_init']
    await dbs_init()


@app.route('/stream')
def stream_status():
    def event_stream():
        """Server-Sent Events (SSE) endpoint that streams the application's current status text to the client in real time."""
        prev = "ready"
        while True:
            if prev != current_status:
                yield f"data: {current_status}\n\n"
                prev = current_status
            time.sleep(1)

    return Response(event_stream(), content_type='text/event-stream')


@app.route("/", methods=["GET"])
async def open_index():
    """Renders the front page HTML and updates the global status."""
    global current_status
    current_status = current_status_messages['open_index']
    return await render_template('index.html')


@app.route("/manage_users", methods=["GET"])
async def open_manage_users():
    """Renders the users management page.
Loads user list from the database.
If the user list cannot be retrieved, displays an error page."""
    global current_status
    current_status = current_status_messages['open_manage_users']
    users_list = await load_users()
    if not users_list["success"]:
        return await render_template('error.html', error=users_list["error"])
    return await render_template('manage_users.html', users_list=users_list['result'])


@app.route("/save_user", methods=["POST"])
@basic_auth_required(username_key="admin", password_key="adminpass")
async def save_user():
    """Adds a new user from the received JSON payload (auth required)"""
    entry = await request.get_json()
    global current_status
    current_status = f"{current_status_messages["saving_user"]} {entry["name"]}"
    result = await add_user(entry)
    if result["success"]:
        return jsonify(result), 200
    return jsonify(result), 300


@app.route('/update_user', methods=['POST'])
@basic_auth_required(username_key="user", password_key="pass")
async def update_user_():
    """Updates a user record (auth required)."""
    global current_status
    entry = await request.get_json()
    current_status = f"{current_status_messages["updating_user"]} {entry["name"]}"
    result = await update_user(entry)
    if result["success"]:
        return jsonify(result), 200
    return jsonify(result), 300


@app.route('/delete_user/<name>', methods=['DELETE'])
@basic_auth_required(username_key="admin", password_key="adminpass")
async def delete_user(name):
    """Deletes a user by name"""
    global current_status
    current_status = f"{current_status_messages["deleting_user"]} {name}"
    result = await delete_user_by_name(name)
    if result["success"]:
        return jsonify(result), 200
    return jsonify(result), 300


@app.route('/manage_vm', methods=['GET'])
async def open_manage_vm():
    "Renders the VM management page."
    global current_status
    current_status = current_status_messages["open_manage_vm"]
    vm_list = await load_stands()
    if not vm_list["success"]:
        return await render_template('error.html', error=vm_list["error"])
    return await render_template('manage_vm.html', vmlist=vm_list['result'])


@app.route('/save_vm', methods=['POST'])
@basic_auth_required(username_key="user", password_key="pass")
async def save_vm():
    "Adds a new VM (auth required)"
    global current_status
    current_status = current_status_messages["saving_vm"]
    entry = await request.get_json()
    result = await save_vm_(entry)
    if result["success"]:
        return jsonify({'success': True}), 200
    else:
        return jsonify(result), 300


@app.route('/update_vm', methods=['POST'])
@basic_auth_required(username_key="user", password_key="pass")
async def update_vm_handler():
    """Updates a VM entry (auth required)"""
    global current_status
    current_status = current_status_messages["updating_vm"]
    entry = await request.get_json()
    if await update_vm(entry):
        return jsonify({'success': True}), 200
    return jsonify({'success': False}), 300


@app.route('/delete/<ip>', methods=['DELETE'])
async def delete_vm(ip):
    """Deletes a VM by IP address"""
    global current_status
    current_status = f"{current_status_messages['deleting_vm']} {ip}"
    result = await delete_vm_by_ip(ip)
    if result['success']:
        return jsonify({'success': True}), 200
    return jsonify({'success': False}), 300


@app.route('/vm', methods=['GET'])
async def open_vm():
    """Renders a page showing a single VM and its monitored processes"""
    ip = request.args.get('ip')
    global current_status
    current_status = f"{current_status_messages['loading _vm']} {ip}"
    vm_list = await load_stands()
    if not vm_list["success"]:
        return await render_template('error.html', error=vm_list["error"])
    vmlist = vm_list['result']
    vm = next((obj for obj in vmlist if obj['ip'] == ip), None)
    proclist = await get_proc_from_processes(ip)
    if not proclist["success"]:
        return await render_template('error.html', error=proclist["error"])
    proclist = [obj for obj in proclist['result']]
    return await render_template('vm.html', vm=vm, proclist=proclist)


@app.route('/update_proc', methods=['POST'])
async def update_proc():
    """Updates a monitored process with new parameters"""
    global current_status
    current_status = current_status_messages["updating_proc"]
    entry = await request.get_json()
    if await update_process(entry):
        return jsonify({'success': True}), 200
    return jsonify({'success': False}), 300


@app.route('/delete_proc', methods=['DELETE'])
async def delete_proc():
    """Deletes a specific process from monitoring"""
    entry = await request.get_json()
    global current_status
    current_status = f"{current_status_messages['deleting_proc']} {entry}"
    result = await delete_process(entry)
    if result['success']:
        return jsonify({'success': True}), 200
    return jsonify({'success': False}), 300


@app.route('/monitoring_vm', methods=['GET'])
async def monitoring_vm():
    """Returns current monitoring/history data for a VM in JSON"""
    ip = request.args.get('ip')
    global current_status
    current_status = f"loading {ip} monitoring_vm"
    result = await load_last_monitoring(ip)
    if result["success"]:
        return jsonify(result)
    return jsonify({'success': False}), 300


@app.route('/add_proc_monitoring', methods=['POST'])
async def add_proc_monitoring():
    """Adds a new process to be monitored on a VM"""
    global current_status
    current_status = "add_proc_monitoring"
    entry = await request.get_json()
    result = await add_proc_to_processes(entry)
    if result["success"]:
        return jsonify({'success': True}), 200
    elif not result["success"]:
        return jsonify({'success': False, "error": "duplicate item"}), 300
    return jsonify({'success': False}), 300


@app.route('/get_processes_from_monitoring', methods=['GET'])
async def get_processes_from_monitoring():
    """Returns the list of configured monitored processes for a specified VM"""
    ip = request.args.get('ip')
    print("get_processes_from_monitoring", ip)
    global current_status
    current_status = f"loading {ip} processes_from_monitoring"
    result = await get_proc_from_processes(ip)
    print(str(result))
    if result:
        print(jsonify(result))
        return jsonify(result)
    return jsonify({'success': False}), 300



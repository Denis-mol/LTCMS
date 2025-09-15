import asyncio
import datetime
import json
import logging
import os
import os.path
import functools
import aiosqlite
import asyncssh
from run import config

# Key Features
# Polling of remote processes over SSH
# Per-VM, per-day tabular storage of monitoring data
# Retrieval of historical monitoring records
# Dynamic discovery of VMs, SSH credentials, and processes to monitor
# Utilities for managing and querying monitoring databases

curdir = os.path.dirname(os.path.abspath(__file__))
VMS_FILE = os.path.join(curdir, "vms.json")
SCR_FILE = 'scr.json'
SCRIPTS_FILE = '../scripts'

logging.basicConfig(format='[%(asctime)s ] %(message)s',
                    datefmt="%m/%d/%Y %I:%M:%S %p", level=logging.DEBUG, filename="application.log", filemode="w")

DICT_FILE = f"{curdir}\\dictionary.json"


# curdir: The current script directory (absolute path).
# VMS_FILE: Path to vms.json.
# SCR_FILE: Path to scr.json.
# SCRIPTS_FILE: Path to ../scripts (relative path).
# DATABASE_VMS, DATABASE_USERS, DATABASE_MONITORING: SQLite database filenames, built from config.
# MONITORING_PATH: Directory to hold per-VM monitoring databases.
# DICT_FILE: Path to dictionary.json with various application messages.


def read_json_file(json_file_path):
    """Synchronously reads a JSON file and parses it as a Python object."""
    try:
        with open(json_file_path, "r") as f:
            logging.info("read_file %s success", json_file_path)
            return json.load(f)
    except Exception as e:
        logging.error("Error %s read_json_file %s", e, json_file_path)
        return {"success": False, "error": read_json_file.__name__ + str(e)}


def get_dictionary():
    logging.info("read dictionary success")
    return read_json_file(DICT_FILE)


dictionary = get_dictionary()
current_status_messages = dictionary["current_status_messages"]
sql = dictionary["sql"]
error_messages = dictionary["error_messages"]
commands = dictionary["commands"]
path = dictionary["path"]
DATABASE_VMS = f"{curdir}{path['DATABASE_VMS']}"
DATABASE_USERS = f"{curdir}{path['DATABASE_USERS']}"
DATABASE_MONITORING = f"{curdir}{path['DATABASE_MONITORING']}"
MONITORING_PATH = f"{curdir}{path['MONITORING_PATH']}"


async def read_file(path):
    """Asynchronously reads a file into a string."""
    try:
        with open(path, "r") as f:
            logging.info("read_file %s success", path)
            return f.read()
    except Exception as e:
        logging.error("Error %s read_file %s", e, path)
        return {"success": False, "error": read_file.__name__ + str(e)}


def async_db_error_handler(func):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        """Decorator for uniform exception handling in async database functions.
        Returns a dictionary with "success": False and error description on failure."""
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            return {"success": False, "error": f'{func.__name__}: {str(e)}'}

    return wrapper


#Database Initialization
def make_dir(path):
    """Ensures the directory at path exists, creates it if missing."""
    if not os.path.isdir(path):
        try:
            os.mkdir(path)
            path_exist = os.path.isdir(path)
            if path_exist:
                logging.info("%s sucsessfully created", path)
                return {"success": True}
            logging.info("%s not opening", path)
            return {"success": False, "error": "{} not opening".format(path)}
        except Exception as e:
            logging.error("Error %s making dir %s", e, path)
            return {"success": False, "error": make_dir.__name__ + str(e)}
    return {"success": True}


@async_db_error_handler
async def db_init(db_path, db_schema):
    """Initializes an SQLite database at db_path with an optional schema (db_schema)."""
    async with aiosqlite.connect(db_path) as db:
        if db_schema:
            await db.executescript(sql_script=db_schema)
            await db.commit()
            logging.info("%s db created", db_path)
        else:
            logging.info("%s db created (empty schema)", db_path)
        return {'success': True}


@async_db_error_handler
async def init_db_with_schema(db_path, schema_path):
    """Reads a schema file and initializes the corresponding database."""
    schema = await read_file(f"{curdir}{schema_path}")
    result = await db_init(db_path, schema)
    return result


@async_db_error_handler
async def dbs_init():
    """Initializes all required databases and directory, running all schemas from the config."""
    make_dir_result = make_dir(MONITORING_PATH)
    if not make_dir_result.get("success", False):
        return make_dir_result

    db_schema_list = [
        (DATABASE_USERS, config['DATABASE_USERS_SCHEMA']),
        (DATABASE_VMS, config['DATABASE_VMS_SCHEMA']),
        (DATABASE_VMS, config['SCRIPTS_SCHEMA']),
        (DATABASE_VMS, config['PROCESSES_SCHEMA']),
        (DATABASE_MONITORING, config['REESTR_SCHEMA'])
    ]

    for db_path, schema_path in db_schema_list:
        result = await init_db_with_schema(db_path, schema_path)
        if not result.get("success", False):
            logging.error(f"Init error {db_path} schema_path {schema_path}: {result.get('error', '')}")
            return result
    return {'success': True}


#User Management
@async_db_error_handler
async def load_users():
    """Loads and returns a list of all users in the system."""
    async with aiosqlite.connect(DATABASE_USERS) as db:
        cursor = await db.execute(sql["load_users"])
        users_list = await cursor.fetchall()
        return {"success": True, "result": [
            {"name": row[0], "status": row[1], "range": row[2], "permissions": row[3]} for row in users_list
        ]}


@async_db_error_handler
async def add_user(entry):
    """Adds a user entry. Returns error if duplicate."""
    if await check_user_exists(entry):
        return json.loads(error_messages["error_duplicate"])
    async with aiosqlite.connect(DATABASE_USERS) as db:
        cursor = await db.execute(sql["add_user"], (
            entry['name'], entry['status'], entry['range'], entry['password'], entry['permissions']
        ))
        await db.commit()
        if cursor.rowcount == 1:
            return {'success': True}
        return json.loads(error_messages["warning_add"])


@async_db_error_handler
async def update_user(entry):
    """Updates an existing user."""
    async with aiosqlite.connect(DATABASE_USERS) as db:
        cursor = await db.execute(sql["update_user"], (
            entry['name'], entry['status'], entry['range'], entry['password'], entry['permissions']
        ))
        await db.commit()
        if cursor.rowcount == 1:
            return {'success': True}
        return json.loads(error_messages["warning_update"])


@async_db_error_handler
async def delete_user_by_name(name):
    """Deletes a user by their name."""
    async with aiosqlite.connect(DATABASE_USERS) as db:
        cursor = await db.execute(sql["delete_user"], (name,))
        await db.commit()
        if cursor.rowcount == 1:
            return {'success': True}
        return json.loads(error_messages["warning_delete"])


#VM Management
@async_db_error_handler
async def load_stands():
    """Loads all virtual machines (VMs), returning a list of dicts with their properties."""
    async with aiosqlite.connect(DATABASE_VMS) as db:
        cursor = await db.execute(sql["load_stands"])
        vmlist = await cursor.fetchall()
        return {
            "success": True,
            "result": [
                {
                    "ip": row[0],
                    "name": row[1],
                    "status": row[2],
                    "monitoring": row[3],
                    "category": row[4]
                }
                for row in vmlist
            ]
        }


@async_db_error_handler
async def check_user_exists(entry):
    """Checks if a user exists by name."""
    async with aiosqlite.connect(DATABASE_USERS) as db:
        cursor = await db.execute(sql["check_user_exists"], (entry["name"],))
        result = await cursor.fetchone()
        return result is not None


@async_db_error_handler
async def check_vm_exists(entry):
    """Checks if a VM exists by IP."""
    async with aiosqlite.connect(DATABASE_VMS) as db:
        cursor = await db.execute(sql["check_stand_exists"], (entry["ip"],))
        result = await cursor.fetchone()
        return bool(result)


@async_db_error_handler
async def save_vm_(entry):
    """Adds a new VM if it does not exist."""
    async with aiosqlite.connect(DATABASE_VMS) as db:
        cursor = await db.execute(sql["check_stand_exists"], (entry["ip"],))
        result = await cursor.fetchone()
        if result:
            return json.loads(error_messages["error_duplicate"])
        cursor2 = await db.execute(sql["save_stand"], (
            entry["ip"], entry['name'], entry['status'], entry['monitoring'], entry['category'],
            entry['ssh_user'], entry['ssh_password'], entry['ssh_port']))
        await db.commit()
        if cursor2.rowcount == 1:
            return {'success': True}
        else:
            return {'success': False, "error": error_messages["warning_add"]}


@async_db_error_handler
async def update_vm(entry):
    """Updates a VM's metadata."""
    async with aiosqlite.connect(DATABASE_VMS) as db:
        cursor = await db.execute(sql["update_stand"], (
            entry["ip"], entry['name'], entry['status'], entry['monitoring'], entry['category'],
            entry['ssh_user'], entry['ssh_password'], entry['ssh_port']))
        await db.commit()
        return {'success': cursor.rowcount == 1}


@async_db_error_handler
async def delete_vm_by_ip(ip):
    """Removes a VM and its records by IP."""
    async with aiosqlite.connect(DATABASE_VMS) as db:
        await db.execute(sql["delete_stand_ip"], (ip,))
        await db.commit()
    return {"success": True}


#Processes Management

@async_db_error_handler
async def add_proc_to_processes(entry):
    """Adds a process to the monitoring system."""
    async with aiosqlite.connect(DATABASE_VMS) as db:
        cursor = await db.execute(sql['add_proc_to_processes'], (
            entry["ip"], entry['name'], entry['version'], entry['monitoring_period'], entry['logs_path']))
        await db.commit()
        if cursor.rowcount == 1:
            return {'success': True}
        return {'success': False, "error": "duplicate item"}


@async_db_error_handler
async def get_all_from_processes():
    """Returns a list of all processes from the monitoring database."""
    async with aiosqlite.connect(DATABASE_VMS) as db:
        cursor = await db.execute(sql["get_all_processes_from_monitoring"])
        results = await cursor.fetchall()
        return {"result": [
            {"ip": row[0], "name": row[1], "version": row[2], "monitoring_period": row[3], "logs_path": row[4]}
            for row in results
        ]}


@async_db_error_handler
async def update_process(entry):
    """Updates an existing process."""
    async with aiosqlite.connect(DATABASE_VMS) as db:
        cursor = await db.execute(sql['update_process'], (
            entry["ip"], entry['name'], entry['version'], entry['monitoring_period'], entry['logs_path']))
        await db.commit()
        if cursor.rowcount == 1:
            return {'success': True}
        return {'success': False, "error": "update_process item"}


@async_db_error_handler
async def delete_process(entry):
    """Deletes a process record."""
    async with aiosqlite.connect(DATABASE_VMS) as db:
        cursor = await db.execute(sql['delete_proc'], (
            entry["ip"], entry['name']))
        await db.commit()
        if cursor.rowcount == 1:
            return {'success': True}
        return {'success': False, "error": "cant delete item"}


#Monitoring Management

@async_db_error_handler
async def load_monitoring_params():
    """Loads processes set for monitoring (monitoring period > 0)."""
    result = await get_all_from_processes()
    if not result.get("success", True):
        return result
    monitoring = [vm for vm in result["result"] if vm["monitoring_period"] > 0]
    return {"success": True, "result": monitoring}


@async_db_error_handler
async def get_ssh_params():
    """Loads all VM SSH connection settings and processes list for monitoring."""
    async with aiosqlite.connect(DATABASE_VMS) as db:
        cursor = await db.execute(sql["load_stands_ssh"])
        params = await cursor.fetchall()
        result = {}
        for row in params:
            ip = row[1]
            proc_result = await get_proc_from_processes(ip)
            proc = (
                [(p['name'], p['monitoring_period']) for p in proc_result.get('result', [])]
                if proc_result and proc_result.get('success', True) else []
            )
            result[ip] = {
                "ip": ip,
                "ssh_user": row[6],
                "ssh_password": row[7],
                "ssh_port": row[8],
                "proc": proc,
            }
        return {"success": True, "result": result}


async def poller(conn, ip, component, interval):
    """ Continuously polls a remote process on a VM via SSH and records its resource usage."""
    cmd = (commands['get_proc_loads'])
    cmd = cmd.format(proc=component)
    while True:
        try:
            res = await conn.run(cmd)
            cpu, mem = res.stdout.strip().split()
            err = res.stderr
            await make_monitoring_record({"ip": ip, "name": component, "cpu": cpu, "ram": mem, "err": err})
        except Exception as e:
            print(f"[{ip}] '{cmd}' error: {e}")
        await asyncio.sleep(interval)


async def session_mgr(ip, username, password, port, processes):
    """For a given VM, establishes an SSH connection and launches pollers for each monitored process."""
    pollers = []
    async with asyncssh.connect(ip, username=username, password=password, port=port, known_hosts=None) as conn:
        for proc in processes:
            if len(proc) > 0 and proc[1] != 0:
                pollers.append(asyncio.create_task(poller(conn, ip, proc[0], proc[1])))
        if pollers:
            await asyncio.gather(*pollers)


async def monitoring_run():
    """ Main entry point to start monitoring for all configured VMs."""
    tasks = []
    vm_params = await get_ssh_params()
    if vm_params["success"]:
        vm_params = vm_params["result"]
        for item in vm_params:
            ip = vm_params[item]["ip"]
            username = vm_params[item]["ssh_user"]
            password = vm_params[item]["ssh_password"]
            port = vm_params[item]["ssh_port"]
            proc = vm_params[item]["proc"]
            tasks = [asyncio.create_task(session_mgr(ip, username, password, port, proc))]
        await asyncio.gather(*tasks)


@async_db_error_handler
async def make_monitoring_record(entry):
    """Writes a monitoring entry to the per-VM SQLite database."""
    db_name = os.path.join(MONITORING_PATH, entry['ip'])
    logging.info("try make_monitoring_record %s ", entry['ip'])
    async with aiosqlite.connect(db_name) as dbp:
        timestamp = datetime.datetime.now()
        date_str = str(timestamp.date())
        await dbp.execute(
            f"""CREATE TABLE IF NOT EXISTS "{date_str}" (
                datetime TIMESTAMP NOT NULL,
                name TEXT,
                cpu REAL,
                ram REAL,
                err TEXT
            )"""
        )
        values = (
            timestamp,
            entry.get('name'),
            entry.get('cpu'),
            entry.get('ram'),
            entry.get('err')
        )
        await dbp.execute(
            f"""INSERT INTO "{date_str}" VALUES (?, ?, ?, ?, ?)""",
            values
        )
        await dbp.commit()
        logging.info("make_monitoring_record %s success", entry['ip'])
    return True


@async_db_error_handler
async def load_names_list_processes_by_ip(ip):
    """Returns all process names configured for monitoring on a specific VM."""
    async with aiosqlite.connect(DATABASE_VMS) as db:
        cursor = await db.execute(sql["select_processes_name_by_ip"], (ip,))
        rows = await cursor.fetchall()
        return {"success": True, "result": [r[0] for r in rows]}


@async_db_error_handler
async def get_proc_from_processes(ip):
    """ Loads the list of monitoring processes configured for a given VM."""

    async with aiosqlite.connect(DATABASE_VMS) as db:
        cursor = await db.execute(sql["get_processes_from_monitoring"], (ip,))
        results = await cursor.fetchall()
        return {
            "success": True,
            "result": [
                {
                    "name": row[0],
                    "version": row[1],
                    "monitoring_period": row[2],
                    "logs_path": row[3]
                }
                for row in results
            ]
        }


@async_db_error_handler
async def search_last_table(procdbename):
    """Retrieves the most recent (or the oldest, see code) monitoring table for a given VM's DB."""
    logging.info("try search_last_table %s ", procdbename)
    async with aiosqlite.connect(procdbename) as db_proc:
        cursor = await db_proc.execute(sql["select_all_tables"])
        tables = await cursor.fetchall()
        if tables:
            table_names = [row[0] for row in tables]
            last_table = min(table_names)  # возможно, тут нужно max? зависит от задачи
            logging.info("search_last_table %s success", procdbename)
            return {"success": True, 'result': last_table}
        logging.error("search_last_table %s not success", procdbename)
        return {"success": False, "error": "No tables found"}


@async_db_error_handler
async def delete_monitoring_bd(ip):
    """Removes all monitoring records relating to a given VM's IP from the central monitoring database."""
    async with aiosqlite.connect(DATABASE_MONITORING) as db:
        await db.execute(sql["delete_monitoring_reestr_ip"], (ip,))
        await db.commit()
    return {"success": True}


@async_db_error_handler
async def load_scr():
    """Loads all scripts from the 'scripts' database table."""
    async with aiosqlite.connect(DATABASE_VMS) as db:
        cursor = await db.execute("SELECT id, name, content FROM scripts")
        all_scripts = await cursor.fetchall()
        return [{"id": row[0], "name": row[1], "content": row[2]} for row in all_scripts]


@async_db_error_handler
async def get_monitoring_records_by_proclist_from_proctable(procdbename, processes):
    """For each specified process, retrieves recent monitoring records from the latest monitoring table."""
    logging.info("try get_monitoring_records_by_proclist_from_proctable %s ", procdbename)
    processes_monitoring = {}
    tail = int(config["MONITORING_TAIL"])
    result_search_last_table = await search_last_table(procdbename)
    if not result_search_last_table.get("success", False):
        return result_search_last_table
    last_table = result_search_last_table['result']
    async with aiosqlite.connect(procdbename) as db_proc:
        for procname in processes:
            cursor_proc = await db_proc.execute(
                f'''
                SELECT datetime, cpu, ram, err
                FROM "{last_table}"
                WHERE name = ?
                ORDER BY datetime DESC
                LIMIT ?
                ''', (procname, tail)
            )
            all_records = await cursor_proc.fetchall()
            processes_monitoring[procname] = [
                {
                    "datetime": row[0],
                    "cpu": row[1],
                    "ram": row[2],
                    "err": row[3],
                }
                for row in all_records
            ]
    logging.info("get_monitoring_records_by_proclist_from_proctable %s success", procdbename)
    return {"success": True, 'result': processes_monitoring}


@async_db_error_handler
async def load_last_monitoring(ip):
    """For a given VM, retrieves the most recent monitoring records for all associated processes."""
    logging.info("try load_last_monitoring %s ", ip)
    procdbename = os.path.join(MONITORING_PATH, ip)
    result = await load_names_list_processes_by_ip(ip)
    if not result.get("success", False):
        return result
    processes = result["result"] + ["base"]
    return await get_monitoring_records_by_proclist_from_proctable(procdbename, processes)

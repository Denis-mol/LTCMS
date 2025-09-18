import functools
import pytest
import tempfile
import os
import logging
from run import config
import json
from application import helpers
from helpers import (
    read_file, read_json_file, make_dir,
    db_init, add_user, load_users, update_user, delete_user_by_name,
    save_vm_, load_stands, update_vm, delete_vm_by_ip,
    add_proc_to_processes, get_all_from_processes, update_process, delete_process, check_vm_exists,sql
)



@pytest.mark.asyncio
async def test_read_file_and_json(tmp_path):
    """testing json helpers"""

    text_file = tmp_path / "myfile.txt"
    text_file.write_text("hello world")
    result = await read_file(str(text_file))
    assert result == "hello world"


    fail = await read_file(str(tmp_path / "absent.txt"))
    assert isinstance(fail, dict) and not fail["success"]


    json_file = tmp_path / "data.json"
    obj = {"x": 10}
    json_file.write_text(json.dumps(obj))
    parsed = read_json_file(str(json_file))
    assert parsed == obj


    broken_file = tmp_path / "broken.json"
    broken_file.write_text("{ not: valid json")
    fail = read_json_file(str(broken_file))
    assert isinstance(fail, dict) and not fail["success"]



def test_make_dir(tmp_path):
    """testing make_dir helper"""
    dir1 = tmp_path / "mydir"
    result = make_dir(str(dir1))
    assert result["success"]

    result = make_dir(str(dir1))
    assert result["success"]

    dir_bad = "/root/likely_forbidden_dir"
    fail = make_dir(dir_bad)
    assert not fail["success"]




@pytest.mark.asyncio
async def test_add_update_delete_user(tmp_path, monkeypatch):
    """testing users_db"""
    db_path = str(tmp_path / "users.db")
    user_schema = config['DATABASE_USERS_SCHEMA']
    await db_init(db_path, user_schema)
    monkeypatch.setattr("helpers.DATABASE_USERS", db_path)
    user = {
        "name": "alice", "status": "active", "range": "1",
        "password": "hash", "permissions": "admin"
    }
    added = await add_user(user)
    assert added["success"]

    dupe = await add_user(user)
    assert not dupe["success"]

    users = await load_users()
    assert users["success"]
    assert any(u["name"] == "alice" for u in users["result"])

    user2 = user.copy()
    user2["status"] = "inactive"
    updated = await update_user(user2)
    assert updated["success"]

    deleted = await delete_user_by_name("alice")
    assert deleted["success"]

    notfound = await delete_user_by_name("ghost")
    assert not notfound["success"]



@pytest.mark.asyncio
async def test_vm_crud(tmp_path, monkeypatch):
    """testing db_vms"""
    db_path = str(tmp_path / "vms.db")
    vm_schema =config['DATABASE_VMS_SCHEMA']
    await db_init(db_path, vm_schema)
    monkeypatch.setattr("helpers.DATABASE_VMS", db_path)

    vm = {
        "ip": "1.1.1.1", "name": "TestVM", "status": "off",
        "monitoring": "yes", "category": "cat",
        "ssh_user": "root", "ssh_password": "pw", "ssh_port": "22"
    }

    result = await save_vm_(vm)
    assert result["success"]

    result = await save_vm_(vm)
    assert not result["success"]

    stands = await load_stands()
    assert stands["success"]
    assert any(x["ip"] == "1.1.1.1" for x in stands["result"])

    vm2 = vm.copy()
    vm2["status"] = "on"
    up = await update_vm(vm2)
    assert up["success"]

    deled = await delete_vm_by_ip("1.1.1.1")
    assert deled["success"]


@pytest.mark.asyncio
async def test_process_crud(tmp_path, monkeypatch):
    """testing process_crud"""
    db_path = str(tmp_path / "vms_processes.db")
    proc_schema =config['PROCESSES_SCHEMA']
    await db_init(db_path, proc_schema)
    monkeypatch.setattr("helpers.DATABASE_VMS", db_path)

    proc = {"ip": "5.5.5.5", "name": "nginx", "version": "1.1.1", "monitoring_period": "30",
            "logs_path": "/var/log/nginx"}

    added = await add_proc_to_processes(proc)
    assert added["success"]

    added2 = await add_proc_to_processes(proc)
    assert not added2["success"]

    allprocs = await get_all_from_processes()
    assert any(x["name"] == "nginx" for x in allprocs["result"])

    proc2 = proc.copy()
    proc2["version"] = "1.2.2"
    up = await update_process(proc2)
    assert up["success"]

    deled = await delete_process(proc)
    assert deled["success"]

    deled2 = await delete_process(proc)
    assert not deled2["success"]



@pytest.mark.asyncio
async def test_vm_crud(tmp_path, monkeypatch):
    """testing vn_crud"""
    db_path = str(tmp_path / "vms_test.db")

    await db_init(db_path, config['DATABASE_VMS_SCHEMA'])
    monkeypatch.setattr("helpers.DATABASE_VMS", db_path)

    monkeypatch.setitem(helpers.sql, "check_stand_exists", "SELECT 1 FROM vms WHERE ip=?")
    monkeypatch.setitem(helpers.sql, "save_stand", "INSERT INTO vms (ip, name, status, monitoring, category, ssh_user, ssh_password, ssh_port) VALUES (?,?,?,?,?,?,?,?)")
    monkeypatch.setitem(helpers.sql, "load_stands", "SELECT ip, name, status, monitoring, category FROM vms")
    monkeypatch.setitem(helpers.sql, "update_stand", "UPDATE vms SET name=?, status=?, monitoring=?, category=?, ssh_user=?, ssh_password=?, ssh_port=? WHERE ip=?")
    monkeypatch.setitem(helpers.sql, "delete_stand_ip", "DELETE FROM vms WHERE ip=?")

    vm = {
        "ip": "10.1.1.1", "name": "host1", "status": "up", "monitoring": "yes",
        "category": "dev", "ssh_user": "root", "ssh_password": "pw", "ssh_port": "22"
    }

    r = await save_vm_(vm)
    assert r["success"]

    r2 = await save_vm_(vm)
    assert not r2["success"], 'Duplicate must fail'

    r = await load_stands()
    assert r["success"]
    assert any(x["ip"] == "10.1.1.1" for x in r["result"])

    r = await check_vm_exists({"ip": "10.1.1.1"})
    assert r

    r = await check_vm_exists({"ip": "no_such_ip"})
    assert not r

    new_vm = vm.copy()
    new_vm["status"] = "down"
    new_vm["category"] = "prod"
    r = await update_vm(new_vm)
    assert r["success"]

    r = await delete_vm_by_ip("10.1.1.1")
    assert r["success"]

    r = await delete_vm_by_ip("10.1.1.1")
    assert r["success"]

@pytest.mark.asyncio
async def test_process_crud(tmp_path, monkeypatch):
    """testing process_crud"""
    db_path = str(tmp_path / "proc_test.db")
    await db_init(db_path, config['PROCESSES_SCHEMA'])
    monkeypatch.setattr("helpers.DATABASE_VMS", db_path)
    monkeypatch.setitem(helpers.sql, "add_proc_to_processes", "INSERT INTO processes (ip, name, version, monitoring_period, logs_path) VALUES (?,?,?,?,?)")
    monkeypatch.setitem(helpers.sql, "get_all_processes_from_monitoring", "SELECT ip,name,version,monitoring_period,logs_path FROM processes")
    monkeypatch.setitem(helpers.sql, "update_process", "UPDATE processes SET version=?, monitoring_period=?, logs_path=? WHERE ip=? AND name=?")
    monkeypatch.setitem(helpers.sql, "delete_proc", "DELETE FROM processes WHERE ip=? AND name=?")

    pr = {"ip": "1.2.3.4", "name": "proc1", "version": "v1", "monitoring_period": 10, "logs_path": "/tmp/log"}
    res = await add_proc_to_processes(pr)
    assert res["success"]

    res = await add_proc_to_processes(pr)
    assert not res["success"]

    res = await get_all_from_processes()
    assert any(x["name"] == "proc1" for x in res["result"])

    pr2 = pr.copy()
    pr2["version"] = "v2"
    pr2["logs_path"] = "/tmp/log2"
    res = await update_process(pr2)
    assert "success" in res

    res = await delete_process(pr)
    assert res["success"]

    res = await delete_process(pr)
    assert not res["success"]


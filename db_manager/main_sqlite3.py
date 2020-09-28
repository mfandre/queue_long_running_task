import sqlite3
import sys
from datetime import datetime
sys.path.append("..") # to fix sibling imports
from custom_exceptions import job_error

DB_PATH = r'C:\_projetos\QUEUES_PYTHON\db_manager\job_manager.db'

class Job():
    job_id = ""
    job_status = "CREATED"
    date = ""
    error_msg = ""
    pid = 0

def open_db_connection():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    return (conn, cur)

def close_db_connection(conn_and_cursor):
    conn = conn_and_cursor[0]
    conn.close()
    #print("closing connection")

def begin_transaction(conn_and_cursor):
    pass

def rollback_transaction(conn_and_cursor):
    conn = conn_and_cursor[0]
    conn.rollback()

def commit_transaction(conn_and_cursor):
    conn = conn_and_cursor[0]
    conn.commit()

def __get_by_id(id, conn_and_cursor = None):
    if conn_and_cursor != None:
        conn = conn_and_cursor[0]
        c = conn_and_cursor[1]
    else:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
    # Do this instead
    t = (id,)
    c.execute('SELECT job_id, date, job_status, error_msg, pid FROM jobs WHERE job_id=?', t)
    returned = c.fetchone()

    if returned == None:
        print("This job_id doesnt exists in your DB")
        raise job_error.JobDontExistsError("This job_id doesnt exists in your DB")

    print("select returned", returned)

    if conn_and_cursor == None:
        conn.close()

    job = Job()

    job.job_id = returned[0]
    job.date = returned[1]
    job.job_status = returned[2]
    job.error_msg = returned[3]
    job.pid = returned[4]

    return job

def __create_job_table(conn_and_cursor = None):
    if conn_and_cursor != None:
        conn = conn_and_cursor[0]
        c = conn_and_cursor[1]
    else:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

    # Create table
    c.execute('''CREATE TABLE jobs
                (job_id text, date text, job_status text, error_msg text, pid integer)''')

    # We can also close the connection if we are done with it.
    # Just be sure any changes have been committed or they will be lost.
    conn.close()

def __delete_all_job():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # Insert a row of data
    returned = c.execute("DELETE FROM jobs")
    #print("delete returned", returned)
    # Save (commit) the changes
    conn.commit()
    # We can also close the connection if we are done with it.
    # Just be sure any changes have been committed or they will be lost.
    conn.close()

def __insert_job(id, date, status, error_msg, conn_and_cursor = None):
    if conn_and_cursor != None:
        conn = conn_and_cursor[0]
        c = conn_and_cursor[1]
    else:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
    # Insert a row of data
    t = (id, date, status, error_msg)
    returned = c.execute("INSERT INTO jobs VALUES (?,?,?,?, 0)", t)
    #print("insert returned", returned)

    if conn_and_cursor == None:
        # Save (commit) the changes
        conn.commit()
        # We can also close the connection if we are done with it.
        # Just be sure any changes have been committed or they will be lost.
        conn.close()

def __update_job_pid(id, pid, conn_and_cursor = None):
    if conn_and_cursor != None:
        conn = conn_and_cursor[0]
        c = conn_and_cursor[1]
    else:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
    
    t = (str(pid), id)
    returned = c.execute("UPDATE jobs SET pid = ? WHERE job_id = ?", t)

    #print("UPDATE jobs SET date = '"+date+"', job_status = '"+status+"' WHERE job_id = '"+id+"'")

    if conn_and_cursor == None:
        # Save (commit) the changes
        conn.commit()
        # We can also close the connection if we are done with it.
        # Just be sure any changes have been committed or they will be lost.
        conn.close()

def __update_job(id, date, status, error_msg, pid, conn_and_cursor = None):
    if conn_and_cursor != None:
        conn = conn_and_cursor[0]
        c = conn_and_cursor[1]
    else:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
    
    if pid == None:
        t = (date, status, error_msg, id)
        returned = c.execute("UPDATE jobs SET date = ?, job_status = ?, error_msg = ? WHERE job_id = ?", t)
    else:
        t = (date, status, error_msg, str(pid), id)
        returned = c.execute("UPDATE jobs SET date = ?, job_status = ?, error_msg = ?, pid = ? WHERE job_id = ?", t)

    #print("UPDATE jobs SET date = '"+date+"', job_status = '"+status+"' WHERE job_id = '"+id+"'")

    if conn_and_cursor == None:
        # Save (commit) the changes
        conn.commit()
        # We can also close the connection if we are done with it.
        # Just be sure any changes have been committed or they will be lost.
        conn.close()

def insert_job_into_db(id, conn_and_cursor = None):
    today = datetime.now()
    today_str = today.strftime("%m-%d-%Y %H:%M:%S")

    __insert_job(id, today_str, "ENQUEUE", "",conn_and_cursor)

    return id

def update_job_into_db(id, status, error_msg, pid, conn_and_cursor = None):
    today = datetime.now()
    today_str = today.strftime("%m-%d-%Y %H:%M:%S")

    __update_job(id, today_str, status, error_msg, pid, conn_and_cursor)

def update_job_pid_into_db(id, pid, conn_and_cursor = None):
    __update_job_pid(id, pid, conn_and_cursor)

def get_job_status(id, conn_and_cursor = None):
    job = __get_by_id(id, conn_and_cursor)
    return job.job_status

def get_job_by_id(id, conn_and_cursor = None):
    job = __get_by_id(id, conn_and_cursor)
    return job

#if __name__ == '__main__':
#   __create_job_table()
#   __delete_all_job()
import psycopg2
import sys
import os
from datetime import datetime
sys.path.append("..") # to fix sibling imports
from custom_exceptions import job_error

def get_env(key):
    try:
        return os.environ[key]
    except:
        return None

DB = get_env('DB_POSTGRES_DB') or 'postgres'
USER = get_env('DB_POSTGRES_USER') or 'postgres'
PASS = get_env('DB_POSTGRES_PASS') or 'postgres'
HOST = get_env('DB_POSTGRES_HOST') or 'localhost'
PORT = get_env('DB_POSTGRES_PORT') or 5432

class Job():
    job_id = ""
    job_status = "CREATED"
    date = ""
    error_msg = ""
    pid = 0
    date_end_execution = ""
    host = ""

def open_db_connection():
    conn = psycopg2.connect(host=HOST, user=USER, password=PASS, dbname=DB, port=int(PORT))
    cur = conn.cursor()
    return (conn, cur)

def close_db_connection(conn_and_cursor):
    conn = conn_and_cursor[0]
    c = conn_and_cursor[1]
    c.close()
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

def __get_by_id(job_id, conn_and_cursor = None):
    if conn_and_cursor != None:
        conn = conn_and_cursor[0]
        c = conn_and_cursor[1]
    else:
        conn = psycopg2.connect(host=HOST, user=USER, password=PASS, dbname=DB, port=int(PORT))
        c = conn.cursor()
    # Do this instead
    c.execute("SELECT job_id, date, job_status, error_msg, pid, date_end_execution, host FROM jobs WHERE job_id='"+job_id+"'")
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
    job.date_end_execution = returned[5]
    job.host = returned[6]

    return job

def __create_job_table():
    print("Creating table")
    try:
        conn = psycopg2.connect(host=HOST, user=USER, password=PASS, dbname=DB, port=int(PORT))
        c = conn.cursor()

        # Create table
        c.execute('''CREATE TABLE public.jobs
                    (id serial PRIMARY KEY, job_id varchar, date varchar, job_status varchar, error_msg text, pid integer, date_end_execution varchar, host varchar)''')

        # We can also close the connection if we are done with it.
        # Just be sure any changes have been committed or they will be lost.
        conn.commit()
        c.close()
        conn.close()
        print("Table CREATED")
    except Exception as e:
        print(e)

def __delete_all_job():
    conn = psycopg2.connect(host=HOST, user=USER, password=PASS, dbname=DB, port=int(PORT))
    c = conn.cursor()
    # Insert a row of data
    returned = c.execute("DELETE FROM jobs")
    #print("delete returned", returned)
    # Save (commit) the changes
    conn.commit()
    # We can also close the connection if we are done with it.
    # Just be sure any changes have been committed or they will be lost.
    c.close()
    conn.close()

def __insert_job(job_id, date, status, error_msg, conn_and_cursor = None):
    if conn_and_cursor != None:
        conn = conn_and_cursor[0]
        c = conn_and_cursor[1]
    else:
        conn = psycopg2.connect(host=HOST, user=USER, password=PASS, dbname=DB, port=int(PORT))
        c = conn.cursor()
    # Insert a row of data
    t = (job_id, date, status, error_msg, 0, "", "")
    returned = c.execute("INSERT INTO jobs (job_id, date, job_status, error_msg, pid, date_end_execution, host) VALUES %s", (t,))
    #print("insert returned", returned)

    if conn_and_cursor == None:
        # Save (commit) the changes
        conn.commit()
        # We can also close the connection if we are done with it.
        # Just be sure any changes have been committed or they will be lost.
        c.close()
        conn.close()

def __update_job_end_execution(job_id, date_end_execution, conn_and_cursor = None):
    if conn_and_cursor != None:
        conn = conn_and_cursor[0]
        c = conn_and_cursor[1]
    else:
        conn = psycopg2.connect(host=HOST, user=USER, password=PASS, dbname=DB, port=int(PORT))
        c = conn.cursor()
    
    returned = c.execute("UPDATE jobs SET date_end_execution = '"+date_end_execution+"' WHERE job_id = '"+job_id+"'")

    #print("UPDATE jobs SET date = '"+date+"', job_status = '"+status+"' WHERE job_id = '"+id+"'")

    if conn_and_cursor == None:
        # Save (commit) the changes
        conn.commit()
        # We can also close the connection if we are done with it.
        # Just be sure any changes have been committed or they will be lost.
        c.close()
        conn.close()


def __update_job_pid(job_id, pid, host, conn_and_cursor = None):
    if conn_and_cursor != None:
        conn = conn_and_cursor[0]
        c = conn_and_cursor[1]
    else:
        conn = psycopg2.connect(host=HOST, user=USER, password=PASS, dbname=DB, port=int(PORT))
        c = conn.cursor()
    
    returned = c.execute("UPDATE jobs SET pid = '"+str(pid)+"', host = '"+host+"' WHERE job_id = '"+job_id+"'")

    #print("UPDATE jobs SET date = '"+date+"', job_status = '"+status+"' WHERE job_id = '"+id+"'")

    if conn_and_cursor == None:
        # Save (commit) the changes
        conn.commit()
        # We can also close the connection if we are done with it.
        # Just be sure any changes have been committed or they will be lost.
        c.close()
        conn.close()

def __update_job(job_id, date, status, error_msg, pid, host, conn_and_cursor = None):
    if conn_and_cursor != None:
        conn = conn_and_cursor[0]
        c = conn_and_cursor[1]
    else:
        conn = psycopg2.connect(host=HOST, user=USER, password=PASS, dbname=DB, port=int(PORT))
        c = conn.cursor()
    
    if pid == None:
        t = (date, status, error_msg, job_id)
        returned = c.execute("UPDATE jobs SET date = '"+date+"', job_status = '"+status+"', error_msg = '"+error_msg+"' WHERE job_id = '"+job_id+"'")
    else:
        returned = c.execute("UPDATE jobs SET date = '"+date+"', job_status = '"+status+"', error_msg = '"+error_msg+"', pid = '"+str(pid)+"', host = '"+host+"' WHERE job_id = '"+job_id+"'")

    #print("UPDATE jobs SET date = '"+date+"', job_status = '"+status+"' WHERE job_id = '"+id+"'")

    if conn_and_cursor == None:
        # Save (commit) the changes
        conn.commit()
        # We can also close the connection if we are done with it.
        # Just be sure any changes have been committed or they will be lost.
        c.close()
        conn.close()

def insert_job_into_db(job_id, conn_and_cursor = None):
    today = datetime.now()
    today_str = today.strftime("%m-%d-%Y %H:%M:%S")

    __insert_job(job_id, today_str, "ENQUEUE", "",conn_and_cursor)


def update_job_into_db(job_id, status, error_msg, pid, host, conn_and_cursor = None):
    today = datetime.now()
    today_str = today.strftime("%m-%d-%Y %H:%M:%S")

    __update_job(job_id, today_str, status, error_msg, pid, host, conn_and_cursor)

def update_job_pid_into_db(job_id, pid, host, conn_and_cursor = None):
    __update_job_pid(job_id, pid, host, conn_and_cursor)

def update_job_end_execution_into_db(job_id, date_end_execution, conn_and_cursor = None):
    __update_job_end_execution(job_id, date_end_execution, conn_and_cursor)

def get_job_status(job_id, conn_and_cursor = None):
    job = __get_by_id(job_id, conn_and_cursor)
    return job.job_status

def get_job_by_id(job_id, conn_and_cursor = None):
    job = __get_by_id(job_id, conn_and_cursor)
    return job

if __name__ == '__main__':
   __create_job_table()
#   __delete_all_job()

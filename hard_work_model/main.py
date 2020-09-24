import pika
import sys
import os
import time
from random import randrange
sys.path.append("..") # to fix sibling imports
from db_manager import main
from custom_exceptions import job_error
from process_controller import process_killer, process_wrapper

DO_WORK_QUEUE_NAME = "hard_model_execution"
KILL_WORK_QUEUE_NAME = "kill_hard_model_execution"
QUEUE_SIZE = 100

def change_job_status_to_error(id, error_msg, conn_and_cursor = None):
    try:
        main.update_job_into_db(id, "ERROR", error_msg, None, conn_and_cursor)
    except Exception as e:
        print("fail to update job status", e)
        raise e

def change_job_status_to_processing(id, conn_and_cursor = None):
    try:
        main.update_job_into_db(id, "PROCESSING", "", None, conn_and_cursor)
    except Exception as e:
        print("fail to update job status", e)
        raise e

def change_job_status_to_finished(id, conn_and_cursor = None):
    try:
        job_status = main.get_job_status(id)
        #dont update if job is killed or canceled
        if(job_status == "KILLED" or job_status == "CANCELLED_BEFORE_EXECUTION"):
            return
        main.update_job_into_db(id, "FINISHED", "", None, conn_and_cursor)
    except Exception as e:
        print("fail to update job status", e)
        raise e

def change_job_status_to_killed(id, conn_and_cursor = None):
    try:
        main.update_job_into_db(id, "KILLED", "", None, conn_and_cursor)
    except Exception as e:
        print("fail to update job status", e)
        raise e

def change_job_status_to_cancelled_before_execution(id, conn_and_cursor = None):
    try:
        main.update_job_into_db(id, "CANCELLED_BEFORE_EXECUTION", "", None, conn_and_cursor)
    except Exception as e:
        print("fail to update job status", e)
        raise e
        
def call_my_very_hard_work_process():
    start = time.time()
    total_iterations = 800000000*10
    for i in range(1,total_iterations):
        pass
        #if i%100000 == 0:
            #print(100*(i/total_iterations))
    end = time.time()
    print("done hard_work in ", end - start)

def do_work(ch, method, properties, body):
    conn_and_cursor = None
    job_id = None
    try:
        print(" [x] Received %r" % body)
        job_id = body.decode()  #decoding because it arrived as BYTE
        print("job_id", job_id)
        conn_and_cursor = main.open_db_connection()
        job_status = main.get_job_status(job_id, conn_and_cursor)
        
        if job_status == "CANCELLED_BEFORE_EXECUTION":
            #ACK to remove the item from QUEUE
            ch.basic_ack(delivery_tag = method.delivery_tag)
            print("This job was previuosly cancelled by user")
            return
        
        if job_status == "KILLED":
            #ACK to remove the item from QUEUE
            ch.basic_ack(delivery_tag = method.delivery_tag)
            print("This job was previuosly killed by user")
            return

        #just to focer some random failures... and check if the renqueue is working
        #rand = randrange(100)
        #if rand < 90:
        #    raise Exception("Random error " + str(rand))

        change_job_status_to_processing(job_id, conn_and_cursor)
        main.commit_transaction(conn_and_cursor) #its important to uptade soon as possible to "processing" state this why I commit

        #call_my_very_hard_work_process() but in a separate process
        pw = process_wrapper.ProcessWrapper(call_my_very_hard_work_process)
        pw.execute()
        #print("================> pw.mainProcessPID", pw.mainProcessPID)
        #print("================> current pid", os.getpid())
        main.update_job_pid_into_db(job_id, pw.mainProcessPID)
        main.commit_transaction(conn_and_cursor)

        pw.join()

        change_job_status_to_finished(job_id, conn_and_cursor)
        main.commit_transaction(conn_and_cursor)
        #main.rollback_transaction(conn_and_cursor) # Just to test if rollback is working... it is!!!
        #ACK to remove the item from QUEUE
        ch.basic_ack(delivery_tag = method.delivery_tag)

    except job_error.JobDontExistsError as de:
        if conn_and_cursor != None:
            main.rollback_transaction(conn_and_cursor)
        ch.basic_ack(delivery_tag = method.delivery_tag)
        print("JobID doesnt exists")

    except Exception as e:
        if conn_and_cursor != None:
            main.rollback_transaction(conn_and_cursor)

        change_job_status_to_error(job_id, str(e), conn_and_cursor)
        main.commit_transaction(conn_and_cursor)

        #Here you can decide if you ACK or NACK... 
        #if NACK the job will again to the QUEUE [NACK to re-QUEUE depends from you QUEUE configuration] 
        #If ACK will be remove from QUEUE
        ch.basic_nack(delivery_tag = method.delivery_tag)
        print("fail to do work", e)

    finally:
        if conn_and_cursor != None:
            main.close_db_connection(conn_and_cursor)

def kill_work(ch, method, properties, body):
    conn_and_cursor = None
    job_id = None
    print(" [x] Received %r" % body)
    job_id = body.decode()  #decoding because it arrived as BYTE
    print("job_id", job_id)

    try:
        conn_and_cursor = main.open_db_connection()
        job_status = main.get_job_status(job_id, conn_and_cursor)
        if(job_status == "PROCESSING"):
            job_from_db = main.get_job_by_id(job_id, conn_and_cursor)
            print("Job is processing, we will kill using PID", job_from_db.pid)
            pk = process_killer.ProcessKiller(job_from_db.pid)
            pk.kill()
            ch.basic_ack(delivery_tag = method.delivery_tag)
            change_job_status_to_killed(job_id, conn_and_cursor)
            main.commit_transaction(conn_and_cursor)
            print("killed worked")
            return

        print("Job is not processing, we just set the status on DB")
        change_job_status_to_cancelled_before_execution(job_id, conn_and_cursor)
        main.commit_transaction(conn_and_cursor)
        ch.basic_ack(delivery_tag = method.delivery_tag)
        print("killed worked")
    except Exception as e:
        print("Kill work fail",e)
        ch.basic_nack(delivery_tag = method.delivery_tag)

def cancelled(method_frame):
    print("cancelled", method_frame)

def start_consumer(queue_name, callback):
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost', 5672, heartbeat=0)) #its important to turn off the hearbeat in the server look: https://stackoverflow.com/questions/14572020/handling-long-running-tasks-in-pika-rabbitmq
    channel = connection.channel()
    #channel.basic_qos(prefetch_count=1)

    channel.queue_declare(queue=queue_name, durable=True, arguments={'x-max-length': QUEUE_SIZE, 'x-overflow': "reject-publish"})

    channel.basic_consume(queue=queue_name,
                        auto_ack=False,
                        on_message_callback=callback)
    channel.add_on_cancel_callback(cancelled)

    print(" [*] "+queue_name+" Waiting for messages. To exit press CTRL+C")
    channel.start_consuming()

def force_quit():
    try:
        sys.exit(0)
    except SystemExit:
        os._exit(0)

if __name__ == '__main__':
    try:
        print(sys.argv)
        if len(sys.argv) <= 1:
            print("Parameter consumer is required: kill_work or do_work)")
            force_quit()
        
        if sys.argv[1] == "do_work":
            start_consumer(DO_WORK_QUEUE_NAME, do_work)
        elif sys.argv[1] == "kill_work":
            start_consumer(KILL_WORK_QUEUE_NAME, kill_work)
    except KeyboardInterrupt:
        print('Interrupted')
        force_quit()
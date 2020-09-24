import pika
import sys
import os
import uuid
sys.path.append("..") # to fix sibling imports
from db_manager import main

DO_WORK_QUEUE_NAME = "hard_model_execution"
KILL_WORK_QUEUE_NAME = "kill_hard_model_execution"
QUEUE_SIZE = 100

def force_quit():
    try:
        sys.exit(0)
    except SystemExit:
        os._exit(0)

def check_status_job(job_id, conn_and_cursor = None):
    try:
        return main.get_job_status(job_id, conn_and_cursor)
    except Exception as e:
        print("fail to get job status")
        raise e

def change_job_status_to_error_during_enqueue(job_id, conn_and_cursor = None):
    try:
        main.update_job_into_db(job_id, "ERROR_ENQUEUE", "", None, conn_and_cursor)
    except Exception as e:
        print("fail to update job status", e)
        raise e

def cancel_callback():
    print("test cancel")

def enqueue_job(job_id):
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters('localhost', 5672))
        channel = connection.channel()
        channel.queue_declare(queue=DO_WORK_QUEUE_NAME, durable=True, arguments={'x-max-length': QUEUE_SIZE, 'x-overflow': "reject-publish"})
        channel.confirm_delivery()

        channel.basic_publish(exchange='',
                        routing_key=DO_WORK_QUEUE_NAME,
                        body=job_id,
                        properties=pika.BasicProperties(
                            delivery_mode=2,  # make message persistent
                        ),
                        mandatory=True)

        print(" [x] Sent 'hard_work_model'")
    except pika.exceptions.UnroutableError:
        print('Message was returned')
        raise
    except pika.exceptions.NackError:
        print('Message was Nack')
        raise
    except Exception as e:
        print("zica grande...", e)
        raise
    finally:
        connection.close()

def kill_job(id):
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters('localhost', 5672))
        channel = connection.channel()
        channel.queue_declare(queue=KILL_WORK_QUEUE_NAME, durable=True, arguments={'x-max-length': QUEUE_SIZE, 'x-overflow': "reject-publish"})
        channel.confirm_delivery()

        channel.basic_publish(exchange='',
                        routing_key=KILL_WORK_QUEUE_NAME,
                        body=id,
                        properties=pika.BasicProperties(
                            delivery_mode=2,  # make message persistent
                        ),
                        mandatory=True)

        print(" [x] Sent 'kill_hard_work_model'")
    except pika.exceptions.UnroutableError:
        print('Message was returned')
        raise
    except pika.exceptions.NackError:
        print('Message was Nack')
        raise
    except Exception as e:
        print("zica grande...", e)
        raise
    finally:
        connection.close()

def show_menu():
    while(True):
        print("==========================")
        print("(1) Enqueue")
        print("(2) Kill")
        print("(0) Exit")
        print("==========================")
        option=int(input('Option (0 to exit):'))
        if(option == 0):
            force_quit()
        elif(option == 1):
            test_job_enqueue()
        elif(option == 2):
            job_id_to_kill=input('Job to kill:')
            test_job_kill(job_id_to_kill)

def test_job_enqueue():
    conn_and_cursor = None
    job_id = None
    try:
        conn_and_cursor = main.open_db_connection()
        job_id = str(uuid.uuid1())
        print("job_id", job_id)
        main.insert_job_into_db(job_id, conn_and_cursor)
        main.commit_transaction(conn_and_cursor)
        try:
            enqueue_job(job_id)
        except:
            #if some shit happens during the enqueue... we need to change the status of our job
            change_job_status_to_error_during_enqueue(job_id, conn_and_cursor)
            raise
    except Exception as e:
        print("Exception", e)
    finally:
        main.close_db_connection(conn_and_cursor)

def test_job_kill(job_id_to_kill):
    kill_job(job_id_to_kill)

if __name__ == '__main__':
    try:
        show_menu()
    except KeyboardInterrupt:
        print('Interrupted')
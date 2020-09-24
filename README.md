# Queue from long running tasks
Python app that uses RabbitMQ to orchestration long running tasks execution

# The idea

![alt idea](https://github.com/mfandre/queue_long_running_task/blob/master/queue_python.png?raw=true)

> It's not prepared for production... I'm still making tests for long-long-long-long-running tasks, this case has several points of fails: sockets closing, RabbitMq heartbeat...

# Project Structure
- custom_exceptions: just exceptions to be more clear in the code
- db_manager: **very basic** functions to manipulate a SQLite3 commands
- hard_work_api: prompt application to send messages to our RabbitMQ. It is our **RabbitMQ PRODUCER**
- hard_work_model: It is our **RabbitMQ Consumer**. It will get messages from our RabbitMQ and simulate a LONG-RUNNING Jobs
- process_controller: ProcessWrapper class is to wrap python functions in new process. ProcessKiller is a class to kill process.

# How to run
- run **docker-compose up --build -d** to up the RabbitMQ
- open two prompt/terminal. Then you open the folder hard_work_model on both. 
- At one executes **python .\main.py do_work** to create a consumer **DO_WORK**
- In another executes **python .\main.py kill_work** to create a consumer **KILL_WORK**
- Open another prompt/terminal and open the folder hard_work_api
- Executes **python .\main.py**
- To create a new job press 1 + enter
- To kill a job press 2 + enter and fill the job_id that you want to kill

# Important notes
- If you will run it in a multiple servers you MUST change the db_manager to use another database instead of SQLite3!
  - Consumer and Producer is running in the same machine that is the reason to SQLite works. If you want to use the consumer in another server you need to change to another DB.
- All my tests was on local machine with RabbitMQ running on Docker container
- I'm a not specialist in python... so, the code is not the best...

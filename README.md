# Password Cracker

This project is a password cracking system, consisting of a master server and multiple minion servers.
The master server distributes password cracking tasks to registered minion servers, keeps track of the progress, and consolidates the final results.

## Master Server

#### Workflow
1. The master server waits to receive registration requests from minion servers.
2. Once registered, the master sends password cracking tasks synchronously to active minions.
> ***Explanation:** The password cracking task includes a **range of passwords** to attempt and a **list of hashed passwords** to crack.*  
> - ***The range** specifies the subset of passwords each minion is responsible for cracking.*  
> - ***The list of hashed passwords** serves as the target for each minion's cracking attempts.*  
> *Sending a list allows each minion to comprehensively go through the password range and respond to the master with all the hashes they've successfully matched, optimizing the process and preventing redundant attempts.*
3. Minions respond with their cracking results.
4. If successful, the master:
   - Updates the final results.
   - Updates the hashed passwords list accordingly.
   - Sends another task to the minion.
5. If unsuccessful - ***Error Handling***
6. The master continues this process until all passwords are cracked or no active minions are available.
7. The final results are written to a file, and the master exits safely.

#### Task Management
- The master keeps track of the next task using a task index, an atomic counter.
- The task index determines the next task to be sent based on the task index and batch size.
- If there are no active minions at any time, the master exits safely while saving the cracked passwords.

>***Note:** When sending a new task to a minion, the master keeps track of each minion along with their number of uncompleted tasks. If a minion already has one task in progress, the master ensures not to assign additional tasks to that minion until the current task is completed.*

#### Error Handling
- If an error occurs during task execution or communication with a minion, the master handles it by reassigning the task to another minion and updating the active minions list.
- If a minion does not respond within a specified timeout, the master removes the minion from the active minions list.
- If the master is terminated, it sends a message to the active minions to inform them of its status.

>***Note:** If the master exits for any reason (e.g., no active minions or an error resulting in termination), the results obtained so far are preserved.*

## Minion Server

#### Workflow
1. The minion server automatically attempt to register with the master upon startup.
2. Once registered, the minion receives passwords cracking task from the master.
3. The minion attempts to crack passwords within the assigned range and sends the results to the master.
4. After receiving a response, the master sends another task to the minion.

>***Dynamic Minion Registration:** Support for dynamic notification allows minions to notify the master when they become operational. Additionally, minions can join the password cracking process even after it has already begun.*

#### Error Handling
- If an error occurs during task execution or communication with the master:
  - The minion sends an error message to the master.
  - The master removes the errored minion from the active minions list.
- If the master is terminated, the minion exits safely.
- If the minion is terminated, it sends a message to the master to inform it of its status.

## Installation Instructions
These instructions will guide you through setting up and installing the necessary dependencies for the *Password Cracker*.

### Prerequisites
- **Python:** Make sure you have Python installed on your machine.

### Clone the Repository
```bash
git clone https://github.com/yuvalalroy/Password_Cracker.git
cd Password_Cracker
```

### Install Dependencies
Navigate to the project directory and install the required dependencies:
```bash
pip install -r requirements.txt
```
### Run the Master Server
```bash 
python Master/master.py <file_path> [<master_port>]
```

**`file_path`** (required): The file path containing the hashed passwords to be cracked.  
**`master_port`** (optional, default=5000): The port on which the master server will listen for connections.

>***Note:** The input file for the master server (`<file_path>`) is expected to contain hashed passwords separated by a new line, Each line represents a single hashed password.*

### Run a Minion Server
```bash
python Minion/minion.py <minion_port> [<master_port>]
```

**`minion_port`** (required): The port on which the minion server will listen for connections.  
**`master_port`** (optional, default=5000): The port on which the master server is running.

Repeat the "Run a Minion Server" step for each additional minion you want to add to the system.  
>***Note:** If you choose a specific server port (`<master_port>` as an argument), ensure to use the same port as an argument when starting the minion nodes for proper communication between the master and minions.*

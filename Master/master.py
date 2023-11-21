from flask import Flask, request, jsonify
from multiprocessing.pool import ThreadPool
from master_settings import build_minion_settings, MAX_POOL_SIZE, RANGE_START, RANGE_END, BATCH_SIZE, TIMEOUT
from master_utils import read_from_file, write_to_file
from atomic_counter import atomic_counter
from typing import List, Dict
import requests
import sys
import atexit
import random
import os

try:
    master_settings = build_minion_settings(sys.argv)
    file_path = master_settings.file_path
    hashed_passwords_list = read_from_file(file_path)
except ValueError as e:
    print(e)
    os._exit(1)


active_minions : List[str] = []
minion_to_incompleted_tasks : Dict[str, atomic_counter] = {}
task_index = atomic_counter()
destroy_flow = atomic_counter()
final_results : Dict[str, str] = {password: None for password in hashed_passwords_list}
master = Flask(__name__)


@master.route('/register_minion', methods=['POST'])
def register_minion():
    data = request.json
    minion_url = data['minion_url']

    if minion_url not in active_minions:
        active_minions.append(minion_url)
        minion_to_incompleted_tasks[minion_url] = atomic_counter()
        print(f'Minion on url {minion_url} added.')
        response = jsonify({'status': 'success', 'message': f'Minion on url {minion_url} added.'})
        send_data_to_minion_async(minion_url)
        return response

    return jsonify({'status': 'error', 'message': f'Minion on url {minion_url} already exists.'})


@master.route('/unregister_minion', methods=['POST'])
def unregister_minion():
    data = request.json
    minion_url = data['minion_url']

    if minion_url in active_minions:
        active_minions.remove(minion_url)
        print(f'Minion on url {minion_url} removed.')

        # If there are no available minions - exit
        if not active_minions:
            print('No available minions.')
        return jsonify({'status': 'success', 'message': f'Minion {minion_url} removed successfully'})

    return jsonify({'status': 'error', 'message': f'Minion {minion_url} not found'})


def send_data_to_minion_async(minion_url):
    lower_bound = RANGE_START + task_index.get_value() * BATCH_SIZE
    task_index.increment()
    task_send(minion_url, lower_bound)


# Handle success response from minion
def send_data_success_cb(response: requests.Response, minion_url, lower_bound):
    if response.status_code == 200:
        data = response.json()
        print(f'Response from {minion_url}: {data}')
        minion_to_incompleted_tasks[minion_url].decrement()

        # If cracked any passwords - add to the final results
        if data['cracked']:
            cracked_passwords = data['passwords']
            final_results.update(cracked_passwords)

        # If cracked all hashed passwords - finish
        if all(final_results.values()):
            print('Cracked all hashed passwords!\n')
            safe_exit()

        # If done going over the range - wait to the last responses
        if RANGE_START + task_index.get_value() * BATCH_SIZE >= RANGE_END:
            return

        # If minion is already working on a task - don't send another one
        if minion_to_incompleted_tasks[minion_url].get_value() < 1:
            send_data_to_minion_async(minion_url)
    else:
        send_data_error_cb(minion_url, lower_bound)


# handle error response from minion
def send_data_error_cb(minion_url, lower_bound):
    if (destroy_flow.get_value()):
        return

    # Remove minion from master's list of active minions
    if minion_url in active_minions:
        active_minions.remove(minion_url)
        minion_to_incompleted_tasks.pop(minion_url, None)
        print(f'Minion on url {minion_url} removed.')

    # Re-assign task to another minion
    if active_minions:
        selected_minion = random.choice(active_minions)
        print(f'Task {lower_bound} assigned from minion {minion_url} to minion {selected_minion}')
        task_send(selected_minion, lower_bound)
    else:
        print('No available minions.')


def task_send(minion_url, lower_bound):
    minion_to_incompleted_tasks[minion_url].increment()

    # Submit the task to the pool
    pool.apply_async(requests.post, args=[f'{minion_url}/crack_password'],
                              kwds={'json': task_data_init(lower_bound), 'timeout': TIMEOUT},
                              callback=lambda e: send_data_success_cb(e, minion_url, lower_bound), 
                              error_callback=lambda e: send_data_error_cb(minion_url, lower_bound))


def task_data_init(lower_bound):
    task_data = {
        'lower_bound': str(lower_bound),
        'upper_bound': str(min(lower_bound + BATCH_SIZE, RANGE_END)),
        'hashes_to_crack': [k for k, v in final_results.items() if v is None]
    }
    return task_data


def safe_exit():
    print('Exiting master')
    destroy_flow.increment()
    results_report()
    notify_minions_on_exit()
    os._exit(1)


# Save results on finish
def results_report():
    try:
        write_to_file(final_results, 'cracked_passwords')
    except ValueError as e:
        print(e)


# Notify all minions that the master is terminating
def notify_minions_on_exit():
    for minion_url in active_minions:
        try:
            response = requests.post(f'{minion_url}/master_done')

            if response.status_code == 200:
                print(f'Notified minion.')
            else:
                print(f'Error. Status code: {response.status_code}')
        except requests.RequestException as e:
            print(f'Notified minion {minion_url} on exit.')


# Register the exit function
atexit.register(safe_exit)


# Start the ThreadPool for handling minion tasks
if __name__ == '__main__':
    pool = ThreadPool(MAX_POOL_SIZE)
    master.run(debug=False, port=master_settings.master_port)

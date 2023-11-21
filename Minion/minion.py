from flask import Flask, request, jsonify
from minion_settings import build_minion_settings
import requests
import hashlib
import sys
import time
import atexit
import os
import signal


try:
    minion_settings = build_minion_settings(sys.argv)
    minion_port = minion_settings.minion_port
    minion_url = minion_settings.minion_url
    master_url = minion_settings.master_url
except ValueError as e:
    print(e)
    os._exit(1)

connected_to_master = False


# Register minion to the master server
def register_to_master(minion_url):
    global connected_to_master
    while True:
        try:
            response = requests.post(f'{master_url}/register_minion', json={'minion_url': minion_url})
            if response.status_code == 200:
                print(f'Master acknowledged. Minion on {minion_url} is now active.')
                connected_to_master = True
                break
            else:
                print(f'Error registering minion. Status code: {response.status_code}')

            time.sleep(2) # Delay before sending the next message


        except requests.RequestException as e:
            print(f'Error: {e}')


# Unregister minion from the master server - in case of unexpected minion's termination
def unregister_from_master(minion_url):
    try:
        response = requests.post(f'{master_url}/unregister_minion', json={'minion_url': minion_url})
        if response.status_code == 200:
            print(f'Master acknowledged. Minion on {minion_url} is now unregistered.')
        else:
            print(f'Error unregistering minion. Status code: {response.status_code}')

    except requests.RequestException as e:
        print('Exiting minion')


def on_exit(minion_url):
    if connected_to_master:
        unregister_from_master(minion_url)
    os._exit(0)


# Initialize the minion Flask app
def minion_init():
    minion = Flask(__name__)

    # Register the exit function to unregister from the master server on exit
    atexit.register(on_exit, minion_url)

    with minion.app_context():
        register_to_master(minion_url)
        return minion

minion = minion_init()


@minion.route('/crack_password', methods=['POST'])
def crack_password():
    task_data = request.json
    lower_bound = int(task_data['lower_bound'])
    upper_bound = int(task_data['upper_bound'])
    hashes_to_crack = task_data['hashes_to_crack']
    cracked_passwords = {}

    for password in range(lower_bound, upper_bound):
        str_password = '0' + str(password)
        full_password = str_password[:3] + '-' + str_password[3:]
        hashed_password = hashlib.md5(full_password.encode()).hexdigest()
        if hashed_password in hashes_to_crack:
            cracked_passwords[hashed_password] = full_password

    if cracked_passwords:
        return jsonify({'passwords': cracked_passwords, 'cracked': True})

    return jsonify({'passwords': None, 'cracked': False})


# Handle termination signal from the master server
@minion.route('/master_done', methods=['POST'])
def master_done_handle():
    print('Master terminated - Exiting minion')
    os._exit(1)


if __name__ == '__main__':
    minion.run(debug=False, port=minion_port, threaded=True)

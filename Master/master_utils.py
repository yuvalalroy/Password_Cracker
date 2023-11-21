from typing import Dict

def validate_input_file_path(file_path):
    if file_path is None:
        raise ValueError('Please provide a file path as a command-line argument.')

def read_from_file(file_path):
    try:
        if file_path:
            with open(file_path, 'r') as file:
                lines_list = [line.strip() for line in file.readlines()]
            if not lines_list:
                raise ValueError(f"Error: File '{file_path}' is empty.")
            return lines_list

    except FileNotFoundError:
        raise ValueError(f'File not found: {file_path}')

    except IOError as e:
        raise ValueError(f'Error reading the file: {e}')

def write_to_file(output : Dict[str, str], file_name):
    output_file_path = f'{file_name}.txt'
    try:
        with open(output_file_path, 'w') as file:
            for key, value in output.items():
                if value is not None:
                    file.write(f'{key}: {value}\n')

        print(f'Results written to {output_file_path}')

    except IOError as e:
        raise ValueError(f'Error writing to the file: {e}')

def validate_input_port(str_port):
        try:
            port = int(str_port)
        except (ValueError, TypeError):
            raise ValueError('Error: Invalid port number.')

        return port


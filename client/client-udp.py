import socket, struct, sys, os, time
from sys import argv

# Usage: python3 client-udp.py 127.0.0.1 2121 1024 -n

def correct_usage_parameters_message():
    if len(argv) != 5:
        print("Usage: python3 client-udp.py <IP> <PORT> <BUFFER_SIZE> [-q <quiet_mode> -n <not_quiet_mode>]")
        exit(1)

def create_socket():
    try:
        UDP_IP = argv[1]
        UDP_PORT = int(argv[2])
        BUFFER_SIZE = int(argv[3])
        QUIET_MODE = argv[4]
        server_address = (UDP_IP, UDP_PORT)

        soc = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        print("Connection successful!")

    except socket.error as e:
        print(f"Connection unsuccessful. Error: {e}")
        exit(1)
    except OSError:
        print("Error: Address already in use. Please try another port.")
        exit(98)
    except KeyboardInterrupt:
        print("Client interrupted by user.")
        exit(1)
    except NameError as e:
        print(f"Error: {e}")
        exit(1)
    except ValueError as e:
        print("Error: Port must be an integer.")
        exit(1)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        exit(1)
    return soc, server_address, BUFFER_SIZE, QUIET_MODE

def store_file_to_server(soc, server_addr, buffer_size, command, file_name, quiet_mode):
    if quiet_mode == "-q":
        sys.stdout = open(os.devnull, 'w')
        sys.stderr = open(os.devnull, 'w')

    if not os.path.exists(file_name):
        print("\nFile does not exist.")
        return

    try:
        soc.sendto(command.encode('utf-8'), server_addr)
        soc.sendto(file_name.encode('utf-8'), server_addr)
        response, _ = soc.recvfrom(buffer_size)
        if response != b"1":
            print("\nError: Server did not acknowledge file name.")
            return

        file_size = os.path.getsize(file_name)
        soc.sendto(struct.pack("i", file_size), server_addr)

        with open(file_name, "rb") as f:
            bytes_sent = 0
            while bytes_sent < file_size:
                data = f.read(buffer_size)
                soc.sendto(data, server_addr)
                bytes_sent += len(data)
        print("\n\tFile stored successfully.")
    except Exception as e:
        print(f"\nError storing file: {e}")
        return

    try:
        # Get performance details from server
        time_elapsed = struct.unpack("f", soc.recv(4))[0]
        print(f"\nTime elapsed: {time_elapsed}s\nFile size: {file_size} bytes")
    except Exception as e:
        print(f"\nError retrieving performance details: {e}")
    finally:
        # Restore stdout and stderr
        if quiet_mode == "-q":
            sys.stdout = sys.__stdout__
            sys.stderr = sys.__stderr__
    return

def retrieve_file_from_server(soc, server_addr, buffer_size, command, file_name, quiet_mode):
    if quiet_mode == "-q":
        sys.stdout = open(os.devnull, 'w')
        sys.stderr = open(os.devnull, 'w')

    try:
        soc.sendto(command.encode('utf-8'), server_addr)
        soc.sendto(file_name.encode('utf-8'), server_addr)
        response, _ = soc.recvfrom(buffer_size)
        if response != b"1":
            print("\nError: File not found on server.")
            return

        file_size, _ = soc.recvfrom(4)
        file_size = struct.unpack("i", file_size)[0]

        with open(file_name, "wb") as f:
            bytes_received = 0
            while bytes_received < file_size:
                data, _ = soc.recvfrom(buffer_size)
                f.write(data)
                bytes_received += len(data)
        print(f"\n\tSuccessfully downloaded {file_name}")
    except Exception as e:
        print(f"\nError retrieving file: {e}")
        return
    
    try:
        # Get performance details from server
        time_elapsed = struct.unpack("f", soc.recv(4))[0]
        print(f"\nTime elapsed: {time_elapsed}s\nFile size: {file_size} bytes")
    except Exception as e:
        print(f"\nError retrieving performance details: {e}")
    finally:
        # Restore stdout and stderr
        if quiet_mode == "-q":
            sys.stdout = sys.__stdout__
            sys.stderr = sys.__stderr__
    return

def list_files_from_server(soc, server_addr, buffer_size, command, quiet_mode):
    if quiet_mode == "-q":
        sys.stdout = open(os.devnull, 'w')
        sys.stderr = open(os.devnull, 'w')

    try:
        soc.sendto(command.encode('utf-8'), server_addr)
        data, _ = soc.recvfrom(buffer_size)
        print("\nFiles on server:\n")
        print(data.decode('utf-8'))
    except Exception as e:
        print(f"\nError listing files: {e}")
        return
    finally:
        # Restore stdout and stderr
        if quiet_mode == "-q":
            sys.stdout = sys.__stdout__
            sys.stderr = sys.__stderr__
    return

def delete_file_from_server(soc, server_addr, buffer_size, command, file_name, quiet_mode):
    if quiet_mode == "-q":
        sys.stdout = open(os.devnull, 'w')
        sys.stderr = open(os.devnull, 'w')

    try:
        # Confirm if user wants to delete file
        confirm_delete = input(f"\nAre you sure you want to delete '{file_name}'? (Y/N)\nCommand: ").upper()
        while confirm_delete not in ["Y", "y", "N", "n", "YES", "Yes", "yes", "NO", "No", "no"]:
            print("Command not recognized, try again")
            confirm_delete = input(f"\nAre you sure you want to delete '{file_name}'? (Y/N)\nCommand: ").upper()
    except KeyboardInterrupt:
        print("\nAction interrupted by user.")
        return
    except Exception as e:
        print(f"\nUnexpected error while confirming deletion status: {e}")
        return

    try:
        soc.sendto(command.encode('utf-8'), server_addr)
        soc.sendto(file_name.encode('utf-8'), server_addr)
        response, _ = soc.recvfrom(buffer_size)
        if response == b"1":
            print("\n\tFile deleted successfully.")
        else:
            print("\nError: File not found on server.")
            return
    except Exception as e:
        print(f"\nError deleting file: {e}")
        return
    
    try:
        # Get performance details from server
        time_elapsed = struct.unpack("f", soc.recv(4))[0]
        print(f"\nTime elapsed: {time_elapsed}s")
    except Exception as e:
        print(f"\nError retrieving performance details: {e}")
    finally:
        # Restore stdout and stderr
        if quiet_mode == "-q":
            sys.stdout = sys.__stdout__
            sys.stderr = sys.__stderr__
    return

def close_socket(soc, buffer_size, server_addr, command):
    try:
        soc.sendto(command.encode('utf-8'), server_addr)
        # Wait for server go-ahead
        soc.recv(buffer_size)
        soc.close()
        print("Client closed successfully.")
    except BrokenPipeError:
        print("\nClient socket not started or already closed.")
    except(OSError, socket.error):
        print("\nError closing server socket.")
    return

def clear_terminal():
    os.system('cls' if os.name == 'nt' else 'clear')
    return

def display_commands():
    # Display all commands
    print("\nAvailable Commands:")
    print("\n\tSTOR file_path       : Upload file")
    print("\tRETR file_path       : Download file")
    print("\tDEL file_path        : Delete file")
    print("\tLIST/LS              : List all files")
    print("\tSHOW/DISPLAY         : Display all commands")
    print("\tCLEAR                : Clear terminal")
    print("\tQUIT/EXIT/BYE        : Exit")
    return

def handle_client(soc, server_addr, buffer_size, quiet_mode):
    # Display all commands
    display_commands()

    try:
        choice = None
        while True:
            choice = input("\nEnter your command: ")

            if choice[:4].upper() == 'STOR':
                store_file_to_server(soc, server_addr, buffer_size, choice[:4], choice[4:].strip(), quiet_mode)
            elif choice[:4].upper() == 'RETR':
                retrieve_file_from_server(soc, server_addr, buffer_size, choice[:4], choice[4:].strip(), quiet_mode)
            elif choice[:3].upper() == 'DEL':
                delete_file_from_server(soc, server_addr, buffer_size, choice[:3], choice[3:].strip(), quiet_mode)
            elif choice[:4].upper() == 'LIST' or choice[:2].upper() == 'LS':
                list_files_from_server(soc, server_addr, buffer_size, choice, quiet_mode)
            elif choice[:4].upper() == 'SHOW' or choice[:7].upper() == 'DISPLAY':
                display_commands()
            elif choice[:5].upper() == 'CLEAR':
                clear_terminal()
            elif choice[:4].upper() == 'QUIT' or choice[:4].upper() == 'EXIT' or choice[:3].upper() == 'BYE':
                print("Client shutting down...")
                close_socket(soc, buffer_size, server_addr, choice)
                break
            else:
                print("Invalid choice. Please try again.")
    except KeyboardInterrupt:
        print("Client interrupted by user.")
        if(choice is not None):
            close_socket(soc, buffer_size, server_addr, choice)
        exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        if(choice is not None):
            close_socket(soc, buffer_size, server_addr, choice)
        exit(1)
    return

def main():
    # Check for correct usage of parameters
    correct_usage_parameters_message()

    # Create socket
    soc, server_address, buffer_size, quiet_mode = create_socket()

    print("\nWelcome to FTP Server!")
    
    # Handle client requests
    handle_client(soc, server_address, buffer_size, quiet_mode)
    return

if __name__ == "__main__":
    main()

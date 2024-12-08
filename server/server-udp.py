import socket, struct, sys, os, time
from sys import argv

# Usage: python3 server-udp.py 127.0.0.1 2121 1024 -q

def correct_usage_parameters_message():
    if len(argv) != 5:
        print("Usage: python3 server.py <IP> <PORT> <BUFFER_SIZE> [-q <quiet_mode> -n <not_quiet_mode>]")
        exit(1)

def create_socket():
    try:
        UDP_IP = argv[1]
        UDP_PORT = int(argv[2])
        BUFFER_SIZE = int(argv[3])
        server_addr = (UDP_IP, UDP_PORT)
        QUIET_MODE = argv[4]

        soc = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        soc.bind((server_addr))

    except socket.error as e:
        print(f"Connection unsuccessful. Error: {e}")
        exit(1)
    except OSError:
        print("Error: Address already in use. Please try another port.")
        exit(98)
    except KeyboardInterrupt:
        print("Server interrupted by user.")
        exit(1)
    except NameError as e:
        print(f"Error: {e}")
        exit(1)
    except ValueError as e:
        print("Error: Port and buffer size must be integers.")
        exit(1)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        exit(1)
    return soc, BUFFER_SIZE, QUIET_MODE

def store_file_to_server(soc, buffer_size, addr, quiet_mode):
    if quiet_mode == "-q":
        sys.stdout = open(os.devnull, 'w')
        sys.stderr = open(os.devnull, 'w')

    try:
        data, addr = soc.recvfrom(buffer_size)
        file_name = data.decode('utf-8')
        soc.sendto(b"1", addr)
    except socket.error:
        print("\nError to send confirmation message to client.")
        return

    try:
        file_size, addr = soc.recvfrom(4)
        file_size = struct.unpack("i", file_size)[0]
    except struct.error:
        print("\nError to unpack file size.")
        return
    except socket.error:
        print("\nError to receive file size.")
        return
    
    try:
        start_time = time.time()
        output_file = open(file_name, "wb")
        bytes_received = 0
        print("\nReceiving...")
        while bytes_received < file_size:
            data, addr = soc.recvfrom(buffer_size)
            output_file.write(data)
            bytes_received += len(data)
        output_file.close()
        print("\nReceived file: {}".format(file_name))
    except OSError:
        print("\nError writing file.")
        return
    except socket.error:
        print("\nError receiving file content from client.")
        return
    except Exception as e:
        print(f"\nUnexpected error receiving file content: {e}")
        return
    
    try:
        # Send download details to client
        soc.sendto(struct.pack("f", time.time() - start_time), addr)
    except(socket.error):
        print("\nError sending download details.")
    finally:
        # Restore stdout and stderr
        if quiet_mode == "-q":
            sys.stdout = sys.__stdout__
            sys.stderr = sys.__stderr__
    return

def retrieve_file_from_server(soc, buffer_size, addr, quiet_mode):
    if quiet_mode == "-q":
        sys.stdout = open(os.devnull, 'w')
        sys.stderr = open(os.devnull, 'w')

    try:
        data, addr = soc.recvfrom(buffer_size)
        file_name = data.decode('utf-8')
        if not os.path.exists(file_name):
            soc.sendto(b"0", addr)
            print("File not found.")
            return
        soc.sendto(b"1", addr)
    except socket.error:
        print("\nError to send confirmation message to client.")
        return

    try:
        file_size = os.path.getsize(file_name)
        soc.sendto(struct.pack("i", file_size), addr)
    except OSError:
        print("\nError getting file size.")
        return

    try:
        start_time = time.time()
        with open(file_name, "rb") as f:
            bytes_sent = 0
            while bytes_sent < file_size:
                data = f.read(buffer_size)
                soc.sendto(data, addr)
                bytes_sent += len(data)
        print("\nSent file: {}".format(file_name))
    except OSError:
        print("\nError reading file.")
    except socket.error:
        print("\nError sending file content to client.")
    except Exception as e:
        print(f"\nUnexpected error sending file content: {e}")

    try:
        # Send download details to client
        soc.sendto(struct.pack("f", time.time() - start_time), addr)
    except(socket.error):
        print("\nError sending download details.")
    finally:
        # Restore stdout and stderr
        if quiet_mode == "-q":
            sys.stdout = sys.__stdout__
            sys.stderr = sys.__stderr__
    return

def list_files_from_server(soc, addr, quiet_mode):
    if quiet_mode == "-q":
        sys.stdout = open(os.devnull, 'w')
        sys.stderr = open(os.devnull, 'w')

    try:
        files = os.listdir('.')
        total_directory_size = 0
        files_info = []
        size = 0

        for file in files:
            file_size = os.path.getsize(file)
            total_directory_size += file_size
            files_info.append(f"\t{file} - {file_size} bytes")
            size += 1

        files_list = "\n".join(files_info)
        files_list += f"\n\nTotal directory size: {total_directory_size} bytes\nTotal number of files: {size}"
        soc.sendto(files_list.encode('utf-8'), addr)
        print("Sent file list to client.")

    except OSError:
        print("\nError listing files.")
    except socket.error:
        print("\nError sending file list to client.")
    finally:
        # Restore stdout and stderr
        if quiet_mode == "-q":
            sys.stdout = sys.__stdout__
            sys.stderr = sys.__stderr__
    return

def delete_file_from_server(soc, addr, buffer_size, quiet_mode):
    if quiet_mode == "-q":
        sys.stdout = open(os.devnull, 'w')
        sys.stderr = open(os.devnull, 'w')

    try:
        start_time = time.time()
        data, addr = soc.recvfrom(buffer_size)
        file_name = data.decode('utf-8')
        if not os.path.exists(file_name):
            soc.sendto(b"0", addr)
            print("File not found.")
            return
        os.remove(file_name)
        soc.sendto(b"1", addr)
        print("Deleted file: {}".format(file_name))
    except OSError:
        print("\nError deleting file.")
        return
    except socket.error:
        print("\nError sending delete confirmation to client.")
        return
    
    try:
        # Send download details to client
        soc.sendto(struct.pack("f", time.time() - start_time), addr)
    except(socket.error):
        print("\nError sending download details.")
    finally:
        # Restore stdout and stderr
        if quiet_mode == "-q":
            sys.stdout = sys.__stdout__
            sys.stderr = sys.__stderr__
    return
    
def close_socket(soc, addr):
    try:
        # Send confirmation to client
        soc.sendto("Server closed successfully.".encode('utf-8'), addr)
        soc.close()
        print("Server closed successfully.")
    except BrokenPipeError:
        print("\nServer socket not started or already closed.")
    except(socket.error, OSError):
        print("\nError closing socket.")
    return

def handle_client(soc, buffer_size, quiet_mode):
    if quiet_mode == "-q":
        sys.stdout = open(os.devnull, 'w')
        sys.stderr = open(os.devnull, 'w')
    
    try:
        addr = None
        while True:
            choice, addr = soc.recvfrom(buffer_size)
            command = choice.decode('utf-8')

            if command.upper() == 'STOR':
                store_file_to_server(soc, buffer_size, addr, quiet_mode)
            elif command.upper() == 'RETR':
                retrieve_file_from_server(soc, buffer_size, addr, quiet_mode)
            elif command.upper() == 'LIST' or command.upper() == 'LS':
                list_files_from_server(soc, addr, quiet_mode)
            elif command.upper() == 'DEL':
                delete_file_from_server(soc, addr, buffer_size, quiet_mode)
            elif command.upper() == 'QUIT' or command.upper() == 'EXIT' or command.upper() == 'BYE':
                print("Server shutting down...")
                close_socket(soc, addr)
                break
            else:
                print("Unknown command received, try again.")
    except KeyboardInterrupt:
        print("\nServer interrupted by user.")
        if(addr is not None):
            close_socket(soc, addr)
        exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        if(addr is not None):
            close_socket(soc, addr)
        exit(1)
    finally:
        # Restore stdout and stderr
        if quiet_mode == "-q":
            sys.stdout = sys.__stdout__
            sys.stderr = sys.__stderr__
    return

def main():
    # Check for correct usage of parameters
    correct_usage_parameters_message()

    # Create socket
    soc, buffer_size, quiet_mode = create_socket()

    print("\nWelcome to FTP Server!\n")
    
    # Handle client requests
    handle_client(soc, buffer_size, quiet_mode)
    return

if __name__ == "__main__":
    main()

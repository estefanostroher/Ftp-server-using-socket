import socket, struct, sys, time, os
from sys import argv

def correct_usage_parameters_message():
    if len(argv) != 5:
        print("Usage: python3 server.py <IP> <PORT> <BUFFER_SIZE> [-q <quiet_mode> -n <not_quiet_mode>]")
        exit(1)

def create_socket_connection():
    try:
        # Set up server parameters
        TCP_IP = argv[1]
        TCP_PORT = int(argv[2])
        BUFFER_SIZE = int(argv[3])
        QUIET_MODE = argv[4]

        # Create a socket to listen for incoming connections
        soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Allow the socket to reuse the address in case it is in TIME_WAIT state
        soc.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        soc.bind((TCP_IP, TCP_PORT))
        soc.listen(1) # Disable when testing with multiple clients
        
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

def store_file_to_server(connect, buffer_size, quiet_mode):
    if quiet_mode == "-q":
        sys.stdout = open(os.devnull, 'w')
        sys.stderr = open(os.devnull, 'w')
    
    try:
        # Send message once server is ready to receive file details
        connect.send(b"1")

        # Receive file name length, then file name
        file_name_size = struct.unpack("h", connect.recv(2))[0]
        file_name = connect.recv(file_name_size).decode('utf-8')

    except struct.error:
        print("\nError to unpack file name size.")
        return
    except socket.error:
        print("\nError to send confirmation message or receive file name")
        return
    except Exception as e:
        print(f"\nErro inesperado ao receber o nome do arquivo: {e}")
        return
    
    try:
        # Send message to let client know server is ready for document content
        connect.send(b"1")

        # Receive file size
        file_size = struct.unpack("i", connect.recv(4))[0]

        # Initialize and enter loop to receive file content
        start_time = time.time()
        output_file = open(file_name, "wb")

        bytes_received = 0
        print("\nReceiving...")
        while bytes_received < file_size:
            data = connect.recv(buffer_size)
            output_file.write(data)
            bytes_received += len(data)
        output_file.close()
        print("\nReceived file: {}".format(file_name))

    except OSError:
        print("\nError writing file.")
        return
    except struct.error:
        print("\nError to unpack file size.")
        return
    except socket.error:
        print("\nError to send confirmation message to client or receiving file content from client.")
        return
    except Exception as e:
        print(f"\nUnexpected error receiving file content: {e}")
        return
    
    try:
        # Send upload performance details
        connect.send(struct.pack("f", time.time() - start_time))
        connect.send(struct.pack("i", file_size))
    except struct.error:
        print("\nError to send performance details (struct).")
    except socket.error:
        print("\nError to send performance details (socket).")
    except Exception as e:
        print(f"\nUnexpected error sending performance details: {e}")
    finally:
        # Restore stdout and stderr
        if quiet_mode == "-q":
            sys.stdout = sys.__stdout__
            sys.stderr = sys.__stderr__
    return

def list_files_from_server(connect, buffer_size, quiet_mode):
    if quiet_mode == "-q":
        sys.stdout = open(os.devnull, 'w')
        sys.stderr = open(os.devnull, 'w')
    
    print("Listing files...")
    
    try:
        # Get list of files in directory
        listing = os.listdir(os.getcwd())
        
        # Send number of files in directory
        connect.send(struct.pack("i", len(listing)))
        
        total_directory_size = 0
        count_files = 0
        for file in listing:
            file_name_size = len(file)
            
            # Send file name and size
            connect.send(struct.pack("i", file_name_size))
            connect.send(file.encode('utf-8'))
            
            # Send file content size
            file_size = os.path.getsize(file)
            connect.send(struct.pack("i", file_size))
            
            total_directory_size += file_size
            
            # Wait for client confirmation
            connect.recv(buffer_size)

            count_files += 1
        
        # Send total directory size
        connect.send(struct.pack("i", total_directory_size))
        
        # Send number of files in directory
        connect.send(struct.pack("i", count_files))
        
        # Wait for client confirmation
        connect.recv(buffer_size)
        print("\nSuccessfully sent file listing")
    except OSError as e:
        print(f"\nOS error when accessing directory or file: {e}")
    except struct.error as e:
        print(f"\nError packing/unpacking struct data: {e}")
    except socket.error as e:
        print(f"\nSocket error when sending data: {e}")
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")
    finally:
        # Restore stdout and stderr
        if quiet_mode == "-q":
            sys.stdout = sys.__stdout__
            sys.stderr = sys.__stderr__
    return

def retrieve_file_from_server(connect, buffer_size, quiet_mode):
    if quiet_mode == "-q":
        sys.stdout = open(os.devnull, 'w')
        sys.stderr = open(os.devnull, 'w')

    try:
        # Send initial confirmation to client
        connect.send(b"1")
    
        # Receive file name
        file_name_length = struct.unpack("h", connect.recv(2))[0]
        file_name = connect.recv(file_name_length).decode('utf-8')
    except(struct.error, socket.error):
        print("\nError sending initial confirmation to client or receiving file name.")
        return
    
    try:
        # Check if file exists
        if os.path.isfile(file_name):
            # If the file exists, send the file size
            connect.send(struct.pack("i", os.path.getsize(file_name)))
        else:
            # If the file doesn't exist, send -1
            print("\nFile name not valid")
            connect.send(struct.pack("i", -1))
            return
    except(OSError, struct.error, socket.error):
        print("\nError checking file existence or sending file size.")
        return
    
    try:
        # Wait for ok to send file
        connect.recv(buffer_size)
    
        # Enter loop to send file
        start_time = time.time()
        print("Sending file", file_name)
        with open(file_name, "rb") as content:
            while True:
                data = content.read(buffer_size)
                if not data:
                    break
                connect.send(data)
    except(OSError, socket.error):
        print("\nError receiving OK from client or reading/sending file data.")
        return
    
    try:
        # Get client go-ahead, then send download details
        connect.recv(buffer_size)
        connect.send(struct.pack("f", time.time() - start_time))
    except(struct.error, socket.error):
        print("\nError sending download details.")
    finally:
        # Restore stdout and stderr
        if quiet_mode == "-q":
            sys.stdout = sys.__stdout__
            sys.stderr = sys.__stderr__
    return

def delete_file_from_server(connect, buffer_size, quiet_mode):
    start_time = 0

    if quiet_mode == "-q":
        sys.stdout = open(os.devnull, 'w')
        sys.stderr = open(os.devnull, 'w')

    try:
        connect.send(b"1")  # Send go-ahead
    except socket.error:
        print("\nError sending go-ahead signal to client.")
        return
    
    try:
        # Receive file name
        file_name_length = struct.unpack("h", connect.recv(2))[0]
        file_name = connect.recv(file_name_length).decode('utf-8')
    except(struct.error, socket.error):
        print("\nError receiving file details.")
        return
    
    try:
        # Check if file exists
        if os.path.isfile(file_name):
            connect.send(struct.pack("i", 1))
        else:
            # File doesn't exist
            connect.send(struct.pack("i", -1))
    except(OSError, struct.error, socket.error):
        print("\nError checking file existence or sending file existence confirmation.")
        return

    try:
        # Receive confirmation to delete file
        confirm_delete = connect.recv(buffer_size).decode('utf-8')
        print("Received deletion confirmation: {}".format(confirm_delete))
        
        start_time = time.time()
        if confirm_delete == "Y":
            try:
                # Delete file
                os.remove(file_name)
                connect.send(struct.pack("i", 1))
            except OSError:
                # Error deleting file
                print("\nFailed to delete {}".format(file_name))
                connect.send(struct.pack("i", -1))
                return
        else:
            print("\nDelete abandoned by client!")
    except socket.error:
        print("\nError receiving deletion confirmation from client.")
        return

    try:
        # Get client go-ahead, then send download details
        connect.recv(buffer_size)
        connect.send(struct.pack("f", time.time() - start_time))
    except(struct.error, socket.error):
        print("\nError sending download details.")
    finally:
        # Restore stdout and stderr
        if quiet_mode == "-q":
            sys.stdout = sys.__stdout__
            sys.stderr = sys.__stderr__
    return

def close_connection(connect, soc):
    try:
        connect.send(b"1")
        connect.close()
        soc.close()
        print("Server connection closed.")
    except(socket.error, OSError):
        print("\nError closing connection.")
    return

def handle_client(connect, soc, buffer_size, quiet_mode):
    if quiet_mode == "-q":
        sys.stdout = open(os.devnull, 'w')
        sys.stderr = open(os.devnull, 'w')

    try:
        while True:
            data = connect.recv(buffer_size).decode('utf-8')
            print("\nReceived instruction: {}".format(data))

            if data == "STOR":
                store_file_to_server(connect, buffer_size, quiet_mode)
            elif data == "LIST" or data == "LS":
                list_files_from_server(connect, buffer_size, quiet_mode)
            elif data == "RETR":
                retrieve_file_from_server(connect, buffer_size, quiet_mode)
            elif data == "DEL":
                delete_file_from_server(connect, buffer_size, quiet_mode)
            elif data == "QUIT" or data == "EXIT" or data == "BYE":
                print("Server shutting down...")
                close_connection(connect, soc)
                break
            else:
                print("Command not recognized.")
            data = None # Reset data for next iteration
    except KeyboardInterrupt:
        print("\nServer interrupted by user.")
        close_connection(connect, soc)
        exit(1)
    except Exception as e:
        print(f"An error occurred: {e}")
        close_connection(connect, soc)
        exit(1)
    finally:
        # Restore stdout and stderr
        if quiet_mode == "-q":
            sys.stdout = sys.__stdout__
            sys.stderr = sys.__stderr__
    return

def main():
    try:
        # Check for correct usage of parameters
        correct_usage_parameters_message()

        soc = connect = None
        print("\nWelcome to FTP Server!\n")

        # Create socket connection
        soc, buffer_size, quiet_mode = create_socket_connection()

        # Accept incoming connection
        connect, addr = soc.accept()
        print("Connected to by address: {}".format(addr))

        # Send buffer size to client as an integer in network byte order
        connect.send(struct.pack("i", buffer_size))

        # Handle client requests
        handle_client(connect, soc, buffer_size, quiet_mode)

    except KeyboardInterrupt:
        print("\nServer interrupted by user.")
        if(connect is not None):
            close_connection(connect, soc)
        exit(1)
    except Exception as e:
        print(f"An error occurred: {e}")
        if(connect is not None):
            close_connection(connect, soc)
        exit(1)
    return

if __name__ == "__main__":
    main()

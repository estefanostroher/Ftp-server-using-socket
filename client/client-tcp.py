import socket, struct, sys, os, time
from sys import argv

def correct_usage_parameters_message():
    if len(argv) != 4:
        print("Usage: python3 client.py <IP> <PORT> [-q <quiet_mode> -n <not_quiet_mode>]")
        exit(1)

def create_socket_connection():
    try:
        # Set up server parameters
        TCP_IP = argv[1]
        TCP_PORT = int(argv[2])
        QUIET_MODE = argv[3]

        # Create a socket to listen for incoming connections
        soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Allow the socket to reuse the address in case it is in TIME_WAIT state
        soc.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # Set a timeout of 10 seconds for blocking socket operations to avoid indefinite waiting
        soc.settimeout(10)

        # Connect to the server
        soc.connect((TCP_IP, TCP_PORT))
        print("Connection successful!")

        # Get buffer size from server
        buffer_size = struct.unpack("i", soc.recv(4))[0]

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
        print("Error: Port size must be integer.")
        exit(1)
    except struct.error as e:
        print(f"Error unpacking buffer size: {e}")
        exit(1)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        exit(1)
    return soc, buffer_size, QUIET_MODE

def store_file_to_server(soc, buffer_size, command, file_name, quiet_mode):
    if quiet_mode == "-q":
        sys.stdout = open(os.devnull, 'w')
        sys.stderr = open(os.devnull, 'w')

    # Upload a file
    print(f"\nUploading file: {file_name}")

    try:
        # Check if the file exists
        content = open(file_name, "rb")

        # Make upload request
        soc.send(command.encode('utf-8'))

        # Wait for server acknowledgement then send file details, Wait for server ok
        soc.recv(buffer_size)

        # Send file name and size
        soc.send(struct.pack("h", len(file_name)))
        soc.send(file_name.encode())

        # Wait for server ok then send file size
        soc.recv(buffer_size)
        soc.send(struct.pack("i", os.path.getsize(file_name)))

        # Send the file in chunks defined by BUFFER_SIZE
        chunks = content.read(buffer_size)
        print("Sending...\n")
        while chunks:
            soc.send(chunks)
            chunks = content.read(buffer_size)
        content.close()

        # Get upload performance details
        upload_time = struct.unpack("f", soc.recv(4))[0]
        upload_size = struct.unpack("i", soc.recv(4))[0]
        print(f"\tSent file: {file_name}\n\nTime elapsed: {upload_time}s\nFile size: {upload_size} bytes")

    except FileNotFoundError:
        print("\nFile not found. Make sure the file name was entered correctly.")
    except socket.error as e:
        print(f"\nSocket error: {e}")
    except struct.error as e:
        print(f"\nStruct packing/unpacking error: {e}")
    except OSError as e:
        print(f"\nOS error: {e}")
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")
    finally:
        # Restore stdout and stderr
        if quiet_mode == "-q":
            sys.stdout = sys.__stdout__
            sys.stderr = sys.__stderr__
    return

def list_files_from_server(soc, command, quiet_mode):
    if quiet_mode == "-q":
        sys.stdout = open(os.devnull, 'w')
        sys.stderr = open(os.devnull, 'w')

    # List the files available on the file server side
    print("\nFiles on server:\n")

    try:
        # Send list request
        soc.send(command.encode('utf-8'))
    except socket.error:
        print("\nCouldn't make server request. Make sure a connection has been established.")
        return
    except Exception as e:
        print(f"\nUnexpected error during server request: {e}")
        return
    
    try:
        # First get the number of files in the directory
        number_of_files = struct.unpack("i", soc.recv(4))[0]

        # Then enter into a loop to receive details of each, one by one
        for _ in range(int(number_of_files)):
            # Get the file name and size first to slightly lessen amount transferred over socket
            file_name_size = struct.unpack("i", soc.recv(4))[0]
            file_name = soc.recv(file_name_size).decode()

            # Also get the file size for each item in the server
            file_size = struct.unpack("i", soc.recv(4))[0]
            print(f"\t{file_name} - {file_size} bytes")

            # Make sure that the client and server are synchronized
            soc.send("1".encode())

        # Get total size of directory
        total_directory_size = struct.unpack("i", soc.recv(4))[0]

        # Get total number of files in the directory
        count_files = struct.unpack("i", soc.recv(4))[0]

        print(f"\nTotal directory size: {total_directory_size} bytes\nTotal number of files: {count_files}")
    except struct.error:
        print("\nError unpacking struct data. Data may be corrupted or incomplete.")
        return
    except socket.error:
        print("\nSocket error occurred while receiving file list.")
        return
    except UnicodeDecodeError:
        print("\nError decoding file name. Data encoding may not match.")
        return
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")
        return
    
    try:
        # Final check
        soc.send("1".encode())
    except(socket.error, Exception):
        print("\nCouldn't get final server confirmation")
    finally:
        # Restore stdout and stderr
        if quiet_mode == "-q":
            sys.stdout = sys.__stdout__
            sys.stderr = sys.__stderr__
    return

def retrieve_file_from_server(soc, buffer_size, command, file_name, quiet_mode):
    if quiet_mode == "-q":
        sys.stdout = open(os.devnull, 'w')
        sys.stderr = open(os.devnull, 'w')

    # Download given file
    print(f"Downloading file: {file_name}")
    
    try:
        # Send request to server
        soc.send(command.encode('utf-8'))

        # Wait for server ok, send file name length then name
        soc.recv(buffer_size)
        soc.send(struct.pack("h", len(file_name)))
        soc.send(file_name.encode())

        # Get file size (if exists)
        file_size = struct.unpack("i", soc.recv(4))[0]
        if file_size == -1:
            # If file size is -1, the file does not exist
            print("File does not exist. Make sure the name was entered correctly")
            return
    except struct.error:
        print("Error unpacking struct data. Possible data corruption.")
        return
    except socket.error:
        print("Socket error while verifying file.")
        return
    except Exception as e:
        print(f"Unexpected error while checking file: {e}")
        return

    try:
        # Send ok to receive file content
        soc.send("1".encode())

        # Enter loop to receive file
        output_file = open(file_name, "wb")

        bytes_received = 0

        print("\nDownloading...\n")
        # Receive file in chunks defined by BUFFER_SIZE
        while bytes_received < file_size:
            chunks = soc.recv(buffer_size)
            output_file.write(chunks)
            bytes_received += len(chunks)
        output_file.close()

        print(f"\tSuccessfully downloaded {file_name}")

        # Tell the server that the client is ready to receive the download performance details
        soc.send("1".encode())

        # Get performance details
        time_elapsed = struct.unpack("f", soc.recv(4))[0]
        print(f"\nTime elapsed: {time_elapsed}s\nFile size: {file_size} bytes")
    except struct.error:
        print("Error unpacking struct data for performance details.")
    except socket.error:
        print("Socket error occurred during file download.")
    except IOError:
        print("Error writing to file.")
    except Exception as e:
        print(f"Unexpected error while downloading file: {e}")
    finally:
        # Restore stdout and stderr
        if quiet_mode == "-q":
            sys.stdout = sys.__stdout__
            sys.stderr = sys.__stderr__
    return

def delete_file_from_server(soc, buffer_size, command, file_name, quiet_mode):
    if quiet_mode == "-q":
        sys.stdout = open(os.devnull, 'w')
        sys.stderr = open(os.devnull, 'w')
        
    # Delete specified file from file server
    print(f"\nDeleting file: {file_name}")

    try:
        # Send request, then wait for go-ahead
        soc.send(command.encode('utf-8'))
        soc.recv(buffer_size)
    except socket.error:
        print("\nCouldn't connect to server. Make sure a connection has been established.")
        return
    except Exception as e:
        print(f"\nUnexpected error during server request: {e}")
        return

    try:
        # Send file length, then file name
        soc.send(struct.pack("h", len(file_name)))
        soc.send(file_name.encode())
    except struct.error:
        print("\nError packing or sending file details.")
        return
    except socket.error:
        print("\nSocket error while sending file details.")
        return
    except Exception as e:
        print(f"\nUnexpected error sending file details: {e}")
        return    

    try:
        # Get confirmation that file does/doesn't exist
        file_exists = struct.unpack("i", soc.recv(4))[0]
        if file_exists == -1:
            print("\nThe file does not exist on the server")
            return
    except struct.error:
        print("\nError unpacking data. Possible data corruption.")
        return
    except socket.error:
        print("\nSocket error occurred while checking file existence.")
        return
    except Exception as e:
        print(f"\nUnexpected error while checking file existence: {e}")
        return

    try:
        # Confirm user wants to delete file
        confirm_delete = input(f"\nAre you sure you want to delete '{file_name}'? (Y/N)\nCommand: ").upper()
        while confirm_delete not in ["Y", "y", "N", "n", "YES", "yes", "NO", "no"]:
            print("Command not recognized, try again")
            confirm_delete = input(f"\nAre you sure you want to delete '{file_name}'? (Y/N)\nCommand: ").upper()
    except KeyboardInterrupt:
        print("Action interrupted by user.")
        return
    except Exception as e:
        print(f"\nUnexpected error while confirming deletion status: {e}")
        return

    try:
        # Send confirmation
        if confirm_delete in ["Y", "y", "YES", "yes"]:
            soc.send("Y".encode())
            delete_status = struct.unpack("i", soc.recv(4))[0]
            if delete_status == 1:
                print("\n\tFile successfully deleted!")
            else:
                print("\nFile failed to delete")
        else:
            soc.send("N".encode())
            print("Delete abandoned by user!")
    except struct.error:
        print("\nError unpacking deletion status.")
        return
    except socket.error:
        print("\nSocket error occurred during deletion process.")
        return
    except Exception as e:
        print(f"\nUnexpected error during file deletion: {e}")
        return

    try:
        # Tell the server that the client is ready to receive the download performance details
        soc.send("1".encode())

        # Get performance details
        time_elapsed = struct.unpack("f", soc.recv(4))[0]
        print(f"\nTime elapsed: {time_elapsed}s")
    except(struct.error, socket.error):
        print("\nError occurred while receiving performance details.")
    except Exception as e:
        print(f"\nUnexpected error while receiving performance details: {e}")
    finally:
        # Restore stdout and stderr
        if quiet_mode == "-q":
            sys.stdout = sys.__stdout__
            sys.stderr = sys.__stderr__
    return

def close_connection(soc, command, buffer_size):
    try:
        soc.send(command.encode('utf-8'))
        # Wait for server go-ahead
        soc.recv(buffer_size)
        soc.close()
        print("Client connection ended.")
    except BrokenPipeError:
        print("\nServer connection not started or already closed.")
    except(OSError, socket.error):
        print("\nError closing server connection.")
    except Exception as e:
        print(f"\nUnexpected error while closing connection: {e}")
    return 

def clear_terminal():
    os.system('cls' if os.name == 'nt' else 'clear')
    return

def display_commands():
    # Display all commands
    print("\nAvailable Commands:")
    print("\n\tSTOR filename     : Upload file")
    print("\tRETR filename       : Download file")
    print("\tDEL filename        : Delete file")
    print("\tLIST/LS              : List all files")
    print("\tSHOW/DISPLAY         : Display all commands")
    print("\tCLEAR                : Clear terminal")
    print("\tQUIT/EXIT/BYE        : Exit")
    return

def handle_client(soc, buffer_size, quiet_mode):   
    # Display all commands
    display_commands()
    
    try:
        choice = None
        while True:
            choice = input("\nEnter a command: ")
            if choice[:4].upper() == "STOR":
                store_file_to_server(soc, buffer_size, choice[:4].upper(), choice[4:].strip(), quiet_mode)
            elif choice[:4].upper() == "LIST" or choice[:2].upper() == "LS":
                list_files_from_server(soc, choice.upper(), quiet_mode)
            elif choice[:4].upper() == "RETR":
                retrieve_file_from_server(soc, buffer_size, choice[:4].upper(), choice[4:].strip(), quiet_mode)
            elif choice[:3].upper() == "DEL":
                delete_file_from_server(soc, buffer_size, choice[:3].upper(), choice[3:].strip(), quiet_mode)
            elif choice[:4].upper() == "SHOW" or choice[:7].upper() == "DISPLAY":
                display_commands()
            elif choice[:5].upper() == "CLEAR":
                clear_terminal()
            elif choice[:4].upper() == "QUIT" or choice[:4].upper() == "EXIT" or choice[:3].upper() == "BYE":
                print("Client shutting down...")
                close_connection(soc, choice.upper(), buffer_size)
                break
            else:
                print("Command not recognized, try again.")
    except KeyboardInterrupt:
        print("\nClient interrupted by user.")
        if(choice is not None):
            close_connection(soc, choice.upper(), buffer_size)
        exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        if(choice is not None):
            close_connection(soc, choice.upper(), buffer_size)
        exit(1)
    return

def main():
    # Check for correct usage of parameters
    correct_usage_parameters_message()

    # Create socket connection
    soc, buffer_size, quiet_mode = create_socket_connection()
        
    print("\nWelcome to FTP Server!\n")

    # Handle client requests
    handle_client(soc, buffer_size, quiet_mode)
    return

if __name__ == "__main__":
    main()

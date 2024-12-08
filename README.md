# Ftp-server-using-socket
Simulated FTP client-server using sockets via TCP/UDP

## Requirements

- **Python3+**: The application was developed in Python3 and may not be compatible with earlier versions.

## Usage Instructions

### Running the Server

#### TCP Server

In the terminal, navigate to the directory where the 

server-tcp.py

 file is located and execute:

```bash
python3 server-tcp.py <IP> <PORT> <BUFFER_SIZE> [-q|-n]
```

- `<IP>`: IP address on which the server will listen (e.g., `127.0.0.1`).
- `<PORT>`: Port on which the server will listen (e.g., `2121`).
- `<BUFFER_SIZE>`: Buffer size for data transfer (e.g., `1024`).
- `-q` or `-n`: Quiet mode (`-q`) or verbose mode (`-n`).

#### UDP Server

Run the UDP server with:

```bash
python3 server-udp.py <IP> <PORT> <BUFFER_SIZE> [-q|-n]
```

The parameters are the same as those for the TCP server.

### Running the Client

#### TCP Client

In the terminal, run the TCP client with:

```bash
python3 client-tcp.py <IP> <PORT> [-q|-n]
```

- `<IP>`: IP address of the server to which the client will connect.
- `<PORT>`: Server port.
- `-q` or `-n`: Quiet mode (`-q`) or verbose mode (`-n`).

#### UDP Client

Run the UDP client with:

```bash
python3 client-udp.py <IP> <PORT> [-q|-n]
```

- `<IP>`: IP address of the server to which the client will connect.
- `<PORT>`: Server port.
- `<BUFFER_SIZE>`: Buffer size for data transfer (e.g., `1024`).
- `-q` or `-n`: Quiet mode (`-q`) or verbose mode (`-n`).

## Available Commands

After connecting, you can use the following commands in the client:

- `STOR <filename>`: Upload a file to the server.
- `RETR <filename>`: Download a file from the server.
- `DEL <filename>`: Delete a file on the server.
- `LIST` or `LS`: List all files available on the server, including their sizes and the total directory size.
- `SHOW` or `DISPLAY`: Show all available commands.
- `CLEAR`: Clear the terminal.
- `QUIT`, `EXIT`, or `BYE`: Close the connection with the server.

**Note**: Replace `<filename>` with the name of the file you wish to manipulate.

## Usage Example

### Starting the TCP Server

```bash
python3 server-tcp.py 127.0.0.1 2121 1024 -n
```

### Connecting the TCP Client

```bash
python3 client-tcp.py 127.0.0.1 2121 -n
```

After connecting, you can type commands like:

```bash
Enter a command: STOR example.txt
Enter a command: LIST
Enter a command: RETR example.txt
Enter a command: DEL example.txt
Enter a command: QUIT
```

## Considerations about TCP and UDP

- **TCP**:
  - Connection-oriented: Ensures packets are delivered in the correct order.
  - Recommended when reliability is critical.
  - More suitable for file transfers where data integrity is essential.

- **UDP**:
  - Connectionless: Does not guarantee delivery or order of packets.
  - Recommended for applications where performance is more critical than reliability.
  - Suitable for real-time audio/video transmissions or online games.

## Conclusion

Feel free to use and modify the code as you wish, whether for college or personal projects.

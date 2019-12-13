# password-server
A simple http sever that protected others from access data directly.

- It is **not** a secure server
- It is not for commercial usage

# What does the server do?
- **python** provides simple http server which can **access files** under the data directory.
```bash
python3 -m http.server [port num]
```
- **password-server** requires password before access the files.
  - An allowed ip can access direcly.
  - An ip would be banned if it attemps to login more than 3 times.
  
# Usage
```bash
python3 password_server.py [port num] --dir [the directory to show files]
```

# Requirements
- **Python 3.6+**

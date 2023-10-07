![Image](https://i.imgur.com/KvVY2G6.png)
# SMBguy for Windows

This program provides a graphical user interface (GUI) to facilitate the mounting and unmounting of SMB shares on Windows drive letters. It is designed to simplify the management of network resources by allowing administrators and users to easily switch between different servers and users. The program also allows for pre-configuring a list of available servers for quick access.

## Features
- Simplified mounting and unmounting of SMB shares.
- Manage switching between different servers, and users.
- Pre-configured server list for quick access.
- Intuitive user interface based on PyQt5.
- Powerfull OS integration via Windows APIs through [pywin32](https://pypi.org/project/pywin32/)

        
## Installation

1. Download last release from [here](https://github.com/Redcat468/SMBguy/releases)
2. Run setup.exe

### Installation and usage from sources

```
pip install PyQt5 pywin32
```

#### Usage
Run main.py to start the application.
Follow the on-screen instructions to mount or unmount SMB shares.

## Screenshots

### login window 

![Image](https://i.imgur.com/ZDZq8ap.png)

### Shares window 

![Image](https://imgur.com/WJE5gFu.png)

### Server list editor

![Image](https://imgur.com/pxqPoII.png)


## Contributing
Pull Requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.


        

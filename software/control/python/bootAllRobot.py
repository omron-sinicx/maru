import sys
from maru import osx001Driver
from serial.tools import list_ports

def main():
    args = sys.argv

    # Exit if no serial port specified
    if len(args) < 2:
        ports = list_ports.comports()
        devices = [info.device for info in ports]
        print("Specify serial port\r\n")
        print("e.g., python bootAllRobot.py COM3\r\n")
        print("Port List : \r\n")
        for port in ports:
            print(port)
        sys.exit(0)

    # initialization
    driver = osx001Driver(args[1])

    driver.bootAllRobot()

if __name__ == '__main__':
    main()

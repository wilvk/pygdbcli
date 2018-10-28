#https://eli.thegreenplace.net/2017/interacting-with-a-long-running-child-process-in-python/

import subprocess
import time
import io
import os
import fcntl

def read_stdout(proc):
    while proc.poll() is None:
        l = proc.stdout.readline()
        if len(l) == 0:
            break
        print(l)

def write_read_stdout(proc, input_command):
    stdout_data = proc.communicate(input=input_command.encode())[0]
    print("result: " + str(stdout_data))

def main():
    command = 'gdb'
    args = ['ls']
    command_line = [command] + args
    proc = subprocess.Popen(command_line, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    fcntl.fcntl(proc.stdout, fcntl.F_SETFL, os.O_NONBLOCK)
    fcntl.fcntl(proc.stderr, fcntl.F_SETFL, os.O_NONBLOCK)

    time.sleep(1)

    read_stdout(proc)
    write_read_stdout(proc, "info")
    time.sleep(1)

    proc.terminate()


if __name__ == "__main__":
        main()

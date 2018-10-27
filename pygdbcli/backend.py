#!/usr/bin/env python3

"""
The entrypoint to accessing gdb/gdbserver
"""

import argparse
import binascii
from distutils.spawn import find_executable
from functools import wraps
import json
import logging
import os
import platform
import pygdbmi
from pygments.lexers import get_lexer_for_filename
from pygdbmi.gdbcontroller import NoGdbProcessError
import re
import signal
import shlex
import sys
import socket
import traceback

USING_WINDOWS = os.name == "nt"
IS_A_TTY = sys.stdout.isatty()
DEFAULT_GDB_EXECUTABLE = "gdb"
GDB_PATH = '/usr/local/bin/gdb'
GDB_ARGS = ''

logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)

handler = logging.StreamHandler()
logger.addHandler(handler)

# create dictionary of signal names
SIGNAL_NAME_TO_OBJ = {}
for n in dir(signal):
    if n.startswith("SIG") and "_" not in n:
        SIGNAL_NAME_TO_OBJ[n.upper()] = getattr(signal, n)

def verify_gdb_exists(gdb_path):
    if find_executable(gdb_path) is None:
        pygdbmi.printcolor.print_red(
            'gdb executable "%s" was not found. Verify the executable exists, or that it is a directory on your $PATH environment variable.'
            % gdb_path
        )
        if USING_WINDOWS:
            print(
                'Install gdb (package name "mingw32-gdb") using MinGW (https://sourceforge.net/projects/mingw/files/Installer/mingw-get-setup.exe/download), then ensure gdb is on your "Path" environement variable: Control Panel > System Properties > Environment Variables > System Variables > Path'
            )
        else:
            print('try "sudo apt-get install gdb" for Linux or "brew install gdb"')
        sys.exit(1)
    elif "lldb" in gdb_path.lower() and "lldb-mi" not in GDB_PATH.lower():
        pygdbmi.printcolor.print_red(
            'gdbgui cannot use the standard lldb executable. You must use an executable with "lldb-mi" in its name.'
        )
        sys.exit(1)

def run_gdb_command(message):
    """
    Endpoint for a websocket route.
    Runs a gdb command.
    Responds only if an error occurs when trying to write the command to
    gdb
    """
    controller = _state.get_controller_from_client_id(request.sid)
    if controller is not None:
        try:
            # the command (string) or commands (list) to run
            cmd = message["cmd"]
            controller.write(cmd, read_response=False)

        except Exception:
            err = traceback.format_exc()
            logger.error(err)
            emit("error_running_gdb_command", {"message": err})
    else:
        emit("error_running_gdb_command", {"message": "gdb is not running"})


def remove_gdb_controller():
    gdbpid = int(request.form.get("gdbpid"))

    orphaned_client_ids = _state.remove_gdb_controller_by_pid(gdbpid)
    num_removed = len(orphaned_client_ids)

    send_msg_to_clients(
        orphaned_client_ids,
        "The underlying gdb process has been killed. This tab will no longer function as expected.",
        error=True,
    )

    msg = "removed %d gdb controller(s) with pid %d" % (num_removed, gdbpid)
    if num_removed:
        return jsonify({"message": msg})

    else:
        return jsonify({"message": msg}), 500


def read_and_forward_gdb_output():
    """A task that runs on a different thread, and emits websocket messages
    of gdb responses"""

    while True:
        socketio.sleep(0.05)
        controllers_to_remove = []
        controller_items = _state.controller_to_client_ids.items()
        for controller, client_ids in controller_items:
            try:
                try:
                    response = controller.get_gdb_response(
                        timeout_sec=0, raise_error_on_timeout=False
                    )
                except NoGdbProcessError:
                    response = None
                    send_msg_to_clients(
                        client_ids,
                        "The underlying gdb process has been killed. This tab will no longer function as expected.",
                        error=True,
                    )
                    controllers_to_remove.append(controller)

                if response:
                    for client_id in client_ids:
                        logger.info(
                            "emiting message to websocket client id " + client_id
                        )
                        socketio.emit(
                            "gdb_response",
                            response,
                            namespace="/gdb_listener",
                            room=client_id,
                        )
                else:
                    # there was no queued response from gdb, not a problem
                    pass

            except Exception:
                logger.error(traceback.format_exc())

        for controller in controllers_to_remove:
            _state.remove_gdb_controller(controller)

def send_signal_to_pid():
    signal_name = request.form.get("signal_name", "").upper()
    pid_str = str(request.form.get("pid"))
    try:
        pid_int = int(pid_str)
    except ValueError:
        return (
            jsonify(
                {
                    "message": "The pid %s cannot be converted to an integer. Signal %s was not sent."
                    % (pid_str, signal_name)
                }
            ),
            400,
        )

    if signal_name not in SIGNAL_NAME_TO_OBJ:
        raise ValueError("no such signal %s" % signal_name)
    signal_value = int(SIGNAL_NAME_TO_OBJ[signal_name])

    try:
        os.kill(pid_int, signal_value)
    except Exception:
        return (
            jsonify(
                {
                    "message": "Process could not be killed. Is %s an active PID?"
                    % pid_int
                }
            ),
            400,
        )
    return jsonify(
        {
            "message": "sent signal %s (%s) to process id %s"
            % (signal_name, signal_value, pid_str)
        }
    )

def _shutdown():
    try:
        _state.exit_all_gdb_processes()
    except Exception:
        logger.error("failed to exit gdb subprocces")
        logger.error(traceback.format_exc())

    pid = os.getpid()
    if app.debug:
        os.kill(pid, signal.SIGINT)
    else:
        socketio.stop()

    return jsonify({})

def main():
    """Entry point from command line"""

    verify_gdb_exists(GDB_PATH)

    if warn_startup_with_shell_off(platform.platform().lower(), GDB_ARGS):
        logger.warning(
            "You may need to set startup-with-shell off when running on a mac. i.e.\n"
            "  gdbgui --gdb-args='--init-eval-command=\"set startup-with-shell off\"'\n"
            "see http://stackoverflow.com/questions/39702871/gdb-kind-of-doesnt-work-on-macos-sierra\n"
            "and https://sourceware.org/gdb/onlinedocs/gdb/Starting.html"
        )

def warn_startup_with_shell_off(platform, gdb_args):
    """return True if user may need to turn shell off
    if mac OS version is 16 (sierra) or higher, may need to set shell off due
    to os's security requirements
    http://stackoverflow.com/questions/39702871/gdb-kind-of-doesnt-work-on-macos-sierra
    """
    darwin_match = re.match("darwin-(\d+)\..*", platform)
    on_darwin = darwin_match is not None and int(darwin_match.groups()[0]) >= 16
    if on_darwin:
        shell_is_off = "startup-with-shell off" in gdb_args
        return not shell_is_off
    return False


if __name__ == "__main__":
    main()

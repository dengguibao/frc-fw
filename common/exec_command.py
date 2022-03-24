import subprocess


class CommandExecTimout(Exception):
    pass


class CommandExecNotSuccess(Exception):
    pass


def send_command(*arguments, out=False, timeout=5):
    try:
        ret = subprocess.run(
            arguments, universal_newlines=True, shell=False, timeout=timeout,
            stderr=subprocess.PIPE,
            stdout=subprocess.PIPE, stdin=subprocess.PIPE
        )

    except subprocess.TimeoutExpired:
        raise CommandExecTimout('command exec timeout!')

    if ret.returncode == 0:
        if out:
            return ret.stdout
        return True
        # CommandExecNotSuccess(process.stderr.read().decode())

    return False

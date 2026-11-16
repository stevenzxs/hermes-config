"""Stream native output without PowerShell 5.1 stderr/ErrorRecord conversion."""
import subprocess
import sys


def main():
    log_path, *command = sys.argv[1:]
    with open(log_path, 'wb') as log:
        with subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT) as child:
            for line in child.stdout:
                log.write(line)
                log.flush()
                sys.stdout.buffer.write(line)
                sys.stdout.buffer.flush()
            return child.wait()


if __name__ == '__main__':
    raise SystemExit(main())

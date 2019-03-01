import os
import subprocess
import tempfile
import pexpect

def ssh(command, password, timeout=30, bg_run=False):
    """SSH'es to a host using the supplied credentials and executes a command.
    Throws an exception if the command doesn't return 0.
    bgrun: run command in the background"""

    fname = tempfile.mktemp()
    fout = open(fname, 'w')

    # options = '-q -oStrictHostKeyChecking=no -oUserKnownHostsFile=/dev/null -oPubkeyAuthentication=no'
    # if bg_run:
    #     options += ' -f'
    # ssh_cmd = 'ssh %s@%s %s "%s"' % ('aaron', '132.239.20.173', options, '.')
    child = pexpect.spawn("")
    child.expect(['password: '])
    child.sendline(password)
    child.logfile = fout
    child.expect(pexpect.EOF)
    child.close()
    fout.close()

    fin = open(fname, 'r')
    stdout = fin.read()
    fin.close()

    if 0 != child.exitstatus:
        raise Exception(stdout)

    return stdout

ssh('scp aaron@132.239.20.173:/home/aaron/catkin_ws/src/SyncTemplate/scripts/counter.py .',' ')
print('end')

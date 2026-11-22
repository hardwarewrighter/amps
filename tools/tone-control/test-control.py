#!/usr/bin/env python3
"""Linux PTY integration tests for the actual Rust serial controller."""
from pathlib import Path
import os
import select
import subprocess
import time
import unittest

BINARY = Path(__file__).resolve().parent / 'dist/tone-control'

class ControllerTests(unittest.TestCase):
    def exchange(self, command, expected, reply):
        master, slave = os.openpty()
        proc = None
        try:
            port = os.ttyname(slave)
            proc = subprocess.Popen([str(BINARY), '--port', port, *command],
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            received = b''
            deadline = time.monotonic() + 3
            while b'\n' not in received and time.monotonic() < deadline:
                if select.select([master], [], [], .1)[0]:
                    received += os.read(master, 1024)
            self.assertEqual(received, expected)
            # Fragment the reply like separate USB packets/serial reads.
            if reply:
                os.write(master, reply[:5])
                time.sleep(.02)
                os.write(master, reply[5:])
            out, err = proc.communicate(timeout=7)
            return proc.returncode, out.decode(), err.decode()
        finally:
            if proc is not None and proc.poll() is None:
                proc.kill()
                proc.communicate()
            os.close(master)
            os.close(slave)

    def test_start_stop_status_and_pitch(self):
        for args, wire in [(['start'], b'START\n'), (['stop'], b'STOP\n'),
                           (['status'], b'STATUS\n'),
                           (['frequency', '880'], b'FREQ 880\n')]:
            with self.subTest(args=args):
                code, out, err = self.exchange(args, wire, b'OK running=1 freq=880 rate=32000\n')
                self.assertEqual(code, 0, err)
                self.assertIn('freq=880', out)

    def test_device_error(self):
        code, out, err = self.exchange(['status'], b'STATUS\n', b'ERR test failure\n')
        self.assertEqual(code, 1)
        self.assertIn('ERR test failure', err)

    def test_timeout(self):
        code, out, err = self.exchange(['status'], b'STATUS\n', None)
        self.assertEqual(code, 1)
        self.assertIn('no firmware acknowledgment', err)

    def test_invalid_pitch_does_not_open_port(self):
        for hz in ['0', '5001', '-1', '440.5', '999999999999999999999']:
            with self.subTest(hz=hz):
                p = subprocess.run([str(BINARY), '--port', '/does-not-exist', 'frequency', hz],
                                   capture_output=True, text=True)
                self.assertNotEqual(p.returncode, 0)
                self.assertIn('20..5000', p.stderr)

if __name__ == '__main__':
    unittest.main()

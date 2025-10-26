import os

if os.name == "nt":
	
	import msvcrt

	class NonBlockingInput:
		def __init__(self):
			pass

		def __enter__(self):
			return self

		def __exit__(self, exc_type, exc_value, exc_traceback):
			pass

		def poll(self):
			return mscvrt.kbhit()

		def getchar(self):
			if msvcrt.kbhit():
				ch = msvcrt.getch()[0]
				if ch == 13:
					ch = 10
				return ch

else:

	import fcntl
	import termios
	import tty

	class NonBlockingInput:
		def __init__(self):
			pass

		def __enter__(self):
			self.stdinfileno = sys.stdin.fileno()
			self.tattr = termios.tcgetattr(self.stdinfileno)
			self.orig_fl = fcntl.fcntl(sys.stdin, fcntl.F_GETFL)
			tty.setcbreak(self.stdinfileno, termios.TCSANOW)
			fcntl.fcntl(sys.stdin, fcntl.F_SETFL, self.orig_fl | os.O_NONBLOCK)
			return self

		def __exit__(self):
			termios.tcsetattr(self.stdinfileno, termios.TCSANOW, self.tattr)
			fcntl.fcntl(sys.stdin, fcntl.F_SETFL, self.orig_fl)

		def getchar(self):
			if data := sys.stdin.buffer.read(1):
				return data[0]


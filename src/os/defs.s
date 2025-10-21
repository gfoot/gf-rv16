MMIO_PUTCHAR = $fffe
MMIO_GETCHAR = $fffe
MMIO_INPUTSTATE = $ffff


os_globals = $ff00

# os_g_* are offsets into os_globals

os_g_serial_in_head = 0
os_g_serial_in_tail = 2
os_g_serial_out_head = 4
os_g_serial_out_tail = 6

os_g_serial_in_buffer = $10    # Block of 16 bytes, aligned to odd multiple of 16
os_g_serial_out_buffer = $30   # Block of 16 bytes, aligned to odd multiple of 16


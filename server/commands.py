from serial import Serial
from text_helper import num_to_sci


class SerialCommands:
    def __init__(self, conn: Serial):
        self.conn = conn

    def update_left_text(self, text: str):
        self._update_text(text, target='L')

    def update_right_text(self, text: str):
        self._update_text(text, target='R')

    def update_center_text(self, text: str):
        self._update_text(text, target='C')

    def _update_text(self, text: str, target: str):
        self.conn.write(f'T{target}{text}\n')

    def set_upper_limit(self, val: int):
        self.update_right_text(num_to_sci(val))
        self._set_range(val, target='U')

    def set_lower_limit(self, val: int):
        self.update_left_text(num_to_sci(val))
        self._set_range(val, target='L')

    def set_current_value(self, val: int):
        self.update_center_text(num_to_sci(val, 8))

    def _set_range(self, val: int, target: str):
        self.conn.write(f'R{target}{val}\n')

    def set_led_green_growing(self):
        data = bytearray([0x00, 0xFF, 0x00, 0xFF, 0xFF, 0xFF])
        self._configure_leds('g', data)

    def set_led_green_shrinking(self):
        data = bytearray([0x00, 0xFF, 0x00, 0xFF, 0xFF, 0xFF])
        self._configure_leds('s', data)

    def _configure_leds(self, mode, data: bytearray):
        self.conn.write(f'L{mode}')
        self.conn.write(data)

import time
import threading

import serial

from commands import SerialCommands
from config import SFX_ACCESS_TOKEN, SERIAL_DEVICE
from endpoint_data_stream import CurrentEndpoints, TrendDirection

endpoint_updater = CurrentEndpoints(SFX_ACCESS_TOKEN)

endpoint_update_thread = threading.Thread(target=endpoint_updater.run_loop, daemon=True)
endpoint_update_thread.start()


with serial.Serial(SERIAL_DEVICE, 115200) as conn:
    commands = SerialCommands(conn)
    commands.set_led_green_growing()
    commands.set_lower_limit(0)
    commands.set_upper_limit(12000000)
    while True:
        print(endpoint_updater.current_endpoints, endpoint_updater.trend_direction)
        commands.set_current_value(endpoint_updater.current_endpoints)
        if endpoint_updater.trend_direction == TrendDirection.UP:
            commands.set_led_green_growing()
        elif endpoint_updater.trend_direction == TrendDirection.DOWN:
            commands.set_led_green_shrinking()

        time.sleep(60)
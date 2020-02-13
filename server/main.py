import time
import threading

import serial

from commands import SerialCommands
from config import SFX_ACCESS_TOKEN, SERIAL_DEVICE
from endpoint_data_stream import CurrentEndpoints, TrendDirection
from text_helper import num_to_sci

endpoint_updater = CurrentEndpoints(SFX_ACCESS_TOKEN)

endpoint_update_thread = threading.Thread(target=endpoint_updater.run_loop, daemon=True)
endpoint_update_thread.start()


with serial.Serial(SERIAL_DEVICE, 115200) as conn:
    commands = SerialCommands(conn)
    commands.set_led_green_growing()
    commands.set_lower_limit(0)
    commands.set_upper_limit(12000000)

    curr_prod = 0
    show_single_prod = False
    last_dial = 0
    while True:
        if endpoint_updater.current_endpoints != last_dial:
            commands.set_current_value(int(endpoint_updater.current_endpoints))
            last_dial = endpoint_updater.current_endpoints

            if endpoint_updater.trend_direction == TrendDirection.UP:
                commands.set_led_green_growing()
            elif endpoint_updater.trend_direction == TrendDirection.DOWN:
                commands.set_led_green_shrinking()

            curr_prod = 0
            show_single_prod = False

        if show_single_prod:
            details = endpoint_updater.endpoint_details[curr_prod]
            commands.update_center_text(details.short_name + ' ' + num_to_sci(details.total, 4))
            curr_prod += 1
            curr_prod %= len(endpoint_updater.endpoint_details)
            print(f'Single prod details: {details}')
        else:
            commands.update_center_text(num_to_sci(int(endpoint_updater.current_endpoints), 8))
            print(f'All prod details: {endpoint_updater.current_endpoints}')

        show_single_prod = not show_single_prod

        time.sleep(1.5)


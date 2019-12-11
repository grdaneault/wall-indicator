from enum import Enum

import signalfx
from signalfx.signalflow import messages

CURRENT_ENDPOINTS_PROGRAM = """
service_filter = filter('server_type', 'services')
current_active_endpoints = data('STORAGE.eh_caches.conferDeviceAuthCache.objects', filter=service_filter) \
    .percentile(99) \
    .publish('current_active_endpoints')
""".strip()


class TrendDirection(Enum):
    UP = 1
    FLAT = 0
    DOWN = -1


class CurrentEndpoints:
    def __init__(self, token):
        self.token = token
        self.current_endpoints = 0
        self.trend_direction = TrendDirection.UP

    def run_loop(self):
        with signalfx.SignalFx().signalflow(self.token) as flow:
            c = flow.execute(CURRENT_ENDPOINTS_PROGRAM)
            tsid = None

            for msg in c.stream():
                if isinstance(msg, messages.DataMessage):
                    # This message comes in once every five minutes and provides the current active endpoints
                    if tsid in msg.data:
                        new_count = msg.data[tsid]

                        if new_count > self.current_endpoints:
                            self.trend_direction = TrendDirection.UP
                        elif new_count == self.current_endpoints:
                            self.trend_direction = TrendDirection.FLAT
                        else:
                            self.trend_direction = TrendDirection.DOWN

                        self.current_endpoints = new_count

                elif isinstance(msg, messages.MetadataMessage):
                    # This message should be the first that comes in, we use it to get the tsid for our computed data
                    tsid = msg.tsid

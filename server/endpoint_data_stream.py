from enum import Enum

import signalfx
from signalfx.signalflow import messages

CURRENT_ENDPOINTS_PROGRAM = """
service_filter = filter('server_type', 'services')
current_active_endpoints = data('STORAGE.eh_caches.conferDeviceAuthCache.objects', filter=service_filter) \
    .percentile(99) \
    .publish('current_active_endpoints')
""".strip()

CURRENT_ENDPOINTS_BY_ENV_AND_OS_PROGRAM = """

filter_prod01 = filter('environment', 'prod01')
prod01_windows = data('cbd.active_devices.windows', rollup='max', filter=filter_prod01).max().publish('prod01_windows')
prod01_mac = data('cbd.active_devices.mac', rollup='max', filter=filter_prod01).max().publish('prod01_mac')
prod01_linux = data('cbd.active_devices.linux', rollup='max', filter=filter_prod01).max().publish('prod01_linux')

filter_prod02 = filter('environment', 'prod02')
prod02_windows = data('cbd.active_devices.windows', rollup='max', filter=filter_prod02).max().publish('prod02_windows')
prod02_mac = data('cbd.active_devices.mac', rollup='max', filter=filter_prod02).max().publish('prod02_mac')
prod02_linux = data('cbd.active_devices.linux', rollup='max', filter=filter_prod02).max().publish('prod02_linux')

filter_prod05 = filter('environment', 'prod05')
prod05_windows = data('cbd.active_devices.windows', rollup='max', filter=filter_prod05).max().publish('prod05_windows')
prod05_mac = data('cbd.active_devices.mac', rollup='max', filter=filter_prod05).max().publish('prod05_mac')
prod05_linux = data('cbd.active_devices.linux', rollup='max', filter=filter_prod05).max().publish('prod05_linux')

filter_prod06 = filter('environment', 'prod06')
prod06_windows = data('cbd.active_devices.windows', rollup='max', filter=filter_prod06).max().publish('prod06_windows')
prod06_mac = data('cbd.active_devices.mac', rollup='max', filter=filter_prod06).max().publish('prod06_mac')
prod06_linux = data('cbd.active_devices.linux', rollup='max', filter=filter_prod06).max().publish('prod06_linux')

filter_prodnrt = filter('environment', 'prodnrt')
prodnrt_windows = data('cbd.active_devices.windows', rollup='max', filter=filter_prodnrt).max().publish('prodnrt_windows')
prodnrt_mac = data('cbd.active_devices.mac', rollup='max', filter=filter_prodnrt).max().publish('prodnrt_mac')
prodnrt_linux = data('cbd.active_devices.linux', rollup='max', filter=filter_prodnrt).max().publish('prodnrt_linux')

""".strip()


class TrendDirection(Enum):
    UP = 1
    FLAT = 0
    DOWN = -1


class EndpointData:
    def __init__(self, name):
        self.name = name
        self.windows_tsid = None
        self.mac_tsid = None
        self.linux_tsid = None
        self.windows = 0
        self.mac = 0
        self.linux = 0

    @property
    def short_name(self):
        if "0" in self.name:
            return 'P' + self.name[-2:]
        else:
            return self.name[-3:].upper()

    def update(self, data):
        if self.windows_tsid in data:
            self.windows = data[self.windows_tsid]
        if self.mac_tsid in data:
            self.mac = data[self.mac_tsid]
        if self.linux_tsid in data:
            self.linux = data[self.linux_tsid]

    def save_tsid(self, msg: messages.MetadataMessage):
        data = msg.properties['sf_streamLabel']
        data = data.split('_')
        if data[0] != self.name:
            return

        if data[1] == 'windows':
            self.windows_tsid = msg.tsid
        elif data[1] == 'mac':
            self.mac_tsid = msg.tsid
        elif data[1] == 'linux':
            self.linux_tsid = msg.tsid

    @property
    def total(self):
        return self.windows + self.mac + self.linux

    def __str__(self):
        return f'{self.name}: {self.windows}/{self.mac}/{self.linux}'


class CurrentEndpoints:
    def __init__(self, token):
        self.token = token
        self.current_endpoints = 0
        self.trend_direction = TrendDirection.UP
        self.endpoint_details = [EndpointData(env) for env in ['prod01', 'prod02', 'prod05', 'prod06', 'prodnrt']]

    def run_loop(self):
        with signalfx.SignalFx().signalflow(self.token) as flow:
            c = flow.execute(CURRENT_ENDPOINTS_BY_ENV_AND_OS_PROGRAM)
            tsid = None

            for msg in c.stream():
                if isinstance(msg, messages.DataMessage):
                    # This message comes in once every five minutes and provides the current active endpoints

                    for env in self.endpoint_details:
                        env.update(msg.data)

                    new_count = sum(e.total for e in self.endpoint_details)

                    if new_count > self.current_endpoints:
                        self.trend_direction = TrendDirection.UP
                    else:
                        self.trend_direction = TrendDirection.DOWN
                    self.current_endpoints = new_count

                elif isinstance(msg, messages.MetadataMessage):
                    # This message should be the first that comes in, we use it to get the tsid for our computed data
                    for env in self.endpoint_details:
                        env.save_tsid(msg)
                    tsid = msg.tsid

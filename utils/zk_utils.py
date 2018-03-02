from common import *
from kazoo.client import KazooClient

DEFAULT_ZK = "localhost:2181"
LOGGER_NAME = "zkUtils"


class zkUtils:
    """Zookeeper utility class implemented with Kazoo"""
    def __init__(self, hosts=DEFAULT_ZK, read_only=True, logging_level=logging.INFO):
        self.zc = KazooClient(hosts=hosts, read_only=read_only)
        self.logger = get_logger(LOGGER_NAME, logging_level)
        self.logger.info("Zookeeper hosts: {}, client util instantiated.".format(hosts))

    def get_path_data(self, path="/"):
        try:
            self.zc.restart()
            if self.zc.exists(path):
                return self.zc.get(path)[0]
            else:
                return None
        except Exception as e:
            self.logger.exception("Get path data exception: {}!".format(str(e)))
            return None

    def get_children_list(self, path="/"):
        try:
            self.zc.restart()
            if self.zc.exists(path):
                return self.zc.get_children(path)
            else:
                return None
        except Exception as e:
            self.logger.exception("Get path data exception: {}!".format(str(e)))
            return None

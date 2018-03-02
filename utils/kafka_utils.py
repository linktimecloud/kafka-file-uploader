import csv
import json
from common import *
from kafka import KafkaProducer, KafkaConsumer

DEFAULT_BOOTSTRAP = "localhost:9092"
DEFAULT_TOPIC = "_schema"
LOGGER_NAME = "kafkaUtils"
TEXT_SET = "txt"
CSV_SET = "csv"
JSON_SET = "json"


class kafkaProducerUtils:
    """Kafka producer utility class implemented with kafka-python"""
    def __init__(self, bootstrap_servers=DEFAULT_BOOTSTRAP, logging_level=logging.INFO):
        self.kp = KafkaProducer(bootstrap_servers=bootstrap_servers, acks="all")
        self.logger = get_logger("{}.producer".format(LOGGER_NAME), logging_level)
        self.logger.info("Kafka bootstrap servers: {}, producer util instantiated.".format(bootstrap_servers))

    def file_producer(self, filename, topic=DEFAULT_TOPIC):
        if os.path.exists(filename):
            try:
                extension = filename.rsplit(".", 1)[1]
                if extension in [TEXT_SET, JSON_SET]:
                    with codecs.open(filename, encoding=UTF_8) as fp:
                        if extension in TEXT_SET:
                            for line in fp.readlines():
                                self.kp.send(topic, b'{}'.format(line.encode(UTF_8)))
                        elif extension in JSON_SET:
                            json_loader = json.load(fp, encoding=UTF_8)
                            self.logger.debug("JSON loader: %s" % json_loader)
                            for key, value in json_loader.items():
                                self.kp.send(topic, b'{}, {}'.format(key, value))
                elif extension in CSV_SET:
                    with codecs.open(filename) as fp:
                        reader = csv.reader(fp, delimiter=',')
                        for row in reader:
                            for word in row:
                                if word:
                                    self.kp.send(topic, b'{}'.format(word.strip()))
                self.kp.flush()
                return True
            except Exception as e:
                self.logger.exception("Read file and send to topic exception: {}".format(str(e)))
                return False
        else:
            self.logger.error("File {} not exists!".format(filename))
            return False


class kafkaCosumerUtils:
    """Kafka consumer utility class implemented with kafka-python"""
    def __init__(self, bootstrap_servers=DEFAULT_BOOTSTRAP, logging_level=logging.INFO, *topics):
        self.kp = KafkaConsumer(bootstrap_servers=bootstrap_servers, *topics)
        self.logger = get_logger("{}.consumer".format(LOGGER_NAME), logging_level)
        self.logger.info("Kafka bootstrap servers: {}, consumer util instantiated.".format(bootstrap_servers))

import os
import json
import logging

from flask import Flask, request, render_template, redirect, url_for, jsonify
from flask_uploads import UploadSet, configure_uploads, patch_request_class, TEXT, DOCUMENTS, DATA, SCRIPTS
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import SubmitField

from utils.zk_utils import zkUtils
from utils.zk_utils import DEFAULT_ZK
from utils.kafka_utils import kafkaProducerUtils
from utils.kafka_utils import DEFAULT_TOPIC
from utils.common import UTF_8, secure_file_name

APP_PORT = 5001
ENV_DEBUG = "DEBUG"
HOST_FIELD = "host"
IGNORED_FILES = set(['.gitignore'])
PORT_FIELD = "port"
SUPPORTED_EXTENSIONS = 'txt csv json'
SUPPORTED_WARNING = u'Only support extensions: {}'.format(SUPPORTED_EXTENSIONS.upper())
ZK_ZNODE_BROKERS = "/brokers"
ZK_ZNODE_BROKERS_IDS = "/brokers/ids"
FIELD_UPLOAD = "upload_success"
FIELD_PRODUCE = "produce_success"
FIELD_MESSAGE = "message"

env = os.getenv("ENV", ENV_DEBUG)
if env == ENV_DEBUG:
    logging_level = logging.DEBUG
else:
    logging_level = logging.INFO

app = Flask(__name__)
app.config['SECRET_KEY'] = 'linktime cloud corp'
app.config['UPLOADED_FILES_DEST'] = os.getcwd() + '/data'
app.logger.setLevel(logging_level)

files = UploadSet('files', tuple(SUPPORTED_EXTENSIONS.split()))
configure_uploads(app, files)
patch_request_class(app)  # set maximum file size, default 64MB


class UploadForm(FlaskForm):
    file = FileField(validators=[FileAllowed(files, u'Only support extensions: {}'
                                                    u''.format(SUPPORTED_EXTENSIONS.upper())),
                                 FileRequired(u'Choose a file!')])
    submit = SubmitField(u'Upload')


def gen_file_name(filename):
    """
    If file was exist already, rename it and return a new name
    """
    i = 1
    while os.path.exists(os.path.join(app.config['UPLOADED_FILES_DEST'], filename)):
        name, extension = os.path.splitext(filename)
        filename = '%s_%s%s' % (name, str(i), extension)
        i += 1
    return filename


def save_uploaded_file(file_storage_obj):
    try:
        file_name = secure_file_name(file_storage_obj.filename.encode(UTF_8))
        file_name = gen_file_name(file_name)
        uploaded_file_path = os.path.join(app.config['UPLOADED_FILES_DEST'], file_name)
        file_storage_obj.save(uploaded_file_path)
        return True, uploaded_file_path
    except Exception:
        return False, None


def get_uploaded_list():
    unicode_file_list = []
    file_list = [f for f in os.listdir(app.config['UPLOADED_FILES_DEST']) if
                 os.path.isfile(os.path.join(app.config['UPLOADED_FILES_DEST'], f)) and f not in IGNORED_FILES]
    file_list.sort(key=lambda a: a.lower())
    for saved_file in file_list:
        unicode_file_list.append(saved_file.decode(UTF_8))
    return unicode_file_list


def get_broker_host(zk_host=DEFAULT_ZK):
    zku = zkUtils(zk_host, logging_level)
    broker_id_list = zku.get_children_list(ZK_ZNODE_BROKERS_IDS)
    if broker_id_list:
        znode_broker = os.path.join(ZK_ZNODE_BROKERS_IDS, broker_id_list[0])
        data = json.loads(zku.get_path_data(znode_broker))
        return "{}:{}".format(data[HOST_FIELD], data[PORT_FIELD])
    else:
        return None


def read_and_send(file_name):
    broker_host = get_bootstrap_server()
    topic = os.getenv("KAFKA_TOPIC", DEFAULT_TOPIC)
    if broker_host:
        kpu = kafkaProducerUtils(broker_host, logging_level)
        return kpu.file_producer(file_name, topic), "Kafka broker: %s" % broker_host
    else:
        return False, "Failed to get Kafka broker from Zookeeper!"


@app.route('/', methods=['GET', 'POST'])
def upload():
    form = UploadForm()
    if form.validate_on_submit():
        flag = True
        for file_storage in request.files.getlist('file'):
            flag = save_uploaded_file(file_storage)[0]
        success = True if flag else False
    else:
        success = False
    return render_template('index.html', form=form, success=success)


@app.route('/manage')
def manage():
    return render_template('manage.html', files=get_uploaded_list())


@app.route('/produce/<filename>')
def produce_file(filename):
    file_path = files.path(filename)
    success, message = read_and_send(file_path)
    return render_template('manage.html', files=get_uploaded_list(),
                           message=message, success=success, fail=not success)


@app.route('/browse/<filename>')
def browse_file(filename):
    file_url = files.url(filename)
    return render_template('browser.html', file_url=file_url)


@app.route('/delete/<filename>')
def delete_file(filename):
    file_path = files.path(filename)
    os.remove(file_path)
    return redirect(url_for('manage'))


@app.route('/bootstrap')
def get_bootstrap_server():
    zk_hosts = os.getenv("ZK_HOSTS", DEFAULT_ZK)
    return get_broker_host(zk_hosts)


@app.route('/api/upload', methods=['POST'])
def api_upload():
    file_obj = request.files['file']
    if request.method == 'POST' and file_obj:
        result = {FIELD_UPLOAD: False, FIELD_PRODUCE: False, FIELD_MESSAGE: SUPPORTED_WARNING}
        try:
            file_name = file_obj.filename.encode(UTF_8)
            extension = os.path.splitext(file_name)[1].lstrip('.')
            if extension not in SUPPORTED_EXTENSIONS.split():
                return jsonify(result)
        except Exception:
            return jsonify(result)
        upload_success, upload_path = save_uploaded_file(request.files['file'])
        if upload_success:
            produce_success, message = read_and_send(upload_path)
        else:
            produce_success, message = False, "Upload Fail!"
        result[FIELD_UPLOAD] = upload_success
        result[FIELD_PRODUCE] = produce_success
        result[FIELD_MESSAGE] = message
        return jsonify(result)


if __name__ == '__main__':
    debug_flag = True if env == ENV_DEBUG else False
    app.run(host='0.0.0.0', port=os.getenv("APP_PORT", APP_PORT), debug=debug_flag)

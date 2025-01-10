import json

import flask



app = flask.Flask(__name__)


@app.route('/')
def index():
    x = "hola mundo"
    return x



if __name__ == '__main__':
  import uuid
  from settings import *
  app.config.from_object(config)
  app.run()
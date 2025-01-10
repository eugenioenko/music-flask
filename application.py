# import os
from flask import Flask, g, redirect, abort, request, session, escape
import controller
import interface
from settings import *
from flask_login import login_required, logout_user, current_user
from flask_session import Session
from functools import wraps
from flask_socketio import SocketIO, join_room, leave_room, emit, send, disconnect

app = Flask(__name__)
flask_config = ProductionConfig()
app.config.from_object(flask_config)
controller = controller.Controller(app)
interface = interface.Interface(app)
Session(app)
#socketio = SocketIO(app, async_mode="eventlet")
socketio = SocketIO(app, async_mode="gevent")

"""
    Decorates app request requiring json post
"""
def json_request(func):
    @wraps(func)
    def wrapped(*args, **kwargs):
        if not request.json:
            abort(400)
        return func(*args, **kwargs)
    return wrapped

"""
Used as: flask create_tables. Creates tables from shell
"""
@app.cli.command('create_tables')
def create_tables():
    return controller.create_tables()


@app.before_request
def before_request():
    g.db = controller.get_db()
    try:
        g.db.connect()
    except:
        pass



@app.after_request
def after_request(response):
    g.db.close()
    return response


@app.teardown_appcontext
def close_db(error):
    db = controller.get_db()
    if not db.is_closed():
        db.close()


@controller.auth.user_loader
def user_loader(uuid):
    return controller.user_get(uuid)


"""
Home rooute of the application
"""
@app.route('/')
@login_required
def home():
    return controller.home()


@app.route('/playlist/')
@app.route('/playlist/<uuid>/')
@login_required
def playlist(uuid):
    return controller.playlist(uuid)


@app.route('/login/', methods=('GET', 'POST'))
@controller.auth.unauthorized_handler
def login():
    return controller.form_login()


@app.route('/signup/', methods=('GET', 'POST'))
def signup():
    return controller.form_signup()


@app.route("/logout/")
@login_required
def logout():
    logout_user()
    return redirect('/')


@app.route("/create_playlist", methods=('GET', 'POST'))
@login_required
def create_playlist():
    return controller.form_create_playlist()


@app.route("/search/user/")
@app.route("/search/user/<term>")
@login_required
def search_user(term='%'):
    return controller.user_search(term)

@app.route("/search/song/", methods=['POST'])
@login_required
@json_request
def song_search_fm():
    return interface.song_search_fm()


@app.route("/search/vsong/", methods=['POST'])
@login_required
@json_request
def song_search_get():
    return interface.song_search_get()


@app.route("/playlist/user/")
@app.route("/playlist/user/<term>")
@login_required
def search_playlist(term='%'):
    return controller.playlist_search(term)


# api
@app.route("/get/profile/")
@app.route("/get/profile/<uuid>")
@login_required
def profile_get(uuid=0):
    return interface.profile_get(uuid)

# api
@app.route("/get/playlist/")
@app.route("/get/playlist/<uuid>")
@login_required
def playlist_get(uuid=0):
    return interface.playlist_get(uuid)

# api
@app.route("/update/playlist/")
@login_required
def playlist_update():
    return interface.playlist_update()

@app.route("/get/playlists/all/", methods=['GET'])
@login_required
def playlist_get_all():
    return interface.playlist_get_all()


@app.route("/get/friends/all/", methods=['GET'])
@login_required
def user_get_all_friends():
    return interface.user_get_all_friends()


@app.route("/get/playlists/user/", methods=['GET'])
@login_required
def user_get_own_playlists():
    return interface.user_get_own_playlists()


@app.route("/get/poster/", methods=['POST'])
@json_request
def poster_get():
    return interface.poster_get()


@app.route("/create/playlist/", methods=['POST'])
@json_request
def playlist_create():
    return interface.playlist_create()


# socket io
def authenticated_only(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated:
            disconnect()
        else:
            return f(*args, **kwargs)
    return wrapped


@socketio.on('connect')
@authenticated_only
def client_connection():
    if 'playlist_uuid' not in session:
        room = 'home'
    else:
        room = session['playlist_uuid']
    join_room(room)


@socketio.on('disconnect')
@authenticated_only
def client_disconnection():
    if 'playlist_uuid' not in session:
        room = 'home'
    else:
        room = session['playlist_uuid']
    leave_room(room)


@socketio.on('change playlist')
@authenticated_only
def client_change_playlist(data):
    if session['old_playlist_uuid']:
        old_room = session['old_playlist_uuid']
        send(current_user.name + ' left the playlist ' + old_room, room=old_room)
        leave_room(old_room)
    new_room = session['playlist_uuid']
    join_room(new_room)
    send(current_user.name + ' joined the playlist ' + new_room, room=new_room)

@socketio.on('song added')
@authenticated_only
def client_adds_song(data):
    emit('update playlist', {}, room=session['playlist_uuid'])

@socketio.on('chat message')
@authenticated_only
def recieved_chat_message(data):
    emit('update chat', {'message': escape(data['message']), 'user': current_user.name, 'who': current_user.uuid }, room=session['playlist_uuid'])

if __name__ == '__main__':
    print 'music-flask is running.'
    socketio.run(app, debug=False, host='0.0.0.0', port=5000)
    #app.run(host='0.0.0.0')

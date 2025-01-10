from flask import  redirect, request, render_template, flash, session
from flask_session import Session
from uuid import uuid4
import datetime
from functools import wraps
import json
import bcrypt
import flask_admin as admin
from flask_admin.contrib.peewee import ModelView
from flask_login import LoginManager, login_user, current_user

from model import *
from settings import Settings
import forms

CURRENT_USER_ID = 1
class AdminView(ModelView):

    def is_accessible(self):
        return current_user.is_authenticated and current_user.email == 'enko@enko.com'

    def inaccessible_callback(self, name, **kwargs):
        # redirect to login page if user doesn't have access
        return redirect(url_for('login', next=request.url))

class Controller:
    # Constructor
    def __init__(self, app):
        self.app = app
        self.config = Settings()
        # Login manager
        self.auth = LoginManager()
        self.auth.init_app(app)
        # Admin manager
        self.admin = admin.Admin(app, name='Admin')
        self.admin.add_view(AdminView(User))
        self.admin.add_view(AdminView(Stats))
        self.admin.add_view(AdminView(UserRole))
        self.admin.add_view(AdminView(Artist))
        self.admin.add_view(AdminView(Album))
        self.admin.add_view(AdminView(Song))
        self.admin.add_view(AdminView(Poster))
        self.admin.add_view(AdminView(PlaylistStyle))
        self.admin.add_view(AdminView(PlaylistPrivacy))
        self.admin.add_view(AdminView(Playlist))
        self.admin.add_view(AdminView(PlaylistSong))
        self.admin.add_view(AdminView(AppLog))


    # Routes
    def home(self):
        session['playlist_uuid'] = 'home'
        return render_template(
            'index.html',
            date=format(datetime.datetime.now()),
            playlist_load=False,
            current_user=current_user.uuid,
            static_url=self.config.static_url,
            poster=Poster.get_random()
        )

    def playlist(self, uuid):
        try:
            p = Playlist.get(Playlist.uuid == uuid)
        except:
            return redirect('/')
        if (PRIVACY_PRIVATE == p.privacy.id) and (current_user.id != p.user_id):
            return redirect('/')
        elif (PRIVACY_FRIEND == p.privacy.id) and not(current_user.is_friend_of(p.user_id)):
            return redirect('/')
        else:
            return render_template(
                'index.html',
                current_user=current_user.uuid,
                date=format(datetime.datetime.now()),
                playlist_load=uuid,
                static_url=self.config.static_url,
                poster=Poster.get_random()
            )

    def create_tables(self):
        # db.connect()
        db.create_tables([PosterUnformated])
            #User, Stats, Friendship, Role, UserRole, Artist, Album, Song, Poster,
            #Cover, Related, PlaylistStyle, PlaylistPrivacy, Playlist])
        db.close()
        print("Tables Created")
        return True

    def get_db(self):
        return db

    # User
    def user_get(self, uuid):
        return User.get_by_uuid(uuid)

    def user_validate(self, email, password):
        try:
            user = User.get(User.email == email)
            if bcrypt.checkpw(
                str(password).encode('utf-8'),
                str(user.password).encode('utf-8')
            ):
                return user
        except:
            return None

    def users_connected(self):
        return User.select(
            User.name, User.uuid
        ).where(
            User.lastactivity >=
            datetime.datetime.now() - datetime.timedelta(hours=1)
        ).dicts()

    def users_friends_connected(self):
        return (
            Friendship.select()
            .join(User, on=Friendship.user_left_id)
            .where(
                (User.lastactivity >=
                    datetime.datetime.now() - datetime.timedelta(hours=1)) &
                (Friendship.user_right_id == current_user.id)
            )
        )

    def user_search(self, term):
        return jsonify(list(User.search(term)))

    # Auth logout

    def form_login(self):
        #form = forms.Login(srf_enabled=False)
        form = forms.Login()
        if form.validate_on_submit():
            login_user(form.user)
            form.user.update_lastlogin()
            flash('Welcome ' + form.user.name)
            return redirect('/')
        return render_template('login.html',
            form=form,
            date=format(datetime.datetime.now()),
            static_url=self.config.static_url)

    def form_signup(self):
        form = forms.SignUp()
        if form.validate_on_submit():
            try:
                user = User()
                form.populate_obj(user)
                user.uuid = uuid4().hex
                user.password = bcrypt.hashpw(
                    str(user.password).encode('utf-8'), bcrypt.gensalt())
                user.save()
                # logs the user and redirects
                login_user(user)
                user.update_lastlogin()
                flash('Welcome ' + user.name)
                return redirect('/')
            except IntegrityError:
                flash('email address already taken')
                return render_template('signup.html', form=form, date=format(datetime.datetime.now()))
            except:
                log = AppLog()
                log.code = 804
                log.log = "Error signing in user: " + json.dumps(form.data)
                log.save()
        return render_template('signup.html',
            form=form,
            date=format(datetime.datetime.now()),
            static_url=self.config.static_url)

    # Roles
    def get_roles(self):
        roles = []
        for role in current_user.roles:
            roles.append(role.name)
        return roles

    def requires_role(self, *roles):
        def wrapper(f):
            @wraps(f)
            def wrapped(*args, **kwargs):
                if not all(role in self.get_roles() for role in roles):
                    return 'Denied'
                return f(*args, **kwargs)
            return wrapped
        return wrapper



    # Playlists
    def form_create_playlist(self):
        form = forms.CreatePlaylist()
        if form.validate_on_submit():
            playlist = Playlist()
            playlist.name = form.name.data
            playlist.privacy = form.privacy.data
            playlist.style = form.style.data
            playlist.user = current_user.id
            playlist.uuid = uuid4().hex
            playlist.save()
            return '<h2>Playlist Created!</h2>'
        return render_template('playlist_create.html', form=form)

    def playlist_get_for_user(self):
        return list(Playlist.of_user(current_user.id))

    def playlist_get_for_friends(self):
        return list(Playlist.of_friends(current_user.id))

    def playlist_search(self, term):
        return jsonify(list(Playlist.search(term)))

    # Api requests

    def api(self):
        r = request.get_json()
        if r is not None:
            method = r['method']
            if method == 'get-playlists':
                return jsonify({"result": "ok", "playlists": list(Playlist.get_of_user(CURRENT_USER_ID))})
            elif method == 'get-friends-playlists':
                return jsonify({"result": "ok", "playlists": list(Playlist.get_of_friends(CURRENT_USER_ID))})
            elif method == 'get-public-playlists':
                return jsonify({"result": "ok", "playlists": list(Playlist.get_public())})
            elif method == 'search-song':
                arg = r['argument']
                return jsonify({"result": "ok", "songs": self.song_search_fm(arg)})
            else:
                return jsonify({"error": "unknown method"})
        else:
            return 'error'

from peewee import *
from settings import *
from uuid import uuid4
from random import randrange
import datetime

db = MySQLDatabase(
    "musikflask",
    host="localhost",
    port=3306,
    user="musikflask",
    passwd="")

PRIVACY_PUBLIC = 1
PRIVACY_FRIEND = 2
PRIVACY_PRIVATE = 3


class BaseModel(Model):
    class Meta:
        database = db


class User(BaseModel):
    id = PrimaryKeyField()
    uuid = FixedCharField(unique=True, max_length=64)
    email = CharField(unique=True)
    name = CharField()
    password = CharField()
    picture = CharField(null=True)
    phrase = CharField(null=True, max_length=255)
    created = DateTimeField(default=datetime.datetime.now())
    lastlogin = DateTimeField(null=True)
    lastactivity = DateTimeField(null=True)
    banned = IntegerField(null=True)

    def update_lastlogin(self):
        self.lastlogin = datetime.datetime.now()
        self.lastactivity = datetime.datetime.now()
        self.save()
        return True

    def update_lastactivity(self):
        self.lastactivity = datetime.datetime.now()
        self.save()
        return True

    @classmethod
    def get_by_uuid(cls, uuid):
        try:
            user = User.get(User.uuid == uuid)
            return user
        except:
            return None

    @classmethod
    def get_by_id(cls, id):
        try:
            user = User.get(User.id == id)
            return user
        except:
            return None

    @classmethod
    def search(cls, term='%'):
        if not term == '%':
            term = '%' + term + '%'
        return User.select(
            User.name, User.email, User.picture, User.phrase
        ).where((User.name ** term) | (User.email ** term) | (User.phrase ** term)).limit(20).dicts()

    def is_active(self):
        return True

    def get_id(self):
        return self.uuid

    def is_authenticated(self):
        return True

    def is_anonymous(self):
        return False

    def get_roles(self):
        return False

    def get_friends(self):
        return Friendship.of_user(self.id)

    def is_friend_of(self, friend_id):
        if self.id == friend_id:
            return True
        try:
            Friendship.get(
                ((Friendship.user_left_id == self.id) & (Friendship.user_right_id == friend_id)) |
                ((Friendship.user_right_id == self.id) & (Friendship.user_left_id == friend_id)))
        except DoesNotExist:
            return False
        return True


class Stats(BaseModel):
    id = PrimaryKeyField()
    user = ForeignKeyField(User, related_name='user_stats')
    songs = IntegerField(null=True)
    playlists = IntegerField(null=True)
    friends = IntegerField(null=True)
    liked = IntegerField(null=True)
    disliked = IntegerField(null=True)


class Friendship(BaseModel):
    id = PrimaryKeyField()
    user_left = ForeignKeyField(User, related_name='friends_left')
    user_right = ForeignKeyField(User, related_name='friends_right')
    requested = DateTimeField(default=datetime.datetime.now())
    confirmed = DateTimeField(null=True)
    denied = IntegerField(null=True)

    @classmethod
    def of_user(cls, user_id):
        return ((Friendship.select(User.name, User.uuid)
                .join(User, on=Friendship.user_right_id)
                .where(Friendship.user_left_id == user_id)) |
                (Friendship.select(User.name, User.uuid)
                .join(User, on=Friendship.user_left_id)
                .where(Friendship.user_right_id == user_id))).dicts()


class Role(BaseModel):
    id = PrimaryKeyField()
    name = CharField()
    description = CharField()


class UserRole(BaseModel):
    id = PrimaryKeyField()
    user = ForeignKeyField(User, related_name='roles')
    role = ForeignKeyField(Role, related_name='users')
    name = property(lambda self: self.role.name)


class Artist(BaseModel):
    id = PrimaryKeyField()
    uuid = FixedCharField(unique=True, max_length=64)
    name = CharField()
    thumb_small = CharField(null=True)
    thumb_medium = CharField(null=True)
    thumb_large = CharField(null=True)
    thumb_extra = CharField(null=True)
    started = IntegerField(null=True)
    finished = IntegerField(null=True)
    created = DateTimeField(default=datetime.datetime.now())
    edited = DateTimeField(null=True)


class Album(BaseModel):
    id = PrimaryKeyField()
    uuid = FixedCharField(unique=True, max_length=64)
    name = CharField()
    artist = ForeignKeyField(Artist, related_name='albums')
    thumb_small = CharField(null=True)
    thumb_medium = CharField(null=True)
    thumb_large = CharField(null=True)
    thumb_extra = CharField(null=True)
    published = IntegerField(null=True)
    created = DateTimeField(default=datetime.datetime.now())
    edited = DateTimeField(null=True)


class Song(BaseModel):
    id = PrimaryKeyField()
    uuid = FixedCharField(unique=True, max_length=64)
    video_id = FixedCharField(max_length=16)
    video_id2 = FixedCharField(null=True, max_length=16)
    video_id3 = FixedCharField(null=True, max_length=16)
    name = CharField()
    duration = IntegerField(default=0)
    likes = IntegerField(default=0)
    dislikes = IntegerField(default=0)
    artist = ForeignKeyField(Artist, related_name='songs')
    artist_name = CharField(default='')
    album = ForeignKeyField(Album, related_name='songs_in_album')
    state = IntegerField(default=0)
    created = DateTimeField(default=datetime.datetime.now())

    @classmethod
    def get_song(csl, uuid, artist, name):
        return Song.get((Song.uuid == uuid) | ((Song.name == name) & (Song.artist_name == artist)))


class Poster(BaseModel):
    id = PrimaryKeyField()
    uuid = FixedCharField(unique=True, max_length=64)
    artist = ForeignKeyField(Artist, related_name='posters')
    artist_name = CharField(null=True)
    origin = CharField(null=True)
    url = CharField(null=True)
    thumbnail = CharField(null=True)
    created = DateTimeField(default=datetime.datetime.now())
    edited = DateTimeField(null=True)

    @classmethod
    def get_random(cls):
        try:
            count = Poster.select().count()
            rand_id = randrange(1, count)
            p = Poster.get(Poster.id == rand_id)
            return p.url
        except:
            return None

    @classmethod
    def get_artist(cls, name):
        try:
            p = Poster.select().where(Poster.artist_name == name).order_by(fn.Rand()).limit(1).get()
            return p.url
        except:
            return None

class PosterUnformated(BaseModel):
    id = PrimaryKeyField()
    artist = ForeignKeyField(Artist)
    artist_name = CharField(null=True)
    data = TextField(null=True)

class Related(BaseModel):
    id = PrimaryKeyField()
    artist = ForeignKeyField(Artist, related_name='from_artist')
    relation = ForeignKeyField(Artist, related_name='to_artist')
    created = DateTimeField(default=datetime.datetime.now())


class PlaylistStyle(BaseModel):
    id = PrimaryKeyField()
    name = CharField(max_length=24)


class AppLog(BaseModel):
    id = PrimaryKeyField()
    code = IntegerField(default=0)
    log = TextField(null=True)
    created = DateTimeField(default=datetime.datetime.now())

    @classmethod
    def make(cls, code, text):
        try:
            log = AppLog()
            log.code = code
            log.log = text
            log.save()
        except:
            pass


class PlaylistPrivacy(BaseModel):
    id = PrimaryKeyField()
    name = FixedCharField(max_length=24)


class Playlist(BaseModel):
    id = PrimaryKeyField()
    uuid = FixedCharField(unique=True, max_length=64)
    user = ForeignKeyField(User, related_name='playlists')
    name = CharField()
    privacy = ForeignKeyField(PlaylistPrivacy, related_name='privacies')
    style = ForeignKeyField(PlaylistStyle, related_name='styles')
    likes = IntegerField(default=0)
    dislikes = IntegerField(default=0)
    created = DateTimeField(default=datetime.datetime.now())

    @classmethod
    def search(cls, term='%'):
        if not term == '%':
            term = '%' + term + '%'
        return (
            Playlist.select(
                Playlist.name, Playlist.uuid)
            .where((Playlist.name ** term))
            .order_by(Playlist.created.desc())
            .limit(20).dicts())

    @classmethod
    def of_user(cls, user_id):
        return Playlist.select(
            Playlist.name, Playlist.uuid, Playlist.likes, Playlist.dislikes,
        ).where(
            Playlist.user == user_id
        ).order_by(Playlist.id.desc()).dicts()

    @classmethod
    def of_public(cls):
        return (Playlist.select(
            Playlist.name, Playlist.uuid, Playlist.likes, Playlist.dislikes,
            User.name.alias('username'))
            .join(User, on=Playlist.user_id)
            .where(Playlist.privacy == PRIVACY_PUBLIC)
            .order_by(Playlist.id.desc()).limit(50).dicts())
    @classmethod
    def of_friends(cls, user_id):
        return []

    def get_songs(self):
        return (PlaylistSong.select(
            PlaylistSong.uuid, PlaylistSong.likes, PlaylistSong.dislikes, PlaylistSong.created,
            User.name.alias('username'), User.uuid.alias('user_id'),
            Song.name, Song.video_id.alias('song_id'), Artist.name.alias('artist'))
            .join(User, on=PlaylistSong.user_id)
            .switch(PlaylistSong)
            .join(Song, on=PlaylistSong.song_id)
            .join(Artist, on=Song.artist_id)
            .where(PlaylistSong.playlist_id == self.id).dicts().order_by(PlaylistSong.id.asc()))


class PlaylistSong(BaseModel):
    id = PrimaryKeyField()
    uuid = FixedCharField(unique=True, max_length=64)
    playlist = ForeignKeyField(Playlist, related_name='songs')
    user = ForeignKeyField(User, related_name='user_playlists')
    song = ForeignKeyField(Song, related_name='in_playlists')
    likes = IntegerField(default=0)
    dislikes = IntegerField(default=0)
    created = DateTimeField(default=datetime.datetime.now())
    @classmethod
    def add_song(cls, playlist_id, user_id, song_id):
        p = PlaylistSong()
        p.uuid = uuid4().hex
        p.playlist = playlist_id
        p.user = user_id
        p.song = song_id
        p.save()

class Vote(BaseModel):
    id = PrimaryKeyField()
    item = FixedCharField(max_length=64)
    user = ForeignKeyField(User, related_name='votes')
    value = IntegerField()


class Comment(BaseModel):
    id = PrimaryKeyField()
    uuid = FixedCharField(unique=True, max_length=64)
    item = FixedCharField(max_length=64)
    user = ForeignKeyField(User, related_name='comments')
    text = TextField(null=True)

class ArtistPage(BaseModel):
    id = PrimaryKeyField()
    letter = FixedCharField(max_length=2)
    body = TextField(null=True)
    parsed = TextField(null=True)
    state = IntegerField(default=0)

class Artists(BaseModel):
    id = PrimaryKeyField()
    name = TextField(null=True)
    links = TextField(null=True)
    state = IntegerField(default=0)


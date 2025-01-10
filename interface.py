from uuid import uuid4
from flask import jsonify, request, session
from flask_session import Session
import json
import urllib
import urllib2
from flask_login import current_user
from model import *
from settings import Settings

UNKNOWN_ARTIST_ID = 1
UNKNOWN_ALBUM_ID = 1

class Interface:
    # Constructor
    def __init__(self, app):
        self.app = app
        self.config = Settings()

    # User and Pofiles
    def profile_get(self, uuid):
        if 'user' == uuid:
            uuid = current_user.uuid
        user = User.get_by_uuid(uuid)
        if user is None:
            return jsonify({"error": "Profile not found"})
        else:
            return jsonify({"result": {
                "username": user.name,
                "picture": user.picture,
                "phrase": user.phrase
            }})
    # Crawler
    def crawler_get(self):
        try:
            artist = Artists.get(Artists.state == 0)
            artist.state = 1;
            artist.save()
        except:
            pass
        return artist.name

    def crawler_set(self):
        r = request.get_json()
        name = r['artist']
        data = r['data']
        artist = Artists.get(Artists.name == name)
        artist.links = data
        artist.state = 2
        artist.save()
        print data
        return 'hoke'

    # Playlist
    def playlist_get_all(self):
        try:
            return jsonify({"result": list(Playlist.of_public())})
        except:
            return jsonify({"error": "Bad request"})

    def playlist_get(self, uuid):
        result = {}
        if 0 == uuid:
            return jsonify({"error": "Empty request parameter"})
        try:
            p = Playlist.get(Playlist.uuid == uuid)
            if (PRIVACY_PRIVATE == p.privacy.id) and (current_user.id != p.user_id):
                result = {"error": "This playlist is private"}
            elif (PRIVACY_FRIEND == p.privacy.id) and not(current_user.is_friend_of(p.user_id)):
                result = {"error": "This playlist is only for friends of " + p.user.name}
            else:
                result = {"result": "Playlist selected"}
                if 'playlist_uuid' in session:
                    session['old_playlist_uuid'] = session['playlist_uuid']
                else:
                    session['old_playlist_uuid'] = False
                session['playlist_uuid'] = p.uuid
                session['playlist_id'] = p.id
        except DoesNotExist:
            result = {"error": "Playlist doesn't exist"}
        return jsonify(result)

    def playlist_update(self):
        try:
            p = Playlist.get(Playlist.uuid == session['playlist_uuid'])
            result = {"result": list(p.get_songs()), "name": p.name, "style": p.style.id}
            return jsonify(result)
        except:
            return jsonify({"error": "Undefined error on update"})

    def playlist_create(self):
        result = {}
        try:
            r = request.get_json()
        except:
            return jsonify({"error": "Empty request"})
        try:
            p = Playlist()
            p.name = r['name']
            p.uuid = uuid4().hex
            p.style = r['style']
            p.privacy = r['privacy']
            p.user_id = current_user.id
            p.save()
            result = {"result": {'name': p.name, 'uuid': p.uuid}}
        except:
            return jsonify({"error": "Bad request"})
        return jsonify(result)

    # User

    def user_get_all_friends(self):
        result = {}
        try:
            f = Friendship.of_user(current_user.id)
            result = {"result": list(f)}
        except DoesNotExist:
            result = {"error": "Bad request"}
        return jsonify(result)

    def user_get_own_playlists(self):
        result = {}
        try:
            f = Playlist.of_user(current_user.id)
            result = {"result": list(f)}
        except DoesNotExist:
            result = {"error": "Bad request"}
        return jsonify(result)


    # Poster
    def poster_get(self):
        try:
            r = request.get_json()
            artist = r['artist']
        except:
            return jsonify({"error": "Bad request"})
        poster = Poster.get_artist(artist)
        if poster is None:
            poster = Poster.get(Poster.id == 1)
            return jsonify({"result": poster.url})
        else:
            return jsonify({"result": poster})


    def poster_create_search(self, artist_name, artist_id):
        try:
            artist_name = artist_name.encode('utf-8')
            bingUrl = 'https://api.datamarket.azure.com/Bing/Search/v1/Image?'
            params = {
                "Query": "'" + artist_name + "'",
                "ImageFilters": "'Size:Width:1920+Size:Height:1080'",
                "$format": "json"

            }
            params = urllib.urlencode(params)
            request = urllib2.Request(bingUrl + params)
            request.add_header('Authorization', 'Basic ' + self.config.bing_azure_key)
            response = urllib2.urlopen(request)
            data = json.loads(response.read())
            for image in data['d']['results'][:5]:
                poster = Poster()
                poster.uuid = uuid4().hex
                poster.artist = artist_id
                poster.artist_name = artist_name
                poster.origin = image['SourceUrl']
                poster.url = image['MediaUrl']
                poster.thumbnail = image['Thumbnail']['MediaUrl']
                poster.save()
            # saving whole query for later
            pu_log = PosterUnformated()
            pu_log.artist = artist_id
            pu_log.artist_name = artist_name
            pu_log.data = json.dumps(data)
            pu_log.save()
            return True
        except:
            poster = Poster()
            poster.uuid = uuid4().hex
            poster.artist = artist_id
            poster.artist_name = artist_name
            poster.origin = 'http://fake.com'
            poster.url = 'http://az616578.vo.msecnd.net/files/2015/12/19/6358614596527738711752945771_music.jpg'
            poster.thumbnail = 'http://az616578.vo.msecnd.net/files/2015/12/19/6358614596527738711752945771_music.jpg'
            poster.save()
            return True

    # Songs
    def song_search_fm(self):
        try:
            r = request.get_json()
            url = 'http://ws.audioscrobbler.com/2.0/?method=track.search&track=' + r['term'] +  '&api_key=' + self.config.last_fm_key + '&format=json&limit=29'
            response = urllib.urlopen(url)
            data = json.loads(response.read())
            return jsonify({"result": data['results']['trackmatches']['track']})
        except:
            return jsonify({"error": "Bad request"})

    def song_get_fm_mbid(self, mbid):
        try:
            url = 'http://ws.audioscrobbler.com/2.0/?method=track.getInfo&mbid=' + mbid + '&api_key=' + self.config.last_fm_key+'&format=json'
            response = urllib.urlopen(url)
            return json.loads(response.read())
        except:
            return None

    def song_get_fm(self, artist, name):
        try:
            url = 'http://ws.audioscrobbler.com/2.0/?method=track.getInfo&track=' + name + '&artist=' + artist + '&api_key=' + self.config.last_fm_key+'&format=json'
            response = urllib.urlopen(url)
            return json.loads(response.read())
        except:
            return None

    def artist_get_fm(self, mbid):
        try:
            url = 'http://ws.audioscrobbler.com/2.0/?method=artist.getInfo&mbid=' + mbid + '&api_key=' + self.config.last_fm_key+'&format=json'
            response = urllib.urlopen(url)
            # print url
            return json.loads(response.read())
        except:
            return None

    def album_get_create(self, query, artist):
        album = Album()
        album.uuid = query['mbid']
        album.name = query['title'].encode('utf-8')
        album.artist = artist
        try:
            album.thumb_small = query['image'][0]['#text']
            album.thumb_medium = query['image'][1]['#text']
            album.thumb_large = query['image'][2]['#text']
        except:
            pass
        try:
            album.thumb_extra = query['album']['image'][3]['#text']
        except:
            pass
        try:
            album.save()
            AppLog.make(101, 'Added album ' + str(album.id) + ' - ' + str(album.name))
            return album
        except IntegrityError:
            return Album.get(Album.uuid == album.uuid)
        except:
            return None


    def artist_search_create(self, artist_mbid):
        query = self.artist_get_fm(artist_mbid)
        if(query is None) or ('error' in query):
            AppLog.make(400, 'Artist not found: ' + artist_mbid)
            return Artist.get(Artist.id == UNKNOWN_ARTIST_ID)
        else:
            query = query['artist']
            artist = Artist()
            artist.uuid = query['mbid']
            artist.name = query['name']
            try:
                artist.thumb_small = query['image'][0]['#text']
                artist.thumb_medium = query['image'][1]['#text']
                artist.thumb_large = query['image'][2]['#text']
            except:
                pass
            try:
                artist.thumb_extra = query['image'][3]['#text']
            except:
                pass
            try:
                artist.save()
                AppLog.make(100, 'Added artist ' + str(artist.id) + ' - ' + artist.name)
                return artist
            except IntegrityError:
                return Artist.get(Artist.uuid == artist.uuid)
            except:
                return None

    def song_search_get(self):
        try:
            r = request.get_json()
            mbid = r['mbid'].encode('utf-8')
            artist = r['artist'].encode('utf-8')
            name = r['name'].encode('utf-8')
        except:
            return jsonify({"error": "Bad request"})
        try:
            song = Song.get_song(mbid, artist, name)
        except DoesNotExist:
            song = self.song_search_create(mbid, artist, name)
            if song is None:
                return jsonify({"error": "Song not found"})
        PlaylistSong.add_song(session['playlist_id'], current_user.id, song.id)
        return jsonify({"result": name})

    def song_search_create(self, mbid, artistname, songname):
        if len(mbid):
            query = self.song_get_fm_mbid(mbid)
        else:
            query = self.song_get_fm(artistname, songname)
            mbid = 'z-' + str(uuid4())
        if (query is None) or ('error' in query):
            AppLog.make(400, 'Song not found: ' + mbid)
            return None
        else:
            query = query['track']
            query['name'] = query['name'].encode('utf-8')
            query['artist']['name'] = query['artist']['name'].encode('utf-8')
            # checking the artist if not exist
            try:
                artist = Artist.get(Artist.uuid == query['artist']['mbid'])
            except KeyError:
                #unknown artist
                artist = Artist.get(Artist.id == UNKNOWN_ARTIST_ID)
            except DoesNotExist:
                #create new artist
                artist = self.artist_search_create(query['artist']['mbid'])
            # checking the posters
            try:
                Poster.get(Poster.artist_name == artist.name)
            except DoesNotExist:
                self.poster_create_search(artist.name, artist.id)
                AppLog.make(107, 'Added posters for ' + artist.name)
            # checking the album if not exist
            try:
                album = Album.get(Album.uuid == query['album']['mbid'])
            except KeyError:
                album = Album.get(Album.id == UNKNOWN_ALBUM_ID)
            except DoesNotExist:
                album = self.album_get_create(query['album'], artist.id)
            # saving the song if not exist
            url = 'https://www.googleapis.com/youtube/v3/search?'
            params = {
                "q": query['artist']['name'] + ' ' + query['name'],
                "part": "id",
                "maxResults": "3",
                "type": "video",
                "key": self.config.google_api_key
            }
            try:
                params = urllib.urlencode(params)
                response = urllib.urlopen(url + params)
                data = json.loads(response.read())
                song = Song()
                song.uuid = mbid
                song.name = songname
                song.video_id = data['items'][0]['id']['videoId']
                try:
                    song.video_id2 = data['items'][1]['id']['videoId']
                except:
                    pass
                try:
                    song.video_id3 = data['items'][2]['id']['videoId']
                except:
                    pass
                song.duration = int(query['duration'])
                song.album = album.id
                song.artist = artist.id
                song.artist_name = artistname
                song.save()
                AppLog.make(103, 'Added song: ' + str(song.id) + ' - ' + song.name)
                return song
            except:
                AppLog.make(406, 'Exception in youtube query on: ' + url + params)
                return None

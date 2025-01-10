# MusicFlask

MusicFlask is a music playlist management app built with Python, Flask, and Peewee. It allows users to create and share music playlists with their friends. The app uses external APIs to search for songs, add tracks to playlists, and set album covers.

## Features

- **Create and manage playlists**: Users can create playlists and add songs to them.
- **Search for songs**: The app integrates with the Last.fm API to search for song details based on user input.
- **Add songs from YouTube**: The app uses the Google YouTube API to add songs to playlists.
- **Album cover search**: Album covers for songs are fetched using the Bing Image Search API.

## Prerequisites

Before running the app, you need to have the following:

- Python 3.x
- Flask
- Peewee
- API keys for Last.fm, Google YouTube, and Bing Image Search APIs

### Required Python packages

To install the necessary packages, use the following command:

```bash
pip install -r requirements.txt
```

### Required api keys

- include/client_secret.json with google oauth keys
- settings.py with last.fm, bing and youtube api keys

## Contributing

Feel free to submit issues, pull requests, and suggestions for improvements!

How to Contribute:

- Fork the repository.
- Create a feature branch.
- Commit your changes.
- Push to the branch.
- Open a pull request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

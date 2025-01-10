from model import *
from interface import *
from scrapy.selector import Selector
import string

"""
letters = dict.fromkeys(string.ascii_lowercase, 0)
for letter in letters:
    url = 'http://www.billboard.com/artists/' + letter
    response = urllib.urlopen(url)
    data = response.read()
    page = ArtistPage()
    page.letter = letter;
    page.body = data
    page.parsed = 0
    page.save()
    print ' letter added ' + letter
"""

count = 0
letters = dict.fromkeys(string.ascii_lowercase, 0)
for letter in letters:
    try:
        print letter + ' ' + str(count)
        p = ArtistPage.get(ArtistPage.letter == letter)
        r = Selector(text=p.body).xpath('//a[contains(@href, "/artist/")]/text()').extract()
        for name in r:
            artist = Artists()
            artist.name = name.encode('utf-8')
            artist.state = 0
            artist.save()
            count = count + 1
    except:
        print 'error: ' + letter
        pass



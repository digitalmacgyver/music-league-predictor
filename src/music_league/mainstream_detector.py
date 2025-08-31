#!/usr/bin/env python3
"""
Enhanced Mainstream Song Detection System

Identifies mainstream/popular songs using multiple criteria:
- Artist popularity and fame level
- Song popularity scores from Spotify
- Stream counts and chart positions
- Classic radio staples and wedding songs
- Historical chart performance
"""

import logging
import re
from typing import Dict, Set, Tuple, Optional, List
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


class MainstreamDetector:
    """Advanced mainstream song detection with multiple signals"""
    
    def __init__(self, spotify_client: Optional[spotipy.Spotify] = None):
        """Initialize with optional Spotify client for popularity checks"""
        self.spotify = spotify_client
        if not self.spotify:
            try:
                self.spotify = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials())
            except:
                logger.warning("Spotify client not available for popularity checks")
                self.spotify = None
        
        # Initialize mainstream databases
        self._init_mainstream_artists()
        self._init_mainstream_songs()
        self._init_radio_staples()
    
    def _init_mainstream_artists(self):
        """Initialize comprehensive mainstream artist list"""
        
        # Tier 1: Global superstars (auto-reject most of their catalog)
        self.tier1_artists = {
            # Modern pop titans
            'taylor swift', 'ed sheeran', 'adele', 'drake', 'beyonce', 'beyoncé',
            'justin bieber', 'ariana grande', 'billie eilish', 'post malone', 
            'the weeknd', 'dua lipa', 'harry styles', 'olivia rodrigo', 'bad bunny',
            'bruno mars', 'lady gaga', 'rihanna', 'shawn mendes', 'doja cat',
            
            # Classic rock legends
            'the beatles', 'the rolling stones', 'led zeppelin', 'pink floyd',
            'queen', 'ac/dc', 'eagles', 'fleetwood mac', 'u2', 'metallica',
            'guns n roses', "guns n' roses", 'bon jovi', 'aerosmith', 'kiss',
            
            # Pop/Rock icons
            'michael jackson', 'madonna', 'prince', 'david bowie', 'elton john',
            'billy joel', 'bruce springsteen', 'bob dylan', 'neil young',
            'paul mccartney', 'john lennon', 'stevie wonder', 'whitney houston',
            
            # Modern rock mainstream
            'coldplay', 'imagine dragons', 'maroon 5', 'onerepublic', 'nickelback',
            'foo fighters', 'red hot chili peppers', 'green day', 'linkin park',
            
            # Hip-hop/R&B mainstream
            'kanye west', 'jay-z', 'eminem', 'kendrick lamar', 'cardi b',
            'megan thee stallion', 'travis scott', 'lil nas x', 'nicki minaj',
            
            # Country mainstream
            'morgan wallen', 'luke combs', 'blake shelton', 'carrie underwood',
            'kenny chesney', 'florida georgia line', 'luke bryan', 'jason aldean'
        }
        
        # Tier 2: Very popular but might have deep cuts worth considering
        self.tier2_artists = {
            'radiohead', 'nirvana', 'pearl jam', 'rem', 'r.e.m.', 'the who',
            'the doors', 'grateful dead', 'bob marley', 'johnny cash',
            'the police', 'sting', 'genesis', 'phil collins', 'peter gabriel',
            'the cure', 'depeche mode', 'new order', 'joy division',
            'arctic monkeys', 'the killers', 'kings of leon', 'mgmt',
            'tame impala', 'the strokes', 'vampire weekend', 'arcade fire',
            'frank ocean', 'tyler the creator', 'childish gambino', 'sza',
            'the lumineers', 'mumford & sons', 'of monsters and men'
        }
        
    def _init_mainstream_songs(self):
        """Initialize definitive mainstream song list"""
        
        # Songs that are auto-rejected regardless of context
        self.banned_songs = {
            # Universal mega-hits
            ('bohemian rhapsody', 'queen'),
            ('stairway to heaven', 'led zeppelin'),
            ('imagine', 'john lennon'),
            ('hotel california', 'eagles'),
            ('sweet child o mine', "guns n' roses"),
            ("sweet child o' mine", "guns n' roses"),
            ('dont stop believin', 'journey'),
            ("don't stop believin'", 'journey'),
            ('gimme shelter', 'the rolling stones'),
            ('gimme shelter', 'rolling stones'),
            ('gimmie shelter', 'the rolling stones'),  # Common typo
            ('gimmie shelter', 'rolling stones'),  # Common typo
            ('sympathy for the devil', 'the rolling stones'),
            ('satisfaction', 'the rolling stones'),
            ("(i can't get no) satisfaction", 'the rolling stones'),
            ('paint it black', 'the rolling stones'),
            ('start me up', 'the rolling stones'),
            ('jumpin jack flash', 'the rolling stones'),
            ("jumpin' jack flash", 'the rolling stones'),
            ('brown sugar', 'the rolling stones'),
            
            # Beatles essentials
            ('hey jude', 'the beatles'),
            ('let it be', 'the beatles'),
            ('yesterday', 'the beatles'),
            ('come together', 'the beatles'),
            ('here comes the sun', 'the beatles'),
            ('twist and shout', 'the beatles'),
            ('i want to hold your hand', 'the beatles'),
            ('help!', 'the beatles'),
            ('all you need is love', 'the beatles'),
            
            # Zeppelin classics
            ('whole lotta love', 'led zeppelin'),
            ('black dog', 'led zeppelin'),
            ('rock and roll', 'led zeppelin'),
            ('immigrant song', 'led zeppelin'),
            ('kashmir', 'led zeppelin'),
            ('ramble on', 'led zeppelin'),
            
            # Pink Floyd essentials  
            ('another brick in the wall', 'pink floyd'),
            ('wish you were here', 'pink floyd'),
            ('comfortably numb', 'pink floyd'),
            ('money', 'pink floyd'),
            ('time', 'pink floyd'),
            
            # Modern streaming giants
            ('shape of you', 'ed sheeran'),
            ('blinding lights', 'the weeknd'),
            ('someone like you', 'adele'),
            ('rolling in the deep', 'adele'),
            ('hello', 'adele'),
            ('uptown funk', 'mark ronson'),
            ('thinking out loud', 'ed sheeran'),
            ('perfect', 'ed sheeran'),
            ('bad guy', 'billie eilish'),
            ('drivers license', 'olivia rodrigo'),
            ('good 4 u', 'olivia rodrigo'),
            ('flowers', 'miley cyrus'),
            ('anti-hero', 'taylor swift'),
            ('shake it off', 'taylor swift'),
            ('blank space', 'taylor swift'),
            
            # Karaoke/Wedding classics
            ('mr. brightside', 'the killers'),
            ('sweet caroline', 'neil diamond'),
            ('livin on a prayer', 'bon jovi'),
            ("livin' on a prayer", 'bon jovi'),
            ('dont stop me now', 'queen'),
            ("don't stop me now", 'queen'),
            ('we will rock you', 'queen'),
            ('we are the champions', 'queen'),
            ('dancing queen', 'abba'),
            ('i wanna dance with somebody', 'whitney houston'),
            ('i will always love you', 'whitney houston'),
            ('september', 'earth wind & fire'),
            ('september', 'earth, wind & fire'),
        }
        
    def _init_radio_staples(self):
        """Songs that appear on every classic rock/pop radio station"""
        
        self.radio_staples_keywords = {
            # Title patterns that indicate radio hits
            'greatest hits', 'best of', 'radio edit', 'single version',
            'remastered', 'anniversary edition'
        }
        
        # Partial title matches for common radio songs
        self.radio_staple_titles = {
            'sweet home alabama', 'free bird', 'more than a feeling',
            'carry on wayward son', 'dust in the wind', 'hold the line',
            'africa', 'rosanna', 'eye of the tiger', 'final countdown',
            'jump', 'panama', 'runnin with the devil', 'you really got me',
            'pour some sugar', 'photograph', 'rock of ages',
            'here i go again', 'is this love', 'still of the night',
            'every breath you take', 'roxanne', 'message in a bottle',
            'walk this way', 'dream on', 'sweet emotion',
            'back in black', 'thunderstruck', 'highway to hell',
            'you shook me all night long', 'dirty deeds',
            'crazy train', 'mr. crowley', 'paranoid', 'iron man',
            'smoke on the water', 'highway star', 'hush',
            'born to be wild', 'magic carpet ride',
            'take it easy', 'desperado', 'life in the fast lane',
            'go your own way', 'dreams', 'the chain', 'rhiannon',
            'dont fear the reaper', "don't fear the reaper", 'burnin for you',
            'come sail away', 'renegade', 'too much time on my hands',
            'juke box hero', 'cold as ice', 'urgent', 'waiting for a girl like you'
        }
    
    def is_mainstream(self, title: str, artist: str, 
                     spotify_id: Optional[str] = None,
                     check_spotify: bool = True) -> Tuple[bool, str]:
        """
        Comprehensive mainstream detection
        
        Returns:
            (is_mainstream, reason) - True if song is mainstream, with explanation
        """
        
        # Clean inputs
        title_clean = self._clean_text(title)
        artist_clean = self._clean_text(artist)
        
        # Check 1: Banned songs list
        if (title_clean, artist_clean) in self.banned_songs:
            return True, "Song is on definitive mainstream/banned list"
        
        # Also check with 'the' prefix removed
        artist_no_the = re.sub(r'^the\s+', '', artist_clean)
        if (title_clean, artist_no_the) in self.banned_songs:
            return True, "Song is on definitive mainstream/banned list"
        
        # Check 2: Tier 1 artists (most songs are mainstream)
        if artist_clean in self.tier1_artists or artist_no_the in self.tier1_artists:
            # For tier 1 artists, check if it's a known hit
            if self._is_artist_hit(title_clean, artist_clean):
                return True, f"Popular song by mainstream artist {artist}"
            # Even non-hits from these artists might be too mainstream
            if check_spotify and spotify_id and self.spotify:
                popularity = self._get_spotify_popularity(spotify_id)
                if popularity and popularity > 50:  # Lower threshold for tier 1
                    return True, f"Song by mainstream artist {artist} with {popularity}% popularity"
        
        # Check 3: Radio staples by title
        if self._is_radio_staple(title_clean):
            return True, "Classic radio staple"
        
        # Check 4: Spotify popularity (if available)
        if check_spotify and spotify_id and self.spotify:
            popularity = self._get_spotify_popularity(spotify_id)
            if popularity:
                if popularity > 70:  # Very popular on Spotify
                    return True, f"High Spotify popularity ({popularity}%)"
                elif popularity > 60 and artist_clean in self.tier2_artists:
                    return True, f"Popular song ({popularity}%) by well-known artist"
        
        # Check 5: Tier 2 artists - only their biggest hits
        if artist_clean in self.tier2_artists or artist_no_the in self.tier2_artists:
            if self._is_artist_hit(title_clean, artist_clean):
                return True, f"Hit song by popular artist {artist}"
        
        return False, "Not detected as mainstream"
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text for matching"""
        if not text:
            return ""
        
        # Lowercase and strip
        text = text.lower().strip()
        
        # Remove featuring artists
        text = re.sub(r'\s*\(feat\..*?\)', '', text)
        text = re.sub(r'\s*\[feat\..*?\]', '', text)
        text = re.sub(r'\s*ft\..*$', '', text)
        text = re.sub(r'\s*featuring.*$', '', text)
        
        # Remove version indicators
        text = re.sub(r'\s*-\s*(remaster|remix|acoustic|live|demo|radio edit|single version).*$', '', text)
        text = re.sub(r'\s*\((remaster|remix|acoustic|live|demo|radio edit|single version).*\)', '', text)
        
        # Normalize punctuation
        text = text.replace("'", "'")
        text = text.replace("`", "'")
        text = text.replace("_", " ")
        
        return text.strip()
    
    def _is_radio_staple(self, title: str) -> bool:
        """Check if song title matches known radio staples"""
        for staple in self.radio_staple_titles:
            if staple in title or title in staple:
                return True
        return False
    
    def _is_artist_hit(self, title: str, artist: str) -> bool:
        """Check if this is a known hit for the artist"""
        
        # Known hits database (partial - would be expanded)
        artist_hits = {
            'the rolling stones': ['satisfaction', 'paint it black', 'gimme shelter', 
                                 'sympathy for the devil', 'start me up', 'angie',
                                 'brown sugar', 'jumpin jack flash', 'wild horses'],
            'the beatles': ['hey jude', 'let it be', 'yesterday', 'help', 
                          'come together', 'here comes the sun', 'twist and shout'],
            'led zeppelin': ['stairway', 'whole lotta love', 'black dog', 
                           'immigrant song', 'kashmir', 'rock and roll'],
            'pink floyd': ['another brick', 'wish you were here', 'money', 
                         'comfortably numb', 'time', 'echoes'],
            'queen': ['bohemian', 'we will rock', 'we are the champions', 
                    'dont stop me', 'another one bites', 'somebody to love'],
            'taylor swift': ['shake it off', 'blank space', 'love story', 
                           'you belong with me', 'anti-hero', 'bad blood'],
            'ed sheeran': ['shape of you', 'thinking out loud', 'perfect', 
                         'photograph', 'castle on the hill', 'shivers'],
        }
        
        # Check if artist has known hits
        artist_no_the = re.sub(r'^the\s+', '', artist)
        hits = artist_hits.get(artist, []) or artist_hits.get(artist_no_the, [])
        
        # Check if title contains any hit keywords
        for hit in hits:
            if hit in title:
                return True
        
        return False
    
    def _get_spotify_popularity(self, spotify_id: str) -> Optional[int]:
        """Get Spotify popularity score for a track"""
        if not self.spotify or not spotify_id:
            return None
        
        try:
            track = self.spotify.track(spotify_id)
            return track.get('popularity', 0)
        except Exception as e:
            logger.debug(f"Could not get Spotify popularity: {e}")
            return None
    
    def get_mainstream_score(self, title: str, artist: str, 
                            spotify_id: Optional[str] = None) -> float:
        """
        Get a mainstream score from 0.0 to 1.0
        Higher scores = more mainstream
        """
        
        score = 0.0
        title_clean = self._clean_text(title)
        artist_clean = self._clean_text(artist)
        artist_no_the = re.sub(r'^the\s+', '', artist_clean)
        
        # Banned songs = max score
        if (title_clean, artist_clean) in self.banned_songs or \
           (title_clean, artist_no_the) in self.banned_songs:
            return 1.0
        
        # Tier 1 artist = high base score
        if artist_clean in self.tier1_artists or artist_no_the in self.tier1_artists:
            score += 0.5
            if self._is_artist_hit(title_clean, artist_clean):
                score += 0.3
        
        # Tier 2 artist = moderate base score  
        elif artist_clean in self.tier2_artists or artist_no_the in self.tier2_artists:
            score += 0.3
            if self._is_artist_hit(title_clean, artist_clean):
                score += 0.3
        
        # Radio staple = high score
        if self._is_radio_staple(title_clean):
            score += 0.4
        
        # Add Spotify popularity if available
        if spotify_id and self.spotify:
            popularity = self._get_spotify_popularity(spotify_id)
            if popularity:
                # Convert 0-100 to 0.0-0.4 contribution
                score += (popularity / 100.0) * 0.4
        
        return min(1.0, score)
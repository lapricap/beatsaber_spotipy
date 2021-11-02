# This code to try to auto populate era and genre of maps for dancesaber.com
# will be pulling maps from a sheet that techbutterfly has provided

import csv
import requests
import time
import re
# import json

rows = []
map_hashes = []
songnames = []
artistnames = []
newcsvrows = []

token = 'INSERT SPOTIFY TOKEN HERE'

def date_to_era(songdate):
    songyear = int(songdate[:4])
    if(songyear<1960):
        return "Pre-60's"
    if(songyear<1980):
        return "1970s"
    if(songyear<1990):
        return "1980s"
    if(songyear<2000):
        return "1990s"
    return "2000s"


with open("aevyn_shorterlist.csv",'r') as file:
    csvreader = csv.reader(file)
    header = next(csvreader)
    for row in csvreader:
        # if(len(songnames)>4):
            # break
        songnames.append(row[2])
        # print('excel song name: ' + row[2])
        map_hashes.append(row[0])
        mappername = row[1]
        map_hash = row[0]
        response = requests.get("https://api.beatsaver.com/maps/hash/"+map_hash)
        excelsongname = row[2]
        print('beatsaver reponse: ' + str(response.status_code))

        if(response.status_code!=200):
            print(excelsongname)
            newcsvrows.append([excelsongname,'',mappername,map_hash,'','','',''])
            continue

        bsaberSongId = response.json()['id']
        artistName = response.json()['metadata']['songSubName']
        if(not artistName):
            newcsvrows.append([excelsongname,'',mappername,map_hash,'','','',''])
            continue
        songname = response.json()['metadata']['songName'] 
        songNameNoBrackets = re.sub("([\(\[]).*?([\)\]])", "", songname) 
        songname = songNameNoBrackets
        print('songname: ' + songname)
        # print('songnamenobrackets: ' + songNameNoBrackets)
        print('artistname: ' + artistName)

        # make request to spotipy
        # artistname is pulled from songsubname instead of songauthorname
        spotifySearchResponse = requests.get("https://api.spotify.com/v1/search?q="+songname+" "+artistName+"&type=track",headers={'accept':"application/json",'content-type':'application/json','authorization':'Bearer '+token})
        print('spotify response: '+ str(spotifySearchResponse.status_code)+"\n")
        # print(spotifySearchResponse.json())
        if(not spotifySearchResponse.json()['tracks']['items']):
            newcsvrows.append([songname,'',mappername,map_hash,'','','',''])
            continue
        spotifySearchItem = spotifySearchResponse.json()['tracks']['items'][0]
        spotifyTrackName = spotifySearchItem['name'] 
        spotifyTrackURL = spotifySearchItem['external_urls']['spotify']
        spotifyTrackID = spotifySearchItem['id']
        spotifyArtists = spotifySearchItem['artists']
        spotifyArtistIDs = [a['id'] for a in spotifyArtists] 
        spotifyTrackReleaseDate = spotifySearchItem['album']['release_date']
        era = date_to_era(spotifyTrackReleaseDate)

        genres = set() 
        # get genre(s) from artist(s)
        for artistID in spotifyArtistIDs:
            spotifyArtistResponse = requests.get("https://api.spotify.com/v1/artists/"+artistID,headers={'accept':"application/json",'content-type':'application/json','authorization':'Bearer '+token})
            # print(spotifyArtistResponse.json())
            genres |= set(spotifyArtistResponse.json()['genres'])
        genres=sorted(genres)

        # song,artist, mapper, hash,date, era, genres, spotify url, bsaberurl
        newcsvrows.append([excelsongname,artistName,mappername,map_hash,spotifyTrackReleaseDate,era,"|".join(genres),'=HYPERLINK("'+spotifyTrackURL+'")','=HYPERLINK("https://bsaber.com/songs/'+bsaberSongId+'/")'])
        # write year, genre, url of found track to CSV (need to make new column for url) 

# write to csv
with open('newcsv.csv','w',newline='') as csvfile:
    csvwriter = csv.writer(csvfile)
    csvwriter.writerow(['song','artist','mapper','hash','date','era','genres','url'])
    csvwriter.writerows(newcsvrows)
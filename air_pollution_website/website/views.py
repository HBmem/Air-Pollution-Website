import csv
import re
import simplekml
import io

from django.shortcuts import render, redirect
from django.contrib import messages

# Create your views here.
def home(request):
    if request.method == 'GET':
        return render(request, "website/home.html")

    elif request.method == 'POST':
        thefile = request.FILES['fileName']
        decoded_file = thefile.read().decode('utf-8').splitlines()
        results = []
        inputfile = csv.reader(decoded_file)
        next(inputfile)  # Go past the header

        for row in inputfile: # each row is a list
            results.append(row)


        kml = simplekml.Kml()
        van = kml.newlinestring(name="Van path")
        van.altitudemode = simplekml.AltitudeMode.relativetoground

        # creating folders for the kml file and creating dictionaries for linesegments
        benfol = kml.newfolder(name='BEN peaks')
        benDict = {}
        ch4fol = kml.newfolder(name='CH4 peaks')
        ch4Dict = {}

        # dictionary keys
        x = 0
        y = 0
        
        
        for row in results:
            van.coords.addcoordinates([(row[1], row[2])])
            van.style.linestyle.color = simplekml.Color.white
            van.style.linestyle.width = 1

            # start of BEN
            if row[3] != '0':
                benDict[x] = row[1], row[2], row[3]
                id = row[3]
                x += 1

            if row[3] == '0' and bool(benDict) is True:
                ben = benfol.newlinestring(name="BEN peak: " + id)
                ben.altitudemode = simplekml.AltitudeMode.relativetoground
                ben.style.linestyle.color = simplekml.Color.blue
                ben.style.linestyle.width = 5

                for benKey in benDict:
                    benValues = benDict.values()
                    benValues = list(benValues)
                    ben.coords.addcoordinates([(benValues[benKey][0], benValues[benKey][1], benValues[benKey][2])])

                benDict = {}
                x = 0
            # end of BEN

            # start of CH4
            if row[4] != '0':
                ch4Dict[y] = row[1], row[2], row[4]
                id = row[4]
                y += 1

            if row[4] == '0' and bool(ch4Dict) is True:
                ch4 = ch4fol.newlinestring(name="CH4 peak: " + id)
                ch4.altitudemode = simplekml.AltitudeMode.relativetoground
                ch4.style.linestyle.color = simplekml.Color.yellow
                ch4.style.linestyle.width = 5

                for key in ch4Dict:
                    ch4Values = ch4Dict.values()
                    ch4Values = list(ch4Values)
                    ch4.coords.addcoordinates([(ch4Values[key][0], ch4Values[key][1], ch4Values[key][2])])

                ch4Dict = {}
                y = 0
            # end of CH4


        kml.save('practice3.kml')
        context = {}

        return render(request, "website/show.html", context)
    else:
        return render(request, "website/home.html")

def show(request):
    return render(request, "website/show.html")
    
import csv, re, simplekml, io, openpyxl, numpy as np, os
from website.models import Location, kmlFile
from django.core.files import File
from pathlib import Path
from django.http import FileResponse

from django.shortcuts import render, redirect
from django.contrib import messages

# Create your views here.
def home(request):
    if request.method == 'GET':
        return render(request, "website/home.html")
    elif request.method == 'POST':
        thefile = request.FILES.get('fileName', None)
        thewind = request.FILES.get('windName', None)
        decoded_file = thefile.read().decode('utf-8').splitlines()
        windList = None
        if thewind is not None:
            inputwind = openpyxl.load_workbook(thewind)
            ws = inputwind.active
            windList = []
            for row in ws.iter_rows(values_only=True): # each row is a list
                windList.append(row)
            windList.pop(0)
        inputfile = csv.reader(decoded_file)
        next(inputfile)  # Go past the header
        xcoord = []
        ycoord = []
        ben = []
        ch = []
        h2 = []
        to = []
        vo = []
        xym = []
        xyp = []

        for row in inputfile: # each row is a list
            xcoord.append(row[0])
            ycoord.append(row[1])
            ben.append(float(row[2]))
            ch.append(float(row[3]))
            h2.append(float(row[4]))
            to.append(float(row[5]))
            vo.append(float(row[6]))
            xym.append(float(row[7]))
            xyp.append(float(row[8]))
        
        # by default, lag = 30, threshold = 2, and influence = 0
        if request.POST.get('lag'):
            lag = int(request.POST.get('lag'))
        else:
            lag = 30

        if request.POST.get('threshold'):
            threshold = int(request.POST.get('threshold'))
        else:
            threshold = 2

        if request.POST.get('influence'):
            influence = int(request.POST.get('influence'))
        else:
            influence = 0

        outputBen = transform(ben, 'BEN', lag, threshold, influence)
        outputCh4 = transform(ch, 'CH4', lag, threshold, influence)
        outputH2s = transform(h2, 'H2S', lag, threshold, influence)
        outputTol = transform(to, 'TOL', lag, threshold, influence)
        outputVoc = transform(vo, 'VOC', lag, threshold, influence)
        outputXym = transform(xym, 'XYM', lag, threshold, influence)
        outputXyp = transform(xyp, 'XYP', lag, threshold, influence)
        final = np.column_stack((xcoord, ycoord, outputBen, outputCh4, outputH2s, outputTol, outputVoc, outputXym, outputXyp))

        kml = visualize(final, windList)
        kml.save('website/conversion.kml')

        module_dir = os.path.dirname(__file__)
        file_path = os.path.join(module_dir, 'conversion.kml')
        
        path = Path(file_path)
        convertedFile = kmlFile(name=path.name)
        context = {}
        
        with path.open(mode='rb') as f:
            print(path.name)
            convertedFile.file = File(f, name=path.name)
            convertedFile.save()
            context = {"file": convertedFile}
            request.session['fileID'] = convertedFile.id

        return render(request, "website/show.html", context)
    else:
        return render(request, "website/home.html")

def download(request):
    fileID = request.session.get('fileID')
    file = kmlFile.objects.get(id=fileID)
    return FileResponse(file.file, as_attachment=True)


def show(request):
    return render(request, "website/show.html")

def visualize(inputfile, windList):
    results = []
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
    h2sfol = kml.newfolder(name='H2S peaks')
    h2sDict = {}
    tolfol = kml.newfolder(name='TOL peaks')
    tolDict = {}
    vocfol = kml.newfolder(name='VOC peaks')
    vocDict = {}
    xymfol = kml.newfolder(name='XYM peaks')
    xymDict = {}
    xypfol = kml.newfolder(name='XYP peaks')
    xypDict = {}
    buidling = kml.newfolder(name='High pollution locations')
    for location in Location.objects.all():
        buildings = buidling.newpoint(name= location.name, coords = [(location.x_coord, location.y_coord)])

    if windList is not None:
        windFol = kml.newfolder(name='Wind directions')
        for row in windList:
            split = row[3].split()
            wind_point = windFol.newpoint(name= split[0]+""+split[1], coords = [(row[0], row[1])])
            wind_point.altitudemode = simplekml.AltitudeMode.relativetoground
            wind_point.style.labelstyle.color = simplekml.Color.white
            wind_point.iconstyle.icon.href = 'http://maps.google.com/mapfiles/kml/shapes/arrow.png'
            wind_point.style.iconstyle.scale = 0.5
            wind_point.iconstyle.heading = float(split[2])
    
    # dictionary keys
    x = 0
    y = 0
    z = 0
    a = 0
    b = 0
    c = 0
    d = 0

    #iterate through array
    for row in results:
        van.coords.addcoordinates([(row[0], row[1])])
        van.style.linestyle.color = simplekml.Color.white
        van.style.linestyle.width = 1

        # start of BEN
        if row[2] != '0.0':
            if x == 0:
                benDict[x] = row[0], row[1], 0
                x += 1
            benDict[x] = row[0], row[1], row[2]
            benid = row[2]
            x += 1

        if row[2] == '0.0' and bool(benDict) is True:
            if float(benid) > 20:
                benHigh = benfol.newlinestring(name="BEN peak: " + benid)
                benHigh.altitudemode = simplekml.AltitudeMode.relativetoground
                benHigh.style.linestyle.color = simplekml.Color.darkblue
                benHigh.style.linestyle.width = 5
                for benKey in benDict:
                    benValues = benDict.values()
                    benValues = list(benValues)
                    benHigh.coords.addcoordinates([(benValues[benKey][0], benValues[benKey][1], benValues[benKey][2])])
                benHigh.coords.addcoordinates([(benValues[benKey][0], benValues[benKey][1], 0)])

            elif float(benid) < 10:
                benLow = benfol.newlinestring(name="BEN peak: " + benid)
                benLow.altitudemode = simplekml.AltitudeMode.relativetoground
                benLow.style.linestyle.color = simplekml.Color.lightblue
                benLow.style.linestyle.width = 5
                for benKey in benDict:
                    benValues = benDict.values()
                    benValues = list(benValues)
                    benLow.coords.addcoordinates([(benValues[benKey][0], benValues[benKey][1], benValues[benKey][2])])
                benLow.coords.addcoordinates([(benValues[benKey][0], benValues[benKey][1], 0)])

            else:
                ben = benfol.newlinestring(name="BEN peak: " + benid)
                ben.altitudemode = simplekml.AltitudeMode.relativetoground
                ben.style.linestyle.color = simplekml.Color.blue
                ben.style.linestyle.width = 5
                for benKey in benDict:
                    benValues = benDict.values()
                    benValues = list(benValues)
                    ben.coords.addcoordinates([(benValues[benKey][0], benValues[benKey][1], benValues[benKey][2])])
                ben.coords.addcoordinates([(benValues[benKey][0], benValues[benKey][1], 0)])

            benDict = {}
            x = 0
        # end of BEN

        # start of CH4
        if row[3] != '0.0':
            if y == 0:
                ch4Dict[y] = row[0], row[1], 0
                y += 1
            ch4Dict[y] = row[0], row[1], row[3]
            ch4id = row[3]
            y += 1

        if row[3] == '0.0' and bool(ch4Dict) is True:
            if float(ch4id) > 20:
                ch4High = ch4fol.newlinestring(name="CH4 peak: " + ch4id)
                ch4High.altitudemode = simplekml.AltitudeMode.relativetoground
                ch4High.style.linestyle.color = 'FF0C6F0C'
                ch4High.style.linestyle.width = 5
                for ch4Key in ch4Dict:
                    ch4Values = ch4Dict.values()
                    ch4Values = list(ch4Values)
                    ch4High.coords.addcoordinates([(ch4Values[ch4Key][0], ch4Values[ch4Key][1], ch4Values[ch4Key][2])])
                ch4High.coords.addcoordinates([(ch4Values[ch4Key][0], ch4Values[ch4Key][1], 0)])

            elif float(ch4id) < 10:
                ch4Low = ch4fol.newlinestring(name="CH4 peak: " + ch4id)
                ch4Low.altitudemode = simplekml.AltitudeMode.relativetoground
                ch4Low.style.linestyle.color = 'FF0C6F0C'
                ch4Low.style.linestyle.width = 5
                for ch4Key in ch4Dict:
                    ch4Values = ch4Dict.values()
                    ch4Values = list(ch4Values)
                    ch4Low.coords.addcoordinates([(ch4Values[ch4Key][0], ch4Values[ch4Key][1], ch4Values[ch4Key][2])])
                ch4Low.coords.addcoordinates([(ch4Values[ch4Key][0], ch4Values[ch4Key][1], 0)])

            else:
                ch4 = ch4fol.newlinestring(name="CH4 peak: " + ch4id)
                ch4.altitudemode = simplekml.AltitudeMode.relativetoground
                ch4.style.linestyle.color = 'FF14B714'
                ch4.style.linestyle.width = 5
                for ch4Key in ch4Dict:
                    ch4Values = ch4Dict.values()
                    ch4Values = list(ch4Values)
                    ch4.coords.addcoordinates([(ch4Values[ch4Key][0], ch4Values[ch4Key][1], ch4Values[ch4Key][2])])
                ch4.coords.addcoordinates([(ch4Values[ch4Key][0], ch4Values[ch4Key][1], 0)])

            ch4Dict = {}
            y = 0
        # end of CH4

        # start of H2S
        if row[4] != '0.0':
            if z == 0:
                h2sDict[z] = row[0], row[1], 0
                z += 1
            h2sDict[z] = row[0], row[1], row[4]
            h2sid = row[4]
            z += 1

        if row[4] == '0.0' and bool(h2sDict) is True:
            if float(h2sid) > 20:
                h2sHigh = h2sfol.newlinestring(name="H2S peak: " + h2sid)
                h2sHigh.altitudemode = simplekml.AltitudeMode.relativetoground
                h2sHigh.style.linestyle.color = simplekml.Color.darkred
                h2sHigh.style.linestyle.width = 5
                for h2sKey in h2sDict:
                    h2sValues = h2sDict.values()
                    h2sValues = list(h2sValues)
                    h2sHigh.coords.addcoordinates([(h2sValues[h2sKey][0], h2sValues[h2sKey][1], h2sValues[h2sKey][2])])
                h2sHigh.coords.addcoordinates([(h2sValues[h2sKey][0], h2sValues[h2sKey][1], 0)])

            elif float(h2sid) < 10:
                h2sLow = h2sfol.newlinestring(name="H2S peak: " + h2sid)
                h2sLow.altitudemode = simplekml.AltitudeMode.relativetoground
                h2sLow.style.linestyle.color = simplekml.Color.salmon
                h2sLow.style.linestyle.width = 5
                for h2sKey in h2sDict:
                    h2sValues = h2sDict.values()
                    h2sValues = list(h2sValues)
                    h2sLow.coords.addcoordinates([(h2sValues[h2sKey][0], h2sValues[h2sKey][1], h2sValues[h2sKey][2])])
                h2sLow.coords.addcoordinates([(h2sValues[h2sKey][0], h2sValues[h2sKey][1], 0)])

            else:
                h2s = h2sfol.newlinestring(name="H2S peak: " + h2sid)
                h2s.altitudemode = simplekml.AltitudeMode.relativetoground
                h2s.style.linestyle.color = simplekml.Color.red
                h2s.style.linestyle.width = 5
                for h2sKey in h2sDict:
                    h2sValues = h2sDict.values()
                    h2sValues = list(h2sValues)
                    h2s.coords.addcoordinates([(h2sValues[h2sKey][0], h2sValues[h2sKey][1], h2sValues[h2sKey][2])])
                h2s.coords.addcoordinates([(h2sValues[h2sKey][0], h2sValues[h2sKey][1], 0)])

            h2sDict = {}
            z = 0
        # end of H2S

        # start of TOL
        if row[5] != '0.0':
            if a == 0:
                tolDict[a] = row[0], row[1], 0
                a += 1
            tolDict[a] = row[0], row[1], row[5]
            tolid = row[5]
            a += 1

        if row[5] == '0.0' and bool(tolDict) is True:
            if float(tolid) > 20:
                tolHigh = tolfol.newlinestring(name="TOL peak: " + tolid)
                tolHigh.altitudemode = simplekml.AltitudeMode.relativetoground
                tolHigh.style.linestyle.color = simplekml.Color.darkviolet
                tolHigh.style.linestyle.width = 5
                for tolKey in tolDict:
                    tolValues = tolDict.values()
                    tolValues = list(tolValues)
                    tolHigh.coords.addcoordinates([(tolValues[tolKey][0], tolValues[tolKey][1], tolValues[tolKey][2])])
                tolHigh.coords.addcoordinates([(tolValues[tolKey][0], tolValues[tolKey][1], 0)])

            elif float(tolid) < 10:
                tolLow = tolfol.newlinestring(name="TOL peak: " + tolid)
                tolLow.altitudemode = simplekml.AltitudeMode.relativetoground
                tolLow.style.linestyle.color = simplekml.Color.palevioletred
                tolLow.style.linestyle.width = 5
                for tolKey in tolDict:
                    tolValues = tolDict.values()
                    tolValues = list(tolValues)
                    tolLow.coords.addcoordinates([(tolValues[tolKey][0], tolValues[tolKey][1], tolValues[tolKey][2])])
                tolLow.coords.addcoordinates([(tolValues[tolKey][0], tolValues[tolKey][1], 0)])

            else:
                tol = tolfol.newlinestring(name="TOL peak: " + tolid)
                tol.altitudemode = simplekml.AltitudeMode.relativetoground
                tol.style.linestyle.color = simplekml.Color.violet
                tol.style.linestyle.width = 5
                for tolKey in tolDict:
                    tolValues = tolDict.values()
                    tolValues = list(tolValues)
                    tol.coords.addcoordinates([(tolValues[tolKey][0], tolValues[tolKey][1], tolValues[tolKey][2])])
                tol.coords.addcoordinates([(tolValues[tolKey][0], tolValues[tolKey][1], 0)])

            tolDict = {}
            a = 0
        # end of TOL

        # start of VOC
        if row[6] != '0.0':
            if b == 0:
                vocDict[b] = row[0], row[1], 0
                b += 1
            vocDict[b] = row[0], row[1], row[6]
            vocid = row[6]
            b += 1

        if row[6] == '0.0' and bool(vocDict) is True:
            if float(vocid) > 20:
                vocHigh = vocfol.newlinestring(name="VOC peak: " + vocid)
                vocHigh.altitudemode = simplekml.AltitudeMode.relativetoground
                vocHigh.style.linestyle.color = simplekml.Color.darkgray
                vocHigh.style.linestyle.width = 5
                for vocKey in vocDict:
                    vocValues = vocDict.values()
                    vocValues = list(vocValues)
                    vocHigh.coords.addcoordinates([(vocValues[vocKey][0], vocValues[vocKey][1], vocValues[vocKey][2])])
                vocHigh.coords.addcoordinates([(vocValues[vocKey][0], vocValues[vocKey][1], 0)])

            elif float(vocid) < 10:
                vocLow = vocfol.newlinestring(name="VOC peak: " + vocid)
                vocLow.altitudemode = simplekml.AltitudeMode.relativetoground
                vocLow.style.linestyle.color = simplekml.Color.lightgray
                vocLow.style.linestyle.width = 5
                for vocKey in vocDict:
                    vocValues = vocDict.values()
                    vocValues = list(vocValues)
                    vocLow.coords.addcoordinates([(vocValues[vocKey][0], vocValues[vocKey][1], vocValues[vocKey][2])])
                vocLow.coords.addcoordinates([(vocValues[vocKey][0], vocValues[vocKey][1], 0)])

            else:
                voc = vocfol.newlinestring(name="VOC peak: " + vocid)
                voc.altitudemode = simplekml.AltitudeMode.relativetoground
                voc.style.linestyle.color = simplekml.Color.gray
                voc.style.linestyle.width = 5
                for vocKey in vocDict:
                    vocValues = vocDict.values()
                    vocValues = list(vocValues)
                    voc.coords.addcoordinates([(vocValues[vocKey][0], vocValues[vocKey][1], vocValues[vocKey][2])])
                voc.coords.addcoordinates([(vocValues[vocKey][0], vocValues[vocKey][1], 0)])

            vocDict = {}
            b = 0
        # end of VOC


        # start of XYM
        if row[7] != '0.0':
            if c == 0:
                xymDict[c] = row[0], row[1], 0
                c += 1
            xymDict[c] = row[0], row[1], row[7]
            xymid = row[7]
            c += 1

        if row[7] == '0.0' and bool(xymDict) is True:
            if float(xymid) > 20:
                xymHigh = xymfol.newlinestring(name="XYM peak: " + xymid)
                xymHigh.altitudemode = simplekml.AltitudeMode.relativetoground
                xymHigh.style.linestyle.color = simplekml.Color.sandybrown
                xymHigh.style.linestyle.width = 5
                for xymKey in xymDict:
                    xymValues = xymDict.values()
                    xymValues = list(xymValues)
                    xymHigh.coords.addcoordinates([(xymValues[xymKey][0], xymValues[xymKey][1], xymValues[xymKey][2])])
                xymHigh.coords.addcoordinates([(xymValues[xymKey][0], xymValues[xymKey][1], 0)])

            elif float(xymid) < 10:
                xymLow = xymfol.newlinestring(name="XYM peak: " + xymid)
                xymLow.altitudemode = simplekml.AltitudeMode.relativetoground
                xymLow.style.linestyle.color = simplekml.Color.rosybrown
                xymLow.style.linestyle.width = 5
                for xymKey in xymDict:
                    xymValues = xymDict.values()
                    xymValues = list(xymValues)
                    xymLow.coords.addcoordinates([(xymValues[xymKey][0], xymValues[xymKey][1], xymValues[xymKey][2])])
                xymLow.coords.addcoordinates([(xymValues[xymKey][0], xymValues[xymKey][1], 0)])

            else:
                xym = xymfol.newlinestring(name="XYM peak: " + xymid)
                xym.altitudemode = simplekml.AltitudeMode.relativetoground
                xym.style.linestyle.color = simplekml.Color.brown
                xym.style.linestyle.width = 5
                for xymKey in xymDict:
                    xymValues = xymDict.values()
                    xymValues = list(xymValues)
                    xym.coords.addcoordinates([(xymValues[xymKey][0], xymValues[xymKey][1], xymValues[xymKey][2])])
                xym.coords.addcoordinates([(xymValues[xymKey][0], xymValues[xymKey][1], 0)])

            xymDict = {}
            c = 0
        # end of XYM

        # start of XYP
        if row[8] != '0.0':
            if d == 0:
                xypDict[d] = row[0], row[1], 0
                d += 1
            xypDict[d] = row[0], row[1], row[8]
            xypid = row[8]
            d += 1

        if row[8] == '0.0' and bool(xypDict) is True:
            if float(xypid) > 20:
                xypHigh = xypfol.newlinestring(name="XYP peak: " + xypid)
                xypHigh.altitudemode = simplekml.AltitudeMode.relativetoground
                xypHigh.style.linestyle.color = simplekml.Color.darkorange
                xypHigh.style.linestyle.width = 5
                for xypKey in xypDict:
                    xypValues = xypDict.values()
                    xypValues = list(xypValues)
                    xypHigh.coords.addcoordinates([(xypValues[xypKey][0], xypValues[xypKey][1], xypValues[xypKey][2])])
                xypHigh.coords.addcoordinates([(xypValues[xypKey][0], xypValues[xypKey][1], 0)])

            elif float(xypid) < 10:
                xypLow = xypfol.newlinestring(name="XYP peak: " + xypid)
                xypLow.altitudemode = simplekml.AltitudeMode.relativetoground
                xypLow.style.linestyle.color = simplekml.Color.orangered
                xypLow.style.linestyle.width = 5
                for xypKey in xypDict:
                    xypValues = xypDict.values()
                    xypValues = list(xypValues)
                    xypLow.coords.addcoordinates([(xypValues[xypKey][0], xypValues[xypKey][1], xypValues[xypKey][2])])
                xypLow.coords.addcoordinates([(xypValues[xypKey][0], xypValues[xypKey][1], 0)])

            else:
                xyp = xypfol.newlinestring(name="XYP peak: " + xypid)
                xyp.altitudemode = simplekml.AltitudeMode.relativetoground
                xyp.style.linestyle.color = simplekml.Color.orange
                xyp.style.linestyle.width = 5
                for xypKey in xypDict:
                    xypValues = xypDict.values()
                    xypValues = list(xypValues)
                    xyp.coords.addcoordinates([(xypValues[xypKey][0], xypValues[xypKey][1], xypValues[xypKey][2])])
                xyp.coords.addcoordinates([(xypValues[xypKey][0], xypValues[xypKey][1], 0)])

            xypDict = {}
            d = 0
        # end of XYP

    return(kml)

def help(request):
    return render(request, "website/help.html")

def about(request):
    return render(request, "website/about.html")

# function to find peak and transform the data
# by default, lag is 30, threshold is 2, and influence is 0
def transform(data, chemical, lag, threshold, influence):
    # find the peak
    signals = np.zeros(len(data))
    filteredData = np.array(data)
    avgFilter = np.zeros(len(data))
    stdFilter = np.zeros(len(data))
    avgFilter[lag - 1] = np.mean(data[0 : lag])
    stdFilter[lag - 1] = np.std(data[0 : lag])

    for i in range(lag, len(data)):
        # peak detection
        if abs(data[i] - avgFilter[i - 1]) > threshold * stdFilter[i - 1]:
            if data[i] > avgFilter[i - 1]:
                signals[i] = 1
            else:
                signals[i] = -1
            filteredData[i] = influence * data[i] + (1 - influence) * filteredData[i - 1]
        else:
            signals[i] = 0
            filteredData[i] = data[i]

        avgFilter[i] = np.mean(filteredData[(i - lag + 1) : i + 1])
        stdFilter[i] = np.std(filteredData[(i - lag + 1) : i + 1])

        # check the peak
        if chemical == 'BEN':
            limit = 5
        elif chemical == 'CH4':
            limit = 2
        elif chemical == 'H2S':
            limit = 20
        elif chemical == 'TOL':
            limit = 9
        elif chemical == 'VOC':
            limit = 1
        elif chemical == 'XYM':
            limit = 28
        else:
            limit = 5

        if signals[i] != 0 and abs(data[i] - avgFilter[i]) < limit:
            signals[i] = 0
            
    # transform the data
    start_index = 0
    while start_index < len(signals):
        # if the current signal is 1 or -1, 
        # then assign the corresponding data with the mean of the consequence of signals 
        if signals[start_index] != 0:
            step = 1
            while start_index + step < len(signals) and signals[start_index + step] != 0:
                step+= 1
            avg = round(sum(data[start_index: start_index + step]) / step, 3) # find the mean
            data[start_index: start_index + step] = [avg] * step # assign data with the new value
            start_index+= step
        # otherwise, if the current signal is 0,
        # then assign the corresponding data as 0 and check the next signal
        else: 
            data[start_index] = 0
            start_index+= 1
            
    return data
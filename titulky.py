#!usr/bin/env python

import urllib2
import re
import sys
import getopt
import os

def main(argv):
    url = spracovanie_arg(argv)
    website = urllib2.urlopen(url)
    html = website.read()
    website.close()
    stranka = str(html)
    ceske_tit = stiahni_cs(stranka)
    angl_tit = stiahni_en(stranka)
    
    cs = spracuj_tit(ceske_tit[0])
    ceske_tit.pop(0)
    najlepsie = zisti_index(cs, angl_tit)
    en = spracuj_tit(angl_tit[najlepsie])
    angl_tit.pop(najlepsie)
    odchylka = 0.0
    for k in range(10):
        odchylka += abs(en[k][0] - cs[k][0])
        
    file = open("vysledok.txt", "w")
    
    for i in range(len(cs)):
        cesky = cs.pop(0)
        angl = en.pop(0)
        if abs(angl[0] - cesky[0]) < odchylka and abs(angl[1] - cesky[1]) < odchylka: 
            file.write(cesky[2] + "\t" + angl[2] + "\n")
        elif angl[0] > cesky[0] and angl[1] > cesky[1]:
            file.write(cesky[2] + "\t\n")
            en.insert(0, angl)
        elif angl[0] < cesky[0] and angl[1] < cesky[1]:
            file.write("\t" + angl[2] + "\n")
            cs.insert(0, cesky)
    file.close()
    try:
        zmaz_txt(ceske_tit)
    except:
        print "Nie je co zmazat!"
    try:
        zmaz_txt(angl_tit)
    except:
        print "Nie je co zmazat!"   
#end_main

# zisti, ktore titulky su najlepsie
# porovna pocty riadkov
# vrati index do pola s nazvami anglickych titulkov
def zisti_index(cs, tit_en):
    index = -1
    rozdiel = 1000
    for tit in tit_en:
        en = spracuj_tit(tit)
        if abs(len(cs) - len(en)) < rozdiel:
            index = tit_en.index(tit)
            rozdiel = abs(len(cs) - len(en))
    return index
#end_zisti_index

# spracuje argumenty
def spracovanie_arg(argv):
    url = ""
    try:
        opts, args = getopt.getopt(argv, "hu:", ["help", "url="])
    except:
        napoveda()
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            napoveda()
            sys.exit(2)
        elif opt in ("-u", "--url"):
            url = arg;
    return url
#end_spracovanie_arg

def napoveda():
    print("napoveda")
#end_napoveda

# stiahne ceske titulky
def stiahni_cs(nieco):
    links = re.findall('"\/cs\/subtitleserve\/file\/[0-9]*?"', nieco)
    linky = []
    for i in links:
        if i not in linky:
            linky.append(i) 
    adr = []
    for i in range(len(linky)):
        novy = "http://www.opensubtitles.org" + linky[i] + "/"
        novy = re.sub('["]', '', novy)
        adr.append(novy)
    idx = 0;
    subory = []
    for i in adr:
        idx += 1
        tit = urllib2.urlopen(i)
        meno_suboru = "titulky_cs_" + str(idx) + ".txt"
        fd = open(meno_suboru, "wb")
        fd.write(tit.read())
        fd.close()
        tit.close()
        subory.append(meno_suboru)
    return subory
#end_stiahni_cs 

# najde stranku so vsetkymi anglickymi titulkami
def stiahni_en(nieco):
    vsetky_tit = re.findall('"\/cs\/search\/sublanguageid-all\/idmovie-[0-9]*?"' ,nieco)
    vsetky_tit = re.sub('["]', '', vsetky_tit[0])
    cisla = re.search("[0-9]+", vsetky_tit)
    id = cisla.group(0)
    angltit = "http://www.opensubtitles.org/cs/search/idmovie-" + id + "/sublanguageid-eng/"
    html = urllib2.urlopen(angltit)
    web = html.read()
    html.close()
    stranka = str(web)
    links = re.findall('"\/cs\/subtitles\/[0-9]+?\/[-a-z]+?"',stranka)
    linky = []
    for i in links:
        if i not in linky:
            linky.append(i)
    adr = []
    for i in linky:
        novy = ""
        novy = "http://www.opensubtitles.org" + i + "/"
        novy = re.sub('["]', '', novy)
        adr.append(novy)
    subory_en = []
    idx = 0
    for i in adr:
        idx += 1
        subory_en.append(stiahni_en_tit(i, idx))
    return subory_en
#eand_stihni_en

# stahuje anglicke titulky
def stiahni_en_tit(adr, idx):
    web = urllib2.urlopen(adr)
    html = web.read()
    web.close()
    stranka = str(html)
    links = re.findall('"\/cs\/subtitleserve\/file\/[0-9]+?"', stranka)
    linky = []
    for i in links:
        if i not in linky:
            linky.append(i)
    novy = "http://opensubtitles.org" + linky[0] + "/"
    novy = re.sub('["]', '', novy)
    tit = urllib2.urlopen(novy)
    meno_suboru = "titulky_en_" + str(idx) + ".txt"
    fd = open(meno_suboru, "wb")
    fd.write(tit.read())
    fd.close()
    tit.close()
    return meno_suboru
#end_stiahni_en_tit   

# zmaze zadane subory podla mena
# parameter je pole mien
def zmaz_txt(mena):
    for i in mena:
        os.remove(i)
#end_zmaz_txt

# spracuje titulky pomocou re
def spracuj_tit(titulky):
    f = open(titulky, "r")
    i = 0
    k = 0
    pom = ""
    zapis = ""
    zoznam = []
    for line in f:
        i += 1
        try:
            cas = re.search("(\d+):(\d+):(\d+),(\d+) --> (\d+):(\d+):(\d+),(\d+)", line)
            zac = float(cas.group(1))*3600 + float(cas.group(2))*60 + float(cas.group(3)) + float(cas. group(4))/1000
            kon = float(cas.group(5))*3600 + float(cas.group(6))*60 + float(cas.group(7)) + float(cas. group(8))/1000
        except AttributeError:
            riadok = re.search("(\d+)|(.*)", line)
            if riadok.group(1) != None:
                if zapis != "":
                    vety = zapis
                    vety = re.sub("(!|\?|\.\.\.|:|;|\.\.|\. )", "\\1|", vety)
                    vety = re.sub("(\.\s)", ".", vety)
                    vety = vety.split("|")
                    del vety[-1]
                    zoznam.append([zac, kon, zapis])
                    zapis = ""
            if riadok.group(2) != None:
                pom = riadok.group(2)
                if pom != "":
                    pom = re.sub("<i>|</i>", "", pom)
                    pom = re.sub("\r", "", pom)
                    zapis += pom + " "                                  
    f.close()
    return zoznam
#end_spracuj_tit
   

if __name__ == "__main__":
    main(sys.argv[1:])

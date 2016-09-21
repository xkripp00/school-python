#!usr/bin/env python

#XTD:xkripp00

import sys
import getopt
import xml.etree.ElementTree as etree
import copy
import string

# funkce vypisujici chybova hlaseni
def chyba(ch):
	if ch == "getopt":
		print("Zlyhala fcia getopt. Zle zadane parametre programu.", file = sys.stderr)
	elif ch == "param":
		print("Zle zadane parametre.", file = sys.stderr)
	elif ch == "open":
		print("Zlyhalo otvorenie suboru.", file=sys.stderr)
	elif ch == "stdin":
		print("Nebol zadany validny xml subor zo standardneho vstupu.", file=sys.stderr)
	elif ch == "kolizia":
		print("Nastala kolizia stlpcov z mien atributov a podelementov.", file=sys.stderr)
	elif ch == "etc":
		print("Nespravna hodnota parametru etc.", file=sys.stderr)
	### chyba_konec

# funkce vypisujici napovedu
def napoveda():
	print("""\
Pouzitie: xtd.py [parametre]
	--help: vypis napovedy, pouzity moze byt len samostatne
	--input=filename, --output=filename: zadanie vstupneho/vystupneho suboru
	--header='hlavicka': hlavicka vlozena na zaciatok vystupneho suboru
	--etc=n: n>=0, max pocet stlpcou z rovnakych elementov
	-a: nebudu sa generovat stlpce z atributov vo vstupnych suboroch
	-b: bude sa uvazovat, ze je jeden element s viacerymi podelementami s rovnakym nazvom
	    nemoze sa kombinovat s parametrom -etc
	-g: vystupny subor bude v XML tvare
""")
	### napoveda_konec

# funkce nacita vstupni xml soubor
# param - jmeno vstupniho souboru, kdyz neni zadane, pouzije se stdin
# vraci nacteny strom
def nacitanie_suboru(par_in):
	if par_in == None:
		sys.stdin = sys.stdin.detach()
		try:
			tree = etree.parse(sys.stdin)
		except:
			chyba("stdin")
			sys.exit(2)
	else:
		try:
			tree = etree.parse(par_in)
		except:
			chyba("open")
			sys.exit(2)
	return tree
	### nacitanie_suboru_konec

# funkce otvori vystupni soubor
# param - jmeno souboru, kdyz None, tak stdout
# vraci deskriptor souboru
def otvorenie_vystupu(output):
	if output == None:
		vystup = sys.stdout
	else:
		try:
			vystup = open(output, 'w')
		except:
			chyba("open")
			sys.exit(3)
	return vystup
	### otvorenie_vystupu_konec

# zjisti ci je retezec cislo
# param - retezec
# vraci cislo, alebo false
def cislo(ret):
	try:
		return int(ret)
	except:
		try:
			return float(ret)
		except:
			return False
	### cislo_konec

# funkce urci typ textovym elementum a typy atributu
# param - prem - promnena, ktere se urcuje typ
#	- in_atrib - oznaceni, ci se jedna od promnenou v artibutu nebo podelementu
# vraci hledany typ
def ziskaj_typ(prem, in_atrib):
	if prem=='0' or prem=='1' or prem=='True' or prem=='False' or prem==None:
		return 'BIT'
	elif type(cislo(prem)) is float:
		return 'FLOAT'
	elif type(cislo(prem)) is int:
		return 'INT'
	else:
		if in_atrib:
			return 'NVARCHAR'
		else:
			return 'NTEXT'
	### ziskaj_typ_konec

# funkce spracuje atributy, transformuje do pole
# param - dictionary atributu (meno -> typ)
# vraci pole [meno, typ]
def spracuj_atributy(atr):
	a = []
	for k,v in atr.items():
		typ = ziskaj_typ(v, True)
		b = [k.lower(),typ]
		a.append(b)
	return a
	### spracuj_atributy_konec

# funkce spracuje podelemnty jednotlivych elemntu
# param - dany elemant
# vraci pole [mano, typ]
def spracuj_podelementy(elem):
	nazov = elem.tag.lower()
	hodnota = ziskaj_typ(elem.text, False)
	e = []
	e.append(nazov)
	e.append(hodnota)
	return e
	### spracuj_podelementy_konec

# funkce spracuje textove elementy
# param - element
# vraci pole [value, typ]
def spracuj_hodnoty(elem):
	iba_biele = False
	aj_znaky = False
	if elem.text != None:
		for i in elem.text:	# zjisti, ci je textovy element tvoreny jen bilymi znaky
			if i=='\n' or i=='\t' or i==' ':
				iba_biele = True
			else:
				aj_znaky = True
	if (iba_biele == True and aj_znaky == False) or elem.text == None:
		return None
	else:
		nove = []
		hodnota = ziskaj_typ(elem.text, False)
		nove.append("value")
		nove.append(hodnota)
		return nove
	### spracuj_hodnity_konec

# funkce zrusi stejne prvky v poli
# param - dane pole
# vraci pole bez duplikatu
def zrus_duplikaty_pola(pole):
	nove = []
	for i in pole:
		if i not in nove:
			nove.append(i)
	return nove
	### zrus_duplikaty_pola_konec

# funkce zjisti, ci se dany prvek jiz nachazi v poli
# param - prvok - dany prvek
# 	- pole - pole, ve kterem se hledaji stejne prvky
# vraci dany prvek nebo None
def uz_je_tam(prvok, pole):
	for i in pole:
		if i[0] == prvok[0] and i[1] == prvok[1] and i[2] != prvok[2]:
			return i
	return None
	### uz_je_tam

# funkce priradi promnenne hodnotu
# param - promnena
# vraci - cislo reprezentujici hodnotu
def prirad_hodnotu(prem):
	if prem == "BIT":
		return 0
	elif prem == "INT":
		return 1
	elif prem == "FLOAT":
		return 2
	elif prem == "NVARCHAR":
		return 3
	elif prem == "NTEXT":
		return 4
	### prirad_hodnotu_konec

# funkce zjisti, ktery typ ma vyssi prioritu
# param - porovnavane prvky
# vraci cislo, ktery prvek ma vyssi priotitu
def porovnaj_hodnotu(prve, druhe):
	jedna = prirad_hodnotu(prve)
	dva = prirad_hodnotu(druhe)
	if jedna == dva:
		return 1
	elif jedna < dva:
		return 1
	else:
		return 2
	## porovnaj_hodnotu_konec

# funkce zrusi prvky se stejnym jmenem v poli
# param - pole
#vraci nove pole
def zrus_dup_atrib(pole):
	nove = []
	cast = []
	zrus = []
	for i in pole:
		zrus = []
		dlzka = len(i)
		for j in range(dlzka):
			for k in range(dlzka-1):
				if j+k+1 >= dlzka:
					break
				if i[j][0] == i[j+k+1][0]:
					ktore = porovnaj_hodnotu(i[j][1], i[j+k+1][1])
					if ktore == 1:
						zrus.append(i[j])
					else:
						zrus.append(i[j+k+1])
		for j in zrus:
			if j in i:
				i.remove(j)
		nove.append(i)
	return nove		
	### zrus_dup_atrib_konec

# funkce funkce upravi pole elemntu, pro pripad etc==0
# param - pole - uravovane pole
#	- tab - tabulka se jmeny vsech tabulek
# vraci upravene pole
def uprav_elem_etcn(pole, tab):
	for i in range(len(pole)):
		for j in pole[i]:
			if "_id" in j[0]:
				continue
			else:
				idx = tab.index(j[0])
				meno = tab[i] + "_id"
				pole[idx].append([meno, "INT"])
	return pole
	### uprav_elem_etcn_konec

# funkce zjisti, ci nejsou stejne stlpce z elemntu a atributu
# param - atrib - pole atributu
#	- podelem - pole elemntu
# vraci true, kdy je kolize, jinak false
def je_kolizia(atrib, podelem):
	for i in atrib:
		for j in podelem:
			if i[0].lower() == j[0].lower():
				return True
	return False
	### nenachdza_sa_konec

# stejne jako predosla funkce, jen pri parametru b
def je_kolizia_b(atrib, podelem):
	for i in atrib:
		for j in podelem:
			pom = j[0] + "_id"
			if i[0].lower() == pom.lower():
				return True
	return False
	### je_kolizia_konec

# funkce spracuje vstupni xml soubor
# param - subor - vstupni soubor
#	- etc - parametr programu
# vraci - pole se jmeny tabulek, s atributy tabulek, s podelemnty tabulek a textovymi elemnety tabulek
def parse_xml(subor, etc):
	if etc == None:		# kdyz neni zadane etc, etc je neomezene (vnitrni reprezentace)
		etc = 999
	tree = nacitanie_suboru(subor)		# nacteni vstupniho souboru
	root = tree.getroot()			# ziskani korene

	pole_tab = []				# inicializovana pole pro hodnoty
	lepsi_vystup_atr = []
	lepsi_vystup_podelem = []
	lepsi_vystup_hodnoty = []
	lep_etcn = []
	for elem in tree.iter():		# ziskani jmen tabulek
		if elem != root:
			try:
				pole_tab.index(elem.tag)
			except:
				pole_tab.append(elem.tag)
	
	for i in pole_tab:		# spacovavani stromu
		vystup_atr = []
		vystup_podelem = []
		vystup_hodnoty = []
		etcn = []
		idx = 0
		for elem in tree.iter():
			if i == elem.tag and elem != root:
				if elem.attrib != {}:
					vystup_atr.extend(spracuj_atributy(elem.attrib))	# ziskani atributu
				for child in elem:						# ziskani sloupcu z podelementu
					if int(etc) != 0:
						vysl = spracuj_podelementy(child)
						vysl.append(idx)
						ruseny_prvok =  uz_je_tam(vysl, vystup_podelem)
						if ruseny_prvok != None:
							vystup_podelem.remove(ruseny_prvok)
						vystup_podelem.append(vysl)
					else:
						vysl = [child.tag, "INT"]
						etcn.append(vysl)
				vystup_hodnoty.append(spracuj_hodnoty(elem))		# ziskani hodnot netextovych elemntu
				idx += 1
		lepsi_vystup_atr.append(vystup_atr)
		lepsi_vystup_podelem.append(vystup_podelem)
		lepsi_vystup_hodnoty.append(vystup_hodnoty)
		lep_etcn.append(etcn)

	upravene_atr = []
	nove_etcn = []
	# upravovani ziskanych prvku
	for i in lepsi_vystup_atr:
		upravene_atr.append(zrus_duplikaty_pola(i))		# ruseni stejnych prvku
	for i in lep_etcn:
		nove_etcn.append(zrus_duplikaty_pola(i))
	nove_etcn = uprav_elem_etcn(nove_etcn, pole_tab)
	if int(etc) == 0:	
		return pole_tab, upravene_atr, nove_etcn, lepsi_vystup_hodnoty
	else:
		return pole_tab, upravene_atr, lepsi_vystup_podelem, lepsi_vystup_hodnoty
	### parse_xml_konec

# rekurzivni funkce urcuje relace mezi tabulkami
# param - podelem - pole cizich klicu
#	- i - index do pole tabulek
#	- vztahy - tabulka vztahu
#	- tab - pole jmen tabulek
#	- tab_c - jedno jmenu z tabulky
# braci doplnene pole vztahu
def rek(podelem, i, vztahy, tab, tab_c):
	for j in podelem[i]:
		if [tab_c, j[0], 0] in vztahy:
			index = vztahy.index([tab_c, j[0], 0])
			vztahy[index][2] = "N:1"
		if [j[0], tab_c, 0] in vztahy:
			index = vztahy.index([j[0], tab_c, 0])
			vztahy[index][2] = "1:N"
		index = tab.index(j[0])
		rek(podelem, index, vztahy, tab, tab_c)
	### rek_konec

# funkce doplni chybejici vztahy N:M
# param - pole vztahu
# vraci doplnene pole
def dopln_vztahy(vztahy):
	for i in range(len(vztahy)):
		if vztahy[i][2] == 0:
			vztahy[i][2] = "N:M"
	return vztahy
	### dopln_vztahy_konec

# funkce pro ziskani vztahu mezi tabulkami
# param - vztahy - inicializovane pole vztahu
#	- podelem - pole cizich klicu
#	- tab - pole jmen tabulek
# vraci pole vztahu
def ziskaj_vztahy(vztahy, podelem, tab):
	for i in range(len(tab)):
		rek(podelem, i, vztahy, tab, tab[i])
	return vztahy
	### ziskaj_vztahy_konec

# funkce vytvori vsechny kombinace vztahu mezi tabulkami
# param - pole jmen tabulek
# vraci inicializovane pole vztahu
def vytvor_vzt(tab):
	vzt = []
	for i in tab:
		for j in tab:
			if i == j:
				vzt.append([i,j,"1:1"])
			else:
				vzt.append([i,j,0])
	return vzt
	### vytvor_vzt_konec

# funkce vypise xml tabulku ze vztahu
# param - vztahy - pole vztahu
#	- header - hlavicka
#	- output - vystupny soubor
#	- tab - pole jmen tabulek
def vypis_xml_tab(vztahy, header, output, tab):
	vystup = otvorenie_vystupu(output)
	if header != None:
		vystup.write("--")
		vystup.write(header)	
		vystup.write("\n\n")
	vystup.write("<tables>\n")
	for i in range(len(tab)):
		vystup.write("\t<table name=\"" + tab[i] + ">\n")
		for j in vztahy:
			if tab[i] == j[0]:
				vystup.write("\t\t<relation to=\"" + j[1] +"\" relation_type=\"" + j[2] + "\" />\n")
		vystup.write("\t</table>\n")
	vystup.write("</tables>\n")
	vystup.close()
	sys.exit(0)
	### vypis_xml_tab

# funkce upravi pole, aby s nim mohly ostatni funkce pracovat
# param - dane pole
def uprav_z_etc0(pole):
	nove_pole = []
	for i in pole:
		zrus = []
		for j in i:
			if "_id" not in j[0].lower():
				zrus.append(j)
		for j in zrus:
			i.remove(j)
		nove_pole.append(i)
	for i in nove_pole:
		for j in i:
			if j[0] != None:
				j[0] = j[0][:-3]
				j.append(963)
	return nove_pole	
	### uprav_zetc0_konec

# funkce pro prepinac g
# param - podelem - pole cizich klicu
#	- ostani jako dotet
def prep_g(tab, podelem, b, etc, header, output):
	if b == False and etc == None:		# vnitrni reprezentace neomezeneho etc
		etc = 999
	pocet = len(tab)	# pocet tabulek

	if etc != None:			# kdyz nebylo zadano b
		if int(etc) == 0:
			podelem = uprav_z_etc0(podelem)
		else:
			for i in range(pocet):
				pocty_stlpcov = {}
				for j in podelem[i]:
					pocet_prvkov = 0
					for k in podelem[i]:
						if j[0] == k[0]:
							pocet_prvkov += 1
					pocty_stlpcov[j[0]] = pocet_prvkov
				for k, h in pocty_stlpcov.items():
					if h > int(etc):
						zmaz = []
						for y in podelem[i]:
							if y[0] == k:
								zmaz.append(y)
						for y in zmaz:
							podelem[i].remove(y)
						index_tab = tab.index(k)
						novy_stlp_meno = tab[i]
						novy_col = [novy_stlp_meno, "INT", 987]
						podelem[index_tab].append(novy_col)

	vztahy = vytvor_vzt(tab)	# vytvori pole vztahu
	for y in podelem:		# upravi cizi klice
		for z in y:
			z[2] = 963
	ach_podelem = []
	for y in podelem:				# zrusi staje prvky
		ach_jaj = zrus_duplikaty_pola(y)
		ach_podelem.append(ach_jaj)
	vztahy = ziskaj_vztahy(vztahy, ach_podelem, tab)	# ziska vztahy 1:N a N:1
	vztahy = dopln_vztahy(vztahy)				# doplni vztahy o N:M
	vypis_xml_tab(vztahy, header, output, tab)		# vypise tabulky
	### prep_g_konec

# funkce vytvori prikazy SQL
def vytvor_sql(tab, atrib, podelem, hodnoty, a, b, etc, header, output):
	vystup = otvorenie_vystupu(output)	# otevreni vystupu

	pocet = len(tab)		# pocet tabulek
	sql_prikaz = ""			# retezec pro sql prikaz
	if b:				# je zadan parametr b
		for y in podelem:	# upravi podelementy
			for z in y:
				z[2] = 963
		for i in range(pocet):			# cyklus pro kazdou tabulku
			sql_prikaz += "CREATE TABLE "		# zacatek sql prikazu
			sql_prikaz += tab[i]
			sql_prikaz += " ( "
			sql_prikaz += "prk_" + tab[i] + "_id INT PRIMARY KEY"
			
			if a == False:		# zadan prepinac a prida sloupce z atributu
				stlpec = ""
				for j in atrib[i]:
					stlpec = stlpec + " , " + j[0] + " " + j[1]
				sql_prikaz += stlpec
			bez_dupl = zrus_duplikaty_pola(podelem[i])	# zrusi stejne prvky v poli
			for j in bez_dupl:					# prida sloupce z podelementu
				stlpec2 = " , " + j[0] + "_id " + "INT"
				sql_prikaz += stlpec2
			
			bez_dupl2 = zrus_duplikaty_pola(hodnoty[i])
			for j in bez_dupl2:				#prida sloupce z textovych elementu
				if j != None:
					stlpec3 = " , " + j[0] + " " + j[1]
					sql_prikaz += stlpec3
			sql_prikaz += " ) ;\n\n"
		
			if je_kolizia_b(atrib[i], podelem[i]):		# zjisti ci nedoslo ke kolizi
				vystup.close()
				chyba("kolizia")
				sys.exit(90)
		if header != None:				# vypise hlavicku, jestli byla zadana
			vystup.write("--")
			vystup.write(header)
			vystup.write("\n\n")
		vystup.write(sql_prikaz)		# vypsani prikazu CREATE TABLE
		vystup.close()
		sys.exit(0)
	if b == False and etc == None:			# nebylo zadano etc ani b, vnitrni interpretace neomezeneho etc
		etc = 999
	pocty_stlpcov = {}			# slovnik na pocty jednotlivych sloupcu
	if etc != None:
		for i in range(pocet):		# cyklus pro kazdou tabulku
			pocty_stlpcov = {}
			sql_prikaz += "CREATE TABLE " + tab[i] + " ( prk_" + tab[i] + "_id INT PRIMARY KEY"	# zacatek sql

			if a == False:			# pridani sloupcu z atributu
				for j in atrib[i]:
					stlpec = ""
					stlpec += " , " + j[0] + " " + j[1]
					sql_prikaz += stlpec

			if int(etc) == 0:		# etc je 0, pole podelem na jinou strukturu
				for j in podelem[i]:
					if "_id" in j[0]:		
						sql_prikaz += " , " + j[0] + " " + j[1]
			else:	
				for j in podelem[i]:			# treba spracovat podelem, zjisteni poctu jednotlivych sloupcu
					pocet_prvkov = 0
					for k in podelem[i]:
						if j[0] == k[0]:
							pocet_prvkov += 1
					pocty_stlpcov[j[0]] = pocet_prvkov
				for k, h in pocty_stlpcov.items():			# porovnavani poctu sloupcu s etc a pridavani typu a pripon
					if h <= int(etc) and int(etc) != 0:
						if h == 1:
							for y in podelem[i]:
								if y[0] == k:
									y[0] += "_id"
									y[1] = "INT"
						else:
							index = 0
							for y in podelem[i]:
								if y[0] == k:
									index += 1
									y[0] = y[0] + str(index) + "_id"
									y[1] = "INT"
					else:					# vice sloupcu ako je etc, musi se do nadrazene tabulky dat cizi klic
							zmaz = []
							for y in podelem[i]:		# nalezeni sloupcu, ktere treba zmazat
								if y[0] == k:
									zmaz.append(y)
							for y in zmaz:			# mazani sloupcu
								podelem[i].remove(y)
							index_tab = tab.index(k)	# vytvoreni noveho sloupce v nadrazene tabulce
							novy_stlp_meno = tab[i]
							novy_col = [novy_stlp_meno, "INT", 987]
							podelem[index_tab].append(novy_col)
			
				for j in podelem[i]:		# pridani sloupcu z podelementu to sql
					stlpec2 = ""
					stlpec2 += " , " + j[0] + " " + j[1]
					sql_prikaz += stlpec2
			kolizia = je_kolizia(atrib[i], podelem[i])	# kontrola kolize mezi sloupci atributu a podelemntu
			if kolizia:
				vystup.close()
				chyba("kolizia")
				sys.exit(90)
			bez_dupl2 = zrus_duplikaty_pola(hodnoty[i])	# doplneni slopcu z textovych elementu do sql
			for j in bez_dupl2:
				if j != None:
					stlpec3 = " , " + j[0] + " " + j[1]
					sql_prikaz += stlpec3
			sql_prikaz += " ) ;\n\n"

		if header != None:		# vypsani hlavicky
			vystup.write("--")
			vystup.write(header)
			vystup.write("\n\n")
		vystup.write(sql_prikaz)	# vypsani prikazu CREATE TABLE
		vystup.close()
		sys.exit(0)
	### vytvor_sql_konec

# hlavni funkce programu
def main():
	# ziskani parametru programu
	try:
		opts, args = getopt.getopt(sys.argv[1:], "abg", ["help", "input=", "output=", "header=", "etc="])
	except:
		chyba("getopt")
		sys.exit(1)
	# inicializace promnenych pro parametry
	help = a = b = g = False
	input = output = header = etc = None
	# zjisteni, ktere parametry byli zadany
	for o, h in opts:
		if o == "--help":
			help = True
		elif o == "-a":
			a = True
		elif o == "-b":
			b = True
		elif o == "-g":
			g = True
		elif o == "--input":
			input = h
		elif o == "--output":
			output = h
		elif o == "--header":
			header = h
		elif o == "--etc":
			etc = h

	# nezadan zaden parametr
	if help == a == b == g == False and input == output == header == etc == None:
		chyba("param")
		sys.exit(1)
	
	# zadana napoveda
	if help == True and a == b == g == False and input == output == header == etc == None:
		napoveda()
		sys.exit(0)	
	
	# --help kombinovan s nejakym jinym parametrem
	if help==True and (a==True or b==True or g==True or input!=None or output!=None or headrer!=None or etc!=None):
		chyba("param")
		sys.exit(1)

	# -b kombinovan s -etc
	if b == True and etc != None:
		chyba("param")
		sys.exit(1)
	# kontrola parametru etc na zaporne cislo nebo prazdny retezec
	try:
		if etc != None and int(etc) < 0:
			chyba("param")
			sys.exit(1)
	except:
		chyba("etc")
		sys.exit(1)

	# spracovani xml
	tab, atrib, podelem, hodnoty = parse_xml(input, etc)
	# upraveni pole atributu
	atrib = zrus_dup_atrib(atrib)

	# zjisteni, jestli se maji vytvaret xml-ka(g), nebo prikazy CREATE TABLE(not g)
	# a zavolani prislouchajicich funkci
	if g == True:
		prep_g(tab, podelem, b, etc, header, output)
	else:
		vytvor_sql(tab, atrib, podelem, hodnoty, a, b, etc, header, output)
	### main_konec

if __name__ == "__main__":
	main()

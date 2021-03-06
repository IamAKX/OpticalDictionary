# To change this license header, choose License Headers in Project Properties.
# To change this template file, choose Tools | Templates
# and open the template in the editor.
import urllib2
from bs4 import BeautifulSoup
import re
import json
import sys
import time
from pymongo import MongoClient

TAG_RE = re.compile(r'<[^>]+>')

__author__ = "akash"
__date__ = "$4 Mar, 2017 9:36:13 AM$"

def remove_tags(text):
    return TAG_RE.sub('', text)

def setElementInEmptyArray(array):
    if(len(array) == 0):
        array.append("Not available")
    return array

if __name__ == "__main__":

	## Loading 3.5lac words
    wordlist = [line.rstrip('\n') for line in open('dictionary.txt')]
    length = len(wordlist)

    ##Establishing MongoLab connection
    connection = MongoClient("ds153710.mlab.com", 53710)
    db = connection["ocr"]
    db.authenticate("iamakx", "akash123")
    lastEnteredIndex = 0

    for i in range(96041,length):
		word = wordlist[i].strip().lower() 
		print "Parsing " + word + "(" + str(i+1) + "/" + str(length) + ") ........",
		# if(i%50000 == 0):
		# 	print 'Sleeping for 3 hours, index = '+str(i)
		# 	time.sleep(3600*3)
		try:
			html_content = urllib2.urlopen("http://wordnik.com/words/"+word)
			soup = BeautifulSoup(html_content,"html.parser")
			html_content = urllib2.urlopen("https://www.howmanysyllables.com/words/"+word)
			syllablesSoup = BeautifulSoup(html_content,"html.parser")
						

			#Parse defination
			def_array = []
			defination = soup.find("div",{"id":"define"}).find_all("li")
			for s in defination:
			    try:
			        x = s.find("abbr",{"title":"partOfSpeech"})
			        def_array.append(x.text + str(s).replace(str(x),'').replace('<li>','').replace('</li>','').strip())
			    except:
			        continue


			#Parse Syllable
			syllable_array = []
			try:
			    sylbl = syllablesSoup.find("p",{"id":"SyllableContentContainer"}).find_all("span",{"class":"Answer_Red"})
			    syllable_array.append(sylbl[0].text.strip())
			except:
			    pass


			#Parse etymologies
			etymologies_array = []
			etymos = soup.find("div",{"class":"word-module module-etymologies"}).find_all("div",{"class":"sub-module"})
			for s in etymos:
			    try:
			        if(s.has_attr('div')):
			            etymologies_array.append(s.find('div').text.strip())
			        else:
			            etymologies_array.append(s.text.strip())
			    except:
			        etymologies_array.append(remove_tags(str(s)).strip())
			        continue

			#Parse examples
			example_array = []
			examples = soup.find("ul",{"class":"examples"}).find_all("li")
			for s in examples:
			    try:
			        x = s.find("p",{"class":"source"})
			        s = str(s).replace(str(x),'').replace('\n','').replace('*','')
			        example_array.append(remove_tags(s).strip())
			    except:
			        pass


			#Parse synonyms
			synonym_array = []
			try:
			    synonyms = soup.find("div",{"class":"clearfix open related-group synonym"}).find_all("li")
			except:
			    pass
			try:
			    for s in synonyms:
			        synonym_array.append(s.find("a").text)
			except:
			    pass

			#Parse antonyms 
			antonym_array = []
			try:
			    antonyms = soup.find("div",{"class":"clearfix open related-group antonym"}).find_all("li")
			    for s in antonyms:
			        antonym_array.append(s.text.replace('\n','').strip())
			except:
			    pass

			#Parse hypernym
			hypernym_array = []
			try:
			    hypernym = soup.find("div",{"class":"clearfix hypernym open related-group"}).find_all("li")
			    for s in hypernym:
			        hypernym_array.append(s.text.strip().replace('\n',''))    
			except:
			    pass


			#Parse samecontext 
			samecontext_array = []
			try:
			    samecontext = soup.find("div",{"class":"clearfix open related-group same-context"}).find_all("li")
			    for s in samecontext:
			        samecontext_array.append(s.text.strip().replace('\n',''))
			except:
			    pass

			#Parse rhyme 
			rhyme_array = []
			try:
			    rhyme = soup.find("div",{"class":"clearfix open related-group rhyme"}).find_all("li")
			    for s in rhyme:
			        rhyme_array.append(s.text.strip().replace('\n',''))
			except:
			    pass


			def_array = setElementInEmptyArray(def_array)
			syllable_array = setElementInEmptyArray(syllable_array)
			etymologies_array = setElementInEmptyArray(etymologies_array)
			example_array = setElementInEmptyArray(example_array)
			synonym_array = setElementInEmptyArray(synonym_array)
			antonym_array = setElementInEmptyArray(antonym_array)
			hypernym_array = setElementInEmptyArray(hypernym_array)
			samecontext_array = setElementInEmptyArray(samecontext_array)
			rhyme_array = setElementInEmptyArray(rhyme_array)

			dict = []
			dict.append({"defination":def_array})
			dict.append({"syllable":syllable_array})
			dict.append({"etymologies":etymologies_array})
			dict.append({"example":example_array})
			dict.append({"synonym":synonym_array})
			dict.append({"antonym":antonym_array})
			dict.append({"hypernym":hypernym_array})
			dict.append({"samecontext":samecontext_array})
			dict.append({"rhyme":rhyme_array})
			jsonobj = str(json.dumps({word:dict}))
			result = db.words.insert_one(json.loads(jsonobj)).inserted_id
			lastEnteredIndex = i

			print " Done! (Word ID : "+str(result)+")"
		except Exception, e:
			igWrds = {"ignored":word}
			result = db.ignored.insert_one(igWrds).inserted_id
			print " Ignored (Word ID : "+str(result)+") Cause : "+str(e)+"  Last entered index = " + str(lastEnteredIndex)
			if "quota" in str(e).lower():
				exit()
    			
        
    print "All words saved!!"
    	

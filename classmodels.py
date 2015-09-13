#Module for establishing class data.  Pulls from Armory and WCL and builds NDB Datastore models to use for character data.

import json
import os
import logging

from google.appengine.api import urlfetch
from google.appengine.api import urlfetch_errors
from google.appengine.ext import ndb
	
class Specialization(ndb.Model):
	wclId = ndb.IntegerProperty()
	name = ndb.StringProperty()
	role = ndb.IntegerProperty()
	buffs = ndb.IntegerProperty(repeated=True)
		
class CharacterClass(ndb.Model):
	name = ndb.StringProperty()
	blizzardId = ndb.IntegerProperty()
	wclId = ndb.IntegerProperty()
	armor = ndb.IntegerProperty()
	token = ndb.IntegerProperty()
	specialization = ndb.KeyProperty(kind=Specialization, repeated=True)
	buffs = ndb.IntegerProperty(repeated=True)
	
class Buff(ndb.Model):
	name = ndb.StringProperty()
	spellId = ndb.IntegerProperty()
	application = ndb.IntegerProperty()
	isExlusive = ndb.BooleanProperty()
	effect = ndb.IntegerProperty(repeated=True)
	
class ReferenceList(ndb.Model):
	entry = ndb.StringProperty(repeated=True)
	
def external_pull(site, api):
	#This will create a JSON object with the data from an external source i.e. WCL or Blizzard.
	site_data = json_pull("apikeys.json")[site]
	url = site_data[api] + site_data["key"]
	
	#XXXThis whole block will need to be updated with whatever front end and logging framework I use.XXX
	try:
		response = urlfetch.fetch(url)
	except urlfetch_errors.DeadlineExceededError:
		run_errors.append("Timeout recieving data from %s." % site)
		return None
	except urlfetch_errors.DownloadError:
		run_errors.append("Network error recieving data from %s." % site)
		return None
	except:
		run_errors.append("%s data pull encounterd an unknown error" % site)
		return None
	
	return json.loads(response.content)
	
def json_pull(dct):
	path = os.path.join(os.path.split(__file__)[0], dct)
	return json.load(open(path))
	
def build_list_data(reference, lst):
	response = ReferenceList(id=lst)
	reference_json = json_pull("reference.json")
	response.entry = []
	
	for entry in reference_json[lst]:
		response.entry.append(entry)
		
	response.put()
	
	return response

# def build_buff_data(): XXXDO_THIS_THINGXXX
	
def build_class_data(reference):	
	#Build the classes and specializations.
	
	CharacterClass.allocate_ids(max=1000)
	Specialization.allocate_ids(max=1000)
	
	class_data = []
	spec_data = []
	response = {}
	
	reference_json = json_pull("reference.json")
	wclClasses = external_pull("WCL", "classes")
	blizzClasses = external_pull("Blizzard", "character classes")
	
	#Each class is built in serial, with their specs built per class.  Keys for classes and specs are stored in class_data and spec_data, respectively, and then stored together.
	for i in range(len(wclClasses)):
		class_data.append(CharacterClass(id= i + 1))
		class_data[i].name = wclClasses[i]["name"]
		class_data[i].wclId = wclClasses[i]["id"]
		for blizzClass in blizzClasses["classes"]:
			if blizzClass["name"] == class_data[i].name:
				class_data[i].blizzardId = blizzClass["id"]
				break
		else:
			logging.error("Was unable to find a Blizzard class ID for %s" % class_data[i].name)
		class_data[i].armor = refer(reference, "armor", reference_json["class_data"][wclClasses[i]["name"]]["armor"])
		class_data[i].token = refer(reference, "token", reference_json["class_data"][wclClasses[i]["name"]]["token"])
		for j in range(len(wclClasses[i]["specs"])):
			new_spec = Specialization(id= ((i + 1) * 10) + j + 1)
			new_spec.name = wclClasses[i]["specs"][j]["name"]
			new_spec.wclId = wclClasses[i]["specs"][j]["id"]
			new_spec.role = refer(reference, "role", reference_json["class_data"][wclClasses[i]["name"]]["roles"][wclClasses[i]["specs"][j]["name"]])
			class_data[i].specialization.append(new_spec.key)
			spec_data.append(new_spec)
		response[class_data[i].name] = class_data[i]
			
	class_data += spec_data
	ndb.put_multi(class_data)
	
	return response

def refer(reference, lst, entry):
	return reference[lst].entry.index(entry)
			
def full_initialize(reference):
	#This should be done at app startup.
	
	# reference_lists = build_list_data()
	# for lst in reference_lists:
		# reference[lst] = reference_lists[lst]
		
	for lst in ["armor", "token", "role", "application", "effect"]:
		reference[lst] = build_list_data(reference, lst)
	
	# reference["buff"] = build_buff_data(reference)
	reference["class"] = build_class_data(reference)
	
	return reference


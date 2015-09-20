#Module for establishing class data.  Pulls from Armory and WCL and builds NDB 
   #Datastore models to use for character data.

import json
import os
import logging

from google.appengine.api import urlfetch
from google.appengine.api import urlfetch_errors
from google.appengine.ext import ndb


class Boss(ndb.Model):
	name = ndb.StringProperty()

	
class Zone(ndb.Model):
	name = ndb.StringProperty()
	tier = ndb.IntegerProperty()
	bosses = ndb.IntegerProperty(repeated = True)

	
class Realm(ndb.Model):
	name = ndb.StringProperty()
	formal_name = ndb.StringProperty()
	english_name = ndb.StringProperty()
	region = ndb.StringProperty()
	ruleset = ndb.StringProperty()
	time_zone = ndb.IntegerProperty()
	language = ndb.StringProperty()
	connected_realms = ndb.IntegerProperty(repeated = True)

	
class Specialization(ndb.Model):
	wcl_id = ndb.IntegerProperty()
	name = ndb.StringProperty()
	role = ndb.IntegerProperty()
	buffs = ndb.IntegerProperty(repeated = True)

	
class CharacterClass(ndb.Model):
	name = ndb.StringProperty()
	blizzard_id = ndb.IntegerProperty()
	wcl_id = ndb.IntegerProperty()
	armor = ndb.IntegerProperty()
	token = ndb.IntegerProperty()
	specialization = ndb.KeyProperty(kind = Specialization, repeated = True)
	buffs = ndb.IntegerProperty(repeated = True)

	
class Buff(ndb.Model):
	name = ndb.StringProperty()
	application = ndb.IntegerProperty()
	is_exclusive = ndb.BooleanProperty()
	effect = ndb.IntegerProperty(repeated = True)

	
class ReferenceList(ndb.Model):
	entry = ndb.StringProperty(repeated=True)

	
class PetFamily(ndb.Model):
	name = ndb.StringProperty()
	is_exotic = ndb.BooleanProperty()
	buffs = ndb.IntegerProperty(repeated = True)
	
	
def external_pull(site, api):
	#This will create a JSON object with the data from an external source i.e. 
	   #WCL or Blizzard.
	site_data = json_pull("apikeys.json")[site]
	url = site_data[api] + site_data["key"]
	
	#XXXThis whole block will need to be updated with whatever front end
	   #framework I use.XXX
	try:
		response = urlfetch.fetch(url)
	except urlfetch_errors.DeadlineExceededError:
		logging.error("Timeout recieving data from %s." % site)
		return None
	except urlfetch_errors.DownloadError:
		logging.error("Network error recieving data from %s." % site)
		return None
	except:
		logging.error("%s data pull encounterd an unknown error" % site)
		return None
	
	return json.loads(response.content)

	
def json_pull(dct):
	path = os.path.join(os.path.split(__file__)[0], dct)
	return json.load(open(path))

	
def build_list_data(list_):
	response = ReferenceList(id=list_)
	reference_json = json_pull("reference.json")
	response.entry = []
	
	for entry in reference_json[list_]:
		response.entry.append(entry)
		
	response.put()	
	return response

	
def build_buff_data():
	#Initializes buffs in Datastore.  Returns a dictionary in the format
	   #{"buff name": NDB_object}
	
	Buff.allocate_ids(max=1000000)	
	response = {}
	buff_data = []	
	reference_json = json_pull("reference.json")
	effects = ndb.Key("ReferenceList", "effect").get().entry
	
	for buff in reference_json["buff_data"]:
		logging.info = reference_json["buff_data"][buff]
		buff_reference = reference_json["buff_data"][buff]
		new_buff = Buff(id=buff_reference["id"])
		new_buff.name = buff
		new_buff.application = buff_reference["application"]
		new_buff.is_exclusive = buff_reference["exlusive"]
		new_buff.effect = []
		for effect in buff_reference["effects"]:
			new_buff.effect.append(effects.index(effect))
		buff_data.append(new_buff)
		response[new_buff.name] = new_buff
		
	ndb.put_multi(buff_data)
	return response
	
	
def build_class_data():	
	#Build the classes and specializations.
	
	CharacterClass.allocate_ids(max=1000)
	Specialization.allocate_ids(max=1000)	
	class_data = []
	spec_data = []
	pet_data = []
	response = {}	
	reference_json = json_pull("reference.json")
	wcl_classes = external_pull("WCL", "classes")
	blizzard_classes = external_pull("Blizzard", "character_classes")
	armors = ndb.Key("ReferenceList", "armor").get().entry
	tokens = ndb.Key("ReferenceList", "token").get().entry
	roles = ndb.Key("ReferenceList", "role").get().entry
	
	#Each class is built in serial, with their specs built per class.  Keys for
	   #classes and specs are stored in class_data and spec_data, 
	   #respectively, and then stored together.
	for wcl_class in wcl_classes:
		new_class = CharacterClass(id = wcl_class["id"])
		new_class.name = wcl_class["name"]
		response[new_class.name] = {"id": new_class.key.id()}
		class_reference = reference_json["class_data"][new_class.name]
		for blizzard_class in blizzard_classes["classes"]:
			if blizzard_class["name"] == new_class.name:
				new_class.blizzard_id = blizzard_class["id"]
				break
		else:
			logging.error("Was unable to find a Blizzard class ID for %s" % 
			              new_class.name)						  
		new_class.armor = armors.index(class_reference["armor"])
		new_class.token = armors.index(class_reference["armor"])
		new_class.buffs = []
		for buff in class_reference["buffs"]:
			new_class.buffs.append(reference_json["buff_data"][buff]["id"])			
		for spec in wcl_class["specs"]:
			new_spec = Specialization(id = \
			                          new_class.key.id() * 10 + spec["id"])
			new_spec.name = spec["name"]
			new_spec.wcl_id = spec["id"]
			new_spec.role = roles.index(class_reference["specs"]\
			                                           [new_spec.name]["role"])
			new_spec.buffs = []
			for buff in class_reference["specs"][new_spec.name]["buffs"]:
				new_spec.buffs.append(reference_json["buff_data"][buff]["id"])
			new_class.specialization.append(new_spec.key)
			spec_data.append(new_spec)
			response[new_class.name][new_spec.name] = new_spec.key.id()
			
	class_data += spec_data
	ndb.put_multi(class_data)
	return response

	
def build_pet_data():
	
	PetFamily.allocate_ids(max=1000)
	pet_data = []
	response = {}
	reference_json = json_pull("reference.json")
	counter = 1
	
	for pet in reference_json["pet_families"]:
		pet_reference = reference_json["pet_families"][pet]
		new_pet = PetFamily(id = counter)
		new_pet.name = pet
		new_pet.is_exotic = pet_reference["exotic"]
		new_pet.buffs = []
		for buff in pet_reference["buffs"]:
			new_pet.buffs.append(reference_json["buff_data"][buff]["id"])
		pet_data.append(new_pet)
		response[new_pet.name] = new_pet
		counter += 1
	
	ndb.put_multi(pet_data)
	return response
	
			
def build_zone_data():
	#Build information about raid instances and bosses.
	
	Zone.allocate_ids(max=1000)
	Boss.allocate_ids(max=100000)
	zone_data = []
	boss_data = []
	response = {}
	response["bosses"] = {}
	wcl_zones = external_pull("WCL", "zones")
	reference_json = json_pull("reference.json")
	zone_filter = []
	
	#zone_filter ensures that I only build zone information for the zones
	   #I have put into reference.json.
	for zone in reference_json["zone_data"]:
		zone_filter.append(zone)
	for zone in wcl_zones:
		if zone["name"] in zone_filter:
			new_zone = Zone(id = zone["id"])
			new_zone.name = zone["name"]
			new_zone.tier = reference_json["zone_data"][new_zone.name]["tier"]
			new_zone.bosses = []
			for boss in zone["encounters"]:
				new_boss = Boss(id = boss["id"])
				new_boss.name = boss["name"]
				new_zone.bosses.append(boss["id"])
				boss_data.append(new_boss)
				response["bosses"][new_boss.name] = new_boss
			zone_data.append(new_zone)
			response[new_zone.name] = new_zone
	
	zone_data += boss_data
	ndb.put_multi(zone_data)
	return response
	
	
def build_realm_data():
	#Build server information.  Currently, only supports NA servers.
	
	Realm.allocate_ids(max=10000)
	realm_data = []
	response = {}
	counter = 1
	
	blizzard_realms = external_pull("Blizzard", "realm_status")
	reference_json = json_pull("reference.json")
	
	for realm in blizzard_realms["realms"]:
		new_realm = Realm(id = counter)
		new_realm.ruleset = realm["type"]
		new_realm.name = realm["slug"]
		new_realm.formal_name = realm["name"]
		new_realm.time_zone = reference_json["time_zone"][realm["timezone"]]
		new_realm.language = reference_json["language"][realm["locale"]]
		response[new_realm.name] = new_realm
		counter += 1
	
	#I have to run through realms a second time because I need the generated
	   #id to store in connected_realms any given realm.
	for realm in blizzard_realms["realms"]:
		response[realm["slug"]].connected_realms = []
		for connected_realm in realm["connected_realms"]:
			response[realm["slug"]].connected_realms.append(
			   response[connected_realm].key.id())
		realm_data.append(response[realm["slug"]])
	
	ndb.put_multi(realm_data)
	return response
		
	
def build_all(reference):
	#This should be done at app startup.
		
	for list_ in ["armor", "token", "role", "application", "effect",\
	              "difficulty", "faction"]:
		reference[list_] = build_list_data(list_)
	
	reference["buff"] = build_buff_data()
	reference["class"] = build_class_data()
	reference["pet"] = build_pet_data()
	reference["zone"] = build_zone_data()
	reference["realm"] = build_realm_data()
	
	return reference
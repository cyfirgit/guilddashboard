
class Character(ndb.Model):
	name = ndb.StringProperty()
	class_ = ndb.IntegerProperty()
	player = ndb.IntegerProperty()
	guild = ndb.IntegerProperty()

class Player(ndb.Model):
	username = ndb.StringProperty()
	#XXX Need to figure out Blizzard OAuth and store a meaningful reference.
	blizzard_id = ndb.StringProperty()
	wcl_id = ndb.StringProperty()
	default_character = ndb.IntegerProperty()
	
class Guild(ndb.Model):
	name = ndb.StringProperty()
	server = ndb.IntegerProperty()
	faction = ndb.BooleanProperty()
	website = ndb.StringProperty()
	description = ndb.StringProperty()
	
class Team(ndb.Model):
	name = ndb.StringProperty()
	guild = ndb.IntegerProperty()
	server = ndb.IntegerProperty()
	website = ndb.IntegerProperty()
	description = ndb.StringProperty()
	
class Log(ndb.Model):
	logger = ndb.IntegerProperty()
	start = ndb.DateTimeProperty()
	end = ndb.DateTimeProperty()
	boss_pulls = ndb.IntegerProperty(repeated = True)
	
class BossPull(ndb.Model):
	team = ndb.IntegerProperty()
	start = ndb.DateTimeProperty()
	end = ndb.DateTimeProperty()
	boss = ndb.IntegerProperty()
	raid_size = ndb.IntegerProperty()
	difficulty = ndb.IntegerProperty()
	is_kill = ndb.BooleanProperty()
	wipe_percentage = ndb.IntegerProperty()
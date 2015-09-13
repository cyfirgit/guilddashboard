
def build_scenarios():
	"""Things that would need to happen:
	Build a scenario for each possible arrangement of recruits, including no recruits.
	Build a scenario for each possible arrangement of attendance.
		Analyze that scenario to determine viable offspec setups, using the specified viability filters.
		calculate rough probability of scenario occuring.
		If viable setups exist, determine the optimal spec arrangemt, preferring:
			all main specs/main roster + standby roster >
			removing standby players >
			adding bench players >
			switching dps to offspec >
			switching heals to offspec >
			switching tanks to offspec >
			switching, in role order, benches to offspec
		Then, if viable setup exists, add optimal spec arrangement to the scenario build.
	"""

def run_scenarios:
	"""
	We want to run each scenario individually and tabulate results.
	Then, we want to present the data in a meaningful fashion:
		If the purpose of the run was to analyze current roster without changes, present a detailed view of the roster:
			Chance by player of-
				sitting a standby player
				calling up a bench player
				running a player in offspec
			Gearing factors, both token and armor.
			Chance of calling the raid/running with a broken comp/pugging in players.
			Chance of missing a raid buff, by buff.
		If the purpose was to recommend a recruiting strategy:
			Present best X recruits, with an expandable breakdown that shows how it *improves* the metrics above.
		THOUGHTS: ALWAYS show the current scenario.  Cache it?  Build it automatically (or in the background,) when you adjust the roster? (Not automatically.  Load on demand though?)
	"""
	
def calculate_scenario(scenario):
	# Once a scenario has validated any fast filters, perform a full calculation of the scenario and return the resulting data.	
	armor_balance = [0, 0, 0, 0]
	token_balance = [0, 0, 0]
	role_balance = [0, 0, 0, 0]
	buff_balance = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]#Need to adjust this in a way that will show which application method, with zero meaning not applied.  Reference list needs to start w/ "Missing".
	exclusive_buffs = []
	for character in scenario:
		armor_balance[character.characterClass.armor] += 1
		token_balance[character.characterClass.token] += 1
		role_balance[character.currentSpecialization.role] += 1
		for buff in character.characterClass.classBuffs:
			for effect in buff.effects:
				buff_balance[effect.effectType] += 1
		for buff in character.currentSpecialization.specializationBuffs:
			for effect in buff.effects:
				buff_balance[effect.effectType] += 1
		if character.characterClass.exclusiveBuffs != None:
			exclusive_buffs.append(character.characterClass.exclusiveBuffs)
	results = [armor_balance, token_balance, role_balance, buff_balance, exclusive_buffs]
	return results
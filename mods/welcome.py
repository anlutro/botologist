import json
import os.path

greets = {
	"afrikaans": "Goeie môre",
	"albanian": "Mirëmëngjes",
	"amharic": "Endermen aderkh",
	"arabic": "Sabah-il-kheir",
	"aramaic": "Yasetel liesbukh",
	"armenian": "Bari luys",
	"assyrian": "Kedamtookh brikhta",
	"azerbaijani": "Sabahiniz Xeyr",
	"bamougoum": "Oli yah",
	"bangla": "Shuvo sokal",
	"basque": "Egun on",
	"belarussian": "Dobray ranitsy",
	"bemba": "Mwashibukeni",
	"bengali": "Shu-probhaat",
	"bisaya": "Maayong adlaw",
	"bosnian": "Dobro jutro",
	"bulgarian": "Dobro utro",
	"cantonese": "Zou san",
	"catalan": "Bon dia",
	"cebuano": "Maayong buntag!",
	"chichewa": "Mwadzuka bwanji",
	"chinese": "Zao shang hao", "mandarin": "Zao shang hao",
	"cornish": "Myttin da",
	"corse": "Bun ghjiornu",
	"creole": "Bonjou",
	"croatian": "Dobro jutro",
	"czech": "Dobré ráno",
	"danish": "God morgen",
	"dari": "Sob Bakhaer",
	"divehi": "Baajjaveri hedhuneh",
	"dutch": "Goedemorgen",
	"english": "Good morning",
	"esperanto": "Bonan matenon",
	"estonian": "Tere hommikust",
	"etsakor": "Naigbia",
	"fanti": "Me ma wo akye",
	"fijian": "Sa Yadra",
	"filipino": "Magandang umaga po",
	"finnish": "Hyvää huomenta",
	"flanders": "Hey-Diddly-Ho",
	"flemish": "Goeie morgen",
	"french": "Bonjour",
	"frisian": "Goeie moarn",
	"galician": "Bos dias",
	"georgian": "Dila mshvidobisa",
	"german": "Guten Morgen",
	"greek": "Kali mera",
	"greenlandic": "Iterluarit",
	"gujarati": "Subh Prabhat",
	"hakka": "On zoh",
	"hausa": "Inaa kwana",
	"hawaiian": "Aloha kakahiaka",
	"hebrew": "Boker tov",
	"hiligaynon": "Maayong aga",
	"hindi": "Shubh prabhat",
	"hungarian": "Jo reggelt",
	"icelandic": "Gódan daginn",
	"ilocano": "Naimbag nga Aldaw",
	"indonesian": "Selamat pagi",
	"irish": "Dia duit ar maidin",
	"italian": "Buon giorno",
	"japanese": "Ohayo gozaimasu",
	"kannada": "Shubhodaya",
	"kapampangan": "Mayap a abak",
	"kazakh": "Kairly Tan",
	"khmer": "Arrun Suo Sdey",
	"kimeru": "Muga rukiiri",
	"kinyarwanda": "Muraho",
	"konkani": "Dev Tuka Boro Dis Divum",
	"korean": "Annyunghaseyo",
	"kurdish badini": "Spede bash",
	"kurdish sorani": "Beyani bash",
	"lao": "Sabaidee",
	"latvian": "Labrit",
	"lithuanian": "Labas rytas",
	"lozi": "U zuhile",
	"luganda": "Wasuze otyano",
	"luo": "Oyawore",
	"luxembourg": "Gudde moien",
	"macedonian": "Dobro utro",
	"malayalam": "Suprabhatham",
	"malay": "Selamat pagi",
	"maltese": "Għodwa it-tajba",
	"manx": "Moghrey mie",
	"maori": "Ata marie",
	"mapudungun": "Mari mari",
	"marathi": "Suprabhat",
	"mongolian": "Öglouny mend",
	"navajo": "Yá'át'ééh abíní",
	"ndebele": "Livukenjani",
	"nepali": "Subha prabhat",
	"northern Sotho": "Thobela",
	"norwegian": "God morgen",
	"owambo": "Wa lalapo",
	"pashto": "Sahar de pa Khair",
	"persian": "Subbakhair",
	"pirate": "Avast, ye scurvy dog",
	"polish": "Witaj",
	"polynesian": "Ia ora na",
	"portuguese": "Bom dia",
	"punjabi": "Sat Shri Akal",
	"rapa Nui": "Iorana",
	"romanian": "Buna dimineata",
	"russian": "Dobroye utro",
	"samoan": "Talofa lava",
	"sanskrit": "Suprabhataha",
	"sardinian": "Bona dia",
	"serbian": "Dobro jutro",
	"shona": "Mangwanani",
	"sinhalese": "Suba Udesanak Wewa",
	"slovak": "Dobré ráno",
	"slovenian": "Dobro jutro",
	"somalian": "Subax wanaagsan",
	"southern sotho": "Dumela",
	"spanish": "Buenos dias",
	"swahili": "Habari za asubuhi",
	"swazi": "Sawubona",
	"swedish": "God morgon",
	"tagalog": "Magandang umaga",
	"taiwanese": "Gau cha",
	"tamil": "Kaalai Vannakkam",
	"telugu": "Subhodayamu",
	"tetum": "Dader diak",
	"thai": "Aroon-Sawass",
	"tibetan": "Nyado delek",
	"tonga": "Mwabuka buti",
	"tswana": "Dumela",
	"twi": "Me ma wo maakye",
	"turkish": "Günaydin",
	"turkmen": "Ertiringiz haiyirli bolsun",
	"ukrainian": "Dobri ranok",
	"urdu": "Subha Ba-khair",
	"uzbek": "Khairli kun",
	"vietnamese": "Xin chao",
	"welsh": "Bore da",
	"xhosa": "Bhota",
	"xitsonga": "Avuxeni",
	"xoruba": "E karo",
	"zulu": "Sawubona",
	"!kung san": "Tuwa",
	"australian": "G'day",
	"klingon": "nuqneH", "tlhingan hol": "nuqneH",
	"vulcan": "Dif-tor heh smusma",
	"romulan": "Brhon mnekha",
	"ferengi": "Welcome to our home. Please place your thumbprint on the legal waivers and deposit your admission fee in the slot by the door. Remember, my house is my house,"
}

users = {}

def stor_path():
	root = os.path.dirname(os.path.dirname(__file__))
	return os.path.realpath(root)

def addgreet(user, lang):
	global greets, users
	lang = lang.lower()

	if lang not in greets:
		return 'I don\'t speak that language!'

	users[user] = lang
	storpath = stor_path() + '/storage/welcome_users.json'
	with open(storpath, 'w+') as f:
		json.dump(users, f)

	return 'I\'ll remember that!'

def addlang(lang, greet):
	global greets
	lang = lang.lower()
	greets[lang] = greet
	storpath = stor_path() + '/storage/welcome_greets.json'
	with open(storpath, 'w+') as f:
		json.dump(greets, f)

def greet(user):
	global greets, users

	if not users:
		storpath = stor_path() + '/storage/welcome_users.json'
		with open(storpath, 'r') as f:
			users = json.load(f)

	if user in users:
		return greets[users[user]] + ' ' + user + '!'

import yaml, json, requests

def LoadYaml(yamlString):
    with open(yamlString, "r") as stream:
        try:
            return yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)
            
            
blueprintData ={}
typeData = {}
piData = {}

bpIDTable = {}
priceData = {}
RegionMarketHistoryData = {}

TheBuildTree = {}
RawMaterials = {}
PIonlyBuildTree = {}

ids = {
	"Scordite":1228,
	"Veldspar":1230,
	"Concentrated Veldspar":17470,
	"Dense Veldspar":17471
}

planetInfo = {
"11":  {"name":"Temperate","materials":["2268","2073","2287","2288","2305"]},
"12":  {"name":"Ice","materials":["2268","2310","2073","2286","2272"]},
"13":  {"name":"Gas","materials":["2268","2309","2310","2311","2267"]},
"2014":{"name":"Oceanic","materials":["2268","2073","2286","2287","2288"]},
"2015":{"name":"Lava","materials":["2308","2267","2272","2306","2307"]},
"2016":{"name":"Barren","materials":["2268","2267","2270","2073","2288"]},
"2014":{"name":"Oceanic","materials":["2268","2073","2286","2287","2288"]}
}

AbaiPlanets = [
{"id":1,"type":"Barren","typeID":2016},
{"id":2,"type":"Lava","typeID":2015},
{"id":3,"type":"Oceanic","typeID":2014},
{"id":4,"type":"Gas","typeID":13},
{"id":5,"type":"Temperate","typeID":11},
{"id":6,"type":"Gas","typeID":13},
{"id":7,"type":"Gas","typeID":13},
{"id":8,"type":"Gas","typeID":13},
{"id":9,"type":"Ice","typeID":12},
]

Regions = {
    "FORGE":10000002,
    "DOMAIN":10000043
}


def Loadin():
    global blueprintData
    global typeData
    global piData
    #   
    print("Loading Blueprint Data - 1/4")
    blueprintData = LoadYaml("blueprints.yaml")
    #
    print("Loading Item Data - 2/4")
    typeData = LoadYaml("typeIDs.yaml")
    #
    print("Loading Planet Data - 3/4")
    piData = LoadYaml("planetSchematics.yaml")
    #
    print("Fetching Prices - 4/4")
    UpdatePrices()
    print("Done Loadin")
    
def NameOf(typeIDString):
    return typeData[int(typeIDString)]["name"]["en"]

def formatPrice(price,dp=2):
    return '{:,.{prec}f}'.format(price,prec=dp)

def GetPrice(typeIDString):
    typeIDString = str(typeIDString)
    global priceData
    if typeIDString in priceData:
        return float(priceData[typeIDString]["price"])
    elif int(typeIDString) in typeData and "basePrice" in typeData[int(typeIDString)]:
        return float(typeData[int(typeIDString)]["basePrice"])
    else:
        return float(-1)
    
    
def UpdatePrices():
    global priceData
    priceData= {}
    pricelist = json.loads(requests.get("https://esi.evetech.net/latest/markets/prices/?datasource=tranquility").content)
    for price in pricelist:
        acutalPrice = 0
        if "average_price" in price:
            acutalPrice = price["average_price"]
        else:
            acutalPrice = price["adjusted_price"]
        priceData[str(price["type_id"])] = {"price":acutalPrice}
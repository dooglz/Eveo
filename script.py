import yaml
import functools
import pprint
import requests
import json
import math

def LoadYaml(yamlString):
    with open(yamlString, "r") as stream:
        try:
            return yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)


blueprintData = LoadYaml("blueprints.yaml")
typeData = LoadYaml("typeIDs.yaml")
piData = LoadYaml("planetSchematics.yaml")
RawMaterials = {}

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

bpIDTable = {}
priceData = {}

def GetAllResourcesForPlanetList(planetList):
    resources = set()
    for planet in planetList:
        resources.update(planetInfo[str(planet["typeID"])]["materials"])
    return resources    

Regions = {
    "FORGE":10000002,
    "DOMAIN":10000043
}

def NameOf(typeIDString):
    return typeData[int(typeIDString)]["name"]["en"]

def formatPrice(price):
    return f'{price:,.2f}'

def GetPrice(typeIDString):
    typeIDString = str(typeIDString)
    global priceData
    if typeIDString in priceData:
        return float(priceData[typeIDString]["price"])
    elif int(typeIDString) in typeData and "basePrice" in typeData[int(typeIDString)]:
        return float(typeData[int(typeIDString)]["basePrice"])
    else:
        return float(-1)


def GetPriceF(typeIDString):
     return formatPrice(GetPrice(typeIDString))

def formatPriceBulk(typeIDString,quantity):
    if quantity == 1:
            return formatPrice(GetPrice(typeIDString))
    return formatPrice(GetPrice(typeIDString)*quantity)+ " ("+ str(quantity)+"*"+GetPriceF(typeIDString)+")"

def SquashBuildListTree(buildList):
    listy = []
    for list in buildList:
        listy+=list
    return listy

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

RegionMarketHistoryData = {}
def GetRegionMarketHistory(region,typeIDString):
    global RegionMarketHistoryData
    hashID = typeIDString+str(region)
    if hashID in RegionMarketHistoryData:
        return RegionMarketHistoryData[hashID]
    jsonData = requests.get("https://esi.evetech.net/latest/markets/"+str(region)+"/history/?datasource=tranquility&type_id="+str(typeIDString)).content
    data = json.loads(jsonData)
    if 'error' in data or len(data) == 0:
        data =  [{'average': 0.0, 'highest': 0.0, 'lowest': 0.0, 'order_count': 0.0, 'volume': 0.0}]
    RegionMarketHistoryData[hashID] = data  
    return data

def AverageRegionMarketHistory(history):
    count = 0
    data = {'average': 0.0, 'highest': 0.0, 'lowest': 0.0, 'order_count': 0.0, 'volume': 0.0}
    for price in history:
        for priceData in data:
            data[priceData] += float(price[priceData])
        count += 1
    for priceData in data:
        data[priceData] /= count
    return data

def getBPIdforID(inID):
    if inID in bpIDTable:
        return bpIDTable[inID]
    for key in blueprintData:
            if("manufacturing" in blueprintData[key]["activities"] and "products" in blueprintData[key]["activities"]["manufacturing"] ):
                for product in blueprintData[key]["activities"]["manufacturing"]["products"]:
                    if product["typeID"] == inID:
                        bpIDTable[inID] = key
                        return key
    return 0

def PrintTree():
    for key in blueprintData:
        myTypedata = typeData[key]
        print("".rjust(40, '-'))
        print(str(key) + " " + myTypedata["name"]["en"])
        if "ImUsedForMaking" in blueprintData[key]:
            print("\n I'm used for making:\n")
            for makeID in blueprintData[key]["ImUsedForMaking"]:
                print("\t"+str(makeID) + " - "+ NameOf(makeID))
        if "manufacturing" in blueprintData[key]["activities"] and "materials" in blueprintData[key]["activities"]["manufacturing"]:
            print("\n I Need:\n\t")
            materials = blueprintData[key]["activities"]["manufacturing"]["materials"]
            txt = "\n\t"
            for material in materials:
                materialID = material["typeID"]
                if not materialID in typeData:
                    txt += str(materialID) + " - NULL: " + str(material["quantity"])+"\n\t"
                    continue
                txt += str(materialID) + " - "+ NameOf(materialID) +": "+ str(material["quantity"])+"\n\t"
            print(txt)


def PrintRawMaterials():
    for materialID in RawMaterials:
        print("".rjust(40, '-'))
        print(str(materialID) + " " + NameOf(materialID))
        for makeID in RawMaterials[materialID]["ImUsedForMaking"]:
                print("\t"+str(makeID) + " - "+ NameOf(makeID))


def RegisterProductOf(materialID,parentID,Registration):
    materialBPID = getBPIdforID(materialID)
    bp_OR_raw_MakingList = False
    if  materialBPID == 0:
        if materialID in typeData:
            if not materialID in RawMaterials:
                  RawMaterials[materialID] = {Registration:[]}
            bp_OR_raw_MakingList = RawMaterials[materialID][Registration]
        else:
            return #Not a BP or a type.
    else:
        if not Registration in blueprintData[materialBPID]:
            blueprintData[materialBPID][Registration] = []
        bp_OR_raw_MakingList = blueprintData[materialBPID][Registration]
    bp_OR_raw_MakingList.append(parentID)



def AddMeToAllComponets_Recursive(parentID,materialID,Registration):
    RegisterProductOf(materialID,parentID,Registration)
    materialBPID = getBPIdforID(materialID)
    if materialBPID != 0:
        childMaterials = getBPMaterials(materialBPID)
        for childMaterial in childMaterials:
            childMaterialID = childMaterials["typeID"]
            AddMeToAllComponets_Recursive(parentID,childMaterialID,Registration)
            

def buildIndyTree():
    for key in blueprintData:
        myTypedata = typeData[key]
        materials = getBPMaterials(key)
        if(materials):
            txt = "\n\t"
            for material in materials:
                materialID = material["typeID"]
                RegisterProductOf(materialID,key,"ImUsedForMaking")
    print("ImUsedForMaking Pass done")
    for key in blueprintData:
        materials = getBPMaterials(key)
        if(materials):
            for material in materials:
                AddMeToAllComponets_Recursive(key,material,"ImIndirectlyUsedForMaking")

    #PrintTree()        

                #print(functools.reduce(lambda r, b: r+typeData[b["typeID"]]["name"]["en"]+":"+str(b["quantity"])+",", materials,""))

def getBPMaterials(inID):
    if inID in blueprintData:
        if("manufacturing" in blueprintData[inID]["activities"] and "materials" in blueprintData[inID]["activities"]["manufacturing"] ):
            return blueprintData[inID]["activities"]["manufacturing"]["materials"]
    return False

TheBuildTree = {}
RawMaterials = {}
PIonlyBuildTree = {}
def ConstructBuildTree():
    global TheBuildTree 
    global RawMaterials
    global PIonlyBuildTree
    TheBuildTree = {}
    RawMaterials = {}
    PIonlyBuildTree = {}
    for bpID in blueprintData:
        if not bpID in typeData or typeData[bpID]["published"] == False:
            #print ("BP is unpublished "+str(bpID))
            continue
        #Bail if this is not something valid that builds something valid
        if( not "manufacturing" in blueprintData[bpID]["activities"] or not "products" in blueprintData[bpID]["activities"]["manufacturing"] ):
            continue
        manufacturingData = blueprintData[bpID]["activities"]["manufacturing"]
        #
        productData  = manufacturingData["products"]
        if len(productData) > 1:
            print ("BP has more than one product! "+str(bpID))
            continue
        #
        iMakeThisID = productData[0]["typeID"]
        if not iMakeThisID in typeData:
            print ("BP makes an uknown product! "+str(bpID))
            continue
        #
        if typeData[iMakeThisID]["published"] == False :
            print ("BP makes an unpublished product! "+str(bpID))
            continue
        #
        IDstring = str(iMakeThisID)
        if IDstring in TheBuildTree:
            print ("BP makes the same product as another! "+str(bpID))
            continue
        #
        if GetPrice(IDstring) == -1:
            print ("BP makes an Unsellable Item! bp:"+str(bpID)+" item:"+IDstring+" - "+typeData[iMakeThisID]["name"]["en"])
            continue
        if not "materials" in manufacturingData:
            print ("BP has no materials! "+str(bpID))
            continue
        #
        badCheck = False
        for material in manufacturingData["materials"]:
            if material["typeID"] == iMakeThisID:
                print ("BP needs itself as material! bp:"+str(bpID)+" - "+typeData[iMakeThisID]["name"]["en"])
                badCheck = True
                continue
        if(badCheck):
            continue
        #
        BuildItem = {}
        BuildItem["ID"] = iMakeThisID
        BuildItem["IDstring"] = IDstring
        BuildItem["blueprintID"] = bpID
        BuildItem["materialsToBuild"] = []
        BuildItem["quantityMade"] = productData[0]["quantity"]
        for material in manufacturingData["materials"]:
            buildMaterial = {"typeID":material["typeID"],"IDstring":str(material["typeID"]), "quantity":material["quantity"]}
            buildMaterial["type"] = "todo"
            BuildItem["materialsToBuild"].append(buildMaterial)
        #
        BuildItem["name"] = typeData[iMakeThisID]["name"]["en"]
        TheBuildTree[IDstring] = BuildItem
    #
    for piDataID in piData:
        piItem = piData[piDataID]
        #
        BuildItem = {}
        BuildItem["PiSchematicID"] = piDataID
        BuildItem["materialsToBuild"] = []
        BuildItem["quantityMade"] = 0
        #
        for inputOutputID in piItem["types"]:
            inputOutputItem = piItem["types"][inputOutputID]
            if (not inputOutputID in typeData):
                print ("PI BP "+str(piDataID)+" is involved with bad type "+str(inputOutputItem))
                continue
            if inputOutputItem["isInput"] == True:
                buildMaterial = {"typeID":inputOutputID,"IDstring":str(inputOutputID), "quantity":inputOutputItem["quantity"]}
                buildMaterial["type"] = "PI"
                BuildItem["materialsToBuild"].append(buildMaterial)
            else:
                 BuildItem["quantityMade"] = inputOutputItem["quantity"]
                 BuildItem["ID"] = inputOutputID
                 BuildItem["IDstring"] = str(inputOutputID)
                 BuildItem["name"] = typeData[inputOutputID]["name"]["en"]
        #
        if(not "ID" in BuildItem):
            print ("PI_BP makes no product!"+str(piDataID))
            continue
        TheBuildTree[BuildItem["IDstring"]] = BuildItem
        PIonlyBuildTree[BuildItem["IDstring"]] = BuildItem
    #
    #Link up Build items to materials/other Build items
    for IDstring in TheBuildTree:
        BuildItem = TheBuildTree[IDstring]
        for material in BuildItem["materialsToBuild"]:
            if material["IDstring"] in TheBuildTree:
                material["type"] = "Buildable"
                materialBuildItem = TheBuildTree[material["IDstring"]]
                if not "itemsIBuild" in materialBuildItem:
                    materialBuildItem["itemsIBuild"] = []
                materialBuildItem["itemsIBuild"].append({"IDstring":IDstring,"forQuantity":material["quantity"]})
            elif material["typeID"] in typeData:
                material["type"] = "RawMaterial"
                if not material["IDstring"] in RawMaterials:
                    RawMaterials[material["IDstring"]] = {"name":typeData[material["typeID"]]["name"]["en"]}
                materialRaw = RawMaterials[material["IDstring"]]
                if not "itemsIBuild" in materialRaw:
                    materialRaw["itemsIBuild"] = []
                materialRaw["itemsIBuild"].append({"IDstring":IDstring,"forQuantity":material["quantity"]})
    #Bom Calculation
    for IDstring in TheBuildTree:
        BuildItem = TheBuildTree[IDstring]
        BuildItem["bom"] = getFullBoM(IDstring)


def WhatCanIBuildWith(materialList):
    #it would be faster to loop though itemsIBuild, but this works neatly.
    buildableList= []
    for IDstring in TheBuildTree:
        BuildItem = TheBuildTree[IDstring]
        materialCount = 0
        for material in BuildItem["materialsToBuild"]:
            if material["IDstring"] in materialList:
                materialCount += 1
        if materialCount == len(BuildItem["materialsToBuild"]):
            buildableList.append(IDstring)
    return buildableList
        
def PrintBuildableList(buildableList):
    if(len(buildableList) > 0 and type(buildableList[0]) == list):
        #This is a tree
        teircount = 0
        for sublist in buildableList:
            print ("---- TEIR "+ str(teircount) + "---")
            PrintBuildableList(sublist)
            teircount +=1
        return
    for IDstring in buildableList:
        buildItem = TheBuildTree[IDstring]
        marketData = AverageRegionMarketHistory(GetRegionMarketHistory(Regions["FORGE"],IDstring))
        print (IDstring + "\t - " + buildItem["name"] + " "+ formatPriceBulk(IDstring, buildItem["quantityMade"])+ " --  mProfit:" + f'{buildItem["bom"]["materialProfit"]:,.2f}' + " -- OrderCount:"+f'{marketData["order_count"]:,.1f}')

def FindAllBuildableWith(materialList):
    buildableTree = [WhatCanIBuildWith(materialList)]
    growingMaterialsSet = set()
    growingMaterialsSet.update(materialList)
    growingMaterialsSet.update(buildableTree[-1])
    #
    while(True):
        #append buildables to materialList
        newBuildableList = WhatCanIBuildWith(list(growingMaterialsSet))
        newMaterials = list(set(newBuildableList) - growingMaterialsSet)
        growingMaterialsSet.update(newBuildableList)
        if len(newMaterials) == 0:
            return buildableTree
        buildableTree.append(newMaterials)


def getFullBoM(itemIDString):
    materials = {}
    makelist = {}
    materialCost = 0
    costToBuyComponents = 0
    quantityMade = TheBuildTree[itemIDString]["quantityMade"]
    for material in TheBuildTree[itemIDString]["materialsToBuild"]:
        materialIDString = material["IDstring"]
        if materialIDString == itemIDString:
            print("BOM RECURSION!:" + itemIDString)
            continue
        if material["type"] == "Buildable":
            subBom = getFullBoM(materialIDString)
            submaterials = subBom["materials"]
            subQuantityProduced = TheBuildTree[materialIDString]["quantityMade"]
            quantityNeeded = material["quantity"]
            runCount = math.ceil(quantityNeeded/subQuantityProduced)
            for key in submaterials:    
                submaterials[key] *= runCount
            materials.update(submaterials)
            makelist.update(subBom["makelist"])
            if not materialIDString in makelist:
                makelist[materialIDString] = {"price":GetPrice(materialIDString),"price_Batch":0,"quantityNeeded":0,"runsRequired":0,"QuantityProduced":subQuantityProduced,"materialCost_x1":subBom["materialCost"],"costToBuyComponents_x1":subBom["costToBuyComponents"],"costToBuyComponents":0,"materialCost":0}
            makelist[materialIDString]["quantityNeeded"] += quantityNeeded
            makelist[materialIDString]["price_Batch"] += quantityNeeded * GetPrice(materialIDString)
            makelist[materialIDString]["runsRequired"] += runCount
            makelist[materialIDString]["costToBuyComponents"] += runCount * subBom["costToBuyComponents"]
            makelist[materialIDString]["materialCost"] += runCount * subBom["materialCost"]
            costToBuyComponents += GetPrice(materialIDString) * quantityNeeded
            materialCost += subBom["materialCost"] * runCount
            continue
        if material["type"] == "RawMaterial":
            if not materialIDString in materials:
                materials[materialIDString] = 0
            materials[materialIDString] += material["quantity"]
            materialCost += GetPrice(materialIDString) * material["quantity"]
            continue
        print("mat type" + material["type"] + " - " + materialIDString)
    priceBatch = quantityMade*GetPrice(itemIDString)
    materialProfit = (priceBatch/materialCost) if not materialCost == 0 else 0
    return {"materials":materials,"materialProfit":materialProfit,"makelist":makelist,"itemIDString":itemIDString, "priceUnit": GetPrice(itemIDString),"priceBatch":priceBatch, "costToBuyComponents":costToBuyComponents,"materialCost":materialCost,"quantityMade":quantityMade}


def PrintBom(bom,recursive=False,prefix="",printHeadder=True):  
    if(printHeadder):
        print(prefix+"["+bom["itemIDString"]+"] " + NameOf(bom["itemIDString"]) + " - Price:"+ formatPriceBulk(bom["itemIDString"],bom["quantityMade"]) +" - mPrice:"+ formatPrice(bom["materialCost"]) + " - PriceOfComponents:"+formatPrice(bom["costToBuyComponents"])+ " - MProfit:"+str(bom["materialProfit"]))
    print(prefix+"Total Raw:")
    for material in bom["materials"]:
        quantity = bom["materials"][material]
        print(prefix+"\t"+material + " - " + NameOf(int(material)) + " x"+ str(quantity) + " - "+ formatPriceBulk(material,quantity))
        if(recursive and material in TheBuildTree):
              print("TODO")
    if len(bom["makelist"]) ==0:
        return
    print(prefix+"Intermediate Products:")
    for material in bom["makelist"]:
        howMuchisMadePerRun = TheBuildTree[material]["quantityMade"]
        quantity = bom["makelist"][material]["quantityNeeded"]
        subBom = getFullBoM(material)
        print(prefix+"\t"+material + " - " + NameOf(int(material))+" --  need:"+ str(quantity) + " perRun:"+str(howMuchisMadePerRun)+ " - Price:" + formatPriceBulk(material,quantity) +" - mPrice:"+ formatPrice(subBom["materialCost"]) + " - PriceOfComponents:"+formatPrice(subBom["costToBuyComponents"])+ " - MProfit:"+str(subBom["materialProfit"]))
        if(recursive and material in TheBuildTree):
            print(prefix+"\t-----------------V")
            myprefix = prefix + "\t\t\t"
            PrintBom(subBom,recursive,myprefix,False)



def GetMaterialCoverage(ItemIDstring,itemsIhaveList):
    externalIsk = 0
    haveIsk = 0
    for material in TheBuildTree[ItemIDstring]["bom"]["materials"]:
        materialPrice = GetPrice(material) * TheBuildTree[ItemIDstring]["bom"]["materials"][material]
        if material in itemsIhaveList:
            haveIsk += materialPrice
        else:
            externalIsk += materialPrice
    percentageHave = haveIsk / (externalIsk+haveIsk)
    return {"marketPrice":GetPrice(ItemIDstring), "haveIsk":haveIsk,"externalIsk":externalIsk,"percentageHave":percentageHave}


def FindProfitableWith(materialList,materialProfitThresh=2.0,orderCountThresh=100,haveIskPercentThresh = 0.7):
    data = []
    for buildItemID in TheBuildTree:
        buildItem  = TheBuildTree[buildItemID]
        materialProfit = buildItem["bom"]["materialProfit"]
        if materialProfit < materialProfitThresh:
            continue
        coverage = GetMaterialCoverage(buildItemID,materialList)
        if coverage["percentageHave"] < haveIskPercentThresh:
            continue
        orderCount =  AverageRegionMarketHistory(GetRegionMarketHistory(Regions["FORGE"],buildItemID))["order_count"]
        if orderCount < orderCountThresh:
            continue
        datapoint = coverage
        datapoint["itemIDString"] = buildItemID
        datapoint["materialProfit"] = materialProfit
        datapoint["order_count"] = orderCount
        data.append(datapoint)
    return data

def PrintProfitableList(profitableList):
    sortedlist = sorted(profitableList,  key=lambda thing:thing["materialProfit"])
    for dataPoint in sortedlist:
        buildItemIDstring = dataPoint["itemIDString"]
        buildItem = TheBuildTree[buildItemIDstring]
        print (buildItemIDstring + "\t - " + NameOf(buildItemIDstring)+ " "+ formatPriceBulk(buildItemIDstring, buildItem["quantityMade"])+ " --  mProfit:" + f'{dataPoint["materialProfit"]:,.2f}' + " -- OrderCount:"+f'{dataPoint["order_count"]:,.1f}' + " -- Have:"+f'{dataPoint["percentageHave"]:,.1f}%')



ConstructBuildTree()
PrintBom(getFullBoM("17404"),True)

itemsIHave = ["34","35","36"] + list(GetAllResourcesForPlanetList(AbaiPlanets))
PrintBuildableList(FindAllBuildableWith(itemsIHave))
PrintBom(getFullBoM("3697"),True)


sortedBuildables = sorted(SquashBuildListTree(FindAllBuildableWith(itemsIHave)),  key=lambda thing:TheBuildTree[thing]["bom"]["materialProfit"] )
PrintBuildableList(sorted(SquashBuildListTree(FindAllBuildableWith(itemsIHave)),  key=lambda thing:TheBuildTree[thing]["bom"]["materialProfit"] ))
AverageRegionMarketHistory(GetRegionMarketHistory(Regions["FORGE"],"28750"))["order_count"]


PrintBuildableList(list(filter(lambda x: (AverageRegionMarketHistory(GetRegionMarketHistory(Regions["FORGE"],x))["order_count"]> 100 and TheBuildTree[x]["bom"]["materialProfit"]>2.0), sortedBuildables)))

pprint.pprint(sorted(FindProfitableWith(itemsIHave),  key=lambda thing:thing["materialProfit"]))


PrintProfitableList(FindProfitableWith(itemsIHave,1.8,80,0.7))





SuprCnDuctrs
Coolant
Rocket Fuel
SyntheticOil
Oxides
SilictGlass
Transmitter
WCooledCPU
MechaParts
ConstrcnBlcks
EnricdUranium
CnsumrELctrics
MiniElectronics
Nanites
Biocells
mFiber Shielding
Viral Agent
Fertilizer
GeneEnh Livstok
Livestock
Polytextiles
Test Cultures
SupertnsilePlstcs
Polyaramids
UkomiSuperCnductr
Condensates
Camera Drones
SyntheticSynapses
HighTechTransmitr
GelMatrixBiopaste
Supercomputers
Robotics
Smartfab Units
Nuclear Reactors
Guidance Systems
Neocoms
Planetary Vehicles
BioT RsrchRports
Vaccines
IndustrialExplsvs
Hermetic Membranes
Tcran Microcotrller
Data Chips
HazmatDetectSystems
CryoprotctntSolution
OrgancMortrAplcators
Sterile Conduits
Nano-Factory
SlfHarmonizngPwerCore
RcursiveComputngModule
Broadcast Node
IntgrityRsponseDrones
Wetware Mainframe
Water
Plasmoids
Electrolytes
Oxygen
Oxidizing Compound
Reactive Metals
Precious Metals
Toxic Metals
Chiral Structures
Silicon
Bacteria
Biomass
Proteins
Biofuels
Industrial Fibers

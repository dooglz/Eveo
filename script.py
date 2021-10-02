import yaml
import functools
import pprint
def LoadYaml(yamlString):
    with open(yamlString, "r") as stream:
        try:
            return yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)


blueprintData = LoadYaml("blueprints.yaml")
typeData = LoadYaml("typeIDs.yaml")
RawMaterials = {}

ids = {
	"Scordite":1228,
	"Veldspar":1230,
	"Concentrated Veldspar":17470,
	"Dense Veldspar":17471
}

rates = {
	""
}


#def GetRegionMarketHistory(a,b,c):
	#requests.get("https://esi.evetech.net/latest/markets/"+str(10000043)"/history/?datasource=tranquility&type_id=28427")

def NameOf(id):
	return typeData[id]["name"]["en"] 


def WhatCanThisBuild(listofItemIDS):
    pass

bpIDTable = {}




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
def ConstructBuildTree():
    global TheBuildTree 
    global RawMaterials
    TheBuildTree = {}
    RawMaterials = {}
    for bpID in blueprintData:
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
        IDstring = str(iMakeThisID)
        if IDstring in TheBuildTree:
            print ("BP makes the same product as another! "+str(bpID))
            continue
        #
        if not "materials" in manufacturingData:
            print ("BP has no materials! "+str(bpID))
            continue
        #
        TheBuildTree[IDstring] = {}
        BuildItem = TheBuildTree[IDstring]
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
    for IDstring in buildableList:
        print (IDstring + "\t - " + TheBuildTree[IDstring]["name"])

def FindAllBuildableWith(materialList):
    buildableList = []
    amount = 0
    growingMaterialsSet = set()
    growingMaterialsSet.update(materialList)
    #
    while(True):
        #append buildables to materialList
        newBuildableList = WhatCanIBuildWith(list(growingMaterialsSet))
        growingMaterialsSet.update(newBuildableList)
        buildableList.append(newBuildableList)
        if len(newBuildableList) == amount:
            return buildableList
        else:
            amount = len(newBuildableList)

    
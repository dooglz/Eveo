import yaml,math
TC = {'R':"\x1b[31m",'C':"\x1b[0m",'G':"\x1b[32;46m",'Y':"\x1b[33m",'BG':"\x1b[92m",'M':"\x1b[95m"}
def TCM(txt,C):
    return TC[C]+txt+TC['C']

def formatPrice(price,dp=2):
    return '{:,.{prec}f}'.format(price,prec=dp)

def LoadYaml(yamlString):
    with open(yamlString, "r") as stream:
        try:
            print("Loading ",yamlString)
            return yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)
            
__PIDATA = 0
    
def inputsDataToItemQtyList(inputslist):
    return list(map(lambda x: ItemQty(x["typeID"],x["perhour"]), inputslist))
    

def GetPiData():
    global __PIDATA
    if (__PIDATA == 0):
        __PIDATA = LoadYaml("PI_DATA.yaml")
    return __PIDATA

def GetPiItemName(ID):
    if not ID in GetPiData():
        return "RAW-"+str(ID)
    return GetPiData()[ID]["shortName"]

class ItemQty:
    def __init__(self, ID, QTY):
        self.id = int(ID)
        self.qty = int(QTY)
        self.name = GetPiItemName(ID)
        if ID in GetPiData():
            data = GetPiData()[self.id]
            self.iskValue = math.floor(data["priceEach"]*self.qty)
            self.volume = data["volumeEach"]*self.qty
        else:
            self.iskValue = -1
            self.volume = -1
    def __repr__(self):
        return ("~ "+TCM("{0}",'M')+" * "+TCM("{1}:",'BG')+"{2} "+TCM("{3}",'BG')+"isk~ ").format(self.qty,self.id,self.name,formatPrice(self.iskValue))
    
class MadeItem:   
    def __init__(self, ID, runs):
        self.id = int(ID)
        self.runs = int(runs)
        self.name = GetPiItemName(ID)
        if ID in GetPiData():
            self.totalQtyProduced = GetPiData()[ID]["amountperHour"] * self.runs
            self.inputs = inputsDataToItemQtyList(GetPiData()[ID]["inputs"])
        else:
            self.totalQtyProduced =0
            self.inputs = []
    def __repr__(self):
        return ("//x"+TCM("{0}",'M')+"runs, making {1}, Taking in:{2}\\\\").format(self.runs,ItemQty(self.id,self.totalQtyProduced),self.inputs)
    

    
tax =0.05
ExampleModels = {}
ExampleModels["synthSyn-BB"]={
    "Buys":   [ ItemQty(2312,10), ItemQty(2319,10) ],
    "Sells":  [ ItemQty(2346,3) ],
    "Makes":  [ MadeItem(2346,1) ],
    "Imports":[ ItemQty(2312,10), ItemQty(2319,10) ],
    "Exports":[ ItemQty(2346,3) ],
    "Name":  "synthSyn-BB"
}

def dontsellbuy(in_model):
    sells = pi.Model["Sells"]
    buys =  pi.Model["Buys"]
    sellSet  = set(map(lambda x: x.id, sells))
    buySet = set(map(lambda x: x.id, buys))
    return len(sellSet & buySet) == 0
    
    

def ValidateModel(in_model):
    sells = in_model["Sells"]
    buys =  in_model["Buys"]
    makes =  in_model["Makes"]

    #Don't sell anything you buy
    sellSet = set(map(lambda x: x.id, sells))
    buySet  = set(map(lambda x: x.id, buys))
    if (not len(sellSet & buySet) == 0):
        return false

    #Only sell made items, Sold items must be made
    for sell in sells:
        QtyMade = 0
        for make in makes:
            if (make.id == sell.id) : QtyMade += make.totalQtyProduced
        if(not QtyMade == sell.qty):
            return false
        
    #All buys must be used in a make
    
    #All Buys must be imported,
    
    #All Sells must be exported,
    
    #Makes Inputs and Output values must be a validated schematic
    
    #All Inputs to makes must be imported or made
    
    #Total Runs for all makes must not exceed a glboal total of 30
    
    #Total Makes cannot exceede 30 items.
    
    #Makes with no imports are considered raw Matrial gains, and are allowed
    
    #Cannot be simplified/reduced to a lower scalability
    #Essentialy, only x1 Runs for final ouput Sell item.
    return True
    
    
def calcPowerGridCPU(in_model):
    cpuUsage = [0,0,200,500,1100]
    psuUsage = [0,0,800,700,400]
    power = 0
    cpu = 0
    facs = 0
    for madeItem in in_model["Makes"]:
        itemMadeTechLvl = GetPiData()[madeItem.id]['tech']
        power += psuUsage[itemMadeTechLvl] * madeItem.runs
        cpu += cpuUsage[itemMadeTechLvl] * madeItem.runs
        facs += madeItem.runs
    return {"powergrid":power,"cpu":cpu, "Facilities":facs}
        
    

    
def CalcItemImportTax(in_ItemQty,planetTax=0.05):
    taxableValue = GetPiData()[in_ItemQty.id]["importExportValue"] * in_ItemQty.qty
    #Import taxes are 50% the tax rate, exports are 100%
    return taxableValue * planetTax * 0.5

def CalcItemExportTax(in_ItemQty,planetTax=0.05):
    taxableValue = GetPiData()[in_ItemQty.id]["importExportValue"] * in_ItemQty.qty
    return taxableValue * planetTax

def CalcBuyCostTotal(in_ItemQty):
    return in_ItemQty.iskValue

def CalcSellTaxCostTotal(in_ItemQty,brokerfee=0.024,salesTax=0.0448):
    return (in_ItemQty.iskValue * brokerfee) + (in_ItemQty.iskValue * salesTax)

def CalcModelCosts(in_model):
    totalcosts = 0
    for purchase in in_model["Buys"]:
        totalcosts += purchase.iskValue
    for soldItem in in_model["Sells"]:
        totalcosts += CalcSellTaxCostTotal(soldItem)
    for imported in in_model["Imports"]:
        totalcosts += CalcItemImportTax(imported)
    for exported in in_model["Exports"]:
        totalcosts += CalcItemExportTax(exported)
    return totalcosts
        
def CalcModelCashIn(in_model):
    cash = 0
    for soldItem in in_model["Sells"]:
        cash +=  soldItem.iskValue
    return cash
        
def ScoreModel(in_model):
    return ( CalcModelCashIn(in_model) - CalcModelCosts(in_model) ) * CalcModelTruescale(in_model)

def CalcModelPlanets(in_model):
    grid = calcPowerGridCPU(in_model)
    lvl4baseMinus = {"powergrid":17000-700-700-700, "cpu":21315-3600-500-500}
    return (max(grid["powergrid"] / lvl4baseMinus["powergrid"], grid["cpu"] / lvl4baseMinus["cpu"]))

def CalcMaxModelScalePerPlanet(in_model):
    lvl4baseMinus = {"powergrid":17000-700-700-700, "cpu":21315-3600-500-500}
    grid = calcPowerGridCPU(in_model)
    return max(math.floor(min( lvl4baseMinus["powergrid"] / grid["powergrid"], lvl4baseMinus["cpu"] / grid["cpu"])),1)

def CalcModelTruescale(in_model):
    #truescale = math.floor((1-planets) * (5 * 3 * 2)) 
    truescale = math.floor((5 * 3 * 2) * CalcMaxModelScalePerPlanet(in_model)) 
    #truescale = math.floor((5) * CalcMaxModelScalePerPlanet(in_model)) 
    return truescale

def CalcModelProfitPerPlanet(in_model):
    return (CalcModelCashIn(in_model) - CalcModelCosts(in_model) ) * CalcMaxModelScalePerPlanet(in_model)

def CalcModelImportM3(in_model):
    m3needed = 0 
    for imported in in_model["Imports"]:
        #print(imported,imported.volume)
        m3needed += imported.volume
    return m3needed


def CalcModelRefilTimeOneRun(in_model):
    storageFacilitym3 = 12000
    needm3 = CalcModelImportM3(in_model)
    return storageFacilitym3 /  (needm3 if needm3 > 0 else 1)
 
def CalcModelRefilTimePerPlanet(in_model):
    return CalcModelRefilTimeOneRun(in_model) / CalcMaxModelScalePerPlanet(in_model)
                 
def DetailModel(in_model):
    totalcosts = 0
    
    buys = 0
                       
    print(TCM("---#----#----#---#-\n",'Y')+"Detailing A model Selling: "+str(in_model["Sells"])+"\n")
    print("---- #")                 
    print(" Buying:")
    for purchase in in_model["Buys"]:
        print(" -"+str(purchase))
        buys += purchase.iskValue
    totalcosts += buys
    print(" Buying total:"+TCM(formatPrice(buys),"R"))
    
    print("\n SellTax:")
    SellTaxes = 0
    for soldItem in in_model["Sells"]:
        print(" -"+str(soldItem))
        SellTaxes += CalcSellTaxCostTotal(soldItem)
    totalcosts += SellTaxes
    print(" SellTax total:"+TCM(formatPrice(SellTaxes),"R"))
    
    print("\n ImportFees:")
    ImportFees = 0
    for imported in in_model["Imports"]:
        print(" -"+str(imported))
        ImportFees += CalcItemImportTax(soldItem)
    totalcosts += ImportFees
    print(" ImportFees total:"+TCM(formatPrice(ImportFees),"R"))
    
    print("\n ExportFees:")
    ExportFees = 0
    for exported in in_model["Exports"]:
        print(" -"+str(exported))
        ExportFees += CalcItemExportTax(exported)
    totalcosts += ExportFees
    print(" ExportFees total:"+TCM(formatPrice(ExportFees),"R"))
    
    print("\n MoneyMade:")
    cashIn = 0
    for soldItem in in_model["Sells"]:
        print(" -"+str(soldItem))
        cashIn +=  soldItem.iskValue
    print(" MoneyMade total:"+TCM(formatPrice(cashIn),"BG"))
    
    print("\n---- #")   
    print("Out:")
    print(" Purchases".ljust(16), formatPrice(buys,0))
    print(" ImportFees".ljust(16),formatPrice(ImportFees,0))
    print(" ExportFees".ljust(16),formatPrice(ExportFees,0))
    print(" SellTaxes".ljust(16), formatPrice(SellTaxes,0))
    print("\nTotal Out:".ljust(16), TCM(formatPrice(totalcosts,0),"R"))
    print("\nIn:")
    print("Sells:".ljust(16), TCM(formatPrice(cashIn,0),"BG"))
    print("---- #")    
    print("Profit:".ljust(16),TCM(formatPrice(cashIn-totalcosts,0),"BG"))
    grid = calcPowerGridCPU(in_model)
    planets = CalcModelPlanets(in_model)    
    truescale = CalcModelTruescale(in_model)    
    print("Grid:".ljust(16),grid)
    print("Planets:".ljust(16),planets)    
    print("True Scalability:".ljust(16),truescale)
    print("True scaled Profit:".ljust(16),TCM(formatPrice((cashIn-totalcosts)*truescale,0),"BG"))
    print("Units / hour:".ljust(16),truescale * in_model["Sells"][0].qty)
    print("RefilTime PerPlanet:".ljust(16),math.floor(CalcModelRefilTimePerPlanet(in_model)),"hours")
    print(TCM("---#----#----#---#-\n",'Y'))
    
    
    
def build():
    #pick random item to build
    #walk inputs down and choose to sell or buy
    #add buys and makes to model accordingly
    #work out optimal import export.
    pass
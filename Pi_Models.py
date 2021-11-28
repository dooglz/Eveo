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
    return GetPiData()[ID]["shortName"]

class ItemQty:
    def __init__(self, ID, QTY):
        self.id = int(ID)
        self.qty = int(QTY)
        self.name = GetPiItemName(ID)
    def __repr__(self):
        return ("~"+TCM("{0}",'M')+"*"+TCM("{1}",'G')+"{2} "+TCM("{3}",'BG')+"isk~").format(self.qty,self.id,self.name,formatPrice(math.floor(GetPiData()[self.id]["priceEach"]*self.qty)))
    
class MadeItem:   
    def __init__(self, ID, runs):
        self.id = int(ID)
        self.runs = int(runs)
        self.name = GetPiItemName(ID)
        self.totalQtyProduced = GetPiData()[ID]["amountperHour"] * self.runs
        self.inputs = inputsDataToItemQtyList(GetPiData()[ID]["inputs"])
    def __repr__(self):
        return ("//x"+TCM("{0}",'M')+"runs, making {1}, Taking in:{2}\\\\").format(self.runs,ItemQty(self.id,self.totalQtyProduced),self.inputs)
    

    
tax =0.05

Model={
    "Buys":   [ ItemQty(2312,10), ItemQty(2319,10)  ],
    "Sells":  [ ItemQty(2346,3) ],
    "Makes":  [ MadeItem(2346,1) ],
    "Imports":[ ItemQty(2312,10), ItemQty(2319,10) ],
    "Exports":[ ItemQty(2346,3) ],
    "Scalability": 30
}


def ValidateModel(in_model):
    #Don't sell anything you buy
    
    #Only sell made items, Sold items must be made
    
    #All Buys must be imported,
    
    #All Sells must be exported,
    
    #Makes Inputs and Output values must be a validated schematic
    
    #All Inputs to makes must be imported or made
    
    #Total Runs for all makes must not exceed a glboal total of 30
    
    #Total Makes cannot exceede 30 items.
    
    #Makes with no imports are considered raw Matrial gains, and are allowed
    
    #Cannot be simplified/reduced to a lower scalability
    #Essentialy, only x1 Runs for final ouput Sell item.
    
    return
    
    
def calcImportTax(in_ItemID,in_Qty):
    return 0

def calcExportTax(in_ItemID,in_Qty):
    return 0

def CalcBuyCostTotal(in_ItemID,in_Qty):
    return 0

def CalcSellTaxCostTotal(in_ItemID,in_Qty):
    taxes = 0
    return taxes

def CalcModelCosts(in_model):
    costs = 0
    for purchase in in_model["Buys"]:
        costs += CalcBuyCostTotal(in_ItemID,in_Qty)
    for soldItem in in_model["Sells"]:
        costs += CalcSellTaxCostTotal(in_ItemID,in_Qty)
    for imported in in_model["Imports"]:
        costs += calcImportTax(in_ItemID,in_Qty)
    for exported in in_model["Exports"]:
        costs += calcExportTax(in_ItemID,in_Qty)
        
def CalcModelCashIn(in_model):
    cash = 0
    for soldItem in in_model["Sells"]:
        cash += getPrice(in_ItemID,in_Qty)
    return cash
        
def ScoreModel(in_model):
    return ( CalcModelCashIn(in_model) - CalcModelCosts(in_model) ) * in_model["Scalability"]



def build():
    #pick random item to build
    #walk inputs down and choose to sell or buy
    #add buys and makes to model accordingly
    #work out optimal import export.
    pass
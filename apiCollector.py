import requests # API access.
import datetime # Recording how long pulling data takes
import json # Storing data
import base64 # Item Data
import nbt # Item Data
import io # Streaming base64
import math  # Std Deviation and statistics


def updateListings(parent):  # Takes the parent thread manager object so the thread can cancel itself when finished.
    auctionReq = requests.get("https://api.hypixel.net/skyblock/auctions")
    if (auctionReq.status_code != 200): return  # Cancels if error with auction.

    with open("whitelist.json") as j:
        whitelisted = json.load(j)["items"]
    prices = {}
    for id in whitelisted:
        prices[id] = {"lowest" : 2200000000, "second_lowest" : 2220000000, "lowest_id" : "none", "bins": []} # Placeholder values for lowest bin, will always be higher than any bin, higher than 32 signed int limit.

    aucData = auctionReq.json()
    pages = aucData["totalPages"]
    auctions = aucData["totalAuctions"]

    dataStore = [ None ] * pages

    print(f"Total Pages: {pages}, Total Auctions: {auctions}")

    bins = 0
    missed = 0 # Amount of pages missed by the api.
    
    start = datetime.datetime.now()
    for page in range(pages):
        print(f"Loading page {page} ({int((page/pages)*100)}%))")
        auctionReq = requests.get("https://api.hypixel.net/skyblock/auctions", params={"page": page})
        if (auctionReq.status_code != 200): 
            print(f"Page {page} did not load")
            missed += 1
        else:
            dataStore[page] = auctionReq.json()["auctions"]

    # Above is loading the data in from the API, below is processing and filtering the data.
    
    for x in range(len(dataStore)- missed):
        for auc in dataStore[x]:
            if "bin" in auc:
                bins +=1    
                nbtfile = nbt.nbt.NBTFile(fileobj=io.BytesIO(base64.b64decode(auc["item_bytes"])))  # Ugly line of code
                tag = nbtfile[0][0]["tag"]["ExtraAttributes"]["id"]
                if str(tag) in whitelisted:
                    startBid = auc["starting_bid"]
                    if "enchantments" in nbtfile[0][0]["tag"]["ExtraAttributes"]:
                        enchantNBT = nbtfile[0][0]["tag"]["ExtraAttributes"]["enchantments"]

                    itemRef = prices[str(tag)]

                    itemRef["bins"].append(startBid)
                    if startBid < itemRef["second_lowest"]:
                        if startBid < itemRef["lowest"]:

                            itemRef["second_lowest"] = itemRef["lowest"]
                            itemRef["lowest"] = startBid
                            itemRef["lowest_id"] = auc["uuid"]
                        else:
                            if not(auc["uuid"] == itemRef["lowest_id"]): # Basically in a co-op, there was dupes i think (may be wrong, seemed like it from testing)
                                itemRef["second_lowest"] = startBid

    end = datetime.datetime.now()

    print(f"It took {(end-start).total_seconds()} seconds")
    print(f"There are {bins} BIN auctions.\n")

    for item in prices:

        if len(prices[item]["bins"]):
            average = sum(prices[item]["bins"]) / len(prices[item]["bins"])
        else:
            average = 0

        devi = stdDev(prices[item]["bins"], average)

        total = 0
        missed = 0
        for price in prices[item]["bins"]:  # If prices are 1 Std Deviation above, dont count in the average.
            if (prices[item]["lowest"]+devi) < price:
                missed += 1
            else:
                total += price
        if (missed != len(prices[item]["bins"])):
            trueAverage = total/(len(prices[item]["bins"]) - missed)
        else:
            trueAverage = 0

        margin = prices[item]["second_lowest"] - prices[item]["lowest"]
        prices[item]["average"] = int(trueAverage)  # Cast to int to clean up the number, was like 10 decimal places
        prices[item]["profit_margin"] = margin
        pop = prices[item].pop("bins", "no bins?")
    
    with open("prices.json", "w+") as r:
        data = json.dumps(prices, indent=4)
        r.write(data)

    print("Auction house has been scanned!")
    parent.removeThread("api")


def stdDev(set, mean):  # Standard deviation, rules out extreme cases, e.g. some boots for 1b, etc.
    working = 0
    for price in set:
        working += ((price - mean) ** 2)
    
    if len(set) != 0:
        final = math.sqrt(working/len(set))
        return final
    else:
        return 0



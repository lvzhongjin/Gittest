
import importlib
import pip

def import_or_install(package):
    try:
        module = importlib.import_module(package)
    except ImportError:
        pip.main(['install', package])
        module = importlib.import_module(package)  # Import the module after installation
    globals()[package] = module  # Make module accessible by the package name
import_or_install("requests")
import_or_install("os")
import_or_install("socket")
import pandas as pd
import random
import time

def createIncreasesCsv(ind, data, ein, url, taxPeriodEndDt):
    """
    Get all the description values and amount values present in the increasing schedule tag and updating in to data frame
    """
    increases = pd.DataFrame()
    values = {"EIN": ein, "xml_url": url, "taxPeriodEndDt": taxPeriodEndDt}
    while ind < len(data) and data[ind].strip() != "</OtherIncreasesSchedule>":

        if data[ind].find("Desc") != -1 or data[ind].find("Description") != -1:
            values['Description'] = data[ind].split('>')[1].split('<')[0].lower()
        if data[ind].find("Amt") != -1 or data[ind].find("Amount") != -1:
            values['Amount'] = data[ind].split('>')[1].split('<')[0]
            values['scheduleType'] = "Increase"
            df = pd.DataFrame.from_dict(values, orient='index')
            df = df.T
            increases = pd.concat([increases, df], join="outer")
            values = {"EIN": ein, "xml_url": url, "taxPeriodEndDt": taxPeriodEndDt}
        ind += 1

    return increases


def createDecreasesCsv(ind, data, ein, url, taxPeriodEndDt):
    """
    Get all the description values and amount values present in the decreasing schedule tag and updating in to data frame
    """
    decreases = pd.DataFrame()
    values = {"EIN": ein, "xml_url": url, "taxPeriodEndDt": taxPeriodEndDt}
    while data[ind].strip() != "</OtherDecreasesSchedule>" and ind < len(data):
        if data[ind].find("Desc") != -1 or data[ind].find("Description") != -1:
            values['Description'] = data[ind].split('>')[1].split('<')[0].lower()
        if data[ind].find("Amt") != -1 or data[ind].find("Amount") != -1:
            values['Amount'] = data[ind].split('>')[1].split('<')[0]
            values['scheduleType'] = "Decrease"
            df = pd.DataFrame.from_dict(values, orient='index')
            df = df.T
            decreases = pd.concat([decreases, df], join="outer")
            values = {"EIN": ein, "xml_url": url, "taxPeriodEndDt": taxPeriodEndDt}
        ind += 1
    return decreases


def financials_parse(url,financials_df, ein, schedules):
    x = requests.get(url)
    data = x.text
    dict = {}
    dict['EIN'] = ein
    dict['xml_url'] = url
    Analysis = False
    data = data.split('\n')
    otherIncreasesSchedule = False
    otherDecreasesSchedule = False
    otherIncreasesScheduleTag = ''
    otherDecreasesScheduleTag = ''

    for ind,i in enumerate(data):
        if i.find('ReturnType') != -1: # 990PF is what we want; ignore 990
            dict['ReturnType'] = i.split('>')[1].split('<')[0]
        if i.find('TaxPeriodEndDt') != -1 or i.find('TaxPeriodEndDate') != -1:
            dict['TaxPeriodEndDt'] = i.split('>')[1].split('<')[0]  #This splits in every condition, will get the data between >outputtext<
        if i.find('TaxYr') != -1 or i.find('TaxYear') != -1:
            dict['TaxYr'] = i.split('>')[1].split('<')[0]
        if i.find('TotalAssetsBOYAmt') != -1 or i.find('TotalAssetsBOY') != -1:
            dict['a040'] = i.split('>')[1].split('<')[0]
        if i.find('TotalAssetsEOYAmt') != -1 or (i.find('TotalAssetsEOY') != -1 and i.find('FMV') == -1):    #Pre-2013 using different tags
            dict['a220'] = i.split('>')[1].split('<')[0]
        if i.find('TotalAssetsEOYFMVAmt') != -1 or i.find('TotalAssetsEOYFMV') != -1 or i.find('TotalAssetsEOY') != -1:
            dict['a400'] = i.split('>')[1].split('<')[0]
        if i.find('ContriRcvdRevAndExpnssAmt') != -1 or i.find('ContriReceivedRevAndExpnss') != -1:
            dict['r010'] = i.split('>')[1].split('<')[0]  
        if i.find('ContriPaidRevAndExpnssAmt') != -1 or i.find('ContriGiftsPaidRevAndExpnss') != -1:
            dict['x140'] = i.split('>')[1].split('<')[0] 
        if i.find('TotalExpensesRevAndExpnssAmt') != -1 or i.find('TotalExpensesRevAndExpnss') != -1:
            dict['x150'] = i.split('>')[1].split('<')[0] 
        if i.find('TotalExpensesDsbrsChrtblAmt') != -1 or i.find('TotalExpensesDsbrsChrtblPrps') != -1:
            dict['x320'] = i.split('>')[1].split('<')[0]  
        if i.find('ContriPaidDsbrsChrtblAmt') != -1 or (i.find('ContriGiftsPaidDsbrsChrtblPrps') != -1):
            dict['x310'] = i.split('>')[1].split('<')[0]
        if i.find('TotalLiabilitiesBOYAmt') != -1 or i.find('TotalLiabilitiesBOY') != -1: 
            dict['l010'] = i.split('>')[1].split('<')[0]
        if i.find('TotalLiabilitiesEOYAmt') != -1 or i.find('TotalLiabilitiesEOY') != -1: 
            dict['l020'] = i.split('>')[1].split('<')[0]
        if i.find('TotNetAstOrFundBalancesEOYAmt') != -1 or i.find('TotalNetAssetsEOY') != -1 or i.find('TotalNetAssetsFundBalances') != -1: #TotalNetAssetsFundBalances
            dict['n020'] = i.split('>')[1].split('<')[0]
        if i.find('QualifyingDistributionsAmt') != -1 or i.find('QualifyingDistributions') != -1:
            dict['d060'] = i.split('>')[1].split('<')[0] 
        if i.find('NetVlNoncharitableAssetsAmt') != -1 or i.find('NetNoncharitableAssets') != -1:
            dict['m010'] = i.split('>')[1].split('<')[0]
        if i.find('DistributableAsAdjustedAmt') != -1 or i.find('DistributableAmountAsAdjusted') != -1:
            dict['m080'] = i.split('>')[1].split('<')[0]
        if i.find('TaxBasedOnInvestmentIncomeAmt') != -1 or i.find('TaxBasedOnInvestmentIncome') != -1:
            dict['t060'] = i.split('>')[1].split('<')[0]



        if i.find('PrivateOperatingFoundationInd') != -1 or i.find('PrivateOperatingFoundation') != -1:  
            try:
                tag = i.split('</')[1].split('>')[0] # Checks for end tag if present we are storing tag name for exact explicit checking
            except:
                tag = ""
            if tag == 'PrivateOperatingFoundationInd' or tag == 'PrivateOperatingFoundation':
                dict['q030'] = i.split('>')[1].split('<')[0]
                if dict['q030'] == '0':     # If the value is '0' change false
                    dict['q030'] = 'false'
                if dict['q030'] == '1':     # If the value is '1' change true
                    dict['q030'] = 'true'

        if i.find('OtherIncreasesAmt') != -1 or i.find('OtherIncreases') != -1:
            try:
               tag = i.split('</')[1].split('>')[0]     # Checks for end tag if present we are storing tag name for exact explicit checking
            except:
               tag = ""
            if tag == 'OtherIncreasesAmt' or tag == 'OtherIncreases':   # If the tag is exact match we store the value
                value = i.split('>')[1].split('<')[0]
                if value.isdigit():     # The value we are expecting is numeric we are storing value if it is digit.
                    dict['b010'] = value

                try:
                    if "referenceDocumentId=" in i.split('<')[1].split('>')[0].split()[1]:
                        otherIncreasesSchedule = True
                        # Creating the schedule tag for adding data into dataframe
                        otherIncreasesScheduleTag = "OtherIncreasesSchedule documentId=" + '"' + i.split('<')[1].split('>')[0].split()[1].split('"')[1] + '"'

                        continue
                except:
                    pass
                
        if i.find('OtherDecreasesAmt') != -1 or i.find('OtherDecreases') != -1:
            try:
                tag = i.split('</')[1].split('>')[0] #end tag
            except:
                tag = ""
            if tag == 'OtherDecreasesAmt' or tag == 'OtherDecreases':
                value = i.split('>')[1].split('<')[0] #whatever between the tag
                if value.isdigit(): #
                    dict['b020'] = value
                try:
                    if "referenceDocumentId=" in i.split('<')[1].split('>')[0].split()[1]:
                        # Creating the schedule tag for adding data into dataframe
                        otherDecreasesScheduleTag = "OtherDecreasesSchedule documentId=" + '"' + i.split('<')[1].split('>')[0].split()[1].split('"')[1] + '"'
                        otherDecreasesSchedule = True
                        continue
                except:
                    pass

        if otherIncreasesSchedule and i.find(otherIncreasesScheduleTag) != -1:
            csv = createIncreasesCsv(ind, data, ein, url, dict['TaxPeriodEndDt'])
            schedules = pd.concat([schedules, csv], join="outer")
            otherIncreasesSchedule = False   # for not to call the function again

        if otherDecreasesSchedule and i.find(otherDecreasesScheduleTag) != -1:
            csv = createDecreasesCsv(ind, data, ein, url, dict['TaxPeriodEndDt'])
            schedules = pd.concat([schedules, csv], join="outer")
            otherDecreasesSchedule = False   # for not to call the function again


    df = pd.DataFrame.from_dict(dict, orient='index')
    df = df.T

    financials_df = pd.concat([financials_df, df], join="outer")
    return financials_df, schedules
 



if __name__ == "__main__":
    if socket.gethostname() == 'GeneLuDellXPS':
        #os.chdir(r'C:\Users\zlu15\Dropbox\P15_PrivateFoundation\Charan\Task2')
        os.chdir(r'C:\Users\zlu15\Dropbox\P15_PrivateFoundation\ScrapingCode\Scraping_XML')
    else:
        os.chdir(r'/scratch/zlu15/XML')

    schedules = pd.DataFrame()  # data frame to record schedules

    # getting the parent directory path to create schedules folder
    parent_directory_path = os.path.dirname(os.getcwd())
    folderPath = os.path.join(parent_directory_path, "Schedules")
    # Check if the Schedules directory exists
    if not os.path.exists(folderPath):
        # Create the  Schedules directory
        os.makedirs(folderPath)

    eins = pd.read_stata("ein_all_xml_do1.dta")  # Input .dta file
    financials_df = pd.DataFrame()
    for i in range(len(eins['xml_url'])):
        print(i)
        start_time = time.time()
        financials_df, schedules = financials_parse(eins['xml_url'][i], financials_df, eins['EIN'][i], schedules)
        end_time = time.time()
        elapsed_time = end_time - start_time
        if elapsed_time < 1.1:
            sleep_time = 1.2 - elapsed_time
            time.sleep(sleep_time)

        if i % 100 == 0:
            financials_df.to_stata('financials_df1.dta')
            schedules.to_stata('schedules1.dta')

    schedules.to_csv(f'{folderPath}/schedules1.csv', index=False)
    financials_df.to_csv('output_new1.csv', index=False)

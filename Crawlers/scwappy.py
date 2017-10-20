import selenium
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
import warnings
import time

basePaths = {'Laptops': 'https://www.ebay.com/b/Laptops-Netbooks/175672/bn_1648276?_pgn=',
             'Tablets': 'https://www.ebay.com/b/Tablets-eBook-Readers/171485/bn_320042?_pgn='
            
            }

class eBayScwaper():
    
    """
    
    Parameters
    ----------
    
    base_path: url of eBay category
    debug: True or False, if True adds the link of the items crawled
    verbose: True or False
    driver: 'Chrome' or 'Firefox' or 'PhantomJS'
    
    """
    
    def __init__(self, base_path, debug = True, verbose = False, driver = 'Chrome'):
        self.base_path = base_path
        self.debug = debug
        self.verbose = verbose
        self.driver = self._set_driver(driver)
        self.scraped_data = pd.DataFrame()
        
    def _set_driver(self, driver_string):
        """Set the selenium driver"""
        if(driver_string == 'Chrome'):
            return webdriver.Chrome()
        elif(driver_string == 'PhantomJS'):
            return webdriver.PhantomJS()
        elif(driver_string == 'Firefox'):
            return webdriver.Firefox()
        else:
            warnings.warn('Option for driver not found, using Chrome instead')
            return webdriver.Chrome()
        
    def _reset_data(self):
        """Resets the scraped data"""
        self.scraped_data = pd.DataFrame()
            
        
    def scrape(self,page_min = 1, page_max = 2, parser = 'lxml', reset_data = False):
        if self.verbose:
            start_time = time.time()
        if reset_data:
            self._reset_data()
        item_number = 0
        for page_number in range(page_min, page_max):
            self.driver.get(self.base_path + str(page_number) + '&rt=nc')
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, 'lxml')
            
            # get a list of links titles and prices from the product overview page 
            links = soup.find_all(attrs={'class': 's-item__link'})
            titles = soup.find_all(attrs={'class': 's-item__title'})
            prices = soup.find_all(attrs={'class': 's-item__price'})
            
            for counter in range(len(links)):
                if self.debug:
                    self.scraped_data.loc[item_number, 'ItemLink'] = links[counter]['href']
                self.scraped_data.loc[item_number, 'Price'] = prices[counter].getText()
                self.scraped_data.loc[item_number, 'Name'] = titles[counter].getText()
                
                
                self.driver.get(links[counter]['href']) # go to page
                item_source = self.driver.page_source
                item_soup = BeautifulSoup(item_source, 'lxml')
                try:
                    self.scraped_data.loc[item_number, 'Image'] = item_soup.find_all(attrs={'id': 'icImg'})[0]['src']
                except:
                    warnings.warn('Image not Found')
                desc_soup = item_soup.find_all(attrs = {'class': 'itemAttr'}) #Soup with the specs table
                try:
                    rows = desc_soup[0].find_all(name = 'tr') # Get the rows

                    isSellerDesc = len(item_soup.find_all(attrs = {'class': 'itmSellerDesc'}))+\
                    len(item_soup.find_all(attrs = {'id':'itmSellerDesc'}))> 0

                    for row_count, row in enumerate(rows):

                        #If seller description exists 
                        if isSellerDesc and row_count == 0:

                            # Row 0 in seller description contains the condition of item along with an annoying tooltip
                            label = row.find_all(name = 'th')[0].getText().replace(':', '').strip()
                            value = row.find_all(name = 'td')[0].getText().split('\n')[0]
                            self.scraped_data.loc[item_number, label] = value

                        elif not isSellerDesc and row_count==0:

                            # Condition is always in the first row and with it brings some annoying tooltips if code breaks
                            #it's probably in one of these
                            labels = row.find_all(attrs = {'class': 'attrLabels'}) #gets all the labels
                            values = row.find_all(name = ['td'], attrs = {'width': True}) # gets all the values
                            label = labels[0].getText().replace(':', '').strip() # first label has condition
                            value = row.find_all(attrs={'aria-live': 'polite'})[0].getText().split(':')[0].strip()
                            self.scraped_data.loc[item_number, label] = value

                            # values and labels from the ends of the list
                            for label_number in range(len(labels)-1, 0, -1):
                                label = labels[label_number].getText().replace(':', '').strip()
                                value = values[len(values)-len(labels)+label_number].getText().strip()
                                self.scraped_data.loc[item_number, label] = value

                        # Second Row has seller description       
                        elif isSellerDesc and row_count==1:
                            label = row.find_all(name = 'th')[0].getText().replace(':', '').strip()
                            value = row.find_all(name = ['span', 'h2'])[0].getText()
                            self.scraped_data.loc[item_number, label] = value
                        else: 
                            labels = row.find_all(attrs = {'class': 'attrLabels'})
                            values = row.find_all(name = ['td'], attrs = {'width': True})
                            for label_number in range(len(labels)):
                                label = labels[label_number].getText().replace(':', '').strip()
                                value = values[label_number].getText().strip()
                                self.scraped_data.loc[item_number, label] = value
                    item_number+=1
                    if self.verbose:
                        print('Items Completed: {}, Time Elapsed: {}'.format(item_number, start_time-time.time()))
                except:
                    warnings.warn('No Table Found')
#! /usr/bin/python3
import requests
from bs4 import BeautifulSoup as bs 
import csv

import concurrent.futures
import nltk
from nltk.corpus import stopwords
from selenium import webdriver
from collections import OrderedDict
from random import randint
import random
import requests
import pandas as pd
import time
import os
from flask import Flask, render_template,  session, redirect, request
from flask_cors import CORS,cross_origin
import matplotlib.pyplot as plt
from wordcloud import WordCloud, STOPWORDS, ImageColorGenerator
from PIL import Image
import numpy as np

import string
from lxml.html import fromstring
import traceback

from http_request_randomizer.requests.proxy.requestProxy import RequestProxy


import copy
from defaultlist import defaultlist

s=set(stopwords.words('english'))

# define global paths for Image and csv folders
IMG_FOLDER = os.path.join('static', 'images')
CSV_FOLDER = os.path.join('static', 'CSVs')
BKG_FOLDER = os.path.join('static', 'background')

#FLASK specific - maybe this is why he is using CORS. So that the origin can be both the web and the folder name.
app = Flask(__name__)
# config environment variables
app.config['IMG_FOLDER'] = IMG_FOLDER
app.config['CSV_FOLDER'] = CSV_FOLDER
app.config['BKG_FOLDER'] = BKG_FOLDER


def create_url(search_term,template='amazon', page=1):
    """Create a url based on search terms. """
    if template=='amazon':
        template = "https://www.amazon.in/s?k={}&ref=nb_sb_noss_2"
    elif template=='flipkart':
        template = "https://www.flipkart.com/search?q={}&otracker=search&otracker1=search&marketplace=FLIPKART&as-show=on&as=off"

    if " " in search_term.strip():
        search_term = search_term.strip().replace(" ", "+")
    else:
        search_term = search_term.strip()

    search_term = search_term.replace(" ","+")

    # Inserting query    
    search_url = template.format(search_term)

    # Add provision to travel through different pages
    search_url += '&page={}' 

    return search_url

def  get_headers_and_proxies():
    """Fetches proxies and randomly selects one of the headers."""

    headers_list = [ 
            {
                'dnt': '1',
                'upgrade-insecure-requests': '1',
                'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.75 Safari/537.36',
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                'sec-fetch-site': 'cross-site',
                'sec-fetch-mode': 'navigate',
                'sec-fetch-user': '?1',
                'sec-fetch-dest': 'document',
                'referer': 'https://www.google.com/',
                'accept-language': 'en-IN,en;q=0.9'
            },
    
            {
                'Connection': 'keep-alive',
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.75 Safari/537.36',
                'DNT': '1',
                'Content-Type': 'text/plain;charset=UTF-8',
                'Accept': '*/*',
                'Origin': 'https://www.amazon.in',
                'Referer': 'https://www.google.com/',
                'Accept-Language': 'en-IN,en;q=0.9,en-GB;q=0.8,en-US;q=0.7,bn;q=0.6',
            },
        
        # Firefox 77 Mac
            {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:77.0) Gecko/20100101 Firefox/77.0",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Referer": "https://www.google.com/",
                "DNT": "1",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1"
            },
            # Firefox 77 Windows
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:77.0) Gecko/20100101 Firefox/77.0",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate, br",
                "Referer": "https://www.google.com/",
                "DNT": "1",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1"
            },
            # Chrome 83 Mac
            {
                "Connection": "keep-alive",
                "DNT": "1",
                "Upgrade-Insecure-Requests": "1",
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
                "Sec-Fetch-Site": "none",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Dest": "document",
                "Referer": "https://www.google.com/",
                "Accept-Encoding": "gzip, deflate, br",
                "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8"
            },
            # Chrome 83 Windows 
            {
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
                "Sec-Fetch-Site": "same-origin",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-User": "?1",
                "Sec-Fetch-Dest": "document",
                "Referer": "https://www.google.com/",
                "Accept-Encoding": "gzip, deflate, br",
                "Accept-Language": "en-US,en;q=0.9"
            }]
    

    ordered_headers_list = []
    #randomly find out headers
    for headers in headers_list:
        h = OrderedDict()
        for header,value in headers.items():
            h[header]=value
        ordered_headers_list.append(h)

    for i in range(1,6):
        #Pick a random browser headers
        headers = random.choice(headers_list)

    req_proxy = RequestProxy() #you may get different number of proxy when  you run this at each time
    proxies = req_proxy.get_proxy_list() #this will create proxy list
    
    #randomly find out proxies
    # url = 'https://free-proxy-list.net/'
    # response = requests.get(url)
    # parser = fromstring(response.text)
    # proxies = []
    # for i in parser.xpath('//tbody/tr')[:14]:
    #     if i.xpath('.//td[7][contains(text(),"yes")]'):
    #         #Grabbing IP and corresponding PORT
    #         proxy = ":".join([i.xpath('.//td[1]/text()')[0], i.xpath('.//td[2]/text()')[0]])
    #         proxies.append(proxy)

    return (headers, proxies)


# def extract_flipkart_search_results(driver,search_term,headers,proxy):
def extract_flipkart_search_results(search_term,headers,proxy):
    """Scrape and return relevant data from flipkart."""

    data = {}
    product = defaultlist(lambda: 'empty')
    price = defaultlist(lambda: 'empty')
    rating = defaultlist(lambda: 'empty')
    review_count = defaultlist(lambda: 'empty')
    product_page = defaultlist(lambda: 'empty')
    comments = defaultlist(lambda: 'empty')

    base_url = "https://www.flipkart.com"
    #creating the query term & fetching the requested page
    url = create_url(search_term, template='flipkart')
    
    for page in range(0,2):
        url = url.format(page)
        
        try:
            page = requests.Session().get(url, headers=headers, proxies={"http": proxy, "https": proxy})   
            # page = driver.get(url, headers=headers, proxies={"http": proxy, "https": proxy})
        except:
            page = requests.Session().get(url, headers=headers)
        
        # page = driver.get(url)

        page_source = page.text
        # page_source = driver.page_source
        #create soup object
        soup = bs(page_source,'html.parser')
        
        # prod_urls = soup.find_all('a',{'rel':'noopener noreferrer'})
        prod_urls = defaultlist(lambda:"empty")
        prod_urls.extend(soup.find_all('a',{'rel':'noopener noreferrer'}))
        
        for i in range(10):
            #Controll craw rate
            time.sleep(randint(1,4))
            try:
                if soup.find('div',{'class':'_3BTv9X'}).img['alt'] != []:
                    product.append(soup.find_all('div',{'class':'_3BTv9X'})[i].img['alt']+'(Flipkart)')

                elif soup.find('a',{'class':'_2cLu-l'})['title'] != []:
                    product.append(soup.find_all('div',{'class':'_2cLu-l'})[i]['title']+'(Flipkart)')

                elif soup.find('a',{'class':'_3wU53n'}).text != []:
                    product.append(soup.find_all('div',{'class':'_3wU53n'})[i].text+'(Flipkart)')
            except:
                product.append('')


            #Return the price of an element
            try:
                price.append(soup.find_all('div','_1vC4OE')[i].text)
            except:
                price.append("")

            #Return rating of an element
            try:
                rating.append(soup.find_all('div','hGSR34')[i].text)
            except:
                rating.append("Not rated")

            #Return number of people who rated and reviewed the product
            try:
#                 if soup.find('span',{'class':'_1SMN2T'}) != None:
#                     review_count.append(soup.find_all('span',{'class':'_1SMN2T'})[i].text.split("&")[0])
#                 elif soup.find('span',{'class':'_38sUEc'}).text != None:
                review_count.append(soup.find_all('span',{'class':'_38sUEc'})[i].span.contents[2].text.replace('\xa0',''))
            except:
                review_count.append("No reviews")

            #Return the full product  URL
            prod_url = prod_urls[i]
            
            if prod_url != 'empty':
                prod_page = base_url+str(prod_url['href'])                
                product_page.append(prod_page)
                reviews_url = prod_page.replace('/p/','/product-reviews/') 
                reviews_page = requests.get(reviews_url, headers=headers)
                page_source = reviews_page.text
                soup_rev = bs(page_source,'html.parser')
                #Find all reviews
                rev_results = soup_rev.find_all('div','qwjRop')
                #Extract all the 
                comments.append([i.text.strip().replace('READ MORE','') if (i.text.strip()!='') else
                                 i.text.strip().replace('READ MORE','') if 'READ MORE' in i else i.text 
                                 for i in rev_results])
                
            else:
                product_page.append("No URL")
                comments.append("No comments")


    data['Product'] = product
    data['Price'] = price
    data['Rating'] = rating
    data['Review count'] = review_count
    data['Product page'] = product_page
    data['Comments'] = comments
    
    return data



def execute_scraper_amazon_requests(search_term,headers,proxy):
# def execute_scraper_amazon_requests(driver,search_term,headers,proxy):
    """Run the scraper and display the values as required from amazon. """
    data = {}
    product = defaultlist(lambda: 'empty')
    price = defaultlist(lambda: 'empty')
    rating = defaultlist(lambda: 'empty')
    review_count = defaultlist(lambda: 'empty')
    product_page = defaultlist(lambda: 'empty')
    comments = defaultlist(lambda: 'empty')
      

    base_url = "https://www.amazon.in"
    
    #creating the query term & fetching the requested page
    url = create_url(search_term, 'amazon')
    for page in range(0,2):

        url = url.format(page)
        
        
        try:
            page = requests.Session().get(url, headers=headers, proxies={"http": proxy, "https": proxy})      
            # page = driver.get(url, headers=headers, proxies={"http": proxy, "https": proxy})      
        except:
            page = requests.Session().get(url, headers=headers)
            # page = driver.get(url, headers=headers)#, proxies={"http": proxy, "https": proxy})
        # page =driver.get(url)
        page_source = page.text
        # page_source = driver.page_source
        soup = bs(page_source,'html.parser')
#         soup = create_soup_object(url)
#         results_a = remove_ads(soup)
    
        results = soup.find_all('div',{'data-component-type':'s-search-result'})
        ads = soup.find_all('div','AdHolder')
        #removing ads
        for i in results:
            if ads != []:
                if i in ads:
                    results.remove(i)
            else:
                break

        time.sleep(randint(1,4))

        for item in results[0:10]:
            tag = item.h2.a
            #Item name
            # if all(i in tag.text.split(' ') for i in search_string.replace("+"," ").split(' ')):
            #     product.append(tag.text.strip()+' (Amazon)')
            # else:
            #     pass
            
            product.append(tag.text.strip()+' (Amazon)')
            
            product_url = base_url+tag.get('href')
            
            #Item URL
            product_page.append(product_url)

            try:
                price_parent = item.find('span','a-price')
                #Item price
                price.append(price_parent.find('span','a-offscreen').text)
            except:
                price.append("No price")

            try:    
                #Item rating
                rating.append(item.i.text)
            except:
                rating.append("No ratings")
            

            try:    
                #Item review countif record:
                review_count.append(item.find("span",{"class":"a-size-base", "dir":"auto"}).text)
            except:
                review_count.append("No reviews")

            reviews_link = product_url.replace('dp','product-reviews').replace('?dchild=1','/reviewerType=all_reviews')

            page_rev = requests.get(reviews_link, headers=headers)
            page_rev_source = page_rev.text
            soup_rev = bs(page_rev_source,'html.parser')
            
            # try:
            comments.append([i.text.strip() if i.text.strip()!='' else "No user comments yet" for i in soup_rev.find_all('span',{'data-hook':'review-body'})])
            # except:
            #     comments.append("No user comments yet")
    
    data['Product'] = product
    data['Price'] = price
    data['Rating'] = rating
    data['Review count'] = review_count
    data['Product page'] = product_page
    data['Comments'] = comments

    return data

def save_as_dataframe(dataframe, fileName):
    """This function saves the scraped data into a file which could be downloaded later."""

    # save the CSV file to CSVs folder
    csv_path = os.path.join(app.config['CSV_FOLDER'],fileName)
    fileExtension = '.csv'
    final_path = f"{csv_path}{fileExtension}"
    # clean previous files -
    
    # save new csv to the csv folder
    dataframe.to_csv(final_path,index=False)
    print("File has been successfully saved!")

    return final_path

#Create a wordcloud and save the same in the IMG_FOLDER. Clear the previous searched wordcloud image from the folder.
def save_wordcloud_image(file, img_filename,search_string):
    """Save it as a wordcloud."""

    # extract all the comments
    txt = " ".join(review.lower() for review in file)
    # txt = dataframe["Comments"].values
    # print(img_filename)
    # if len(file)>1:
    try:
        # generate the wordcloud
        mask = np.array(Image.open(os.path.join(app.config["BKG_FOLDER"],"cloud.png")))

        STOPWORDS.update(s)
        STOPWORDS.update([*string.punctuation])
        STOPWORDS.update(['google','apple','amazon','flipkart','oppo','vivo','oneplus','samsung','lg','screen','price','redmi'])
        STOPWORDS.update(['one','plus','shoes','pants','jeans','sneakers','nike','back','nokia','oneplus','phone','mobile','camera','glass','battery'])
        STOPWORDS.update(['processor','ram','resolution','phones','case','smartphone','device','product'])
        STOPWORDS.update([i.lower() for i in search_string.split("+")])
        STOPWORDS.update([j.lower() for j in img_filename.split(" ")])
        
        print(STOPWORDS)
        wc = WordCloud(width=800, height=400, background_color='white',mask=mask,stopwords=STOPWORDS).generate(str(txt))
        plt.figure(figsize=(20,10), facecolor='k', edgecolor='k')
        plt.imshow(wc, interpolation='bilinear') 
        plt.axis('off')
        plt.tight_layout()

        image_path = os.path.join(app.config['IMG_FOLDER'], img_filename + '.png')
    
        plt.savefig(image_path)
        plt.close()
        print("saved wc")
    # else:
    #     pass
    except:
        pass



#Clear the image and the csv files from their respective directories.

def clear_cache():
    # only proceed if directory is not empty
    directory=[app.config['IMG_FOLDER'],app.config['CSV_FOLDER']]
    for i in directory:
        if os.listdir(i) != []:
            # iterate over the files and remove each file
            files = os.listdir(i)
            for fileName in files:
                print(fileName)
                os.remove(os.path.join(i,fileName))
        print("cleaned!")


@app.route('/',methods=['GET'])  
@cross_origin()
def homePage():
    return render_template("index.html")


# route to display the review page

@app.route('/')
@app.route('/review', methods=("POST", "GET"))
@cross_origin()
def index():
    if request.method == 'POST':
        # try:

        # driver = webdriver.Chrome()

        # driver.set_window_position(-10000,0)
        
            
        if (os.listdir(app.config['IMG_FOLDER']) != []) or (os.listdir(app.config['CSV_FOLDER']) != []):
            clear_cache()
        else:
            pass

        search_string = request.form.get('content')

        if " " in search_string.strip():
            search_string = search_string.strip().replace(" ", "+")
        else:
            search_string = search_string.strip()
        
        print('processing...')
        
        start = time.perf_counter()

        print('check1')
        #Fetch headers and proxies
        headers, proxies = get_headers_and_proxies()

        try:
            proxy = proxies[randint(1,len(proxies))].get_address()
        except:
            proxy = proxies[-1].get_address()

        print('check2')

        with concurrent.futures.ThreadPoolExecutor() as executor:
            flipkart_exec = executor.submit(extract_flipkart_search_results,search_string,headers,proxy)
            flipkart_data = flipkart_exec.result()
            amazon_exec = executor.submit(execute_scraper_amazon_requests,search_string,headers,proxy)
            amazon_data = amazon_exec.result()
            # for i,j in zip(flipkart_data['Comments'],flipkart_data['Product']):
            #     executor.submit(save_wordcloud_image(i,j,search_string))
            # for i,j in zip(amazon_data['Comments'],amazon_data['Product']):
            #     executor.submit(save_wordcloud_image(i, j,search_string))
        
        #Scrape results first
        # amazon_data = execute_scraper_amazon_requests(driver,search_string, headers, proxy)
        # amazon_data = execute_scraper_amazon_requests(search_string, headers, proxy)
        print('check3')
        # flipkart_data = extract_flipkart_search_results(driver,search_string, headers, proxy)
        # flipkart_data = extract_flipkart_search_results(search_string, headers, proxy)
        print('check4')

        flip_copy = copy.deepcopy(flipkart_data)
        amaz_copy = copy.deepcopy(amazon_data)

        #Flipkart block

        #build wordcloud
        # for i,j in zip(flipkart_data['Comments'],flipkart_data['Product']):
        #     save_wordcloud_image(file=i, img_filename=j,search_string=search_string)
        # with concurrent.futures.ThreadPoolExecutor() as executor:
        #     for i,j in zip(flipkart_data['Comments'],flipkart_data['Product']):
        #         executor.submit(save_wordcloud_image(i,j,search_string))
        #     for i,j in zip(amazon_data['Comments'],amazon_data['Product']):
        #         executor.submit(save_wordcloud_image(i, j,search_string))
        
        for i,j in zip(flipkart_data['Comments'],flipkart_data['Product']):
            save_wordcloud_image(i,j,search_string)
        print('check5')
        for i,j in zip(amazon_data['Comments'],amazon_data['Product']):
            save_wordcloud_image(i, j,search_string)
        print('check6')

        # for i,j in zip(amazon_data['Comments'],amazon_data['Product']):
        #     save_wordcloud_image(file=i, img_filename=j,search_string=search_string)
        

                
        #Edit the reviews and embed the link to the reviews wordcloud
        flip_copy_img = [i if "(Flipkart)" in i  else "" for i in os.listdir(app.config['IMG_FOLDER']) ]

        flip_copy['Review count'] = [f'<a href="/show/{j}.png" target="_blank">{i}</a>' if j+".png" in flip_copy_img else i for i,j in zip(flip_copy['Review count'],flip_copy['Product'])]

        #Edit Product with page url
        flip_copy['Product'] = [f'<a target="_blank" href="{j}">{i}</a>' for i,j in zip(flip_copy['Product'],flip_copy['Product page'])]


        #Filtering values
        flip_copy.pop('Comments') #remove comments
        flip_copy.pop('Product page') ##remove product url


        #Dataframe to be visualised
        flipkart_df = pd.DataFrame.from_dict(flip_copy)
        print('check7')


        #Amazon block
                    
        #Edit the reviews and embed the link to the reviews wordcloud
        amaz_copy_img = [i for i in os.listdir(app.config['IMG_FOLDER']) if "(Amazon)" in i ]
        
        amaz_copy['Review count'] = [f'<a href="/show/{j}.png" target="_blank">{i}</a>' if j+".png" in amaz_copy_img else i for i,j in zip(amaz_copy['Review count'],amaz_copy['Product'])]
        #Edit Product with page url
        amaz_copy['Product'] = [f'<a target="_blank" href="{j}">{i}</a>' for i,j in zip(amaz_copy['Product'],amaz_copy['Product page'])]

                 
        #Filtering or removing values
        amaz_copy.pop('Comments') #remove comments
        amaz_copy.pop('Product page') ##remove product url
        
        #Dataframe to be visualised
        amazon_df = pd.DataFrame.from_dict(amaz_copy)
        print('check8')        


        #Dataframes to be saved
        amaz_df=pd.DataFrame.from_dict(amazon_data)
        flip_df=pd.DataFrame.from_dict(flipkart_data)


        download_path_a = save_as_dataframe(amaz_df,fileName=(search_string.replace("+", "_")+'_Amazon'))
        

        download_path_f = save_as_dataframe(flip_df,fileName=(search_string.replace("+", "_")+'_Flipkart'))
        print('check9')        

        finish = time.perf_counter()
        print(f"program finished with and timelapsed: {finish - start} second(s)")

        # driver.close()
        
        return render_template('review.html',
            tables_flip=[flipkart_df.to_html(classes='content-table',index=False,escape=False)],
            tables_amaz=[amazon_df.to_html(classes='content-table-n',index=False,escape=False)],
            download_csv_f=download_path_f,download_csv_a=download_path_a) 
    
        
        # except Exception as e:
        #     print(e)
        #     return render_template("404.html")
            
    else:
        return render_template("index.html") # return index page if home is pressed or for the first run

# route to display wordcloud
@app.route('/')
@app.route('/show/<product_name>')  # <product_name>
@cross_origin() #product_name
def show_wordcloud(product_name):
    
    # try:
    if product_name in os.listdir(app.config['IMG_FOLDER']):
        for i in os.listdir(app.config['IMG_FOLDER']):
            if i == product_name:
                file = product_name 
                full_filename = "\\" + os.path.join(app.config['IMG_FOLDER'], file)

        return render_template("show.html", user_image = full_filename)
    else:
        return render_template("404.html")
    # except Exception as e:
    #     print(e)
    #     return render_template("404.html")
#     finally:
#         clear_cache()


if __name__ == '__main__':
	app.run(debug=True)




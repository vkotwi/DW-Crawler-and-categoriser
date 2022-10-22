from itemadapter import ItemAdapter

from pymongo import MongoClient
from datetime import datetime
from bs4 import BeautifulSoup

import re


class TorCrawlerPipeline:
    def __init__(self):
        self.entry = {
            'url': None,  # url.strip(),
            'title': None,  # For quickly recognising website without visiting
            'redirects': [],
            'dateLastChecked': None,  # dt
            'parent_sites': [],
            'status': None,  # online, offline, unknown
            'topics': [],
            'data': [],
            'categories': [],  # set my ml
            'relevant': None,
            'visited': False,
            'username': "",
            'password': ""
        }

    def open_spider(self, spider):
        self.client = MongoClient('mongodb://localhost:27017/')
        self.db = self.client["DWProject"]["DW_URLs"]

    def close_spider(self, spider):
        self.client.close()

    def process_item(self, item, spider):
        # Adds/Updates URL entry to/in DB

        def categorise_page():
            soup = BeautifulSoup(item['response'], "html.parser")
            soup = soup.get_text()

            soup_no_nl = re.sub(r"\n", " ", soup)
            soup_no_tab = re.sub(r"\t", " ", soup_no_nl)

            soup = re.sub('\s+',' ', soup_no_tab)
            soup = soup.lower()

            print(soup)

            # Temp while gathering training set
            keywords = ["security", "vulnerable", "vulnerability", "exploit", "malware", "virus", "viruses", "trojan",
                        "trojans", "ransomware", "cybercrime", "server", "linux", "authenticate", "authentication",
                        "auth", "p2p", "hacked", "rat", "hack", "hacking", "bypass", "secure", "insecure", "secured",
                        "password", "passwords", "sql injection", "encrypt", "encryption", "decrypt", "decryption",
                        "command", "line", "cmd", "cmdl", "dns", "leaked", "bank", "bank details", "remotely",
                        "remoting", "database", "system", "network", "critical", "command line", "windows", "unix",
                        "macos", "mac os", "osx", "os x", "remote", "tool", "exploitable", "exploited", "scammer",
                        "scam", "overflow", "root", "privilege escalation", "rootkit", "backdoor", "backdoors",
                        "shell code", "code injection", "xss", "cross-site"]

            words_found = []
            score = 0
            for word in keywords:
                if word in soup:
                    score += 1
                    words_found.append(word)

            self.db.update_one(
                {'url': item['url']},  # Where item is the URL
                {
                    # '$addToSet': {'redirects': item['redirects']},  # Update entry if not already in there
                    '$set': {
                        'score': score,
                        'keywords': words_found
                    }
                },
            )

            # print("Soup:", soup)

        def update_url(url_from_db):
            # TODO: check if in db (parent or redirect) to update list of parent sites
            # TODO: not recording parent sites for now or redirects

            # Checks to see if new url is already in the database
            check = self.db.find_one({'url': item['url']}, {"_id": 1, "visited": 1, "status": 1})

            # If it is, it checks to see which one it should update
            if check is not None and item["url"] != url_from_db:
                if check["visited"] == True and check["status"] == 200:
                    self.db.remove({'url': url_from_db})
                    url_from_db = item['url']
                else:
                    self.db.remove({'url': item['url']})

            # If not, can update as normal
            try:
                self.db.update_one(
                    {'url': url_from_db},  # Where item is the URL
                    {
                        # '$addToSet': {'redirects': item['redirects']},  # redirects to (original site)
                        '$set': {
                            'url': item['url'],
                            'title': title,
                            'status': item['status'],
                            'dateLastChecked': datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                            'redirects': item['redirects'],
                            'data': cleaned_data,
                            'visited': True
                        }
                    },
                )
            except Exception as e:
                print("Could not update url:", e)

        # Checks to see if url already in database in different form e.g. with a https instead of http
        def dup_check(dup_url):
            url1 = dup_url.replace('https://', '').replace('http://', '')  # try without protocol
            url2 = "http://" + dup_url  # try with http protocol
            url3 = "https://" + dup_url

            freq = 0 # if greater than 1, there's a duplicate in teh database

            check0 = self.db.find_one({'url': dup_url}, {"_id": 1})  # checks if url is in db
            check1 = self.db.find_one({'url': url1}, {"_id": 1})  # checks if url without http(s) exists
            check2 = self.db.find_one({'url': url2}, {"_id": 1})  # checks if url with http exists
            check3 = self.db.find_one({'url': url3}, {"_id": 1})  # checks if url with https exists
            check4 = self.db.find_one({'url': url1 + "/"}, {"_id": 1})  # checks if url without http(s) exists
            check5 = self.db.find_one({'url': url2 + "/"}, {"_id": 1})  # checks if url with http exists
            check6 = self.db.find_one({'url': url3 + "/"}, {"_id": 1})  # checks if url with https exists

            # Check if also not current url

            if check0 is not None:
                freq += 1
            if check1 is not None:
                freq += 1
            if check2 is not None:
                freq += 1
            if check3 is not None:
                freq += 1
            if check4 is not None:
                freq += 1
            if check5 is not None:
                freq += 1
            if check6 is not None:
                freq += 1

            if freq >= 2:
                return True
            return False

        # Adds newly found urls to the db
        def add_new_urls(nu):
            for u in nu:
                # Checks to see if URL already int the database as mongodb has removed this functionality
                if not dup_check(u) and self.db.find_one({'url': u}, {"_id": 1}) is None: # if false (not in the database so not a duplicate)
                    try:
                        self.db.insert_one(
                        {
                            'url': u,
                            'visited': False
                        })
                    except Exception as e:
                        print(e)
                        pass

                # If it's already in the database, updates parent site(s)
                else:
                    if u != item['url']:
                        if self.db.find_one({'url': u, 'parent_sites': item['url']}) is None:
                            try:
                                self.db.update_one({'url': u}, {
                                    '$push':
                                    {
                                        'parent_sites': item['url']
                                    }
                                })
                            except:
                                print("could not update parent_sites list")
                                pass

        # Pulls complete URLs from the html of the web page
        def get_urls():
            urls = []
            if item['response'] == '':
                return urls

            soup = BeautifulSoup(item['response'], "html.parser")

            for a in soup.find_all('a', href=True):
                #print("Found the URL:", a['href'])
                if a['href'] != "#":
                    if "http://" in a['href'] or "https://" in a['href']:
                        if ".onion" in a['href']:
                            if "http://http://" in a['href']:
                                a['href'] = a['href'][7:]
                            if "https://https://" in a['href']:
                                a['href'] = a['href'][8:]
                            if a['href'][-2:] == "//":
                                a['href'] = a['href'][:-1]

                            urls.append(a['href'])

                            
                    else:
                        if str(a['href'])[:1] == "/":
                            a['href'] = str(item['url'])+ str(a['href'])[1:]
                        elif str(a['href'])[:1]  == '\\' or str(a['href'])[:1]  == '?' or str(a['href'])[:1] == '#':
                            a['href'] = str(item['url'])[:-1] + str(a['href'])
                        else:
                            a['href'] = str(item['url']) + str(a['href'])

                        # May not need, here just in case
                        a['href'] = a['href'].replace(".html/", ".html")
                        a['href'] = a['href'].replace(".xht/", ".xht")
                        a['href'] = a['href'].replace(".php/", ".php")
                        
                        urls.append(a['href'])
                    
                else:
                    pass
                    #print("Interactive")

            soup = soup.get_text()

            # Can find links BS4 can't
            url_16 = re.compile(r'(?:\bhttp://\b|\bhttps://\b)*(?:[a-zA-Z0-9-_][\.]*)*[a-zA-Z2-7]{16}\.onion(?:[/:#?=]+[a-zA-Z0-9-]*)*')
            url_56 = re.compile(r'(?:\bhttp://\b|\bhttps://\b)*(?:[a-zA-Z0-9-_][\.]*)*[a-zA-Z2-7]{56}\.onion(?:[/:#?=]+[a-zA-Z0-9-]*)*')

            urls.extend(re.findall(url_16, soup))
            urls.extend(re.findall(url_56, soup))

            temp = []
            for u1 in urls:
                temp.append(u1.strip())

            urls = temp

            urls = list(set(urls))
            # TODO: remove images
            count = 0
            for i in urls:
                if i[-1:] == ".":
                    urls[count] = i[:-1]  # removes fullstops at end of string from list
                count += 1

            return urls

        # Gets all data from website
        def parse_data():
            # TODO: do without BS4?
            title = ""
            data = []

            try:
                soup = BeautifulSoup(item['response'], "html.parser")
            except:
                return [title, data]

            try:
                title = soup.find("title").get_text()
            except:
                pass

            try:
                soup = soup.get_text()

                rmv_space = re.compile(r'\s{2,}', flags=re.UNICODE)  # \s\s+
                # Remove excessive white space and newline characters
                soup = (re.sub(rmv_space, ' ', soup))
                soup = soup.replace('\n', ' ')

                #if soup != "":
                #    soup_list = soup.split(' ')
                #    data = list(set(soup_list))  # Removes duplicate words from the list because for categorising only
                data = soup
            except:
                pass

            return [title, data]

        # Returns url that's in database if current url not in there exactly e.g. different protocol or has a / at the end
        def find_db_url():
            url = item['url']
            url1 = url.replace('https://', '').replace('http://', '') # try without protocol
            url2 = "http://" + url # try with http protocol
            url3 = "https://" + url

            check1 = self.db.find_one({'url': url1}, {"_id": 1})  # checks if url without http(s) exists
            check2 = self.db.find_one({'url': url2}, {"_id": 1})  # checks if url with http exists
            check3 = self.db.find_one({'url': url3}, {"_id": 1})  # checks if url with https exists
            check4 = self.db.find_one({'url': url1[:-1]}, {"_id": 1})  # checks if url without "/" at end
            check5 = self.db.find_one({'url': url2[:-1]}, {"_id": 1})
            check6 = self.db.find_one({'url': url3[:-1]}, {"_id": 1})

            #im sorry
            if check1 is not None:
                url = url1
            elif check2 is not None:
                url = url2
            elif check3 is not None:
                url = url3
            elif check4 is not None:
                url = url1[:-1]
            elif check5 is not None:
                url = url2[:-1]
            elif check6 is not None:
                url = url3[:-1]

            return url


        if item['url'] != "":
            db_url = find_db_url()  # url that's currently in the database

            res = item['response']
            try:
                item['response'] = item['response'].text
            except:
                item['response'] = ''

            print("item['redirects']:", item['redirects'])

            if item['status'] >= 400:
                print("Response:", item['status'])
                print("dd: ", item["response"])
                if dup_check(item['url']):
                    print("DUP FOUND")
                    self.db.remove({'url': item['url']})

                elif "https://" in item['url']:
                    self.db.update_one(
                        {'url': db_url},  # Where item is the URL
                        {
                            '$set': {
                                'status': item['status'],
                                'redirects': item['redirects'],
                                'dateLastChecked': datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                                'visited': True
                            }
                        },
                    )

                elif "http://" in item['url']:
                    # tries to connect to the url again by saving it as https
                    # If the url had no protocol, automatically tries http first so there's no need to
                    # check for that one as well here
                    new_url = item['url'].replace("http://", "https://")
                    self.db.update_one(
                        {'url': db_url},  # Where item is the URL
                        {
                            '$set': {
                                'url': new_url,
                                'redirects': item['redirects'],
                                'status': item['status'],
                                'dateLastChecked': datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                                'visited': False
                            }
                        },
                    )

            else:
                # If response successful
                title, cleaned_data = parse_data()
                new_urls = get_urls()

                update_url(db_url)
                add_new_urls(new_urls)
                categorise_page()


        try:
            self.db.close()
        except:
            pass

        return item

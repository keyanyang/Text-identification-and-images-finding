import re
import operator
import argparse
from urllib.request import urlopen
from bs4 import BeautifulSoup
from pyquery import PyQuery as pq
import time
import sys
from unidecode import unidecode
import os

debug = False
test = True

url = sys.argv[1]
# url = 'https://www.nytimes.com/2017/04/22/sports/basketball/golden-state-warriors-steve-kerr-portland.html?rref=collection%2Fsectioncollection%2Fsports'

def is_number(s):
    try:
        float(s) if '.' in s else int(s)
        return True
    except ValueError:
        return False


def load_stop_words(stop_word_file):

    stop_words = []
    for line in open(stop_word_file):
        if line.strip()[0:1] != "#":
            for word in line.split():  # in case more than one per line
                stop_words.append(word)
    return stop_words


def separate_words(text, min_word_return_size):

    splitter = re.compile('[^a-zA-Z0-9_\\+\\-/]')
    words = []
    for single_word in splitter.split(text):
        current_word = single_word.strip().lower()
        #leave numbers in phrase, but don't count as words, since they tend to invalidate scores of their phrases
        if len(current_word) > min_word_return_size and current_word != '' and not is_number(current_word):
            words.append(current_word)
    return words


def split_sentences(text):

    sentence_delimiters = re.compile(u'[.!?,;:\t\\\\"\\(\\)\\\'\u2019\u2013]|\\s\\-\\s')
    sentences = sentence_delimiters.split(text)
    return sentences


def build_stop_word_regex(stop_word_file_path):
    stop_word_list = load_stop_words(stop_word_file_path)
    stop_word_regex_list = []
    for word in stop_word_list:
        word_regex = r'\b' + word + r'(?![\w-])'  # added look ahead for hyphen
        stop_word_regex_list.append(word_regex)
    stop_word_pattern = re.compile('|'.join(stop_word_regex_list), re.IGNORECASE)
    return stop_word_pattern


def generate_candidate_keywords(sentence_list, stopword_pattern):
    phrase_list = []
    for s in sentence_list:
        tmp = re.sub(stopword_pattern, '|', s.strip())
        phrases = tmp.split("|")
        for phrase in phrases:
            phrase = phrase.strip().lower()
            if phrase != "":
                phrase_list.append(phrase)
    return phrase_list


def calculate_word_scores(phraseList):
    word_frequency = {}
    word_degree = {}
    for phrase in phraseList:
        word_list = separate_words(phrase, 0)
        word_list_length = len(word_list)
        word_list_degree = word_list_length - 1

        for word in word_list:
            word_frequency.setdefault(word, 0)
            word_frequency[word] += 1
            word_degree.setdefault(word, 0)
            word_degree[word] += word_list_degree  #orig.

    for item in word_frequency:
        word_degree[item] = word_degree[item] + word_frequency[item]


    word_score = {}
    for item in word_frequency:
        word_score.setdefault(item, 0)
        word_score[item] = word_degree[item] / (word_frequency[item] * 1.0)  #orig.

    return word_score


def generate_candidate_keyword_scores(phrase_list, word_score):
    keyword_candidates = {}
    for phrase in phrase_list:
        keyword_candidates.setdefault(phrase, 0)
        word_list = separate_words(phrase, 0)
        candidate_score = 0
        for word in word_list:
            candidate_score += word_score[word]
        keyword_candidates[phrase] = candidate_score
    return keyword_candidates


class Rake(object):
    def __init__(self, stop_words_path):
        self.stop_words_path = stop_words_path
        self.__stop_words_pattern = build_stop_word_regex(stop_words_path)

    def run(self, text):
        sentence_list = split_sentences(text)

        phrase_list = generate_candidate_keywords(sentence_list, self.__stop_words_pattern)

        word_scores = calculate_word_scores(phrase_list)

        keyword_candidates = generate_candidate_keyword_scores(phrase_list, word_scores)

        sorted_keywords = sorted(keyword_candidates.items(), key=operator.itemgetter(1), reverse=True)
        return sorted_keywords


if test:
    #text_test = "Compatibility of systems of linear constraints over the set of natural numbers. Criteria of compatibility of a system of linear Diophantine equations, strict inequations, and nonstrict inequations are considered. Upper bounds for components of a minimal set of solutions and algorithms of construction of minimal generating sets of solutions for all types of systems are given. These criteria and the corresponding algorithms for constructing a minimal supporting set of solutions can be used in solving all the considered types of systems and systems of mixed types."


    d = pq(url=url)
    text = d('.story-content').text()

    text = text
    # Split text into sentences
    sentenceList = split_sentences(text)
    #stoppath = "FoxStoplist.txt" #Fox stoplist contains "numbers", so it will not find "natural numbers" like in Table 1.1
    stoppath = "SmartStoplist.txt"  #SMART stoplist misses some of the lower-scoring keywords in Figure 1.5, which means that the top 1/3 cuts off one of the 4.0 score words in Table 1.1
    stopwordpattern = build_stop_word_regex(stoppath)

    # generate candidate keywords
    phraseList = generate_candidate_keywords(sentenceList, stopwordpattern)

    # calculate individual word scores
    wordscores = calculate_word_scores(phraseList)

    # generate candidate keyword scores
    keywordcandidates = generate_candidate_keyword_scores(phraseList, wordscores)
    if debug: print (keywordcandidates)

    sortedKeywords = sorted(keywordcandidates.items(), key=operator.itemgetter(1), reverse=True)
    if debug: print (sortedKeywords)

    totalKeywords = len(sortedKeywords)
    if debug: print (totalKeywords)
    #print (sortedKeywords[0:(totalKeywords / 3)])

    rake = Rake("SmartStoplist.txt")
    keywords = rake.run(text)
    search_keyword = [unidecode(keywords[0][0])]

    keywords = [' ']


    def download_page(url):
        version = (3, 0)
        cur_version = sys.version_info
        if cur_version >= version:  # If the Current Version of Python is 3.0 or above
            import urllib.request  # urllib library for Extracting web pages
            try:
                headers = {}
                headers[
                    'User-Agent'] = "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36"
                req = urllib.request.Request(url, headers=headers)
                resp = urllib.request.urlopen(req)
                respData = str(resp.read())
                return respData
            except Exception as e:
                print(str(e))
        else:  # If the Current Version of Python is 2.x
            import urllib2
            try:
                headers = {}
                headers[
                    'User-Agent'] = "Mozilla/5.0 (X11; Linux i686) AppleWebKit/537.17 (KHTML, like Gecko) Chrome/24.0.1312.27 Safari/537.17"
                req = urllib2.Request(url, headers=headers)
                response = urllib2.urlopen(req)
                page = response.read()
                return page
            except:
                return "Page Not found"


    # Finding 'Next Image' from the given raw page
    def _images_get_next_item(s):
        start_line = s.find('rg_di')
        if start_line == -1:  # If no links are found then give an error!
            end_quote = 0
            link = "no_links"
            return link, end_quote
        else:
            start_line = s.find('"class="rg_meta"')
            start_content = s.find('"ou"', start_line + 1)
            end_content = s.find(',"ow"', start_content + 1)
            content_raw = str(s[start_content + 6:end_content - 1])
            return content_raw, end_content


    # Getting all links with the help of '_images_get_next_image'
    def _images_get_all_items(page):
        items = []
        while True:
            item, end_content = _images_get_next_item(page)
            if item == "no_links":
                break
            else:
                items.append(item)  # Append all the links in the list named 'Links'
                time.sleep(0.1)  # Timer could be used to slow down the request for image downloads
                page = page[end_content:]
        return items

    t0 = time.time()  # start the timer

    # Download Image Links
    i = 0
    while i < len(search_keyword):
        items = []
        iteration = "Item no.: " + str(i + 1) + " -->" + " Item name = " + str(search_keyword[i])
        print(iteration)
        print("Evaluating...")
        search_keywords = search_keyword[i]
        search = search_keywords.replace(' ', '%20')
        j = 0
        while j < len(keywords):
            pure_keyword = keywords[j].replace(' ', '%20')
            url = 'https://www.google.com/search?q=' + search + pure_keyword + '&espv=2&biw=1366&bih=667&site=webhp&source=lnms&tbm=isch&sa=X&ei=XosDVaCXD8TasATItgE&ved=0CAcQ_AUoAg'
            raw_html = (download_page(url))
            time.sleep(0.1)
            items = items + (_images_get_all_items(raw_html))
            j = j + 1
        # print ("Image Links = "+str(items))
        print("Total Image Links = " + str(len(items)))
        print("\n")
        i = i + 1

        if not os.path.exists('outputs'):
            os.makedirs('outputs')

        # write all the links into a test file. This text file will be created in the same directory as your code. You can comment out the below 3 lines to stop writing the output to the text file.
        info = open('outputs/output.txt', 'a')  # Open the text file called database.txt
        info.write(
            str(i) + ': ' + str(search_keyword[i - 1]) + ": " + str(items) + "\n\n\n")  # Write the title of the page
        info.close()  # Close the file

    t1 = time.time()  # stop the timer
    total_time = t1 - t0  # Calculating the total time required to crawl, find and download all the links of 60,000 images
    print("Total time taken: " + str(total_time) + " Seconds")
    print("Starting Download...")

    ## To save imges to the same directory
    # IN this saving process we are just skipping the URL if there is any error

    k = 0
    errorCount = 0
    while (k < len(items)):
        from urllib.request import Request, urlopen
        from urllib.error import URLError, HTTPError

        try:
            req = Request(items[k], headers={
                "User-Agent": "Mozilla/5.0 (X11; Linux i686) AppleWebKit/537.17 (KHTML, like Gecko) Chrome/24.0.1312.27 Safari/537.17"})
            response = urlopen(req)
            output_file = open("outputs/" + str(k + 1) + ".jpg", 'wb')
            data = response.read()
            output_file.write(data)
            response.close()

            print("completed ====> " + str(k + 1))

            k = k + 1

        except IOError:  # If there is any IOError

            errorCount += 1
            print("IOError on image " + str(k + 1))
            k = k + 1

        except HTTPError as e:  # If there is any HTTPError

            errorCount += 1
            print("HTTPError" + str(k))
            k = k + 1
        except URLError as e:

            errorCount += 1
            print("URLError " + str(k))
            k = k + 1

    print("\n")
    print("All are downloaded")
    print("\n" + str(errorCount) + " ----> total Errors")
# Text-identification-and-images-finding
This project uses Python to find the best images based on the theme of specific article. 

1. Edit url in line 14 of the Python script (At this time, articles on nytimes.com work)
2. Run Python file

The coding work, which is a Python script, consists of three parts. The first part uses Rapid Automatic Keyword Extraction (RAKE) algorithm with NLKT to identify keywords of article. The second part extracts text from HTML. The third part downloads images based on keywords of article. Part of code and theories in this project come from others’ blogs and open source projects. Here Hardik Vasa developed a program to download images from Google (https://github.com/hardikvasa/google-images-download). Sujit Pal talked about the use of RAKE on natural language processing (http://sujitpal.blogspot.com/2013/03/implementing-rake-algorithm-with-nltk.html). 

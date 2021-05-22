# flyingv-data-crawler
This project aims to help get data of [flyingV](https://www.flyingv.cc/ "link"), a fundraising website in Taiwan.

It's also a simple sample of asynchronous web scraping.

## Environment
* Windows

## Prerequisite
* Clone the repo
  ```
  $ git clone https://github.com/thronepohan/flyingv-data-crawler.git
  ```
* Run the commands under flyingv-data-crawler
  ```
  $ pip install -r requirement.txt
  ```
* Download the appropriate version of [ChromeDriver](https://chromedriver.chromium.org/downloads "link"), and replace `chromedriver.exe`
  
## Configuration
* Check main.py
  ```Python
  # times to scroll web page
  SCROLL_COUNT = 3

  # succeesful or failed projects
  SUCCESSFUL_OR_FAILED = True

  # IS_FLEXIBLE set true to input url & output filename by user
  IS_FLEXIBLE = True
  INPUT_URL = "https://www.flyingv.cc/projects?filter=all&sort=end&category=product"
  OUTPUT_FILENAME = "ethan-test"
  ```
* If you want to use fixed url and output filename, configure as following:
  ```Python
  IS_FLEXIBLE = False
  INPUT_URL = <your_url>
  OUTPUT_FILENAME = <custom_filename>
  ```
* Sample URL:
  * https://www.flyingv.cc/projects?filter=all&sort=end&category=all
  * https://www.flyingv.cc/projects?filter=all&sort=end&category=music

## Usage
```
$ python main.py
```

## Unit test
```
python -m pytest test
```

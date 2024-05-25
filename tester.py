# basic testing for utils and functions

from utils.processors import scan_file
import logging

log_format = "%(asctime)s - %(levelname)-5s - %(filename)s:%(lineno)s - %(funcName)s - %(message)s"
logging.basicConfig(filename='dev-ai-test.log', filemode='w',level=logging.INFO,format=log_format)


print(scan_file("tests/index.html.erb","html"))
print(scan_file("tests/user.rb","ruby"))

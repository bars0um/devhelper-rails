# basic testing for utils and functions

from utils.processors import scan_file, get_file_path
import logging

log_format = "%(asctime)s - %(levelname)-5s - %(filename)s:%(lineno)s - %(funcName)s - %(message)s"
logging.basicConfig(filename='dev-ai-test.log', filemode='w',level=logging.INFO,format=log_format)


print(scan_file("tests/index.html.erb","html"))
print(scan_file("tests/user.rb","ruby"))

test_file_paths_1="""
```html
<!-- /app/myapp/index.html.erb -->

```
"""

print(get_file_path(test_file_paths_1))

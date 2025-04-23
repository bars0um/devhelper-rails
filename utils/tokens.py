import tiktoken
import os
                                 
                                 
tiktoken_cache_dir = "/data/tiktoken"
os.environ["TIKTOKEN_CACHE_DIR"] = tiktoken_cache_dir                                  
                                 
# see https://stackoverflow.com/questions/76106366/how-to-use-tiktoken-in-offline-mode-computer
                                 
def num_tokens_from_string(string: str, encoding_name: str) -> int:
    # default should be encoding_name = "cl100k_base"
    #assert os.path.exists(os.path.join(tiktoken_cache_dir,"9b5ad71b2ce5302211f9c61530b329a4922fc6a4")):
    try:
        encoding = tiktoken.get_encoding(encoding_name)
        num_tokens = len(encoding.encode(string))
        return num_tokens
    except:
        return 'could not load ' + encoding_name
                                 
#  f = open("/test.prompt", "r")
#  text_to_count = f.read()                                 
# "Hello world, let's test tiktoken."
#  print(num_tokens_from_string(text_to_count, "cl100k_base"))


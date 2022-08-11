"""
Check URL

Verify that the url sent is reachable

We assume that a URL exist
"""

import urllib
from urllib import request
from urllib.error import HTTPError

class check_url:
    """
    The following class verifies if a url is valid or not

    Please add a valid url:

    """

    def __init__(self,url):
        self.url=url

    def validate_url(url):
        """
        validate a url to see if a response is available  
        """
        
        print("\n------------------")
        print("verify the url")
        print(url)

        try:

            response = request.urlopen(url)
            #response = request.
            response_code = response.code
            print("the response code is : {0}".format(response_code))
            
            # compare urls to see if a redirect has occured
            final_url = response.url 
            if(url != final_url):
                print("Warning: The URL is a Redirect")
            print("----------------")

        except HTTPError as e:
                        # display the internal HTTP error
            print(e.reason)
            response_error = e.code
            print("Error: the response code is: {0}".format(response_error))
            response_error = 400
            print("----------------")
        except (ValueError) as e:
            # display the internal HTTP error
            print(e)
            response_error = "Invalid URL"
            print("Error: the response code is: {0}".format(response_error))
            print("----------------")



# check if the url is a redirect


# check if the url passes
url1 = "https://www.google.com"
url2 = "https://github.com/conda-forg"
url3 = "http://astroid.readthedocs.io/en/latest/?badge=latest"
url4 = "google.com"


if __name__ == "__main__":

    check_url.validate_url(url1)
    check_url.validate_url(url2)
    check_url.validate_url(url3)
    check_url.validate_url(url4)

from urllib.request import urlopen


def downloadResource(url):
    response = urlopen(url)
    data = response.read()
    return data.decode("utf-8")

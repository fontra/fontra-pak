import re

from release_helpers import downloadResource


def getLatestChanges(text):
    m = re.search(r"\n## .*?\n(.*?)\n## ", text, re.DOTALL)
    return m.group(1).strip()


changeLogURL = (
    "https://raw.githubusercontent.com/fontra/fontra/refs/heads/main/CHANGELOG.md"
)

changeLogText = downloadResource(changeLogURL)

print(getLatestChanges(changeLogText))

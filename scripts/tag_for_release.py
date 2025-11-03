import json
import subprocess

from release_helpers import downloadResource


def parseTag(tag):
    try:
        yyyy, mm, patch = [int(item) for item in tag.split(".")]
    except ValueError:
        return (0, 0, 0)
    return (yyyy, mm, patch)


def getLatestTag():
    tagsURL = "https://api.github.com/repos/fontra/fontra/tags"
    tagsInfo = json.loads(downloadResource(tagsURL))

    tags = sorted([info["name"] for info in tagsInfo], key=parseTag)

    return tags[-1]


latestTag = getLatestTag()
print(f"Using tag: {latestTag}")

subprocess.run(
    ["git", "tag", "-a", latestTag, "-m", f"Version {latestTag}"],
    check=True,
)

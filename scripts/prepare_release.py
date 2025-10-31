import json
import pathlib
import subprocess

from release_helpers import downloadResource


def parseTag(tag):
    try:
        yyyy, mm, patch = [int(item) for item in tag.split()]
    except ValueError:
        return (0, 0, 0)
    return (yyyy, mm, patch)


def getLatestTag():
    tagsURL = "https://api.github.com/repos/fontra/fontra/tags"
    tagsInfo = json.loads(downloadResource(tagsURL))

    tags = sorted([info["name"] for info in tagsInfo], key=parseTag)

    return tags[-1]


def updateRequirements(reqsPath, latestTag):
    reqsText = reqsPath.read_text()
    lines = reqsText.splitlines(keepends=True)

    target = "git+https://github.com/fontra/fontra.git"

    newLines = []
    for line in lines:
        if line.startswith(target):
            line = line[: len(target)] + "@" + latestTag + "\n"
        newLines.append(line)

    newReqsText = "".join(newLines)
    if newReqsText != reqsText:
        reqsPath.write_text(newReqsText)
        return True

    return False


repoDir = pathlib.Path(__file__).resolve().parent.parent
reqsPath = repoDir / "requirements.txt"

latestTag = getLatestTag()

if updateRequirements(reqsPath, latestTag):
    subprocess.run(
        ["git", "commit", "-m", f"bump to {latestTag}", "requirements.txt"],
        cwd=repoDir,
        check=True,
    )
else:
    print("requirements.txt not changed")

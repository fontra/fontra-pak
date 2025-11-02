import pathlib
import sys


def patchRequirements(reqsPath, tag):
    reqsText = reqsPath.read_text()
    lines = reqsText.splitlines(keepends=True)

    target = "git+https://github.com/fontra/fontra.git"

    newLines = []
    for line in lines:
        if line.startswith(target):
            line = line[: len(target)] + "@" + tag + "\n"
        newLines.append(line)

    newReqsText = "".join(newLines)
    if newReqsText != reqsText:
        reqsPath.write_text(newReqsText)
        return True

    return False


repoDir = pathlib.Path(__file__).resolve().parent.parent
reqsPath = repoDir / "requirements.txt"

tag = sys.argv[1]
print(f"using fontra git tag: {tag}")
patchRequirements(reqsPath, tag)

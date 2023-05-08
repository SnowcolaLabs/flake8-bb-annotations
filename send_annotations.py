import os
import requests
import fileinput

WORKSPACE = os.environ.get("BITBUCKET_WORKSPACE")
REPO = os.environ.get("BITBUCKET_REPO_SLUG")
COMMIT = os.environ.get("BITBUCKET_COMMIT")
PR_ID = os.environ.get("BITBUCKET_PR_ID")
API_SERVER = os.environ.get("API_SERVER", "https://api.bitbucket.org")
BUILD = os.environ.get("BITBUCKET_BUILD_NUMBER", "no-build")
REPORT_ID = "flake8-annotations-{pr}-{build}".format(pr=PR_ID, build=BUILD)
AUTH = os.environ.get("AUTH")

headers={"User-Agent": "Mozilla",
    "Cookie": "troute=t1",
    "Authorization": "Basic {auth}".format(auth=AUTH)
    }

url="{server_url}/2.0/repositories/{workspace}/{repo_slug}/commit/{commit}/reports/{report_id}"
formatted_url = url.format(
    server_url = API_SERVER,
    workspace = WORKSPACE,
    repo_slug = REPO,
    commit = COMMIT,
    report_id = REPORT_ID,
)

def create_or_update_report(url, annotations, headers):
    res=requests.put(
            url=url,
            json={
            "title": "Flake 8 Report",
            "details": "This report identifies code style, syntax and best practice violations",
            "report_type": "TEST",
            "reporter": "Flake 8",
            "result": "FAILED" if annotations else "PASSED",
            "data": [
                {
                    "title": "Linting Errors",
                    "type": "NUMBER",
                    "value": len(annotations)
                },]
            },
            headers=headers)
    return res

def create_or_update_annotations(url, annotations, headers):
    res = requests.post(url=url+"/annotations", json=annotations, headers=headers)
    return res

def categorize(error_code):
    code = error_code.upper()
    if code.startswith(("B", "E9", "F8", "F9", "W6")):
        return ("HIGH", "BUG")
    elif code.startswith("MAX"):
        return ("HIGH", "BUG")
    elif code.startswith(("W1", "W6", "E722")):
        return ("HIGH", "CODE_SMELL")
    elif code.startswith(("F4", "E7", "N")):
        return ("MEDIUM", "CODE_SMELL")
    elif code.startswith(("E1", "E2", "E3", "E4", "E5", "W2", "W3", "W5")):
        return ("LOW", "CODE_SMELL")
    return ("LOW", "CODE_SMELL")


def parse_violation(violation, id):
    f, line, col, err = violation.split(":")
    error_info = err.strip().split(" ")
    error_code = error_info[0]
    error_txt = " ".join(error_info[1:])
    sev, a_type = categorize(error_code)
    return {
        "external_id": "{report}-{id:03}".format(report=REPORT_ID, id=id),
        "title": error_code,
        "annotation_type": a_type,
        "summary": error_txt,
        "severity": sev,
        "path": f,
        "line": line
    } 


def main():
    annotations = []
    id = 1
    for line in fileinput.input():
        print(line.strip().split(":"))
        annotations.append(parse_violation(line, id))
        id += 1
    report_r = create_or_update_report(formatted_url, annotations, headers)
    print("Report Submitted: ", report_r.status_code)
    annot_r = create_or_update_annotations(formatted_url, annotations, headers)
    print("Annotations Submitted: ", annot_r.status_code)


if __name__ == "__main__": 
    main()
import argparse
from defectdojo_reporting import reporting


def print_findings(findings):
    print("Critical: " + str(findings[4]))
    print("High: " + str(findings[3]))
    print("Medium: " + str(findings[2]))
    print("Low: " + str(findings[1]))
    print("Info: " + str(findings[0]))


def summary(api_client, test_id):
    total_findings = reporting.list_findings(
        api_client, test=test_id, duplicate=False, active=True, verified=True)
    duplicate_findings = reporting.list_findings(
        api_client, test=test_id, duplicate=True)
    findings_sla_overdue = [
        finding for finding in total_findings if (finding.sla_days_remaining or 0) < 0]

    print("==============================================")
    print(f"Total Number of New Findings: {len(total_findings)}")
    print("==============================================")
    print_findings(reporting.sum_severity(total_findings))
    print("")

    print("==============================================")
    print(f"Total Number of Duplicate Findings: {len(duplicate_findings)}")
    print("==============================================")
    print_findings(reporting.sum_severity(duplicate_findings))
    print("")

    print(
        f"Total Number of Findings with SLA overdue: {len(findings_sla_overdue)}")
    print("==============================================")
    print_findings(reporting.sum_severity(findings_sla_overdue))
    print("")

    if len(findings_sla_overdue) > 0:
        print("Build Failed: SLA overdue :(")
    elif len(total_findings) > 0:
        print("Build Passed! But there issue to fix :/")
    else:
        print("Build Passed! :)")

    print("==============================================")


def main():
    parser = argparse.ArgumentParser(
        description='CI/CD integration for DefectDojo')
    parser.add_argument('--host', help="DefectDojo Hostname", required=True)
    parser.add_argument('--api_token', help="API Key", required=True)
    parser.add_argument('--user', help="User", required=True)

    parser.add_argument(
        '--branch_name', help="Reference to branch being scanned", 
        required=True)
    parser.add_argument(
        '--branch_sla_one', help="Does this branch have SLA control?", 
        required=False, type=bool, default=False)
    parser.add_argument(
        '--product', help="DefectDojo Product ID", required=True, type=int)
    parser.add_argument('--repo', help="Repo Name", required=True)
    parser.add_argument('--push_to_jira', help="Push to Jira?",
                        required=False, type=bool, default=False)

    parser.add_argument('--file', help="Findings file", required=True)
    parser.add_argument('--test_type_id', help="Scanner Type ID", required=True)

    args = vars(parser.parse_args())

    host = args["host"]
    api_token = args["api_token"]
    user = args["user"]

    product = args["product"]
    repo = args["repo"]
    branch_name = args["branch_name"]
    push_to_jira = args["push_to_jira"]
    test_type_id = args["test_type_id"]
    file = args["file"]
    api_client = reporting.get_api_client(host, api_token)
    user_id = reporting.get_user_id(api_client, user)
    test_type_obj = reporting.get_test_type(api_client, test_type_id)
    product_id = reporting.get_product_id(api_client, product)
    engagement_id = reporting.get_engagement_id(
        api_client, product_id, user_id, repo, branch_name)

    test_id = reporting.get_test_id(
        api_client, engagement_id, test_type_obj.name, test_type_obj.id, 1)
    
    reporting.reimport(api_client, test_id, file, True,
                       test_type_obj.name, push_to_jira)
    summary(api_client, test_id)


if __name__ == '__main__':
    main()

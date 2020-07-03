import argparse
from defectdojo_reporting import reporting


def print_findings(findings):
    for level in findings:
        print(level + ": " + str(findings[level]))


def summary_sla(total_findings):
    
    # finding must be verified
    findings_not_verified = [
        finding for finding in total_findings if finding.verified is False
    ]
    if len(findings_not_verified) > 0:
        print("======================================================================")
        print(f"Total number of findings not verified: {len(findings_not_verified)}")
        print("======================================================================")
        print_findings(reporting.sum_severity(findings_not_verified))
        print("")
        print("Build Failed!")
        print("======================================================================")
        exit(1)
    
    findings_sla_overdue = [
        finding for finding in total_findings if (finding.sla_days_remaining or 0) < 0
    ]
    if len(findings_sla_overdue) > 0:
        print("======================================================================")
        # finding sla_days_remaining cannot be negative(SLA overdue)
        print(f"Total number of findings with SLA overdue: {len(findings_sla_overdue)}")
        print("======================================================================")
        print_findings(reporting.sum_severity(findings_sla_overdue))
        print("")
        print("Build Failed! :(")
        print("======================================================================")
        exit(1)

def summary_level_severity(total_findings, control_level):
    severity_control = {
        'Critical': 5,
        'High': 4,
        'Medium': 3,
        'Low': 2,
        'Info': 1
    }

    min_level =  severity_control[control_level.capitalize()]
    findings_filtered = [
        finding for finding in total_findings \
            if min_level <= severity_control[finding.severity]
    ]
    if len(findings_filtered) > 0:
        print("======================================================================")
        print(f"Total number of findings with control severity violoted: {len(findings_filtered)}")
        print("======================================================================")
        print_findings(reporting.sum_severity(findings_filtered))
        print("")
        print("Build Failed! :(")
        print("======================================================================")
        exit(1)

def summary(api_client, test_id, control_sla, control_level):
    total_findings = reporting.list_findings(
        api_client, test=test_id, duplicate=False, active=True)

    print("======================================================================")
    print(f"Total number of findings: {len(total_findings)}")
    print("======================================================================")
    print_findings(reporting.sum_severity(total_findings))
    print("")

    if control_sla:
        summary_sla(total_findings)
    elif control_level:
        summary_level_severity(total_findings, control_level)
    
    if len(total_findings) > 0:
        print("Build Passed! But there issue to fix :/")
    else:
        print("Build Passed! :)")
    print("======================================================================")
    exit(0)


def main():
    parser = argparse.ArgumentParser(
        description='CI/CD integration for DefectDojo')
    
    # auth
    parser.add_argument('--host', help="DefectDojo Hostname", required=True)
    parser.add_argument('--api_token', help="API Key", required=True)
    parser.add_argument('--user', help="User", required=True)

    # project
    parser.add_argument(
        '--product', help="DefectDojo Product ID", required=True, type=int)
    parser.add_argument('--repo', help="Repo Name", required=True)
    parser.add_argument(
        '--branch_name', help="Reference to branch being scanned", required=True)
    
    # importing results
    parser.add_argument('--file', help="Findings file", required=True)
    parser.add_argument('--test_type_id', help="Scanner Type ID", required=True)

    # controls
    parser.add_argument(
        '--control_sla', help="Does this branch have SLA control?", 
        type=bool, default=False)
    parser.add_argument(
        '--control_level', help="Minimum level of severity control", 
        choices=['critical', 'high', 'medium', 'low', 'info'], 
        required=False, default='info')
    parser.add_argument(
        '--push_to_jira', help="Push to Jira?", required=False, 
        type=bool, default=False)

    args = vars(parser.parse_args())

    # auth
    host = args["host"]
    api_token = args["api_token"]
    user = args["user"]

    # project
    product = args["product"]
    repo = args["repo"]
    branch_name = args["branch_name"]
    
    # importing results
    file = args["file"]
    test_type_id = args["test_type_id"]
    
    # controls
    control_sla = args["control_sla"]
    control_level = args["control_level"]
    push_to_jira = args["push_to_jira"]
    
    api_client = reporting.get_api_client(host, api_token)
    user_id = reporting.get_user_id(api_client, user)
    test_type_obj = reporting.get_test_type(api_client, test_type_id)
    product_id = reporting.get_product_id(api_client, product)
    engagement_id = reporting.get_engagement_id(
        api_client, product_id, user_id, repo, branch_name)
    test_id = reporting.get_test_id(
        api_client, engagement_id, test_type_obj.name, test_type_obj.id, 1)
    reporting.reimport(
        api_client, test_id, file, True, test_type_obj.name, push_to_jira)
    summary(api_client, test_id, control_sla, control_level)

if __name__ == '__main__':
    main()

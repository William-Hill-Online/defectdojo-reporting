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
        print("=============================================================")
        print(f"Total number of findings not verified: {len(findings_not_verified)}")
        print("=============================================================")
        print_findings(reporting.sum_severity(findings_not_verified))
        print("\n")
        print("Build Failed!")
        print("=============================================================")
        exit(1)
    
    findings_sla_overdue = [
        finding for finding in total_findings if (finding.sla_days_remaining or 0) < 0
    ]
    if len(findings_sla_overdue) > 0:
        print("=============================================================")
        # finding sla_days_remaining cannot be negative(SLA overdue)
        print(f"Total number of findings with SLA overdue: {len(findings_sla_overdue)}")
        print("=============================================================")
        print_findings(reporting.sum_severity(findings_sla_overdue))
        print("\n")
        print("Build Failed! :(")
        print("=============================================================")
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
        print("=============================================================")
        print(f"Total number of findings with control severity violated: {len(findings_filtered)}")
        print("=============================================================")
        print_findings(reporting.sum_severity(findings_filtered))
        print("\n")
        print("Build Failed! :(")
        print("=============================================================")
        exit(1)

def summary(api_client, test_id, control_level):
    total_findings = reporting.list_findings(
        api_client, test=test_id, duplicate=False, active=True)
    
    print("=============================================================")
    print("Summary")
    print("=============================================================")
    host = api_client.configuration.host    
    link = f"{host[0:host.find('/api')]}/test/{test_id}"
    print(f"Dashboard: {link}")
    print(f"Severity Control: {control_level.upper()}")
    print("\n")
    
    print("=============================================================")
    print(f"Total number of findings: {len(total_findings)}")
    print("=============================================================")
    print_findings(reporting.sum_severity(total_findings))
    print("\n")

    if control_level == 'sla':
        summary_sla(total_findings)
    else:
        summary_level_severity(total_findings, control_level)
    
    if len(total_findings) > 0:
        print("Build Passed! But there are issues to fix yet :/")
    else:
        print("Build Passed! :)")
    print("=============================================================")
    exit(0)


def main():
    parser = argparse.ArgumentParser(
        description='CI/CD integration for DefectDojo')
    
    # connection
    parser.add_argument('--ssl_ca_cert', help="SSL CA CERT", required=True)
    parser.add_argument('--host', help="DefectDojo Hostname", required=True)

    # auth
    parser.add_argument('--api_token', help="API Key", required=True)

    # project
    parser.add_argument('--lead_testing', help="Lead Testing", required=True)
    parser.add_argument('--product_type', help="Product Type", required=True)
    parser.add_argument('--product_name', help="Product Name", required=True)
    parser.add_argument(
        '--product_description', help="Product Description", required=True)
    parser.add_argument(
        '--jira_project_key', help="Jira Project Key", required=True)
    parser.add_argument(
        '--engagement_name', help="Engagement Name", required=True)
    parser.add_argument('--tags', help="Tags", required=True)
    
    # importing results
    parser.add_argument('--file', help="Findings file", required=True)
    parser.add_argument(
        '--test_type_id', help="Test Type ID", required=True, type=int)
    parser.add_argument('--scan_type', help="Scan Type", required=True)

    # controls
    parser.add_argument(
        '--control_level', help="Minimum level of severity control", 
        choices=['critical', 'high', 'medium', 'low', 'info', 'sla'], 
        required=False, default='info')
    parser.add_argument(
        '--push_to_jira', help="Push to Jira?", required=False, 
        type=bool, default=False)

    args = vars(parser.parse_args())

    # connection
    ssl_ca_cert = args["ssl_ca_cert"]
    host = args["host"]

    # auth
    api_token = args["api_token"]

    # project
    lead_testing = args["lead_testing"]
    product_type = args["product_type"]
    product_name = args["product_name"]
    product_description = args["product_description"]
    jira_project_key = args["jira_project_key"]
    engagement_name = args["engagement_name"]
    tags = args["tags"].split(',')
    
    # importing results
    file = args["file"]
    test_type_id = args["test_type_id"]
    scan_type = args["scan_type"]
    
    # controls
    control_level = args["control_level"]
    push_to_jira = args["push_to_jira"]
    
    api_client = reporting.get_api_client(host, api_token, ssl_ca_cert)
    user_id = reporting.get_user_id(api_client, lead_testing)
    test_type_obj = reporting.get_test_type(api_client, test_type_id)
    product_type_id = reporting.get_product_type_id(api_client, product_type)
    product_id = reporting.get_product_id(
        api_client, product_type_id, product_name, tags, product_description)
    engagement_id = reporting.get_engagement_id(
        api_client, product_id, user_id, engagement_name)
    test_id = reporting.get_test_id(
        api_client, engagement_id, test_type_obj.name, test_type_obj.id, 1)
    reporting.reimport(
        api_client, test_id, file, True, scan_type, push_to_jira)
    summary(api_client, test_id, control_level)

if __name__ == '__main__':
    main()

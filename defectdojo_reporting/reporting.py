from urllib.parse import urlparse, parse_qs
import defectdojo_api_swagger
from defectdojo_api_swagger.rest import ApiException
from datetime import datetime, timedelta
import os, sys
import argparse
import time

def get_api_client(host, api_token):
    # Configure API key authorization: api_key
    configuration = defectdojo_api_swagger.Configuration()
    configuration.api_key['Authorization'] = f'Token {host}'
    configuration.host = api_token
    
    return defectdojo_api_swagger.ApiClient(configuration)


def get_user_id(api_client, username):
    api_instance = defectdojo_api_swagger.UsersApi(api_client)
    users = api_instance.users_list(username=username)
    
    if users.count == 1:
        return users.results[0].id
    else:
        raise ValueError('User not found: ' + str(username))


def get_product_id(api_client, product_id):
    api_instance = defectdojo_api_swagger.ProductsApi(api_client)
    try:
        products = api_instance.products_read(id=product_id)
        return products.id
    except ApiException:
        raise ValueError('Product not found: ' + str(product_id))
    
def get_engagement_id(api_client, product_id, user_id, repo, branch):
    engagement_branch = f'{repo} ({branch})'
    api_instance = defectdojo_api_swagger.EngagementsApi(api_client)
    
    engagements = api_instance.engagements_list(
        name=engagement_branch,product=product_id)
    if engagements.count == 1 and \
        engagements.results[0].engagement_type == "CI/CD":   
        return engagements.results[0].id
    else:
        # No engagement found, so create a new one
        start_date = datetime.now()
        end_date = start_date + timedelta(days=10)
        engagement_description = "CI/CD Engagement created by CI/CD script"
        status = "In Progress"
        engagement_type = "CI/CD"

        data = defectdojo_api_swagger.Engagement(
            name=engagement_branch,
            engagement_type=engagement_type,
            product=product_id,
            lead=user_id, 
            status=status, 
            target_start=start_date.date(),
            target_end=end_date.date(), 
            branch_tag=branch, 
            description=engagement_description
        ) 
        engagement = api_instance.engagements_create(data)
        return engagement.id


def get_test_id(api_client, engagement_id, test_type_obj, environment):
    api_instance = defectdojo_api_swagger.TestsApi(api_client)
    tests = api_instance.tests_list(engagement=engagement_id, 
                                    title=test_type_obj.name)
    
    if tests.count == 1:   
        return tests.results[0].id
    else:
        # No test found, so create a new one
        target_start = datetime.now()
        target_end = target_start + timedelta(days=10)

        data = defectdojo_api_swagger.Test(
            title=test_type_obj.name, 
            engagement=engagement_id, 
            test_type=test_type_obj.id, 
            environment=environment, 
            target_start=target_start, 
            target_end=target_end
        )
        test = api_instance.tests_create(data)
        return test.id


def get_test_type(api_client, test_type_id):
    api_instance = defectdojo_api_swagger.TestTypesApi(api_client)
    try:
        test = api_instance.test_types_read(id=test_type_id)
        return test
    except ApiException:
        raise ValueError('Test Type not found: ' + str(test_type_id))


def reimport(api_client, test_id, file, active, test_type_obj, push_to_jira):
    date = datetime.now()

    api_instance = defectdojo_api_swagger.ReimportScanApi(api_client)

    scan = api_instance.reimport_scan_create(
        test=test_id,
        scan_type=test_type_obj.name,
        file=file,
        active=active,
        scan_date=date.date(),
        push_to_jira=push_to_jira
    )
    return scan

def list_findings(api_client, **kwargs):
    api_instance = defectdojo_api_swagger.FindingsApi(api_client)
    all_findings = []
    while True:
        findings = api_instance.findings_list(**kwargs)
        all_findings += findings.results
        if findings.next:
            kwargs['offset'] = parse_qs(urlparse(findings.next).query)['offset'][0]
            kwargs['limit'] = parse_qs(urlparse(findings.next).query)['limit'][0]
        else:
            break

    return all_findings

def sum_severity(findings):
    severity = [0,0,0,0,0]
    for finding in findings:
        if finding.severity == "Critical":
            severity[4] = severity[4] + 1
        if finding.severity == "High":
            severity[3] = severity[3] + 1
        if finding.severity == "Medium":
            severity[2] = severity[2] + 1
        if finding.severity == "Low":
            severity[1] = severity[1] + 1
        if finding.severity == "Info":
            severity[0] = severity[0] + 1

    return severity

def sum_severity_sla(findings):
    severity = [0,0,0,0,0]
    for finding in findings:
        if finding.sla_days_remaining < 0:
            if finding.severity == "Critical":
                severity[4] = severity[4] + 1
            if finding.severity == "High":
                severity[3] = severity[3] + 1
            if finding.severity == "Medium":
                severity[2] = severity[2] + 1
            if finding.severity == "Low":
                severity[1] = severity[1] + 1
            if finding.severity == "Info":
                severity[0] = severity[0] + 1

    return severity

def print_findings(findings):
    print("Critical: " + str(findings[4]))
    print("High: " + str(findings[3]))
    print("Medium: " + str(findings[2]))
    print("Low: " + str(findings[1]))
    print("Info: " + str(findings[0]))

def summary(api_client, test_id):
    total_findings = list_findings(
        api_client, test=test_id, duplicate=False, active=True, verified=True)
    duplicate_findings = list_findings(
        api_client, test=test_id, duplicate=True)
    findings_sla_overdue = [finding for finding in total_findings if finding.sla_days_remaining < 0]
    
    print("==============================================")
    print(f"Total Number of New Findings: {len(total_findings)}")
    print("==============================================")
    print_findings(sum_severity(total_findings))
    print("")
    print("==============================================")
    print(f"Total Number of Duplicate Findings: {len(duplicate_findings)}")
    print("==============================================")
    print_findings(sum_severity(duplicate_findings))
    print("")
    print(f"Total Number of Findings with SLA overdue: {len(findings_sla_overdue)}")
    print("==============================================")
    print_findings(sum_severity(findings_sla_overdue))
    print("")
    if len(findings_sla_overdue) > 0:
        print("Build Failed: SLA overdue :(")
    elif len(total_findings) > 0:
        print("Build Passed! But there issue to fix :/")
    else:
        print("Build Passed! :)")
    print("==============================================")



class Main:
    if __name__ == "__main__":
        parser = argparse.ArgumentParser(
            description='CI/CD integration for DefectDojo')
        parser.add_argument('--host', 
                            help="DefectDojo Hostname", 
                            required=True)
        parser.add_argument('--proxy', 
                            help="Proxy ex:localhost:8080", 
                            required=False, 
                            default=None)
        parser.add_argument('--api_token', 
                            help="API Key", 
                            required=True)
        parser.add_argument('--debug', 
                            help="Debug Mode", 
                            required=False)        
        parser.add_argument('--user', 
                            help="User", 
                            required=True)

        parser.add_argument('--branch_name', 
                            help="Reference to branch being scanned", 
                            required=True)        
        parser.add_argument('--product', 
                            help="DefectDojo Product ID", 
                            required=True, 
                            type=int)
        parser.add_argument('--repo', 
                            help="Repo Name", 
                            required=True)
        parser.add_argument('--push_to_jira', 
                            help="Push to Jira", 
                            required=False, 
                            type=bool, 
                            default=False)

        parser.add_argument('--file', 
                            help="Scanner file", 
                            required=True)
        parser.add_argument('--test_type', 
                            help="Type of scanner", 
                            required=True)
        
        args = vars(parser.parse_args())
        
        host = args["host"]
        api_token = args["api_token"]
        user = args["user"]
        proxy = args["proxy"]
        debug = args["debug"]
        
        product = args["product"]
        repo = args["repo"]
        branch_name = args["branch_name"]
        push_to_jira = args["push_to_jira"]
        test_type = args["test_type"]    
        file = args["file"]

        api_client = get_api_client(host, api_token)

        user_id = get_user_id(api_client, user)        
        test_type_obj = get_test_type(api_client, test_type)
        product_id = get_product_id(api_client, product)
        engagement_id = get_engagement_id(api_client, product_id, user_id, repo, branch_name)

        test_id = get_test_id(api_client, engagement_id, test_type_obj, 1)
        scan = reimport(api_client, test_id, file, True, test_type_obj.name, push_to_jira)
        summary(api_client, test_id)

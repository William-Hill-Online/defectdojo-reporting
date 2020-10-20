from urllib.parse import urlparse, parse_qs
import defectdojo_api_client
from defectdojo_api_client.rest import ApiException
from datetime import datetime, timedelta


def get_api_client(host, api_token, ssl_ca_cert):
    # Configure API key authorization: api_key
    configuration = defectdojo_api_client.Configuration(
        host=host, api_key={'api_key': f'Token {api_token}'}
    )
    configuration.ssl_ca_cert = ssl_ca_cert
    return defectdojo_api_client.ApiClient(configuration)


def get_user_id(api_client, username):
    api_instance = defectdojo_api_client.UsersApi(api_client)
    users = api_instance.users_list(username=username)

    if users.count == 1:
        return users.results[0].id
    else:
        raise ValueError('User not found: ' + str(username))


def get_product_type_id(api_client, team):
    api_instance = defectdojo_api_client.ProductTypesApi(api_client)

    product_types = api_instance.product_types_list(name=team)
    if product_types.count == 1:
        return product_types.results[0].id
    else:
        # No product type found, so create a new one
        data = defectdojo_api_client.ProductType(
            name=team
        )

        product_type = api_instance.product_types_create(data)
        return product_type.id


def get_product_id(api_client, prod_type, repo, tags):
    api_instance = defectdojo_api_client.ProductsApi(api_client)

    products = api_instance.products_list(name=repo)
    if products.count == 1:
        products.results[0].tags = list(set(products.results[0].tags + tags)) 
        products.results[0].prod_type = prod_type
        product = api_instance.products_partial_update(products.results[0].id, products.results[0])
        return products.results[0].id
    else:
        # No product found, so create a new one
        description = f'{repo}'
        data = defectdojo_api_client.Product(
            name=repo,
            description=description,
            prod_type=prod_type,
            tags=tags
        )

        product = api_instance.products_create(data)
        return product.id


def get_engagement_id(api_client, product_id, user_id, branch):
    api_instance = defectdojo_api_client.EngagementsApi(api_client)

    engagements = api_instance.engagements_list(
        name=branch, product=product_id)
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

        data = defectdojo_api_client.Engagement(
            name=branch,
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


def get_test_id(api_client, engagement_id, test_name, test_type_id, environment):
    api_instance = defectdojo_api_client.TestsApi(api_client)
    tests = api_instance.tests_list(engagement=engagement_id,
                                    title=test_name)

    if tests.count == 1:
        return tests.results[0].id
    else:
        # No test found, so create a new one
        target_start = datetime.now()
        target_end = target_start + timedelta(days=10)

        data = defectdojo_api_client.Test(
            title=test_name,
            engagement=engagement_id,
            test_type=test_type_id,
            environment=environment,
            target_start=target_start,
            target_end=target_end
        )

        test = api_instance.tests_create(data)
        return test.id


def get_test_type(api_client, test_type_id):
    api_instance = defectdojo_api_client.TestTypesApi(api_client)
    try:
        test = api_instance.test_types_read(id=test_type_id)
        return test
    except ApiException:
        raise ValueError('Test Type not found: ' + str(test_type_id))


def reimport(api_client, test_id, file, active, scan_type, push_to_jira):
    date = datetime.now()

    api_instance = defectdojo_api_client.ReimportScanApi(api_client)

    scan = api_instance.reimport_scan_create(
        test=test_id,
        scan_type=scan_type,
        file=file,
        active=active,
        scan_date=date.date(),
        push_to_jira=push_to_jira
    )
    return scan


def list_findings(api_client, **kwargs):
    api_instance = defectdojo_api_client.FindingsApi(api_client)
    all_findings = []
    while True:
        findings = api_instance.findings_list(**kwargs)
        all_findings += findings.results
        if findings.next:
            kwargs['offset'] = parse_qs(
                urlparse(findings.next).query)['offset'][0]
            kwargs['limit'] = parse_qs(
                urlparse(findings.next).query)['limit'][0]
        else:
            break

    return all_findings


def sum_severity(findings):
    severity = {
        'Critical': 0,
        'High': 0,
        'Medium': 0,
        'Low': 0,
        'Info': 0
    }
    for finding in findings:
        severity[finding.severity] += 1

    return severity
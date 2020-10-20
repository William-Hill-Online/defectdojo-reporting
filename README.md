# DefectDojo Reporting
Python Library to import results of security tools into DefectDojo and provide quality gate to use in CI

## Instalation

```
pip install git+https://github.com/William-Hill-Online/defectdojo-reporting.git
```

## Usage

### CLI parameters
| Param              | Description                         | Type                                         | Required | Example                                  |
|--------------------|-------------------------------------|----------------------------------------------|----------|------------------------------------------|
| host               | DefectDojo Hostname                 | string                                       | yes      | http://localhost:8080/api/v2             |
| api_token          | API Key                             | string                                       | yes      | 41f5776a19792fc0fd5e1ea5032d07e2fe4b20f6 |
| lead_testing       | Lead Testing                        | string                                       | yes      | gitlabci                                 |
| repo               | Repo Name                           | string                                       | yes      | appsec/repo-abc                          |
| tags               | Tags                                | string                                       | yes      | tagX, tagY                               |
| team               | Team                                | string                                       | yes      | appsec-team                              |
| branch_name        | Reference to branch being scanned   | string                                       | yes      | master                                   |
| file               | Findings file                       | string                                       | yes      | /tmp/ccvs.json                           |
| test_type_id       | Test Type ID                        | int                                          | yes      | 181                                      |
| scan_type          | Scan Type                           | string                                       | yes      | CCVS Report                              |
| control_level      | Minimum level of severity control   | enum(critical, high, medium, low, info, sla) | no       | medium                                   |
| push_to_jira       | Push to Jira?                       | bool                                         | no       | false                                    |
| ssl_ca_cert        | SSL CA Cert File                    | string                                       | yes      | /path/cert.pem                           |


### Using in CI to have Quality Gate

**Example of build failing because the mimimum control level is medium, and there are issues with level medium and high**
```
defectdojo-reporting --host=http://localhost:8080/api/v2 --api_token=41f5776a19792fc0fd5e1ea5032d07e2fe4b20f6 --lead_testing=gitlabci \
--branch_name=master --repo="appsec/repo-abc" --file=/tmp/ccvs.json --tags=tag1,tag2 --team=appsec --test_type_id=181 --control_level=medium \
--ssl_ca_cert=""
=============================================================
Summary
=============================================================
Dashboard: http://localhost:8080/test/90
Severity Control: MEDIUM

=============================================================
Total number of findings: 227
=============================================================
Critical: 0
High: 28
Medium: 26
Low: 30
Info: 143

=============================================================
Total number of findings with control severity violated: 54
=============================================================
Critical: 0
High: 28
Medium: 26
Low: 0
Info: 0

Build Failed! :(
============================================================
```

**Example of build failing with warning because there no critical issues, but there are issues to fix**
```
defectdojo-reporting --host=http://localhost:8080/api/v2 --api_token=41f5776a19792fc0fd5e1ea5032d07e2fe4b20f6 --lead_testing=gitlabci \
--branch_name=master --repo="appsec/repo-abc" --file=/tmp/ccvs.json --tags=tag1,tag2 --team=appsec --test_type_id=181 --control_level=critical \
--ssl_ca_cert=""
=============================================================
Summary
=============================================================
Dashboard: http://localhost:8080/test/90
Severity Control: CRITICAL

=============================================================
=============================================================
Total number of findings: 227
=============================================================
Critical: 0
High: 28
Medium: 26
Low: 30
Info: 143

Build Passed! But there are issues to fix yet :/
=============================================================
```

**Example of build passing with warning because there no SLAs overdue, but there are issues to fix**
```
defectdojo-reporting --host=http://localhost:8080/api/v2 --api_token=41f5776a19792fc0fd5e1ea5032d07e2fe4b20f6 --lead_testing=gitlabci \
--branch_name=master --repo="appsec/repo-abc" --file=/tmp/ccvs.json --tags=tag1,tag2 --team=appsec --test_type_id=181 --control_level=sla \
--ssl_ca_cert=""
=============================================================
Summary
=============================================================
Dashboard: http://localhost:8080/test/90
Severity Control: SLA

=============================================================
=============================================================
Total number of findings: 227
=============================================================
Critical: 0
High: 28
Medium: 26
Low: 30
Info: 143

Build Passed! But there are issues to fix yet :/
=============================================================
```

**Example of build failing because there are SLAs overdue**
```
defectdojo-reporting --host=http://localhost:8080/api/v2 --api_token=41f5776a19792fc0fd5e1ea5032d07e2fe4b20f6 --lead_testing=gitlabci \
--branch_name=master --repo="appsec/repo-abc" --file=/tmp/ccvs.json --tags=tag1,tag2 --team=appsec --test_type_id=181 --control_level=sla \
--ssl_ca_cert=""
=============================================================
Summary
=============================================================
Dashboard: http://localhost:8080/test/90
Severity Control: SLA

=============================================================
=============================================================
Total number of findings: 227
=============================================================
Critical: 0
High: 28
Medium: 26
Low: 30
Info: 143

=============================================================
Total number of findings with SLA overdue: 28
=============================================================
Critical: 0
High: 28
Medium: 0
Low: 0
Info: 0

Build Failed! :(
=============================================================
```
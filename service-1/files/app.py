import json
import subprocess
from prometheus_client import CollectorRegistry, Counter, Gauge, push_to_gateway
import os

#####################
# Set these values  #
#####################

# The name of this integration. It will form part of the metric name.
INTEGRATION_NAME = "tracetest"

# Your Prometheus Push Gateway endpoint
# eg. "prometheus-pushgateway.monitoring.svc.cluster.local:9091"
PROM_GATEWAY = "prometheus-pushgateway.monitoring.svc.cluster.local:9091"

############################
# End configurable values  #
############################

# These variables are passed to job-executor-service automatically on job startup
# So you can assume they're available
KEPTN_PROJECT = os.getenv("KEPTN_PROJECT", "NULL")
KEPTN_SERVICE = os.getenv("KEPTN_SERVICE", "NULL")
KEPTN_STAGE = os.getenv("KEPTN_STAGE", "NULL")

PROM_LABELS = [
    "ci_platform",
    "keptn_project",
    "keptn_service",
    "keptn_stage"
]

########################
# Do your work here... #
########################
test_result = subprocess.run([
    'tracetest',
    '--config',
    '/keptn/files/config.yml',
    'test',
    'run',
    '--definition',
    '/keptn/files/testdef.yaml',
    '--wait-for-result'
    ], capture_output=True)

test_result_json = json.loads(test_result.stdout)

print(test_result_json)

#####################
# v2 Logic:
# if .testRun.result.allPassed is true then all checks have passed
# otherwise some tests failed
#####################
if 'allPassed' in test_result_json['testRun']['result']:
    print("All tests passed...")
else:
    print("Some tests failed...")

assertion_count = len(test_result_json['testRun']['result']['results'])
check_count = 0

for assertion in test_result_json['testRun']['result']['results']:
    check_count_for_this_assertion = len(assertion['results'])
    check_count += check_count_for_this_assertion

print(f"{assertion_count} assertions defined...")
print(f"{check_count} checks defined...")

##########################
# PUSH METRICS TO PROM   #
##########################
reg = CollectorRegistry()

# Create assertionCount Prom metric
metric_name = "assertionCount"
g = Gauge(name=f"keptn_{INTEGRATION_NAME}_{metric_name}", documentation='', registry=reg, labelnames=PROM_LABELS)
# Set the labels and values
g.labels(
  ci_platform="keptn",
  keptn_project=KEPTN_PROJECT,
  keptn_service=KEPTN_SERVICE,
  keptn_stage=KEPTN_STAGE
).set(assertion_count)

# Create checkCount Prom metric
metric_name = "checkCount"
g = Gauge(name=f"keptn_{INTEGRATION_NAME}_{metric_name}", documentation='', registry=reg, labelnames=PROM_LABELS)
# Set the labels and values
g.labels(
  ci_platform="keptn",
  keptn_project=KEPTN_PROJECT,
  keptn_service=KEPTN_SERVICE,
  keptn_stage=KEPTN_STAGE
).set(check_count)

# Send the metrics to Prometheus Push Gateway
push_to_gateway(gateway=PROM_GATEWAY,job=f"job-executor-service", registry=reg)
    
exit()

#####################
# v1 Logic: Parse the results and fail the Keptn task if ALL tracetest checks FAIL
# Cause the task to fail simply by outputting a non-zero exit code
# According to a discussion on discord with schoren, apparently this is even easier:
# if .testRun.result.allPassed is true then all checks have passed
# if .testRun.result.allPassed is missing or false, we can assume some checks have failed
#####################

check_results = []

for selector_result in test_result_json['testRun']['result']['results']:

    selector_query = selector_result['selector']['query']
    #print(f"Got selector_query: {selector_query}")

    for assertion_result in selector_result['results']:

        assertion_name = assertion_result['assertion']['attribute']
        if "allPassed" in assertion_result:
            #print(f"Assertion: {assertion_name} passed for selector: {selector_query}")
            check_results.append({
                "name": assertion_name,
                "selector": selector_query,
                "status": "Pass"
            })
        else:
            #print(f"Assertion: {assertion_name} failed for selector: {selector_query}")
            check_results.append({
                "name": assertion_name,
                "selector": selector_query,
                "status": "Fail"
            })

# Output Results for Checks.
passed_checks = sum(1 for check in check_results if check['status'] == "Pass")
failed_checks = sum(1 for check in check_results if check['status'] == "Fail")
pass_percentage = round(passed_checks / len(check_results) * 100)

print(f"{passed_checks} checks passed")
print(f"{failed_checks} checks failed")
print(f"Pass percentage: {pass_percentage}%")

#for check in check_results:
#    print(f"Assertion: {check['name']} for selector: {check['selector']} status: {check['status']}")

#if pass_percentage == 0:
#    print("-------------")
#    print("No tests passed, failing the task...")
    # If this script exits with a non-zero exit code, the task will fail as desired
#    exit(1)

#print(check_results)

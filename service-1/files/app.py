import json
import subprocess
from prometheus_client import CollectorRegistry, Counter, Gauge, push_to_gateway
import os
import sys

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

specification_count = 0
assertion_count = 0
passed_assertions = 0
failed_assertions = 0
pass_percentage = 0

def push_to_prometheus():
    ##########################
    # PUSH METRICS TO PROM   #
    ##########################
    reg = CollectorRegistry()

    # Create assertionCount Prom metric
    metric_name = "specificationCount"
    g = Gauge(name=f"keptn_{INTEGRATION_NAME}_{metric_name}", documentation='', registry=reg, labelnames=PROM_LABELS)
    # Set the labels and values
    g.labels(
      ci_platform="keptn",
      keptn_project=KEPTN_PROJECT,
      keptn_service=KEPTN_SERVICE,
      keptn_stage=KEPTN_STAGE
    ).set(specification_count)

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

    # Create passedAssertionCount Prom metric
    metric_name = "passedAssertionCount"
    g = Gauge(name=f"keptn_{INTEGRATION_NAME}_{metric_name}", documentation='', registry=reg, labelnames=PROM_LABELS)
    # Set the labels and values
    g.labels(
      ci_platform="keptn",
      keptn_project=KEPTN_PROJECT,
      keptn_service=KEPTN_SERVICE,
      keptn_stage=KEPTN_STAGE
    ).set(passed_assertions)

    # Create failedAssertionCount Prom metric
    metric_name = "failedAssertionCount"
    g = Gauge(name=f"keptn_{INTEGRATION_NAME}_{metric_name}", documentation='', registry=reg, labelnames=PROM_LABELS)
    # Set the labels and values
    g.labels(
      ci_platform="keptn",
      keptn_project=KEPTN_PROJECT,
      keptn_service=KEPTN_SERVICE,
      keptn_stage=KEPTN_STAGE
    ).set(failed_assertions)

    # This calculation could be done in Prom
    # But for convenience, push as a metric
    # Create passedAssertionPercentage Prom metric
    metric_name = "passedAssertionPercentage"
    g = Gauge(name=f"keptn_{INTEGRATION_NAME}_{metric_name}", documentation='', registry=reg, labelnames=PROM_LABELS)
    # Set the labels and values
    g.labels(
      ci_platform="keptn",
      keptn_project=KEPTN_PROJECT,
      keptn_service=KEPTN_SERVICE,
      keptn_stage=KEPTN_STAGE
    ).set(pass_percentage)

    # Send the metrics to Prometheus Push Gateway
    push_to_gateway(gateway=PROM_GATEWAY,job=f"job-executor-service", registry=reg)

def process_tracetest_json():
    if 'allPassed' in test_result_json['testRun']['result']:
        print("All test specifications passed...")
    else:
        print("Some test specifications failed...")
        
    specification_count = len(test_result_json['testRun']['result']['results'])

    for specification in test_result_json['testRun']['result']['results']:
        assertion_count_for_this_specification = len(specification['results'])
        assertion_count += assertion_count_for_this_specification

    print(f"{specification_count} specifications defined...")
    print(f"{assertion_count} assertions defined...")

    assertion_results = []

    for selector_result in test_result_json['testRun']['result']['results']:
        selector_query = selector_result['selector']['query']
        #print(f"Got selector_query: {selector_query}")

    for specification_result in selector_result['results']:
        assertion_name = specification_result['assertion']['attribute']
        if "allPassed" in specification_result:
            assertion_results.append({
                "name": assertion_name,
                "selector": selector_query,
                "status": "Pass"
            })
        else:
            assertion_results.append({
                "name": assertion_name,
                "selector": selector_query,
                "status": "Fail"
            })

    # Output Results for assertions.
    passed_assertions = sum(1 for assertion in assertion_results if assertion['status'] == "Pass")
    failed_assertions = sum(1 for assertion in assertion_results if assertion['status'] == "Fail")
    pass_percentage = round(passed_assertions / len(assertion_results) * 100)

    print(f"{passed_assertions} assertions passed")
    print(f"{failed_assertions} assertions failed")
    print(f"Pass percentage: {pass_percentage}%")


# Run tracetest and wait for results...
test_result = subprocess.run([
    'tracetest',
    'test',
    'run',
    '--config',
    '/keptn/files/config.yml',
    '--definition',
    '/keptn/files/testdef.yaml',
    '--wait-for-result',
    '-o',
    'json'
    ], capture_output=True)

test_result_json = json.loads(test_result.stdout)

print(test_result_json)

######################
# If .testRun.state == "FAILED"
# Something went wrong
# So all metrics should be zero
# and return immediately
#####################
if test_result_json['testRun']['state'] == "FAILED":
    print(f"tracetest failed because: {test_result_json['testRun']['lastErrorState']}")
    print("Pushing metrics all set to 0 to prom and exiting cleanly. Please investigate")
    push_to_prometheus()
    exit()


process_tracetest_json()

# Push metrics to Prometheus
push_to_prometheus()

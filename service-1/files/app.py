import json
import subprocess

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

###################
# v2 logic
# As above, check `.testRun.result.allPassed` if true, assume all checks passed
# else assume some checks failed

#all_tests_passed = test_result_json['testRun']['result']['allPassed']
#print(f"All tests passed: {all_tests_passed}")

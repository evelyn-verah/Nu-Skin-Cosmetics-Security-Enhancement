import subprocess
import sys
from pathlib import Path

RESULTS_DIR = Path('results')
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

def run_pytest(target: str, junit_name: str) -> int:
    """Run pytest on a target path and save a JUnit XML report."""
    print(f'Running tests in: {target}')
    cmd = [
        sys.executable, '-m', 'pytest',
        '-q',
        target,
        f'--junitxml={RESULTS_DIR / junit_name}',
        '--disable-warnings',
        '--maxfail=1'
    ]
    return subprocess.call(cmd)

def main():
    rc_ui = run_pytest('tests/ui_tests', 'junit_ui.xml')
    rc_api = run_pytest('tests/api_tests', 'junit_api.xml')
    rc_reg = run_pytest('tests/regression_suite', 'junit_regression.xml')

    rc = rc_ui or rc_api or rc_reg
    if rc != 0:
        print('Some tests failed. See results/*.xml for details.')
    else:
        print('All test suites passed.')
    sys.exit(rc)

if __name__ == '__main__':
    main()

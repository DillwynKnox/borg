# Simple DIY branch coverage

coverage = {}

def mark(branch_id):
    coverage[branch_id] = True

def report():
    print("\n=== DIY COVERAGE REPORT ===")
    for k in sorted(coverage):
        print(f"Branch {k}: taken")
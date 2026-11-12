from core.planner import make_plan

tests = [
    ("Find all PDF files related to cybersecurity", "search"),
    ("Sort my assignments into folders by subject", "organize"),
    ("Show me copies of the same file", "find_duplicates"),
    ("What is this research paper about?", "summarize"),
    ("My files have names like doc1 and final_final, fix them", "rename"),
    ("Where is my networking presentation?", "search"),
]

passed = 0
for instruction, expected in tests:
    plan = make_plan(instruction)
    ok = plan["intent"] == expected
    passed += ok
    print(f"{'PASS' if ok else 'FAIL'} | {instruction}\n       -> {plan}\n")

print(f"{passed}/{len(tests)} correct")
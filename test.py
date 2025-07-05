from langgraph_flow import app   # your compiled StateGraph from langgraph_flow.py

def main():
    # 1. Start with an empty state (or seed your repo/text if you made it dynamic)
    initial_state = {}

    # 2. Invoke the graph synchronously
    final_state = app.invoke(initial_state)

    # 3. Print out the summary
    print("\n=== Weekly Dev Report Summary ===\n")
    print(final_state.get("summary", "No summary generated"))

if __name__ == "__main__":
    main()
    
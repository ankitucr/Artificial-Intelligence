import sys
import json
import os

# Reroute standard prints to stderr so Node.js JSON parsing doesn't crash
original_stdout = sys.stdout
sys.stdout = sys.stderr

from pika_core import PikaNeuralCore


def send_to_node(data_dict):
    sys.stdout = original_stdout
    print(json.dumps(data_dict))
    sys.stdout = sys.stderr


def find_neuron(core, neuron_id):
    return next((n for n in core.neurons if n.get("id") == neuron_id), None)


def main():
    try:
        input_json = sys.argv[1]
        data = json.loads(input_json)
        action = data.get("action")

        # Naya Neural Core jagao — har action ke liye same core instance.
        # skills_file wired in so error-fixing ALSO auto-checks the grown
        # skill library before hitting any API (not just the evolution loop).
        skills_file = os.path.join(os.path.dirname(__file__), "..", "skills", "pika_skills.py")
        core = PikaNeuralCore(skills_file=skills_file)

        if action == "fix_error":
            file_path = data.get("file_path")
            func_name = data.get("function_name")
            error_log = data.get("error_log")

            result = core.analyze_and_fix(file_path, func_name, error_log)
            send_to_node(result)

        elif action == "report_outcome":
            # Auto-runner ye batata hai ki apply kiya gaya fix asal me kaam kiya ya nahi.
            # Yehi se Pika ka reinforcement learning hota hai.
            neuron_id = data.get("neuron_id")
            success = bool(data.get("success"))

            neuron = find_neuron(core, neuron_id)
            if neuron is None:
                send_to_node({"status": "error", "message": f"No neuron found with id {neuron_id}"})
                return

            core.record_outcome(neuron, success=success)
            send_to_node({
                "status": "success",
                "neuron_id": neuron_id,
                "success_count": neuron.get("success_count", 0),
                "fail_count": neuron.get("fail_count", 0),
            })

        elif action == "consolidate":
            # Periodic brain cleanup — duplicate/failing neurons hatao
            result = core.consolidate()
            send_to_node({"status": "success", **result})

        elif action == "report":
            stats = core.report()
            send_to_node({"status": "success", "stats": stats, "neuron_count": len(core.neurons)})

        else:
            send_to_node({"status": "error", "message": "Unknown Action Command"})

    except Exception as e:
        send_to_node({"status": "critical_bridge_error", "error": str(e)})


if __name__ == "__main__":
    main()

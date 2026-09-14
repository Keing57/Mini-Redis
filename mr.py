import sys

storage = {}

def execute_command(command_line):
    parts = command_line.strip().split()
    if not parts:
        return ""
    
    cmd = parts[0].upper()
    
    if cmd == "SET":
        if len(parts) < 3:
            return "ERR syntax error: SET key value"
        key = parts[1]
        val = " ".join(parts[2:])
        storage[key] = val
        return "OK"
    elif cmd == "GET":
        if len(parts) < 2:
            return "ERR syntax error: GET key"
        key = parts[1]
        return storage.get(key, "(nil)")
    elif cmd == "DEL":
        if len(parts) < 2:
            return "ERR syntax error: DEL key"
        key = parts[1]
        if key in storage:
            del storage[key]
            return "(integer) 1"
        return "(integer) 0"
    elif cmd == "EXISTS":
        if len(parts) < 2:
            return "ERR syntax error: EXISTS key"
        key = parts[1]
        if key in storage:
            return "(integer) 1"
        return "(integer) 0"
    elif cmd == "KEYS":
        keys = list(storage.keys())
        if not keys:
            return "(empty list or set)"
        return "\n".join(f"{i+1}) \"{k}\"" for i, k in enumerate(keys))
    elif cmd == "INCR":
        if len(parts) < 2:
            return "ERR syntax error: INCR key"
        key = parts[1]
        current = storage.get(key, "0")
        try:
            val = int(current) + 1
            storage[key] = str(val)
            return f"(integer) {val}"
        except ValueError:
            return "ERR value is not an integer or out of range"
    elif cmd == "DECR":
        if len(parts) < 2:
            return "ERR syntax error: DECR key"
        key = parts[1]
        current = storage.get(key, "0")
        try:
            val = int(current) - 1
            storage[key] = str(val)
            return f"(integer) {val}"
        except ValueError:
            return "ERR value is not an integer or out of range"
    elif cmd == "FLUSHALL":
        storage.clear()
        return "OK"
    elif cmd == "HELP":
        commands = [
            "SET key value - Store string value",
            "GET key - Retrieve value by key",
            "DEL key - Delete a key",
            "EXISTS key - Check if key exists",
            "KEYS - List all keys",
            "INCR key - Increment integer value",
            "DECR key - Decrement integer value",
            "FLUSHALL - Clear all stored data",
            "HELP - Show manual",
            "QUIT - Exit server"
        ]
        return "\n".join(commands)
    elif cmd == "QUIT":
        sys.exit(0)
    else:
        return f"ERR unknown command '{cmd}'"

def main():
    while True:
        try:
            line = input("miniredis> ")
            response = execute_command(line)
            if response:
                print(response)
        except (EOFError, KeyboardInterrupt):
            break

if __name__ == "__main__":
    main()
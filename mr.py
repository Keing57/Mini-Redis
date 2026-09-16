import sys
import time

class StorageEngine:
    def __init__(self):
        self.storage = {}
        self.expires = {}

    def _check_expired(self, key):
        if key in self.expires:
            if time.time() >= self.expires[key]:
                if key in self.storage:
                    del self.storage[key]
                del self.expires[key]
                return True
        return False

    def execute(self, command_line):
        parts = command_line.strip().split()
        if not parts:
            return ""
        
        cmd = parts[0].upper()
        
        if cmd == "SET":
            if len(parts) < 3:
                return "ERR syntax error: SET key value"
            key = parts[1]
            val = " ".join(parts[2:])
            self.storage[key] = val
            if key in self.expires:
                del self.expires[key]
            return "OK"
        elif cmd == "GET":
            if len(parts) < 2:
                return "ERR syntax error: GET key"
            key = parts[1]
            if self._check_expired(key):
                return "(nil)"
            return self.storage.get(key, "(nil)")
        elif cmd == "DEL":
            if len(parts) < 2:
                return "ERR syntax error: DEL key"
            key = parts[1]
            self._check_expired(key)
            existed = False
            if key in self.storage:
                del self.storage[key]
                existed = True
            if key in self.expires:
                del self.expires[key]
            return "(integer) 1" if existed else "(integer) 0"
        elif cmd == "EXISTS":
            if len(parts) < 2:
                return "ERR syntax error: EXISTS key"
            key = parts[1]
            if self._check_expired(key):
                return "(integer) 0"
            if key in self.storage:
                return "(integer) 1"
            return "(integer) 0"
        elif cmd == "KEYS":
            for k in list(self.storage.keys()):
                self._check_expired(k)
            keys = list(self.storage.keys())
            if not keys:
                return "(empty list or set)"
            return "\n".join(f"{i+1}) \"{k}\"" for i, k in enumerate(keys))
        elif cmd == "EXPIRE":
            if len(parts) < 3:
                return "ERR syntax error: EXPIRE key seconds"
            key = parts[1]
            if self._check_expired(key) or key not in self.storage:
                return "(integer) 0"
            try:
                seconds = int(parts[2])
                if seconds <= 0:
                    if key in self.storage:
                        del self.storage[key]
                    if key in self.expires:
                        del self.expires[key]
                    return "(integer) 1"
                self.expires[key] = time.time() + seconds
                return "(integer) 1"
            except ValueError:
                return "ERR value is not an integer or out of range"
        elif cmd == "TTL":
            if len(parts) < 2:
                return "ERR syntax error: TTL key"
            key = parts[1]
            if self._check_expired(key) or key not in self.storage:
                return "(integer) -2"
            if key not in self.expires:
                return "(integer) -1"
            remaining = int(self.expires[key] - time.time())
            if remaining < 0:
                self._check_expired(key)
                return "(integer) -2"
            return f"(integer) {remaining}"
        elif cmd == "INCR":
            if len(parts) < 2:
                return "ERR syntax error: INCR key"
            key = parts[1]
            self._check_expired(key)
            current = self.storage.get(key, "0")
            try:
                val = int(current) + 1
                self.storage[key] = str(val)
                return f"(integer) {val}"
            except ValueError:
                return "ERR value is not an integer or out of range"
        elif cmd == "DECR":
            if len(parts) < 2:
                return "ERR syntax error: DECR key"
            key = parts[1]
            self._check_expired(key)
            current = self.storage.get(key, "0")
            try:
                val = int(current) - 1
                self.storage[key] = str(val)
                return f"(integer) {val}"
            except ValueError:
                return "ERR value is not an integer or out of range"
        elif cmd == "FLUSHALL":
            self.storage.clear()
            self.expires.clear()
            return "OK"
        elif cmd == "HELP":
            commands = [
                "SET key value - Store string value",
                "GET key - Retrieve value by key",
                "DEL key - Delete a key",
                "EXISTS key - Check if key exists",
                "KEYS - List all keys",
                "EXPIRE key seconds - Set timeout on a key",
                "TTL key - Get remaining time to live",
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
    engine = StorageEngine()
    while True:
        try:
            line = input("miniredis> ")
            response = engine.execute(line)
            if response:
                print(response)
        except (EOFError, KeyboardInterrupt):
            break

if __name__ == "__main__":
    main()
import sys
import time
import threading

class StorageEngine:
    def __init__(self):
        self.storage = {}
        self.expires = {}
        self.lock = threading.Lock()
        self.running = True
        self.cleaner_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self.cleaner_thread.start()

    def _cleanup_loop(self):
        while self.running:
            time.sleep(1)
            with self.lock:
                now = time.time()
                expired_keys = [k for k, exp in self.expires.items() if now >= exp]
                for k in expired_keys:
                    self.storage.pop(k, None)
                    self.expires.pop(k, None)

    def _check_expired(self, key):
        if key in self.expires:
            if time.time() >= self.expires[key]:
                self.storage.pop(key, None)
                self.expires.pop(key, None)
                return True
        return False

    def execute(self, command_line):
        parts = command_line.strip().split()
        if not parts:
            return ""
        
        cmd = parts[0].upper()
        
        with self.lock:
            if cmd == "SET":
                if len(parts) < 3:
                    return "ERR syntax error: SET key value"
                key = parts[1]
                val = " ".join(parts[2:])
                self.storage[key] = val
                self.expires.pop(key, None)
                return "OK"
            elif cmd == "SETEX":
                if len(parts) < 4:
                    return "ERR syntax error: SETEX key seconds value"
                key = parts[1]
                try:
                    seconds = int(parts[2])
                    if seconds <= 0:
                        return "ERR invalid expire time in setex"
                    val = " ".join(parts[3:])
                    self.storage[key] = val
                    self.expires[key] = time.time() + seconds
                    return "OK"
                except ValueError:
                    return "ERR value is not an integer or out of range"
            elif cmd == "GET":
                if len(parts) < 2:
                    return "ERR syntax error: GET key"
                key = parts[1]
                if self._check_expired(key):
                    return "(nil)"
                if key not in self.storage:
                    return "(nil)"
                if not isinstance(self.storage[key], str):
                    return "WRONGTYPE Operation against a key holding the wrong kind of value"
                return self.storage[key]
            elif cmd == "DEL":
                if len(parts) < 2:
                    return "ERR syntax error: DEL key"
                key = parts[1]
                self._check_expired(key)
                existed = False
                if key in self.storage:
                    del self.storage[key]
                    existed = True
                self.expires.pop(key, None)
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
                        self.storage.pop(key, None)
                        self.expires.pop(key, None)
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
                if not isinstance(current, str):
                    return "WRONGTYPE Operation against a key holding the wrong kind of value"
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
                if not isinstance(current, str):
                    return "WRONGTYPE Operation against a key holding the wrong kind of value"
                try:
                    val = int(current) - 1
                    self.storage[key] = str(val)
                    return f"(integer) {val}"
                except ValueError:
                    return "ERR value is not an integer or out of range"
            elif cmd == "LPUSH":
                if len(parts) < 3:
                    return "ERR syntax error: LPUSH key value [value ...]"
                key = parts[1]
                self._check_expired(key)
                if key in self.storage and not isinstance(self.storage[key], list):
                    return "WRONGTYPE Operation against a key holding the wrong kind of value"
                if key not in self.storage:
                    self.storage[key] = []
                for val in parts[2:]:
                    self.storage[key].insert(0, val)
                return f"(integer) {len(self.storage[key])}"
            elif cmd == "RPUSH":
                if len(parts) < 3:
                    return "ERR syntax error: RPUSH key value [value ...]"
                key = parts[1]
                self._check_expired(key)
                if key in self.storage and not isinstance(self.storage[key], list):
                    return "WRONGTYPE Operation against a key holding the wrong kind of value"
                if key not in self.storage:
                    self.storage[key] = []
                for val in parts[2:]:
                    self.storage[key].append(val)
                return f"(integer) {len(self.storage[key])}"
            elif cmd == "LRANGE":
                if len(parts) < 4:
                    return "ERR syntax error: LRANGE key start stop"
                key = parts[1]
                if self._check_expired(key) or key not in self.storage:
                    return "(empty list or set)"
                if not isinstance(self.storage[key], list):
                    return "WRONGTYPE Operation against a key holding the wrong kind of value"
                try:
                    start = int(parts[2])
                    stop = int(parts[3])
                except ValueError:
                    return "ERR value is not an integer or out of range"
                lst = self.storage[key]
                n = len(lst)
                if start < 0:
                    start = max(0, n + start)
                if stop < 0:
                    stop = n + stop
                if start > stop or start >= n:
                    return "(empty list or set)"
                stop = min(stop, n - 1)
                sub = lst[start:stop + 1]
                if not sub:
                    return "(empty list or set)"
                return "\n".join(f"{i+1}) \"{item}\"" for i, item in enumerate(sub))
            elif cmd == "LPOP":
                if len(parts) < 2:
                    return "ERR syntax error: LPOP key"
                key = parts[1]
                if self._check_expired(key) or key not in self.storage:
                    return "(nil)"
                if not isinstance(self.storage[key], list):
                    return "WRONGTYPE Operation against a key holding the wrong kind of value"
                lst = self.storage[key]
                if not lst:
                    return "(nil)"
                val = lst.pop(0)
                if not lst:
                    del self.storage[key]
                    self.expires.pop(key, None)
                return f"\"{val}\""
            elif cmd == "RPOP":
                if len(parts) < 2:
                    return "ERR syntax error: RPOP key"
                key = parts[1]
                if self._check_expired(key) or key not in self.storage:
                    return "(nil)"
                if not isinstance(self.storage[key], list):
                    return "WRONGTYPE Operation against a key holding the wrong kind of value"
                lst = self.storage[key]
                if not lst:
                    return "(nil)"
                val = lst.pop()
                if not lst:
                    del self.storage[key]
                    self.expires.pop(key, None)
                return f"\"{val}\""
            elif cmd == "LLEN":
                if len(parts) < 2:
                    return "ERR syntax error: LLEN key"
                key = parts[1]
                if self._check_expired(key) or key not in self.storage:
                    return "(integer) 0"
                if not isinstance(self.storage[key], list):
                    return "WRONGTYPE Operation against a key holding the wrong kind of value"
                return f"(integer) {len(self.storage[key])}"
            elif cmd == "HSET":
                if len(parts) < 4:
                    return "ERR syntax error: HSET key field value"
                key = parts[1]
                field = parts[2]
                val = " ".join(parts[3:])
                self._check_expired(key)
                if key in self.storage and not isinstance(self.storage[key], dict):
                    return "WRONGTYPE Operation against a key holding the wrong kind of value"
                if key not in self.storage:
                    self.storage[key] = {}
                is_new = 1 if field not in self.storage[key] else 0
                self.storage[key][field] = val
                return f"(integer) {is_new}"
            elif cmd == "HGET":
                if len(parts) < 3:
                    return "ERR syntax error: HGET key field"
                key = parts[1]
                field = parts[2]
                if self._check_expired(key) or key not in self.storage:
                    return "(nil)"
                if not isinstance(self.storage[key], dict):
                    return "WRONGTYPE Operation against a key holding the wrong kind of value"
                return f"\"{self.storage[key][field]}\"" if field in self.storage[key] else "(nil)"
            elif cmd == "HDEL":
                if len(parts) < 3:
                    return "ERR syntax error: HDEL key field [field ...]"
                key = parts[1]
                if self._check_expired(key) or key not in self.storage:
                    return "(integer) 0"
                if not isinstance(self.storage[key], dict):
                    return "WRONGTYPE Operation against a key holding the wrong kind of value"
                deleted = 0
                for f in parts[2:]:
                    if f in self.storage[key]:
                        del self.storage[key][f]
                        deleted += 1
                if not self.storage[key]:
                    del self.storage[key]
                    self.expires.pop(key, None)
                return f"(integer) {deleted}"
            elif cmd == "HGETALL":
                if len(parts) < 2:
                    return "ERR syntax error: HGETALL key"
                key = parts[1]
                if self._check_expired(key) or key not in self.storage:
                    return "(empty list or set)"
                if not isinstance(self.storage[key], dict):
                    return "WRONGTYPE Operation against a key holding the wrong kind of value"
                d = self.storage[key]
                if not d:
                    return "(empty list or set)"
                res = []
                idx = 1
                for f, v in d.items():
                    res.append(f"{idx}) \"{f}\"")
                    res.append(f"{idx+1}) \"{v}\"")
                    idx += 2
                return "\n".join(res)
            elif cmd == "SADD":
                if len(parts) < 3:
                    return "ERR syntax error: SADD key member [member ...]"
                key = parts[1]
                self._check_expired(key)
                if key in self.storage and not isinstance(self.storage[key], set):
                    return "WRONGTYPE Operation against a key holding the wrong kind of value"
                if key not in self.storage:
                    self.storage[key] = set()
                added = 0
                for member in parts[2:]:
                    if member not in self.storage[key]:
                        self.storage[key].add(member)
                        added += 1
                return f"(integer) {added}"
            elif cmd == "SMEMBERS":
                if len(parts) < 2:
                    return "ERR syntax error: SMEMBERS key"
                key = parts[1]
                if self._check_expired(key) or key not in self.storage:
                    return "(empty list or set)"
                if not isinstance(self.storage[key], set):
                    return "WRONGTYPE Operation against a key holding the wrong kind of value"
                members = list(self.storage[key])
                if not members:
                    return "(empty list or set)"
                return "\n".join(f"{i+1}) \"{m}\"" for i, m in enumerate(members))
            elif cmd == "SREM":
                if len(parts) < 3:
                    return "ERR syntax error: SREM key member [member ...]"
                key = parts[1]
                if self._check_expired(key) or key not in self.storage:
                    return "(integer) 0"
                if not isinstance(self.storage[key], set):
                    return "WRONGTYPE Operation against a key holding the wrong kind of value"
                removed = 0
                for member in parts[2:]:
                    if member in self.storage[key]:
                        self.storage[key].remove(member)
                        removed += 1
                if not self.storage[key]:
                    del self.storage[key]
                    self.expires.pop(key, None)
                return f"(integer) {removed}"
            elif cmd == "SISMEMBER":
                if len(parts) < 3:
                    return "ERR syntax error: SISMEMBER key member"
                key = parts[1]
                if self._check_expired(key) or key not in self.storage:
                    return "(integer) 0"
                if not isinstance(self.storage[key], set):
                    return "WRONGTYPE Operation against a key holding the wrong kind of value"
                return "(integer) 1" if parts[2] in self.storage[key] else "(integer) 0"
            elif cmd == "SCARD":
                if len(parts) < 2:
                    return "ERR syntax error: SCARD key"
                key = parts[1]
                if self._check_expired(key) or key not in self.storage:
                    return "(integer) 0"
                if not isinstance(self.storage[key], set):
                    return "WRONGTYPE Operation against a key holding the wrong kind of value"
                return f"(integer) {len(self.storage[key])}"
            elif cmd == "FLUSHALL":
                self.storage.clear()
                self.expires.clear()
                return "OK"
            elif cmd == "HELP":
                commands = [
                    "SET key value - Store string value",
                    "SETEX key seconds value - Store string value with expiration",
                    "GET key - Retrieve value by key",
                    "DEL key - Delete a key",
                    "EXISTS key - Check if key exists",
                    "KEYS - List all keys",
                    "EXPIRE key seconds - Set timeout on a key",
                    "TTL key - Get remaining time to live",
                    "INCR key - Increment integer value",
                    "DECR key - Decrement integer value",
                    "LPUSH key value... - Insert elements at head of list",
                    "RPUSH key value... - Append elements to tail of list",
                    "LRANGE key start stop - Get range of elements from list",
                    "LPOP key - Remove and return first element of list",
                    "RPOP key - Remove and return last element of list",
                    "LLEN key - Return length of list",
                    "HSET key field value - Set hash field to value",
                    "HGET key field - Get hash field value",
                    "HDEL key field... - Delete one or more hash fields",
                    "HGETALL key - Get all fields and values in hash",
                    "SADD key member... - Add one or more members to set",
                    "SMEMBERS key - Get all members of set",
                    "SREM key member... - Remove one or more members from set",
                    "SISMEMBER key member - Check membership in set",
                    "SCARD key - Return number of members in set",
                    "FLUSHALL - Clear all stored data",
                    "HELP - Show manual",
                    "QUIT - Exit server"
                ]
                return "\n".join(commands)
            elif cmd == "QUIT":
                self.running = False
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
            engine.running = False
            break

if __name__ == "__main__":
    main()
import socket
import sys

try:
    import readline
except ImportError:
    pass

def main():
    host = "127.0.0.1"
    port = 6379

    if len(sys.argv) >= 2:
        host = sys.argv[1]
    if len(sys.argv) >= 3:
        try:
            port = int(sys.argv[2])
        except ValueError:
            print("Ervenytelen portszam.")
            return

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect((host, port))
    except ConnectionRefusedError:
        print(f"Nem sikerult kapcsolodni a szerverhez: {host}:{port}")
        return

    print(f"Csatlakozva a Mini-Redis szerverhez ({host}:{port})")
    print("Hasznald a HELP parancsot a leirashoz, kilepeshez ird be: QUIT\n")

    while True:
        try:
            cmd = input(f"{host}:{port}> ").strip()
            if not cmd:
                continue

            sock.sendall((cmd + "\n").encode("utf-8"))
            data = sock.recv(65536)
            if not data:
                print("A szerver bontotta a kapcsolatot.")
                break

            response = data.decode("utf-8").rstrip("\r\n")
            print(response)

            if cmd.upper() == "QUIT":
                break
        except (KeyboardInterrupt, EOFError):
            try:
                sock.sendall(b"QUIT\n")
            except Exception:
                pass
            print("\nViszlat!")
            break
        except Exception as e:
            print(f"Hiba tortent: {e}")
            break

    sock.close()

if __name__ == "__main__":
    main()
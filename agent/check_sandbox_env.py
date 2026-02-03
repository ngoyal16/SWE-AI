import logging
import sys
import time
from agent.sandbox.daytona import DaytonaSandbox
from agent.common.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(message)s')

def check_env():
    session_id = f"debug-env-{int(time.time())}"
    print(f"Creating debug session: {session_id}")
    
    try:
        sandbox = DaytonaSandbox(session_id)
        print("Setting up sandbox...")
        sandbox.setup()
        
        commands = [
            "git --version",
            "curl --version",
            "openssl version",
            "cat /etc/os-release",
            "getent ahosts gitlab.pixelvide.com",
            "curl -4 ifconfig.io",
            "curl -4 -vkI https://gitlab.pixelvide.com/"
        ]
        
        print("\n=== SYSTEM VERSIONS ===")
        for cmd in commands:
            print(f"\n[COMMAND] {cmd}")
            try:
                res = sandbox.run_command(cmd)
                print(res.strip())
            except Exception as e:
                print(f"Error: {e}")
        print("\n=======================\n")
        
        print("Tearing down sandbox...")
        sandbox.teardown()
        
    except Exception as e:
        print(f"Failed to check environment: {e}")
        sys.exit(1)

if __name__ == "__main__":
    check_env()

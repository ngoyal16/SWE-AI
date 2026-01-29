import os
import shutil
from app.tools import create_filesystem_tools
from app.config import settings

# Setup workspace
if os.path.exists(settings.WORKSPACE_DIR):
    shutil.rmtree(settings.WORKSPACE_DIR)
os.makedirs(settings.WORKSPACE_DIR)

def test_tools():
    # Setup tools for the workspace
    tools = create_filesystem_tools(settings.WORKSPACE_DIR)
    tool_map = {t.name: t for t in tools}

    print("Testing write_file...")
    res = tool_map["write_file"].invoke({"filepath": "test.txt", "content": "Hello World"})
    print(res)
    assert "Successfully wrote" in res

    print("\nTesting read_file...")
    content = tool_map["read_file"].invoke({"filepath": "test.txt"})
    print(f"Content: {content}")
    assert content == "Hello World"

    print("\nTesting list_files...")
    files = tool_map["list_files"].invoke({"path": "."})
    print(f"Files: {files}")
    assert "test.txt" in files

    print("\nTesting run_command...")
    output = tool_map["run_command"].invoke({"command": "ls -l"})
    print(f"Output: {output}")
    assert "test.txt" in output

    print("\nAll tool tests passed!")

if __name__ == "__main__":
    test_tools()

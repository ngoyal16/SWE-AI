import os
import shutil
from app.tools import read_file, write_file, list_files, run_command
from app.config import settings

# Setup workspace
if os.path.exists(settings.WORKSPACE_DIR):
    shutil.rmtree(settings.WORKSPACE_DIR)
os.makedirs(settings.WORKSPACE_DIR)

def test_tools():
    print("Testing write_file...")
    res = write_file.invoke({"filepath": "test.txt", "content": "Hello World"})
    print(res)
    assert "Successfully wrote" in res

    print("\nTesting read_file...")
    content = read_file.invoke({"filepath": "test.txt"})
    print(f"Content: {content}")
    assert content == "Hello World"

    print("\nTesting list_files...")
    files = list_files.invoke({"path": "."})
    print(f"Files: {files}")
    assert "test.txt" in files

    print("\nTesting run_command...")
    output = run_command.invoke({"command": "ls -l"})
    print(f"Output: {output}")
    assert "test.txt" in output

    print("\nAll tool tests passed!")

if __name__ == "__main__":
    test_tools()

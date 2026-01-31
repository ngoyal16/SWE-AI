import os
import ssl
from app.sandbox.base import Sandbox
from app.config import settings

# Bypass SSL verification for self-signed certificates
try:
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    ssl._create_default_https_context = ssl._create_unverified_context
    # Deep patch for urllib3
    from urllib3.util import ssl_
    original_create_urllib3_context = ssl_.create_urllib3_context
    def unverified_create_urllib3_context(*args, **kwargs):
        kwargs['cert_reqs'] = ssl.CERT_NONE
        return original_create_urllib3_context(*args, **kwargs)
    ssl_.create_urllib3_context = unverified_create_urllib3_context
except (AttributeError, ImportError):
    pass

try:
    from daytona import Daytona, DaytonaConfig, CreateSandboxFromImageParams
except ImportError as e:
    print(f"Failed to import daytona: {e}")
    Daytona = None
    DaytonaConfig = None
    CreateSandboxFromImageParams = None

class DaytonaSandbox(Sandbox):
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.daytona = None
        self.sandbox = None

    def setup(self):
        if not Daytona:
            raise ImportError("Daytona SDK not installed. Please install 'daytona'.")

        config = DaytonaConfig(
            api_key=settings.DAYTONA_API_KEY,
            api_url=settings.DAYTONA_API_URL
        )
        self.daytona = Daytona(config)

        # Explicitly disable SSL verification on the internal api clients if they exist
        if hasattr(self.daytona, '_api_client'):
            self.daytona._api_client.configuration.verify_ssl = False
        if hasattr(self.daytona, '_sandbox_api'):
            self.daytona._sandbox_api.api_client.configuration.verify_ssl = False


        # Check if sandbox already exists (resuming?)
        # For now, we assume new session = new sandbox, or we try to find one.
        # But generic worker logic usually calls setup().
        # We try to create.

        params = CreateSandboxFromImageParams(
            name=f"swe-agent-{self.session_id}",
            image=settings.DAYTONA_TARGET_IMAGE
        )

        try:
            self.sandbox = self.daytona.create(params)
        except Exception as e:
            # Maybe it already exists?
            # We could try to find it.
            # But the SDK raises error.
            # Let's list sandboxes and check?
            # For now, just raise or print.
            print(f"Error creating sandbox: {e}")
            # Try to find existing
            sandboxes = self.daytona.list()
            for s in sandboxes:
                if s.name == f"swe-agent-{self.session_id}":
                    self.sandbox = s
                    break
            if not self.sandbox:
                raise e

        return self

    def teardown(self):
        if self.sandbox:
            try:
                self.daytona.delete(self.sandbox)
            except Exception as e:
                print(f"Error deleting sandbox: {e}")

    def run_command(self, command: str, cwd: str = None) -> str:
        if not self.sandbox:
            return "Error: Sandbox not initialized."

        try:
            resp = self.sandbox.process.exec(command, cwd=cwd)
            # Combine result and check exit code if needed, but the interface returns string output
            output = resp.result
            if resp.exit_code != 0:
                 # Should we append exit code info?
                 # Base sandbox usually just returns stdout/stderr.
                 pass
            return output
        except Exception as e:
            return f"Error running command: {str(e)}"

    def read_file(self, filepath: str) -> str:
        if not self.sandbox:
            return "Error: Sandbox not initialized."

        try:
            content_bytes = self.sandbox.fs.download_file(filepath)
            return content_bytes.decode('utf-8')
        except Exception as e:
            return f"Error reading file: {str(e)}"

    def write_file(self, filepath: str, content: str) -> str:
        if not self.sandbox:
            return "Error: Sandbox not initialized."

        try:
            self.sandbox.fs.upload_file(content.encode('utf-8'), filepath)
            return f"Successfully wrote to {filepath}"
        except Exception as e:
            return f"Error writing file: {str(e)}"

    def list_files(self, path: str) -> str:
        if not self.sandbox:
            return "Error: Sandbox not initialized."

        try:
            files = self.sandbox.fs.list_files(path)
            # Format: name/ for dirs, name for files
            formatted = []
            for f in files:
                name = f.name
                if f.is_dir:
                    name += "/"
                formatted.append(name)
            return "\n".join(formatted)
        except Exception as e:
            return f"Error listing files: {str(e)}"

    def get_root_path(self) -> str:
        if self.sandbox:
            return self.sandbox.get_work_dir()
        return "/workspace"

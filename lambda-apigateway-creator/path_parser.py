"""
Path parser for API Gateway resource paths.

Handles parsing and validation of URI paths.
"""
import re


class PathParser:
    """Parse and validate API Gateway resource paths."""

    def __init__(self, path):
        """
        Initialize path parser.

        Args:
            path: URI path (e.g., /v2/campaigns/{id})
        """
        self.path = path
        self.segments = self._parse_segments()

    def _parse_segments(self):
        """
        Parse path into segments.

        Returns:
            List of path segments
        """
        clean_path = self.path.strip("/")
        if not clean_path:
            return []

        return clean_path.split("/")

    def get_segments(self):
        """
        Get parsed segments.

        Returns:
            List of segments
        """
        return self.segments

    def has_parameters(self):
        """
        Check if path contains parameters.

        Returns:
            True if path has {param} placeholders
        """
        return bool(re.search(r'\{\w+\}', self.path))

    def get_parameters(self):
        """
        Extract parameter names from path.

        Returns:
            List of parameter names
        """
        return re.findall(r'\{(\w+)\}', self.path)

    def is_valid(self):
        """
        Validate path format.

        Returns:
            True if path is valid
        """
        if not self.path:
            return False

        if not self.path.startswith('/'):
            return False

        # Check for invalid characters
        if not re.match(r'^/[\w\-/{}]+$', self.path):
            return False

        return True

from .processing import process_file_stream
from .reporting import report_stats

def analyze_file(file_path: str) -> None:
    """
    Orchestrates the pre-cleaning analysis pipeline.

    1. Prints header.
    2. Displays native pandas info (memory, types).
    3. Streams file to update detailed stats.
    4. Prints comprehensive report.
    """

    # 2. Deep Analysis (Stream/PyArrow)
    stats = process_file_stream(file_path)

    # 3. Report
    report_stats(stats)

import os
from IPython.display import display, Markdown
from .processing import process_file_stream
from .reporting import report_stats

def analyze_file(file_path: str) -> None:
    """
    Orchestrates the pre-cleaning analysis pipeline.

    1. Prints header.
    2. Streams file to update stats.
    3. Prints comprehensive report.
    """

    filename = os.path.basename(file_path)
    # Emojis in display(...) are fine as they are not source code literals but data
    display(Markdown(f"### Analysis: `{filename}`"))
    print(f"{'='*40}")

    # Process
    stats = process_file_stream(file_path)

    # Report
    report_stats(stats)

    print(f"{'='*40}\n")

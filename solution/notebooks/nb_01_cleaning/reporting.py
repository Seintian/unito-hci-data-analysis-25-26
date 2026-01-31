from typing import Dict, Any, List


def display_cleaning_summary(step_name: str, metrics: Dict[str, Any]):
    """
    Displays a user-friendly summary of the cleaning process.
    """

    print(f"--- {step_name} Summary ---")

    for key, value in metrics.items():
        if key == 'id_map':
            print(f"  Merges (ID Mappings): {len(value)}")
        elif isinstance(value, float):
            print(f"  {key}: {value:.2f}")
        else:
            print(f"  {key}: {value}")

def display_foreign_key_merges(samples: List[Dict]):
    """
    Displays samples of ID remappings applied to foreign keys.
    """

    if not samples:
        return

    print("\n--- Foreign Key Remapping ---")
    print("Updated references to merged IDs:")

    for i, sample_batch in enumerate(samples, 1):
        mappings = ", ".join([f"{old} -> {new:.0f}" for old, new in sample_batch.items()])
        print(f"  Batch {i}: {mappings}")
    print("-" * 30)

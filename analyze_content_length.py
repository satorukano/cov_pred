#!/usr/bin/env python3
"""
Analyze role user content token count from bulk_training.jsonl and bulk_validation.jsonl
in output/activemq_59 and output/zookeeper_48 directories using Llama3 tokenizer.
"""

import json
from pathlib import Path
from typing import List, Tuple
from transformers import AutoTokenizer


def get_llama3_tokenizer():
    """
    Load and return the Llama3 tokenizer.

    Returns:
        Llama3 tokenizer instance
    """
    # Using Llama3 model tokenizer
    tokenizer = AutoTokenizer.from_pretrained("meta-llama/Meta-Llama-3-8B")
    return tokenizer


def load_oracle_data(oracle_file_path: Path) -> dict:
    """
    Load oracle data from bulk_validation_oracle.json file.

    Args:
        oracle_file_path: Path to the oracle JSON file

    Returns:
        Dictionary mapping test IDs to oracle content
    """
    if not oracle_file_path.exists():
        print(f"Warning: Oracle file {oracle_file_path} does not exist")
        return {}

    with open(oracle_file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def extract_user_content_tokens(file_path: Path, tokenizer, oracle_data: dict = None) -> List[Tuple[int, int, int, int, int, str]]:
    """
    Extract token counts from bulk_validation.jsonl file (Batch API format).
    For validation data, we check if the total tokens (user + assistant + oracle) exceed the threshold.

    Args:
        file_path: Path to the JSONL file
        tokenizer: Llama3 tokenizer instance
        oracle_data: Dictionary mapping test IDs to oracle content

    Returns:
        List of tuples (line_number, user_token_count, assistant_token_count, oracle_token_count, total_token_count, combined_content)
    """
    token_data = []
    oracle_data = oracle_data or {}

    with open(file_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            try:
                data = json.loads(line.strip())

                # Extract custom_id to match with oracle
                custom_id = data.get('custom_id', '')
                # Remove the trailing "-0", "-1", etc. from custom_id to match oracle key
                test_id = custom_id.rsplit('-', 1)[0] if custom_id else ''

                # Extract messages from body.messages (Batch API format)
                if 'body' in data and 'messages' in data['body']:
                    messages = data['body']['messages']
                    user_content = ''
                    assistant_content = ''

                    for msg in messages:
                        if isinstance(msg, dict):
                            if msg.get('role') == 'user':
                                user_content += msg.get('content', '')
                            elif msg.get('role') == 'assistant':
                                assistant_content += msg.get('content', '')

                    # Get oracle content for this test
                    oracle_content = oracle_data.get(test_id, '')

                    # Count tokens for user, assistant, oracle, and combined content
                    user_tokens = tokenizer.encode(user_content) if user_content else []
                    assistant_tokens = tokenizer.encode(assistant_content) if assistant_content else []
                    oracle_tokens = tokenizer.encode(oracle_content) if oracle_content else []
                    combined_content = user_content + assistant_content + oracle_content
                    combined_tokens = tokenizer.encode(combined_content) if combined_content else []

                    user_token_count = len(user_tokens)
                    assistant_token_count = len(assistant_tokens)
                    oracle_token_count = len(oracle_tokens)
                    total_token_count = len(combined_tokens)

                    token_data.append((line_num, user_token_count, assistant_token_count, oracle_token_count, total_token_count, combined_content))

            except json.JSONDecodeError as e:
                print(f"Warning: Failed to parse line {line_num} in {file_path}: {e}")
                continue

    return token_data


def extract_combined_content_tokens(file_path: Path, tokenizer) -> List[Tuple[int, int, int, int, str]]:
    """
    Extract token counts of combined 'role: user' and 'role: assistant' content from a JSONL file.
    This is specifically for bulk_training.jsonl files.

    Args:
        file_path: Path to the JSONL file
        tokenizer: Llama3 tokenizer instance

    Returns:
        List of tuples (line_number, user_token_count, assistant_token_count, total_token_count, combined_content)
    """
    token_data = []

    with open(file_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            try:
                data = json.loads(line.strip())

                # Extract messages from the data
                if 'messages' in data:
                    messages = data['messages']
                    user_content = ''
                    assistant_content = ''

                    for msg in messages:
                        if isinstance(msg, dict):
                            if msg.get('role') == 'user':
                                user_content += msg.get('content', '')
                            elif msg.get('role') == 'assistant':
                                assistant_content += msg.get('content', '')

                    # Count tokens for user, assistant, and combined content
                    user_tokens = tokenizer.encode(user_content)
                    assistant_tokens = tokenizer.encode(assistant_content)
                    combined_content = user_content + assistant_content
                    combined_tokens = tokenizer.encode(combined_content)

                    user_token_count = len(user_tokens)
                    assistant_token_count = len(assistant_tokens)
                    total_token_count = len(combined_tokens)

                    token_data.append((line_num, user_token_count, assistant_token_count, total_token_count, combined_content))

            except json.JSONDecodeError as e:
                print(f"Warning: Failed to parse line {line_num} in {file_path}: {e}")
                continue

    return token_data


def main():
    # Define the directories and files to analyze
    base_dir = Path('output')
    projects = ['activemq_59', 'zookeeper_48']
    file_names = ['bulk_training.jsonl', 'bulk_validation.jsonl']

    # Token threshold
    TOKEN_THRESHOLD = 8192

    print("Loading Llama3 tokenizer...")
    tokenizer = get_llama3_tokenizer()
    print("Tokenizer loaded successfully!")
    print("=" * 60)

    # Load oracle data for each project
    oracle_data_map = {}
    for project in projects:
        oracle_file = base_dir / project / 'bulk_validation_oracle.json'
        oracle_data_map[project] = load_oracle_data(oracle_file)

    all_token_counts = []
    entries_over_threshold = []

    print(f"Analyzing content token counts (threshold: {TOKEN_THRESHOLD} tokens)...")
    print("=" * 60)

    # Process each project and file
    for project in projects:
        for file_name in file_names:
            file_path = base_dir / project / file_name

            if not file_path.exists():
                print(f"Warning: {file_path} does not exist, skipping...")
                continue

            print(f"\nProcessing: {file_path}")

            # For bulk_training.jsonl, check combined user + assistant tokens
            if file_name == 'bulk_training.jsonl':
                token_data = extract_combined_content_tokens(file_path, tokenizer)

                if token_data:
                    total_token_counts = [total_count for _, _, _, total_count, _ in token_data]
                    user_token_counts = [user_count for _, user_count, _, _, _ in token_data]
                    assistant_token_counts = [assistant_count for _, _, assistant_count, _, _ in token_data]

                    over_threshold = [(line_num, user_count, assistant_count, total_count, content, file_path)
                                     for line_num, user_count, assistant_count, total_count, content in token_data
                                     if total_count > TOKEN_THRESHOLD]

                    print(f"  Found {len(token_data)} entries")
                    print(f"  User tokens - Min: {min(user_token_counts)}, Max: {max(user_token_counts)}, Avg: {sum(user_token_counts) / len(user_token_counts):.2f}")
                    print(f"  Assistant tokens - Min: {min(assistant_token_counts)}, Max: {max(assistant_token_counts)}, Avg: {sum(assistant_token_counts) / len(assistant_token_counts):.2f}")
                    print(f"  Total tokens - Min: {min(total_token_counts)}, Max: {max(total_token_counts)}, Avg: {sum(total_token_counts) / len(total_token_counts):.2f}")
                    print(f"  Entries over {TOKEN_THRESHOLD} tokens (combined): {len(over_threshold)}")

                    all_token_counts.extend(total_token_counts)
                    entries_over_threshold.extend(over_threshold)
                else:
                    print(f"  No content found")

            # For other files (bulk_validation.jsonl), check combined user + assistant + oracle tokens
            else:
                oracle_data = oracle_data_map.get(project, {})
                token_data = extract_user_content_tokens(file_path, tokenizer, oracle_data)

                if token_data:
                    total_token_counts = [total_count for _, _, _, _, total_count, _ in token_data]
                    user_token_counts = [user_count for _, user_count, _, _, _, _ in token_data]
                    assistant_token_counts = [assistant_count for _, _, assistant_count, _, _, _ in token_data]
                    oracle_token_counts = [oracle_count for _, _, _, oracle_count, _, _ in token_data]

                    over_threshold = [(line_num, user_count, assistant_count, oracle_count, total_count, content, file_path)
                                     for line_num, user_count, assistant_count, oracle_count, total_count, content in token_data
                                     if total_count > TOKEN_THRESHOLD]

                    print(f"  Found {len(token_data)} entries")
                    print(f"  User tokens - Min: {min(user_token_counts)}, Max: {max(user_token_counts)}, Avg: {sum(user_token_counts) / len(user_token_counts):.2f}")
                    print(f"  Assistant tokens - Min: {min(assistant_token_counts)}, Max: {max(assistant_token_counts)}, Avg: {sum(assistant_token_counts) / len(assistant_token_counts):.2f}")
                    print(f"  Oracle tokens - Min: {min(oracle_token_counts)}, Max: {max(oracle_token_counts)}, Avg: {sum(oracle_token_counts) / len(oracle_token_counts):.2f}")
                    print(f"  Total tokens - Min: {min(total_token_counts)}, Max: {max(total_token_counts)}, Avg: {sum(total_token_counts) / len(total_token_counts):.2f}")
                    print(f"  Entries over {TOKEN_THRESHOLD} tokens (combined): {len(over_threshold)}")

                    all_token_counts.extend(total_token_counts)
                    entries_over_threshold.extend(over_threshold)
                else:
                    print(f"  No content found")

    # Print overall statistics
    print("\n" + "=" * 60)
    print("Overall Statistics (Both directories combined)")
    print("=" * 60)

    if all_token_counts:
        print(f"Total user content entries: {len(all_token_counts)}")
        print(f"Minimum token count: {min(all_token_counts)}")
        print(f"Maximum token count: {max(all_token_counts)}")
        print(f"Average token count: {sum(all_token_counts) / len(all_token_counts):.2f}")
        print(f"Total entries over {TOKEN_THRESHOLD} tokens: {len(entries_over_threshold)}")

        # Display entries that exceed the threshold
        if entries_over_threshold:
            print("\n" + "=" * 60)
            print(f"Entries exceeding {TOKEN_THRESHOLD} tokens:")
            print("=" * 60)
    else:
        print("No user content found in any files")


if __name__ == "__main__":
    main()

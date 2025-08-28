def format_for_gpt_training(item):
    return {
        "messages": [
            {
                "role": "system",
                "content": "Given two application logs, provide estimated execution paths between two logs, where applicable: file name: executed lines|file name: executed lines"
            },
            {
                "role": "user",
                "content": item.keys()[0]
            },
            {
                "role": "assistant",
                "content": item.values()[0]
            }
        ]
    }
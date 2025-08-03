import json


def parse_llm_recommendations(content):
    start_marker = "```json"
    end_marker = "```"

    try:

        start_index = content.find(start_marker)

        if start_index == -1:
            print(f"No '{start_marker}' found in the file.")
            return None

        json_content_start = start_index + len(start_marker)

        end_index = content.find(end_marker, json_content_start)

        if end_index == -1:
            print(f"'{start_marker}' found, but no matching '{end_marker}' afterwards.")
            return None

        json_string = content[json_content_start:end_index].strip()

        if not json_string:
            print("Extracted JSON content is empty.")
            return None

        try:
            data = json.loads(json_string)
            print("JSON data successfully extracted and loaded!")
            return data
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON: {e}")
            print(f"Problematic JSON string:\n---\n{json_string}\n---")
            return None

    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None

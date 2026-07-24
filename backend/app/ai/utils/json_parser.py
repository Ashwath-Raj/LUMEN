import json
import re

def extract_json_from_text(text: str) -> dict | list:
    """
    Extracts and parses JSON from a text string. 
    Handles cases where the LLM wraps the response in markdown code blocks.
    
    Raises json.JSONDecodeError if valid JSON cannot be found.
    """
    # Try to parse the entire text first
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        pass
        
    # Look for json markdown block
    match = re.search(r'```(?:json)?\s*(.*?)\s*```', text, re.DOTALL)
    if match:
        json_str = match.group(1).strip()
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            pass
            
    # Try to find the first '{' or '[' and the last '}' or ']'
    start_idx = text.find('{')
    list_start_idx = text.find('[')
    
    if start_idx == -1 and list_start_idx == -1:
        raise json.JSONDecodeError("No JSON object or array found in text", text, 0)
        
    if start_idx != -1 and (list_start_idx == -1 or start_idx < list_start_idx):
        # Starts with object
        end_idx = text.rfind('}')
        if end_idx != -1 and end_idx > start_idx:
            json_str = text[start_idx:end_idx+1]
            return json.loads(json_str)
            
    if list_start_idx != -1 and (start_idx == -1 or list_start_idx < start_idx):
        # Starts with array
        end_idx = text.rfind(']')
        if end_idx != -1 and end_idx > list_start_idx:
            json_str = text[list_start_idx:end_idx+1]
            return json.loads(json_str)
            
    raise json.JSONDecodeError("Could not extract JSON from text", text, 0)

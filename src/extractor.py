import os
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


def get_client():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    return OpenAI(
        api_key=api_key,
        base_url=os.getenv("OPENAI_BASE_URL"),
        timeout=120.0
    )

def extract_relationships(text, subject_name):
    """
    Extracts relationships from the given text using an LLM.
    
    Args:
        text (str): The text to analyze.
        subject_name (str): The name of the main subject (celebrity).
        
    Returns:
        list: A list of tuples (source, target, relation).
    """
    client = get_client()
    if not client:
        print("Warning: OPENAI_API_KEY not found. Skipping relationship extraction.")
        return []
    
    language = os.getenv("DEFAULT_LANGUAGE", "en")
    language_instruction = ""
    if language == "zh":
        language_instruction = "IMPORTANT: Translate the 'relation' description into Chinese (Simplified)."
    
    prompt = f"""
    You are an expert information extraction system.
    Your task is to extract relationships involving "{subject_name}" from the provided text.
    
    IMPORTANT: Focus ONLY on relationships with other FAMOUS PEOPLE, CELEBRITIES, or PUBLIC FIGURES.
    Do not include non-famous family members (unless they are also public figures), generic groups, or organizations unless highly relevant.
    
    {language_instruction}
    
    Return the output as a JSON list of objects, where each object has:
    - "source": The subject of the relationship (should be "{subject_name}").
    - "target": The object of the relationship (must be a specific famous person or public figure).
    - "relation": A concise description of the relationship (e.g., "dated", "collaborated with", "rival").
    - "intimacy": An integer score from 1 to 10 indicating the closeness of the relationship (10 = extremely close/family/spouse, 1 = distant/acquaintance).
    
    Limit to the most important 20 relationships.
    
    Text:
    {text[:4000]}  # Limit text length to avoid token limits
    """
    
    try:
        model_name = os.getenv("OPENAI_MODEL_NAME", "qwen3-30b-a3b-instruct-2507")
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": "You are a helpful assistant that extracts relationship triplets."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        
        content = response.choices[0].message.content
        data = json.loads(content)
        
        relationships = []
        items = []
        
        # Handle different potential JSON structures
        if isinstance(data, list):
            items = data
        elif isinstance(data, dict):
            items = data.get("relationships", data.get("items", []))
            
        for item in items:
            # Ensure item is a dictionary
            if not isinstance(item, dict):
                continue
                
            source = item.get("source")
            target = item.get("target")
            relation = item.get("relation")
            intimacy = item.get("intimacy", 5) # Default to 5 if not provided
            
            if source and target and relation:
                relationships.append((source, target, relation, intimacy))
                
        return relationships

    except Exception as e:
        # Check for data inspection failed (Aliyun/Content Filter)
        error_str = str(e)
        if "data_inspection_failed" in error_str or "400" in error_str:
            print(f"Content Filter Error: {e}")
            raise ValueError("Content Blocked") # Raise specific error for app.py to handle
            
        print(f"Error extracting relationships: {e}")
        return []

if __name__ == "__main__":
    # Test with dummy text
    text = "Taylor Swift is an American singer. She dated Travis Kelce. Her father is Scott Swift."
    print(extract_relationships(text, "Taylor Swift"))

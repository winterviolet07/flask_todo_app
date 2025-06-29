import requests
import json

def test_extraction():
    url = "http://127.0.0.1:5000/debug-extract"
    
    # Test text containing all 6 action items
    text = """
    We need to meet with Arista next week. 
    We gotta get their eyes on it and see what we need to do. 
    We need to start moving them to what they need to do. 
    We have to make a payment service and all the stuff that revolves around that. 
    We need to handle data for autopay and scheduled payments. 
    Finally, we need to transition everything over.
    """
    
    # Make the POST request
    response = requests.post(
        url,
        json={"text": text},
        headers={"Content-Type": "application/json"}
    )
    
    # Print the results
    print("Status Code:", response.status_code)
    print("\nResponse:")
    print(json.dumps(response.json(), indent=2))

if __name__ == "__main__":
    test_extraction() 
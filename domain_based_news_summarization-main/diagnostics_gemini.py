#!/usr/bin/env python3
"""
Diagnose Gemini API issues and test available models
"""

import sys
import os

# Suppress deprecation warning for now
import warnings
warnings.filterwarnings("ignore")

try:
    import google.generativeai as genai
    
    # Use the API key from environment or fallback
    api_key = os.environ.get("GEMINI_API_KEY", "AIzaSyCIhq2ZgJqHGfq6E2TbmUpN9JrnOqskA3c")
    
    print("=" * 60)
    print("GEMINI API DIAGNOSTICS")
    print("=" * 60)
    
    print(f"\n[1] API Key Status:")
    print(f"    Key provided: {'✓ Yes' if api_key else '✗ No'}")
    print(f"    Key length: {len(api_key)}")
    print(f"    Key starts with: {api_key[:10]}...")
    
    print(f"\n[2] Configuring Gemini...")
    try:
        genai.configure(api_key=api_key)
        print("    ✓ Configuration successful")
    except Exception as e:
        print(f"    ✗ Configuration failed: {e}")
        sys.exit(1)
    
    print(f"\n[3] Listing available models...")
    try:
        models = genai.list_models()
        available_models = []
        for model in models:
            # Check if model supports generateContent
            capabilities = [method for method in dir(model) if not method.startswith('_')]
            if any('generate' in cap.lower() for cap in model.__dict__):
                available_models.append(model.name)
        
        if available_models:
            print(f"    ✓ Found {len(available_models)} models:")
            for model in available_models[:10]:  # Show first 10
                print(f"      - {model}")
        else:
            print("    ✗ No available models found")
    except Exception as e:
        print(f"    ✗ Error listing models: {e}")
        print("\n    Note: This might be due to invalid API key or quota limits")
        sys.exit(1)
    
    print(f"\n[4] Testing model instantiation...")
    test_models = [
        "gemini-1.5-flash",
        "gemini-1.5-pro",
        "gemini-pro",
        "gemini-2.0-flash",
        "gemini-2.0-pro"
    ]
    
    working_model = None
    for model_name in test_models:
        try:
            model = genai.GenerativeModel(model_name)
            print(f"    ✓ {model_name}: Available")
            if not working_model:
                working_model = model_name
        except Exception as e:
            print(f"    ✗ {model_name}: {str(e)[:50]}...")
    
    if working_model:
        print(f"\n[5] Testing API call with {working_model}...")
        try:
            model = genai.GenerativeModel(working_model)
            response = model.generate_content("Say 'hello' in one word")
            print(f"    ✓ API call successful")
            print(f"    Response: {response.text[:50]}...")
        except Exception as e:
            print(f"    ✗ API call failed: {e}")
    
    print("\n" + "=" * 60)
    print("RECOMMENDATIONS")
    print("=" * 60)
    
    if not available_models:
        print("""
✗ No models available - possible causes:
  1. Invalid API key
  2. API key doesn't have Generative AI access
  3. API key quota exceeded
  4. Google Cloud project not configured
  
Fix:
  - Get a valid API key from https://aistudio.google.com/app/apikey
  - Ensure the project has Generative AI API enabled
  - Check quota at https://console.cloud.google.com/quotas
""")
    elif not working_model:
        print("""
✗ No working models found - this shouldn't happen
  Please check API key validity
""")
    else:
        print(f"""
✓ Working model found: {working_model}
  
To fix the backend, update backend/main.py:
  Change: model = genai.GenerativeModel("gemini-1.5-flash")
  To:     model = genai.GenerativeModel("{working_model}")
""")
    
    print("=" * 60)

except ImportError:
    print("✗ google.generativeai not installed")
    print("  Run: pip install -q google-generativeai")
    sys.exit(1)
except Exception as e:
    print(f"✗ Unexpected error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

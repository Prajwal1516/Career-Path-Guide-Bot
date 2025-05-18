import streamlit as st
import json
from groq import Groq
import re
import time

# Set page configuration
st.set_page_config(
    page_title="Career Path Guide Bot",
    page_icon="🧭",
    layout="centered",
    initial_sidebar_state="expanded"
)

# Hardcoded API key - replace "your_api_key_here" with your actual Groq API key
GROQ_API_KEY = "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"

# Initialize session states
if "api_configured" not in st.session_state:
    st.session_state.api_configured = True  # Set to True by default since we're hardcoding

# Your Groq API key is now hardcoded
if "api_key" not in st.session_state:
    st.session_state.api_key = GROQ_API_KEY

# Initialize Groq client with hardcoded API key
@st.cache_resource(show_spinner=False)
def get_groq_client(api_key):
    if not api_key:
        return None
    try:
        client = Groq(api_key=api_key)
        # Test the client with a minimal request
        client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[{"role": "user", "content": "test"}],
            max_tokens=10
        )
        return client
    except Exception as e:
        st.error(f"Failed to initialize API client: {str(e)}")
        return None

# Completely revised JSON parsing function with better pattern matching
def extract_json_from_text(text):
    """Extract valid JSON from text that might contain markdown or other content."""
    # Try multiple approaches to find valid JSON
    
    # First, try to extract JSON between triple backticks with or without json tag
    json_patterns = [
        r"```json\s*([\s\S]*?)```",  # JSON with json tag
        r"```\s*([\s\S]*?)```",       # JSON without specific tag
    ]
    
    for pattern in json_patterns:
        matches = re.findall(pattern, text, re.DOTALL)
        if matches:
            for json_str in matches:
                try:
                    return json.loads(json_str.strip())
                except json.JSONDecodeError:
                    continue  # Try next match or pattern
    
    # Try extracting between outermost braces
    try:
        start_idx = text.find('{')
        end_idx = text.rfind('}') + 1
        
        if start_idx >= 0 and end_idx > start_idx:
            json_str = text[start_idx:end_idx]
            return json.loads(json_str)
    except json.JSONDecodeError:
        pass  # Continue to more aggressive approaches
    
    # Try to fix common JSON issues with progressive repair attempts
    try:
        # Find what looks like JSON between braces with more precise regex
        json_candidate = re.search(r'(\{[\s\S]*\})', text)
        if json_candidate:
            json_str = json_candidate.group(1)
            
            # Series of fixes for common issues
            
            # 1. Fix misnamed keys (specifically the "needed" issue)
            json_str = json_str.replace('"needed":', '"skills_needed":')
            
            # 2. Fix missing quotes around keys
            json_str = re.sub(r'([{,]\s*)(\w+)(\s*:)', r'\1"\2"\3', json_str)
            
            # 3. Fix trailing commas in lists/objects
            json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)
            
            # 4. Fix single quotes to double quotes
            json_str = json_str.replace("'", '"')
            
            # 5. Fix unquoted values
            json_str = re.sub(r':\s*([^"{}\[\],\s][^,\]}]*)', r': "\1"', json_str)
            
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                pass  # Continue if this fix attempt failed
                
            # 6. More aggressive repair: handle all key-value pairs individually
            result = {}
            try:
                # Find all career recommendations sections
                career_sections = re.findall(r'"career_recommendations"\s*:\s*\[([\s\S]*?)\]', json_str)
                if career_sections:
                    careers = []
                    career_items = re.findall(r'\{([\s\S]*?)\}', career_sections[0])
                    for item in career_items:
                        career = {}
                        # Extract key fields with flexible patterns
                        title_match = re.search(r'"title"\s*:\s*"([^"]*)"', item)
                        if title_match:
                            career["title"] = title_match.group(1)
                        
                        desc_match = re.search(r'"description"\s*:\s*"([^"]*)"', item)
                        if desc_match:
                            career["description"] = desc_match.group(1)
                            
                        match_match = re.search(r'"match_reason"\s*:\s*"([^"]*)"', item)
                        if match_match:
                            career["match_reason"] = match_match.group(1)
                            
                        edu_match = re.search(r'"education_requirements"\s*:\s*"([^"]*)"', item)
                        if edu_match:
                            career["education_requirements"] = edu_match.group(1)
                            
                        # Handle both "skills_needed" and "needed" keys
                        skills_match = re.search(r'"skills_needed"\s*:\s*\[([\s\S]*?)\]', item)
                        if skills_match:
                            skills_text = skills_match.group(1)
                            career["skills_needed"] = [s.strip(' "\'') for s in skills_text.split(',')]
                        else:
                            needed_match = re.search(r'"needed"\s*:\s*\[([\s\S]*?)\]', item)
                            if needed_match:
                                skills_text = needed_match.group(1)
                                career["skills_needed"] = [s.strip(' "\'') for s in skills_text.split(',')]
                            
                        growth_match = re.search(r'"growth_outlook"\s*:\s*"([^"]*)"', item)
                        if growth_match:
                            career["growth_outlook"] = growth_match.group(1)
                            
                        if career:  # Only add if we found at least one field
                            careers.append(career)
                    
                    if careers:
                        result["career_recommendations"] = careers
                        
                # Similar approach for educational paths and other sections
                # ... add more extraction patterns for other sections...
                
                if result and "career_recommendations" in result:
                    return result
            except Exception:
                pass  # Fallback to default
    except Exception:
        pass  # Fallback to default
    
    # If all extraction attempts fail, return default response
    return create_default_response("Could not extract valid JSON from response")

# Create a standardized default response
def create_default_response(error_message):
    return {
        "career_recommendations": [
            {
                "title": "Software Developer",
                "description": "Develops applications and systems using programming languages and development tools.",
                "match_reason": "Based on your profile. Note: " + error_message,
                "education_requirements": "Bachelor's degree in Computer Science or related field",
                "skills_needed": ["Programming", "Problem Solving", "Teamwork"],
                "growth_outlook": "Excellent growth prospects in the tech industry"
            },
            {
                "title": "Data Analyst",
                "description": "Analyzes data to extract insights and support decision-making.",
                "match_reason": "Based on your profile. Note: " + error_message,
                "education_requirements": "Bachelor's degree in Statistics, Mathematics, or related field",
                "skills_needed": ["Data Analysis", "SQL", "Visualization"],
                "growth_outlook": "Strong demand across industries"
            }
        ],
        "educational_paths": [
            {
                "path": "Computer Science Degree",
                "description": "Four-year bachelor's degree covering programming, algorithms, and computer systems.",
                "duration": "4 years",
                "recommended_resources": ["University Programs", "Online Courses"]
            },
            {
                "path": "Coding Bootcamp",
                "description": "Intensive program teaching practical coding skills for specific industries.",
                "duration": "3-6 months",
                "recommended_resources": ["Local Bootcamps", "Online Platforms"]
            }
        ],
        "next_steps": [
            "Research specific job requirements",
            "Develop a portfolio of projects",
            "Network with professionals in the field"
        ],
        "additional_advice": f"Note: {error_message}. This is a generic response. Please try again for personalized recommendations."
    }

# Career recommendation function using Groq - with improved error handling
def get_career_recommendations(client, user_profile):
    if not client:
        return create_error_response("API client not properly configured")
        
    system_prompt = """
    You are CareerGuide, an expert career counselor with deep knowledge of job markets, 
    career paths, educational requirements, and professional development. Analyze the 
    user's profile and provide tailored career recommendations.
    
    You MUST return a JSON object in the following format:
    
    {
        "career_recommendations": [
            {
                "title": "Career Title",
                "description": "Brief description of the career",
                "match_reason": "Why this matches their profile",
                "education_requirements": "Required education",
                "skills_needed": ["Skill 1", "Skill 2", "Skill 3"],
                "growth_outlook": "Growth prospects in this field"
            }
        ],
        "educational_paths": [
            {
                "path": "Educational path name",
                "description": "Description of this educational approach",
                "duration": "Typical time to complete",
                "recommended_resources": ["Resource 1", "Resource 2"]
            }
        ],
        "next_steps": ["Actionable step 1", "Actionable step 2", "Actionable step 3"],
        "additional_advice": "Personalized career development advice"
    }
    
    CRITICAL RULES:
    1. Use EXACTLY "skills_needed" (not "needed") as the key for skills
    2. All array fields must be properly formatted with square brackets
    3. Provide 3-5 well-matched career recommendations and 2-3 educational paths
    4. Return ONLY the JSON - no explanation, markdown, or formatting
    """
    
    user_prompt = f"""
    Please analyze this user profile and provide career guidance:
    
    Interests: {user_profile['interests']}
    Strengths: {user_profile['strengths']}
    Current Education: {user_profile['education']}
    Experience Level: {user_profile['experience']}
    Skills: {user_profile['skills']}
    Work Values: {user_profile['values']}
    Career Goals: {user_profile['goals']}
    
    Return ONLY the JSON object with career recommendations.
    """
    
    try:
        with st.spinner("Analyzing your profile..."):
            try:
                # First try with json response format
                try:
                    completion = client.chat.completions.create(
                        model="llama3-70b-8192",
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        temperature=0.2,
                        max_tokens=2048,
                        response_format={"type": "json_object"}  # Try with JSON response format first
                    )
                except Exception:
                    # If JSON response format fails, try without it
                    completion = client.chat.completions.create(
                        model="llama3-70b-8192",
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        temperature=0.2,
                        max_tokens=2048
                    )
                
                response_text = completion.choices[0].message.content
                
                # Process the JSON response
                try:
                    # First try direct parsing
                    json_data = json.loads(response_text)
                except json.JSONDecodeError:
                    # Fall back to extraction function if direct parsing fails
                    json_data = extract_json_from_text(response_text)
            except Exception as api_error:
                # Handle specific API errors
                error_str = str(api_error)
                if "json_validate_failed" in error_str and "failed_generation" in error_str:
                    # Try to extract the partial JSON from the error message
                    failed_json_match = re.search(r"'failed_generation': '(.*?)'}}", error_str, re.DOTALL)
                    if failed_json_match:
                        failed_json = failed_json_match.group(1)
                        # Try to extract JSON from the failed generation
                        json_data = extract_json_from_text(failed_json)
                    else:
                        # Couldn't extract JSON from error, use default
                        json_data = create_default_response("Error in API response format")
                else:
                    # Fall back to a second attempt with different parameters
                    try:
                        # Try a different approach with lower temperature
                        completion = client.chat.completions.create(
                            model="llama3-70b-8192",
                            messages=[
                                {"role": "system", "content": "Return only a JSON object following this structure: " + system_prompt},
                                {"role": "user", "content": user_prompt}
                            ],
                            temperature=0.1,  # Lower temperature for more deterministic output
                            max_tokens=2048
                        )
                        response_text = completion.choices[0].message.content
                        json_data = extract_json_from_text(response_text)
                    except Exception:
                        # If all else fails, use default response
                        json_data = create_default_response(f"API Error: {str(api_error)}")
                
            # Validate and fill in missing parts if needed
            json_data = ensure_valid_structure(json_data)
            return json_data
            
    except Exception as e:
        st.error(f"Error getting recommendations: {str(e)}")
        return create_error_response(f"Error: {str(e)}")

# Ensure valid JSON structure for recommendations - improved with better validation
def ensure_valid_structure(json_data):
    if not json_data:
        return create_default_response("Empty response")
        
    default_data = create_default_response("Partial data filled in")
    result = {}
    
    # Ensure all top-level keys exist
    required_keys = ["career_recommendations", "educational_paths", "next_steps", "additional_advice"]
    for key in required_keys:
        if key not in json_data or not json_data[key]:
            result[key] = default_data[key]
        else:
            result[key] = json_data[key]
    
    # Ensure career recommendations have all required fields
    if "career_recommendations" in json_data and json_data["career_recommendations"]:
        result["career_recommendations"] = []
        for i, career in enumerate(json_data["career_recommendations"]):
            clean_career = {}
            career_keys = ["title", "description", "match_reason", "education_requirements", "skills_needed", "growth_outlook"]
            
            # Special case for skills_needed/needed mixup
            if "needed" in career and "skills_needed" not in career:
                career["skills_needed"] = career["needed"]
                
            for key in career_keys:
                if key not in career or not career[key]:
                    if i < len(default_data["career_recommendations"]):
                        clean_career[key] = default_data["career_recommendations"][i][key]
                    else:
                        clean_career[key] = f"Default {key}"
                else:
                    clean_career[key] = career[key]
            
            # Ensure skills_needed is a list
            if not isinstance(clean_career["skills_needed"], list):
                if isinstance(clean_career["skills_needed"], str):
                    # Try to convert string to list by splitting
                    if "," in clean_career["skills_needed"]:
                        clean_career["skills_needed"] = [s.strip() for s in clean_career["skills_needed"].split(",")]
                    else:
                        clean_career["skills_needed"] = [clean_career["skills_needed"]]
                else:
                    clean_career["skills_needed"] = [str(clean_career["skills_needed"])]
            
            result["career_recommendations"].append(clean_career)
    else:
        result["career_recommendations"] = default_data["career_recommendations"]
    
    # Ensure educational paths have all required fields
    if "educational_paths" in json_data and json_data["educational_paths"]:
        result["educational_paths"] = []
        for i, path in enumerate(json_data["educational_paths"]):
            clean_path = {}
            path_keys = ["path", "description", "duration", "recommended_resources"]
            for key in path_keys:
                if key not in path or not path[key]:
                    if i < len(default_data["educational_paths"]):
                        clean_path[key] = default_data["educational_paths"][i][key]
                    else:
                        clean_path[key] = f"Default {key}"
                else:
                    clean_path[key] = path[key]
            
            # Ensure recommended_resources is a list
            if not isinstance(clean_path["recommended_resources"], list):
                if isinstance(clean_path["recommended_resources"], str):
                    # Try to convert string to list by splitting
                    if "," in clean_path["recommended_resources"]:
                        clean_path["recommended_resources"] = [s.strip() for s in clean_path["recommended_resources"].split(",")]
                    else:
                        clean_path["recommended_resources"] = [clean_path["recommended_resources"]]
                else:
                    clean_path["recommended_resources"] = [str(clean_path["recommended_resources"])]
            
            result["educational_paths"].append(clean_path)
    else:
        result["educational_paths"] = default_data["educational_paths"]
    
    # Ensure next_steps is a list
    if "next_steps" in json_data and json_data["next_steps"]:
        if not isinstance(json_data["next_steps"], list):
            if isinstance(json_data["next_steps"], str):
                # Try to convert string to list by splitting
                if "," in json_data["next_steps"]:
                    result["next_steps"] = [s.strip() for s in json_data["next_steps"].split(",")]
                else:
                    result["next_steps"] = [json_data["next_steps"]]
            else:
                result["next_steps"] = [str(json_data["next_steps"])]
        else:
            result["next_steps"] = json_data["next_steps"]
    else:
        result["next_steps"] = default_data["next_steps"]
    
    return result

# Create standardized error response
def create_error_response(error_message):
    return {
        "career_recommendations": [{
            "title": "Unable to generate recommendations",
            "description": "There was an error processing your request.",
            "match_reason": error_message,
            "education_requirements": "N/A",
            "skills_needed": ["N/A"],
            "growth_outlook": "N/A"
        }],
        "educational_paths": [{
            "path": "General education path",
            "description": "Please try again after resolving the error.",
            "duration": "Varies",
            "recommended_resources": ["Try again after fixing API connection"]
        }],
        "next_steps": ["Check your API key", 
                      "Verify your internet connection",
                      "Try again in a few minutes"],
        "additional_advice": f"Technical error: {error_message}. Please try again."
    }

# Function to get advice on specific career questions - with improved error handling
def get_career_advice(client, user_profile, question):
    if not client:
        return "I'm unable to connect to the career guidance service. Please check that your API key is correctly configured."
        
    try:
        with st.spinner("Thinking..."):
            system_prompt = """
            You are CareerGuide, an expert career counselor. Provide specific, actionable advice
            to career-related questions. Draw on the user's profile to personalize your guidance.
            Keep responses concise, practical and supportive.
            """
            
            user_context = f"""
            User profile:
            Interests: {user_profile['interests']}
            Strengths: {user_profile['strengths']}
            Current Education: {user_profile['education']}
            Experience: {user_profile['experience']}
            Skills: {user_profile['skills']}
            Values: {user_profile['values']}
            Goals: {user_profile['goals']}
            """
            
            user_prompt = f"{user_context}\n\nQuestion: {question}"
            
            # Add retry mechanism
            max_retries = 2
            retries = 0
            
            while retries <= max_retries:
                try:
                    completion = client.chat.completions.create(
                        model="llama3-70b-8192",
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        temperature=0.5,
                        max_tokens=1024
                    )
                    
                    return completion.choices[0].message.content
                except Exception as e:
                    retries += 1
                    if retries > max_retries:
                        return f"I'm having trouble connecting to the career guidance service right now. Error: {str(e)}"
                    time.sleep(1)  # Wait a second before retrying
            
    except Exception as e:
        return f"I'm having trouble connecting to the career guidance service right now. Error: {str(e)}"

# Sidebar for application info
with st.sidebar:
    st.title("🧭 Career Guide Bot")
    
    st.markdown("---")
    st.markdown("### About Career Path Guide")
    st.info("""
    This app helps you discover career paths based on your profile.
    
    1. Fill out your profile
    2. Get personalized recommendations
    3. Ask follow-up questions
    
    Your data is only used for generating recommendations.
    """)

# Main app
st.title("🧭 Career Path Guide Bot")
st.write("Discover your ideal career path based on your interests, strengths, and qualifications.")

# Initialize session state for various components
if "messages" not in st.session_state:
    st.session_state.messages = []

if "profile_completed" not in st.session_state:
    st.session_state.profile_completed = False
    
if "user_profile" not in st.session_state:
    st.session_state.user_profile = {
        "interests": "",
        "strengths": "",
        "education": "",
        "experience": "",
        "skills": "",
        "values": "",
        "goals": ""
    }

if "recommendations" not in st.session_state:
    st.session_state.recommendations = None

# Check if API client can be initialized
client = get_groq_client(st.session_state.api_key)
if not client:
    st.error("⚠️ API connection failed. Please check the hardcoded API key.")
else:
    # Profile collection tab
    if not st.session_state.profile_completed:
        st.subheader("Tell us about yourself")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.session_state.user_profile["interests"] = st.text_area(
                "What are your interests and passions?",
                help="E.g., technology, helping others, creative work, problem-solving",
                value=st.session_state.user_profile["interests"]
            )
            
            st.session_state.user_profile["strengths"] = st.text_area(
                "What are your key strengths?",
                help="E.g., analytical thinking, communication, creativity, organization",
                value=st.session_state.user_profile["strengths"]
            )
            
            st.session_state.user_profile["education"] = st.text_area(
                "What's your educational background?",
                help="E.g., degrees, certifications, or current studies",
                value=st.session_state.user_profile["education"]
            )
        
        with col2:
            st.session_state.user_profile["experience"] = st.selectbox(
                "What's your experience level?",
                ["Student/No experience", "Entry level (0-2 years)", 
                "Mid-level (3-5 years)", "Experienced (5+ years)"],
                index=0 if not st.session_state.user_profile["experience"] else 
                    ["Student/No experience", "Entry level (0-2 years)", 
                    "Mid-level (3-5 years)", "Experienced (5+ years)"].index(st.session_state.user_profile["experience"])
            )
            
            st.session_state.user_profile["skills"] = st.text_area(
                "What skills do you have?",
                help="E.g., programming languages, soft skills, technical skills",
                value=st.session_state.user_profile["skills"]
            )
            
            st.session_state.user_profile["values"] = st.text_area(
                "What do you value in a job?",
                help="E.g., work-life balance, high pay, creative freedom, stability",
                value=st.session_state.user_profile["values"]
            )
            
            st.session_state.user_profile["goals"] = st.text_area(
                "What are your career goals?",
                help="E.g., leadership roles, specialized expertise, entrepreneurship",
                value=st.session_state.user_profile["goals"]
            )
        
        if st.button("Get Career Recommendations", type="primary"):
            if not (st.session_state.user_profile["interests"] and 
                    st.session_state.user_profile["strengths"]):
                st.error("Please fill in at least your interests and strengths.")
            else:
                # Get recommendations
                recommendations = get_career_recommendations(client, st.session_state.user_profile)
                
                if recommendations:
                    st.session_state.recommendations = recommendations
                    st.session_state.profile_completed = True
                    
                    # Clear previous messages and add a single welcome message
                    st.session_state.messages = [{
                        "role": "assistant", 
                        "content": "I've analyzed your profile and prepared some career recommendations!"
                    }]
                    st.rerun()

    # Display recommendations and chat interface
    else:
        # Button to edit profile
        if st.button("Edit Profile"):
            st.session_state.profile_completed = False
            st.rerun()
            
        # Display recommendations
        if st.session_state.recommendations:
            recommendations = st.session_state.recommendations
            
            # Only show error message if we have a true error response
            if "title" in recommendations.get("career_recommendations", [{}])[0] and "Unable to generate" in recommendations["career_recommendations"][0]["title"]:
                st.error("There was an issue generating your career recommendations.")
                st.warning(recommendations["career_recommendations"][0]["match_reason"])
                
                if st.button("Try Again"):
                    st.session_state.profile_completed = False
                    st.rerun()
            else:
                st.subheader("🎯 Recommended Careers")
                
                # Check if there's a note about default responses
                if recommendations.get("additional_advice") and "Note:" in recommendations["additional_advice"]:
                    st.info("Note: Some recommendations may be generic due to processing limitations. For best results, try again if needed.")
                
                for i, career in enumerate(recommendations["career_recommendations"]):
                    with st.expander(f"{career['title']}", expanded=i==0):
                        st.markdown(f"**Description:** {career['description']}")
                        st.markdown(f"**Why this matches you:** {career['match_reason']}")
                        st.markdown(f"**Education needed:** {career['education_requirements']}")
                        st.markdown("**Key skills:**")
                        for skill in career['skills_needed']:
                            st.markdown(f"- {skill}")
                        st.markdown(f"**Growth outlook:** {career['growth_outlook']}")
                
                st.subheader("🎓 Educational Pathways")
                for path in recommendations["educational_paths"]:
                    with st.expander(f"{path['path']}"):
                        st.markdown(f"**Description:** {path['description']}")
                        st.markdown(f"**Typical duration:** {path['duration']}")
                        st.markdown("**Recommended resources:**")
                        for resource in path['recommended_resources']:
                            st.markdown(f"- {resource}")
                
                st.subheader("⏱️ Recommended Next Steps")
                for step in recommendations["next_steps"]:
                    st.markdown(f"- {step}")
                    
                st.markdown(f"**Additional Advice:** {recommendations['additional_advice']}")
        
        # Chat interface
        st.markdown("---")
        st.subheader("💬 Ask me about your career path")
        
        # Display chat messages
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        
        # Chat input
        if prompt := st.chat_input("Ask a question about your career options..."):
            # Add user message to chat history
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            # Display user message
            with st.chat_message("user"):
                st.markdown(prompt)
            
            # Generate and display assistant response
            with st.chat_message("assistant"):
                response = get_career_advice(client, st.session_state.user_profile, prompt)
                st.markdown(response)
            
            # Add assistant response to chat history
            st.session_state.messages.append({"role": "assistant", "content": response})
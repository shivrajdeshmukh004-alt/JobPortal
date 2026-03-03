from sambanova import SambaNova
import os
from django.conf import settings

def get_sambanova_response(prompt):
    """
    Sends a prompt to SambaNova AI and returns the generated text.
    """
    api_key = os.getenv('SAMBANOVA_API_KEY')
    if not api_key:
        return "SambaNova API Key not configured. Please add it to your .env file."

    try:
        client = SambaNova(
            api_key=api_key,
            base_url="https://api.sambanova.ai/v1",
        )
        
        # System instructions to make it professional and helpful
        system_instruction = (
            "You are RecruitAI Support Assistant. You help candidates and recruiters "
            "navigate the RecruitAI job portal. Be professional, concise, and helpful. "
            "If asked about technical issues, suggest contacting admin. "
            "If asked about job applications, explain that they can track them in 'My Applications'."
        )
        
        response = client.chat.completions.create(
            model="Meta-Llama-3.1-8B-Instruct",
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            top_p=0.1
        )
        
        return response.choices[0].message.content
    except Exception as e:
        return f"Error: {str(e)}"
